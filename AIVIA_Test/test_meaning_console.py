"""THE MEANING-TEST CONSOLE's own tests (Design_Chatbot.md ruling,
2026-09-11). Two tiers, per the live-seat rule:

DETERMINISTIC (always run, keyless): the scoped index, the
technical adjacency, exact-tier matching, the planner (minimal
connecting subgraph), the GQL writer's Fabric legality, cache
seeding, and the honest outcomes (gap · relaxation · zero).

THE LIVE BATTERY (AIVIA_LIVE=1 + OPENAI_API_KEY): ~8 questions in
five families — findability · meaning readback · column search ·
relationship grounding · absence honesty — DRAFTED for Sunny's
gap-check and blessing; assertions pin laws and expected crowns,
never verbatim model wording.

Proves: contract:aivia-design-to-code
"""
import json
import os
import pathlib

import pytest

from aivia import meaning_console as mc
from aivia.console import build_store
from aivia.flows import ask
from aivia.graph.read_api import ReadApi

ADT = "emr|dbo|ADT_EVENTS"
BED = "emr|dbo|BED_CONFIG"


@pytest.fixture(scope="module")
def world():
    from aivia.flows import glossary
    store, base = build_store("ed_sepsis_dev")
    read = ReadApi(store)
    # the store-as-ruled: the glossary ledger's blessed slice loads
    # as acronym nodes (journal_path is None here, so NOTHING is
    # written — tests never touch estate files)
    glossary.seed_journal(store, read, base / "glossary")
    entries, exclusions = mc.technical_scope(read)
    adj, directed = mc.technical_adjacency(read)
    return read, entries, exclusions, adj, directed


# ---- the scoped index ------------------------------------------------
def test_scope_carries_the_speaking_technical_grains(world):
    read, entries, exclusions, _, _ = world
    counts = {}
    for e in entries:
        counts[e["label"]] = counts.get(e["label"], 0) + 1
    full = ask.build_index(read)
    assert counts["table"] == sum(
        1 for e in full if e["label"] == "table")
    assert counts["column"] == sum(
        1 for e in full if e["label"] == "column")
    kinds = {e["name"] for e in entries if e["label"] == "label"}
    assert kinds == {"table", "column"}
    edge_kinds = {e["identity"] for e in entries
                  if e["label"] == "edge_kind"}
    assert edge_kinds == {"edgekind::has_part", "edgekind::joins_to"}


def test_every_exclusion_is_counted_never_silent(world):
    read, entries, exclusions, _, _ = world
    full = ask.build_index(read)
    out_of_scope = [e for e in full
                    if e["label"] not in mc.TECHNICAL_SPEAKING]
    # the speechless technical grains are counted too
    assert exclusions["db"] == 1
    assert exclusions["db_schema"] == 3
    spoken_exclusions = {k: v for k, v in exclusions.items()
                         if k not in ("db", "db_schema")}
    assert sum(spoken_exclusions.values()) == len(out_of_scope)
    line = mc.coverage_line(entries, exclusions)
    assert "excluded (counted" in line and "db_schema 3" in line


# ---- the technical adjacency ----------------------------------------
def test_adjacency_spine_and_declared_joins(world):
    read, _, _, adj, directed = world
    db_id = next(n.identity for n in read.nodes("db"))
    assert sum(1 for _, lbl in adj[db_id]
               if lbl == "has_part") == 3       # db → 3 schemas
    assert (ADT, BED, "joins_to") in directed   # the dictionary pair
    assert any(b == BED and lbl == "joins_to" for b, lbl in adj[ADT])
    assert any(b == ADT and lbl == "joins_to" for b, lbl in adj[BED])
    col = next(n.identity for n in read.nodes("column")
               if n.identity.startswith(ADT + "|"))
    assert any(b == col and lbl == "has_part" for b, lbl in adj[ADT])


# ---- step 3: matching (deterministic tiers, keyless) ----------------
def test_exact_instance_token_matches_without_a_model(world):
    _, entries, _, _, _ = world
    m = mc.match_token("ADT_EVENTS", entries, None)
    assert m["tier"] == "exact"
    top = m["matches"][0]
    assert top["class"] == "instance" and top["score"] == 1.0
    assert top["identity"] == ADT


def test_kind_and_edge_kind_tokens_classify(world):
    _, entries, _, _, _ = world
    kind = mc.match_token("table", entries, None)
    assert any(x["class"] == "kind" for x in kind["matches"])
    ek = mc.match_token("joins to", entries, None)
    assert ek["matches"][0]["class"] == "edge-kind"


def test_no_model_no_match_is_an_honest_none(world):
    _, entries, _, _, _ = world
    m = mc.match_token("zzz_never_a_name", entries, None)
    assert m["tier"] == "none" and m["matches"] == []


