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
        # single-member flags only — multi-member certify OPENS
        # the CONSOLE-3 chooser and records one of the three
        # outcome verbs below
        "persona": "steward",
        "lands": "DG glossary/asset description via the Queue + "
                 "graph certification edge + flag disposition",
        "grade": "steward-certified",
        "needs_reason": False},
    # CONSOLE-3 (Sunny's glass: certify needs a TARGET and an
    # OUTCOME — the choice a steward actually makes)
    "certify_official": {
        "persona": "steward",
        "lands": "the chosen member becomes the name's canonical "
                 "bearer — glossary/asset update for THAT member "
                 "via the Queue + designation edge; the others "
                 "remain, flagged for differentiation",
        "grade": "steward-certified",
        "needs_reason": False, "needs_member": True},
    "differentiate_all": {
        "persona": "steward",
        "lands": "disposition resolves with NO official — every "
                 "member ruled a legitimate distinct purpose and "
                 "queued for its own label (the 0054 canonical "
                 "outcome); term updates/relations via the Queue",
        "grade": "steward-certified",
        "needs_reason": False},
    "certify_definition": {
        "persona": "steward",
        "lands": "the picked member's definition certified via the "
                 "Queue WITHOUT designating the name's official",
        "grade": "steward-certified",
        "needs_reason": False, "needs_member": True},
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
    "reopen": {
        # CONSOLE-5: a ruling is REOPENED by appending, never by
        # mutating the record — the reopen itself is testimony
        "persona": "any",
        "lands": "graph testimony that the prior ruling is under "
                 "review; the flag returns to the open queue "
                 "(the earlier decision stays in the record)",
        "grade": "asserted",
        "needs_reason": True},
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

_REOPEN_VERB = "reopen"

_DISPOSITION_VERBS = {"certify": "certified",
                      "certify_official": "official designated",
                      "differentiate_all": "differentiated",
                      "certify_definition": "definition certified",
                      "deny": "denied",
                      "delegate": "delegated"}


class ConsoleRefusal(Exception):
    def __init__(self, reason_class: str, message: str) -> None:
        self.reason_class = reason_class
        super().__init__(message)


def check_action(verb: str, persona: str, reason: str = "",
                 member_ids: "list[str] | None" = None) -> dict:
    """The gate every act passes: the verb must have a landing row,
    the persona must match, a deny must carry its reason, and a
    picker verb must carry its picked member (CONSOLE-3)."""
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
    if row.get("needs_member") and not (member_ids or []):
        raise ConsoleRefusal(
            "member_required",
            f"{verb} certifies a PICKED member — choose which one "
            "you mean")
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
        if verb == _REOPEN_VERB:
            for tid in list(ev.get("ids_read") or [])[:1]:
                out.pop(str(tid), None)   # back to the open queue
            continue
        if verb not in _DISPOSITION_VERBS \
                and verb != "approve_technical":
            continue
        ids = list(ev.get("ids_read") or [])
        for tid in ids[:1]:           # the flag; members ride the
            out[str(tid)] = {          # decision, not the fold key
                "verb": verb,
                "state": _DISPOSITION_VERBS.get(verb, "approved"),
                "by": str(ev.get("user_id") or ""),
                "at": str(ev.get("event_at") or "")[:19],
                "persona": str(d.get("persona") or ""),
                "reason": str(d.get("reason") or ""),
                "targets": [str(x) for x in
                            (d.get("targets") or [])],
                "grade": str(d.get("grade") or "")}
    return out


def inbox_state(run_kql, events_path, persona: str) -> dict:
    """The Inbox: flags to resolve (steward) + writes to approve
    (per persona) — flags from the live census, decision state
    folded from the event store."""
    from src.orchestrator.ops import (
        OpsSession,
        _member_labels,
        op_census,
    )
    from src.orchestrator.tools import GOV_FLAG_MEMBER_NAMES_QUERY
    decided = effective_dispositions(events_path)
    # CONSOLE-3: the certify chooser picks by MEMBER — ids ride
    # each flag alongside the qualified labels
    members_by_cluster: "dict[str, list]" = {}
    try:
        for mr in run_kql(GOV_FLAG_MEMBER_NAMES_QUERY, {}):
            names = _member_labels(
                list(mr.get("member_names") or []),
                list(mr.get("member_ids") or []))
            ids = [str(i) for i in (mr.get("member_ids") or [])]
            members_by_cluster[str(mr.get("cluster"))] = [
                {"id": mid, "name": nm}
                for mid, nm in zip(ids, names)]
    except Exception:   # noqa: BLE001 — picker enrich is additive
        members_by_cluster = {}
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
            "members": members_by_cluster.get(fid, []),
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
                 user: str, reason: str, event_at: str,
                 member_ids: "list[str] | None" = None) -> dict:
    """The 0056-shape decision event an act records — graded per
    the landing row, always; picked members ride the decision AND
    ids_read (CONSOLE-3: target ids in the decision)."""
    row = check_action(verb, persona, reason, member_ids)
    members = tuple(str(m) for m in (member_ids or []))
    return {
        "event_at": event_at,
        "user_id": user,
        "question": f"[CONSOLE:{verb.upper()}] {target_id}",
        "tools_used": ("console",),
        "ids_read": (target_id,) + members,
        "basis": f"resolution console — lands: {row['lands']}",
        "answered": True,
        "conversation_id": "console", "turn_index": -1,
        "decision": {"made_by": "console_action", "verb": verb,
                     "persona": persona, "reason": reason,
                     "targets": list(members),
                     "grade": row["grade"],
                     "lands": row["lands"]},
        "trace": ({"tool": "console",
                   "args": {"verb": verb, "target": target_id},
                   "result": row["grade"]},),
    }
