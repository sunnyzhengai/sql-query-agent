"""Fabric Notebook: Validate Pipeline and Build Summary

Reads from: all Delta tables (sql_sources, parse_*, graph_*, metric_logic)
Writes to:  pipeline_validation, build_summary (Delta tables)

Run 02-04 at least once before this.
Validates every step of the pipeline per metric and saves a summary.
"""

# %% Cell 0: Setup (run once per session)
%pip install pydantic pyyaml

import json
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.schemas import to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# %% Cell 1: Load all data
sql_sources = [r.asDict() for r in spark.table(config.lakehouse.sql_sources).selectExpr(
    "metric_id", "name", "cast(null as string) as steward"
).collect()]

nodes = {}
for r in spark.table(config.lakehouse.graph_nodes).collect():
    rd = r.asDict()
    nodes[rd["node_id"]] = rd

edges_by_source = {}
for r in spark.table(config.lakehouse.graph_edges).collect():
    rd = r.asDict()
    edges_by_source.setdefault(rd["source_id"], []).append(rd)

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

# %% Cell 2: Validate each metric
from pyspark.sql.types import StringType, StructField, StructType, IntegerType, BooleanType

results = []
for source in sql_sources:
    mid = source["metric_id"]

    step1_loaded = True
    step2_parsed = mid in parse_ok_set

    canonical_id = f"canonical:{mid}"
    step3_canonical = canonical_id in nodes

    transform_nodes = [nid for nid in nodes if nid.startswith(f"transform:{mid}:")]
    step4_transforms = len(transform_nodes) > 0

    c2t_edges = edges_by_source.get(canonical_id, [])
    c2t_count = len([e for e in c2t_edges if e["edge_type"] == "canonical_to_transform"])
    step5_edges = c2t_count > 0

    tech_reachable = 0
    if step5_edges:
        for c2t in c2t_edges:
            target = c2t["target_id"]
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
print(f"Step 1 — Source loaded:      {s1}/{total} ({100*s1//max(total,1)}%)")
print(f"Step 2 — Parse succeeded:    {s2}/{total} ({100*s2//max(total,1)}%)")
print(f"Step 3 — Canonical node:     {s3}/{total} ({100*s3//max(total,1)}%)")
print(f"Step 4 — Transform nodes:    {s4}/{total} ({100*s4//max(total,1)}%)")
print(f"Step 5 — Edges created:      {s5}/{total} ({100*s5//max(total,1)}%)")
print(f"Step 6 — Traversal works:    {s6}/{total} ({100*s6//max(total,1)}%)")

print(f"\n=== Drop-off Analysis ===")
print(f"Parsed but no transforms:    {s2 - s4}")
print(f"Transforms but no edges:     {s4 - s5}")
print(f"Edges but no traversal:      {s5 - s6}")

# %% Cell 4: Show failures at each step
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

# %% Cell 5: Save validation results
from src.schemas import PIPELINE_VALIDATION, to_spark_schema

schema = to_spark_schema(PIPELINE_VALIDATION)
rows = [(r["metric_id"], r["step1_loaded"], r["step2_parsed"], r["step3_canonical"],
         r["step4_transforms"], r["step5_edges"], r["step6_traversal"],
         r["transform_count"], r["edge_count"], r["tech_reachable"])
        for r in results]

validation_df = spark.createDataFrame(rows, schema=schema)
validation_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("pipeline_validation")
print(f"\nSaved {len(rows)} validation results to pipeline_validation table")

# %% Cell 6: Build summary (append-only history)
from collections import Counter
from datetime import datetime, timezone
from src.schemas import BUILD_SUMMARY

now = datetime.now(timezone.utc).isoformat()
summary_rows = [
    (now, "total_sources", str(total), ""),
    (now, "parse_successes", str(s2), ""),
    (now, "parse_errors", str(len(parse_error_set)), ""),
    (now, "canonical_nodes", str(s3), ""),
    (now, "with_transforms", str(s4), ""),
    (now, "with_edges", str(s5), ""),
    (now, "with_traversal", str(s6), ""),
    (now, "total_nodes", str(len(nodes)), ""),
    (now, "total_edges", str(sum(len(v) for v in edges_by_source.values())), ""),
]

summary_df = spark.createDataFrame(summary_rows, schema=to_spark_schema(BUILD_SUMMARY))
try:
    summary_df.write.format("delta").mode("append").saveAsTable("build_summary")
except Exception:
    summary_df.write.format("delta").mode("overwrite").saveAsTable("build_summary")

print(f"Saved {len(summary_rows)} summary records to build_summary")
