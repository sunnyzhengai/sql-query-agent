"""Unit tests for SQL parser — deterministic: SQL in -> structured output."""

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
        import pytest

        with pytest.raises(ValueError, match="Failed to parse"):
            parse_sql("NOT VALID SQL !!!")
