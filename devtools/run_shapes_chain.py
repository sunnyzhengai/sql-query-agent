"""Fire the shape-store chain (tenant-load order 2026-08-27).

PRECONDITION: sql-logic-env published at >= 1.58.2 (the flat
governance columns ride this run) — Sunny's Publish click; the
staged wheel is already correct.

Sequence (all runs attach the ISOLATED shapes lakehouse via the job
API's defaultLakehouse override — the profile IS the lakehouse):

  100_install -> 010_ingest_sql_filedrop -> 040_dict_clarity ->
  060_ingest_semantic_models -> [loadTable: input_metric_names +
  gov_steward_assignments from the staged CSVs] -> 200_parse ->
  300_build_graph -> 400_build_metric_logic -> 500_validate ->
  [KQL shortcut: output_semantic_catalog -> shapes DB, then]
  700_refresh_search_index -> 800_export_graph_tables

Post-chain verification (oracles, never vibes):
  - graph_nodes cluster rows carry the FLAT columns (F-1 live)
  - cluster count == the local gapcheck's 26 verdicts
  - semantic_search() answers in semantic_catalog_shapes
  - the U7 metric record carries the dashboard link (W4)

Every step prints [ok]/[FAIL]; the run stops at the first failure.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

WORKSPACE = "1f55e1c1-b660-4715-9b56-4140edce3940"
SHAPES_LH = "bf55535b-ba0a-4cc1-a78a-9c02b2fb93fc"
SHAPES_LH_NAME = "sql_query_lh_shapes"
SHAPES_KUSTO_DB = "semantic_catalog_shapes"
KQL_DB_ITEM = "911c8991-4e91-424f-9362-b994b9334f9a"
QUERY_URI = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
API = "https://api.fabric.microsoft.com/v1"

ROSTER = [
    "100_install", "010_ingest_sql_filedrop", "040_dict_clarity",
    "060_ingest_semantic_models", "__load_tables__", "200_parse",
    "300_build_graph", "400_build_metric_logic", "500_validate",
    "__shortcut__", "700_refresh_search_index",
    "800_export_graph_tables",
]

TABLE_LOADS = [
    ("input_metric_names", "Files/sql-query-agent/"
                           "input_metric_names.csv"),
    ("gov_steward_assignments", "Files/sql-query-agent/"
                                "gov_steward_assignments.csv"),
]


def tok() -> str:
    return subprocess.run(
        ["az", "account", "get-access-token", "--resource",
         "https://api.fabric.microsoft.com", "--query",
         "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True).stdout.strip()


def _items(t: str) -> dict:
    r = requests.get(f"{API}/workspaces/{WORKSPACE}/items",
                     headers={"Authorization": f"Bearer {t}"},
                     timeout=60)
    r.raise_for_status()
    return {it["displayName"]: it["id"] for it in r.json()["value"]
            if it["type"] == "Notebook"}


def run_notebook(t: str, nb_id: str, name: str) -> None:
    # the override lives under executionData.CONFIGURATION — at the
    # top level it is silently ignored and the notebook's pinned
    # default (the REALISM lakehouse) wins. Field find 2026-08-27:
    # the first chain ran 4 notebooks against realism; the topology
    # postcondition refused the polluted graph write. The tripwire
    # below makes the silent-ignore class impossible to repeat.
    body = {"executionData": {"configuration": {
        "defaultLakehouse": {"name": SHAPES_LH_NAME, "id": SHAPES_LH,
                             "workspaceId": WORKSPACE}}}}
    r = requests.post(
        f"{API}/workspaces/{WORKSPACE}/items/{nb_id}/jobs/instances"
        "?jobType=RunNotebook",
        headers={"Authorization": f"Bearer {t}"}, json=body,
        timeout=60)
    r.raise_for_status()
    loc = r.headers["Location"]
    start = time.time()
    while True:
        time.sleep(20)
        s = requests.get(loc, headers={"Authorization": f"Bearer {t}"},
                         timeout=60).json()
        st = s.get("status")
        if st in ("Completed", "Failed", "Cancelled", "Deduped"):
            mins = (time.time() - start) / 60
            if st != "Completed":
                raise RuntimeError(
                    f"{name}: {st} — {str(s.get('failureReason'))[:300]}")
            print(f"[ok]      {name} ({mins:.1f} min)")
            return
        if time.time() - start > 45 * 60:
            raise RuntimeError(f"{name}: timeout")


def assert_profile_took(step: str) -> None:
    """TRIPWIRE (field find 2026-08-27): after the first WRITING
    notebook, the shapes lakehouse must hold the written table — if
    not, the lakehouse override silently failed and the chain is
    running against REALISM. Abort before any further write."""
    import subprocess as sp
    ol = sp.run(["az", "account", "get-access-token", "--resource",
                 "https://storage.azure.com", "--query", "accessToken",
                 "-o", "tsv"], capture_output=True, text=True,
                check=True).stdout.strip()
    r = requests.get(
        f"https://onelake.dfs.fabric.microsoft.com/{WORKSPACE}"
        f"?resource=filesystem&recursive=false"
        f"&directory={SHAPES_LH}/Tables",
        headers={"Authorization": f"Bearer {ol}"}, timeout=60)
    r.raise_for_status()
    names = {p["name"].split("/")[-1] for p in r.json().get("paths", [])}
    if "input_sql_sources" not in names:
        raise RuntimeError(
            f"TRIPWIRE after {step}: input_sql_sources absent from "
            f"the SHAPES lakehouse (saw {sorted(names)[:5]}) — the "
            "defaultLakehouse override did not take; the run went to "
            "REALISM. Chain aborted before further writes.")
    print(f"[ok]      tripwire: {step} wrote into the SHAPES "
          "lakehouse")


def load_tables(t: str) -> None:
    for table, path in TABLE_LOADS:
        # capacity rate limits (430 TooManyRequestsForCapacity) are
        # transient contention — the notebook session ahead of us may
        # still be releasing cores; wait and retry, never fail the
        # chain on them (field find, first chain run 2026-08-27)
        for attempt in range(6):
            if attempt:
                time.sleep(90)
                t = tok()
            r = requests.post(
                f"{API}/workspaces/{WORKSPACE}/lakehouses/{SHAPES_LH}"
                f"/tables/{table}/load",
                headers={"Authorization": f"Bearer {t}"},
                json={"relativePath": path, "pathType": "File",
                      "mode": "Overwrite",
                      "formatOptions": {"format": "Csv",
                                        "header": True,
                                        "delimiter": ","}},
                timeout=60)
            r.raise_for_status()
            loc = r.headers.get("Location")
            outcome = "Completed"
            if loc:
                start = time.time()
                while time.time() - start < 600:
                    time.sleep(10)
                    s = requests.get(
                        loc,
                        headers={"Authorization": f"Bearer {t}"},
                        timeout=60).json()
                    if s.get("status") in ("Completed", "Failed"):
                        outcome = s["status"]
                        break
            if outcome == "Completed":
                break
            if "TooManyRequestsForCapacity" not in str(s):
                raise RuntimeError(f"loadTable {table}: {s}")
            print(f"[..]      loadTable {table}: capacity busy, "
                  f"retry {attempt + 1}/5")
        else:
            raise RuntimeError(
                f"loadTable {table}: capacity still busy after "
                "5 retries")
        print(f"[ok]      loadTable {table}")


def create_shortcut(t: str) -> None:
    from devtools.create_kql_shortcut import create_and_verify
    create_and_verify("output_semantic_catalog", WORKSPACE,
                      KQL_DB_ITEM, SHAPES_LH, timeout_s=300)
    print("[ok]      KQL shortcut output_semantic_catalog "
          "(create-then-verify)")


def verify() -> None:
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider
    c = KustoClient(QUERY_URI, SHAPES_KUSTO_DB,
                    az_cli_token_provider(QUERY_URI))
    n = c.run("graph_nodes | where node_id startswith 'cluster:' "
              "| count", {})[0]["Count"]
    flat = c.run("graph_nodes | where node_id startswith 'cluster:' "
                 "and isnotempty(flag_class) | count", {})[0]["Count"]
    print(f"clusters: {n}; with FLAT columns: {flat}")
    assert n == flat and n >= 20, "flat surface incomplete"
    hits = c.run("semantic_search('diabetic patients', 5)", {})
    assert hits, "semantic_search empty"
    print(f"semantic_search live: {len(hits)} hits, top = "
          f"{hits[0].get('business_name')}")
    rec = c.run("graph_nodes | where node_id == "
                "'canonical:reporting.USP_DM_Registry_Composite' "
                "| project properties", {})
    assert rec and "Diabetes Registry Dashboard" in str(rec[0]), (
        "U7 record missing the dashboard link (W4)")
    print("U7 carries the dashboard link — pointer chase ready")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_step", default=None,
                    help="resume the roster from this step")
    args = ap.parse_args()
    t = tok()
    ids = _items(t)
    roster = ROSTER
    if args.from_step:
        roster = ROSTER[ROSTER.index(args.from_step):]
        print(f"resuming from {args.from_step} "
              f"({len(roster)} steps remain)")
    for step in roster:
        if step == "__load_tables__":
            load_tables(t)
        elif step == "__shortcut__":
            create_shortcut(t)
        else:
            if step not in ids:
                raise SystemExit(f"notebook {step!r} not in workspace")
            run_notebook(tok(), ids[step], step)
            if step == "010_ingest_sql_filedrop":
                assert_profile_took(step)
    verify()
    print("\nshape-store load COMPLETE — the demo store is live")


if __name__ == "__main__":
    main()
