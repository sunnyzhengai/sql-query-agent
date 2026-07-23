"""Fabric Notebook: Debug parse errors and edge wiring

Run after orchestrator to check:
1. What are the 39 parse errors?
2. Are edges being created at all?
3. Why is traversal empty?

Reads from Delta tables + builder object in memory.
"""

# %% Cell 1: Show all parse errors
spark.sql("""
    SELECT metric_id, error
    FROM parse_errors
    ORDER BY metric_id
""").show(50, truncate=150)

# %% Cell 2: Check edge counts
c2t = len([e for e in builder.edges if e.edge_type.value == "canonical_to_transform"])
t2tech = len([e for e in builder.edges if e.edge_type.value == "transform_to_technical"])
t2t = len([e for e in builder.edges if e.edge_type.value == "transform_to_transform"])

print(f"canonical_to_transform: {c2t}")
print(f"transform_to_technical: {t2tech}")
print(f"transform_to_transform: {t2t}")
print(f"Total edges: {len(builder.edges)}")

# %% Cell 3: Check if ANY canonical node has edges
has_edges = set()
for e in builder.edges:
    if e.edge_type.value == "canonical_to_transform":
        has_edges.add(e.source_id)

from collections import Counter
layer_counts = Counter(n.layer.value for n in builder.nodes.values())

print(f"\nCanonical nodes: {layer_counts.get('canonical', 0)}")
print(f"Canonical WITH edges: {len(has_edges)}")
print(f"Transform nodes: {layer_counts.get('transformation', 0)}")
print(f"Technical nodes: {layer_counts.get('technical', 0)}")

# %% Cell 4: Sample a parsed metric and check its edges
# Find one that should have edges
for source in sql_sources[:20]:
    mid = source["metric_id"]
    canon_id = f"canonical:{mid}"
    edges_for = [e for e in builder.edges if mid in e.source_id or mid in e.target_id]
    if edges_for:
        print(f"\n{mid}: {len(edges_for)} edges")
        for e in edges_for[:5]:
            print(f"  {e.source_id} -> {e.target_id} ({e.edge_type.value})")
        break
else:
    print("No metrics with edges found in first 20!")

    # Check what build_from_parsed_sql actually produced
    print("\nChecking last parsed result...")
    if scriptdom_available:
        test_sql = sql_sources[0]["sql"]
        test_queries = extract_with_scriptdom(test_sql)
        print(f"ScriptDom extracted {len(test_queries)} queries")
        if test_queries:
            print(f"First query: {test_queries[0][:100]}...")

            # Try parsing directly
            from src.parser.sql_parser import _parse_single_statement
            result = _parse_single_statement(test_queries[0], "tsql")
            if result:
                print(f"Parsed OK: {len(result.ctes)} CTEs, {len(result.final_select_tables)} tables")
                print(f"Tables: {result.final_select_tables[:5]}")
            else:
                print("Parse returned None!")

# %% Cell 5: Check if the issue is in build_from_parsed_sql
# Manually build one metric and check
test_source = sql_sources[0]
mid = test_source["metric_id"]
test_sql = test_source["sql"]

print(f"Testing: {mid}")

if scriptdom_available:
    queries = extract_with_scriptdom(test_sql)
    print(f"Extracted {len(queries)} queries")

    from src.parser.sql_parser import _parse_single_statement, _extract_temp_table_name, ParsedSQL, CTEInfo

    all_ctes = []
    all_final_tables = []
    all_final_cte_refs = []
    temp_table_names = set()
    parsed_count = 0

    for qi, q in enumerate(queries):
        temp_name = _extract_temp_table_name(q)
        if temp_name:
            temp_table_names.add(temp_name)
            print(f"  Query {qi+1}: SELECT INTO #{temp_name}")

        result = _parse_single_statement(q, "tsql")
        if result:
            parsed_count += 1
            print(f"  Query {qi+1}: {len(result.ctes)} CTEs, {len(result.final_select_tables)} tables")
        else:
            print(f"  Query {qi+1}: PARSE FAILED — {q[:60]}...")

    print(f"\nParsed {parsed_count}/{len(queries)} queries")
    print(f"Temp tables: {temp_table_names}")
    print(f"All CTEs: {len(all_ctes)}")
    print(f"All final tables: {all_final_tables[:10]}")
