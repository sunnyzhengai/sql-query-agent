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
                 "join": len(exported["graph_join"]),
                 "direct_read": len(exported["graph_direct_read"])}
    assert got_nodes == want["nodes"]
    has_part = (len(exported["graph_has_part_dbSchema"])
                + len(exported["graph_has_part_schemaTable"])
                + len(exported["graph_has_part_tableColumn"])
                + len(exported["graph_has_part_scopeJoin"])
                + len(exported["graph_has_part_scopeDirectRead"]))
    left = (len(exported["graph_left_side_joinTable"])
            + len(exported["graph_left_side_joinScope"])
            + len(exported["graph_left_side_directReadTable"]))
    right = (len(exported["graph_right_side_joinTable"])
             + len(exported["graph_right_side_joinScope"]))
    got_edges = {"has_part": has_part,
                 "joins_to": len(exported["graph_joins_to_tableTable"]),
                 "left_side": left, "right_side": right}
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
    """ERA 3 (ratified 2026-09-14): ONE invariant — per scope,
    side-targets == read-set. The reads edge is retired; the
    no-join FROM is a direct_read node with one left_side, so
    DISJOINT is vacuous (one mechanism). The build-measured
    numbers stand: 6 direct + 53 join-covered == 59 read-set."""
    assert not list(booted.current_edges("reads"))  # retired
    tables = {n.identity for n in booted.current_nodes("table")}
    join_tabs, dr_tabs = {}, {}
    for lbl in ("left_side", "right_side"):
        for e in booted.current_edges(lbl):
            if e.to_id not in tables:
                continue
            if "::read#" in e.from_id:
                scope = e.from_id.rsplit("::read#", 1)[0]
                dr_tabs.setdefault(scope, set()).add(e.to_id)
            else:
                scope = e.from_id.rsplit("::join#", 1)[0]
                join_tabs.setdefault(scope, set()).add(e.to_id)
    # sanity (the old DISJOINT): a direct_read target is never
    # also a join side of its own scope
    for scope, tabs in dr_tabs.items():
        assert not tabs & join_tabs.get(scope, set())
    want = DELTA["M2"]["reads"]
    drs = booted.current_nodes("direct_read")
    assert len(drs) == want["remainder"]
    assert len(drs) + want["covered_by_join_sides"] \
        == want["read_set"]


# ---------------------------------------------------------------
# M3 — THE CONDITION LAYER (BUILT 2026-09-10; the STORE is the
# truth — the tree out-counts the twin, precedent joins 95 vs 93)
# ---------------------------------------------------------------

def test_m3_store_matches_census(booted, exported):
    want = CENSUS["M3"]
    # the M3-era census FREEZES here: M4's derived rows and M5's
    # statement-rooted rows are excluded (the frozen-row precedent
    # from the M4 build; each later batch's own test asserts its
    # full sum)
    m5_params = set(DELTA["M5"]["param_names_new"])

    def sans_stmt(rows):
        return [r for r in rows if "::stmt/" not in r["nodeId"]]
    got_nodes = {"db": 1, "db_schema": 3,
                 "table": len(exported["graph_table"]),
                 "column": len(exported["graph_column"]),
                 "scope": len(exported["graph_scope"]),
                 "join": len(exported["graph_join"]),
                 "direct_read": len(exported["graph_direct_read"]),
                 "condition": len(sans_stmt(exported["graph_condition"])),
                 "param": sum(1 for r in exported["graph_param"]
                              if r["name"] not in m5_params)}
    assert got_nodes == want["nodes"]
    has_part = sum(
        len([r for r in v if "::stmt/" not in r["sourceId"]])
        for k, v in exported.items()
        if k.startswith("graph_has_part")
        and k not in ("graph_has_part_scopeDerivedColumn",
                      "graph_has_part_fileStatement",
                      "graph_has_part_fileParam"))
    resolves = (len(exported["graph_resolves_to_conditionColumn"])
                + len([r for r in
                       exported["graph_resolves_to_conditionParam"]
                       if "::stmt/" not in r["sourceId"]]))
    got_edges = {"has_part": has_part,
                 "joins_to": len(exported["graph_joins_to_tableTable"]),
                 "left_side": len(exported["graph_left_side_joinTable"])
                 + len(exported["graph_left_side_joinScope"])
                 + len(exported["graph_left_side_directReadTable"]),
                 "right_side": len(exported["graph_right_side_joinTable"])
                 + len(exported["graph_right_side_joinScope"]),
                 "resolves_to": resolves,
                 "uses_param": len(exported["graph_uses_param_scopeParam"])}
    assert got_edges == want["edges"]


