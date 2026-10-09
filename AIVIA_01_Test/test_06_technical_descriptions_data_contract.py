"""Phase 06 contract tests
(AIVIA_01_Design/06_technical_descriptions_data_contract.md,
APPROVED 2026-10-02).

Current section: L03 — predicate voicing (R4 kinds + the ruled
negation closed set, R5 subject words, R6 degenerates, R8
annotations, 3a value meanings MEANING-FIRST).

Written test-first: RED until technical_descriptions.py exposes
    render_predicates(dir05, dir02, dir01) -> (rows, counted)

Byte-exact posture (design decision 7): sentences are pinned as
EXACT strings. A wording change is a deliberate re-pin with a
BASIS_VERSION bump, never a drift.

Zero API cost — phase 06 is fully deterministic.
"""

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
DIR05 = REPO_ROOT / "AIVIA_01_Data" / "05_semantic_graph"
DIR02 = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
SQL_DIR_06 = REPO_ROOT / "AIVIA_01_Data" / "01_subject_sql_files"
KIND_LIBRARY = DIR05 / "05_kind_library.json"

sys.path.insert(0, str(CODE_DIR))
import semantic_graph  # noqa: E402
import technical_descriptions  # noqa: E402


def _mini_dict06(tmp: Path) -> Path:
    """A controlled 02 estate WITH column descriptions (R5 needs
    them): T1 columns exercise temporal/numeric/pattern words; T1
    MYSTERY_COL has NO description (the column_words_gap case);
    CAT_C routes to ZC_CAT (J3) whose values map 7 -> Lucky."""
    d = tmp / "mini_dict06"
    d.mkdir()

    def col(tab, name, desc, pk=False):
        return {"table_name": tab, "column_name": name,
                "schema_name": "dbo", "column_description": desc,
                "is_primary_key": "Y" if pk else "N"}

    cols = [
        col("T1", "ID", "The identifier of the record.", pk=True),
        col("T1", "ADMIT_DATE", "The date of the visit."),
        col("T1", "BED_COUNT", "The count of beds."),
        col("T1", "PATIENT_NAME", "The name of the patient."),
        col("T1", "CAT_C", "The category of the record."),
        col("T1", "MYSTERY_COL", ""),
        col("T1", "EVENT_INSTANT", "The instant of the event."),
        col("T1", "SUPP_FLAG",
            "Supplemental: the flag of the run."),
        col("ZC_CAT", "CAT_C", "The category code.", pk=True),
        col("ZC_CAT", "NAME", "The name of the category."),
    ]
    joins = [{"join_id": "J3", "ordinal": 1,
              "source_table_name": "T1",
              "source_column_name": "CAT_C",
              "destin_table_name": "ZC_CAT",
              "destin_column_name": "CAT_C"}]
    vals = [{"table_name": "ZC_CAT", "code": "7",
             "meaning": "Lucky"}]
    (d / "02_emr_data_dictionary_extraction_column.json").write_text(
        json.dumps(cols))
    (d / "02_emr_data_dictionary_extraction_join.json").write_text(
        json.dumps(joins))
    (d / "02_emr_data_dictionary_extraction_value.json").write_text(
        json.dumps(vals))
    return d


def _render(tmp_path, sql_text):
    """Build the 05 graph over one fabricated file, then render
    the predicate descriptions from the sheets (never the SQL,
    except R8's one permitted comment read)."""
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "fab.sql").write_text(sql_text)
    out = tmp_path / "05_semantic_graph"
    out.mkdir()
    shutil.copy(KIND_LIBRARY, out / "05_kind_library.json")
    dict_dir = _mini_dict06(tmp_path)
    semantic_graph.build(sql, out, dict_dir)
    return technical_descriptions.render_predicates(out, dict_dir,
                                                    sql)


def _sentences(rows):
    return [r["sentence"] for r in rows]


# ---------------------------------------- R4 + R5 + 3a (byte-exact)

def test_eq_with_value_meaning_is_meaning_first(tmp_path):
    """3a's ruled format: MEANING (code) — supersedes the prior
    estate's code-first form."""
    rows, counted = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C = 7;")
    assert _sentences(rows) == ["The record category is 'Lucky' (7)."]


