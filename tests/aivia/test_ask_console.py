"""ADR 0078 exit: the F9 ask-console answer keys go RUNNABLE.

Index totality + drift-by-name (the search law) · the three honest
outcomes with H5 usage events · every closed op over the sepsis
corpus · replay determinism (Group E) · the no-shapes claim: a scope
answers with its own FLOOR. Requires ScriptDom (ADR 0001).

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import ask
from aivia.graph.read_api import ReadApi
from aivia.lenses import ask_index

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
CASES = json.loads((FIX / "F9_ask" / "cases.json").read_text())
T0 = "2026-09-06T12:00:00Z"


@pytest.fixture(scope="module")
def store():
    from aivia.console import build_store
    return build_store("sepsis")


def _ask(store, q):
    return ask.ask(store, q, author="person:test", occurred_at=T0)


def test_ix1_every_kg1_column_findable(store):
    read = ReadApi(store)
    index = ask_index.lens_ask_index(read, None)["yield"]
    have = {e["identity"] for e in index if e["kind"] == "column"}
    for n in read.nodes("column"):
        assert n.identity in have


def test_ix2_drift_findable_by_name(store):
    # DATE_STAMP is BOTH computed (a derived member in some scopes)
    # AND drift (read where nothing declares it) — the ambiguous
    # listing shows the whole story; picking the drift identity
    # yields the finding (key corrected at build: richer than the
    # single-outcome premise)
    result = _ask(store, "what is DATE_STAMP")
    assert result["outcome"] == "ambiguous"
    kinds = {c["kind"] for c in result["resolution"]["candidates"]}
    assert "drift" in kinds and "derived column" in kinds
    drift_id = next(c["identity"] for c in
                    result["resolution"]["candidates"]
                    if c["kind"] == "drift")
    picked = _ask(store, f"what is {drift_id}")
    assert picked["outcome"] == "matched"
    assert "READER/WRITER DRIFT" in picked["answer"]
    assert "silently-failing" in picked["answer"]


def test_ix3_scopes_findable_cross_file_ambiguity_honest(store):
    # the readmit scope lives in TWO files — ambiguity is the truthful
    # outcome; the full identity resolves it (key corrected at build)
    r = _ask(store, "what is #Base_Pop_ED_Readmit")
    assert r["outcome"] == "ambiguous"
    assert len({c["identity"] for c in
                r["resolution"]["candidates"]}) >= 2
    full = _ask(store, "what is "
                "reporting/USP_ED_SEPSIS.sql::#Base_Pop_ED_Readmit")
    assert full["outcome"] == "matched"
    assert _ask(store, "what is USP_ED_SEPSIS")["outcome"] == "matched"


def test_oc1_matched_answer_and_usage_about(store):
    result = _ask(store, "what is THERA_CLASS_CODE")
    assert result["outcome"] == "matched"
    events = [u for u in store.current_nodes("usage")
              if u.properties.get("payload", "").endswith(
                  "THERA_CLASS_CODE")]
    assert events and events[-1].properties["outcome"] == "matched"
    assert events[-1].properties.get("about")


def test_oc2_ambiguous_candidates_no_about(store):
    result = _ask(store, "what is TIME_LINE")
    assert result["outcome"] == "ambiguous"
    assert "pick one" in result["answer"]
    events = [u for u in store.current_nodes("usage")
              if u.properties.get("payload", "").endswith("TIME_LINE")]
    assert events[-1].properties["outcome"] == "ambiguous"
    assert events[-1].properties.get("about") is None


def test_oc3_no_match_honest_counted(store):
    result = _ask(store, "what is FLUX_CAPACITOR_ID")
    assert result["outcome"] == "no-match"
    assert "NO MATCH" in result["answer"]
    events = [u for u in store.current_nodes("usage")
              if "FLUX_CAPACITOR_ID" in u.properties.get("payload", "")]
    assert events[-1].properties["outcome"] == "no-match"
    assert events[-1].properties.get("about") is None


def test_oc4_replay_determinism(store):
    a = _ask(store, "lineage of ED_ENCOUNTERS_DM")["answer"]
    b = _ask(store, "lineage of ED_ENCOUNTERS_DM")["answer"]
    assert a == b


def test_op2_filters_on_voices_the_grammar(store):
    result = _ask(store, "filters on THERA_CLASS_CODE")
    assert result["op"] == "filters_on"
    # voiced through the DICTIONARY words (R5), not the raw name
    assert "is 11 (annotated 'Antibiotics' in the source)" in \
        result["answer"]
    assert "therapeutic class" in result["answer"]


def test_op3_lineage_finds_the_readmit_scope(store):
    result = _ask(store, "lineage of ED_ENCOUNTERS_DM")
    assert result["outcome"] == "matched"
    assert "#Base_Pop_ED_Readmit" in result["answer"]


def test_op5_gaps_prints_the_taxonomy(store):
    result = _ask(store, "gaps")
    assert "GAP TAXONOMY" in result["answer"]
    assert "drift refs (estate findings)" in result["answer"]


def test_op6_scope_answers_with_its_own_floor_no_shapes(store):
    result = _ask(store, "what is "
                  "reporting/USP_ED_SEPSIS.sql::#Base_Pop_ED_Readmit")
    assert "Drawn from the ed positivescores selection" in \
        result["answer"]
    assert "24 hours after" in result["answer"]
    assert "The first time line is 1." in result["answer"]


def test_llm_parse_hook_is_caged(store):
    # a model proposing an op OUTSIDE the closed set is refused and
    # the deterministic parse stands — parse, never generate
    result = ask.ask(store, "what is emr|dbo|PATIENTS",
                     author="person:test",
                     occurred_at=T0,
                     llm_parse=lambda q: ("write_me_a_poem", "x"))
    assert result["op"] == "lookup"
    assert result["outcome"] == "matched"
