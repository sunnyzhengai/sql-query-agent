"""Tests for parse error classification."""

from src.parser.error_classifier import classify_parse_error


def test_no_select_error():
    result = classify_parse_error(
        "ScriptDom found no SELECT statements", "USP_LOAD_DATA", 50
    )
    assert result["error_category"] == "no_query"
    assert "USP_LOAD_DATA" in result["user_explanation"]
    assert "reporting" in result["suggested_action"].lower()


def test_tokenizer_error():
    result = classify_parse_error(
        "Error tokenizing ','121676','122129','122131'", "USP_WASTE_RPT", 428
    )
    assert result["error_category"] == "complex_sql"
    assert "428 lines" in result["user_explanation"]
    assert "IN(" in result["suggested_action"] or "IN(...)" in result["suggested_action"]


def test_none_parsed_error():
    result = classify_parse_error(
        "Failed to parse SQL: none of 5 extracted queries parsed successfully",
        "USP_COMPLEX", 300
    )
    assert result["error_category"] == "all_queries_failed"
    assert "5" in result["user_explanation"]


def test_generic_parse_error():
    result = classify_parse_error(
        "Failed to parse SQL: SELECT DISTINCT...", "USP_REPORT", 100
    )
    assert result["error_category"] == "parse_failure"


def test_unknown_error():
    result = classify_parse_error(
        "Something completely unexpected happened", "USP_MYSTERY", 10
    )
    assert result["error_category"] == "unknown"
    assert "unexpected" in result["user_explanation"].lower()


def test_all_categories_have_required_keys():
    """Every classification must return all three required fields."""
    test_cases = [
        "no SELECT statements found",
        "Error tokenizing blah",
        "none of 3 extracted queries parsed successfully",
        "Failed to parse SQL: xyz",
        "ScriptDom service error",
        "random garbage",
    ]
    for msg in test_cases:
        result = classify_parse_error(msg, "TEST", 100)
        assert "error_category" in result, f"Missing error_category for: {msg}"
        assert "user_explanation" in result, f"Missing user_explanation for: {msg}"
        assert "suggested_action" in result, f"Missing suggested_action for: {msg}"
        assert len(result["user_explanation"]) > 20, f"Explanation too short for: {msg}"
        assert len(result["suggested_action"]) > 20, f"Action too short for: {msg}"
