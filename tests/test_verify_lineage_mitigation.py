"""L0 tests for the lineage-mitigation verifier's answer check
(HANDOFF_FABRIC_LINEAGE_MITIGATION item 4). The checker owns the
pass/fail semantics: every expected name carried, zero cousin-family
leakage, with the also-expected carve-out."""

from devtools.verify_lineage_mitigation import check

EXPECTED = ["Sepsis Case Details", "Sepsis Case Encounters"]
FORBIDDEN = ["Sepsis Patient Timeline", "Sepsis Case Encounters"]


def test_full_carry_no_leak_passes():
    r = check("Readers: Sepsis Case Details and Sepsis Case Encounters.",
              EXPECTED, FORBIDDEN)
    assert r["ok"] is True
    assert r["absent"] == [] and r["cousin_leak"] == []


def test_absent_expected_name_fails():
    r = check("Only Sepsis Case Details reads it.", EXPECTED, FORBIDDEN)
    assert r["ok"] is False
    assert r["absent"] == ["Sepsis Case Encounters"]


def test_cousin_leak_fails_even_with_full_carry():
    r = check("Sepsis Case Details, Sepsis Case Encounters, and "
              "Sepsis Patient Timeline.", EXPECTED, FORBIDDEN)
    assert r["ok"] is False
    assert r["cousin_leak"] == ["Sepsis Patient Timeline"]


def test_forbidden_name_that_is_also_expected_is_not_a_leak():
    # 'Sepsis Case Encounters' reads BOTH tables — carrying it must
    # never count as cousin leakage
    r = check("Sepsis Case Details and Sepsis Case Encounters.",
              EXPECTED, FORBIDDEN)
    assert r["cousin_leak"] == []


def test_matching_is_case_insensitive():
    r = check("sepsis case details; SEPSIS CASE ENCOUNTERS",
              EXPECTED, FORBIDDEN)
    assert r["ok"] is True


def test_empty_answer_fails_with_all_absent():
    r = check("", EXPECTED, FORBIDDEN)
    assert r["ok"] is False
    assert r["absent"] == EXPECTED
