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


def normalize_sql_whitespace(sql: str) -> str:
    """Normalize whitespace in SQL text for clean storage and readability.

    Raw SQL from ScriptDom extraction preserves original formatting with
    \\r\\n\\t characters. This normalizes to clean, readable SQL.
    """
    sql = sql.replace('\r\n', '\n').replace('\r', '\n')
    sql = re.sub(r'[ \t]+', ' ', sql)
    sql = '\n'.join(line.strip() for line in sql.split('\n') if line.strip())
    return sql


def _clean_extracted_query(sql: str) -> str:
    """Light cleanup on an individual extracted query before sqlglot parsing.

    Unlike the old _preprocess_simple which tried to clean entire procs,
    this only cleans individual query statements that the extractor already
    isolated. Much safer because the SQL is already a single SELECT/WITH.
    """
    # Remove OPTION(...) query hints
    sql = re.sub(r"\bOPTION\s*\([^)]*\)\s*;?", "", sql, flags=re.IGNORECASE)

    # Remove trailing semicolons
    sql = sql.rstrip().rstrip(";").rstrip()

    # Remove inline comments that break parsing (but keep block comments)
    # Only remove single-line comments at the END of lines, not comment-only lines
    sql = re.sub(r"--[^\n]*$", "", sql, flags=re.MULTILINE)

    # Remove block comments
    sql = re.sub(r"/\*[\s\S]*?\*/", "", sql)

    # Strip #temp table names to plain names (sqlglot may not handle # prefix)
    sql = re.sub(r"#(\w+)", r"__temp_\1__", sql)

    return sql.strip()


def _parse_single_statement(sql: str, dialect: str) -> ParsedSQL | None:
    """Parse a single SQL statement and extract structure.

    Applies light cleanup before parsing. Returns ParsedSQL or None if parsing fails.
    """
    sql = _clean_extracted_query(sql)

    if not sql:
        return None

    try:
        parsed = sqlglot.parse_one(sql, dialect=dialect)
    except (sqlglot.errors.ParseError, sqlglot.errors.TokenError):
        return None

    result = ParsedSQL(normalized_sql=sql)

    # Extract CTEs
    for cte in parsed.find_all(exp.CTE):
        cte_name = cte.alias
        cte_body = cte.this
        col_refs = _extract_column_refs(cte_body)

        all_table_refs = [t.name for t in cte_body.find_all(exp.Table)]
        cte_names = [c.alias for c in parsed.find_all(exp.CTE)]
        depends_on = [t for t in all_table_refs if t in cte_names]
        physical_tables = [t for t in all_table_refs if t not in cte_names]

        result.ctes.append(CTEInfo(
            name=cte_name,
            sql_fragment=cte_body.sql(dialect=dialect),
            column_refs=col_refs,
            table_refs=physical_tables,
            depends_on=depends_on,
        ))

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


