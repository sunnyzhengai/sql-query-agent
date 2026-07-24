"""Classify parse errors into user-facing categories with explanations.

Turns raw Python exceptions into business-language explanations
that the Data Agent can relay to users. Each error gets:
- category: short label for grouping/filtering
- explanation: what happened in plain English
- action: what the admin/developer should do
"""

from __future__ import annotations

import re


def classify_parse_error(error_message: str, metric_id: str, line_count: int) -> dict:
    """Classify a parse error into a user-facing category.

    Returns dict with keys: error_category, user_explanation, suggested_action.
    """
    err = error_message.lower()

    # No SELECT found — proc may be DDL-only, EXEC-only, or control flow only
    if "no select" in err or "no sql queries found" in err:
        return {
            "error_category": "no_query",
            "user_explanation": (
                f"The stored procedure '{metric_id}' does not contain any SELECT queries. "
                "It may be a utility procedure (e.g., data loading, maintenance) that "
                "does not produce reportable output."
            ),
            "suggested_action": (
                "Review whether this procedure is used for reporting. "
                "If it only performs INSERT/UPDATE/DELETE operations, it can be excluded "
                "from the knowledge graph. No action needed if it's not a report source."
            ),
        }

    # Tokenizer/parser error — SQL syntax too complex for the parser
    if "error tokenizing" in err or "unexpected token" in err or "invalid expression" in err:
        return {
            "error_category": "complex_sql",
            "user_explanation": (
                f"The stored procedure '{metric_id}' ({line_count} lines) contains SQL syntax "
                "that the parser cannot process. This typically happens with very long "
                "IN lists, dynamic SQL, or uncommon T-SQL extensions."
            ),
            "suggested_action": (
                "A developer should review this procedure. Common fixes: "
                "replace long IN(...) lists with reference table JOINs, "
                "move dynamic SQL to a separate procedure, "
                "or simplify nested CASE expressions."
            ),
        }

    # None of N queries parsed — ScriptDom extracted but sqlglot rejected all
    if "none of" in err and "parsed successfully" in err:
        count_match = re.search(r"none of (\d+)", err)
        count = count_match.group(1) if count_match else "multiple"
        return {
            "error_category": "all_queries_failed",
            "user_explanation": (
                f"The stored procedure '{metric_id}' was successfully split into {count} "
                "individual queries, but none could be structurally analyzed. "
                "The SQL may use dialect-specific features not yet supported."
            ),
            "suggested_action": (
                "A developer should review the extracted queries to identify "
                "which T-SQL features are causing the failure. "
                "This procedure's logic is not yet available in the knowledge graph."
            ),
        }

    # Failed to parse single statement
    if "failed to parse sql" in err:
        return {
            "error_category": "parse_failure",
            "user_explanation": (
                f"The stored procedure '{metric_id}' could not be parsed. "
                "The SQL structure may use features the parser doesn't support yet."
            ),
            "suggested_action": (
                "Check the '/errors' report for the specific error message. "
                "A developer can review whether the procedure can be simplified."
            ),
        }

    # ScriptDom extraction issue
    if "scriptdom" in err:
        return {
            "error_category": "extraction_failure",
            "user_explanation": (
                f"The SQL extractor could not process '{metric_id}'. "
                "The procedure may contain syntax errors or unsupported T-SQL constructs."
            ),
            "suggested_action": (
                "Verify the procedure compiles successfully in SQL Server Management Studio. "
                "If it does, report this as a parser enhancement request."
            ),
        }

    # Catch-all
    return {
        "error_category": "unknown",
        "user_explanation": (
            f"An unexpected error occurred while processing '{metric_id}': "
            f"{error_message[:150]}"
        ),
        "suggested_action": (
            "Report this error to the system administrator for investigation."
        ),
    }
