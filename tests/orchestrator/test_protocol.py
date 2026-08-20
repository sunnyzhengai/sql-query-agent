"""Tests for the plan protocol (ADR 0036): interpret -> confirm ->
execute -> caption, with a scripted planner that misbehaves on cue."""

import json

from src.orchestrator.protocol import (
    ProtocolSession,
    caption_turn,
    execute_confirmed,
    propose_turn,
    validate_component,
)
from tests.orchestrator.test_tools import REF_A, REF_B, fake_kql


def scripted_planner(payloads):
    """chat_api that returns each payload as the forced tool call."""
    it = iter(payloads)

    def call(messages, tools, tool_choice=None):
        name = tools[0]["function"]["name"]
        assert tool_choice["function"]["name"] == name   # forced
        return {"role": "assistant", "content": None, "tool_calls": [
            {"id": "c1", "type": "function",
             "function": {"name": name,
                          "arguments": json.dumps(next(it))}}]}
    return call


PLAN_OK = {"components": [
    {"op": "search", "params": {"phrase": "ED sepsis", "mode": "semantic"},
     "note": "find candidates"},
    {"op": "retrieve", "params": {"ids": [REF_A, REF_B]},
     "note": "full records"},
    {"op": "compare", "params": {"refs": ["$2"]}, "note": "same logic?"},
]}


class TestPropose:
    def test_valid_plan_passes_validation(self):
        s = ProtocolSession()
        plan = propose_turn(s, "does A share B's logic?",
                            scripted_planner([PLAN_OK]))
        assert [c["valid"] for c in plan["components"]] == [True] * 3
        assert s.history[0]["content"].startswith("You translate")

    def test_invalid_components_trigger_one_repair_round(self):
        bad = {"components": [{"op": "search",
                               "params": {"phrase": "x", "mode": "fuzzy"}}]}
        s = ProtocolSession()
        plan = propose_turn(s, "q", scripted_planner([bad, PLAN_OK]))
        assert all(c["valid"] for c in plan["components"])   # repaired

    def test_unrepaired_invalid_is_shown_not_dropped(self):
        bad = {"components": [{"op": "teleport", "params": {}}]}
        s = ProtocolSession()
        plan = propose_turn(s, "q", scripted_planner([bad, bad]))
        assert plan["components"][0]["valid"] is False
        assert "unknown operation" in plan["components"][0]["invalid_reason"]

    def test_clarification_instead_of_components(self):
        s = ProtocolSession()
        plan = propose_turn(s, "how is it defined?", scripted_planner([
            {"components": [],
             "clarification": "Which metric do you mean?"}]))
        assert plan["components"] == []
        assert "Which metric" in plan["clarification"]

    def test_census_component_validates_and_normalizes_plural(self):
        c = validate_component({"op": "census",
                                "params": {"kind": "Metrics"}}, 1)
        assert c["valid"] and c["params"]["kind"] == "metric"
        c = validate_component({"op": "census",
                                "params": {"kind": "dashboards"}}, 1)
        assert not c["valid"] and "metric, step, term" in c["invalid_reason"]

    def test_census_executes_and_declares_exact_count(self):
        from tests.orchestrator.test_tools import fake_kql
        s = ProtocolSession()
        outs = execute_confirmed(
            s, {"components": [{"op": "census",
                                "params": {"kind": "metrics"}}]}, fake_kql)
        r = outs[0]["result"]
        assert r["complete"] is True and len(r["rows"]) == 2
        assert "count is exact" in r["universe"]

    def test_approved_unbuilt_ops_fail_honestly(self):
        c = validate_component({"op": "traverse", "params": {}}, 1)
        assert not c["valid"] and "not yet built" in c["invalid_reason"]
        c = validate_component({"op": "update", "params": {}}, 1)
        assert not c["valid"] and "access-control" in c["invalid_reason"]