# ---- step 4: the planner + the GQL artifact -------------------------
def test_planner_connects_a_declared_join_in_one_hop(world):
    read, entries, _, adj, directed = world
    anchors = [e for e in entries if e["identity"] in (ADT, BED)]
    plan = mc.plan_connection(anchors, adj, allowed={"joins_to"})
    assert len(plan["paths"]) == 1 and not plan["gaps"]
    assert plan["edges"] == [(ADT, BED, "joins_to")] or \
        plan["edges"] == [(BED, ADT, "joins_to")]
    gql = mc.write_gql(plan["paths"][0], directed,
                       {ADT: "table", BED: "table"})
    assert ":joins_to" in gql
    assert "ADT_EVENTS" in gql and "BED_CONFIG" in gql


def test_gql_is_fabric_legal_never_opencypher(world):
    read, entries, _, adj, directed = world
    anchors = [e for e in entries if e["identity"] in (ADT, BED)]
    plan = mc.plan_connection(anchors, adj)
    for p in plan["paths"]:
        gql = mc.write_gql(p, directed, {})
        assert "type(" not in gql             # the dialect corpse
        assert gql.startswith("MATCH ")
        assert " FILTER " in gql and " RETURN " in gql


def test_edge_constraint_relaxes_honestly(world):
    read, entries, _, adj, _ = world
    col = next(e for e in entries if e["label"] == "column"
               and e["identity"].startswith(ADT + "|"))
    tab = next(e for e in entries if e["identity"] == BED)
    # a column has no joins_to edges: the constrained walk fails,
    # the planner relaxes and SAYS so
    plan = mc.plan_connection([col, tab], adj, allowed={"joins_to"})
    assert plan["relaxed"] and not plan["gaps"]
    assert plan["paths"]


# ---- step 5: the whole loop, keyless (the seat floor) ---------------
def test_two_names_answer_with_query_and_evidence(world):
    read, entries, _, adj, directed = world
    r = mc.answer_question("ADT_EVENTS BED_CONFIG", None, entries,
                           None, read, adj, directed)
    assert r["seat"] == "floor"
    assert len(r["anchors"]) == 2
    assert r["gql"] and all("type(" not in g for g in r["gql"])
    joined = "\n".join(r["evidence"])
    assert "ADT_EVENTS" in joined and "BED_CONFIG" in joined


def test_single_anchor_answers_its_neighborhood(world):
    read, entries, _, adj, directed = world
    r = mc.answer_question("ADT_EVENTS", None, entries, None,
                           read, adj, directed)
    assert len(r["anchors"]) == 1
    assert len(r["gql"]) == 1 and "ADT_EVENTS" in r["gql"][0]
    assert any("ADT_EVENTS" in line for line in r["evidence"])


def test_nothing_matches_is_an_honest_zero(world):
    read, entries, _, adj, directed = world
    r = mc.answer_question("qqq zzz", None, entries, None,
                           read, adj, directed)
    assert not r["anchors"] and not r["gql"] and not r["evidence"]
    assert r["unmatched"]


def test_fallback_tokens_are_mechanical():
    toks = mc.fallback_tokens("  what   joins ADT_EVENTS  ")
    assert toks[0] == "what joins ADT_EVENTS"   # the whole question
    assert "ADT_EVENTS" in toks and "joins" in toks


# ---- the cache seed --------------------------------------------------
def test_seed_cache_copies_once_and_never_overwrites(tmp_path):
    src = tmp_path / "src.json"
    dst = tmp_path / "sub" / "dst.json"
    src.write_text('{"k": [1.0]}')
    assert mc.seed_cache(src, dst) is True
    assert dst.read_text() == '{"k": [1.0]}'
    src.write_text('{"k": [2.0]}')
    assert mc.seed_cache(src, dst) is False     # dst present: no-op
    assert dst.read_text() == '{"k": [1.0]}'
    assert mc.seed_cache(tmp_path / "absent.json",
                         tmp_path / "other.json") is False


# ---- the glossary chain (the machinery lives in flows/glossary;
# tests/aivia/test_glossary.py owns it — this proves the CONSOLE
# INDEX carries the blessed expansions end-to-end) -------------------
def test_blessed_acronyms_join_the_console_index(tmp_path):
    from aivia.flows import glossary
    journal = tmp_path / "governance" / "journal.jsonl"
    store, _ = build_store("ed_sepsis_dev", journal_path=journal)
    read = ReadApi(store)
    (tmp_path / glossary.LEDGER).write_text(json.dumps({
        t: {"status": "blessed", "expansions": [e],
            "approved_by": "person:sunny",
            "approved_at": "2026-09-09T12:00:00Z"}
        for t, e in [("med", "medication"), ("alt", "alternative"),
                     ("cnt", "count")]}))
    glossary.seed_journal(store, read, tmp_path)
    entries, _ = mc.technical_scope(read)
    crown = next(e for e in entries
                 if e["name"] == "WRONG_MED_ALT_CNT")
    for word in ("medication", "alternative", "count"):
        assert word in crown["expansions_text"]


