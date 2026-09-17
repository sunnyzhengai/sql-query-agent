"""THE SPEECH PARITY GATE (Sunny's ruling 2026-09-16, from the
AGE_IN_DAYS find + THE PLACEHOLDER LAW): every Speech_Sources row
gets a MECHANICAL verifier — the ask surface must actually speak
what the sheet declares. A declaration with no check is a hope
(the RG-B1 principle applied to speech).

The deciding case this gate exists for: the index's
derived_column entries spoke a placeholder ("a computed output of
the … selection") written before computed columns had stored
descriptions; when M4 landed the real descriptions the
placeholder kept speaking, and no test could see it. This file is
the tripwire: the moment a label's declared source exists on the
store node, the index MUST speak it.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.console import build_store
from aivia.flows import ask, speech
from aivia.graph.read_api import ReadApi


@pytest.fixture(scope="module")
def world():
    store, _ = build_store("ed_sepsis_dev")
    read = ReadApi(store)
    return read, ask.build_index(read)


# The verifier per Speech_Sources row — the closed assignment.
# "stored": every index entry's words == its store node's
#   description, lowercased (the speak() contract for stored
#   speech). "render": non-empty recomputed phrase. "aboutness":
#   empty allowed (a counted gap until the Scribe writes).
# "absent": the label is ruled OUT of the ask index.
# literal: schema-mirror lenses.Speech_Sources
VERIFIERS = {
    "table": "stored", "column": "stored",
    "scope (selection)": "stored",
    "derived_column": "stored",
    "condition (predicate)": "render", "parameter": "render",
    "file": "aboutness", "pbi_report": "render",
    "drift name": "render", "term (KG3)": "render",
    "kind (node type)": "self-rows",
    "join (ON predicate container)": "absent",
    "operational statement": "absent",
    "statement": "absent",
}


def test_every_speech_row_has_a_verifier():
    declared = set(speech.sources())
    rows = {r for r in declared
            if not r.startswith(("_self", "_edge"))}
    unverified = rows - set(VERIFIERS)
    assert not unverified, (
        f"Speech_Sources rows with NO mechanical verifier "
        f"{sorted(unverified)} — a declaration with no check is a "
        f"hope; add the row to VERIFIERS with its check")


def test_every_index_label_is_declared(world):
    _, index = world
    labels = {e["label"] for e in index}
    missing = {lb for lb in labels
               if lb not in speech.SHEET_KINDS}
    assert not missing, (
        f"index labels with no Speech_Sources assignment: "
        f"{sorted(missing)}")


def test_stored_speech_is_the_node_description(world):
    """The center law, mechanically: for every label declaring
    'stored' speech, each index entry's words == its store node's
    description (lowercased — the speak() contract). This is the
    test that would have caught the derived_column placeholder the
    day M4 landed."""
    read, index = world
    stored_labels = [k for k, sheet in speech.SHEET_KINDS.items()
                     if VERIFIERS.get(sheet) == "stored"]
    assert "derived_column" in stored_labels
    nodes = {}
    for label in stored_labels:
        for n in read.nodes(label):
            nodes[n.identity] = n
    checked = {label: 0 for label in stored_labels}
    for e in index:
        if e["label"] not in stored_labels:
            continue
        node = nodes.get(e["identity"])
        assert node is not None, (
            f"index entry {e['identity']} ({e['label']}) has no "
            f"store node — the entry grain must BE the node grain")
        want = (node.properties.get("description") or "").lower()
        assert e.get("words", "") == want, (
            f"{e['label']} {e['name']}: the index speaks "
            f"{e.get('words', '')!r} but the store node's "
            f"description is {want!r}")
        checked[e["label"]] += 1
    for label, n in checked.items():
        assert n > 0, (f"no {label} entries were checked — the "
                       f"gate went vacuous")


def test_absent_labels_stay_out_of_the_index(world):
    _, index = world
    labels = {e["label"] for e in index}
    assert "join" not in labels
    assert "statement" not in labels


def test_render_speech_is_never_empty(world):
    """Render-declared labels: every entry speaks SOMETHING (file
    is aboutness — empty is a counted gap, exempt)."""
    _, index = world
    render_labels = {k for k, sheet in speech.SHEET_KINDS.items()
                     if VERIFIERS.get(sheet) == "render"}
    for e in index:
        if e["label"] in render_labels:
            assert (e.get("words") or "").strip(), (
                f"{e['label']} {e['name']} speaks nothing under a "
                f"render obligation")
