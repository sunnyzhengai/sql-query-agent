#!/usr/bin/env python3
"""Extract all table and column names referenced in SQL files.

Scans SQL files and reports which tables and columns are used,
so you only need to export those from the data dictionary.

Usage:
    python scripts/extract_referenced_tables.py path/to/sql/files/

    # Or specify multiple paths:
    python scripts/extract_referenced_tables.py folder1/ folder2/

    # Save to CSV for dictionary export:
    python scripts/extract_referenced_tables.py folder/ --csv output.csv

Output:
    - List of unique table names referenced across all SQL files
    - List of unique table.column pairs
    - Per-file breakdown of which tables each SQL file uses
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


def extract_table_refs(sql: str) -> set[str]:
    """Extract table names from SQL text using pattern matching.

    Looks for:
    - FROM table / FROM schema.table / FROM db.schema.table
    - JOIN table / JOIN schema.table
    - INTO #table (temp tables — included for completeness)
    """
    tables = set()

    # FROM and JOIN patterns: capture the last identifier (table name)
    # Handles: FROM table, FROM schema.table, FROM db.schema.table
    # Also handles: FROM [bracketed].[names]
    pattern = r'(?:FROM|JOIN)\s+(?:[\w\[\]]+\.)*(\[?\w+\]?)\s'
    for match in re.finditer(pattern, sql, re.IGNORECASE):
        name = match.group(1).strip('[]')
        # Skip common noise
        if name.upper() not in ('SELECT', 'WHERE', 'SET', 'AS', 'ON', 'AND', 'OR', 'NOT', 'NULL', 'INTO'):
            tables.add(name)

    # INTO #temp patterns
    for match in re.finditer(r'INTO\s+#(\w+)', sql, re.IGNORECASE):
        tables.add(f"#{match.group(1)}")

    return tables


def extract_column_refs(sql: str) -> set[tuple[str, str]]:
    """Extract table.column pairs from SQL text.

    Looks for alias.COLUMN_NAME patterns in SELECT, WHERE, ON, GROUP BY.
    Returns set of (alias_or_table, column) tuples.
    """
    columns = set()

    # Pattern: alias.column or [alias].[column]
    pattern = r'\[?(\w+)\]?\.\[?(\w+)\]?'
    for match in re.finditer(pattern, sql):
        table_or_alias = match.group(1)
        column = match.group(2)
        # Skip schema.table patterns (dbo.TABLE_NAME) by checking if
        # the "column" looks like a known schema prefix
        if table_or_alias.upper() in ('DBO', 'CLARITY', 'REPORTING', 'SYS'):
            continue
        # Skip common SQL keywords that look like table.column
        if column.upper() in ('NAME', 'VALUE', 'TYPE', 'ID', 'COUNT', 'MAX', 'MIN', 'SUM', 'AVG'):
            # These are ambiguous — include them since they could be real columns
            pass
        columns.add((table_or_alias, column))

    return columns


def scan_sql_files(paths: list[Path]) -> dict:
    """Scan all SQL files and collect table/column references.

    Returns dict with:
    - tables: set of all unique table names
    - columns: set of all unique (table_or_alias, column) pairs
    - per_file: dict of filename -> set of tables
    """
    all_tables = set()
    all_columns = set()
    per_file = {}

    sql_files = []
    for p in paths:
        if p.is_file() and p.suffix.lower() == '.sql':
            sql_files.append(p)
        elif p.is_dir():
            sql_files.extend(p.rglob('*.sql'))

    for sql_file in sorted(sql_files):
        sql = sql_file.read_text(errors='replace')
        tables = extract_table_refs(sql)
        columns = extract_column_refs(sql)
        all_tables |= tables
        all_columns |= columns
        # Remove temp tables from per-file view
        physical_tables = {t for t in tables if not t.startswith('#')}
        per_file[sql_file.name] = physical_tables

    return {
        'tables': sorted(all_tables - {t for t in all_tables if t.startswith('#')}),
        'temp_tables': sorted(t for t in all_tables if t.startswith('#')),
        'columns': sorted(all_columns),
        'per_file': per_file,
        'file_count': len(sql_files),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_referenced_tables.py path/to/sql/files/ [--csv output.csv]")
        sys.exit(1)

    # Parse args
    paths = []
    csv_output = None
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--csv' and i + 1 < len(sys.argv):
            csv_output = sys.argv[i + 1]
            i += 2
        else:
            paths.append(Path(sys.argv[i]))
            i += 1

    # Scan
    result = scan_sql_files(paths)

    # Report
    print(f"Scanned {result['file_count']} SQL files\n")

    print(f"{'=' * 60}")
    print(f"PHYSICAL TABLES ({len(result['tables'])} unique)")
    print(f"{'=' * 60}")
    for t in result['tables']:
        # Count how many files reference this table
        file_count = sum(1 for files in result['per_file'].values() if t in files)
        print(f"  {t} (used in {file_count} files)")

    print(f"\n{'=' * 60}")
    print(f"TEMP TABLES ({len(result['temp_tables'])} unique)")
    print(f"{'=' * 60}")
    for t in result['temp_tables']:
        print(f"  {t}")

    print(f"\n{'=' * 60}")
    print(f"COLUMNS ({len(result['columns'])} unique table.column pairs)")
    print(f"{'=' * 60}")
    # Group by table/alias
    by_table = {}
    for table, col in result['columns']:
        by_table.setdefault(table, set()).add(col)
    for table in sorted(by_table.keys()):
        cols = sorted(by_table[table])
        print(f"\n  {table}:")
        for col in cols[:20]:
            print(f"    .{col}")
        if len(cols) > 20:
            print(f"    ... and {len(cols) - 20} more")

    # CSV output
    if csv_output:
        with open(csv_output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['table_name', 'column_name', 'file_count'])
            for t in result['tables']:
                file_count = sum(1 for files in result['per_file'].values() if t in files)
                writer.writerow([t, '', file_count])
            for table, col in result['columns']:
                writer.writerow([table, col, ''])
        print(f"\nSaved to {csv_output}")

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  SQL files scanned:  {result['file_count']}")
    print(f"  Physical tables:    {len(result['tables'])}")
    print(f"  Temp tables:        {len(result['temp_tables'])}")
    print(f"  Column references:  {len(result['columns'])}")
    print(f"\nExport these {len(result['tables'])} tables from your data dictionary.")


if __name__ == "__main__":
    main()
