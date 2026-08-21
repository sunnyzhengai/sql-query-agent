"""Cage tests for the one-mind turn engine (ADR 0051, Floor 1).

These prove the BOUNDS — never that the mind is smart (that is
MEASURED by devtools/answer_evals.py): read-only refusal, anti-flail,
round cap with honest exhaustion, full evidence into ONE persistent
history, graceful compaction that never drops headlines, the caption
gate at the boundary, and the machine-verified verdict quote."""

import json

from src.orchestrator.turn_engine import (
    ENGINE_TOOLS,
    EngineSession,
    run_turn,
)
from tests.orchestrator.test_tools import REF_A, fake_kql


def scripted_engine(steps):
    """chat_api producing scripted assistant messages. Each step is
    either {"text": ...} (plain answer), {"calls": [(name, args), ...]}
    (tool calls), or {"verdict": {...}} consumed by the forced verdict
    call."""
    it = iter(steps)

    def call(messages, tools, tool_choice=None):
        step = next(it)
        if tool_choice is not None:            # the forced verdict form
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": "v1", "type": "function",
                 "function": {"name": "file_verdict",
                              "arguments": json.dumps(
                                  step.get("verdict", {}))}}]}
        if "calls" in step:
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": f"c{i}", "type": "function",
                 "function": {"name": name,
                              "arguments": json.dumps(args)}}
                for i, (name, args) in enumerate(step["calls"])]}
        return {"role": "assistant", "content": step["text"],
                "tool_calls": []}
    return call


GOOD_QUOTE = "measures ED Sepsis Screening"    # verbatim in fake rows


class TestLoop:
    def test_search_then_answer_full_rows_in_history(self):
        s = EngineSession()
        out = run_turn(s, "what exists for ed sepsis?", scripted_engine([
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"text": "Two candidates are shown in R1."},
            {"verdict": {"answered": True, "evidence_quote": GOOD_QUOTE}},
        ]), fake_kql)
        assert out["rounds"] == 1 and not out["exhausted"]
        assert out["outputs"][0]["result"]["headline"].startswith("R1:")
        tool_msgs = [m for m in s.history if m.get("role") == "tool"]
        payload = json.loads(tool_msgs[0]["content"])
        assert payload["rows"] and payload["headline"]   # FULL evidence
        # P2: the whole exchange persists in ONE history
        roles = [m["role"] for m in s.history]
        assert roles.count("tool") == 1 and roles[-1] == "assistant"

    def test_memory_across_turns_is_the_same_history(self):
        s = EngineSession()
        run_turn(s, "find ed sepsis", scripted_engine([
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"text": "Shown."}, {"verdict": {"answered": False}},
        ]), fake_kql)
        n_before = len(s.history)
        out2 = run_turn(s, "retrieve the first one", scripted_engine([
            {"calls": [("retrieve", {"ids": [REF_A]})]},
            {"text": "Retrieved."}, {"verdict": {"answered": False}},
        ]), fake_kql)
        # the id surfaced in turn 1 is retrievable in turn 2 (read
        # guarantee crosses turns because the SESSION persists)
        assert "result" in out2["outputs"][0]
        assert len(s.history) > n_before        # same growing history

    def test_write_flavored_tool_refused_in_dispatch(self):
        s = EngineSession()
        out = run_turn(s, "q", scripted_engine([
            {"calls": [("update", {"id": REF_A})]},
            {"text": "ok"}, {"verdict": {"answered": False}},
        ]), fake_kql)
        assert "read-only" in out["outputs"][0]["error"]
        assert "plan-confirm" in out["outputs"][0]["error"]

    def test_anti_flail_duplicate_becomes_an_observed_error(self):
        s = EngineSession()
        out = run_turn(s, "q", scripted_engine([
            {"calls": [("search", {"phrase": "x", "mode": "exact"}),
                       ("search", {"phrase": "x", "mode": "exact"})]},
            {"text": "done"}, {"verdict": {"answered": False}},
        ]), fake_kql)
        assert "already ran this turn" in out["outputs"][1]["error"]
        # P6: the refusal went INTO the conversation as a tool result
        tool_payloads = [json.loads(m["content"]) for m in s.history
                        if m.get("role") == "tool"]
        assert any("already ran" in str(p.get("error")) for p in tool_payloads)

    def test_round_cap_exhausts_honestly(self):
        s = EngineSession()
        steps = [{"calls": [("search", {"phrase": f"p{i}",
                                        "mode": "semantic"})]}
                 for i in range(20)]
        steps.append({"verdict": {"answered": False}})
        out = run_turn(s, "q", scripted_engine(steps), fake_kql)
        assert out["exhausted"] and out["rounds"] == 8
        assert "tool budget" in out["answer"]
        assert out["answered"] is False

    def test_infra_failure_is_an_observed_result(self):
        def dying_kql(query, params):
            raise RuntimeError(
                '{"error": {"@message": "Delta table does not exist"}}')
        s = EngineSession()
        out = run_turn(s, "q", scripted_engine([
            {"calls": [("census", {"kind": "metric"})]},
            {"text": "The store is unreachable."},
            {"verdict": {"answered": False}},
        ]), dying_kql)
        err = out["outputs"][0]["error"]
        assert "Delta table does not exist" in err
        assert "capacity paused" in err


