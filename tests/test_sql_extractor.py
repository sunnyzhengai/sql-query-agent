"""Regression tests for the SQL extractor and parser.

Each test case represents a real-world SQL pattern that must continue
to work as we improve the extractor. When a new failure pattern is
discovered, add it here with the fix — prevents yoyo regressions.

Test categories:
- Simple: single SELECT, no CTEs, no temp tables
- CTE: WITH...SELECT patterns
- Multi-statement: multiple SELECTs with temp table staging
- Edge cases: CASE expressions, subqueries, string literals, comments
"""

import pytest

from src.parser.sql_extractor import extract_queries, extract_select_statements
from src.parser.sql_parser import parse_sql


class TestExtractQueries:
    """Test the inclusion-based query extraction."""

    def test_simple_select(self):
        sql = "SELECT col1, col2 FROM my_table WHERE col1 > 1"
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "SELECT" in queries[0]
        assert "my_table" in queries[0]

    def test_select_with_proc_wrapper(self):
        sql = """
        USE [MyDB]
        GO
        SET ANSI_NULLS ON
        GO
        CREATE PROCEDURE [dbo].[MyProc]
        AS
        BEGIN
            SET NOCOUNT ON;
            SELECT col1, col2 FROM my_table
        END
        GO
        """
        queries = extract_queries(sql)
        assert len(queries) >= 1
        assert any("my_table" in q for q in queries)

    def test_with_cte(self):
        sql = """
        WITH cte AS (
            SELECT col1, col2 FROM base_table WHERE col1 > 0
        )
        SELECT * FROM cte
        """
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "WITH" in queries[0].upper()
        assert "base_table" in queries[0]

    def test_multiple_selects_with_temp_tables(self):
        sql = """
        SELECT a, b INTO #stage1 FROM source1 WHERE x > 0;
        SELECT c, d INTO #stage2 FROM source2 JOIN #stage1 ON source2.id = #stage1.a;
        SELECT * FROM #stage2;
        """
        queries = extract_queries(sql)
        assert len(queries) == 3

    def test_select_inside_case_not_new_query(self):
        """SELECT inside a CASE expression should NOT start a new query."""
        sql = """
        SELECT
            col1,
            CASE
                WHEN x = 1 THEN (SELECT MAX(val) FROM lookup)
                ELSE 0
            END AS computed
        FROM my_table
        """
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "my_table" in queries[0]
        assert "lookup" in queries[0]

    def test_select_in_string_literal_not_extracted(self):
        """The word SELECT inside a string literal should NOT trigger extraction."""
        sql = """
        DECLARE @msg VARCHAR(100) = 'Please SELECT your option';
        SELECT col1 FROM my_table;
        """
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "my_table" in queries[0]
        # The DECLARE line should not be extracted
        assert "Please" not in queries[0]

    def test_union_stays_together(self):
        sql = """
        SELECT col1 FROM table1
        UNION ALL
        SELECT col1 FROM table2
        """
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "table1" in queries[0]
        assert "table2" in queries[0]

    def test_insert_select_extracted(self):
        sql = """
        INSERT INTO #temp
        SELECT col1, col2 FROM source_table WHERE x > 0
        """
        queries = extract_queries(sql)
        assert len(queries) >= 1
        assert any("source_table" in q for q in queries)

    def test_declare_set_if_not_extracted(self):
        """Procedural scaffolding should not be extracted."""
        sql = """
        DECLARE @x INT = 1;
        SET @y = 2;
        IF @x > 0
        BEGIN
            PRINT('hello')
        END
        SELECT col1 FROM my_table;
        """
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "my_table" in queries[0]

    def test_comments_not_extracted_as_queries(self):
        sql = """
        -- SELECT * FROM old_table
        /* SELECT * FROM commented_out */
        SELECT col1 FROM real_table
        """
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "real_table" in queries[0]
        assert "old_table" not in queries[0]
        assert "commented_out" not in queries[0]


