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

from src.orchestrator.caption_gate import (
    caption_violations,
    enforce_caption,
    stamped_headline,
)
from src.orchestrator.ops import (
    OpError,
    OpsSession,
    ResultSet,
    normalize_kind,
    op_census,
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
    "phrase. Phrases are NAMES of things — never category words.\n"
    "- census: params {kind} (metric|step|term|report|measure). "
    "Complete enumeration of a KIND with the exact count. ALWAYS use "
    "this for 'how many X are there' / 'list all X' — a kind word "
    "(metrics, reports) in a search phrase finds only items NAMED "
    "that word.\n"
    "- retrieve: params {ids}. Full records for ids the user named or "
    "a prior result surfaced.\n"
    "- compare: params {refs, aspect?}. Deterministic comparison over "
    "result sets: refs are prior results (R1, R2...) or THIS plan's "
    "components ($1 = output of component 1). aspect omitted/logic = "
    "content partition; steps = step-aligned diff of metric "
    "decompositions (says WHERE definitions diverge); tables = set "
    "algebra; a field name = field diff.\n"
    "Rules: one component per operation, in execution order; each "
    "component carries a short note saying why. If the question is "
    "genuinely ambiguous, return NO components and set clarification "
    "to the question you need answered."
    # ADR 0051 (P4): the question-shape casebook that lived here is
    # DELETED, not ported — the one-mind engine composes freely and
    # the suite measures whether it does so natively.
)

# B (Sunny's verdict, 2026-08-20): un-drifting the slogan. "The answer
# is a caption" always meant the caption IS the answer, grounded in
# displayed results — not a description of the display.
CAPTION_PROMPT = (
    "You ANSWER the user's question using ONLY the displayed result "
    "sets (reference them as R1, R2...). The answer is a caption: "
    "concise, business language, every claim grounded in a displayed "
    "set. Respect each set's declared completeness: never claim "
    "'all/none/only' from a set marked incomplete. If the displayed "
    "sets do not contain the answer, say so plainly and name the "
    "operation that would produce it. "
    # ADR 0051 (P4): the mandatory-bridge and topic-count casebook
    # clauses that lived here are DELETED, not ported.
    "When you declare answered=true you MUST also "
    "supply evidence_quote: a verbatim substring (>= 20 characters) "
    "copied exactly from a displayed row that carries the answer — it "
    "is machine-verified, and an unverifiable quote demotes the "
    "verdict. "
    "Never output patient identifiers. No greetings; SQL only if the "
    "user asked for it. Then suggest 0-3 useful next operations as "
    "structured components."
)

GOAL_CHECK_PROMPT = (
    "You judge ONE thing from the displayed result sets: do they "
    "contain the answer to the user's question? If yes: answered=true. "
    "If no and a read-only operation (search, census, retrieve, "
    "compare — same parameters as planning; R1... refs work) could "
    "produce the missing part, propose those components. If nothing "
    "could, answered=false with no components and say in 'note' what "
    "is missing. Judge only from what is displayed. In follow-up "
    "components, ids must be explicit (from displayed rows) — $n "
    "placeholders do not exist here."
    # ADR 0051 (P4): the pointer-doctrine casebook that lived here is
    # DELETED, not ported.
)

