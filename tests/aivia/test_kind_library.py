"""Slice 2: the kind-library case families (F7) — construct,
adversarial (the corpse catalog securing PM-4's clean-room bet), and
remainder (conservation: a deferred construct is COUNTED, never
guessed). Requires ScriptDom (no fallback grammar exists, ADR 0001).

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.graph import kg2_mapper

CASES = json.loads((pathlib.Path(__file__).resolve().parents[2] /
                    "AIVIA_Product" / "fixtures" / "F7_kind_library" /
                    "cases.json").read_text())


def _where(tree):
    return tree["statements"][0]["scope"]["where"]


def _ids(family):
    return [c["id"] for c in CASES[family]]


@pytest.mark.parametrize("case_id", _ids("construct"))
def test_construct_case(case_id):
    case = next(c for c in CASES["construct"] if c["id"] == case_id)
    tree = kg2_mapper.map_tree("case.sql", case["sql"])
    assert tree["remainder"] == [], "construct cases map with EMPTY remainder"
    where = _where(tree)
    assert where["kind"] == case["where_kind"]
    for role, kind in case.get("roles", {}).items():
        assert where[role]["kind"] == kind, role
    if "child_kinds" in case:
        assert [c["kind"] for c in where["children"]] == case["child_kinds"]
    if "comparand_count" in case:
        members = where["comparand_list"]
        assert len(members) == case["comparand_count"]
        assert [m["position"] for m in members] == \
            list(range(1, len(members) + 1))
    for prop, value in case.get("properties", {}).items():
        got = where[prop]
        assert value.lower() in str(got).lower(), (prop, got)


@pytest.mark.parametrize("case_id", _ids("adversarial"))
def test_adversarial_case(case_id):
    case = next(c for c in CASES["adversarial"] if c["id"] == case_id)
    tree = kg2_mapper.map_tree("case.sql", case["sql"])
    assert tree["remainder"] == []
    if "where_kind" in case:
        where = _where(tree)
        assert where["kind"] == case["where_kind"]
        if "child_kinds" in case:
            assert [c["kind"] for c in where["children"]] == \
                case["child_kinds"]
        for role, kind in case.get("roles", {}).items():
            assert where[role]["kind"] == kind
    expect = case.get("expect", {})
    scope = tree["statements"][0]["scope"]
    if "inner_scope_predicates" in expect:
        derived = [r["derived_scope"] for r in scope["from_refs"]
                   if "derived_scope" in r]
        assert len(derived) == 1
        inner = derived[0]["where"]
        assert [inner["kind"]] == expect["inner_scope_predicates"]
        assert [scope["where"]["kind"]] == expect["outer_scope_predicates"]
    if "scope_names" in expect:
        ctes = tree["statements"][0].get("ctes", [])
        assert [c["name"] for c in ctes] == expect["scope_names"]
        assert [c["name_key"] for c in ctes] == \
            [f"case.sql::{n}" for n in expect["scope_names"]]


@pytest.mark.parametrize("case_id", _ids("remainder"))
def test_remainder_case(case_id):
    case = next(c for c in CASES["remainder"] if c["id"] == case_id)
    tree = kg2_mapper.map_tree("case.sql", case["sql"])
    assert len(tree["remainder"]) == case["expect_remainder"]
    assert case["remainder_contains"] in tree["remainder"][0]["type"]
    assert tree["remainder"][0]["fragment"], "remainder carries evidence"


def test_duplicate_scope_names_get_hash_suffix():
    sql = ("WITH Base AS (SELECT A FROM dbo.T) "
           "SELECT B.A INTO #Base FROM Base B")
    tree = kg2_mapper.map_tree("f.sql", sql)
    keys = [c["name_key"] for c in tree["statements"][0]["ctes"]]
    assert keys == ["f.sql::Base"]  # distinct names -> no suffix needed
    sql2 = ("WITH Base AS (SELECT A FROM dbo.T) SELECT B.A FROM Base B; "
            "WITH Base AS (SELECT C FROM dbo.U) SELECT B.C FROM Base B")
    tree2 = kg2_mapper.map_tree("f.sql", sql2)
    keys2 = [c["name_key"] for s in tree2["statements"]
             for c in s.get("ctes", [])]
    assert keys2 == ["f.sql::Base", "f.sql::Base#2"]  # A3's model
