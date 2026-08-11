"""Agent-events ingest step: surfaces' JSONL -> gov_turn_events /
gov_feedback_events rows (admin telemetry phase 1, 2026-08-11).

The web surface and CLI append TurnEvent/FeedbackEvent JSONL (locally,
or to OneLake Files via OneLakeJsonlSink). This step's pure transforms
flatten them onto the Delta contracts — decision flags become columns
so the admin report slices on them directly — and the dedupe helper
makes re-ingestion idempotent (the files are never truncated by us).

Pure and offline-testable; the notebook wrapper does only Spark IO.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class AgentEventsOutput:
    turn_rows: "list[dict]" = field(default_factory=list)
    feedback_rows: "list[dict]" = field(default_factory=list)
    malformed: int = 0


_DECISION_FLAGS = ("verified_by_tool", "llm_assembled",
                   "unverified_sameness_language", "search_only", "no_tools")


def _turn_row(e: dict) -> dict:
    decision = e.get("decision") or {}
    row = {
        "event_at": e["event_at"],
        "user_id": e.get("user_id", ""),
        "conversation_id": e.get("conversation_id", ""),
        "turn_index": int(e.get("turn_index", 0)),
        "question": e.get("question", ""),
        "tools_used": ",".join(e.get("tools_used") or []),
        "ids_read": ",".join(e.get("ids_read") or []),
        "basis": e.get("basis", ""),
        "answered": bool(e.get("answered", False)),
        "tool_errors": int(decision.get("tool_errors", 0)),
        "trace": json.dumps(e.get("trace") or []),
    }
    for flag in _DECISION_FLAGS:
        row[flag] = bool(decision.get(flag, False)) if decision else None
    return row


def _feedback_row(e: dict) -> dict:
    return {
        "event_at": e["event_at"],
        "user_id": e.get("user_id", ""),
        "conversation_id": e.get("conversation_id", ""),
        "turn_index": int(e.get("turn_index", 0)),
        "verdict": e["verdict"],
        "comment": e.get("comment", ""),
    }


def parse_agent_events(jsonl_lines: "list[str]") -> AgentEventsOutput:
    """Both event types ride the same files; the shape tells them apart
    (feedback has a verdict, turns have a question). Malformed lines are
    counted, never fatal — an event log must survive its own noise."""
    out = AgentEventsOutput()
    for line in jsonl_lines:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            if "verdict" in e:
                out.feedback_rows.append(_feedback_row(e))
            elif "question" in e:
                out.turn_rows.append(_turn_row(e))
            else:
                out.malformed += 1
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            out.malformed += 1
    return out


def event_key(row: dict) -> "tuple":
    return (row["conversation_id"], row["turn_index"], row["event_at"])


def dedupe_events(rows: "list[dict]",
                  existing_keys: "set[tuple]") -> "list[dict]":
    """Idempotent re-ingestion: drop rows already in the Delta table
    (by conversation/turn/timestamp) AND duplicates within the batch."""
    fresh, seen = [], set(existing_keys)
    for row in rows:
        k = event_key(row)
        if k in seen:
            continue
        seen.add(k)
        fresh.append(row)
    return fresh
