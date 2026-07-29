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

# %% Cell 3: Generate business descriptions via Data Agent
from src.adapters.fabric_agent import FabricAgentClient

# mssparkutils is injected into notebook scope but not importable from modules
token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")

agent = FabricAgentClient(
    workspace_id=WORKSPACE_ID,
    agent_id=AGENT_ID,
    access_token=token,
)

# Discover the agent's tool name
tool_name = agent.discover_tool_name()
print(f"Data Agent tool: {tool_name}")

# Generate descriptions for each _PBI metric
metric_names = [m.name for m in pbi_metrics]
agent_results = agent.generate_descriptions_bulk(metric_names)

succeeded = sum(1 for r in agent_results.values() if r.status == "success")
failed = sum(1 for r in agent_results.values() if r.status == "failed")
print(f"\nGenerated {succeeded} descriptions ({failed} failed)")

# Build description lookup
desc_lookup = {}
for name, resp in agent_results.items():
    if resp.status == "success" and resp.answer:
        desc_lookup[name] = resp.answer

# Show samples
for name in list(desc_lookup.keys())[:3]:
    desc = desc_lookup[name]
    print(f"\n  {name}:")
    print(f"    {desc[:150]}..." if len(desc) > 150 else f"    {desc}")

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
