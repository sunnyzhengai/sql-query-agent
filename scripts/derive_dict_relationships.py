"""Derive dict_relationships.csv from the corpus's own join predicates.

Provenance rule (Sunny, 2026-08-19): the join map is DEDUCED from our
de-dialected SQL corpus — the users'-reality evidence layer of ADR
0046 — never extracted from a vendor's proprietary dictionary. Every
row cites how many statements evidence it.

Bootstrap status: after ADR 0044 phase 1b, relationships regenerate
from graph_decision_sites on the tenant (ScriptDom-parsed, alias
lineage resolved); this script then retires. Its statement splitter is
offline demo surgery, verified by the 0-mismatch reconciliation method
of TREE_PHASE1_ED_SEPSIS.md — it is not, and must never become, a
production parse path (native-parser law).

Usage: python scripts/derive_dict_relationships.py
Reads  data/synthetic/sql/**/*.sql + data/synthetic/dict_tables.csv
Writes data/synthetic/dict_relationships.csv
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

import sqlglot
from sqlglot import exp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tree.extract import build_decision_tree  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SQL_DIR = REPO / "data" / "synthetic" / "sql"
DICT_TABLES = REPO / "data" / "synthetic" / "dict_tables.csv"
OUT = REPO / "data" / "synthetic" / "dict_relationships.csv"

_HEAD = re.compile(
    r"^(SELECT|INSERT|UPDATE|DELETE|IF|DROP|DECLARE|CREATE|SET|;?\s*WITH)\b",
    re.I,
)


def _strip_noise(s: str) -> str:
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    s = re.sub(r"--[^\n]*", " ", s)
    return re.sub(r"'[^']*'", "''", s)


def split_statements(text: str) -> "list[str]":
    """Paren-depth-aware statement bounding (statement heads only count
    at depth 0, outside block comments)."""
    lines = text.split("\n")
    heads: "list[int]" = []
    depth = 0
    in_comment = False
    for i, ln in enumerate(lines):
        if _HEAD.match(ln) and depth == 0 and not in_comment:
            heads.append(i)
        probe = ln
        if in_comment:
            if "*/" not in probe:
                continue
            in_comment = False
            probe = probe.split("*/", 1)[1]
        probe = re.sub(r"--.*", "", probe)
        if "/*" in probe and "*/" not in probe:
            in_comment = True
        probe = _strip_noise(probe)
        depth += probe.count("(") - probe.count(")")
    heads.append(len(lines))
    return ["\n".join(lines[a:b]).strip() for a, b in zip(heads, heads[1:])]


def _ident(name: str) -> str:
    """Fold an identifier to its bare uppercase form — sqlglot renders
    [bracketed] T-SQL identifiers as \"quoted\", which must not create
    phantom aliases."""
    return name.strip('"[]').upper()


def alias_map(statement: str) -> "dict[str, str]":
    """alias/name (upper) -> bare table name (upper) for every base
    table in the statement. Temp tables map to '#'-prefixed names; CTE
    aliases map to themselves so both classes are recognizably
    step-side, not dictionary tables."""
    mapping: "dict[str, str]" = {}
    try:
        parsed = sqlglot.parse(statement, read="tsql")
    except Exception:  # noqa: BLE001 — unparseable statements contribute no aliases; join evidence is conservative by design
        return mapping
    for stmt in parsed:
        if stmt is None:
            continue
        for cte in stmt.find_all(exp.CTE):
            name = _ident(cte.alias or "")
            if name:
                mapping[name] = name
        for t in stmt.find_all(exp.Table):
            # take the name from the RENDERED form: sqlglot's t.name
            # drops the '#' temp marker (live find 2026-08-19 — a temp
            # named like a base table could otherwise fabricate
            # evidence); rendering keeps it.
            rendered = t.sql(dialect="tsql").split(" AS ")[0].strip()
            name = _ident(rendered.split(".")[-1])
            alias = _ident(t.alias_or_name or "")
            if not name:
                continue
            mapping.setdefault(name, name)
            if alias:
                mapping[alias] = name
    return mapping


def join_pairs(statement: str):
    """Yield ((tableA, colA), (tableB, colB), skip_reason). Reason is
    None for a resolved base-table pair; otherwise the pair is counted,
    never silently dropped (conservation, applied to evidence)."""
    aliases = alias_map(statement)
    tree = build_decision_tree(statement)
    for node in tree.nodes:
        if node.kind != "predicate" or node.op != "EQ":
            continue
        if len(node.columns) != 2:
            continue  # literal comparisons and expression sides carry no pair
        sides = []
        reason = None
        for ref in node.columns:
            if "." not in ref:
                reason = "unqualified"
                break
            qual, col = ref.rsplit(".", 1)
            table = aliases.get(_ident(qual))
            if table is None:
                reason = "unknown_alias"
                break
            sides.append((table, _ident(col)))
        if reason is None and len(sides) == 2:
            a, b = sides
            if a[0] == b[0]:
                reason = "self_join_or_same_table"
            elif a[0].startswith("#") or b[0].startswith("#"):
                reason = "temp_side"
        if reason is None and len(sides) == 2:
            a, b = sorted(sides)
            yield a, b, None
        else:
            yield None, None, reason or "unresolved"


def main() -> None:
    base_tables = {
        row["TABLE_NAME"].upper()
        for row in csv.DictReader(open(DICT_TABLES))
    }
    pair_counts: "Counter[tuple]" = Counter()
    skips: "Counter[str]" = Counter()
    files = sorted(SQL_DIR.rglob("*.sql"))
    for path in files:
        for statement in split_statements(path.read_text(encoding="utf-8-sig")):
            for a, b, reason in join_pairs(statement):
                if reason is not None:
                    skips[reason] += 1
                    continue
                if a[0] not in base_tables or b[0] not in base_tables:
                    skips["step_or_undictionaried_side"] += 1
                    continue
                pair_counts[(a, b)] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["SOURCE_TABLE", "SOURCE_COLUMN", "DEST_TABLE",
                    "DEST_COLUMN", "CARDINALITY", "EVIDENCE",
                    "EVIDENCE_COUNT"])
        for (a, b), n in sorted(pair_counts.items()):
            w.writerow([a[0], a[1], b[0], b[1], "", "corpus", n])

    print(f"corpus files: {len(files)}")
    print(f"distinct base-table join pairs: {len(pair_counts)} "
          f"(evidence occurrences: {sum(pair_counts.values())})")
    print("counted skips (no silent drops):")
    for reason, n in skips.most_common():
        print(f"  {reason}: {n}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
