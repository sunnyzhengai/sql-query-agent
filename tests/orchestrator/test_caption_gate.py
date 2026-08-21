"""The caption gate (spec:E6 mechanical): a caption may claim only what
the displayed result sets support; violations drop to the template
floor — stilted but true, visibly corrected."""

from src.orchestrator.caption_gate import (
    caption_violations,
    enforce_caption,
    stamped_headline,
    template_caption,
)

EMPTY_NAME_SEARCH = {
    "component": {"op": "search", "index": 1},
    "result": {"ref": "R1", "op": "search",
               "params": {"phrase": "metrics", "mode": "exact"},
               "rows": [], "complete": True,
               "universe": "every catalog item whose name, business name, "
                           "or ref equals the phrase (case-insensitive)"},
}
CENSUS_TWO = {
    "component": {"op": "census", "index": 1},
    "result": {"ref": "R1", "op": "census", "params": {"kind": "metric"},
               "rows": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
               "complete": True,
               "universe": "every metric in the certified catalog — the "
                           "count is exact"},
}
CENSUS_ZERO = {
    "component": {"op": "census", "index": 1},
    "result": {"ref": "R1", "op": "census", "params": {"kind": "term"},
               "rows": [], "complete": True,
               "universe": "every term in the certified catalog — the "
                           "count is exact"},
}
SEMANTIC_TOP_K = {
    "component": {"op": "search", "index": 1},
    "result": {"ref": "R1", "op": "search",
               "params": {"phrase": "sepsis", "mode": "semantic"},
               "rows": [{"id": "a", "name": "A", "closeness": 0.7}],
               "complete": False,
               "universe": "closest matches by meaning — NOT exhaustive"},
}


class TestViolations:
    def test_the_field_incident_verbatim(self):
        """2026-08-20 web-UI test: empty NAME search captioned as 'no
        metrics exist' — the exact over-claim the gate exists to kill."""
        caption = ("The search for metrics yielded no results, indicating "
                   "that there are currently no metrics available in the "
                   "catalog.")
        out = caption_violations(caption, [EMPTY_NAME_SEARCH])
        assert any("kind-level absence" in v for v in out)

    def test_kind_absence_backed_by_zero_row_census_is_honest(self):
        caption = "There are no terms in the catalog."
        assert caption_violations(caption, [CENSUS_ZERO]) == []

    def test_name_scoped_absence_beside_a_full_census_is_not_floored(self):
        """Suite finding (2026-08-20 first run): 'no metrics are NAMED
        sepsis' beside a 28-row census is honest — the census headline
        stamps the true count; the lint must stand down."""
        caption = ("No metrics are named 'sepsis' exactly, but the "
                   "catalog holds 2 metrics in total (R1).")
        assert caption_violations(
            caption, [EMPTY_NAME_SEARCH, CENSUS_TWO]) == []

    def test_counts_from_a_census_are_grounded(self):
        assert caption_violations(
            "There are 2 metrics: A and B.", [CENSUS_TWO]) == []

    def test_invented_numbers_die(self):
        out = caption_violations("There are 7 metrics.", [CENSUS_TWO])
        assert any("invented number: '7'" in v for v in out)

    def test_absolute_claims_need_a_complete_set(self):
        out = caption_violations(
            "These are all the sepsis metrics.", [SEMANTIC_TOP_K])
        assert any("absolute claim" in v for v in out)
        assert caption_violations(
            "These are all the metrics.", [CENSUS_TWO]) == []

    def test_result_refs_are_not_numbers(self):
        # R1/R2 tokens must not trip the invented-number check
        assert caption_violations("Shown in R1.", [CENSUS_TWO]) == []


class TestEnforcement:
    def test_violating_caption_drops_to_the_template_floor(self):
        text, violations = enforce_caption(
            "No metrics exist anywhere.", [EMPTY_NAME_SEARCH])
        assert violations
        assert text == template_caption([EMPTY_NAME_SEARCH])
        assert "0 row(s)" in text and "R1" in text

    def test_clean_caption_passes_untouched(self):
        text, violations = enforce_caption(
            "There are 2 metrics: A and B.", [CENSUS_TWO])
        assert not violations and text.startswith("There are 2")

    def test_empty_caption_gets_the_floor_without_violations(self):
        text, violations = enforce_caption("", [CENSUS_TWO])
        assert text and not violations

    def test_floor_reports_failed_components_honestly(self):
        failed = {"component": {"op": "compare", "index": 2},
                  "error": "needs two items"}
        text = template_caption([CENSUS_TWO, failed])
        assert "compare: needs two items" in text


