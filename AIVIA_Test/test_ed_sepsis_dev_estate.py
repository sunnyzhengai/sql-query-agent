"""The one-proc dev estate + THE M-GATE ANSWER KEY (Sunny's
rulings 2026-09-10, incl. the M2 REDESIGN): batches build, test,
and gate on ed_sepsis_dev (USP_ED_SEPSIS alone); every batch
gates on the FULL CENSUS — every label counted, every edge type
counted, exact both directions (the blob-corpse lesson: spot
checks pass while the graph doesn't exist).

The redesigned ladder: M1 technical (+joins_to, re-homed) →
M2 THE JOIN LAYER (scope + join + sides + the reads REMAINDER) →
M3 THE CONDITION LAYER (condition + param) → M4 derived_column →
M5 statement → M6 file → M7 governance. Joins and conditions are
SEPARATE batches so each is testable alone (Sunny's ruling).

The key (expected_m_gates.json) is AUTHORED AHEAD, derived from
the twin. These tests recompute every derivable number from the
twin each run and hold the key to them — the key cannot rot
silently; a metamodel bump that moves a number fails here by
name, and the key updates by hand with the bump recorded.

Proves: contract:aivia-design-to-code
"""
import json
import pathlib
import re
from collections import Counter

import pytest

from aivia.console import build_store
from aivia.flows.export_graph import export_tables
from aivia.graph.read_api import ReadApi

FILE_ID = "repo://sepsis-corpus/reporting/USP_ED_SEPSIS.sql"
BASE = pathlib.Path(__file__).resolve().parents[1] / \
    "AIVIA_Product" / "estates" / "ed_sepsis_dev"
KEY = json.loads((BASE / "expected_m_gates.json").read_text())
CENSUS = KEY["census_after"]
DELTA = KEY["batch_deltas"]


@pytest.fixture(scope="module")
def booted():
    store, base = build_store("ed_sepsis_dev")
    assert base == BASE
    return store


@pytest.fixture(scope="module")
def exported(booted):
    return export_tables(ReadApi(booted))


@pytest.fixture(scope="module")
def twin(booted):
    blob = booted.current_nodes("meaning_twin")[0].properties["twin"]
    assert isinstance(blob, dict)
    assert blob["translator_version"] == KEY["basis"]["translator_version"]
    assert blob["metamodel_version"] == KEY["basis"]["metamodel_version"]
    return blob["nodes"]


def _in_scope(path):
    return "/scope" in path or "/ctes/" in path


def _columns(ids):
    return [i for i in ids if i.count("|") == 3]


def _join_containers(twin):
    return sorted({m.group(1) for n in twin
                   for m in [re.search(r"^(.*?/join_on/\d+)",
                                       n["points_at"])] if m})


# ---------------------------------------------------------------
# the estate itself
# ---------------------------------------------------------------

def test_one_file_full_dictionary(booted):
    files = booted.current_nodes("file")
    assert [n.identity for n in files] == [FILE_ID]
    # KG1 is dictionary truth, never narrowed by which procs read it
    assert len(booted.current_nodes("table")) == 90
    assert len(booted.current_nodes("column")) == 4554
    assert len(booted.current_edges("joins_to")) == 65


# ---------------------------------------------------------------
# the census tables are internally consistent: totals equal the
# sum of parts; each batch's census equals the prior plus its delta
# ---------------------------------------------------------------

def test_census_arithmetic():
    for m, c in CENSUS.items():
        if m.startswith("_"):
            continue
        assert sum(c["nodes"].values()) == c["node_total"], m
        assert sum(c["edges"].values()) == c["edge_total"], m
    order = ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]
    for prev, cur in zip(order, order[1:]):
        grew = {k: CENSUS[cur]["nodes"].get(k, 0)
                - CENSUS[prev]["nodes"].get(k, 0)
                for k in CENSUS[cur]["nodes"]}
        want = {k: v for k, v in DELTA[cur]["new_nodes"].items() if v}
        assert {k: v for k, v in grew.items() if v} == want, cur
        edge_growth = sum(CENSUS[cur]["edges"].values()) \
            - sum(CENSUS[prev]["edges"].values())
        assert edge_growth == sum(DELTA[cur]["new_edges"].values()), cur


# ---------------------------------------------------------------
# M1 — the technical layer + joins_to (re-homed): export matches
# ---------------------------------------------------------------

