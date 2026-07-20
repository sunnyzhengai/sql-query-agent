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


def extract_select_statements(sql: str) -> str:
    """Extract only SELECT/WITH/UNION statements from a stored procedure.

    Uses sqlparse to split into statements and filter by type.
    Deterministic, instant, zero-cost.

    Args:
        sql: Raw stored procedure text (CREATE PROCEDURE ... END).

    Returns:
        Clean SQL containing only data query statements, separated by semicolons.
    """
    # Step 1: Strip the proc wrapper
    body = _strip_proc_wrapper(sql)

    # Step 2: Strip procedural preamble
    body = _strip_preamble(body)

    # Step 3: Replace @variables with placeholders (sqlparse handles them better than sqlglot)
    body = re.sub(r"@(\w+)", r"__param_\1__", body)

    # Step 4: Split into individual statements using sqlparse
    statements = sqlparse.split(body)

    # Step 5: Parse each statement and filter
    kept = []
    dropped = []

    for stmt_text in statements:
        stmt_text = stmt_text.strip()
        if not stmt_text or stmt_text == ";":
            continue

        parsed = sqlparse.parse(stmt_text)
        if not parsed:
            continue

        stmt = parsed[0]
        stmt_type = _get_statement_type(stmt)

        # Keep SELECT statements (includes WITH...SELECT, UNION, etc.)
        if stmt_type == "SELECT":
            kept.append(stmt_text)
            continue

        # Keep statements that start with WITH (CTEs) — sqlparse may type these as None
        first_token = stmt_text.strip().split()[0].upper() if stmt_text.strip() else ""
        if first_token in ("WITH", "SELECT"):
            kept.append(stmt_text)
            continue

        # Keep INSERT...SELECT INTO #temp (staging queries with business logic)
        if stmt_type == "INSERT" and re.search(r"\bSELECT\b", stmt_text, re.IGNORECASE):
            kept.append(stmt_text)
            continue

        # Keep SELECT...INTO #temp (staging queries)
        if "INTO" in stmt_text.upper() and "SELECT" in stmt_text.upper():
            kept.append(stmt_text)
            continue

        # Drop everything else (SET, DECLARE, DROP, CREATE INDEX, PRINT, IF, etc.)
        dropped.append((stmt_type or "UNKNOWN", stmt_text[:60]))

    if dropped:
        logger.info("Dropped %d non-query statements: %s",
                    len(dropped),
                    ", ".join(f"{t}" for t, _ in dropped[:5]))

    if not kept:
        logger.warning("No SELECT statements found after filtering")
        # Return the body as-is and let sqlglot try
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
