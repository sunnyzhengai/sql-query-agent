"""AgentBackend — one interface for "ask the agent", many implementations.

The Fabric Data Agent is the production consumer of the knowledge graph;
during development the same interface is served by a direct-LLM stand-in
(devtools/local_llm.py, not shipped) and by ReplayBackend, which makes
recorded conversations deterministic for CI. Grounding evals run against
the interface, so the same eval suite scores every implementation.

One-home rules established here:
- build_description_prompt() is THE description prompt (07 and the Fabric
  client historically carried inline copies — migrate them here).
- REJECTION_MARKERS is THE refusal vocabulary: phrases that indicate the
  agent declined to answer (Path B). Used by description generation (to
  reject non-answers) and by grounding evals (to verify refusals).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

from src.parser.identity import fold_identifier

REJECTION_MARKERS = [
    "wasn't able to find", "couldn't find", "not found",
    "hasn't been", "i'm happy to help", "don't have information",
    "not available", "no documented", "i don't have",
]


def is_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return any(marker in lowered for marker in REJECTION_MARKERS)


class AgentBackend(Protocol):
    """Anything that can answer questions about the certified metrics."""

    def answer(self, question: str) -> str: ...

    def describe_metric(self, metric_row: "dict[str, Any]") -> str: ...


def build_description_prompt(metric_row: "dict[str, Any]") -> str:
    """The one description prompt, grounded in the metric's contract row."""
    return (
        f"For the metric {metric_row['metric_id']}, write a concise business "
        "description in this format:\n\n"
        "First, one sentence stating the business purpose of the report "
        "(why it exists, who uses it, what decisions it supports).\n\n"
        "Then add a blank line and 'Business logic:' followed by a bulleted "
        "list of the key rules, filters, and criteria applied, in business "
        "terms (not SQL).\n\n"
        "Ground your answer ONLY in this certified calculation data:\n"
        f"Calculation logic: {metric_row.get('calculation_logic') or '(none)'}\n"
        f"Source tables: {metric_row.get('source_tables') or '(none)'}\n"
        f"Table descriptions: {metric_row.get('table_descriptions') or '(none)'}\n\n"
        "No greetings, no preamble, no markdown headers, no bold text. "
        "Start directly with the purpose sentence."
    )


def retrieve_metric_rows(
    question: str,
    metric_rows: "list[dict[str, Any]]",
    top_k: int = 3,
) -> "list[dict[str, Any]]":
    """Keyword retrieval over metric_logic rows (case-folded), for grounding
    a local stand-in the way the Data Agent grounds itself in the table."""
    folded_question = fold_identifier(question)
    scored = []
    for row in metric_rows:
        terms = [row["metric_id"], row.get("metric_name") or ""]
        terms += (row.get("source_tables") or "").split(",")
        score = sum(
            1 for t in terms
            if t.strip() and fold_identifier(t.strip()) in folded_question
        )
        if score:
            scored.append((score, row["metric_id"], row))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [row for _, _, row in scored[:top_k]]


class ReplayBackend:
    """Record/replay wrapper — the VCR pattern for agent conversations.

    modes:
      replay  - serve from cassette; a miss raises with re-record guidance
      record  - delegate to the wrapped backend and persist every exchange
      auto    - replay on hit, otherwise record (requires a wrapped backend)
    """

    def __init__(
        self,
        cassette_path: "str | Path",
        backend: "AgentBackend | None" = None,
        mode: str = "replay",
    ) -> None:
        assert mode in ("replay", "record", "auto")
        if mode in ("record", "auto") and backend is None:
            raise ValueError(f"mode={mode} requires a wrapped backend")
        self.cassette_path = Path(cassette_path)
        self.backend = backend
        self.mode = mode
        self._cache: "dict[str, str]" = {}
        if self.cassette_path.exists():
            for line in self.cassette_path.read_text().splitlines():
                entry = json.loads(line)
                self._cache[entry["key"]] = entry["response"]

    @staticmethod
    def _key(kind: str, payload: str) -> str:
        return hashlib.sha256(f"{kind}\n{payload}".encode()).hexdigest()[:24]

    def _lookup_or_delegate(self, kind: str, payload: str, delegate) -> str:
        key = self._key(kind, payload)
        if key in self._cache and self.mode in ("replay", "auto"):
            return self._cache[key]
        if self.mode == "replay":
            raise KeyError(
                f"No recorded response for this {kind} in {self.cassette_path} — "
                f"re-record with mode='record' (payload: {payload[:80]}...)"
            )
        response = delegate()
        self._cache[key] = response
        with open(self.cassette_path, "a") as f:
            f.write(json.dumps({"key": key, "kind": kind,
                                "payload": payload[:200], "response": response}) + "\n")
        return response

    def answer(self, question: str) -> str:
        return self._lookup_or_delegate(
            "answer", question, lambda: self.backend.answer(question)
        )

    def describe_metric(self, metric_row: "dict[str, Any]") -> str:
        payload = build_description_prompt(metric_row)
        return self._lookup_or_delegate(
            "describe", payload, lambda: self.backend.describe_metric(metric_row)
        )


class FabricAgentBackend:
    """Production backend: the Fabric Data Agent via the MCP client."""

    def __init__(self, workspace_id: str, agent_id: str, access_token: str) -> None:
        from src.adapters.fabric_agent import FabricAgentClient  # lazy: needs requests

        self._client = FabricAgentClient(
            workspace_id=workspace_id, agent_id=agent_id, access_token=access_token
        )
        self._client.discover_tool_name()

    def answer(self, question: str) -> str:
        return self._client.query(question).answer

    def describe_metric(self, metric_row: "dict[str, Any]") -> str:
        return self._client.query(build_description_prompt(metric_row)).answer
