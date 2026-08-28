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


def test_no_primitive_fails_closed_with_the_offer():
    with pytest.raises(ParseRefusal, match="relation vocabulary"):
        compose_plan(Parse(["A"], []), _anchors(REF_A))


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
    assert [r["op"] for r in out["results"]] == ["retrieve", "compare"]
    assert any("group" in row for r in out["results"]
               for row in r["rows"])
