"""ADR 0080 — the center and the three censuses, red-first.

The center law: readings never author — the ask index is a VERBATIM
projection of stored speech. The three censuses: reachable / speaks /
searchable as conservation equations. Riders: thresholds never
cliffs; the trace displays; expansions land as terms on confirmation.
The F10 census family (CE-1..5) executes here.

Proves: contract:aivia-design-to-code
"""
import pathlib

import pytest

from aivia.flows import ask, grounding, speech
from aivia.flows import censuses as census
from aivia.graph.read_api import ReadApi

from .test_ask_console import fake_embed, fake_interpreter, \
    seed_vocabulary

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
T0 = "2026-09-07T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _base = build_store("sepsis")
    seed_vocabulary(store)
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, fake_embed,
                                       "fake-64", cache_path=None)
    return store, read, index, semantic


# ---- the center law --------------------------------------------------
def test_verbatim_census_every_entry_is_stored_speech(world):
    _store, read, index, _semantic = world
    # the one-home law: every text the index carries equals the
    # node's declared speech, recomputed — a reading that authored
    # its own words cannot pass this
    for e in index:
        assert e["words"] == speech.speak(read, e), e["identity"]


def test_mutation_probe_index_reads_never_rederives(world):
    store, _read, index, _semantic = world
    node = next(n for n in store.current_nodes("column")
                if n.identity.endswith("ED_ENCOUNTERS_FACT|ENCOUNTER_ID"))
    original = node.properties.get("description")
    try:
        node.properties["description"] = "A PROBE SENTINEL sentence."
        fresh = ask.build_index(ReadApi(store))
        entry = next(e for e in fresh
                     if e["identity"] == node.identity)
        assert "probe sentinel" in entry["words"].lower()
    finally:
        node.properties["description"] = original


def test_composition_stored_in_twin_carries_the_subject(world):
    store, _read, _index, _semantic = world
    # CE-1 (the cause-1 corpse): the translator STORES the file's
    # up-composed subject; it carries emergency-department meaning,
    # never only the self-referential delivery slice
    twin_node = next(n for n in store.current_nodes("meaning_twin")
                     if n.identity.endswith(
                         "reporting/USP_ED_SEPSIS.sql"))
    subject = twin_node.properties["twin"]["subject"]
    assert "emergency department" in subject.lower()


def test_file_speech_reads_the_stored_subject(world):
    _store, _read, index, _semantic = world
    target = next(e for e in index if e["kind"] == "file"
                  and e["identity"].endswith(
                      "reporting/USP_ED_SEPSIS.sql"))
    assert "emergency department" in target["words"].lower()


# ---- census 2+3: speech and searchability ----------------------------
def test_conditions_speak_and_carry_owners(world):
    _store, _read, index, _semantic = world
    conditions = [e for e in index if e["kind"] == "condition"]
    assert len(conditions) > 50  # the sepsis estate's voiced filters
    for c in conditions[:20]:
        assert c["words"]
        assert "::" in c["owner"]  # a scope key
        # the owner chain reaches a file
        files = {e["identity"] for e in index if e["kind"] == "file"}
        owner_file = c["owner"].split("::")[0]
        assert any(f.endswith(owner_file) for f in files)


def test_kinds_are_searchable_nodes(world):
    _store, _read, index, _semantic = world
    kinds = [e for e in index if e["kind"] == "kind"]
    assert kinds  # node types are part of the search (ADR 0080)
    file_kind = next(e for e in kinds if e["name"] == "file")
    assert file_kind["words"]  # its registry definition speaks


def test_speech_census_equation(world):
    _store, read, index, _semantic = world
    c = census.speech_census(read, index)
    assert c["speaks"] + c["counted_gap"] + c["ruled_mute"] \
        == c["total"]
    assert c["unassigned_kinds"] == []  # closed at birth


def test_searchability_equation(world):
    _store, read, index, _semantic = world
    c = census.searchability_census(read, index)
    assert c["searchable"] + c["ruled_silent"] == c["speaks"]


# ---- census 1: reachability ------------------------------------------
def test_reachability_census(world):
    _store, read, _index, _semantic = world
    c = census.reachability_census(read)
    assert c["reachable"] + c["ruled_isolated"] == c["total"]
    assert c["isolated"] == []  # unruled orphans are a failure
    assert c["total"] > 4000


