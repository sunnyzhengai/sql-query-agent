"""Brief_Closed_Shape (Sunny 2026-09-20: F12 "i agree with your
recommendation, draft the brief" + "agree with F11, approved"):
THE NAME GRAMMAR CONFORMANCE PIN. T-SQL's object-name grammar is
Microsoft's and FINITE — 1 to 4 dot-separated parts, inner parts
may be empty — so every legal way an author can write a known
table's name is generated here and asserted to land in its RULED
bucket. A shape outside the grammar counts as shape_unrecognized,
never coerced into the nearest known shape (the generator find:
the ABX corpse and F9's diagnosis were the same defect class).

Every unresolved ref carries a class from the CLOSED enum
(Contract_Logic_Layer, THE NAME GRAMMAR): schema_not_mapped ·
table_not_in_dictionary · cross_database · cross_server ·
no_default_schema · reader_writer_drift · shape_unrecognized —
and the census reports unresolved_by_class, so a class failing
100% is visible at a glance.

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
BOUND = "simemr|dbo|ENCOUNTER"


@pytest.fixture(scope="module")
def built():
    store = Store()
    reg = json.loads((F1 / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(F1 / "simemr_snapshot"),
        known_packs={"simemr-pack-0.1"})
    return store, reg


def _resolved(store, reg, written, default_schema="dbo"):
    try:
        tree = kg2_mapper.map_tree(
            "t.sql", f"SELECT e.ENCOUNTER_ID FROM {written} e;")
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    kg2_mapper.resolve(tree, store, reg, default_schema=default_schema)
    ref = tree["statements"][0]["scope"]["from_refs"][0]
    return ref, tree["resolution_census"]


# ---- the generated grammar table: every arity, each ruled ----

@pytest.mark.parametrize("written", [
    "ENCOUNTER",                       # 1 part -> default_schema
    "dbo.ENCOUNTER",                   # 2 parts
    "[dbo].[ENCOUNTER]",               # bracketed (identifiers fold)
    "SIMDB.dbo.ENCOUNTER",             # 3 parts, db matches
    "SIMDB..ENCOUNTER",                # empty schema -> default
    ".ENCOUNTER",                      # elided schema -> default
    "SIMSERVER.SIMDB.dbo.ENCOUNTER",   # 4 parts, server matches (F11)
])
def test_every_binding_form_binds(built, written):
    store, reg = built
    ref, census = _resolved(store, reg, written)
    assert ref["resolves_to"] == BOUND, written
    assert census["unresolved_refs"] == 0, written


def test_foreign_db_class(built):
    store, reg = built
    ref, census = _resolved(store, reg, "OTHERDB.dbo.ENCOUNTER")
    assert ref["resolves_to"] is None
    assert census["cross_database_reads"] == [
        {"ref": "OTHERDB.dbo.ENCOUNTER", "db": "OTHERDB"}]
    assert census["unresolved_detail"][0]["class"] == "cross_database"
    assert census["unresolved_by_class"] == {"cross_database": 1}


def test_foreign_server_class(built):
    """F11 ruled (the ruling-(8) symmetry): a linked-server read is
    another machine's data — never bound locally, counted with the
    server NAMED."""
    store, reg = built
    ref, census = _resolved(store, reg, "OTHERSRV.SIMDB.dbo.ENCOUNTER")
    assert ref["resolves_to"] is None
    assert census["cross_server_reads"] == [
        {"ref": "OTHERSRV.SIMDB.dbo.ENCOUNTER", "server": "OTHERSRV"}]
    assert census["unresolved_detail"][0]["class"] == "cross_server"
    assert census["unresolved_by_class"] == {"cross_server": 1}


def test_waived_server_binds_and_is_reported(built):
    """Server not declared in the registration (optional, MR1a) →
    binds on db/schema/table per the waiver; the census reports the
    server names seen so the waiver is visible."""
    store, reg = built
    waived = {k: v for k, v in reg.items() if k != "server"}
    ref, census = _resolved(store, waived,
                            "OTHERSRV.SIMDB.dbo.ENCOUNTER")
    assert ref["resolves_to"] == BOUND
    assert census["server_names_seen"] == ["OTHERSRV"]


def test_no_default_schema_class(built):
    store, reg = built
    ref, census = _resolved(store, reg, "ENCOUNTER",
                            default_schema=None)
    assert ref["resolves_to"] is None
    assert census["unresolved_detail"][0]["class"] == "no_default_schema"


def test_schema_not_mapped_vs_table_not_in_dictionary(built):
    store, reg = built
    _, census = _resolved(store, reg, "nosuchschema.ENCOUNTER")
    assert census["unresolved_detail"][0]["class"] == "schema_not_mapped"
    _, census = _resolved(store, reg, "dbo.NO_SUCH_TABLE")
    assert census["unresolved_detail"][0]["class"] == \
        "table_not_in_dictionary"


def test_drift_columns_carry_the_class(built):
    store, reg = built
    try:
        tree = kg2_mapper.map_tree(
            "t.sql", "SELECT e.NO_SUCH_COLUMN FROM dbo.ENCOUNTER e;")
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    kg2_mapper.resolve(tree, store, reg, default_schema="dbo")
    census = tree["resolution_census"]
    assert census["unresolved_detail"][0]["class"] == \
        "reader_writer_drift"
    assert census["unresolved_by_class"] == {"reader_writer_drift": 1}


# ---- the wording rule (proposal 3): diagnoses stay honest ----

def _sheet(tmp_path, built, detail):
    store, reg = built
    from aisql.graph.read_api import ReadApi
    report = inbound.EstateReport()
    report.trees = {"f.sql": {"name": "f.sql", "resolution_census": {
        "unresolved": [detail["ref"]], "unresolved_detail": [detail]}}}
    inbound.write_intake_result_tables(
        tmp_path, reg, [], report, ReadApi(store))
    return (tmp_path / "unresolved_references.csv").read_text()


def test_unrecognized_shape_blames_the_engine_not_the_data(
        tmp_path, built):
    sheet = _sheet(tmp_path, built, {
        "ref": "a.b.c.d.e", "kind": "table",
        "schema": "(unreadable)", "class": "shape_unrecognized"})
    assert "engine finding" in sheet
    assert "report this to AISQL" in sheet
    assert "SCHEMA MISMATCH" not in sheet


def test_cross_reads_name_the_other_side(tmp_path, built):
    sheet = _sheet(tmp_path, built, {
        "ref": "OTHERDB.dbo.ENCOUNTER", "kind": "table",
        "schema": "dbo", "class": "cross_database",
        "cross_database": "OTHERDB"})
    assert "CROSS-DATABASE" in sheet and "OTHERDB" in sheet
    sheet = _sheet(tmp_path, built, {
        "ref": "OTHERSRV.SIMDB.dbo.ENCOUNTER", "kind": "table",
        "schema": "dbo", "class": "cross_server",
        "cross_server": "OTHERSRV"})
    assert "CROSS-SERVER" in sheet and "OTHERSRV" in sheet
