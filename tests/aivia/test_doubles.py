"""THE SCRIPTED-PROPOSALS CONTRACT (Sunny's ruling, 2026-09-09:
"'fake interpreter' for this part is misleading"). The double is
AUTHORED TEST INPUT — a proposal the test declares as its given,
the same species as authored SQL fixtures — never a model stand-in.
Two laws land here:

1. LOUD MISS — an unscripted question raises ScriptGap naming the
   question and every scripted key; the silent default
   {"mentions": [question]} died (it made three tests vacuous
   before anyone noticed).
2. THE GENERATOR FIX — keys fold at CONSTRUCTION (whitespace +
   case), so the lowercase-lookup trap CLASS cannot occur (Echo
   Law: a third occurrence demands the mechanism one level up).

Proves: contract:aivia-design-to-code
"""
import pytest

from .doubles import ScriptGap, scripted_proposals


def test_a_scripted_question_returns_its_authored_proposal():
    interp = scripted_proposals(
        {"what reports are about ed": {"mentions": ["reports", "ED"]}})
    assert interp("what reports are about ed") == {
        "mentions": ["reports", "ED"]}


def test_an_unscripted_question_raises_loudly():
    interp = scripted_proposals({"a": {"mentions": ["a"]}})
    with pytest.raises(ScriptGap) as err:
        interp("something never scripted")
    assert "something never scripted" in str(err.value)
    assert "a" in str(err.value)  # the script's keys are named


def test_keys_fold_at_construction_killing_the_case_trap():
    # the author wrote the key with capitals and doubled spaces —
    # the trap that bit three times; folding at construction makes
    # the mismatch impossible instead of merely loud
    interp = scripted_proposals(
        {"What Reports  are about ED": {"mentions": ["reports", "ED"]}})
    assert interp("what reports are about ed") == {
        "mentions": ["reports", "ED"]}
    assert interp("  What reports are ABOUT ed ") == {
        "mentions": ["reports", "ED"]}
