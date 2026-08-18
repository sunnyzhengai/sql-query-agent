"""Supplemental stub tables: everything the corpus REFERENCES that the
lineage-derived seed missed (write-targets, suppressed extractions).

The first seed built stubs from recorded parse lineage — reads only.
The first live EXECs (PBI partitions, 2026-08-18) hit tables the
lineage never captured (dbo.MED_MIX_COMPONENTS et al). This scanner
works from the RAW corpus text instead: every FROM/JOIN/INSERT INTO/
UPDATE/MERGE/DELETE target that is not created by the corpus itself
and not already stubbed gets a stub, with columns harvested from
alias-scoped references and types inferred from usage (aggregate /
date-function args need real types even on empty tables — SUM(nvarchar)
fails at COMPILE time).

Output: data/demo/seed_demo_tables_supplement.sql
        (idempotent; GO after every statement; loud verification tail
        listing ANY referenced table still missing — run it, expect an
        empty result set).

Usage: python scripts/build_demo_stub_supplement.py
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "demo" / "seed_demo_source.sql"
SEED = REPO / "data" / "demo" / "seed_demo_tables.sql"
OUT = REPO / "data" / "demo" / "seed_demo_tables_supplement.sql"

KEYWORDS = {
    "SELECT", "WHERE", "GROUP", "ORDER", "INNER", "LEFT", "RIGHT", "FULL",
    "CROSS", "OUTER", "JOIN", "ON", "AND", "OR", "NOT", "AS", "CASE",
    "WHEN", "THEN", "ELSE", "END", "EXISTS", "VALUES", "DUAL", "OPENJSON",
    "STRING_SPLIT", "UNPIVOT", "PIVOT",
}


def _norm(schema: "str | None", name: str) -> str:
    return f"{(schema or 'dbo').strip('[]')}.{name.strip('[]')}".lower()


def strip_noise(sql: str) -> str:
    """Remove comments and string literals — both are full of words that
    pattern-match as table references (the first run caught 'dbo.the')."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"'(?:[^']|'')*'", "''", sql)
    return sql


def cte_names(sql: str) -> "set[str]":
    """CTE identifiers — referenced in FROM/JOIN but never real tables."""
    names: "set[str]" = set()
    for m in re.finditer(r"(?:\bWITH|,)\s*(\[?[A-Za-z_][\w]*\]?)\s+AS\s*\(",
                         sql, re.IGNORECASE):
        names.add(m.group(1).strip("[]").lower())
    return names


def referenced_tables(sql: str) -> "set[str]":
    sql = strip_noise(sql)
    ctes = cte_names(sql)
    refs: "set[str]" = set()
    pattern = re.compile(
        r"\b(?:FROM|JOIN|INTO|UPDATE|MERGE\s+INTO|DELETE\s+FROM)\s+"
        r"(\[?[A-Za-z_][\w]*\]?)(?:\s*\.\s*(\[?[A-Za-z_][\w]*\]?))?",
        re.IGNORECASE,
    )
    for m in pattern.finditer(sql):
        first, second = m.group(1), m.group(2)
        name = (second or first).strip("[]")
        schema = first.strip("[]") if second else "dbo"
        if name.startswith(("#", "@")) or name.upper() in KEYWORDS:
            continue
        if not second and name.lower() in ctes:
            continue  # CTE reference, not a table
        if schema.lower() in ("sys", "information_schema"):
            continue
        refs.add(_norm(schema, name))
    return refs


def created_objects(sql: str) -> "set[str]":
    out: "set[str]" = set()
    for m in re.finditer(
        r"CREATE\s+(?:OR\s+ALTER\s+)?(?:PROC(?:EDURE)?|VIEW|TABLE|FUNCTION)\s+"
        r"(\[?[A-Za-z_][\w]*\]?)(?:\s*\.\s*(\[?[A-Za-z_][\w]*\]?))?",
        sql, re.IGNORECASE,
    ):
        first, second = m.group(1), m.group(2)
        name = (second or first).strip("[]")
        schema = first.strip("[]") if second else "dbo"
        out.add(_norm(schema, name))
    return out