GOAL_TOOL = {
    "type": "function",
    "function": {
        "name": "assess_answer",
        "description": "Judge answer-completeness; propose next "
                       "read-only components if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "answered": {"type": "boolean"},
                "components": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string"},
                        "params": {"type": "object"},
                        "note": {"type": "string"},
                    },
                    "required": ["op", "params"]}},
                "note": {"type": "string"},
            },
            "required": ["answered"],
        },
    },
}

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
        "description": "Answer the question from the displayed results; "
                       "declare answered honestly; suggest next ops.",
        "parameters": {
            "type": "object",
            "properties": {
                "caption": {"type": "string"},
                # Typed self-declaration (HANDOFF_ANSWER_LOOP): the
                # machine-readable verdict the grader cross-checks —
                # answered:true without the required facts is DISHONEST.
                "answered": {"type": "boolean",
                             "description": "true ONLY if the caption "
                             "actually answers the user's question from "
                             "the displayed sets"},
                "missing_op": {"type": "string",
                               "description": "when answered=false: the "
                               "operation that would produce the answer, "
                               "or empty if none could"},
                # Iteration 6: answered=true must be PROVABLE — a
                # verbatim quote from a displayed row, verified by code.
                "evidence_quote": {"type": "string",
                                   "description": "when answered=true: "
                                   "a VERBATIM substring (>=20 chars) "
                                   "copied from a displayed row that "
                                   "carries the answer; code verifies "
                                   "it — an unverifiable quote demotes "
                                   "the verdict"},
                "suggestions": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string"},
                        "params": {"type": "object"},
                        "note": {"type": "string"},
                    },
                    "required": ["op", "params"]}},
            },
            "required": ["caption", "answered"],
        },
    },
}

_REF_SHAPE = re.compile(r"^(R\d+|\$\d+)$")

IMPLEMENTED_OPS = ("search", "census", "retrieve", "compare")

# The auto-continue bound (Sunny's verdict, 2026-08-20): only these ops
# may run WITHOUT per-round human confirmation. Enforced in the
# executor path, never by prompt. Writes always confirm — any future
# mutating op must NOT be added here without its own ruling.
READ_ONLY_OPS = frozenset({"search", "census", "retrieve", "compare"})
MAX_AUTO_ROUNDS = 3
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
    elif op == "census":
        kind = normalize_kind(str(p.get("kind", "")))
        if kind is None:
            out["invalid_reason"] = ("census kind must be metric, step, "
                                     "term, report, or measure")
        else:
            out["params"]["kind"] = kind
            out["valid"] = True
    elif op == "retrieve":
        ids = p.get("ids")
        if isinstance(ids, str):
            ids = [ids]                      # planners say "$1"; normalize
        if not isinstance(ids, list) or not ids:
            out["invalid_reason"] = "retrieve needs a non-empty ids list"
        else:
            out["params"]["ids"] = [str(i) for i in ids]
            out["valid"] = True
    elif op == "compare":
        refs = p.get("refs")
        if isinstance(refs, str):
            refs = [refs]
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


def _infra_error(e: Exception) -> str:
    """Admin-facing infrastructure error: NAME the broken thing
    (error-contract philosophy — live find 2026-08-20: 'may be
    unavailable' hid 'Delta table does not exist', sending the admin
    guessing between a paused capacity and a broken shortcut)."""
    text = str(e)
    m = re.search(r'"@message"\s*:\s*"([^"]{1,160})', text)
    detail = (m.group(1) if m else text[:140]).strip()
    return (f"operation failed ({type(e).__name__}: {detail}) — "
            "common causes: capacity paused (resume it) or a broken "
            "OneLake shortcut in the KQL database (re-create it)")


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
            shown = rs.display()
            # The stamped headline (spec:E6, ADR 0032 pattern): the
            # panel's quantitative sentence is code, never LLM prose.
            shown["headline"] = stamped_headline(shown)
            outputs.append({"component": c, "result": shown})
        except OpError as e:
            outputs.append({"component": c, "error": str(e)})
        except Exception as e:              # noqa: BLE001 — infra visible
            outputs.append({"component": c, "error": _infra_error(e)})
    session.turns += 1
    return outputs


_DISPLAY_BUDGET = 20000
_WS = re.compile(r"\s+")


def _norm_ws(text: str) -> str:
    """Whitespace-fold for quote verification: JSON escapes and line
    wrapping must not defeat a genuinely verbatim quote."""
    return _WS.sub(" ", text.replace("\\n", " ").replace('\\"', '"')).strip()


