"""Fabric Notebook: Extract and Parse SQL Sources

Reads from: sql_sources (Delta table)
Writes to:  parse_results, parse_errors, parse_successes (Delta tables)

parse_results stores the full parsed output (CTEs as JSON) so
03_build_graph.py can rebuild the graph without re-parsing.
"""

# %% Cell 0: Setup (run once per session)
%pip install pydantic pyyaml sqlglot sqlparse pythonnet

import json
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.schemas import to_spark_schema
from src.parser.scriptdom_fabric import load_scriptdom

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")
scriptdom_available, extract_with_scriptdom = load_scriptdom()

if scriptdom_available:
    print("ScriptDom loaded!")
else:
    print("ScriptDom not available, using sqlparse fallback")
    from src.parser.sql_extractor import extract_select_statements

def read_source(name_or_path):
    """Read a data source by name or path."""
    if name_or_path.endswith(".csv"):
        return spark.read.option("header", "true").option("inferSchema", "true").csv(name_or_path)
    elif "abfss://" in name_or_path or "/" in name_or_path:
        return spark.read.format("delta").load(name_or_path)
    else:
        return spark.table(name_or_path)

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

# %% Cell 2: Extract and parse each SQL source
import time as _time
from src.parser.sql_parser import parse_sql, parse_extracted_queries
from src.parser.error_classifier import classify_parse_error

extractor_name = "ScriptDom" if scriptdom_available else "sqlparse"
print(f"Extracting and parsing SQL with {extractor_name}...")

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
            queries = extract_with_scriptdom(sql)
            if not queries:
                raise ValueError("ScriptDom found no SELECT statements")
            parsed = parse_extracted_queries(queries, dialect="tsql")
        else:
            clean_sql = extract_select_statements(sql)
            parsed = parse_sql(clean_sql)

        # Store parse result as JSON for downstream notebooks
        ctes_json = json.dumps([{
            "name": c.name,
            "sql_fragment": c.sql_fragment,
            "table_refs": c.table_refs,
            "depends_on": c.depends_on,
        } for c in parsed.ctes])

        parse_results_data.append({
            "metric_id": metric_id,
            "name": name,
            "ctes_json": ctes_json,
            "final_select_tables": json.dumps(parsed.final_select_tables),
            "final_select_cte_refs": json.dumps(parsed.final_select_cte_refs),
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

# %% Cell 3: Save results to Delta tables
from src.schemas import PARSE_ERRORS, PARSE_SUCCESSES, to_spark_schema
from pyspark.sql.types import StringType, StructField, StructType, IntegerType

# Save parse results (intermediate table for 03_build_graph)
if parse_results_data:
    pr_schema = StructType([
        StructField("metric_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("ctes_json", StringType(), True),
        StructField("final_select_tables", StringType(), True),
        StructField("final_select_cte_refs", StringType(), True),
        StructField("cte_count", IntegerType(), True),
        StructField("table_count", IntegerType(), True),
        StructField("line_count", IntegerType(), True),
    ])
    pr_rows = [(r["metric_id"], r["name"], r["ctes_json"], r["final_select_tables"],
                r["final_select_cte_refs"], r["cte_count"], r["table_count"], r["line_count"])
               for r in parse_results_data]
    pr_df = spark.createDataFrame(pr_rows, schema=pr_schema)
    pr_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("parse_results")
    print(f"Saved {len(parse_results_data)} parse results to 'parse_results' table")

# Save parse errors
if parse_errors:
    errors_rows = [(e["metric_id"], e["name"], e["error"], e.get("error_category"),
                    e.get("user_explanation"), e.get("suggested_action"), e["line_count"])
                   for e in parse_errors]
    errors_df = spark.createDataFrame(errors_rows, schema=to_spark_schema(PARSE_ERRORS))
    errors_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("parse_errors")
    print(f"Saved {len(parse_errors)} parse errors to 'parse_errors' table")
    print("\nTop errors:")
    for e in sorted(parse_errors, key=lambda x: x["line_count"], reverse=True)[:5]:
        print(f"  {e['metric_id']} ({e['line_count']} lines): [{e['error_category']}] {e['error'][:80]}")

# Save parse successes
if parse_successes:
    success_rows = [(s["metric_id"], s["name"], s["cte_count"], s["table_count"], s["line_count"])
                    for s in parse_successes]
    success_df = spark.createDataFrame(success_rows, schema=to_spark_schema(PARSE_SUCCESSES))
    success_df.write.format("delta").mode("overwrite").saveAsTable("parse_successes")
    print(f"Saved {len(parse_successes)} parse successes to 'parse_successes' table")

print("\n→ Next: run 03_build_graph.py (no need to rerun this unless SQL sources changed)")
