"""THE MEANING-SMELL CENSUS + THE PHRASE-CORPUS SWEEP (Sunny's go,
2026-09-14 "go on both"; direction ruled in the 09-12 GENERATOR NOTE —
generator-level moves instead of per-round phrasing fixes).

Detectors are mechanical and closed — no model, no threshold. A smell
is a flag for Sunny's sweep, never a verdict: lawful renders can smell
(the 2.8.0 name-words join render "The ed disposition code is the ed
disposition." is ruled AND echo-smelled — the census surfaces it, the
sweep rules on it). The census is a conservation equation in the
ADR 0080 family: clean ⊎ smelled == total voicings. The corpus
artifact renders every class — no silent caps.

The founding corpses are the acceptance tests: the join tautology
("The encounter is the encounter."), the sentinel placeholder
(38 rows, killed 2026-09-14), the source-phrase stutter ("med admin
records records"), raw fragments in prose.

Proves: contract:aivia-design-to-code
"""
from dataclasses import dataclass, field
from typing import Dict, List

import pytest

from aivia.flows import smells
from aivia.graph.read_api import ReadApi

# ---- the detectors (closed, mechanical) ------------------------------

def test_tautology_names_the_join_corpse():
    assert "tautology" in smells.detect("The encounter is the encounter.")


def test_tautology_survives_a_noted_annotation():
    assert "tautology" in smells.detect(
        "The encounter is the encounter (noted 'same visit').")


def test_echo_catches_the_near_tautology():
    # lawful under Grammar 2.8.0 AND smelled — the census flags,
    # the sweep rules
    found = smells.detect("The ed disposition code is the ed disposition.")
    assert "echo" in found
    assert "tautology" not in found


def test_tautology_is_not_double_counted_as_echo():
    found = smells.detect("The encounter is the encounter.")
    assert "tautology" in found and "echo" not in found


def test_stutter_catches_the_repeated_word():
    assert "stutter" in smells.detect(
        "Drawn from the med admin records records.")


def test_placeholder_catches_the_sentinel_class():
    assert "placeholder" in smells.detect("No value is present.")
    assert "placeholder" in smells.detect("NULL")
    assert "placeholder" in smells.detect(
        "(description pending re-anonymization)")


def test_empty_is_a_counted_smell():
    assert smells.detect("") == ["empty"]
    assert smells.detect("   ") == ["empty"]


def test_identifier_leak_catches_raw_fragments():
    assert "identifier" in smells.detect(
        "The EEF.ENCOUNTER_ID is recorded.")
    assert "identifier" in smells.detect(
        "Filtered where ed_disposition_code is 7.")


def test_clean_sentences_pass():
    for text in (
        "The taken time is before the ed departure time "
        "(noted 'while in ED').",
        "The route of administration for a medication is 11 "
        "(noted 'intravenous').",
        "The taken time is recorded.",
        "The category value that identifies the patient's race.",
    ):
        assert smells.detect(text) == [], text


# ---- the shape template (dedup-by-class) -----------------------------

def test_template_groups_same_shape():
    a = smells.template("The encounter is the encounter.")
    b = smells.template("The event record unique is the event record unique.")
    assert a == b


def test_template_separates_different_structure():
    a = smells.template("The taken time is recorded.")
    b = smells.template(
        "The taken time is before the ed departure time.")
    assert a != b


def test_template_masks_values_and_quotes():
    a = smells.template("The route for a medication is 11 (noted 'x').")
    b = smells.template("The route for a medication is 42 (noted 'y').")
    assert a == b


# ---- the census: clean ⊎ smelled == total ----------------------------

@dataclass
class _Node:
    label: str
    identity: str
    properties: Dict = field(default_factory=dict)


class _FakeRead:
    def __init__(self, nodes: List[_Node]):
        self._n = nodes

    def nodes(self, label):
        return [n for n in self._n
                if label is None or n.label == label]


def test_vacuity_a_synthetic_smell_is_seen():
    # a census that cannot fail is decoration (ADR 0080's own law)
    read = _FakeRead([
        _Node("condition", "c1",
              {"kind": "COMPARE_EQ",
               "description": "No value is present."}),
        _Node("condition", "c2",
              {"kind": "COMPARE_EQ",
               "description": "The taken time is recorded."}),
        _Node("scope", "s1", {"description": ""}),
    ])
    c = smells.smell_census(read)
    assert c["total"] == 3
    assert c["clean"] + c["smelled"] == c["total"]
    assert c["smelled"] == 2
    assert c["by_smell"]["placeholder"] == 1
    assert c["by_smell"]["empty"] == 1


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _base = build_store("sepsis")
    return ReadApi(store)


def test_census_conservation_on_the_estate(world):
    c = smells.smell_census(world)
    assert c["total"] == (len(world.nodes("condition"))
                          + len(world.nodes("scope")))
    assert c["clean"] + c["smelled"] == c["total"]
    assert c["total"] > 0


def test_corpus_classes_partition_the_estate(world):
    rows = smells.phrase_corpus(world)
    classes = smells.corpus_classes(rows)
    assert sum(k["count"] for k in classes) == len(rows)
    by_class = {k["class"]: k for k in classes}
    for row in rows:
        assert row["identity"] in by_class[row["class"]]["members"]


def test_smelled_class_shows_a_smelled_exemplar():
    # the sweep must see the evidence: a class whose smells came
    # from a non-first member still exemplifies with a smelled one
    read = _FakeRead([
        _Node("condition", "c1",
              {"kind": "COMPARE_EQ",
               "description": "The line number is 1."}),
        _Node("condition", "c2",
              {"kind": "COMPARE_EQ",
               "description": "The encounter is encounter."}),
    ])
    classes = smells.corpus_classes(smells.phrase_corpus(read))
    smelled = [k for k in classes if k["smells"]]
    assert smelled and smelled[0]["exemplar"] == "The encounter is encounter."


def test_corpus_render_covers_every_class(world):
    # no silent caps: every class line reaches the sweep artifact
    rows = smells.phrase_corpus(world)
    classes = smells.corpus_classes(rows)
    doc = smells.render_corpus(rows)
    for k in classes:
        assert k["exemplar"] in doc, k["class"]
    census = smells.smell_census(world)
    assert f"{census['total']} voicings" in doc


def test_report_carries_the_smell_census(world):
    # the gap-check report bucket speaks the fourth equation
    from aivia.flows import ask, censuses
    index = ask.build_index(world)
    text = censuses.report(world, index)
    assert "meaning-smell" in text
