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

"""Fabric Notebook: Validate Pipeline and Build Summary

Reads from: all Delta tables (input_sql_sources, ops_parse_*, graph_*)
Writes to:  ops_pipeline_validation, ops_build_summary (Delta)

Run 200-400 at least once before this.
"""

# %% Cell 0: Setup
# Prerequisites: Attach 'sql-logic-env' Fabric Environment. No %pip install.
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

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.24"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "500_validate")


from src.config import load_config
from src.schemas import BUILD_SUMMARY, PIPELINE_VALIDATION, to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load all data from Delta
# Registry-driven precondition gate: every required input (sources, dict,
# graph, parse outcomes) must exist before validation computes anything —
# absence means an upstream notebook never ran, and the failure names it.
from src.steps.gates import precondition_gate

precondition_gate("500_validate", table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count())

sql_source_ids = [r.asDict()["metric_id"] for r in spark.table(config.lakehouse.sql_sources).collect()]

nodes = {}
for r in spark.table(config.lakehouse.graph_nodes).collect():
    rd = r.asDict()
    nodes[rd["node_id"]] = rd

edges_by_source = {}
for r in spark.table(config.lakehouse.graph_edges).collect():
    rd = r.asDict()
    edges_by_source.setdefault(rd["source_id"], []).append(rd)

parse_ok_ids = {r["metric_id"] for r in spark.table("ops_parse_successes").collect()}
parse_error_ids = {r["metric_id"] for r in spark.table("ops_parse_errors").collect()}

print(f"Loaded: {len(sql_source_ids)} sources, {len(nodes)} nodes, "
      f"{sum(len(v) for v in edges_by_source.values())} edges")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Validate (all logic in src/)
from src.governance.validation import summarize_validation, validate_pipeline_per_metric

results = validate_pipeline_per_metric(sql_source_ids, parse_ok_ids, nodes, edges_by_source)
summary = summarize_validation(results)

total = summary["total"]
print("\n=== Pipeline Health ===")
for step_key in ["s1_loaded", "s2_parsed", "s3_canonical", "s4_transforms", "s5_edges", "s6_traversal"]:
    label = step_key.replace("s", "Step ", 1).replace("_", " — ", 1)
    count = summary[step_key]
    print(f"  {label}: {count}/{total} ({100*count//max(total,1)}%)")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Show failures
print("\n=== Parsed but NO Transforms ===")
for r in results:
    if r["step2_parsed"] and not r["step4_transforms"]:
        print(f"  {r['metric_id']}")

