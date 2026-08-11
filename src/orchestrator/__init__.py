"""AIVIA orchestrator — Deterministic Core, LLM Edges (ADR 0032/0034).

The LLM translates. The data answers. The human decides.

Two LLM touchpoints (the conversational entry edge routes to a closed
verb menu; the narrate edge speaks computed facts); everything between
is replayable code. This package is the core's spine — also the engine
of the paraphrase-robustness suite.
"""

from src.orchestrator.core import (  # noqa: F401
    Candidate,
    Intent,
    ResolutionResult,
    parse_pick,
    produce_intent,
    produce_search_token,
    resolve,
)