class TestBoundary:
    def test_verdict_requires_machine_verified_quote(self):
        s = EngineSession()
        out = run_turn(s, "q", scripted_engine([
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"text": "It is the screening metric."},
            {"verdict": {"answered": True,
                         "evidence_quote": "totally invented quote of "
                                           "sufficient length"}},
        ]), fake_kql)
        assert out["answered"] is False
        out2 = run_turn(EngineSession(), "q", scripted_engine([
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"text": "It is the screening metric."},
            {"verdict": {"answered": True,
                         "evidence_quote": GOOD_QUOTE}},
        ]), fake_kql)
        assert out2["answered"] is True

    def test_over_claiming_answer_is_floored_by_the_gate(self):
        s = EngineSession()
        out = run_turn(s, "how many?", scripted_engine([
            {"calls": [("search", {"phrase": "nope", "mode": "exact"})]},
            {"text": "There are 999 metrics in the catalog."},
            {"text": "There are 999 metrics in the catalog."},  # retry
            {"verdict": {"answered": True,
                         "evidence_quote": GOOD_QUOTE}},
        ]), fake_kql)
        assert out["caption_corrected"]
        assert out["answer"].startswith("Results as displayed.")
        assert out["answered"] is False     # floored can never claim

    def test_compaction_keeps_headline_and_totals(self):
        from src.orchestrator import turn_engine
        s = EngineSession()
        s.history = [{"role": "system", "content": "sys"}]
        for i in range(6):
            s.history.append({
                "role": "tool", "tool_call_id": f"t{i}",
                "content": json.dumps({
                    "ref": f"R{i}", "headline": f"R{i}: census — 28 row(s).",
                    "rows_total": 28,
                    "rows": [{"d": "x" * 500}] * 200})})
        old_budget = turn_engine.HISTORY_BUDGET_CHARS
        turn_engine.HISTORY_BUDGET_CHARS = 10_000
        try:
            turn_engine._compact_history(s.history)
        finally:
            turn_engine.HISTORY_BUDGET_CHARS = old_budget
        compacted = [json.loads(m["content"]) for m in s.history
                     if m.get("role") == "tool"
                     and "compacted" in str(m.get("content"))]
        assert compacted, "oldest results must compact under pressure"
        assert all(c["headline"] and c["rows_total"] == 28
                   for c in compacted)

    def test_replay_same_script_same_outputs(self):
        def once():
            s = EngineSession()
            return run_turn(s, "q", scripted_engine([
                {"calls": [("search", {"phrase": "ed sepsis",
                                       "mode": "semantic"})]},
                {"text": "Shown in R1."},
                {"verdict": {"answered": False}},
            ]), fake_kql)
        a, b = once(), once()
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_system_prompt_is_invariants_only_no_casebook():
    """P4 pin: no question-family vocabulary in the engine prompt."""
    from src.orchestrator.turn_engine import SYSTEM_PROMPT
    for banned in ("how is", "defined", "did you mean", "bridge",
                   "criteria", "pointer", "how many"):
        assert banned not in SYSTEM_PROMPT.lower(), banned
    assert len(ENGINE_TOOLS) == 4


