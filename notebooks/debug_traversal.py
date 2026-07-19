"""Fabric Notebook: Debug traversal issues.

Run after orchestrator_v2 to diagnose why traversal returns empty results.
Checks table name matching between parsed SQL and dictionary.

To use: copy cells into your Fabric notebook after running orchestrator_v2.
Requires: builder, sql_sources, dict_tables, parse_sql all in scope from orchestrator_v2.
"""

# %% Cell 1: Check a successfully parsed metric for table name matching
from src.parser.sql_parser import parse_sql

dict_table_names = set(row["TABLE_NAME"] for row in dict_tables)
print(f"Dictionary has {len(dict_table_names)} table names")
print(f"Sample dict names: {sorted(list(dict_table_names))[:10]}")
print()

found_one = False
for source in sql_sources:
    metric_id = source["metric_id"]
    try:
        parsed = parse_sql(source["sql"])
        if parsed.ctes or parsed.final_select_tables:
            print(f"Metric: {metric_id}")
            print(f"  CTEs: {[c.name for c in parsed.ctes]}")
            print(f"  CTE table_refs: {[c.table_refs for c in parsed.ctes[:3]]}")
            print(f"  Final tables (first 10): {parsed.final_select_tables[:10]}")

            # Check matches
            all_parsed_tables = set()
            for c in parsed.ctes:
                all_parsed_tables.update(c.table_refs)
            all_parsed_tables.update(parsed.final_select_tables)

            matched = all_parsed_tables & dict_table_names
            unmatched = all_parsed_tables - dict_table_names

            print(f"  Matched in dict ({len(matched)}): {sorted(list(matched))[:10]}")
            print(f"  NOT in dict ({len(unmatched)}): {sorted(list(unmatched))[:10]}")
            found_one = True
            break
    except Exception:
        continue

if not found_one:
    print("No successfully parsed metrics with tables found!")

# %% Cell 2: Check graph nodes - are technical nodes being created?
from collections import Counter

layer_counts = Counter(n.layer.value for n in builder.nodes.values())
print(f"Graph nodes by layer: {dict(layer_counts)}")

# Sample technical nodes
tech_nodes = [n for n in builder.nodes.values() if n.layer.value == "technical"]
print(f"\nSample technical node names (first 10):")
for n in tech_nodes[:10]:
    print(f"  {n.node_id} -> {n.name}")

# Sample canonical nodes
can_nodes = [n for n in builder.nodes.values() if n.layer.value == "canonical"]
print(f"\nSample canonical node names (first 10):")
for n in can_nodes[:10]:
    print(f"  {n.node_id} -> {n.name}")

# %% Cell 3: Check edges - are any edges being created?
from collections import Counter

edge_counts = Counter(e.edge_type.value for e in builder.edges)
print(f"Edges by type: {dict(edge_counts)}")

# Sample edges
print(f"\nSample edges (first 10):")
for e in builder.edges[:10]:
    print(f"  {e.source_id} -> {e.target_id} ({e.edge_type.value})")

# %% Cell 4: Check a specific metric's edges
test_metric = sql_sources[0]["metric_id"]
print(f"Checking edges for metric: {test_metric}")

canonical_id = f"canonical:{test_metric}"
metric_edges = [e for e in builder.edges if test_metric in e.source_id or test_metric in e.target_id]
print(f"Edges involving this metric: {len(metric_edges)}")
for e in metric_edges[:20]:
    print(f"  {e.source_id} -> {e.target_id} ({e.edge_type.value})")

# Check if transform nodes exist for this metric
transform_nodes = [n for n in builder.nodes.values()
                   if n.layer.value == "transformation" and test_metric in n.node_id]
print(f"\nTransform nodes for this metric: {len(transform_nodes)}")
for n in transform_nodes:
    print(f"  {n.node_id}")

# %% Cell 5: Quick stats - how many metrics have any edges?
metrics_with_edges = set()
for e in builder.edges:
    if e.edge_type.value == "canonical_to_transform":
        metric_id = e.source_id.replace("canonical:", "")
        metrics_with_edges.add(metric_id)

total_metrics = len([n for n in builder.nodes.values() if n.layer.value == "canonical"])
print(f"Total canonical metrics: {total_metrics}")
print(f"Metrics with edges to transforms: {len(metrics_with_edges)}")
print(f"Metrics with NO edges: {total_metrics - len(metrics_with_edges)}")
