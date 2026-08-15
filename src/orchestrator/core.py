"""The retrieval core (ADR 0032/0035).

resolve(token) — ONE fixed KQL command, the token is the only
parameter; threshold/rank/ties are config and math, never generation;
stratified plurality (closest metrics + closest steps). Consumed by
the ADR 0035 toolset (tools.py) and the robustness suite.

Replay property (CI-enforced): same token + same catalog state =>
identical candidate list, order, and basis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

TOKEN_SYSTEM_PROMPT = (
    "You turn a user's question about business metrics into ONE short "
    "search phrase (2-6 words) naming the core business concept. Output "
    "the phrase only — no punctuation, no quotes, no explanation. Do not "
    "add words the question does not imply."
)

# The ONE fixed command. The token is the only variable — parameterized
# via Kusto's declare statement so user text is data, never query syntax.
# Fetches a wide slice (100) so stratification below has material.
RESOLVE_QUERY = (
    "declare query_parameters(token:string);\n"
    "semantic_search(token, 100)"
)

# Stratified plurality (live find 2026-08-10): steps outnumber metrics
# 413:28 and sibling steps cluster in embedding space, so a flat top-10
# buried every metric but one under a single proc's branch steps
# ("ED2GEN, ED2ICU, IV, ETT..." while ED Sepsis (Regulatory) went
# unshown). The candidate list is the ROADMAP Phase A full plurality:
# the closest METRICS and the closest STEPS as labeled groups, with a
# per-proc cap inside the step group for diversity. Pure code —
# closeness order within groups, node_id ties, replayable.
METRICS_SHOWN = 5
STEPS_SHOWN = 5
STEPS_PER_PROC = 2


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
    ordered = sorted(rows, key=lambda r: (-float(r["closeness"]), r["node_id"]))

    metrics = [r for r in ordered if r["kind"] == "metric"][:METRICS_SHOWN]
    steps, per_proc = [], {}
    for r in ordered:
        if r["kind"] != "step":
            continue
        if per_proc.get(r["ref"], 0) >= STEPS_PER_PROC:
            continue
        per_proc[r["ref"]] = per_proc.get(r["ref"], 0) + 1
        steps.append(r)
        if len(steps) >= STEPS_SHOWN:
            break
    other = [r for r in ordered if r["kind"] not in ("metric", "step")]

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
        for r in metrics + steps + other[:2]
    )
    total = int(ordered[0]["total_matches"]) if ordered else 0
    basis = (
        f"semantic_search({token!r}) -> {total} above threshold; "
        f"showing {len(metrics)} metric(s) + {len(steps)} step(s)"
    )
    return ResolutionResult(
        token=token, candidates=candidates, total_matches=total, basis=basis
    )
