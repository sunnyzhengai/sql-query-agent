"""Push the graph export to Fabric and verify — the M-batch loader
(born 2026-09-09: Sunny: "i have a hard time loading and testing
these tables. can you do it").

Does the whole per-batch cycle headlessly:
  1. write the export tables as DELTA straight into the lakehouse's
     Tables/ area over OneLake (no Files upload, no Load-to-Tables,
     no CSV parsing layer — the missing-86 corpse stays dead)
  2. trigger the graph model refresh (Fabric item job)
  3. wait for the refresh, then run the gate queries and DIFF the
     answers against the export truth — the same equalities the
     shape census pins locally, now verified on the served graph

Auth: az CLI login (founder tenant). Capacity 429s are retried
with backoff — trial capacities throttle after heavy refreshes.

Usage: python3.11 scripts/fabric_graph_push.py [estate] [--verify-only]
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

WORKSPACE_ID = "1f55e1c1-b660-4715-9b56-4140edce3940"   # AIVIA-DEV-2
GRAPH_MODEL_ID = "176d0b87-9874-48ca-a19e-41a97697f053"  # AIVIA_GRAPH
WORKSPACE_NAME = "AIVIA-DEV-2"
LAKEHOUSE_NAME = "AIVIA_GRAPH"
FABRIC = "https://api.fabric.microsoft.com/v1"


def az_token(resource: str) -> str:
    return subprocess.run(
        ["az", "account", "get-access-token", "--resource", resource,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True).stdout.strip()


def fabric_call(token, method, path, payload=None, retries=8):
    url = FABRIC + path
    for attempt in range(retries):
        req = urllib.request.Request(
            url, method=method,
            data=json.dumps(payload).encode() if payload else None,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read()
                return r.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 429 and attempt < retries - 1:
                wait = min(600, 60 * (attempt + 1))
                print(f"  capacity 429 — backing off {wait}s "
                      f"(attempt {attempt + 1}/{retries})")
                time.sleep(wait)
                continue
            return e.code, {"error": body[:500]}
    return 0, {}


def push_tables(estate: str) -> None:
    import pyarrow.parquet as pq
    from deltalake import write_deltalake
    storage_token = az_token("https://storage.azure.com")
    base = (pathlib.Path(__file__).resolve().parents[1]
            / "AIVIA_Product" / "estates" / estate / "graph_export")
    files = sorted(base.glob("*.parquet"))
    assert files, f"no export at {base} — run the export first"
    for f in files:
        table = pq.read_table(f)
        dest = (f"abfss://{WORKSPACE_NAME}@onelake.dfs.fabric."
                f"microsoft.com/{LAKEHOUSE_NAME}.Lakehouse/Tables/"
                f"{f.stem}")
        write_deltalake(
            dest, table, mode="overwrite",
            schema_mode="overwrite",
            storage_options={"bearer_token": storage_token,
                             "use_fabric_endpoint": "true"})
        print(f"  pushed {f.stem:<36} {table.num_rows:>6} rows")


def refresh_graph(token) -> None:
    # the graph model materializes via an on-demand item job
    status, body = fabric_call(
        token, "POST",
        f"/workspaces/{WORKSPACE_ID}/items/{GRAPH_MODEL_ID}"
        f"/jobs/instances?jobType=Refresh", payload={})
    print(f"  refresh trigger: HTTP {status} "
          f"{json.dumps(body)[:200] if body else ''}")


def gql(token, query):
    status, body = fabric_call(
        token, "POST",
        f"/workspaces/{WORKSPACE_ID}/GraphModels/{GRAPH_MODEL_ID}"
        f"/executeQuery?preview=true", payload={"query": query})
    if status != 200:
        return None, body
    return body.get("data", []), body.get("status")


def verify(estate: str, token) -> bool:
    import pyarrow.parquet as pq
    base = (pathlib.Path(__file__).resolve().parents[1]
            / "AIVIA_Product" / "estates" / estate / "graph_export")
    truth_nodes, truth_edges = {}, 0
    for f in sorted(base.glob("*.parquet")):
        n = pq.read_metadata(f).num_rows
        if f.stem.startswith("graph_has_part"):
            truth_edges += n
        else:
            truth_nodes[f.stem.removeprefix("graph_")] = n

    ok = True
    for attempt in range(20):
        data, st = gql(token, "MATCH (n) RETURN labels(n) AS "
                              "nodeType, count(*) AS cnt "
                              "GROUP BY nodeType")
        if data is None and "GraphNotQueryable" in json.dumps(st):
            print(f"  graph not queryable yet — waiting 60s "
                  f"({attempt + 1}/20)")
            time.sleep(60)
            continue
        break
    if data is None:
        print("  Q1 FAILED:", json.dumps(st)[:300])
        return False
    got = {}
    for row in data:
        vals = list(row.values()) if isinstance(row, dict) else row
        got[str(vals[0]).strip("[]'\" ")] = int(vals[1])
    for label, n in sorted(truth_nodes.items()):
        g = got.pop(label, 0)
        mark = "OK " if g == n else "MISMATCH"
        if g != n:
            ok = False
        print(f"  Q1 {label:<12} graph {g:>5}  truth {n:>5}  {mark}")
    for label, g in got.items():
        ok = False
        print(f"  Q1 UNDECLARED label in graph: {label} ({g})")

    data, st = gql(token, "MATCH ()-[c:has_part]->() "
                          "RETURN count(c) AS cnt")
    if data is None:
        print("  Q3 FAILED:", json.dumps(st)[:300])
        return False
    g = int(list(data[0].values())[0] if isinstance(data[0], dict)
            else data[0][0])
    mark = "OK " if g == truth_edges else "MISMATCH"
    if g != truth_edges:
        ok = False
    print(f"  Q3 has_part     graph {g:>5}  truth {truth_edges:>5}  {mark}")

    data, _ = gql(token, "MATCH (c:column WHERE c.name = "
                         "'WRONG_MED_ALT_CNT') RETURN "
                         "c.description AS descr")
    corpse = (data and '"NDC Not Part of Order"' in
              json.dumps(data[0]))
    print(f"  corpse row quotes intact: {bool(corpse)}")
    ok = ok and bool(corpse)
    return ok


def main() -> None:
    estate = next((a for a in sys.argv[1:] if not a.startswith("-")),
                  "sepsis")
    fabric_token = az_token("https://api.fabric.microsoft.com")
    if "--verify-only" not in sys.argv:
        print("PUSH: delta tables over OneLake")
        push_tables(estate)
        print("REFRESH: graph model")
        refresh_graph(fabric_token)
    print("VERIFY: the gate, served graph vs export truth")
    ok = verify(estate, fabric_token)
    print("RESULT:", "GATE GREEN" if ok else "GATE RED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