class TestExecuteConfirmed:
    def test_nothing_runs_at_propose_time(self):
        calls = []
        def counting_kql(q, p):
            calls.append(q)
            return fake_kql(q, p)
        s = ProtocolSession()
        propose_turn(s, "q", scripted_planner([PLAN_OK]))
        assert calls == []                        # interpret only

    def test_confirmed_plan_executes_in_order_with_plan_refs(self):
        s = ProtocolSession()
        s.ops.note_user(f"{REF_A} {REF_B}")
        out = execute_confirmed(s, PLAN_OK, fake_kql)
        assert "result" in out[0] and out[0]["result"]["op"] == "search"
        assert out[1]["result"]["op"] == "retrieve"
        cmp_rows = out[2]["result"]["rows"]       # $2 -> retrieve output
        groups = [r for r in cmp_rows if "group" in r]
        assert len(groups) == 2                   # SELECT 1 vs SELECT 2

    def test_human_edits_are_honored(self):
        s = ProtocolSession()
        edited = {"components": [
            {"op": "search",
             "params": {"phrase": "Scores", "mode": "exact"},   # human
             "note": "user switched to exact"}]}
        out = execute_confirmed(s, edited, fake_kql)
        assert out[0]["result"]["complete"] is True
        assert out[0]["result"]["params"]["mode"] == "exact"

    def test_errors_are_visible_per_component(self):
        s = ProtocolSession()          # REF_A never surfaced/named
        plan = {"components": [
            {"op": "retrieve", "params": {"ids": [REF_A]}}]}
        out = execute_confirmed(s, plan, fake_kql)
        assert "not been surfaced" in out[0]["error"]

    def test_forward_plan_ref_fails_visibly(self):
        s = ProtocolSession()
        plan = {"components": [
            {"op": "compare", "params": {"refs": ["$5"]}}]}
        out = execute_confirmed(s, plan, fake_kql)
        assert "has not produced a result" in out[0]["error"]


class TestCaption:
    def test_caption_inputs_stamped_and_suggestions_validated(self):
        s = ProtocolSession()
        s.ops.note_user(f"{REF_A} {REF_B}")
        outputs = execute_confirmed(s, PLAN_OK, fake_kql)
        raw = {"caption": "R3 shows two distinct definitions.",
               "suggestions": [
                   {"op": "compare",
                    "params": {"refs": ["R2"], "aspect": "tables"}},
                   {"op": "teleport", "params": {}}]}
        out = caption_turn(s, outputs, scripted_planner([raw]))
        assert out["caption"].startswith("R3")
        assert out["caption_inputs"] == ["R1", "R2", "R3"]   # code-stamped
        assert len(out["suggestions"]) == 1                  # invalid dropped
        assert out["suggestions"][0]["params"]["aspect"] == "tables"

    def test_caption_gate_retry_then_floor(self):
        """spec:E6 mechanical: an over-claiming caption gets one
        corrective retry; still dirty → the deterministic floor ships,
        visibly corrected."""
        s = ProtocolSession()
        s.ops.note_user(f"{REF_A} {REF_B}")
        outputs = execute_confirmed(s, PLAN_OK, fake_kql)
        bad = {"caption": "There are 99 metrics in every result."}
        out = caption_turn(s, outputs, scripted_planner([bad, bad]))
        assert out["caption_corrected"] is True
        assert any("99" in v for v in out["caption_violations"])
        assert out["caption"].startswith("Results as displayed.")

    def test_caption_gate_retry_can_recover(self):
        s = ProtocolSession()
        s.ops.note_user(f"{REF_A} {REF_B}")
        outputs = execute_confirmed(s, PLAN_OK, fake_kql)
        bad = {"caption": "There are 99 metrics."}
        good = {"caption": "R3 compares the two definitions shown."}
        out = caption_turn(s, outputs, scripted_planner([bad, good]))
        assert out["caption_corrected"] is False
        assert out["caption"].startswith("R3 compares")


class TestResultPiping:
    """Live find (2026-08-13): the planner naturally writes
    retrieve {ids: "$1"} — pipe a search's results into retrieve.
    Data-shaped plumbing, now supported everywhere ids appear."""

    def test_retrieve_pipes_from_search(self):
        s = ProtocolSession()
        plan = {"components": [
            {"op": "search", "params": {"phrase": "Scores",
                                        "mode": "exact"}},
            {"op": "retrieve", "params": {"ids": "$1"}},   # scalar too
            {"op": "compare", "params": {"refs": "$2"}},
        ]}
        out = execute_confirmed(s, plan, fake_kql)
        assert out[1]["result"]["count"] == 2          # both family steps
        groups = [r for r in out[2]["result"]["rows"] if "group" in r]
        assert len(groups) == 1                        # respaced == same

    def test_forward_pipe_fails_visibly(self):
        s = ProtocolSession()
        plan = {"components": [
            {"op": "retrieve", "params": {"ids": ["$3"]}}]}
        out = execute_confirmed(s, plan, fake_kql)
        assert "has not produced a result" in out[0]["error"]
