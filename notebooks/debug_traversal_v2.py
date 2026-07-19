"""Fabric Notebook: Debug traversal v2.

Quick tests to find metrics that DO have edges and verify traversal works.
Run after orchestrator_v2 — uses builder, traverser, sql_sources in scope.
"""

# %% Cell 1: Find a metric WITH edges and test traversal
from src.graph.traversal import GraphTraverser

traverser = GraphTraverser(builder.nodes, builder.edges)

print("=== First 5 metrics WITH edges ===")
found = 0
for e in builder.edges:
    if e.edge_type.value == "canonical_to_transform":
        metric_id = e.source_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)
        if subgraph:
            canonical = subgraph["canonical"]
            tables = [t.name for t in subgraph["technical"] if t.properties.get("column") is None]
            print(f"\n{canonical.name} ({metric_id})")
            print(f"  Steward: {canonical.properties.get('steward', 'N/A')}")
            print(f"  Transforms: {len(subgraph['transformations'])}")
            print(f"  Tables ({len(tables)}): {tables[:10]}{'...' if len(tables) > 10 else ''}")
            found += 1
            if found >= 5:
                break

# %% Cell 2: Find metrics WITHOUT edges — why?
print("=== First 5 metrics WITHOUT edges ===")
metrics_with_edges = set()
for e in builder.edges:
    if e.edge_type.value == "canonical_to_transform":
        metrics_with_edges.add(e.source_id.replace("canonical:", ""))

found = 0
for source in sql_sources:
    mid = source["metric_id"]
    if mid not in metrics_with_edges:
        print(f"\n{mid} ({source['name']})")
        # Try parsing to see what happened
        try:
            from src.parser.sql_parser import parse_sql
            parsed = parse_sql(source["sql"])
            print(f"  Parsed OK: {len(parsed.ctes)} CTEs, {len(parsed.final_select_tables)} final tables")
            print(f"  final_select_cte_refs: {parsed.final_select_cte_refs}")
            if parsed.final_select_tables:
                print(f"  Final tables: {parsed.final_select_tables[:5]}")
            if not parsed.ctes and not parsed.final_select_tables:
                print(f"  -> No CTEs and no tables extracted (parser returned empty)")
        except Exception as ex:
            print(f"  Parse error: {str(ex)[:100]}")
        found += 1
        if found >= 5:
            break

# %% Cell 3: Summary stats
print("\n=== Summary ===")
total = len(sql_sources)
with_edges = len(metrics_with_edges)
parse_ok = sum(1 for s in sql_sources if s["metric_id"] in
    {n.node_id.split(":")[1].split(":")[0] for n in builder.nodes.values()
     if n.layer.value == "transformation"})

print(f"Total SQL sources: {total}")
print(f"Metrics with edges (traversable): {with_edges} ({100*with_edges//total}%)")
print(f"Metrics without edges: {total - with_edges}")
print(f"Unique metrics with transform nodes: {len(set(n.properties.get('metric_id','') for n in builder.nodes.values() if n.layer.value == 'transformation'))}")
