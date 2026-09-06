"""Phase D exit (ADR 0077): the F8 phase-D answer keys go RUNNABLE.

The anchor rule live: certifications ride MEANING identity
(content_key at a scope path), never syntax. PD-1 survival under
syntax-only churn · PD-2 visible orphaning on a truth change · PD-3
deletion orphans with meaning-found candidates (the rename case
resolves itself for the human) · PD-4 the migration equation.
Requires ScriptDom — no fallback (ADR 0001).

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import inbound, produce
from aivia.graph import kg1_intake, kg2_mapper, kg2_translator, kg3_artifacts
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import anchors

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
F1 = FIX / "F1_minimal_estate"
F2 = FIX / "F2_estate_files"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}
T0 = "2026-09-06T00:00:00Z"
T1 = "2026-09-06T01:00:00Z"
VISITS = "usp_diabetic_visits.sql"
RECENT = f"{VISITS}::#Recent"


@pytest.fixture()
def produced():
    store = Store()
    reg = json.loads((F1 / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    for src in ("simemr", "org"):
        inbound.receive_extract(
            store, reg,
            kg1_intake.load_snapshot(F1 / f"{src}_snapshot"),
            known_packs=KNOWN_PACKS)
    inbound.receive_estate(store, reg, F2 / "estate_snapshot")
    produce.run(store, occurred_at=T0)
    return store, reg


def _reapply(store, reg, text, file_name=VISITS):
    manifest = json.loads(
        (F2 / "estate_snapshot" / "manifest.json").read_text())
    tree = kg2_mapper.apply_file(
        store, reg, file_id=f"{manifest['location']}{file_name}",
        file_name=file_name, text=text, as_of=T1,
        default_schema=manifest.get("default_schema"))
    kg2_translator.apply_twin(store, f"{manifest['location']}{file_name}",
                              tree, T1)
    return tree


def _source_text():
    return (F2 / "estate_snapshot" / VISITS).read_text()


def test_pd4_migration_equation(produced):
    store, _ = produced
    # strip anchors to simulate the pre-Phase-D estate
    for v in store.current_nodes("description"):
        v.properties.pop("anchor", None)
    read = ReadApi(store)
    report = kg3_artifacts.migrate_anchors(
        store, anchors.selection_keys(read), T1)
    assert report["candidates"] == 4
    assert report["migrated"] + len(report["orphaned"]) \
        + len(report["human_held"]) == report["candidates"]
    assert report["migrated"] == 4 and not report["orphaned"]
    census = anchors.lens_anchor_census(ReadApi(store), None)["yield"]
    assert len(census["intact"]) == 4
    assert not census["unanchored"]


def test_produce_anchors_at_write_time(produced):
    store, _ = produced
    for v in store.current_nodes("description"):
        anchor = v.properties.get("anchor")
        assert anchor and anchor["scope"] == v.properties["about"][0]
        assert anchor["content_key"]


def test_pd1_certification_survives_syntax_churn(produced):
    store, reg = produced
    kg3_artifacts.append_disposition(
        store, about=f"description:{RECENT}", ruling="accept",
        author="person:sunny", occurred_at=T0)
    twins_before = len(store.current_nodes("meaning_twin"))
    reformatted = _source_text().replace("SELECT", "SELECT\n  ") \
                                .replace(" AND ", "\n    AND ")
    _reapply(store, reg, reformatted)
    census = anchors.lens_anchor_census(ReadApi(store), None)["yield"]
    assert RECENT in census["intact"]          # survives SILENTLY
    assert not census["drift_orphans"]
    # idempotent at the meaning grain: no new twin version either
    assert len(store.current_nodes("meaning_twin")) == twins_before
    dispositions = store.current_nodes("disposition")
    assert any(d.properties["about"] == f"description:{RECENT}"
               for d in dispositions)          # the human act stands


def test_pd2_truth_change_orphans_visibly(produced):
    store, reg = produced
    changed = _source_text().replace("APPT_STATUS_C = 2",
                                     "APPT_STATUS_C = 3")
    assert changed != _source_text()
    _reapply(store, reg, changed)
    census = anchors.lens_anchor_census(ReadApi(store), None)["yield"]
    assert RECENT in census["drift_orphans"]   # flagged, never silent
    # the artifact is never deleted and never silently re-attached
    assert any(v.properties["about"] == [RECENT]
               for v in store.current_nodes("description"))


def test_pd3_deleted_scope_orphans_with_meaning_candidates(produced):
    store, reg = produced
    renamed = _source_text().replace("#Recent", "#Fresh")
    _reapply(store, reg, renamed)
    census = anchors.lens_anchor_census(ReadApi(store), None)["yield"]
    orphan = next(o for o in census["deleted_orphans"]
                  if o["scope"] == RECENT)
    # the rename case resolves itself: the SAME MEANING under the new
    # name is the candidate — found by content_key, not by name
    assert f"{VISITS}::#Fresh" in orphan["candidates"]
