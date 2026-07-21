"""Fabric Notebook: Inspect Extracted SQL

Runs the extractor on all SQL sources and saves the cleaned output
to a Delta table for manual inspection. Each row shows:
- Original metric name
- Number of queries extracted
- The clean SQL that would be parsed
- Parse success/failure

Run AFTER load_sql_files.py has populated sql_sources.
"""

# %% Cell 1: Install dependencies
%pip install pydantic pyyaml sqlglot sqlparse

# %% Cell 2: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.parser.sql_extractor import extract_queries, extract_select_statements
from src.parser.sql_parser import parse_sql

# %% Cell 3: Load SQL sources
sql_sources_df = spark.table("sql_sources")
sql_sources = [row.asDict() for row in sql_sources_df.collect()]
print(f"Loaded {len(sql_sources)} SQL sources")

# %% Cell 4: Extract and inspect all
results = []

for i, source in enumerate(sql_sources):
    metric_id = source["metric_id"]
    raw_sql = source["sql"]
    line_count = raw_sql.count("\n") + 1

    # Extract
    try:
        queries = extract_queries(raw_sql)
        clean_sql = ";\n".join(queries)
        extraction_ok = True
        extraction_error = ""
        query_count = len(queries)
    except Exception as e:
        queries = []
        clean_sql = ""
        extraction_ok = False
        extraction_error = str(e)[:500]
        query_count = 0

    # Parse
    parse_ok = False
    parse_error = ""
    cte_count = 0
    table_count = 0
    if extraction_ok and clean_sql:
        try:
            parsed = parse_sql(clean_sql)
            parse_ok = True
            cte_count = len(parsed.ctes)
            table_count = len(parsed.final_select_tables)
        except Exception as e:
            parse_error = str(e)[:500]

    results.append({
        "metric_id": metric_id,
        "line_count": line_count,
        "query_count": query_count,
        "extraction_ok": extraction_ok,
        "extraction_error": extraction_error,
        "parse_ok": parse_ok,
        "parse_error": parse_error,
        "cte_count": cte_count,
        "table_count": table_count,
        "raw_sql": raw_sql,
        "clean_sql": clean_sql,
    })

    if (i + 1) % 100 == 0:
        ok = sum(1 for r in results if r["parse_ok"])
        print(f"  Processed {i + 1}/{len(sql_sources)} ({ok} parsed ok)")

# Summary
total = len(results)
parsed_ok = sum(1 for r in results if r["parse_ok"])
extracted_ok = sum(1 for r in results if r["extraction_ok"])
print(f"\nDone: {parsed_ok}/{total} parsed ({100 * parsed_ok // total}%)")
print(f"Extraction: {extracted_ok}/{total} succeeded")

# %% Cell 5: Save to Delta table for inspection
from pyspark.sql.types import StringType, StructField, StructType, IntegerType, BooleanType

schema = StructType([
    StructField("metric_id", StringType(), False),
    StructField("line_count", IntegerType(), True),
    StructField("query_count", IntegerType(), True),
    StructField("extraction_ok", BooleanType(), True),
    StructField("extraction_error", StringType(), True),
    StructField("parse_ok", BooleanType(), True),
    StructField("parse_error", StringType(), True),
    StructField("cte_count", IntegerType(), True),
    StructField("table_count", IntegerType(), True),
    StructField("raw_sql", StringType(), True),
    StructField("clean_sql", StringType(), True),
])

rows = [
    (r["metric_id"], r["line_count"], r["query_count"],
     r["extraction_ok"], r["extraction_error"],
     r["parse_ok"], r["parse_error"],
     r["cte_count"], r["table_count"],
     r["raw_sql"], r["clean_sql"])
    for r in results
]

results_df = spark.createDataFrame(rows, schema=schema)
results_df.write.format("delta").mode("overwrite").saveAsTable("extraction_inspection")
print(f"Saved {len(rows)} rows to extraction_inspection table")

# %% Cell 6: Quick inspection — show failures
print("\n=== Parse Failures ===")
failures = [r for r in results if not r["parse_ok"]]
print(f"Total failures: {len(failures)}\n")

for r in failures[:5]:
    print(f"{'='*60}")
    print(f"Metric: {r['metric_id']} ({r['line_count']} lines)")
    print(f"Queries extracted: {r['query_count']}")
    print(f"Parse error: {r['parse_error'][:200]}")
    print(f"\nClean SQL (first 300 chars):")
    print(r["clean_sql"][:300])
    print()

# %% Cell 7: Quick inspection — show successes
print("\n=== Parse Successes (top 5 by complexity) ===")
successes = sorted(
    [r for r in results if r["parse_ok"]],
    key=lambda r: r["cte_count"],
    reverse=True,
)

