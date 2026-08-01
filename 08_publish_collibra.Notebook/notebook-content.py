# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "f7c297eb-4659-4600-ab89-0e860638fb6c",
# META       "default_lakehouse_name": "sql_query_lh",
# META       "default_lakehouse_workspace_id": "1f55e1c1-b660-4715-9b56-4140edce3940",
# META       "known_lakehouses": [
# META         {
# META           "id": "f7c297eb-4659-4600-ab89-0e860638fb6c"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "0776fc8d-1451-838d-47e6-f5c7a0bd174b",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# CELL ********************

"""Fabric Notebook: Publish Descriptions to Collibra

Reads from: graph_nodes, graph_edges (Delta tables)
Writes to:  Collibra Dev (REST API)

Wires together:
1. Graph traversal → identifies _PBI metrics and their graph context
2. Fabric Data Agent → generates business descriptions from SQL logic
3. Lineage matching → maps _PBI procs/views to Collibra PBI report assets
4. Collibra adapter → updates Description attribute on matched reports

Run 03_build_graph.py at least once before this.
"""

# %% Cell 0: Setup
import json
import sys
# If the wheel is installed via Fabric Environment, src is already importable.
# Fallback to sys.path for dev mode or non-wheel deployments.
try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from src.config import load_config

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

WORKSPACE_ID = config.fabric_graph.workspace_id
AGENT_ID = config.fabric_graph.data_agent_id

# %% Cell 1: Load graph from Delta
from src.models import GraphNode, NodeLayer, GraphEdge, EdgeType

nodes_df = spark.table(config.lakehouse.graph_nodes)
edges_df = spark.table(config.lakehouse.graph_edges)

nodes = {}
for row in nodes_df.collect():
    r = row.asDict()
    props = json.loads(r["properties"]) if r["properties"] else {}
    nodes[r["node_id"]] = GraphNode(
        node_id=r["node_id"],
        layer=NodeLayer(r["layer"]),
        name=r["name"],
        description=r["description"] or "",
        properties=props,
    )

edges = []
for row in edges_df.collect():
    r = row.asDict()
    props = json.loads(r["properties"]) if r["properties"] else {}
    edges.append(GraphEdge(
        source_id=r["source_id"],
        target_id=r["target_id"],
        edge_type=EdgeType(r["edge_type"]),
        properties=props,
    ))

print(f"Loaded {len(nodes)} nodes, {len(edges)} edges from Delta")

# %% Cell 2: Identify _PBI metrics
from src.adapters.collibra_lineage_match import extract_match_key

# Find canonical nodes with _PBI suffix
pbi_metrics = []
for node in nodes.values():
    if node.layer == NodeLayer.CANONICAL and extract_match_key(node.name) is not None:
        pbi_metrics.append(node)

print(f"Found {len(pbi_metrics)} _PBI-suffixed canonical metrics")
for m in pbi_metrics[:5]:
    print(f"  {m.name} (key: '{extract_match_key(m.name)}')")
if len(pbi_metrics) > 5:
    print(f"  ... and {len(pbi_metrics) - 5} more")

# %% Cell 3: Generate business descriptions via Data Agent (incremental)
import hashlib
from src.adapters.fabric_agent import FabricAgentClient

# mssparkutils is injected into notebook scope but not importable from modules
token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")

agent = FabricAgentClient(
    workspace_id=WORKSPACE_ID,
    agent_id=AGENT_ID,
    access_token=token,
)

tool_name = agent.discover_tool_name()
print(f"Data Agent tool: {tool_name}")

# Compute SQL hash for each _PBI metric from metric_logic
sql_hashes = {}
try:
    ml_df = spark.table("output_metric_logic")
    for row in ml_df.collect():
        r = row.asDict()
        logic = r.get("calculation_logic") or ""
        sql_hashes[r["metric_name"]] = hashlib.sha256(logic.encode()).hexdigest()[:16]
except Exception:
    print("  metric_logic table not found — will generate all descriptions")

