"""Fabric Notebook: Publish Descriptions to Collibra

Reads from: graph_nodes, graph_edges (Delta tables)
Writes to:  Collibra Dev (REST API)

Wires together:
1. Graph traversal → generates descriptions from source tables + transform steps
2. Lineage matching → maps _PBI procs/views to Collibra PBI report assets
3. Collibra adapter → updates Description attribute on matched reports

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

# %% Cell 2: Generate descriptions from graph
from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.adapters.metadata_generator import generate_metric_records

# Reconstruct builder from loaded data
builder = GraphBuilder()
builder.nodes = nodes
builder.edges = edges

records = generate_metric_records(builder)
print(f"Generated {len(records)} metric records with descriptions")

# Show a sample
for r in records[:3]:
    print(f"\n  {r.name}:")
    print(f"    {r.description[:120]}..." if len(r.description) > 120 else f"    {r.description}")

# %% Cell 3: Connect to Collibra and match procs/views to PBI reports
from src.adapters.collibra import CollibraAdapter, CollibraConfig
from src.adapters.collibra_lineage import CollibraClient
from src.adapters.collibra_lineage_match import CollibraLineageMatcher, extract_match_key

collibra_cfg = config.adapters.collibra

# Adapter for writing descriptions
adapter = CollibraAdapter(CollibraConfig(
    base_url=collibra_cfg.base_url,
    username=collibra_cfg.username,
    password=collibra_cfg.password,
    api_key=collibra_cfg.api_key,
    domain_id=collibra_cfg.domain_id,
    community_id=collibra_cfg.community_id,
    asset_type_id=collibra_cfg.asset_type_id,
))

# Client for lineage matching (needs base URL without /rest/2.0)
base = collibra_cfg.base_url.replace("/rest/2.0", "")
client = CollibraClient(base, collibra_cfg.username, collibra_cfg.password)

print("Testing connection...")
if adapter.test_connection():
    print("Connected to Collibra!")
else:
    print("Connection failed. Check org_config.yaml")

# %% Cell 4: Match metrics to Collibra PBI reports
# Build the list of _PBI objects from canonical node names
objects = []
for r in records:
    key = extract_match_key(r.name)
    if key is not None:
        objects.append({
            "object_name": r.name,
            "object_type": "SQL_STORED_PROCEDURE",
        })

print(f"Found {len(objects)} _PBI-suffixed metrics out of {len(records)} total")

matcher = CollibraLineageMatcher(client, min_score=0.5)
match_result = matcher.match_objects(objects)
print(f"\n{match_result}")

# %% Cell 5: Review matches before publishing
print(f"{'='*80}")
print(f"MATCHED — will update descriptions ({len(match_result.matched)})")
print(f"{'='*80}")

# Build lookup: metric name → description
desc_lookup = {r.name: r.description for r in records}

for m in match_result.matched:
    desc = desc_lookup.get(m.object_name, "")
    print(f"\n  Proc/View: {m.object_name}")
    print(f"  Collibra:  {m.report_name}")
    print(f"  Score:     {m.score:.2f}")
    print(f"  Description: {desc[:100]}..." if len(desc) > 100 else f"  Description: {desc}")

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
    # Filter to specific reports if set
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
print(f"  Total metrics:     {len(records)}")
print(f"  _PBI suffixed:     {len(objects)}")
print(f"  Matched to report: {len(match_result.matched)}")
print(f"  Published:         {succeeded}")
print(f"  Failed:            {failed}")
print(f"  Skipped (no desc): {skipped}")
print(f"  Unmatched:         {len(match_result.unmatched_objects)}")
