"""Slice 6 exit: the F5 script against the BUILT approve/land flows.

Maria accepts the #Recent description; admin confirms one send to
catalog_a; the bridge observes it published. Every derived state and
refusal F5 authors must hold: certification-without-edit ownership,
dispositions-only surface, A15-bound headers with zero custom
attributes, the attribution prefix, sent-before-transport ordering,
anti-repeat via the current-outcome lens, append-only observations.

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import approve, inbound, land, materialize, produce
from aivia.graph import kg1_intake, kg3_artifacts
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import census, derivation

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}
T0 = "2026-09-05T12:00:00Z"
RECENT = "description:usp_diabetic_visits.sql::#Recent"


def _produced_store():
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
    produce.run(store, occurred_at=T0)
    return store


@pytest.fixture()
def approved():
    store = _produced_store()
    approve.rule(store, about=RECENT, ruling="accept",
                 author="person:maria", occurred_at=T0)
    return store


# ---- approve (F5 derived_after_approve) ----
def test_queue_is_a_lens_rendering():
    store = _produced_store()
    q = approve.queue(ReadApi(store))
    assert RECENT in q["pending"]
    assert q["pending"][RECENT]["ownership"] == "machine"
    assert "stamp" in q


def test_derived_after_approve(approved):
    read = ReadApi(approved)
    assert derivation.lens_standing(read, None)["yield"][RECENT] \
        == "accepted"
    # ownership human via the accepting disposition, though every
    # version is machine-authored (certification without edit)
    assert derivation.lens_ownership(read, None)["yield"][RECENT] == "human"


def test_approve_surface_writes_dispositions_only(approved):
    """APPR-1 behaviorally: the rule() call adds the disposition and
    NOTHING ELSE of content — plus, since step 3 (the birth-edge
    law), the actor's own node on first act."""
    store = _produced_store()
    before = store.state_stamp()
    approve.rule(store, about=RECENT, ruling="accept",
                 author="person:maria", occurred_at=T0)
    after = store.state_stamp()
    assert after[0] - before[0] == 2  # disposition + minted actor
    assert len(store.current_nodes("disposition")) == 1
    assert [n.identity for n in store.current_nodes("person")] \
        == ["person:maria"]


def test_agent_ruling_refused_through_the_surface():
    store = _produced_store()
    with pytest.raises(kg3_artifacts.RefusalKG3):
        approve.rule(store, about=RECENT, ruling="accept",
                     author="agent:produce", occurred_at=T0)


# ---- land (F5 land_script + derived_after_land) ----
def test_render_native_columns_only_with_prefix(approved):
    payload = land.render(ReadApi(approved), RECENT, "catalog_a")
    binding = land.HEADERS["targets"]["catalog_a"]["description"]
    assert list(payload) == binding["columns"]  # LAND-4, order included
    assert payload["Name"] == "#Recent"
    assert payload["Full Name"] == "usp_diabetic_visits.sql::#Recent"
    assert payload["Description"].startswith("AIVIA agent generated: ")
    assert payload["Stewards"] == "person:maria"


def test_send_orders_sent_event_before_transport(approved):
    order = []

    def transport(payload):
        order.append(("transport",
                      len(approved.current_nodes("proposal"))))
        return "receipt-1"
    sent, receipt = land.send(approved, ReadApi(approved), RECENT,
                              "catalog_a", "person:admin", transport)
    assert receipt == "receipt-1"
    # at transport time the sent event ALREADY existed (LAND-3)
    assert order == [("transport", 1)]
    assert sent.properties["author"] == "person:admin"
    assert sent.properties["about"] == RECENT  # the accepted version


def test_send_refusals_land1(approved):
    store = _produced_store()  # nothing accepted here
    with pytest.raises(land.LandRefusal) as exc:
        land.send(store, ReadApi(store), RECENT, "catalog_a",
                  "person:admin", lambda p: None)
    assert exc.value.rule == "LAND-1"
    with pytest.raises(land.LandRefusal) as exc:  # agent confirmation
        land.send(approved, ReadApi(approved), RECENT, "catalog_a",
                  "agent:bridge", lambda p: None)
    assert exc.value.rule == "LAND-1"


def test_observe_then_anti_repeat(approved):
    sent, _ = land.send(approved, ReadApi(approved), RECENT, "catalog_a",
                        "person:admin", lambda p: "ok")
    land.observe(approved, sent.identity, "published",
                 author="agent:bridge", occurred_at=T0)
    read = ReadApi(approved)
    assert derivation.lens_current_outcome(read, None)["yield"][
        sent.identity] == "published"
    # a later denial flips the current outcome; re-send then refuses
    land.observe(approved, sent.identity, "denied",
                 author="agent:bridge", occurred_at=T0)
    with pytest.raises(land.LandRefusal) as exc:
        land.send(approved, ReadApi(approved), RECENT, "catalog_a",
                  "person:admin", lambda p: "ok")
    assert exc.value.rule == "LAND-2"
    # a NEW version clears the anti-repeat (it is a different send)
    kg3_artifacts.append_description(
        approved, artifact_id=RECENT,
        about=["usp_diabetic_visits.sql::#Recent"], text="Maria rewrote.",
        status=None, author="person:maria", basis=None, created_at=T0)
    sent2, _ = land.send(approved, ReadApi(approved), RECENT, "catalog_a",
                         "person:admin", lambda p: "ok")
    assert sent2.properties["about"] != RECENT  # the new version id


def test_unbound_target_refused(approved):
    with pytest.raises(land.LandRefusal) as exc:
        land.render(ReadApi(approved), RECENT, "catalog_zz")
    assert exc.value.rule == "A15"


# ---- materialize (OPS-1) ----
def test_materialize_lands_stamped_regenerable_surface(approved):
    read = ReadApi(approved)
    surface = materialize.run(approved, read, "gap-census", T0)
    direct = census.lens_gap_census(read, None)
    assert surface["result"]["grain_not_declared"] == \
        direct["grain_not_declared"]
    assert surface["graph_stamp"]
    nodes = approved.current_nodes("report_surface")
    assert len(nodes) == 1 and nodes[0].identity == "surface:gap-census"
    materialize.run(approved, ReadApi(approved), "gap-census", T0)
    assert len(approved.current_nodes("report_surface")) == 1  # replaced
    with pytest.raises(KeyError):
        materialize.run(approved, read, "not-a-lens", T0)