def test_temporal_gte_from_the_word_test(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.ADMIT_DATE >= '2024-01-01';")
    assert _sentences(rows) == [
        "The visit date is on or after '2024-01-01'."]


def test_numeric_gt_exceeds(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.BED_COUNT > 5;")
    assert _sentences(rows) == ["The count of beds exceeds 5."]


def test_pattern_match_wildcard_shapes(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.PATIENT_NAME LIKE 'E11%' "
        "AND T1.PATIENT_NAME LIKE '%son';")
    assert _sentences(rows) == [
        "The patient name starts with 'E11'.",
        "The patient name ends with 'son'."]


def test_range_inclusive(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.BED_COUNT BETWEEN 1 AND 9;")
    assert _sentences(rows) == [
        "The count of beds is between 1 and 9 (inclusive)."]


def test_null_check(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.ADMIT_DATE IS NULL;")
    assert _sentences(rows) == [
        "The visit date has no recorded value."]


def test_in_list_meanings_where_bound(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C IN (7, 5);")
    assert _sentences(rows) == [
        "The record category is one of the values 'Lucky' (7), 5."]


# ------------------------------------------- negation (closed set)

def test_not_null_speaks_the_positive_fact_in_name_words(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.ADMIT_DATE IS NOT NULL;")
    assert _sentences(rows) == ["The admit date is recorded."]


def test_negated_compare_flips_kind(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE NOT (T1.BED_COUNT > 5);")
    assert _sentences(rows) == ["The count of beds is at most 5."]


def test_negated_pattern_negates_the_verb(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 "
        "WHERE T1.PATIENT_NAME NOT LIKE 'E11%';")
    assert _sentences(rows) == [
        "The patient name does not start with 'E11'."]


# ------------------------------------------------ R6 + R5 gap + R8

def test_degenerate_never_voiced_but_counted(tmp_path):
    rows, counted = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE 1 = 1 AND T1.CAT_C = 7;")
    assert _sentences(rows) == ["The record category is 'Lucky' (7)."]
    assert not any("1 = 1" in s or "1=1" in s
                   for s in _sentences(rows))
    deg = [c for c in counted
           if c["class"] == "degenerate_never_voiced"]
    assert len(deg) == 1


def test_column_without_description_voices_name_and_counts(tmp_path):
    rows, counted = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.MYSTERY_COL = 1;")
    assert _sentences(rows) == ["The mystery col is 1."]
    gaps = [c for c in counted if c["class"] == "column_words_gap"]
    assert len(gaps) == 1


# RE-PINNED 2026-10-08 (D15 comment-first, BASIS 06.4.0, the
# ruled re-pin path): the comment is voiced AS the meaning in
# 3a's meaning-first shape; the "(annotated ...)" tail retires
# where a comment exists; a disagreeing DECLARED meaning is now
# the counted side. RED until the flip lands.

def test_trailing_comment_is_the_meaning(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 "
        "WHERE T1.BED_COUNT = 5  --five beds\n;")
    assert _sentences(rows) == [
        "The count of beds is 'five beds' (5)."]


def test_comment_wins_disagreement_counted(tmp_path):
    rows, counted = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C = 7  --Unlucky\n;")
    assert _sentences(rows) == [
        "The record category is 'Unlucky' (7)."]
    dis = [c for c in counted
           if c["class"] == "annotation_disagreement"]
    assert len(dis) == 1


def test_non_value_comment_keeps_the_honest_suffix(tmp_path):
    """The home-estate regression (caught at the 06.4.0 re-pin
    diff): a column-vs-column predicate with a revision comment
    must NOT wrap a trailing WORD as if it were a value — the
    meaning-first wrap is for NUMBERS; words keep the suffix."""
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 JOIN ZC_CAT Z "
        "ON T1.CAT_C = Z.CAT_C  --Added on 7/6/2026\n;")
    (s,) = _sentences(rows)
    assert "(annotated 'Added on 7/6/2026' in the source)" in s
    assert "'Added on 7/6/2026' (" not in s


def test_no_comment_voices_exactly_as_before(tmp_path):
    """The flip touches ONLY commented predicates — the declared
    meaning-first shape stands untouched everywhere else."""
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C = 7;")
    assert _sentences(rows) == ["The record category is 'Lucky' (7)."]


def test_header_description_read_not_stored(tmp_path):
    """D15: the header block's Description: line — read at build
    time, collapsed, None when absent; the SQL is the one store."""
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "fab.sql").write_text(
        "/**********************\n"
        "Create date: 01/01/2020\n"
        "Description:\tThis view returns all fix members and\n"
        "\t\ttheir current fix provider\n"
        "======================\n"
        "Revision Detail\n"
        "**********************/\n"
        "CREATE VIEW dbo.V_FAB AS SELECT 1 AS A;\n")
    (sql / "bare.sql").write_text(
        "CREATE VIEW dbo.V_BARE AS SELECT 1 AS A;\n")
    got = technical_descriptions.header_description(sql, "fab")
    assert got == ("This view returns all fix members and "
                   "their current fix provider")
    assert technical_descriptions.header_description(
        sql, "bare") is None
    # the SECOND header shape in the wild (the home census
    # proc): -- line comments, divider-terminated
    (sql / "dash.sql").write_text(
        "-- =============\n"
        "-- Author: fix\n"
        "-- Description:    Replaces the fix Crystal report  \n"
        "-- =============\n"
        "CREATE PROCEDURE dbo.USP_FIX AS SELECT 1 AS A;\n")
    assert technical_descriptions.header_description(
        sql, "dash") == "Replaces the fix Crystal report"


def test_column_comparand_speaks_words_never_raw_tokens(tmp_path):
    """R5: raw column tokens never reach prose — a column-vs-column
    predicate (the join shape) voices BOTH sides' words."""
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 JOIN ZC_CAT z "
        "ON T1.CAT_C = z.CAT_C;")
    assert _sentences(rows) == [
        "The record category is the category code."]
    assert not any("z.CAT_C" in s for s in _sentences(rows))


# --------------------------- L04: condition composition (red first)


def _render_cond(tmp_path, sql_text):
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "fab.sql").write_text(sql_text)
    out = tmp_path / "05_semantic_graph"
    out.mkdir()
    shutil.copy(KIND_LIBRARY, out / "05_kind_library.json")
    dict_dir = _mini_dict06(tmp_path)
    semantic_graph.build(sql, out, dict_dir)
    return technical_descriptions.render_conditions(out, dict_dir,
                                                    sql)


def test_and_joins_with_lowered_continuations(tmp_path):
    rows, _, _ = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C = 7 "
        "AND T1.ADMIT_DATE >= '2024-01-01';")
    assert _sentences(rows) == [
        "The record category is 'Lucky' (7) and the visit date is "
        "on or after '2024-01-01'."]


def test_top_level_or_stays_plain(tmp_path):
    rows, _, _ = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C = 7 "
        "OR T1.BED_COUNT > 5;")
    assert _sentences(rows) == [
        "The record category is 'Lucky' (7) or the count of beds "
        "exceeds 5."]


def test_nested_or_group_gains_either(tmp_path):
    rows, _, _ = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.MYSTERY_COL = 1 "
        "AND (T1.CAT_C = 7 OR T1.BED_COUNT > 5);")
    assert _sentences(rows) == [
        "The mystery col is 1 and either the record category is "
        "'Lucky' (7) or the count of beds exceeds 5."]


