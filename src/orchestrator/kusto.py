"""Minimal Kusto REST client for the deterministic core.

Plain HTTPS to the Eventhouse query endpoint (Kusto v2 REST protocol) —
no SDK dependency, no LLM anywhere near it. The bearer token arrives
via an injected provider: az CLI locally, notebookutils in Fabric,
MSAL in a deployed surface. Queries run under the CALLER's identity,
so the ai_embeddings impersonation inside semantic_search charges the
caller's Azure OpenAI role — the no-stored-keys property end to end.
"""

from __future__ import annotations

import json
import time
from typing import Callable

import requests


class KustoQueryError(RuntimeError):
    """The query failed (fully or MID-STREAM). Raised so partial data can
    never masquerade as an answer — the v2 protocol reports mid-stream
    failures as an error OBJECT appended to Rows, which a naive zip turns
    into a fake row (live find 2026-08-10: node_id='OneApiErrors')."""


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
        # RW-BATCH-6: keep-alive — a fresh TLS handshake per query
        # added ~0.2-0.5s to every one of an op's many round trips.
        # urllib3's pool underneath is thread-safe; we set no cookies.
        self._session = requests.Session()

    def run(self, query: str, parameters: "dict | None" = None) -> "list[dict]":
        """Execute one KQL query; return PrimaryResult rows as dicts.

        Transient transport failures (SSL EOF / connection reset — the
        cold-connection signature of a resuming or resizing capacity,
        field find 2026-08-20) are retried twice with backoff; a
        persistent failure still raises."""
        body: dict = {"db": self.database, "csl": query}
        if parameters:
            body["properties"] = {"Parameters": parameters}
        last_err: "Exception | None" = None
        for attempt in range(3):
            if attempt:
                time.sleep(2 * attempt)
            try:
                resp = self._session.post(
                    f"{self.query_uri}/v2/rest/query",
                    headers={
                        "Authorization": f"Bearer {self._token()}",
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    json=body,
                    timeout=self.timeout,
                )
            except (requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as err:
                last_err = err
                continue
            resp.raise_for_status()
            return self._primary_rows(resp.json())
        raise last_err  # type: ignore[misc]

    def mgmt(self, command: str) -> "list[dict]":
        """Execute one management (dot) command; return first-table rows.

        Dot commands (.set-or-replace, .drop, ...) are rejected by the
        query endpoint — they run on /v1/rest/mgmt, whose response is
        the v1 shape ({"Tables": [...]}), not the v2 frame stream."""
        resp = requests.post(
            f"{self.query_uri}/v1/rest/mgmt",
            headers={
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"db": self.database, "csl": command},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        tables = resp.json().get("Tables") or []
        if not tables:
            return []
        cols = [c["ColumnName"] for c in tables[0]["Columns"]]
        return [dict(zip(cols, row)) for row in tables[0]["Rows"]]

    @staticmethod
    def _primary_rows(frames: "list[dict]") -> "list[dict]":
        """Kusto v2 protocol: find the PrimaryResult table, zip rows.
        Any error — top-level frame, dataset-completion errors, or an
        error object inside Rows — RAISES; partial data is never
        returned as if complete."""
        for frame in frames:
            if frame.get("FrameType") == "DataSetCompletion" and frame.get(
                    "HasErrors"):
                raise KustoQueryError(
                    "query completed with errors: "
                    f"{json.dumps(frame.get('OneApiErrors'))[:400]}")
        for frame in frames:
            if (
                frame.get("FrameType") == "DataTable"
                and frame.get("TableKind") == "PrimaryResult"
            ):
                cols = [c["ColumnName"] for c in frame["Columns"]]
                rows = []
                for row in frame["Rows"]:
                    if isinstance(row, dict):   # mid-stream error object
                        raise KustoQueryError(
                            "query failed mid-stream: "
                            f"{json.dumps(row)[:400]}")
                    rows.append(dict(zip(cols, row)))
                return rows
        return []


def az_cli_token_provider(resource: str) -> "Callable[[], str]":
    """Dev-machine token provider (az CLI must be logged in).

    RW-BATCH-6 (E-battery, 2026-08-29): the provider used to shell
    out to `az` on EVERY query (~0.4-2s each) — and CONCURRENT az
    subprocesses serialize on the CLI's token-cache file lock, which
    is exactly why the parallel grounding showed no overlap live
    (B2: 3 entities = 152s). The token now caches IN PROCESS for 40
    minutes (AAD tokens live ~60-75); refresh takes a lock so the
    subprocess runs once, not once per thread."""
    import subprocess
    import threading
    import time as _t

    state = {"token": "", "expires": 0.0}
    lock = threading.Lock()

    def provider() -> str:
        now = _t.monotonic()
        if state["token"] and now < state["expires"]:
            return state["token"]
        with lock:
            if state["token"] and _t.monotonic() < state["expires"]:
                return state["token"]
            out = subprocess.run(
                ["az", "account", "get-access-token", "--resource",
                 resource, "--query", "accessToken", "-o", "tsv"],
                capture_output=True, text=True, check=True,
            )
            state["token"] = out.stdout.strip()
            state["expires"] = _t.monotonic() + 40 * 60
            return state["token"]

    return provider
