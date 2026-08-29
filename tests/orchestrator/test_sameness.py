"""Walk W6/W7 (Sunny live, 2026-08-23): sameness honesty. The corpse:
"Yes, two other metrics use the same base population" declared from a
MENTION census — ground truth 9 procs with materially different logic.

Three layers under test:
1. ops: the step-name-universe stamp (bridge pattern) on census and
   exact search — code states the true universe and the caveat.
2. caption gate: the sameness duty — caveat echo or compare-on-screen,
   else floored (and the floor carries the caveat headline).
3. suite grade: the sameness oracle path (structural, no word oracle).

Proves: law:walk-finds
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


# --- layer 2b: the RW-15 sameness-VERDICT duty -------------------------


def _two_metric_output():
    """Two same-kind records displayed this turn — no caveat stamp,
    no compare (the fifth routing specimen's shape: verdict from
    descriptions with the machine diff one call away)."""
    return {"component": {"op": "retrieve", "params": {}},
            "result": {"ref": "R1", "op": "retrieve", "params": {},
                       "complete": True, "universe": "records",
                       "rows": [
                           {"id": "transform:reporting.USP_A:Codeset",
                            "kind": "step", "name": "Diabetic Codeset"},
                           {"id": "transform:reporting.USP_B:Codeset",
                            "kind": "step", "name": "Diabetic Codeset"},
                       ]}}


class TestSamenessVerdictDuty:
    """RW-15 (morning re-walk 2026-08-29, MANDATORY — the RW-8
    pattern): a same/differ VERDICT requires a displayed compare
    basis this turn; descriptions and names never compute it."""

    def test_verdict_without_compare_floors_naming_the_op(self):
        v = caption_violations(
            "The two codesets differ — one has 80 literals, the "
            "other 81.", [_two_metric_output()])
        [hit] = [x for x in v if "sameness-verdict duty" in x]
        assert "compare(refs=[" in hit
        assert "transform:reporting.USP_A:Codeset" in hit

    def test_sameness_wording_also_floors(self):
        v = caption_violations(
            "Both procs use the same codeset definition.",
            [_two_metric_output()])
        assert any("sameness-verdict duty" in x for x in v)

    def test_compare_on_screen_satisfies_the_duty(self):
        compare = {"component": {"op": "compare", "params": {}},
                   "result": {"ref": "R2", "op": "compare", "params": {},
                              "complete": True, "universe": "content",
                              "rows": [{"verdict": "DIFFERS"}]}}
        v = caption_violations(
            "The definitions DIFFER — E11.80 is present in only one.",
            [_two_metric_output(), compare])
        assert not any("sameness-verdict duty" in x for x in v)

    def test_no_same_kind_pair_no_duty(self):
        # a lone record + sameness wording: nothing on screen to
        # compare against — the duty is data-anchored, never fires
        # on language alone
        lone = _two_metric_output()
        lone["result"]["rows"] = lone["result"]["rows"][:1]
        v = caption_violations(
            "This codeset is different from last year's.", [lone])
        assert not any("sameness-verdict duty" in x for x in v)

    def test_verdictless_caption_untouched(self):
        v = caption_violations(
            "Two codeset steps are displayed; retrieve either for "
            "its logic.", [_two_metric_output()])
        assert not any("sameness-verdict duty" in x for x in v)

    def test_errored_compare_hands_off_to_w12b(self):
        # a FAILED compare is the W12b duty's jurisdiction — RW-15
        # must not double-floor the honest "remains unverified" echo
        err = {"component": {"op": "compare", "params": {}},
               "error": "compare failed: fragments unavailable"}
        v = caption_violations(
            "Whether they differ remains unverified — the comparison "
            "failed.", [_two_metric_output(), err])
        assert not any("sameness-verdict duty" in x for x in v)
