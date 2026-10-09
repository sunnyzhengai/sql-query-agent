"""Phase 05 contract tests (AIVIA_01_Design/05_semantic_graph_data_contract.md).

Current section: STAGE 1 (L03) — file + statement sheets, contains
edges, exclusion ledger (design decisions 3, 8; contract identity /
evidence / conservation laws; the two L03 refinements: dotted
position paths, the disposition field).

Written test-first: RED until semantic_graph.py exposes
    build(sql_dir, out_dir) -> census dict
writing 05_semantic_graph_file_output.json, 05_semantic_graph_statement_output.json,
05_semantic_graph_contains_edges_output.json, 05_semantic_graph_exclusion_ledger_output.json into out_dir.

Zero API cost — phase 05 is fully deterministic: ScriptDom + plain
Python, no LLM, no embeddings.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
SQL_DIR = REPO_ROOT / "AIVIA_01_Data" / "01_subject_sql_files"
DIR02 = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
DIR05 = REPO_ROOT / "AIVIA_01_Data" / "05_semantic_graph"
KIND_LIBRARY = DIR05 / "05_kind_library.json"

sys.path.insert(0, str(CODE_DIR))
import semantic_graph  # noqa: E402

# THE NAMING LAW (ruled 2026-10-08, step table row 05; approved
# same day): <step>_<content>_output.json, "_sheet" dies, the
# kind library keeps its name (asset, not output). RED until the
# rename lands.
SHEETS = [
    "05_semantic_graph_file_output.json",
    "05_semantic_graph_statement_output.json",
    "05_semantic_graph_scope_output.json",
    "05_semantic_graph_structure_output.json",
    "05_semantic_graph_predicate_output.json",
    "05_semantic_graph_expression_output.json",
    "05_semantic_graph_parameter_output.json",
    "05_semantic_graph_resolves_edges_output.json",
    "05_semantic_graph_discovered_joins_output.json",
    "05_semantic_graph_contains_edges_output.json",
    "05_semantic_graph_exclusion_ledger_output.json",
]

PREDICATE_KINDS = {
    "COMPARE_EQ", "COMPARE_NEQ", "COMPARE_GT", "COMPARE_GTE",
    "COMPARE_LT", "COMPARE_LTE", "PATTERN_MATCH", "IN_LIST",
    "IN_SELECTION", "RANGE", "NULL_CHECK", "EXISTS_SELECTION",
    "QUANTIFIED_COMPARE",
}
EXPRESSION_KINDS = {
    "column_ref", "table_ref", "literal", "parameter_ref", "function",
    "arithmetic", "case", "cast", "unary", "subquery_ref",
}
REQUIRED_ROLES = {  # library Predicate_Kinds "Roles" column
    "COMPARE_EQ": {"subject", "comparand"},
    "COMPARE_NEQ": {"subject", "comparand"},
    "COMPARE_GT": {"subject", "comparand"},
    "COMPARE_GTE": {"subject", "comparand"},
    "COMPARE_LT": {"subject", "comparand"},
    "COMPARE_LTE": {"subject", "comparand"},
    "PATTERN_MATCH": {"subject", "pattern"},
    "IN_LIST": {"subject", "comparand"},
    "IN_SELECTION": {"subject", "selection"},
    "RANGE": {"subject", "lower_bound", "upper_bound"},
    "NULL_CHECK": {"subject"},
    "EXISTS_SELECTION": {"selection"},
    "QUANTIFIED_COMPARE": {"subject", "selection"},
}
BOOLEAN_STRUCTURES = {"AND", "OR", "NOT"}

POPULATION_KINDS = {"SELECT", "SELECT INTO", "INSERT", "UPDATE", "DELETE"}
MAIN_SCOPE_KINDS = {"delivery", "temp_table", "write_target"}


def _prep_out(tmp: Path) -> Path:
    """An output folder holding the ratified kind library (the build
    loads it from there — contract Input File 1)."""
    out = tmp / "05_semantic_graph"
    out.mkdir(parents=True)
    shutil.copy(KIND_LIBRARY, out / "05_kind_library.json")
    return out


def _load(out: Path, name: str):
    return json.loads((out / name).read_text())


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One build over the real 8 files."""
    out = _prep_out(tmp_path_factory.mktemp("real"))
    census = semantic_graph.build(SQL_DIR, out, DIR02)
    return out, census


# ---------------------------------------------------------------- the gate

def test_ratification_gate_refuses_unratified_library(tmp_path):
    out = _prep_out(tmp_path)
    lib_path = out / "05_kind_library.json"
    lib = json.loads(lib_path.read_text())
    lib["status"] = "PORTED 2026-10-01; AWAITING SUNNY'S RATIFICATION."
    lib_path.write_text(json.dumps(lib))
    with pytest.raises(ValueError, match="05_kind_library.json"):
        semantic_graph.build(SQL_DIR, out, DIR02)


# ------------------------------------------------- the real 8-file estate

def test_all_eight_files_build_with_no_exclusions(built):
    out, _ = built
    files = _load(out, "05_semantic_graph_file_output.json")
    assert len(files) == 8
    assert _load(out, "05_semantic_graph_exclusion_ledger_output.json") == []


def test_conservation_per_file(built):
    out, _ = built
    for row in _load(out, "05_semantic_graph_file_output.json"):
        assert (
            row["statements_handled"]
            + row["statements_operational"]
            + row["statements_gap"]
            + row["remainder_total"]
            == row["statement_total"]
        ), row["file_name"]
        assert row["statement_total"] > 0, row["file_name"]


def test_every_statement_row_carries_evidence(built):
    out, _ = built
    for row in _load(out, "05_semantic_graph_statement_output.json"):
        ev = row["evidence"]
        assert ev["fragment"].strip(), row["node_id"]
        assert ev["line"] >= 1 and ev["column"] >= 1, row["node_id"]


def test_identity_law_ids_deterministic_across_runs(built, tmp_path):
    out1, _ = built
    out2 = _prep_out(tmp_path)
    semantic_graph.build(SQL_DIR, out2, DIR02)
    for name in SHEETS:
        a, b = _load(out1, name), _load(out2, name)
        if name == "05_semantic_graph_file_output.json":  # parsed_at is the ONE
            for row in a + b:             # non-deterministic field
                row.pop("parsed_at")
        assert a == b, name


