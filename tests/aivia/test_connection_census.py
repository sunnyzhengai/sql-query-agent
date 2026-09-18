"""STEP 1 of the Connection Ledger build — THE TEST SUITE, shown to
Sunny before any implementation (the step discipline).

Scope of step 1 (per Audit_Graph_Integrity_Review, 'go' 2026-09-07):
the adjacency exposes connections that ALREADY EXIST IN DATA (the
ten UNWALKABLE rows), the Connection_Ledger registry sheet becomes
the ruled expected-edges data (the literal law: never a code dict —
RULED_ISOLATED_KINDS dies in this step), and the CONNECTION CENSUS
replaces reachability:

    birth_edged ⊎ counted_missing ⊎ rooted == total

Explicitly NOT in step 1 (later steps, their own suites):
- term ORIGIN data (step 2 — today's junk self-about stays counted)
- person nodes + author edges (step 3)
- condition/parameter belongs_to edges (step 4)
- excluded_file -> root (step 5)

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import censuses, connect
from aivia.graph import kg3_artifacts
from aivia.graph.read_api import ReadApi

T0 = "2026-09-07T12:00:00Z"


@pytest.fixture(scope="module")
def accreted():
    """The sepsis store with governance accreted, so every KG3 kind
    under test exists live."""
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    kg3_artifacts.append_usage(
        store, "asked", "person:probe", T0, payload="q",
        outcome="matched", about="emr|dbo|ADT_EVENTS")
    kg3_artifacts.append_description(
        store, "desc::probe", ["emr|dbo|ADT_EVENTS"],
        "a probe description", "gate_passed", "agent:probe",
        {"kind": "probe"}, T0)
    kg3_artifacts.append_responsibility(
        store, "resp::probe", "steward", "person:probe",
        "emr|dbo|ADT_EVENTS", "person:probe", T0)
    probe_event = store.current_nodes("usage")[-1]
    kg3_artifacts.append_term(
        store, "term::probe", "PROBE", "a probe term",
        "person:probe", T0,
        derived_from=[probe_event.identity])
    read = ReadApi(store)
    return store, read, connect.build_adjacency(read)


# ---- the ten UNWALKABLE rows become walkable -------------------------
def test_usage_events_walk_to_what_they_touched(accreted):
    _store, read, adj = accreted
    usage = next(n for n in read.nodes("usage")
                 if n.properties.get("about") == "emr|dbo|ADT_EVENTS")
    edges = {(n, lbl) for n, lbl in adj.get(usage.identity, [])}
    assert ("emr|dbo|ADT_EVENTS", "about") in edges
    # and the item sees the event back (edges are two-ended)
    back = {(n, lbl) for n, lbl in adj.get("emr|dbo|ADT_EVENTS", [])}
    assert (usage.identity, "about") in back


def test_descriptions_walk_to_their_subjects(accreted):
    _store, _read, adj = accreted
    edges = {(n, lbl) for n, lbl in adj.get("desc::probe", [])}
    assert ("emr|dbo|ADT_EVENTS", "describes") in edges


def test_responsibilities_walk_to_their_targets(accreted):
    _store, _read, adj = accreted
    edges = {(n, lbl) for n, lbl in adj.get("resp::probe", [])}
    assert ("emr|dbo|ADT_EVENTS", "assigns") in edges


def test_twins_walk_to_their_files(accreted):
    _store, read, adj = accreted
    twin = next(n for n in read.nodes("meaning_twin")
                if n.identity.endswith("USP_ED_SEPSIS.sql"))
    file_id = twin.identity.removeprefix("twin::")
    edges = {(n, lbl) for n, lbl in adj.get(twin.identity, [])}
    assert (file_id, "translates") in edges


def test_kg1_spine_is_walkable(accreted):
    """db -> schema -> table: the graph's own hierarchy walks."""
    _store, read, adj = accreted
    db = next(n for n in read.nodes("db"))
    schemas = {n for n, lbl in adj.get(db.identity, [])
               if lbl == "has_part"}
    assert schemas  # db contains its schemas
    schema = sorted(schemas)[0]
    tables = {n for n, lbl in adj.get(schema, []) if lbl == "has_part"}
    assert tables  # schema contains its tables


# ---- the ledger is registry data (the literal law) -------------------
def test_expected_edges_come_from_the_registry():
    """RULED_ISOLATED_KINDS (offense #3) is DEAD: the per-kind
    expected-birth-edge table is the Connection_Ledger sheet, read
    from the registry — never a code dict."""
    ledger = censuses.connection_ledger()
    assert ledger["usage"]["edge"] == "about"
    assert ledger["meaning_twin"]["edge"] == "translates"
    assert ledger["db"]["status"] == "rooted"
    # step 2 LANDED: the term row flipped to edged (derived_from)
    assert ledger["term"]["status"] == "edged"
    assert not hasattr(censuses, "RULED_ISOLATED_KINDS")


# ---- the connection census (census 1's successor) --------------------
def test_connection_census_equation_holds(accreted):
    _store, read, _adj = accreted
    c = censuses.connection_census(read)
    assert c["birth_edged"] + c["counted_missing"] + c["rooted"] \
        == c["total"]
    # the ten unwalkable rows are healed AND (step 2) terms are
    # well-born here; at M6 the statement debt RETIRED at its
    # named landing step (file→statement birth-edges all 67 —
    # the placeholder law honored end to end): nothing is missing
    assert c["counted_missing_kinds"] == []
    assert c["unledgered_kinds"] == []  # closed at birth


def test_census_vacuity_an_orphan_is_seen(accreted):
    """A census that cannot fail is decoration: a node of a kind
    whose ledger row expects an edge, born WITHOUT one, must land
    in counted_missing — never silently absent."""
    store, _read, _adj = accreted
    store.append_node("usage", "usage::orphan-probe",
                      {"action": "confirmed",
                       "author": "person:probe",
                       "occurred_at": T0}, T0, "probe")
    c = censuses.connection_census(ReadApi(store))
    assert c["counted_missing"] >= 1
    assert "usage" in c["counted_missing_kinds"]


def test_census_prints_in_the_report(accreted):
    _store, read, _adj = accreted
    from aivia.flows import ask
    text = censuses.report(read, ask.build_index(read))
    assert "connection" in text.lower()
    assert "birth-edged" in text.lower()