def test_structural_not_wraps_the_group(tmp_path):
    rows, _, _ = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 WHERE NOT (T1.CAT_C = 7 "
        "OR T1.BED_COUNT > 5);")
    assert _sentences(rows) == [
        "It is not the case that either the record category is "
        "'Lucky' (7) or the count of beds exceeds 5."]


def test_single_predicate_tree_is_its_sentence(tmp_path):
    rows, _, _ = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C = 7;")
    assert _sentences(rows) == ["The record category is 'Lucky' (7)."]


def test_degenerate_leaf_pruned_from_the_phrase(tmp_path):
    rows, _, _ = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 WHERE 1 = 1 AND T1.CAT_C = 7;")
    assert _sentences(rows) == ["The record category is 'Lucky' (7)."]
    assert not any("1 = 1" in s or "1=1" in s
                   for s in _sentences(rows))


def test_all_degenerate_tree_no_row_counted_once(tmp_path):
    rows, counted, _ = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 WHERE 1 = 1;")
    assert _sentences(rows) == []
    cond_deg = [c for c in counted
                if c["class"] == "degenerate_never_voiced"
                and c["grain"] == "condition"]
    assert len(cond_deg) == 1


def test_join_tree_neutral_row_and_on_class_parts(tmp_path):
    rows, _, parts = _render_cond(tmp_path,
        "SELECT T1.ID FROM T1 LEFT JOIN ZC_CAT z "
        "ON T1.CAT_C = z.CAT_C AND z.NAME = 'Lucky';")
    assert _sentences(rows) == [
        "The record category is the category code and the "
        "category name is 'Lucky'."]
    tree = next(iter(parts))
    assert parts[tree] == {
        "join_pair": ["The record category is the category code"],
        "lookup_shaping": ["The category name is 'Lucky'"]}


