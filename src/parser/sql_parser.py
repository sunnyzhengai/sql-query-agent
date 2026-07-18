"""Parse SQL into structured representations for graph building.

Uses sqlglot to parse SQL and extract:
- CTE structure (transformation nodes)
- Table/column references (technical nodes)
- SQL fragments (minimal logic snippets, NOT full SQL blobs)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)


@dataclass
class ColumnRef:
    table: str | None
    column: str


@dataclass
class CTEInfo:
    """A single CTE extracted from a SQL statement."""

    name: str
    sql_fragment: str
    column_refs: list[ColumnRef] = field(default_factory=list)
    table_refs: list[str] = field(default_factory=list)  # actual table names (not aliases, not CTEs)
    depends_on: list[str] = field(default_factory=list)  # other CTE names


@dataclass
class ParsedSQL:
    """Result of parsing a SQL statement."""

    ctes: list[CTEInfo] = field(default_factory=list)
    final_select_tables: list[str] = field(default_factory=list)
    final_select_columns: list[ColumnRef] = field(default_factory=list)


def _preprocess_tsql(sql: str) -> str:
    """Clean T-SQL-specific syntax that sqlglot can't handle directly.

    Handles:
    - GO batch separators
    - SET statements (NOCOUNT, ANSI_NULLS, QUOTED_IDENTIFIER, TRANSACTION ISOLATION)
    - DECLARE @variable statements
    - Leading semicolons before WITH
    - CREATE/ALTER PROCEDURE wrappers (with or without parameters)
    - USE [database] statements
    - DROP TABLE IF EXISTS statements
    - SELECT ... INTO #temp_table -> SELECT ... (strips INTO clause)
    - Comment blocks
    """
    # Remove GO batch separators (standalone on a line)
    sql = re.sub(r'^\s*GO\s*$', '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove USE [database] statements
    sql = re.sub(r'^\s*USE\s+\[?\w+\]?\s*;?\s*$', '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove SET statements (handles multi-word like SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED)
    sql = re.sub(r'^\s*SET\s+[\w\s]+(?:ON|OFF|UNCOMMITTED|COMMITTED)\s*;?\s*$',
                 '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove DROP TABLE IF EXISTS statements
    sql = re.sub(r'^\s*DROP\s+TABLE\s+IF\s+EXISTS\s+#?\w+\s*;?\s*$',
                 '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove CREATE/ALTER PROCEDURE ... AS wrapper (with optional multi-line parameter block)
    # MUST run before @variable replacement
    sql = re.sub(
        r'CREATE\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+[\[\]\w.]+\s*(?:\([\s\S]*?\))?\s*AS\b',
        '', sql, flags=re.IGNORECASE
    )

    # Remove DECLARE @variable blocks (everything from DECLARE to the line before WITH/SELECT/DROP)
    # MUST run before @variable replacement
    sql = re.sub(
        r'\bDECLARE\s+@\w+[\s\S]*?(?=\bWITH\b|\bSELECT\b|\bDROP\b)',
        '', sql, flags=re.IGNORECASE
    )

    # Replace @variables with placeholder literals so parser doesn't choke
    sql = re.sub(r'@(\w+)', r"'__var_\1__'", sql)

    # Remove leading semicolon before WITH (T-SQL style ;WITH)
    sql = re.sub(r';\s*WITH\b', 'WITH', sql, flags=re.IGNORECASE)

    # Strip INTO #temp_table clauses (SELECT ... INTO #foo FROM -> SELECT ... FROM)
    sql = re.sub(r'\bINTO\s+#\w+\s*\n?', '', sql, flags=re.IGNORECASE)

    # Replace #temp_table references with regular table names (strip the #)
    sql = re.sub(r'#(\w+)', r'__temp_\1', sql)

    # Strip leading/trailing whitespace
    sql = sql.strip()

    return sql


def parse_sql(sql: str, dialect: str = "tsql") -> ParsedSQL:
    """Parse a SQL statement and extract structure.

    Handles real-world T-SQL including stored procedures, DECLARE statements,
    GO separators, and @variables.

    Args:
        sql: The SQL statement to parse.
        dialect: SQL dialect (default: tsql for SQL Server / Fabric).

    Returns:
        ParsedSQL with extracted CTEs, tables, and columns.
    """
    sql = _preprocess_tsql(sql)
    logger.info("Preprocessed SQL (%d chars)", len(sql))

    try:
        parsed = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError as e:
        logger.error("Failed to parse SQL: %s", e)
        raise ValueError(f"Failed to parse SQL: {e}") from e

    result = ParsedSQL()

    # Extract CTEs
    for cte in parsed.find_all(exp.CTE):
        cte_name = cte.alias
        cte_body = cte.this

        # Extract column references from the CTE body
        col_refs = _extract_column_refs(cte_body)

        # Find dependencies on other CTEs and actual table references
        all_table_refs = [t.name for t in cte_body.find_all(exp.Table)]
        cte_names = [c.alias for c in parsed.find_all(exp.CTE)]
        depends_on = [t for t in all_table_refs if t in cte_names]
        physical_tables = [t for t in all_table_refs if t not in cte_names]

        result.ctes.append(
            CTEInfo(
                name=cte_name,
                sql_fragment=cte_body.sql(dialect=dialect),
                column_refs=col_refs,
                table_refs=physical_tables,
                depends_on=depends_on,
            )
        )

    # Extract final SELECT table/column references
    # (the main query after all CTEs)
    main_select = parsed.find(exp.Select)
    if main_select:
        # Get tables from the final select (excluding CTE-defined tables)
        for table in parsed.find_all(exp.Table):
            if table.name not in [c.name for c in result.ctes]:
                if table.name not in result.final_select_tables:
                    result.final_select_tables.append(table.name)

        result.final_select_columns = _extract_column_refs(main_select)

    return result


def _extract_column_refs(node: exp.Expression) -> list[ColumnRef]:
    """Extract column references from an expression node."""
    refs = []
    for col in node.find_all(exp.Column):
        table = col.table if col.table else None
        refs.append(ColumnRef(table=table, column=col.name))
    return refs
