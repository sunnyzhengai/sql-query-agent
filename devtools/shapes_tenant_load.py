"""Shape-store tenant load — asset staging + uploads (ordered
2026-08-27; design record in HANDOFF_0055_BUILD: the profile IS the
lakehouse).

Stages every input the chain needs into the ISOLATED shapes
lakehouse (`sql_query_lh_shapes`), then the chain runs with
defaultLakehouse overridden per run:

  Files/sql-query-agent/org_config.yaml   tenant realism config +
      targeted edits (search db -> the shapes catalog DB;
      semantic_models -> folder source holding ONLY the Diabetes
      Registry Dashboard TMDL — sepsis stays out of the demo store,
      isolation in BOTH directions)
  Files/sql-query-agent/libs/...ScriptDom.dll   copied from the
      realism lakehouse (same OneLake, server-side read)
  Files/sql-query-agent/sql_input/*.sql   the 38 corpus procs,
      schema-prefixed on basename collision (reports__X.sql)
  Files/sql-query-agent/dictionary/dict_{tables,columns}.csv
  Files/sql-query-agent/input_metric_names.csv   palette names +
      the dashboard's report link (URL resolved from the live
      workspace items)
  Files/sql-query-agent/gov_steward_assignments.csv   personas
  Files/sql-query-agent/semantic_models/...   the dashboard TMDL
      (git version — placeholder parameters only, endpoint-hygiene)

Tokens come from `az account get-access-token` (Fabric API +
OneLake). Every step prints [ok]/[BLOCKED] — a blocked step becomes
a runbook line, never a silent gap.
"""

from __future__ import annotations

import csv
import io
import subprocess
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.shapes.generator import (  # noqa: E402
    dict_rows,
    load_palette,
    metric_name_rows,
    steward_rows,
)

WORKSPACE = "1f55e1c1-b660-4715-9b56-4140edce3940"
REALISM_LH = "f7c297eb-4659-4600-ab89-0e860638fb6c"
SHAPES_LH = "bf55535b-ba0a-4cc1-a78a-9c02b2fb93fc"
SHAPES_KUSTO_DB = "semantic_catalog_shapes"
# the isolated demo source (source leg, field find 2026-08-27);
# the catalog NAME is config data, the server host stays tenant-side
SHAPES_SRC_DB = "aivia_shapes_src-b5f4544d-731d-43fb-966b-be4a300054d0"
API = "https://api.fabric.microsoft.com/v1"
ONELAKE = "https://onelake.dfs.fabric.microsoft.com"
DASHBOARD = "Diabetes Registry Dashboard"


def _token(resource: str) -> str:
    return subprocess.run(
        ["az", "account", "get-access-token", "--resource", resource,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True).stdout.strip()


def ol_read(tok: str, item: str, path: str) -> bytes:
    r = requests.get(f"{ONELAKE}/{WORKSPACE}/{item}/{path}",
                     headers={"Authorization": f"Bearer {tok}"},
                     timeout=120)
    r.raise_for_status()
    return r.content


def ol_write(tok: str, item: str, path: str, data: bytes) -> None:
    base = f"{ONELAKE}/{WORKSPACE}/{item}/{path}"
    h = {"Authorization": f"Bearer {tok}"}
    r = requests.put(f"{base}?resource=file", headers=h, timeout=60)
    r.raise_for_status()
    r = requests.patch(f"{base}?action=append&position=0", data=data,
                       headers={**h, "Content-Type":
                                "application/octet-stream"},
                       timeout=300)
    r.raise_for_status()
    r = requests.patch(
        f"{base}?action=flush&position={len(data)}",
        headers={**h, "Content-Length": "0"}, timeout=60)
    r.raise_for_status()
    # boundary echo contract: the flush 200 is a CLAIM — the
    # read-back length is the FACT (a 202-append + failed flush once
    # left a file untouched while looking half-done)
    back = requests.get(base, headers=h, timeout=120)
    back.raise_for_status()
    if len(back.content) != len(data):
        raise RuntimeError(
            f"ol_write postcondition failed: {path} read back "
            f"{len(back.content)} bytes, wrote {len(data)}")


def _csv_bytes(rows: "list[dict]") -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode()


def dashboard_report_url(fabric_tok: str) -> str:
    r = requests.get(f"{API}/workspaces/{WORKSPACE}/items",
                     headers={"Authorization": f"Bearer {fabric_tok}"},
                     timeout=60)
    r.raise_for_status()
    for it in r.json()["value"]:
        if it["type"] == "Report" and it["displayName"] == DASHBOARD:
            return (f"https://app.fabric.microsoft.com/groups/"
                    f"{WORKSPACE}/reports/{it['id']}")
    return ""


def shapes_org_config(realism_yaml: str) -> str:
    """Targeted line edits only (org_config law) — never a rewrite."""
    out = []
    in_sm = False
    for line in realism_yaml.splitlines():
        if line.startswith("semantic_models:"):
            in_sm = True
            out.append("semantic_models:")
            out.append('  source_type: "folder"')
            out.append('  folder_path: "/lakehouse/default/Files/'
                       'sql-query-agent/semantic_models"')
            continue
        if in_sm:
            if line.strip() and not line.startswith(" "):
                in_sm = False
            else:
                continue        # replaced block
        if not in_sm and line.strip().startswith("kusto_db:"):
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f'{indent}kusto_db: "{SHAPES_KUSTO_DB}"')
            continue
        # source leg (field find 2026-08-27): the extractor block
        # points at the ISOLATED shapes source DB — same server
        # host, its own catalog
        if not in_sm and line.strip().startswith("database:") \
                and SHAPES_SRC_DB:
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f'{indent}database: "{SHAPES_SRC_DB}"')
            continue
        if not in_sm:
            out.append(line)
    return "\n".join(out) + "\n"


