"""PHASE E1 — THE GOVERNANCE JOURNAL (Sunny's ruling: all user
decisions are stored in the user tree, PERSISTENTLY — the 5:11pm
confirmations died with that console). Suite first.

Design: every governance write (the kg3@ extract family: usage
events, terms, acronyms, descriptions, dispositions, minted actors)
appends a line to the estate's governance/journal.jsonl; at boot
the journal REPLAYS into the store after the estate loads. Builder
writes (sources) never journal — they reload from the estate.

Pins:
1. A confirmation survives a full store rebuild — the ledger
   answers via 'ledger' with every model seat dead.
2. Terms survive with their origins intact.
3. Builder writes do NOT journal (the journal holds decisions,
   not data).
4. Replay is idempotent — rebuilding twice doesn't double events.

Proves: contract:aisql-design-to-code
"""
import json

import pytest

from aisql.flows import ask, grounding
from aisql.graph.read_api import ReadApi

from . import doubles
from .doubles import recorded_embed, scripted_proposals

T0 = "2026-09-08T12:00:00Z"


@pytest.fixture()
def journal(tmp_path):
    return tmp_path / "journal.jsonl"


def _build(journal_path):
    from aisql.console import build_store
    store, _ = build_store("sepsis", journal_path=journal_path)
    return store


def test_confirmations_survive_rebirth(journal):
    store1 = _build(journal)
    read1 = ReadApi(store1)
    index = ask.build_index(read1)
    sem = grounding.SemanticIndex(index, recorded_embed, doubles.EMBED_MODEL,
                                  cache_path=None)
    q = "which files mention the sepsis dates proc"
    interp = scripted_proposals({q: {
        "mentions": ["USP_IP_SepsisDates"]}})
    r = ask.ask(store1, q, "person:sunny", T0,
                interpret_fn=interp, semantic=sem)
    assert r.get("pending_confirmation")
    ask.confirm(store1, q, r["interpretation"], "person:sunny", T0,
                semantic=sem)
    assert journal.is_file() and journal.read_text().strip()

    # THE REBIRTH: a fresh store, same estate, same journal
    store2 = _build(journal)

    def dead_model(qq):
        raise AssertionError("no model on a ledger hit")
    again = ask.ask(store2, q, "person:sunny", T0,
                    interpret_fn=dead_model, semantic=None)
    assert again["status"] == "answer"
    assert again["via"] == "ledger"


def test_terms_survive_with_their_origins(journal):
    from aisql.graph import kg3_artifacts
    store1 = _build(journal)
    kg3_artifacts.append_usage(store1, "confirmed", "person:sunny",
                               T0, payload="blessing act")
    act = store1.current_nodes("usage")[-1]
    kg3_artifacts.append_term(store1, "term::t", "T", "a def",
                             "person:sunny", T0,
                             derived_from=[act.identity])
    store2 = _build(journal)
    read2 = ReadApi(store2)
    term = next(n for n in read2.nodes("term"))
    assert term.properties["derived_from"] == [act.identity]
    people = {n.identity for n in read2.nodes("person")}
    assert "person:sunny" in people  # minted actors replay too


def test_builder_writes_never_journal(journal):
    _build(journal)
    if journal.is_file():
        lines = [json.loads(x) for x in
                 journal.read_text().splitlines()]
        assert not [ln for ln in lines
                    if ln["label"] in ("table", "column", "file",
                                       "pbi_report")]
    # a fresh estate build with no decisions writes no journal at
    # all, or only replayed-nothing


def test_replay_is_idempotent(journal):
    from aisql.graph import kg3_artifacts
    store1 = _build(journal)
    kg3_artifacts.append_usage(store1, "asked", "person:sunny", T0,
                               payload="q", outcome="no-match")
    store2 = _build(journal)
    store3 = _build(journal)
    n2 = len([n for n in store2.current_nodes("usage")])
    n3 = len([n for n in store3.current_nodes("usage")])
    assert n2 == n3 == 1