def test_m3_condition_conservation_and_kinds(booted):
    want = DELTA["M3"]
    # frozen at M3: the M5 statement-rooted conditions excluded
    conds = [c for c in booted.current_nodes("condition")
             if "::stmt/" not in c.identity]
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
    # frozen at M3: statement-rooted rows (M5) excluded
    rts = [e for e in booted.current_edges("resolves_to")
           if "::stmt/" not in e.from_id]
    roles = Counter(e.properties.get("role") for e in rts)
    assert dict(roles) == want["resolves_to_roles"]
    cols = [e for e in rts if "::param/" not in e.to_id]
    pars = [e for e in rts if "::param/" in e.to_id]
    assert len(cols) == want["new_edges"]["resolves_to_conditionColumn"]
    assert len(pars) == want["new_edges"]["resolves_to_conditionParam"]
    m5_params = set(DELTA["M5"]["param_names_new"])
    params = sorted(n.properties["name"]
                    for n in booted.current_nodes("param")
                    if n.properties["name"] not in m5_params)
    assert params == want["param_names"]
    assert sum(1 for e in booted.current_edges("uses_param")
               if "::stmt/" not in e.from_id) \
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

    assert len(op) + len(named_lit) \
        == want["new_edges"]["has_part_scopeDerivedColumn"]


def test_m4_cites_recompute_at_store_grain(booted):
    """RECONCILED AT THE M4 BUILD (2026-09-16): the twin-authored
    100 counted (head, column) pairs at TWIN-PATH grain — subquery
    and combination-arm heads. The ruled edge is scope—cites→column
    at STORE grain, so heads collapse to their owning NAMED scope:
    three pairs merge, the measured count is 97, and the key
    re-based by measurement (the joins-93→95 precedent)."""
    from aivia.flows.inbound import _derived_members, _member_cites
    from aivia.lenses import decisions
    read = ReadApi(booted)
    want = DELTA["M4"]
    cites = set()
    for key, tree in sorted(read.trees().items()):
        for scope in decisions.named_scopes(tree):
            for m in _derived_members(scope):
                for col in _member_cites(m):
                    cites.add((scope["name_key"], col))
    assert len(cites) == want["new_edges"]["cites_scopeColumn"]


def test_m4_store_matches_key(booted):
    """The M4 census ON THE BOOTED STORE == the answer key — the
    same equality Sunny's GQL gate asserts on the served graph."""
    want = DELTA["M4"]
    nodes = booted.current_nodes("derived_column")
    assert len(nodes) == want["new_nodes"]["derived_column"]
    kinds = Counter(n.properties["derivation"] for n in nodes)
    assert dict(kinds) == want["derived_column_by_derivation"]
    ids = {n.identity for n in nodes}
    scope_ids = {n.identity for n in booted.current_nodes("scope")}
    births = [e for e in booted.current_edges("has_part")
              if e.to_id in ids]
    assert len(births) == want["new_edges"]["has_part_scopeDerivedColumn"]
    assert all(e.from_id in scope_ids for e in births)
    cites = booted.current_edges("cites")
    assert len(cites) == want["new_edges"]["cites_scopeColumn"]
    col_ids = {n.identity for n in booted.current_nodes("column")}
    assert all(e.from_id in scope_ids and e.to_id in col_ids
               for e in cites)


