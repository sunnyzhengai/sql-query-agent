"""Fabric Notebook: Debug parse errors.

Finds specific procs that failed to parse and shows their SQL
so you can inspect what's causing the failure.

Run after orchestrator_v2 — uses sql_sources, parse_sql in scope.
"""

# %% Cell 1: Find one proc that failed with each error type
from src.parser.sql_parser import parse_sql
from src.parser.proc_normalize import ProcNotViewShaped

error_examples = {}  # error_type -> (metric_id, error_detail, first_lines)

for source in sql_sources:
    metric_id = source["metric_id"]
    sql = source["sql"]

    try:
        parsed = parse_sql(sql)
    except Exception as ex:
        error_type = str(ex)[:50]
        if error_type not in error_examples:
            # Get first 20 non-empty, non-comment lines of the SQL
            lines = []
            for line in sql.split("\n"):
                stripped = line.strip()
                if stripped and not stripped.startswith("--") and not stripped.startswith("/*") and not stripped.startswith("*"):
                    lines.append(stripped)
                if len(lines) >= 20:
                    break
            error_examples[error_type] = (metric_id, str(ex), lines)

    if len(error_examples) >= 10:
        break

print(f"Found {len(error_examples)} distinct error types:\n")
for i, (error_type, (metric_id, full_error, lines)) in enumerate(error_examples.items()):
    print(f"{'='*70}")
    print(f"ERROR TYPE {i+1}: {error_type}")
    print(f"METRIC: {metric_id}")
    print(f"FULL ERROR: {full_error[:200]}")
    print(f"FIRST 20 LINES OF SQL:")
    for line in lines:
        print(f"  {line[:120]}")
    print()

# %% Cell 2: Count how many procs fail with each error type
from collections import Counter

error_counts = Counter()

for source in sql_sources:
    try:
        parsed = parse_sql(source["sql"])
    except Exception as ex:
        # Categorize the error
        err_str = str(ex)
        if "procedural" in err_str:
            error_counts["procedural (IF/WHILE/GOTO)"] += 1
        elif "not view shaped" in err_str.lower() or "ProcNotViewShaped" in err_str:
            error_counts["not view shaped"] += 1
        elif "unsupported_statement" in err_str:
            error_counts["unsupported statement"] += 1
        elif "Failed to parse SQL" in err_str:
            error_counts["sqlglot parse failure"] += 1
        elif "multiple_terminal_selects" in err_str:
            error_counts["multiple terminal SELECTs"] += 1
        elif "no_terminal_select" in err_str:
            error_counts["no terminal SELECT"] += 1
        else:
            error_counts[f"other: {err_str[:60]}"] += 1

print("=== Error Breakdown ===")
for error_type, count in error_counts.most_common():
    print(f"  {count:4d}  {error_type}")
print(f"\n  {sum(error_counts.values()):4d}  TOTAL ERRORS")

# %% Cell 3: Show the specific proc name for one "not view shaped" error
print("\n=== One 'procedural' proc for inspection ===")
for source in sql_sources:
    try:
        parsed = parse_sql(source["sql"])
    except Exception as ex:
        if "procedural" in str(ex):
            print(f"Metric ID: {source['metric_id']}")
            print(f"Name: {source['name']}")
            print(f"Error: {str(ex)[:200]}")
            print(f"\nFirst 30 lines:")
            for i, line in enumerate(source["sql"].split("\n")[:30]):
                print(f"  {i+1:3d}: {line.rstrip()[:120]}")
            break