# Load existing descriptions (if any)
existing_descs = {}
existing_hashes = {}
try:
    existing_df = spark.table("ops_agent_descriptions")
    for row in existing_df.collect():
        r = row.asDict()
        existing_descs[r["metric_name"]] = r["description"]
        existing_hashes[r["metric_name"]] = r.get("sql_hash", "")
except Exception:
    print("  No existing agent_descriptions table — will generate all")

# Determine which metrics need (re)generation
needs_generation = []
for m in pbi_metrics:
    current_hash = sql_hashes.get(m.name, "")
    prev_hash = existing_hashes.get(m.name, "")

    if m.name not in existing_descs:
        needs_generation.append(m.name)  # new metric
    elif current_hash and current_hash != prev_hash:
        needs_generation.append(m.name)  # SQL changed
    # else: description exists and SQL unchanged — skip

reused = len(pbi_metrics) - len(needs_generation)
print(f"\n{len(pbi_metrics)} _PBI metrics total")
print(f"  {reused} already have current descriptions (skipped)")
print(f"  {len(needs_generation)} need generation")

# Generate only for new/changed metrics, saving incrementally to Delta.
# This ensures descriptions survive token expiry — just restart kernel
# and re-run; already-generated descriptions will be skipped.
from pyspark.sql.types import StructType, StructField, StringType

REJECT_PHRASES = ["wasn't able to find", "couldn't find", "not found", "hasn't been", "I'm happy to help"]
SAVE_EVERY = 25  # persist to Delta every N successful generations

desc_schema = StructType([
    StructField("metric_name", StringType(), False),
    StructField("description", StringType(), False),
    StructField("sql_hash", StringType(), True),
])

def _save_all_descriptions(desc_lookup, sql_hashes):
    """Persist all descriptions (existing + new) to Delta."""
    rows = [
        (name, desc, sql_hashes.get(name, ""))
        for name, desc in desc_lookup.items()
    ]
    df = spark.createDataFrame(rows, schema=desc_schema)
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("ops_agent_descriptions")
    return len(rows)

# Start with existing descriptions
desc_lookup = {}
for name, desc in existing_descs.items():
    if name not in needs_generation:
        desc_lookup[name] = desc

new_descs = {}
if needs_generation:
    succeeded = 0
    failed = 0
    unsaved_count = 0

    for i, name in enumerate(needs_generation):
        resp = agent.generate_metric_description(name)

        if resp.status == "success" and resp.answer:
            if any(phrase in resp.answer.lower() for phrase in REJECT_PHRASES):
                print(f"  REJECTED {name} — agent returned a non-answer")
                failed += 1
                continue
            new_descs[name] = resp.answer
            desc_lookup[name] = resp.answer
            succeeded += 1
            unsaved_count += 1
        else:
            failed += 1
            print(f"Failed for {name}: {resp.error}")

        # Incremental save every SAVE_EVERY successes
        if unsaved_count >= SAVE_EVERY:
            saved = _save_all_descriptions(desc_lookup, sql_hashes)
            print(f"  [{i+1}/{len(needs_generation)}] Saved {saved} total descriptions ({succeeded} new, {failed} failed)")
            unsaved_count = 0

        # Progress log
        elif (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(needs_generation)}] {succeeded} succeeded, {failed} failed")

    # Final save
    if unsaved_count > 0:
        saved = _save_all_descriptions(desc_lookup, sql_hashes)
        print(f"  Final save: {saved} total descriptions")

    print(f"\nGenerated {succeeded} new descriptions ({failed} failed)")
else:
    print("\nAll descriptions are current — nothing to generate.")

# Show newly generated samples
for name in list(new_descs.keys())[:3]:
    desc = new_descs[name]
    print(f"\n  NEW: {name}:")
    print(f"    {desc[:150]}..." if len(desc) > 150 else f"    {desc}")

# %% Cell 3c: Load descriptions from Delta (use instead of cell 3 + 3b on restart)
# Uncomment this cell and skip cells 3 + 3b if no regeneration needed.
# desc_df = spark.table("ops_agent_descriptions")
# desc_lookup = {row.metric_name: row.description for row in desc_df.collect()}
# print(f"Loaded {len(desc_lookup)} descriptions from Delta")

