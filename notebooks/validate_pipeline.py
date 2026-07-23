"""Fabric Notebook: Validate every step of the pipeline

Measures success at each stage and saves results to a Delta table.
Run after orchestrator to verify end-to-end pipeline health.

Steps validated:
1. SQL source loaded? (exists in sql_sources)
2. ScriptDom extraction? (queries found?)
3. sqlglot parsing? (CTEs/tables extracted?)
4. Graph nodes created? (canonical + transform nodes exist?)
5. Graph edges created? (canonical_to_transform edges?)
6. Traversal works? (can reach technical tables?)
"""

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from pyspark.sql.types import StringType, StructField, StructType, IntegerType, BooleanType

# %% Cell 2: Validate every metric end-to-end
print("=== Pipeline Validation ===\n")

# Load all data from Delta tables
sql_sources = [r.asDict() for r in spark.table("sql_sources").selectExpr(
    "metric_id", "name", "cast(null as string) as steward"
).collect()]

nodes = {}
for r in spark.table("graph_nodes").collect():
    rd = r.asDict()
    nodes[rd["node_id"]] = rd

edges_by_source = {}
for r in spark.table("graph_edges").collect():
    rd = r.asDict()
    edges_by_source.setdefault(rd["source_id"], []).append(rd)

# Check parse results
parse_ok_set = set()
try:
    for r in spark.table("parse_successes").collect():
        parse_ok_set.add(r.asDict()["metric_id"])
except Exception:
    pass

parse_error_set = set()
try:
    for r in spark.table("parse_errors").collect():
        parse_error_set.add(r.asDict()["metric_id"])
except Exception:
    pass

print(f"Loaded: {len(sql_sources)} sources, {len(nodes)} nodes, {sum(len(v) for v in edges_by_source.values())} edges")
print(f"Parse successes: {len(parse_ok_set)}, Parse errors: {len(parse_error_set)}")

# Validate each metric
results = []

for source in sql_sources:
    mid = source["metric_id"]

    # Step 1: Source loaded
    step1_loaded = True  # if we're iterating it, it's loaded

    # Step 2: Parse succeeded
    step2_parsed = mid in parse_ok_set

    # Step 3: Canonical node exists
    canonical_id = f"canonical:{mid}"
    step3_canonical = canonical_id in nodes

    # Step 4: Transform nodes exist
    transform_nodes = [nid for nid in nodes if nid.startswith(f"transform:{mid}:")]
    step4_transforms = len(transform_nodes) > 0

    # Step 5: Canonical-to-transform edges exist
    c2t_edges = edges_by_source.get(canonical_id, [])
    c2t_count = len([e for e in c2t_edges if e["edge_type"] == "canonical_to_transform"])
    step5_edges = c2t_count > 0

    # Step 6: Can reach technical nodes (traverse one level)
    tech_reachable = 0
    if step5_edges:
        for c2t in c2t_edges:
            target = c2t["target_id"]
            # Check if transform has edges to technical
            t2tech = edges_by_source.get(target, [])
            tech_reachable += len([e for e in t2tech if e["edge_type"] == "transform_to_technical"])
    step6_traversal = tech_reachable > 0

    results.append({
        "metric_id": mid,
        "step1_loaded": step1_loaded,
        "step2_parsed": step2_parsed,
        "step3_canonical": step3_canonical,
        "step4_transforms": step4_transforms,
        "step5_edges": step5_edges,
        "step6_traversal": step6_traversal,
        "transform_count": len(transform_nodes),
        "edge_count": c2t_count,
        "tech_reachable": tech_reachable,
    })

# %% Cell 3: Summary
total = len(results)
s1 = sum(1 for r in results if r["step1_loaded"])
s2 = sum(1 for r in results if r["step2_parsed"])
s3 = sum(1 for r in results if r["step3_canonical"])
s4 = sum(1 for r in results if r["step4_transforms"])
s5 = sum(1 for r in results if r["step5_edges"])
s6 = sum(1 for r in results if r["step6_traversal"])

print(f"\n=== Pipeline Health ===")
print(f"Step 1 — Source loaded:      {s1}/{total} ({100*s1//total}%)")
print(f"Step 2 — Parse succeeded:    {s2}/{total} ({100*s2//total}%)")
print(f"Step 3 — Canonical node:     {s3}/{total} ({100*s3//total}%)")
print(f"Step 4 — Transform nodes:    {s4}/{total} ({100*s4//total}%)")
print(f"Step 5 — Edges created:      {s5}/{total} ({100*s5//total}%)")
print(f"Step 6 — Traversal works:    {s6}/{total} ({100*s6//total}%)")

# Where do metrics drop off?
print(f"\n=== Drop-off Analysis ===")
print(f"Parsed but no transforms:    {s2 - s4}")
print(f"Transforms but no edges:     {s4 - s5}")
print(f"Edges but no traversal:      {s5 - s6}")

# %% Cell 4: Show metrics that fail at each step
print("\n=== Parsed OK but NO Transform Nodes ===")
for r in results:
    if r["step2_parsed"] and not r["step4_transforms"]:
        print(f"  {r['metric_id']}")

print("\n=== Transforms exist but NO Edges ===")
for r in results:
    if r["step4_transforms"] and not r["step5_edges"]:
        print(f"  {r['metric_id']} ({r['transform_count']} transforms)")

print("\n=== Edges exist but NO Traversal to Technical ===")
for r in results:
    if r["step5_edges"] and not r["step6_traversal"]:
        print(f"  {r['metric_id']} ({r['edge_count']} edges)")

# %% Cell 5: Save validation results to Delta table
schema = StructType([
    StructField("metric_id", StringType(), False),
    StructField("step1_loaded", BooleanType(), True),
    StructField("step2_parsed", BooleanType(), True),
    StructField("step3_canonical", BooleanType(), True),
    StructField("step4_transforms", BooleanType(), True),
    StructField("step5_edges", BooleanType(), True),
    StructField("step6_traversal", BooleanType(), True),
    StructField("transform_count", IntegerType(), True),
    StructField("edge_count", IntegerType(), True),
    StructField("tech_reachable", IntegerType(), True),
])

rows = [(r["metric_id"], r["step1_loaded"], r["step2_parsed"], r["step3_canonical"],
         r["step4_transforms"], r["step5_edges"], r["step6_traversal"],
         r["transform_count"], r["edge_count"], r["tech_reachable"])
        for r in results]

validation_df = spark.createDataFrame(rows, schema=schema)
validation_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("pipeline_validation")
print(f"\nSaved {len(rows)} validation results to pipeline_validation table")

# %% Cell 6: Query specific failures
# After running, you can query:
#
# Metrics that parsed but have no edges:
#   SELECT * FROM pipeline_validation WHERE step2_parsed = true AND step5_edges = false
#
# Metrics with edges but no traversal:
#   SELECT * FROM pipeline_validation WHERE step5_edges = true AND step6_traversal = false
#
# Full pipeline success rate:
#   SELECT step6_traversal, COUNT(*) FROM pipeline_validation GROUP BY step6_traversal
print("\nQuery 'pipeline_validation' table for detailed analysis.")
