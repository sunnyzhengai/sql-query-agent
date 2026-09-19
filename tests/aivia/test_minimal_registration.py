"""Brief_Minimal_Registration (Sunny, 2026-09-19: "keep db name and
server names optional" · MR1 ruled "a"): db_name and server leave
the mandatory set. Absent db_name, the graph roots at the estate's
SINGLE registered source (db:clarity); two sources with no db_name
cannot anchor — a named refusal, never a guess. Providing db_name
keeps every prior behavior byte-identical, including the
wrong-database cross-check (INTAKE-8/9), which narrows from
mandatory to OPT-IN: both sides naming a db arms it; omission
waives it, and the waiver is the caller's recorded choice.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.graph import kg1_intake


def _reg(**over):
    reg = {
        "dba_team": "role:dba",
        "registered_sources": ["clarity"],
        "registered_at": "2026-09-19T00:00:00Z",
        "schema_sources": {"dbo": "clarity"},
    }
    reg.update(over)
    return reg


def _manifest(**over):
    m = {
        "source": "clarity",
        "operator": "pilot",
        "as_of": "2026-09-19T00:00:00Z",
        "source_pack_version": "clarity-pack-1.1",
    }
    m.update(over)
    return m


def _snap(manifest):
    return kg1_intake.ExtractSnapshot(
        manifest=manifest, tables=[], columns=[], pks=[], joins=[],
        values=[])


def test_absent_db_name_roots_at_the_single_source():
    store = kg1_intake.new_store()
    kg1_intake.apply_registration(store, _reg())
    ids = [n.identity for n in store.current_nodes("db")]
    assert ids == ["db:clarity"]


def test_present_db_name_behaves_byte_identically():
    store = kg1_intake.new_store()
    kg1_intake.apply_registration(store, _reg(db_name="MYDB"))
    node = next(iter(store.current_nodes("db")))
    assert node.identity == "db:MYDB"
    assert node.properties["name"] == "MYDB"


def test_two_sources_without_db_name_refuse_by_name():
    store = kg1_intake.new_store()
    with pytest.raises(kg1_intake.Refusal, match="INTAKE-10"):
        kg1_intake.apply_registration(
            store, _reg(registered_sources=["clarity", "caboodle"]))


def test_minimal_manifest_passes_intake_1():
    kg1_intake.validate_extract(
        _reg(), _snap(_manifest()),
        known_packs={"clarity-pack-1.1"})


def test_cross_check_stays_armed_when_both_sides_name_the_db():
    with pytest.raises(kg1_intake.Refusal, match="INTAKE-8"):
        kg1_intake.validate_extract(
            _reg(db_name="PROD"), _snap(_manifest(db_name="TEST")),
            known_packs={"clarity-pack-1.1"})


def test_one_sided_db_name_waives_the_cross_check():
    kg1_intake.validate_extract(
        _reg(db_name="PROD"), _snap(_manifest()),
        known_packs={"clarity-pack-1.1"})
    kg1_intake.validate_extract(
        _reg(), _snap(_manifest(db_name="PROD")),
        known_packs={"clarity-pack-1.1"})
