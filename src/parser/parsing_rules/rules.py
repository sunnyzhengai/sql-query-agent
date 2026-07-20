"""The ordered parsing-rule registry.

Each entry is one T-SQL construct sqlglot can't parse natively.
Rule ordering matters: rules higher in the list run first, and later
rules see SQL the earlier ones have already transformed.

Ported from sql-business-logic-extractor.
"""

import re

from .rule import Rule

PARSING_RULES: list[Rule] = [
    Rule(
        id="strip_ssms_preamble",
        description=(
            "SSMS Generate-Scripts prefaces every exported view/proc with "
            "USE [db], GO, SET ANSI_NULLS, /****** Object: ... ******/, etc. "
            "This rule trims everything before the first CREATE statement."
        ),
        pattern=(
            r"\A.*?"
            r"(?=CREATE\s+(?:OR\s+(?:ALTER|REPLACE)\s+)?"
            r"(?:VIEW|PROCEDURE|PROC|FUNCTION|TRIGGER)\b)"
        ),
        replacement="",
        flags=re.IGNORECASE | re.DOTALL,
    ),
    Rule(
        id="create_view_explicit_column_list",
        description=(
            "T-SQL allows CREATE VIEW name (col1, col2, ...) AS SELECT ... "
            "sqlglot doesn't parse this form. Strip the column list."
        ),
        pattern=(
            r"((?:CREATE\s+(?:OR\s+ALTER\s+)?|ALTER\s+)VIEW\s+"
            r"(?:\[[^\]]+\]|\w+)"
            r"(?:\.(?:\[[^\]]+\]|\w+))?)"
            r"\s*\((?:\[[^\]]*\]|[^)])*\)"
            r"[\s\S]*?"
            r"\bAS\b"
        ),
        replacement=r"\1 AS",
        flags=re.IGNORECASE | re.DOTALL,
    ),
    Rule(
        id="strip_procedure_wrapper",
        description=(
            "Strip CREATE [OR ALTER] PROCEDURE name [(params)] AS wrapper. "
            "Handles multi-line parameter blocks and AS keyword disambiguation."
        ),
        pattern=(
            r"\bCREATE\s+(?:OR\s+ALTER\s+)?"
            r"(?:PROCEDURE|PROC|FUNCTION|TRIGGER)\s+"
            r"(?:\[[^\]]+\]|\w+)"
            r"(?:\.(?:\[[^\]]+\]|\w+))?"
            r"[\s\S]*?"
            r"\bAS\s+"
            r"(?=BEGIN\b|SELECT\b|WITH\b|DECLARE\b|RETURN\b|"
            r"INSERT\b|UPDATE\b|DELETE\b|MERGE\b|EXEC\b|SET\b|IF\b|DROP\b)"
        ),
        replacement="",
        flags=re.IGNORECASE | re.DOTALL,
    ),
    Rule(
        id="strip_proc_begin_end_wrapper",
        description=(
            "After stripping the procedure wrapper, the body is often wrapped "
            "in BEGIN ... END. Strip the outermost pair only."
        ),
        pattern=(
            r"\A\s*BEGIN\b\s*([\s\S]*?)\s*\bEND\s*;?\s*(?:\bGO\b\s*)?\Z"
        ),
        replacement=r"\1",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="rewrite_odbc_escape_clause",
        description=(
            "Rewrite ODBC {escape '<char>'} -> ESCAPE '<char>'."
        ),
        pattern=r"\{\s*escape\s+('[^']*')\s*\}",
        replacement=r"ESCAPE \1",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="strip_set_transaction_isolation",
        description=(
            "Strip SET TRANSACTION ISOLATION LEVEL ... statements. "
            "Session settings with no lineage content."
        ),
        pattern=(
            r"^[ \t]*SET\s+TRANSACTION\s+ISOLATION\s+LEVEL\s+"
            r"(?:READ\s+UNCOMMITTED|READ\s+COMMITTED|REPEATABLE\s+READ"
            r"|SERIALIZABLE|SNAPSHOT)\b[ \t]*;?[ \t]*\r?\n?"
        ),
        replacement="",
        flags=re.IGNORECASE | re.MULTILINE,
    ),
]
