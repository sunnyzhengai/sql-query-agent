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

"""Fabric Notebook: Extract and Parse SQL Sources

Reads from: sql_sources (Delta table)
Writes to:  parse_results, parse_errors, parse_successes (Delta tables)

parse_results stores the full parsed output (CTEs as JSON) so
300_build_graph.py can rebuild the graph without re-parsing.
"""

# %% Cell 0: Setup
# Prerequisites: Attach 'sql-logic-env' Fabric Environment. DO NOT use %pip install.
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
REQUIRES_ENGINE = "1.22"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "200_parse")


# Load pythonnet + ScriptDom directly (do not call load_scriptdom — it re-triggers init)
from pythonnet import load

try:
    load("coreclr")
except Exception:  # noqa: BLE001, S110 — idempotent init: already-loaded runtime throws, which is fine
    pass

from System.Reflection import Assembly

Assembly.LoadFrom("/lakehouse/default/Files/sql-query-agent/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll")
from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
from System.IO import StringReader

print("ScriptDom loaded!")

# Import parsing functions from src/ — all logic lives there, not in this notebook
from src.config import load_config
from src.parser.scriptdom_fabric import extract_from_fragment, parse_from_fragment

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")


def _parse_raw(raw_sql):
    """Parse raw SQL string into a ScriptDom AST fragment."""
    parser = TSql160Parser(True)
    reader = StringReader(raw_sql)
    result = parser.Parse(reader, None)
    return result[0] if isinstance(result, tuple) else result


def parse_with_scriptdom(raw_sql):
    """Parse T-SQL and return ParsedSQL. Thin wrapper: init here, logic in src/."""
    return parse_from_fragment(_parse_raw(raw_sql))


def extract_with_scriptdom(raw_sql):
    """Extract raw SQL strings. Thin wrapper: init here, logic in src/."""
    return extract_from_fragment(_parse_raw(raw_sql))


print("ScriptDom ready")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load SQL sources
from src.steps.gates import precondition_gate

# Required inputs must exist (and be non-empty where the contract says so)
# BEFORE work starts — a missing table fails with a message naming the
# producing notebook, not a pyspark stack trace. Registry-driven; see
# src/steps/gates.py.
precondition_gate("200_parse", table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count())


sql_sources_df = spark.table(config.lakehouse.sql_sources)

sql_sources_df = sql_sources_df.selectExpr(
    "metric_id",
    "name",
    "sql",
    "cast(null as string) as steward",
    "cast(null as string) as developer",
)

sql_sources = [row.asDict() for row in sql_sources_df.collect()]
print(f"Loaded {len(sql_sources)} SQL sources")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Parse all sources (logic in src/steps/parse.py)
import time as _time

from src.steps.parse import parse_step

# ScriptDom only — no fallback parser. If ScriptDom failed to load, Cell 0
# already stopped the run; degrading to a weaker parser silently thins the
# graph (18 known extraction gaps in the sqlglot path).
print("Parsing SQL with ScriptDom (Option B)...")
parse_fn = parse_with_scriptdom

# Previous run state (read BEFORE any writes) for regression detection.
# Absence = first run (legit); a FAILED read must raise — a swallowed error
# here silently disabled regression detection (audit 2026-08-15).
previous_error_records, previous_success_ids = [], []
if spark.catalog.tableExists("ops_error_log"):
    previous_error_records = [r.asDict() for r in spark.table("ops_error_log").collect()]
if spark.catalog.tableExists("ops_parse_successes"):
    previous_success_ids = [r["metric_id"] for r in spark.table("ops_parse_successes").collect()]
if not previous_success_ids:
    print("No previous run history — regression detection starts next run")

# Prior PHI findings carry steward dispositions forward (ADR 0025)
previous_phi_records = []
if spark.catalog.tableExists("ops_phi_findings"):
    previous_phi_records = [r.asDict() for r in spark.table("ops_phi_findings").collect()]
else:
    print("No previous PHI findings — first scan")

from datetime import datetime, timezone

start_time = _time.time()
out = parse_step(
    sql_sources, parse_fn,
    previous_error_records=previous_error_records,
    previous_success_ids=previous_success_ids,
    progress=lambda done, total: print(f"  Progress: {done}/{total}") if done % 100 == 0 else None,
    previous_phi_records=previous_phi_records,
    scan_timestamp=datetime.now(timezone.utc).isoformat(),
)
elapsed = _time.time() - start_time