print("\n=== Transforms but NO Edges ===")
for r in results:
    if r["step4_transforms"] and not r["step5_edges"]:
        print(f"  {r['metric_id']}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 4: Save validation + build summary to Delta
from datetime import datetime, timezone

rows = [(r["metric_id"], r["step1_loaded"], r["step2_parsed"], r["step3_canonical"],
         r["step4_transforms"], r["step5_edges"], r["step6_traversal"],
         r["transform_count"], r["edge_count"], r["tech_reachable"])
        for r in results]

spark.createDataFrame(rows, schema=to_spark_schema(PIPELINE_VALIDATION)) \
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ops_pipeline_validation")
print(f"Saved {len(rows)} validation results")

now = datetime.now(timezone.utc).isoformat()
summary_rows = [
    (now, "total_sources", str(total), ""),
    (now, "parse_successes", str(summary["s2_parsed"]), ""),
    (now, "parse_errors", str(len(parse_error_ids)), ""),
    (now, "canonical_nodes", str(summary["s3_canonical"]), ""),
    (now, "with_transforms", str(summary["s4_transforms"]), ""),
    (now, "with_traversal", str(summary["s6_traversal"]), ""),
    (now, "total_nodes", str(len(nodes)), ""),
    (now, "total_edges", str(sum(len(v) for v in edges_by_source.values())), ""),
]
summary_df = spark.createDataFrame(summary_rows, schema=to_spark_schema(BUILD_SUMMARY))
# ops_build_summary is append-only history. Create it explicitly on first
# run; a failing append must RAISE — never silently become an overwrite
# that destroys every prior run's telemetry (audit 2026-08-15).
if spark.catalog.tableExists("ops_build_summary"):
    summary_df.write.format("delta").mode("append").saveAsTable("ops_build_summary")
    print("Appended build summary")
else:
    summary_df.write.format("delta").saveAsTable("ops_build_summary")
    print("Created ops_build_summary with first build summary")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 5: Deployment readiness gate
s2 = summary["s2_parsed"]
s4 = summary["s4_transforms"]
s6 = summary["s6_traversal"]

# Coverage logic lives in src/steps/readiness.py (pure, tested). No
# try/except here: if the dictionary table can't be read, the run FAILS —
# the gate-integrity contract in readiness_gate blocks any run where a
# required check is missing, so this can never silently vanish again.
from src.steps.readiness import dictionary_coverage_threshold, tech_table_names

table_col = config.dictionary.table_name_col
dict_table_names = {
    r[table_col] for r in spark.table(config.lakehouse.dict_tables).select(table_col).collect()
}

THRESHOLDS = {
    "parse_rate": (s2 / max(total, 1), 0.90, True),
    "calculation_logic": (s4 / max(total, 1), 0.80, True),
    "traversal_coverage": (s6 / max(total, 1), 0.70, False),
    "dictionary_coverage": dictionary_coverage_threshold(
        dict_table_names, tech_table_names(nodes.values())),
}

# Schema-ambiguity gate (ADR 0016): the dictionary matches tables by bare
# name (it has no schema column). If the SQL references the same bare name
# in multiple schemas, description attachment is ambiguous — block unless
# the admin acknowledged it via dictionary.accept_schema_ambiguity.
from src.dictionary import find_cross_schema_collisions

schema_table_pairs = []
for nid, node in nodes.items():
    if nid.startswith("tech:"):
        raw_props = node.get("properties", {})
        props = json.loads(raw_props) if isinstance(raw_props, str) else raw_props
        if props.get("table") and not props.get("column"):
            schema_table_pairs.append((props.get("schema") or "dbo", props["table"]))
schema_ambiguities = find_cross_schema_collisions(schema_table_pairs)
ambiguity_acknowledged = bool(getattr(config.dictionary, "accept_schema_ambiguity", False))

# Data-contract invariants: enforce unique / allowed_values / reference
# rules declared in TABLE_REGISTRY against the actual Delta tables.
from src.invariants import check_all_invariants


def _fetch(table_name, columns):
    return [r.asDict() for r in spark.table(table_name).select(*columns).collect()]

def _table_exists(table_name):
    return spark.catalog.tableExists(table_name)

invariant_violations = check_all_invariants(_fetch, _table_exists)

# The readiness decision is a pure function (src/steps/readiness.py) —
# identical logic wherever the pipeline runs, testable in CI.
from src.steps.readiness import readiness_gate

gate = readiness_gate(THRESHOLDS, invariant_violations, schema_ambiguities, ambiguity_acknowledged)

print(f"\n{'=' * 60}")
print("DEPLOYMENT READINESS GATE")
print(f"{'=' * 60}")
for line in gate.lines:
    print(f"  {line}")

if gate.blocked:
    print("\n  >>> DEPLOYMENT BLOCKED <<<")
else:
    print("\n  >>> DEPLOYMENT READY <<<")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 6: Freshness / staleness (Trust family — WARNING, never a gate)
from datetime import datetime, timezone

from src.schemas import FALLOUT, to_spark_schema
from src.steps.readiness import stale_metrics

if spark.catalog.tableExists("output_metric_logic"):
    _metric_rows = [r.asDict() for r in
                    spark.table("output_metric_logic")
                    .select("metric_id", "source_extracted_at").collect()]
    _now = datetime.now(timezone.utc).isoformat()
    _threshold = config.freshness.stale_after_days
    stale, unknown = stale_metrics(_metric_rows, _now, _threshold)
    print(f"\nFreshness: threshold {_threshold}d — {len(stale)} stale, "
          f"{unknown} unknown age (file-drop route), "
          f"{len(_metric_rows) - len(stale) - unknown} fresh")
    for metric_id, ts, age in stale[:10]:
        print(f"  [!] {metric_id}: source extracted {age}d ago ({ts})")
    if stale:
        _rows = [(_now, "500_freshness", m, "stale_source",
                  f"source extraction {age}d old (threshold {_threshold}d) — "
                  f"re-run the 00c extraction route",
                  "contract:output_metric_logic")
                 for m, ts, age in stale]
        spark.createDataFrame(_rows, schema=to_spark_schema(FALLOUT)) \
            .write.format("delta").mode("append").saveAsTable("ops_fallout")
        print(f"  -> {len(_rows)} stale_source rows appended to ops_fallout "
              "(health funnel; NOT a deployment gate)")
else:
    print("\nFreshness: output_metric_logic absent — run 400 first")

print("\nNext (optional path): 600/610 descriptions -> 700 index -> "
      "800 export -> 900-series publishers.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 7: The pipeline funnel — per stage: in -> out, and WHY it fell
from src.governance.funnel import (
    FunnelStage,
    funnel_lines,
    funnel_rows,
    reasons_from_fallout,
)
from src.schemas import FUNNEL

_fallout_rows = []
if spark.catalog.tableExists("ops_fallout"):
    _fallout_rows = [r.asDict() for r in spark.table("ops_fallout").collect()]

_stages = []

# 02: corpus -> parsed (error reasons from ops_parse_errors)
_err_reasons = {}
for r in spark.table("ops_parse_errors").collect():
    code = r["error_category"] or "parse_error"
    _err_reasons[code] = _err_reasons.get(code, 0) + 1
_stages.append(FunnelStage(
    "200_parse", len(sql_source_ids), len(parse_ok_ids), _err_reasons,
    derived_from="input_sql_sources -> ops_parse_successes / ops_parse_errors"))

# 03: parsed -> canonical nodes in the graph
_canonical = sum(1 for nid in nodes if nid.startswith("canonical:"))
_stages.append(FunnelStage(
    "300_build_graph", len(parse_ok_ids), _canonical,
    derived_from="ops_parse_successes -> graph_nodes(canonical)"))

# 04: canonical -> cards with calculation logic
if spark.catalog.tableExists("output_metric_logic"):
    _card_rows = [r.asDict() for r in
                  spark.table("output_metric_logic")
                  .select("metric_id", "calculation_logic").collect()]
    _with_logic = sum(1 for r in _card_rows if r["calculation_logic"])
    _stages.append(FunnelStage(
        "400_build_metric_logic", _canonical, _with_logic,
        derived_from="graph_nodes(canonical) -> output_metric_logic"
                     "(calculation_logic)"))

# 12: collected partition files -> report source rows (fallout-backed)
if spark.catalog.tableExists("input_report_sources"):
    _src_count = spark.table("input_report_sources").count()
    _p_reasons = reasons_from_fallout(_fallout_rows, "060_partition_parse")
    _stages.append(FunnelStage(
        "060_ingest_semantic_models", _src_count + sum(_p_reasons.values()),
        _src_count, _p_reasons,
        derived_from="input_report_sources + ops_fallout"
                     "(060_partition_parse, latest run)"))

# 07b: planned descriptions -> ok (rejected rows are the reasons)
if spark.catalog.tableExists("ops_agent_descriptions"):
    _desc = [r.asDict() for r in
             spark.table("ops_agent_descriptions").select("status").collect()]
    _ok = sum(1 for r in _desc if r["status"] == "ok")
    _rej = len(_desc) - _ok
    _stages.append(FunnelStage(
        "610_generate_agent_descriptions", len(_desc), _ok,
        {"rejected_by_agent": _rej} if _rej else {},
        derived_from="ops_agent_descriptions(status)"))

_funnel = funnel_rows(_stages, run_at=now)
for line in funnel_lines(_funnel):
    print(line)

spark.createDataFrame(
    [(r["run_at"], r["stage"], r["in_count"], r["out_count"],
      r["fell_off"], r["reasons"], r["derived_from"]) for r in _funnel],
    schema=to_spark_schema(FUNNEL)) \
    .write.format("delta").mode("append").saveAsTable("ops_funnel")
print(f"[+] ops_funnel: {len(_funnel)} stage rows appended "
      "(each fell-off links to ops_fallout / ops_parse_errors rows)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 8: Journey tables — one row, the whole pipeline (family G)
# Metric-grain + report-grain, joins over contract tables ONLY; the
# dashboard reads these and computes nothing (accuracy contract).
from src.governance.journey import metric_journey_rows, report_journey_rows
from src.schemas import METRIC_JOURNEY, REPORT_JOURNEY

_sql_sources = [r.asDict() for r in
                spark.table(config.lakehouse.sql_sources)
                .select("metric_id", "source_type", "source_schema").collect()]
_validation = [r.asDict() for r in spark.table("ops_pipeline_validation").collect()]
_parse_errs = [r.asDict() for r in
               spark.table("ops_parse_errors")
               .select("metric_id", "error_category").collect()]
_cards2 = ([r.asDict() for r in
            spark.table("output_metric_logic")
            .select("metric_id", "calculation_logic").collect()]
           if spark.catalog.tableExists("output_metric_logic") else [])
_descs = ([r.asDict() for r in spark.table("ops_agent_descriptions").collect()]
          if spark.catalog.tableExists("ops_agent_descriptions") else [])
_report_srcs = ([r.asDict() for r in spark.table("input_report_sources").collect()]
                if spark.catalog.tableExists("input_report_sources") else [])
_pub_log = ([r.asDict() for r in spark.table("gov_publish_log").collect()]
            if spark.catalog.tableExists("gov_publish_log") else [])

journey = metric_journey_rows(
    now, _sql_sources, _validation, _parse_errs, _cards2, _descs,
    _report_srcs, _pub_log)
spark.createDataFrame(
    [tuple(r[c] for c, _, _ in METRIC_JOURNEY["columns"]) for r in journey],
    schema=to_spark_schema(METRIC_JOURNEY)) \
    .write.format("delta").mode("append").saveAsTable("ops_metric_journey")
tied = sum(1 for r in journey if r["report_count"])
print(f"\nops_metric_journey: {len(journey)} metrics "
      f"({tied} tied to PBI reports)")

report_journey = report_journey_rows(
    now, _report_srcs,
    corpus_metric_ids={s["metric_id"] for s in _sql_sources})
if report_journey:
    spark.createDataFrame(
        [tuple(r[c] for c, _, _ in REPORT_JOURNEY["columns"])
         for r in report_journey],
        schema=to_spark_schema(REPORT_JOURNEY)) \
        .write.format("delta").mode("append").saveAsTable("ops_report_journey")
print(f"ops_report_journey: {len(report_journey)} reports")
print("\nThe journey dashboard reads these two tables + ops_funnel — "
      "see docs/internal/RUNBOOK_JOURNEY_DASHBOARD.md")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
