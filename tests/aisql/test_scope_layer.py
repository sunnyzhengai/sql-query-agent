"""M2 (bottom-up re-ruling, 2026-09-10) — THE SCOPE LAYER.

Scopes tie straight DOWN into the verified technical layer:
scope—reads→table at true grain. And the shape contract lands on
them: the description is STORED on the node at build (the lead
render, composed bottom-up from KG1 words — Sunny's summing law),
with the verbatim law enforced mechanically: stored == recomputed.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql.flows import speech
from aisql.graph.read_api import ReadApi
from aisql.lenses import decisions

ED_SCOPE = "reporting/USP_ED_SEPSIS.sql::#Base_Pop"


@pytest.fixture(scope="module")
def world():
    from aisql.console import build_store
    store, _ = build_store("sepsis")
    return store, ReadApi(store)


def test_every_scope_stores_a_description(world):
    _store, read = world
    scopes = read.nodes("scope")
    assert scopes
    empty = [n.identity for n in scopes
             if not (n.properties.get("description") or "").strip()]
    assert not empty, f"{len(empty)} scopes without stored "\
                      f"descriptions, first: {empty[:3]}"


def test_stored_equals_recomputed_the_verbatim_law(world):
    """R16 (v2.16.0, Brief_Business_Voice): the stored text is the
    tier's answer — blessed > gate-passed proposed > the mechanical
    R14 floor — recomputed through THE ONE DOOR
    (business_voice.effective_sentence, the registry read as input
    data exactly like KG1 descriptions). stored == recomputed,
    byte-exact."""
    import pathlib

    from aisql.flows import business_voice
    _store, read = world
    glossary = (pathlib.Path(__file__).resolve().parents[2]
                / "AIVIA_Product" / "estates" / "sepsis" / "glossary")
    rows = business_voice.load_rows(glossary)
    synonyms = business_voice.load_synonyms(glossary)
    acronyms = business_voice.load_acronym_expansions(glossary)
    trees = read.trees()
    by_id = {n.identity: n for n in read.nodes("scope")}
    checked = 0
    for key, tree in sorted(trees.items()):
        for scope in decisions.named_scopes(tree):
            node = by_id.get(scope["name_key"])
            if node is None:
                continue
            sentence, _tier = business_voice.effective_sentence(
                read, tree, scope, rows, synonyms=synonyms,
                acronyms=acronyms)
            assert node.properties["description"] == sentence, \
                scope["name_key"]
            checked += 1
    assert checked == len(by_id)


def test_speech_reads_the_stored_property(world):
    _store, read = world
    entry = {"label": "scope", "identity": ED_SCOPE,
             "name": "#Base_Pop"}
    text = speech.speak(read, entry)
    node = next(n for n in read.nodes("scope")
                if n.identity == ED_SCOPE)
    assert text == node.properties["description"].lower()
    # grammar 2.14.0 (R14): the Business Term sentence leads —
    # #Base_Pop's grain source is its DISTINCT (slice E capture)
    assert text.startswith("one record per distinct")