def _build_view(outputs: "list[dict]", rows_cap: int,
                text_cap: int) -> "list[dict]":
    view = []
    for o in outputs:
        c = o.get("component") or {}
        entry: dict = {"op": c.get("op"), "params": c.get("params")}
        if c.get("auto_round"):
            entry["auto_round"] = c["auto_round"]
        if "error" in o:
            entry["error"] = o["error"]
            view.append(entry)
            continue
        r = o.get("result") or {}
        rows = r.get("rows") or []
        entry.update({
            "ref": r.get("ref"),
            "headline": r.get("headline"),
            "complete": r.get("complete"),
            "rows_total": len(rows),
            "rows_shown": min(len(rows), rows_cap),
        })
        compact = []
        for row in rows[:rows_cap]:
            compact.append({
                k: (v[:text_cap] if isinstance(v, str) else v)
                for k, v in row.items() if v not in (None, "")
            })
        entry["rows"] = compact
        if len(rows) > rows_cap:
            entry["note"] = (f"{len(rows) - rows_cap} more rows "
                             "displayed to the user but omitted here — "
                             "counts come from rows_total/headline")
        view.append(entry)
    return view


def _display_for_llm(outputs: "list[dict]") -> str:
    """The result payload the caption/goal LLMs read. Suite finding
    (2026-08-20): a naive json.dumps(outputs)[:6000] TRUNCATED the
    stamped headline (appended after the rows) and most rows — the
    captioner counted the surviving rows and invented '6 metrics'.
    Headline FIRST, rows compacted, totals explicit, and over-budget
    payloads DEGRADE (fewer/shorter rows) instead of being chopped —
    headlines and totals survive every tier."""
    blob = ""
    for rows_cap, text_cap in ((40, 400), (12, 240), (5, 160)):
        blob = json.dumps(_build_view(outputs, rows_cap, text_cap))
        if len(blob) <= _DISPLAY_BUDGET:
            return blob
    return blob[:_DISPLAY_BUDGET]      # last resort; headline-first order


