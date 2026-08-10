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
