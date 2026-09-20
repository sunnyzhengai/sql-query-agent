"""THE MEANING-TEST CONSOLE's own tests (Design_Chatbot.md ruling,
2026-09-11). Two tiers, per the live-seat rule:

DETERMINISTIC (always run, keyless): the scoped index, the
technical adjacency, exact-tier matching, the planner (minimal
connecting subgraph), the GQL writer's Fabric legality, cache
seeding, and the honest outcomes (gap · relaxation · zero).

THE LIVE BATTERY (AISQL_LIVE=1 + OPENAI_API_KEY): 21 questions —
findability · meaning readback · column search · relationship ·
absence honesty · enumeration · impact · the join-layer family
(18 BLESSED by Sunny, "bless them all" 2026-09-11: his six by
use, the drafted rest by his word) + the condition family (3,
drafted 2026-09-11 night, blessing per the standing path);
assertions pin laws and expected crowns, never verbatim model
wording.

Proves: contract:aisql-design-to-code
"""
import json
import os
import pathlib

import pytest

from aisql import meaning_console as mc
from aisql.console import build_store
from aisql.flows import ask
from aisql.graph.read_api import ReadApi

ADT = "emr|dbo|ADT_EVENTS"
BED = "emr|dbo|BED_CONFIG"


@pytest.fixture(scope="module")
def world():
    from aisql.flows import glossary
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
    assert counts["scope"] == 44          # the second target (M2)
    assert counts["condition"] > 300      # the third target (M3)
    assert counts["param"] == 4  # +2 at M5 (@StartDate/@EndDate)
    kinds = {e["name"] for e in entries if e["label"] == "label"}
    assert kinds == {"table", "column", "scope", "condition",
                     "parameter"}
    edge_kinds = {e["identity"] for e in entries
                  if e["label"] == "edge_kind"}
    # reads joined the closed set 2026-09-14 (THE READS COMPOUND)
    assert edge_kinds == {"edgekind::has_part", "edgekind::joins_to",
                          "edgekind::reads"}


def test_every_exclusion_is_counted_never_silent(world):
    read, entries, exclusions, _, _ = world
    full = ask.build_index(read)
    out_of_scope = [e for e in full
                    if e["label"] not in mc.TECHNICAL_SPEAKING]
    # the speechless technical grains are counted too
    assert exclusions["db"] == 1
    assert exclusions["db_schema"] == 3
    # full-index leftovers stay conserved (store-grain exclusion
    # keys — condition_on/degenerate, join_structure — count
    # STORE nodes, not index rows, so they sit outside this sum)
    from_index = {k: v for k, v in exclusions.items()
                  if k not in ("db", "db_schema", "condition_on",
                               "condition_degenerate",
                               "join_structure",
                               "direct_read_structure")}
    assert sum(from_index.values()) == len(out_of_scope)
    assert exclusions["condition_census"] == 69   # the twin retired
    assert exclusions["join_structure"] == 95     # ruled unindexed
    assert exclusions["direct_read_structure"] == 6  # era 3, counted
    assert exclusions["condition_on"] > 0
    assert exclusions["condition_degenerate"] > 0
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


# ---- THE LABEL CONSTRAINT (Sunny's ADT_EVENT round, 2026-09-11:
# 'what does the ADT_EVENT table mean' crowned the COLUMN
# ADT_EVENT_ID over the table the user's own word named — the
# ruled kind→label-constraint was display-only. These replay the
# REAL recorded ranking of that round as the acceptance test.) ----
class _ScriptedSemantic:
    """A scripted vector seat: replays a recorded search ranking
    (the deterministic-tier law — replayed recordings + scripted
    inputs, never a live model)."""

    def __init__(self, rankings):
        self.rankings = rankings

    def search(self, token, top_k=None, kind=None):
        return [dict(h) for h in self.rankings.get(token, [])]


def _scripted_tokens(mentions, relations=()):
    return lambda q: {"mentions": list(mentions),
                      "relations": list(relations)}


def test_label_constraint_crowns_the_grain_the_user_named(world):
    read, entries, _, adj, directed = world
    by_id = {e["identity"]: e for e in entries}
    col = dict(by_id["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"])
    tab = dict(by_id[ADT])
    # the recorded 2026-09-11 ranking: the column edged the table
    semantic = _ScriptedSemantic({"ADT_EVENT": [
        {**col, "score": 1.603}, {**tab, "score": 1.470}]})
    r = mc.answer_question("what does the ADT_EVENT table mean",
                           _scripted_tokens(["ADT_EVENT", "table"]),
                           entries, semantic, read, adj, directed)
    assert r["label_constraint"] == ["table"]
    assert r["label_relaxed"] == []
    assert [a["identity"] for a in r["anchors"]] == [ADT]
    assert r["gql"] and "(a:table)" in r["gql"][0] \
        and "ADT_EVENTS" in r["gql"][0]


def test_meaning_card_default_names_the_grain_gets_the_meaning(
        world):
    # law 4 THE MEANING CARD DEFAULT (Sunny, 2026-09-13: "the
    # table question came back with too much information. can we
    # make table answers like the column answers?"): naming the
    # grain ("…table mean") delivers the anchor's OWN meaning row
    # — the old neighborhood dump was a population-size accident
    read, entries, _, adj, directed = world
    by_id = {e["identity"]: e for e in entries}
    col = dict(by_id["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"])
    tab = dict(by_id[ADT])
    semantic = _ScriptedSemantic({"ADT_EVENT": [
        {**col, "score": 1.603}, {**tab, "score": 1.470}]})
    r = mc.answer_question("what does the ADT_EVENT table mean",
                           _scripted_tokens(["ADT_EVENT", "table"]),
                           entries, semantic, read, adj, directed)
    assert r["mode"] == "list"
    assert len(r["rows"]) == 1
    assert r["rows"][0]["a"] == "ADT_EVENTS"
    assert "repository" in r["rows"][0]["words"]  # its own aboutness
    # the neighborhood stays ONE ASK away: the bare name keeps it
    r2 = mc.answer_question("ADT_EVENTS",
                            _scripted_tokens(["ADT_EVENTS"]),
                            entries, None, read, adj, directed)
    assert r2["mode"] == "neighborhood"