def alias_columns(sql: str, table_key: str) -> "set[str]":
    """Columns referenced through aliases of this table + INSERT lists."""
    schema, name = table_key.split(".")
    cols: "set[str]" = set()
    alias_pat = re.compile(
        rf"\b(?:FROM|JOIN)\s+\[?{schema}\]?\s*\.\s*\[?{name}\]?\s+"
        rf"(?:AS\s+)?(\[?[A-Za-z_][\w]*\]?)",
        re.IGNORECASE,
    )
    aliases = {m.group(1).strip("[]") for m in alias_pat.finditer(sql)}
    aliases -= {a for a in aliases if a.upper() in KEYWORDS}
    for alias in aliases:
        for m in re.finditer(rf"\b{re.escape(alias)}\s*\.\s*\[?([A-Za-z_][\w]*)\]?",
                             sql):
            cols.add(m.group(1))
    ins = re.search(
        rf"INSERT\s+INTO\s+\[?{schema}\]?\s*\.\s*\[?{name}\]?\s*\(([^)]*)\)",
        sql, re.IGNORECASE | re.DOTALL,
    )
    if ins:
        for c in ins.group(1).split(","):
            c = c.strip().strip("[]")
            if re.fullmatch(r"[A-Za-z_][\w]*", c):
                cols.add(c)
    return cols


def infer_type(sql: str, col: str) -> str:
    """Empty tables still COMPILE: aggregates and date functions need
    plausible types."""
    if re.search(rf"\b(?:SUM|AVG)\s*\(\s*[\w\[\]]*\.?\[?{re.escape(col)}\]?\s*[\)\+\-\*/]",
                 sql, re.IGNORECASE):
        return "DECIMAL(18,4)"
    if re.search(rf"DATE(?:DIFF|ADD|PART)\s*\([^)]*\b{re.escape(col)}\b",
                 sql, re.IGNORECASE) or re.search(
            r"DATE|TIME|DTTM|INSTANT|_DT\b", col, re.IGNORECASE):
        return "DATETIME2"
    if re.search(r"_ID$|_C$|_CODE$|COUNT$|_NUM$|LINE$", col, re.IGNORECASE):
        return "DECIMAL(18,4)"
    return "NVARCHAR(400)"


def main() -> None:
    corpus = CORPUS.read_text()
    seeded = created_objects(SEED.read_text())
    created = created_objects(corpus)
    missing = sorted(referenced_tables(corpus) - seeded - created)

    lines = [
        "-- Supplemental stubs: corpus-referenced tables the lineage seed",
        "-- missed (write-targets, suppressed extractions). Generated by",
        "-- scripts/build_demo_stub_supplement.py. Idempotent; GO-separated",
        "-- so one failure can NEVER silently kill the rest of the batch.",
        "",
    ]
    for key in missing:
        schema, name = key.split(".")
        cols = sorted(alias_columns(corpus, key)) or ["STUB_COL"]
        lines.append(f"IF OBJECT_ID('{schema}.{name}') IS NULL")
        lines.append(f"CREATE TABLE [{schema}].[{name}] (")
        body = [f"    [{c}] {infer_type(corpus, c)} NULL" for c in cols]
        lines.append(",\n".join(body))
        lines.append(");")
        lines.append("GO")
        lines.append("")

    # loud verification tail: EVERY corpus-referenced table, one probe —
    # run this and expect ZERO rows; each row names a missing table.
    every = sorted(referenced_tables(corpus) - created)
    lines.append("-- VERIFICATION: expect an EMPTY result. Each row = a")
    lines.append("-- referenced table still missing from this database.")
    lines.append("SELECT v.full_name AS missing_table FROM (VALUES")
    lines.append(",\n".join(f"    ('{k}')" for k in every))
    lines.append(") v(full_name) WHERE OBJECT_ID(v.full_name) IS NULL;")
    lines.append("GO")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"missing stubs generated: {len(missing)}")
    for k in missing:
        print("  ", k)
    print(f"verification probes: {len(every)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