def test_m1_export_matches_census(exported):
    want = CENSUS["M1"]
    got_nodes = {"db": 1, "db_schema": 3,
                 "table": len(exported["graph_table"]),
                 "column": len(exported["graph_column"])}
    assert got_nodes == want["nodes"]
    has_part = (len(exported["graph_has_part_dbSchema"])
                + len(exported["graph_has_part_schemaTable"])
                + len(exported["graph_has_part_tableColumn"]))
    assert has_part == want["edges"]["has_part"]
    assert len(exported["graph_joins_to_tableTable"]) \
        == want["edges"]["joins_to"]


def test_scope_descriptions_stored(exported):
    # scopes carry stored descriptions (built; they ship in M2)
    want = DELTA["M2"]["checks"]["scope_descriptions_nonempty"]
    scopes = exported["graph_scope"]
    assert len(scopes) == DELTA["M2"]["new_nodes"]["scope"]
    assert sum(1 for r in scopes if r["description"].strip()) == want
    # NOTE: the export's current reads table (45 true-grain edges) is
    # SUPERSEDED by the remainder rule — the reworked M2 export ships
    # join nodes + sides + ~6 remainder reads; pinned at build.


# ---------------------------------------------------------------
# M2 — THE JOIN LAYER (BUILT 2026-09-10; the STORE is the truth
# the key is held against — twin-derived authoring retired here)
# ---------------------------------------------------------------

def test_m2_store_matches_census(booted, exported):
    want = CENSUS["M2"]
    got_nodes = {"db": 1, "db_schema": 3,
                 "table": len(exported["graph_table"]),
                 "column": len(exported["graph_column"]),
                 "scope": len(exported["graph_scope"]),
                 "join": len(exported["graph_join"])}
    assert got_nodes == want["nodes"]
    has_part = (len(exported["graph_has_part_dbSchema"])
                + len(exported["graph_has_part_schemaTable"])
                + len(exported["graph_has_part_tableColumn"])
                + len(exported["graph_has_part_scopeJoin"]))
    left = (len(exported["graph_left_side_joinTable"])
            + len(exported["graph_left_side_joinScope"]))
    right = (len(exported["graph_right_side_joinTable"])
             + len(exported["graph_right_side_joinScope"]))
    got_edges = {"has_part": has_part,
                 "joins_to": len(exported["graph_joins_to_tableTable"]),
                 "left_side": left, "right_side": right,
                 "reads": len(exported["graph_reads_scopeTable"])}
    assert got_edges == want["edges"]
    d = DELTA["M2"]
    assert d["side_targets"]["table"] == \
        len(exported["graph_left_side_joinTable"]) \
        + len(exported["graph_right_side_joinTable"])
    assert d["side_targets"]["scope"] == \
        len(exported["graph_left_side_joinScope"]) \
        + len(exported["graph_right_side_joinScope"])


def test_m2_join_conservation_and_verbatim(booted):
    from aivia.flows.inbound import join_render
    want = DELTA["M2"]["join_conservation"]
    joins = booted.current_nodes("join")
    left = {e.from_id: e.to_id
            for e in booted.current_edges("left_side")}
    right = {e.from_id: e.to_id
             for e in booted.current_edges("right_side")}
    two = sum(1 for j in joins
              if j.identity in left and j.identity in right)
    one = sum(1 for j in joins
              if j.identity in left and j.identity not in right)
    none = len(joins) - two - one
    assert {"joins": len(joins), "two_sided": two, "one_sided": one,
            "no_sided": none, "overflow_3plus": 0} == want
    # every join has a birth edge from its scope, a non-empty
    # description, and — the verbatim law — stored == recomputed
    parents = {e.to_id for e in booted.current_edges("has_part")
               if "::join#" in e.to_id}
    for j in joins:
        assert j.identity in parents
        sides = [s for s in (left.get(j.identity),
                             right.get(j.identity)) if s]
        assert j.properties["description"] == \
            join_render(sides, j.properties["on"])


def test_m2_drift_query_on_store(booted):
    """THE PRODUCT QUERY, live on the built store: practiced pairs
    with no declared joins_to == exactly the two findings."""
    tables = {n.identity for n in booted.current_nodes("table")}
    left = {e.from_id: e.to_id
            for e in booted.current_edges("left_side")}
    right = {e.from_id: e.to_id
             for e in booted.current_edges("right_side")}
    declared = set()
    for e in booted.current_edges("joins_to"):
        declared.add((e.from_id, e.to_id))
        declared.add((e.to_id, e.from_id))
    findings = set()
    for j, a in left.items():
        b = right.get(j)
        if b and a in tables and b in tables and (a, b) not in declared:
            findings.add(tuple(sorted((a, b))))
    assert sorted(findings) == [
        tuple(f) for f in DELTA["M2"]["checks"]["drift_findings_exact"]]