print(f"\nDone in {elapsed:.0f}s")
print(f"Parsed: {len(out.parse_successes)}/{len(sql_sources)} "
      f"({100 * len(out.parse_successes) // max(len(sql_sources), 1)}%)")
print(f"Errors: {len(out.parse_errors)}")

# Suppressed AST-walk exceptions: nonzero means refs may be MISSING from
# procs that still count as parse successes. Loud here, per-proc in the row.
suppressed_total = sum(r.get("extraction_suppressed") or 0 for r in out.parse_results)
if suppressed_total:
    worst = sorted(out.parse_results, key=lambda r: r.get("extraction_suppressed") or 0, reverse=True)[:5]
    print(f"[!] {suppressed_total} AST extraction(s) suppressed across "
          f"{sum(1 for r in out.parse_results if r.get('extraction_suppressed'))} procs — "
          f"refs may be missing despite parse success. Worst:")
    for r in worst:
        if r.get("extraction_suppressed"):
            print(f"    {r['metric_id']}: {r['extraction_suppressed']}")
else:
    print("[+] 0 suppressed AST extractions — every parsed ref was captured")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Save results to Delta and run the postcondition gate
from src.schemas import (
    ERROR_LOG,
    PARSE_ERRORS,
    PARSE_RESULTS,
    PARSE_SUCCESSES,
    PHI_FINDINGS,
    to_spark_schema,
)
from src.steps.gates import postcondition_gate

# Every outcome table is written UNCONDITIONALLY — an empty table means
# "200 ran and found nothing", a missing table means "200 never ran". The
# write-only-if-nonempty made those two states indistinguishable downstream
# old made those states indistinguishable (audit 2026-08-15).
spark.createDataFrame(out.parse_results, schema=to_spark_schema(PARSE_RESULTS)) \
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ops_parse_results")
print(f"Saved {len(out.parse_results)} parse results to ops_parse_results")

spark.createDataFrame(out.parse_errors, schema=to_spark_schema(PARSE_ERRORS)) \
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ops_parse_errors")
print(f"Saved {len(out.parse_errors)} parse errors to ops_parse_errors")
if out.parse_errors:
    print("\nTop errors:")
    for e in sorted(out.parse_errors, key=lambda x: x["line_count"], reverse=True)[:5]:
        print(f"  {e['metric_id']} ({e['line_count']} lines): [{e['error_category']}] {e['error'][:80]}")

spark.createDataFrame(out.parse_successes, schema=to_spark_schema(PARSE_SUCCESSES)) \
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ops_parse_successes")
print(f"Saved {len(out.parse_successes)} parse successes to ops_parse_successes")

spark.createDataFrame(out.phi_findings, schema=to_spark_schema(PHI_FINDINGS)) \
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ops_phi_findings")
n_redact = sum(1 for f in out.phi_findings if f["disposition"] == "redact")
n_open = sum(1 for f in out.phi_findings if f["disposition"] == "open")
print(f"Saved {len(out.phi_findings)} PHI findings to ops_phi_findings "
      f"({n_redact} redact, {n_open} open for steward review)")

if out.error_log.current_run:
    spark.createDataFrame(out.error_log.to_records(), schema=to_spark_schema(ERROR_LOG)) \
        .write.format("delta").mode("append").saveAsTable("ops_error_log")
    print(f"Appended {len(out.error_log.current_run)} entries to ops_error_log")
    print(out.error_log.summary_text())
if out.run_summary.get("regressions"):
    print(f"[!] REGRESSIONS — previously passing, now failing: {out.run_summary['regressed_metrics']}")
if out.run_summary.get("resolved"):
    print(f"[+] Resolved since last run: {out.run_summary['resolved_metrics']}")

# Postcondition gate: prove the persisted state honors this step's contracts
checked = postcondition_gate(
    "200_parse",
    fetch=lambda t, cols: [r.asDict() for r in spark.table(t).select(*cols).collect()],
    table_exists=spark.catalog.tableExists,
)
print(f"[+] Postcondition gate passed for: {', '.join(checked)}")

print("\n→ Next: run 300_build_graph (no need to rerun this unless SQL sources changed)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
