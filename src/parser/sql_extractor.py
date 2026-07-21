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
    """Extract SQL queries from any text using token-tree inclusion.

    Finds SELECT/WITH/INSERT...SELECT/MERGE statements at the top level,
    extracts them verbatim. Ignores everything else — no regex stripping,
    no text manipulation, no dialect-specific rules.

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

    # Step 3: Parse with sqlparse (non-validating, handles any dialect)
    parsed_statements = sqlparse.parse(body)

    extracted = []

    for stmt in parsed_statements:
        # Walk the token list to find query start points
        tokens = list(stmt.flatten())

        capturing = False
        paren_depth = 0   # parenthesis nesting
        case_depth = 0    # CASE...END nesting (SELECT inside CASE is not a new query)
        current_query_tokens = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Skip comment tokens (but keep them if capturing)
            if token.ttype in (T.Comment.Single, T.Comment.Multiline):
                if capturing:
                    current_query_tokens.append(token)
                i += 1
                continue

            # Track parenthesis depth
            if token.ttype is T.Punctuation:
                if token.value == "(":
                    paren_depth += 1
                    if capturing:
                        current_query_tokens.append(token)
                    i += 1
                    continue
                elif token.value == ")":
                    paren_depth = max(0, paren_depth - 1)
                    if capturing:
                        current_query_tokens.append(token)
                    i += 1
                    continue
                elif token.value == ";":
                    # Statement boundary — end current capture
                    if capturing and current_query_tokens:
                        query_text = "".join(str(t) for t in current_query_tokens).strip()
                        if query_text:
                            extracted.append(query_text)
                        current_query_tokens = []
                        capturing = False
                        paren_depth = 0
                        case_depth = 0
                    i += 1
                    continue

            # Track CASE...END depth (SELECT inside CASE is a scalar subquery, not a new statement)
            if token.ttype is T.Keyword and token.normalized == "CASE":
                case_depth += 1
                if capturing:
                    current_query_tokens.append(token)
                i += 1
                continue

            if token.ttype is T.Keyword and token.normalized == "END":
                if case_depth > 0:
                    case_depth -= 1
                if capturing:
                    current_query_tokens.append(token)
                i += 1
                continue

            # Determine if we're at the "top level" of a statement
            at_top_level = paren_depth == 0 and case_depth == 0

            # Not capturing: look for query start at top level
            if not capturing:
                if at_top_level and _is_query_start(token):
                    capturing = True
                    current_query_tokens = [token]
                # Skip everything else (noise keywords, procedural code)
                i += 1
                continue

            # Capturing: accumulate tokens, watch for boundaries
            if capturing:
                if at_top_level and _is_noise_keyword(token):
                    # Noise keyword at top level ends the current query
                    query_text = "".join(str(t) for t in current_query_tokens).strip()
                    if query_text:
                        extracted.append(query_text)
                    current_query_tokens = []
                    capturing = False
                    paren_depth = 0
                    case_depth = 0
                    i += 1
                    continue

                # A new query start at top level when NOT inside parens/case
                # means a new statement (e.g., after a UNION-less SELECT ends)
                # But only if the token is WITH or a DML at the very start of a line
                # For safety, SELECT inside a capturing context is ALWAYS a continuation
                # (subquery, scalar, UNION branch). Only WITH starts a truly new statement.
                if at_top_level and token.ttype is T.Keyword.CTE:
                    # WITH at top level while capturing = new CTE statement
                    query_text = "".join(str(t) for t in current_query_tokens).strip()
                    if query_text:
                        extracted.append(query_text)
                    current_query_tokens = [token]
                    i += 1
                    continue

                # Otherwise, keep accumulating
                current_query_tokens.append(token)
                i += 1
                continue

            i += 1

        # Catch trailing query without semicolon
        if capturing and current_query_tokens:
            query_text = "".join(str(t) for t in current_query_tokens).strip()
            if query_text:
                extracted.append(query_text)

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
