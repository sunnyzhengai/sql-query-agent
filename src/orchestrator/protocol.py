"""The plan protocol (ADR 0036): interpret -> confirm -> execute -> caption.

The LLM's entire linguistic authority is compressed into two structured
calls: PROPOSE a plan of primitive components, and CAPTION displayed
results. Between them sit the two human moments the methodology exists
for: the plan is CONFIRMED before anything runs (the surface's job —
this module structurally cannot execute an unconfirmed plan, because
execution takes the plan as externally supplied data), and results
DISPLAY as first-class sets.

Structural validation on everything the model emits; invalid components
are flagged and shown, never silently dropped — the human sees exactly
what the translator tried to do.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable

from src.orchestrator.ops import (
    OpError,
    OpsSession,
    ResultSet,
    op_compare,
    op_retrieve,
    op_search,
)

PLANNER_PROMPT = (
    "You translate a user's question about certified metrics metadata "
    "into a PLAN of primitive operations. You never answer questions "
    "yourself — you only plan. Operations:\n"
    "- search: params {phrase, mode}. mode=semantic finds the closest "
    "matches by meaning (top-K, NEVER exhaustive); mode=exact "
    "enumerates every item whose name/business name/ref equals the "
    "phrase (the ONLY mode that supports 'all/none/unique' claims).\n"
    "- retrieve: params {ids}. Full records for ids the user named or "
    "a prior result surfaced.\n"
    "- compare: params {refs, aspect?}. Deterministic comparison over "
    "result sets: refs are prior results (R1, R2...) or THIS plan's "
    "components ($1 = output of component 1). aspect omitted/logic = "
    "content partition; tables = set algebra; a field name = field "
    "diff.\n"
    "Rules: one component per operation, in execution order; each "
    "component carries a short note saying why. If the question is "
    "genuinely ambiguous, return NO components and set clarification "
    "to the question you need answered. Plan completeness honestly: "
    "questions about 'all/any other/unique' need exact search or an "
    "exhaustive retrieve, never semantic search alone."
)

CAPTION_PROMPT = (
    "You caption results that the user can already SEE on screen. "
    "Write a concise narration grounded ONLY in the displayed result "
    "sets provided (reference them as R1, R2...). Respect each set's "
    "declared completeness: never claim 'all/none/only' from a set "
    "marked incomplete. Never output patient identifiers. Then suggest "
    "0-3 useful next operations as structured components. No "
    "greetings; business language; SQL only if the user asked for it."
)

PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "propose_plan",
        "description": "Propose the plan of primitive operations.",
        "parameters": {
            "type": "object",
            "properties": {
                "components": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string"},
                        "params": {"type": "object"},
                        "note": {"type": "string"},
                    },
                    "required": ["op", "params"]}},
                "clarification": {"type": "string"},
            },
            "required": ["components"],
        },
    },
}

CAPTION_TOOL = {
    "type": "function",
    "function": {
        "name": "caption_results",
        "description": "Caption the displayed results; suggest next ops.",
        "parameters": {
            "type": "object",
            "properties": {
                "caption": {"type": "string"},
                "suggestions": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string"},
                        "params": {"type": "object"},
                        "note": {"type": "string"},
                    },
                    "required": ["op", "params"]}},
            },
            "required": ["caption"],
        },
    },
}

_REF_SHAPE = re.compile(r"^(R\d+|\$\d+)$")

IMPLEMENTED_OPS = ("search", "retrieve", "compare")
APPROVED_UNBUILT = {"traverse": "approved (ADR 0037) but not yet built",
                    "update": "approved (ADR 0036/0038) but gated on the "
                              "access-control ADR"}


def validate_component(c: dict, index: int) -> "dict":
    """Structural validation; returns the normalized component with
    valid/invalid_reason set. Invalid components are SHOWN, not dropped."""
    out = {"index": index, "op": str(c.get("op", "")),
           "params": dict(c.get("params") or {}),
           "note": str(c.get("note", ""))[:300],
           "valid": False, "invalid_reason": ""}
    op, p = out["op"], out["params"]
    if op in APPROVED_UNBUILT:
        out["invalid_reason"] = APPROVED_UNBUILT[op]
        return out
    if op not in IMPLEMENTED_OPS:
        out["invalid_reason"] = f"unknown operation {op!r}"
        return out
    if op == "search":
        if not str(p.get("phrase", "")).strip():
            out["invalid_reason"] = "search needs a phrase"
        elif p.get("mode") not in ("semantic", "exact"):
            out["invalid_reason"] = "search mode must be semantic or exact"
        else:
            out["valid"] = True
    elif op == "retrieve":
        ids = p.get("ids")
        if not isinstance(ids, list) or not ids:
            out["invalid_reason"] = "retrieve needs a non-empty ids list"
        else:
            out["params"]["ids"] = [str(i) for i in ids]
            out["valid"] = True
    elif op == "compare":
        refs = p.get("refs")
        if not isinstance(refs, list) or not refs:
            out["invalid_reason"] = "compare needs refs (R1... or $n)"
        elif not all(_REF_SHAPE.match(str(r)) for r in refs):
            out["invalid_reason"] = ("compare refs must be prior results "
                                     "(R1...) or plan components ($1...)")
        else:
            out["params"]["refs"] = [str(r) for r in refs]
            if p.get("aspect") is not None:
                out["params"]["aspect"] = str(p["aspect"])[:80]
            out["valid"] = True
    return out


def validate_plan(raw: dict) -> dict:
    comps = [validate_component(c, i + 1)
             for i, c in enumerate(raw.get("components") or [])]
    return {"components": comps,
            "clarification": str(raw.get("clarification", ""))[:500]}


def _forced_call(chat_api, messages, tool) -> dict:
    message = chat_api(messages, [tool],
                       {"type": "function",
                        "function": {"name": tool["function"]["name"]}})
    calls = message.get("tool_calls") or []
    if not calls:
        return {}
    try:
        return json.loads(calls[0]["function"]["arguments"] or "{}")
    except json.JSONDecodeError:
        return {}


@dataclass
class ProtocolSession:
    """One conversation: shared ops session (result registry + read
    guarantee), message history, and the plan/result log."""

    ops: OpsSession = field(default_factory=OpsSession)
    history: "list[dict]" = field(default_factory=list)
    turns: int = 0


def propose_turn(session: ProtocolSession, question: str,
                 chat_api) -> dict:
    """Interpret only. Returns the validated plan for CONFIRMATION —
    nothing executes here. One repair round if components were invalid."""
    session.ops.note_user(question)
    if not session.history:
        session.history.append({"role": "system", "content": PLANNER_PROMPT})
    session.history.append({"role": "user", "content": question})

    plan = validate_plan(_forced_call(chat_api, session.history, PLAN_TOOL))
    invalid = [c for c in plan["components"] if not c["valid"]]
    if invalid and not plan["clarification"]:
        repair = ("Some components were invalid: " + "; ".join(
            f"#{c['index']} {c['op']}: {c['invalid_reason']}"
            for c in invalid) + ". Re-propose the full corrected plan.")
        session.history.append({"role": "user", "content": repair})
        plan = validate_plan(
            _forced_call(chat_api, session.history, PLAN_TOOL))
    session.history.append({
        "role": "assistant",
        "content": f"[proposed plan] {json.dumps(plan)[:1500]}"})
    return plan


def execute_confirmed(session: ProtocolSession, plan: dict,
                      run_kql) -> "list[dict]":
    """Execute a HUMAN-CONFIRMED plan (possibly edited — this function
    trusts only its structure, so it re-validates). Returns display
    dicts per component: a ResultSet display or a visible error.
    $n placeholders resolve to this plan's component outputs."""
    validated = validate_plan(plan)
    outputs: "list[dict]" = []
    produced: "dict[int, str]" = {}     # component index -> ResultSet ref
    for c in validated["components"]:
        if not c["valid"]:
            outputs.append({"component": c, "error": c["invalid_reason"]})
            continue
        try:
            rs = _run_component(c, produced, run_kql, session.ops)
            produced[c["index"]] = rs.ref
            outputs.append({"component": c, "result": rs.display()})
        except OpError as e:
            outputs.append({"component": c, "error": str(e)})
        except Exception as e:              # noqa: BLE001 — infra visible
            outputs.append({"component": c, "error":
                            f"operation failed ({type(e).__name__}) — the "
                            "data platform may be unavailable"})
    session.turns += 1
    return outputs


