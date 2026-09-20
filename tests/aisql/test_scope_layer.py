"""M2 (bottom-up re-ruling, 2026-09-10) — THE SCOPE LAYER.

Scopes tie straight DOWN into the verified technical layer:
scope—reads→table at true grain. And the shape contract lands on
them: the description is STORED on the node at build (the lead
render, composed bottom-up from KG1 words — Sunny's summing law),
with the verbatim law enforced mechanically: stored == recomputed.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql.flows import produce, speech
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
    """R14 (v2.14.0, Brief_Pilot_Build_3): the stored text is the
    Business Term sentence — stored == recomputed, byte-exact."""
    _store, read = world
    trees = read.trees()
    by_id = {n.identity: n for n in read.nodes("scope")}
    checked = 0
    for key, tree in sorted(trees.items()):
        for scope in decisions.named_scopes(tree):
            node = by_id.get(scope["name_key"])
            if node is None:
                continue
            sentence = produce.scope_sentence(read, tree, scope)
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
