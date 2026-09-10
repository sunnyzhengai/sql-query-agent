"""Slice 5 exit: produce vs the RATIFIED floor grammar — F4 upgraded
to byte-exact (A13 closed 2026-09-05).

Every produced description must equal floor_texts.json exactly; the
run event is the only production ledger (PROD-1) with the F4-expected
accounting; the worklist is the staleness lens (PROD-2 — and a second
run finds nothing stale, producing NO noise); gate outcomes stay in
the closed vocabulary (PROD-3); human-owned artifacts render proposed,
never current (PROD-4, via A6); replay: two fresh builds produce
identical floors (PROD-5).

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import gates, inbound, produce
from aivia.graph import kg1_intake, kg3_artifacts
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import derivation

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}
T0 = "2026-09-05T12:00:00Z"
PAYLOAD = json.loads((FIX / "F4_produce" / "floor_texts.json").read_text())
F4 = json.loads((FIX / "F4_produce" / "expected_produce.json").read_text())


def _build():
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
    inbound.receive_estate(store, reg,
                           FIX / "F2_estate_files" / "estate_snapshot")
    return store


@pytest.fixture(scope="module")
def produced():
    store = _build()
    event = produce.run(store, occurred_at=T0)
    return store, event


def test_floor_texts_byte_exact(produced):
    """THE F4 upgrade: acceptance is byte-for-byte the ratified payload."""
    store, _ = produced
    descs = {d.properties["about"][0]: d.properties["description"]
             for d in store.current_nodes("description")}
    assert descs == PAYLOAD["texts"]


def test_statuses_in_gate_vocab_and_floor_shipped(produced):
    store, _ = produced
    for d in store.current_nodes("description"):
        target = d.properties["about"][0]
        assert d.properties["status"] in \
            F4["targets"][target]["gate_outcome_allowed"]
        assert d.properties["status"] == "skeleton_floor"  # no model ran


def test_run_event_matches_f4_accounting(produced):
    _, event = produced
    want = F4["run_event_expected"]["accounting_per_class"]["descriptions"]
    got = event.properties["accounting"]["descriptions"]
    assert got["attempted"] == want["attempted"] == 4
    assert got["shipped"] == want["shipped"] == 4
    assert got["absent"] == want["absent"] == 0
    assert got["killed_lines"] == 0
    assert event.properties["accounting"]["terms"]["attempted"] == 0
    assert event.properties["author"] == "agent:produce"
    assert event.properties["outcome"] == "completed"
    assert event.properties["basis"]["floor_grammar"] == "2.3.0"
    assert set(event.properties["basis"]["worklist"]) == set(F4["targets"])


def test_prod2_second_run_produces_no_noise(produced):
    store, _ = produced
    assert derivation.lens_staleness(ReadApi(store), None)["yield"] == []
    event = produce.run(store, occurred_at=T0)
    assert event.properties["accounting"]["descriptions"]["attempted"] == 0
    assert len(store.current_nodes("description")) == 4  # nothing re-shipped


def test_prod4_human_owned_never_overwritten(produced):
    store, _ = produced
    target = "usp_diabetic_visits.sql::#Recent"
    kg3_artifacts.append_description(
        store, artifact_id=f"description:{target}", about=[target],
        text="Maria's own words.", status=None, author="person:maria",
        basis=None, created_at=T0)
    # simulate a later machine append (what a staleness-triggered
    # produce would do): current must STAY the human version (A6)
    kg3_artifacts.append_description(
        store, artifact_id=f"description:{target}", about=[target],
        text="Machine again.", status="skeleton_floor",
        author="agent:produce", basis={"floor_grammar": "1.0.0"},
        created_at=T0)
    current = derivation.lens_current(ReadApi(store), None)["yield"][
        f"description:{target}"]
    assert current["description"] == "Maria's own words."


def test_prod5_replay_two_fresh_builds_identical():
    floors_a = {t: produce.compose_floor(ReadApi(_build()), t)
                for t in PAYLOAD["texts"]}
    floors_b = {t: produce.compose_floor(ReadApi(_build()), t)
                for t in PAYLOAD["texts"]}
    assert floors_a == floors_b == PAYLOAD["texts"]


def test_smoothed_path_gate_passes_clean_rephrase():
    store = _build()
    def smooth(floor):
        return floor.replace("This is a selection of patients.",
                             "Selects patients.")
    produce.run(store, occurred_at=T0, smooth=smooth)
    descs = {d.properties["about"][0]: d for d in
             store.current_nodes("description")}
    odd = descs["usp_odd_join.sql::delivery"]
    assert odd.properties["status"] == "gate_passed"
    assert odd.properties["description"].startswith("Selects patients.")


def test_smoothed_path_violation_ships_the_floor():
    store = _build()
    def smooth(floor):
        return floor + "\n- Also, status 3 ('Canceled') rows are dropped."
    event = produce.run(store, occurred_at=T0, smooth=smooth)
    for d in store.current_nodes("description"):
        assert d.properties["status"] == "skeleton_floor"
        assert "Canceled" not in d.properties["description"]  # the floor shipped
    killed = event.properties["accounting"]["descriptions"]["killed_lines"]
    assert killed > 0  # counted, never silent


def test_gate_injection_cases():
    floor = ("This is a selection of patient encounters.\n"
             "- The appointment status is 2 ('Completed').")
    forbidden = ["ENCOUNTER", "APPT_STATUS_C", "E.APPT_STATUS_C"]
    assert gates.check_text(floor, floor, forbidden) == []
    dropped = gates.check_text(
        "This is a selection of patient encounters.", floor, forbidden)
    assert any("dropped" in v for v in dropped)
    added = gates.check_text(floor + " Also 99.", floor, forbidden)
    assert any("added" in v for v in added)
    leaked = gates.check_text(
        floor.replace("appointment status", "APPT_STATUS_C"),
        floor, forbidden)
    assert any("raw identifier" in v for v in leaked)
    assert any("empty" in v for v in gates.check_text("  ", "", []))


def test_econ_params_are_declared_data(monkeypatch):
    assert produce.ECON["version"] == "econ-v1"
    assert produce.ECON["batch_size"] == 50
    assert produce.ECON["run_budget"] == 500
    assert produce.ECON["priority"] == "usage-weighted"
    store = _build()
    monkeypatch.setitem(produce.ECON, "batch_size", 2)
    event = produce.run(store, occurred_at=T0)
    assert event.properties["accounting"]["descriptions"]["attempted"] == 2
    assert len(store.current_nodes("description")) == 2  # the batch paced
