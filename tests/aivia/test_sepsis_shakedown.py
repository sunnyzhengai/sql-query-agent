"""The sepsis shakedown (round 2) — conservation counters pinned;
the floors themselves are the HUMAN deliverable (gap_check_report.md,
per the ED-sepsis acceptance law) and pin after Sunny's verdict.
"""
import json
import pathlib

import pytest

from aivia.flows import inbound, produce
from aivia.graph import kg1_intake
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import census, decisions

BASE = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "estates" / "sepsis"
EXPECTED = json.loads((BASE / "expected_shakedown.json").read_text())


@pytest.fixture(scope="module")
def shaken():
    store = Store()
    reg = json.loads((BASE / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    extract = inbound.receive_extract(
        store, reg, kg1_intake.load_snapshot(BASE / "sepsis_snapshot"),
        known_packs={"sepsis-pack-1.2"})
    estate = inbound.receive_estate(store, reg, BASE / "estate_snapshot")
    return store, extract, estate


def test_extract_counters(shaken):
    store, extract, _ = shaken
    want = EXPECTED["extract"]
    assert len(store.current_nodes("table")) == want["tables"]
    assert len(store.current_nodes("column")) == want["columns"]
    assert len(extract.pending_references) == want["pending"]


def test_estate_conservation(shaken):
    _, _, estate = shaken
    want = EXPECTED["estate"]
    assert len(estate.acquired) == want["acquired"]
    assert len(estate.counted_excluded) == want["counted_excluded"]
    for key in ("resolved_refs", "same_tree_refs", "unresolved_refs"):
        assert sum(t["resolution_census"][key]
                   for t in estate.trees.values()) == want[key], key
    assert sum(len(t["remainder"]) for t in estate.trees.values()) \
        == want["remainder_total"]


def test_lens_counters_and_produce_drains(shaken):
    store, _, _ = shaken
    read = ReadApi(store)
    want = EXPECTED["lenses"]
    dec = decisions.lens_decisions(read, {"class": "membership"})
    assert len(dec["yield"]) == want["scopes"]
    assert sum(1 for v in dec["yield"].values() if v) == \
        want["scopes_with_decisions"]
    ws = census.lens_working_set(read, None)
    assert len(ws["yield"]) == want["working_set_touched"]
    assert len(ws["yield"]) + len(ws["not_touched"]) == \
        want["working_set_total"]
    shipped = 0
    while True:
        event = produce.run(store, occurred_at="2026-09-06T00:00:00Z")
        attempted = event.properties["accounting"]["descriptions"][
            "attempted"]
        if attempted == 0:
            break
        shipped += event.properties["accounting"]["descriptions"]["shipped"]
    assert shipped == EXPECTED["produce_total"]
    for d in store.current_nodes("description"):
        assert d.properties["text"].strip()


def test_two_alias_corpse_voices_both_filters(shaken):
    """Sunny's ED-sepsis gap-check, finding 2 (grammar v1.1.0): the
    same table read under two aliases, each filtered EVENT_SUBTYPE_CODE
    <> 2 — TWO decisions about two different events. The floor voices
    BOTH, instance-marked, never merged (dedup at predicate identity,
    not rendered-string, grain)."""
    from aivia.flows import produce as _produce
    store, _, _ = shaken
    floor = _produce.compose_floor(ReadApi(store),
                                   "reporting/USP_ED_SEPSIS.sql::#ADT")
    both = [line for line in floor.splitlines()
            if "modified or removed is not 2" in line]
    assert len(both) == 2
    assert any(line.startswith("- For the first") for line in both)
    assert any(line.startswith("- For the second") for line in both)