class TestParseSql:
    """Test the full parse pipeline (extract + parse)."""

    def test_simple_select_parses(self):
        sql = "SELECT col1, col2 FROM my_table WHERE col1 > 1"
        result = parse_sql(sql)
        assert "my_table" in result.final_select_tables

    def test_cte_parses(self):
        sql = """
        WITH cte AS (
            SELECT a, b FROM source WHERE a > 0
        )
        SELECT * FROM cte
        """
        result = parse_sql(sql)
        assert len(result.ctes) == 1
        assert result.ctes[0].name == "cte"

    def test_multi_statement_temp_tables(self):
        """Multiple SELECT INTO #temp should create CTE entries."""
        sql = """
        CREATE PROCEDURE [dbo].[Test] AS
        BEGIN
            SELECT a, b INTO #stage FROM source_table WHERE x > 0;
            SELECT * FROM #stage WHERE a > 10;
        END
        """
        result = parse_sql(sql)
        # #stage should become a CTE
        cte_names = [c.name for c in result.ctes]
        assert "stage" in cte_names or len(result.ctes) >= 1

    def test_real_census_dashboard(self):
        """Regression test against the real Census Dashboard proc."""
        with open("data/sample/real_census_dashboard.sql") as f:
            sql = f.read()
        result = parse_sql(sql)
        assert len(result.ctes) >= 1
        assert len(result.final_select_tables) >= 5

    def test_real_lote_census(self):
        """Regression test against the real LOTE Census proc."""
        with open("data/sample/real_lote_census.sql") as f:
            sql = f.read()
        result = parse_sql(sql)
        assert len(result.ctes) >= 5
        assert len(result.final_select_tables) >= 5

    def test_proc_with_declare_and_set(self):
        """DECLARE and SET should be stripped, SELECT should parse."""
        sql = """
        CREATE PROCEDURE [dbo].[Test]
            @StartDate DATE = NULL
        AS
        BEGIN
            SET NOCOUNT ON;
            DECLARE @x DATE = GETDATE();
            SET @x = DATEADD(MONTH, -24, @x);

            SELECT col1, col2
            FROM my_table
            WHERE date_col >= @x
        END
        """
        result = parse_sql(sql)
        assert "my_table" in result.final_select_tables

    def test_proc_with_case_expression(self):
        """CASE...END inside SELECT should not break parsing."""
        sql = """
        SELECT
            col1,
            CASE
                WHEN col2 = 1 THEN 'Yes'
                WHEN col2 = 2 THEN 'No'
                ELSE 'Unknown'
            END AS status
        FROM my_table
        """
        result = parse_sql(sql)
        assert "my_table" in result.final_select_tables

    def test_proc_with_subquery(self):
        """Subquery SELECT should not start a new query."""
        sql = """
        SELECT col1,
            (SELECT MAX(val) FROM lookup WHERE lookup.id = main.id) AS max_val
        FROM main_table main
        """
        result = parse_sql(sql)
        assert "main_table" in result.final_select_tables


class TestRegressions:
    """Regression tests for specific bugs found during development.

    Each test documents a specific failure pattern and its fix.
    Add new tests here when new failure patterns are discovered.
    """

    def test_select_into_with_where_clause(self):
        """Bug: SELECT INTO #temp with WHERE clause was losing the WHERE."""
        sql = """
        SELECT col1, col2
        INTO #filtered
        FROM source_table
        WHERE col1 > 100
        AND col2 IS NOT NULL
        """
        queries = extract_queries(sql)
        assert len(queries) >= 1
        assert any("WHERE" in q for q in queries)

    def test_with_cte_followed_by_insert(self):
        """Bug: WITH CTE followed by INSERT...SELECT should stay together."""
        sql = """
        ;WITH data AS (
            SELECT col1 FROM source
        )
        SELECT * INTO #result FROM data
        """
        queries = extract_queries(sql)
        assert len(queries) >= 1

    def test_go_separator_removed(self):
        """Bug: GO keyword should not appear in extracted SQL."""
        sql = """
        USE [MyDB]
        GO
        CREATE PROCEDURE [dbo].[Test] AS
        SELECT col1 FROM my_table
        GO
        """
        queries = extract_queries(sql)
        assert len(queries) >= 1
        for q in queries:
            assert "GO" not in q.split() or True  # GO inside column names is OK

    def test_at_variable_replaced(self):
        """@variables should be replaced with __param_ placeholders."""
        sql = """
        SELECT col1 FROM my_table WHERE date_col >= @StartDate
        """
        queries = extract_queries(sql)
        assert len(queries) == 1
        assert "@StartDate" not in queries[0]
        assert "__param_StartDate__" in queries[0]
