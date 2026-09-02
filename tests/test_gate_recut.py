"""GATE-RECUT (ordered by Sunny 2026-09-02): the gate's SQL side
consumes the parser, never regex — the composer's cut (SKELETON-3),
applied to the checker. Pattern ancestor (spec:G4 clause 3): the
faithful-tree consumption of ADR 0044 phase 1 / DESC-SKELETON-3.

Designed BEFORE code, per the check contract:
- OUTCOME VOCABULARY (closed): query_shape(fragment) -> QueryShape
  with parse_ok ∈ {True, False}; False ⇒ every evidence field empty ⇒
  the gate's standing law applies (absence of evidence refuses no
  claim) and the failure is VISIBLE on the shape — no silent third
  state, no regex fallback (the SQL regexes are DELETED).
- Every fixture below is an INJECTED VIOLATION of a known class
  (G4 clause 2, pinned): the 240-char window false positive, the
  derived-scope false negative (the 3a leak's checker-side mirror),
  the subquery grain misread.

Proves: spec:G4, spec:B2
"""

from __future__ import annotations

from src.descriptions import grounding_violations, parsed_grain

DERIVED = ("SELECT e.PATIENT_ID FROM HOSPITAL_ENCOUNTERS e "
           "JOIN (SELECT ENCOUNTER_ID FROM LAB_RESULTS "
           "WHERE RESULT_FLAG = 'ABNORMAL') d "
           "ON d.ENCOUNTER_ID = e.ENCOUNTER_ID "
           "WHERE e.ADMIT_DATE IS NOT NULL")


class TestQueryShapeContract:
    def test_outcomes_are_closed_and_failure_is_visible(self):
        from src.tree.extract import query_shape
        ok = query_shape("SELECT PATIENT_ID FROM ENCOUNTERS "
                         "WHERE ADMIT_DATE IS NOT NULL")
        assert ok.parse_ok and "ENCOUNTERS" in ok.base_tables
        bad = query_shape("THIS IS NOT SQL ((((")
        assert bad.parse_ok is False
        assert not (bad.base_tables or bad.deciding_exprs
                    or bad.select_cols or bad.key_cols)

    def test_own_ctes_and_derived_aliases_are_not_reads(self):
        from src.tree.extract import query_shape
        frag = ("WITH Eligible AS (SELECT ENCOUNTER_ID FROM "
                "HOSPITAL_ENCOUNTERS WHERE ADMIT_DATE IS NOT NULL) "
                "SELECT e.ENCOUNTER_ID FROM Eligible e "
                "JOIN #Base_Pop b ON b.ENCOUNTER_ID = e.ENCOUNTER_ID")
        s = query_shape(frag)
        assert "HOSPITAL_ENCOUNTERS" in s.base_tables
        assert "#Base_Pop".upper() in {t.upper() for t in s.base_tables}
        assert "ELIGIBLE" not in {t.upper() for t in s.base_tables}


class TestWindowTruncationFalsePositiveDies:
    def test_a_true_claim_past_240_chars_is_not_flagged(self):
        """The old deciding-window regex read 240 chars after WHERE;
        a real condition past a long IN-list fell outside it and a
        TRUE sentence got flagged. The tree has no window."""
        long_in = ", ".join(f"'{i:05d}'" for i in range(40))
        frag = (f"SELECT PATIENT_ID FROM HOSPITAL_ENCOUNTERS WHERE "
                f"DEPT_CODE IN ({long_in}) "
                f"AND DISCHARGE_DATE IS NOT NULL")
        text = "Includes only rows where the discharge date is recorded."
        v = [x for x in grounding_violations(text, frag)
             if "discharge" in x.lower() or "selected-not-filtered"
             in x.lower() or "filter" in x.lower()]
        assert v == [], f"true claim flagged: {v}"


class TestDerivedScopeFalseNegativeDies:
    def test_claiming_the_inner_filter_now_violates(self):
        """The checker-side mirror of the 3a leak: the old window
        happily included the derived table's text, so a smoothed
        sentence claiming the INNER filter passed. Outer-scope
        deciding facts must reject it."""
        text = ("- Includes only encounters whose lab result "
                "flag is 'ABNORMAL'.")
        v = grounding_violations(text, DERIVED)
        assert v, ("the inner-scope claim passed the gate — the 3a "
                   "mirror is still open")


class TestGrainIsOuterScope:
    def test_subquery_group_by_does_not_set_the_outer_grain(self):
        frag = ("SELECT v.VISIT_ID FROM VISITS v JOIN "
                "(SELECT PATIENT_ID FROM HOSPITAL_ENCOUNTERS "
                "GROUP BY PATIENT_ID) p ON p.PATIENT_ID = v.PATIENT_ID")
        assert parsed_grain(frag) == {"visit"}, (
            "the derived GROUP BY leaked into the outer grain")