def continue_rounds(session: ProtocolSession, question: str,
                    outputs: "list[dict]", chat_api, run_kql,
                    max_rounds: int = MAX_AUTO_ROUNDS) -> dict:
    """The bounded read-only loop (Sunny's verdict, 2026-08-20 —
    ADR 0035's intelligence shape inside ADR 0036's honesty frame).

    After the confirmed plan runs, ask ONE question per round: does the
    display answer the user's question? If not, the proposed follow-up
    components auto-run — but the bound is enforced HERE, in the
    executor path, never by prompt: any component whose op is not in
    READ_ONLY_OPS is refused before validation, refusal displayed;
    writes always confirm. Every auto-hop lands in `outputs` exactly
    like a confirmed hop (stamped headline, visible error). The error
    mode, by construction: one more visible read-only hop, or an
    honest "couldn't answer" with what is missing named.

    Mutates `outputs` in place (appending auto-hops) and returns
    {rounds, exhausted, status_line, unanswered_note}."""
    # Deterministic follow-up (data-state-shaped, like the anti-flail
    # bound — NOT a question template): an exact name search that
    # returned 0 rows ALWAYS gets its semantic sibling run by CODE
    # before any judge speaks — the did-you-mean material is fetched
    # mechanically, never left to an LLM's whim. (Iteration 3 finding:
    # missing bridge material was the top dumbness source at n=6.)
    shown = {
        (str((o.get("component") or {}).get("op", "")),
         json.dumps((o.get("component") or {}).get("params") or {},
                    sort_keys=True))
        for o in outputs
    }
    pre = []
    for o in outputs:
        c = o.get("component") or {}
        r = o.get("result")
        params = c.get("params") or {}
        if (c.get("op") == "search" and params.get("mode") == "exact"
                and r is not None and not (r.get("rows") or [])):
            phrase = str(params.get("phrase", ""))
            key = ("search", json.dumps(
                {"mode": "semantic", "phrase": phrase}, sort_keys=True))
            if phrase and key not in shown:
                shown.add(key)
                pre.append({"op": "search",
                            "params": {"phrase": phrase,
                                       "mode": "semantic"},
                            "note": "deterministic follow-up: empty "
                                    "exact name lookup — fetching the "
                                    "closest certified items"})
    if pre:
        executed = execute_confirmed(session, {"components": pre}, run_kql)
        for o in executed:
            o["component"]["auto_round"] = "pre"
        outputs.extend(executed)

    rounds: "list[dict]" = []
    unanswered_note = ""
    for round_no in range(1, max_rounds + 1):
        display_blob = _display_for_llm(outputs)
        messages = list(session.history) + [
            {"role": "system", "content": GOAL_CHECK_PROMPT},
            {"role": "user", "content":
             f"Question: {question}\nDisplayed results:\n{display_blob}"}]
        raw = _forced_call(chat_api, messages, GOAL_TOOL)
        components = list(raw.get("components") or [])
        if raw.get("answered") or not components:
            unanswered_note = ("" if raw.get("answered")
                               else str(raw.get("note", ""))[:300])
            status = (f"auto-continue: answered after "
                      f"{len(rounds)} read-only round(s)"
                      if raw.get("answered") else
                      f"auto-continue: stopped after {len(rounds)} "
                      f"read-only round(s) — no further read-only "
                      f"operation would help")
            return {"rounds": rounds, "exhausted": False,
                    "status_line": status,
                    "unanswered_note": unanswered_note}

        # THE BOUNDS, in code: non-read-only ops never auto-run, and a
        # component identical to one already displayed this turn is
        # refused — repeating it cannot add information (anti-flail,
        # suite finding 2026-08-20: three identical semantic searches
        # in three rounds).
        already = {
            (str((o.get("component") or {}).get("op", "")),
             json.dumps((o.get("component") or {}).get("params") or {},
                        sort_keys=True))
            for o in outputs
        }
        runnable, refused = [], []
        for comp in components:
            op_name = str(comp.get("op", ""))
            key = (op_name, json.dumps(dict(comp.get("params") or {}),
                                       sort_keys=True))
            if op_name not in READ_ONLY_OPS:
                reason = (f"{op_name!r} refused: auto-continue is "
                          "read-only; writes always confirm")
            elif key in already:
                reason = (f"{op_name} with identical parameters already "
                          "ran this turn — repeating it cannot add "
                          "information")
            else:
                runnable.append(comp)
                already.add(key)
                continue
            refused.append({
                "component": {"index": 0, "op": op_name,
                              "params": dict(comp.get("params") or {}),
                              "note": "", "valid": False,
                              "auto_round": round_no},
                "error": reason,
            })
        round_outputs = list(refused)
        if runnable:
            executed = execute_confirmed(
                session, {"components": runnable}, run_kql)
            for o in executed:
                o["component"]["auto_round"] = round_no
            round_outputs.extend(executed)
        outputs.extend(round_outputs)
        rounds.append({"round": round_no,
                       "note": str(raw.get("note", ""))[:300],
                       "outputs": round_outputs})

    return {"rounds": rounds, "exhausted": True,
            "status_line": (f"auto-continue: round cap ({max_rounds}) "
                            "reached — answer may be incomplete"),
            "unanswered_note": ""}


def _expand_ids(ids: "list[str]", produced: "dict[int, str]",
                ops: OpsSession) -> "list[str]":
    """$n inside an ids list expands to the ids of component n's result
    rows — result piping is parameter plumbing, not a new operation."""
    out = []
    for i in ids:
        if _REF_SHAPE.match(i) and i.startswith("$"):
            idx = int(i[1:])
            if idx not in produced:
                raise OpError(f"{i} refers to component {idx}, which has "
                              "not produced a result")
            out.extend(r["id"] for r in ops.results[produced[idx]].rows
                       if r.get("id"))
        else:
            out.append(i)
    return out


