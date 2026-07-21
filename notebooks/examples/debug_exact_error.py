"""Fabric Notebook: Debug exact parse error location

Reads from extraction_inspection Delta table — no need to re-run
the inspect notebook. Just point to a metric and see what breaks.
"""

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

%pip install pydantic pyyaml sqlglot sqlparse

# %% Cell 2: Pick a failing metric
# UPDATE this to the metric you want to debug
TARGET_METRIC = "USP_CCMC_SURGERY_QUALITY_INDICATOR_PBI"

row = spark.sql(f"""
    SELECT metric_id, line_count, query_count, parse_ok, parse_error, raw_sql, clean_sql
    FROM extraction_inspection
    WHERE metric_id = '{TARGET_METRIC}'
""").collect()

if not row:
    print(f"Metric {TARGET_METRIC} not found in extraction_inspection table")
else:
    r = row[0].asDict()
    print(f"Metric: {r['metric_id']} ({r['line_count']} lines)")
    print(f"Queries extracted: {r['query_count']}")
    print(f"Parse OK: {r['parse_ok']}")
    print(f"Parse error: {(r['parse_error'] or '')[:200]}")

# %% Cell 3: Show exact error location in the clean SQL
import sqlglot
import re

sql = r["clean_sql"]

try:
    sqlglot.parse_one(sql, dialect="tsql")
    print("Parsed OK!")
except sqlglot.errors.ParseError as e:
    error_str = str(e)
    print(f"Error: {error_str[:300]}\n")

    match = re.search(r"Line (\d+),\s*Col:?\s*(\d+)", error_str)
    if match:
        line_no = int(match.group(1))
        col_no = int(match.group(2))
        lines = sql.split("\n")
        start = max(0, line_no - 5)
        end = min(len(lines), line_no + 5)
        print(f"SQL around line {line_no}, col {col_no}:")
        print("-" * 80)
        for i in range(start, end):
            marker = ">>>" if i == line_no - 1 else "   "
            print(f"  {marker} {i+1:4d}: {lines[i]}")
            if i == line_no - 1:
                pointer = " " * (col_no + 9) + "^"
                print(pointer)
        print("-" * 80)

# %% Cell 4: Parse each extracted query individually
from src.parser.sql_extractor import extract_queries
from src.parser.sql_parser import _clean_extracted_query

raw_sql = r["raw_sql"]
queries = extract_queries(raw_sql)

print(f"Extracted {len(queries)} queries. Parsing each:\n")

for i, q in enumerate(queries):
    cleaned = _clean_extracted_query(q)
    try:
        sqlglot.parse_one(cleaned, dialect="tsql")
        print(f"  Query {i+1}: OK ({cleaned[:60]}...)")
    except sqlglot.errors.ParseError as e:
        error_msg = str(e)
        print(f"  Query {i+1}: FAIL")
        print(f"    Error: {error_msg[:150]}")
        print(f"    SQL: {cleaned[:150]}...")
        print()

# %% Cell 5: List all failing metrics from Delta table
print("=== All Failing Metrics ===\n")
spark.sql("""
    SELECT metric_id, line_count, query_count,
           SUBSTRING(parse_error, 1, 100) as error_preview
    FROM extraction_inspection
    WHERE parse_ok = false
    ORDER BY line_count DESC
""").show(30, truncate=100)

# %% Cell 6: Error pattern analysis
print("=== Error Patterns ===\n")
spark.sql("""
    SELECT
        CASE
            WHEN parse_error LIKE '%Unexpected token%' THEN 'Unexpected token'
            WHEN parse_error LIKE '%Expected%' THEN 'Expected keyword missing'
            WHEN parse_error LIKE '%Error tokenizing%' THEN 'Tokenizer error'
            WHEN parse_error LIKE '%none of%parsed successfully%' THEN 'All queries failed'
            WHEN parse_error LIKE '%no SQL queries found%' THEN 'No queries extracted'
            ELSE 'Other'
        END as error_type,
        COUNT(*) as count
    FROM extraction_inspection
    WHERE parse_ok = false
    GROUP BY 1
    ORDER BY count DESC
""").show(truncate=100)
