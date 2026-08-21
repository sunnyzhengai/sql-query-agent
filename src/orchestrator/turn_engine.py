"""The one-mind turn engine (ADR 0051) — one conversation decides,
the boundary enforces.

Derived from the six principles of HANDOFF_ONE_MIND, not from the
retired three-call protocol:

P1  one mind: a single conversation plans, judges, and answers.
P2  full evidence, persistent: complete tool results enter THIS
    history and persist across turns; compaction degrades the oldest
    results to their stamped headline + totals, never drops them.
P3  thinking room: no forced tool_choice inside the loop; the only
    form-fill is the final typed verdict.
P4  free composition: the deterministic ops are the tools; the system
    prompt holds invariants and tool semantics ONLY — no question
    shapes, no casebook.
P5  honesty at the boundary: stamped headlines on every panel; the
    final answer passes the caption gate; the typed verdict requires a
    machine-verified verbatim evidence quote; ops are read-only (any
    future write op plan-confirms, ADR 0050); caps and the anti-flail
    bound are code.
P6  failure is observation: tool errors return into the conversation
    as named results; the model adapts; the caps bound flailing.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from src.branding import product_name
from src.orchestrator.caption_gate import (
    caption_violations,
    enforce_caption,
    stamped_headline,
)
from src.orchestrator.ops import (
    OpError,
    OpsSession,
    op_census,
    op_compare,
    op_retrieve,
    op_search,
)

MAX_TOOL_ROUNDS = 8
HISTORY_BUDGET_CHARS = 350_000        # ~ model window, not a 20k amputation
_WS = re.compile(r"\s+")

# Invariants + tool semantics ONLY (P4). No question-family rules.
SYSTEM_PROMPT = (
    f"You are {product_name()}, answering questions about this "
    "organization's certified metric definitions.\n"
    "Invariants — absolute:\n"
    "1. Every factual claim must come from a tool result in this "
    "conversation. You may arrange and summarize facts; never add, "
    "estimate, or fill gaps. If the tools cannot support an answer, "
    "say so plainly.\n"
    "2. Every tool result is ALSO displayed to the user with a "
    "machine-stamped headline (exact counts, scope, completeness). "
    "Respect each result's declared completeness: a top-K result is "
    "never exhaustive; 'complete' results carry exact counts.\n"
    "3. Business language; raw SQL only when asked. Never output "
    "patient identifiers or personal names from inside SQL text.\n"
    "4. Be concise and direct; no greetings.\n"
    "When the displayed results settle the question (or prove it "
    "unanswerable), reply in plain text — that reply is shown to the "
    "user verbatim. You will then file a short verdict form; claiming "
    "answered requires a verbatim quote from a displayed row, which "
    "is machine-verified."
)

ENGINE_TOOLS = [
    {"type": "function", "function": {
        "name": "search",
        "description": ("Find catalog items. mode=semantic: closest by "
                        "meaning plus name-containment matches — top-K, "
                        "never exhaustive; its row count is a property "
                        "of the search window, never a count of "
                        "anything. mode=exact: every item whose name/"
                        "business name/ref equals the phrase exactly "
                        "(complete)."),
        "parameters": {"type": "object", "properties": {
            "phrase": {"type": "string"},
            "mode": {"type": "string", "enum": ["semantic", "exact"]}},
            "required": ["phrase", "mode"]}}},
    {"type": "function", "function": {
        "name": "census",
        "description": ("Complete enumeration of one catalog kind — "
                        "the ONLY operation whose results support an "
                        "exact count or an exhaustive statement about "
                        "the catalog. Optional contains: filter the "
                        "complete enumeration to items whose name, "
                        "business name, or description mentions the "
                        "text — the count stays exact."),
        "parameters": {"type": "object", "properties": {
            "kind": {"type": "string",
                     "enum": ["metric", "step", "term", "report",
                              "measure"]},
            "contains": {"type": "string"}},
            "required": ["kind"]}}},
    {"type": "function", "function": {
        "name": "retrieve",
        "description": ("Full certified records for ids that were "
                        "surfaced by a tool result in this conversation "
                        "or named by the user. Metric records list "
                        "their calculation step ids; step records carry "
                        "the step's logic."),
        "parameters": {"type": "object", "properties": {
            "ids": {"type": "array", "items": {"type": "string"}}},
            "required": ["ids"]}}},
    {"type": "function", "function": {
        "name": "compare",
        "description": ("Deterministic comparison over prior result "
                        "sets (refs like R1, R2). aspect omitted/"
                        "logic = content partition; steps = step-"
                        "aligned diff; tables = set algebra; a field "
                        "name = field diff."),
        "parameters": {"type": "object", "properties": {
            "refs": {"type": "array", "items": {"type": "string"}},
            "aspect": {"type": "string"}},
            "required": ["refs"]}}},
]

VERDICT_TOOL = {
    "type": "function",
    "function": {
        "name": "file_verdict",
        "description": "File the typed verdict for the answer just "
                       "given (machine-verified).",
        "parameters": {
            "type": "object",
            "properties": {
                "answered": {"type": "boolean"},
                "evidence_quote": {"type": "string",
                                   "description": "when answered=true: "
                                   "a VERBATIM substring (>=20 chars) "
                                   "copied from a displayed row that "
                                   "carries the answer"},
                "missing_op": {"type": "string",
                               "description": "when answered=false: "
                               "the operation that would produce the "
                               "answer, or empty if none could"},
            },
            "required": ["answered"],
        },
    },
}

READ_ONLY_TOOLS = frozenset({"search", "census", "retrieve", "compare"})


@dataclass
class EngineSession:
    """One conversation: shared ops session (result registry + read
    guarantee), the SINGLE history (P1/P2), and every display panel."""
    ops: OpsSession = field(default_factory=OpsSession)
    history: "list[dict]" = field(default_factory=list)
    displays: "list[dict]" = field(default_factory=list)
    turns: int = 0


def _norm(text: str) -> str:
    return _WS.sub(" ", text.replace("\\n", " ").replace('\\"', '"')).strip()


def _run_op(name: str, args: dict, run_kql, ops: OpsSession):
    if name == "search":
        return op_search(str(args.get("phrase", "")),
                         str(args.get("mode", "")), run_kql, ops)
    if name == "census":
        return op_census(str(args.get("kind", "")), run_kql, ops,
                         contains=(str(args["contains"])
                                   if args.get("contains") else None))
    if name == "retrieve":
        return op_retrieve([str(i) for i in (args.get("ids") or [])],
                           run_kql, ops)
    if name == "compare":
        return op_compare([str(r) for r in (args.get("refs") or [])],
                          args.get("aspect"), run_kql, ops)
    raise OpError(f"unknown tool {name!r}")


def _infra_error(e: Exception) -> str:
    text = str(e)
    m = re.search(r'"@message"\s*:\s*"([^"]{1,160})', text)
    detail = (m.group(1) if m else text[:140]).strip()
    return (f"operation failed ({type(e).__name__}: {detail}) — "
            "common causes: capacity paused (resume it) or a broken "
            "OneLake shortcut in the KQL database (re-create it)")


def _compact_history(history: "list[dict]") -> None:
    """P2 graceful degradation: oldest tool results compact to their
    stamped headline + totals (never dropped); recent results whole."""
    def total() -> int:
        return sum(len(str(m.get("content") or "")) for m in history)
    if total() <= HISTORY_BUDGET_CHARS:
        return
    for m in history:
        if m.get("role") != "tool":
            continue
        content = str(m.get("content") or "")
        if len(content) < 2000 or '"compacted"' in content:
            continue
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            continue
        m["content"] = json.dumps({
            "compacted": True,
            "ref": payload.get("ref"),
            "headline": payload.get("headline"),
            "rows_total": payload.get("rows_total",
                                      len(payload.get("rows") or [])),
            "note": "full rows were shown earlier in this conversation "
                    "and compacted to fit the window",
        })
        if total() <= HISTORY_BUDGET_CHARS:
            return


def run_turn(session: EngineSession, question: str, chat_api,
             run_kql, max_rounds: int = MAX_TOOL_ROUNDS) -> dict:
    """One user turn: the loop, then the boundary. Returns
    {answer, outputs, rounds, answered, missing_op, evidence_quote,
    caption_corrected, caption_violations, exhausted}."""
    if not session.history:
        session.history.append({"role": "system", "content": SYSTEM_PROMPT})
    session.ops.note_user(question)
    session.history.append({"role": "user", "content": question})

    outputs: "list[dict]" = []
    seen_calls: "set[tuple]" = set()
    answer = ""
    rounds = 0
    exhausted = False
    raw: dict = {}
    answered = False
    quote = ""
    violations: "list[str]" = []

    # Verdict-driven continuation (P6, suite find 2026-08-21): the
    # model kept filing its OWN verdict as not-answered with the
    # missing operation named — then stopping with rounds to spare. A
    # self-diagnosed miss is an observed error, not a terminal fact:
    # when the verdict (or a floored caption) names what is missing
    # and budget remains, the observation goes into the conversation
    # and the SAME bounded loop runs once more. Round cap unchanged;
    # anti-flail persists across passes; one continuation only.
    #
    # Review reframe (approved 2026-08-21): this is an M5 fix, not
    # just P6 — `answered=false ∧ missing_op ≠ null ∧ budget > 0 →
    # continue` is a COMPUTABLE decision, and it was resting on a
    # stochastic decider (the model's whim to take the next hop). The
    # 0.83/0.67/0.50 bounce on identical code was a misfiled decision
    # type, not noise. The trigger reads TYPED verdict fields, never
    # language (M4 — the pin stands legitimately).
    #
    # WATCH (typed M2, do not stamp): humble-but-blind — the model
    # declares not-answered naming an op it ALREADY ran; dedup rightly
    # blocks the repeat while the facts sit displayed. If that grows,
    # it is an evidence-PRESENTATION problem, not a loop problem.
    for pass_no in (1, 2):
        got_answer = False
        while rounds < max_rounds:
            _compact_history(session.history)
            message = chat_api(session.history, ENGINE_TOOLS)
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                answer = (message.get("content") or "").strip()
                session.history.append({"role": "assistant",
                                        "content": answer})
                got_answer = True
                break
            session.history.append(message)
            rounds += 1
            for call in tool_calls:
                name = call["function"]["name"]
                try:
                    args = json.loads(call["function"]["arguments"] or "{}")
                except json.JSONDecodeError:
                    args = {}
                key = (name, json.dumps(args, sort_keys=True))
                display: dict
                if name not in READ_ONLY_TOOLS:
                    payload = {"error": f"{name!r} refused: this surface "
                                        "runs read-only tools; writes "
                                        "always plan-confirm"}
                    display = {"component": {"op": name, "params": args,
                                             "auto_round": rounds},
                               "error": payload["error"]}
                elif key in seen_calls:
                    payload = {"error": f"{name} with identical parameters "
                                        "already ran this turn — repeating "
                                        "it cannot add information"}
                    display = {"component": {"op": name, "params": args,
                                             "auto_round": rounds},
                               "error": payload["error"]}
                else:
                    seen_calls.add(key)
                    try:
                        rs = _run_op(name, args, run_kql, session.ops)
                        shown = rs.display()
                        shown["headline"] = stamped_headline(shown)
                        display = {"component": {"op": name, "params": args,
                                                 "auto_round": rounds},
                                   "result": shown}
                        payload = {"ref": shown.get("ref"),
                                   "headline": shown.get("headline"),
                                   "complete": shown.get("complete"),
                                   "universe": shown.get("universe"),
                                   "rows_total": len(rs.rows),
                                   "rows": rs.rows}       # FULL rows (P2)
                    except OpError as e:
                        payload = {"error": str(e)}
                        display = {"component": {"op": name, "params": args,
                                                 "auto_round": rounds},
                                   "error": str(e)}
                    except Exception as e:  # noqa: BLE001 — P6: observed
                        payload = {"error": _infra_error(e)}
                        display = {"component": {"op": name, "params": args,
                                                 "auto_round": rounds},
                                   "error": payload["error"]}
                outputs.append(display)
                session.history.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "content": json.dumps(payload),
                })
        if not got_answer:
            exhausted = True
            answer = ("I hit the per-question tool budget before "
                      "finishing — the operations run so far are "
                      "displayed; ask a narrower question or continue "
                      "from a shown result.")
            session.history.append({"role": "assistant",
                                    "content": answer})

        # ---- the boundary (P5) --------------------------------------
        # Claims are checked against every result displayed this
        # conversation (P1/P2 — the walk's zero-round '122 steps'
        # answer restated a prior turn's rows and was floored as
        # invented); the template floor still renders only this turn's
        # outputs.
        gate_ground = list(session.displays) + outputs
        violations = (caption_violations(answer, gate_ground)
                      if answer else [])
        if violations and answer and not exhausted:
            note = ("Your answer was REJECTED by the honesty gate:\n"
                    + "\n".join(f"- {v}" for v in violations)
                    + "\nRewrite it claiming only what the displayed "
                    "results support.")
            session.history.append({"role": "user", "content": note})
            retry_msg = chat_api(session.history, [])
            retried = (retry_msg.get("content") or "").strip()
            if retried:
                answer = retried
                session.history.append({"role": "assistant",
                                        "content": answer})
        answer, violations = enforce_caption(answer, outputs,
                                             ground=gate_ground)

        # The typed verdict — the ONE legal form-fill (P3), verified.
        raw = {}
        try:
            v_msg = chat_api(
                session.history + [{
                    "role": "user",
                    "content": "File the verdict form for the answer "
                               "above."}],
                [VERDICT_TOOL],
                {"type": "function", "function": {"name": "file_verdict"}})
            calls = v_msg.get("tool_calls") or []
            if calls:
                raw = json.loads(calls[0]["function"]["arguments"] or "{}")
        except Exception:           # noqa: BLE001 — verdict is boundary
            raw = {}
        # An exhausted turn is by construction NOT an answer — corpse
        # fixture 2026-08-21: the continuation drove a flail to the
        # round cap, and the verdict then declared answered=True on
        # the budget apology with a quote validly drawn from earlier
        # rows. The budget message never carries an answer.
        answered = (bool(raw.get("answered")) and not violations
                    and not exhausted)
        quote = _norm(str(raw.get("evidence_quote", "")))
        if answered:
            # Evidence ground = every row DISPLAYED this conversation,
            # not just this turn's (P1/P2 — the walk's 'show me the
            # sql' turn answered verbatim from a prior retrieve with
            # zero new rounds and was denied a verified verdict;
            # session.displays still holds only PRIOR turns here,
            # extended below).
            ground = _norm(json.dumps(
                [row for o in (list(session.displays) + outputs)
                 for row in ((o.get("result") or {}).get("rows") or [])],
                ensure_ascii=False))
            if len(quote) < 20 or quote.lower() not in ground.lower():
                answered = False
                raw = {**raw, "missing_op": raw.get("missing_op")
                       or "an operation whose displayed rows contain "
                          "the claimed answer"}
        if not answered and violations and not raw.get("missing_op"):
            # a floored caption is itself a named gap — the engine
            # knows what is missing even when the model's form is bare
            raw = {**raw, "missing_op":
                   "an operation whose displayed rows support the "
                   "claim the gate rejected"}

        if (answered or exhausted or pass_no == 2
                or not raw.get("missing_op")
                or rounds >= max_rounds):
            break
        session.history.append({
            "role": "user",
            "content": ("Your verdict filed NOT answered — missing: "
                        f"{raw['missing_op']}. Tool rounds remain: run "
                        "the missing operation(s), then answer "
                        "again.")})

    session.displays.extend(outputs)
    session.turns += 1
    return {
        "answer": answer,
        "outputs": outputs,
        "rounds": rounds,
        "exhausted": exhausted,
        "answered": answered,
        "evidence_quote": quote if answered else "",
        "missing_op": str(raw.get("missing_op", ""))[:120],
        "caption_corrected": bool(violations),
        "caption_violations": violations,
    }