def test_m2_coverage_invariants(booted):
    """Disjoint: no table connected by BOTH a reads edge and a join
    side of the same scope. Covering: remainder + covered == the
    parse read-set (nothing silently unconnected)."""
    tables = {n.identity for n in booted.current_nodes("table")}
    side_tabs = {}
    for lbl in ("left_side", "right_side"):
        for e in booted.current_edges(lbl):
            if e.to_id in tables:
                scope = e.from_id.rsplit("::join#", 1)[0]
                side_tabs.setdefault(scope, set()).add(e.to_id)
    reads = booted.current_edges("reads")
    assert all(e.to_id not in side_tabs.get(e.from_id, set())
               for e in reads)
    want = DELTA["M2"]["reads"]
    assert len(reads) == want["remainder"]
    # covering: the union equals the read-set measured at build
    assert len(reads) + want["covered_by_join_sides"] \
        == want["read_set"]


# ---------------------------------------------------------------
# M3 — THE CONDITION LAYER (BUILT 2026-09-10; the STORE is the
# truth — the tree out-counts the twin, precedent joins 95 vs 93)
# ---------------------------------------------------------------

def test_m3_store_matches_census(booted, exported):
    want = CENSUS["M3"]
    got_nodes = {"db": 1, "db_schema": 3,
                 "table": len(exported["graph_table"]),
                 "column": len(exported["graph_column"]),
                 "scope": len(exported["graph_scope"]),
                 "join": len(exported["graph_join"]),
                 "condition": len(exported["graph_condition"]),
                 "param": len(exported["graph_param"])}
    assert got_nodes == want["nodes"]
    has_part = sum(len(v) for k, v in exported.items()
                   if k.startswith("graph_has_part"))
    resolves = (len(exported["graph_resolves_to_conditionColumn"])
                + len(exported["graph_resolves_to_conditionParam"]))
    got_edges = {"has_part": has_part,
                 "joins_to": len(exported["graph_joins_to_tableTable"]),
                 "left_side": len(exported["graph_left_side_joinTable"])
                 + len(exported["graph_left_side_joinScope"]),
                 "right_side": len(exported["graph_right_side_joinTable"])
                 + len(exported["graph_right_side_joinScope"]),
                 "reads": len(exported["graph_reads_scopeTable"]),
                 "resolves_to": resolves,
                 "uses_param": len(exported["graph_uses_param_scopeParam"])}
    assert got_edges == want["edges"]


def test_m3_condition_conservation_and_kinds(booted):
    want = DELTA["M3"]
    conds = booted.current_nodes("condition")
    assert len(conds) == want["new_nodes"]["condition"]
    parents = {e.to_id: e.from_id
               for e in booted.current_edges("has_part")
               if "::cond#" in e.to_id}
    roots_join = sum(1 for c in conds
                     if "::join#" in parents.get(c.identity, ""))
    nested = sum(1 for c in conds
                 if "::cond#" in parents.get(c.identity, ""))
    roots_scope = len(conds) - roots_join - nested
    got = {"conditions": len(conds), "roots_join": roots_join,
           "roots_scope": roots_scope, "nested": nested}
    assert got == want["condition_conservation"]
    kinds = Counter(c.properties["kind"] for c in conds)
    assert dict(kinds) == want["condition_by_kind"]
    assert sum(1 for c in conds
               if c.properties["degenerate"] == "true") \
        == want["condition_degenerate"]
    # every condition has a parent, a kind, and a description
    for c in conds:
        assert c.identity in parents
        assert c.properties["kind"]
        assert c.properties["description"].strip()


def test_m3_resolves_roles_and_params(booted):
    want = DELTA["M3"]
    roles = Counter(e.properties.get("role")
                    for e in booted.current_edges("resolves_to"))
    assert dict(roles) == want["resolves_to_roles"]
    cols = [e for e in booted.current_edges("resolves_to")
            if "::param/" not in e.to_id]
    pars = [e for e in booted.current_edges("resolves_to")
            if "::param/" in e.to_id]
    assert len(cols) == want["new_edges"]["resolves_to_conditionColumn"]
    assert len(pars) == want["new_edges"]["resolves_to_conditionParam"]
    params = sorted(n.properties["name"]
                    for n in booted.current_nodes("param"))
    assert params == want["param_names"]
    assert len(booted.current_edges("uses_param")) \
        == want["new_edges"]["uses_param_scopeParam"]


