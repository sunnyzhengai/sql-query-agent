"""ADR 0074's implementation contract, locked in RED (the 0044
pattern): every D-item's exit gate is a strict-xfail test here —
CI fails the moment one starts passing until its marker is removed,
so flipping a marker IS the exit gate.

Wiring fact the contract pins (found at lock time): describe_step —
the DESC-MEANING-1 skeleton path — exists and is unit-tested but is
NOT wired into generate_descriptions; the production loop still runs
the pre-skeleton acceptance and can fail `grounded_to_empty`.

Proves: spec:B2
"""

from __future__ import annotations

import pytest

from src.descriptions import PROVENANCE, DescriptionResult
from src.models import NodeLayer

D = pytest.mark.xfail(strict=True, reason="ADR 0074 build item — red "
                      "by design until its D-item ships")


# ---------------------------------------------------------------- D1
def test_d1_provenance_vocabulary_matches_the_spec_ledger():
    """GREEN NOW (the vocabulary is the ratified law): the code's
    closed set must equal spec:B2's — one writer, cross-checked."""
    from src.spec_registry import SPEC_REGISTRY
    law = SPEC_REGISTRY["B2"]["law"]
    inside = law.split("{")[1].split("}")[0]
    assert tuple(x.strip() for x in inside.split(",")) == PROVENANCE


def test_d1_every_described_node_carries_provenance():
    # FLIPPED 09-02 (D1 shipped: provenance through result, cache
    # tuple values, ops_description_cache column + allowed_values)
    """Exit: DescriptionResult labels every stored description with a
    value from the closed set; the cache carries it; the
    ops_description_cache contract declares the column with an
    allowed_values invariant."""
    r = DescriptionResult()
    assert hasattr(r, "provenance"), "DescriptionResult.provenance missing"
    from src.schemas import DESCRIPTION_CACHE
    cols = [c[0] for c in DESCRIPTION_CACHE["columns"]]
    assert "provenance" in cols


# ---------------------------------------------------------------- D2
def test_d2_the_instrument_declares_its_build_stopper():
    # FLIPPED 09-02 (THRESHOLDS as data on the corpus instrument)
    """Exit: the corpus instrument (grown from devtools/desc_corpus)
    pins thresholds as data — fabrications past the retry = 0 is the
    BUILD-STOPPER, emptied counted; the scorecard is emitted, the
    re-scoped round-trip verifier grades gate output (spec:F/T1 as
    the measurement instrument)."""
    from devtools import desc_corpus
    th = desc_corpus.THRESHOLDS
    assert th["fabricated"] == 0 and th["role"] == "build_stopper"


# ---------------------------------------------------------------- D3
@D
def test_d3_single_statement_procs_get_a_file_description():
    """Exit (DESC-WHOLE-1, 46% of the estate silent): the deliverable
    is a description per SQL FILE — a single-SELECT proc with no
    steps still yields one block; result exposes file-level
    coverage."""
    r = DescriptionResult()
    assert hasattr(r, "file_descriptions")


# ------------------------------------------------- D-wiring (D1/D3)
def test_wiring_skeleton_floor_replaces_grounded_to_empty():
    # FLIPPED 09-02 (the 0074 wiring: describe_step in the loop)
    """Exit: generate_descriptions routes steps through the skeleton
    path — a describe() that returns ungroundable garbage yields the
    SKELETON (plain but true), provenance skeleton_floor, never a
    grounded_to_empty failure. (Today: the old path fails the node.)"""
    import json

    from src.descriptions import generate_descriptions
    nodes = [{
        "node_id": "t1", "name": "Base_Pop",
        "layer": NodeLayer.TRANSFORMATION.value,
        "properties": json.dumps({"sql_fragment":
                       "SELECT PATIENT_ID INTO #Base_Pop FROM "
                       "HOSPITAL_ENCOUNTERS WHERE ADMIT_DATE IS NOT NULL"}),
    }]
    r = generate_descriptions(nodes, [], lambda p: "The 123/456 codes "
                              "prove eligibility per policy 9.")
    assert r.descriptions.get("t1"), "skeleton floor did not ship"
    assert r.provenance.get("t1") == "skeleton_floor"


def test_wiring_voice_kill_beats_the_skeleton_and_is_counted():
    # FLIPPED 09-02 (result.emptied — the empties-(a) counter)
    """Exit (the empties-(a) ruling's precedence, ADR 0074 §5.3a:
    voice/gate kill > skeleton floor > absent): when even the
    skeleton violates voice, the description is ABSENT and the node
    is COUNTED on a dedicated field — never stored, never silent."""
    r = DescriptionResult()
    assert hasattr(r, "emptied"), "the emptied counter is not a field"


# ---------------------------------------------------------------- D4
@D
def test_d4_the_xray_report_carries_the_description_sample():
    """Exit (the wedge contract, 0074 call 4): the report includes a
    hand-gradable description sample with provenance chips."""
    src = open("devtools/run_xray.py").read()
    assert "description sample" in src.lower()
    assert "provenance" in src.lower()


# ------------------------------------------------- D5: FLIPPED 09-02
def test_d5_derived_table_filters_do_not_leak_into_the_outer_step():
    """GREEN (exit gate flipped 2026-09-02 — DESC-SKELETON-3 shipped:
    scope-aware AST composer): a filter
    inside a derived table is the DERIVED step's decision; the outer
    step's skeleton must not claim it as its own."""
    from src.descriptions import compose_skeleton
    frag = ("SELECT e.PATIENT_ID FROM HOSPITAL_ENCOUNTERS e "
            "JOIN (SELECT ENCOUNTER_ID FROM LAB_RESULTS "
            "WHERE RESULT_FLAG = 'ABNORMAL') d "
            "ON d.ENCOUNTER_ID = e.ENCOUNTER_ID "
            "WHERE e.ADMIT_DATE IS NOT NULL")
    sk = compose_skeleton(frag, {"ADMIT_DATE": "admission date",
                                 "RESULT_FLAG": "lab result flag"})
    assert "ABNORMAL" not in sk, (
        "derived-table filter leaked into the outer step's skeleton")
