# fabric_assets.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/04_fabric_move.md (M04, decision 7 stage A)
# Contract: AIVIA_01_Design/04_fabric_move_data_contract.md (Output
#           File 3: the asset source becomes a parameter, never a fork)
# Tests:    AIVIA_01_Test/test_04_fabric_move_data_contract.py (grows a
#           stage-A section, RED first)
#
# PURPOSE. The chat reads its assets FROM Fabric: the eleven Delta
# tables (the Fabric truth, Delta-only ruling) become the same assets
# dict the local json sheets produce — one engine, two sources, zero
# behavioral difference. Acceptance: startup census parity TO THE
# DIGIT, then Sunny's twelve shapes rerun.
#
# ---------------------------------------------------------------------
# THE ONE DECISION THIS STEP NEEDS (Sunny rules before code):
#   Reading Delta tables from local Python requires ONE new pinned
#   package: `deltalake` (delta-rs — no Spark, reads OneLake over
#   abfss with a bearer token; its wheel bundles the arrow reader).
#   - Why not avoid it: without a Delta reader the only no-package
#     path is re-reading the json TRANSPORT files from OneLake — which
#     validates the wrong artifact (the Files are the load's input;
#     the TABLES are the Fabric truth the chat must prove it can live
#     on).
#   - The law it touches: the pinned-packages list in CLAUDE.md
#     operational facts gains `deltalake <version pinned at install>`.
#     Local only — the Fabric notebooks keep using Spark; this package
#     never ships in the wheel's requirements.
#   RECOMMENDED: yes. On Sunny's yes: pip install, pin the version in
#   CLAUDE.md, proceed.
#
# ---------------------------------------------------------------------
# THE SHAPE (no fork, one refactor + one new reader):
#
# 1. chat_bot.load_assets REFACTORS into:
#      _build_assets(sheets, terms_rows, abstract_rows) — the existing
#        index/census/layout construction, byte-identical behavior,
#        source-blind.
#      load_assets(dir02, dir03) — the local frontend, exactly today's
#        behavior (reads json + terms md + abstracts json, calls
#        _build_assets). All existing tests stay green untouched.
#
# 2. THIS module adds the Fabric frontend:
#      load_assets_fabric(workspace, lakehouse, token)
#        - reads the Delta tables via deltalake over OneLake:
#          abfss://<workspace>@onelake.dfs.fabric.microsoft.com/
#              <lakehouse>/Tables/<name>
#          token: the sync_wheel sign_in with the STORAGE scope (the
#          sync_files pattern — browser sign-in, token in memory only).
#        - UN-CAMELS every row back to snake_case (_snake, the exact
#          inverse of the loader's _camel — tableId -> table_id) so the
#          sheets dict is byte-equal to the local one. columnPairs in
#          graph tables stay untouched (the chat never reads graph_*;
#          listed for completeness, not loaded).
#        - reconstructs: sheets (tables, columns, joins, values,
#          value_embeddings, no_match), terms rows
#          (chat_technical_terms), abstract rows (chat_abstract_names)
#          — then calls chat_bot._build_assets. Same dict out.
#        - loads ONLY what the chat reads: the six dict_* tables + the
#          two chat_* tables. The graph_* tables stay Fabric's.
#
# 3. chat_bot CLI grows the source parameter (never a fork):
#      local (unchanged):
#        chat_bot.py <02 dir> <03 dir> [port] [flags]
#      stage A:
#        chat_bot.py --fabric --workspace <id> --lakehouse <id>
#            [--tenant <id>] [port] [flags]
#      --fabric signs in (browser), loads from Delta, then the server
#      runs EXACTLY as before — same census print, same page, same
#      everything. The census line gains one word: the source
#      ("assets: local" / "assets: fabric").
#
# ---------------------------------------------------------------------
# CLAUDE'S TESTS (stage-A section of test_04, red first; the LIVE
# Fabric read is Sunny's hand via the runbook — not pytest-able):
#   - _snake inverts _camel exactly, for EVERY field name in the
#     loader's eleven table schemas (round-trip identity).
#   - THE PARITY TEST, pure and offline: take the real local assets,
#     run them through the loader's _camel_rows (what Fabric stores),
#     back through _snake rows (what load_assets_fabric reconstructs),
#     feed _build_assets — the census must equal the direct local
#     load's census EXACTLY. Proves the round trip loses nothing,
#     without a network.
#   - chat_bot's existing tests stay green through the refactor
#     (behavior-preservation is the refactor's acceptance).
#   - --fabric without --workspace/--lakehouse refuses, naming them.
#
# After build: the runbook gains Step F (the stage-A startup command +
# "census must match local to the digit" + the twelve shapes rerun);
# Sunny's shapes run against the Fabric-backed chat by her hand.

import chat_bot

ONELAKE_DFS = "onelake.dfs.fabric.microsoft.com"

# The eight tables the chat reads; the graph_* tables stay Fabric's.
CHAT_TABLES = {
    "tables": "dict_tables",
    "columns": "dict_columns",
    "joins": "dict_joins",
    "values": "dict_values",
    "value_embeddings": "dict_value_embeddings",
    "no_match": "dict_no_match",
}


def _snake(name):
    """The exact inverse of load_dictionary_tables._camel."""
    out = []
    for ch in name:
        if ch.isupper():
            out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
    return "".join(out)


def _snake_rows(rows):
    return [{_snake(k): v for k, v in row.items()} for row in rows]


def _table_urls(workspace, lakehouse, table):
    """Schema-enabled lakehouses (ours: the dbo schema, met live
    2026-10-01) keep tables under Tables/dbo/<name>; legacy ones under
    Tables/<name>. Try in that order."""
    base = f"abfss://{workspace}@{ONELAKE_DFS}/{lakehouse}/Tables"
    return [f"{base}/dbo/{table}", f"{base}/{table}"]


def _read_delta_rows(workspace, lakehouse, table, token):
    from deltalake import DeltaTable

    last_error = None
    for url in _table_urls(workspace, lakehouse, table):
        try:
            dt = DeltaTable(url, storage_options={
                "bearer_token": token, "use_fabric_endpoint": "true"})
            return dt.to_pyarrow_table().to_pylist()
        except Exception as e:  # noqa: BLE001 — the kernel's not-found
            last_error = e     # types vary; both paths get their try
    raise SystemExit(
        f"could not read Delta table {table!r} at either path "
        f"(Tables/dbo/ or Tables/): {last_error}")


def load_assets_fabric(workspace, lakehouse, token):
    """The Fabric frontend: the eight Delta tables (the Fabric truth,
    Delta-only ruling) un-camel back to byte-equal sheets, then the
    same _build_assets as local — one engine, two sources."""
    sheets = {}
    for sheet_key, table in CHAT_TABLES.items():
        print(f"  reading {table}…")
        sheets[sheet_key] = _snake_rows(
            _read_delta_rows(workspace, lakehouse, table, token))
    terms = _snake_rows(
        _read_delta_rows(workspace, lakehouse,
                         "chat_technical_terms", token))
    abstract_rows = _snake_rows(
        _read_delta_rows(workspace, lakehouse,
                         "chat_abstract_names", token))
    return chat_bot._build_assets(sheets, terms, abstract_rows)
