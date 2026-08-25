"""org_config referential integrity — every tenant-artifact id the
config names must resolve against the LIVE tenant.

Ops find 2 (2026-08-24, the 610 corpse): the tenant org_config's
fabric_graph.data_agent_id pointed at the Delta Agent retired two
days earlier; the pipeline burned 45 minutes before dying inside 610
with a cancelled Spark session. A dead reference must fail loud, with
its error contract, BEFORE any chain fires.

Checks (each failure names the config key, the dead id, and the fix):
- fabric_graph.workspace_id     -> workspace exists
- fabric_graph.data_agent_id    -> DataAgent item exists in that workspace
- fabric_graph.graph_model_id   -> item exists (warn-only: no reader yet)
- search.kusto_uri + kusto_db   -> store answers `semantic_catalog | count`

Audits the LOCAL org_config.yaml by default; --tenant audits the
Lakehouse copy (the one notebooks read — the copy that failed).

Usage:
    python3.11 devtools/org_config_audit.py [--tenant]
Exit 0 = every reference resolves; exit 1 = dead reference(s), each
printed with its remediation. Run before firing any notebook chain.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

FABRIC = "https://api.fabric.microsoft.com/v1"
LAKEHOUSE_CONFIG_URL = (
    "https://onelake.dfs.fabric.microsoft.com/"
    "1f55e1c1-b660-4715-9b56-4140edce3940/"
    "f7c297eb-4659-4600-ab89-0e860638fb6c/Files/sql-query-agent/"
    "org_config.yaml")


def _token(resource: str) -> str:
    out = subprocess.run(
        ["az", "account", "get-access-token", "--resource", resource,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _get(url: str, resource: str) -> "tuple[int, dict]":
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {_token(resource)}"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {}


def collect_refs(cfg: dict) -> "list[dict]":
    """The audited references: (key, id, kind, severity). Pure —
    L0-tested; severity 'fail' breaks the audit, 'warn' prints."""
    fg = cfg.get("fabric_graph") or {}
    refs = []
    if fg.get("workspace_id"):
        refs.append({"key": "fabric_graph.workspace_id",
                     "id": str(fg["workspace_id"]),
                     "kind": "workspace", "severity": "fail"})
    if fg.get("data_agent_id"):
        refs.append({"key": "fabric_graph.data_agent_id",
                     "id": str(fg["data_agent_id"]),
                     "kind": "item", "severity": "fail",
                     "remedy": ("repoint to the CURRENT production "
                                "agent — retirement runbook step 7.0; "
                                "610_generate_agent_descriptions dies "
                                "on a dead agent")})
    if fg.get("graph_model_id"):
        refs.append({"key": "fabric_graph.graph_model_id",
                     "id": str(fg["graph_model_id"]),
                     "kind": "item", "severity": "warn"})
    return refs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant", action="store_true",
                    help="audit the Lakehouse copy notebooks read")
    args = ap.parse_args()

    import yaml
    if args.tenant:
        req = urllib.request.Request(LAKEHOUSE_CONFIG_URL, headers={
            "Authorization":
                f"Bearer {_token('https://storage.azure.com')}"})
        with urllib.request.urlopen(req) as r:
            cfg = yaml.safe_load(r.read().decode())
        where = "TENANT (Lakehouse Files/sql-query-agent)"
    else:
        cfg = yaml.safe_load(
            (PROJECT_ROOT / "org_config.yaml").read_text())
        where = "LOCAL (repo root)"
    print(f"auditing {where} org_config.yaml")

    failures: "list[str]" = []
    fg = cfg.get("fabric_graph") or {}
    ws = str(fg.get("workspace_id") or "")
    for ref in collect_refs(cfg):
        if ref["kind"] == "workspace":
            status, _ = _get(f"{FABRIC}/workspaces/{ref['id']}",
                             "https://api.fabric.microsoft.com")
        else:
            status, _ = _get(
                f"{FABRIC}/workspaces/{ws}/items/{ref['id']}",
                "https://api.fabric.microsoft.com")
        ok = status == 200
        mark = "ok " if ok else ("WARN" if ref["severity"] == "warn"
                                 else "DEAD")
        print(f"[{mark}] {ref['key']} = {ref['id']} (HTTP {status})")
        if not ok and ref["severity"] == "fail":
            failures.append(
                f"{ref['key']} -> {ref['id']} does not resolve "
                f"(HTTP {status}). "
                + ref.get("remedy", "repoint to a live artifact."))

    search = cfg.get("search") or {}
    uri, db = search.get("kusto_uri"), search.get("kusto_db")
    if uri and db:
        try:
            from src.orchestrator.kusto import (
                KustoClient,
                az_cli_token_provider,
            )
            n = KustoClient(str(uri), str(db),
                            az_cli_token_provider(str(uri))).run(
                "semantic_catalog | count", {})[0].get("Count")
            print(f"[ok ] search.kusto_uri/kusto_db -> "
                  f"semantic_catalog {n} row(s)")
        except Exception as e:              # noqa: BLE001 — audited
            failures.append(
                f"search.kusto_uri/kusto_db -> store unreachable "
                f"({type(e).__name__}). Wrong DB name after a rename, "
                "paused capacity, or a broken shortcut.")
            print(f"[DEAD] search store: {type(e).__name__}")

    if failures:
        print(f"\n[X] org_config audit: {len(failures)} dead "
              "reference(s) — fix BEFORE firing any chain:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("\norg_config audit: every reference resolves")


if __name__ == "__main__":
    main()