def test_node_id_shape(built):
    out, _ = built
    file_names = {r["file_name"] for r in _load(out, "05_semantic_graph_file_output.json")}
    for row in _load(out, "05_semantic_graph_statement_output.json"):
        prefix, _, pos = row["node_id"].rpartition("::stmt/")
        assert pos == row["position"], row["node_id"]
        assert prefix.removeprefix("file::") in file_names, row["node_id"]


# ------------------------------------------------- stage 2: the scopes

def test_every_scope_is_owned_and_evidenced(built):
    out, _ = built
    stmt_ids = {r["node_id"] for r in _load(out, "05_semantic_graph_statement_output.json")}
    scopes = _load(out, "05_semantic_graph_scope_output.json")
    assert scopes  # the 8-file corpus is not scope-free
    for s in scopes:
        assert s["owning_statement"] in stmt_ids, s["node_id"]
        assert s["evidence"]["fragment"].strip(), s["node_id"]


def test_population_statements_mint_exactly_one_main_scope(built):
    out, _ = built
    scopes = _load(out, "05_semantic_graph_scope_output.json")
    by_owner = {}
    for s in scopes:
        by_owner.setdefault(s["owning_statement"], []).append(s)
    for row in _load(out, "05_semantic_graph_statement_output.json"):
        owned = by_owner.get(row["node_id"], [])
        mains = [s for s in owned if s["scope_kind"] in MAIN_SCOPE_KINDS]
        if row["statement_kind"] in POPULATION_KINDS:
            assert len(mains) == 1, row["node_id"]
        else:
            assert owned == [], row["node_id"]  # IF/WHILE/SET mint none


# --------------------------------------------- stage 3: the structures

def test_every_structure_owned_and_evidenced(built):
    out, _ = built
    scope_ids = {s["node_id"] for s in _load(out, "05_semantic_graph_scope_output.json")}
    structures = _load(out, "05_semantic_graph_structure_output.json")
    assert structures  # the corpus is not structure-free
    for s in structures:
        assert s["owning_scope"] in scope_ids, s["node_id"]
        assert s["evidence"]["fragment"].strip(), s["node_id"]


def test_select_scopes_have_exactly_one_projection_or_combination(built):
    out, _ = built
    scopes = _load(out, "05_semantic_graph_scope_output.json")
    by_scope = {}
    for s in _load(out, "05_semantic_graph_structure_output.json"):
        by_scope.setdefault(s["owning_scope"], []).append(s)
    arm_parents = {s["node_id"].rsplit("::arm", 1)[0]
                   for s in scopes if s["scope_kind"] == "union_arm"}
    for scope in scopes:
        if scope["operation"] != "select":
            continue
        kinds = [s["structure_kind"]
                 for s in by_scope.get(scope["node_id"], [])]
        if scope["node_id"] in arm_parents:
            assert kinds.count("COMBINATION") == 1, scope["node_id"]
            assert "PROJECTION" not in kinds, scope["node_id"]
        else:
            assert kinds.count("PROJECTION") == 1, scope["node_id"]

def _write_sql(folder: Path, name: str, text: str):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(text)


def test_exclusion_is_counted_never_fatal(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "good.sql", "SELECT 1 AS a;")
    _write_sql(sql, "broken.sql", "SELEC 1 FORM nowhere;;;")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    ledger = _load(out, "05_semantic_graph_exclusion_ledger_output.json")
    assert [r["file_name"] for r in ledger] == ["broken.sql"]
    assert ledger[0]["reasons"]  # the parser's verbatim strings
    assert [r["file_name"] for r in _load(out, "05_semantic_graph_file_output.json")] == ["good"]


def test_remainder_rows_are_visible_not_just_counted(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "odd.sql", "WAITFOR DELAY '00:00:01';")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    rows = _load(out, "05_semantic_graph_statement_output.json")
    assert len(rows) == 1
    row = rows[0]
    assert row["disposition"] == "remainder"
    assert row["statement_kind"] == row["scriptdom_type"]  # repeats it
    files = _load(out, "05_semantic_graph_file_output.json")
    assert files[0]["remainder_total"] == 1


def test_dynamic_sql_is_a_named_gap_never_naked(tmp_path):
    """Decision 9: EXEC of a STRING is the dynamic_sql gap class;
    a procedure-call EXEC is NOT — it stays visibly in the remainder
    until its own ruling."""
    sql = tmp_path / "sql"
    _write_sql(sql, "dyn.sql", "EXEC ('SELECT 1 AS a');")
    _write_sql(sql, "call.sql", "EXEC dbo.SomeProc;")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    rows = {r["node_id"]: r for r in _load(out, "05_semantic_graph_statement_output.json")}
    dyn = rows["file::dyn::stmt/1"]
    assert dyn["disposition"] == "gap"
    assert dyn["gap_class"] == "dynamic_sql"
    call = rows["file::call::stmt/1"]
    assert call["disposition"] == "remainder"
    assert call["gap_class"] is None
    files = {r["file_name"]: r for r in _load(out, "05_semantic_graph_file_output.json")}
    assert files["dyn"]["statements_gap"] == 1
    assert files["call"]["remainder_total"] == 1


# --------------------------------------------- stage 5: resolution

RESOLUTION_CLASSES = {
    "unknown_table", "unknown_column", "blocked_by_unknown_table",
    "ambiguous_column", "wildcard", "table_function",
    "scope_column_missing", "value_code_unknown", "unknown_parameter",
}
RESOLVED_TO_KINDS = {"table", "column", "value", "scope", "member",
                     "parameter", "declared_join"}


@pytest.fixture(scope="module")
def built5(tmp_path_factory):
    """One stage-5 build over the real 8 files + the real dictionary."""
    out = _prep_out(tmp_path_factory.mktemp("real5"))
    census = semantic_graph.build(SQL_DIR, out, DIR02)
    return out, census


