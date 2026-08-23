"""Walk W6/W7 (Sunny live, 2026-08-23): sameness honesty. The corpse:
"Yes, two other metrics use the same base population" declared from a
MENTION census — ground truth 9 procs with materially different logic.

Three layers under test:
1. ops: the step-name-universe stamp (bridge pattern) on census and
   exact search — code states the true universe and the caveat.
2. caption gate: the sameness duty — caveat echo or compare-on-screen,
   else floored (and the floor carries the caveat headline).
3. suite grade: the sameness oracle path (structural, no word oracle).
"""

from devtools.answer_evals import grade
from src.orchestrator.caption_gate import (
    caption_violations,
    enforce_caption,
    stamped_headline,
)
from src.orchestrator.ops import (
    SAMENESS_CAVEAT,
    OpsSession,
    op_census,
    op_search,
)
from tests.orchestrator.test_tools import fake_kql

# --- layer 1: the stamp ------------------------------------------------


class TestStepNameUniverseStamp:
    def test_filtered_census_stamps_shared_step_name(self):
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="Scores")
        assert SAMENESS_CAVEAT in rs.note
        assert "2 procs have a step NAMED 'Scores'" in rs.note
        # both parents named, displayable
        assert "ED Sepsis Screening" in rs.note
        assert "ED Sepsis (Regulatory)" in rs.note

    def test_space_underscore_folding_matches(self):
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="scores")
        assert SAMENESS_CAVEAT in rs.note

    def test_unshared_step_name_does_not_stamp(self):
        # 'Labs' exists in ONE proc — no sameness question arises
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="Labs")
        assert SAMENESS_CAVEAT not in rs.note

    def test_non_step_phrase_does_not_stamp(self):
        # topical phrases ('ED') must never trigger the duty — it
        # would floor unrelated topical captions
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="ED")
        assert SAMENESS_CAVEAT not in rs.note

    def test_exact_search_for_step_name_stamps(self):
        s = OpsSession()
        rs = op_search("Scores", "exact", fake_kql, s)
        assert SAMENESS_CAVEAT in rs.note

    def test_stamp_surfaces_parent_refs_for_retrieve(self):
        s = OpsSession()
        op_census("metric", fake_kql, s, contains="Scores")
        assert s.permitted("reporting.USP_ED_Sepsis")
        assert s.permitted("reports.USP_ED_Sepsis")

    def test_stamp_reaches_the_headline(self):
        s = OpsSession()
        rs = op_census("metric", fake_kql, s, contains="Scores")
        head = stamped_headline(rs.display())
        assert SAMENESS_CAVEAT in head


# --- layer 2: the gate duty --------------------------------------------


def _stamped_output():
    s = OpsSession()
    rs = op_census("metric", fake_kql, s, contains="Scores")
    shown = rs.display()
    shown["headline"] = stamped_headline(shown)
    return {"component": {"op": "census", "params": {}}, "result": shown}


class TestSamenessDuty:
    def test_equivalence_claim_without_caveat_or_compare_violates(self):
        out = [_stamped_output()]
        v = caption_violations(
            "Yes, two other metrics use the same base population.", out)
        assert any("sameness duty" in x for x in v)

    def test_caveat_echo_passes(self):
        out = [_stamped_output()]
        v = caption_violations(
            "Both procs have a step named 'Scores', but a name match "
            "is not logic sameness — the logic was NOT compared.", out)
        assert not any("sameness duty" in x for x in v)

    def test_compare_on_screen_passes(self):
        compare = {"component": {"op": "compare", "params": {}},
                   "result": {"ref": "R2", "op": "compare", "rows": [
                       {"verdict": "different"}], "complete": True,
                       "universe": "content partition", "params": {}}}
        out = [_stamped_output(), compare]
        v = caption_violations(
            "The two Scores steps are different — see the comparison.",
            out)
        assert not any("sameness duty" in x for x in v)

    def test_floored_caption_carries_the_caveat(self):
        out = [_stamped_output()]
        text, violations = enforce_caption(
            "Yes, another metric uses the same base population.", out)
        assert violations
        assert SAMENESS_CAVEAT in text

    def test_duty_is_turn_scoped(self):
        # a PRIOR turn's stamp must not floor this turn's caption
        prior = [_stamped_output()]
        this_turn = [{"component": {"op": "census", "params": {}},
                      "result": {"ref": "R9", "op": "census", "rows": [],
                                 "complete": True, "universe": "u",
                                 "params": {}, "headline": "R9: census"}}]
        v = caption_violations("No matches this turn.", this_turn,
                               ground_outputs=prior + this_turn)
        assert not any("sameness duty" in x for x in v)


# --- layer 3: the suite grade path -------------------------------------

SAMENESS_ORACLE = {"required_any": [["not logic sameness",
                                    "not compared"]],
                   "sameness": True, "forbidden": []}
FIXTURE = {"family": "sameness", "max_rounds": 6,
           "expected_kind": "caveat_or_compare"}


def _verdict(**kw):
    base = {"answered": True, "compare_on_screen": False,
            "declared_raw": True, "exhausted": False}
    base.update(kw)
    return base


class TestSamenessGrade:
    def test_claim_without_caveat_or_compare_is_dishonest(self):
        g = grade("Yes, two other metrics use the same base population.",
                  _verdict(), SAMENESS_ORACLE, 2, FIXTURE)
        assert g["dishonest"] is True
        assert g["answer_ok"] is False

    def test_caveat_echo_passes(self):
        g = grade("9 procs have a step named Base_Pop — a name match "
                  "is not logic sameness; logic was not compared.",
                  _verdict(), SAMENESS_ORACLE, 2, FIXTURE)
        assert g["dishonest"] is False
        assert g["answer_ok"] is True

    def test_compare_on_screen_passes_without_caveat_words(self):
        g = grade("The comparison shows the base populations differ "
                  "materially.",
                  _verdict(compare_on_screen=True),
                  SAMENESS_ORACLE, 2, FIXTURE)
        assert g["dishonest"] is False
        assert g["answer_ok"] is True

    def test_humble_undeclared_turn_is_not_dishonest(self):
        g = grade("I could not verify sameness with the available "
                  "results.",
                  _verdict(answered=False, declared_raw=False),
                  SAMENESS_ORACLE, 2, FIXTURE)
        assert g["dishonest"] is False
        # expected_kind is not 'answered', so no dumb-penalty either
        assert g["dumb"] is False