# ---- THE LIVE MEANING BATTERY (drafted for Sunny's blessing) --------
live = pytest.mark.skipif(
    not os.environ.get("AIVIA_LIVE"),
    reason="the live battery runs with AIVIA_LIVE=1 (live-seat rule)")

# family · question · crowns (any-of, real store names — never
# invented); assertions pin the LAW (crown surfaces in matches or
# evidence), never model wording
BATTERY = [
    ("findability",
     "which tables hold sepsis screening results?",
     ["IP_SEPSIS", "SEVERE_SEPSIS_STAGING",
      "NON_SEVERE_SEPSIS_STAGING"]),
    ("findability",
     "where are emergency department encounters stored?",
     ["ED_ENCOUNTERS_FACT", "ED_ENCOUNTERS_DM"]),
    ("meaning-readback",
     "what does the ADT_EVENTS table hold?",
     ["ADT_EVENTS"]),
    pytest.param(
        "column-search",
        "which column counts wrong medication alternatives?",
        ["WRONG_MED_ALT_CNT"],
        marks=pytest.mark.xfail(
            strict=False,
            reason="THE FIRST MEANING FINDING, re-ruled 2026-09-11: "
            "Sunny blessed alt=ALERT on evidence (the description "
            "counts warnings; the crosswalk shows Epic ALT=alert) — "
            "so THIS QUESTION embeds the refuted expansion "
            "'alternatives' and rightly stays lost, while the "
            "truthful phrasing '…wrong medication alerts?' ranks "
            "the crown #8. The question's wording awaits Sunny's "
            "gap-check; cnt sits matched-unratified in the ledger "
            "(blessing it is the next findability lever).")),
    ("relationship",
     "how do ADT_EVENTS and DEPARTMENTS connect?",
     ["ADT_EVENTS", "DEPARTMENTS"]),
    ("relationship",
     "what joins ALERT_ACTIONS to ALERT_HISTORY?",
     ["ALERT_ACTIONS", "ALERT_HISTORY"]),
    ("kind-grounding",
     "show me the tables",
     []),                       # law: 'tables' grounds as a KIND
    ("absence-honesty",
     "which table stores billing invoice line items?",
     []),                       # law: nothing invented
]


@pytest.fixture(scope="module")
def live_world(world):
    from aivia.console import EMBEDDING_MODEL, _env_key, make_embedder, make_interpreter
    from aivia.flows import grounding
    key = _env_key()
    assert key, "OPENAI_API_KEY missing — the live battery needs it"
    read, entries, _, adj, directed = world
    base = (pathlib.Path(__file__).resolve().parents[1]
            / "AIVIA_Product" / "estates" / "ed_sepsis_dev")
    mc.seed_cache(
        base.parent / "sepsis" / ".cache" / "embeddings.json",
        base / ".cache" / "embeddings.json")
    semantic = grounding.SemanticIndex(
        entries, make_embedder(key), EMBEDDING_MODEL,
        cache_path=base / ".cache" / "embeddings.json")
    interpret = make_interpreter(key, cache_path=None)
    return read, entries, adj, directed, semantic, interpret


@live
@pytest.mark.parametrize(
    "family,question,crowns", BATTERY,
    ids=[getattr(b, "values", b)[0] for b in BATTERY])
def test_live_meaning_battery(live_world, family, question, crowns):
    read, entries, adj, directed, semantic, interpret = live_world
    r = mc.answer_question(question, interpret, entries, semantic,
                           read, adj, directed)
    surfaced = "\n".join(
        r["evidence"]
        + [m["name"] for ms in r["match_sets"] for m in ms["matches"]])
    if crowns:
        assert any(c in surfaced for c in crowns), \
            f"{family}: none of {crowns} surfaced for {question!r}"
    if family == "kind-grounding":
        assert r["kind_constraints"] or any(
            m["class"] == "kind"
            for ms in r["match_sets"] for m in ms["matches"])
    if family == "absence-honesty":
        # every evidence line names a real indexed thing or a real
        # store identity — nothing invented; unmatched is reported.
        # The speechless spine nodes (db, db_schema) are real too:
        # the planner may route through them.
        real = {e["name"] for e in entries}
        for lbl in ("db", "db_schema"):
            real |= {n.identity.rsplit("|", 1)[-1]
                     for n in read.nodes(lbl)}
        for line in r["evidence"]:
            name = line.split("] ", 1)[-1].split(" — ")[0]
            assert name in real
    if family == "relationship" and r["anchors"] and len(
            r["anchors"]) >= 2:
        assert r["gql"], "two anchors must yield a query artifact"