def test_label_constraint_is_a_proposal_never_a_veto(world):
    read, entries, _, adj, directed = world
    by_id = {e["identity"]: e for e in entries}
    col = dict(by_id["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"])
    # nothing labeled 'table' in the match set: the constraint
    # RELAXES and reports — the best overall still anchors
    semantic = _ScriptedSemantic(
        {"ADT_EVENT": [{**col, "score": 1.603}]})
    r = mc.answer_question("what does the ADT_EVENT table mean",
                           _scripted_tokens(["ADT_EVENT", "table"]),
                           entries, semantic, read, adj, directed)
    assert r["label_relaxed"] == [("ADT_EVENT", ["table"])]
    assert [a["identity"] for a in r["anchors"]] == \
        ["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"]
    html_out = mc.render_round(r)
    assert "constraint was relaxed" in html_out


def test_no_label_word_leaves_anchoring_unconstrained(world):
    read, entries, _, adj, directed = world
    by_id = {e["identity"]: e for e in entries}
    col = dict(by_id["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"])
    tab = dict(by_id[ADT])
    semantic = _ScriptedSemantic({"ADT_EVENT": [
        {**col, "score": 1.603}, {**tab, "score": 1.470}]})
    r = mc.answer_question("ADT_EVENT",
                           _scripted_tokens(["ADT_EVENT"]),
                           entries, semantic, read, adj, directed)
    assert r["label_constraint"] == []
    assert [a["identity"] for a in r["anchors"]] == \
        ["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"]


# ---- THE CHOICE STEP (ruled by Sunny 2026-09-11: after tokens
# match, the runners-up are OFFERED; a click pins a candidate and
# re-runs the round — the pin is the HUMAN ACT, outranking scores
# and constraints; a vanished pick is an honest miss) ---------------
def _adt_ranking(entries):
    by_id = {e["identity"]: e for e in entries}
    col = dict(by_id["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"])
    tab = dict(by_id[ADT])
    return {"ADT_EVENT": [{**col, "score": 1.603},
                          {**tab, "score": 1.470}]}


def test_pin_overrides_the_scored_crown(world):
    read, entries, _, adj, directed = world
    semantic = _ScriptedSemantic(_adt_ranking(entries))
    r = mc.answer_question("what does ADT_EVENT mean",
                           _scripted_tokens(["ADT_EVENT"]),
                           entries, semantic, read, adj, directed,
                           pins={"ADT_EVENT": ADT})
    assert [a["identity"] for a in r["anchors"]] == [ADT]
    assert r["pinned"] == [("ADT_EVENT", "ADT_EVENTS")]
    assert "pinned by you" in mc.render_round(r)


def test_pin_outranks_the_label_constraint(world):
    read, entries, _, adj, directed = world
    semantic = _ScriptedSemantic(_adt_ranking(entries))
    col_id = "emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"
    # the user said 'table' but PINNED the column — the human act
    # wins; no relaxation is reported (nothing was relaxed FOR him)
    r = mc.answer_question("what does the ADT_EVENT table mean",
                           _scripted_tokens(["ADT_EVENT", "table"]),
                           entries, semantic, read, adj, directed,
                           pins={"ADT_EVENT": col_id})
    assert [a["identity"] for a in r["anchors"]] == [col_id]
    assert r["label_relaxed"] == []


def test_a_vanished_pick_is_an_honest_miss(world):
    read, entries, _, adj, directed = world
    semantic = _ScriptedSemantic(_adt_ranking(entries))
    r = mc.answer_question("what does ADT_EVENT mean",
                           _scripted_tokens(["ADT_EVENT"]),
                           entries, semantic, read, adj, directed,
                           pins={"ADT_EVENT": "emr|dbo|GONE"})
    assert r["pin_misses"] == [("ADT_EVENT", "emr|dbo|GONE")]
    # the round proceeds unpinned on the scored crown
    assert [a["identity"] for a in r["anchors"]] == \
        ["emr|dbo|ED_EVENT_INFO|ADT_EVENT_ID"]
    assert "no longer in the match set" in mc.render_round(r)


def test_the_runners_up_are_offered_as_picks(world):
    read, entries, _, adj, directed = world
    semantic = _ScriptedSemantic(_adt_ranking(entries))
    r = mc.answer_question("what does ADT_EVENT mean",
                           _scripted_tokens(["ADT_EVENT"]),
                           entries, semantic, read, adj, directed)
    out = mc.render_round(r)
    assert "choose for 'ADT_EVENT'" in out
    assert 'class=pick' in out
    assert 'data-ident="emr|dbo|ADT_EVENTS"' in out   # the runner-up
    assert "ADT_EVENTS (table, 1.47)" in out


# ---- THE MATCHED GRAPH (ruled by Sunny 2026-09-11: the crown
# rule is dead — let the matched graph drive the query and the
# delivery; acceptance = the EVENT_ID round) ------------------------
EVENT_ID_TABLES = ["ADT_EVENTS", "ED_EVENT_INFO", "ED_PATIENT_INFO",
                   "V_PATIENT_LOCATION_HISTORY"]


