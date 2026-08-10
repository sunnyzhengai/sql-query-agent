"""The two edges and the deterministic core (ADR 0032).

Entry edge:  produce_search_token(question)  — one LLM call, one string out.
Core:        resolve(token)                  — ONE fixed KQL command, the
             token is the only parameter; threshold/rank/ties are config
             and math, never generation.
Pick:        parse_pick(reply, candidates)   — structural: number or exact
             name, parsed by code. (Optional LLM fallback lives in the
             surface layer, validated against the candidate set.)
Exit edge:   narrate(...)                    — surface-layer concern; the
             core returns facts and a code-stamped basis, never prose.

Replay property (CI-enforced): same token + same catalog state =>
identical candidate list, order, and basis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.graph.templates import _fold  # case-fold used across resolution

TOKEN_SYSTEM_PROMPT = (
    "You turn a user's question about business metrics into ONE short "
    "search phrase (2-6 words) naming the core business concept. Output "
    "the phrase only — no punctuation, no quotes, no explanation. Do not "
    "add words the question does not imply."
)

TOKENS_SYSTEM_PROMPT = (
    "You turn a user's question about business metrics into search "
    "phrases. Output ONE short phrase (2-6 words) per DISTINCT business "
    "concept the question asks about, one per line, at most 3 lines. A "
    "question about a single concept gets exactly one line; a comparison "
    "of two things gets two lines. No numbering, no punctuation, no "
    "explanation. Do not add concepts the question does not name."
)

MAX_TOKENS_PER_QUESTION = 3

# The ONE fixed command. The token is the only variable — parameterized
# via Kusto's declare statement so user text is data, never query syntax.
RESOLVE_QUERY = (
    "declare query_parameters(token:string);\n"
    "semantic_search(token)"
)


@dataclass(frozen=True)
class Candidate:
    node_id: str
    kind: str            # metric | step | term
    ref: str             # metric_id or term_id
    name: str
    business_name: str
    display_text: str
    closeness: float
    total_matches: int


@dataclass(frozen=True)
class ResolutionResult:
    token: str
    candidates: "tuple[Candidate, ...]"   # ranked, ALL above threshold (<=k)
    total_matches: int                    # how many cleared the threshold
    basis: str                            # stamped by code, never by an LLM


def _sanitize(raw: str) -> str:
    token = " ".join(raw.replace('"', " ").replace("'", " ").split())
    return token[:120]


def produce_search_tokens(
    question: str, chat: "Callable[[str, str], str]"
) -> "list[str]":
    """Entry edge, multi-concept: 1..MAX tokens, one per concept the
    question names. Still translation-only — decomposing a comparison
    into two phrases is a linguistic act, not a retrieval decision; a
    wrong split degrades UX, never correctness.
    """
    raw = chat(TOKENS_SYSTEM_PROMPT, question)
    tokens = [_sanitize(line) for line in raw.splitlines() if _sanitize(line)]
    return tokens[:MAX_TOKENS_PER_QUESTION] or [_sanitize(raw)]


def produce_search_token(question: str, chat: "Callable[[str, str], str]") -> str:
    """Entry edge. `chat(system, user) -> str` is the injected LLM client.

    The output is sanitized to a bare phrase — even a misbehaving model
    cannot smuggle syntax into the core (the core parameterizes anyway;
    this is belt-and-braces).
    """
    return _sanitize(chat(TOKEN_SYSTEM_PROMPT, question))


def resolve(
    token: str,
    run_kql: "Callable[[str, dict], list[dict]]",
) -> ResolutionResult:
    """The deterministic core. `run_kql(query, parameters) -> rows` is the
    injected Kusto client; this function decides nothing at runtime —
    threshold and top_k live in the semantic_search function definition
    (config), ranking is the vector math, ties break on node_id.
    """
    rows = run_kql(RESOLVE_QUERY, {"token": token})
    candidates = tuple(
        Candidate(
            node_id=r["node_id"],
            kind=r["kind"],
            ref=r["ref"],
            name=r["name"],
            business_name=r.get("business_name") or "",
            display_text=r.get("display_text") or "",
            closeness=float(r["closeness"]),
            total_matches=int(r["total_matches"]),
        )
        for r in sorted(
            rows, key=lambda r: (-float(r["closeness"]), r["node_id"])
        )
    )
    total = candidates[0].total_matches if candidates else 0
    basis = (
        f"semantic_search({token!r}) -> {total} above threshold, "
        f"showing {len(candidates)}"
    )
    return ResolutionResult(
        token=token, candidates=candidates, total_matches=total, basis=basis
    )


def parse_pick(reply: str, candidates: "tuple[Candidate, ...]") -> "int | None":
    """Structural pick: 1-based number, or exact (case-folded) name /
    business name / ref. Returns the candidate index or None (re-prompt).
    Never interprets — a fuzzy reply is the surface layer's optional,
    validated LLM fallback, not the core's concern.
    """
    text = reply.strip()
    if text.isdigit():
        n = int(text)
        return n - 1 if 1 <= n <= len(candidates) else None
    folded = _fold(text)
    for i, c in enumerate(candidates):
        if folded in (_fold(c.name), _fold(c.business_name), _fold(c.ref)):
            return i
    return None