def _extract_temp_table_name(sql: str) -> str | None:
    """Extract the #temp table name from a SELECT...INTO #temp statement."""
    match = re.search(r"\bINTO\s+#(\w+)", sql, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def parse_extracted_queries(queries: list[str], dialect: str = "tsql") -> ParsedSQL:
    """Parse pre-extracted SQL queries and merge into a single ParsedSQL.

    This is the core multi-statement merging logic. Call this when you already
    have individual SQL queries (e.g., from ScriptDom via pythonnet or the
    microservice). Handles:
    - Single query: parse directly
    - Multiple queries: merge CTEs, track temp table dependencies

    Args:
        queries: List of individual SQL queries (already extracted).
        dialect: SQL dialect for sqlglot parsing.

    Returns:
        ParsedSQL with merged CTEs, tables, and columns.

    Raises:
        ValueError: If no queries provided or none parse successfully.
    """
    if not queries:
        raise ValueError("Failed to parse SQL: no SQL queries found in input")

    # Single query — parse directly
    if len(queries) == 1:
        result = _parse_single_statement(queries[0], dialect)
        if result:
            return result
        raise ValueError(f"Failed to parse SQL: {queries[0][:100]}...")

    # Multiple queries — parse each individually, merge results
    logger.info("Parsing %d extracted queries individually", len(queries))

    all_ctes: list[CTEInfo] = []
    all_final_tables: list[str] = []
    all_final_cte_refs: list[str] = []
    all_final_columns: list[ColumnRef] = []
    temp_table_names: set[str] = set()
    parsed_count = 0

    for i, query in enumerate(queries):
        temp_name = _extract_temp_table_name(query)
        if temp_name:
            temp_table_names.add(temp_name)

        result = _parse_single_statement(query, dialect)
        if result is None:
            logger.warning("Failed to parse query %d/%d: %s...", i + 1, len(queries), query[:60])
            continue

        parsed_count += 1

        # Build lookup for temp table matching: both raw name and __temp_X__ form
        # _clean_extracted_query() converts #name → __temp_name__, so sqlglot sees
        # __temp_name__ in table refs. We need to match both forms.
        temp_name_variants = set()
        for tn in temp_table_names:
            temp_name_variants.add(tn)
            temp_name_variants.add(f"__temp_{tn}__")

        def _is_temp_ref(table_name: str) -> bool:
            """Check if a table reference is actually a temp table."""
            return table_name in temp_name_variants

        def _temp_canonical(table_name: str) -> str:
            """Get the canonical temp table name (without __temp_ prefix)."""
            if table_name.startswith("__temp_") and table_name.endswith("__"):
                return table_name[7:-2]
            return table_name

        if temp_name:
            # Temp table query → treat as CTE definition
            clean_fragment = normalize_sql_whitespace(query)
            fragment = clean_fragment[:500] if len(clean_fragment) > 500 else clean_fragment
            all_table_refs = list(result.final_select_tables)
            # Filter out self-reference (INTO #X creates __temp_X__ as a table ref)
            self_variants = {temp_name, f"__temp_{temp_name}__"}
            all_table_refs = [t for t in all_table_refs if t not in self_variants]
            cte_table_refs = [t for t in all_table_refs if not _is_temp_ref(t)]
            cte_depends = [_temp_canonical(t) for t in all_table_refs if _is_temp_ref(t)]

            all_ctes.append(CTEInfo(
                name=temp_name,
                sql_fragment=fragment,
                column_refs=result.final_select_columns,
                table_refs=cte_table_refs,
                depends_on=cte_depends,
            ))
            for cte in result.ctes:
                all_ctes.append(cte)
        else:
            # Terminal SELECT
            for cte in result.ctes:
                all_ctes.append(cte)
            for t in result.final_select_tables:
                if t not in all_final_tables:
                    all_final_tables.append(t)
            for t in result.final_select_cte_refs:
                if t not in all_final_cte_refs:
                    all_final_cte_refs.append(t)
            all_final_columns.extend(result.final_select_columns)

    if parsed_count == 0:
        raise ValueError(f"Failed to parse SQL: none of {len(queries)} extracted queries parsed successfully")

    # Reclassify temp table refs in final tables
    # Check both raw name and __temp_X__ form since _clean_extracted_query
    # converts #name → __temp_name__
    temp_final_variants = set()
    for tn in temp_table_names:
        temp_final_variants.add(tn)
        temp_final_variants.add(f"__temp_{tn}__")

    for t in all_final_tables[:]:
        if t in temp_final_variants:
            all_final_tables.remove(t)
            # Store canonical name (without __temp_ prefix) in cte_refs
            canonical = t[7:-2] if t.startswith("__temp_") and t.endswith("__") else t
            if canonical not in all_final_cte_refs:
                all_final_cte_refs.append(canonical)

    merged = ParsedSQL(
        ctes=all_ctes,
        final_select_tables=all_final_tables,
        final_select_cte_refs=all_final_cte_refs,
        final_select_columns=all_final_columns,
        normalized_sql=";\n".join(queries),
    )

    logger.info(
        "Merged %d/%d queries: %d CTEs, %d final tables, %d CTE refs",
        parsed_count, len(queries),
        len(merged.ctes), len(merged.final_select_tables), len(merged.final_select_cte_refs),
    )
    return merged


def parse_sql(sql: str, dialect: str = "tsql", llm_backend=None,
              scriptdom_url: str = "") -> ParsedSQL:
    """Parse raw SQL and extract structure. Handles extraction + parsing.

    Extraction strategy:
    1. ScriptDom (if microservice is running) — 100% accurate T-SQL parsing
    2. sqlparse-based extractor — fallback if ScriptDom unavailable

    For pre-extracted queries (e.g., from ScriptDom via pythonnet in Fabric),
    use parse_extracted_queries() directly instead.

    Args:
        sql: The raw SQL statement or stored procedure to parse.
        dialect: SQL dialect (default: tsql for SQL Server / Fabric).
        llm_backend: Optional LLM backend (not used in current architecture).
        scriptdom_url: URL of ScriptDom microservice (default: tries localhost:5111).

    Returns:
        ParsedSQL with extracted CTEs, tables, and columns.
    """
    queries = None

    # Try ScriptDom first (production-grade, 100% accurate for T-SQL)
    if scriptdom_url or dialect == "tsql":
        try:
            from src.parser.scriptdom_extractor import ScriptDomExtractor
            url = scriptdom_url or "http://localhost:5111"
            extractor = ScriptDomExtractor(url)
            if extractor.is_healthy():
                queries = extractor.extract_sql_strings(sql)
                logger.info("ScriptDom extracted %d queries", len(queries))
        except Exception as e:
            logger.info("ScriptDom not available (%s), falling back to sqlparse", e)

    # Fallback to sqlparse-based extractor
    if queries is None:
        from src.parser.sql_extractor import extract_queries as sqlparse_extract
        queries = sqlparse_extract(sql)
        logger.info("sqlparse extracted %d queries", len(queries))

    return parse_extracted_queries(queries, dialect)


def _extract_column_refs(node: exp.Expression) -> list[ColumnRef]:
    """Extract column references from an expression node."""
    refs = []
    for col in node.find_all(exp.Column):
        table = col.table if col.table else None
        refs.append(ColumnRef(table=table, column=col.name))
    return refs