def test_matched_graph_enumerates_the_event_id_carriers(world):
    # THE ACCEPTANCE ROUND: 'show me all tables that use EVENT_ID'
    # — 'tables' grounds as the kind (scripted; kind-vs-instance
    # crowning is a recorded open finding), EVENT_ID exact-matches
    # ALL four carrier columns; the existing has_part edges ARE
    # the answer: exactly the four tables, as rows, with counts.
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::table")
    semantic = _ScriptedSemantic({"tables": [{**kind, "score": 1.2}]})
    r = mc.answer_question("show me all tables that use EVENT_ID",
                           _scripted_tokens(["tables", "EVENT_ID"]),
                           entries, semantic, read, adj, directed)
    assert r["mode"] == "enumeration"
    assert sorted({row["a"] for row in r["rows"]}) == EVENT_ID_TABLES
    # the 4 containment rows are all present; the third target
    # adds TRUE extra rows (tables whose join/condition logic
    # touches EVENT_ID, cited via the connective chain)
    hp = {(row["a"], row["b"]) for row in r["rows"]
          if row["edge"] == "has_part"}
    assert hp == {(t, "EVENT_ID") for t in EVENT_ID_TABLES}
    assert r["counts"]["connected"] == 4


def test_mechanical_net_catches_the_dropped_steering_word(world):
    # LAW 5 — THE MECHANICAL NET (Sunny's screenshot round,
    # 2026-09-13: the interpreter tokenized 'tables' · 'EVENT_ID'
    # and DROPPED 'contain'): the seat proposes, the closed
    # vocabulary guarantees — the question's own words sweep the
    # structure pool, no model attention required
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::table")
    hp = next(e for e in entries
              if e["identity"] == "edgekind::has_part")
    semantic = _ScriptedSemantic({
        "tables": [{**kind, "score": 1.2}],
        "contain": [{**hp, "score": 1.1}]})
    r = mc.answer_question(
        'show me all tables that contain "EVENT_ID"',
        _scripted_tokens(["tables", "EVENT_ID"]),  # seat drops it
        entries, semantic, read, adj, directed)
    assert r["net_caught"] == ["contain"]
    assert r["edge_constraints"] == ["has_part"]
    got = {(row["a"], row["edge"], row["b"]) for row in r["rows"]}
    assert got == {(t, "has_part", "EVENT_ID")
                   for t in EVENT_ID_TABLES}  # 4 rows, no dupes


def test_ownership_default_when_no_steering_word(world):
    # LAW 6 — THE OWNERSHIP DEFAULT: silence defaults to the
    # ownership relation; the connective routes never row here
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::table")
    semantic = _ScriptedSemantic({"tables": [{**kind, "score": 1.2}]})
    r = mc.answer_question(
        "show me all tables with EVENT_ID",
        _scripted_tokens(["tables", "EVENT_ID"]),
        entries, semantic, read, adj, directed)
    assert r["edge_constraints"] == []  # nothing steered
    assert all(row["edge"] == "has_part" for row in r["rows"])
    assert sorted({row["a"] for row in r["rows"]}) == EVENT_ID_TABLES
    assert len(r["rows"]) == 4  # one row per member, ownership only


def test_member_grain_holds_even_on_the_wide_reach(world):
    # LAW 7 — MEMBER GRAIN: reach=wide delivers the connective
    # routes too, but never two rows for one (member, anchor) —
    # farther routes are counted, the nearest cites
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::table")
    semantic = _ScriptedSemantic({"tables": [{**kind, "score": 1.2}]})
    r = mc.answer_question(
        "show me all tables with EVENT_ID",
        _scripted_tokens(["tables", "EVENT_ID"]),
        entries, semantic, read, adj, directed, reach="wide")
    keys = [(row["a_id"], row["b_id"]) for row in r["rows"]]
    assert len(keys) == len(set(keys))  # one row per member-anchor
    assert r["counts"].get("extra_routes", 0) >= 1  # routes counted
    assert r["counts"]["population"] == 90
    assert r["counts"]["label"] == "table"
    assert len(r["anchors"]) == 4          # nothing discarded
    gql = r["gql"][0]
    assert "(a:table)" in gql and "has_part" in gql \
        and "EVENT_ID" in gql
    out = mc.render_round(r)
    assert "<table class=rows>" in out
    assert "4 of 90 table(s) connect; 86 do not." in out


def test_kind_subsumption_beats_circular_label_credit(world):
    # measured live 2026-09-11: 'tables' scored table INSTANCES
    # above the kind entry (their own label cards — circular
    # credit); the ruled rule: a kind >= MATCH_SCORE whose name
    # equals the top instance's label CLAIMS the token
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::table")
    a_table = next(e for e in entries if e["label"] == "table")
    semantic = _ScriptedSemantic({"tables": [
        {**dict(a_table), "score": 1.760},
        {**dict(kind), "score": 1.576}]})
    r = mc.answer_question("show me all tables that use EVENT_ID",
                           _scripted_tokens(["tables", "EVENT_ID"]),
                           entries, semantic, read, adj, directed)
    assert r["mode"] == "enumeration"
    assert sorted({row["a"] for row in r["rows"]}) == EVENT_ID_TABLES


def test_exact_set_keeps_all_equal_citizens(world):
    # one token, four exact matches: the set IS the answer (list
    # mode) — the old crown rule kept one and dropped three
    read, entries, _, adj, directed = world
    r = mc.answer_question("EVENT_ID", None, entries, None,
                           read, adj, directed)
    assert r["mode"] == "list"
    assert sorted({row["b"] for row in r["rows"]}) == EVENT_ID_TABLES
    assert len(r["anchors"]) == 4