def _mini_dict(tmp: Path) -> Path:
    """A controlled dictionary: T1/T2/ZC_CAT; one single-pair declared
    join (J1), one TWO-ordinal join (J2 — the real dictionary has no
    multi-pair joins, so partial coverage needs this fixture), one
    value route (J3); ZC_CAT value rows + T2 as a direct value table
    (PK = ID)."""
    d = tmp / "mini_dict"
    d.mkdir()

    def col(tab, name, pk=False):
        return {"table_name": tab, "column_name": name,
                "schema_name": "dbo", "is_primary_key": "Y" if pk
                else "N"}

    cols = [col("T1", "ID", pk=True), col("T1", "A"), col("T1", "B"),
            col("T1", "NAME"), col("T1", "CAT_C"),
            col("T2", "ID", pk=True), col("T2", "NAME"),
            col("T2", "K1"), col("T2", "K2"),
            col("ZC_CAT", "CAT_C", pk=True), col("ZC_CAT", "NAME")]

    def jrow(jid, ordinal, st, sc, dt, dc):
        return {"join_id": jid, "ordinal": ordinal,
                "source_table_name": st, "source_column_name": sc,
                "destin_table_name": dt, "destin_column_name": dc}

    joins = [jrow("J1", 1, "T1", "ID", "T2", "ID"),
             jrow("J2", 1, "T1", "A", "T2", "K1"),
             jrow("J2", 2, "T1", "B", "T2", "K2"),
             jrow("J3", 1, "T1", "CAT_C", "ZC_CAT", "CAT_C")]
    vals = [{"table_name": "ZC_CAT", "code": "7", "meaning": "Lucky"},
            {"table_name": "T2", "code": "5", "meaning": "Five"}]
    (d / "02_emr_data_dictionary_extraction_column.json").write_text(
        json.dumps(cols))
    (d / "02_emr_data_dictionary_extraction_join.json").write_text(
        json.dumps(joins))
    (d / "02_emr_data_dictionary_extraction_value.json").write_text(
        json.dumps(vals))
    return d


def _build5(tmp_path, sql_texts: dict):
    sql = tmp_path / "sql"
    for name, text in sql_texts.items():
        _write_sql(sql, name, text)
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, _mini_dict(tmp_path))
    return out


def _resolves(out, **filters):
    rows = _load(out, "05_semantic_graph_resolves_edges_output.json")
    for k, v in filters.items():
        rows = [r for r in rows if r.get(k) == v]
    return rows


def test_resolution_conservation_and_closed_classes(built5):
    out, _ = built5
    rows = _load(out, "05_semantic_graph_resolves_edges_output.json")
    assert rows
    by_from = {}
    for r in rows:
        assert (r["to_kind"] in RESOLVED_TO_KINDS
                or (r["to_kind"] == "unresolved"
                    and r["class"] in RESOLUTION_CLASSES)), r
        by_from.setdefault(r["from_id"], []).append(r)
    # every reference expression gets EXACTLY one BINDING (D3 as
    # reopened 2026-10-02): one row — or a star_member fan, N rows
    # one per origin (same from_id) plus at most one behind_star
    # remainder for a blind arm
    ref_exprs = [e for e in _load(out, "05_semantic_graph_expression_output.json")
                 if e["expression_kind"] in ("column_ref", "table_ref",
                                             "parameter_ref")]
    for e in ref_exprs:
        grp = by_from.get(e["node_id"], [])
        if len(grp) == 1:
            continue
        bases = [r.get("match_basis") for r in grp]
        assert (grp
                and all(b in ("star_member", "behind_star")
                        for b in bases)
                and bases.count("star_member") >= 1
                and bases.count("behind_star") <= 1), e["node_id"]
    # every qualified JOIN: a declared binding or a discovered row
    joins = [s for s in _load(out, "05_semantic_graph_structure_output.json")
             if s["structure_kind"] == "JOIN"
             and s["join_type"] not in ("comma", "Cross")]
    bound = {r["from_id"] for r in rows
             if r["to_kind"] == "declared_join"}
    discovered = _load(out, "05_semantic_graph_discovered_joins_output.json")
    assert len(joins) == len(bound) + len(discovered)


def test_unknown_table_queue_and_cascade(tmp_path):
    """D2's queue + cascade, on a fabricated estate. (Originally
    pinned the corpus's CR_STAT_EXECUTION gap; Sunny's supplemental
    entry cleared it 2026-10-02 — the corpus queue is now EMPTY,
    which test_corpus_queue_is_empty pins instead.)"""
    out = _build5(tmp_path, {"uq.sql":
                  "SELECT g.A, g.B FROM GHOST_TABLE g "
                  "WHERE g.A = 1;"})
    unknown = [r for r in _resolves(out, to_kind="unresolved")
               if r["class"] == "unknown_table"]
    assert len(unknown) == 1
    assert "GHOST_TABLE" in unknown[0]["ref_text"].upper()
    blocked = [r for r in _resolves(out, to_kind="unresolved")
               if r["class"] == "blocked_by_unknown_table"]
    assert len(blocked) == 3  # g.A (twice) and g.B inherit the cause


def test_corpus_queue_is_empty(built5):
    """The gap-first gate's clearance, pinned: after the 2026-10-02
    supplemental entry, the corpus has NO unknown tables and NO
    blocked columns."""
    out, _ = built5
    classes = {r["class"] for r in _resolves(out, to_kind="unresolved")}
    assert "unknown_table" not in classes
    assert "blocked_by_unknown_table" not in classes


def test_corpus_binds_to_the_dictionary(built5):
    out, _ = built5
    tables = _resolves(out, to_kind="table")
    assert any(r["to_id"] == "V_REPORT_RUN_FACT" for r in tables)
    assert _resolves(out, to_kind="column")  # plenty must bind
    stars = [r for r in _resolves(out, to_kind="unresolved")
             if r["class"] == "wildcard"]
    star_refs = [e for e in _load(out, "05_semantic_graph_expression_output.json")
                 if e["expression_kind"] == "column_ref"
                 and e["ref"] == "*"]
    assert len(stars) == len(star_refs)