def main() -> None:
    fab = _token("https://api.fabric.microsoft.com")
    ol = _token("https://storage.azure.com")
    palette = load_palette(
        PROJECT_ROOT / "data" / "shapes" / "palette_diabetes.json")
    steps: "list[tuple[str, str]]" = []

    def step(label, fn):
        try:
            fn()
            steps.append(("ok", label))
            print(f"[ok]      {label}")
        except Exception as e:                  # noqa: BLE001
            steps.append(("BLOCKED", f"{label} :: {e}"))
            print(f"[BLOCKED] {label} :: {e}")

    root = "Files/sql-query-agent"

    def up(path, data):
        ol_write(ol, SHAPES_LH, f"{root}/{path}", data)

    # 1. org_config: realism copy + targeted edits
    def do_config():
        y = ol_read(ol, REALISM_LH,
                    f"{root}/org_config.yaml").decode()
        up("org_config.yaml", shapes_org_config(y).encode())
    step("org_config.yaml (targeted variant)", do_config)

    # 2. ScriptDom DLL (server-side copy via read+write)
    def do_dll():
        dll = ("libs/Microsoft.SqlServer.TransactSql."
               "ScriptDom.dll")
        up(dll, ol_read(ol, REALISM_LH, f"{root}/{dll}"))
    step("ScriptDom DLL", do_dll)

    # 3. the 38 corpus SQL files (flattened; collisions prefixed)
    def do_sql():
        sql_dir = (PROJECT_ROOT / "data" / "shapes" / "generated"
                   / "sql")
        files = sorted(sql_dir.rglob("*.sql"))
        seen: "dict[str, int]" = {}
        for f in files:
            seen[f.name] = seen.get(f.name, 0) + 1
        for f in files:
            name = (f"{f.parent.name}__{f.name}"
                    if seen[f.name] > 1 else f.name)
            up(f"sql_input/{name}", f.read_bytes())
    step("38 corpus SQL files -> sql_input/", do_sql)

    # 4. dictionary CSVs
    def do_dict():
        tables, columns = dict_rows(palette)
        up("dictionary/dict_tables.csv", _csv_bytes(tables))
        up("dictionary/dict_columns.csv", _csv_bytes(columns))
    step("dictionary CSVs", do_dict)

    # 5. metric names CSV (palette + the dashboard link on U7)
    def do_names():
        url = dashboard_report_url(fab)
        rows = metric_name_rows(palette)
        for r in rows:
            if r["metric_id"] == "reporting.USP_DM_Registry_Composite":
                r["report_name"] = DASHBOARD
                r["report_url"] = url
        up("input_metric_names.csv", _csv_bytes(rows))
    step("input_metric_names.csv (+dashboard link)", do_names)

    # 6. steward personas CSV
    def do_stewards():
        up("gov_steward_assignments.csv",
           _csv_bytes(steward_rows(palette)))
    step("gov_steward_assignments.csv (personas)", do_stewards)

    # 7. the dashboard TMDL for the folder source (git version —
    #    placeholders only; endpoint hygiene holds by construction)
    def do_tmdl():
        sm = PROJECT_ROOT / f"{DASHBOARD}.SemanticModel"
        for f in sorted((sm / "definition" / "tables").glob("*.tmdl")):
            up(f"semantic_models/{DASHBOARD}.SemanticModel/"
               f"definition/tables/{f.name}", f.read_bytes())
    step("dashboard TMDL (folder source)", do_tmdl)

    print()
    blocked = [s for s in steps if s[0] == "BLOCKED"]
    print(f"staging: {len(steps) - len(blocked)}/{len(steps)} ok"
          + (f"; {len(blocked)} BLOCKED -> runbook" if blocked
             else " — all assets staged"))
    raise SystemExit(1 if blocked else 0)


if __name__ == "__main__":
    main()
