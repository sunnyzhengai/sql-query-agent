"""Slice 1: KG1 intake vs the F1 answer key — the graph, node by node.

The exit criterion is the fixture: applying registration + both F1
snapshots must reproduce expected_graph.json exactly (nodes, edges,
values, gap lists, the layer-3 dba responsibility), pass INTAKE-0..10,
and be idempotent on re-apply (LC-S3 / CHECK-TL-3).
"""
import csv
import json
import pathlib

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake
from aivia.graph.store import Store

F1 = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "fixtures" / "F1_minimal_estate"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


@pytest.fixture()
def built():
    """Registration + both snapshots applied in the fixture's order."""
    store = Store()
    reg = json.loads((F1 / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    reports = {}
    for src in ("simemr", "org"):
        snap = kg1_intake.load_snapshot(F1 / f"{src}_snapshot")
        reports[src] = inbound.receive_extract(
            store, reg, snap, known_packs=KNOWN_PACKS)
    return store, reports


@pytest.fixture()
def expected():
    return json.loads((F1 / "expected_graph.json").read_text())


def _current(store, kind):
    return {n.identity: n for n in store.current_nodes(kind)}


def test_db_minted_from_registration_not_extracts(built, expected):
    store, reports = built
    dbs = _current(store, "db")
    assert set(dbs) == {"db:SIMDB"}
    assert dbs["db:SIMDB"].properties["minted_from"].startswith("registration")
    # A1: the org apply did NOT re-create the db
    assert "db" not in reports["org"].change_report_kinds_created


def test_schema_nodes_match_answer_key(built, expected):
    store, _ = built
    schemas = _current(store, "schema")
    for exp in expected["nodes"]["schemas"]:
        assert exp["id"] in schemas
        assert schemas[exp["id"]].as_of == exp["as_of"]
    assert len(schemas) == len(expected["nodes"]["schemas"])


def test_table_nodes_match_answer_key(built, expected):
    store, _ = built
    tables = _current(store, "table")
    for exp in expected["nodes"]["tables"]:
        node = tables[exp["id"]]
        assert node.properties["grain"] == exp["grain"], exp["id"]
        assert node.properties["pk_columns"] == exp["pk_columns"]
        assert node.properties["description"] == exp["description"]
    assert len(tables) == len(expected["nodes"]["tables"])


def test_every_csv_column_lands_verbatim(built):
    store, _ = built
    cols = _current(store, "column")
    n = 0
    for src in ("simemr", "org"):
        for row in csv.DictReader(open(F1 / f"{src}_snapshot" / "columns.csv")):
            n += 1
            node = cols[f"{src}|{row['schema']}|{row['table']}|{row['column']}"]
            assert node.properties["description"] == row["description"]
    assert len(cols) == n == 21


def test_values_map_lands_on_the_referencing_column(built, expected):
    store, _ = built
    cols = _current(store, "column")
    exp = expected["nodes"]["columns"]["values_map"]
    key = "simemr|dbo|ENCOUNTER|APPT_STATUS_C"
    want = {k: v for k, v in exp[key].items() if not k.startswith("_")}
    assert cols[key].properties["values"] == want
    with_values = [c for c in cols.values() if c.properties.get("values")]
    assert len(with_values) == 1


def test_joins_to_edges_match_answer_key_exactly(built, expected):
    store, _ = built
    got = {(e.from_id, e.to_id, tuple(map(tuple, e.properties["on"])),
            e.properties["cardinality"]) for e in store.current_edges("joins_to")}
    want = {(e["from"], e["to"], tuple(map(tuple, e["on"])), e["cardinality"])
            for e in expected["edges"]["joins_to"]}
    assert got == want  # incl. the fk 3+4 dedup: category column wins


def test_containment_chain_complete(built):
    store, _ = built
    contains = store.current_edges("contains")
    kinds = {}
    for kind in ("db", "schema", "table", "column"):
        kinds.update({n.identity: kind for n in store.current_nodes(kind)})
    children_with_parent = {e.to_id for e in contains}
    for identity, kind in kinds.items():
        if kind != "db":
            assert identity in children_with_parent, f"orphan {kind} {identity}"


def test_gap_lists_match_answer_key(built, expected):
    _, reports = built
    grain_gap = sorted(reports["simemr"].gap_lists["grain_not_declared"]
                       + reports["org"].gap_lists["grain_not_declared"])
    assert grain_gap == sorted(expected["gap_lists"]["grain_not_declared"])
    for rep in reports.values():
        assert rep.gap_lists["pk_missing"] == []
        assert rep.pending_references == []


def test_dba_responsibility_minted_from_prereq(built, expected):
    store, _ = built
    resp = store.current_nodes("responsibility")
    assert len(resp) == 1
    exp = expected["nodes"]["layer3_expected"][0]
    assert resp[0].properties["kind"] == exp["kind"]
    assert resp[0].properties["holder"] == exp["holder"]
    assert resp[0].properties["about"] == "db:SIMDB"


def test_change_reports_match_expectation(built):
    _, reports = built
    assert reports["simemr"].objects_created == 7  # 6 tables + schema chain
    assert reports["org"].objects_created == 2     # org_custom chain + 1 table


def test_rebuild_is_idempotent(built):
    store, _ = built
    reg = json.loads((F1 / "registration.json").read_text())
    stamp = store.state_stamp()
    for src in ("simemr", "org"):
        snap = kg1_intake.load_snapshot(F1 / f"{src}_snapshot")
        rep = inbound.receive_extract(store, reg, snap,
                                      known_packs=KNOWN_PACKS)
        assert rep.objects_created == 0  # LC-S3: unchanged -> NO new version
    assert store.state_stamp() == stamp


def test_metamodel_conformance_over_the_built_graph(built):
    """CHECK-TL-4: every node/edge validates against the ratified
    kg1_technical registry — kinds, required properties, shapes."""
    from aivia.graph import metamodel
    store, _ = built
    problems = metamodel.validate_technical_layer(store)
    assert problems == []