def test_corpus_reads_through_scopes(built5):
    out, _ = built5
    assert _resolves(out, to_kind="scope")  # FROM #temp binds to minters
    # D3 as reopened 2026-10-02: every corpus star sits over a scope
    # with explicit outputs, so NO read stays behind_star; the 67
    # former blind reads expand — 59 #combined_census reads gain BOTH
    # arm origins (#census_monthly + #clinic_monthly), 8 #coverage
    # reads gain matching_coverages' = 126 star_member rows
    # (prediction red-first; a deviation at build = investigate, then
    # re-base by measurement with the finding recorded)
    star_members = [r for r in _resolves(out, to_kind="member")
                    if r.get("match_basis") == "star_member"]
    assert len(star_members) == 126
    assert not any(r.get("match_basis") == "behind_star"
                   for r in _resolves(out, to_kind="scope"))


def test_name_law_qualifiers_fold_and_alias(tmp_path):
    out = _build5(tmp_path, {"nl.sql":
                  "SELECT x.a FROM SomeDb.dbo.t1 AS x WHERE x.a = 1;"})
    trow = _resolves(out, to_kind="table")[0]
    assert trow["to_id"] == "T1"
    assert trow["match_basis"] == "fold"  # t1 vs T1
    crow = [r for r in _resolves(out, to_kind="column")
            if r["to_id"] == "T1.A"]
    assert crow  # the alias walked


def test_ambiguous_column_never_picked(tmp_path):
    out = _build5(tmp_path, {"amb.sql":
                  "SELECT NAME FROM T1, T2;"})
    amb = [r for r in _resolves(out, to_kind="unresolved")
           if r["class"] == "ambiguous_column"]
    assert len(amb) == 1
    assert sorted(amb[0]["candidates"]) == ["T1.NAME", "T2.NAME"]


def test_join_coverage_full_partial_discovered(tmp_path):
    out = _build5(tmp_path, {
        "full.sql": "SELECT T1.A FROM T1 INNER JOIN T2 ON T1.ID = T2.ID;",
        "part.sql": "SELECT T1.A FROM T1 INNER JOIN T2 ON T1.A = T2.K1;",
        "disc.sql": "SELECT T1.A FROM T1 INNER JOIN T2 "
                    "ON T1.NAME = T2.NAME;",
    })
    full = [r for r in _resolves(out, to_kind="declared_join")
            if r["coverage"] == "full"]
    assert [r["to_id"] for r in full] == ["J1"]
    part = [r for r in _resolves(out, to_kind="declared_join")
            if r["coverage"] == "partial"]
    assert [r["to_id"] for r in part] == ["J2"]
    assert part[0]["missing_ordinals"] == [2]
    disc = _load(out, "05_semantic_graph_discovered_joins_output.json")
    assert len(disc) == 1
    assert disc[0]["file_name"] == "disc"


def test_on_class_stamped_by_join_type(tmp_path):
    out = _build5(tmp_path, {
        "inner.sql": "SELECT T1.A FROM T1 INNER JOIN T2 "
                     "ON T1.ID = T2.ID AND T2.NAME = 'x';",
        "outer.sql": "SELECT T1.A FROM T1 LEFT JOIN T2 "
                     "ON T1.ID = T2.ID AND T2.NAME = 'x';",
    })
    preds = {p["node_id"]: p for p in _load(out, "05_semantic_graph_predicate_output.json")}
    by_file = {"inner": [], "outer": []}
    for p in preds.values():
        for f in by_file:
            if p["node_id"].startswith(f"file::{f}"):
                by_file[f].append(p)
    for f, residue_class in (("inner", "population_filter"),
                             ("outer", "lookup_shaping")):
        classes = sorted(p["on_class"] for p in by_file[f])
        assert classes == ["join_pair", residue_class], (f, classes)


def test_value_bridge_routes_miss_and_silence(tmp_path):
    out = _build5(tmp_path, {
        "vb.sql": "SELECT T1.A FROM T1 WHERE T1.CAT_C = 7;",
        "miss.sql": "SELECT T1.A FROM T1 WHERE T1.CAT_C = 99;",
        "direct.sql": "SELECT T2.NAME FROM T2 WHERE T2.ID = 5;",
        "quiet.sql": "SELECT T1.A FROM T1 WHERE T1.A = 1;",
    })
    vals = _resolves(out, to_kind="value")
    assert {r["to_id"] for r in vals} == {"ZC_CAT::7", "T2::5"}
    misses = [r for r in _resolves(out, to_kind="unresolved")
              if r["class"] == "value_code_unknown"]
    assert len(misses) == 1 and "99" in misses[0]["ref_text"]
    # no route -> no attempt: the quiet literal has NO resolves row
    quiet_lits = [e["node_id"]
                  for e in _load(out, "05_semantic_graph_expression_output.json")
                  if e["node_id"].startswith("file::quiet")
                  and e["expression_kind"] == "literal"]
    touched = {r["from_id"] for r in _load(out, "05_semantic_graph_resolves_edges_output.json")}
    assert not (set(quiet_lits) & touched)


def test_member_binding_and_scope_column_missing(tmp_path):
    out = _build5(tmp_path, {"mb.sql":
                  "SELECT T1.A AS out_a INTO #t FROM T1;\n"
                  "SELECT out_a, zz FROM #t;"})
    member = _resolves(out, to_kind="member")
    assert len(member) == 1
    assert member[0]["match_basis"] == "member"
    # the member target is the projection-member expression of #t
    assert member[0]["to_id"].startswith("file::mb::scope/#t::structure/"
                                         "PROJECTION/1::expr/")
    missing = [r for r in _resolves(out, to_kind="unresolved")
               if r["class"] == "scope_column_missing"]
    assert len(missing) == 1 and "zz" in missing[0]["ref_text"]


def test_parameter_sheet_and_resolution(tmp_path):
    out = _build5(tmp_path, {"pp.sql":
                  "CREATE PROCEDURE dbo.pp @Month varchar(10) AS\n"
                  "BEGIN\n"
                  "DECLARE @Local INT = 5;\n"
                  "SELECT T1.A FROM T1 "
                  "WHERE T1.A = @Local AND T1.B = @Ghost "
                  "AND T1.NAME = @Month;\n"
                  "END"})
    params = {p["name"]: p for p in _load(out, "05_semantic_graph_parameter_output.json")}
    assert params["@Month"]["kind"] == "procedure_parameter"
    assert params["@Local"]["kind"] == "local_variable"
    assert params["@Local"]["default_text"].strip() == "5"
    bound = _resolves(out, to_kind="parameter")
    assert {r["to_id"] for r in bound} == {
        "file::pp::param/@Month", "file::pp::param/@Local"}
    ghost = [r for r in _resolves(out, to_kind="unresolved")
             if r["class"] == "unknown_parameter"]
    assert len(ghost) == 1 and "@Ghost" in ghost[0]["ref_text"]