def test_list_rows_carry_the_meaning(world):
    # Sunny's BED_STAY_ID round (2026-09-11): 'what does the
    # column BED_STAY_ID mean' listed name+owner but dropped the
    # DESCRIPTIONS — a meaning question must deliver the meaning
    read, entries, _, adj, directed = world
    r = mc.answer_question("BED_STAY_ID", None, entries, None,
                           read, adj, directed)
    assert r["mode"] == "list" and len(r["rows"]) == 2
    assert all(row["words"] for row in r["rows"])
    out = mc.render_round(r)
    assert "serial_number" in out or "bed" in out.lower()


def test_same_named_picks_are_owner_qualified(world):
    read, entries, _, adj, directed = world
    r = mc.answer_question("BED_STAY_ID", None, entries, None,
                           read, adj, directed)
    out = mc.render_round(r)
    assert "ADT_EVENTS.BED_STAY_ID" in out
    assert "BED_CONFIG.BED_STAY_ID" in out


def test_neighborhood_cap_is_counted_never_silent(world):
    # the ADT_EVENTS round showed 20 columns with no remainder —
    # the visible cap must COUNT what it hides
    read, entries, _, adj, directed = world
    r = mc.answer_question("ADT_EVENTS", None, entries, None,
                           read, adj, directed)
    assert r["mode"] == "neighborhood"
    shown, total = r["capped"]
    assert shown == 20 and total > 20
    assert f"showing 20 of {total} connections" in \
        mc.render_round(r)


def test_kind_alone_lists_its_population(world):
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::table")
    semantic = _ScriptedSemantic({"tables": [{**kind, "score": 1.2}]})
    r = mc.answer_question("show me the tables",
                           _scripted_tokens(["tables"]),
                           entries, semantic, read, adj, directed)
    assert r["mode"] == "list"
    assert len(r["rows"]) == 90
    assert "showing 20 of 90 rows" in mc.render_round(r)


def test_semantic_band_stays_narrow_within_the_margin(world):
    # the recorded ADT_EVENT ranking: 1.603 vs 1.470 — outside
    # UNIQUE_MARGIN, so the band holds ONE member and behaves like
    # the old single-anchor round (paths stay paths)
    read, entries, _, adj, directed = world
    semantic = _ScriptedSemantic(_adt_ranking(entries))
    r = mc.answer_question("what does ADT_EVENT mean",
                           _scripted_tokens(["ADT_EVENT"]),
                           entries, semantic, read, adj, directed)
    assert r["mode"] == "neighborhood"
    assert len(r["anchors"]) == 1


# ---- THE SECOND TARGET: the join layer (M2, ruled 2026-09-11 —
# scopes speak, joins are connective structure, THE PASS-THROUGH
# RULE makes scope—join—table ONE connection) -----------------------
SCOPE_BASE_POP = "reporting/USP_ED_SEPSIS.sql::#Base_Pop"


def test_scopes_speak_in_the_index(world):
    _, entries, _, _, _ = world
    sc = next(e for e in entries if e["identity"] == SCOPE_BASE_POP)
    assert sc["label"] == "scope"
    # grammar 2.4.0: the floor opens with the composition sentence
    assert sc["words"].startswith("drawn from")


def test_join_layer_adjacency_walks_scope_join_table(world):
    read, _, _, adj, _directed = world
    j1 = SCOPE_BASE_POP + "::join#1"
    assert any(b == j1 and lbl == "has_part"
               for b, lbl in adj[SCOPE_BASE_POP])
    sides = {b for b, lbl in adj[j1]
             if lbl in ("left_side", "right_side")}
    assert sides & {"emr|dbo|ED_ENCOUNTERS_FACT",
                    "emr|dbo|HOSPITAL_ENCOUNTERS"}


def test_connection_without_a_relation_word_keeps_both(world):
    # the 2026-09-11 impact view, RE-HOMED (2026-09-14): a question
    # naming NO relation asks CONNECTION, and the co-side
    # connection is store truth worth showing — #ADT owns the
    # joins, #Base_Pop is joined AGAINST the table in #ADT's join
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::scope")
    semantic = _ScriptedSemantic(
        {"scopes": [{**dict(kind), "score": 1.2}]})
    r = mc.answer_question("which scopes touch ADT_EVENTS?",
                           _scripted_tokens(["scopes",
                                             "ADT_EVENTS"]),
                           entries, semantic, read, adj, directed)
    assert r["mode"] == "enumeration"
    assert {row["a"] for row in r["rows"]} == {"#ADT", "#Base_Pop"}
    assert all(row["edge"].startswith("via ") for row in r["rows"])
    assert r["counts"]["population"] == 44


def test_read_word_grounds_by_declared_edge_speech(world):
    # THE READS VOCABULARY (Sunny's live round, 2026-09-14: 'read'
    # had no entry to ground against, so the question fell to the
    # free connection walk): the reads edge kind now speaks, and
    # its declared synonym head grounds 'read' EXACTLY — no model
    _, entries, _, _, _ = world
    assert any(e["identity"] == "edgekind::reads" for e in entries)
    m = mc.match_token("read", entries, None)
    assert m["tier"] == "exact"
    assert m["matches"][0]["identity"] == "edgekind::reads"


