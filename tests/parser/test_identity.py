"""Tests for SQL object identity extraction (metric_id source of truth)."""

from src.parser.identity import (
    extract_object_identity,
    find_duplicate_identities,
    normalize_sql_text,
)


def test_procedure_with_schema_and_brackets():
    sql = "CREATE PROCEDURE [reporting].[USP_ED_Sepsis] AS BEGIN SELECT 1 END"
    assert extract_object_identity(sql) == ("reporting", "USP_ED_Sepsis", "procedure")


def test_create_or_alter_procedure():
    sql = "CREATE OR ALTER PROCEDURE reporting.USP_X AS SELECT 1"
    assert extract_object_identity(sql) == ("reporting", "USP_X", "procedure")


def test_procedure_without_schema_defaults_to_dbo():
    sql = "ALTER PROCEDURE USP_Solo AS SELECT 1"
    assert extract_object_identity(sql) == ("dbo", "USP_Solo", "procedure")


def test_view_with_schema():
    sql = "CREATE VIEW [reporting].[V_ED_CENSUS] AS SELECT * FROM encounter"
    assert extract_object_identity(sql) == ("reporting", "V_ED_CENSUS", "view")


def test_alter_view_without_schema_defaults_to_dbo():
    sql = "alter view V_Daily as select 1"
    assert extract_object_identity(sql) == ("dbo", "V_Daily", "view")


def test_same_name_different_schema_yields_distinct_identities():
    a = extract_object_identity("CREATE PROCEDURE [reporting].[USP_ED] AS SELECT 1")
    b = extract_object_identity("CREATE PROCEDURE [reports].[USP_ED] AS SELECT 1")
    assert a != b
    assert a[1] == b[1] == "USP_ED"


def test_whitespace_around_dot_is_tolerated():
    sql = "CREATE PROCEDURE [reporting] . [USP_X] AS SELECT 1"
    assert extract_object_identity(sql) == ("reporting", "USP_X", "procedure")


def test_no_object_definition_returns_nones():
    assert extract_object_identity("SELECT * FROM encounter") == (None, None, None)


def test_normalize_sql_text_converts_crlf_at_entry():
    assert normalize_sql_text("SELECT 1\r\nFROM t\r\n") == "SELECT 1\nFROM t\n"


def test_find_duplicate_identities_reports_colliding_files():
    dupes = find_duplicate_identities([
        ("reporting.USP_ED", "a/USP_ED.sql"),
        ("reports.USP_ED", "b/USP_ED.sql"),
        ("reporting.USP_ED", "c/USP_ED_v2.sql"),
        ("dbo.USP_OK", "USP_OK.sql"),
    ])
    assert dupes == {"REPORTING.USP_ED": ["a/USP_ED.sql", "c/USP_ED_v2.sql"]}


def test_duplicate_detection_is_case_insensitive():
    """SQL Server identifiers are case-insensitive (default collation) —
    [Reporting].[USP_X] and [reporting].[USP_X] are the same object."""
    dupes = find_duplicate_identities([
        ("Reporting.USP_X", "a.sql"),
        ("reporting.USP_X", "b.sql"),
    ])
    assert dupes == {"REPORTING.USP_X": ["a.sql", "b.sql"]}
