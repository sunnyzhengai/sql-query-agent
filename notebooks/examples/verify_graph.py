"""Fabric Notebook: Verify graph has traversable metrics

Quick check after orchestrator run to confirm the graph works.
"""

# %% Cell 1: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.models import GraphNode, GraphEdge, NodeLayer, EdgeType

# %% Cell 2: Load graph
nodes_df = spark.table("graph_nodes")
edges_df = spark.table("graph_edges")

builder = GraphBuilder()
for row in nodes_df.collect():
    r = row.asDict()
    props = json.loads(r.get("properties", "{}"))
    builder.nodes[r["node_id"]] = GraphNode(
        node_id=r["node_id"], layer=NodeLayer(r["layer"]),
        name=r["name"], description=r.get("description", ""), properties=props,
    )

for row in edges_df.collect():
    r = row.asDict()
    props = json.loads(r.get("properties", "{}"))
    builder.edges.append(GraphEdge(
        source_id=r["source_id"], target_id=r["target_id"],
        edge_type=EdgeType(r["edge_type"]), properties=props,
    ))

traverser = GraphTraverser(builder.nodes, builder.edges)

from collections import Counter
layer_counts = Counter(n.layer.value for n in builder.nodes.values())
print(f"Graph: {len(builder.nodes)} nodes, {len(builder.edges)} edges")
print(f"  Canonical: {layer_counts.get('canonical', 0)}")
print(f"  Transformation: {layer_counts.get('transformation', 0)}")
print(f"  Technical: {layer_counts.get('technical', 0)}")

# %% Cell 3: Find first 5 traversable metrics
print("\n=== First 5 traversable metrics ===")
found = 0
for e in builder.edges:
    if e.edge_type.value == "canonical_to_transform":
        metric_id = e.source_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)
        if subgraph:
            canonical = subgraph["canonical"]
            tables = [t.name for t in subgraph["technical"] if t.properties.get("column") is None]
            print(f"\n  {canonical.name}")
            print(f"    Transforms: {len(subgraph['transformations'])}")
            print(f"    Tables: {len(tables)}")
            found += 1
            if found >= 5:
                break

# %% Cell 4: Overall stats
metrics_with_edges = set()
for e in builder.edges:
    if e.edge_type.value == "canonical_to_transform":
        metrics_with_edges.add(e.source_id.replace("canonical:", ""))

total_canonical = sum(1 for n in builder.nodes.values() if n.layer == NodeLayer.CANONICAL)
print(f"\n=== Coverage ===")
print(f"Total canonical: {total_canonical}")
print(f"Traversable (have edges): {len(metrics_with_edges)}")
print(f"No edges: {total_canonical - len(metrics_with_edges)}")

# %% Cell 5: Check parse results tables
print("\n=== Parse Results ===")
try:
    success_count = spark.table("parse_successes").count()
    error_count = spark.table("parse_errors").count()
    print(f"Successes: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Success rate: {100 * success_count // (success_count + error_count)}%")

    print("\nTop 5 errors by proc size:")
    spark.table("parse_errors").orderBy("line_count", ascending=False).show(5, truncate=80)
except Exception as e:
    print(f"Parse results tables not found: {e}")
