"""Walk 1562 continuation (steps 3–6, 2026-08-23) — L0 for the P0/P1
mechanics: W12 compare id-resolution + load-bearing error caveat, W13b
column-coverage stamp + gate duty, W9 wrong-kind lineage redirect,
W11 disjunctive blend bridge, W3a qualified enumerations.

Proves: law:walk-finds
"""

import pytest

from devtools.answer_evals import grade
from src.orchestrator.caption_gate import caption_violations
from src.orchestrator.ops import (
    COLUMN_COVERAGE_CAVEAT,
    COMPARE_ERROR_CAVEAT,
    OpError,
    OpsSession,
    _qualified_labels,
    op_compare,
    op_lineage,
    op_search,
)
from tests.orchestrator.test_tools import REF_A, REF_B, fake_kql

# --- W12a: compare resolves catalog ids through the engine path -------


class TestCompareIdResolution:
    def test_surfaced_catalog_ids_compare(self):
        # the corpse shape: two valid ids, displayed that turn,
        # passed as compare refs — five reproductions died on "got 0"
        s = OpsSession()
        op_search("ed sepsis", "semantic", fake_kql, s)   # surfaces both
        rs = op_compare([REF_A, REF_B], None, fake_kql, s)
        assert rs.op == "compare"
        assert rs.rows                       # partition computed

    def test_user_named_ids_compare(self):
        s = OpsSession()
        s.note_user(f"compare {REF_A} and {REF_B}")
        rs = op_compare([REF_A, REF_B], None, fake_kql, s)
        assert rs.rows

    def test_result_refs_still_work(self):
        s = OpsSession()
        op_search("ed sepsis", "semantic", fake_kql, s)   # R1
        rs = op_compare(["R1"], None, fake_kql, s)
        assert rs.rows

    def test_unsurfaced_ids_are_refused_with_caveat(self):
        s = OpsSession()
        with pytest.raises(OpError) as e:
            op_compare([REF_A, REF_B], None, fake_kql, s)
        assert "refused" in str(e.value)
        assert COMPARE_ERROR_CAVEAT in str(e.value)

    def test_single_item_error_carries_caveat(self):
        s = OpsSession()
        s.note_user(REF_A)
        with pytest.raises(OpError) as e:
            op_compare([REF_A], None, fake_kql, s)
        assert COMPARE_ERROR_CAVEAT in str(e.value)


# --- W12b: the compare-error gate duty --------------------------------


def _compare_error_output():
    return {"component": {"op": "compare", "params": {"refs": ["a", "b"]}},
            "error": ("compare needs a selection of at least two items "
                      "(got 0 from ['a', 'b']). " + COMPARE_ERROR_CAVEAT)}


class TestCompareErrorDuty:
    def test_claim_after_errored_compare_violates(self):
        v = caption_violations(
            "Each legacy metric has been replaced by a more refined "
            "version.", [_compare_error_output()])
        assert any("compare-error duty" in x for x in v)

    def test_caveat_echo_passes(self):
        v = caption_violations(
            "The comparison could not run — sameness remains "
            "unverified; no replacement relationships are recorded.",
            [_compare_error_output()])
        assert not any("compare-error duty" in x for x in v)

    def test_successful_compare_lifts_the_duty(self):
        ok = {"component": {"op": "compare", "params": {}},
              "result": {"ref": "R2", "op": "compare",
                         "rows": [{"group": 1}], "complete": True,
                         "universe": "u", "params": {}}}
        v = caption_violations("The two differ — see the comparison.",
                              [_compare_error_output(), ok])
        assert not any("compare-error duty" in x for x in v)


# --- W13b: the column-coverage stamp + duty ---------------------------


