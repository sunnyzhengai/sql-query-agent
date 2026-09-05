"""Slice 2: the PHI boundary — both doors, fixture-driven.

Door 1 acceptance floor: the ported rule behaviors (contact/id/name
redact on SQL text; dates/thresholds counted, deferred to egress —
derived from the ratified F2 key keeping analytical dates verbatim).
Door 2 acceptance: the authored phi_door2.json fixtures (PM-1's owed
fixtures), exercised now because the gate is pure.
"""
import json
import pathlib

from aivia.graph import phi_gate

DOOR2 = pathlib.Path(__file__).resolve().parents[2] / \
    "AIVIA_Product" / "fixtures" / "F6_refusals" / "phi_door2.json"


def test_door1_redacts_high_severity_literals():
    sql = ("SELECT * FROM PT WHERE PAT_MRN = '12345678' "
           "AND PATIENT_NAME = 'JANE DOE' AND SSN = '123-45-6789'")
    result = phi_gate.door1_redact(sql)
    assert "12345678" not in result.text
    assert "JANE DOE" not in result.text
    assert "123-45-6789" not in result.text
    assert result.redaction_count == 3


def test_door1_keeps_analytical_dates_verbatim_but_counts_them():
    sql = "SELECT 1 FROM E WHERE VISIT_DATE >= '2026-01-01'"
    result = phi_gate.door1_redact(sql)
    assert "'2026-01-01'" in result.text  # the ratified F2 key's law
    assert result.redaction_count == 0
    assert result.counted_findings.get("date_literal") == 1


def test_door1_thresholds_counted_never_redacted():
    sql = "SELECT 1 FROM E WHERE LOS_DAYS > 30"
    result = phi_gate.door1_redact(sql)
    assert result.text == sql
    assert result.counted_findings.get("threshold_literal") == 1


def test_door1_parameters_never_match():
    sql = "SELECT 1 FROM E WHERE VISIT_DATE >= @StartDate"
    result = phi_gate.door1_redact(sql)
    assert result.text == sql
    assert result.redaction_count == 0


def test_door2_fixture_cases():
    cases = json.loads(DOOR2.read_text())["cases"]
    assert len(cases) >= 9
    for case in cases:
        result = phi_gate.door2_redact(case["payload"])
        assert result.text == case["redacted"], case["id"]
        assert result.redaction_count == case["count"], case["id"]


def test_estate_fixture_sql_passes_untouched():
    est = pathlib.Path(__file__).resolve().parents[2] / \
        "AIVIA_Product" / "fixtures" / "F2_estate_files" / "estate_snapshot"
    for path in est.glob("*.sql"):
        text = path.read_text()
        assert phi_gate.door1_redact(text).text == text, path.name
