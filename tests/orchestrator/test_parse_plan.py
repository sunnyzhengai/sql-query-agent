"""ADR 0060 prototype L0: closure is structural, grounding is exact,
composition is deterministic, refusal fails closed with the
vocabulary offer. The parse is the plan; the plan confirms on glass.

Proves: contract:suite-legibility
"""

import pytest

from src.orchestrator.ops import OpsSession
from src.orchestrator.parse_plan import (
    PARSE_TOOL,
    PRIMITIVES,
    Parse,
    ParseRefusal,
    compose_plan,
    ground_entities,
    parse_question,
    run_parse_traverse,
)
from tests.orchestrator.test_tools import REF_A, REF_B, fake_kql


def scripted_parser(payload):
    def call(messages, tools, tool_choice=None):
        import json
        return {"role": "assistant", "tool_calls": [
            {"id": "p1", "type": "function",
             "function": {"name": "file_parse",
                          "arguments": json.dumps(payload)}}]}
    return call


def _anchors(*ids):
    return [{"entity": i, "id": i, "kind": "metric", "rows": [{}]}
            for i in ids]


def test_vocabulary_closure_is_structural():
    enum = (PARSE_TOOL["function"]["parameters"]["properties"]
            ["primitives"]["items"]["enum"])
    assert tuple(enum) == PRIMITIVES     # schema IS the closed set


def test_out_of_vocabulary_primitive_is_dropped_at_parse():
    p = parse_question("whatever", scripted_parser(
        {"entities": ["X"], "primitives": ["hallucinated", "flags"]}))
    assert p.primitives == ["flags"]


def test_sameness_over_two_anchors_composes_retrieve_then_compare():
    plan = compose_plan(Parse(["A", "B"], ["same_or_different"]),
                        _anchors(REF_A, REF_B))
    assert [s["op"] for s in plan] == ["retrieve", "compare"]
    assert plan[1]["aspect"] == "logic"


def test_no_primitive_with_grounding_composes_the_default_map():
    # 0062 (card-everywhere, ratified emergent-shape debate): no
    # relation word + a grounded entity = the DEFAULT MAP reading —
    # retrieve the records; the shape emerges from the subgraph
    plan = compose_plan(Parse(["A"], []), _anchors(REF_A))
    assert plan == [{"op": "retrieve", "ids": [REF_A]}]
    assert "the map around" in Parse(["A"], []).render()


def test_no_primitive_and_no_grounding_still_fails_closed():
    with pytest.raises(ParseRefusal, match="same/different"):
        compose_plan(Parse(["Zzz"], []), [
            {"entity": "Zzz", "id": None, "kind": None, "rows": []}])


def test_sameness_with_no_anchor_fails_closed():
    with pytest.raises(ParseRefusal, match="at least one"):
        compose_plan(Parse([], ["same_or_different"]), [])


def test_grounding_is_exact_first_and_reports_misses():
    s = OpsSession()
    anchors = ground_entities(["ED Sepsis Screening", "NoSuchThing"],
                              fake_kql, s)
    assert anchors[0]["id"] is not None
    assert anchors[1]["id"] is None      # reported, never guessed


def test_end_to_end_sameness_answers_with_stamped_results():
    out = run_parse_traverse(
        "how is ED Sepsis Screening different from the regulatory "
        "one?",
        scripted_parser({"entities": [REF_A, REF_B],
                         "primitives": ["same_or_different"]}),
        fake_kql)
    assert out["refused"] is None
    assert "same_or_different" in out["confirm"]
    ops_run = [r["op"] for r in out["results"]]
    assert ops_run == ["retrieve", "compare"]
    # the compare partition ran — groups present in the display rows
    assert any("group" in row for r in out["results"]
               for row in r["rows"])


def test_end_to_end_refusal_carries_the_offer():
    out = run_parse_traverse(
        "write me a poem about the warehouse",
        scripted_parser({"entities": [], "primitives": []}),
        fake_kql)
    assert out["refused"] and "relation vocabulary" not in out["confirm"]
    assert "same/different" in out["refused"]
    assert out["results"] == []


