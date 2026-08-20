"""The caption gate (spec:E6 mechanical): a caption may claim only what
the displayed result sets support; violations drop to the template
floor — stilted but true, visibly corrected."""

from src.orchestrator.caption_gate import (
    caption_violations,
    enforce_caption,
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