def test_reads_relation_rows_the_owner_never_the_co_side(world):
    # THE M2 SEMANTICS REACH THE ASK (2026-09-14, superseding the
    # 2026-09-11 both-scopes pin for READ-worded questions): the
    # reader is the join's OWNER; a scope on the join's other side
    # is being READ, not reading — excluded AND counted. The live
    # corpse: #Base_Pop rowed as a reader of ADT_EVENTS while its
    # own composition sentence never mentions adt events.
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::scope")
    semantic = _ScriptedSemantic(
        {"scopes": [{**dict(kind), "score": 1.2}]})
    r = mc.answer_question(
        "which scopes read ADT_EVENTS?",
        _scripted_tokens(["scopes", "read", "ADT_EVENTS"],
                         relations=["read"]),
        entries, semantic, read, adj, directed)
    assert r["mode"] == "enumeration"
    assert "reads" in r["edge_constraints"]
    assert {row["a"] for row in r["rows"]} == {"#ADT"}
    assert r["counts"]["connected"] == 1
    assert r["counted_out"].get(
        "joined against (read by, never a reader)") == 1
    # the artifact renders only walks that rowed — never a
    # side-to-side (co-side) shape
    assert r["gql"]
    assert not any("left_side" in g and "right_side" in g
                   for g in r["gql"])


def test_reads_relation_includes_the_direct_reads(world):
    # era 3 (2026-09-14): the no-join FROM is a direct_read node —
    # a reads-worded question must include its owner as a reader
    read, entries, _, adj, directed = world
    store = read._store
    dr = read.nodes("direct_read")[0]
    edge = next(e for e in store.current_edges("left_side")
                if e.from_id == dr.identity)
    table_name = edge.to_id.rsplit("|", 1)[-1]
    scope_name = dr.identity.rsplit(
        "::read#", 1)[0].split("::")[-1]
    kind = next(e for e in entries if e["identity"] == "kind::scope")
    semantic = _ScriptedSemantic(
        {"scopes": [{**dict(kind), "score": 1.2}]})
    r = mc.answer_question(
        f"which scopes read {table_name}?",
        _scripted_tokens(["scopes", "read", table_name],
                         relations=["read"]),
        entries, semantic, read, adj, directed)
    assert scope_name in {row["a"] for row in r["rows"]}


def test_scope_neighborhood_cites_join_evidence(world):
    read, entries, _, adj, directed = world
    r = mc.answer_question("#Base_Pop", None, entries, None,
                           read, adj, directed)
    assert r["mode"] == "neighborhood"
    assert any(line.startswith("[join]") and "—" in line
               for line in r["evidence"])
    # Sunny's round (2026-09-11): the ANCHOR speaks IN FULL — the
    # floor's logic, not just its first sentence
    anchor_line = next(line for line in r["evidence"]
                       if line.startswith("[scope] #Base_Pop"))
    assert "drawn from" in anchor_line
    assert "locations records" in anchor_line   # the FULL list,
    # not the first sentence; the WHERE conditions are condition
    # grains — counted out until §D by the standing ruling
    # same-named joins carry their owner
    assert all("::join#" in line for line in r["evidence"]
               if line.startswith("[join]"))


def test_connection_walks_through_a_join(world):
    read, entries, _, adj, directed = world
    r = mc.answer_question("#Base_Pop ED_ENCOUNTERS_FACT", None,
                           entries, None, read, adj, directed)
    assert r["mode"] == "connection"
    assert not r["gaps"]
    assert r["gql"] and any(":join" in g for g in r["gql"])


# ---- THE THIRD TARGET: the condition layer (M3, ruled 2026-09-11
# — scope-rooted conditions speak their voiced phrases; ON
# conditions stay connective; the pass-through generalizes) --------
def test_scope_rooted_conditions_speak_on_conditions_stay_out(
        world):
    _, entries, exclusions, _, _ = world
    conds = [e for e in entries if e["label"] == "condition"]
    assert conds and all("::cond#" in e["identity"] for e in conds)
    # R5.b blessed vocabulary (2026-09-13): ADT_ARRIVAL_DATE
    # speaks its blessed name "arrival date"
    arrival = next(e for e in conds if "arrival date" in e["words"])
    assert arrival["identity"].endswith("#Base_Pop::cond#12")
    # the vacuous ON equalities are NOT searchable grains
    assert exclusions["condition_on"] > 0


def test_params_speak(world):
    _, entries, _, _, _ = world
    assert {e["name"] for e in entries if e["label"] == "param"} \
        == {"@dStartDate", "@dEndDate",
            "@StartDate", "@EndDate"}  # +2 at M5 (the IF params)


def test_where_bullets_join_the_scope_neighborhood(world):
    read, entries, _, adj, directed = world
    r = mc.answer_question("#ADT", None, entries, None,
                           read, adj, directed)
    assert r["mode"] == "neighborhood"
    assert any(line.startswith("[condition]")
               for line in r["evidence"])


def test_condition_pass_through_finds_the_filtering_scope(world):
    # 'which scopes filter on ADT_ARRIVAL_DATE?' — the chain
    # column ←resolves_to— cond#12 ←has_part— #Base_Pop is ONE
    # connection, cited by the leaf's voiced phrase
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::scope")
    semantic = _ScriptedSemantic(
        {"scopes": [{**dict(kind), "score": 1.2}]})
    r = mc.answer_question(
        "which scopes filter on ADT_ARRIVAL_DATE?",
        _scripted_tokens(["scopes", "ADT_ARRIVAL_DATE"]),
        entries, semantic, read, adj, directed)
    assert r["mode"] == "enumeration"
    hits = [row for row in r["rows"] if row["a"] == "#Base_Pop"]
    assert hits and any("arrival date" in row["edge"]
                        for row in hits)  # blessed words (R5.b)


