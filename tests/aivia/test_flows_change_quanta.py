"""The flows' change quanta (CONTRACT_DATALOAD §13 + the flows
registry sheet; the last ruled-not-built flow machinery): KG1 intake
goes INCREMENTAL by object hash (INTAKE-11/12/13) with §11 retire;
KG2 skips unchanged files at the file quantum, re-resolving without
re-parsing on a KG1 ripple. Total reload survives only as the RULE
path (version bumps) and as INTAKE-12's mechanical equivalence audit.

Proves: contract:aivia-design-to-code
"""
import json
import pathlib
import shutil

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake
from aivia.graph.store import Store

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
F1 = FIX / "F1_minimal_estate"
F2 = FIX / "F2_estate_files"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


def _snapshot_copy(tmp_path, as_of="2026-09-07T00:00:00Z"):
    dst = tmp_path / "simemr_snapshot"
    shutil.copytree(F1 / "simemr_snapshot", dst)
    manifest = json.loads((dst / "manifest.json").read_text())
    manifest["as_of"] = as_of
    (dst / "manifest.json").write_text(json.dumps(manifest))
    return dst


@pytest.fixture()
def loaded():
    store = Store()
    reg = json.loads((F1 / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    for src in ("simemr", "org"):
        inbound.receive_extract(
            store, reg,
            kg1_intake.load_snapshot(F1 / f"{src}_snapshot"),
            known_packs=KNOWN_PACKS)
    return store, reg


def test_intake_13_unchanged_extract_writes_nothing(loaded, tmp_path):
    store, reg = loaded
    before = len(store._nodes)
    snap = kg1_intake.load_snapshot(_snapshot_copy(tmp_path))
    report = inbound.receive_extract(store, reg, snap,
                                     known_packs=KNOWN_PACKS)
    assert report.changed_objects == []      # a NEW as_of, ZERO writes
    assert report.retired_objects == []
    assert len(store._nodes) == before
    assert report.check_outcomes["INTAKE-13"].startswith("pass (0 ")


def test_object_grain_change_supersedes_exactly_one(loaded, tmp_path):
    store, reg = loaded
    dst = _snapshot_copy(tmp_path)
    cols = (dst / "columns.csv").read_text().splitlines()
    target = cols[1].split(",")
    target[-1] = '"An amended description for the change-quanta test."'
    cols[1] = ",".join(target)
    (dst / "columns.csv").write_text("\n".join(cols) + "\n")
    report = inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(dst),
        known_packs=KNOWN_PACKS)
    assert len(report.changed_objects) == 1  # the staleness feed
    identity = report.changed_objects[0]
    versions = [n for n in store._nodes if n.identity == identity]
    assert len(versions) == 2                # superseded, never edited
    assert versions[0].valid_to is not None


def test_section_11_retire_on_absence(loaded, tmp_path):
    store, reg = loaded
    dst = _snapshot_copy(tmp_path)
    tables = (dst / "tables.csv").read_text().splitlines()
    dropped = tables.pop()                    # drop the last table
    name = dropped.split(",")[1]
    for f in ("columns.csv", "pk.csv"):
        rows = [r for r in (dst / f).read_text().splitlines()
                if f",{name}," not in r]
        (dst / f).write_text("\n".join(rows) + "\n")
    (dst / "tables.csv").write_text("\n".join(tables) + "\n")
    report = inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(dst),
        known_packs=KNOWN_PACKS)
    assert any(name in r for r in report.retired_objects)
    current = {n.identity for n in store.current_nodes("table")}
    assert not any(name in i for i in current)   # marked, not current
    everything = {n.identity for n in store.current_nodes.__self__
                  ._nodes if n.label == "table"}
    assert any(name in i for i in everything)    # never removed


def test_intake_12_equivalence_audit(loaded):
    store, reg = loaded
    snap = kg1_intake.load_snapshot(F1 / "simemr_snapshot")
    assert kg1_intake.audit_incremental(store, reg, snap) == []
    # inject divergence: corrupt one live hash — the audit must name it
    victim = store.current_nodes("column")[0]
    victim.properties["content_hash"] = "poisoned"
    findings = kg1_intake.audit_incremental(store, reg, snap)
    assert len(findings) == 1
    assert victim.identity in findings[0]
    assert findings[0].startswith("INTAKE-12:")


def test_file_quantum_skips_unchanged_estate(loaded):
    store, reg = loaded
    first = inbound.receive_estate(store, reg, F2 / "estate_snapshot")
    assert first.reused == []
    nodes_before = len(store._nodes)
    second = inbound.receive_estate(store, reg, F2 / "estate_snapshot")
    assert sorted(second.reused) == sorted(second.acquired)
    assert len(store._nodes) == nodes_before  # no parse, no writes
    assert second.twins.keys() == first.twins.keys()


def test_kg1_ripple_reresolves_without_reparse(loaded):
    store, reg = loaded
    inbound.receive_estate(store, reg, F2 / "estate_snapshot")
    nodes_before = len(store._nodes)
    # a ripple naming an uncited object: files re-RESOLVE (no skip)
    # but nothing changes, so idempotence holds — zero new versions
    report = inbound.receive_estate(
        store, reg, F2 / "estate_snapshot",
        kg1_changed={"simemr|dbo|NOT_A_REAL|COLUMN"})
    assert len(store._nodes) == nodes_before
    assert sorted(report.reused) == sorted(report.acquired)
