"""STEP 3 of the Connection Ledger build — PERSON NODES. The test
suite, shown to Sunny before any implementation (step discipline).

The review's MISSING-KIND row: every author in the system is a
string ("person:console") — the user tree has no trunk, and step
1's usage ruling ("a usage event is connected to the user AND the
item it used") could only land its item half. Step 3:

- ACTORS ARE MINTED ON FIRST ACT: any KG3 write by "person:X" /
  "agent:X" / "role:X" ensures a node of that kind exists
  (idempotent — one node, however many acts).
- ACTS WALK TO THEIR ACTORS: every authored KG3 node gains a
  —by→ actor edge in the adjacency (two-ended), completing the
  usage ruling's second half.
- THE USER TREE WALKS: person → their acts → the items touched is
  pure traversal — "what did I look at" becomes a graph query.
- The ledger gains person/agent/role rows (edge "performed_by", edged);
  registry 1.23.0. A hand-written actor with no acts counts
  missing — the census sees fakes.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql.flows import censuses, connect
from aisql.graph import kg3_artifacts
from aisql.graph.kg1_intake import new_store
from aisql.graph.read_api import ReadApi

T0 = "2026-09-07T12:00:00Z"


@pytest.fixture()
def store():
    s = new_store()
    kg3_artifacts.append_usage(s, "asked", "person:alice", T0,
                               payload="q", outcome="matched",
                               about="emr|dbo|ADT_EVENTS")
    kg3_artifacts.append_description(
        s, "desc::p", ["emr|dbo|ADT_EVENTS"], "words",
        "gate_passed", "agent:gate", {"kind": "probe"}, T0)
    return s


# ---- minting ---------------------------------------------------------
def test_actors_are_minted_on_first_act(store):
    read = ReadApi(store)
    people = {n.identity for n in read.nodes("person")}
    assert "person:alice" in people


def test_minting_is_idempotent(store):
    kg3_artifacts.append_usage(store, "asked", "person:alice", T0,
                               payload="q2", outcome="no-match")
    read = ReadApi(store)
    alices = [n for n in read.nodes("person")
              if n.identity == "person:alice"]
    assert len(alices) == 1  # one node, however many acts


def test_agents_mint_their_own_kind(store):
    read = ReadApi(store)
    agents = {n.identity for n in read.nodes("agent")}
    assert "agent:gate" in agents
    # and never cross-minted as persons
    people = {n.identity for n in read.nodes("person")}
    assert "agent:gate" not in people


# ---- the acts walk to their actors -----------------------------------
def test_acts_walk_to_their_actors(store):
    read = ReadApi(store)
    adj = connect.build_adjacency(read)
    usage = next(n for n in read.nodes("usage")
                 if n.properties.get("about") == "emr|dbo|ADT_EVENTS")
    edges = {(n, lbl) for n, lbl in adj.get(usage.identity, [])}
    assert ("person:alice", "performed_by") in edges
    back = {(n, lbl) for n, lbl in adj.get("person:alice", [])}
    assert (usage.identity, "performed_by") in back


def test_the_user_tree_walks(store):
    """person -> act -> item: 'what did alice touch' is traversal."""
    read = ReadApi(store)
    adj = connect.build_adjacency(read)
    acts = {n for n, lbl in adj.get("person:alice", [])
            if lbl == "performed_by"}
    assert acts
    touched = set()
    for act in acts:
        touched |= {n for n, lbl in adj.get(act, [])
                    if lbl == "about"}
    assert "emr|dbo|ADT_EVENTS" in touched


# ---- the census covers actors ----------------------------------------
def test_ledger_and_census_cover_actors(store):
    ledger = censuses.connection_ledger()
    for kind in ("person", "agent", "role"):
        assert ledger[kind]["edge"] == "performed_by"
        assert ledger[kind]["status"] == "edged"
    c = censuses.connection_census(ReadApi(store))
    assert c["unledgered_kinds"] == []
    assert "person" not in c["counted_missing_kinds"]


def test_an_actor_with_no_acts_counts_missing(store):
    """The census sees fakes: a hand-written person node with no
    act pointing at it is counted, never silently present."""
    store.append_node("person", "person:ghost",
                      {"identity": "person:ghost"}, T0, "probe")
    c = censuses.connection_census(ReadApi(store))
    assert "person" in c["counted_missing_kinds"]
