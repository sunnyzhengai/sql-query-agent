"""The corpus answer key — right answers authored as DATA, asserted
without an LLM (Sunny's retro test-first order, 2026-09-03).

Every corpus case in devtools/desc_corpus.py carries its authored
right answer: `expect` (substrings the DETERMINISTIC skeleton must
contain), optional `forbid`, and `outcome` — the production
acceptance's verdict on the un-smoothed skeleton, including the one
case whose right answer IS a counted empty. The live corpus leg
smooths on top of this; the answers themselves never depend on a
model.

This closes the instrument-staleness finding (the 09-03 report
review): the 11-case corpus scored 11/11 both before and after the
compositional rebuild — green that proved too little. The corpus now
encodes the week's gate food (expression depth, arithmetic, NOT_IN,
NOT_BETWEEN, tautology scaffolding, parameter defaults, elision
counts, sentence-shaped meanings, the 'value set' placeholder FP,
CASE-in-predicate) with answers written before this test first ran.
Pattern ancestors (spec:G4): the 0044 red-first law; spec:F/T1 (the
instrument); the single-source rule — the corpus file IS the case
data, this test only reads it.

Proves: spec:G5
"""

from __future__ import annotations

import pytest

from devtools.desc_corpus import CASES, case_dict_lines
from src.descriptions import (
    compose_skeleton,
    describe_step,
    grounding_violations,
    line_level_kill,
)


def _ids():
    return [f"{c['cls']}:{c['name']}" for c in CASES]


def test_every_case_carries_its_answer():
    """Deny-by-default: a case without an authored answer is not a
    test case, it is a hope."""
    missing = [c["name"] for c in CASES
               if "expect" not in c or "outcome" not in c]
    assert not missing, f"case(s) without authored answers: {missing}"
    bad = [c["name"] for c in CASES
           if c["outcome"] not in ("ships", "emptied")]
    assert not bad, f"outcome outside the closed vocabulary: {bad}"


@pytest.mark.parametrize("case", CASES, ids=_ids())
def test_skeleton_matches_the_authored_answer(case):
    sk = compose_skeleton(case["sql"], case.get("meanings"))
    for want in case["expect"]:
        assert want in sk, (
            f"{case['name']}: expected {want!r} in skeleton:\n{sk}")
    for bad in case.get("forbid", []):
        assert bad not in sk, (
            f"{case['name']}: forbidden {bad!r} present in:\n{sk}")


@pytest.mark.parametrize("case", CASES, ids=_ids())
def test_acceptance_verdict_matches_the_authored_outcome(case):
    """The production acceptance on the un-smoothed skeleton
    (describe_step with no model + the §5.3a-1 SENTENCE-grain voice
    kill) must reach the authored verdict — including 'emptied'
    where absence IS the right answer."""
    sd = describe_step(case["sql"], case.get("meanings"), smooth=None)
    shipped, killed, kill = line_level_kill(
        sd.text, case["sql"], case_dict_lines(case))
    got = "ships" if shipped else "emptied"
    assert got == case["outcome"], (
        f"{case['name']}: expected {case['outcome']}, got {got}"
        + (f" — kill: {kill[:2]}" if kill else f"\n{sd.text}"))


@pytest.mark.parametrize(
    "case", [c for c in CASES if "expect_shipped" in c],
    ids=lambda c: f"{c['cls']}:{c['name']}")
def test_shipped_text_matches_the_authored_answer(case):
    """0074 §5.3a-1 (kill unit = the SENTENCE, ruled 09-04): on a
    MIXED step the violating line dies, the true lines ship, and
    every dropped line is counted. Nothing formerly-killed may leak
    into shipped prose."""
    sd = describe_step(case["sql"], case.get("meanings"), smooth=None)
    shipped, killed, _kill = line_level_kill(
        sd.text, case["sql"], case_dict_lines(case))
    for want in case["expect_shipped"]:
        assert want in shipped, (
            f"{case['name']}: expected {want!r} in shipped:\n{shipped}")
    for bad in case.get("forbid_shipped", []):
        assert bad not in shipped, (
            f"{case['name']}: formerly-killed content leaked "
            f"({bad!r}) into:\n{shipped}")
    assert len(killed) == case["killed"], (
        f"{case['name']}: expected {case['killed']} killed line(s), "
        f"got {len(killed)}: {killed}")
    # and the surviving text is clean by the SAME gate — a partial
    # ship is never a loosened ship
    assert grounding_violations(shipped, case["sql"],
                                case_dict_lines(case)) == []
