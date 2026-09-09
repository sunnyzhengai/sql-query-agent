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
import csv

import pytest

from aivia.flows import connect, export_graph
from aivia.graph.read_api import ReadApi

M1_LABELS = ("db", "schema", "table", "column")


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
        if not name.startswith("graph_contains"):
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
    ruled = {("db", "schema"), ("schema", "table"),
             ("table", "column")}  # containment points parent->child
    store_contains = {(s, t) for s, es in adj.items()
                      for t, lbl in es if lbl == "contains"
                      and (label_of.get(s), label_of.get(t)) in ruled}
    exported = set()
    for pair in ("dbSchema", "schemaTable", "tableColumn"):
        for r in tables[f"graph_contains_{pair}"]:
            exported.add((r["sourceId"], r["targetId"]))
    assert exported == store_contains


def test_csv_write_is_deterministic(tmp_path, world):
    _read, tables = world
    a, b = tmp_path / "a", tmp_path / "b"
    export_graph.write_csvs(tables, a)
    export_graph.write_csvs(tables, b)
    for f in sorted(a.iterdir()):
        assert f.read_bytes() == (b / f.name).read_bytes()
        with open(f, newline="") as fh:
            assert csv.reader(fh)  # parseable