def test_table_function_classed(tmp_path):
    out = _build5(tmp_path, {"tf.sql":
                  "DECLARE @csv VARCHAR(100) = 'a,b';\n"
                  "SELECT value FROM STRING_SPLIT(@csv, ',');"})
    tf = [r for r in _resolves(out, to_kind="unresolved")
          if r["class"] == "table_function"]
    assert len(tf) == 1
    assert "STRING_SPLIT" in tf[0]["ref_text"].upper()


# --------------------------------- stage 4: predicates + expressions

def test_denominator_mirror_is_locked():
    """Every 'mapped' boolean type in the ratified TSQL_Denominator
    has a home in the builder's closed mirror — the red-build law's
    code half."""
    lib = json.loads(KIND_LIBRARY.read_text())
    mapped = {r["ScriptDom type"] for r in lib["sheets"]["TSQL_Denominator"]
              if r["Disposition"] == "mapped"}
    covered = (set(semantic_graph.PREDICATE_TYPE_MIRROR)
               | semantic_graph.BOOLEAN_SHAPE_TYPES)
    assert mapped <= covered, mapped - covered


def test_predicates_and_expressions_owned_kinds_closed(built):
    out, _ = built
    known = set()
    for sheet in ("05_semantic_graph_statement_output.json", "05_semantic_graph_structure_output.json",
                  "05_semantic_graph_predicate_output.json", "05_semantic_graph_expression_output.json"):
        known |= {r["node_id"] for r in _load(out, sheet)}
    preds = _load(out, "05_semantic_graph_predicate_output.json")
    exprs = _load(out, "05_semantic_graph_expression_output.json")
    assert preds and exprs  # the corpus has filters
    for p in preds:
        assert (p["predicate_kind"] in PREDICATE_KINDS
                or p["predicate_kind"].startswith("DEFERRED:")), p
        assert p["node_id"].rsplit("::pred/", 1)[0] in known, p["node_id"]
        assert p["evidence"]["fragment"].strip(), p["node_id"]
    for e in exprs:
        assert e["expression_kind"] in EXPRESSION_KINDS, e
        assert e["node_id"].rsplit("::expr/", 1)[0] in known, e["node_id"]
        assert e["evidence"]["fragment"].strip(), e["node_id"]


def test_predicate_roles_complete_per_kind(built):
    out, _ = built
    roles_by_parent = {}
    for edge in _load(out, "05_semantic_graph_contains_edges_output.json"):
        if edge["role"] and edge["role"] != "condition":
            roles_by_parent.setdefault(edge["from_id"], set()).add(
                edge["role"])
    for p in _load(out, "05_semantic_graph_predicate_output.json"):
        need = REQUIRED_ROLES.get(p["predicate_kind"])
        if need is None:  # DEFERRED rows carry no operand law
            continue
        have = roles_by_parent.get(p["node_id"], set())
        assert need <= have, (p["node_id"], p["predicate_kind"],
                              need - have)


def test_projection_conservation_members_plus_stars(built):
    out, _ = built
    owned = {}
    for e in _load(out, "05_semantic_graph_expression_output.json"):
        owner = e["node_id"].rsplit("::expr/", 1)[0]
        owned[owner] = owned.get(owner, 0) + 1
    for s in _load(out, "05_semantic_graph_structure_output.json"):
        if s["structure_kind"] == "PROJECTION":
            assert (owned.get(s["node_id"], 0) + s["star_total"]
                    == s["member_total"]), s["node_id"]


def test_filter_structures_own_exactly_one_tree_root(built):
    out, _ = built
    structures = {s["node_id"]: s
                  for s in _load(out, "05_semantic_graph_structure_output.json")}
    preds = {p["node_id"] for p in _load(out, "05_semantic_graph_predicate_output.json")}
    roots = {}
    for e in _load(out, "05_semantic_graph_contains_edges_output.json"):
        if e["from_id"] in structures and (
                e["to_id"] in preds
                or structures.get(e["to_id"], {}).get("structure_kind")
                in BOOLEAN_STRUCTURES):
            roots[e["from_id"]] = roots.get(e["from_id"], 0) + 1
    for s in structures.values():
        if s["structure_kind"] in ("WHERE", "HAVING"):
            assert roots.get(s["node_id"], 0) == 1, s["node_id"]
        elif s["structure_kind"] == "JOIN":
            expected = 0 if s["join_type"] in ("comma", "Cross") else 1
            assert roots.get(s["node_id"], 0) == expected, s["node_id"]


