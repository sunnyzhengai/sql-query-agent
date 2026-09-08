"""STEP 2 of the Connection Ledger build — TERM ORIGINS. The test
suite, shown to Sunny before any implementation (step discipline).

Sunny's overrule (the row that started the audit): "a term should
not be alone — a term is deduced from a file's SQL." Step 2 makes
that structural:

- append_term gains ORIGIN parameters: derived_from (the act/event
  that deduced it — a confirmation, a minting) and about (the
  entities it describes/grounds). The junk self-about dies.
- A NEW term without an origin is REFUSED (no node is alone — at
  birth, not by census cleanup). Legacy orphans stay COUNTED.
- ask.confirm's expansion-blessed vocabulary terms cite their
  confirming usage event.
- The adjacency walks term —derived_from→ event and term —about→
  entities; the ledger row flips term to edged (registry 1.22.0),
  so a well-born term counts birth-edged and an orphan counts
  missing — automatically, per node.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import ask, censuses, connect, grounding
from aivia.graph import kg3_artifacts
from aivia.graph.read_api import ReadApi

from .test_ask_console import fake_embed, fake_interpreter, \
    seed_vocabulary

T0 = "2026-09-07T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    seed_vocabulary(store)
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, fake_embed,
                                       "fake-64", cache_path=None)
    return store, semantic


# ---- the origin parameters -------------------------------------------
def test_terms_carry_their_origins():
    from aivia.graph.kg1_intake import new_store
    store = new_store()
    kg3_artifacts.append_usage(store, "confirmed", "person:t", T0,
                               payload="q")
    event = store.current_nodes("usage")[-1]
    kg3_artifacts.append_term(
        store, "term::t1", "T1", "a well-born term", "person:t", T0,
        derived_from=[event.identity],
        about=["emr|dbo|ADT_EVENTS"])
    term = store.current_nodes("term")[-1]
    assert term.properties["derived_from"] == [event.identity]
    assert term.properties["about"] == ["emr|dbo|ADT_EVENTS"]
    # the junk self-about is dead: about is never the term's own name
    assert term.properties["about"] != ["T1"]


def test_a_new_term_without_an_origin_is_refused():
    from aivia.graph.kg1_intake import new_store
    from aivia.graph.kg3_artifacts import RefusalKG3
    store = new_store()
    with pytest.raises(RefusalKG3):
        kg3_artifacts.append_term(store, "term::orphan", "ORPHAN",
                                  "no node is alone", "person:t", T0)


# ---- blessed vocabulary cites its confirmation -----------------------
def test_confirmed_expansions_cite_the_confirming_event(world):
    store, semantic = world
    q = "which reports cover the icu"
    interp = fake_interpreter({q: {
        "mentions": ["reports", "icu"],
        "kinds": {"reports": "file"},
        "expansions": {"icu": ["intensive care unit"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result.get("pending_confirmation")
    ask.confirm(store, q, result["interpretation"], "person:test",
                T0, semantic=semantic)
    read = ReadApi(store)
    term = next(n for n in read.nodes("term")
                if n.properties.get("name") == "icu")
    origins = term.properties.get("derived_from") or []
    assert origins, "a blessed word cites the act that blessed it"
    events = {n.identity for n in read.nodes("usage")
              if n.properties.get("action") == "confirmed"}
    assert set(origins) <= events


# ---- the graph walks the origins -------------------------------------
def test_adjacency_walks_term_origins(world):
    store, _semantic = world
    read = ReadApi(store)
    term = next(n for n in read.nodes("term")
                if n.properties.get("derived_from"))
    adj = connect.build_adjacency(read)
    edges = {(n, lbl) for n, lbl in adj.get(term.identity, [])}
    origin = term.properties["derived_from"][0]
    assert (origin, "derived_from") in edges


# ---- the census flips ------------------------------------------------
def test_well_born_terms_count_birth_edged(world):
    store, _semantic = world
    ledger = censuses.connection_ledger()
    assert ledger["term"]["status"] == "edged"
    assert ledger["term"]["edge"] == "derived_from"
    c = censuses.connection_census(ReadApi(store))
    # the seeded + blessed vocabulary is all well-born now:
    # term never appears as a missing kind in this store
    assert "term" not in c["counted_missing_kinds"]


def test_legacy_orphan_terms_stay_counted(world):
    store, _semantic = world
    # a legacy term written before the law (direct store append —
    # simulating pre-step-2 data) has no origin: COUNTED, never
    # silent, never blocking
    store.append_node("term", "term::legacy-orphan",
                      {"artifact_id": "term::legacy-orphan",
                       "name": "LEGACY", "definition": "old",
                       "author": "person:old", "created_at": T0},
                      T0, "legacy")
    c = censuses.connection_census(ReadApi(store))
    assert "term" in c["counted_missing_kinds"]
