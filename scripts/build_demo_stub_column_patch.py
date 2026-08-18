"""Column patch for demo stubs: every column the corpus references on a
stubbed table that the stub doesn't carry (the dictionary is the stub's
source, and dictionaries lag code — 'Invalid column name VALUE_SET_ABBR',
2026-08-18).

Scans BOTH seed files' CREATE TABLE column lists, harvests alias-scoped
and INSERT-list column references per table from the noise-stripped
corpus, and emits idempotent ALTER TABLE ... ADD statements (COL_LENGTH
guard, GO-separated) plus a verification tail: expect an EMPTY result;
each row names a still-missing (table, column).

Output: data/demo/seed_demo_columns_patch.sql
Usage:  python scripts/build_demo_stub_column_patch.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from build_demo_stub_supplement import (  # noqa: E402
    alias_columns,
    infer_type,
    strip_noise,
)

CORPUS = REPO / "data" / "demo" / "seed_demo_source.sql"
SEEDS = [REPO / "data" / "demo" / "seed_demo_tables.sql",
         REPO / "data" / "demo" / "seed_demo_tables_supplement.sql"]
OUT = REPO / "data" / "demo" / "seed_demo_columns_patch.sql"


def stub_columns(seed_sql: str) -> "dict[str, set[str]]":
    """table_key -> lowercase column set, from CREATE TABLE blocks."""
    out: "dict[str, set[str]]" = {}
    for m in re.finditer(
        r"CREATE\s+TABLE\s+\[?(\w+)\]?\s*\.\s*\[?(\w+)\]?\s*\((.*?)\);",
        seed_sql, re.IGNORECASE | re.DOTALL,
    ):
        key = f"{m.group(1)}.{m.group(2)}".lower()
        cols = {c.lower() for c in re.findall(r"\[(\w+)\]", m.group(3))}
        out.setdefault(key, set()).update(cols)
    return out


def proc_blocks(corpus: str) -> "list[str]":
    """Split the corpus at CREATE PROCEDURE/VIEW boundaries — alias
    scoping is per object (the SAME alias binds different tables in
    different procs; a global scan cross-contaminates stubs and creates
    'Ambiguous column name' errors the real schema never had)."""
    idx = [m.start() for m in re.finditer(
        r"CREATE\s+(?:OR\s+ALTER\s+)?(?:PROC(?:EDURE)?|VIEW)\b",
        corpus, re.IGNORECASE)]
    if not idx:
        return [corpus]
    blocks = [corpus[: idx[0]]]
    for a, b in zip(idx, idx[1:] + [len(corpus)]):
        blocks.append(corpus[a:b])
    return blocks


def scoped_references(corpus: str, table_keys: "list[str]") -> "dict[str, set[str]]":
    refs: "dict[str, set[str]]" = {k: set() for k in table_keys}
    for block in proc_blocks(corpus):
        for key in table_keys:
            schema, name = key.split(".")
            if not re.search(rf"\[?{schema}\]?\s*\.\s*\[?{name}\]?",
                             block, re.IGNORECASE):
                continue
            refs[key].update(alias_columns(block, key))
    return refs


def applied_patch_columns(path: Path) -> "list[tuple[str, str]]":
    """(table_key, column) pairs from an existing patch file (v1) —
    needed to compute which already-applied columns must be dropped."""
    if not path.exists():
        return []
    out = []
    for m in re.finditer(
        r"ALTER\s+TABLE\s+\[(\w+)\]\.\[(\w+)\]\s+ADD\s+\[(\w+)\]",
        path.read_text(), re.IGNORECASE,
    ):
        out.append((f"{m.group(1)}.{m.group(2)}".lower(), m.group(3)))
    return out


REVERT = REPO / "data" / "demo" / "seed_demo_columns_revert.sql"


def main() -> None:
    corpus_raw = CORPUS.read_text()
    corpus = strip_noise(corpus_raw)
    stubs: "dict[str, set[str]]" = {}
    for seed in SEEDS:
        for key, cols in stub_columns(seed.read_text()).items():
            stubs.setdefault(key, set()).update(cols)

    v1 = applied_patch_columns(OUT)
    scoped = scoped_references(corpus, sorted(stubs))

    patches: "list[tuple[str, str, str]]" = []
    correct: "set[tuple[str, str]]" = set()
    for key, existing in sorted(stubs.items()):
        for col in sorted(scoped.get(key, set()), key=str.lower):
            correct.add((key, col.lower()))
            if col.lower() not in existing:
                patches.append((key, col, infer_type(corpus, col)))
                existing.add(col.lower())

    lines = [
        "-- Column patch v2 (PER-PROC alias scoping): corpus-referenced",
        "-- columns missing from the dictionary-derived stubs. Generated",
        "-- by scripts/build_demo_stub_column_patch.py. Idempotent;",
        "-- GO-separated; verification tail expects an EMPTY result.",
        "",
    ]
    for key, col, sqltype in patches:
        schema, name = key.split(".")
        lines.append(f"IF COL_LENGTH('{schema}.{name}', '{col}') IS NULL")
        lines.append(f"ALTER TABLE [{schema}].[{name}] ADD [{col}] {sqltype} NULL;")
        lines.append("GO")
        lines.append("")
    lines.append("-- VERIFICATION: expect an EMPTY result.")
    lines.append("SELECT v.tbl AS table_name, v.col AS missing_column FROM (VALUES")
    lines.append(",\n".join(f"    ('{k}', '{c}')" for k, c, _ in patches))
    lines.append(") v(tbl, col) WHERE COL_LENGTH(v.tbl, v.col) IS NULL;")
    lines.append("GO")

    # REVERT: v1 additions that per-proc scoping does NOT confirm —
    # cross-proc contamination; already applied to the live DB and now
    # causing 'Ambiguous column name'. Drop them.
    contaminated = [(k, c) for (k, c) in v1 if (k, c.lower()) not in correct]
    rl = [
        "-- REVERT contaminated v1 patch columns (cross-proc alias",
        "-- contamination -> 'Ambiguous column name'). Idempotent.",
        "",
    ]
    for k, c in contaminated:
        schema, name = k.split(".")
        rl.append(f"IF COL_LENGTH('{schema}.{name}', '{c}') IS NOT NULL")
        rl.append(f"ALTER TABLE [{schema}].[{name}] DROP COLUMN [{c}];")
        rl.append("GO")
        rl.append("")
    rl.append("-- VERIFICATION: expect an EMPTY result (none of these remain).")
    rl.append("SELECT v.tbl, v.col FROM (VALUES")
    rl.append(",\n".join(f"    ('{k}', '{c}')" for k, c in contaminated) or "    ('none','none')")
    rl.append(") v(tbl, col) WHERE COL_LENGTH(v.tbl, v.col) IS NOT NULL;")
    rl.append("GO")
    REVERT.write_text("\n".join(rl) + "\n")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"correct columns needed: {len(patches)} (v2, per-proc scoped)")
    print(f"v1 additions: {len(v1)}; contaminated (to drop): {len(contaminated)}")
    for k, c in contaminated[:20]:
        print("   drop", k, c)
    print(f"wrote {OUT}")
    print(f"wrote {REVERT}")


if __name__ == "__main__":
    main()
