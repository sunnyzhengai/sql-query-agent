"""Local LLM stand-in for the Fabric Data Agent — dev only, never shipped.

Serves the AgentBackend interface with a direct chat-completions call
(OpenAI-compatible; endpoint/model/key via env vars), grounded in
metric_logic rows the same way the Data Agent is grounded in the table:
retrieve relevant rows, answer ONLY from them, refuse beyond them.

Fidelity caveat: this validates OUR half (data quality, grounding rules,
refusal behavior) — not Fabric's internal NL2SQL orchestration. Final
agent verification remains a Fabric milestone task.

Env:
  OPENAI_API_KEY    required for live calls
  OPENAI_BASE_URL   default https://api.openai.com/v1
  AIVIA_LLM_MODEL   default gpt-4o-mini
"""

from __future__ import annotations

import os
from typing import Any

from src.agent_backend import build_description_prompt, retrieve_metric_rows
from src.llm_client import chat_completion as _chat_completion


def chat_completion(
    system: str,
    user: str,
    *,
    api_key: "str | None" = None,
    base_url: "str | None" = None,
    model: "str | None" = None,
    timeout: int = 60,
) -> str:
    """Env-driven wrapper over src.llm_client — devtools' LLM doorway.

    Azure header/url handling lives in src.llm_client (shared with 07);
    this only resolves the dev-environment defaults.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    return _chat_completion(
        system, user,
        endpoint=base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        api_key=key,
        model=model or os.environ.get("AIVIA_LLM_MODEL", "gpt-4o-mini"),
        timeout=timeout,
    )


GROUNDING_INSTRUCTIONS = (
    "You answer questions about certified business metrics using ONLY the "
    "metric data provided below. Every claim must come from the provided "
    "calculation logic, source tables, or descriptions. If the provided data "
    "does not contain the answer, reply exactly: "
    "\"I don't have that information in the certified knowledge base.\" "
    "Never invent metrics, tables, or logic."
)


class LocalLLMBackend:
    def __init__(
        self,
        metric_rows: "list[dict[str, Any]]",
        api_key: "str | None" = None,
        base_url: "str | None" = None,
        model: "str | None" = None,
        timeout: int = 60,
    ) -> None:
        self.metric_rows = metric_rows
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = model or os.environ.get("AIVIA_LLM_MODEL", "gpt-4o-mini")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set — the local stand-in makes live LLM "
                "calls (or use ReplayBackend with a recorded cassette)."
            )

    def _chat(self, system: str, user: str) -> str:
        return chat_completion(
            system, user,
            api_key=self.api_key, base_url=self.base_url,
            model=self.model, timeout=self.timeout,
        )

    @staticmethod
    def _row_context(rows: "list[dict[str, Any]]") -> str:
        if not rows:
            return "(no matching certified metrics)"
        blocks = []
        for r in rows:
            blocks.append(
                f"metric_id: {r['metric_id']}\n"
                f"  name: {r.get('metric_name')}\n"
                f"  calculation_logic: {r.get('calculation_logic')}\n"
                f"  source_tables: {r.get('source_tables')}\n"
                f"  table_descriptions: {r.get('table_descriptions')}"
            )
        return "\n\n".join(blocks)

    def answer(self, question: str) -> str:
        rows = retrieve_metric_rows(question, self.metric_rows)
        context = self._row_context(rows)
        return self._chat(
            GROUNDING_INSTRUCTIONS,
            f"Certified metric data:\n{context}\n\nQuestion: {question}",
        )

    def describe_metric(self, metric_row: "dict[str, Any]") -> str:
        return self._chat(GROUNDING_INSTRUCTIONS, build_description_prompt(metric_row))
