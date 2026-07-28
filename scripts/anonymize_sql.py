"""
Anonymize SQL files using the master crosswalk.

Reads SQL files from data/synthetic/sepsis_sql/procs/,
applies all replacements from data/synthetic/crosswalk.json,
writes anonymized files to data/synthetic/sql/.

Usage:
    python scripts/anonymize_sql.py
    python scripts/anonymize_sql.py --dry-run     # preview without writing
    python scripts/anonymize_sql.py --verbose      # show each replacement
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "data" / "synthetic" / "sepsis_sql" / "procs"
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic" / "sql"
CROSSWALK_PATH = PROJECT_ROOT / "data" / "synthetic" / "crosswalk.json"


def load_crosswalk() -> dict:
    with open(CROSSWALK_PATH) as f:
        return json.load(f)


def build_replacements(crosswalk: dict) -> list[tuple[str, str, str]]:
    """Build ordered list of (pattern, replacement, category) tuples.

    Order matters — longer/more-specific patterns first to avoid
    partial matches (e.g., 'CookClarity' before 'Clarity').
    """
    replacements: list[tuple[str, str, str]] = []

    # --- 1. Vendor functions (most specific, multi-part names) ---
    for orig, anon in crosswalk.get("vendor_functions", {}).items():
        replacements.append((orig, anon, "vendor_function"))

    # --- 2. Procedure CREATE statements (schema.proc_name) ---
    for key, entry in crosswalk.get("procedures", {}).items():
        if isinstance(entry, dict) and "original" in entry:
            replacements.append((entry["original"], entry["anonymized"], "procedure"))
            # Also handle without brackets and with varied casing
            orig_bare = entry["original"].replace("[", "").replace("]", "")
            anon_bare = entry["anonymized"].replace("[", "").replace("]", "")
            if orig_bare != entry["original"]:
                replacements.append((orig_bare, anon_bare, "procedure_bare"))

    # --- 3. Department names (before prefix patterns — more specific) ---
    for orig, anon in crosswalk.get("org_references_to_remove", {}).get("department_names", {}).items():
        replacements.append((orig, anon, "department_name"))

    # --- 4. File paths ---
    for orig, anon in crosswalk.get("org_references_to_remove", {}).get("file_paths", {}).items():
        replacements.append((orig, anon, "file_path"))

    # --- 5. Report paths ---
    for orig, anon in crosswalk.get("org_references_to_remove", {}).get("report_paths", {}).items():
        replacements.append((orig, anon, "report_path"))

    # --- 6. Org-specific tables (before databases/schemas — contain org prefixes) ---
    # Mark with ~ci suffix for case-insensitive matching
    for orig, anon in crosswalk.get("tables", {}).get("_org_specific_tables", {}).items():
        replacements.append((orig, anon, "org_table~ci"))

    # --- 7. EMR tables ---
    for orig, anon in crosswalk.get("tables", {}).get("_emr_tables", {}).items():
        if orig != anon:
            replacements.append((orig, anon, "emr_table~ci"))

    # --- 8. Databases (longer names first) ---
    db_items = sorted(crosswalk.get("databases", {}).items(), key=lambda x: -len(x[0]))
    for orig, anon in db_items:
        if orig != anon:
            replacements.append((orig, anon, "database"))

    # --- 9. Schemas (longer names first) ---
    schema_items = sorted(crosswalk.get("schemas", {}).items(), key=lambda x: -len(x[0]))
    for orig, anon in schema_items:
        if orig != anon:
            replacements.append((orig, anon, "schema"))

    # --- 10. Author names (longer names first to avoid partial) ---
    author_items = sorted(crosswalk.get("author_names", {}).items(), key=lambda x: -len(x[0]))
    for orig, anon in author_items:
        replacements.append((orig, anon, "author"))

    # --- 11. Ticket numbers ---
    for orig, anon in crosswalk.get("ticket_numbers", {}).items():
        replacements.append((orig, anon, "ticket"))

    # --- 12. String literals ---
    lit_items = sorted(
        crosswalk.get("org_references_to_remove", {}).get("string_literals", {}).items(),
        key=lambda x: -len(x[0]),
    )
    for orig, anon in lit_items:
        replacements.append((orig, anon, "string_literal"))

    # --- 13. Grouper name prefixes ---
    for orig, anon in crosswalk.get("org_references_to_remove", {}).get("grouper_name_prefixes", {}).items():
        replacements.append((orig, anon, "grouper_prefix"))

    # --- 14. Prefix patterns (shorter, more generic — last among text) ---
    prefix_items = sorted(
        crosswalk.get("org_references_to_remove", {}).get("prefix_patterns", {}).items(),
        key=lambda x: -len(x[0]),
    )
    for orig, anon in prefix_items:
        replacements.append((orig, anon, "prefix_pattern"))

    # --- 15. COOK_FY column renames ---
    for orig, anon in crosswalk.get("cook_fy_columns_to_rename", {}).items():
        replacements.append((orig, anon, "cook_fy_column"))

    # --- 16. Proc codes ---
    proc_code_items = sorted(crosswalk.get("proc_codes", {}).items(), key=lambda x: -len(x[0]))
    for orig, anon in proc_code_items:
        replacements.append((orig, anon, "proc_code"))

    # --- 17. Hardcoded IDs (all categories) ---
    for id_category, mapping in crosswalk.get("hardcoded_ids", {}).items():
        if not isinstance(mapping, dict) or id_category.startswith("_"):
            continue
        # Sort by length descending to avoid partial matches (e.g., '100108' before '1001')
        id_items = sorted(mapping.items(), key=lambda x: -len(x[0]))
        for orig, anon in id_items:
            if orig != anon:
                replacements.append((orig, anon, f"id:{id_category}"))

    return replacements


def apply_replacements(
    sql: str,
    replacements: list[tuple[str, str, str]],
    verbose: bool = False,
) -> tuple[str, list[str]]:
    """Apply all replacements to SQL text. Returns (anonymized_sql, log_entries)."""
    log = []

    for orig, anon, category in replacements:
        use_ci = category.endswith("~ci")
        use_word_boundary = category.startswith("id:")
        base_category = category.removesuffix("~ci")

        if use_ci:
            # Case-insensitive regex replacement with word boundaries
            # Use \b to avoid replacing inside other words (e.g., "patients" for "PATIENT")
            pattern = re.compile(r"\b" + re.escape(orig) + r"\b", re.IGNORECASE)
            matches = pattern.findall(sql)
            if not matches:
                continue
            count = len(matches)
            sql = pattern.sub(anon, sql)
        elif use_word_boundary:
            # Word-boundary matching for numeric IDs to avoid partial matches
            # Use lookahead/lookbehind for non-digit boundaries
            pattern = re.compile(r"(?<!\d)" + re.escape(orig) + r"(?!\d)")
            matches = pattern.findall(sql)
            if not matches:
                continue
            count = len(matches)
            sql = pattern.sub(anon, sql)
        else:
            if orig not in sql:
                continue
            count = sql.count(orig)
            sql = sql.replace(orig, anon)

        entry = f"  [{base_category}] {orig!r} -> {anon!r} ({count}x)"
        log.append(entry)
        if verbose:
            print(entry)

    return sql, log


def scan_for_missed(sql: str, crosswalk: dict) -> list[str]:
    """Check anonymized SQL for any remaining proprietary terms."""
    warnings = []

    # Check for remaining org references
    org_terms = [
        "Cook", "CCMC", "PCCMC", "CCHCS", "CCHP",
        "Clarity", "CookClarity", "COOK_RPT", "EPIC_UTIL",
        "EFN_DIN", "IPSO_",
    ]
    for term in org_terms:
        # Case-insensitive search, but skip if it's inside an anonymized name
        matches = [m for m in re.finditer(re.escape(term), sql, re.IGNORECASE)]
        for m in matches:
            # Get surrounding context
            start = max(0, m.start() - 30)
            end = min(len(sql), m.end() + 30)
            context = sql[start:end].replace("\n", " ").strip()
            warnings.append(f"  MISSED: '{term}' found in: ...{context}...")

    return warnings


def process_file(
    input_path: Path,
    replacements: list[tuple[str, str, str]],
    crosswalk: dict,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Process a single SQL file. Returns stats dict."""
    sql = input_path.read_text(encoding="utf-8-sig")

    anonymized, log = apply_replacements(sql, replacements, verbose)
    output_path = get_output_path(input_path, crosswalk, anonymized)
    warnings = scan_for_missed(anonymized, crosswalk)

    stats = {
        "file": str(input_path.relative_to(INPUT_DIR)),
        "output": str(output_path.relative_to(OUTPUT_DIR)),
        "replacements": len(log),
        "warnings": len(warnings),
        "warning_details": warnings,
    }

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(anonymized, encoding="utf-8")

    return stats


