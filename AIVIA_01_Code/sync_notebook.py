# sync_notebook.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design: AIVIA_01_Design/01_subject_sql_files.md — F21: notebook
#         definitions sync from AIVIA_01_Code via the sync script;
#         RUNNING stays by Sunny's hand.
#
# WHAT THIS ENDS: the F11 cell living in comments + Sunny's clipboard.
# From now on the notebook's source is a REAL versioned file:
#
#     AIVIA_01_Code/notebook_f11_load_lh_table.py
#
# (created in this same step — it holds exactly the cell that ran F11:
# import to_table_rows, build rows from the Files path, write the full
# table f01_subject_sql_files_lh_table, write the embedding-free
# f01_subject_sql_files_graph). Git is the source of truth; the Fabric
# notebook item becomes a copy this script refreshes.
#
# THE CRITICAL SAFETY RULE — merge, never replace:
#     A Fabric notebook's definition holds MORE than code: its metadata
#     carries the attached default lakehouse and environment. Pushing a
#     bare new definition would silently DETACH AIVIA_01_LH and
#     AIVIA_01_ENV — the exact failure class we just spent an afternoon
#     on. So the sync is read-modify-write:
#       1. GET the notebook's current definition (ipynb form).
#       2. Replace ONLY the code cells with the source file's content
#          (one cell per "# %%"-separated block; a plain file = one cell).
#       3. Keep every piece of notebook metadata exactly as it was.
#       4. Push the merged definition back; poll the operation to done.
#     Consequence: Sunny attaches lakehouse/environment ONCE by hand
#     (already done); the sync never touches that again.
#
# CAPACITY: updating a definition is a metadata write — no Spark, no
# capacity. RUNNING the notebook is capacity and stays Sunny's hand
# (F21's own words). The script never triggers a run.
#
# THE COMMAND (standalone):
#     /opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_notebook.py \
#         --workspace <workspace-id> --notebook <notebook-item-id> \
#         --source AIVIA_01_Code/notebook_f11_load_lh_table.py
#     The notebook item id comes from the portal URL with the notebook
#     open (.../synapsenotebooks/<notebook-item-id>). Sign-in is the
#     same browser flow as sync_wheel (imported from it, not copied).
#
# AND THE ONE-COMMAND PATH (the ask: "sync notebooks when I sync the
# wheel"): sync_wheel.py gains an OPTIONAL --notebook <item-id> flag.
# When present, after the wheel is staged it also syncs the notebook
# source via this module — one sign-in, one command, wheel + notebook
# together. Without the flag, sync_wheel behaves exactly as today.
#
# PSEUDO CODE
#
# Step 1 — read the source file.
#     Split on lines starting with "# %%" into cells (standard cell
#     markers); no marker = the whole file is one code cell.
#
# Step 2 — sign in (reuse sync_wheel's browser sign-in, same token
#     scope; passed in when called from sync_wheel so she signs in once).
#
# Step 3 — GET the current definition.
#     Fabric REST: POST .../notebooks/<id>/getDefinition?format=ipynb,
#     decode the notebook-content part (base64 json).
#
# Step 4 — merge.
#     Keep the ipynb's top-level metadata untouched (lakehouse +
#     environment attachments live there). Replace the "cells" list with
#     code cells built from Step 1. Fail loudly if the decoded content
#     is not the shape we expect — never push a guess.
#
# Step 5 — push and wait.
#     POST .../notebooks/<id>/updateDefinition with the merged part.
#     A 202 answer carries an operation id — poll it to Succeeded, and
#     fail loudly with Fabric's words on anything else.
#     Print: "notebook definition updated — open it in Fabric and RUN
#     it by your hand when ready."
#
# TESTS (test_01_sync_notebook.py, red first) — the pure parts:
#   - splitting: no marker -> 1 cell; two "# %%" blocks -> 2 cells,
#     marker lines not included in cell text
#   - merging: metadata (lakehouse/environment) comes through BYTE-equal;
#     cells are replaced; wrong-shaped input raises, never guesses
#   - the source file notebook_f11_load_lh_table.py agrees with the
#     record: imports to_table_rows, writes BOTH table names (full +
#     graph) — pins the file to the F11/F13 rulings
#   - the command refuses to run without --workspace/--notebook/--source,
#     naming what is missing
#   The live GET/merge/push is acceptance-tested by Sunny's first real
#   run: she syncs, opens the notebook in Fabric, sees the same cell,
#   attachments intact, runs it by hand.

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

FABRIC_API = "https://api.fabric.microsoft.com/v1"


# --------------------------------------------------------------------------
# Steps 1 + 4 — pure: split the source, merge into the definition
# --------------------------------------------------------------------------


def split_cells(text):
    lines = text.splitlines()
    if not any(line.startswith("# %%") for line in lines):
        stripped = text.strip()
        return [stripped] if stripped else []
    cells, current = [], []
    for line in lines:
        if line.startswith("# %%"):
            if "\n".join(current).strip():
                cells.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    if "\n".join(current).strip():
        cells.append("\n".join(current).strip())
    return cells


