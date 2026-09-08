"""STEP B — THE SEARCH IS THE ANSWER (Sunny's pipeline, ruled
2026-09-07). Supersedes the kinds-removal suite (its pins are
absorbed) and, by the ruling, the tier-ladder pins (GR-1 exact
tiers, GR-3 kind words, the CN-2 provenance buckets, the MT
special-cased metric answer).

The pipeline: LLM (intention, mentions, expansions) -> vector
search against EVERYTHING (labels as entries, names, descriptions)
-> RANKED SCORED HITS returned -> clicks are steer. No string tier
anywhere in the search path; exact matching is the cosine≈1 case.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import ask, grounding
from aivia.graph.read_api import ReadApi

from .test_ask_console import fake_embed, fake_interpreter

T0 = "2026-09-07T12:00:00Z"


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")  # cold: nothing earned
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, fake_embed,
                                       "fake-2k", cache_path=None)
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


def test_labels_are_searchable_entries(world):
    _store, _read, index, _semantic = world
    labels = [e for e in index
              if e["identity"].startswith("label::")]
    names = {e["name"] for e in labels}
    assert {"table", "column", "file"} <= names


# ---- the ranked answer -----------------------------------------------
def test_ranked_hits_are_the_answer(world):
    """'what reports are about ED' -> ranked scored hits including
    the ED files, mixed labels welcome, scores visible — never a
    branch, never '0 term(s)'."""
    store, _read, _index, semantic = world
    q = "what reports are about ED"
    interp = fake_interpreter({q.lower(): {
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


def test_type_words_hit_the_label_group(world):
    """'what tables are there' cold: the label entry 'table' ranks
    at the top (near-identical vectors) — the group hit, clickable,
    carrying its member count."""
    store, _read, _index, semantic = world
    q = "what tables are there"
    interp = fake_interpreter({q: {"mentions": ["tables"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    top = result["hits"][0]
    assert top["identity"] == "label::table"
    assert "90" in result["answer"]


def test_expansions_are_the_search_text(world):
    """The expansions join the query: 'ED' + 'emergency department'
    finds description-carrying nodes the bare acronym cannot."""
    store, _read, _index, semantic = world
    q = "things about the emergency dept"
    interp = fake_interpreter({q: {
        "mentions": ["emergency dept"],
        "expansions": {"emergency dept": ["emergency department"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    assert result["hits"]
    # the trace shows what was searched
    assert any(t.get("searched_as") for t in result["trace"])


def test_nonsense_shows_only_weakness(world):
    """Corrected pin (embedder physics: cosines are never empty —
    for the real model or the fake): honesty for nonsense is
    VISIBLE WEAKNESS — no strong hits, every score shown below the
    match line, or the empty door."""
    store, _read, _index, semantic = world
    q = "wibble wobble zorp"
    interp = fake_interpreter({q: {"mentions": ["zorpwibble"]}})
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
    i1 = fake_interpreter({q1.lower(): {
        "mentions": ["Ed"],
        "expansions": {"Ed": ["emergency department"]}}})
    r1 = ask.ask(store, q1, "person:test", T0,
                 interpret_fn=i1, semantic=semantic)
    assert r1["context_set"]
    i2 = fake_interpreter({"the first one": {
        "mentions": ["the first one"],
        "references": {"the first one": "ordinal:1"}}})
    r2 = ask.ask(store, "the first one", "person:test", T0,
                 interpret_fn=i2, semantic=semantic,
                 context=r1["context_set"])
    assert r2["status"] == "answer"
    assert r1["context_set"][0] in " ".join(r2["context_set"])
