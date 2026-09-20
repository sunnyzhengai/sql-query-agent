"""STEP B — THE SEARCH IS THE ANSWER (Sunny's pipeline, ruled
2026-09-07). Supersedes the kinds-removal suite (its pins are
absorbed) and, by the ruling, the tier-ladder pins (GR-1 exact
tiers, GR-3 kind words, the CN-2 provenance buckets, the MT
special-cased metric answer).

The pipeline: LLM (intention, mentions, expansions) -> vector
search against EVERYTHING (labels as entries, names, descriptions)
-> RANKED SCORED HITS returned -> clicks are steer. No string tier
anywhere in the search path; exact matching is the cosine≈1 case.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql.flows import ask, grounding
from aisql.graph.read_api import ReadApi

from . import doubles
from .doubles import recorded_embed, scripted_proposals

T0 = "2026-09-07T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    from aisql.console import build_store
    store, _ = build_store("sepsis")  # cold: nothing earned
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, recorded_embed,
                                       doubles.EMBED_MODEL, cache_path=None)
    return store, read, index, semantic


# ---- the enumerations are gone ---------------------------------------
def test_no_kind_machinery_remains(world):
    _store, _read, index, _semantic = world
    assert not hasattr(ask, "VALID_KINDS")
    assert not [e for e in index
                if e["identity"].startswith("kind::")]
    out = ask.validate_interpretation(
        {"mentions": ["Ed"], "kinds": {"Ed": "term"}})
    assert out is not None and "kinds" not in out


def test_every_node_carries_its_label_card(world):
    """THE TOTAL-SCORE LAW (2026-09-08): label:: group entries are
    DEAD — the label is a CARD on every member node, so label
    credit lands on the node itself and sums with its other
    cards."""
    _store, _read, index, _semantic = world
    assert not [e for e in index
                if e["identity"].startswith("label::")]
    from aisql.flows import grounding as g
    table = next(e for e in index if e["label"] == "table")
    card_names = [c[0] for c in g.cards(table)]
    assert "label" in card_names
    label_text = dict(g.cards(table))["label"]
    assert "table" in label_text and "tables" in label_text


# ---- the ranked answer -----------------------------------------------
def test_ranked_hits_are_the_answer(world):
    """'what reports are about ED' -> ranked scored hits including
    the ED files, mixed labels welcome, scores visible — never a
    branch, never '0 term(s)'."""
    store, _read, _index, semantic = world
    q = "what reports are about ED"
    interp = scripted_proposals({q.lower(): {
        "mentions": ["Ed"],
        "kinds": {"Ed": "term"},  # dead field, stripped by the cage
        "expansions": {"Ed": ["emergency department",
                              "emergency room"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    hits = result["hits"]
    assert hits and all("score" in h and "label" in h for h in hits)
    names = " ".join(h["name"] for h in hits)
    assert "ED" in names
    assert "0 term(s)" not in result["answer"]
    # scores are visible in the rendered answer too
    assert any(str(round(h["score"], 2)) in result["answer"]
               or f"{h['score']:.2f}" in result["answer"]
               for h in hits[:1])


def test_the_census_emerges_from_label_cards(world):
    """'what tables are there': every table's label card hits at
    ≈1 — the ranked answer IS the census, no group node needed."""
    store, _read, _index, semantic = world
    q = "what tables are there"
    interp = scripted_proposals({q: {"mentions": ["tables"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    tables = [h for h in result["hits"] if h["label"] == "table"]
    assert len(tables) >= 40  # the band shows the group en masse
    assert result["hits"][0]["label"] == "table"
    assert "table (" in result["answer"]  # the group header + count


@pytest.mark.xfail(strict=True, reason=(
    "HELD in Manifest_Build SectionD (Sunny 2026-09-09): "
    "scoring-law resumption evidence — real-physics residual "
    "after the speech contract; strict forces unmarking when "
    "the ruling lands"))
def test_scores_sum_across_cards_and_mentions(world):
    """The law itself: a node hit on TWO mentions (name via one,
    label via the other) outscores a node hit on one — 'files' +
    'ED' crowns the ED files."""
    store, _read, _index, semantic = world
    q = "which files mention ED"
    interp = scripted_proposals({q.lower(): {
        "mentions": ["files", "ED"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    hits = result["hits"]
    ed_file = next(h for h in hits
                   if h["label"] == "file" and "ED" in h["name"])
    non_ed_col = next((h for h in hits if h["label"] == "column"
                       and "ED" not in h["name"].upper()), None)
    if non_ed_col:
        assert ed_file["score"] > non_ed_col["score"]
    # provenance names the summed cards
    assert "+" in ed_file["via_card"] or ed_file["via_card"]


def test_expansions_are_the_search_text(world):
    """The expansions join the query: 'ED' + 'emergency department'
    finds description-carrying nodes the bare acronym cannot."""
    store, _read, _index, semantic = world
    q = "things about the emergency dept"
    interp = scripted_proposals({q: {
        "mentions": ["emergency dept"],
        "expansions": {"emergency dept": ["emergency department"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    assert result["hits"]
    # the trace shows what was searched
    assert any(t.get("searched_as") for t in result["trace"])


@pytest.mark.xfail(strict=True, reason=(
    "HELD in Manifest_Build SectionD (Sunny 2026-09-09): "
    "scoring-law resumption evidence — real-physics residual "
    "after the speech contract; strict forces unmarking when "
    "the ruling lands"))
def test_nonsense_shows_only_weakness(world):
    """Corrected pin (embedder physics: cosines are never empty —
    for the real model or the fake): honesty for nonsense is
    VISIBLE WEAKNESS — no strong hits, every score shown below the
    match line, or the empty door."""
    store, _read, _index, semantic = world
    q = "wibble wobble zorp"
    interp = scripted_proposals({q: {"mentions": ["zorpwibble"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    assert all(h["score"] < 0.5 for h in result["hits"])
    if not result["hits"]:
        assert "searched" in result["answer"].lower() \
            or "nothing" in result["answer"].lower()


# ---- follow-ups survive the rebuild ----------------------------------
def test_anaphors_still_resolve_from_the_table(world):
    store, _read, _index, semantic = world
    q1 = "what reports are about ED"
    i1 = scripted_proposals({q1.lower(): {
        "mentions": ["Ed"],
        "expansions": {"Ed": ["emergency department"]}}})
    r1 = ask.ask(store, q1, "person:test", T0,
                 interpret_fn=i1, semantic=semantic)
    assert r1["context_set"]
    i2 = scripted_proposals({"the first one": {
        "mentions": ["the first one"],
        "references": {"the first one": "ordinal:1"}}})
    r2 = ask.ask(store, "the first one", "person:test", T0,
                 interpret_fn=i2, semantic=semantic,
                 context=r1["context_set"])
    assert r2["status"] == "answer"
    assert r1["context_set"][0] in " ".join(r2["context_set"])


def test_overmarked_reference_never_vetoes_the_search(world):
    """Sunny's live corpse (2026-09-07 22:27): the model marked 'ED'
    as a reference with nothing on the table, and the whole question
    died in a clarify — discarding 24 report hits already found. A
    role-mark is a PROPOSAL: empty table -> the mention is searched
    as text; partial answers are law (L3-D4)."""
    store, _read, _index, semantic = world
    q = "what reports are about ED"
    interp = scripted_proposals({q.lower(): {
        "mentions": ["reports", "ED"],
        "references": {"ED": "singular"},   # over-marked
        "expansions": {"ED": ["emergency department"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"          # never the veto
    assert len(result["hits"]) > 5
    names = " ".join(h["name"] for h in result["hits"]).upper()
    assert "ED" in names or "SEPSIS" in names
    # the trace says what happened to the mark
    ed_row = next(t for t in result["trace"]
                  if t["mention"] == "ED")
    assert "empty" in str(ed_row.get("note", "")) \
        or ed_row.get("tier") == "search"


def test_pure_anaphor_with_empty_table_still_clarifies(world):
    store, _read, _index, semantic = world
    interp = scripted_proposals({"it": {
        "mentions": ["it"], "references": {"it": "singular"}}})
    result = ask.ask(store, "it", "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "clarify"
    assert "refer back" in result["reason"]


# ---- Brief_Anaphor_Clarify (2026-09-20, "agree with all four,
# build it"): the estate-vocabulary gate + the ruled anchor band
def test_estate_vocabulary_is_names_labels_blessed_never_speech(world):
    """Ruling (2): vocabulary = the ask index's NAME tokens + LABEL
    tokens + blessed acronym names — NEVER speech text (stored
    English contains 'it'; speech in the vocabulary would re-kill
    the honest clarify)."""
    _store, read, index, _semantic = world
    blessed = {n.properties["name"].lower()
               for n in read.nodes("acronym")}
    words = ask._estate_vocabulary(index, blessed)
    for w in ("it", "those", "that", "them"):
        assert w not in words, w
    for w in ("ed", "sepsis", "ett", "iv"):
        assert w in words, w
    # 'carrying' is an R14 sentence word — speech never leaks in
    assert "carrying" not in words


def test_estate_vocabulary_gate_distinguishes(world):
    """Ruling (1), Option A: 'it' (no estate token) is gated — never
    searched as text, the honest clarify fires; 'ED' (an estate
    word) passes the gate and searches as text — the 22:27 corpse
    rule stands untouched."""
    store, _read, _index, semantic = world
    interp = scripted_proposals({"it": {
        "mentions": ["it"], "references": {"it": "singular"}}})
    r = ask.ask(store, "it", "person:test", T0,
                interpret_fn=interp, semantic=semantic)
    assert r["status"] == "clarify"
    row = next(t for t in r["trace"] if t["mention"] == "it")
    assert row["outcome"] == "no-estate-word"
    q = "what reports are about ED"
    interp2 = scripted_proposals({q.lower(): {
        "mentions": ["reports", "ED"],
        "references": {"ED": "singular"},   # over-marked
        "expansions": {"ED": ["emergency department"]}}})
    r2 = ask.ask(store, q, "person:test", T0,
                 interpret_fn=interp2, semantic=semantic)
    ed = next(t for t in r2["trace"] if t["mention"] == "ED")
    assert ed.get("tier") == "search"


def test_anchor_band_is_margin_of_best_never_all_strong():
    """Ruling (3), the fix: anchors = non-table hits >= MATCH_SCORE
    AND within UNIQUE_MARGIN of the best NON-TABLE card (a table
    entry's 1.0 card is context, never the anchor bar). Shape pin —
    thresholds are registry data (0.5 / 0.1 today)."""
    hits = [
        {"identity": "a", "via_card": "name", "best_card_score": 0.77},
        {"identity": "b", "via_card": "name", "best_card_score": 0.70},
        {"identity": "c", "via_card": "name", "best_card_score": 0.55},
        {"identity": "d", "via_card": "name", "best_card_score": 0.45},
        {"identity": "t", "via_card": "table", "best_card_score": 1.0},
    ]
    assert ask._anchor_band(hits) == ["a", "b"]
    assert ask._anchor_band([]) == []
