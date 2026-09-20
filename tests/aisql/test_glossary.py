"""THE GLOSSARY PROCESS (Ruling_Glossary_Process.md, ruled
2026-09-11): the token ledger with its conservation law, THE FIELD
LAW (machine fields refresh, ruled fields are human-only), Phase-2
dictionary matching with position constraints, and the seed that
births the governance journal from the ledger's blessed slice.

Proves: contract:aisql-design-to-code
"""
import json

import pytest

from aisql.console import build_store
from aisql.flows import glossary
from aisql.graph.read_api import ReadApi

T0 = "2026-09-09T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    store, _ = build_store("ed_sepsis_dev")
    return store, ReadApi(store)


def _write_dictionary(gdir, entries):
    gdir.mkdir(parents=True, exist_ok=True)
    (gdir / glossary.DICTIONARY).write_text(json.dumps(
        {"source": "test fixture", "entries": entries}))


# ---- phase 1: the total scan ----------------------------------------
def test_scan_carries_count_sample_and_position(world):
    _store, read = world
    found = glossary.scan(read)
    cnt = found["cnt"]
    assert cnt["carriers"] > 1
    assert any("WRONG_MED_ALT_CNT" in s for s in cnt["sample"]) or \
        cnt["carriers"] >= len(cnt["sample"])
    assert "last" in cnt["position"]


def test_scan_excludes_governance_kinds(world):
    store, read = world
    from aisql.graph import kg3_artifacts
    kg3_artifacts.append_acronym(store, "zzglossx", ["test only"],
                                 approved_by="person:sunny",
                                 approved_at=T0)
    found = glossary.scan(ReadApi(store))
    assert "zzglossx" not in found
    assert "sunny" not in found


# ---- phases 1+2: the refresh + conservation -------------------------
def test_refresh_creates_the_ledger_and_conserves_every_token(
        world, tmp_path):
    _store, read = world
    census = glossary.ledger_refresh(read, tmp_path)
    ledger = glossary.load_ledger(tmp_path)
    assert sum(census.values()) == len(ledger)          # conservation
    assert set(census) <= set(glossary.MACHINE_STATUSES)
    assert ledger["alt"]["status"] == "unreviewed"      # no dictionary


def test_refresh_matches_the_dictionary_and_cites_it(world, tmp_path):
    _store, read = world
    _write_dictionary(tmp_path, {"cnt": {"expansions": ["count"]}})
    glossary.ledger_refresh(read, tmp_path)
    row = glossary.load_ledger(tmp_path)["cnt"]
    assert row["status"] == "matched"
    assert row["proposed"] == ["count"]
    assert glossary.DICTIONARY in row["evidence"]


def test_position_constrained_entry_matches_only_there(world,
                                                       tmp_path):
    _store, read = world
    # 'wrong' never sits last in a name here; a last-only entry
    # must NOT match it, while an unconstrained one would
    _write_dictionary(tmp_path, {
        "wrong": {"expansions": ["never"], "position": "last"}})
    glossary.ledger_refresh(read, tmp_path)
    assert glossary.load_ledger(tmp_path)["wrong"]["status"] == \
        "unreviewed"


def test_refresh_never_touches_ruled_fields(world, tmp_path):
    _store, read = world
    _write_dictionary(tmp_path, {"alt": {"expansions": ["wrong"]}})
    (tmp_path / glossary.LEDGER).write_text(json.dumps({
        "alt": {"status": "blessed", "expansions": ["alternative"],
                "approved_by": "person:sunny", "approved_at": T0,
                "carriers": 999},
        "cd": {"status": "held", "why_held": "code vs clinical doc"},
    }))
    glossary.ledger_refresh(read, tmp_path)
    ledger = glossary.load_ledger(tmp_path)
    alt = ledger["alt"]
    assert alt["status"] == "blessed"           # dictionary can't demote
    assert alt["expansions"] == ["alternative"]
    assert alt["carriers"] != 999               # machine facts DO refresh
    assert ledger["cd"]["status"] == "held"
    assert ledger["cd"]["why_held"] == "code vs clinical doc"