# ------------------------------- L05: scope sentences (red first)


def _render_scopes(tmp_path, sql_text):
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "fab.sql").write_text(sql_text)
    out = tmp_path / "05_semantic_graph"
    out.mkdir()
    shutil.copy(KIND_LIBRARY, out / "05_kind_library.json")
    dict_dir = _mini_dict06(tmp_path)
    semantic_graph.build(sql, out, dict_dir)
    return technical_descriptions.render_scopes(out, dict_dir, sql)


def test_scope_lead_membership_payload(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.ID, T1.PATIENT_NAME FROM T1 "
        "WHERE T1.CAT_C = 7;")
    assert _sentences(rows) == [
        "This is a selection from T1: the record category is "
        "'Lucky' (7); carrying the record identifier, "
        "the patient name."]


def test_scope_honest_no_conditions(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.ID FROM T1;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; carrying the record identifier."]


def test_scope_inner_join_matched_where(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.ID FROM T1 JOIN ZC_CAT z "
        "ON T1.CAT_C = z.CAT_C WHERE T1.BED_COUNT > 5;")
    assert _sentences(rows) == [
        "This is a selection from T1, joined with ZC_CAT "
        "(matched where the record category is the category "
        "code): the count of beds exceeds 5; carrying the "
        "record identifier."]


def test_scope_left_join_attaches_never_filters(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.ID FROM T1 LEFT JOIN ZC_CAT z "
        "ON T1.CAT_C = z.CAT_C AND z.NAME = 'Lucky';")
    assert _sentences(rows) == [
        "This is a selection from T1, attaching ZC_CAT "
        "(matched where the record category is the category "
        "code; attachment rule: the category name is 'Lucky'): "
        "no membership conditions are applied; carrying the "
        "record identifier."]


def test_scope_inner_on_literal_joins_membership(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.ID FROM T1 JOIN ZC_CAT z "
        "ON T1.CAT_C = z.CAT_C AND z.NAME = 'Lucky';")
    assert _sentences(rows) == [
        "This is a selection from T1, joined with ZC_CAT "
        "(matched where the record category is the category "
        "code): the category name is 'Lucky'; carrying the "
        "record identifier."]


def test_scope_delete_is_removal(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "DELETE FROM T1 WHERE T1.CAT_C = 7;")
    assert _sentences(rows) == [
        "This step removes records from T1: the record category "
        "is 'Lucky' (7)."]


def test_scope_no_source_derived_values(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT 1 AS a;")
    assert _sentences(rows) == [
        "This step produces derived values; no source records "
        "are read; carrying a (the constant 1)."]


def test_scope_computed_output_inside_out(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT DATEDIFF(DAY, T1.ADMIT_DATE, GETDATE()) AS los "
        "FROM T1;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; carrying los (the number of days between "
        "the visit date and the current date and time)."]


def test_scope_unvoiced_function_counted_remainder(tmp_path):
    rows, counted = _render_scopes(tmp_path,
        "SELECT SOUNDEX(T1.PATIENT_NAME) AS n FROM T1;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; carrying n (a value computed from the "
        "patient name)."]
    misses = [c for c in counted
              if c["class"] == "unvoiced_function"]
    assert len(misses) == 1


def test_scope_member_lineage_spoken(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.ID AS out_a INTO #t FROM T1;\n"
        "SELECT out_a FROM #t;")
    reader = [r for r in rows
              if r["node_id"].endswith("scope/delivery")]
    assert [r["sentence"] for r in reader] == [
        "This is a selection from #t: no membership conditions "
        "are applied; carrying out a (built in #t, from T1.ID)."]


def test_scope_star_member_dual_origins_spoken(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.ID, T1.NAME INTO #a FROM T1;\n"
        "SELECT T2.ID, T2.NAME INTO #b FROM T2;\n"
        "SELECT * INTO #u FROM #a UNION SELECT * FROM #b;\n"
        "SELECT u.NAME FROM #u u;")
    reader = [r for r in rows
              if r["node_id"].endswith("scope/delivery")]
    assert [r["sentence"] for r in reader] == [
        "This is a selection from #u: no membership conditions "
        "are applied; carrying name (read through #u, origins "
        "#a.NAME and #b.NAME)."]


def test_scope_behind_star_honestly_blind(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT * INTO #t FROM T1;\n"
        "SELECT x.A FROM #t x;")
    reader = [r for r in rows
              if r["node_id"].endswith("scope/delivery")]
    assert [r["sentence"] for r in reader] == [
        "This is a selection from #t: no membership conditions "
        "are applied; carrying a (from #t, read through a "
        "SELECT *; base origin not traced)."]


def test_scope_case_cast_arithmetic_by_rule(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT CASE WHEN T1.CAT_C = 7 THEN 1 ELSE 0 END AS "
        "flag, CAST(T1.BED_COUNT AS INT) AS n, "
        "T1.BED_COUNT + 1 AS n1 FROM T1;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; carrying flag (a value derived by rule), "
        "n (the count of beds), n1 (the count of beds plus 1)."]


def test_scope_group_by_spoken(tmp_path):
    rows, _ = _render_scopes(tmp_path,
        "SELECT T1.CAT_C FROM T1 GROUP BY T1.CAT_C;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; grouped per the record category; carrying "
        "the record category."]


def test_null_string_description_is_a_gap_not_words(tmp_path):
    """A 02 description holding the literal string 'NULL' is no
    description — readable name + counted gap, never 'the NULL'
    (the corpus ZC_PAT_SERVICE.HOSP_SERV_C find, 2026-10-03)."""
    d = _mini_dict06(tmp_path)
    cols = json.loads(
        (d / "02_emr_data_dictionary_extraction_column.json")
        .read_text())
    for c in cols:
        if c["column_name"] == "MYSTERY_COL":
            c["column_description"] = "NULL"
    (d / "02_emr_data_dictionary_extraction_column.json"
     ).write_text(json.dumps(cols))
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "fab.sql").write_text(
        "SELECT T1.ID FROM T1 WHERE T1.MYSTERY_COL = 1;")
    out = tmp_path / "05_semantic_graph"
    out.mkdir()
    shutil.copy(KIND_LIBRARY, out / "05_kind_library.json")
    semantic_graph.build(sql, out, d)
    rows, counted = technical_descriptions.render_predicates(
        out, d, sql)
    assert _sentences(rows) == ["The mystery col is 1."]
    assert any(c["class"] == "column_words_gap" for c in counted)


def test_every_function_voicing_row_has_a_renderer(tmp_path):
    """The library is the ruled registry; the code must cover
    every row — a row without a renderer would silently fall to
    the remainder phrase, lying about the library."""
    lib = json.loads(KIND_LIBRARY.read_text())
    ops = {r["Operation"] for r in
           lib["sheets"]["Function_Voicings"]
           if r["Operation"] != "_ruling"}
    covered = set(technical_descriptions.FUNCTION_RENDERERS)
    assert ops <= covered, ops - covered


def test_computed_member_speaks_its_output_name(tmp_path):
    """A read through a COMPUTED member speaks the author's
    output name, never the defining expression's raw tokens (the
    'calendar dt))' corpus find, 2026-10-03)."""
    rows, _ = _render(tmp_path,
        "SELECT CAST(T1.ADMIT_DATE AS DATE) AS start_date "
        "INTO #m FROM T1;\n"
        "SELECT T1.ID FROM T1 JOIN #m m "
        "ON m.start_date = T1.ADMIT_DATE;")
    joined = " ".join(_sentences(rows))
    assert "The start date is the visit date." in joined
    assert ")" not in joined.replace("(inclusive)", "")


# ------- gap-check rulings 2026-10-03 (five items, red first)


def test_ratified_aggregate_voicings(tmp_path):
    rows, counted = _render_scopes(tmp_path,
        "SELECT MAX(T1.ADMIT_DATE) AS m, MIN(T1.BED_COUNT) AS lo, "
        "COUNT(*) AS n, COUNT(T1.ID) AS nid, "
        "SUM(T1.BED_COUNT) AS s FROM T1;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; carrying m (the latest visit date), "
        "lo (the smallest count of beds), n (the count of "
        "records), nid (the count of the record identifier), "
        "s (the total of the count of beds)."]
    assert not [c for c in counted
                if c["class"] == "unvoiced_function"]


def test_ratified_scalar_voicings(tmp_path):
    rows, counted = _render_scopes(tmp_path,
        "SELECT CONCAT(T1.ID, T1.PATIENT_NAME) AS c, "
        "FORMAT(T1.ADMIT_DATE, 'yyyy-MM') AS f, "
        "CHAR(10) AS ch FROM T1;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; carrying c (the record identifier, the "
        "patient name joined into one text), f (the visit date, "
        "formatted as 'yyyy-MM'), ch (the character with code "
        "10)."]
    assert not [c for c in counted
                if c["class"] == "unvoiced_function"]


def test_row_number_interim_voicing(tmp_path):
    rows, counted = _render_scopes(tmp_path,
        "SELECT ROW_NUMBER() OVER (ORDER BY T1.ID) AS rn "
        "FROM T1;")
    assert _sentences(rows) == [
        "This is a selection from T1: no membership conditions "
        "are applied; carrying rn (its position in an ordered "
        "sequence of records)."]
    assert not [c for c in counted
                if c["class"] == "unvoiced_function"]


def test_supplemental_prefix_stripped(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.SUPP_FLAG = 1;")
    assert _sentences(rows) == ["The run flag is 1."]


def test_instant_word_is_temporal(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 "
        "WHERE T1.EVENT_INSTANT >= '2024-01-01';")
    assert _sentences(rows) == [
        "The event instant is on or after '2024-01-01'."]


# -------------- L06: statements, file floor, ledger (red first)


def _render_all(tmp_path, sql_text):
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "fab.sql").write_text(sql_text)
    out = tmp_path / "05_semantic_graph"
    out.mkdir()
    shutil.copy(KIND_LIBRARY, out / "05_kind_library.json")
    dict_dir = _mini_dict06(tmp_path)
    semantic_graph.build(sql, out, dict_dir)
    return technical_descriptions.render_all(out, dict_dir, sql)


def _grain(rows, grain):
    return [r for r in rows if r["grain"] == grain]


def test_statement_voicings_build_and_deliver(tmp_path):
    rows, ledger = _render_all(tmp_path,
        "SELECT T1.ID INTO #a FROM T1;\n"
        "SELECT T1.ID FROM T1;")
    assert _sentences(_grain(rows, "statement")) == [
        "Builds the a selection.",
        "Delivers the procedure's result set."]


def test_statement_unvoiced_and_operational_counted(tmp_path):
    rows, ledger = _render_all(tmp_path,
        "DECLARE @x INT;\nSET @x = 1;\n"
        "SELECT T1.ID FROM T1;")
    assert _sentences(_grain(rows, "statement")) == [
        "Delivers the procedure's result set."]
    classes = [c["class"] for c in ledger
               if c["grain"] == "statement"]
    assert classes.count("operational_statement") == 1  # DECLARE
    assert classes.count("unvoiced_statement_kind") == 1  # SET


def test_file_three_levels_byte_exact(tmp_path):
    rows, _ = _render_all(tmp_path,
        "SELECT T1.ID AS out_a INTO #t FROM T1 "
        "WHERE T1.CAT_C = 7;\n"
        "SELECT out_a FROM #t;")
    file_rows = _grain(rows, "file")
    assert len(file_rows) == 1
    assert file_rows[0]["sentence"] == (
        "Delivers a selection from #t: no membership conditions "
        "are applied; carrying out a (built in #t, from T1.ID).\n"
        "Pipeline: (1) Builds the t selection. "
        "(2) Delivers the procedure's result set.\n"
        "Presents: out a (built in #t, from T1.ID).\n"
        "Population: In #t: the record category is 'Lucky' (7).\n"
        "Steps: 2, 2 voiced, 0 operational, 0 gap. "
        "Selections: #t.")


def test_file_gap_sentence_amended_shape(tmp_path):
    rows, ledger = _render_all(tmp_path,
        "DECLARE @s VARCHAR(100);\n"
        "SET @s = 'SELECT 1';\n"
        "EXEC(@s);")
    text = _grain(rows, "file")[0]["sentence"]
    assert ("Part of this file's logic is built as a string at "
            "run time and is not described here; it is executed "
            "by \"EXEC(@s)\". 1 of 3 statements is in this gap."
            ) in text
    assert [c for c in ledger
            if c["class"] == "dynamic_sql_gap"]


def test_file_parameter_voicing_verbatim_default(tmp_path):
    rows, _ = _render_all(tmp_path,
        "CREATE PROCEDURE p (@d DATE = '2024-01-01') AS\n"
        "SELECT T1.ID FROM T1 WHERE T1.ADMIT_DATE >= @d;")
    text = _grain(rows, "file")[0]["sentence"]
    assert ("Parameters shaping the population: @d (default "
            "\"'2024-01-01'\").") in text


def test_lookup_attachment_counted_apart(tmp_path):
    rows, ledger = _render_all(tmp_path,
        "SELECT T1.ID FROM T1 LEFT JOIN ZC_CAT z "
        "ON T1.CAT_C = z.CAT_C AND z.NAME = 'Lucky';")
    apart = [c for c in ledger
             if c["class"] == "lookup_shaping_attachment"]
    assert len(apart) == 1
    # the predicate IS voiced — in the scope's attachment rule
    scope = _grain(rows, "scope")[0]["sentence"]
    assert "attachment rule: the category name is 'Lucky'" in scope


def test_the_equation_closes_on_the_real_corpus():
    """DECISION 5 AS A TEST: voiced + counted == total, per file
    per grain, on the real 8 files. A red ledger does not ship."""
    rows, ledger = technical_descriptions.render_all(
        DIR05, DIR02, SQL_DIR_06)
    silence = {"degenerate_never_voiced", "operational_statement",
               "dynamic_sql_gap", "unvoiced_statement_kind",
               "unvoiced_function"}
    counted = [c for c in ledger if c["class"] in silence]

    preds = json.loads(
        (DIR05 / "05_semantic_graph_predicate_output.json").read_text())
    stmts = json.loads(
        (DIR05 / "05_semantic_graph_statement_output.json").read_text())
    scopes = json.loads(
        (DIR05 / "05_semantic_graph_scope_output.json").read_text())
    files = json.loads(
        (DIR05 / "05_semantic_graph_file_output.json").read_text())

    def by_file(items, key="node_id"):
        out = {}
        for i in items:
            out.setdefault(i[key].split("::")[1], []).append(i)
        return out

    rows_f = by_file(rows)
    counted_f = by_file(counted)
    for f in files:
        name = f["file_name"]
        frows = rows_f.get(name, [])
        fcount = counted_f.get(name, [])

        def n(grain, items):
            return len([x for x in items
                        if x["grain"] == grain])
        # predicate grain
        total_preds = len([p for p in preds
                           if p["node_id"].split("::")[1] == name])
        assert n("predicate", frows) + n("predicate", fcount) \
            == total_preds, name
        # scope grain
        total_scopes = len([s for s in scopes
                            if s["node_id"].split("::")[1] == name])
        assert n("scope", frows) == total_scopes, name
        # statement grain
        total_stmts = len([s for s in stmts
                           if s["node_id"].split("::")[1] == name])
        assert n("statement", frows) + n("statement", fcount) \
            == total_stmts, name
        # file grain
        assert n("file", frows) == 1, name


# ------------------- L07: the artifacts land (red first)


def _build06(tmp_path, sql_text):
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "fab.sql").write_text(sql_text)
    d05 = tmp_path / "05_semantic_graph"
    d05.mkdir()
    shutil.copy(KIND_LIBRARY, d05 / "05_kind_library.json")
    dict_dir = _mini_dict06(tmp_path)
    semantic_graph.build(sql, d05, dict_dir)
    out06 = tmp_path / "06_technical_descriptions"
    out06.mkdir()
    technical_descriptions.build06(d05, out06, dict_dir, sql)
    return out06


