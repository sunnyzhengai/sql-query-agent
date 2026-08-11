"""AIVIA chat — surface v1 (terminal REPL).

The ADR 0032/0034 loop, human-visible: the conversational entry edge
routes every question to ONE typed call from the closed verb menu
(search / detail / variants / compare / unsupported); the deterministic
engine executes fixed lookups and computations; the narrate edge turns
computed facts into prose; the human picks whenever candidates exist.

No bypass: one candidate is presented exactly like ten. Run:

    python -m src.orchestrator.cli
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from src.orchestrator.assemble import AssemblyError, assemble
from src.orchestrator.compare import build_comparison
from src.orchestrator.core import (
    ResolutionResult,
    duplicate_list,
    parse_pick,
    produce_intent,
    resolve,
)
from src.orchestrator.events import ConfirmEvent, JsonlEventSink, PickEvent
from src.orchestrator.narrate import narrate_many, narrate_question
from src.orchestrator.variants import variants_answer

# Terminal reality (live find, 2026-08-10): Esc/arrow keys glue invisible
# escape sequences onto typed replies — "\x1b2" is not a digit, so a real
# pick fell through to the new-question hatch. Strip ANSI sequences, then
# any remaining non-printable characters, before parsing ANY input.
_ANSI_SEQ = re.compile(r"\x1b\[[0-9;?]*[A-Za-z~]")


def clean_input(text: str) -> str:
    text = _ANSI_SEQ.sub("", text)
    return "".join(ch for ch in text if ch.isprintable()).strip()


WEAK_CLOSENESS = 0.40   # display label only — never a gate (ADR 0032)

REFUSAL_MESSAGE = (
    "Nothing in the certified knowledge base is sufficiently related to "
    "that. Try naming the metric, report, or business concept differently."
)

# Verb-gap refusals (scorecard amendment 4): honest, named, logged —
# never a degraded pick list into the wrong question. Fact-gap routing
# (amendment 5) lives in the wording where the fact's canonical home is
# known.
UNSUPPORTED_MESSAGES = {
    "lineage": (
        "Lineage questions (what feeds a table, what is downstream of "
        "it) aren't supported yet. I can explain any specific metric, "
        "compare two, or check whether a named step's definitions agree."),
    "enumerate": (
        "Listing everything that matches a filter isn't supported yet. "
        "I can answer about a specific metric or step if you name one."),
    "usage": (
        "Usage questions (who uses what, how often) aren't supported "
        "yet. I can tell you a metric's steward and developer."),
    "data-values": (
        "I answer questions about how metrics are DEFINED — never about "
        "actual patient or row-level data. For data values, run the "
        "certified report itself."),
}


def render_detail(command: str, fact_sets) -> str:
    """Pure code — facts straight from the last assembly, no LLM."""
    out = []
    for fs in fact_sets:
        f = fs.facts
        label = (f.get("business_name") or f.get("metric_name")
                 or f.get("step_name") or fs.ref)
        if command == "sql":
            sql = f.get("calculation_logic") or f.get("sql_fragment")
            if not sql:   # variants fact set: one block per definition
                blocks = [f"-- {k.replace('_', ' ')}\n{v}"
                          for k, v in f.items() if k.endswith("_sql")]
                sql = "\n\n".join(blocks) or None
            out.append(f"--- SQL for {label} ---\n{sql or '(no SQL recorded)'}")
        elif command == "owner":
            out.append(f"{label}: steward = "
                       f"{f.get('steward') or '(none assigned)'}, developer = "
                       f"{f.get('developer') or '(none assigned)'}")
        elif command == "tables":
            out.append(f"{label}: {f.get('source_tables') or '(not recorded)'}")
        elif command == "link":
            if f.get("report_name") and f.get("report_url"):
                out.append(f"{label}: {f['report_name']} — {f['report_url']}")
            else:
                out.append(f"{label}: no report link recorded")
    out.append(f"Basis: {'; '.join(fs.basis for fs in fact_sets)} (cached "
               "from your last answer)")
    return "\n".join(out)


_GROUP_LABELS = {"metric": "Metrics:", "step": "Calculation steps:"}


def render_candidates(result: ResolutionResult, header: str = "") -> str:
    """Stratified display: the closest metrics, then the closest steps —
    continuous numbering so picks stay simple. The honest signal is the
    closeness column; the floor count is context, not a relevance claim."""
    lines = []
    if header:
        lines.append(header)
    lines.append(
        f"Closest matches ({result.total_matches} item(s) cleared the "
        "similarity floor):"
    )
    current_kind = None
    for i, c in enumerate(result.candidates, 1):
        if c.kind != current_kind:
            current_kind = c.kind
            lines.append(
                _GROUP_LABELS.get(c.kind, f"{c.kind.title()}s:"))
        weak = "  (weak match)" if c.closeness < WEAK_CLOSENESS else ""
        label = c.business_name or c.name
        lines.append(
            f"  {i}. {label} — {c.display_text}  "
            f"[closeness {c.closeness:.2f}]{weak}"
        )
    lines.append("Pick a number or exact name ('n' for none of these):")
    return "\n".join(lines)


def build_context(last_fact_sets, last_shown) -> str:
    """Code-built conversation state for the entry edge — what 'this',
    'it', 'they', 'these two' can refer to. Labels carry the id in
    parentheses so the LLM can name subjects unambiguously."""
    parts = []
    if last_fact_sets:
        labels = []
        for fs in last_fact_sets:
            f = fs.facts
            name = (f.get("business_name") or f.get("metric_name")
                    or f.get("step_name") or fs.ref)
            labels.append(f"{name} ({fs.kind} {fs.ref})")
        parts.append("Last answer covered: " + "; ".join(labels))
    if last_shown:
        items = [f"{c.business_name or c.name} ({c.kind} {c.ref})"
                 for c in last_shown[:10]]
        parts.append("Visible candidate list: " + "; ".join(items))
    return "\n".join(parts)


class _NewQuestion(Exception):
    def __init__(self, text: str) -> None:
        self.text = text


def _ask_pick(ask, say, result) -> "int | None":
    """Pick prompt with a deterministic escape hatch: a reply that is
    neither a valid pick, a digit, nor a decline is a NEW QUESTION —
    the shown list is recorded as declined and the conversation moves
    on. A chat must never trap the user in a menu.
    """
    while True:
        reply = ask("pick> ").strip()
        if not reply:
            continue   # stray Enter / swallowed escape key: just re-prompt
        if reply.lower() in ("n", "none"):
            return None
        picked = parse_pick(reply, result.candidates)
        if picked is not None:
            return picked
        if reply.isdigit():
            say(f"Pick a number between 1 and {len(result.candidates)}, "
                "or 'n' for none.")
            continue
        say("(Taking that as a new question.)")
        raise _NewQuestion(reply)


_REF_IN_PARENS = re.compile(r"\(([^()]+)\)\s*$")


def _bind_subject(subject: str, run_kql, ask, say, sink, user_id, question):
    """Turn a compare subject into a metric ref. Order: the id the LLM
    copied from context ('Label (metric ref)'), then the text as an
    exact ref, then ordinary resolution with a human pick. Returns a
    ref or None (nothing matched / user declined)."""
    text = subject.strip()
    m = _REF_IN_PARENS.search(text)
    if m:
        inner = m.group(1).strip()
        inner = inner.split()[-1] if inner else inner   # "metric x.Y" -> "x.Y"
        if _is_metric_ref(inner, run_kql):
            return inner
        text = _REF_IN_PARENS.sub("", text).strip()
    if _is_metric_ref(text, run_kql):
        return text
    result = resolve(text, run_kql)
    if not result.candidates:
        say(f"For '{text}': nothing sufficiently related.")
        return None
    say(render_candidates(result, f"For '{text}':"))
    picked = _ask_pick(ask, say, result)   # _NewQuestion propagates
    if picked is None:
        _record(sink, user_id, question, result, None)
        return None
    candidate = result.candidates[picked]
    _record(sink, user_id, question, result, candidate)
    return candidate.ref


def _is_metric_ref(text: str, run_kql) -> bool:
    from src.orchestrator.assemble import METRIC_FACTS_QUERY
    return bool(text) and bool(run_kql(METRIC_FACTS_QUERY, {"p_ref": text}))


def chat_loop(chat, run_kql, sink, user_id: str = "local-dev",
              ask=input, say=print) -> None:
    raw_ask = ask
    ask = lambda prompt="": clean_input(raw_ask(prompt))
    say("AIVIA — ask about your certified metrics ('q' to quit)\n")
    pending = None
    last_fact_sets = []
    last_shown = []
    while True:
        if pending is not None:
            question, pending = pending, None
        else:
            question = ask("you> ").strip()
        if question.lower() in ("q", "quit", "exit"):
            return
        if not question:
            continue

        context = build_context(last_fact_sets, last_shown)
        intent = produce_intent(question, chat, context)

        if intent.verb == "detail":
            command = intent.tokens[0]
            if last_fact_sets:
                say("\n" + render_detail(command, last_fact_sets) + "\n")
            else:
                say("Ask about a metric first — then I can show its "
                    f"{command}.")
            continue

        if intent.verb == "unsupported":
            reason = intent.tokens[0]
            say(UNSUPPORTED_MESSAGES[reason])
            _record_refusal(sink, user_id, question, f"unsupported:{reason}")
            continue

        if intent.verb == "compare":
            try:
                fs = _compare_flow(intent, question, chat, run_kql,
                                   sink, user_id, ask, say)
            except _NewQuestion as nq:
                pending = nq.text
                continue
            if fs is not None:
                last_fact_sets = [fs]
                say("\n" + narrate_question(fs, question, chat) + "\n")
            continue

        if intent.verb == "variants":
            fs = variants_answer(intent.tokens[0], run_kql)
            if fs is not None:
                last_fact_sets = [fs]
                say("\n" + narrate_question(fs, question, chat) + "\n")
                continue
            # misfired classification or fuzzy name: degrade to search
            say(f"No step named '{intent.tokens[0]}' found by exact "
                "name — searching instead.")

        tokens = intent.tokens
        fact_sets = []
        any_candidates = False
        shown_id_sets = []

        try:
            for token in tokens:
                result = resolve(token, run_kql)
                if not result.candidates:
                    if len(tokens) > 1:
                        say(f"For '{token}': nothing sufficiently related.")
                    _record(sink, user_id, question, result, None)
                    continue
                ids = {c.node_id for c in result.candidates}
                if duplicate_list(ids, shown_id_sets):
                    say(f"(Skipping '{token}' — repeats the list above.)")
                    continue   # nothing shown, so nothing to record
                shown_id_sets.append(ids)
                any_candidates = True
                last_shown = list(result.candidates)
                header = f"For '{token}':" if len(tokens) > 1 else ""
                say(render_candidates(result, header))
                try:
                    picked = _ask_pick(ask, say, result)
                except _NewQuestion as nq:
                    _record(sink, user_id, question, result, None)
                    pending = nq.text
                    raise
                if picked is None:
                    say("Noted — none of these matched what you meant.")
                    _record(sink, user_id, question, result, None)
                    continue
                candidate = result.candidates[picked]
                _record(sink, user_id, question, result, candidate)
                try:
                    fact_sets.append(assemble(candidate, run_kql))
                except AssemblyError as e:
                    say(f"Could not assemble facts: {e}")
        except _NewQuestion:
            continue

        if fact_sets:
            last_fact_sets = fact_sets
            say("\n" + narrate_many(fact_sets, question, chat) + "\n")
            pending = _confirm(ask, say, sink, user_id, question, fact_sets)
        elif not any_candidates:
            say(REFUSAL_MESSAGE)


def _compare_flow(intent, question, chat, run_kql, sink, user_id,
                  ask, say):
    """Bind both subjects (context id, exact ref, or resolve+pick),
    then run the fixed panel. `choose` reuses the ordinary pick UI for
    ambiguous concept aspects (amendment 2)."""
    refs = []
    for subject in intent.tokens:
        ref = _bind_subject(subject, run_kql, ask, say, sink, user_id,
                            question)
        if ref is None:
            say("Could not identify both sides of the comparison.")
            return None
        refs.append(ref)

    def choose(prompt_label, candidates):
        say(prompt_label)
        fake = ResolutionResult(token=prompt_label, candidates=candidates,
                                total_matches=len(candidates), basis="")
        say(render_candidates(fake))
        return _ask_pick(ask, say, fake)   # None = skip the zoom;
                                           # _NewQuestion propagates

    try:
        return build_comparison(refs[0], refs[1], run_kql,
                                chosen_aspect=intent.aspect, choose=choose)
    except AssemblyError as e:
        say(f"Could not assemble facts: {e}")
        return None


def _confirm(ask, say, sink, user_id, question, fact_sets) -> "str | None":
    """The strong signal: after READING the answer, does the human stand
    by their pick? y = endorsement, n = rejection, Enter = skip (no
    signal). Anything else is a new question — same no-trap rule as the
    pick prompt. Returns the new question text, or None."""
    reply = ask("was this what you needed? (y/n, Enter to skip)> ").strip()
    verdict = {"y": "confirmed", "yes": "confirmed",
               "n": "rejected", "no": "rejected"}.get(reply.lower())
    if verdict is None and reply:
        say("(Taking that as a new question.)")
        return reply
    if verdict:
        now = datetime.now(timezone.utc).isoformat()
        for fs in fact_sets:
            sink.record(ConfirmEvent(
                event_at=now, user_id=user_id, question=question,
                picked_node_id=f"{fs.kind}:{fs.ref}", picked_ref=fs.ref,
                verdict=verdict,
            ))
        say("Thanks — recorded." if verdict == "confirmed"
            else "Noted — that definition didn't match what you meant.")
    return None


def _record(sink, user_id, question, result, candidate) -> None:
    sink.record(PickEvent(
        event_at=datetime.now(timezone.utc).isoformat(),
        user_id=user_id,
        question=question,
        token=result.token,
        candidates_shown=tuple(c.node_id for c in result.candidates),
        picked_node_id=candidate.node_id if candidate else None,
        picked_ref=candidate.ref if candidate else None,
        total_matches=result.total_matches,
    ))


def _record_refusal(sink, user_id, question, token) -> None:
    """Verb-gap refusals are logged (scorecard amendment 4): the miss
    stream demand-ranks the punch list of unbuilt verbs."""
    sink.record(PickEvent(
        event_at=datetime.now(timezone.utc).isoformat(),
        user_id=user_id, question=question, token=token,
        candidates_shown=(), picked_node_id=None, picked_ref=None,
        total_matches=0,
    ))


def main() -> None:
    """Dev entrypoint: az CLI auth, live Eventhouse, local event log."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from devtools.grounding_evals import _load_dotenv
    from devtools.local_llm import chat_completion
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider

    _load_dotenv()
    query_uri = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
    client = KustoClient(query_uri, "probe-eh", az_cli_token_provider(query_uri))
    sink = JsonlEventSink(Path("data") / "events" / "pick_events.jsonl")
    chat_loop(chat_completion, client.run, sink)


if __name__ == "__main__":
    main()
