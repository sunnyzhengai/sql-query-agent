"""AIVIA orchestrator — agentic conversation, deterministic tools
(ADR 0032/0035).

The LLM owns the conversation. The engine owns every computation. The
trace is always code. Right answers are computed, judgments are
disclosed, language is generated.
"""

from src.orchestrator.core import (  # noqa: F401
    Candidate,
    ResolutionResult,
    produce_search_token,
    resolve,
)
