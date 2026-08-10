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

from datetime import datetime, timezone

from src.orchestrator.assemble import AssemblyError, assemble
from src.orchestrator.core import (
    ResolutionResult,
    parse_pick,
    produce_search_token,
    resolve,
)
from src.orchestrator.events import JsonlEventSink, PickEvent
from src.orchestrator.narrate import narrate

WEAK_CLOSENESS = 0.40   # display label only — never a gate (ADR 0032)

REFUSAL_MESSAGE = (
    "Nothing in the certified knowledge base is sufficiently related to "
    "that. Try naming the metric, report, or business concept differently."
)


def render_candidates(result: ResolutionResult) -> str:
    lines = [
        f"Found {result.total_matches} related item(s); showing "
        f"{len(result.candidates)}:"
    ]
    for i, c in enumerate(result.candidates, 1):
        weak = "  (weak match)" if c.closeness < WEAK_CLOSENESS else ""
        label = c.business_name or c.name
        lines.append(
            f"  {i}. {label} — {c.display_text}  "
            f"[closeness {c.closeness:.2f}]{weak}"
        )
    lines.append("Pick a number or exact name ('n' for none of these):")
    return "\n".join(lines)


def chat_loop(chat, run_kql, sink, user_id: str = "local-dev",
              ask=input, say=print) -> None:
    say("AIVIA — ask about your certified metrics ('q' to quit)\n")
    while True:
        question = ask("you> ").strip()
        if question.lower() in ("q", "quit", "exit"):
            return
        if not question:
            continue

        token = produce_search_token(question, chat)
        result = resolve(token, run_kql)

        if not result.candidates:
            say(REFUSAL_MESSAGE)
            say(f"Basis: {result.basis}")
            _record(sink, user_id, question, result, None)
            continue

        say(render_candidates(result))
        picked = None
        while picked is None:
            reply = ask("pick> ").strip()
            if reply.lower() in ("n", "none"):
                break
            picked = parse_pick(reply, result.candidates)
            if picked is None:
                say("Reply with the item number or its exact name "
                    "('n' for none).")
        if picked is None:
            say("Noted — none of these matched what you meant.")
            _record(sink, user_id, question, result, None)
            continue

        candidate = result.candidates[picked]
        _record(sink, user_id, question, result, candidate)
        try:
            facts = assemble(candidate, run_kql)
        except AssemblyError as e:
            say(f"Could not assemble facts: {e}")
            continue
        say("\n" + narrate(facts, chat) + "\n")


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
