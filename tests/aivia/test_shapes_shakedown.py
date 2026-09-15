"""The shapes shakedown — the engine over the 38-file ADR 0055 corpus,
pinned to the authored answer key (expected_shakedown.json).

This is round 1 of the real-estate program: the SYNTHETIC corpus does
the mechanical job (scale, conservation counters, pacing); the ED
sepsis suite does the truth job (Sunny's gap-check) in round 2. Every
counter here recomputes from a fresh build — drift in the mapper, the
resolver, the gate, or the pack fails this suite by number.

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import inbound, produce
from aivia.graph import kg1_intake
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import census, compliance, decisions, derivation

BASE = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "estates" / "shapes"
EXPECTED = json.loads((BASE / "expected_shakedown.json").read_text())
T0 = "2026-09-06T00:00:00Z"


@pytest.fixture(scope="module")
def shaken():
    store = Store()
    reg = json.loads((BASE / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    extract = inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(BASE / "shapes_snapshot"),
        known_packs={"shapes-pack-1.1"})
    estate = inbound.receive_estate(store, reg, BASE / "estate_snapshot")
    return store, extract, estate


def test_extract_counters(shaken):
    store, extract, _ = shaken
    want = EXPECTED["extract"]
    assert len(store.current_nodes("table")) == want["tables"]
    assert len(store.current_nodes("column")) == want["columns"]
    assert len(extract.quarantined_join_groups) == want["quarantined"]
    assert len(extract.illegal_declarations) == want["illegal"]
    assert len(extract.pending_references) == want["pending"]


def test_data_type_rides_the_extract(shaken):
    """Pack 1.1 (contract §2b): the synthetic vendor's seed DDL
    declares every palette column, so every column node carries its
    declared type — verbatim, none empty."""
    store, _, _ = shaken
    cols = store.current_nodes("column")
    assert cols and all(
        c.properties.get("data_type", "").strip() for c in cols)


def test_estate_conservation_counters(shaken):
    _, _, estate = shaken
    want = EXPECTED["estate"]
    assert len(estate.acquired) == want["acquired"]
    assert len(estate.counted_excluded) == want["counted_excluded"]
    census_totals = {
        "resolved_refs": sum(t["resolution_census"]["resolved_refs"]
                             for t in estate.trees.values()),
        "same_tree_refs": sum(t["resolution_census"]["same_tree_refs"]
                              for t in estate.trees.values()),
        "unresolved_refs": sum(t["resolution_census"]["unresolved_refs"]
                               for t in estate.trees.values())}
    for key, value in census_totals.items():
        assert value == want[key], key
    assert sum(t["phi_redactions"] for t in estate.trees.values()) \
        == want["phi_redactions"]
    kinds = {}
    for t in estate.trees.values():
        for r in t["remainder"]:
            kinds[r["type"]] = kinds.get(r["type"], 0) + 1
    assert kinds == want["remainder_types"]
    assert sum(kinds.values()) == want["remainder_total"]


def test_lens_counters(shaken):
    store, _, _ = shaken
    read = ReadApi(store)
    want = EXPECTED["lenses"]
    ws = census.lens_working_set(read, None)
    assert len(ws["yield"]) == want["working_set_touched"]
    assert len(ws["yield"]) + len(ws["not_touched"]) == \
        want["working_set_total"]
    assert [t.split("|")[-1] for t in ws["not_touched"]] == \
        want["untouched"]
    jc = compliance.lens_join_compliance(read, None)
    assert len(jc["violations"]) == want["compliance_violations"]
    assert jc["violations"][0]["practiced"] == want["violation_practiced"]
    assert len(jc["compliant_practiced"]) == want["compliance_compliant"]
    assert len(jc["not_judged"]) == want["compliance_not_judged"]
    dec = decisions.lens_decisions(read, {"class": "membership"})
    assert len(dec["yield"]) == want["scopes"]
    assert sum(1 for v in dec["yield"].values() if v) == \
        want["scopes_with_decisions"]
    assert len(decisions.lens_degenerate(read, None)["yield"]) == \
        want["degenerate"]
    gc = census.lens_gap_census(read, None)
    assert gc["grain_not_declared"] == want["grain_not_declared"]
    assert gc["unresolved_refs"] == []


def test_econ_pacing_drains_the_worklist(shaken):
    store, _, _ = shaken
    waves = []
    for _ in EXPECTED["produce_waves"]:
        event = produce.run(store, occurred_at=T0)
        waves.append(
            event.properties["accounting"]["descriptions"]["attempted"])
    assert waves == EXPECTED["produce_waves"]
    assert derivation.lens_staleness(ReadApi(store), None)["yield"] == []
    descs = store.current_nodes("description")
    assert len(descs) == EXPECTED["lenses"]["scopes"]
    for d in descs:  # every floor grounded, none empty, all statused
        assert d.properties["description"].strip()
        assert d.properties["status"] == "skeleton_floor"
