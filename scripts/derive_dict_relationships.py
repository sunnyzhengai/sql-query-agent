"""Derive dict_relationships.csv from the corpus's own join predicates
— NATIVE parser only (ScriptDom, ADR 0001; sqlglot banned 2026-08-19).

Provenance rule (Sunny, 2026-08-19): the join map is DEDUCED from our
de-dialected SQL corpus — the users'-reality evidence layer of ADR
0046 — never extracted from a vendor's proprietary dictionary. Every
row cites how many statements evidence it.

Completeness (HANDOFF_TREE_PHASE_1B criterion, "we can't miss joins"):
statement splitting and alias resolution come from ScriptDom itself,
so the sqlglot bootstrap's measured blind spot (33 unparseable
statements, 192 unevidenced JOINs) is closed; any residual
unparseable statement is printed as a counted number, never silence.

Bootstrap status: once 300 persists decision→column edges tenant-side
(phase 1b remainder), relationships regenerate from
graph_decision_sites and this script retires.

Usage: python3.11 scripts/derive_dict_relationships.py
Reads  data/synthetic/sql/**/*.sql + data/synthetic/dict_tables.csv
Writes data/synthetic/dict_relationships.csv
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.parser.scriptdom_loader import parse_tsql  # noqa: E402
from src.tree.extract import (  # noqa: E402
    build_decision_tree,
    find_nodes,
    statement_texts,
)

SQL_DIR = REPO / "data" / "synthetic" / "sql"
DICT_TABLES = REPO / "data" / "synthetic" / "dict_tables.csv"
OUT = REPO / "data" / "synthetic" / "dict_relationships.csv"


def alias_map(statement: str) -> "dict[str, str]":
    """alias/name (upper) -> table name (upper) for every table in the
    statement. Temp names keep their '#' (ScriptDom preserves it in
    BaseIdentifier); CTE names map to themselves so both classes are
    recognizably step-side, never dictionary tables."""
    mapping: "dict[str, str]" = {}
    fragment, errors = parse_tsql(statement)
    if errors:
        return mapping
    ctes = find_nodes(fragment, {"CommonTableExpression"})
    tables = find_nodes(fragment, {"NamedTableReference"})
    derived = find_nodes(fragment, {"QueryDerivedTable"})
    for d in derived:  # subquery aliases are step-side, like CTEs
        try:
            if d.Alias is not None:
                name = d.Alias.Value.upper()
                mapping[name] = name
        except Exception:  # noqa: BLE001, S112 — .NET reflection edge; unmapped aliases surface as skips
            continue
    for cte in ctes:
        try:
            name = cte.ExpressionName.Value.upper()
            mapping[name] = name
        except Exception:  # noqa: BLE001, S112 — .NET reflection edge; unmapped aliases surface as skips
            continue
    for t in tables:
        try:
            name = t.SchemaObject.BaseIdentifier.Value.upper()
            mapping.setdefault(name, name)
            if t.Alias is not None:
                mapping[t.Alias.Value.upper()] = name
        except Exception:  # noqa: BLE001, S112 — .NET reflection edge; unmapped aliases surface as skips
            continue
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
            # a 3-part ref (dbo.TABLE.COL) qualifies by its last part
            table = aliases.get(qual.split(".")[-1].upper())
            if table is None:
                reason = "unknown_alias"
                break
            sides.append((table, col.upper()))
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
    blind_statements = 0
    files = sorted(SQL_DIR.rglob("*.sql"))
    for path in files:
        try:
            statements = statement_texts(path.read_text(encoding="utf-8-sig"))
        except ValueError:
            blind_statements += 1  # whole-file parse failure — counted
            continue
        for statement in statements:
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
    print(f"BLIND SPOT: {blind_statements} unparseable files "
          f"(native parser — expected 0)")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
