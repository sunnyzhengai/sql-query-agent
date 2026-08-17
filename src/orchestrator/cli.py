"""Certified-metrics chat — surface v1 (terminal REPL), ADR 0035 thin.

The surface relays the conversation and prints the code-stamped Basis
under each answer. No menus, no grammars, no dialogue machinery — the
agent owns the conversation; the tools own the computations. Run:

    python -m src.orchestrator.cli
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from src.orchestrator.agent import azure_chat_api, run_turn
from src.orchestrator.events import JsonlEventSink, TurnEvent, decision_shape
from src.orchestrator.tools import Session

# Terminal reality (live find, 2026-08-10): Esc/arrow keys glue
# invisible escape sequences onto typed input — strip ANSI sequences,
# then any remaining non-printables, before anything sees it.
_ANSI_SEQ = re.compile(r"\x1b\[[0-9;?]*[A-Za-z~]")


def clean_input(text: str) -> str:
    text = _ANSI_SEQ.sub("", text)
    return "".join(ch for ch in text if ch.isprintable()).strip()


def chat_loop(chat_api, run_kql, sink, user_id: str = "local-dev",
              ask=input, say=print) -> None:
    from src.branding import product_name
    say(f"{product_name()} — ask about your certified metrics ('q' to quit)\n")
    import json as _json
    import uuid

    history: "list[dict]" = []
    session = Session()
    conv_id = f"cli-{uuid.uuid4()}"
    turn_index = 0
    while True:
        question = clean_input(ask("you> "))
        if question.lower() in ("q", "quit", "exit"):
            return
        if not question:
            continue
        turn = run_turn(history, question, chat_api, run_kql, session)
        say(f"\n{turn.answer}\n\nBasis: {turn.basis}\n")
        sink.record(TurnEvent(
            event_at=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            question=question,
            tools_used=tuple(t["tool"] for t in turn.trace),
            ids_read=tuple(sorted({
                t["args"].get("id") or t["args"].get("ref")
                for t in turn.trace
                if t["tool"] in ("get_facts", "list_steps")
                and (t["args"].get("id") or t["args"].get("ref"))})),
            basis=turn.basis,
            answered=bool(turn.answer),
            conversation_id=conv_id, turn_index=turn_index,
            decision=decision_shape(turn.trace, turn.answer),
            trace=tuple(
                {"tool": t["tool"], "args": t["args"],
                 "result": _json.dumps(t["result"])[:1500]}
                for t in turn.trace),
        ))
        turn_index += 1


def main() -> None:
    """Dev entrypoint: az CLI auth, live Eventhouse, local event log."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from devtools.grounding_evals import _load_dotenv
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider

    _load_dotenv()
    query_uri = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
    client = KustoClient(query_uri, "probe-eh", az_cli_token_provider(query_uri))
    sink = JsonlEventSink(Path("data") / "events" / "turn_events.jsonl")
    chat_loop(azure_chat_api(), client.run, sink)


if __name__ == "__main__":
    main()
