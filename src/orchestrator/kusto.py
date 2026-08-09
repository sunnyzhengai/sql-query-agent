"""Minimal Kusto REST client for the deterministic core.

Plain HTTPS to the Eventhouse query endpoint (Kusto v2 REST protocol) —
no SDK dependency, no LLM anywhere near it. The bearer token arrives
via an injected provider: az CLI locally, notebookutils in Fabric,
MSAL in a deployed surface. Queries run under the CALLER's identity,
so the ai_embeddings impersonation inside semantic_search charges the
caller's Azure OpenAI role — the no-stored-keys property end to end.
"""

from __future__ import annotations

from typing import Callable

import requests


class KustoClient:
    def __init__(
        self,
        query_uri: str,
        database: str,
        token_provider: "Callable[[], str]",
        timeout: int = 120,
    ) -> None:
        self.query_uri = query_uri.rstrip("/")
        self.database = database
        self._token = token_provider
        self.timeout = timeout

    def run(self, query: str, parameters: "dict | None" = None) -> "list[dict]":
        """Execute one KQL query; return PrimaryResult rows as dicts."""
        body: dict = {"db": self.database, "csl": query}
        if parameters:
            body["properties"] = {"Parameters": parameters}
        resp = requests.post(
            f"{self.query_uri}/v2/rest/query",
            headers={
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=body,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return self._primary_rows(resp.json())

    @staticmethod
    def _primary_rows(frames: "list[dict]") -> "list[dict]":
        """Kusto v2 protocol: find the PrimaryResult table, zip rows."""
        for frame in frames:
            if (
                frame.get("FrameType") == "DataTable"
                and frame.get("TableKind") == "PrimaryResult"
            ):
                cols = [c["ColumnName"] for c in frame["Columns"]]
                return [dict(zip(cols, row)) for row in frame["Rows"]]
        return []


def az_cli_token_provider(resource: str) -> "Callable[[], str]":
    """Dev-machine token provider (az CLI must be logged in)."""
    import subprocess

    def provider() -> str:
        out = subprocess.run(
            ["az", "account", "get-access-token", "--resource", resource,
             "--query", "accessToken", "-o", "tsv"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()

    return provider