def _run_component(c: dict, produced: "dict[int, str]", run_kql,
                   ops: OpsSession) -> ResultSet:
    p = c["params"]
    if c["op"] == "search":
        return op_search(p["phrase"], p["mode"], run_kql, ops)
    if c["op"] == "census":
        return op_census(p["kind"], run_kql, ops)
    if c["op"] == "retrieve":
        return op_retrieve(_expand_ids(p["ids"], produced, ops),
                           run_kql, ops)
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
                 chat_api, question: str = "") -> dict:
    """ANSWER the question from what is on screen (B, 2026-08-20: the
    caption IS the answer); suggest next components (validated). The
    caption's inputs are stamped by code: the refs it was shown."""
    shown_refs = [o["result"]["ref"] for o in outputs if "result" in o]
    display_blob = _display_for_llm(outputs)
    messages = list(session.history) + [
        {"role": "system", "content": CAPTION_PROMPT},
        {"role": "user", "content":
         f"The user's question: {question or '(not restated)'}\n\n"
         f"Displayed results (the user sees these):\n{display_blob}\n\n"
         "Answer the question from these results (or say what "
         "operation would), then suggest next operations."}]
    raw = _forced_call(chat_api, messages, CAPTION_TOOL)
    caption = str(raw.get("caption", "")).strip()

    # The caption gate (spec:E6, mechanical — see caption_gate.py):
    # one corrective retry, then the deterministic template floor.
    violations = caption_violations(caption, outputs)
    if violations and caption:
        note = ("Your caption was REJECTED by the honesty gate:\n"
                + "\n".join(f"- {v}" for v in violations)
                + "\nRewrite it claiming only what the displayed result "
                "sets support; drop any claim you cannot ground.")
        retry = _forced_call(
            chat_api, messages + [{"role": "user", "content": note}],
            CAPTION_TOOL)
        retried = str(retry.get("caption", "")).strip()
        if retried:
            caption, raw = retried, retry
    caption, violations = enforce_caption(caption, outputs)

    # Verdict proof, in code (iteration 6 — Sunny: "fix the dishonest
    # caption shape"): answered=true requires a verbatim quote from a
    # displayed row, and CODE verifies the quote. Claiming without
    # grounding becomes structurally impossible — the basis-stamping
    # family, applied to the verdict itself.
    if raw.get("answered"):
        quote = _norm_ws(str(raw.get("evidence_quote", "")))
        ground = _norm_ws(json.dumps(
            [row for o in outputs
             for row in ((o.get("result") or {}).get("rows") or [])],
            ensure_ascii=False))
        if len(quote) < 20 or quote.lower() not in ground.lower():
            raw = {**raw, "answered": False,
                   "missing_op": (raw.get("missing_op")
                                  or "an operation whose displayed rows "
                                     "contain the claimed answer")}

    # ADR 0051 (P4): the pointer-doctrine verdict demotion that lived
    # here was question-family control flow — REMOVED. The
    # evidence-quote proof above is the boundary mechanism that stays.

    suggestions = [validate_component(s, i + 1)
                   for i, s in enumerate(raw.get("suggestions") or [])][:3]
    session.history.append({"role": "assistant", "content": caption})
    return {"caption": caption,
            "caption_inputs": shown_refs,        # stamped by code
            "caption_corrected": bool(violations),
            "caption_violations": violations,
            # Typed self-declaration (HANDOFF_ANSWER_LOOP): graded by
            # the conversation suite; logged as the miss stream. A
            # floored caption is by definition not an answer.
            "answered": bool(raw.get("answered", False)) and not violations,
            "missing_op": str(raw.get("missing_op", ""))[:120],
            "suggestions": [s for s in suggestions if s["valid"]]}
