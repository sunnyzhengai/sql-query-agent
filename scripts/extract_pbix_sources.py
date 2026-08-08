#!/usr/bin/env python3
"""Extract stored procedure/view calls from Power BI (.pbix) files.

Parses the DataMashup inside .pbix files to find SQL execution calls
like EXEC USP_*, Sql.Database queries, and Value.NativeQuery calls.

Usage:
    # Single file:
    python scripts/extract_pbix_sources.py report.pbix

    # Folder of .pbix files:
    python scripts/extract_pbix_sources.py path/to/pbix/folder/

    # Save results to CSV:
    python scripts/extract_pbix_sources.py path/to/folder/ --csv output.csv
"""

from __future__ import annotations

import csv
import io
import re
import sys
import zipfile
from pathlib import Path


def extract_m_queries_from_pbix(pbix_path: str | Path) -> list[dict]:
    """Extract Power Query M code from a .pbix file.

    A .pbix file is a ZIP archive containing a DataMashup file,
    which holds the M query definitions including SQL connections.

    Returns list of dicts with keys: report_name, query_name, m_code, sql_source
    """
    pbix_path = Path(pbix_path)
    report_name = pbix_path.stem
    results = []

    try:
        with zipfile.ZipFile(pbix_path, 'r') as z:
            # Find the DataMashup file
            datamashup_names = [n for n in z.namelist() if 'DataMashup' in n]
            if not datamashup_names:
                print(f"  No DataMashup found in {report_name}")
                return results

            for dm_name in datamashup_names:
                dm_bytes = z.read(dm_name)

                # DataMashup is itself a ZIP-like structure
                # Try to extract M code from it
                m_queries = _extract_m_from_datamashup(dm_bytes)

                for query_name, m_code in m_queries:
                    sql_source = _find_sql_source(m_code)
                    results.append({
                        "report_name": report_name,
                        "query_name": query_name,
                        "m_code": m_code,
                        "sql_source": sql_source,
                    })

    except zipfile.BadZipFile:
        print(f"  {report_name}: Not a valid ZIP/PBIX file")
    except Exception as e:
        print(f"  {report_name}: Error: {e}")

    return results


def _extract_m_from_datamashup(dm_bytes: bytes) -> list[tuple[str, str]]:
    """Extract M query text from DataMashup binary.

    The DataMashup contains a nested ZIP with Section1.m or
    similar files containing the Power Query M code.
    """
    queries = []

    # Try to read DataMashup as a nested ZIP
    try:
        with zipfile.ZipFile(io.BytesIO(dm_bytes), 'r') as inner_z:
            for name in inner_z.namelist():
                if name.endswith('.m') or 'Section1' in name or 'Formulas' in name:
                    content = inner_z.read(name).decode('utf-8', errors='replace')
                    # Parse individual queries from Section1.m
                    parsed = _parse_section_m(content)
                    queries.extend(parsed)
                    if not parsed:
                        queries.append(("_raw_", content))
    except zipfile.BadZipFile:
        # DataMashup might not be a ZIP — try to extract M code from raw bytes
        text = dm_bytes.decode('utf-8', errors='replace')
        # Look for M code patterns in the raw binary
        m_fragments = _extract_m_from_raw(text)
        queries.extend(m_fragments)

    return queries


def _parse_section_m(content: str) -> list[tuple[str, str]]:
    """Parse Section1.m file into individual named queries.

    Format:
        shared QueryName = let
            Source = ...
        in
            Result;
    """
    queries = []

    # Pattern: shared <name> = <expression>;
    pattern = r'shared\s+([\w#"]+)\s*=\s*(.*?)(?=\nshared\s|\Z)'
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1).strip('"#')
        code = match.group(2).strip().rstrip(';')
        if len(code) > 10:  # Skip trivial entries
            queries.append((name, code))

    # If no shared blocks found, return the whole content
    if not queries and len(content) > 20:
        queries.append(("_section_", content))

    return queries


def _extract_m_from_raw(text: str) -> list[tuple[str, str]]:
    """Extract M code fragments from raw binary text.

    When DataMashup isn't a proper ZIP, search for M code patterns.
    """
    queries = []

    # Look for Sql.Database calls
    for match in re.finditer(r'(Sql\.Database\([^)]+\)[^;]*)', text):
        queries.append(("_sql_db_", match.group(1)))

    # Look for Value.NativeQuery calls
    for match in re.finditer(r'(Value\.NativeQuery\([^)]+\))', text):
        queries.append(("_native_query_", match.group(1)))

    # Look for EXEC patterns in any text
    for match in re.finditer(r'(EXEC\s+\[?\w+\]?\.\[?\w+\]?\.\[?\w+\]?[^"]*)', text, re.IGNORECASE):
        queries.append(("_exec_", match.group(1)[:200]))

    return queries