def test_the_lab_path_named_case_step_anchored_sameness():
    # RW-4's routing half, transferred to 0060 by the PM rerun: "who
    # shares this step's logic" — the step name grounds to EVERY
    # same-named step (collision-grounding), and sameness composes
    # retrieve -> compare over their fragments
    out = run_parse_traverse(
        "which other metrics define the cohort using the same "
        "Scores logic?",
        scripted_parser({"entities": ["Scores"],
                         "primitives": ["same_or_different"]}),
        fake_kql)
    assert out["refused"] is None
    # FUZZ-FINDINGS-3: the deterministic pass reads THREE relations
    # in this sentence (define/using/same) — a legitimate
    # multi-relation plan; the invariant is that the COMPARE runs
    ops_run = [r["op"] for r in out["results"]]
    assert "compare" in ops_run and "retrieve" in ops_run
    assert any("group" in row for r in out["results"]
               for row in r["rows"])


def test_d2_grounding_queries_run_concurrently():
    """TESTPLAN_0062 D2 (RW-18b): per-entity grounding overlaps —
    the mock store counts concurrent entries."""
    import threading
    import time

    active, peak = [0], [0]
    lock = threading.Lock()

    def slow_kql(query, params):
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        time.sleep(0.03)
        try:
            return fake_kql(query, params)
        finally:
            with lock:
                active[0] -= 1

    s = OpsSession()
    ground_entities(["ED Sepsis Screening", "ED Sepsis (Regulatory)",
                     "Scores"], slow_kql, s)
    assert peak[0] >= 2, "grounding ran serially"


def test_count_rows_is_a_lexicon_word_not_a_shape():
    plan = compose_plan(Parse(["A"], ["count_rows"]), _anchors(REF_A))
    assert plan == [{"op": "retrieve", "ids": [REF_A]}]


def test_kind_words_become_filters_never_entities():
    # RW-BATCH-6 item 3 (B6): "certified metrics" is a KIND phrase —
    # it filters the plan and never pollutes SHOW as a missed entity
    from src.orchestrator.parse_plan import split_kind_words
    real, kinds = split_kind_words(
        ["Diabetes Registry dashboard", "certified metrics"])
    assert real == ["Diabetes Registry dashboard"]
    assert kinds == ["certified metrics"]


def test_bare_table_word_composes_lineage_ungrounded():
    # RW-BATCH-6 item 4 (B4): a reads/feeds question over a table
    # WORD needs no catalog anchor — lineage probes the name and its
    # result stamps its own honesty
    plan = compose_plan(
        Parse(["ENCOUNTERS"], ["reads_or_feeds"]),
        [{"entity": "ENCOUNTERS", "id": None, "kind": None,
          "rows": []}])
    assert plan == [{"op": "lineage", "table": "ENCOUNTERS"}]


def test_tier2_semantic_candidates_nominate_labeled():
    """TIER2-1: when the exact tier misses, semantic candidates join
    the anchors RANKED and LABELED — nominate-only, prunable."""
    s = OpsSession()
    got = ground_entities(["screening for sepsis cases"], fake_kql, s)
    sems = [a for a in got if a.get("semantic")]
    assert sems, "no semantic nominations surfaced"
    assert all(a["id"] for a in sems)
    assert len(sems) <= 3


def test_exact_hit_takes_no_semantic_nominations():
    # a precise name needs no nominations — zero extra noise
    s = OpsSession()
    got = ground_entities(["ED Sepsis Screening"], fake_kql, s)
    assert not any(a.get("semantic") for a in got)


def test_fuzz_findings_1_surface_forms_consumed():
    """FUZZ-FINDINGS-1 item 2: the fuzzer's five missed phrasings
    are lexicon food — their words now sit in the sameness surface
    forms (identical/equivalent/uniform/uniformity/matching)."""
    from src.orchestrator.parse_plan import PARSE_PROMPT
    for word in ("identical", "uniform", "uniformity", "matching",
                 "consistent"):
        assert word in PARSE_PROMPT, word


