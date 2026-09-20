"""Brief_Pilot_Build_1 slice A2 (Brief_Pilot_Findings_R1 F9, ruling
(8) "i agree with option b"): db-qualified three-part names
(`db.schema.table`) split db · schema · table and BIND ON SCHEMA —
the old split-at-the-last-dot made the schema key `db.schema`,
unresolvable by construction, and a whole proc's voices degraded
(FL12's raw join fallback, bare name words, silent value maps).

The db part stays meaningful, COUNTED-NEVER-REFUSED:
- registered db == ref's db → binds (the match IS the cross-check
  passing);
- registered db != ref's db → unresolved, counted as a
  cross-database read WITH THE DB NAMED (legitimate SQL; the count
  is product signal toward multi-source registration);
- db_name omitted (the minimal path) → schema-only binding stands
  per the waiver, and the census REPORTS distinct db names seen so
  the risky waiver becomes visible.

Proves: contract:aisql-design-to-code
"""
import json
import pathlib

import pytest

from aisql.flows import inbound
from aisql.graph import kg1_intake, kg2_mapper
from aisql.graph.kg2_mapper.scriptdom_loader import ScriptDomUnavailable
from aisql.graph.store import Store

F1 = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "fixtures" / "F1_minimal_estate"


@pytest.fixture(scope="module")
def built():
    store = Store()
    reg = json.loads((F1 / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(F1 / "simemr_snapshot"),
        known_packs={"simemr-pack-0.1"})
    return store, reg


def _resolved(store, reg, sql):
    try:
        tree = kg2_mapper.map_tree("t.sql", sql)
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    kg2_mapper.resolve(tree, store, reg)
    ref = tree["statements"][0]["scope"]["from_refs"][0]
    return ref, tree["resolution_census"]


def test_registered_db_binds_on_schema(built):
    store, reg = built
    ref, census = _resolved(
        store, reg,
        "SELECT e.ENCOUNTER_ID FROM SIMDB.dbo.ENCOUNTER e;")
    assert ref["resolves_to"] == "simemr|dbo|ENCOUNTER"
    assert census["unresolved_refs"] == 0


def test_db_match_folds_case(built):
    store, reg = built
    ref, _ = _resolved(
        store, reg, "SELECT e.ENCOUNTER_ID FROM simdb.dbo.ENCOUNTER e;")
    assert ref["resolves_to"] == "simemr|dbo|ENCOUNTER"


def test_foreign_db_is_a_counted_cross_database_read(built):
    store, reg = built
    ref, census = _resolved(
        store, reg,
        "SELECT e.ENCOUNTER_ID FROM OTHERDB.dbo.ENCOUNTER e;")
    assert ref["resolves_to"] is None
    assert census["unresolved_refs"] == 1
    assert census["cross_database_reads"] == [
        {"ref": "OTHERDB.dbo.ENCOUNTER", "db": "OTHERDB"}]


def test_waived_db_binds_and_the_census_names_what_it_saw(built):
    store, reg = built
    waived = {k: v for k, v in reg.items() if k != "db_name"}
    ref, census = _resolved(
        store, waived,
        "SELECT e.ENCOUNTER_ID FROM WORKDB.dbo.ENCOUNTER e;")
    assert ref["resolves_to"] == "simemr|dbo|ENCOUNTER"
    assert census["db_names_seen"] == ["WORKDB"]


def test_two_part_names_are_untouched(built):
    store, reg = built
    ref, census = _resolved(
        store, reg, "SELECT e.ENCOUNTER_ID FROM dbo.ENCOUNTER e;")
    assert ref["resolves_to"] == "simemr|dbo|ENCOUNTER"
    assert "db_names_seen" not in census
    assert "cross_database_reads" not in census
