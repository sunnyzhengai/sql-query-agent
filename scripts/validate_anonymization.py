"""
Validate integrity of anonymized synthetic data.

Checks:
1. SQL → Dictionary: Every table referenced in SQL exists in dict_tables
2. Dictionary → SQL: Every dict_tables entry is used in at least one SQL file
3. dict_tables → dict_columns: Every table has columns defined
4. dict_columns → dict_tables: No orphan column entries
5. Proc names: CREATE PROCEDURE name matches the filename
6. Cross-references: Table names in SQL match dictionary exactly (case-sensitive)
7. Proprietary term scan: Deep scan for any remaining vendor/org terms
8. SQL parsability: Basic syntax checks (balanced parens, BEGIN/END)

Usage:
    python scripts/validate_anonymization.py
"""

import csv
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "data" / "synthetic" / "sql"
DICT_TABLES = PROJECT_ROOT / "data" / "synthetic" / "dict_tables.csv"
DICT_COLUMNS = PROJECT_ROOT / "data" / "synthetic" / "dict_columns.csv"

# Comprehensive list of proprietary terms to scan for
PROPRIETARY_TERMS = [
    # Vendor products
    "Epic", "Clarity", "Caboodle", "Hyperspace", "EpicCare", "EpicWeb",
    "EpicEurope",
    # Org names
    "Cook Children", "Cook_", "CookClarity", "CookCDW", "CDWPRD",
    "CCMC", "PCCMC", "CCHCS", "CCHP",
    "cookchildrens",
    # Schemas
    "COOK_RPT", "EPIC_UTIL", "EFN_DIN",
    # Prefixes in identifiers
    "IPSO_",
    # People
    "Shiva Peddibhotla", "Eric Tong", "Heidi Dammen", "GHANASHYAM",
    "V_OGSP8451", "V_TSET8589", "VODBP1980", "Ma020294", "He023165",
    "Stephanie Lavin",
    # Tickets
    "ZD#", "ZD #", "RITM0",
]

# Terms that are OK in column names (not in descriptions/SQL)
COLUMN_NAME_EXCEPTIONS = [
    "INTERNAL_DAT", "INTERNAL_DTE", "INTERNAL_PAT_ID", "INTERNAL_EMP_ID",
    "INTERNAL_PROV_ID", "CLINICAL_PAT_YN", "CLINICAL_PROV_YN",
]


class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def ok(self, msg: str):
        self.info.append(msg)

    def print_summary(self):
        print(f"\n{'=' * 60}")
        print("VALIDATION RESULTS")
        print(f"{'=' * 60}")
        print(f"  Passed: {len(self.info)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Errors: {len(self.errors)}")

        if self.warnings:
            print("\n--- WARNINGS ---")
            for w in self.warnings:
                print(f"  ⚠ {w}")

        if self.errors:
            print("\n--- ERRORS ---")
            for e in self.errors:
                print(f"  ✗ {e}")

        if not self.errors and not self.warnings:
            print("\n  All checks passed.")


