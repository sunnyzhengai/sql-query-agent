"""Tests for Collibra lineage matching — proc/view → PBI report."""

import pytest

from src.adapters.collibra_lineage_match import (
    extract_match_key,
    fuzzy_match_score,
    normalize_report_name,
)


class TestExtractMatchKey:
    """extract_match_key strips prefix, company, and _PBI suffix."""

    def test_view_standard(self):
        assert extract_match_key("V_CCHP_SomeReport_PBI") == "somereport"

    def test_view_multi_word(self):
        assert extract_match_key("V_CCHP_Some_Report_Name_PBI") == "some report name"

    def test_proc_standard(self):
        assert extract_match_key("USP_CCHP_Some_Report_PBI") == "some report"

    def test_proc_different_company(self):
        assert extract_match_key("USP_COOK_ED_Sepsis_PBI") == "ed sepsis"

    def test_view_with_numbers(self):
        assert extract_match_key("V_CCHP_340B_Charges_PBI") == "340b charges"

    def test_no_pbi_suffix_returns_none(self):
        assert extract_match_key("USP_CCHP_SomeReport") is None

    def test_no_pbi_suffix_view_returns_none(self):
        assert extract_match_key("V_CCHP_SomeReport") is None

    def test_case_insensitive_pbi(self):
        assert extract_match_key("V_CCHP_Test_pbi") == "test"

    def test_proc_case_insensitive_prefix(self):
        assert extract_match_key("usp_CCHP_Test_PBI") == "test"

    def test_view_case_insensitive_prefix(self):
        assert extract_match_key("v_CCHP_Test_PBI") == "test"

    def test_single_word_after_company(self):
        assert extract_match_key("V_CCHP_Dashboard_PBI") == "dashboard"

    def test_long_name(self):
        assert extract_match_key("USP_CCHP_IP_Sepsis_Compliance_By_Shift_PBI") == "ip sepsis compliance by shift"


class TestNormalizeReportName:
    """normalize_report_name strips bracketed UUIDs and normalizes."""

    def test_brackets_stripped(self):
        name = "[433bbb97-5965-48fd-9045-9d55b7963378] 340B Eligible Charges [667ad212-fbb1-475e-8f8d-18d224c1757d]"
        assert normalize_report_name(name) == "340b eligible charges"

    def test_no_brackets(self):
        assert normalize_report_name("Some Report Name") == "some report name"

    def test_extra_whitespace(self):
        assert normalize_report_name("  Some   Report  ") == "some report"


class TestFuzzyMatchScore:
    def test_exact_match(self):
        assert fuzzy_match_score("340b charges", "340b eligible charges for hb and pb") >= 0.5

    def test_full_match(self):
        assert fuzzy_match_score("sepsis", "sepsis compliance report") == 1.0

    def test_multi_token_partial(self):
        score = fuzzy_match_score("ed sepsis", "ed sepsis dashboard")
        assert score == 1.0

    def test_no_match(self):
        assert fuzzy_match_score("oncology", "sepsis compliance report") == 0.0

    def test_empty_key(self):
        assert fuzzy_match_score("", "some report") == 0.0

    def test_substring_match(self):
        # "compliance" is substring of "compliancemetrics" → should match
        score = fuzzy_match_score("compliance metrics", "ip sepsis compliancemetrics report")
        assert score >= 0.5
