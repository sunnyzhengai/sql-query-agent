"""AIVIA orchestrator — Deterministic Core, LLM Edges (ADR 0032).

The LLM translates. The data answers. The human decides.

Two LLM touchpoints (produce the search token; narrate assembled
facts); everything between is replayable code. This package is the
core's spine — also the engine of the paraphrase-robustness suite.
"""

from src.orchestrator.core import (  # noqa: F401
    Candidate,
    ResolutionResult,
    parse_pick,
    produce_search_token,
    resolve,
)