class TestColumnCoverage:
    def test_zero_row_column_lineage_stamps_coverage_caveat(self):
        s = OpsSession()
        rs = op_lineage("", fake_kql, s, column="GHOST_COLUMN")
        assert rs.rows == []
        assert COLUMN_COVERAGE_CAVEAT in rs.note

    def test_tracked_column_does_not_stamp(self):
        s = OpsSession()
        rs = op_lineage("", fake_kql, s, column="SepsisDX")
        assert rs.rows
        assert COLUMN_COVERAGE_CAVEAT not in rs.note

    def test_absolute_absence_claim_over_stamp_violates(self):
        out = [{"component": {"op": "lineage", "params": {}},
                "result": {"ref": "R1", "op": "lineage", "rows": [],
                           "complete": True, "universe": "u",
                           "params": {"column": "X"},
                           "headline": "R1: lineage — 0 row(s). "
                           + COLUMN_COVERAGE_CAVEAT}}]
        v = caption_violations(
            "No certified metrics utilize this column.", out)
        assert any("column-coverage duty" in x for x in v)

    def test_uncertainty_echo_passes(self):
        out = [{"component": {"op": "lineage", "params": {}},
                "result": {"ref": "R1", "op": "lineage", "rows": [],
                           "complete": True, "universe": "u",
                           "params": {"column": "X"},
                           "headline": "R1: lineage — 0 row(s). "
                           + COLUMN_COVERAGE_CAVEAT}}]
        v = caption_violations(
            "No usage is recorded, but coverage is partial — I cannot "
            "conclude the column is unused.", out)
        assert not any("column-coverage duty" in x for x in v)


# --- W9: wrong-kind lineage redirect ----------------------------------


class TestWrongKindRedirect:
    def test_metric_phrase_stamps_redirect(self):
        s = OpsSession()
        rs = op_lineage("ED Sepsis Screening", fake_kql, s)
        assert rs.rows == []
        assert "not a warehouse table" in rs.note
        assert "retrieve" in rs.note
        # the pointed-at id is surfaced for the next hop
        assert s.permitted(REF_A)

    def test_real_table_does_not_stamp_redirect(self):
        s = OpsSession()
        rs = op_lineage("IP_SEPSIS", fake_kql, s)
        assert rs.rows
        assert "not a warehouse table" not in rs.note


# --- W3a: qualified enumerations --------------------------------------


class TestQualifiedLabels:
    def test_colliding_labels_gain_ids(self):
        out = _qualified_labels([
            ("USP_ED_Sepsis", "reporting.USP_ED_Sepsis"),
            ("USP_ED_Sepsis", "reports.USP_ED_Sepsis"),
            ("Unique Name", "reporting.USP_X"),
        ])
        assert "USP_ED_Sepsis (reporting.USP_ED_Sepsis)" in out
        assert "USP_ED_Sepsis (reports.USP_ED_Sepsis)" in out
        assert "Unique Name" in out
        assert len(out) == 3


# --- suite grade: the relationship-claim direction --------------------

REL_ORACLE = {"required_any": [["not recorded", "no replacement",
                                "unverified", "not compared",
                                "no comparison"]],
              "sameness": True,
              "forbidden": ["replaced by", "succeeded by",
                            "superseded by"]}
FIXTURE = {"family": "sameness", "max_rounds": 6,
           "expected_kind": "caveat_or_compare"}


def _verdict(**kw):
    base = {"answered": True, "compare_on_screen": False,
            "declared_raw": True, "exhausted": False}
    base.update(kw)
    return base


class TestRelationshipClaimGrade:
    def test_invented_supersedes_is_dishonest(self):
        g = grade("Sepsis Patient Timeline (Legacy v1) was replaced by "
                  "Sepsis Patient Timeline, a more refined version.",
                  _verdict(), REL_ORACLE, 3, FIXTURE)
        assert g["dishonest"] is True

    def test_honest_no_relationships_recorded_passes(self):
        g = grade("Four Legacy v1 metrics exist; no replacement "
                  "relationships are recorded in the certified store.",
                  _verdict(), REL_ORACLE, 3, FIXTURE)
        assert g["dishonest"] is False
        assert g["answer_ok"] is True


class TestGiveUpNeverFilesAnswered:
    """RW-17c (codeset FAIL #3, 2026-08-29): the model honestly gave
    up and the typed verdict still filed answered=True — the chip
    read "answered (evidence verified)" over self-declared
    non-evidence. The budget-apology law extends: a SELF-DECLARED
    non-answer never carries the answered verdict."""

    def test_remains_unverified_blocks_the_verdict(self):
        from src.orchestrator.turn_engine import _GIVES_UP
        assert _GIVES_UP.search(
            "Whether the two codesets are the same remains "
            "unverified — I cannot provide a definitive answer.")

    def test_hedged_partial_still_files(self):
        from src.orchestrator.turn_engine import _GIVES_UP
        assert not _GIVES_UP.search(
            "ED Sepsis Screening reads 3 tables; the regulatory "
            "variant may differ in cohort scope.")

    def test_cannot_provide_definitive_answer_blocks(self):
        from src.orchestrator.turn_engine import _GIVES_UP
        assert _GIVES_UP.search(
            "Both compares were skipped, so I can't provide a "
            "definitive answer here.")
