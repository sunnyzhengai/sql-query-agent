"""Parse SQL into structured representations for graph building.

Uses sqlglot to parse SQL and extract:
- CTE structure (transformation nodes)
- Table/column references (technical nodes)
- SQL fragments (minimal logic snippets, NOT full SQL blobs)

For multi-statement stored procedures (temp tables, multiple SELECTs),
uses proc_normalize to convert to a single CTE-based SELECT first.
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
    final_select_tables: list[str] = field(default_factory=list)    # physical tables only
    final_select_cte_refs: list[str] = field(default_factory=list)  # CTEs referenced by final SELECT
    final_select_columns: list[ColumnRef] = field(default_factory=list)
    normalized_sql: str = ""  # the SQL after normalization (for debugging/review)


def _is_multi_statement(sql: str) -> bool:
    """Heuristic: does this SQL look like a multi-statement stored procedure?

    Checks for temp table patterns (SELECT INTO #, #table references,
    DROP TABLE #) which indicate multi-statement staging.
    """
    return bool(re.search(r'(?:INTO\s+#|FROM\s+#|JOIN\s+#|DROP\s+TABLE\s+.*#)\w+', sql, re.IGNORECASE))


def _preprocess_simple(sql: str) -> str:
    """Lightweight preprocessing for simple single-statement queries.

    Handles: GO, USE, SET, CREATE PROCEDURE (no params or simple params),
    DECLARE blocks, @variables, ;WITH, DROP TABLE IF EXISTS.
    """
    # Remove GO batch separators
    sql = re.sub(r'^\s*GO\s*$', '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove USE [database]
    sql = re.sub(r'^\s*USE\s+\[?\w+\]?\s*;?\s*$', '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove SET statements
    sql = re.sub(r'^\s*SET\s+[\w\s]+(?:ON|OFF|UNCOMMITTED|COMMITTED)\s*;?\s*$',
                 '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove DROP TABLE IF EXISTS
    sql = re.sub(r'^\s*DROP\s+TABLE\s+IF\s+EXISTS\s+#?\w+\s*;?\s*$',
                 '', sql, flags=re.MULTILINE | re.IGNORECASE)

    # Remove CREATE PROCEDURE ... AS (with optional multi-line params)
    sql = re.sub(
        r'CREATE\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+[\[\]\w.]+\s*(?:\([\s\S]*?\))?\s*AS\b',
        '', sql, flags=re.IGNORECASE
    )

    # Remove DECLARE blocks (before @variable replacement)
    sql = re.sub(
        r'\bDECLARE\s+@\w+[\s\S]*?(?=\bWITH\b|\bSELECT\b|\bDROP\b)',
        '', sql, flags=re.IGNORECASE
    )

    # Replace @variables with placeholders
    sql = re.sub(r'@(\w+)', r"'__var_\1__'", sql)

    # ;WITH -> WITH
    sql = re.sub(r';\s*WITH\b', 'WITH', sql, flags=re.IGNORECASE)

    # Remove OPTION(...) query hints
    sql = re.sub(r'\bOPTION\s*\([^)]*\)\s*;?', '', sql, flags=re.IGNORECASE)

    # Remove INSERT INTO #temp VALUES(...)
    sql = re.sub(r'\bINSERT\s+INTO\s+#\w+\s+VALUES\s*\([^)]*\)\s*;?', '', sql, flags=re.IGNORECASE)

    # Remove CREATE INDEX on temp tables
    sql = re.sub(
        r'\bCREATE\s+(?:UNIQUE\s+)?(?:CLUSTERED\s+|NONCLUSTERED\s+)?INDEX\s+\w+\s+ON\s+#\w+\s*\([^)]*\)\s*;?',
        '', sql, flags=re.IGNORECASE
    )

    # Remove PRINT statements
    sql = re.sub(r'\bPRINT\s*\([^)]*\)\s*;?', '', sql, flags=re.IGNORECASE)

    # Remove IF ... BEGIN ... END blocks (parameter defaulting)
    sql = re.sub(r'\bIF\b[^;]*\bBEGIN\b[\s\S]*?\bEND\s*;?', '', sql, flags=re.IGNORECASE)

    return sql.strip()


def parse_sql(sql: str, dialect: str = "tsql", llm_backend=None) -> ParsedSQL:
    """Parse a SQL statement and extract structure.

    Extraction strategy (in order):
    1. proc_normalize — deterministic, handles temp tables → CTEs
    2. Simple regex preprocessing — lightweight fallback
    3. LLM extraction — if llm_backend provided, uses LLM to extract clean SQL
       when both deterministic methods fail

    Args:
        sql: The SQL statement to parse (can be a full stored procedure).
        dialect: SQL dialect (default: tsql for SQL Server / Fabric).
        llm_backend: Optional LLM backend for extraction fallback.
            Pass an object that implements generate(prompt) -> str.

    Returns:
        ParsedSQL with extracted CTEs, tables, and columns.
    """
    normalized_sql = ""
    parse_error = None

    if _is_multi_statement(sql):
        # Multi-statement procedure: use proc_normalize to convert temp tables to CTEs
        logger.info("Detected multi-statement procedure, using proc_normalize")
        from src.parser.proc_normalize import select_into_to_cte, ProcNotViewShaped
        try:
            normalized_sql = select_into_to_cte(sql, dialect=dialect, emit_create_view=False)
            logger.info("proc_normalize succeeded (%d chars)", len(normalized_sql))
        except ProcNotViewShaped as e:
            logger.warning("Proc not view-shaped (%s: %s), falling back to simple parse", e.reason, e.detail)
            normalized_sql = _preprocess_simple(sql)
        except Exception as e:
            logger.warning("proc_normalize failed (%s), falling back to simple parse", e)
            normalized_sql = _preprocess_simple(sql)
    else:
        # Simple query: lightweight preprocessing
        normalized_sql = _preprocess_simple(sql)
        logger.info("Simple query, preprocessed (%d chars)", len(normalized_sql))

    # Parse the normalized SQL
    try:
        parsed = sqlglot.parse_one(normalized_sql, dialect=dialect)
    except sqlglot.errors.ParseError as e:
        parse_error = e
        parsed = None

    # If deterministic parsing failed and we have an LLM backend, try LLM extraction
    if parsed is None and llm_backend is not None:
        logger.info("Deterministic parse failed, trying LLM extraction")
        try:
            from src.parser.llm_extractor import extract_sql
            llm_sql = extract_sql(sql, llm_backend)
            normalized_sql = llm_sql
            parsed = sqlglot.parse_one(llm_sql, dialect=dialect)
            logger.info("LLM extraction succeeded (%d chars)", len(llm_sql))
        except Exception as llm_e:
            logger.error("LLM extraction also failed: %s", llm_e)
            # Fall through to raise the original error

    if parsed is None:
        logger.error("Failed to parse SQL: %s", parse_error)
        raise ValueError(f"Failed to parse SQL: {parse_error}") from parse_error

    result = ParsedSQL(normalized_sql=normalized_sql)

    # Extract CTEs
    for cte in parsed.find_all(exp.CTE):
        cte_name = cte.alias
        cte_body = cte.this

        col_refs = _extract_column_refs(cte_body)

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
    cte_name_set = {c.name for c in result.ctes}
    main_select = parsed.find(exp.Select)
    if main_select:
        for table in parsed.find_all(exp.Table):
            if table.name in cte_name_set:
                if table.name not in result.final_select_cte_refs:
                    result.final_select_cte_refs.append(table.name)
            else:
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
