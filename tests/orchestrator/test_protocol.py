"""Tests for the plan protocol (ADR 0036): interpret -> confirm ->
execute -> caption, with a scripted planner that misbehaves on cue."""

import json

from src.orchestrator.protocol import (
    IMPLEMENTED_OPS,
    MAX_AUTO_ROUNDS,
    READ_ONLY_OPS,
    ProtocolSession,
    caption_turn,
    continue_rounds,
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

    def test_infra_errors_name_the_broken_thing(self):
        """Live find (2026-08-20): 'may be unavailable' hid 'Delta
        table does not exist' — the admin guessed between a paused
        capacity and a broken shortcut. The cause is named now."""
        def dying_kql(query, params):
            raise RuntimeError(
                '{"error": {"@message": "Query execution has resulted '
                'in error: Delta table does not exist: graph_nodes"}}')
        s = ProtocolSession()
        out = execute_confirmed(
            s, {"components": [
                {"op": "census", "params": {"kind": "metric"}}]},
            dying_kql)
        err = out[0]["error"]
        assert "Delta table does not exist" in err
        assert "capacity paused" in err and "shortcut" in err

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

    def test_every_result_carries_a_stamped_headline(self):
        """spec:E6 ENFORCED half: the quantitative sentence is code-
        stamped onto every result at the protocol layer — all surfaces
        inherit it; no count reaches the user only through LLM prose."""
        s = ProtocolSession()
        s.ops.note_user(f"{REF_A} {REF_B}")
        outs = execute_confirmed(s, PLAN_OK, fake_kql)
        for o in outs:
            if "result" in o:
                assert "row(s)." in o["result"]["headline"]
                assert o["result"]["headline"].startswith(o["result"]["ref"])

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


class TestAutoContinue:
    """The bounded read-only loop (Sunny's verdict, 2026-08-20): 0035's
    intelligence shape inside 0036's honesty frame. These tests prove
    the BOUNDS — the error mode is one more visible read-only hop or an
    honest exhaustion — never that the loop is smart (that is MEASURED,
    devtools/answer_evals.py)."""

    def _base(self):
        s = ProtocolSession()
        s.ops.note_user(f"{REF_A} {REF_B}")
        outputs = execute_confirmed(s, PLAN_OK, fake_kql)
        return s, outputs

    def test_answered_verdict_stops_immediately(self):
        s, outputs = self._base()
        n = len(outputs)
        loop = continue_rounds(s, "q", outputs, scripted_planner(
            [{"answered": True}]), fake_kql)
        assert loop["rounds"] == [] and not loop["exhausted"]
        assert len(outputs) == n            # nothing ran

    def test_one_read_only_round_then_answered(self):
        s, outputs = self._base()
        n = len(outputs)
        loop = continue_rounds(s, "q", outputs, scripted_planner([
            {"answered": False, "components": [
                {"op": "retrieve", "params": {"ids": [REF_A]},
                 "note": "need the record"}]},
            {"answered": True},
        ]), fake_kql)
        assert len(loop["rounds"]) == 1 and not loop["exhausted"]
        assert len(outputs) == n + 1        # the hop is displayed
        new = outputs[-1]
        assert new["component"]["auto_round"] == 1
        assert "headline" in new["result"]  # stamped like every hop

    def test_non_read_only_op_is_refused_in_the_executor(self):
        """The bound lives in code, not prompt: a write-flavored op
        proposed by the loop is refused BEFORE validation, refusal
        displayed, nothing executed."""
        s, outputs = self._base()
        loop = continue_rounds(s, "q", outputs, scripted_planner([
            {"answered": False, "components": [
                {"op": "update", "params": {"id": REF_A}}]},
            {"answered": True},
        ]), fake_kql)
        refused = loop["rounds"][0]["outputs"][0]
        assert "error" in refused
        assert "read-only" in refused["error"]
        assert "writes always confirm" in refused["error"]

    def test_rounds_are_bounded_then_honest_exhaustion(self):
        s, outputs = self._base()
        never_satisfied = [{"answered": False, "components": [
            {"op": "retrieve", "params": {"ids": [REF_A]}}]}] * 99
        loop = continue_rounds(s, "q", outputs,
                               scripted_planner(never_satisfied), fake_kql)
        assert len(loop["rounds"]) == MAX_AUTO_ROUNDS
        assert loop["exhausted"] is True
        assert loop["status_line"].startswith("auto-continue:")

    def test_read_only_set_is_pinned_to_the_implemented_ops(self):
        """Today every implemented op is read-only; the day that stops
        being true, this test forces a conscious decision."""
        assert set(IMPLEMENTED_OPS) == set(READ_ONLY_OPS)

    def test_duplicate_component_is_refused_anti_flail(self):
        """Suite finding (2026-08-20): three identical semantic
        searches in three rounds. Repetition is refused in code."""
        s, outputs = self._base()
        loop = continue_rounds(s, "q", outputs, scripted_planner([
            {"answered": False, "components": [
                {"op": "retrieve", "params": {"ids": [REF_A]}}]},
            {"answered": False, "components": [
                {"op": "retrieve", "params": {"ids": [REF_A]}}]},
            {"answered": True},
        ]), fake_kql)
        second = loop["rounds"][1]["outputs"][0]
        assert "error" in second
        assert "already ran this turn" in second["error"]

    def test_trace_ops_stay_inside_the_read_only_whitelist(self):
        s, outputs = self._base()
        continue_rounds(s, "q", outputs, scripted_planner([
            {"answered": False, "components": [
                {"op": "retrieve", "params": {"ids": [REF_A]}},
                {"op": "census", "params": {"kind": "metric"}}]},
            {"answered": True},
        ]), fake_kql)
        auto_ops = {o["component"]["op"] for o in outputs
                    if o["component"].get("auto_round")}
        assert auto_ops and auto_ops <= set(READ_ONLY_OPS)

    def test_replay_same_decisions_same_catalog_identical_trace(self):
        """Floor-1 clause 4 (HANDOFF_ANSWER_LOOP): scripted decisions +
        fixed catalog ⇒ byte-identical trace."""
        import json as _j
        traces = []
        for _ in range(2):
            s, outputs = self._base()
            continue_rounds(s, "q", outputs, scripted_planner([
                {"answered": False, "components": [
                    {"op": "retrieve", "params": {"ids": [REF_A]}}]},
                {"answered": True},
            ]), fake_kql)
            traces.append(_j.dumps(outputs, sort_keys=True))
        assert traces[0] == traces[1]

    def test_typed_verdict_ships_beside_the_prose(self):
        """The self-declaration the grader cross-checks; a floored
        caption can never claim answered."""
        s, outputs = self._base()
        out = caption_turn(s, outputs, scripted_planner(
            [{"caption": "R3 compares the two shown definitions.",
              "answered": True}]), question="q")
        assert out["answered"] is True
        out2 = caption_turn(s, outputs, scripted_planner(
            [{"caption": "There are 99 metrics.", "answered": True},
             {"caption": "There are 99 metrics.", "answered": True}]),
            question="q")
        assert out2["caption_corrected"] and out2["answered"] is False

    def test_caption_receives_the_question_and_answer_contract(self):
        s, outputs = self._base()
        seen = {}

        def capture(messages, tools, tool_choice=None):
            seen["system"] = messages[-2]["content"]
            seen["user"] = messages[-1]["content"]
            return scripted_planner([{"caption": "R1 answers it."}])(
                messages, tools, tool_choice)

        caption_turn(s, outputs, capture,
                     question="how is X defined")
        assert "how is X defined" in seen["user"]
        assert "ANSWER the user's question" in seen["system"]


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
