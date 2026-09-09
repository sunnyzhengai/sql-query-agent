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

from .test_ask_console import fake_embed, fake_interpreter, seed_vocabulary

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
                                       "fake-2k", cache_path=None)
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
    target = next(e for e in index if e["label"] == "file"
                  and e["identity"].endswith(
                      "reporting/USP_ED_SEPSIS.sql"))
    assert "emergency department" in target["words"].lower()


# ---- census 2+3: speech and searchability ----------------------------
def test_conditions_speak_and_carry_owners(world):
    _store, _read, index, _semantic = world
    conditions = [e for e in index if e["label"] == "condition"]
    assert len(conditions) > 50  # the sepsis estate's voiced filters
    for c in conditions[:20]:
        assert c["words"]
        assert "::" in c["owner"]  # a scope key
        # the owner chain reaches a file
        files = {e["identity"] for e in index if e["label"] == "file"}
        owner_file = c["owner"].split("::")[0]
        assert any(f.endswith(owner_file) for f in files)


def test_labels_are_searchable_nodes(world):
    """ADAPTED 2026-09-07 (the kinds removal + THE SEARCH IS THE
    ANSWER): labels replaced kind nodes — derived from the live
    store, speaking their own plural."""
    _store, _read, index, _semantic = world
    labels = [e for e in index if e["label"] == "label"]
    assert labels
    file_label = next(e for e in labels if e["name"] == "file")
    assert file_label["words"] == "files"


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
def test_connection_census_succeeds_reachability(world):
    """Census 1's successor (the birth-edge law; the exemption list
    died under Sunny's review — its first two rows were both
    overruled)."""
    _store, read, _index, _semantic = world
    c = census.connection_census(read)
    assert c["birth_edged"] + c["counted_missing"] + c["rooted"] \
        == c["total"]
    assert c["unledgered_kinds"] == []  # closed at birth
    assert c["total"] > 4000


def test_connection_vacuity_detects_a_new_node(world):
    store, read, _index, _semantic = world
    # an orphan by design: the lawful API now REFUSES origin-less
    # terms (step 2), so the orphan enters as legacy data — a raw
    # store write — and the census still SEES it
    store.append_node("term", "term::vacuity-probe",
                      {"artifact_id": "term::vacuity-probe",
                       "name": "VACUITY_PROBE",
                       "definition": "an orphan by design",
                       "author": "person:test", "created_at": T0},
                      T0, "probe")
    c = census.connection_census(ReadApi(store))
    assert c["total"] >= 4001
    assert "term" in c["counted_missing_kinds"]


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


def test_ed_finds_reports_never_bed_config(world):
    """ADAPTED (the ranked search): 'ED' + its expansion find the
    ED files; BED_CONFIG never rides (whole-word vectors, not
    substrings)."""
    store, _read, _index, semantic = world
    q = "what reports are about ED"
    interp = fake_interpreter({q.lower(): {
        "mentions": ["ED"],
        "expansions": {"ED": ["emergency department"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    names = " ".join(h["name"] for h in result["hits"])
    assert "ED" in names or "SEPSIS" in names.upper()
    assert "BED_CONFIG" not in names


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
    # file, with the facet named (rollup + provenance, never blend).
    # The query is drawn from a real condition's voiced words
    # (USP_ED_SEPSIS #AllMeds c2) so the fake bag-of-words embedder
    # has true overlap to find, not hash luck.
    topic = "category number route of administration medication"
    q = f"what reports are about {topic}"
    interp = fake_interpreter({q: {"mentions": ["reports", topic]}})
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
    q = "the ed encounters table"
    interp = fake_interpreter(
        {q: {"mentions": ["ED_ENCOUNTERS_DM"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    trace = result["trace"]
    assert trace and (trace[0].get("tier")
                      or trace[0].get("searched_as"))


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


def test_facet_cards_name_card_wins_for_name_shaped_queries(world):
    _store, _read, _index, semantic = world
    # THE FACET DECISION's deciding case: 'ED Sepsis' finds the file
    # through its NAME card — the blend that buried it is dead
    hits = semantic.search("ED Sepsis", top_k=3, kind="file")
    assert hits[0]["name"] in ("USP_ED_SEPSIS", "USP_RPTS_ED_Sepsis")
    assert hits[0]["via_card"] == "name"
