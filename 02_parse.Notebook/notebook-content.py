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


# %% Cell 2: Extract and parse each SQL source
import time as _time
from src.parser.sql_parser import parse_sql
from src.parser.error_classifier import classify_parse_error

extractor_name = "ScriptDom (Option B)" if scriptdom_available else "sqlparse + sqlglot"
print(f"Parsing SQL with {extractor_name}...")

parse_errors = []
parse_successes = []
parse_results_data = []
start_time = _time.time()

for i, source in enumerate(sql_sources):
    metric_id = source["metric_id"]
    name = source["name"]
    sql = source["sql"]

    try:
        if scriptdom_available:
            # Option B: ScriptDom extracts structure directly from AST
            # No sqlglot, no cleanup rules, 100% T-SQL compatibility
            parsed = parse_with_scriptdom(sql)
        else:
            # Fallback: sqlparse extraction + sqlglot parsing
            parsed = parse_sql(sql)

        # Store parse result as JSON for downstream notebooks
        ctes_json = json.dumps([{
            "name": c.name,
            "sql_fragment": c.sql_fragment,
            "table_refs": [{"table": t.table, "schema": t.schema, "database": t.database}
                           if hasattr(t, 'schema') else {"table": t, "schema": "dbo", "database": None}
                           for t in c.table_refs],
            "depends_on": c.depends_on,
            "column_refs": [{"table": cr.table, "column": cr.column} for cr in c.column_refs],
        } for c in parsed.ctes])

        parse_results_data.append({
            "metric_id": metric_id,
            "name": name,
            "ctes_json": ctes_json,
            "final_select_tables": json.dumps([
                {"table": t.table, "schema": t.schema, "database": t.database}
                if hasattr(t, 'schema') else {"table": t, "schema": "dbo", "database": None}
                for t in parsed.final_select_tables
            ]),
            "final_select_cte_refs": json.dumps(parsed.final_select_cte_refs),
            "normalized_sql": parsed.normalized_sql or "",
            "cte_count": len(parsed.ctes),
            "table_count": len(parsed.final_select_tables),
            "line_count": sql.count("\n") + 1,
        })

        parse_successes.append({
            "metric_id": metric_id,
            "name": name,
            "cte_count": len(parsed.ctes),
            "table_count": len(parsed.final_select_tables),
            "line_count": sql.count("\n") + 1,
        })
        print(f"  Parsed: {metric_id} — {len(parsed.ctes)} CTEs, {len(parsed.final_select_tables)} tables")

    except Exception as e:
        lc = sql.count("\n") + 1
        classification = classify_parse_error(str(e), metric_id, lc)
        parse_errors.append({
            "metric_id": metric_id,
            "name": name,
            "error": str(e)[:200],
            "error_category": classification["error_category"],
            "user_explanation": classification["user_explanation"],
            "suggested_action": classification["suggested_action"],
            "line_count": lc,
        })
        print(f"  ERROR: {metric_id} [{classification['error_category']}] {str(e)[:100]}")

    if (i + 1) % 100 == 0:
        elapsed = _time.time() - start_time
        print(f"  Progress: {i + 1}/{len(sql_sources)} ({len(parse_successes)} ok, {len(parse_errors)} errors, {elapsed:.0f}s)")

elapsed = _time.time() - start_time
print(f"\nDone in {elapsed:.0f}s")
print(f"Parsed: {len(parse_successes)}/{len(sql_sources)} ({100 * len(parse_successes) // max(len(sql_sources), 1)}%)")
print(f"Errors: {len(parse_errors)}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Save results to Delta tables
from src.governance.error_log import ErrorLog
from src.schemas import ERROR_LOG, PARSE_ERRORS, PARSE_SUCCESSES, to_spark_schema
from pyspark.sql.types import StringType, StructField, StructType, IntegerType

# Read previous run state BEFORE overwriting, so the error log can detect
# regressions (passed last run, fails now) and resolutions.
error_log = ErrorLog()
try:
    error_log.load_history([r.asDict() for r in spark.table("ops_error_log").collect()])
    error_log.set_previous_successes(
        [r["metric_id"] for r in spark.table("ops_parse_successes").collect()]
    )
except Exception:
    print("No previous run history — regression detection starts next run")
error_log.start_run()

# Save parse results (intermediate table for 03_build_graph)
if parse_results_data:
    pr_schema = StructType([
        StructField("metric_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("ctes_json", StringType(), True),
        StructField("final_select_tables", StringType(), True),
        StructField("final_select_cte_refs", StringType(), True),
        StructField("normalized_sql", StringType(), True),
        StructField("cte_count", IntegerType(), True),
        StructField("table_count", IntegerType(), True),
        StructField("line_count", IntegerType(), True),
    ])
    pr_rows = [(r["metric_id"], r["name"], r["ctes_json"], r["final_select_tables"],
                r["final_select_cte_refs"], r["normalized_sql"], r["cte_count"], r["table_count"], r["line_count"])
               for r in parse_results_data]
    pr_df = spark.createDataFrame(pr_rows, schema=pr_schema)
    pr_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("ops_parse_results")
    print(f"Saved {len(parse_results_data)} parse results to 'parse_results' table")

# Save parse errors
if parse_errors:
    errors_rows = [(e["metric_id"], e["name"], e["error"], e.get("error_category"),
                    e.get("user_explanation"), e.get("suggested_action"), e["line_count"])
                   for e in parse_errors]
    errors_df = spark.createDataFrame(errors_rows, schema=to_spark_schema(PARSE_ERRORS))
    errors_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("ops_parse_errors")
    print(f"Saved {len(parse_errors)} parse errors to 'parse_errors' table")
    print("\nTop errors:")
    for e in sorted(parse_errors, key=lambda x: x["line_count"], reverse=True)[:5]:
        print(f"  {e['metric_id']} ({e['line_count']} lines): [{e['error_category']}] {e['error'][:80]}")

# Save parse successes
if parse_successes:
    success_rows = [(s["metric_id"], s["name"], s["cte_count"], s["table_count"], s["line_count"])
                    for s in parse_successes]
    success_df = spark.createDataFrame(success_rows, schema=to_spark_schema(PARSE_SUCCESSES))
    success_df.write.format("delta").mode("overwrite").saveAsTable("ops_parse_successes")
    print(f"Saved {len(parse_successes)} parse successes to 'parse_successes' table")

# Append this run's errors to the persistent error log (ops_error_log)
for e in parse_errors:
    error_log.record_error(
        metric_id=e["metric_id"],
        metric_name=e["name"],
        error_type="parse",
        error_message=e["error"],
        line_count=e["line_count"],
    )
run_summary = error_log.finish_run([s["metric_id"] for s in sql_sources])
if error_log.current_run:
    el_df = spark.createDataFrame(error_log.to_records(), schema=to_spark_schema(ERROR_LOG))
    el_df.write.format("delta").mode("append").saveAsTable("ops_error_log")
    print(f"Appended {len(error_log.current_run)} entries to ops_error_log")
    print(error_log.summary_text())
if run_summary.get("regressions"):
    print(f"[!] REGRESSIONS — previously passing, now failing: {run_summary['regressed_metrics']}")
if run_summary.get("resolved"):
    print(f"[+] Resolved since last run: {run_summary['resolved_metrics']}")

print("\n→ Next: run 03_build_graph.py (no need to rerun this unless SQL sources changed)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
