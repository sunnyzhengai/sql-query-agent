"""Publish a Fabric Environment via REST and surface the REAL error.

The portal's Publish button reports failures as a bare
"PbiApiError: Failed to publish environment"; the REST API returns the
actual error code/message and the publish state machine. Run this locally
to trigger a publish and watch it, e.g.:

    python devtools/publish_environment.py \
        --workspace 1f55e1c1-b660-4715-9b56-4140edce3940 \
        --environment a0bd174b-f5c7-47e6-838d-14510776fc8d

Auth: uses `az account get-access-token` (Azure CLI logged into the
tenant) unless --token / FABRIC_TOKEN is provided. From a Fabric notebook
instead, the same calls work with:
    token = notebookutils.credentials.getToken('pbi')

Read-only unless --publish is passed: by default it prints the
environment's current publish state and the staged library changes, which
is usually enough to see what the portal is choking on.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import requests

API = "https://api.fabric.microsoft.com/v1"


def get_token(cli_arg: "str | None") -> str:
    token = cli_arg or os.environ.get("FABRIC_TOKEN")
    if token:
        return token
    result = subprocess.run(
        ["az", "account", "get-access-token",
         "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"az token failed ({result.stderr.strip()}); "
                 "pass --token or set FABRIC_TOKEN")
    return result.stdout.strip()


def show(label: str, response: requests.Response) -> "dict | None":
    print(f"\n=== {label} [{response.status_code}] ===")
    try:
        body = response.json()
    except ValueError:
        print(response.text[:2000] or "(empty body)")
        return None
    print(json.dumps(body, indent=2)[:4000])
    return body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--environment", required=True)
    ap.add_argument("--token")
    ap.add_argument("--publish", action="store_true",
                    help="trigger a publish (default: just inspect state)")
    args = ap.parse_args()

    headers = {"Authorization": f"Bearer {get_token(args.token)}"}
    base = f"{API}/workspaces/{args.workspace}/environments/{args.environment}"

    env = show("Environment (current publish state)",
               requests.get(base, headers=headers, timeout=30))
    show("Staged library changes",
         requests.get(f"{base}/staging/libraries", headers=headers, timeout=30))

    if not args.publish:
        print("\n(read-only pass — add --publish to trigger a publish)")
        return

    body = show("POST staging/publish",
                requests.post(f"{base}/staging/publish", headers=headers, timeout=60))
    if body is None:
        return

    # Poll until the publish state machine leaves 'running'
    for _ in range(60):
        time.sleep(15)
        r = requests.get(base, headers=headers, timeout=30)
        details = (r.json().get("properties", {}) or {}).get("publishDetails", {})
        state = details.get("state", "unknown")
        print(f"  publish state: {state}")
        if state.lower() not in ("running", "waiting", "unknown"):
            print(json.dumps(details, indent=2))
            break
    else:
        print("still running after 15 min — check the portal")

    if env is not None:
        print("\nDone. Compare against the pre-publish state above.")


if __name__ == "__main__":
    main()
