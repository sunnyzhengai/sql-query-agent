"""M1 — THE FABRIC GRAPH EXPORT READING (the materialization plan,
Manifest_Build §E5; ruled 2026-09-09: no Neo4j — the verification
surface is Fabric Graph on Sunny's capacity).

A READING: writes nothing to the graph; produces one table per
node label and one per (source, edge, target) pair — flattened
camelCase columns, nodeId key (the proven NL2GQL shape). M1 scope
is the TECHNICAL LAYER only: db · schema · table · column +
contains. The export mirrors the store EXACTLY — the same Q1/Q3
equalities Sunny will run in GQL are pinned here first.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import connect, export_graph
from aivia.graph.read_api import ReadApi

M1_LABELS = ("db", "db_schema", "table", "column")


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    read = ReadApi(store)
    return read, export_graph.export_tables(read, labels=M1_LABELS)


def test_one_node_table_per_label_with_store_counts(world):
    read, tables = world
    for label in M1_LABELS:
        rows = tables[f"graph_{label}"]
        assert len(rows) == len(read.nodes(label))


def test_camel_case_columns_and_node_id_key(world):
    _read, tables = world
    for name, rows in tables.items():
        assert rows, f"{name} is empty"
        for col in rows[0]:
            assert "_" not in col, f"{name}.{col} is not camelCase"
        if not (name.startswith("graph_has_part")
                    or name.startswith("graph_reads")):
            assert "nodeId" in rows[0]
            ids = [r["nodeId"] for r in rows]
            assert len(ids) == len(set(ids)), f"{name}: dup nodeIds"


def test_descriptions_ride_verbatim(world):
    read, tables = world
    by_id = {r["nodeId"]: r for r in tables["graph_table"]}
    for n in read.nodes("table"):
        assert by_id[n.identity]["description"] == \
            (n.properties.get("description") or "")


def test_contains_edges_split_per_pair_and_mirror_the_store(world):
    read, tables = world
    adj = connect.build_adjacency(read)
    label_of = {n.identity: lbl for lbl in M1_LABELS
                for n in read.nodes(lbl)}
    ruled = {("db", "db_schema"), ("db_schema", "table"),
             ("table", "column")}  # containment points parent->child
    store_contains = {(s, t) for s, es in adj.items()
                      for t, lbl in es if lbl == "has_part"
                      and (label_of.get(s), label_of.get(t)) in ruled}
    exported = set()
    for pair in ("dbSchema", "schemaTable", "tableColumn"):
        for r in tables[f"graph_has_part_{pair}"]:
            exported.add((r["sourceId"], r["targetId"]))
    assert exported == store_contains


def test_parquet_write_is_deterministic_and_lossless(tmp_path, world):
    """Parquet by corpse (2026-09-09): CSV quote-escaping broke
    Fabric's loader — quote-bearing descriptions loaded NULL and
    their nodes/edges vanished. Parquet round-trips VERBATIM."""
    import pyarrow.parquet as pq
    _read, tables = world
    a, b = tmp_path / "a", tmp_path / "b"
    export_graph.write_parquet(tables, a)
    export_graph.write_parquet(tables, b)
    for f in sorted(a.iterdir()):
        assert f.read_bytes() == (b / f.name).read_bytes()
    # the corpse row survives byte-perfect, quotes and all
    cols = pq.read_table(a / "graph_column.parquet").to_pylist()
    victim = next(r for r in cols
                  if r["name"] == "WRONG_MED_ALT_CNT")
    assert '"NDC Not Part of Order"' in victim["description"]


# ---- M2: the scope layer (bottom-up re-ruling, 2026-09-10) ----------
def test_scope_rows_carry_stored_descriptions(world):
    read, tables = world
    rows = tables["graph_scope"]
    assert len(rows) == len(read.nodes("scope"))
    for r in rows:
        assert r["description"], f"{r['nodeId']}: empty description"
    names = {r["name"] for r in rows}
    assert "#Base_Pop" in names


def test_scope_reads_table_edges_at_true_grain(world):
    read, tables = world
    edges = tables["graph_reads_scopeTable"]
    scopes = {r["nodeId"] for r in tables["graph_scope"]}
    table_ids = {n.identity for n in read.nodes("table")}
    assert edges
    for e in edges:
        assert e["sourceId"] in scopes
        assert e["targetId"] in table_ids
    # the deciding example: the ED base population reads the fact
    assert {"sourceId": "reporting/USP_ED_SEPSIS.sql::#Base_Pop",
            "targetId": "emr|dbo|ED_ENCOUNTERS_FACT"} in edges
    pairs = [(e["sourceId"], e["targetId"]) for e in edges]
    assert len(pairs) == len(set(pairs))


# ---- THE RESERVED-WORD GATE (Sunny 2026-09-09: 'let's replace
# these key words' — checked against the vendored OFFICIAL list,
# never discovered live in the query editor again) ----------------
def test_no_name_collides_with_gql_reserved_words(world):
    import json
    import pathlib

    from aivia.graph.metamodel import REGISTRY_DIR
    reserved = set(json.loads(
        (pathlib.Path(REGISTRY_DIR).parent
         / "Registry_GQL_Reserved_Words.json")
        .read_text())["reserved"])
    _read, tables = world
    offenders = []
    ledger = metamodel_ledger()
    for name, row in ledger:
        if name.upper() in reserved:
            offenders.append(f"ledger {row['Kind']} '{name}'")
    for tname, rows in tables.items():
        if tname.upper() in reserved:
            offenders.append(f"table '{tname}'")
        for col in (rows[0] if rows else {}):
            if col.upper() in reserved:
                offenders.append(f"{tname}.{col}")
    assert not offenders, (
        "GQL-reserved names in the export/ledger — rename by "
        f"ruling before shipping: {offenders}")


def metamodel_ledger():
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Shape_Ledger"]
    return [(r["Name"], r) for r in sheet if r["Name"] != "-"]
