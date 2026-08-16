"""TMDL source profiles: where semantic-model definitions come from.

Mirrors the SQL extractor's connection profiles (ADR 0040 / handoff
item 2): the PARSING is identical everywhere; only the fetch differs.

  folder     — a directory containing *.SemanticModel folders: a
               git-synced Fabric workspace checkout, an uploaded Files/
               area, or a local clone. No credentials. This is the
               Fabric-native path.
  devops_git — Azure DevOps Git repos via DevOpsTmdlClient. The PAT is
               fetched at run time (Key Vault via notebookutils in the
               notebook) and passed in — never stored in config or code.

Both produce the same shape: TmdlFile records for the pure
semantic_models_step to parse.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