# %% Cell 4: Connect to Collibra and match to PBI reports
from src.adapters.collibra import CollibraAdapter, CollibraConfig
from src.adapters.collibra_lineage import CollibraClient
from src.adapters.collibra_lineage_match import CollibraLineageMatcher

collibra_cfg = config.adapters.collibra

adapter = CollibraAdapter(CollibraConfig(
    base_url=collibra_cfg.base_url,
    username=collibra_cfg.username,
    password=collibra_cfg.password,
    api_key=collibra_cfg.api_key,
    domain_id=collibra_cfg.domain_id,
    community_id=collibra_cfg.community_id,
    asset_type_id=collibra_cfg.asset_type_id,
))

base = collibra_cfg.base_url.replace("/rest/2.0", "")
client = CollibraClient(base, collibra_cfg.username, collibra_cfg.password)

print("Testing connection...")
if adapter.test_connection():
    print("Connected to Collibra!")
else:
    print("Connection failed. Check org_config.yaml")

# Match _PBI metrics to Collibra reports
objects = [{"object_name": name, "object_type": "SQL_STORED_PROCEDURE"} for name in desc_lookup]
matcher = CollibraLineageMatcher(client, min_score=0.5)
match_result = matcher.match_objects(objects)
print(f"\n{match_result}")

# %% Cell 5: Review matches before publishing
print(f"{'='*80}")
print(f"MATCHED — will update descriptions ({len(match_result.matched)})")
print(f"{'='*80}")

for m in match_result.matched:
    desc = desc_lookup.get(m.object_name, "")
    print(f"\n  Proc/View: {m.object_name}")
    print(f"  Collibra:  {m.report_name}")
    print(f"  Score:     {m.score:.2f}")
    print(f"  Description: {desc[:150]}..." if len(desc) > 150 else f"  Description: {desc}")

if match_result.unmatched_objects:
    print(f"\n{'='*80}")
    print(f"UNMATCHED — no Collibra report found ({len(match_result.unmatched_objects)})")
    print(f"{'='*80}")
    for name in match_result.unmatched_objects:
        print(f"  {name}  (key: '{extract_match_key(name)}')")

# %% Cell 6: Publish descriptions to Collibra
# Review cell 5 output first!
# To publish only specific reports, add names to PUBLISH_ONLY.
# Leave empty [] to publish all matched reports.

PUBLISH_ONLY = []  # e.g., ["CCHP Executive Dashboard", "Another Report"]

publish_results = []
for m in match_result.matched:
    if PUBLISH_ONLY and not any(name.lower() in m.report_name.lower() for name in PUBLISH_ONLY):
        continue

    desc = desc_lookup.get(m.object_name, "")
    if not desc:
        print(f"  SKIP {m.object_name} — no description generated")
        continue

    result = adapter.update_description(
        asset_name=m.report_name,
        description=desc,
    )
    publish_results.append((m.object_name, m.report_name, result))
    status = result.status.value
    print(f"  {status}: {m.object_name} → {result.message}")

# %% Cell 7: Summary
succeeded = sum(1 for _, _, r in publish_results if r.status.value == "success")
failed = sum(1 for _, _, r in publish_results if r.status.value == "failed")
skipped = len(match_result.matched) - len(publish_results)

print(f"\n{'='*80}")
print(f"PUBLISH SUMMARY")
print(f"{'='*80}")
print(f"  Total canonical metrics: {len([n for n in nodes.values() if n.layer == NodeLayer.CANONICAL])}")
print(f"  _PBI suffixed:           {len(pbi_metrics)}")
print(f"  Agent descriptions:      {len(desc_lookup)}")
print(f"  Matched to Collibra:     {len(match_result.matched)}")
print(f"  Published:               {succeeded}")
print(f"  Failed:                  {failed}")
print(f"  Skipped (no desc):       {skipped}")
print(f"  Unmatched:               {len(match_result.unmatched_objects)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
