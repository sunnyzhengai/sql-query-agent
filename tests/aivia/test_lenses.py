"""Slice 3 exit: the F3 answer key against the BUILT lenses.

Lenses are pure reads over read_api (the plank enforces the import
law); every yield declares completeness. F3 asserts: membership
decisions per scope (join keys and both-sides-literals EXCLUDED — the
09-05 ruling), the degenerate yield, join compliance with the A12
direct-only boundary and its declared loophole, the working set, the
gap census, and staleness_t0 == the F4 produce worklist. Referenced
keys check against F1's expected map. Derivation lenses run total
over the (empty until slice 4) artifact layer.
"""
import json
import pathlib

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake
from aivia.graph.read_api import ReadApi
from aivia.graph.store import Store
from aivia.lenses import census, compliance, decisions, derivation, families, registry

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


@pytest.fixture(scope="module")
def read():
    store = Store()
    reg = json.loads((FIX / "F1_minimal_estate" / "registration.json")
                     .read_text())
    kg1_intake.apply_registration(store, reg)
    for src in ("simemr", "org"):
        inbound.receive_extract(
            store, reg,
            kg1_intake.load_snapshot(FIX / "F1_minimal_estate"
                                     / f"{src}_snapshot"),
            known_packs=KNOWN_PACKS)
    inbound.receive_estate(store, reg,
                           FIX / "F2_estate_files" / "estate_snapshot")
    return ReadApi(store)


@pytest.fixture(scope="module")
def f3():
    return json.loads((FIX / "F3_lenses" / "expected_lenses.json")
                      .read_text())


def test_decisions_membership_matches_answer_key(read, f3):
    got = decisions.lens_decisions(read, {"class": "membership"})
    for key, want in f3["decisions_membership"].items():
        if key.startswith("_") or key == "completeness":
            continue
        assert got["yield"].get(key, []) == want, key
    assert got["completeness"] == "total per tree"


def test_degenerate_matches_answer_key(read, f3):
    got = decisions.lens_degenerate(read, None)
    assert got["yield"] == f3["degenerate"]["yield"]
    assert got["completeness"] == "total"


def test_join_compliance_matches_answer_key(read, f3):
    got = compliance.lens_join_compliance(read, None)
    want = f3["join_compliance"]
    assert len(got["violations"]) == len(want["violations"])
    for w, g in zip(want["violations"], got["violations"]):
        assert g["file"] == w["file"]
        assert g["practiced"] == w["practiced"]
        assert g["declared_path"] == w["declared_path"]
    want_compliant = [{k: v for k, v in c.items() if not k.startswith("_")}
                      for c in want["compliant_practiced"]]
    assert got["compliant_practiced"] == want_compliant
    # A12: exactly one scope-mediated join in this estate, NOT judged
    assert len(got["not_judged"]) == 1
    assert "declared" in got["completeness"]  # the loophole, on every result


def test_working_set_matches_answer_key(read, f3):
    got = census.lens_working_set(read, None)
    assert set(got["yield"]) == set(f3["working_set"]["yield"])
    assert set(got["not_touched"]) == set(f3["working_set"]["not_touched"])
    assert got["completeness"] == "total over resolved refs"


def test_gap_census_matches_answer_key(read, f3):
    got = census.lens_gap_census(read, None)
    want = f3["gap_census"]
    assert got["unresolved_refs"] == want["unresolved_refs"]
    assert got["grain_not_declared"] == want["grain_not_declared"]
    assert got["keyless_tables"] == want["keyless_tables"]
    assert got["unmapped_remainder"] == want["unmapped_remainder"]
    assert got["unsupported_dialect_files"] == \
        want["unsupported_dialect_files"]


def test_staleness_t0_is_the_produce_worklist(read, f3):
    got = derivation.lens_staleness(read, None)
    assert set(got["yield"]) == set(f3["staleness_t0"]["yield"])
    f4 = json.loads((FIX / "F4_produce" / "expected_produce.json")
                    .read_text())
    assert set(got["yield"]) == set(f4["targets"])  # PROD-2 as arithmetic


def test_referenced_keys_matches_f1_expected(read):
    f1 = json.loads((FIX / "F1_minimal_estate" / "expected_graph.json")
                    .read_text())
    want = {k: {tuple(ks) for ks in v}
            for k, v in f1["nodes"]["referenced_keys_expected"].items()
            if not k.startswith("_")}
    got = census.lens_referenced_keys(read, None)
    assert {k: {tuple(ks) for ks in v}
            for k, v in got["yield"].items()} == want
    assert got["completeness"] == "total over referenced tables"


def test_derivation_lenses_total_over_the_t0_artifact_layer(read):
    """At t0 exactly ONE layer-3 citizen exists: the dba responsibility
    minted from the registration prerequisite (F1's layer3_expected).
    The derivation lenses must find it — and nothing else."""
    dba = "responsibility:dba:db:SIMDB"
    for lens in (derivation.lens_ownership, derivation.lens_authorship,
                 derivation.lens_version, derivation.lens_standing):
        got = lens(read, None)
        assert set(got["yield"]) == {dba}, lens.__name__
        assert got["completeness"].startswith("total")
    assert derivation.lens_ownership(read, None)["yield"][dba] == "human"
    assert derivation.lens_standing(read, None)["yield"][dba] == "pending"
    assert derivation.lens_current_outcome(read, None)["yield"] == {}


def test_relatedness_is_deterministic_and_total(read):
    a = families.lens_relatedness(read, None)
    b = families.lens_relatedness(read, None)
    assert a == b  # M5: same graph state, same answer, replayable
    assert a["completeness"] == "total over parsed estate"
    member_files = {f for fam in a["yield"].values() for f in fam}
    assert member_files == {"usp_diabetic_visits.sql",
                            "vw_completed_visits.sql", "usp_odd_join.sql"}


def test_check_lens_d1_catalog_closure(read):
    """CHECK-LENS-D1: every v1 catalog row has exactly one implementation
    and nothing is implemented off-catalog — reachability as arithmetic."""
    problems = registry.d1_closure()
    assert problems == []


def test_every_lens_declares_completeness(read):
    for name, fn in registry.V1_LENSES.items():
        result = fn(read, {"class": "membership"} if "decisions" in name
                    else None)
        assert "completeness" in result, name
        data_keys = set(result) - {"completeness", "stamp"}
        assert data_keys, f"{name}: declares completeness over nothing"