def test_param_impact_enumerates_the_using_scopes(world):
    read, entries, _, adj, directed = world
    kind = next(e for e in entries if e["identity"] == "kind::scope")
    semantic = _ScriptedSemantic(
        {"scopes": [{**dict(kind), "score": 1.2}]})
    r = mc.answer_question("which scopes use @dStartDate?",
                           _scripted_tokens(["scopes",
                                             "@dStartDate"]),
                           entries, semantic, read, adj, directed)
    assert r["mode"] == "enumeration"
    assert {row["a"] for row in r["rows"]} >= {"#Base_Pop"}


# ---- THE ARTIFACT LAW + OWNER-QUALIFY (fixes 2026-09-12, from
# Sunny's condition & param screenshots: the artifact rendered
# condition-[:has_part]->scope — backwards — and a fictional
# column-[:has_part]->scope; cond#1 rendered twelve times bare) ----
def _base_pop_condition_round(world):
    read, entries, _, adj, directed = world
    return mc.answer_question(
        "what condition does #Base_Pop have?",
        _scripted_tokens(["condition", "#Base_Pop"]),
        entries, None, read, adj, directed)


def test_enumeration_artifact_directions_are_store_truth(world):
    # the screenshot corpse: MATCH (a:condition)-[:has_part]->
    # (b:scope) — the store's edge runs scope—has_part→condition
    r = _base_pop_condition_round(world)
    assert r["mode"] == "enumeration" and r["rows"]
    assert ("MATCH (a:condition)<-[:has_part]-(b:scope) FILTER "
            "(b.name = '#Base_Pop') AND a.kind <> 'AND' AND "
            "a.kind <> 'OR' AND a.degenerate <> 'true' "
            "RETURN a.name, b.name") in r["gql"]
    for g in r["gql"]:
        assert "(a:condition)-[:has_part]->" not in g
        assert g.startswith("MATCH ") and " FILTER " in g \
            and " RETURN " in g and "type(" not in g


def test_enumeration_artifact_covers_the_pass_through(world):
    # the artifact describes the DELIVERED walk (the live-fire
    # finding): condition rows now descend the tree, so the
    # descent shapes appear; join-chain shapes live where joins
    # still row the walk — the column population (see the column
    # test) — because STRUCTURE NEVER ROWS killed them here
    # #Base_Pop's own answer is ONE direct WHERE condition (the
    # arrival-window RANGE) — one shape, exactly
    r = _base_pop_condition_round(world)
    assert r["gql"] == [
        "MATCH (a:condition)<-[:has_part]-(b:scope) FILTER "
        "(b.name = '#Base_Pop') AND a.kind <> 'AND' AND "
        "a.kind <> 'OR' AND a.degenerate <> 'true' "
        "RETURN a.name, b.name"]
    # #AllMeds' filters sit under its AND root — the descent shape
    ra = _allmeds_filters_round(world)
    assert any("(c1:condition)<-[:has_part]-(b:scope)" in g
               for g in ra["gql"])
    assert not any(":join)" in g for g in ra["gql"])


def test_near_first_default_owns_the_condition_answer(world):
    # THE NEAR-FIRST DEFAULT (ruled "all 3, go"): an owner anchor
    # asking about its owned logic answers from its OWN subtree —
    # the 60-row flood of 2026-09-12's screenshots is dead; what
    # the walk excludes is COUNTED by class, never lost
    r = _base_pop_condition_round(world)
    owners = {row["a_id"].rsplit("::", 2)[-2]
              for row in r["rows"]}
    assert owners == {"#Base_Pop"}
    assert "join structure" in r["counted_out"]
    # display names are bare when unique — no false qualification
    seen = {}
    for row in r["rows"]:
        seen.setdefault(row["a"], set()).add(row["a_id"])
    assert all(len(ids) == 1 for ids in seen.values())


def test_column_enumeration_artifact_never_invents_an_edge(world):
    # 'what filters are in the #Base_Pop subquery' emitted
    # MATCH (a:column)-[:has_part]->(b:scope) — no such edge exists
    # in the design; columns reach scopes through conditions/joins
    read, entries, _, adj, directed = world
    kind = next(e for e in entries
                if e["identity"] == "kind::column")
    semantic = _ScriptedSemantic(
        {"filters": [{**dict(kind), "score": 1.2}]})
    # reach=wide since law 6 (2026-09-13): the ownership default
    # counts the join-side routes instead of rowing them — the
    # side shapes this test pins only DELIVER on the wide reach
    r = mc.answer_question(
        "what filters are in the #Base_Pop subquery",
        _scripted_tokens(["filters", "#Base_Pop"]),
        entries, semantic, read, adj, directed, reach="wide")
    assert r["mode"] == "enumeration" and r["rows"]
    for g in r["gql"]:
        assert "(a:column)-[:has_part]->(b:scope)" not in g
    assert any(":resolves_to]" in g for g in r["gql"])
    # the join-chain shapes live HERE (columns row through joins;
    # condition enumerations count them as structure instead)
    assert any(":join)" in g for g in r["gql"])
    assert any("_side]->(b:scope)" in g for g in r["gql"])
    # the ENCOUNTER_ID flood owner-qualifies (TABLE.COLUMN)
    seen = {}
    for row in r["rows"]:
        seen.setdefault(row["a"], set()).add(row["a_id"])
    assert all(len(ids) == 1 for ids in seen.values())
    assert any(row["a"].endswith(".ENCOUNTER_ID")
               for row in r["rows"])


