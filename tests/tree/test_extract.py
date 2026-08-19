"""Decision-site extraction (ADR 0044 clause 1, phase 1).

The conservation law is exercised two ways: shape-by-shape on the real
corpus constructs from the traced proc, and corpus-wide over EVERY
fragment in the recorded fixtures — the equation must hold on any
input, including the stale truncated fragments the fixtures still
carry (recorded pre-1.25.0; re-record follows the full tenant rerun).
"""

import json
from pathlib import Path

from src.tree.extract import (
    build_decision_tree,
    decision_site_rows,
    unextracted_fallout_rows,
)

RECORDED = Path(__file__).parent.parent / "fixtures" / "recorded" / \
    "parse_results.json"


def _conserved(tree):
    return tree.handled_count + len(tree.unextracted) == \
        tree.decision_sites_total


class TestConservationLaw:
    def test_holds_for_every_recorded_corpus_fragment(self):
        rows = json.load(open(RECORDED))
        fragments = [
            (r["metric_id"], cte.get("name"), cte.get("sql_fragment") or "")
            for r in rows for cte in json.loads(r["ctes_json"])
        ]
        assert len(fragments) > 300, "corpus fixture shrank unexpectedly"
        for metric_id, step, fragment in fragments:
            tree = build_decision_tree(fragment)
            assert _conserved(tree), (
                f"conservation violated on {metric_id}:{step}"
            )

    def test_empty_fragment_is_zero_everything(self):
        tree = build_decision_tree("   \n ")
        assert tree.decision_sites_total == 0
        assert tree.handled_count == 0 and not tree.unextracted

    def test_no_decision_fragment_has_zero_sites(self):
        tree = build_decision_tree("SELECT a, b INTO #copy FROM #prior")
        assert tree.decision_sites_total == 0 and _conserved(tree)


class TestRealCorpusShapes:
    def test_exists_is_a_leaf_and_its_subquery_where_its_own_site(self):
        tree = build_decision_tree(
            "SELECT a INTO #neg FROM #Base_Pop EEF "
            "WHERE NOT EXISTS (SELECT 1 FROM #ED_PositiveScores PS "
            "WHERE PS.ENCOUNTER_ID = EEF.ENCOUNTER_ID)")
        ops = [n.op for n in tree.nodes if n.kind == "predicate"]
        assert "EXISTS" in ops
        # the inner equality is counted as its own site, not lost
        assert ops.count("EQ") == 1
        assert tree.decision_sites_total == 2 and _conserved(tree)
        kinds = [n.kind for n in tree.nodes]
        assert "not" in kinds, "NOT must survive as a node — polarity is meaning"

    def test_computed_expression_predicate_keeps_its_columns(self):
        # The systolic parse: threshold applies to an EXPRESSION over
        # MEAS_VALUE — the predicate must carry the column and the
        # faithful expression, and column= must NOT claim a bare column.
        tree = build_decision_tree(
            "SELECT a FROM t WHERE CONVERT(INTEGER, LEFT(FSD.MEAS_VALUE, "
            "CHARINDEX('/', FSD.MEAS_VALUE) - 1)) < 100")
        leaf = [n for n in tree.nodes if n.kind == "predicate"][0]
        assert leaf.op == "LT"
        assert leaf.column is None
        assert "FSD.MEAS_VALUE" in leaf.columns
        assert "100" in leaf.operands

    def test_in_list_operands_are_captured_verbatim(self):
        tree = build_decision_tree(
            "SELECT a FROM t WHERE FLO_MEAS_ID IN ('900112', '900111')")
        leaf = [n for n in tree.nodes if n.kind == "predicate"][0]
        assert leaf.op == "IN"
        assert any("900112" in o for o in leaf.operands)
        assert any("900111" in o for o in leaf.operands)

    def test_case_when_in_select_list_is_a_decision_site(self):
        tree = build_decision_tree(
            "SELECT CASE WHEN AGE_YEARS > 13 AND MEAS_VALUE > 4 "
            "THEN 'Y' ELSE 'N' END AS FLAG FROM #vitals")
        contexts = {n.context for n in tree.nodes if n.kind == "predicate"}
        assert contexts == {"case_when"}
        assert tree.handled_count == 2

    def test_join_on_predicates_are_sites(self):
        tree = build_decision_tree(
            "SELECT a FROM t1 INNER JOIN t2 ON t1.id = t2.id "
            "LEFT JOIN t3 ON t2.k = t3.k AND t3.kind = 'x'")
        join_leaves = [n for n in tree.nodes
                       if n.kind == "predicate" and n.context == "join_on"]
        assert len(join_leaves) == 3

    def test_or_shape_is_not_reported_when_absent(self):
        tree = build_decision_tree(
            "SELECT a FROM t WHERE x = '900112' AND y = 3022")
        assert not tree.has_or_node(within=["900112", "3022"])