def test_boolean_tree_parens_dissolve_negation_folds(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql, "bool.sql",
        "SELECT a FROM T WHERE a = 1 "
        "AND (b <> 2 OR c NOT LIKE 'x%') AND d IS NOT NULL;",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    preds = {p["node_id"]: p for p in _load(out, "05_semantic_graph_predicate_output.json")}
    structures = {s["node_id"]: s
                  for s in _load(out, "05_semantic_graph_structure_output.json")}
    by_kind = {}
    for p in preds.values():
        by_kind.setdefault(p["predicate_kind"], []).append(p)
    assert by_kind["COMPARE_EQ"][0]["negated"] is False
    assert by_kind["COMPARE_NEQ"][0]["negated"] is False
    assert by_kind["PATTERN_MATCH"][0]["negated"] is True   # NOT LIKE
    assert by_kind["NULL_CHECK"][0]["negated"] is True      # IS NOT NULL
    bools = [s for s in structures.values()
             if s["structure_kind"] in BOOLEAN_STRUCTURES]
    kinds = sorted(s["structure_kind"] for s in bools)
    assert kinds == ["AND", "AND", "OR"] or kinds == ["AND", "OR"]
    # the OR group sits under an AND; the parentheses left no node
    or_node = [s for s in bools if s["structure_kind"] == "OR"][0]
    parent = or_node["node_id"].rsplit("::structure/", 1)[0]
    assert structures[parent]["structure_kind"] == "AND"


def test_range_roles_and_parameter_refs(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "rng.sql",
               "SELECT a FROM T WHERE dt BETWEEN @s AND @e;")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    pred = _load(out, "05_semantic_graph_predicate_output.json")[0]
    assert pred["predicate_kind"] == "RANGE"
    exprs = {e["role"]: e for e in _load(out, "05_semantic_graph_expression_output.json")
             if e["node_id"].startswith(pred["node_id"])}
    assert exprs["subject"]["expression_kind"] == "column_ref"
    assert exprs["lower_bound"]["expression_kind"] == "parameter_ref"
    assert exprs["upper_bound"]["expression_kind"] == "parameter_ref"


def test_in_list_comparands_ordered(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "inl.sql",
               "SELECT a FROM T WHERE x IN ('a', 'b', 'c');")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    pred = _load(out, "05_semantic_graph_predicate_output.json")[0]
    assert pred["predicate_kind"] == "IN_LIST"
    members = [e for e in _load(out, "05_semantic_graph_expression_output.json")
               if e["role"] == "comparand"]
    assert [m["raw_text"] for m in members] == ["'a'", "'b'", "'c'"]


def test_exists_subquery_mints_full_scope(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql, "ex.sql",
        "SELECT a FROM T WHERE EXISTS "
        "(SELECT 1 FROM U WHERE U.k = T.k);",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    pred_kinds = {p["predicate_kind"]: p
                  for p in _load(out, "05_semantic_graph_predicate_output.json")}
    assert "EXISTS_SELECTION" in pred_kinds
    assert "COMPARE_EQ" in pred_kinds  # the subquery's own WHERE
    sub = [s for s in _load(out, "05_semantic_graph_scope_output.json")
           if s["scope_kind"] == "subquery"]
    assert [s["node_id"] for s in sub] == ["file::ex::stmt/1::scope/sub1"]
    sub_structs = {s["structure_kind"]
                   for s in _load(out, "05_semantic_graph_structure_output.json")
                   if s["owning_scope"] == sub[0]["node_id"]}
    assert {"PROJECTION", "FROM", "WHERE"} <= sub_structs  # never empty
    sel = [e for e in _load(out, "05_semantic_graph_expression_output.json")
           if e["role"] == "selection"]
    assert sel[0]["expression_kind"] == "subquery_ref"


def test_if_condition_attaches_to_the_statement(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "ifc.sql",
               "IF 1 = 1\nBEGIN\n  SELECT 1 AS a;\nEND")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    preds = _load(out, "05_semantic_graph_predicate_output.json")
    on_stmt = [p for p in preds
               if p["node_id"].startswith("file::ifc::stmt/1::pred/")]
    assert len(on_stmt) == 1
    edge = [e for e in _load(out, "05_semantic_graph_contains_edges_output.json")
            if e["to_id"] == on_stmt[0]["node_id"]][0]
    assert edge["from_id"] == "file::ifc::stmt/1"
    assert edge["role"] == "condition"


def test_case_whens_hold_predicates(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql, "cs.sql",
        "SELECT CASE WHEN a > 1 THEN 'hi' ELSE b END AS c FROM T;",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    case = [e for e in _load(out, "05_semantic_graph_expression_output.json")
            if e["expression_kind"] == "case"][0]
    assert case["output_name"] == "c"
    when = [p for p in _load(out, "05_semantic_graph_predicate_output.json")
            if p["node_id"].startswith(case["node_id"])]
    assert when[0]["predicate_kind"] == "COMPARE_GT"
    children = [e for e in _load(out, "05_semantic_graph_expression_output.json")
                if e["node_id"].startswith(case["node_id"] + "::expr/")]
    kinds = {e["expression_kind"] for e in children}
    assert {"literal", "column_ref"} <= kinds  # THEN 'hi', ELSE b


def test_structure_kinds_properties_and_sibling_numbering(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql, "full.sql",
        "SELECT DISTINCT TOP 5 T1.a, T2.b\n"
        "FROM T1\n"
        "INNER JOIN T2 ON T1.x = T2.x\n"
        "LEFT JOIN T3 ON T2.y = T3.y\n"
        "WHERE T1.a = 1\n"
        "GROUP BY T1.a, T2.b\n"
        "HAVING COUNT(*) > 1\n"
        "ORDER BY T1.a;",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    structures = _load(out, "05_semantic_graph_structure_output.json")
    scope_id = "file::full::scope/delivery"
    assert {s["owning_scope"] for s in structures} == {scope_id}
    by_kind = {}
    for s in structures:
        by_kind.setdefault(s["structure_kind"], []).append(s)
    assert set(by_kind) == {"PROJECTION", "FROM", "JOIN", "WHERE",
                            "GROUP BY", "HAVING", "ORDER BY", "TOP"}
    proj = by_kind["PROJECTION"][0]
    assert proj["distinct"] is True
    assert proj["member_total"] == 2
    joins = sorted(by_kind["JOIN"], key=lambda s: s["node_id"])
    assert [j["node_id"] for j in joins] == [
        f"{scope_id}::structure/JOIN/1",
        f"{scope_id}::structure/JOIN/2",
    ]
    assert [j["join_type"] for j in joins] == ["Inner", "LeftOuter"]
    assert by_kind["TOP"][0]["top_text"].strip() == "5"
    positions = [s["position"] for s in structures]
    assert sorted(positions) == list(range(1, len(structures) + 1))


def test_comma_join_is_named_not_invisible(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "cj.sql",
               "SELECT a FROM T1, T2 WHERE T1.k = T2.k;")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    joins = [s for s in _load(out, "05_semantic_graph_structure_output.json")
             if s["structure_kind"] == "JOIN"]
    assert len(joins) == 1
    assert joins[0]["join_type"] == "comma"


def test_union_arms_are_full_scopes_never_empty(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "un.sql",
               "SELECT a FROM T1 UNION SELECT a FROM T2;")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    scope_id = "file::un::scope/delivery"
    scopes = {s["node_id"]: s for s in _load(out, "05_semantic_graph_scope_output.json")}
    structures = _load(out, "05_semantic_graph_structure_output.json")
    combos = [s for s in structures
              if s["structure_kind"] == "COMBINATION"]
    assert len(combos) == 1
    assert combos[0]["owning_scope"] == scope_id
    assert combos[0]["combination_type"] == "Union"
    assert combos[0]["all"] is False
    for arm_id in (f"{scope_id}::arm1", f"{scope_id}::arm2"):
        arm = scopes[arm_id]
        assert arm["scope_kind"] == "union_arm"
        arm_kinds = [s["structure_kind"] for s in structures
                     if s["owning_scope"] == arm_id]
        assert arm_kinds.count("PROJECTION") == 1, arm_id  # FULL scopes
        assert arm_kinds.count("FROM") == 1, arm_id
    edge_pairs = {(e["from_id"], e["to_id"])
                  for e in _load(out, "05_semantic_graph_contains_edges_output.json")}
    assert (combos[0]["node_id"], f"{scope_id}::arm1") in edge_pairs
    assert (combos[0]["node_id"], f"{scope_id}::arm2") in edge_pairs


def test_star_elements_count_in_member_total(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "star.sql", "SELECT T.*, a FROM T;")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    proj = [s for s in _load(out, "05_semantic_graph_structure_output.json")
            if s["structure_kind"] == "PROJECTION"][0]
    assert proj["member_total"] == 2  # the star is COUNTED, not skipped


def test_cte_scopes_name_keyed_in_declaration_order(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql, "wcte.sql",
        "WITH c1 AS (SELECT 1 AS a), c2 AS (SELECT a FROM c1)\n"
        "SELECT a FROM c2;",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    scopes = {s["node_id"]: s for s in _load(out, "05_semantic_graph_scope_output.json")}
    assert scopes["file::wcte::scope/c1"]["scope_kind"] == "cte"
    assert scopes["file::wcte::scope/c2"]["scope_kind"] == "cte"
    delivery = scopes["file::wcte::scope/delivery"]
    assert delivery["scope_kind"] == "delivery"
    assert delivery["scope_name"] == "delivery"
    # declaration order on the statement->scope edges; main scope last
    pos = {e["to_id"]: e["position"]
           for e in _load(out, "05_semantic_graph_contains_edges_output.json")
           if e["to_id"].startswith("file::wcte::scope/")}
    assert pos["file::wcte::scope/c1"] < pos["file::wcte::scope/c2"] \
        < pos["file::wcte::scope/delivery"]


def test_select_into_temp_scope_and_duplicate_names(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql, "tt.sql",
        "SELECT 1 AS a INTO #x;\nSELECT 2 AS a INTO #x;",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    scopes = {s["node_id"]: s for s in _load(out, "05_semantic_graph_scope_output.json")}
    first = scopes["file::tt::scope/#x"]
    second = scopes["file::tt::scope/#x#2"]  # the duplicate law
    for s in (first, second):
        assert s["scope_kind"] == "temp_table"
        assert s["scope_name"] == "#x"
        assert s["operation"] == "select"


def test_write_target_scopes_carry_their_operation(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql, "wt.sql",
        "INSERT INTO dbo.T (a) SELECT 1 AS a;\n"
        "DELETE FROM dbo.T WHERE a = 1;",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    scopes = _load(out, "05_semantic_graph_scope_output.json")
    by_op = {s["operation"]: s for s in scopes}
    assert set(by_op) == {"insert", "delete"}
    for s in scopes:
        assert s["scope_kind"] == "write_target"
        assert s["scope_name"] == "T"
    assert by_op["insert"]["node_id"] == "file::wt::scope/T"
    assert by_op["delete"]["node_id"] == "file::wt::scope/T#2"


def test_from_level_subquery_is_positional_and_nameless(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(sql, "sub.sql",
               "SELECT a FROM (SELECT 1 AS a) AS t;")
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    scopes = {s["node_id"]: s for s in _load(out, "05_semantic_graph_scope_output.json")}
    sub = scopes["file::sub::stmt/1::scope/sub1"]
    assert sub["scope_kind"] == "subquery"
    assert sub["scope_name"] is None
    assert scopes["file::sub::scope/delivery"]["scope_kind"] == "delivery"


def test_nested_statements_recurse_with_dotted_paths(tmp_path):
    sql = tmp_path / "sql"
    _write_sql(
        sql,
        "nested.sql",
        "IF 1 = 1\nBEGIN\n  SELECT 1 AS a;\n  SELECT 2 AS b;\nEND",
    )
    out = _prep_out(tmp_path)
    semantic_graph.build(sql, out, DIR02)
    by_pos = {r["position"]: r for r in _load(out, "05_semantic_graph_statement_output.json")}
    assert set(by_pos) == {"1", "1.1", "1.2"}  # nothing silently skipped
    edges = _load(out, "05_semantic_graph_contains_edges_output.json")
    pairs = {(e["from_id"], e["to_id"]) for e in edges}
    assert ("file::nested", "file::nested::stmt/1") in pairs
    assert ("file::nested::stmt/1", "file::nested::stmt/1.1") in pairs
    assert ("file::nested::stmt/1", "file::nested::stmt/1.2") in pairs


# ------------- D3 REOPENED 2026-10-02: star expansion (red first)
# Stars over SCOPES expand through the graph's own stored outputs
# (match_basis star_member, one edge per union arm, recursing to
# explicit outputs); star over a BASE TABLE stays behind_star.


def test_star_member_union_arms_dual_origin(tmp_path):
    out = _build5(tmp_path, {"su.sql":
                  "SELECT T1.ID, T1.NAME INTO #a FROM T1;\n"
                  "SELECT T2.ID, T2.NAME INTO #b FROM T2;\n"
                  "SELECT * INTO #u FROM #a UNION SELECT * FROM #b;\n"
                  "SELECT u.NAME FROM #u u;"})
    rows = [r for r in _resolves(out, to_kind="member",
                                 ref_text="u.NAME")
            if r.get("match_basis") == "star_member"]
    assert len(rows) == 2  # one origin PER ARM — dual is the truth
    targets = sorted(r["to_id"] for r in rows)
    assert any("::scope/#a::" in t for t in targets), targets
    assert any("::scope/#b::" in t for t in targets), targets


def test_star_member_single_source(tmp_path):
    out = _build5(tmp_path, {"ss.sql":
                  "SELECT T1.ID, T1.NAME INTO #a FROM T1;\n"
                  "SELECT * INTO #c FROM #a;\n"
                  "SELECT c.ID FROM #c c;"})
    rows = [r for r in _resolves(out, to_kind="member",
                                 ref_text="c.ID")
            if r.get("match_basis") == "star_member"]
    assert len(rows) == 1
    assert "::scope/#a::" in rows[0]["to_id"]


def test_star_member_recurses_through_star_fed_scopes(tmp_path):
    out = _build5(tmp_path, {"sr.sql":
                  "SELECT T1.ID, T1.NAME INTO #a FROM T1;\n"
                  "SELECT * INTO #c FROM #a;\n"
                  "SELECT * INTO #d FROM #c;\n"
                  "SELECT d.NAME FROM #d d;"})
    rows = [r for r in _resolves(out, to_kind="member",
                                 ref_text="d.NAME")
            if r.get("match_basis") == "star_member"]
    assert len(rows) == 1
    # walked #d -> #c -> #a until EXPLICIT outputs, per the contract
    assert "::scope/#a::" in rows[0]["to_id"]


def test_star_over_base_table_stays_blind(tmp_path):
    out = _build5(tmp_path, {"sb.sql":
                  "SELECT * INTO #t FROM T1;\n"
                  "SELECT x.A FROM #t x;"})
    rows = _resolves(out, ref_text="x.A")
    assert len(rows) == 1
    assert rows[0]["to_kind"] == "scope"
    assert rows[0]["match_basis"] == "behind_star"
    assert not [r for r in _resolves(out, to_kind="member")
                if r.get("match_basis") == "star_member"]


def test_star_name_no_arm_holds_is_missing_not_blind(tmp_path):
    out = _build5(tmp_path, {"sm.sql":
                  "SELECT T1.ID INTO #a FROM T1;\n"
                  "SELECT T2.ID INTO #b FROM T2;\n"
                  "SELECT * INTO #u FROM #a UNION SELECT * FROM #b;\n"
                  "SELECT u.GHOST FROM #u u;"})
    rows = _resolves(out, ref_text="u.GHOST")
    assert len(rows) == 1
    assert rows[0]["to_kind"] == "unresolved"
    assert rows[0]["class"] == "scope_column_missing"


def test_star_mixed_arm_blind_keeps_remainder(tmp_path):
    """One arm expandable, one arm star-over-base-table: the traced
    origin rides star_member, the blind arm stays recorded as ONE
    behind_star remainder. [The mixed-case shape is flagged for
    Sunny's call at pseudo-code approval — zero corpus cases.]"""
    out = _build5(tmp_path, {"sx.sql":
                  "SELECT T1.ID, T1.NAME INTO #a FROM T1;\n"
                  "SELECT * INTO #u FROM #a UNION SELECT * FROM T2;\n"
                  "SELECT u.NAME FROM #u u;"})
    rows = _resolves(out, ref_text="u.NAME")
    bases = sorted(r.get("match_basis") for r in rows)
    assert bases == ["behind_star", "star_member"]


# ------------------------------------------------- the view class (D13)
# 10_work_wheel.md D13, ruled 2026-10-07 (her work scale-up: "we need to
# add views, there are hundreds"). RED until semantic_graph unwraps the
# THREE view wrappers to their SELECT, the proc precedent: a wrapper
# contributes its body in place. A view's body is ONE SelectStatement
# (not a StatementList) — the unwrap gets a view branch.

_VIEW_BODY = ("SELECT FIX_COL_A, FIX_COL_B\n"
              "FROM FIX_TABLE_ONE\nWHERE FIX_COL_A = 1\n")
_VIEW_VARIANTS = {
    "v_fix_create.sql": "CREATE VIEW rpt.V_FIX_CREATE AS\n" + _VIEW_BODY,
    "v_fix_alter.sql": "ALTER VIEW rpt.V_FIX_ALTER AS\n" + _VIEW_BODY,
    "v_fix_coa.sql":
        "CREATE OR ALTER VIEW rpt.V_FIX_COA AS\n" + _VIEW_BODY,
}


def test_view_class_all_three_variants_handled(tmp_path):
    """Every view variant lands handled — zero remainder, zero gap."""
    out = _build5(tmp_path, dict(_VIEW_VARIANTS))
    for row in _load(out, "05_semantic_graph_file_output.json"):
        assert row["remainder_total"] == 0, row["file_name"]
        assert row["statements_handled"] == 1, row["file_name"]


def test_view_select_is_mapped_as_select(tmp_path):
    """The statement row speaks SELECT, not the wrapper's type name."""
    out = _build5(tmp_path, dict(_VIEW_VARIANTS))
    stmts = _load(out, "05_semantic_graph_statement_output.json")
    assert len(stmts) == 3
    for row in stmts:
        assert row["statement_kind"] == "SELECT", row["node_id"]
        assert row["disposition"] == "handled", row["node_id"]


def test_view_builds_a_delivery_scope_with_structure(tmp_path):
    """The view's SELECT builds the same graph a proc's SELECT does:
    a delivery scope per file, FROM + WHERE structures under it."""
    out = _build5(tmp_path, dict(_VIEW_VARIANTS))
    scopes = _load(out, "05_semantic_graph_scope_output.json")
    structures = _load(out, "05_semantic_graph_structure_output.json")
    for stem in ("v_fix_create", "v_fix_alter", "v_fix_coa"):
        mine = [s for s in scopes
                if s["node_id"].split("::")[1] == stem]
        assert mine, f"no scope for {stem}"
        assert any(s["scope_kind"] == "delivery" for s in mine), stem
        kinds = {st["structure_kind"] for st in structures
                 if st["node_id"].split("::")[1] == stem}
        assert {"FROM", "WHERE"} <= kinds, (stem, kinds)
