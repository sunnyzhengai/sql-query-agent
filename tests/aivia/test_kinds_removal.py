"""THE KINDS REMOVAL — Sunny's ruling (2026-09-07): remove the kind
nodes, the "kind is the answer shape" rule, all enumerated kinds,
and every kinds-related item from the ask path. The test suite,
shown before any implementation (step discipline).

What survives (physics, not enumeration): the store's node TYPES
(n.kind = the metamodel), per-type speech rules, and grouping by
type as PRESENTATION. What dies: kind:: nodes/entries, the kind
grounding outcome, kindset/display special-casing, VALID_KINDS,
the proposal's kinds field + prompt menu, the metric pseudo-kind.

SUPERSEDES (by this ruling, recorded): the GR-3 key ("kind words
ground to kind-sets"), the special-cased practiced/governed metric
answer (live-find #2's corpse — "metrics" becomes ordinary earned
vocabulary), and the kinds-mark machinery.

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
    store, _ = build_store("sepsis")  # NO seeded vocabulary: cold
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, fake_embed,
                                       "fake-64", cache_path=None)
    return store, read, index, semantic


# ---- the enumerations are gone ---------------------------------------
def test_no_kind_machinery_remains(world):
    _store, _read, index, _semantic = world
    assert not hasattr(ask, "VALID_KINDS")
    # no kind:: nodes in the searchable surface
    assert not [e for e in index
                if e["identity"].startswith("kind::")]
    # the cage strips/ignores a kinds field — the model cannot
    # propose type targets at all
    out = ask.validate_interpretation(
        {"mentions": ["Ed"], "kinds": {"Ed": "term"}})
    assert out is not None and "kinds" not in out


def test_grounding_has_no_kind_outcome(world):
    _store, _read, index, semantic = world
    g = grounding.ground("reports", index, {}, semantic)
    assert g["outcome"] != "kind"


# ---- the original disease, cured end to end --------------------------
def test_the_ed_proposal_now_finds_the_ed_files(world):
    """The four-disease cached proposal (mentions ['Ed'], kinds
    {'Ed': 'term'}, good expansions): with no kind target to obey,
    'Ed' grounds by its own evidence and the answer is the ED
    files — never '0 term(s)'."""
    store, _read, _index, semantic = world
    q = "what reports are about ED"
    interp = fake_interpreter({q: {
        "mentions": ["Ed"],
        "kinds": {"Ed": "term"},  # dead field, ignored by the cage
        "expansions": {"Ed": ["emergency department",
                              "emergency room"]}}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    text = result.get("answer", "")
    if result["status"] == "clarify":
        names = [c["name"] for c in result["candidates"]]
        assert any("ED" in n for n in names)
        assert "0 term(s)" not in text
    else:
        assert "USP_ED_SEPSIS" in text or "USP_RPTS_ED_Sepsis" in text
        assert "0 term(s)" not in text


# ---- cold start: the absence door offers the estate's groups ---------
def test_cold_type_word_opens_the_door_with_groups(world):
    """'what tables are there', nothing earned: an honest door —
    the estate's TYPE GROUPS (presentation over n.kind, physics)
    offered for the pick; never a fabricated kind answer."""
    store, _read, _index, semantic = world
    q = "what tables are there"
    interp = fake_interpreter({q: {"mentions": ["tables"]}})
    result = ask.ask(store, q, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    text = result.get("answer", "") or " ".join(
        str(result.get(k, "")) for k in ("mention", "reason"))
    assert "90" in text and "table" in text.lower()  # the group line


# ---- earned vocabulary yields type-sets ------------------------------
def test_confirmed_type_word_yields_the_set(world):
    """Confirm once that 'reports' means the file type (target =
    the metamodel type, physics — not a node): thereafter the word
    yields the 28 files as a plain set."""
    store, _read, _index, semantic = world
    from aivia.graph import kg3_artifacts
    kg3_artifacts.append_usage(store, "confirmed", "person:sunny",
                               T0, payload="vocab act")
    act = store.current_nodes("usage")[-1]
    kg3_artifacts.append_term(
        store, "term::vocab/REPORTS", "reports",
        "a word for the file type", "person:sunny", T0,
        parent="type:file", derived_from=[act.identity])
    q2 = "what reports are there"
    interp = fake_interpreter({q2: {"mentions": ["reports"]}})
    result = ask.ask(store, q2, "person:test", T0,
                     interpret_fn=interp, semantic=semantic)
    assert result["status"] == "answer"
    assert "28" in result["answer"]
    assert "USP_ED_SEPSIS" in result["answer"]
