"""Unit tests for SQL parser — deterministic: SQL in -> structured output."""

from src.parser.sql_parser import parse_sql, parse_extracted_queries


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
        import pytest

        with pytest.raises(ValueError, match="Failed to parse"):
            parse_sql("NOT VALID SQL !!!")


class TestParseExtractedQueries:
    """Tests for parse_extracted_queries — the shared multi-statement logic."""

    def test_single_query(self):
        queries = ["SELECT col_a FROM table1"]
        result = parse_extracted_queries(queries)
        assert len(result.ctes) == 0
        assert "table1" in result.final_select_tables

    def test_multi_query_with_temp_tables(self):
        queries = [
            "SELECT col_a, col_b INTO #staging FROM base_table WHERE x > 0",
            "SELECT col_a, SUM(col_b) AS total FROM #staging GROUP BY col_a",
        ]
        result = parse_extracted_queries(queries)
        # #staging should become a CTE-like entry (name stored without # prefix)
        cte_names = [c.name for c in result.ctes]
        assert "staging" in cte_names
        # The CTE should reference base_table (after #temp cleanup: __temp_base_table__)
        staging_cte = [c for c in result.ctes if c.name == "staging"][0]
        assert len(staging_cte.table_refs) > 0
        # staging should be in final_select_cte_refs, not final_select_tables
        assert "staging" not in result.final_select_tables

    def test_empty_queries_raises(self):
        import pytest
        with pytest.raises(ValueError, match="no SQL queries found"):
            parse_extracted_queries([])

    def test_unparseable_queries_raises(self):
        import pytest
        with pytest.raises(ValueError, match="none of"):
            parse_extracted_queries(["GARBAGE !!!", "MORE GARBAGE !!!"])

    def test_complex_temp_table_chain(self):
        """Regression: USP_CCHCS_ScanningSummaryReports_PBI pattern.

        9 temp tables in a dependency chain. Must produce:
        - 9 CTEs with correct depends_on
        - Physical tables in leaf CTEs only
        - Final CTE refs pointing to the two summary tables
        - No __temp_X__ pollution in table_refs or depends_on
        """
        queries = [
            "SELECT col1, col2 into #lab FROM ORDER_PROC_3 LEFT JOIN CLARITY_DEP dep ON dep.ID = 1",
            "SELECT ORDER_ID, min(SCANNED) as Compliant into #lab_compliant_by_dept from #lab group by ORDER_ID",
            "SELECT ORDER_ID, USER_ID into #lab_compliant_by_user from #lab group by ORDER_ID, USER_ID",
            "SELECT med.ID, dep.NAME into #blood_and_meds FROM HEP_SUM_MED_ADMIN med LEFT JOIN CLARITY_DEP dep ON med.DEPT_ID = dep.ID",
            "SELECT ID as Order_ID, case when SCANNED=1 then 1 else 0 end as Compliant into #blood_meds_compliant from #blood_and_meds",
            "SELECT Order_ID, Compliant into #blood_meds_compliant_by_dept from #blood_meds_compliant",
            "SELECT Order_ID, Compliant into #blood_meds_compliant_by_user from #blood_meds_compliant",
            "SELECT AREA, COUNT(*) as cnt into #dep_summary from (select * from #lab_compliant_by_dept union all select * from #blood_meds_compliant_by_dept) a group by AREA",
            "SELECT USER_ID, COUNT(*) as cnt into #user_summary from (select * from #lab_compliant_by_user union all select * from #blood_meds_compliant_by_user) a group by USER_ID",
            "select * From #dep_summary",
            "select * from #user_summary",
        ]
        result = parse_extracted_queries(queries)

        # Should have 9 CTEs (one per temp table)
        assert len(result.ctes) == 9
        cte_map = {c.name: c for c in result.ctes}

        # Leaf CTEs should have physical tables
        assert "ORDER_PROC_3" in cte_map["lab"].table_refs
        assert "HEP_SUM_MED_ADMIN" in cte_map["blood_and_meds"].table_refs

        # Mid-chain CTEs should depend on upstream temp tables
        assert "lab" in cte_map["lab_compliant_by_dept"].depends_on
        assert "blood_and_meds" in cte_map["blood_meds_compliant"].depends_on

        # Summary CTEs should depend on dept/user CTEs
        assert "lab_compliant_by_dept" in cte_map["dep_summary"].depends_on
        assert "blood_meds_compliant_by_dept" in cte_map["dep_summary"].depends_on

        # Final refs should point to the two summaries
        assert "dep_summary" in result.final_select_cte_refs
        assert "user_summary" in result.final_select_cte_refs
        assert len(result.final_select_tables) == 0

        # No __temp_X__ pollution anywhere
        for c in result.ctes:
            for t in c.table_refs:
                assert not t.startswith("__temp_"), f"__temp_ in table_refs: {t}"
            for d in c.depends_on:
                assert not d.startswith("__temp_"), f"__temp_ in depends_on: {d}"

    def test_whitespace_normalized_in_fragments(self):
        queries = [
            "SELECT\r\n\t\tcol_a,\r\n\t\tcol_b\r\n\tINTO #stage\r\n\tFROM table1",
            "SELECT * FROM #stage",
        ]
        result = parse_extracted_queries(queries)
        staging_cte = [c for c in result.ctes if c.name == "stage"][0]
        # Fragment should not contain \r or \t
        assert "\r" not in staging_cte.sql_fragment
        assert "\t" not in staging_cte.sql_fragment
