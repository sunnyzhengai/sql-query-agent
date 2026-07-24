"""Fabric Notebook: Debug ScriptDom extraction and traversal issues

Run after orchestrator to investigate:
1. The 41 parse failures — what exactly fails and why
2. Empty traversal — why canonical nodes have no edges

Reads from Delta tables, no need to re-run orchestrator.
"""

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

# %% Cell 2: Analyze parse errors
print("=== Parse Errors Analysis ===\n")

errors_df = spark.table("parse_errors")
errors = [row.asDict() for row in errors_df.collect()]

# Categorize errors
scriptdom_no_select = [e for e in errors if "no SELECT" in (e.get("error") or "")]
sqlglot_failures = [e for e in errors if "Failed to parse" in (e.get("error") or "")]
other_errors = [e for e in errors if e not in scriptdom_no_select and e not in sqlglot_failures]

print(f"Total errors: {len(errors)}")
print(f"  ScriptDom found no SELECT: {len(scriptdom_no_select)}")
print(f"  sqlglot parse failures: {len(sqlglot_failures)}")
print(f"  Other: {len(other_errors)}")

# Show ScriptDom no-select procs
if scriptdom_no_select:
    print(f"\n--- ScriptDom No SELECT ({len(scriptdom_no_select)}) ---")
    for e in scriptdom_no_select[:5]:
        print(f"  {e['metric_id']} ({e.get('line_count', '?')} lines)")

# Show sqlglot failures with SQL preview
if sqlglot_failures:
    print(f"\n--- sqlglot Failures ({len(sqlglot_failures)}) ---")
    for e in sqlglot_failures[:5]:
        print(f"\n  {e['metric_id']} ({e.get('line_count', '?')} lines)")
        print(f"  Error: {(e.get('error') or '')[:200]}")

# %% Cell 3: Investigate one sqlglot failure
# Look at what ScriptDom extracted vs what sqlglot choked on
if sqlglot_failures:
    target = sqlglot_failures[0]["metric_id"]
    print(f"Investigating: {target}\n")

    # Get the raw SQL
    raw = spark.sql(f"SELECT sql FROM sql_sources WHERE metric_id = '{target}'").collect()
    if raw:
        raw_sql = raw[0]["sql"]
        print(f"Raw SQL: {len(raw_sql)} chars, {raw_sql.count(chr(10))} lines")

        # Run ScriptDom extraction
        queries = extract_with_scriptdom(raw_sql)
        print(f"ScriptDom extracted: {len(queries)} queries")
        for i, q in enumerate(queries[:3]):
            print(f"\n  Query {i+1} ({len(q)} chars):")
            print(f"  {q[:200]}...")

        # Try parsing each individually with sqlglot
        import sqlglot
        for i, q in enumerate(queries):
            # Replace @variables
            import re
            cleaned = re.sub(r"@(\w+)", r"__param_\1__", q)
            # Strip #temp names
            cleaned = re.sub(r"#(\w+)", r"__temp_\1__", cleaned)
            # Remove comments
            cleaned = re.sub(r"--[^\n]*$", "", cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned)
            try:
                sqlglot.parse_one(cleaned, dialect="tsql")
                print(f"  Query {i+1}: sqlglot OK")
            except Exception as e:
                print(f"  Query {i+1}: sqlglot FAIL — {str(e)[:150]}")
                print(f"    SQL: {cleaned[:150]}...")

# %% Cell 4: Diagnose empty traversal
print("\n=== Traversal Diagnosis ===\n")

nodes_df = spark.table("graph_nodes")
edges_df = spark.table("graph_edges")

# Count by layer
print("Nodes by layer:")
nodes_df.groupBy("layer").count().orderBy("layer").show()

# Count by edge type
print("Edges by type:")
edges_df.groupBy("edge_type").count().orderBy("edge_type").show()

# How many canonical nodes have edges?
canonical_count = nodes_df.filter("layer = 'canonical'").count()
canonical_with_edges = edges_df.filter("edge_type = 'canonical_to_transform'").select("source_id").distinct().count()
print(f"Canonical nodes: {canonical_count}")
print(f"Canonical with edges: {canonical_with_edges}")
print(f"Canonical WITHOUT edges: {canonical_count - canonical_with_edges}")

# %% Cell 5: Check a specific metric's edges
print("\n=== Spot Check ===")

# Find a metric that parsed successfully
successes_df = spark.table("parse_successes")
if successes_df.count() > 0:
    sample = successes_df.limit(5).collect()
    for row in sample:
        mid = row["metric_id"]
        canonical_edges = edges_df.filter(f"source_id = 'canonical:{mid}'").count()
        transform_edges = edges_df.filter(f"source_id LIKE 'transform:{mid}%'").count()
        print(f"  {mid}: {canonical_edges} canonical edges, {transform_edges} transform edges")
else:
    print("  No parse_successes table found")

# %% Cell 6: Check if transform nodes exist
print("\n=== Transform Nodes Check ===")
transform_count = nodes_df.filter("layer = 'transformation'").count()
print(f"Total transformation nodes: {transform_count}")

# Show first 5 transform nodes
print("\nSample transform nodes:")
nodes_df.filter("layer = 'transformation'").select("node_id", "name").show(5, truncate=80)

# Show first 5 edges
print("Sample edges:")
edges_df.show(5, truncate=80)

# %% Cell 7: Debug a specific parse error — see what ScriptDom extracted and what sqlglot rejects
# Change METRIC_ID to the proc that failed
METRIC_ID = "USP_CCHCS_Controlled_Substance_Waste_PBI"

from src.parser.sql_parser import _parse_single_statement, _extract_temp_table_name, _clean_extracted_query

raw_sql = spark.sql(f"SELECT sql FROM sql_sources WHERE metric_id = '{METRIC_ID}'").collect()[0]["sql"]
print(f"=== Debug Parse Error: {METRIC_ID} ===")
print(f"Raw SQL: {len(raw_sql)} chars\n")

# Extract with ScriptDom
queries = extract_with_scriptdom(raw_sql)
print(f"ScriptDom extracted: {len(queries)} queries\n")

# Try parsing each one individually
for i, q in enumerate(queries):
    print(f"--- Query {i+1} ({len(q)} chars) ---")
    print(f"Preview: {q[:150]}...")
    temp_name = _extract_temp_table_name(q)
    if temp_name:
        print(f"  Temp table: #{temp_name}")
    cleaned = _clean_extracted_query(q)
    try:
        result = _parse_single_statement(q, "tsql")
        if result:
            print(f"  OK: {len(result.ctes)} CTEs, {len(result.final_select_tables)} tables")
        else:
            print(f"  SKIPPED (returned None)")
    except Exception as e:
        print(f"  FAILED: {str(e)[:200]}")
        print(f"  Cleaned SQL preview: {cleaned[:300]}")
    print()
