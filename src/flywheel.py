"""FLYWHEEL-1 — the 0056 mechanism, v1 (Sunny-authorized
2026-08-29): captured decision events become per-item usage
weights, cards disclose provenance, and the Ground-Truth Shelf
serves My definitions / My reports / My questions from the
existing TurnEvent store. Single-user; promotion mechanics (usage
threshold + steward veto, the ruled ladder) stub until the
multi-user store.

Event shapes counted (the four decision classes):
  confirm  — "[PLANNER] q" turns (a confirmed reading executed)
  run      — "[RUN] step_id" (the run button)
  prune    — "[PRUNE] q" (unchecked candidates)
  escalate — "[ESCALATE] q" (the developer door)
Engine-answered turns also count ids_read as reads (weak signal,
kept separate from confirms).
"""

from __future__ import annotations

import json
from pathlib import Path

_CLASSES = (("[PLANNER] ", "confirmed"), ("[RUN] ", "run"),
            ("[PRUNE] ", "pruned"), ("[ESCALATE] ", "escalated"))


def _iter_events(events_path: "Path | str"):
    p = Path(events_path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def usage_weights(events_path: "Path | str",
                  user: "str | None" = None) -> "dict[str, dict]":
    """id -> {confirmed, run, pruned, escalated, read} counts."""
    weights: "dict[str, dict]" = {}
    for ev in _iter_events(events_path):
        if user and ev.get("user_id") != user:
            continue
        q = str(ev.get("question") or "")
        bucket = next((b for pre, b in _CLASSES
                       if q.startswith(pre)), None)
        if bucket is None:
            bucket = "read" if ev.get("answered") else None
        if bucket is None:
            continue
        for rid in ev.get("ids_read") or []:
            w = weights.setdefault(str(rid), {
                "confirmed": 0, "run": 0, "pruned": 0,
                "escalated": 0, "read": 0})
            w[bucket] += 1
    return weights


def provenance_line(w: "dict | None") -> str:
    """The card's disclosure — usage facts + the standing truth
    that no official is designated (single-user v1; the promotion
    ladder fills this in when it lands)."""
    if not w or not any(w.get(k) for k in
                        ("confirmed", "run", "read")):
        return ""
    parts = []
    if w.get("confirmed"):
        parts.append(f"confirmed {w['confirmed']}×")
    if w.get("run"):
        parts.append(f"run {w['run']}×")
    if not parts and w.get("read"):
        parts.append(f"read {w['read']}×")
    if w.get("pruned"):
        parts.append(f"pruned {w['pruned']}×")
    return " · ".join(parts) + " — no official designated"


def my_shelf(events_path: "Path | str", user: str,
             limit: int = 8) -> dict:
    """The Ground-Truth Shelf v1: definitions, reports, questions —
    replay is a saved operation (the question re-posts)."""
    weights = usage_weights(events_path, user=user)

    def top(pred):
        rows = [(rid, w) for rid, w in weights.items() if pred(rid)]
        rows.sort(key=lambda x: -(x[1]["confirmed"] * 3
                                  + x[1]["run"] * 3 + x[1]["read"]))
        return [{"id": rid, "usage": provenance_line(w)}
                for rid, w in rows[:limit]]

    questions: "list[str]" = []
    seen = set()
    for ev in _iter_events(events_path):
        if ev.get("user_id") != user:
            continue
        q = str(ev.get("question") or "")
        for pre, _b in _CLASSES:
            if q.startswith(pre):
                q = q[len(pre):]
                break
        q = q.strip()
        if not q or q in seen or q.startswith("transform:"):
            continue
        seen.add(q)
        questions.append(q)
    return {
        "definitions": top(lambda r: not r.startswith(
            ("report:", "table:", "cluster:", "measure:"))),
        "reports": top(lambda r: r.startswith(("report:",
                                               "measure:"))),
        "questions": questions[-limit:][::-1],
    }