def merge_definition(notebook, cell_texts):
    if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
        raise ValueError(
            "notebook definition shape not recognized (no 'cells' list) — "
            "refusing to push a guess"
        )
    merged = dict(notebook)  # metadata/nbformat keys carried over untouched
    merged["cells"] = [
        {
            "cell_type": "code",
            "source": text.splitlines(keepends=True),
            "metadata": {},
            "outputs": [],
            "execution_count": None,
        }
        for text in cell_texts
    ]
    return merged


# --------------------------------------------------------------------------
# Steps 3 + 5 — the Fabric calls (long-running-operation aware)
# --------------------------------------------------------------------------


def _call(token, method, url, body=None):
    """One http call. Returns (status, headers, parsed-json-or-{})."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {token}"},
    )
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"Fabric said no to {method} {url} "
            f"(HTTP {e.code}):\n{e.read().decode(errors='replace')}"
        )


def _wait_for_operation(token, headers):
    """A 202 answer points at an operation; poll it to Succeeded and
    return the operation url (its /result holds any payload)."""
    op_url = headers.get("Location")
    if not op_url:
        raise SystemExit("Fabric answered 202 without a Location to poll")
    while True:
        time.sleep(int(headers.get("Retry-After", 3)))
        _, headers, body = _call(token, "GET", op_url)
        state = body.get("status", "")
        if state == "Succeeded":
            return op_url
        if state in ("Failed", "Cancelled"):
            raise SystemExit(
                f"Fabric operation {state} — verbatim:\n{json.dumps(body, indent=2)}"
            )


def get_notebook_ipynb(token, workspace, notebook):
    url = (
        f"{FABRIC_API}/workspaces/{workspace}/notebooks/{notebook}"
        f"/getDefinition?format=ipynb"
    )
    status, headers, body = _call(token, "POST", url)
    if status == 202:
        op_url = _wait_for_operation(token, headers)
        _, _, body = _call(token, "GET", f"{op_url}/result")
    parts = body.get("definition", {}).get("parts", [])
    for part in parts:
        if part.get("path", "").endswith(".ipynb"):
            content = json.loads(base64.b64decode(part["payload"]))
            return content, part["path"], parts
    raise SystemExit(
        "no .ipynb part in the notebook definition — parts were: "
        + ", ".join(p.get("path", "?") for p in parts)
    )


def push_notebook_ipynb(token, workspace, notebook, ipynb, ipynb_path, parts):
    payload = base64.b64encode(json.dumps(ipynb).encode()).decode()
    new_parts = [
        {"path": p["path"], "payload": p["payload"], "payloadType": "InlineBase64"}
        if not p.get("path", "").endswith(".ipynb")
        else {"path": ipynb_path, "payload": payload, "payloadType": "InlineBase64"}
        for p in parts
    ]
    url = (
        f"{FABRIC_API}/workspaces/{workspace}/notebooks/{notebook}/updateDefinition"
    )
    status, headers, _ = _call(
        token, "POST", url, body={"definition": {"format": "ipynb", "parts": new_parts}}
    )
    if status == 202:
        _wait_for_operation(token, headers)


def sync_definition(token, workspace, notebook, source_path):
    """The whole read-modify-write. Reused by sync_wheel's --notebook flag."""
    cells = split_cells(Path(source_path).read_text(encoding="utf-8"))
    if not cells:
        raise SystemExit(f"{source_path} has no code — refusing to empty the notebook")
    ipynb, ipynb_path, parts = get_notebook_ipynb(token, workspace, notebook)
    merged = merge_definition(ipynb, cells)
    push_notebook_ipynb(token, workspace, notebook, merged, ipynb_path, parts)
    print(
        f"notebook definition updated from {Path(source_path).name} "
        f"({len(cells)} cell{'s' if len(cells) != 1 else ''}) — "
        "open it in Fabric and RUN it by your hand when ready"
    )


# --------------------------------------------------------------------------
# The standalone command
# --------------------------------------------------------------------------


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Sync a notebook's definition from a source file in "
        "AIVIA_01_Code (F21). Code cells are replaced; the notebook's "
        "lakehouse/environment attachments are never touched. The notebook "
        "item id is in the portal URL with the notebook open.",
    )
    parser.add_argument("--workspace", required=True, help="Fabric workspace id")
    parser.add_argument("--notebook", required=True, help="Notebook item id")
    parser.add_argument("--source", required=True, help="source .py file to push")
    parser.add_argument(
        "--tenant", default="organizations",
        help="Entra tenant id (default: asked during sign-in)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    from sync_wheel import sign_in  # same browser sign-in, imported not copied

    token = sign_in(args.tenant)
    sync_definition(token, args.workspace, args.notebook, args.source)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
