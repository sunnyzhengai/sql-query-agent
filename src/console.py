"""CONSOLE-1 (ADR 0063 §3 — the Resolution Console / the Inbox).

Tier 2 v1 is NOT open chat: sessions start from machine-found
flags with computed evidence, and every action is a predefined
button — the 0056 verbs in uniform. The Inbox unifies the console
with the Write-Back Queue: stewards see flags to resolve and
business writes to approve; developers see technical writes to
approve. Every approval lands through the queue, graded, logged.

THE LANDING MAP IS DATA (0063's two invariants, mechanized the
trace-registry way): every verb this module accepts MUST have a
row here (no action without a landing), and every row carries its
grade (no landing without a grade). tests/test_console.py holds
totality — a verb without a row is a red test, not a runtime
surprise.

v1 honesty: decisions land as 0056 EVENTS (the same store the
flywheel reads); the flag disposition in the GRAPH updates on the
next pipeline run from those events, and DG writes ride the
stage-1 file exports — both recorded as the deliberate v1 shape,
not gaps.
"""

from __future__ import annotations

import json
from pathlib import Path

# verb -> where it lands + the grade + who may press it
# (0063 total landing map, verbatim landings)
LANDING_MAP: "dict[str, dict]" = {
    "certify": {
        "persona": "steward",
        "lands": "DG glossary/asset description via the Queue + "
                 "graph certification edge + flag disposition",
        "grade": "steward-certified",
        "needs_reason": False},
    "deny": {
        "persona": "steward",
        "lands": "graph testimony + flag disposition; DG only if "
                 "deprecating something previously synced",
        "grade": "asserted",
        "needs_reason": True},
    "delegate": {
        "persona": "steward",
        "lands": "delegation queue + notification; the delegate's "
                 "answer returns as testimony; the STEWARD lands "
                 "the conclusion",
        "grade": "asserted",
        "needs_reason": False},
    "compare": {
        "persona": "any",
        "lands": "nowhere permanent — evidence; its conclusion "
                 "lands via certify/deny",
        "grade": "evidence",
        "needs_reason": False},
    "approve_technical": {
        "persona": "developer",
        "lands": "the write lands to DG/PBI via the stage-1 file "
                 "export, publish-logged",
        "grade": "parsed-by-engine, approved-by-developer",
        "needs_reason": False},
    "fork": {
        "persona": "developer",
        "lands": "new variant node, enters differentiation "
                 "(the 0038 path)",
        "grade": "asserted, owner = creator",
        "needs_reason": False},
}

_DISPOSITION_VERBS = {"certify": "certified",
                      "deny": "denied",
                      "delegate": "delegated"}


class ConsoleRefusal(Exception):
    def __init__(self, reason_class: str, message: str) -> None:
        self.reason_class = reason_class
        super().__init__(message)


def check_action(verb: str, persona: str,
                 reason: str = "") -> dict:
    """The gate every act passes: the verb must have a landing row,
    the persona must match, a deny must carry its reason."""
    row = LANDING_MAP.get(verb)
    if row is None:
        raise ConsoleRefusal(
            "unknown_verb",
            f"{verb!r} has no landing row — no action without a "
            "landing (0063); the verb does not ship until it has "
            "one")
    if row["persona"] not in ("any", persona):
        raise ConsoleRefusal(
            "persona",
            f"{verb} is a {row['persona']} action — you are acting "
            f"as {persona}")
    if row["needs_reason"] and not reason.strip():
        raise ConsoleRefusal(
            "reason_required",
            "deny lands as testimony — it carries its reason, "
            "always")
    return row


def _console_events(events_path: "Path | str"):
    p = Path(events_path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        q = str(ev.get("question") or "")
        if q.startswith("[CONSOLE:"):
            yield ev


def effective_dispositions(events_path) -> "dict[str, dict]":
    """target_id -> the LATEST disposition-bearing console action
    (events fold in file order; the newest decision wins)."""
    out: "dict[str, dict]" = {}
    for ev in _console_events(events_path):
        d = ev.get("decision") or {}
        verb = str(d.get("verb") or "")
        if verb not in _DISPOSITION_VERBS \
                and verb != "approve_technical":
            continue
        for tid in ev.get("ids_read") or []:
            out[str(tid)] = {
                "verb": verb,
                "state": _DISPOSITION_VERBS.get(verb, "approved"),
                "by": str(ev.get("user_id") or ""),
                "persona": str(d.get("persona") or ""),
                "reason": str(d.get("reason") or ""),
                "grade": str(d.get("grade") or "")}
    return out


def inbox_state(run_kql, events_path, persona: str) -> dict:
    """The Inbox: flags to resolve (steward) + writes to approve
    (per persona) — flags from the live census, decision state
    folded from the event store."""
    from src.orchestrator.ops import OpsSession, op_census
    decided = effective_dispositions(events_path)
    flags = []
    for f in op_census("flag", run_kql, OpsSession()).rows:
        fid = str(f.get("id"))
        state = decided.get(fid)
        flags.append({
            "id": fid,
            "identity": f.get("identity"),
            "flag_class": f.get("flag_class"),
            "severity": f.get("severity"),
            "member_count": f.get("member_count"),
            "member_names": (f.get("member_names") or [])[:12],
            "why": f.get("description") or "",
            "store_disposition": f.get("disposition") or "open",
            "console_state": state,   # None = untouched
        })
    # open-first, then severity; decided items sink but stay visible
    flags.sort(key=lambda x: (x["console_state"] is not None,
                              str(x["severity"]),
                              str(x["identity"])))
    return {"persona": persona, "flags": flags,
            "landing_map": {v: {"lands": r["lands"],
                                "grade": r["grade"],
                                "persona": r["persona"]}
                            for v, r in LANDING_MAP.items()}}


def action_event(verb: str, target_id: str, persona: str,
                 user: str, reason: str, event_at: str) -> dict:
    """The 0056-shape decision event an act records — graded per
    the landing row, always."""
    row = check_action(verb, persona, reason)
    return {
        "event_at": event_at,
        "user_id": user,
        "question": f"[CONSOLE:{verb.upper()}] {target_id}",
        "tools_used": ("console",),
        "ids_read": (target_id,),
        "basis": f"resolution console — lands: {row['lands']}",
        "answered": True,
        "conversation_id": "console", "turn_index": -1,
        "decision": {"made_by": "console_action", "verb": verb,
                     "persona": persona, "reason": reason,
                     "grade": row["grade"],
                     "lands": row["lands"]},
        "trace": ({"tool": "console",
                   "args": {"verb": verb, "target": target_id},
                   "result": row["grade"]},),
    }