def test_m3_join_type_closed(booted):
    want = DELTA["M3"]["joinType_closed"]
    got = Counter(n.properties.get("joinType")
                  for n in booted.current_nodes("join"))
    assert dict(got) == want


# ---------------------------------------------------------------
# M4 — derived_column (authored ahead)
# ---------------------------------------------------------------

def test_m4_key_matches_twin(twin):
    want = DELTA["M4"]
    projs = [n for n in twin if n["kind"] == "projection"]
    op = [p for p in projs
          if "operation" in (p["content"].get("derivation") or {})]
    words = [p for p in projs
             if "words" in (p["content"].get("derivation") or {})]
    rest = [p for p in projs if p not in op and p not in words]
    named_lit = [p for p in rest if p["content"].get("output")]
    anon = [p for p in rest if not p["content"].get("output")]
    assert len(op) == want["derived_column_by_derivation"]["operation"]
    assert len(named_lit) \
        == want["derived_column_by_derivation"]["named_literal"]
    assert len(op) + len(named_lit) == want["new_nodes"]["derived_column"]
    assert len(words) == want["not_derived_columns"]["passthrough_projections"]
    assert len(anon) == want["not_derived_columns"]["anonymous_exists_select"]

    cites = set()
    for r in (n for n in twin if n["kind"] == "reference"):
        if "/projection/" in r["points_at"]:
            head = r["points_at"].split("/projection/")[0]
            for c in _columns(r.get("draws_from") or []):
                cites.add((head, c))
    assert len(cites) == want["new_edges"]["cites_scopeColumn"]


# ---------------------------------------------------------------
# M5 — statement + the M3 holdovers (authored ahead)
# ---------------------------------------------------------------

def test_m5_key_matches_twin(twin):
    want = DELTA["M5"]
    sts = [n for n in twin if n["kind"] == "statement"]
    assert len(sts) == want["new_nodes"]["statement"]
    assert sum(1 for s in sts if s.get("subkind") == "operational") \
        == want["statement_operational_subkind"]

    conds = [n for n in twin if n["kind"] == "condition"]
    cpaths = {c["points_at"] for c in conds}
    st = [c for c in conds if not _in_scope(c["points_at"])]
    roots = [c for c in st
             if not any(c["points_at"].startswith(q + "/") for q in cpaths)]
    assert len(roots) == want["new_edges"]["has_part_statementCondition"]
    assert len(st) - len(roots) \
        == want["new_edges"]["has_part_conditionCondition"]

    # counted-missing debt: statements with no downward edge until M6
    idx = sorted({int(m.group(1)) for n in twin
                  for m in [re.match(r"^/statements/(\d+)", n["points_at"])]
                  if m})
    has_scope = {i for i in idx if any(
        n["points_at"].startswith(f"/statements/{i}/scope")
        or n["points_at"].startswith(f"/statements/{i}/ctes")
        for n in twin)}
    has_cond = {i for i in idx if any(
        c["points_at"].startswith(f"/statements/{i}/predicate")
        for c in conds)}
    floaters = [i for i in idx if i not in has_scope and i not in has_cond]
    assert len(floaters) == 31  # the declared Connection_Ledger debt
    assert want["new_edges"]["has_part_statementScope"] == 44


# ---------------------------------------------------------------
# M6/M7 — file + governance (authored ahead; store-checkable)
# ---------------------------------------------------------------

def test_m6_m7_key_matches_store(booted):
    assert len(booted.current_nodes("file")) == 1
    want = DELTA["M7"]
    for label, n in want["new_nodes"].items():
        assert len(booted.current_nodes(label)) == n, label
    rpt = booted.current_nodes("pbi_report")[0]
    executes = rpt.properties["executes"]
    if not isinstance(executes, list):
        executes = json.loads(executes.replace("'", '"'))
    resolved = [e for e in executes if e.startswith("repo://")]
    unresolved = [e for e in executes if not e.startswith("repo://")]
    assert len(resolved) == want["new_edges"]["executes"]
    assert unresolved == want["checks"]["executes_counted_unresolved"]
