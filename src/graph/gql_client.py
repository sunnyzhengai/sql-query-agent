"""GQL query client for Fabric Graph API.

Sends GQL queries to the Fabric Graph executeQuery endpoint and returns
parsed results. Authentication mirrors FabricAgentClient: uses
mssparkutils in Fabric, or an explicit access token for local testing.

API Reference:
    POST https://api.fabric.microsoft.com/v1/workspaces/{wid}/GraphModels/{gid}/executeQuery?preview=true
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.fabric.microsoft.com/v1"


@dataclass
class GQLResult:
    """Parsed result from a GQL query."""
    columns: list[dict] = field(default_factory=list)
    data: list[dict] = field(default_factory=list)
    status_code: str = "00000"
    status_description: str = ""


class GQLClient:
    """Low-level GQL query client for Fabric Graph API."""

    def __init__(
        self,
        workspace_id: str,
        graph_model_id: str,
        access_token: str = "",
    ) -> None:
        self.workspace_id = workspace_id
        self.graph_model_id = graph_model_id
        self._access_token = access_token
        self._endpoint = (
            f"{BASE_URL}/workspaces/{workspace_id}"
            f"/GraphModels/{graph_model_id}/executeQuery?preview=true"
        )

    def _get_token(self) -> str:
        if self._access_token:
            return self._access_token
        try:
            from notebookutils import mssparkutils  # type: ignore[import-untyped]
            return mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
        except ImportError:
            raise RuntimeError(
                "No access_token provided and mssparkutils not available. "
                "Pass access_token explicitly for local testing."
            )

    def execute(self, gql_query: str) -> GQLResult:
        """Execute a GQL query and return parsed results.

        Raises RuntimeError on transport or application errors.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self._get_token()}",
        }
        payload = {"query": gql_query}

        logger.debug("GQL query: %s", gql_query)
        response = requests.post(self._endpoint, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        body = response.json()
        status = body.get("status", {})
        status_code = status.get("code", "99999")

        if not status_code.startswith(("00", "01", "02", "03")):
            description = status.get("description", "Unknown error")
            cause = status.get("cause", {}).get("description", "")
            raise RuntimeError(
                f"GQL query failed [{status_code}]: {description}"
                + (f" — cause: {cause}" if cause else "")
            )

        result_body = body.get("result", {})
        if result_body.get("kind") == "TABLE":
            return GQLResult(
                columns=result_body.get("columns", []),
                data=result_body.get("data", []),
                status_code=status_code,
                status_description=status.get("description", ""),
            )

        return GQLResult(
            status_code=status_code,
            status_description=status.get("description", ""),
        )
