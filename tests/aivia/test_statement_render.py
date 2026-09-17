"""§R11 THE STATEMENT STEP — byte-exact render pins (authored
FAILING before the renderer; suite-first per Sunny's 2026-09-10
ruling; Brief_M5_Statement_Layer approved 2026-09-17).

The estate's two IF phrases join this file at the checkpoint,
pinned from the presented 36 after Sunny's gap-check (the
answer-key precedent: authored from measurement, his eye the
authority). The estate-grain verbatim law lives in
AIVIA_Test/test_ed_sepsis_dev_estate.py.

Proves: contract:aivia-design-to-code
"""

from aivia.flows import produce


def _stmt(kind, scope=None, ctes=(), emits=False):
    # literal: shape — the tree statement dict the mapper writes
    s = {"statement_kind": kind}
    if scope is not None:
        s["scope"] = {"name": scope, "name_key": f"f.sql::{scope}"}
    if ctes:
        s["ctes"] = [{"name": c, "name_key": f"f.sql::{c}"}
                     for c in ctes]
    if emits:
        s["emits"] = True
    return s


def test_select_into_plain():
    assert produce.statement_phrase(
        _stmt("SELECT INTO", scope="#Base_Pop")) \
        == "Builds the base pop selection."


def test_select_into_folds_the_authors_name():
    assert produce.statement_phrase(
        _stmt("SELECT INTO", scope="#FirstABXAdminTimeDetails")) \
        == "Builds the firstabxadmintimedetails selection."


def test_select_into_one_helper():
    assert produce.statement_phrase(
        _stmt("SELECT INTO", scope="#BasePopABX", ctes=("ABX",))) \
        == ("Builds the basepopabx selection, preparing the abx "
            "selection first.")


def test_select_into_two_helpers_join_with_and():
    assert produce.statement_phrase(
        _stmt("SELECT INTO", scope="#LDA",
              ctes=("All_LDAs", "TimeOrdered_LDAs"))) \
        == ("Builds the lda selection, preparing the all ldas "
            "selection and the timeordered ldas selection first.")


def test_select_into_three_helpers_comma_then_and():
    assert produce.statement_phrase(
        _stmt("SELECT INTO", scope="#Cultures",
              ctes=("AllCultures", "PositiveCultures",
                    "NegativeCultures"))) \
        == ("Builds the cultures selection, preparing the "
            "allcultures selection, the positivecultures "
            "selection and the negativecultures selection first.")


def test_if_embeds_the_predicate_phrase_lowered():
    got = produce.statement_phrase(
        {"statement_kind": "IF", "predicate": {"kind": "NULL_CHECK"}},
        predicate_phrase="The start date parameter is missing.")
    assert got == ("A decision step, taken when the start date "
                   "parameter is missing.")


def test_emitting_select_is_the_delivery_step():
    assert produce.statement_phrase(
        _stmt("SELECT", scope="delivery", emits=True)) \
        == "Delivers the procedure's result set."


def test_the_estate_if_sentences_byte_exact():
    """The two real IF phrases, pinned at the checkpoint from the
    presented 36 (Sunny 'ratified', 2026-09-17) — the answer-key
    precedent: authored from measurement, his eye the authority."""
    from aivia.console import build_store
    store, _ = build_store("ed_sepsis_dev")
    got = {n.identity.rsplit("::", 1)[-1]:
           n.properties.get("description")
           for n in store.current_nodes("statement")
           if n.properties.get("does") == "IF"}
    assert got == {
        "stmt/5": ("A decision step, taken when the start date "
                   "parameter is not recorded or the start date "
                   "parameter is ''."),
        "stmt/6": ("A decision step, taken when the end date "
                   "parameter is not recorded or the end date "
                   "parameter is ''."),
    }


def test_operational_kinds_speak_nothing():
    """The (b) ruling: no fixed phrase restating the kind field."""
    for kind in ("DropTableStatement", "CreateIndexStatement",
                 "DeclareVariableStatement",
                 "SetTransactionIsolationLevelStatement",
                 "PredicateSetStatement"):
        assert produce.statement_phrase(_stmt(kind)) is None


def test_unlisted_data_producing_kind_is_none_never_invented():
    """An unlisted kind stores NOTHING — the builder counts it in
    statement_remainders; the renderer never invents a phrase."""
    assert produce.statement_phrase(
        _stmt("MERGE", scope="#X")) is None
