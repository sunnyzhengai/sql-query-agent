"""The sepsis shakedown (round 2) — conservation counters pinned;
the floors themselves are the HUMAN deliverable (gap_check_report.md,
per the ED-sepsis acceptance law) and pin after Sunny's verdict.

Proves: contract:aivia-design-to-code
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


def test_twin_conservation(shaken):
    """Phase B (ADR 0077): the meaning twin over the whole corpus —
    homomorphism already asserted inside translate() per file; here
    the corpus-wide census pins and the stored twins count."""
    store, _, estate = shaken
    want = EXPECTED["twin"]
    totals = {k: sum(t["census"][k] for t in estate.twins.values())
              for k in ("twin_nodes", "translated", "gaps",
                        "degenerate", "coverage_gaps")}
    for key, value in totals.items():
        assert value == want[key], key
    assert totals["translated"] + totals["gaps"] == totals["twin_nodes"]
    assert len(store.current_nodes("meaning_twin")) \
        == want["stored_twins"]


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


def test_r8_annotations_attributed_never_bare(shaken):
    """Sunny's gap-check finding 1, tier 3 (grammar v1.2.0): trailing
    comments voice WITH attribution — predicate-level and IN-member-
    level — never as bare fact."""
    from aivia.flows import produce as _produce
    store, _, _ = shaken
    floor = _produce.compose_floor(ReadApi(store),
                                   "reporting/USP_ED_SEPSIS.sql::#ADT")
    assert "(annotated 'TRANSFER OUT' in the source)" in floor
    assert "(annotated 'TRANSFER IN' in the source)" in floor
    assert "200108022 (annotated 'Emergency' in the source)" in floor
    assert "200108015 (noted 'MAIN 95 TOWER EAST')" in floor
    assert "TRANSFER OUT." not in floor  # attributed, never bare fact


def test_bpa_corpse_on_clause_filter_is_membership(shaken):
    """Sunny's gap-check finding 3 (grammar v1.3.0): a col=literal
    filter riding an INNER JOIN's ON clause is MEMBERSHIP — the old
    build over-applied the join-key exclusion to the whole ON clause.
    OUTER-join residues stay out (match conditions) and are counted."""
    from aivia.flows import produce as _produce
    from aivia.lenses import census as _census
    store, _, _ = shaken
    floor = _produce.compose_floor(ReadApi(store),
                                   "reporting/USP_ED_SEPSIS.sql::#BPA")
    assert "'900130001'" in floor  # the recovered ON-clause filter
    gc = _census.lens_gap_census(ReadApi(store), None)
    assert gc["outer_join_conditions_not_voiced"] == 87  # counted, declared


def test_r5_phrasing_corpses(shaken):
    """v1.3.1: the two rendering corpses from Sunny's gap-check —
    token-head glue ('...it became effective id') and boilerplate
    leakage ('the best practice alert this') — never regress."""
    from aivia.flows import produce as _produce
    store, _, _ = shaken
    adt = _produce.compose_floor(ReadApi(store),
                                 "reporting/USP_ED_SEPSIS.sql::#ADT")
    assert "effective id" not in adt
    assert ("the unit associated with the event record at the time "
            "it became effective is one of the values 200108022") in adt
    bpa = _produce.compose_floor(ReadApi(store),
                                 "reporting/USP_ED_SEPSIS.sql::#BPA")
    assert "alert this" not in bpa
    assert "'900130001'" in bpa
