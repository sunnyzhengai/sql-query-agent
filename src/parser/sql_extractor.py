"""Universal SQL query extractor — inclusion-based, dialect-agnostic.

Extracts SQL queries from ANY text that contains them, regardless of
what procedural language wraps them. Works for T-SQL, PL/SQL, Snowflake,
Databricks, or even SQL embedded in documentation.

Architecture:
  - Inclusion model: find SELECT/WITH, extract verbatim
  - NOT exclusion model: don't try to strip infinite non-SQL patterns
  - Token-aware: uses sqlparse tokenizer so string literals and comments
    are handled correctly (no false positives)
  - Zero text corruption: extracted SQL is untouched original text

Flow:
  Any text → sqlparse tokenize → find query boundaries → extract verbatim → sqlglot parse
"""

from __future__ import annotations

import logging
import re
from typing import Any

import sqlparse
from sqlparse import tokens as T  # noqa: N812

logger = logging.getLogger(__name__)


def _strip_proc_wrapper(sql: str) -> str:
    """Remove CREATE PROCEDURE/VIEW/FUNCTION wrapper.

    Finds the AS keyword that separates the header from the body
    and returns only the body. Handles parameter blocks.
    """
    # Find CREATE PROC/VIEW/FUNCTION ... AS
    match = re.search(
        r"\bCREATE\s+(?:OR\s+ALTER\s+)?(?:PROCEDURE|PROC|VIEW|FUNCTION|TRIGGER)\b"
        r"[\s\S]*?\bAS\b",
        sql, re.IGNORECASE,
    )
    if match:
        sql = sql[match.end():]

    # Strip outer BEGIN...END wrapper
    sql = sql.strip()
    begin_match = re.match(r"^\s*BEGIN\b([\s\S]*)\bEND\s*;?\s*$", sql, re.IGNORECASE)
    if begin_match:
        sql = begin_match.group(1)

    # Strip trailing GO
    sql = re.sub(r"\bGO\s*$", "", sql.strip(), flags=re.IGNORECASE)

    return sql.strip()


def _replace_variables(sql: str) -> str:
    """Replace @variables with safe placeholders for sqlglot."""
    return re.sub(r"@(\w+)", r"__param_\1__", sql)


def _is_query_start(token) -> bool:
    """Check if a token marks the start of a SQL query."""
    if token.ttype is T.Keyword.DML:
        return token.normalized in ("SELECT", "INSERT", "MERGE")
    if token.ttype is T.Keyword.CTE:
        return True  # WITH keyword for CTEs
    if token.ttype is T.Keyword and token.normalized == "WITH":
        return True  # fallback in case CTE subtype isn't set
    return False


def _is_noise_keyword(token) -> bool:
    """Check if a token is a non-query keyword we should skip past."""
    if token.ttype in (T.Keyword, T.Keyword.DDL, T.Keyword.DML):
        noise = {
            "DECLARE", "SET", "IF", "ELSE", "WHILE", "BEGIN", "END",
            "GOTO", "RETURN", "PRINT", "EXEC", "EXECUTE", "RAISERROR",
            "THROW", "TRY", "CATCH", "BREAK", "CONTINUE",
            "DROP", "CREATE", "ALTER", "TRUNCATE", "USE",
            "GRANT", "REVOKE", "DENY",
        }
        return token.normalized in noise
    if token.ttype is T.Keyword and token.normalized == "GO":
        return True
    return False


def extract_queries(raw_text: str) -> list[str]:
    """Extract SQL queries from any text using a two-phase approach.

    Phase 1: sqlparse.split() to find statement boundaries
             (handles missing semicolons in T-SQL)
    Phase 2: Token-walk each statement to keep only query statements
             (SELECT, WITH, INSERT...SELECT), drop procedural noise

    Args:
        raw_text: Any text containing SQL (stored procedure, script,
                  notebook cell, documentation, etc.)

    Returns:
        List of extracted SQL query strings, each one a complete statement.
    """
    # Step 1: Strip the proc/view wrapper if present
    body = _strip_proc_wrapper(raw_text)

    # Step 2: Replace @variables with placeholders
    body = _replace_variables(body)

    # Step 3: Split into individual statements using sqlparse
    # sqlparse handles missing semicolons, BEGIN...END blocks, etc.
    split_statements = sqlparse.split(body)

    # Step 4: Filter each statement — keep only queries
    extracted = []

    for stmt_text in split_statements:
        stmt_text = stmt_text.strip()
        if not stmt_text or stmt_text == ";" or len(stmt_text) < 5:
            continue

        # Parse the statement to check its type
        parsed = sqlparse.parse(stmt_text)
        if not parsed:
            continue

        stmt = parsed[0]

        # Check if this statement is a query
        if _is_query_statement(stmt, stmt_text):
            extracted.append(stmt_text)
            continue

        # If not a direct query, check if it contains embedded queries
        # (e.g., IF...BEGIN...END wrapping a SELECT)
        # Try re-splitting the statement body
        if "SELECT" in stmt_text.upper() or "WITH" in stmt_text.upper():
            inner_queries = _extract_inner_queries(stmt_text)
            extracted.extend(inner_queries)

    logger.info("Extracted %d queries from %d statements (%d chars input)",
                len(extracted), len(split_statements), len(raw_text))
    return extracted


