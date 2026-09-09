"""PHASE I — ACRONYM ENRICHMENT (the one-vocabulary law, ruled
2026-09-08). Suite first.

The model: acronym nodes (label: acronym) — {name, expansions[],
approved_by, approved_at}; —approved_by→ the person (direct,
timestamp as data, no ceremony event); —used_by→ every node whose
name carries the token, DERIVED AT GRAPH BUILD (new nodes connect
automatically — contract text). Both readers consume the same
stored expansions: cards gain an EXPANSION card; queries append
the expansions deterministically. Scan → Scribe (proposals only)
→ bless (human) → acronym nodes; the pipeline is hermetic here
(fake scribe); the LIVE run awaits Sunny's blessing.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import ask, censuses, connect, grounding
from aivia.graph import kg3_artifacts
from aivia.graph.read_api import ReadApi

from .test_ask_console import fake_embed, fake_interpreter

T0 = "2026-09-08T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    kg3_artifacts.append_acronym(
        store, "ED", ["emergency department", "emergency room"],
        approved_by="person:sunny", approved_at=T0)
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, fake_embed,
                                       "fake-2k", cache_path=None)
    return store, read, index, semantic


# ---- the node and its law --------------------------------------------
def test_acronyms_require_an_approver():
    from aivia.graph.kg1_intake import new_store
    from aivia.graph.kg3_artifacts import RefusalKG3
    store = new_store()
    with pytest.raises(RefusalKG3):
        kg3_artifacts.append_acronym(store, "ED", ["emergency"],
                                     approved_by="", approved_at=T0)
    with pytest.raises(RefusalKG3):
        kg3_artifacts.append_acronym(store, "ED", [],
                                     approved_by="person:s",
                                     approved_at=T0)


def test_acronym_stores_the_ruled_shape(world):
    store, read, _index, _semantic = world
    node = next(n for n in read.nodes("acronym"))
    assert node.properties["name"] == "ED"
    assert node.properties["expansions"] == [
        "emergency department", "emergency room"]
    assert node.properties["approved_by"] == "person:sunny"
    assert node.properties["approved_at"] == T0


def test_edges_walk_approver_and_carriers(world):
    _store, read, _index, _semantic = world
    adj = connect.build_adjacency(read)
    acr = next(n for n in read.nodes("acronym"))
    edges = {(t, lbl) for t, lbl in adj.get(acr.identity, [])}
    assert ("person:sunny", "approved_by") in edges
    used = {t for t, lbl in edges if lbl == "used_by"}
    assert "emr|dbo|ED_ENCOUNTERS_DM" in used  # carriers, derived
    c = censuses.connection_census(read)
    assert "acronym" not in c["counted_missing_kinds"]
    assert c["unledgered_kinds"] == []


# ---- both readers, one vocabulary ------------------------------------
def test_carrier_nodes_gain_the_expansion_card(world):
    _store, _read, index, _semantic = world
    dm = next(e for e in index
              if e["identity"] == "emr|dbo|ED_ENCOUNTERS_DM")
    card = dict(grounding.cards(dm)).get("expansion", "")
    assert "emergency department" in card


def test_queries_expand_deterministically(world):
    store, _read, _index, semantic = world
    q = "things about ED"
    interp = fake_interpreter({q.lower(): {"mentions": ["ED"]}})
    # expansions proposed — the blessed vocabulary supplies them
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    row = next(t for t in result["trace"] if t["mention"] == "ED")
    assert "emergency department" in row["searched_as"]


def test_the_expansion_card_answers_the_full_phrase(world):
    store, _read, _index, semantic = world
    q = "emergency department tables"
    interp = fake_interpreter({q: {"mentions":
                                   ["emergency department",
                                    "tables"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    hits = result["hits"]
    ed_dm = next((h for h in hits
                  if h["identity"] == "emr|dbo|ED_ENCOUNTERS_DM"),
                 None)
    assert ed_dm is not None
    assert "expansion" in ed_dm["via_card"]


# ---- the pipeline: scan -> scribe -> bless ---------------------------
def test_scan_scribe_bless_roundtrip(tmp_path):
    from aivia.console import build_store
    from aivia.flows import enrich
    store, _ = build_store("sepsis")
    read = ReadApi(store)
    tokens = enrich.scan_name_tokens(read)
    assert "ed" in tokens and "dttm" in tokens

    def fake_scribe(token_list):
        return {"dttm": ["date and time"]}
    proposals = enrich.propose(tokens, fake_scribe)
    assert proposals == {"dttm": ["date and time"]}
    made = enrich.bless(store, proposals,
                        approved_by="person:sunny", approved_at=T0)
    assert made == 1
    acr = next(n for n in ReadApi(store).nodes("acronym")
               if n.properties["name"] == "dttm")
    assert acr.properties["approved_by"] == "person:sunny"
