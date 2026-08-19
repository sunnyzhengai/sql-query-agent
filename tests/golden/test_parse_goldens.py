"""NATIVE parse goldens over the corpus (ADR 0001, hardened 2026-08-19).

History: these were fallback-parser smoke tests, skipped on CI because
sqlparse/sqlglot statement splitting was environment-fragile — a
CI-invisible tier that sat red on dev machines for three days
(HANDOFF_FALLBACK_GOLDEN_DRIFT). The fallback is abolished; ScriptDom
parses the corpus identically everywhere, so the goldens are now exact
structural pins and RUN EVERYWHERE — no skip, no tier.

Deliberate corpus changes regenerate the pins:
    python3.11 scripts/regenerate_parse_goldens.py
"""

import json
from pathlib import Path

import pytest

from src.parser.sql_parser import parse_sql

GOLDEN_PATH = Path(__file__).parent / "parse_goldens.json"
SQL_DIR = Path(__file__).parent.parent.parent / "data" / "synthetic" / "sql"

GOLDENS = json.loads(GOLDEN_PATH.read_text())


def test_corpus_manifest_covers_all_sql_files():
    """Every SQL file in the corpus has a golden entry, and vice versa."""
    on_disk = {str(p.relative_to(SQL_DIR)) for p in SQL_DIR.rglob("*.sql")}
    assert on_disk == set(GOLDENS), (
        f"golden/disk drift — only in goldens: {sorted(set(GOLDENS) - on_disk)}; "
        f"only on disk: {sorted(on_disk - set(GOLDENS))}"
    )


@pytest.mark.parametrize("rel_path", sorted(GOLDENS), ids=sorted(GOLDENS))
def test_native_parse_matches_golden(rel_path):
    """The native parser must parse every corpus file and reproduce the
    pinned structure EXACTLY — same counts on every machine."""
    golden = GOLDENS[rel_path]
    parsed = parse_sql((SQL_DIR / rel_path).read_text(encoding="utf-8-sig"))
    tables = {t.table for c in parsed.ctes for t in c.table_refs}
    tables |= {t.table for t in parsed.final_select_tables}
    assert len(parsed.ctes) == golden["cte_count"], rel_path
    assert len(tables) == golden["physical_table_count"], rel_path


def test_total_step_count_matches_recorded_fixtures():
    """The local native parse and the Fabric recording agree on the
    corpus's total step count — one parser, one truth, everywhere."""
    recorded = json.loads(
        (Path(__file__).parent.parent / "fixtures" / "recorded"
         / "parse_results.json").read_text())
    recorded_steps = sum(r["cte_count"] for r in recorded)
    golden_steps = sum(v["cte_count"] for v in GOLDENS.values())
    assert golden_steps == recorded_steps == 417