def get_output_path(input_path: Path, crosswalk: dict, anonymized_sql: str) -> Path:
    """Determine output path based on the anonymized CREATE PROCEDURE name."""
    rel = input_path.relative_to(INPUT_DIR)
    schema_folder = rel.parts[0]  # 'reporting' or 'reports'

    # Extract proc name from the anonymized SQL
    m = re.search(
        r"CREATE\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+"
        r"(?:\[?\w+\]?\.)?\[?(\w+)\]?",
        anonymized_sql, re.IGNORECASE,
    )
    if m:
        proc_name = m.group(1)
        return OUTPUT_DIR / schema_folder / f"{proc_name}.sql"

    # Fallback: use input filename
    filename = rel.parts[-1]
    if not filename.endswith(".sql"):
        filename += ".sql"
    return OUTPUT_DIR / schema_folder / filename


def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv

    if dry_run:
        print("=== DRY RUN — no files will be written ===\n")

    crosswalk = load_crosswalk()
    replacements = build_replacements(crosswalk)

    print(f"Loaded {len(replacements)} replacement rules from crosswalk")
    print(f"Input:  {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}\n")

    # Find all SQL files (with or without .sql extension)
    input_files = sorted(
        p for p in INPUT_DIR.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    )

    print(f"Found {len(input_files)} files to process\n")

    total_replacements = 0
    total_warnings = 0
    all_warnings = []

    for input_path in input_files:
        if verbose:
            print(f"\n--- {input_path.relative_to(INPUT_DIR)} ---")

        stats = process_file(
            input_path, replacements, crosswalk,
            dry_run=dry_run, verbose=verbose,
        )

        status = "OK" if stats["warnings"] == 0 else f"WARN({stats['warnings']})"
        print(f"  {status} {stats['file']} -> {stats['output']} ({stats['replacements']} replacements)")

        total_replacements += stats["replacements"]
        total_warnings += stats["warnings"]
        if stats["warnings"] > 0:
            all_warnings.append((stats["file"], stats["warning_details"]))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Files processed: {len(input_files)}")
    print(f"Total replacements: {total_replacements}")
    print(f"Total warnings: {total_warnings}")

    if all_warnings:
        print(f"\n{'=' * 60}")
        print("WARNINGS — Possible missed proprietary terms:\n")
        for filename, details in all_warnings:
            print(f"  {filename}:")
            for d in details:
                print(f"    {d}")

    if dry_run:
        print("\n=== DRY RUN complete — no files were written ===")
    else:
        print(f"\nAnonymized files written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