def test_reachability_vacuity_detects_an_orphan(world):
    store, read, _index, _semantic = world
    from aivia.graph import kg3_artifacts
    kg3_artifacts.append_term(store, "term::vacuity-probe",
                              "VACUITY_PROBE", "an orphan by design",
                              "person:test", T0)
    c = census.reachability_census(ReadApi(store))
    # the census SEES the new node — a census that can't move is
    # decoration
    assert c["total"] >= 4001
    assert "term" in c["ruled_isolated_kinds"] \
        or "term::vacuity-probe" in c["isolated"]


# ---- riders: no cliffs, word grain, honest zero ----------------------
def test_no_cliffs_below_threshold_yields_scored_candidates(world):
    _store, _read, index, semantic = world
    kinds = ask._earned_vocabulary(_read)
    # 'encounter' shares meaning words with many entries: below
    # MATCH_SCORE it must surface as candidates WITH scores — never
    # 'unknown' while hits stand above the floor
    g = grounding.ground("encounter details", index, kinds, semantic)
    assert g["outcome"] in ("matched", "candidates")
    if g["outcome"] == "candidates":
        assert all("score" in c for c in g["candidates"])
    # true noise is still an honest unknown (deterministic tiers;
    # the 64-dim fake embedder hash-collides random strings into
    # common buckets, so the no-semantic path proves the branch)
    g2 = grounding.ground("zzqqxx", index, kinds, None)
    assert g2["outcome"] == "unknown"


def test_thresholds_come_from_the_registry():
    t = grounding.thresholds()
    assert t["MATCH_SCORE"] == 0.5
    assert t["CANDIDATE_FLOOR"] == 0.25


def test_word_grain_ed_finds_reports_never_bed_config(world):
    store, _read, _index, semantic = world
    q = "what reports are about ED"
    interp = fake_interpreter({q: {"mentions": ["reports", "ED"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    assert result["pending_confirmation"]  # L7-D2: inline, non-blocking
    final = ask.confirm(store, q, result["interpretation"],
                        "person:test", T0, semantic=semantic)
    assert final["status"] == "answer"
    assert "USP_ED_SEPSIS" in final["answer"]
    assert "BED_CONFIG" not in final["answer"]


def test_honest_zero_never_no_match_while_a_kind_grounded(world):
    store, _read, _index, semantic = world
    q = "what terms are about xylophone"
    interp = fake_interpreter({q: {"mentions": ["terms",
                                                "xylophone"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    if result.get("pending_confirmation"):
        result = ask.confirm(store, q, result["interpretation"],
                             "person:test", T0, semantic=semantic)
    assert result["status"] == "answer"
    assert "NO MATCH" not in result["answer"]
    assert "0 " in result["answer"]  # the counted zero speaks


def test_facet_rollup_with_provenance(world):
    store, _read, _index, semantic = world
    # CE-3: a query matching a CONDITION facet surfaces the owning
    # file, with the facet named (rollup + provenance, never blend)
    q = "what reports are about best practice alert"
    interp = fake_interpreter({q: {"mentions":
                                   ["reports", "best practice alert"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    if result.get("pending_confirmation"):
        result = ask.confirm(store, q, result["interpretation"],
                             "person:test", T0, semantic=semantic)
    assert result["status"] == "answer"
    assert "USP_ED_SEPSIS" in result["answer"]
    assert "via" in result["answer"].lower()  # provenance visible


# ---- riders: the trace and expansions --------------------------------
def test_trace_rides_every_answer(world):
    store, _read, _index, semantic = world
    result = ask.ask(store, "emr|dbo|ED_ENCOUNTERS_DM",
                     "person:test", T0, semantic=semantic)
    assert result["status"] == "answer"
    trace = result["trace"]
    assert trace and trace[0]["tier"]  # what was searched, and how


def test_expansions_are_searched_and_confirmation_lands_a_term(world):
    store, _read, _index, semantic = world
    q = "which reports cover the emergency dept"
    interp = fake_interpreter({q: {
        "mentions": ["reports", "emergency dept"],
        "expansions": {"emergency dept": ["emergency department"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    assert result["pending_confirmation"]  # L7-D2: inline, non-blocking
    final = ask.confirm(store, q, result["interpretation"],
                        "person:test", T0, semantic=semantic)
    assert final["status"] == "answer"
    assert any(t.get("expansions_tried") for t in final["trace"])
    # the confirmation landed the vocabulary as a KG3 term: the
    # ledger remembers, the next session grounds it as data
    read2 = ReadApi(store)
    terms = [n for n in read2.nodes("term")
             if n.properties.get("name", "").lower()
             == "emergency dept"]
    assert terms
    assert "emergency department" in \
        terms[0].properties["definition"].lower()