TWO_STEP = ("SELECT T1.ID AS out_a INTO #t FROM T1 "
            "WHERE T1.CAT_C = 7;\n"
            "SELECT out_a FROM #t;")


def test_build_writes_all_artifacts(tmp_path):
    out = _build06(tmp_path, TWO_STEP)
    names = {p.name for p in out.iterdir()}
    # THE NAMING LAW (ruled 2026-10-08, step table row 06; the
    # per-file txt/svg keep their subject names — approved).
    # RED until the rename lands.
    assert names == {"06_technical_descriptions_output.json",
                     "06_technical_descriptions_voicing_output.json",
                     "fab.txt", "fab.svg"}
    rows = json.loads(
        (out / "06_technical_descriptions_output.json").read_text())
    grains = {r["grain"] for r in rows}
    assert grains == {"predicate", "condition", "scope",
                      "statement", "file"}


def test_text_blocks_byte_exact(tmp_path):
    out = _build06(tmp_path, TWO_STEP)
    assert (out / "fab.txt").read_text() == (
        "==== fab ====\n"
        "basis " + technical_descriptions.BASIS_VERSION + "\n"
        "\n"
        "-- THE SELECTIONS --\n"
        "#t: This is a selection from T1: the record category "
        "is 'Lucky' (7); carrying out a (the record "
        "identifier).\n"
        "delivery: This is a selection from #t: no membership "
        "conditions are applied; carrying out a (built in #t, "
        "from T1.ID).\n"
        "\n"
        "-- THE STEPS --\n"
        "(1) Builds the t selection.\n"
        "(2) Delivers the procedure's result set.\n"
        "\n"
        "-- THE FILE --\n"
        "Delivers a selection from #t: no membership conditions "
        "are applied; carrying out a (built in #t, from T1.ID).\n"
        "Pipeline: (1) Builds the t selection. "
        "(2) Delivers the procedure's result set.\n"
        "Presents: out a (built in #t, from T1.ID).\n"
        "Population: In #t: the record category is 'Lucky' (7).\n"
        "Steps: 2, 2 voiced, 0 operational, 0 gap. "
        "Selections: #t.\n")