class TestStampedHeadline:
    """The load-bearing half (review-session verdict, 2026-08-20):
    stamped by code per ADR 0032, never written by the LLM. The
    2026-08-20 transcript is the fixture — the machine-stamped sentence
    must preempt the exact over-claim that happened."""

    def test_the_transcript_fixture(self):
        from src.orchestrator.caption_gate import stamped_headline
        # The actual incident: caption said "there are currently no
        # metrics available in the catalog" over this result.
        head = stamped_headline(EMPTY_NAME_SEARCH["result"])
        assert "0 row(s)" in head
        assert "name, business name, or ref equals the phrase" in head
        assert "'metrics' is a catalog KIND" in head
        assert "census metric for the actual count" in head

    def test_census_headline_carries_exact_count_and_scope(self):
        from src.orchestrator.caption_gate import stamped_headline
        head = stamped_headline(CENSUS_TWO["result"])
        assert head.startswith("R1: census of kind 'metric' — 2 row(s).")
        assert "count is exact" in head

    def test_incomplete_results_say_so(self):
        from src.orchestrator.caption_gate import stamped_headline
        assert stamped_headline(SEMANTIC_TOP_K["result"]).endswith(
            "Not exhaustive.")

    def test_ordinary_empty_name_search_gets_no_census_redirect(self):
        from src.orchestrator.caption_gate import stamped_headline
        r = dict(EMPTY_NAME_SEARCH["result"],
                 params={"phrase": "NotARealProc", "mode": "exact"})
        head = stamped_headline(r)
        assert "0 row(s)" in head and "KIND" not in head

    def test_deterministic_replay(self):
        from src.orchestrator.caption_gate import stamped_headline
        a = stamped_headline(CENSUS_TWO["result"])
        assert a == stamped_headline(dict(CENSUS_TWO["result"]))


class TestBridgeAndDrilldownStamps:
    """Iteration 3: the bridge set and the step pointer are DATA —
    computed and stamped by code, never left to the captioner."""

    def test_near_name_siblings_are_stamped_when_no_exact_hit(self):
        from src.orchestrator.caption_gate import stamped_headline
        r = {"ref": "R1", "op": "search",
             "params": {"phrase": "Sepsis Case", "mode": "semantic"},
             "rows": [
                 {"name": "X1", "business_name": "Sepsis Case Details"},
                 {"name": "X2", "business_name": "Sepsis Case Encounters"},
                 {"name": "X3", "business_name": "Severe Sepsis Episodes"},
             ],
             "complete": False, "universe": "top-K"}
        head = stamped_headline(r)
        assert "Nothing is NAMED 'Sepsis Case' exactly" in head
        assert "Sepsis Case Details" in head
        assert "Sepsis Case Encounters" in head
        assert "Severe Sepsis Episodes" not in head.split("closest")[1]

    def test_exact_hit_suppresses_the_bridge_stamp(self):
        from src.orchestrator.caption_gate import stamped_headline
        r = {"ref": "R1", "op": "search",
             "params": {"phrase": "Sepsis Case Details", "mode": "exact"},
             "rows": [{"name": "USP_X",
                       "business_name": "Sepsis Case Details"}],
             "complete": True, "universe": "u"}
        assert "Nothing is NAMED" not in stamped_headline(r)

    def test_retrieve_stamps_the_step_pointer(self):
        from src.orchestrator.caption_gate import stamped_headline
        r = {"ref": "R2", "op": "retrieve", "params": {"ids": ["m"]},
             "rows": [{"id": "m", "kind": "metric",
                       "steps": [{"id": "s1"}, {"id": "s2"}]}],
             "complete": True, "universe": "full records"}
        head = stamped_headline(r)
        assert "2 calculation step id(s)" in head
        assert "criteria live in the step records" in head


class TestNoteInHeadline:
    """Walk step 1 (Sunny, 2026-08-21): the empty exact search carries
    its near-names in `note`; the headline stamps it so the template
    floor renders the did-you-mean verbatim."""

    def test_note_is_stamped_into_the_headline(self):
        r = {"ref": "R1", "op": "search",
             "params": {"phrase": "Sepsis Case", "mode": "exact"},
             "rows": [], "complete": True, "universe": "u",
             "note": "Nothing is NAMED 'Sepsis Case' exactly; closest "
                     "by name: Sepsis Case Details, Sepsis Case "
                     "Encounters."}
        head = stamped_headline(r)
        assert "closest by name: Sepsis Case Details" in head

    def test_noted_headline_engages_the_siblings_first_ruling(self):
        r = {"ref": "R1", "op": "search",
             "params": {"phrase": "Sepsis Case", "mode": "exact"},
             "rows": [], "complete": True, "universe": "u",
             "note": "Nothing is NAMED 'Sepsis Case' exactly; closest "
                     "by name: Sepsis Case Details."}
        r["headline"] = stamped_headline(r)
        out = [{"component": {"op": "search"}, "result": r}]
        bad = "Semantically related: Severe Sepsis Episodes. Also " \
              "close by name: Sepsis Case Details."
        assert any("presented FIRST" in v
                   for v in caption_violations(bad, out)) is False
        # the stamped sibling IS mentioned and nothing else displayed
        # competes, so no violation — the ruling needs a displayed
        # competitor named earlier, which empty rows cannot supply


