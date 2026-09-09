"""E2 — THE VERBATIM CENSUS (integrity battery #8, ratified in
Design_Graph_Engine.md; code first exists 2026-09-09 — the audit
found the equation had NO implementation anywhere).

The equation: index words == recomputed speech, entry by entry —
matched ⊎ counted-mismatch == total. A stale or hand-mutated index
is COUNTED, never silent.

Proves: contract:aivia-design-to-code
"""
import pytest

from aivia.flows import ask, censuses
from aivia.graph.read_api import ReadApi


@pytest.fixture(scope="module")
def world():
    from aivia.console import build_store
    store, _ = build_store("sepsis")
    read = ReadApi(store)
    return read, ask.build_index(read)


def test_the_equation_holds_on_a_fresh_index(world):
    read, index = world
    c = censuses.verbatim_census(read, index)
    assert c["matched"] + c["mismatched"] == c["total"] == len(index)
    assert c["mismatched"] == 0
    assert c["mismatches"] == []


def test_a_drifted_entry_is_counted_and_named(world):
    read, index = world
    tampered = [dict(e) for e in index]
    victim = next(e for e in tampered if e["words"])
    victim["words"] = victim["words"] + " smuggled words"
    c = censuses.verbatim_census(read, tampered)
    assert c["mismatched"] == 1
    assert victim["identity"] in c["mismatches"]


def test_the_report_carries_the_verbatim_line(world):
    read, index = world
    text = censuses.report(read, index)
    assert "verbatim" in text.lower()