def test_fuzz_findings_1_multi_relation_plan_dedups():
    # same_or_different + defines over the same anchors: ONE
    # retrieve, then the compare — never a duplicate-op refusal
    plan = compose_plan(
        Parse(["A", "B"], ["same_or_different", "defines"]),
        _anchors(REF_A, REF_B))
    ops = [s["op"] for s in plan]
    assert ops == ["retrieve", "compare"]
    assert len(plan) == len({str(s) for s in plan})


def test_fuzz_findings_2_surface_forms_consumed():
    """FUZZ-FINDINGS-2: the four fuzzer misses become surface
    forms — the whole-phrase sameness forms and the flags words."""
    from src.orchestrator.parse_plan import PARSE_PROMPT
    for phrase in ("defined uniformly", "definitions match",
                   "red flags", "concerns", "governance issues"):
        assert phrase in PARSE_PROMPT, phrase


def test_fuzz_findings_2_flags_census_uses_canonical_name():
    # the user said "diabetic individuals"; the anchor grounded
    # "Diabetic Patients" — the flags filter uses the CANONICAL
    plan = compose_plan(
        Parse(["diabetic individuals"], ["flags"]),
        [{"entity": "diabetic individuals", "id": "m1",
          "kind": "metric",
          "rows": [{"business_name": "Diabetic Patients",
                    "name": "USP_Diabetic_Patients"}]}])
    assert plan == [{"op": "census", "kind": "flag",
                     "contains": "Diabetic Patients"}]


class TestFuzzFindings3DeterministicRelations:
    """FUZZ-FINDINGS-3 (the generator clause invoked): the same
    phrasings flip-flopped oracles across runs — LLM primitive
    variance. The relation pass is now a PURE FUNCTION of the
    question string; the flip-flop class structurally cannot
    exist."""

    def test_flip_flop_phrasings_resolve_the_same_every_time(self):
        from src.orchestrator.parse_plan import detect_relations
        for q in ("Do all the Diabetic codesets have the same "
                  "definitions?",
                  "Are the Diabetic codesets identical?",
                  "Is there uniformity across the Diabetic codesets?",
                  "Are the codesets defined uniformly?",
                  "Do the codeset definitions match?"):
            for _ in range(3):
                assert "same_or_different" in detect_relations(q), q

    def test_battery_seeds_route_deterministically(self):
        from src.orchestrator.parse_plan import detect_relations
        cases = {
            "which metrics use ENCOUNTERS?": "reads_or_feeds",
            "What governance red flags exist for Diabetic "
            "Patients?": "flags",
            "How many patients are currently in the cohort?":
                "count_rows",
            "is there another way of defining the cohort?":
                "variants",
            "How is the Diabetic Patients cohort defined?":
                "defines",
        }
        for q, prim in cases.items():
            assert prim in detect_relations(q), (q, prim)

    def test_longest_form_wins_its_span(self):
        from src.orchestrator.parse_plan import detect_relations
        # "red flags" must claim its span before bare "flags"
        got = detect_relations("any red flags here?")
        assert got == ["flags"]

    def test_scan_owns_primitives_llm_is_fallback_only(self):
        from src.orchestrator.parse_plan import parse_question

        def llm(messages, tools, tool_choice=None):
            import json as _j
            return {"content": "", "tool_calls": [{
                "id": "p", "function": {"name": "file_parse",
                    "arguments": _j.dumps({
                        "entities": ["X"],
                        "primitives": ["flags"]})}}]}
        # the question SAYS sameness — the LLM's 'flags' loses
        p = parse_question("are X and Y the same?", llm)
        assert p.primitives == ["same_or_different"]
        # no relation words → the schema-closed LLM guess stands
        p2 = parse_question("X please", llm)
        assert p2.primitives == ["flags"]

    def test_prompt_generates_from_the_lexicon_single_source(self):
        from src.orchestrator.parse_plan import (
            PARSE_PROMPT,
            RELATION_LEXICON,
        )
        for forms in RELATION_LEXICON.values():
            for f in forms:
                assert f in PARSE_PROMPT, f