def test_refresh_is_idempotent(world, tmp_path):
    _store, read = world
    first = glossary.ledger_refresh(read, tmp_path)
    text1 = (tmp_path / glossary.LEDGER).read_text()
    second = glossary.ledger_refresh(read, tmp_path)
    assert first == second
    assert (tmp_path / glossary.LEDGER).read_text() == text1


# ---- the seed: ledger blessed slice → the governance journal --------
def test_seed_births_the_journal_from_the_blessed_slice(tmp_path):
    journal = tmp_path / "governance" / "journal.jsonl"
    store, _ = build_store("ed_sepsis_dev", journal_path=journal)
    read = ReadApi(store)
    (tmp_path / glossary.LEDGER).write_text(json.dumps({
        "med": {"status": "blessed", "expansions": ["medication"],
                "approved_by": "person:sunny", "approved_at": T0},
        "cd": {"status": "held", "why_held": "unruled"},
        "alt": {"status": "unreviewed"},
    }))
    assert glossary.seed_journal(store, read, tmp_path) == 1
    idents = [json.loads(x)["identity"]
              for x in journal.read_text().splitlines()]
    assert "acronym::MED" in idents and "person:sunny" in idents
    assert not any("CD" in i or "ALT" in i for i in idents
                   if i.startswith("acronym::"))
    # rebirth: a fresh build replays the journal — the blessing
    # survives; the seed then has nothing to do (delta by name)
    store2, _ = build_store("ed_sepsis_dev", journal_path=journal)
    read2 = ReadApi(store2)
    assert {n.properties["name"]
            for n in read2.nodes("acronym")} == {"med"}
    assert glossary.seed_journal(store2, read2, tmp_path) == 0


def test_seed_lands_a_ruled_delta_and_never_rejournals(tmp_path):
    journal = tmp_path / "governance" / "journal.jsonl"
    store, _ = build_store("ed_sepsis_dev", journal_path=journal)
    read = ReadApi(store)
    f = tmp_path / glossary.LEDGER
    row = {"status": "blessed", "expansions": ["medication"],
           "approved_by": "person:sunny", "approved_at": T0}
    f.write_text(json.dumps({"med": row}))
    assert glossary.seed_journal(store, read, tmp_path) == 1
    # the alt/cnt path: a later ruling blesses one more name — the
    # next boot lands exactly that delta
    f.write_text(json.dumps({
        "med": row,
        "cnt": {"status": "blessed", "expansions": ["count"],
                "approved_by": "person:sunny",
                "approved_at": "2026-09-11T12:00:00Z"}}))
    assert glossary.seed_journal(store, read, tmp_path) == 1
    idents = [json.loads(x)["identity"]
              for x in journal.read_text().splitlines()]
    assert idents.count("acronym::MED") == 1
    assert idents.count("acronym::CNT") == 1


def test_seed_without_a_ledger_is_a_quiet_zero(tmp_path):
    store, _ = build_store("ed_sepsis_dev",
                           journal_path=tmp_path / "j.jsonl")
    assert glossary.seed_journal(store, ReadApi(store),
                                 tmp_path) == 0


# ---- the ruling view -------------------------------------------------
def test_review_queue_orders_matched_first_then_by_impact(tmp_path):
    (tmp_path / glossary.LEDGER).write_text(json.dumps({
        "aaa": {"status": "unreviewed", "carriers": 50},
        "bbb": {"status": "matched", "carriers": 2},
        "ccc": {"status": "proposed", "carriers": 9},
        "ddd": {"status": "blessed", "carriers": 99,
                "expansions": ["x"], "approved_by": "person:sunny",
                "approved_at": T0},
    }))
    q = [t for t, _ in glossary.review_queue(tmp_path)]
    assert q == ["bbb", "ccc", "aaa"]           # blessed never queues