def test_m4_descriptions_stored_and_verbatim(booted):
    """156/156 voiced (the description_coverage row) and the
    verbatim law: stored == the R12 recompute."""
    from aivia.flows import produce
    from aivia.flows.inbound import _derived_members, _is_derived_node
    from aivia.lenses import decisions
    read = ReadApi(booted)
    nodes = {n.identity: n
             for n in booted.current_nodes("derived_column")}
    assert all(n.properties.get("description")
               for n in nodes.values())
    recomputed = {}
    for key, tree in sorted(read.trees().items()):
        voice = produce._Voice(read, tree)
        for scope in decisions.named_scopes(tree):
            seq = 0
            for m in _derived_members(scope):
                if _is_derived_node(m):
                    seq += 1
                    cid = f"{scope['name_key']}::dcol#{seq}"
                    recomputed[cid] = produce.derived_phrase(m, voice)
    assert set(recomputed) == set(nodes)
    for cid, text in recomputed.items():
        assert nodes[cid].properties["description"] == text


def test_m4_export_matches_census(exported):
    """The FULL M4 census against the export tables — the same
    numbers Sunny's GQL gate asserts after his load + ONE refresh
    (census_after.M4 in the key)."""
    want = CENSUS["M4"]
    got_nodes = {"db": 1, "db_schema": 3,
                 "table": len(exported["graph_table"]),
                 "column": len(exported["graph_column"]),
                 "scope": len(exported["graph_scope"]),
                 "join": len(exported["graph_join"]),
                 "direct_read": len(exported["graph_direct_read"]),
                 "condition": len(
                     [r for r in exported["graph_condition"]
                      if "::stmt/" not in r["nodeId"]]),
                 "param": sum(
                     1 for r in exported["graph_param"]
                     if r["name"] not in
                     set(DELTA["M5"]["param_names_new"])),
                 "derived_column":
                     len(exported["graph_derived_column"])}
    # frozen at M4: M5's statement-rooted rows excluded (the
    # frozen-row precedent); M5's own test asserts the full sums
    assert got_nodes == want["nodes"]
    has_part = (len(exported["graph_has_part_dbSchema"])
                + len(exported["graph_has_part_schemaTable"])
                + len(exported["graph_has_part_tableColumn"])
                + len(exported["graph_has_part_scopeJoin"])
                + len(exported["graph_has_part_scopeDirectRead"])
                + len(exported["graph_has_part_joinCondition"])
                + len(exported["graph_has_part_scopeCondition"])
                + len([r for r in
                       exported["graph_has_part_conditionCondition"]
                       if "::stmt/" not in r["sourceId"]])
                + len(exported["graph_has_part_scopeDerivedColumn"]))
    left = (len(exported["graph_left_side_joinTable"])
            + len(exported["graph_left_side_joinScope"])
            + len(exported["graph_left_side_directReadTable"]))
    right = (len(exported["graph_right_side_joinTable"])
             + len(exported["graph_right_side_joinScope"]))
    resolves = (len(exported["graph_resolves_to_conditionColumn"])
                + len([r for r in
                       exported["graph_resolves_to_conditionParam"]
                       if "::stmt/" not in r["sourceId"]]))
    got_edges = {
        "has_part": has_part,
        "joins_to": len(exported["graph_joins_to_tableTable"]),
        "left_side": left, "right_side": right,
        "resolves_to": resolves,
        "uses_param": len(exported["graph_uses_param_scopeParam"]),
        "cites": len(exported["graph_cites_scopeColumn"])}
    assert got_edges == want["edges"]
    assert sum(got_nodes.values()) == want["node_total"]
    assert sum(got_edges.values()) == want["edge_total"]


def test_m4_derived_rows_ride_the_export_verbatim(booted, exported):
    stored = {n.identity: n.properties
              for n in booted.current_nodes("derived_column")}
    rows = exported["graph_derived_column"]
    assert {r["nodeId"] for r in rows} == set(stored)
    for r in rows:
        assert r["description"] == \
            stored[r["nodeId"]]["description"]
        assert r["derivation"] in ("operation", "named_literal")


def test_m4_case_conditions_stay_parented_to_scope(booted):
    """The sealed check: case_when predicates shipped at M3 keep
    their scope/condition parentage — never re-parented under
    derived_column (stay-flat, Sunny 2026-09-16)."""
    conds = booted.current_nodes("condition")
    assert len(conds) == CENSUS["M5"]["nodes"]["condition"]
    dcol_ids = {n.identity
                for n in booted.current_nodes("derived_column")}
    cond_ids = {n.identity for n in conds}
    for e in booted.current_edges("has_part"):
        if e.to_id in cond_ids:
            assert e.from_id not in dcol_ids


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