def test_silent_steps_are_loud_in_the_text(tmp_path):
    out = _build06(tmp_path,
        "DECLARE @s VARCHAR(100);\n"
        "SET @s = 'SELECT 1';\n"
        "EXEC(@s);")
    text = (out / "fab.txt").read_text()
    assert "(1) [operational_statement]" in text
    assert "(2) [unvoiced_statement_kind]" in text
    assert "(3) [dynamic_sql_gap]" in text


def test_svg_deterministic_and_grounded(tmp_path):
    out = _build06(tmp_path, TWO_STEP)
    svg1 = (out / "fab.svg").read_bytes()
    # a second build over the same inputs: identical bytes
    out06b = tmp_path / "06b"
    out06b.mkdir()
    technical_descriptions.build06(
        tmp_path / "05_semantic_graph", out06b,
        tmp_path / "mini_dict06", tmp_path / "sql")
    assert svg1 == (out06b / "fab.svg").read_bytes()
    svg = svg1.decode()
    assert "#t" in svg and "delivery" in svg
    assert "T1.CAT_C = 7" in svg      # the predicate's fragment
    assert "'Lucky' (7)" in svg       # the value bind, spoken
    assert "member" in svg            # the lineage edge label


def test_svg_star_fan_shows_both_arms(tmp_path):
    out = _build06(tmp_path,
        "SELECT T1.ID, T1.NAME INTO #a FROM T1;\n"
        "SELECT T2.ID, T2.NAME INTO #b FROM T2;\n"
        "SELECT * INTO #u FROM #a UNION SELECT * FROM #b;\n"
        "SELECT u.NAME FROM #u u;")
    svg = (out / "fab.svg").read_text()
    assert svg.count("star_member") >= 2  # one edge per arm


