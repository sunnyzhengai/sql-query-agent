"""Slice 4: the ledger — KG3 artifact layer lifecycle + derived states.

The fixture families from the ratified registry: ownership flip
(including F5's certification-without-edit branch), disagreement (two
rulers, names shown, no winner), succession (version = chain depth,
derived), plus the structural laws: no retire path EXISTS, events
refuse supersede, empty shells refused, machine versions carry basis,
dispositions are HUMAN-ONLY (LC3-C3), usage events obey H5/A5, and
redaction is the ONE destruction path — human-ruled, tombstoned.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.graph import kg3_artifacts as kg3
from aivia.graph import kg4_concepts as kg4
from aivia.graph import metamodel
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import derivation

T0 = "2026-09-05T00:00:00Z"
SCOPE = "usp_diabetic_visits.sql::#Recent"
BASIS = {"model": "m-1", "prompt": "p-1", "lens": "l-1", "metamodel": "1.0.0",
         "tree_version": "t-1"}


def _machine_desc(store, n=1, artifact="desc:recent"):
    last = None
    for i in range(n):
        last = kg3.append_description(
            store, artifact_id=artifact, about=[SCOPE],
            text=f"Machine text v{i + 1}.", status="gate_passed",
            author="agent:produce", basis=BASIS, created_at=T0)
    return last


# ---- ownership flip family ----
def test_machine_chain_is_machine_owned():
    store = Store()
    _machine_desc(store, n=2)
    read = ReadApi(store)
    assert derivation.lens_ownership(read, None)["yield"]["desc:recent"] \
        == "machine"


def test_human_edit_flips_ownership_and_pins_current():
    store = Store()
    _machine_desc(store, n=1)
    kg3.append_description(store, artifact_id="desc:recent", about=[SCOPE],
                           text="Human text.", status=None,
                           author="person:maria", basis=None, created_at=T0)
    m3 = _machine_desc(store, n=1)  # pipeline appends AFTER the human
    read = ReadApi(store)
    assert derivation.lens_ownership(read, None)["yield"]["desc:recent"] \
        == "human"
    # LC3-S2: the machine append renders PROPOSED, never current (A6)
    current = derivation.lens_current(read, None)["yield"]["desc:recent"]
    assert "Human text." in current["description"]
    # ...until a human accepts the proposed version (A6 witness)
    kg3.append_disposition(store, about=m3.identity, ruling="accept",
                           author="person:maria", occurred_at=T0)
    current = derivation.lens_current(ReadApi(store), None)["yield"][
        "desc:recent"]
    assert current["version_id"] == m3.identity


def test_certification_without_edit_flips_ownership():
    """F5's branch: every version machine-authored, ownership flips
    HUMAN via the accepting disposition alone."""
    store = Store()
    _machine_desc(store, n=1)
    kg3.append_disposition(store, about="desc:recent", ruling="accept",
                           author="person:maria", occurred_at=T0)
    read = ReadApi(store)
    assert derivation.lens_ownership(read, None)["yield"]["desc:recent"] \
        == "human"
    assert derivation.lens_standing(read, None)["yield"]["desc:recent"] \
        == "accepted"


# ---- disagreement family ----
def test_two_rulers_conflicting_is_disagreement_with_names():
    store = Store()
    _machine_desc(store)
    kg3.append_disposition(store, about="desc:recent", ruling="accept",
                           author="person:maria", occurred_at=T0)
    kg3.append_disposition(store, about="desc:recent", ruling="reject",
                           author="person:bob", occurred_at=T0)
    standing = derivation.lens_standing(ReadApi(store), None)["yield"][
        "desc:recent"]
    assert standing.startswith("disagreement")
    assert "person:maria" in standing and "person:bob" in standing


def test_one_ruler_changing_their_mind_is_not_disagreement():
    store = Store()
    _machine_desc(store)
    kg3.append_disposition(store, about="desc:recent", ruling="accept",
                           author="person:maria", occurred_at=T0)
    kg3.append_disposition(store, about="desc:recent", ruling="revoke",
                           author="person:maria", occurred_at=T0)
    assert derivation.lens_standing(ReadApi(store), None)["yield"][
        "desc:recent"] == "revoked"


# ---- succession family ----
def test_version_is_chain_depth_derived():
    store = Store()
    _machine_desc(store, n=3)
    read = ReadApi(store)
    versions = derivation.lens_version(read, None)["yield"]
    assert versions["desc:recent"] == 3
    supersedes = read.edges("supersedes")
    assert len(supersedes) == 2  # v3->v2, v2->v1, nothing edited in place


# ---- structural laws ----
def test_no_retire_path_exists_in_the_layer():
    assert not any("retire" in name.lower() for name in dir(kg3)), \
        "LC3-R1: ending is done BY WRITING, the retire action must not exist"


def test_events_refuse_supersede():
    store = Store()
    d = kg3.append_disposition(store, about="desc:x", ruling="accept",
                               author="person:maria", occurred_at=T0)
    with pytest.raises(kg3.RefusalKG3) as exc:
        kg3.supersede(store, d.identity, {"ruling": "reject"},
                      author="person:maria", created_at=T0)
    assert "event" in str(exc.value)


def test_empty_shell_refused():
    store = Store()
    with pytest.raises(kg3.RefusalKG3) as exc:
        kg3.append_description(store, artifact_id="desc:x", about=[SCOPE],
                               text="   ", status="gate_passed",
                               author="agent:produce", basis=BASIS,
                               created_at=T0)
    assert "LC3-F5" in str(exc.value)


def test_machine_version_without_basis_refused():
    store = Store()
    with pytest.raises(kg3.RefusalKG3) as exc:
        kg3.append_description(store, artifact_id="desc:x", about=[SCOPE],
                               text="t", status="gate_passed",
                               author="agent:produce", basis=None,
                               created_at=T0)
    assert "basis" in str(exc.value)


def test_agent_disposition_refused_lc3_c3():
    store = Store()
    with pytest.raises(kg3.RefusalKG3) as exc:
        kg3.append_disposition(store, about="desc:x", ruling="accept",
                               author="agent:produce", occurred_at=T0)
    assert "LC3-C3" in str(exc.value)


# ---- usage events (H5 / A5) ----
def test_asked_no_match_carries_outcome_and_no_about():
    store = Store()
    e = kg3.append_usage(store, action="asked", outcome="no-match",
                         payload="patient MRN 12345678 twice?",
                         author="person:ana", occurred_at=T0)
    assert e.properties["outcome"] == "no-match"
    assert "about" not in e.properties
    assert "<ID>" in e.properties["payload"]  # door 2 ran
    with pytest.raises(kg3.RefusalKG3):
        kg3.append_usage(store, action="asked", outcome="no-match",
                         about=SCOPE, payload="x", author="person:ana",
                         occurred_at=T0)


def test_asked_matched_takes_about():
    store = Store()
    e = kg3.append_usage(store, action="asked", outcome="matched",
                         about=SCOPE, payload="which scope?",
                         author="person:ana", occurred_at=T0)
    assert e.properties["about"] == SCOPE


# ---- proposals ----
def test_current_outcome_is_the_latest_observation():
    store = Store()
    sent = kg3.append_proposal(store, kind="sent", about="desc:recent#v1",
                               target_system="catalog_a",
                               author="person:admin", occurred_at=T0)
    kg3.append_proposal(store, kind="observed", about=sent.identity,
                        outcome="published", author="agent:bridge",
                        occurred_at=T0)
    kg3.append_proposal(store, kind="observed", about=sent.identity,
                        outcome="edited", author="agent:bridge",
                        occurred_at=T0)
    out = derivation.lens_current_outcome(ReadApi(store), None)["yield"]
    assert out[sent.identity] == "edited"


# ---- redaction: the ONE destruction path ----
def test_redaction_act_tombstones_and_logs():
    store = Store()
    v = _machine_desc(store)
    kg3.redaction_act(store, version_id=v.identity, field="description",
                      why="PHI reached evidence",
                      human_confirmation="person:admin")
    versions, _ = store.read(v.identity, mode="all")
    assert versions[-1].properties["description"] == "<REDACTED>"
    events = store.current_nodes("redaction")
    assert len(events) == 1 and events[0].properties["why"]
    with pytest.raises(kg3.RefusalKG3):
        kg3.redaction_act(store, version_id=v.identity, field="description",
                          why="no human", human_confirmation="agent:x")


# ---- KG4 ----
def test_mint_requires_a_human_act():
    store = Store()
    _machine_desc(store)
    d = kg3.append_disposition(store, about="fam:abc", ruling="acknowledge",
                               author="person:maria", occurred_at=T0)
    concept = kg4.mint(store, family_snapshot={"members": ["a.sql", "b.sql"],
                                               "lens_version": "1"},
                       minting_act=d.identity, created_at=T0)
    assert concept.identity.startswith("concept:")
    assert concept.properties["basis"]["members"] == ["a.sql", "b.sql"]
    # content-keyed: same family -> same id, second mint refused as dup
    with pytest.raises(kg4.RefusalKG4):
        kg4.mint(store, family_snapshot={"members": ["a.sql", "b.sql"],
                                         "lens_version": "1"},
                 minting_act=d.identity, created_at=T0)


def test_mint_refuses_machine_acts_and_stores_no_members():
    store = Store()
    e = kg3.append_usage(store, action="asked", outcome="matched",
                         about="x", payload="q", author="agent:mind",
                         occurred_at=T0)
    with pytest.raises(kg4.RefusalKG4) as exc:
        kg4.mint(store, family_snapshot={"members": ["a.sql"]},
                 minting_act=e.identity, created_at=T0)
    assert "human" in str(exc.value)
    assert not any(edge.kind == "member" for edge in Store().current_edges())


# ---- conformance ----
def test_check_kg3_7_conformance():
    store = Store()
    _machine_desc(store, n=2)
    kg3.append_disposition(store, about="desc:recent", ruling="accept",
                           author="person:maria", occurred_at=T0)
    assert metamodel.validate_artifact_layer(store) == []
