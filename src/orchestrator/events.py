"""Flywheel capture at the pick (ADR 0023/0031/0032).

The human's pick is disambiguation AND endorsement — captured the
moment it happens, by code. v1 sink: local JSONL (append-only, crash-
safe); the rows already speak the gov_usage_events contract so the
production sink (Eventhouse ingest or lakehouse writer) is a transport
swap, not a redesign.
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