def test_corpus_build_lands_everything(tmp_path):
    out06 = tmp_path / "06"
    out06.mkdir()
    technical_descriptions.build06(
        DIR05, out06, DIR02, SQL_DIR_06)
    files = {p.name for p in out06.iterdir()}
    assert "06_technical_descriptions_output.json" in files
    assert "06_technical_descriptions_voicing_output.json" in files
    assert len([f for f in files if f.endswith(".txt")]) == 8
    assert len([f for f in files if f.endswith(".svg")]) == 8
    rows = json.loads(
        (out06 / "06_technical_descriptions_output.json").read_text())
    ledger = json.loads(
        (out06 / "06_technical_descriptions_voicing_output.json").read_text())
    # the measured corpus census, pinned (re-base by measurement
    # with the finding recorded, never silently)
    assert len(rows) == 362
    assert len(ledger) == 93


# ---------------------------------------------------- row contract

def test_rows_carry_the_contract_fields(tmp_path):
    rows, _ = _render(tmp_path,
        "SELECT T1.ID FROM T1 WHERE T1.CAT_C = 7;")
    row = rows[0]
    assert row["grain"] == "predicate"
    assert row["node_id"].endswith("::pred/1")
    assert row["basis_version"] == \
        technical_descriptions.BASIS_VERSION
    assert row["evidence_refs"]  # every claim traceable
    # determinism: a second render is byte-identical
    rows2, _ = technical_descriptions.render_predicates(
        tmp_path / "05_semantic_graph", tmp_path / "mini_dict06",
        tmp_path / "sql")
    assert rows == rows2
