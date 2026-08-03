"""Tests for the crosswalk anonymization engine (src/anonymization.py)."""

from src.anonymization import (
    anonymize_record,
    apply_replacements,
    build_replacements,
    get_scan_terms,
    scan_for_missed,
)

CROSSWALK = {
    "_scan_terms": ["MegaHealth", "MHC_"],
    "databases": {"MegaHealthClarity": "ClarityDB"},
    "schemas": {"MHC_RPT": "reports"},
    "tables": {
        "_org_specific_tables": {"MHC_CENSUS": "org_census"},
        "_emr_tables": {"PAT_ENC": "encounter"},
    },
    "procedures": {
        "p1": {"original": "[MHC_RPT].[USP_ED_Sepsis]",
               "anonymized": "[reports].[USP_ED_Sepsis]"},
    },
    "hardcoded_ids": {"departments": {"100108": "900001"}},
}

REPLACEMENTS = build_replacements(CROSSWALK)


def test_longer_names_replace_before_shorter():
    text, _ = apply_replacements("USE MegaHealthClarity;", REPLACEMENTS)
    assert "ClarityDB" in text and "MegaHealth" not in text


def test_case_insensitive_word_boundary_for_tables():
    text, _ = apply_replacements("FROM pat_enc JOIN PAT_ENC_HSP", REPLACEMENTS)
    assert "FROM encounter" in text
    # word boundary: PAT_ENC_HSP is a different table, must not be mangled...
    # (underscore is a word character, so \b does not split PAT_ENC_HSP)
    assert "PAT_ENC_HSP" in text


def test_numeric_ids_use_digit_boundaries():
    text, _ = apply_replacements("WHERE dept IN (100108, 1001081)", REPLACEMENTS)
    assert "900001," in text
    assert "1001081" in text  # longer ID untouched


def test_bracketed_and_bare_procedure_forms():
    text, _ = apply_replacements(
        "CREATE PROC [MHC_RPT].[USP_ED_Sepsis] -- was MHC_RPT.USP_ED_Sepsis",
        REPLACEMENTS,
    )
    assert "MHC_RPT" not in text


def test_scan_for_missed_finds_leftovers_with_context():
    warnings = scan_for_missed("SELECT * FROM MegaHealth_Extra", ["MegaHealth"])
    assert len(warnings) == 1 and "MegaHealth_Extra" in warnings[0]
    assert scan_for_missed("clean text", ["MegaHealth"]) == []


def test_scan_terms_come_from_crosswalk():
    assert get_scan_terms(CROSSWALK) == ["MegaHealth", "MHC_"]
    assert get_scan_terms({}, fallback=["X"]) == ["X"]


def test_anonymize_record_reaches_nested_json_strings():
    record = {
        "metric_id": "MHC_RPT.USP_ED_Sepsis",
        "ctes_json": '[{"sql_fragment": "SELECT * FROM PAT_ENC WHERE d=100108"}]',
    }
    out, log = anonymize_record(record, REPLACEMENTS)
    assert out["metric_id"] == "reports.USP_ED_Sepsis"
    assert "encounter" in out["ctes_json"] and "900001" in out["ctes_json"]
    assert "PAT_ENC" not in out["ctes_json"]
    assert log  # replacements were recorded
