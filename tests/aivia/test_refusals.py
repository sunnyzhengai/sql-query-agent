"""Slice 1: the F6 refusal set — every refusal NAMES its rule.

The error-contract law: a failed intake is self-serviceable by the
customer's DBA without a support call. Each case is a minimal delta
from F1's accepted snapshots; refused extracts write NOTHING (LC-F5
atomicity). A14's malformed fk group is the one non-refusal: it
quarantines, counts, alerts the DBA, and the load proceeds.

Proves: contract:aivia-design-to-code
"""
import json
import pathlib
import shutil

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake
from aivia.graph.store import Store

F1 = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "fixtures" / "F1_minimal_estate"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


@pytest.fixture()
def registered():
    store = Store()
    reg = json.loads((F1 / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    return store, reg


def _mutated(tmp_path, src, mutate):
    snap_dir = tmp_path / f"{src}_snapshot"
    shutil.copytree(F1 / f"{src}_snapshot", snap_dir)
    mutate(snap_dir)
    return kg1_intake.load_snapshot(snap_dir)


def _expect_refusal(store, reg, snap, rule_name, *fragments):
    stamp = store.state_stamp()
    with pytest.raises(kg1_intake.Refusal) as exc:
        inbound.receive_extract(store, reg, snap, known_packs=KNOWN_PACKS)
    assert exc.value.rule == rule_name
    for frag in fragments:
        assert frag in str(exc.value)
    assert store.state_stamp() == stamp  # LC-F5: NOTHING written


def test_r_db_unregistered_db(registered, tmp_path):
    store, reg = registered

    def mutate(d):
        m = json.loads((d / "manifest.json").read_text())
        m["db_name"] = "OTHERDB"
        (d / "manifest.json").write_text(json.dumps(m))
    snap = _mutated(tmp_path, "simemr", mutate)
    _expect_refusal(store, reg, snap, "INTAKE-8", "OTHERDB", "SIMDB")


def test_r_capture_declared_vs_captured(registered, tmp_path):
    store, reg = registered

    def mutate(d):
        m = json.loads((d / "manifest.json").read_text())
        m["captured_db_name"] = "SIMDB_TEST"
        (d / "manifest.json").write_text(json.dumps(m))
    snap = _mutated(tmp_path, "simemr", mutate)
    _expect_refusal(store, reg, snap, "INTAKE-9", "SIMDB", "SIMDB_TEST")


def test_r_keyless_table_refuses_whole_extract(registered, tmp_path):
    store, reg = registered

    def mutate(d):
        rows = (d / "pk.csv").read_text().splitlines()
        keep = [r for r in rows if "STAGING_LOG" not in r]
        (d / "pk.csv").write_text("\n".join(keep) + "\n")
    snap = _mutated(tmp_path, "simemr", mutate)
    _expect_refusal(store, reg, snap, "INTAKE-10", "dbo.STAGING_LOG")


def test_r_fkgroup_quarantines_and_alerts_never_refuses(registered, tmp_path):
    store, reg = registered

    def mutate(d):
        text = (d / "joins.csv").read_text()
        text = text.replace("2,2,dbo,DX_COMMENT,DX_LINE,dbo,ENCOUNTER_DX,LINE",
                            "2,3,dbo,DX_COMMENT,DX_LINE,dbo,ENCOUNTER_DX,LINE")
        (d / "joins.csv").write_text(text)
    snap = _mutated(tmp_path, "simemr", mutate)
    report = inbound.receive_extract(store, reg, snap,
                                     known_packs=KNOWN_PACKS)
    # A14: quarantined + counted + DBA alerted BY NAME; load proceeded
    assert len(report.quarantined_join_groups) == 1
    assert report.dba_alerts and "fk group 2" in report.dba_alerts[0]
    edges = {(e.from_id, e.to_id) for e in store.current_edges("joins_to")}
    assert ("simemr|dbo|DX_COMMENT", "simemr|dbo|ENCOUNTER_DX") not in edges
    assert ("simemr|dbo|ENCOUNTER", "simemr|dbo|PATIENT") in edges


def test_r_orphancol_refused_not_half_created(registered, tmp_path):
    store, reg = registered

    def mutate(d):
        with open(d / "columns.csv", "a") as f:
            f.write('dbo,GHOST,X,"Ghost column."\n')
    snap = _mutated(tmp_path, "simemr", mutate)
    _expect_refusal(store, reg, snap, "LC-C3", "dbo.GHOST.X")


def test_r_mixedschema_refused_at_the_door(registered, tmp_path):
    store, reg = registered

    def mutate(d):
        (d / "tables.csv").write_text(
            'schema,table,description\n'
            'dbo,ORG_SNEAK,"A table in a schema org does not own."\n')
        (d / "columns.csv").write_text(
            'schema,table,column,description\n'
            'dbo,ORG_SNEAK,ID,"Id."\n')
        (d / "pk.csv").write_text("schema,table,column,ordinal\n"
                                  "dbo,ORG_SNEAK,ID,1\n")
        (d / "joins.csv").write_text(
            "fk_num,ordinal,src_schema,src_table,src_column,"
            "dest_schema,dest_table,dest_column\n")
    snap = _mutated(tmp_path, "org", mutate)
    _expect_refusal(store, reg, snap, "INTAKE-8", "dbo", "org")


def test_intake6_illegal_declaration_counted_not_loaded(registered, tmp_path):
    store, reg = registered
    # apply simemr first so the epic-side tables exist
    inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(F1 / "simemr_snapshot"),
        known_packs=KNOWN_PACKS)

    def mutate(d):
        with open(d / "joins.csv", "a") as f:
            f.write("9,1,dbo,STAGING_LOG,LOAD_ID,dbo,PATIENT,PATIENT_ID\n")
    snap = _mutated(tmp_path, "org", mutate)
    report = inbound.receive_extract(store, reg, snap,
                                     known_packs=KNOWN_PACKS)
    assert len(report.illegal_declarations) == 1
    assert "INTAKE-6" in report.illegal_declarations[0]
    edges = {(e.from_id, e.to_id) for e in store.current_edges("joins_to")}
    assert ("simemr|dbo|STAGING_LOG", "simemr|dbo|PATIENT") not in edges


def test_intake7_unknown_pack_version_refused(registered):
    store, reg = registered
    snap = kg1_intake.load_snapshot(F1 / "simemr_snapshot")
    stamp = store.state_stamp()
    with pytest.raises(kg1_intake.Refusal) as exc:
        inbound.receive_extract(store, reg, snap,
                                known_packs={"some-other-pack-9.9"})
    assert exc.value.rule == "INTAKE-7"
    assert "simemr-pack-0.1" in str(exc.value)
    assert store.state_stamp() == stamp


def test_intake0_missing_part_is_a_named_refusal(registered, tmp_path):
    store, reg = registered

    def mutate(d):
        (d / "pk.csv").unlink()
    snap_dir = tmp_path / "simemr_snapshot"
    shutil.copytree(F1 / "simemr_snapshot", snap_dir)
    mutate(snap_dir)
    with pytest.raises(kg1_intake.Refusal) as exc:
        kg1_intake.load_snapshot(snap_dir)
    assert exc.value.rule == "INTAKE-0"
    assert "pk.csv" in str(exc.value)