def load_dict_tables() -> dict[str, str]:
    """Load dict_tables.csv → {TABLE_NAME: DESCRIPTION}"""
    tables = {}
    with open(DICT_TABLES, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tables[row["TABLE_NAME"].strip()] = row["DESCRIPTION"].strip()
    return tables


def load_dict_columns() -> dict[str, list[str]]:
    """Load dict_columns.csv → {TABLE_NAME: [COLUMN_NAME, ...]}"""
    columns: dict[str, list[str]] = {}
    with open(DICT_COLUMNS, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            table = row["TABLE_NAME"].strip()
            col = row["COLUMN_NAME"].strip()
            columns.setdefault(table, []).append(col)
    return columns


def extract_tables_from_sql(sql: str) -> set[str]:
    """Extract table names referenced in SQL (FROM, JOIN, INTO targets)."""
    tables = set()
    # Match table references after FROM, JOIN, INTO (with optional schema prefix)
    # Handles: [schema].[table], schema.table, table
    patterns = [
        r'(?:FROM|JOIN|INTO|TRUNCATE\s+TABLE|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+'
        r'(?:\[?\w+\]?\.)?\[?(\w+)\]?',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, sql, re.IGNORECASE):
            name = m.group(1)
            # Skip temp tables and common keywords
            if name.startswith("#") or name.upper() in (
                "SET", "BEGIN", "END", "SELECT", "WHERE", "AND", "OR",
                "CASE", "WHEN", "THEN", "ELSE", "AS", "ON", "NULL",
                "NOT", "EXISTS", "IN", "IS", "LIKE", "BETWEEN",
                "TOP", "DISTINCT", "TABLE", "VIEW", "PROCEDURE",
            ):
                continue
            tables.add(name)
    return tables


def extract_proc_name_from_sql(sql: str):
    """Extract the proc name from CREATE PROCEDURE statement."""
    m = re.search(
        r'CREATE\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+'
        r'(?:\[?\w+\]?\.)?\[?(\w+)\]?',
        sql, re.IGNORECASE,
    )
    return m.group(1) if m else None


def check_sql_to_dict(result: ValidationResult):
    """Check 1: Every table in SQL exists in dictionary."""
    dict_tables = load_dict_tables()
    dict_table_upper = {t.upper(): t for t in dict_tables}

    sql_files = sorted(SQL_DIR.rglob("*.sql"))
    all_sql_tables: set[str] = set()
    missing_by_file: dict[str, list[str]] = {}

    for sql_file in sql_files:
        sql = sql_file.read_text(encoding="utf-8")
        tables = extract_tables_from_sql(sql)
        all_sql_tables.update(tables)

        for t in tables:
            if t.upper() not in dict_table_upper:
                missing_by_file.setdefault(str(sql_file.relative_to(SQL_DIR)), []).append(t)

    if missing_by_file:
        for f, tables in sorted(missing_by_file.items()):
            unique = sorted(set(tables))
            result.warn(f"SQL→Dict: {f} references tables not in dictionary: {', '.join(unique)}")
    else:
        result.ok(f"SQL→Dict: All {len(all_sql_tables)} SQL table references found in dictionary")


def check_dict_to_sql(result: ValidationResult):
    """Check 2: Every dict_tables entry is used in at least one SQL file."""
    dict_tables = load_dict_tables()

    # Read all SQL content
    all_sql = ""
    for sql_file in SQL_DIR.rglob("*.sql"):
        all_sql += sql_file.read_text(encoding="utf-8") + "\n"
    all_sql_upper = all_sql.upper()

    unused = []
    for table_name in dict_tables:
        if table_name.upper() not in all_sql_upper:
            unused.append(table_name)

    if unused:
        result.warn(f"Dict→SQL: {len(unused)} dictionary tables not referenced in any SQL: "
                    f"{', '.join(sorted(unused)[:10])}{'...' if len(unused) > 10 else ''}")
    else:
        result.ok(f"Dict→SQL: All {len(dict_tables)} dictionary tables referenced in SQL")


def check_tables_have_columns(result: ValidationResult):
    """Check 3: Every dict_tables entry has columns in dict_columns."""
    dict_tables = load_dict_tables()
    dict_columns = load_dict_columns()

    no_columns = [t for t in dict_tables if t not in dict_columns]

    if no_columns:
        result.warn(f"Tables→Columns: {len(no_columns)} tables have no columns: {', '.join(sorted(no_columns)[:10])}")
    else:
        result.ok(f"Tables→Columns: All {len(dict_tables)} tables have column entries")


def check_columns_have_tables(result: ValidationResult):
    """Check 4: Every dict_columns table exists in dict_tables."""
    dict_tables = load_dict_tables()
    dict_columns = load_dict_columns()

    orphan_tables = [t for t in dict_columns if t not in dict_tables]

    if orphan_tables:
        result.error(f"Columns→Tables: {len(orphan_tables)} column tables not in dict_tables: "
                     f"{', '.join(sorted(orphan_tables))}")
    else:
        result.ok("Columns→Tables: All column entries have matching table entries")


def check_proc_names_match_files(result: ValidationResult):
    """Check 5: CREATE PROCEDURE name matches the filename."""
    mismatches = []
    for sql_file in sorted(SQL_DIR.rglob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        proc_name = extract_proc_name_from_sql(sql)
        file_stem = sql_file.stem

        if proc_name and proc_name.upper() != file_stem.upper():
            mismatches.append(f"{sql_file.name}: CREATE PROCEDURE [{proc_name}] != filename [{file_stem}]")

    if mismatches:
        for m in mismatches:
            result.error(f"Proc→File: {m}")
    else:
        result.ok("Proc→File: All proc names match filenames")


def check_proprietary_terms_sql(result: ValidationResult):
    """Check 6: Scan SQL files for remaining proprietary terms."""
    hits = []
    for sql_file in sorted(SQL_DIR.rglob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        for term in PROPRIETARY_TERMS:
            matches = list(re.finditer(re.escape(term), sql, re.IGNORECASE))
            for m in matches:
                start = max(0, m.start() - 20)
                end = min(len(sql), m.end() + 20)
                context = sql[start:end].replace("\n", " ").strip()
                hits.append(f"{sql_file.name}: '{term}' → ...{context}...")

    if hits:
        for h in hits[:20]:
            result.error(f"Proprietary: {h}")
        if len(hits) > 20:
            result.error(f"Proprietary: ... and {len(hits) - 20} more")
    else:
        result.ok("Proprietary: No vendor/org terms found in SQL files")


def check_proprietary_terms_dict(result: ValidationResult):
    """Check 7: Scan dictionary files for remaining proprietary terms."""
    hits = []
    for dict_file in [DICT_TABLES, DICT_COLUMNS]:
        content = dict_file.read_text(encoding="utf-8")
        for term in PROPRIETARY_TERMS:
            if term in ["Epic", "Clarity"]:
                # More specific matching to avoid false positives in anonymized names
                matches = list(re.finditer(r"\b" + re.escape(term) + r"\b", content))
            else:
                matches = list(re.finditer(re.escape(term), content, re.IGNORECASE))
            for m in matches:
                start = max(0, m.start() - 30)
                end = min(len(content), m.end() + 30)
                context = content[start:end].replace("\n", " ").strip()
                hits.append(f"{dict_file.name}: '{term}' → ...{context}...")

    if hits:
        for h in hits[:20]:
            result.error(f"Dict Proprietary: {h}")
        if len(hits) > 20:
            result.error(f"Dict Proprietary: ... and {len(hits) - 20} more")
    else:
        result.ok("Dict Proprietary: No vendor/org terms found in dictionary files")


def check_sql_syntax(result: ValidationResult):
    """Check 8: Basic SQL syntax validation."""
    issues = []
    for sql_file in sorted(SQL_DIR.rglob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        name = sql_file.name

        # Check balanced parentheses
        open_count = sql.count("(")
        close_count = sql.count(")")
        if open_count != close_count:
            issues.append(f"{name}: Unbalanced parentheses (open={open_count}, close={close_count})")

        # Check BEGIN/END balance (approximate — skip strings/comments)
        begins = len(re.findall(r"\bBEGIN\b", sql, re.IGNORECASE))
        ends = len(re.findall(r"\bEND\b", sql, re.IGNORECASE))
        # END can appear in CASE...END too, so just flag gross mismatches
        if abs(begins - ends) > 2:
            issues.append(f"{name}: BEGIN/END mismatch (BEGIN={begins}, END={ends})")

        # Check CREATE PROCEDURE exists
        if not re.search(r"CREATE\s+", sql, re.IGNORECASE):
            issues.append(f"{name}: No CREATE statement found")

    if issues:
        for i in issues:
            result.warn(f"Syntax: {i}")
    else:
        result.ok(f"Syntax: All {len(list(SQL_DIR.rglob('*.sql')))} SQL files pass basic syntax checks")


def check_table_name_consistency(result: ValidationResult):
    """Check 9: Table names used consistently across SQL and dictionary."""
    dict_tables = load_dict_tables()

    # Build case-sensitive set of dictionary table names
    dict_names = set(dict_tables.keys())

    # Find all table references in SQL with their exact casing
    case_issues = []
    for sql_file in sorted(SQL_DIR.rglob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        tables = extract_tables_from_sql(sql)
        for t in tables:
            # Check if table exists in dict but with different casing
            matches = [d for d in dict_names if d.upper() == t.upper()]
            if matches and t not in matches:
                case_issues.append(f"{sql_file.name}: SQL uses '{t}' but dict has '{matches[0]}'")

    if case_issues:
        unique_issues = sorted(set(case_issues))
        for i in unique_issues[:15]:
            result.warn(f"Case: {i}")
        if len(unique_issues) > 15:
            result.warn(f"Case: ... and {len(unique_issues) - 15} more")
    else:
        result.ok("Case: Table name casing consistent between SQL and dictionary")


def main():
    result = ValidationResult()

    print("Validating anonymized synthetic data...")
    print(f"SQL dir:      {SQL_DIR}")
    print(f"dict_tables:  {DICT_TABLES}")
    print(f"dict_columns: {DICT_COLUMNS}")

    sql_count = len(list(SQL_DIR.rglob("*.sql")))
    dict_tables = load_dict_tables()
    dict_columns = load_dict_columns()
    total_cols = sum(len(v) for v in dict_columns.values())

    print(f"\nFiles: {sql_count} SQL, {len(dict_tables)} tables, {total_cols} columns\n")

    check_sql_to_dict(result)
    check_dict_to_sql(result)
    check_tables_have_columns(result)
    check_columns_have_tables(result)
    check_proc_names_match_files(result)
    check_table_name_consistency(result)
    check_proprietary_terms_sql(result)
    check_proprietary_terms_dict(result)
    check_sql_syntax(result)

    result.print_summary()

    sys.exit(1 if result.errors else 0)


if __name__ == "__main__":
    main()