for r in successes[:5]:
    print(f"{'='*60}")
    print(f"Metric: {r['metric_id']} ({r['line_count']} lines)")
    print(f"Queries: {r['query_count']}, CTEs: {r['cte_count']}, Tables: {r['table_count']}")
    print(f"\nClean SQL (first 300 chars):")
    print(r["clean_sql"][:300])
    print()

# %% Cell 8: Query the inspection table
# After running, you can inspect in Fabric:
#
# All failures:
#   SELECT metric_id, line_count, parse_error, clean_sql
#   FROM extraction_inspection WHERE parse_ok = false
#   ORDER BY line_count DESC
#
# All successes:
#   SELECT metric_id, cte_count, table_count, clean_sql
#   FROM extraction_inspection WHERE parse_ok = true
#   ORDER BY cte_count DESC
#
# Compare raw vs clean:
#   SELECT metric_id, raw_sql, clean_sql
#   FROM extraction_inspection WHERE metric_id = 'USP_PTA_CensusDashboard_PBI'
print("Inspection table ready. Query 'extraction_inspection' in Fabric SQL or notebook.")
print("Columns: metric_id, line_count, query_count, extraction_ok, parse_ok, parse_error, raw_sql, clean_sql")

# %% Cell 9: Persistent error log — tracks errors across runs
from src.governance.error_log import ErrorLog

error_log = ErrorLog()

# Load history from previous runs
try:
    history_df = spark.table("error_log")
    history_records = [row.asDict() for row in history_df.collect()]
    error_log.load_history(history_records)

    # Set previous successes (metrics that passed in the last run)
    last_run = max(r["run_id"] for r in history_records) if history_records else ""
    last_failures = {r["metric_id"] for r in history_records if r["run_id"] == last_run}
    all_ids = {r["metric_id"] for r in results}
    error_log.set_previous_successes(list(all_ids - last_failures))
except Exception:
    print("No previous error_log table — starting fresh")

# Start new run
error_log.start_run()

# Record all errors from this run
for r in results:
    if not r["parse_ok"]:
        error_type = "extraction" if not r["extraction_ok"] else "parse"
        error_msg = r["extraction_error"] if not r["extraction_ok"] else r["parse_error"]
        error_log.record_error(
            metric_id=r["metric_id"],
            metric_name=r["metric_id"],
            error_type=error_type,
            error_message=error_msg,
            line_count=r["line_count"],
            query_count=r["query_count"],
            clean_sql_preview=r["clean_sql"][:300] if r["clean_sql"] else "",
        )

# Finish run and detect regressions
all_metric_ids = [r["metric_id"] for r in results]
summary = error_log.finish_run(all_metric_ids)

print(f"\n=== Error Log Summary ===")
print(f"Total metrics: {summary['total_metrics']}")
print(f"Success rate: {summary['success_rate']}%")
print(f"New errors: {summary['new_errors']}")
print(f"Known errors: {summary['known_errors']}")
print(f"Regressions: {summary['regressions']}")
print(f"Resolved: {summary['resolved']}")

if summary["regressions"] > 0:
    print(f"\n*** REGRESSIONS DETECTED ***")
    print(f"These metrics previously passed but now fail:")
    for mid in summary.get("regressed_metrics", [])[:10]:
        print(f"  - {mid}")

if summary["resolved"] > 0:
    print(f"\nResolved (previously failed, now passing):")
    for mid in summary["resolved_metrics"][:10]:
        print(f"  + {mid}")

# Save error log to Delta table (append, preserves history)
error_schema = StructType([
    StructField("run_id", StringType(), False),
    StructField("run_timestamp", StringType(), False),
    StructField("metric_id", StringType(), False),
    StructField("metric_name", StringType(), True),
    StructField("error_type", StringType(), True),
    StructField("error_message", StringType(), True),
    StructField("line_count", IntegerType(), True),
    StructField("query_count", IntegerType(), True),
    StructField("clean_sql_preview", StringType(), True),
    StructField("status", StringType(), True),
])

error_records = error_log.to_records()
if error_records:
    error_df = spark.createDataFrame(
        [(r["run_id"], r["run_timestamp"], r["metric_id"], r["metric_name"],
          r["error_type"], r["error_message"], r["line_count"], r["query_count"],
          r["clean_sql_preview"], r["status"])
         for r in error_records],
        schema=error_schema,
    )
    try:
        error_df.write.format("delta").mode("append").saveAsTable("error_log")
    except Exception:
        error_df.write.format("delta").mode("overwrite").saveAsTable("error_log")
    print(f"\nSaved {len(error_records)} error entries to error_log table")

print(f"\n{error_log.summary_text()}")
