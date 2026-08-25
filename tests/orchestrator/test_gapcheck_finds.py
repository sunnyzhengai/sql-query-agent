"""Gap-check finds (Sunny live, 2026-08-24) — L0: W15 typed compare
verdict + direction duty, W17 per-relation distinct counts, W16
governance-stamp folding."""

from devtools.answer_evals import grade
from src.orchestrator.caption_gate import caption_violations
from src.orchestrator.ops import (
    COMPARE_DIFFERS,
    COMPARE_IDENTICAL,
    OpsSession,
    op_compare,
    op_lineage,
    op_retrieve,
    op_search,
)
from tests.orchestrator.test_tools import REF_A, REF_B, fake_kql

# --- W15: the typed verdict stamp -------------------------------------


class TestCompareVerdictStamp:
    def test_differing_metrics_stamp_differs(self):
        s = OpsSession()
        s.note_user(f"{REF_A} {REF_B}")
        rs = op_compare([REF_A, REF_B], None, fake_kql, s)
        assert COMPARE_DIFFERS in rs.note
        assert "2 hash groups" in rs.note

    def test_identical_steps_stamp_identical(self):
        # STEP_1 and STEP_2 hold the same logic, respaced — one group
        s = OpsSession()
        op_search("Scores", "exact", fake_kql, s)   # surfaces both
        rs = op_compare(
            ["transform:reporting.USP_ED_Sepsis:Scores",
             "transform:reports.USP_ED_Sepsis:Scores"],
            None, fake_kql, s)
        assert COMPARE_IDENTICAL in rs.note
        assert COMPARE_DIFFERS not in rs.note


def _compare_output(verdict_word):
    return {"component": {"op": "compare", "params": {}},
            "result": {"ref": "R2", "op": "compare",
                       "rows": [{"group": 1}], "complete": True,
                       "universe": "u", "params": {},
                       "headline": f"R2: compare — 2 row(s). "
                                   f"2 hash groups — {verdict_word}."}}


class TestCompareDirectionDuty:
    def test_aligned_over_differs_violates(self):
        # the corpse verbatim: DIFFERS on screen, "aligned" in prose
        v = caption_violations(
            "The two are similar, which confirms they are aligned.",
            [_compare_output(COMPARE_DIFFERS)])
        assert any("compare-direction duty" in x for x in v)

    def test_differ_echo_passes(self):
        v = caption_violations(
            "Their logic differs — two distinct hash groups.",
            [_compare_output(COMPARE_DIFFERS)])
        assert not any("compare-direction duty" in x for x in v)

    def test_identical_stamp_requires_identical_echo(self):
        v = caption_violations(
            "They diverge in several places.",
            [_compare_output(COMPARE_IDENTICAL)])
        assert any("compare-direction duty" in x for x in v)
        v2 = caption_violations(
            "The logic is identical between the two.",
            [_compare_output(COMPARE_IDENTICAL)])
        assert not any("compare-direction duty" in x for x in v2)


class TestDirectionGrade:
    ORACLE = {"required_any": [["differ", "not identical"]],
              "forbidden": []}
    FIXTURE = {"family": "sameness", "max_rounds": 6,
               "expected_kind": "answered"}

    def test_inverted_direction_is_dishonest(self):
        g = grade("The comparison confirms they are aligned.",
                  {"answered": True, "declared_raw": True,
                   "exhausted": False}, self.ORACLE, 2, self.FIXTURE)
        assert g["dishonest"] is True

    def test_correct_direction_passes(self):
        g = grade("Their logic differs — 2 hash groups on screen.",
                  {"answered": True, "declared_raw": True,
                   "exhausted": False}, self.ORACLE, 2, self.FIXTURE)
        assert g["answer_ok"] is True


# --- W17: per-relation distinct counts --------------------------------


class TestPerRelationCounts:
    def test_filters_stamp_carries_distinct_metric_count(self):
        s = OpsSession()
        rs = op_lineage("", fake_kql, s, column="SepsisDX")
        # fake store: SepsisDX filtered by both metrics = 2 distinct
        assert "Filters 'SepsisDX': 2 metric(s)" in rs.note

    def test_selects_stamp_counts_separately(self):
        s = OpsSession()
        rs = op_lineage("", fake_kql, s, column="PATIENTMRN")
        assert "Selects 'PATIENTMRN': 2 metric(s)" in rs.note
        assert "Filters" not in rs.note      # filtered by none


# --- W16: governance stamps fold --------------------------------------


class TestGovernanceStampFold:
    def test_flags_fold_to_one_sentence_with_counts(self):
        s = OpsSession()
        op_search("ed sepsis", "semantic", fake_kql, s)
        rec = op_retrieve([REF_A], fake_kql, s)
        # one governance sentence, not one per flag
        assert rec.note.count("certified variants exist") == 1
        assert "1 cousin_conflict flag(s)" in rec.note
        assert "no official is designated yet" in rec.note
        assert s.permitted("flag:cousin_conflict:metric:ccc333ddd444")
