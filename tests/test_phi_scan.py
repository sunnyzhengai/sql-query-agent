"""Tests for PHI / hardcoded-literal scanning (ADR 0025)."""

from src.phi_scan import (
    PLACEHOLDERS,
    apply_dispositions,
    redact,
    scan_sql,
    to_records,
)
from src.schemas import PHI_FINDINGS


def rules_of(findings):
    return [f.rule for f in findings]


class TestRules:
    def test_ssn_shape_is_contact(self):
        f = scan_sql("m", "WHERE ssn = '123-45-6789'")
        assert rules_of(f) == ["contact_literal"]
        assert f[0].severity == "high" and f[0].disposition == "redact"

    def test_email_and_phone_are_contact(self):
        f = scan_sql("m", "WHERE email = 'a.b@example.com' OR phone = '312-555-1234'")
        assert rules_of(f) == ["contact_literal", "contact_literal"]

    def test_id_literal_against_id_column(self):
        f = scan_sql("m", "WHERE peh.PAT_ENC_CSN_ID = 123456789")
        assert rules_of(f) == ["id_literal"]
        assert f[0].matched_text == "123456789"

    def test_id_in_list_flags_every_member(self):
        f = scan_sql("m", "WHERE PAT_MRN_ID IN (1234567, 7654321, 1112223)")
        assert rules_of(f) == ["id_literal"] * 3
        assert {x.matched_text for x in f} == {"1234567", "7654321", "1112223"}

    def test_quoted_in_list_members_all_flagged_and_redacted(self):
        sql = "AND meas.FLO_MEAS_ID in ('9000002731','9000002732','9000002733')"
        f = scan_sql("m", sql)
        assert len(f) == 3
        out = redact(sql, f)
        assert "9000002" not in out and out.count("<ID>") == 3

    def test_name_literal_against_name_column(self):
        f = scan_sql("m", "WHERE PROVIDER_NAME LIKE '%SMITH%'")
        assert rules_of(f) == ["name_literal"]
        assert f[0].matched_text == "'%SMITH%'"

    def test_date_literals(self):
        f = scan_sql("m", "BETWEEN '2023-01-01' AND '2023-12-31 23:59:59'")
        assert rules_of(f) == ["date_literal", "date_literal"]
        assert f[0].severity == "medium"

    def test_threshold_is_low_and_open(self):
        f = scan_sql("m", "WHERE lactate.RESULT_VALUE >= 2.0")
        assert rules_of(f) == ["threshold_literal"]
        assert f[0].severity == "low" and f[0].disposition == "open"

    def test_parameters_never_match(self):
        assert scan_sql("m", "WHERE dt BETWEEN @dStartDate AND @dEndDate") == []

    def test_short_numbers_against_id_columns_ignored(self):
        # LINE = 1, ORDER_ID = 3 — join/positional plumbing, not identifiers
        assert scan_sql("m", "WHERE ped.LINE = 1 AND x.GROUP_ID = 3") == []

    def test_no_double_claim_across_rules(self):
        # the SSN must not re-fire as anything else
        f = scan_sql("m", "WHERE ssn = '123-45-6789'")
        assert len(f) == 1

    def test_empty_sql(self):
        assert scan_sql("m", "") == []


class TestRedaction:
    def test_redacts_only_redact_disposition(self):
        sql = "WHERE PAT_ENC_CSN_ID = 123456789 AND score >= 2"
        findings = scan_sql("m", sql)
        out = redact(sql, findings)
        assert "123456789" not in out and "<ID>" in out
        assert ">= 2" in out  # threshold left alone (open)

    def test_datetime_inside_date_no_fragments(self):
        sql = "BETWEEN '2023-01-01' AND '2023-01-01 23:59:59'"
        out = redact(sql, scan_sql("m", sql))
        assert "2023" not in out
        assert out.count("<DATE>") == 2

    def test_context_is_masked(self):
        f = scan_sql("m", "WHERE PAT_MRN_ID = 99887766 -- lookup")
        assert "99887766" not in f[0].masked_context
        assert "<ID>" in f[0].masked_context


class TestPersistence:
    def test_records_match_contract_columns(self):
        f = scan_sql("m", "WHERE PAT_MRN_ID = 1234567")
        record = to_records(f, first_seen="2026-08-06T00:00:00Z")[0]
        contract_cols = {c[0] for c in PHI_FINDINGS["columns"]}
        assert set(record.keys()) == contract_cols

    def test_finding_id_stable_across_scans(self):
        a = scan_sql("m", "WHERE PAT_MRN_ID = 1234567")[0]
        b = scan_sql("m", "WHERE PAT_MRN_ID = 1234567")[0]
        assert a.finding_id == b.finding_id

    def test_steward_allow_survives_rescan(self):
        sql = "WHERE PAT_MRN_ID = 1234567"
        first = scan_sql("m", sql)
        persisted = to_records(first)
        persisted[0]["disposition"] = "allow"  # steward: false positive
        rescanned = apply_dispositions(scan_sql("m", sql), persisted)
        assert rescanned[0].disposition == "allow"
        assert redact(sql, rescanned) == sql  # allow => not redacted

    def test_steward_redact_on_threshold_survives(self):
        sql = "WHERE age_days < 21"
        first = to_records(scan_sql("m", sql))
        first[0]["disposition"] = "redact"
        rescanned = apply_dispositions(scan_sql("m", sql), first)
        out = redact(sql, rescanned)
        assert "21" not in out and PLACEHOLDERS["threshold_literal"] in out
