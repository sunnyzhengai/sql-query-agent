"""Fabric Notebook: Debug extraction stats

Run after inspect_extracted_sql to understand where failures are.
Requires 'results' variable in scope from Cell 4.
"""

# %% Cell 1: Extraction vs parse breakdown
no_queries = sum(1 for r in results if r["query_count"] == 0)
low_queries = sum(1 for r in results if 0 < r["query_count"] <= 2)
found_but_failed = sum(1 for r in results if r["query_count"] > 0 and not r["parse_ok"])
parsed_ok = sum(1 for r in results if r["parse_ok"])

print(f"Total: {len(results)}")
print(f"No queries extracted: {no_queries}")
print(f"1-2 queries only: {low_queries}")
print(f"Queries found but parse failed: {found_but_failed}")
print(f"Parsed OK: {parsed_ok}")

# %% Cell 2: Show procs with zero queries extracted
print("\n=== Zero Queries Extracted ===")
zeros = [r for r in results if r["query_count"] == 0]
for r in zeros[:5]:
    print(f"\n  {r['metric_id']} ({r['line_count']} lines)")
    print(f"  Raw SQL first 200 chars:")
    print(f"  {r['raw_sql'][:200]}")

# %% Cell 3: Show procs that extracted but failed to parse
print("\n=== Extracted But Failed Parse ===")
ext_fail = [r for r in results if r["query_count"] > 0 and not r["parse_ok"]]
for r in ext_fail[:5]:
    print(f"\n  {r['metric_id']} ({r['line_count']} lines, {r['query_count']} queries)")
    print(f"  Parse error: {r['parse_error'][:150]}")
    print(f"  Clean SQL first 200 chars:")
    print(f"  {r['clean_sql'][:200]}")

# %% Cell 4: Compare with old extractor
# Run both extractors on the same data to see which finds more
from src.parser.sql_extractor import extract_queries

query_count_dist = {}
for r in results:
    qc = r["query_count"]
    bucket = "0" if qc == 0 else "1" if qc == 1 else "2-5" if qc <= 5 else "6-20" if qc <= 20 else "21-50" if qc <= 50 else "50+"
    query_count_dist[bucket] = query_count_dist.get(bucket, 0) + 1

print("\n=== Query Count Distribution ===")
for bucket in ["0", "1", "2-5", "6-20", "21-50", "50+"]:
    count = query_count_dist.get(bucket, 0)
    print(f"  {bucket} queries: {count} procs")