# ---- THE STRUCTURE-WORD CLAIM + THE RELATION-WORD SEAT (ruled
# 2026-09-12, Sunny's "fix these gaps" after the #AllMeds
# gap-check; prompt 3.1.0 unparked by the same word) + THE
# MEANING ROWS (his "all 3, go": structure never rows ·
# near-first default · composites compose) ------------------------
def _allmeds_filters_round(world, kind_id="kind::condition",
                           relations=(), reach="near"):
    read, entries, _, adj, directed = world
    by_id = {e["identity"]: e for e in entries}
    kind = dict(by_id[kind_id])
    hp = dict(by_id["edgekind::has_part"])
    noise = dict(next(e for e in entries if e["label"] == "column"))
    # the screenshot ranking shape: a noise column instance on top,
    # the structure entries beneath — all above MATCH_SCORE
    semantic = _ScriptedSemantic({
        "filters": [{**noise, "score": 1.41},
                    {**kind, "score": 1.35}],
        "in": [{**noise, "score": 1.2}, {**hp, "score": 0.9}]})
    mentions = ["filters", "#AllMeds"] + (["in"] if relations
                                          else [])

    def interp(q):
        # literal: shape
        return {"mentions": mentions, "relations": list(relations)}
    return mc.answer_question(
        "what filters are in the #AllMeds subquery?", interp,
        entries, semantic, read, adj, directed, reach=reach)


def test_structure_word_claims_over_noise_instances(world):
    # the screenshot corpse: kind 'column' claimed 'filters' via
    # the NOISE instance's label; the ruled law claims by the
    # kind's OWN score — 'filters' reaches kind condition
    r = _allmeds_filters_round(world)
    assert r["label_constraint"] == ["condition"]
    assert r["mode"] == "enumeration"
    assert r["counts"]["label"] == "condition"


def test_relation_word_constrains_traversal_and_counts(world):
    # 'in' (relation-marked) grounds as the has_part edge kind on
    # a COLUMN population: the walk keeps #AllMeds' own structure;
    # columns reached only through other scopes' joins are
    # EXCLUDED AND COUNTED
    r = _allmeds_filters_round(world, kind_id="kind::column",
                               relations=("in",))
    assert r["edge_constraints"] == ["has_part"]
    assert r["mode"] == "enumeration" and r["rows"]
    assert r["constrained_out"] >= 1
    out = mc.render_round(r)
    assert "connect only outside the constrained edge kind(s)" \
        in out


def test_condition_tree_delivers_whole(world):
    # THE MEANING ROWS (Sunny's ruled #AllMeds table, "all 3,
    # go"): the answer IS the four filters, each speaking its
    # phrase — structure frames, folds, and counts; it never rows
    r = _allmeds_filters_round(world)
    by_tail = {row["a_id"].rsplit("::", 1)[-1]: row
               for row in r["rows"]}
    assert set(by_tail) == {"cond#6", "cond#8", "cond#9",
                            "cond#10"}
    # NOT folded into its child — the positive fact spoken with
    # the name-words subject (grammar 2.5.0 + 2.6.0), and since
    # the records-records sitting blessed MED_ADMIN_RECORDS
    # (2026-09-15), R5.c's owner-possessive speaks: "the
    # medication administration's taken time". (This pin went
    # stale at that blessing — the sitting ran the estate battery,
    # not the console round; caught at the M4 full-suite gate.)
    assert by_tail["cond#6"]["words"] == \
        "the medication administration's taken time is recorded."
    # 2.7.0 THE RELATION RULE: name words BOTH sides + the SQL
    # author's noted intent riding (Sunny's "still not fixed" round)
    assert by_tail["cond#8"]["words"] == ("the taken time is before "
                                          "the ed departure time "
                                          "(noted 'while in ed').")
    # R5.b blessed vocabulary (Sunny's delegated curation,
    # 2026-09-13): MED_ROUTE_CODE speaks "medication route"
    assert by_tail["cond#9"]["words"] == ("the medication route is "
                                          "11 (noted "
                                          "'intravenous').")
    assert "is one of the values" in by_tail["cond#10"]["words"]
    # the conjunction semantics FRAME the list
    assert r["frames"] and "AND" in r["frames"][0]
    # the frame line speaks — frame-descent rows cite NOTHING
    # (Sunny's live round: the vacuous arity via is dead)
    assert all(row["edge"] == "" for row in r["rows"])
    # the artifact carries the class exclusions (the live DIVERGE:
    # served rows included the 1=1 degenerate)
    assert all("a.kind <> 'AND'" in g
               and "a.degenerate <> 'true'" in g
               for g in r["gql"])
    # literal: shape — Sunny's ruled exclusion classes, exact
    assert r["counted_out"] == {"join structure": 3, "frame": 1,
                                "degenerate": 1,
                                "folded into NOT": 1}
    out = mc.render_round(r)
    assert "frame:" in out and "not rows, counted:" in out


def test_wide_reach_keeps_the_laws(world):
    # the wider reach is ONE CLICK AWAY (near-first default) —
    # and structure still never rows there; display names stay
    # unique per identity (the owner-qualify invariant)
    near = _allmeds_filters_round(world)
    wide = _allmeds_filters_round(world, reach="wide")
    assert len(wide["rows"]) >= len(near["rows"])
    assert wide["far_out"] == 0          # nothing hidden near
    assert "frame" in wide["counted_out"]
    seen = {}
    for row in wide["rows"]:
        seen.setdefault(row["a"], set()).add(row["a_id"])
    assert all(len(ids) == 1 for ids in seen.values())


def test_relation_word_never_instance_anchors(world):
    # the estate holds a grain literally named 'In' — a
    # relation-marked token must not be captured by it; with no
    # structure entry clearing the bar it is a COUNTED no-claim
    read, entries, _, adj, directed = world

    def interp(q):
        # literal: shape
        return {"mentions": ["ADT_EVENTS", "in"],
                "relations": ["in"]}
    r = mc.answer_question("in ADT_EVENTS", interp, entries, None,
                           read, adj, directed)
    assert r["relation_unclaimed"] == ["in"]
    assert all(m["name"] != "In" for m in r["anchors"])
    assert "matched no structure vocabulary" in mc.render_round(r)


