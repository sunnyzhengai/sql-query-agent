"""Fabric Data Agent programmatic client.

Calls the Fabric Data Agent via REST API to generate business descriptions
by leveraging the agent's graph traversal and persona instructions.

The agent produces better descriptions than direct LLM calls because it:
- Traverses the knowledge graph to find relevant sql_fragments
- Applies the persona instructions (business-friendly translation)
- Uses the SQL-to-business translation table
- Produces structured, criteria-focused output

API endpoint:
  POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{agentId}/chat/completions
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from the Data Agent."""
    question: str
    answer: str
    status: str  # "success" or "failed"
    error: str = ""


class FabricAgentClient:
    """Programmatic client for the Fabric Data Agent.

    Sends natural language questions and captures the agent's responses
    for use as metadata descriptions.

    Authentication: uses mssparkutils.credentials.getToken() in Fabric,
    or an explicit access token for testing.
    """

    BASE_URL = "https://api.fabric.microsoft.com/v1"

    def __init__(self, workspace_id: str, agent_id: str, access_token: str = "") -> None:
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self._access_token = access_token

    def _get_token(self) -> str:
        if self._access_token:
            return self._access_token
        try:
            import mssparkutils  # type: ignore
            return mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
        except ImportError:
            raise RuntimeError(
                "mssparkutils not available. Run in a Fabric Notebook "
                "or pass access_token explicitly."
            )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def query(self, question: str) -> AgentResponse:
        """Send a question to the Data Agent and return the response.

        Args:
            question: Natural language question for the agent.

        Returns:
            AgentResponse with the agent's answer.
        """
        import requests

        # Try multiple endpoint patterns (Fabric API has evolved)
        endpoints = [
            # Current public API
            f"{self.BASE_URL}/workspaces/{self.workspace_id}/items/{self.agent_id}/chat/completions",
            # Alternative paths
            f"{self.BASE_URL}/workspaces/{self.workspace_id}/dataagents/{self.agent_id}/chat/completions",
            f"{self.BASE_URL}/workspaces/{self.workspace_id}/aiskills/{self.agent_id}/chat/completions",
            # MCP endpoint
            f"{self.BASE_URL}/mcp/workspaces/{self.workspace_id}/dataagents/{self.agent_id}/agent",
        ]

        payload = {
            "messages": [
                {"role": "user", "content": question}
            ]
        }

        for endpoint in endpoints:
            try:
                resp = requests.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=120,  # agent may take time on complex queries
                )

                if resp.status_code == 200:
                    result = resp.json()
                    # Extract answer from response (format may vary)
                    answer = self._extract_answer(result)
                    logger.info("Agent responded via %s", endpoint.split("/")[-2])
                    return AgentResponse(
                        question=question,
                        answer=answer,
                        status="success",
                    )
                elif resp.status_code == 404:
                    continue  # try next endpoint
                else:
                    logger.warning("Agent endpoint %s returned %s: %s",
                                 endpoint, resp.status_code, resp.text[:200])
                    continue

            except Exception as e:
                logger.warning("Agent endpoint %s failed: %s", endpoint, e)
                continue

        return AgentResponse(
            question=question,
            answer="",
            status="failed",
            error="All agent endpoints failed. Check workspace_id and agent_id.",
        )

    def _extract_answer(self, response: dict[str, Any]) -> str:
        """Extract the answer text from the agent's API response."""
        # OpenAI-compatible format
        if "choices" in response:
            choices = response["choices"]
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "")

        # Fabric-specific format
        if "result" in response:
            return response["result"]

        if "answer" in response:
            return response["answer"]

        if "content" in response:
            return response["content"]

        # Fallback: return the whole response as string
        return str(response)

    def generate_metric_description(self, metric_name: str) -> AgentResponse:
        """Generate a business description for a metric using the Data Agent.

        Asks the agent a structured question that produces the same
        high-quality output as the interactive chat.
        """
        question = (
            f"Describe what the metric '{metric_name}' measures. "
            f"Include: what data it tracks, what criteria and filters are applied, "
            f"and what the output represents. Be specific about the business rules."
        )
        return self.query(question)

    def generate_descriptions_bulk(
        self,
        metric_names: list[str],
        batch_log_interval: int = 10,
    ) -> dict[str, AgentResponse]:
        """Generate descriptions for multiple metrics.

        Args:
            metric_names: List of metric names to describe.
            batch_log_interval: Log progress every N metrics.

        Returns:
            Dict of metric_name -> AgentResponse.
        """
        results: dict[str, AgentResponse] = {}
        succeeded = 0
        failed = 0

        logger.info("Generating descriptions for %d metrics via Data Agent", len(metric_names))

        for i, name in enumerate(metric_names):
            response = self.generate_metric_description(name)
            results[name] = response

            if response.status == "success":
                succeeded += 1
            else:
                failed += 1
                logger.warning("Failed for %s: %s", name, response.error)

            if (i + 1) % batch_log_interval == 0:
                logger.info("  Processed %d/%d metrics (%d succeeded, %d failed)",
                           i + 1, len(metric_names), succeeded, failed)

        logger.info("Done: %d succeeded, %d failed out of %d",
                    succeeded, failed, len(metric_names))
        return results
