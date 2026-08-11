"""Flywheel capture (ADR 0023/0031/0032) — two signals, two strengths.

PICK (weak signal, click-through): chosen from one-line candidates,
BEFORE reading the full answer — useful ranking data, not endorsement.
CONFIRMATION (strong signal, endorsement): the considered verdict
AFTER reading — "this IS the definition I'm using" (Sunny, 2026-08-09).
Weight derivation counts confirmations heavily, picks lightly.

Append-only discipline throughout (ADR 0023): a confirmation is a new
event, never an update. v1 sink: local JSONL; the rows speak the
gov_usage_events contract (its feedback column anticipated exactly
this), so the production sink is a transport swap.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class PickEvent:
    event_at: str            # ISO timestamp — supplied by the surface
    user_id: str
    question: str
    token: str
    candidates_shown: "tuple[str, ...]"   # node_ids, ranked as displayed
    picked_node_id: "str | None"          # None = user declined all
    picked_ref: "str | None"
    total_matches: int

    def to_usage_event_row(self) -> dict:
        """Project onto the gov_usage_events contract (ADR 0023)."""
        return {
            "event_at": self.event_at,
            "user_id": self.user_id,
            "user_name": "",
            "department": "",
            "question": self.question,
            "metric_id": self.picked_ref,
            "outcome": "answered" if self.picked_node_id else "refused",
            "feedback": "none",
        }


class JsonlEventSink:
    def __init__(self, path: "str | Path") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: PickEvent) -> None:
        with self.path.open("a") as f:
            f.write(json.dumps(asdict(event)) + "\n")


@dataclass(frozen=True)
class TurnEvent:
    """ADR 0035 flywheel grain: one conversational turn — the question,
    the tools consulted (the code-stamped trace), the ids read, and the
    DECISION SHAPE (Sunny, 2026-08-11): when a user says "this is not
    the solution I wanted", the record must say whether the answer's
    load-bearing decisions were made by deterministic tools or by the
    LLM in its own head — so no-solution patterns attribute to the
    right component. Append-only as ever."""

    event_at: str
    user_id: str
    question: str
    tools_used: "tuple[str, ...]"
    ids_read: "tuple[str, ...]"
    basis: str
    answered: bool
    conversation_id: str = ""
    turn_index: int = 0
    decision: "dict | None" = None      # see decision_shape()
    trace: "tuple[dict, ...]" = ()      # full tool calls (args + results)


def decision_shape(trace: "list[dict]", answer: str) -> dict:
    """Code-computed classification of WHO made this turn's decisions.

    - verified_by_tool: a same/different-logic verdict came from
      check_same_logic (the engine decided)
    - llm_assembled: the answer draws on 2+ fact sets with no verify
      call — comparisons/intersections computed by the LLM in memory
      (legitimate for small facts per ADR 0035, but recorded so failure
      patterns can point here)
    - unverified_sameness_language: the answer speaks of same/identical/
      differ while NO verify tool ran — the highest-risk LLM decision
    - search_only / no_tools: the answer rests on a candidate list only,
      or on nothing (refusals, smalltalk)
    - tool_errors: tools refused or failed this turn (visible recovery)
    """
    tools = [t["tool"] for t in trace]
    reads = sum(1 for t in tools if t in ("get_facts", "list_steps"))
    verified = "check_same_logic" in tools
    sameness_words = any(w in answer.lower() for w in (
        "same logic", "identical", "differ", "not the same", "share the same"))
    return {
        "verified_by_tool": verified,
        "llm_assembled": reads >= 2 and not verified,
        "unverified_sameness_language": sameness_words and not verified,
        "search_only": bool(tools) and reads == 0 and not verified,
        "no_tools": not tools,
        "tool_errors": sum(1 for t in trace if "error" in t["result"]),
    }


@dataclass(frozen=True)
class FeedbackEvent:
    """The user's verdict on a turn ("this is/isn't what I wanted"),
    joined to the TurnEvent by (conversation_id, turn_index) — the
    other half of decision attribution."""

    event_at: str
    user_id: str
    conversation_id: str
    turn_index: int
    verdict: str             # helpful | not_helpful
    comment: str = ""


@dataclass(frozen=True)
class ConfirmEvent:
    """The strong signal: verdict after reading the narrated answer."""

    event_at: str
    user_id: str
    question: str
    picked_node_id: str
    picked_ref: str
    verdict: str             # confirmed | rejected

    def to_usage_event_row(self) -> dict:
        return {
            "event_at": self.event_at,
            "user_id": self.user_id,
            "user_name": "",
            "department": "",
            "question": self.question,
            "metric_id": self.picked_ref,
            "outcome": "answered",
            "feedback": self.verdict,
        }
