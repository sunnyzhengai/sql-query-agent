"""The conversational agent (ADR 0035): LLM owns the conversation,
tools own every computation, code stamps the trace.

One function-calling loop over the customer's Azure OpenAI. The system
prompt is invariants only — no question templates, no verb menus, no
conversation shapes. The Basis line under every answer is built by
code from the actual tool calls of that turn; the model never writes
its own provenance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from src.orchestrator.tools import TOOL_SCHEMAS, Session, dispatch

SYSTEM_PROMPT = (
    "You are AIVIA, the certified-metrics assistant for this "
    "organization's data governance knowledge base.\n"
    "Invariants — these are absolute:\n"
    "1. Every factual claim must come from a tool result in this "
    "conversation. You may arrange and summarize facts; you may never "
    "add, estimate, or fill gaps. If the tools cannot support an "
    "answer, say so plainly.\n"
    "2. Questions outside the certified knowledge base: refuse honestly "
    "and say what you CAN answer. Outside it are: actual patient or "
    "row-level data and counts; LINEAGE (which metrics read from or are "
    "downstream of a table — the tools cannot answer this; search "
    "results are NOT lineage, never present them as such); usage "
    "statistics; and listing all items by a filter such as owner.\n"
    "2b. NEVER refuse a question that mentions a clinical or business "
    "concept without searching first — 'how is X defined' means how "
    "this ORGANIZATION defines/calculates X, which the certified "
    "metrics likely answer. Search, show what exists, and only then "
    "say what is missing.\n"
    "3. For any question about whether SQL logic is the same or "
    "different, call check_same_logic — never judge SQL equality "
    "yourself.\n"
    "4. Closeness is the relevance signal. Plausible matches (roughly "
    "0.5 and above): show the candidates by business name and either "
    "ask which the user meant or answer the most likely one while "
    "naming the alternatives — never silently pretend there was only "
    "one. Only weak matches (below roughly 0.5): say nothing "
    "sufficiently related exists — never present weak matches as if "
    "they were relevant.\n"
    "4b. Answer the question actually asked, about the item actually "
    "named: a question about a specific named STEP operates on that "
    "step's ids (not the whole metrics); a question about TABLES uses "
    "the source tables in metric facts (not the step list). If the "
    "user names an item that has not been surfaced UNDER THAT NAME in "
    "this conversation, look it up (find_by_name, then search) — NEVER "
    "substitute a similarly-themed item you happen to have seen; a "
    "name mismatch is a wrong answer.\n"
    "5. Translate SQL into business language in answers; show raw SQL "
    "only when asked for it.\n"
    "6. Never output personal names from inside SQL text, medical "
    "record numbers, or patient identifiers.\n"
    "7. Mention a report/dashboard link only if BOTH its name and URL "
    "appear in tool results.\n"
    "8. Be concise and direct; no greetings, no confidence "
    "percentages."
)

MAX_TOOL_ROUNDS = 8


@dataclass
class Turn:
    answer: str
    basis: str
    trace: "list[dict]" = field(default_factory=list)


def _basis_from_trace(trace: "list[dict]", had_prior_facts: bool = False) -> str:
    """Guarantee 2 (ADR 0035): disclosure is stamped, not written."""
    parts = []
    for t in trace:
        name, args, result = t["tool"], t["args"], t["result"]
        if "error" in result:
            parts.append(f"{name}({_short(args)}) -> error")
        elif name == "search_catalog":
            n = len(result.get("candidates", []))
            parts.append(f"search({args.get('phrase', '')!r}) -> "
                         f"{n} candidates shown")
        elif name == "find_by_name":
            parts.append(f"find_by_name({args.get('name', '')!r}) -> "
                         f"{result.get('count', 0)} exact matches")
        elif name == "get_facts":
            parts.append(f"facts[{args.get('id', '')}]")
        elif name == "list_steps":
            parts.append(f"steps[{args.get('ref', '')}] -> "
                         f"{result.get('count', 0)}")
        elif name == "check_same_logic":
            ids = args.get("ids", [])
            shown = ", ".join(ids[:4]) + (", ..." if len(ids) > 4 else "")
            parts.append(
                f"same_logic([{shown}]) -> "
                f"{result.get('distinct_definitions', '?')} distinct")
    if parts:
        return "; ".join(parts)
    if had_prior_facts:
        return ("no new lookups — answered from facts already retrieved "
                "in this conversation")
    return "no tools consulted"


def _short(args: dict) -> str:
    s = json.dumps(args)
    return s if len(s) <= 60 else s[:60] + "..."


def run_turn(
    history: "list[dict]",
    user_text: str,
    chat_api: "Callable[[list[dict], list[dict]], dict]",
    run_kql,
    session: Session,
) -> Turn:
    """One conversational turn. `history` is mutated in place (system
    prompt + prior turns + this turn's tool exchanges). `chat_api`
    takes (messages, tool_schemas) and returns the assistant message
    dict (OpenAI chat-completions shape).
    """
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
    session.note_user(user_text)
    history.append({"role": "user", "content": user_text})

    trace: "list[dict]" = []
    for _ in range(MAX_TOOL_ROUNDS):
        message = chat_api(history, TOOL_SCHEMAS)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            answer = (message.get("content") or "").strip()
            basis = _basis_from_trace(trace, bool(session.surfaced))
            history.append({"role": "assistant", "content": answer})
            return Turn(answer=answer, basis=basis, trace=trace)
        history.append(message)
        for call in tool_calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            result = dispatch(name, args, run_kql, session)
            trace.append({"tool": name, "args": args, "result": result})
            history.append({
                "role": "tool",
                "tool_call_id": call.get("id", ""),
                "content": json.dumps(result),
            })

    answer = ("I hit the per-question tool budget before finishing — "
              "please ask a narrower question.")
    history.append({"role": "assistant", "content": answer})
    return Turn(answer=answer, basis=_basis_from_trace(trace), trace=trace)


def azure_chat_api(timeout: int = 120) -> "Callable[[list[dict], list[dict]], dict]":
    """Live chat-completions caller with tools, env-driven like
    devtools.local_llm (shared url/header logic from src.llm_client)."""
    import os

    import requests

    from src.llm_client import build_chat_request

    endpoint = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("AIVIA_LLM_MODEL", "gpt-4o-mini")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    url, headers = build_chat_request(endpoint, api_key)

    def call(messages: "list[dict]", tools: "list[dict]") -> dict:
        resp = requests.post(
            url, headers=headers,
            json={"model": model, "messages": messages, "tools": tools},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]

    return call
