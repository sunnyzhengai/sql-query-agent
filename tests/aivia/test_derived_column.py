"""M4 THE DERIVED-COLUMN LAYER — structural pins on the F2 fixture
estate (authored BEFORE the builder; test-first law).

F2's three files are ALL passthrough projections — the sealed M4
census law says passthroughs are NEVER nodes, so the fixture estate
must mint ZERO derived_column nodes while the machinery is live.
The positive pins (156 nodes, cites, voicings) live in
AIVIA_Test/test_ed_sepsis_dev_estate.py against the dev estate —
the acceptance surface.

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake
from aivia.graph.store import Store

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


@pytest.fixture(scope="module")
def built():
    store = Store()
    reg = json.loads((FIX / "F1_minimal_estate" / "registration.json")
                     .read_text())
    kg1_intake.apply_registration(store, reg)
    for src in ("simemr", "org"):
        inbound.receive_extract(
            store, reg,
            kg1_intake.load_snapshot(FIX / "F1_minimal_estate"
                                     / f"{src}_snapshot"),
            known_packs=KNOWN_PACKS)
    report = inbound.receive_estate(
        store, reg, FIX / "F2_estate_files" / "estate_snapshot")
    return store, report


def test_passthroughs_are_never_nodes(built):
    store, report = built
    assert store.current_nodes("derived_column") == []
    layer = report.derived_layer
    assert layer["derived_columns"] == 0
    assert layer["passthrough_skipped"] > 0
    assert layer["cites"] > 0  # outputs still cite their columns


def test_cites_reach_only_dictionary_columns(built):
    store, _ = built
    cols = {n.identity for n in store.current_nodes("column")}
    scopes = {n.identity for n in store.current_nodes("scope")}
    cites = [e for e in store.current_edges("cites")]
    assert cites, "the F2 outputs cite their source columns"
    for e in cites:
        assert e.from_id in scopes
        assert e.to_id in cols
        assert e.to_id.count("|") == 3


def test_rebooting_is_idempotent(built):
    store, _ = built
    before = len(store.current_edges("cites"))
    layer = inbound._store_derived_column_layer(
        store, "2026-09-16T00:00:00Z")
    assert layer["derived_columns"] == 0
    assert len(store.current_edges("cites")) == before


def test_no_unlisted_operations_in_the_fixture(built):
    _, report = built
    assert report.derived_layer["function_remainders"] == {}
