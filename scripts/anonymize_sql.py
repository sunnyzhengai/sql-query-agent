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

sys.path.insert(0, str(PROJECT_ROOT))


from src.anonymization import (  # noqa: E402
    apply_replacements,
    build_replacements,
    get_scan_terms,
    scan_for_missed,
)


def load_crosswalk() -> dict:
    with open(CROSSWALK_PATH) as f:
        return json.load(f)


# Dev-only scan list (this script is not shipped); crosswalk _scan_terms wins.
LEGACY_SCAN_TERMS = [
    "Cook", "CCMC", "PCCMC", "CCHCS", "CCHP",
    "Clarity", "CookClarity", "COOK_RPT", "EPIC_UTIL",
    "EFN_DIN", "IPSO_",
]


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
    warnings = scan_for_missed(anonymized, get_scan_terms(crosswalk, LEGACY_SCAN_TERMS))

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
