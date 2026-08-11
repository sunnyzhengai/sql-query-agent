"""Tests for the agent loop (ADR 0035): the LLM converses via scripted
tool calls; code dispatches, bounds, and stamps the Basis."""

import json

from src.orchestrator.agent import MAX_TOOL_ROUNDS, SYSTEM_PROMPT, run_turn
from src.orchestrator.tools import Session
from tests.orchestrator.test_tools import REF_A, REF_B, STEP_1, fake_kql


def scripted_api(script):
    """Each entry: list of (tool, args) to call, or a final string."""
    it = iter(script)

    def call(messages, tools):
        step = next(it)
        if isinstance(step, str):
            return {"role": "assistant", "content": step}
        return {"role": "assistant", "content": None, "tool_calls": [
            {"id": f"c{i}", "type": "function",
             "function": {"name": name, "arguments": json.dumps(args)}}
            for i, (name, args) in enumerate(step)]}
    return call


class TestLoop:
    def test_search_then_answer_with_stamped_basis(self):
        api = scripted_api([
            [("search_catalog", {"phrase": "ed sepsis"})],
            "ED Sepsis Screening tracks sepsis in the ED.",
        ])
        history = []
        turn = run_turn(history, "how is ed sepsis calculated?",
                        api, fake_kql, Session())
        assert turn.answer.startswith("ED Sepsis Screening")
        assert "search('ed sepsis') -> 2 candidates shown" in turn.basis
        assert history[0]["content"] == SYSTEM_PROMPT
        assert history[-1]["role"] == "assistant"

    def test_same_logic_flow_end_to_end(self):
        # the Q2 shape: search both, verify by computation, answer
        api = scripted_api([
            [("search_catalog", {"phrase": "ed sepsis screening"})],
            [("check_same_logic", {"ids": [REF_A, REF_B]})],
            "No — their calculations are two distinct definitions.",
        ])
        session = Session()
        session.note_user(REF_B)      # the user named the second metric
        turn = run_turn([], f"does ED Sepsis Screening use the same "
                        f"logic as {REF_B}?", api, fake_kql, session)
        assert "two distinct definitions" in turn.answer
        assert "same_logic(2 ids) -> 2 distinct" in turn.basis

    def test_guarantee_violation_is_visible_and_recoverable(self):
        # model tries an unsurfaced id; error returns AS a tool result,
        # model recovers by searching; the failed attempt stays in basis
        api = scripted_api([
            [("get_facts", {"id": REF_A})],           # not surfaced yet
            [("search_catalog", {"phrase": "ed sepsis"}),
             ("get_facts", {"id": REF_A})],           # now legitimate
            "Here are the facts.",
        ])
        turn = run_turn([], "tell me about that sepsis metric",
                        api, fake_kql, Session())
        assert "error" in turn.trace[0]["result"]
        assert turn.trace[2]["result"]["kind"] == "metric"
        assert "-> error" in turn.basis               # disclosed, not hidden
        assert f"facts[{REF_A}]" in turn.basis

    def test_no_tools_no_fabricated_basis(self):
        turn = run_turn([], "hello", scripted_api(["Ask me about metrics."]),
                        fake_kql, Session())
        assert turn.basis == "no tools consulted"

    def test_tool_round_cap_ends_the_turn_honestly(self):
        api = scripted_api(
            [[("search_catalog", {"phrase": "x"})]] * (MAX_TOOL_ROUNDS + 2))
        turn = run_turn([], "loop forever", api, fake_kql, Session())
        assert "tool budget" in turn.answer

    def test_history_carries_context_across_turns(self):
        history, session = [], Session()
        run_turn(history, "how is ed sepsis calculated?", scripted_api([
            [("search_catalog", {"phrase": "ed sepsis"})], "Answer one.",
        ]), fake_kql, session)
        # second turn: the model reads STEP_1 surfaced in turn one —
        # permitted because Session persists across the conversation
        turn2 = run_turn(history, "show me its sql", scripted_api([
            [("get_facts", {"id": STEP_1})], "Here is the SQL.",
        ]), fake_kql, session)
        assert turn2.trace[0]["result"]["kind"] == "step"
        roles = [m["role"] for m in history]
        assert roles.count("user") == 2 and roles[0] == "system"