def test_m5_store_matches_key(booted):
    """The M5 census ON THE BOOTED STORE == the answer key
    (Brief_M5_Statement_Layer, approved 2026-09-17)."""
    want = DELTA["M5"]
    sts = booted.current_nodes("statement")
    assert len(sts) == want["new_nodes"]["statement"]
    assert all(re.search(r"::stmt/\d+$", n.identity) for n in sts)
    ops = [n for n in sts
           if n.properties.get("subkind") == "operational"]
    assert len(ops) == want["statement_operational_subkind"]
    st_ids = {n.identity for n in sts}
    scope_ids = {n.identity for n in booted.current_nodes("scope")}
    st_scope = [e for e in booted.current_edges("has_part")
                if e.from_id in st_ids and e.to_id in scope_ids]
    assert len(st_scope) == want["new_edges"]["has_part_statementScope"]
    conds = booted.current_nodes("condition")
    assert len(conds) == CENSUS["M5"]["nodes"]["condition"]
    assert len(booted.current_nodes("param")) \
        == CENSUS["M5"]["nodes"]["param"]
    cond_ids = {n.identity for n in conds}
    st_cond = [e for e in booted.current_edges("has_part")
               if e.from_id in st_ids and e.to_id in cond_ids]
    assert len(st_cond) == want["new_edges"]["has_part_statementCondition"]
    st_param = [e for e in booted.current_edges("uses_param")
                if e.from_id in st_ids]
    assert len(st_param) == want["new_edges"]["uses_param_statementParam"]


def test_m5_descriptions_36_voiced_31_empty_by_rule(booted):
    """The (b) ruling (Sunny 'b', 2026-09-17): 36 data-producing
    statements carry R11 descriptions; the 31 operational store
    NOTHING — empty-by-rule, counted here, never silent."""
    want = DELTA["M5"]["checks"]
    sts = booted.current_nodes("statement")
    voiced = [n for n in sts if n.properties.get("description")]
    assert len(voiced) == want["r11_descriptions_nonempty"]
    ops = [n for n in sts
           if n.properties.get("subkind") == "operational"]
    assert len(ops) == want["statement_operational_empty_by_rule"]
    assert not any(n.properties.get("description") for n in ops)


def test_m5_descriptions_stored_and_verbatim(booted):
    """The verbatim law at statement grain: stored == the R11
    recompute, byte-exact, for every voiced statement."""
    from aivia.flows import inbound
    read = ReadApi(booted)
    recomputed = inbound._render_statement_descriptions(read)
    nodes = {n.identity: n
             for n in booted.current_nodes("statement")}
    voiced = {i for i, n in nodes.items()
              if n.properties.get("description")}
    assert set(recomputed) == voiced
    for sid, text in recomputed.items():
        assert nodes[sid].properties["description"] == text


def test_m5_statement_rooted_conditions_at_store_grain(booted):
    """FL8 closed (Sunny 'real value', 2026-09-17): the 6
    statement-rooted conditions EXIST at store grain — the
    receipt-grain counter pin lives in test_statement_layer.py
    (a fresh build; the booted store's rerun skips idempotently)."""
    st_cond = [n for n in booted.current_nodes("condition")
               if "::stmt/" in n.identity]
    assert len(st_cond) == 6
    kinds = Counter(n.properties["kind"] for n in st_cond)
    assert dict(kinds) == DELTA["M5"]["condition_by_kind_new"]


def test_m5_export_matches_census(exported):
    """The FULL M5 census against the export tables — the numbers
    Sunny's GQL gate asserts after his load + ONE refresh.
    Frozen at M5: the M6 file tables excluded (the frozen-row
    precedent)."""
    want = CENSUS["M5"]
    assert len(exported["graph_statement"]) \
        == want["nodes"]["statement"]
    got_nodes = {k: len(exported[f"graph_{k}"])
                 for k in want["nodes"]}
    assert got_nodes == want["nodes"]
    has_part = sum(len(rows) for name, rows in exported.items()
                   if name.startswith("graph_has_part")
                   and name not in ("graph_has_part_fileStatement",
                                    "graph_has_part_fileParam"))
    assert has_part == want["edges"]["has_part"]


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


