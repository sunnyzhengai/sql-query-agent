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
# M2 — THE JOIN LAYER (authored ahead; joins testable alone)
# ---------------------------------------------------------------

def test_m2_joins_key_matches_twin(twin, booted):
    want = DELTA["M2"]
    refs = [n for n in twin if n["kind"] == "reference"]
    joins = _join_containers(twin)
    assert len(joins) == want["new_nodes"]["join"]
    assert len(joins) == want["new_edges"]["has_part_scopeJoin"]
    assert len(joins) == want["new_edges"]["left_side"]
    assert len(joins) == want["new_edges"]["right_side"]
    assert all(_in_scope(j) for j in joins)

    pair_tables = {}
    for j in joins:
        ts = set()
        for r in refs:
            if r["points_at"].startswith(j + "/") or r["points_at"] == j:
                for c in _columns(r.get("draws_from") or []):
                    ts.add(c.rsplit("|", 1)[0])
        pair_tables[j] = ts
    sizes = {"both_tables": 0, "one_table": 0, "no_table_scope_sided": 0}
    for ts in pair_tables.values():
        sizes[{2: "both_tables", 1: "one_table",
               0: "no_table_scope_sided"}[len(ts)]] += 1
    assert sizes == want["join_table_set_sizes"]
    assert sizes["both_tables"] * 2 + sizes["one_table"] \
        == want["side_targets"]["table"]
    assert len(joins) * 2 - want["side_targets"]["table"] \
        == want["side_targets"]["scope"]

    # THE DRIFT QUERY at parse level — needs joins + joins_to only,
    # no condition nodes (why joins are testable alone)
    declared = set()
    for e in booted.current_edges("joins_to"):
        declared.add((e.from_id, e.to_id))
        declared.add((e.to_id, e.from_id))
    pairs = {tuple(sorted(ts)) for ts in pair_tables.values()
             if len(ts) == 2}
    findings = sorted(p for p in pairs if p not in declared)
    assert findings == [tuple(f) for f in
                        want["checks"]["drift_findings_exact"]]


# ---------------------------------------------------------------
# M3 — THE CONDITION LAYER (authored ahead; testable alone)
# ---------------------------------------------------------------

def test_m3_conditions_key_matches_twin(twin):
    want = DELTA["M3"]
    conds = [n for n in twin if n["kind"] == "condition"]
    refs = [n for n in twin if n["kind"] == "reference"]
    sc = [c for c in conds if _in_scope(c["points_at"])]
    st = [c for c in conds if not _in_scope(c["points_at"])]
    assert len(sc) == want["new_nodes"]["condition"]
    assert len(st) == DELTA["M5"]["new_nodes"]["condition"]

    def clause_of(p):
        if "/join_on/" in p:
            return "join_on"
        if "/when" in p or "/else" in p:
            return "case_when"
        return "where"
    assert dict(Counter(clause_of(c["points_at"]) for c in sc)) \
        == want["condition_by_clause"]
    assert sum(1 for c in conds if c.get("subkind") == "degenerate") \
        == want["condition_degenerate_subkind"]

    def kind_of(c):
        return c["content"].get("predicate") or c["content"].get("shape")
    assert dict(Counter(kind_of(c) for c in sc)) == want["condition_by_kind"]
    assert dict(Counter(kind_of(c) for c in st)) \
        == DELTA["M5"]["condition_by_kind_new"]

    # parent split: ON roots parent to their JOIN; where/case roots
    # to their scope; the rest nest under conditions
    cpaths = {c["points_at"] for c in conds}
    containers = set(_join_containers(twin))
    roots = [c for c in sc
             if not any(c["points_at"].startswith(q + "/") for q in cpaths)]
    join_roots = [c for c in roots if c["points_at"] in containers]
    assert len(join_roots) == want["new_edges"]["has_part_joinCondition_roots"]
    assert len(roots) - len(join_roots) \
        == want["new_edges"]["has_part_scopeCondition_roots"]
    assert len(sc) - len(roots) \
        == want["new_edges"]["has_part_conditionCondition"]

    # params by user grain: scope-used ship at M3, statement-only at M5
    grains = {}
    for r in refs:
        p = r.get("content", {}).get("parameter")
        if p:
            grains.setdefault(p, set()).add(
                "scope" if _in_scope(r["points_at"]) else "statement")
    assert sorted(p for p, g in grains.items() if "scope" in g) \
        == want["param_names"]
    assert sorted(p for p, g in grains.items() if "scope" not in g) \
        == DELTA["M5"]["param_names_new"]

    # resolves_to with roles: condition→column and condition→param
    cond_paths = [c["points_at"] for c in conds]
    def owner(p):
        owners = [q for q in cond_paths if p.startswith(q + "/")]
        return max(owners, key=len) if owners else None
    cc, cp, roles = set(), set(), Counter()
    for r in refs:
        o = owner(r["points_at"])
        if not o:
            continue
        for c in _columns(r.get("draws_from") or []):
            if (o, c) not in cc:
                roles[r["points_at"][len(o) + 1:].split("/")[0]] += 1
            cc.add((o, c))
        p = r.get("content", {}).get("parameter")
        if p:
            cp.add((o, p))
    assert len(cc) == want["new_edges"]["resolves_to_conditionColumn"]
    assert all(_in_scope(o) for o, _ in cc)
    assert dict(roles) == want["resolves_to_roles"]
    cp_m3 = {x for x in cp if _in_scope(x[0])}
    assert len(cp_m3) == want["new_edges"]["resolves_to_conditionParam"]
    assert len(cp) - len(cp_m3) \
        == DELTA["M5"]["new_edges"]["resolves_to_conditionParam"]


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
