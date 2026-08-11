"""Tests for the agent-events ingest transforms (admin telemetry)."""

import json

from src.schemas import FEEDBACK_EVENTS, TURN_EVENTS
from src.steps.agent_events import (
    dedupe_events,
    event_key,
    parse_agent_events,
)


def turn_line(**over):
    e = {
        "event_at": "2026-08-11T12:00:00Z", "user_id": "sunny@aivia",
        "question": "how is ed sepsis calculated?",
        "tools_used": ["search_catalog", "get_facts"],
        "ids_read": ["reporting.USP_ED_Sepsis"],
        "basis": "search(...) -> 10; facts[...]", "answered": True,
        "conversation_id": "c1", "turn_index": 0,
        "decision": {"verified_by_tool": False, "llm_assembled": False,
                     "unverified_sameness_language": False,
                     "search_only": False, "no_tools": False,
                     "tool_errors": 0},
        "trace": [{"tool": "search_catalog", "args": {}, "result": "{}"}],
    }
    e.update(over)
    return json.dumps(e)


def feedback_line(**over):
    e = {"event_at": "2026-08-11T12:01:00Z", "user_id": "sunny@aivia",
         "conversation_id": "c1", "turn_index": 0,
         "verdict": "not_helpful", "comment": "wrong metric"}
    e.update(over)
    return json.dumps(e)


class TestParse:
    def test_both_types_from_one_stream(self):
        out = parse_agent_events([turn_line(), feedback_line(), "", "  "])
        assert len(out.turn_rows) == 1 and len(out.feedback_rows) == 1
        assert out.malformed == 0

    def test_rows_match_schemas(self):
        out = parse_agent_events([turn_line(), feedback_line()])
        assert set(out.turn_rows[0]) == {c[0] for c in TURN_EVENTS["columns"]}
        assert set(out.feedback_rows[0]) == {
            c[0] for c in FEEDBACK_EVENTS["columns"]}
        row = out.turn_rows[0]
        assert row["tools_used"] == "search_catalog,get_facts"
        assert row["verified_by_tool"] is False
        assert json.loads(row["trace"])[0]["tool"] == "search_catalog"

    def test_legacy_rows_without_decision_survive(self):
        legacy = turn_line()
        e = json.loads(legacy)
        del e["decision"], e["trace"], e["conversation_id"]
        out = parse_agent_events([json.dumps(e)])
        assert len(out.turn_rows) == 1
        assert out.turn_rows[0]["verified_by_tool"] is None
        assert out.turn_rows[0]["conversation_id"] == ""

    def test_noise_counted_never_fatal(self):
        out = parse_agent_events(["not json{", json.dumps({"x": 1}),
                                  turn_line()])
        assert out.malformed == 2 and len(out.turn_rows) == 1


class TestDedupe:
    def test_idempotent_reingestion(self):
        out = parse_agent_events([turn_line(), turn_line(),
                                  turn_line(turn_index=1)])
        existing = {event_key(out.turn_rows[0])}
        fresh = dedupe_events(out.turn_rows, existing)
        assert len(fresh) == 1                    # batch dup + existing dropped
        assert fresh[0]["turn_index"] == 1