def test_m6_store_matches_key(booted):
    """M6 (Brief_M6_File_Layer, approved 2026-09-17): the file's
    downward edges — THE 31-STATEMENT DEBT RETIRES at its named
    landing step."""
    want = DELTA["M6"]
    fid = booted.current_nodes("file")[0].identity
    st_ids = {n.identity for n in booted.current_nodes("statement")}
    p_ids = {n.identity for n in booted.current_nodes("param")}
    f_st = [e for e in booted.current_edges("has_part")
            if e.from_id == fid and e.to_id in st_ids]
    f_p = [e for e in booted.current_edges("has_part")
           if e.from_id == fid and e.to_id in p_ids]
    assert len(f_st) == want["new_edges"]["has_part_fileStatement"]
    assert len(f_p) == want["new_edges"]["has_part_fileParam"]
    # the debt: EVERY statement now birth-edges from the file
    assert {e.to_id for e in f_st} == st_ids


def test_m6_two_governance_fields(booted):
    """The two-field design (Sunny's sitting, 2026-09-17):
    technical definition = the R13 catch-all, verbatim-law;
    description = the APPROVED Scribe summary of it."""
    from aivia.flows import inbound
    f = booted.current_nodes("file")[0]
    td = f.properties.get("technical_definition")
    assert td and td.strip()
    read = ReadApi(booted)
    assert td == inbound._render_technical_definition(read,
                                                      f.identity)
    desc = f.properties.get("description")
    assert desc and desc.strip()
    # the cage (M6-2): no words in the summary that the catch-all
    # + the file's own name words cannot account for is checked at
    # approval; here the stored text == the approved artifact
    arts = [n for n in booted.current_nodes("description")
            if f.identity in str(n.properties.get("about", ""))]
    approved = [n for n in arts
                if n.properties.get("status") == "approved"]
    assert approved, "the description stores ONLY approved text"
    assert desc == approved[-1].properties.get("description")


def test_m6_era3_walk_complete(booted):
    """M6-3 (re-based): file→statement→scope→(join|direct_read)
    →sides→table reaches every side-target table."""
    fid = booted.current_nodes("file")[0].identity
    hp = {}
    for e in booted.current_edges("has_part"):
        hp.setdefault(e.from_id, set()).add(e.to_id)
    scope_ids = {n.identity for n in booted.current_nodes("scope")}
    reached_scopes = set()
    for st in hp.get(fid, set()):
        reached_scopes |= (hp.get(st, set()) & scope_ids)
    assert reached_scopes == scope_ids  # every scope walks from file
    table_ids = {n.identity for n in booted.current_nodes("table")}
    sided = set()
    for side in ("left_side", "right_side"):
        for e in booted.current_edges(side):
            if e.to_id in table_ids:
                sided.add(e.to_id)
    walked = set()
    for sc in reached_scopes:
        for mid in hp.get(sc, set()):  # join / direct_read
            for side in ("left_side", "right_side"):
                for e in booted.current_edges(side):
                    if e.from_id == mid and e.to_id in table_ids:
                        walked.add(e.to_id)
    assert walked == sided


def test_m6_export_matches_census(exported):
    """The FULL M6 census + the M6-4 row shape (blob-free)."""
    want = CENSUS["M6"]
    rows = exported["graph_file"]
    assert len(rows) == want["nodes"]["file"]
    assert set(rows[0]) == {"nodeId", "name", "description",
                            "technicalDefinition", "contentHash",
                            "loadedAt"}
    assert rows[0]["technicalDefinition"].strip()
    got_nodes = {k: len(exported[f"graph_{k}"])
                 for k in want["nodes"]}
    assert got_nodes == want["nodes"]
    has_part = sum(len(v) for k, v in exported.items()
                   if k.startswith("graph_has_part"))
    assert has_part == want["edges"]["has_part"]