class TestExactStampPrecedence:
    """1.50.9: the exact-mode stamp names the USER'S missed phrase; a
    model-widened semantic search stamps near-everything and must not
    dilute the siblings-first duty."""

    def _outputs(self):
        exact = {"ref": "R1", "op": "search",
                 "params": {"phrase": "Sepsis Case", "mode": "exact"},
                 "rows": [], "complete": True, "universe": "u",
                 "headline": "R1: … Nothing is NAMED 'Sepsis Case' "
                             "exactly; closest by name: Sepsis Case "
                             "Details, Sepsis Case Encounters."}
        widened = {"ref": "R2", "op": "search",
                   "params": {"phrase": "Sepsis", "mode": "semantic"},
                   "rows": [{"id": "x", "name": "USP_Severe_Sepsis",
                             "business_name": "Severe Sepsis Episodes"}],
                   "complete": False, "universe": "u",
                   "headline": "R2: … closest by name: Severe Sepsis "
                               "Episodes."}
        return [{"component": {"op": "search"}, "result": exact},
                {"component": {"op": "search"}, "result": widened}]

    def test_widened_stamp_does_not_dilute_the_duty(self):
        bad = ("Related metrics include Severe Sepsis Episodes. Also "
               "close: Sepsis Case Details.")
        vs = caption_violations(bad, self._outputs())
        assert any("presented FIRST" in v for v in vs)

    def test_siblings_first_across_results_passes(self):
        good = ("Closest by name: Sepsis Case Details and Sepsis Case "
                "Encounters. Meaning-related: Severe Sepsis Episodes.")
        assert not [v for v in caption_violations(good, self._outputs())
                    if "presented FIRST" in v]


class TestStampVerification:
    """ADR 0051: the bridge-duty check was removed (question-family
    control flow); what remains verified is that the FLOOR renders
    the stamped headlines — machine truth survives every path."""

    BRIDGED = {
        "component": {"op": "search", "index": 1},
        "result": {"ref": "R1", "op": "search",
                   "params": {"phrase": "Sepsis Case",
                              "mode": "semantic"},
                   "rows": [{"name": "X1",
                             "business_name": "Sepsis Case Details"}],
                   "complete": False, "universe": "top-K",
                   "headline": "R1: search for 'Sepsis Case' (semantic) "
                               "— 1 row(s). Nothing is NAMED 'Sepsis "
                               "Case' exactly; closest by name: Sepsis "
                               "Case Details, Sepsis Case Encounters. "
                               "Not exhaustive."},
    }

    def test_the_floor_renders_the_stamped_headlines(self):
        text = template_caption([self.BRIDGED])
        assert "closest by name: Sepsis Case Details" in text
        # so a floored bridge turn still hands the user the bridge


class TestBridgeAcceptanceRuling:
    """Sunny's ruling, 2026-08-21: name-siblings presented FIRST,
    mandatory; meaning-related permitted after, labeled. Boundary
    enforcement grounded in the stamped list + displayed rows."""

    RESULT = {
        "component": {"op": "search", "index": 1},
        "result": {"ref": "R1", "op": "search",
                   "params": {"phrase": "Sepsis Case",
                              "mode": "semantic"},
                   "rows": [
                       {"name": "USP_A",
                        "business_name": "Sepsis Case Details"},
                       {"name": "USP_B",
                        "business_name": "Severe Sepsis Episodes"},
                   ],
                   "complete": False, "universe": "top-K",
                   "headline": "R1: search — 2 row(s). Nothing is NAMED "
                               "'Sepsis Case' exactly; closest by name: "
                               "Sepsis Case Details. Not exhaustive."},
    }

    def test_siblings_first_passes(self):
        assert caption_violations(
            "Nothing is named that exactly — closest by name: Sepsis "
            "Case Details. Related by meaning: Severe Sepsis Episodes.",
            [self.RESULT]) == []

    def test_meaning_first_violates(self):
        out = caption_violations(
            "Severe Sepsis Episodes defines severe sepsis cases; also "
            "see Sepsis Case Details.", [self.RESULT])
        assert any("presented FIRST" in v for v in out)

    def test_siblings_absent_violates_when_candidates_are_discussed(self):
        out = caption_violations(
            "Severe Sepsis Episodes covers this topic.", [self.RESULT])
        assert any("presented FIRST" in v for v in out)

    def test_no_candidate_mentions_is_not_forced(self):
        # a caption that discusses none of the displayed candidates is
        # not forced to bridge — the floor renders the stamp anyway
        assert caption_violations(
            "I could not resolve that name to a certified item.",
            [self.RESULT]) == []
