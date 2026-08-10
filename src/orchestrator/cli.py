"""AIVIA chat — surface v1 (terminal REPL).

The full ADR 0032 loop, human-visible:

    question -> token -> candidates (ALL shown, ranked, closeness
    visible, weak matches labeled) -> the human picks (number or exact
    name; 'n' declines) -> fixed assembly -> narration + code-stamped
    Basis -> pick captured to the flywheel sink.

No bypass: one candidate is presented exactly like ten. Run:

    python -m src.orchestrator.cli
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from src.orchestrator.assemble import AssemblyError, assemble
from src.orchestrator.core import (
    ResolutionResult,
    duplicate_list,
    parse_pick,
    produce_search_tokens,
    resolve,
)

# Terminal reality (live find, 2026-08-10): Esc/arrow keys glue invisible
# escape sequences onto typed replies — "\x1b2" is not a digit, so a real
# pick fell through to the new-question hatch. Strip ANSI sequences, then
# any remaining non-printable characters, before parsing ANY input.
_ANSI_SEQ = re.compile(r"\x1b\[[0-9;?]*[A-Za-z~]")


def clean_input(text: str) -> str:
    text = _ANSI_SEQ.sub("", text)
    return "".join(ch for ch in text if ch.isprintable()).strip()
from src.orchestrator.events import ConfirmEvent, JsonlEventSink, PickEvent
from src.orchestrator.narrate import narrate_many

WEAK_CLOSENESS = 0.40   # display label only — never a gate (ADR 0032)

REFUSAL_MESSAGE = (
    "Nothing in the certified knowledge base is sufficiently related to "
    "that. Try naming the metric, report, or business concept differently."
)

# Deterministic follow-up commands about the LAST answer (ADR 0032:
# follow-ups are structural, not a new LLM decision). Matching: strip
# filler words; the remainder must be exactly one command's keywords.
_FILLER = {"show", "me", "its", "the", "their", "his", "her", "please",
           "can", "you", "what", "is", "are", "give", "of", "this", "that",
           "it", "who", "which", "does", "do", "for", "a", "an", "?"}
DETAIL_COMMANDS = {
    "sql": {"sql", "code", "query", "logic"},
    "owner": {"owner", "owners", "steward", "developer", "owns"},
    "tables": {"tables", "sources", "table"},
    "link": {"link", "url", "report", "dashboard"},
}


def match_detail_command(question: str) -> "str | None":
    words = [w.strip("?.,!").lower() for w in question.split()]
    rest = {w for w in words if w and w not in _FILLER}
    if not rest:
        return None
    for command, keywords in DETAIL_COMMANDS.items():
        if rest <= keywords:
            return command
    return None


def render_detail(command: str, fact_sets) -> str:
    """Pure code — facts straight from the last assembly, no LLM."""
    out = []
    for fs in fact_sets:
        f = fs.facts
        label = (f.get("business_name") or f.get("metric_name")
                 or f.get("step_name") or fs.ref)
        if command == "sql":
            sql = f.get("calculation_logic") or f.get("sql_fragment")
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


def render_candidates(result: ResolutionResult, header: str = "") -> str:
    lines = []
    if header:
        lines.append(header)
    lines.append(
        f"Found {result.total_matches} related item(s); showing "
        f"{len(result.candidates)}:"
    )
    for i, c in enumerate(result.candidates, 1):
        weak = "  (weak match)" if c.closeness < WEAK_CLOSENESS else ""
        label = c.business_name or c.name
        lines.append(
            f"  {i}. {label} — {c.display_text}  "
            f"[closeness {c.closeness:.2f}]{weak}"
        )
    lines.append("Pick a number or exact name ('n' for none of these):")
    return "\n".join(lines)


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


def chat_loop(chat, run_kql, sink, user_id: str = "local-dev",
              ask=input, say=print) -> None:
    raw_ask = ask
    ask = lambda prompt="": clean_input(raw_ask(prompt))
    say("AIVIA — ask about your certified metrics ('q' to quit)\n")
    pending = None
    last_fact_sets = []
    while True:
        if pending is not None:
            question, pending = pending, None
        else:
            question = ask("you> ").strip()
        if question.lower() in ("q", "quit", "exit"):
            return
        if not question:
            continue

        command = match_detail_command(question)
        if command:
            if last_fact_sets:
                say("\n" + render_detail(command, last_fact_sets) + "\n")
            else:
                say("Ask about a metric first — then I can show its "
                    f"{command}.")
            continue

        tokens = produce_search_tokens(question, chat)
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