def _find_sql_source(m_code: str) -> str | None:
    """Find SQL stored procedure or view reference in M code.

    Looks for patterns like:
    - EXEC [schema].[USP_Name]
    - EXEC schema.USP_Name
    - Sql.Database("server", "db", [Query="EXEC ..."])
    - Value.NativeQuery(..., "EXEC ...")
    - FROM [schema].[view_name]
    """
    # EXEC stored procedure calls
    exec_match = re.search(
        r'EXEC\s+(?:\[?\w+\]?\.)?(?:\[?\w+\]?\.)?\[?(\w+)\]?',
        m_code, re.IGNORECASE
    )
    if exec_match:
        return f"EXEC {exec_match.group(1)}"

    # Sql.Database with Query parameter
    query_match = re.search(
        r'Query\s*=\s*"([^"]*)"',
        m_code, re.IGNORECASE
    )
    if query_match:
        sql = query_match.group(1)
        # Extract proc name from the SQL
        exec_in_query = re.search(r'EXEC\s+(?:\[?\w+\]?\.)*\[?(\w+)\]?', sql, re.IGNORECASE)
        if exec_in_query:
            return f"EXEC {exec_in_query.group(1)}"
        # Extract view/table name from SELECT FROM
        from_match = re.search(r'FROM\s+(?:\[?\w+\]?\.)*\[?(\w+)\]?', sql, re.IGNORECASE)
        if from_match:
            return f"FROM {from_match.group(1)}"
        return f"SQL: {sql[:100]}"

    # Value.NativeQuery
    native_match = re.search(
        r'Value\.NativeQuery\s*\([^,]+,\s*"([^"]*)"',
        m_code
    )
    if native_match:
        sql = native_match.group(1)
        exec_in_native = re.search(r'EXEC\s+(?:\[?\w+\]?\.)*\[?(\w+)\]?', sql, re.IGNORECASE)
        if exec_in_native:
            return f"EXEC {exec_in_native.group(1)}"
        return f"NativeQuery: {sql[:100]}"

    # Direct table/view reference: Sql.Database("server", "db") then {[Schema="x", Item="view"]}
    item_match = re.search(r'Item\s*=\s*"(\w+)"', m_code)
    schema_match = re.search(r'Schema\s*=\s*"(\w+)"', m_code)
    if item_match:
        schema = schema_match.group(1) if schema_match else "dbo"
        return f"FROM {schema}.{item_match.group(1)}"

    return None


def scan_pbix_files(paths: list[Path]) -> list[dict]:
    """Scan .pbix files and extract SQL source definitions."""
    all_results = []
    pbix_files = []

    for p in paths:
        if p.is_file() and p.suffix.lower() == '.pbix':
            pbix_files.append(p)
        elif p.is_dir():
            pbix_files.extend(p.rglob('*.pbix'))

    print(f"Found {len(pbix_files)} .pbix files\n")

    for pbix in sorted(pbix_files):
        print(f"Processing: {pbix.name}")
        results = extract_m_queries_from_pbix(pbix)
        sql_sources = [r for r in results if r['sql_source']]
        if sql_sources:
            for r in sql_sources:
                print(f"  → {r['sql_source']}")
                all_results.append(r)
        else:
            print("  (no SQL source found)")
            # Still add with None sql_source for reporting
            for r in results:
                all_results.append(r)

    return all_results


def friendly_name_from_report(report_name: str) -> str:
    """Report filename -> business-friendly display name.

    'IP_Sepsis_Compliance_Dashboard' -> 'IP Sepsis Compliance Dashboard'.
    Purely mechanical (separators to spaces, collapse whitespace) — no
    vocabulary invention; the report author chose these words.
    """
    return " ".join(re.split(r"[_\-]+", report_name)).strip()


def build_metric_name_records(results: "list[dict]") -> "list[dict]":
    """input_metric_names rows from scan results: one row per SQL source.

    A proc feeding multiple reports keeps the FIRST report's name and
    lists the rest in report_name for steward review — one business name
    per metric (the input_metric_names unique invariant), no guessing
    about which report is canonical.
    """
    by_source: "dict[str, list[str]]" = {}
    for r in results:
        if r.get("sql_source"):
            # sql_source carries an access-verb prefix ("EXEC USP_X",
            # "FROM schema.view") — strip it down to the object reference
            # so it fold-matches metric_ids (raw SQL: fragments are skipped)
            m = re.match(r"(?:EXEC|FROM)\s+([\w.]+)$", r["sql_source"], re.IGNORECASE)
            if not m:
                continue
            by_source.setdefault(m.group(1), []).append(r["report_name"])
    records = []
    for source, reports in sorted(by_source.items()):
        records.append({
            "metric_id": source,
            "business_name": friendly_name_from_report(reports[0]),
            "source": "pbi_report",
            "report_name": "; ".join(dict.fromkeys(reports)),
            "report_url": "",  # fill from the workspace (app.powerbi.com link)
            "assigned_date": "",
        })
    return records


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_pbix_sources.py <path_to_pbix_or_folder> "
              "[--csv output.csv] [--names-csv input_metric_names.csv]")
        sys.exit(1)

    paths = []
    csv_output = None
    names_csv = None
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--csv' and i + 1 < len(sys.argv):
            csv_output = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--names-csv' and i + 1 < len(sys.argv):
            names_csv = sys.argv[i + 1]
            i += 2
        else:
            paths.append(Path(sys.argv[i]))
            i += 1

    results = scan_pbix_files(paths)

    # Summary
    with_source = [r for r in results if r['sql_source']]
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Reports processed: {len(set(r['report_name'] for r in results))}")
    print(f"  Queries found:     {len(results)}")
    print(f"  With SQL source:   {len(with_source)}")

    if with_source:
        print("\n  SQL Sources found:")
        for r in with_source:
            print(f"    {r['report_name']} → {r['sql_source']}")

    if csv_output:
        with open(csv_output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['report_name', 'query_name', 'sql_source', 'm_code'])
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print(f"\n  Saved to {csv_output}")

    if names_csv:
        records = build_metric_name_records(results)
        with open(names_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'metric_id', 'business_name', 'source', 'report_name', 'report_url', 'assigned_date',
            ])
            writer.writeheader()
            for r in records:
                writer.writerow(r)
        print(f"  Saved {len(records)} business-name mappings to {names_csv} "
              f"(upload as input_metric_names)")


if __name__ == "__main__":
    main()