def _run_component(c: dict, produced: "dict[int, str]", run_kql,
                   ops: OpsSession) -> ResultSet:
    p = c["params"]
    if c["op"] == "search":
        return op_search(p["phrase"], p["mode"], run_kql, ops)
    if c["op"] == "retrieve":
        return op_retrieve(p["ids"], run_kql, ops)
    refs = []
    for r in p["refs"]:
        if r.startswith("$"):
            idx = int(r[1:])
            if idx not in produced:
                raise OpError(f"{r} refers to component {idx}, which has "
                              "not produced a result")
            refs.append(produced[idx])
        else:
            refs.append(r)
    return op_compare(refs, p.get("aspect"), run_kql, ops)


def caption_turn(session: ProtocolSession, outputs: "list[dict]",
                 chat_api) -> dict:
    """Caption what is on screen; suggest next components (validated).
    The caption's inputs are stamped by code: the refs it was shown."""
    shown_refs = [o["result"]["ref"] for o in outputs if "result" in o]
    display_blob = json.dumps(outputs)[:6000]
    messages = list(session.history) + [
        {"role": "system", "content": CAPTION_PROMPT},
        {"role": "user", "content":
         f"Displayed results (the user sees these):\n{display_blob}\n\n"
         "Caption them and suggest next operations."}]
    raw = _forced_call(chat_api, messages, CAPTION_TOOL)
    suggestions = [validate_component(s, i + 1)
                   for i, s in enumerate(raw.get("suggestions") or [])][:3]
    caption = str(raw.get("caption", "")).strip()
    session.history.append({"role": "assistant", "content": caption})
    return {"caption": caption,
            "caption_inputs": shown_refs,        # stamped by code
            "suggestions": [s for s in suggestions if s["valid"]]}
