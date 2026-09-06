"""Slice 2 exit: the F2 answer key against the BUILT trees.

Walks every assertion the ratified key states: statement kinds and
positions, scope name_keys (A11 ::delivery), from_ref resolutions,
predicate kinds with subject/comparand resolutions, the parameter-
default pattern, estate conservation (E5), and the resolution census
(unresolved and same-tree EXACT; resolved is a superset — the key
enumerates the deciding refs, the mapper resolves all of them).

Also here: GV-E evidence tiling goes RUNNABLE (every node's fragment
locatable at its recorded offset; child spans nested in statement
spans) and CHECK-KG2-7 conformance (built kinds validate against the
ratified kind library). Requires ScriptDom — no fallback (ADR 0001).

Proves: contract:aivia-design-to-code
"""
import json
import pathlib

import pytest

from aivia.flows import inbound
from aivia.graph import kg1_intake, metamodel
from aivia.graph.store import Store

FIX = pathlib.Path(__file__).resolve().parents[2] / "AIVIA_Product" / "fixtures"
F1 = FIX / "F1_minimal_estate"
F2 = FIX / "F2_estate_files"
KNOWN_PACKS = {"simemr-pack-0.1", "org-pack-0.1"}


@pytest.fixture(scope="module")
def built():
    store = Store()
    reg = json.loads((F1 / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    for src in ("simemr", "org"):
        inbound.receive_extract(
            store, reg, kg1_intake.load_snapshot(F1 / f"{src}_snapshot"),
            known_packs=KNOWN_PACKS)
    report = inbound.receive_estate(store, reg, F2 / "estate_snapshot")
    return store, reg, report


@pytest.fixture(scope="module")
def expected():
    return json.loads((F2 / "expected_trees.json").read_text())


def _norm_where(where):
    if where is None:
        return None, []
    if where["kind"] in ("AND", "OR"):
        return where["kind"], where["children"]
    return None, [where]


def _expr_matches(exp, got):
    if "column_ref" in exp:
        assert got["kind"] == "column_ref" and got["ref"] == exp["column_ref"]
    elif "parameter_ref" in exp:
        assert got["kind"] == "parameter_ref"
        assert got["ref"] == exp["parameter_ref"]
    elif "literal" in exp:
        assert got["kind"] == "literal" and got["value"] == exp["literal"]
    if "resolves_to" in exp:
        want = exp["resolves_to"]
        if want and want.startswith("file parameter"):
            assert got["resolves_to"] == want
        else:
            assert got.get("resolves_to") == want


def _predicate_matches(exp, got):
    assert got["kind"] == exp["kind"]
    for role in ("subject", "comparand", "pattern"):
        if role in exp and isinstance(exp[role], dict):
            _expr_matches(exp[role], got[role])
    if "comparand_list" in exp:
        assert len(got["comparand_list"]) == len(exp["comparand_list"])
        for e, g in zip(exp["comparand_list"], got["comparand_list"]):
            assert g["position"] == e["position"]
            assert g["value"] == e["literal"]


def test_estate_conservation(built, expected):
    _, _, report = built
    # E5 is a SET equation (acquired u excluded = present) — the key's
    # list order is authoring order, not a contract
    assert set(report.acquired) == \
        set(expected["estate_conservation"]["acquired"])
    got_excluded = {e["file"] for e in report.counted_excluded}
    want_excluded = {e["file"] for e in
                     expected["estate_conservation"]["counted_excluded"]}
    assert got_excluded == want_excluded


def test_every_expected_file_assertion_holds(built, expected):
    _, _, report = built
    for exp_file in expected["files"]:
        name = exp_file["id"].rsplit("/", 1)[1]
        tree = report.trees[name]
        assert tree["dialect"] == exp_file["dialect"]
        assert len(tree["statements"]) == len(exp_file["statements"])
        for exp_stmt in exp_file["statements"]:
            stmt = tree["statements"][exp_stmt["position"] - 1]
            assert stmt["statement_kind"] == \
                exp_stmt["statement_kind"].split(" (")[0]
            if "predicate" in exp_stmt:
                assert stmt["predicate"]["kind"] == \
                    exp_stmt["predicate"]["kind"]
            if "parameter_node" in exp_stmt:
                want = exp_stmt["parameter_node"]
                assert {"name": want["name"],
                        "default_logic": want["default_logic"]} in \
                    [{"name": p["name"], "default_logic": p["default_logic"]}
                     for p in tree["parameters"]]
            if "scope" not in exp_stmt:
                continue
            exp_scope, scope = exp_stmt["scope"], stmt["scope"]
            if "name_key" in exp_scope:
                assert scope["name_key"] == exp_scope["name_key"]
            if "structures" in exp_scope:
                assert set(exp_scope["structures"]) <= \
                    set(scope["structures"])
            for exp_ref in exp_scope.get("from_refs", []):
                got_ref = next(r for r in scope["from_refs"]
                               if r.get("table_ref") == exp_ref["table_ref"])
                assert got_ref["resolves_to"] == exp_ref["resolves_to"]
            for exp_ref in exp_scope.get("select_refs", []):
                got = next(r for r in scope["select_refs"]
                           if r.get("ref") == exp_ref["column_ref"])
                assert got.get("resolves_to") == exp_ref["resolves_to"]
            if "join_on" in exp_scope:
                got_kinds = [j["kind"] for j in scope["join_on"]]
                assert got_kinds == [j["kind"] for j in exp_scope["join_on"]]
            if "where" in exp_scope:
                boolean, predicates = _norm_where(scope["where"])
                if "boolean" in exp_scope["where"]:
                    assert boolean == exp_scope["where"]["boolean"]
                exp_preds = exp_scope["where"]["predicates"]
                assert len(predicates) == len(exp_preds)
                for e, g in zip(exp_preds, predicates):
                    _predicate_matches(e, g)


def test_resolution_census(built, expected):
    _, _, report = built
    cen = expected["resolution_census"]
    resolved = sum(t["resolution_census"]["resolved_refs"]
                   for t in report.trees.values())
    same_tree = sum(t["resolution_census"]["same_tree_refs"]
                    for t in report.trees.values())
    unresolved = [u for t in report.trees.values()
                  for u in t["resolution_census"]["unresolved"]]
    assert resolved >= cen["resolved_refs"]  # key enumerates the deciders
    assert same_tree == cen["same_tree_refs"]
    assert unresolved == ["L.NOTE_TXT"]


def test_no_plural_emitters_in_this_estate(built, expected):
    _, _, report = built
    assert expected["multi_result_set_files"]["expected"] == []
    for tree in report.trees.values():
        assert tree["plural_emitters"] is False


def test_no_phi_redactions_in_fixture_estate(built):
    _, _, report = built
    for tree in report.trees.values():
        assert tree["phi_redactions"] == 0


def _walk_evidence(node, out):
    if isinstance(node, dict):
        if "evidence" in node:
            out.append(node["evidence"])
        for v in node.values():
            _walk_evidence(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_evidence(v, out)


def test_gv_e_evidence_tiling_now_runnable(built):
    """GV-E against the BUILT mapper (closes the fixture validator's
    honest NOT-RUNNABLE): every node's fragment is locatable at its
    recorded offset in the file text, and every node's span nests
    inside its statement's span."""
    _, _, report = built
    est = F2 / "estate_snapshot"
    for name, tree in report.trees.items():
        text = est.joinpath(name).read_text() \
            .replace("\r\n", "\n").replace("\r", "\n")
        for stmt in tree["statements"]:
            s_ev = stmt["evidence"]
            s_start, s_end = s_ev["offset"], s_ev["offset"] + \
                len(s_ev["fragment"])
            nodes = []
            _walk_evidence(stmt, nodes)
            assert nodes, name
            for ev in nodes:
                start = ev["offset"]
                assert text[start:start + len(ev["fragment"])] == \
                    ev["fragment"], (name, ev)
                assert s_start <= start and \
                    start + len(ev["fragment"]) <= s_end


def test_check_kg2_7_built_kinds_conform_to_the_registry(built):
    kl = metamodel.load("kg2_kind_library").sheets
    predicate_kinds = {r["Kind"] for r in kl["Predicate_Kinds"]
                       if not r["Kind"].startswith("(")}
    structure_kinds = {r["Kind"] for r in kl["Structure_Kinds"]
                       if not r["Kind"].startswith("(")}
    expression_kinds = {r["Kind"] for r in kl["Expression_Kinds"]}
    _, _, report = built

    def walk(node):
        if isinstance(node, dict):
            family, kind = node.get("node"), node.get("kind")
            if family == "predicate":
                assert kind in predicate_kinds | {"remainder"}, kind
            elif family == "structure":
                assert kind in structure_kinds, kind
            elif family == "expression":
                assert kind in expression_kinds | {"remainder_ref"}, kind
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    for tree in report.trees.values():
        walk(tree["statements"])


def test_estate_reapply_is_idempotent(built):
    store, reg, _ = built
    stamp = store.state_stamp()
    inbound.receive_estate(store, reg, F2 / "estate_snapshot")
    assert store.state_stamp() == stamp
