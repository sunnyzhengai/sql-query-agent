"""Tests for Collibra lineage matching — proc/view → PBI report."""


from src.adapters.collibra_lineage_match import (
    CollibraLineageMatcher,
    extract_match_key,
    fuzzy_match_score,
    normalize_report_name,
)


class TestExtractMatchKey:
    """extract_match_key strips prefix, company, and _PBI suffix."""

    def test_view_standard(self):
        assert extract_match_key("V_ACME_SomeReport_PBI") == "somereport"

    def test_view_multi_word(self):
        assert extract_match_key("V_ACME_Some_Report_Name_PBI") == "some report name"

    def test_proc_standard(self):
        assert extract_match_key("USP_ACME_Some_Report_PBI") == "some report"

    def test_proc_different_company(self):
        assert extract_match_key("USP_ACME_ED_Sepsis_PBI") == "ed sepsis"

    def test_view_with_numbers(self):
        assert extract_match_key("V_ACME_340B_Charges_PBI") == "340b charges"

    def test_no_pbi_suffix_returns_none(self):
        assert extract_match_key("USP_ACME_SomeReport") is None

    def test_no_pbi_suffix_view_returns_none(self):
        assert extract_match_key("V_ACME_SomeReport") is None

    def test_case_insensitive_pbi(self):
        assert extract_match_key("V_ACME_Test_pbi") == "test"

    def test_proc_case_insensitive_prefix(self):
        assert extract_match_key("usp_ACME_Test_PBI") == "test"

    def test_view_case_insensitive_prefix(self):
        assert extract_match_key("v_ACME_Test_PBI") == "test"

    def test_single_word_after_company(self):
        assert extract_match_key("V_ACME_Dashboard_PBI") == "dashboard"

    def test_long_name(self):
        assert extract_match_key("USP_ACME_IP_Sepsis_Compliance_By_Shift_PBI") == "ip sepsis compliance by shift"


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


class TestExactMatchTier:
    """Exact TMDL-derived names beat the heuristic (follow-up 2026-08-16)."""

    def _matcher(self):
        m = CollibraLineageMatcher(client=None, min_score=0.5)
        m._report_cache = [
            {"id": "asset-1", "name": "Sepsis Compliance Dashboard"},
            {"id": "asset-2", "name": "ED Throughput"},
        ]
        return m

    def test_exact_name_matches_deterministically(self):
        match = self._matcher().match_object(
            "USP_ACME_Whatever", exact_report_name="Sepsis Compliance Dashboard"
        )
        assert match is not None
        assert match.report_asset_id == "asset-1"
        assert match.score == 1.0

    def test_exact_name_is_case_insensitive(self):
        match = self._matcher().match_object(
            "USP_X", exact_report_name="sepsis compliance DASHBOARD"
        )
        assert match is not None and match.report_asset_id == "asset-1"

    def test_known_but_absent_name_never_falls_back_to_fuzzy(self):
        # The asset is not in Collibra yet: correct answer is NO match,
        # not a fuzzy guess against a name we know exactly.
        match = self._matcher().match_object(
            "USP_ACME_ED_Throughput_PBI", exact_report_name="Missing Report"
        )
        assert match is None

    def test_match_objects_uses_known_names_case_insensitively(self):
        result = self._matcher().match_objects(
            [{"object_name": "USP_A", "object_type": "SQL_STORED_PROCEDURE"}],
            known_report_names={"usp_a": "ED Throughput"},
        )
        assert len(result.matched) == 1
        assert result.matched[0].report_asset_id == "asset-2"

    def test_without_known_name_heuristic_still_applies(self):
        result = self._matcher().match_objects(
            [{"object_name": "USP_ACME_ED_Throughput_PBI",
              "object_type": "SQL_STORED_PROCEDURE"}],
        )
        assert len(result.matched) == 1
        assert result.matched[0].report_name == "ED Throughput"
