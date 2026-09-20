"""THE JOINS_TO LOCK (Sunny's directive 2026-09-10, after the
THIRD omission of joins_to from the technical layer — M1's export
missed it, the shape census read the adjacency instead of the
store, and the gate drafts kept re-forgetting it). The memory now
lives here as physics, not discipline:

1. joins_to is TECHNICAL-LAYER content: the dictionary ALONE —
   registration + snapshot, no estate, no parser — must carry all
   65 edges. A build where joins_to arrives any later, or from
   anywhere else, fails here.
2. joins_to is NEVER derived from SQL files: the two joins the
   proc PRACTICES but the dictionary never declared must have NO
   edge — they are the drift findings, query output only.
3. Conservation: 68 declared fk groups == 65 edges + 2 counted
   pending (A8: target not yet registered, resolves on arrival)
   + 1 collapsed duplicate.

Proves: contract:aisql-design-to-code
"""
import json
import pathlib

import pytest

from aisql.flows import inbound
from aisql.flows.export_graph import export_tables
from aisql.graph import kg1_intake
from aisql.graph.read_api import ReadApi

BASE = pathlib.Path(__file__).resolve().parents[1] / \
    "AIVIA_Product" / "estates" / "ed_sepsis_dev"

EXPECTED_EDGES = 65
EXPECTED_FK_GROUPS = 68
EXPECTED_PENDING = 2
# the two joins USP_ED_SEPSIS practices that the dictionary never
# declared — the drift findings; an edge for either is a violation
# of "we never derive joins from sql files"
NEVER_DECLARED = [
    ("emr|dbo|ENCOUNTER_VISIT_REASONS", "emr|dbo|VISIT_REASONS"),
    ("emr|dbo|MEDICATIONS", "emr|dbo|REF_GENERIC_MED"),
]


@pytest.fixture(scope="module")
def dictionary_only():
    """The technical layer alone — no estate, no parser."""
    store = kg1_intake.new_store()
    reg = json.loads((BASE / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    pack = json.loads(
        (BASE / "sepsis_snapshot" / "manifest.json").read_text()
    ).get("source_pack_version", "")
    extract = inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(BASE / "sepsis_snapshot"),
        known_packs={pack})
    return store, extract


def test_dictionary_alone_carries_all_joins(dictionary_only):
    store, _ = dictionary_only
    assert len(store.current_edges("joins_to")) == EXPECTED_EDGES


def test_conservation_68_groups(dictionary_only):
    import csv
    _, extract = dictionary_only
    rows = list(csv.DictReader(open(BASE / "sepsis_snapshot" / "joins.csv")))
    groups = {r["fk_num"] for r in rows}
    assert len(groups) == EXPECTED_FK_GROUPS
    pending = [p for p in extract.pending_references
               if "fk group" in str(p)]
    assert len(pending) == EXPECTED_PENDING
    # 68 = 65 edges + 2 pending + 1 collapsed duplicate
    assert EXPECTED_FK_GROUPS - EXPECTED_EDGES - EXPECTED_PENDING == 1


def test_every_edge_carries_keys_and_cardinality(dictionary_only):
    store, _ = dictionary_only
    for e in store.current_edges("joins_to"):
        assert e.properties.get("on"), (e.from_id, e.to_id)
        assert e.properties.get("cardinality") == "many_to_one"


def test_witness_adt_events_neighbors(dictionary_only):
    store, _ = dictionary_only
    adt = sorted((e.to_id.split("|")[-1], e.properties["on"])
                 for e in store.current_edges("joins_to")
                 if e.from_id.endswith("|ADT_EVENTS"))
    assert adt == [
        ("BED_CONFIG", [["BED_STAY_ID", "BED_STAY_ID"]]),
        ("CONFIG_VALUE_SET", [["DEPARTMENT_ID", "CODE"]]),
        ("DEPARTMENTS", [["DEPARTMENT_ID", "DEPARTMENT_ID"]]),
        ("HOSPITAL_ENCOUNTERS", [["ENCOUNTER_ID", "ENCOUNTER_ID"]]),
    ]


def test_never_derived_from_sql(dictionary_only):
    store, _ = dictionary_only
    pairs = set()
    for e in store.current_edges("joins_to"):
        pairs.add((e.from_id, e.to_id))
        pairs.add((e.to_id, e.from_id))
    for a, b in NEVER_DECLARED:
        assert (a, b) not in pairs and (b, a) not in pairs, (a, b)


def test_export_ships_joins_to_with_technical_layer(dictionary_only):
    """The M1 export surface: joins_to rides the technical layer's
    export with onColumns — the omission that started this lock."""
    store, _ = dictionary_only
    tables = export_tables(ReadApi(store))
    rows = tables["graph_joins_to_tableTable"]
    assert len(rows) == EXPECTED_EDGES
    assert all(r["onColumns"] for r in rows)