def test_edge_kinds_speak_their_own_speech(world):
    _, entries, _, _, _ = world
    hp = next(e for e in entries
              if e["identity"] == "edgekind::has_part")
    assert "contains" in hp["words"]        # the _edge speech row
    assert "spine" not in hp["words"]       # Notes retired as speech


def test_cage_validates_relations():
    from aisql.flows import ask
    out = ask.validate_interpretation(
        {"mentions": ["tables", "in", "X"],
         "relations": ["in", "in", "ghost", 7]})
    assert out["relations"] == ["in"]       # mentions only, deduped
    out = ask.validate_interpretation(
        {"mentions": ["X"], "relations": "in"})
    assert "relations" not in out           # a non-list is refused


def test_owner_qualify_deepens_only_until_unique():
    # literal: shape — authored collision fixture
    rows = [{"a": "ENCOUNTER_ID", "a_id": "emr|dbo|T1|ENCOUNTER_ID"},
            {"a": "ENCOUNTER_ID", "a_id": "emr|dbo|T2|ENCOUNTER_ID"},
            {"a": "LONELY_COL", "a_id": "emr|dbo|T1|LONELY_COL"},
            {"a": "cond#1", "a_id": "f.sql::#A::join#1::cond#1"},
            {"a": "cond#1", "a_id": "f.sql::#B::join#1::cond#1"}]
    mc.owner_qualify(rows)
    assert rows[0]["a"] == "T1.ENCOUNTER_ID"
    assert rows[1]["a"] == "T2.ENCOUNTER_ID"
    assert rows[2]["a"] == "LONELY_COL"          # unique stays bare
    # depth 2 (join#1::cond#1) still collides → depth 3 resolves
    assert rows[3]["a"] == "#A::join#1::cond#1"
    assert rows[4]["a"] == "#B::join#1::cond#1"


# ---- the glossary chain (the machinery lives in flows/glossary;
# tests/aisql/test_glossary.py owns it — this proves the CONSOLE
# INDEX carries the blessed expansions end-to-end) -------------------
def test_blessed_acronyms_join_the_console_index(tmp_path):
    from aisql.flows import glossary
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


# ---- THE LIVE MEANING BATTERY (BLESSED in full, 2026-09-11) ---------
live = pytest.mark.skipif(
    not os.environ.get("AISQL_LIVE"),
    reason="the live battery runs with AISQL_LIVE=1 (live-seat rule)")

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
    # THE FIRST MEANING FINDING, closed 2026-09-11: born as
    # "...alternatives?" xfail (crown unfindable, rank 25, no
    # blessed acronyms). Sunny ruled alt=ALERT on evidence (the
    # description counts warnings; the crosswalk shows Epic
    # ALT=alert), blessed the vocabulary, and re-drafted the
    # question to the truthful wording — a normal battery member
    # since.
    ("column-search",
     "which column counts wrong medication alerts?",
     ["WRONG_MED_ALT_CNT"]),
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
    # ---- SUNNY'S SIX (hand-tested on the web UI and PASSED,
    # 2026-09-11 — blessed by use; pinned as regression guards
    # across all engine modes) --------------------------------
    ("meaning-readback",
     "what does the ADT_EVENT table mean",
     ["ADT_EVENTS"]),
    ("meaning-readback",
     "what does the column BED_STAY_ID mean",
     ["BED_STAY_ID"]),
    ("enumeration",
     "which tables contain the column BED_ID",
     ["BED_CONFIG", "HOSPITAL_ENCOUNTERS"]),
    ("enumeration",
     'show me all tables that contain "EVENT_ID"',
     ["ED_PATIENT_INFO", "V_PATIENT_LOCATION_HISTORY"]),
    ("relationship",
     "how do tables ADT_EVENTS and ED_PATIENT_INFO join?",
     ["ADT_EVENTS", "ED_PATIENT_INFO"]),
    ("impact",
     "IF i update the column ENCOUNTER_ID, which tables are "
     "impacted?",
     ["ED_ENCOUNTERS_FACT", "HOSPITAL_ENCOUNTERS"]),
    # ---- THE JOIN-LAYER FAMILY (the second target — BLESSED
    # with the rest, "bless them all" 2026-09-11) --------------
    ("scope-meaning",
     "what does the #Base_Pop selection mean?",
     ["#Base_Pop"]),
    ("scope-enumeration",
     "which scopes read ADT_EVENTS?",
     ["#ADT"]),
    ("scope-reads",
     "which tables does the #AllMeds selection use?",
     ["MEDICATION_ORDERS", "MED_ADMIN_RECORDS"]),
    ("relationship",
     "how do #AllMeds and MEDICATION_ORDERS connect?",
     ["#AllMeds", "MEDICATION_ORDERS"]),
    # ---- THE CONDITION FAMILY (the third target — DRAFTED
    # 2026-09-11 night; blessing per the standing path) --------
    ("condition-meaning",
     "what conditions does #Base_Pop apply?",
     ["#Base_Pop"]),
    ("condition-filter",
     "which scopes filter on the patient arrival date?",
     ["#Base_Pop"]),
    ("param-impact",
     "which scopes use the @dStartDate parameter?",
     ["#Base_Pop"]),
]


@pytest.fixture(scope="module")
def live_world(world):
    from aisql.console import EMBEDDING_MODEL, _env_key, make_embedder, make_interpreter
    from aisql.flows import grounding
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
        + [row["a"] for row in r.get("rows", [])]
        + [row["b"] for row in r.get("rows", [])]
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
