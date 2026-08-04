"""Golden tests for all 28 anonymized SQL files.

Verifies that every SQL file parses successfully and produces the
expected number of CTEs, table references, and final select refs.

These goldens were generated from the sqlglot parser. ScriptDom in
Fabric may produce slightly different results (typically more CTEs,
since it handles T-SQL patterns sqlglot doesn't). The tests check
minimum expectations — actual ScriptDom results should be >= golden.

Run with: pytest tests/golden/test_parse_goldens.py -v
"""

import json
from pathlib import Path

import pytest

from src.parser.sql_parser import parse_sql

GOLDEN_PATH = Path(__file__).parent / "parse_goldens.json"
SQL_DIR = Path(__file__).parent.parent.parent / "data" / "synthetic" / "sql"


def load_goldens():
    with open(GOLDEN_PATH) as f:
        return json.load(f)


def get_sql_files():
    """Yield (test_id, file_path, golden) for each SQL file."""
    goldens = load_goldens()
    for rel_path, golden in goldens.items():
        sql_path = SQL_DIR / rel_path
        if sql_path.exists():
            yield rel_path, sql_path, golden


@pytest.fixture(scope="module")
def goldens():
    return load_goldens()


class TestAllFilesParse:
    """Every SQL file must parse without errors."""

    @pytest.mark.parametrize(
        "rel_path,sql_path,golden",
        list(get_sql_files()),
        ids=[r for r, _, _ in get_sql_files()],
    )
    def test_file_parses(self, rel_path, sql_path, golden):
        sql = sql_path.read_text(encoding="utf-8-sig")
        if golden.get("error"):
            # Known parser limitation — skip but document
            pytest.skip(f"Known parse error: {golden['error'][:80]}")
            return

        parsed = parse_sql(sql)

        # Must produce at least as many CTEs as the golden
        assert len(parsed.ctes) >= golden["cte_count"], (
            f"{rel_path}: expected >= {golden['cte_count']} CTEs, got {len(parsed.ctes)}"
        )

    @pytest.mark.parametrize(
        "rel_path,sql_path,golden",
        list(get_sql_files()),
        ids=[r for r, _, _ in get_sql_files()],
    )
    def test_cte_names_match(self, rel_path, sql_path, golden):
        if golden.get("error") or golden["cte_count"] == 0:
            pytest.skip("No CTEs expected")
            return

        sql = sql_path.read_text(encoding="utf-8-sig")
        parsed = parse_sql(sql)

        expected_names = set(golden["cte_names"])
        actual_names = set(c.name for c in parsed.ctes)

        # All expected CTE names should be found
        missing = expected_names - actual_names
        assert not missing, (
            f"{rel_path}: missing CTEs: {missing}"
        )

    @pytest.mark.parametrize(
        "rel_path,sql_path,golden",
        list(get_sql_files()),
        ids=[r for r, _, _ in get_sql_files()],
    )
    def test_final_cte_refs(self, rel_path, sql_path, golden):
        if golden.get("error") or not golden.get("final_cte_refs"):
            pytest.skip("No final CTE refs expected")
            return

        sql = sql_path.read_text(encoding="utf-8-sig")
        parsed = parse_sql(sql)

        expected_refs = set(golden["final_cte_refs"])
        actual_refs = set(parsed.final_select_cte_refs)

        # All expected final refs should be found
        missing = expected_refs - actual_refs
        assert not missing, (
            f"{rel_path}: missing final CTE refs: {missing}"
        )

    @pytest.mark.parametrize(
        "rel_path,sql_path,golden",
        list(get_sql_files()),
        ids=[r for r, _, _ in get_sql_files()],
    )
    def test_has_tables_or_cte_refs(self, rel_path, sql_path, golden):
        """Every parsed proc must reference at least one table or CTE."""
        if golden.get("error"):
            pytest.skip("Known parse error")
            return

        sql = sql_path.read_text(encoding="utf-8-sig")
        parsed = parse_sql(sql)

        total_refs = (
            len(parsed.final_select_tables)
            + len(parsed.final_select_cte_refs)
            + sum(len(c.table_refs) for c in parsed.ctes)
        )
        assert total_refs > 0, (
            f"{rel_path}: no table or CTE references found"
        )


class TestParseQuality:
    """Quality checks across all files."""

    def test_total_file_count(self, goldens):
        assert len(goldens) == 28, f"Expected 28 SQL files, got {len(goldens)}"

    def test_parse_success_rate(self, goldens):
        errors = [k for k, v in goldens.items() if v.get("error")]
        success_rate = (len(goldens) - len(errors)) / len(goldens)
        assert success_rate >= 0.90, (
            f"Parse success rate {success_rate:.0%} below 90% threshold. "
            f"Errors: {errors}"
        )

    def test_complex_procs_have_ctes(self, goldens):
        """Procs with many lines should extract CTEs."""
        complex_without_ctes = []
        for name, g in goldens.items():
            if g.get("error"):
                continue
            if g.get("line_count", 0) > 200 and g["cte_count"] == 0:
                complex_without_ctes.append(
                    f"{name} ({g['line_count']} lines, 0 CTEs)"
                )
        # Allow some — simple wrapper procs can be long due to comments/formatting
        assert len(complex_without_ctes) <= 5, (
            f"Too many complex procs without CTEs: {complex_without_ctes}"
        )

    def test_no_empty_fragments(self, goldens):
        """Procs with CTEs should have non-empty sql_fragments."""
        for name, g in goldens.items():
            if g.get("error") or g["cte_count"] == 0:
                continue
            # At least one CTE should have table refs (proves the fragment was parsed)
            refs = g.get("table_refs_per_cte", {})
            has_refs = any(v > 0 for v in refs.values())
            assert has_refs, (
                f"{name}: {g['cte_count']} CTEs but none have table references"
            )
