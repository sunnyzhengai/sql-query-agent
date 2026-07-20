"""Fabric Notebook: Test sqlparse-based SQL Extractor

Tests the deterministic SQL extractor (no LLM needed) against
small, medium, and large stored procedures.

Run AFTER load_sql_files.py has populated the sql_sources table.
"""

# %% Cell 1: Install dependencies
%pip install pydantic pyyaml sqlglot sqlparse

# %% Cell 2: Setup
import json
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.parser.sql_extractor import (
    extract_select_statements,
    categorize_by_size,
    test_extraction_sample,
)

# %% Cell 3: Load SQL sources
sql_sources_df = spark.table("sql_sources")
sql_sources = [row.asDict() for row in sql_sources_df.collect()]
print(f"Loaded {len(sql_sources)} SQL sources")

# %% Cell 4: Categorize by size
categories = categorize_by_size(sql_sources)
for cat, sources in categories.items():
    if sources:
        lines = [s["line_count"] for s in sources]
        print(f"  {cat}: {len(sources)} procs ({min(lines)}-{max(lines)} lines)")

# %% Cell 5: Test extraction on 5 from each category
print("Testing extraction + parsing on 15 sample procs...\n")
results = test_extraction_sample(sql_sources, n_per_category=5)

for cat_name, cat_results in results.items():
    print(f"\n{'='*60}")
    print(f"  {cat_name.upper()} QUERIES")
    print(f"{'='*60}")

    for r in cat_results:
        status = "OK" if r["parse_ok"] else "FAIL"
        print(f"\n  [{status}] {r['metric_id']} ({r['line_count']} lines)")
        if r["parse_ok"]:
            print(f"       CTEs: {r['cte_count']}, Tables: {r['table_count']}")
        else:
            if r["extraction_error"]:
                print(f"       Extraction error: {r['extraction_error'][:100]}")
            if r["parse_error"]:
                print(f"       Parse error: {r['parse_error'][:100]}")
        print(f"       SQL preview: {r['clean_sql_preview'][:120]}...")

# %% Cell 6: Summary
total = sum(len(r) for r in results.values())
passed = sum(1 for cat in results.values() for r in cat if r["parse_ok"])
failed = total - passed
print(f"\n{'='*60}")
print(f"SUMMARY: {passed}/{total} parsed successfully ({100*passed//total}%)")
print(f"{'='*60}")

# %% Cell 7: Run extraction on ALL procs and count success rate
print(f"Running extraction on all {len(sql_sources)} procs...\n")

from src.parser.sql_parser import parse_sql

success = 0
errors = []

for i, source in enumerate(sql_sources):
    try:
        clean = extract_select_statements(source["sql"])
        parsed = parse_sql(clean)
        success += 1
    except Exception as e:
        errors.append((source["metric_id"], str(e)[:80]))

    if (i + 1) % 100 == 0:
        print(f"  Processed {i + 1}/{len(sql_sources)}... ({success} ok, {len(errors)} errors)")

print(f"\nFinal: {success}/{len(sql_sources)} parsed successfully ({100*success//len(sql_sources)}%)")
print(f"Errors: {len(errors)}")

if errors:
    print(f"\nFirst 10 errors:")
    for mid, err in errors[:10]:
        print(f"  {mid}: {err}")
