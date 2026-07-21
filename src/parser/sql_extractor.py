"""Deterministic SQL extractor using sqlparse.

Splits stored procedure bodies into individual statements using sqlparse
(a non-validating, forgiving parser), then filters to keep only
SELECT/WITH statements. Discards all procedural scaffolding.

This replaces the LLM-based extraction with a deterministic, instant,
zero-cost approach that works across SQL dialects.

Architecture:
  Raw proc → sqlparse.split() → filter by type → clean SQL → sqlglot parse
"""

from __future__ import annotations

import logging
import re
from typing import Any

import sqlparse
from sqlparse.sql import Statement

logger = logging.getLogger(__name__)

# Procedural keywords to strip before splitting
_PROC_PREAMBLE_RE = re.compile(
    r"^\s*(?:"
    r"USE\s+\[?\w+\]?\s*;?"
    r"|GO\b"
    r"|SET\s+\w[\w\s]*(?:ON|OFF|UNCOMMITTED|COMMITTED)\s*;?"
    r"|SET\s+TRANSACTION\s+ISOLATION\s+LEVEL\s+\w[\w\s]*;?"
    r"|CREATE\s+(?:OR\s+ALTER\s+)?(?:PROCEDURE|PROC|FUNCTION|TRIGGER)\b[\s\S]*?\bAS\b"
    r"|DECLARE\s+@[\s\S]*?(?=;|\bSELECT\b|\bWITH\b|\bINSERT\b|\bIF\b|\bBEGIN\b|\bDROP\b)"
    r"|DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?#?\w+\s*;?"
    r"|IF\s+OBJECT_ID\s*\([^)]*\)\s+IS\s+NOT\s+NULL\s+(?:BEGIN\s+)?DROP\s+TABLE\s+#\w+\s*;?(?:\s+END)?\s*;?"
    r"|CREATE\s+(?:UNIQUE\s+)?(?:CLUSTERED\s+|NONCLUSTERED\s+)?INDEX\s+\w+\s+ON\s+#?\w+\s*\([^)]*\)\s*;?"
    r"|PRINT\s*\(.*?\)\s*;?"
    r"|GOTO\s+\w+\s*;?"
    r"|RETURN\b\s*;?"
    r"|RAISERROR\b.*?;?"
    r"|THROW\b.*?;?"
    r")\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# BEGIN...END wrapper
_BEGIN_END_RE = re.compile(
    r"^\s*BEGIN\b([\s\S]*)\bEND\s*;?\s*$",
    re.IGNORECASE,
)


def _strip_proc_wrapper(sql: str) -> str:
    """Remove CREATE PROCEDURE wrapper and BEGIN...END block."""
    # Strip everything before CREATE PROC ... AS
    create_match = re.search(
        r"\bCREATE\s+(?:OR\s+ALTER\s+)?(?:PROCEDURE|PROC)\b[\s\S]*?\bAS\b",
        sql, re.IGNORECASE,
    )
    if create_match:
        sql = sql[create_match.end():]

    # Strip outer BEGIN...END
    sql = sql.strip()
    begin_match = _BEGIN_END_RE.match(sql)
    if begin_match:
        sql = begin_match.group(1)

    # Strip trailing GO
    sql = re.sub(r"\bGO\s*$", "", sql.strip(), flags=re.IGNORECASE)

    return sql.strip()


def _strip_preamble(sql: str) -> str:
    """Remove procedural preamble lines (USE, SET, DECLARE, DROP, etc.)."""
    # Multiple passes since removing one line may expose another
    for _ in range(5):
        cleaned = _PROC_PREAMBLE_RE.sub("", sql)
        if cleaned == sql:
            break
        sql = cleaned
    return sql.strip()


def _get_statement_type(stmt: Statement) -> str | None:
    """Get the DML type of a parsed sqlparse statement."""
    return stmt.get_type()


def _deep_clean(body: str) -> str:
    """Remove all non-query constructs that sqlparse splitting may miss."""

    # Remove SSMS boilerplate before CREATE PROC
    body = re.sub(
        r"\A.*?(?=CREATE\s+(?:OR\s+(?:ALTER|REPLACE)\s+)?(?:PROCEDURE|PROC|VIEW|FUNCTION)\b)",
        "", body, flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove USE [database]
    body = re.sub(r"^\s*USE\s+\[?\w+\]?\s*;?\s*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove GO batch separators
    body = re.sub(r"^\s*GO\s*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove all SET statements (multi-word variants)
    body = re.sub(
        r"^\s*SET\s+(?:NOCOUNT|ANSI_NULLS|ANSI_PADDING|ANSI_WARNINGS|ARITHABORT|"
        r"CONCAT_NULL_YIELDS_NULL|QUOTED_IDENTIFIER|NUMERIC_ROUNDABORT|"
        r"XACT_ABORT|DATEFIRST|DATEFORMAT|DEADLOCK_PRIORITY|FMTONLY|"
        r"IDENTITY_INSERT|LANGUAGE|LOCK_TIMEOUT|ROWCOUNT|TEXTSIZE|"
        r"TRANSACTION\s+ISOLATION\s+LEVEL)\s+[\w\s]+;?\s*$",
        "", body, flags=re.MULTILINE | re.IGNORECASE,
    )

    # Remove SET @variable = ... (single line)
    body = re.sub(r"^\s*SET\s+@\w+\s*=.*?;?\s*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove all DECLARE blocks (single and multi-line with commas)
    body = re.sub(
        r"\bDECLARE\s+@[\s\S]*?(?=\b(?:SELECT|WITH|INSERT|IF|BEGIN|DROP|CREATE\s+INDEX|;)\b)",
        "", body, flags=re.IGNORECASE,
    )
    # Catch remaining single-line DECLARE
    body = re.sub(r"^\s*DECLARE\s+.*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove DROP TABLE statements
    body = re.sub(r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?#?\w+\s*;?", "", body, flags=re.IGNORECASE)

    # Remove IF OBJECT_ID(...) DROP TABLE guards
    body = re.sub(
        r"IF\s+OBJECT_ID\s*\([^)]*\)\s+IS\s+NOT\s+NULL\s+"
        r"(?:BEGIN\s+)?DROP\s+TABLE\s+#\w+\s*;?(?:\s+END)?\s*;?",
        "", body, flags=re.IGNORECASE,
    )

    # Remove CREATE INDEX on temp or regular tables
    body = re.sub(
        r"\bCREATE\s+(?:UNIQUE\s+)?(?:CLUSTERED\s+|NONCLUSTERED\s+)?INDEX\s+\w+\s+ON\s+#?\w+\s*\([^)]*\)\s*;?",
        "", body, flags=re.IGNORECASE,
    )

    # Remove PRINT statements (with parens or without)
    body = re.sub(r"\bPRINT\s*\(.*?\)\s*;?", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\bPRINT\s+'[^']*'\s*;?", "", body, flags=re.IGNORECASE)

    # Remove GOTO / labels
    body = re.sub(r"^\s*GOTO\s+\w+\s*;?\s*$", "", body, flags=re.MULTILINE | re.IGNORECASE)
    body = re.sub(r"^\s*\w+:\s*$", "", body, flags=re.MULTILINE)

    # Remove RETURN statements
    body = re.sub(r"^\s*RETURN\b.*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove EXEC/EXECUTE statements
    body = re.sub(r"^\s*EXEC(?:UTE)?\s+.*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove RAISERROR / THROW
    body = re.sub(r"^\s*RAISERROR\b.*$", "", body, flags=re.MULTILINE | re.IGNORECASE)
    body = re.sub(r"^\s*THROW\b.*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove OPTION(...) query hints
    body = re.sub(r"\bOPTION\s*\([^)]*\)\s*;?", "", body, flags=re.IGNORECASE)

    # Remove INSERT INTO #temp VALUES(...) — seed data (multi-line aware)
    body = re.sub(
        r"\bINSERT\s+INTO\s+#\w+\s*(?:\([^)]*\))?\s*VALUES\s*\([^)]*\)\s*;?",
        "", body, flags=re.IGNORECASE,
    )

    # Remove simple IF blocks (IF ... BEGIN ... END)
    # Non-greedy to avoid eating nested structures
    body = re.sub(
        r"\bIF\b[^;]*?\bBEGIN\b[\s\S]*?\bEND\s*;?",
        "", body, flags=re.IGNORECASE,
    )

    # Remove standalone IF (single line, no BEGIN)
    body = re.sub(r"^\s*IF\s+.*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove WHILE loops
    body = re.sub(
        r"\bWHILE\b[\s\S]*?\bBEGIN\b[\s\S]*?\bEND\s*;?",
        "", body, flags=re.IGNORECASE,
    )

    # Remove BEGIN TRY / BEGIN CATCH blocks
    body = re.sub(
        r"\bBEGIN\s+TRY\b[\s\S]*?\bEND\s+TRY\b\s*\bBEGIN\s+CATCH\b[\s\S]*?\bEND\s+CATCH\b\s*;?",
        "", body, flags=re.IGNORECASE,
    )

    # Remove standalone BEGIN/END (outer wrapper)
    body = re.sub(r"^\s*BEGIN\s*$", "", body, flags=re.MULTILINE | re.IGNORECASE)
    body = re.sub(r"^\s*END\s*;?\s*$", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Remove comment-only lines that look like SQL (e.g., "--SELECT * FROM #temp")
    body = re.sub(r"^\s*--.*$", "", body, flags=re.MULTILINE)

    # Remove block comments that span multiple lines
    body = re.sub(r"/\*[\s\S]*?\*/", "", body)

    return body.strip()


def extract_select_statements(sql: str) -> str:
    """Extract only SELECT/WITH/UNION statements from a stored procedure.

    Uses aggressive stripping + sqlparse splitting + type filtering.
    Deterministic, instant, zero-cost.

    Args:
        sql: Raw stored procedure text (CREATE PROCEDURE ... END).

    Returns:
        Clean SQL containing only data query statements, separated by semicolons.
    """
    # Step 1: Strip the proc wrapper
    body = _strip_proc_wrapper(sql)

    # Step 2: Deep clean — remove all non-query constructs
    body = _deep_clean(body)

    # Step 3: Replace @variables with placeholders
    body = re.sub(r"@(\w+)", r"__param_\1__", body)

    # Step 4: Split into individual statements using sqlparse
    statements = sqlparse.split(body)

    # Step 5: Parse each statement and filter
    kept = []
    dropped = []

    for stmt_text in statements:
        stmt_text = stmt_text.strip()
        if not stmt_text or stmt_text == ";" or len(stmt_text) < 5:
            continue

        # Skip if it's just a comment remnant or whitespace
        if all(line.strip().startswith("--") or not line.strip() for line in stmt_text.split("\n")):
            continue

        parsed = sqlparse.parse(stmt_text)
        if not parsed:
            continue

        stmt = parsed[0]
        stmt_type = _get_statement_type(stmt)

        # Get the first meaningful token (skip whitespace/comments)
        first_word = ""
        for line in stmt_text.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("--") and not stripped.startswith("/*"):
                first_word = stripped.split()[0].upper() if stripped.split() else ""
                break

        # Keep SELECT statements
        if stmt_type == "SELECT" or first_word == "SELECT":
            kept.append(stmt_text)
            continue

        # Keep WITH (CTE) statements
        if first_word == "WITH":
            kept.append(stmt_text)
            continue

        # Keep INSERT...SELECT (staging queries with business logic)
        if (stmt_type == "INSERT" or first_word == "INSERT") and re.search(r"\bSELECT\b", stmt_text, re.IGNORECASE):
            # But NOT INSERT INTO #temp VALUES (seed data without SELECT)
            if not re.search(r"\bVALUES\s*\(", stmt_text, re.IGNORECASE):
                kept.append(stmt_text)
                continue

        # Drop everything else
        dropped.append((stmt_type or first_word or "UNKNOWN", stmt_text[:60]))

    if dropped:
        logger.info("Dropped %d non-query statements: %s",
                    len(dropped),
                    ", ".join(f"{t}" for t, _ in dropped[:5]))

    if not kept:
        logger.warning("No SELECT statements found after filtering")
        return body

    result = ";\n".join(kept)
    logger.info("Extracted %d query statements (%d dropped)", len(kept), len(dropped))
    return result


def categorize_by_size(
    sql_sources: list[dict[str, Any]],
    small_max: int = 50,
    medium_max: int = 200,
) -> dict[str, list[dict[str, Any]]]:
    """Categorize SQL sources by line count.

    Args:
        sql_sources: List of dicts with 'metric_id', 'name', 'sql' keys.
        small_max: Max lines for "small" category.
        medium_max: Max lines for "medium" category.

    Returns:
        Dict with keys 'small', 'medium', 'large', each containing
        a list of sql_source dicts sorted by line count.
    """
    categories: dict[str, list[dict[str, Any]]] = {
        "small": [],
        "medium": [],
        "large": [],
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

    # Sort each category by line count
    for cat in categories.values():
        cat.sort(key=lambda x: x["line_count"])

    logger.info(
        "Categorized %d sources: %d small (≤%d lines), %d medium (%d-%d), %d large (>%d)",
        len(sql_sources),
        len(categories["small"]), small_max,
        len(categories["medium"]), small_max + 1, medium_max,
        len(categories["large"]), medium_max,
    )
    return categories


def test_extraction_sample(
    sql_sources: list[dict[str, Any]],
    n_per_category: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """Extract and parse a sample of small, medium, and large queries.

    Picks the top N from each size category, runs extraction + sqlglot parsing,
    and returns the results for review.

    Args:
        sql_sources: List of dicts with 'metric_id', 'name', 'sql' keys.
        n_per_category: Number of queries to test per category.

    Returns:
        Dict with 'small', 'medium', 'large' keys, each containing
        a list of result dicts with extraction and parse outcomes.
    """
    from src.parser.sql_parser import parse_sql

    categories = categorize_by_size(sql_sources)
    results: dict[str, list[dict[str, Any]]] = {
        "small": [],
        "medium": [],
        "large": [],
    }

    for cat_name, sources in categories.items():
        # Pick top N (smallest in small, middle in medium, largest in large)
        if cat_name == "large":
            sample = sources[-n_per_category:]  # largest
        elif cat_name == "medium":
            mid = len(sources) // 2
            start = max(0, mid - n_per_category // 2)
            sample = sources[start:start + n_per_category]
        else:
            sample = sources[:n_per_category]  # smallest

        for source in sample:
            metric_id = source["metric_id"]
            line_count = source["line_count"]

            # Extract clean SQL
            try:
                clean_sql = extract_select_statements(source["sql"])
                extraction_ok = True
                extraction_error = ""
            except Exception as e:
                clean_sql = ""
                extraction_ok = False
                extraction_error = str(e)

            # Parse the extracted SQL
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