PINNED_PROMPT_SHA = ("20781efb5545aebce28e7a1c402c5a09"
                     "684403f29048f5302a8d5ea3de9114b9")


class TestPGroup:
    """P-group verification (HANDOFF_ONE_MIND Verification section):
    prompt-capture instruments — assert what the model MUST see."""

    def test_p2_round_two_request_carries_round_one_full_results(self):
        captured = []

        def capturing(steps):
            inner = scripted_engine(steps)

            def call(messages, tools, tool_choice=None):
                captured.append({"messages": [dict(m) for m in messages],
                                 "tool_choice": tool_choice})
                return inner(messages, tools, tool_choice)
            return call

        s = EngineSession()
        run_turn(s, "q", capturing([
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"calls": [("retrieve", {"ids": [REF_A]})]},
            {"text": "done"},
            {"verdict": {"answered": False}},
        ]), fake_kql)
        # request #2 (after round 1 executed) must contain round 1's
        # FULL tool payload — rows included, headline included
        second_request = captured[1]["messages"]
        tool_msgs = [m for m in second_request if m.get("role") == "tool"]
        assert tool_msgs, "round-1 results must be in the round-2 request"
        payload = json.loads(tool_msgs[0]["content"])
        assert payload["rows"], "FULL rows, not a compacted stub"
        assert payload["headline"]

    def test_p3_no_forced_tool_choice_inside_the_loop(self):
        captured = []

        def capturing(steps):
            inner = scripted_engine(steps)

            def call(messages, tools, tool_choice=None):
                captured.append(tool_choice)
                return inner(messages, tools, tool_choice)
            return call

        s = EngineSession()
        run_turn(s, "q", capturing([
            {"calls": [("search", {"phrase": "x", "mode": "exact"})]},
            {"text": "done"},
            {"verdict": {"answered": False}},
        ]), fake_kql)
        # every loop call unforced; exactly ONE forced call (verdict)
        forced = [c for c in captured if c is not None]
        assert len(forced) == 1
        assert forced[0]["function"]["name"] == "file_verdict"
        assert captured[-1] is not None      # the forced one is last

    def test_p6_turn_continues_after_an_observed_error(self):
        calls_seen = []

        def flaky_kql(query, params):
            calls_seen.append(query)
            if len(calls_seen) == 1:
                raise RuntimeError('{"error": {"@message": "blip"}}')
            return fake_kql(query, params)

        s = EngineSession()
        out = run_turn(s, "q", scripted_engine([
            {"calls": [("census", {"kind": "metric"})]},
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"text": "recovered"},
            {"verdict": {"answered": False}},
        ]), flaky_kql)
        assert "error" in out["outputs"][0]          # observed
        assert "result" in out["outputs"][1]         # and continued
        assert not out["exhausted"]

    def test_p4_thesis_prompt_hash_is_pinned(self):
        """The thesis test runs with the prompt content-hash PINNED —
        a pass that needed new prompt lines is visible as a hash change
        and fails here. Changing the prompt is a conscious act: update
        the pin AND note it in the Round-4 RESULTS log."""
        import hashlib

        from src.orchestrator.turn_engine import SYSTEM_PROMPT
        assert hashlib.sha256(
            SYSTEM_PROMPT.encode()).hexdigest() == PINNED_PROMPT_SHA
