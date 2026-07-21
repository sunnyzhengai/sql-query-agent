"""Fabric Notebook: Debug exact parse error location

Shows the EXACT line and column where sqlglot fails for a specific proc.
Run after inspect_extracted_sql.py — requires 'results' in scope.
"""

# %% Cell 1: Pick a failing metric to investigate
# UPDATE this to the metric you want to debug
TARGET_METRIC = "USP_CCMC_SURGERY_QUALITY_INDICATOR_PBI"

target = next((r for r in results if r["metric_id"] == TARGET_METRIC), None)
if not target:
    print(f"Metric {TARGET_METRIC} not found in results")
else:
    print(f"Metric: {target['metric_id']} ({target['line_count']} lines)")
    print(f"Queries extracted: {target['query_count']}")
    print(f"Parse error: {target['parse_error'][:200]}")

# %% Cell 2: Show exact error location in the clean SQL
import sqlglot
import re

sql = target["clean_sql"]

try:
    sqlglot.parse_one(sql, dialect="tsql")
    print("Parsed OK!")
except sqlglot.errors.ParseError as e:
    error_str = str(e)
    print(f"Error: {error_str[:300]}\n")

    # Extract line and column numbers
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
                # Show column pointer
                pointer = " " * (col_no + 9) + "^"
                print(pointer)
        print("-" * 80)

# %% Cell 3: Try parsing each extracted query individually
from src.parser.sql_extractor import extract_queries

raw_sql = target["raw_sql"]
queries = extract_queries(raw_sql)

print(f"Extracted {len(queries)} queries. Parsing each:\n")

for i, q in enumerate(queries):
    try:
        sqlglot.parse_one(q, dialect="tsql")
        print(f"  Query {i+1}: OK ({q[:60]}...)")
    except sqlglot.errors.ParseError as e:
        error_msg = str(e)
        print(f"  Query {i+1}: FAIL")
        print(f"    Error: {error_msg[:150]}")
        print(f"    SQL: {q[:150]}...")
        print()

# %% Cell 4: Show the clean SQL after _clean_extracted_query
from src.parser.sql_parser import _clean_extracted_query

print("=== Clean SQL for each failing query ===\n")
for i, q in enumerate(queries):
    cleaned = _clean_extracted_query(q)
    try:
        sqlglot.parse_one(cleaned, dialect="tsql")
    except sqlglot.errors.ParseError:
        print(f"Query {i+1} FAILS after cleaning:")
        print(f"  Original ({len(q)} chars): {q[:100]}...")
        print(f"  Cleaned  ({len(cleaned)} chars): {cleaned[:100]}...")
        print(f"  Diff: {'same' if q == cleaned else 'changed'}")
        print()

# %% Cell 5: Investigate a different metric
# Change TARGET_METRIC in Cell 1 and re-run all cells
