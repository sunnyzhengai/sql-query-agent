"""TMDL source profiles: where semantic-model definitions come from.

Mirrors the SQL extractor's connection profiles (ADR 0040 / handoff
item 2): the PARSING is identical everywhere; only the fetch differs.

  folder     — a directory containing *.SemanticModel folders: a
               git-synced Fabric workspace checkout, an uploaded Files/
               area, or a local clone. No credentials.
  workspace  — the Fabric REST API (list semantic models +
               getDefinition, TMDL format): works on ANY workspace, git
               integration or not. The truly turn-key path; auth is the
               notebook's own AAD token.
  devops_git — Azure DevOps Git repos via DevOpsTmdlClient. The PAT is
               fetched at run time (Key Vault via notebookutils in the
               notebook) and passed in — never stored in config or code.

All produce the same shape: TmdlFile records for the pure
semantic_models_step to parse.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Auto-generated PBI date tables carry no business logic
_SKIP_TABLE_PREFIXES = ("LocalDateTable_", "DateTableTemplate_")


@dataclass
class TmdlFile:
    report_name: str
    table_name: str
    content: str
    repo_name: str = ""
    semantic_model_path: str = ""


def _skip(table_name: str) -> bool:
    return table_name.startswith(_SKIP_TABLE_PREFIXES)


class FolderTmdlSource:
    """Collect TMDL files from a directory tree of *.SemanticModel folders."""

    def __init__(self, root: str) -> None:
        self.root = Path(root)

    def collect(self) -> "list[TmdlFile]":
        files: "list[TmdlFile]" = []
        for tmdl in sorted(self.root.rglob("*.SemanticModel/definition/tables/*.tmdl")):
            table_name = tmdl.stem
            if _skip(table_name):
                continue
            sm_dir = tmdl.parent.parent.parent  # the *.SemanticModel folder
            files.append(TmdlFile(
                report_name=sm_dir.name.removesuffix(".SemanticModel"),
                table_name=table_name,
                content=tmdl.read_text(),
                semantic_model_path=str(sm_dir.relative_to(self.root)),
            ))
        return files


class FabricWorkspaceTmdlSource:
    """Collect TMDL straight from a Fabric workspace via the REST API.

    No git integration, no DevOps, no exports — list the workspace's
    semantic models and ask each for its definition in TMDL format
    (getDefinition). Auto-generated date tables and non-table parts are
    filtered exactly like the other profiles.

    getDefinition is a long-running operation: a 202 response carries a
    Location to poll. The poll budget is bounded — a model that never
    finishes is reported, not waited on forever.
    """

    BASE_URL = "https://api.fabric.microsoft.com/v1"
    POLL_SECONDS = 2
    MAX_POLLS = 30

    def __init__(
        self, workspace_id: str, token_provider: "Callable[[], str]",
        http=None, sleep: "Callable[[float], None]" = time.sleep,
    ) -> None:
        if http is None:
            import requests as http  # noqa: PLC0415 — optional dep, adapter-style
        self._http = http
        self._sleep = sleep
        self.workspace_id = workspace_id
        self._token_provider = token_provider

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token_provider()}"}

    def _get_json(self, url: str) -> dict:
        resp = self._http.get(url, headers=self._headers(), timeout=60)
        resp.raise_for_status()
        return resp.json()

    def list_semantic_models(self) -> "list[dict]":
        url = f"{self.BASE_URL}/workspaces/{self.workspace_id}/semanticModels"
        models: "list[dict]" = []
        while url:
            payload = self._get_json(url)
            models.extend(payload.get("value", []))
            url = payload.get("continuationUri")
        return models

    def get_definition_parts(self, model_id: str) -> "list[dict]":
        """The model's definition parts (path + base64 payload), TMDL format."""
        url = (
            f"{self.BASE_URL}/workspaces/{self.workspace_id}"
            f"/semanticModels/{model_id}/getDefinition?format=TMDL"
        )
        resp = self._http.post(url, headers=self._headers(), timeout=60)
        if resp.status_code == 202:
            location = resp.headers.get("Location", "")
            for _ in range(self.MAX_POLLS):
                self._sleep(self.POLL_SECONDS)
                op = self._http.get(location, headers=self._headers(), timeout=60)
                op.raise_for_status()
                if op.json().get("status") == "Succeeded":
                    result = self._http.get(
                        f"{location}/result", headers=self._headers(), timeout=60)
                    result.raise_for_status()
                    resp = result
                    break
                if op.json().get("status") == "Failed":
                    raise RuntimeError(
                        f"getDefinition failed for semantic model {model_id}")
            else:
                raise RuntimeError(
                    f"getDefinition still running for {model_id} after "
                    f"{self.MAX_POLLS * self.POLL_SECONDS}s — retry later")
        else:
            resp.raise_for_status()
        return resp.json().get("definition", {}).get("parts", [])

    def collect(self) -> "list[TmdlFile]":
        files: "list[TmdlFile]" = []
        for model in self.list_semantic_models():
            report_name = model.get("displayName", "")
            for part in self.get_definition_parts(model["id"]):
                path = part.get("path", "")
                if "definition/tables/" not in path or not path.endswith(".tmdl"):
                    continue
                table_name = path.rsplit("/", 1)[-1].removesuffix(".tmdl")
                if _skip(table_name):
                    continue
                content = base64.b64decode(part.get("payload", "")).decode("utf-8")
                files.append(TmdlFile(
                    report_name=report_name,
                    table_name=table_name,
                    content=content,
                    semantic_model_path=f"workspace:{self.workspace_id}/{model['id']}",
                ))
        return files


def collect_from_workspaces(
    workspace_ids: "list[str]",
    token_provider: "Callable[[], str]",
    current_workspace_id: str = "",
    source_factory=None,
) -> "tuple[list[TmdlFile], dict[str, int]]":
    """Collect TMDL across MULTIPLE workspaces in one pass (2026-08-18:
    reports live across 4-5 workspaces at real customers).

    Returns (all files IN WORKSPACE ORDER, per-workspace file counts).
    Order is load-bearing: file order feeds the metric-naming priority
    rule (earlier workspace's report names a shared metric). One
    combined list -> ONE downstream write — sequential per-workspace
    runs would clobber each other under overwrite semantics.
    """
    if source_factory is None:
        source_factory = lambda ws: FabricWorkspaceTmdlSource(ws, token_provider)  # noqa: E731
    files: "list[TmdlFile]" = []
    counts: "dict[str, int]" = {}
    for ws in workspace_ids:
        ws_id = ws or current_workspace_id
        ws_files = source_factory(ws_id).collect()
        counts[ws_id] = len(ws_files)
        files.extend(ws_files)
    return files, counts


def collect_from_devops(client, repo_name: str) -> "list[TmdlFile]":
    """Collect TMDL files from a DevOps repo via DevOpsTmdlClient."""
    files: "list[TmdlFile]" = []
    for model in client.find_semantic_models(repo_name):
        tables_path = f"{model['path']}/definition/tables"
        for item in client.list_items(repo_name, tables_path):
            path = item.get("path", "")
            if not path.endswith(".tmdl"):
                continue
            table_name = path.rsplit("/", 1)[-1].removesuffix(".tmdl")
            if _skip(table_name):
                continue
            files.append(TmdlFile(
                report_name=model["report_name"],
                table_name=table_name,
                content=client.get_file(repo_name, path),
                repo_name=repo_name,
                semantic_model_path=model["path"],
            ))
    return files