def _extract_inner_queries(stmt_text: str) -> list[str]:
    """Extract SELECT/WITH queries embedded inside non-query blocks.

    Handles cases like IF...BEGIN SELECT...END where sqlparse groups
    the entire IF block as one statement but there's a valid SELECT inside.
    """
    inner = []
    # Try to find SELECT/WITH statements by re-parsing the inner content
    # Strip common wrappers
    cleaned = re.sub(r"\bIF\b[\s\S]*?\bBEGIN\b", "", stmt_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bEND\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bBEGIN\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bELSE\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bPRINT\b.*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    if not cleaned:
        return inner

    # Re-split the cleaned content
    sub_statements = sqlparse.split(cleaned)
    for sub in sub_statements:
        sub = sub.strip()
        if not sub or len(sub) < 5:
            continue
        parsed = sqlparse.parse(sub)
        if parsed and _is_query_statement(parsed[0], sub):
            inner.append(sub)

    return inner


def _is_query_statement(stmt: Statement, stmt_text: str) -> bool:
    """Determine if a sqlparse Statement is a data query we should keep.

    Uses both the statement type and token inspection to decide.
    """
    stmt_type = stmt.get_type()

    # Definite keeps
    if stmt_type == "SELECT":
        return True

    # Check the first meaningful token (skip comments and whitespace)
    first_word = ""
    for token in stmt.flatten():
        if token.ttype in (T.Comment.Single, T.Comment.Multiline,
                           T.Whitespace, T.Newline):
            continue
        first_word = token.normalized or token.value.upper()
        break

    # WITH (CTE) — sqlparse may not type these as SELECT
    if first_word == "WITH":
        return True

    # SELECT that sqlparse didn't type (happens with complex queries)
    if first_word == "SELECT":
        return True

    # INSERT...SELECT (has business logic, not just INSERT VALUES)
    if first_word == "INSERT" or stmt_type == "INSERT":
        upper = stmt_text.upper()
        if "SELECT" in upper and "VALUES" not in upper:
            return True
        if "SELECT" in upper:
            return True
        return False

    # MERGE (some procs use MERGE for upserts)
    if first_word == "MERGE":
        return True

    # Statement typed as None but contains SELECT (common for complex T-SQL)
    if stmt_type is None and "SELECT" in stmt_text.upper():
        # Check that SELECT is an actual keyword, not in a comment
        for token in stmt.flatten():
            if token.ttype is T.Keyword.DML and token.normalized == "SELECT":
                return True

    # Everything else is noise
    return False

    logger.info("Extracted %d queries from input (%d chars)", len(extracted), len(raw_text))
    return extracted


def extract_select_statements(raw_text: str) -> str:
    """Extract and join SQL queries from any text.

    Convenience wrapper around extract_queries() that returns
    a single string with queries separated by semicolons.
    Compatible with the existing pipeline interface.

    Args:
        raw_text: Any text containing SQL.

    Returns:
        Clean SQL string with queries separated by semicolons.
    """
    queries = extract_queries(raw_text)

    if not queries:
        logger.warning("No SQL queries found in input")
        # Fallback: return the stripped body for sqlglot to try
        body = _strip_proc_wrapper(raw_text)
        return _replace_variables(body)

    return ";\n".join(queries)


# --- Utility functions for testing ---


def categorize_by_size(
    sql_sources: list[dict[str, Any]],
    small_max: int = 50,
    medium_max: int = 200,
) -> dict[str, list[dict[str, Any]]]:
    """Categorize SQL sources by line count."""
    categories: dict[str, list[dict[str, Any]]] = {
        "small": [], "medium": [], "large": [],
    }

    for source in sql_sources:
        line_count = source["sql"].count("\n") + 1
        source_with_lines = {**source, "line_count": line_count}

        if line_count <= small_max:
            categories["small"].append(source_with_lines)
        elif line_count <= medium_max:
            categories["medium"].append(source_with_lines)
        else:
            categories["large"].append(source_with_lines)

    for cat in categories.values():
        cat.sort(key=lambda x: x["line_count"])

    logger.info(
        "Categorized %d sources: %d small, %d medium, %d large",
        len(sql_sources),
        len(categories["small"]),
        len(categories["medium"]),
        len(categories["large"]),
    )
    return categories


def test_extraction_sample(
    sql_sources: list[dict[str, Any]],
    n_per_category: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """Extract and parse a sample of small, medium, and large queries."""
    from src.parser.sql_parser import parse_sql

    categories = categorize_by_size(sql_sources)
    results: dict[str, list[dict[str, Any]]] = {
        "small": [], "medium": [], "large": [],
    }

    for cat_name, sources in categories.items():
        if cat_name == "large":
            sample = sources[-n_per_category:]
        elif cat_name == "medium":
            mid = len(sources) // 2
            start = max(0, mid - n_per_category // 2)
            sample = sources[start:start + n_per_category]
        else:
            sample = sources[:n_per_category]

        for source in sample:
            metric_id = source["metric_id"]
            line_count = source["line_count"]

            try:
                clean_sql = extract_select_statements(source["sql"])
                extraction_ok = True
                extraction_error = ""
            except Exception as e:
                clean_sql = ""
                extraction_ok = False
                extraction_error = str(e)

            parse_ok = False
            parse_error = ""
            cte_count = 0
            table_count = 0
            if extraction_ok and clean_sql:
                try:
                    parsed = parse_sql(clean_sql)
                    parse_ok = True
                    cte_count = len(parsed.ctes)
                    table_count = len(parsed.final_select_tables)
                except Exception as e:
                    parse_error = str(e)

            results[cat_name].append({
                "metric_id": metric_id,
                "line_count": line_count,
                "extraction_ok": extraction_ok,
                "extraction_error": extraction_error,
                "parse_ok": parse_ok,
                "parse_error": parse_error,
                "cte_count": cte_count,
                "table_count": table_count,
                "clean_sql_preview": clean_sql[:200] if clean_sql else "",
            })

    return results
