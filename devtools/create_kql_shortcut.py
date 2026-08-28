"""Create a OneLake shortcut in a KQL database — create-then-VERIFY.

Ops find 1 (2026-08-24, the gov_red_flags ghost): the shortcut API
201'd and REGISTERED the name (the list showed it; a UI create then
failed on name-conflict) but the shortcut never MOUNTED — the table
stayed invisible and unqueryable. The 201 vouches for phase one of a
two-phase operation; the registration list lies.

The mechanism: create, then poll the QUERY path (`<table> | count`)
until green, or DELETE THE GHOST and fail loud with the remediation.
Any future automation that creates KQL shortcuts goes through this
script, never a bare POST.

Usage:
    python3.11 devtools/create_kql_shortcut.py <table_name>
        [--workspace WS] [--kqldb ITEM] [--lakehouse ITEM]
        [--timeout-s 300]
Defaults target the AIVIA-DEV-2 semantic-catalog stack.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.answer_evals import DATABASE, QUERY_URI  # noqa: E402
from src.orchestrator.kusto import KustoClient, az_cli_token_provider  # noqa: E402

FABRIC = "https://api.fabric.microsoft.com/v1"
DEFAULT_WS = "1f55e1c1-b660-4715-9b56-4140edce3940"
DEFAULT_KQLDB = "718853ec-f07d-4960-a780-93215fb67189"
DEFAULT_LAKEHOUSE = "f7c297eb-4659-4600-ab89-0e860638fb6c"


def _token() -> str:
    out = subprocess.run(
        ["az", "account", "get-access-token", "--resource",
         "https://api.fabric.microsoft.com", "--query", "accessToken",
         "-o", "tsv"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _api(method: str, url: str, body: "dict | None" = None) -> int:
    req = urllib.request.Request(
        url, method=method,
        headers={"Authorization": f"Bearer {_token()}",
                 "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def create_and_verify(table: str, ws: str, kqldb: str, lakehouse: str,
                      timeout_s: int = 300,
                      target_path: "str | None" = None,
                      verify_db: "str | None" = None) -> None:
    """target_path: the OneLake path of the Delta table —
    Tables/dbo/<t> on schema-enabled lakehouses (the realism
    default), Tables/<t> on plain ones (the shapes store).
    verify_db: the KQL database the mount is verified in."""
    url = f"{FABRIC}/workspaces/{ws}/items/{kqldb}/shortcuts"
    status = _api("POST", url, {
        "name": table, "path": "/Tables",
        "target": {"oneLake": {"workspaceId": ws, "itemId": lakehouse,
                               "path": target_path or
                               f"Tables/dbo/{table}"}}})
    if status not in (200, 201):
        raise SystemExit(f"[X] shortcut create failed (HTTP {status}) "
                         f"for {table!r}")
    print(f"[.] created (HTTP {status}) — now VERIFYING the query path "
          "(the 201 alone proves registration, not mounting)")
    client = KustoClient(QUERY_URI, verify_db or DATABASE,
                         az_cli_token_provider(QUERY_URI))
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            n = client.run(f"{table} | count", {})[0].get("Count")
            print(f"[+] MOUNTED and queryable: {table} -> {n} row(s)")
            return
        except Exception:               # noqa: BLE001 — still mounting
            time.sleep(15)
    # ghost: registered but never mounted — remove it so a retry
    # (API or UI) doesn't die on name-conflict, then fail LOUD
    del_status = _api(
        "DELETE", f"{url}/Tables/{table}")
    raise SystemExit(
        f"[X] GHOST SHORTCUT: {table!r} registered but never became "
        f"queryable within {timeout_s}s. Ghost delete: HTTP "
        f"{del_status}. Remediation: retry (this script or the KQL "
        "database UI: New -> OneLake shortcut); if it recurs, check "
        "the Delta table exists at "
        f"Tables/dbo/{table} in the Lakehouse.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("--workspace", default=DEFAULT_WS)
    ap.add_argument("--kqldb", default=DEFAULT_KQLDB)
    ap.add_argument("--lakehouse", default=DEFAULT_LAKEHOUSE)
    ap.add_argument("--timeout-s", type=int, default=300)
    args = ap.parse_args()
    create_and_verify(args.table, args.workspace, args.kqldb,
                      args.lakehouse, args.timeout_s)


if __name__ == "__main__":
    main()
