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

# The conversational entry edge (ADR 0034): the LLM ROUTES — it reads
# the conversation state plus the new question and chooses ONE typed
# request from a closed menu. It never composes a query and never
# answers. Plain lines are the safe default (search), so malformed or
# unrecognized output degrades to the ordinary flow, never breaks.
INTENT_SYSTEM_PROMPT = (
    "You route a user's request in a conversation about business "
    "metrics. You receive conversation state (the last answer, any "
    "visible candidate list) and the new question. Output EXACTLY ONE "
    "typed request — never answer the question yourself. Forms:\n"
    "1. DETAIL: sql|owner|tables|link — the question asks for that "
    "detail of what the last answer covered ('show me its sql', 'who "
    "owns it').\n"
    "2. VARIANTS: <name> — the question asks whether definitions of one "
    "NAMED step, table, or calculation agree, differ, or have drifted "
    "across procedures or reports.\n"
    "3. COMPARE: <subject A> | <subject B> — the question compares two "
    "metrics or reports; name each subject exactly as the conversation "
    "state names it (prefer the id in parentheses when shown). Append "
    "| on=<aspect> when one specific aspect is compared — a field "
    "(developer, steward, tables, steps, sql, report) or a concept "
    "phrase (e.g. sepsis definition).\n"
    "4. UNSUPPORTED: lineage|enumerate|usage|data-values — the question "
    "asks for a known-unsupported thing: lineage (what feeds a table / "
    "what is downstream of it), enumerate (list all items matching a "
    "filter), usage (who uses what, how often), data-values (actual "
    "row-level data, counts, totals).\n"
    "5. Otherwise (the DEFAULT): output ONE short search phrase (2-6 "
    "words) per DISTINCT business concept the question asks about, one "
    "per line, at most 3 lines. A single concept gets exactly ONE line; "
    "never two phrasings of the same concept. Plain lines only — no "
    "numbering, no punctuation, no explanation.\n"
    "Never add concepts, subjects, or aspects the question does not "
    "imply. When unsure, use form 5."
)

MAX_TOKENS_PER_QUESTION = 3

DETAIL_KEYS = ("sql", "owner", "tables", "link")
UNSUPPORTED_REASONS = ("lineage", "enumerate", "usage", "data-values")

# Deterministic backstop for over-split tokens (live find, 2026-08-10:
# "which metrics defined sepsis" -> 'sepsis metrics' + 'sepsis definition
# metrics', two near-identical candidate lists, two pick rounds). The
# prompt discourages the split; this guard makes the duplicate harmless.
DUPLICATE_LIST_OVERLAP = 0.5

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
class Intent:
    verb: str                    # search | variants | detail | compare | unsupported
    tokens: "tuple[str, ...]"    # phrases / (name,) / (command,) / subjects / (reason,)
    aspect: "str | None" = None  # compare only: field name or concept phrase


def produce_intent(
    question: str, chat: "Callable[[str, str], str]", context: str = ""
) -> Intent:
    """The conversational entry edge: route + translate in one call.
    `context` is the code-built conversation state (last answer, visible
    candidates) — the LLM resolves 'this/it/they' against it. Every
    prefixed form is validated structurally; anything malformed falls
    through to search, so a misbehaving model can only ever degrade to
    the default flow.
    """
    user = f"{context}\nQuestion: {question}" if context else question
    raw = chat(INTENT_SYSTEM_PROMPT, user)
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    first = lines[0].strip() if lines else ""
    upper = first.upper()
    if upper.startswith("VARIANTS:"):
        name = _sanitize(first.split(":", 1)[1])
        if name:
            return Intent(verb="variants", tokens=(name,))
    elif upper.startswith("DETAIL:"):
        command = first.split(":", 1)[1].strip().lower()
        if command in DETAIL_KEYS:
            return Intent(verb="detail", tokens=(command,))
    elif upper.startswith("UNSUPPORTED:"):
        reason = first.split(":", 1)[1].strip().lower()
        if reason in UNSUPPORTED_REASONS:
            return Intent(verb="unsupported", tokens=(reason,))
    elif upper.startswith("COMPARE:"):
        parts = [p.strip() for p in first.split(":", 1)[1].split("|")]
        subjects = [p for p in parts if p and not p.lower().startswith("on=")]
        aspects = [p[3:].strip() for p in parts if p.lower().startswith("on=")]
        if len(subjects) == 2 and all(subjects):
            return Intent(verb="compare", tokens=tuple(subjects),
                          aspect=aspects[0] if aspects and aspects[0] else None)
    tokens = [_sanitize(ln) for ln in lines if _sanitize(ln)]
    tokens = tokens[:MAX_TOKENS_PER_QUESTION] or [_sanitize(raw)]
    return Intent(verb="search", tokens=tuple(tokens))


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


def duplicate_list(
    new_ids: "set[str]", prior_id_sets: "list[set[str]]"
) -> bool:
    """True when a candidate list substantially repeats one already shown
    for THIS question — noise from an over-split token, not a second
    concept. Overlap coefficient (shared / smaller list) against each
    prior list; deterministic set math, never a model judgment.
    """
    for prior in prior_id_sets:
        denom = min(len(new_ids), len(prior))
        if denom and len(new_ids & prior) / denom >= DUPLICATE_LIST_OVERLAP:
            return True
    return False


def parse_pick(reply: str, candidates: "tuple[Candidate, ...]") -> "int | None":
    """Structural pick: 1-based number, or exact (case-folded) name /
    business name / ref. Returns the candidate index or None (re-prompt).
    Never interprets — a fuzzy reply is the surface layer's optional,
    validated LLM fallback, not the core's concern.
    """
    text = reply.strip()
    if not text:
        return None   # empty must never exact-match an empty business_name
    if text.isdigit():
        n = int(text)
        return n - 1 if 1 <= n <= len(candidates) else None
    folded = _fold(text)
    for i, c in enumerate(candidates):
        if folded in (_fold(c.name), _fold(c.business_name), _fold(c.ref)):
            return i
    return None