class TestHonestFailureModes:
    def test_for_xml_path_lands_in_unextracted_never_dropped(self):
        # Real corpus construct (Base_Pop_ENC_Reason): STUFF(... FOR XML
        # PATH('')) — a genuine sqlglot gap; the equation makes it loud.
        tree = build_decision_tree(
            "SELECT DISTINCT CAT.ENCOUNTER_ID,\n"
            "STUFF(( SELECT '% ' + DIAG.DX_NAME\n"
            "FROM #Main SUB\n"
            "INNER JOIN dbo.ENCOUNTER_DIAGNOSES EDX "
            "ON EDX.ENCOUNTER_ID = SUB.ENCOUNTER_ID\n"
            "INNER JOIN dbo.DIAGNOSES DIAG ON DIAG.DX_ID = EDX.DX_ID\n"
            "WHERE SUB.ENCOUNTER_ID = CAT.ENCOUNTER_ID\n"
            "FOR XML PATH('')\n"
            "), 1, 1, '') AS [AllEncReasons]\n"
            "INTO #Base_Pop_ENC_Reason FROM #Main CAT")
        assert _conserved(tree)
        assert tree.unextracted, "an unparseable construct must be counted"

    def test_one_argument_format_does_not_crash_the_extractor(self):
        # Live find 2026-08-19: sqlglot's tsql FORMAT() internals raise
        # a bare AssertionError, not a ParseError.
        tree = build_decision_tree(
            "SELECT FORMAT(x) AS f FROM t WHERE a = 1")
        assert _conserved(tree)

    def test_truncated_fragment_is_counted_not_crashed(self):
        # The stale-fixture class: amputated mid-token.
        tree = build_decision_tree(
            "SELECT a, b FROM t WHERE x = 1 AND LEFT JOIN [dbo].[")
        assert _conserved(tree) and tree.unextracted

    def test_dynamic_sql_reason_code_is_specific(self):
        tree = build_decision_tree(
            "DECLARE @sql NVARCHAR(MAX) = 'SELECT 1'; EXEC (@sql)")
        assert [u.reason_code for u in tree.unextracted] == ["dynamic_sql"]


class TestPersistenceRows:
    def _tree(self):
        return build_decision_tree(
            "SELECT a INTO #x FROM #p WHERE d BETWEEN @s AND @e "
            "AND (c IN ('1a', '2b') OR v = 3022)")

    def test_site_rows_make_conservation_queryable_in_table(self):
        tree = self._tree()
        rows = decision_site_rows(tree, "USP_X", step_name="Base_Pop")
        extracted = [r for r in rows if r["status"] == "extracted"]
        unex = [r for r in rows if r["status"] == "unextracted"]
        assert sum(r["predicate_count"] for r in extracted) == \
            tree.handled_count
        assert len(unex) == len(tree.unextracted)
        for r in rows:
            assert r["metric_id"] == "USP_X"
            assert r["step_name"] == "Base_Pop"

    def test_extracted_row_tree_json_is_faithful(self):
        rows = decision_site_rows(self._tree(), "USP_X")
        where = [r for r in rows if r["context"] == "where"][0]
        payload = json.loads(where["tree"])
        kinds = set()

        def walk(n):
            kinds.add(n["kind"])
            for c in n["children"]:
                walk(c)
        walk(payload)
        assert "or" in kinds, "boolean shape must survive serialization"
        assert json.loads(where["columns_used"])

    def test_fallout_rows_escalate_with_contract_id(self):
        tree = build_decision_tree("EXEC (@sql)")
        rows = unextracted_fallout_rows(
            tree, "USP_X", step_name="Final", run_at="2026-08-19T00:00:00")
        assert len(rows) == 1
        row = rows[0]
        assert row["stage"] == "300_tree_unextracted"
        assert row["resolution"] == "escalated"
        assert row["contract_id"] == "contract:graph_decision_sites"
        assert row["entity_id"].startswith("USP_X:Final:")
        assert row["run_at"] == "2026-08-19T00:00:00"
