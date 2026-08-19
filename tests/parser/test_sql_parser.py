"""SQL parsing — NATIVE parser only (ScriptDom, ADR 0001 hardened
2026-08-19): SQL in -> structured output, same grammar everywhere.
Multi-statement temp-table procs parse as one script; there is no
fallback parser and no per-statement pre-extraction."""

import pytest

from src.parser.sql_parser import parse_sql


class TestParseCTEs:
    def test_single_cte(self):
        sql = """
        WITH cte1 AS (
            SELECT col_a, col_b FROM table1
        )
        SELECT * FROM cte1
        """
        result = parse_sql(sql)
        assert len(result.ctes) == 1
        assert result.ctes[0].name == "cte1"
        assert "col_a" in result.ctes[0].sql_fragment

    def test_multiple_ctes(self):
        sql = """
        WITH cte1 AS (
            SELECT col_a FROM table1
        ),
        cte2 AS (
            SELECT col_a FROM cte1
        )
        SELECT * FROM cte2
        """
        result = parse_sql(sql)
        assert len(result.ctes) == 2
        assert result.ctes[1].depends_on == ["cte1"]

    def test_no_ctes(self):
        sql = "SELECT col_a FROM table1"
        result = parse_sql(sql)
        assert len(result.ctes) == 0
        assert "table1" in result.final_select_tables


class TestParseColumnRefs:
    def test_qualified_column(self):
        sql = "WITH c AS (SELECT t.col_a FROM table1 AS t) SELECT * FROM c"
        result = parse_sql(sql)
        refs = result.ctes[0].column_refs
        col_names = [r.column for r in refs]
        assert "col_a" in col_names

    def test_invalid_sql_raises(self):
        with pytest.raises(ValueError, match="parse errors"):
            parse_sql("NOT VALID SQL !!!")

    def test_no_select_raises(self):
        with pytest.raises(ValueError, match="no SELECT"):
            parse_sql("DROP TABLE #x")


class TestMultiStatementProcs:
    """Temp-table staging chains parse as ONE script — ScriptDom owns
    statement splitting (the fallback's environment-fragile splitting
    is gone with the fallback)."""

    def test_temp_tables_become_cte_entries(self):
        sql = (
            "SELECT col_a, col_b INTO #staging FROM base_table WHERE x > 0\n"
            "SELECT col_a, SUM(col_b) AS total FROM #staging GROUP BY col_a"
        )
        result = parse_sql(sql)
        cte_names = [c.name for c in result.ctes]
        assert "staging" in cte_names
        staging = [c for c in result.ctes if c.name == "staging"][0]
        assert len(staging.table_refs) > 0
        assert "staging" not in result.final_select_tables
        assert "staging" in result.final_select_cte_refs

    def test_complex_temp_table_chain(self):
        """Regression: 9 temp tables in a dependency chain — correct
        depends_on, physical tables in leaf CTEs only, final refs to
        the two summaries."""
        sql = "\n".join([
            "SELECT col1, col2 into #lab FROM ORDER_PROC_3 LEFT JOIN CLARITY_DEP dep ON dep.ID = 1",
            "SELECT ORDER_ID, min(SCANNED) as Compliant into #lab_compliant_by_dept from #lab group by ORDER_ID",
            "SELECT ORDER_ID, USER_ID into #lab_compliant_by_user from #lab group by ORDER_ID, USER_ID",
            "SELECT med.ID, dep.NAME into #blood_and_meds FROM HEP_SUM_MED_ADMIN med LEFT JOIN CLARITY_DEP dep ON med.DEPT_ID = dep.ID",  # noqa: E501
            "SELECT ID as Order_ID, case when SCANNED=1 then 1 else 0 end as Compliant into #blood_meds_compliant from #blood_and_meds",  # noqa: E501
            "SELECT Order_ID, Compliant into #blood_meds_compliant_by_dept from #blood_meds_compliant",
            "SELECT Order_ID, Compliant into #blood_meds_compliant_by_user from #blood_meds_compliant",
            "SELECT AREA, COUNT(*) as cnt into #dep_summary from (select * from #lab_compliant_by_dept union all select * from #blood_meds_compliant_by_dept) a group by AREA",  # noqa: E501
            "SELECT USER_ID, COUNT(*) as cnt into #user_summary from (select * from #lab_compliant_by_user union all select * from #blood_meds_compliant_by_user) a group by USER_ID",  # noqa: E501
            "select * From #dep_summary",
            "select * from #user_summary",
        ])
        result = parse_sql(sql)

        assert len(result.ctes) == 9
        cte_map = {c.name: c for c in result.ctes}

        assert "ORDER_PROC_3" in cte_map["lab"].table_refs
        assert "HEP_SUM_MED_ADMIN" in cte_map["blood_and_meds"].table_refs

        assert "lab" in cte_map["lab_compliant_by_dept"].depends_on
        assert "blood_and_meds" in cte_map["blood_meds_compliant"].depends_on

        assert "lab_compliant_by_dept" in cte_map["dep_summary"].depends_on
        assert "blood_meds_compliant_by_dept" in cte_map["dep_summary"].depends_on

        assert "dep_summary" in result.final_select_cte_refs
        assert "user_summary" in result.final_select_cte_refs
        assert len(result.final_select_tables) == 0

    def test_whitespace_normalized_in_fragments(self):
        sql = ("SELECT\r\n\t\tcol_a,\r\n\t\tcol_b\r\n\tINTO #stage\r\n\tFROM table1\n"
               "SELECT * FROM #stage")
        result = parse_sql(sql)
        stage = [c for c in result.ctes if c.name == "stage"][0]
        assert "\r" not in stage.sql_fragment
        assert "\t" not in stage.sql_fragment


def test_fragments_are_never_truncated():
    """2026-08-19: a 500-char cap fed the description LLM amputated SQL
    (column list only, no WHERE) — it fabricated the missing filters —
    and blinded same-logic hashes past char 500. Fragments must carry
    the FULL statement text."""
    filler = ",\n".join(f"    col_{i:04d}" for i in range(120))
    sql = (
        "CREATE PROCEDURE dbo.USP_Long AS\n"
        "WITH big_step AS (\n"
        f"    SELECT\n{filler}\n"
        "    FROM base_table\n"
        "    WHERE status_code = 42\n"
        ")\n"
        "SELECT * FROM big_step"
    )
    parsed = parse_sql(sql)
    frags = [getattr(c, "sql_fragment", "") or "" for c in parsed.ctes]
    long_frag = max(frags, key=len)
    assert len(long_frag) > 500
    assert "status_code = 42" in long_frag, (
        "the WHERE clause must survive into the stored fragment")
