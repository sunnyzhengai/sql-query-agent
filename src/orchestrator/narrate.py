"""The exit edge: the LLM narrates assembled facts — language only.

The prose is grounded in the FactSet and nothing else; the Basis line
is appended BY CODE after narration, so provenance can never be
invented. Invariants here are the product's constitution, not question
templates.
"""

from __future__ import annotations

from typing import Callable

from src.orchestrator.assemble import FactSet

NARRATE_SYSTEM = (
    "You write clear business prose from the provided facts — nothing "
    "else. Rules:\n"
    "1. Every claim must come from the facts given. Never add outside "
    "knowledge, never estimate, never fill gaps.\n"
    "2. Translate any SQL into business language; never paste raw SQL.\n"
    "3. If a fact is null or missing, either omit it or say it is not "
    "recorded — do not invent it.\n"
    "4. Never output personal names from inside SQL text, medical record "
    "numbers, or patient identifiers; use generic labels.\n"
    "5. ONLY if BOTH report_name AND report_url appear in the facts, end "
    "with: Used in: <report_name> (<report_url>). If either is absent, "
    "write NO Used-in line at all — never substitute the business name "
    "or write placeholders like (not recorded).\n"
    "6. No greetings, no confidence claims, no percentages of certainty."
)


def facts_block(fact_set: FactSet) -> str:
    lines = [f"{k}: {v}" for k, v in fact_set.facts.items() if v not in (None, "")]
    return "\n".join(lines)


def narrate(fact_set: FactSet, chat: "Callable[[str, str], str]") -> str:
    """chat(system, user) -> str is the injected LLM client. Returns the
    full answer: LLM prose + the code-stamped Basis line."""
    prose = chat(
        NARRATE_SYSTEM,
        f"Facts about this {fact_set.kind}:\n{facts_block(fact_set)}\n\n"
        "Write the explanation a business user needs.",
    ).strip()
    return f"{prose}\n\nBasis: {fact_set.basis}"


def narrate_question(
    fact_set: FactSet, question: str, chat: "Callable[[str, str], str]"
) -> str:
    """Exit edge for verbs whose answer depends on what was asked (e.g.
    variants: 'do A and B agree?' is answered from the full partition).
    Same facts-only rules; the question frames, the facts bound."""
    prose = chat(
        NARRATE_SYSTEM,
        f"The user asked: {question}\n\nFacts about this {fact_set.kind}:\n"
        f"{facts_block(fact_set)}\n\n"
        "Answer their question using ONLY these facts.",
    ).strip()
    return f"{prose}\n\nBasis: {fact_set.basis}"


def narrate_many(
    fact_sets: "list[FactSet]",
    question: str,
    chat: "Callable[[str, str], str]",
) -> str:
    """Exit edge for multi-concept questions (comparisons, contrasts):
    same facts-only rules, several fact sets, the user's question for
    framing. The Basis lists every lookup — stamped by code."""
    if len(fact_sets) == 1:
        return narrate(fact_sets[0], chat)
    blocks = [
        f"--- Facts, item {i} ({fs.kind}) ---\n{facts_block(fs)}"
        for i, fs in enumerate(fact_sets, 1)
    ]
    prose = chat(
        NARRATE_SYSTEM,
        f"The user asked: {question}\n\n" + "\n\n".join(blocks) +
        "\n\nAnswer their question using ONLY these facts. If they asked "
        "for a comparison, compare the items point by point.",
    ).strip()
    basis = "; ".join(fs.basis for fs in fact_sets)
    return f"{prose}\n\nBasis: {basis}"
