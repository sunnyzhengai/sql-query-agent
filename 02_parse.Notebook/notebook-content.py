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
03_build_graph.py can rebuild the graph without re-parsing.
"""

# %% Cell 0: Setup
# Prerequisites: Attach 'sql-logic-env' Fabric Environment. DO NOT use %pip install.
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

# Load pythonnet + ScriptDom directly (do not call load_scriptdom — it re-triggers init)
from pythonnet import load
try:
    load("coreclr")
except Exception:
    pass

import clr
from System.Reflection import Assembly
Assembly.LoadFrom("/lakehouse/default/Files/sql-query-agent/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll")
from Microsoft.SqlServer.TransactSql.ScriptDom import TSql160Parser
from System.IO import StringReader
print("ScriptDom loaded!")

# Import parsing functions from src/ — all logic lives there, not in this notebook
from src.parser.scriptdom_fabric import parse_from_fragment, extract_from_fragment
from src.config import load_config
from src.schemas import to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
scriptdom_available = True


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


print(f"ScriptDom ready: {scriptdom_available}")


def read_source(name_or_path):
    if name_or_path.endswith(".csv"):
        return spark.read.option("header", "true").option("inferSchema", "true").csv(name_or_path)
    elif "abfss://" in name_or_path or "/" in name_or_path:
        return spark.read.format("delta").load(name_or_path)
    else:
        return spark.table(name_or_path)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load SQL sources
sql_sources_df = read_source(config.lakehouse.sql_sources)

sql_sources_df = sql_sources_df.selectExpr(
    "metric_id",
    "name",
    "sql",
    "cast(null as string) as steward",
    "cast(null as string) as developer",
)

sql_sources = [row.asDict() for row in sql_sources_df.limit(50).collect()]  # Remove .limit(50) for full run
print(f"Loaded {len(sql_sources)} SQL sources")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Parse all sources (logic in src/steps/parse.py)
import time as _time
from src.parser.sql_parser import parse_sql
from src.steps.parse import parse_step

extractor_name = "ScriptDom (Option B)" if scriptdom_available else "sqlparse + sqlglot"
print(f"Parsing SQL with {extractor_name}...")
parse_fn = parse_with_scriptdom if scriptdom_available else parse_sql

# Previous run state (read BEFORE any writes) for regression detection
previous_error_records, previous_success_ids = [], []
try:
    previous_error_records = [r.asDict() for r in spark.table("ops_error_log").collect()]
    previous_success_ids = [r["metric_id"] for r in spark.table("ops_parse_successes").collect()]
except Exception:
    print("No previous run history — regression detection starts next run")

start_time = _time.time()
out = parse_step(
    sql_sources, parse_fn,
    previous_error_records=previous_error_records,
    previous_success_ids=previous_success_ids,
    progress=lambda done, total: print(f"  Progress: {done}/{total}") if done % 100 == 0 else None,
)
elapsed = _time.time() - start_time

print(f"\nDone in {elapsed:.0f}s")
print(f"Parsed: {len(out.parse_successes)}/{len(sql_sources)} "
      f"({100 * len(out.parse_successes) // max(len(sql_sources), 1)}%)")
print(f"Errors: {len(out.parse_errors)}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Save results to Delta and run the postcondition gate
from src.schemas import ERROR_LOG, PARSE_ERRORS, PARSE_RESULTS, PARSE_SUCCESSES, to_spark_schema
from src.steps.gates import postcondition_gate

if out.parse_results:
    spark.createDataFrame(out.parse_results, schema=to_spark_schema(PARSE_RESULTS)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("ops_parse_results")
    print(f"Saved {len(out.parse_results)} parse results to ops_parse_results")

if out.parse_errors:
    spark.createDataFrame(out.parse_errors, schema=to_spark_schema(PARSE_ERRORS)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable("ops_parse_errors")
    print(f"Saved {len(out.parse_errors)} parse errors to ops_parse_errors")
    print("\nTop errors:")
    for e in sorted(out.parse_errors, key=lambda x: x["line_count"], reverse=True)[:5]:
        print(f"  {e['metric_id']} ({e['line_count']} lines): [{e['error_category']}] {e['error'][:80]}")

if out.parse_successes:
    spark.createDataFrame(out.parse_successes, schema=to_spark_schema(PARSE_SUCCESSES)) \
        .write.format("delta").mode("overwrite").saveAsTable("ops_parse_successes")
    print(f"Saved {len(out.parse_successes)} parse successes to ops_parse_successes")

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
    "02_parse",
    fetch=lambda t, cols: [r.asDict() for r in spark.table(t).select(*cols).collect()],
    table_exists=spark.catalog.tableExists,
)
print(f"[+] Postcondition gate passed for: {', '.join(checked)}")

print("\n→ Next: run 03_build_graph.py (no need to rerun this unless SQL sources changed)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
