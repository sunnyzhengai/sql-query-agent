"""DESC-SKELETON-3 — the AST-first composer (ADR 0074 / the ruled
re-cut, 7e506a5): compose_skeleton consumes the faithful decision
tree (ScriptDom, scope-aware), never regex over SQL text. Fixtures
are the four decoy-class corpses the independent probe found
(864af2f) plus the derived-table leak (8a8f13d) — every one a real
failure of the regex composer, red-first.

Proves: spec:B2, spec:G2
"""

from __future__ import annotations

import inspect

from src.descriptions import compose_skeleton

M = {"RESULT_FLAG": "lab result flag", "ADMIT_DATE": "admission date",
     "ENCOUNTER_TYPE": "encounter type", "PATIENT_CLASS": "patient class",
     "LACTATE_LEVEL": "lactate level", "DEPT_NAME": "department name"}


class TestScopeAwareness:
    def test_derived_table_filter_stays_out_of_the_outer_claims(self):
        """The 8a8f13d leak: the derived table's WHERE is ITS decision,
        not the outer step's."""
        frag = ("SELECT e.PATIENT_ID FROM HOSPITAL_ENCOUNTERS e "
                "JOIN (SELECT ENCOUNTER_ID FROM LAB_RESULTS "
                "WHERE RESULT_FLAG = 'ABNORMAL') d "
                "ON d.ENCOUNTER_ID = e.ENCOUNTER_ID "
                "WHERE e.ADMIT_DATE IS NOT NULL")
        sk = compose_skeleton(frag, M)
        assert "ABNORMAL" not in sk
        assert "admission date is recorded" in sk

    def test_in_subquery_inner_filter_stays_out(self):
        frag = ("SELECT PATIENT_ID FROM HOSPITAL_ENCOUNTERS WHERE "
                "ENCOUNTER_ID IN (SELECT ENCOUNTER_ID FROM LAB_RESULTS "
                "WHERE LACTATE_LEVEL > 2) AND ENCOUNTER_TYPE = 'ED'")
        sk = compose_skeleton(frag, M)
        assert "lactate" not in sk.lower()
        assert "encounter type is 'ED'" in sk


class TestDecoyClasses:
    def test_not_exists_is_voiced_not_silent(self):
        """Decoy 1: the regex composer had nothing for EXISTS shapes —
        an exclusion criterion vanished from the description."""
        frag = ("SELECT e.PATIENT_ID FROM HOSPITAL_ENCOUNTERS e WHERE "
                "NOT EXISTS (SELECT 1 FROM LAB_RESULTS l "
                "WHERE l.ENCOUNTER_ID = e.ENCOUNTER_ID) "
                "AND e.ADMIT_DATE IS NOT NULL")
        sk = compose_skeleton(frag, M)
        assert "no matching" in sk.lower() or "excludes" in sk.lower()

    def test_having_is_kept(self):
        """Decoy 2: HAVING dropped — the threshold that DEFINES a
        high-utilizer step disappeared."""
        frag = ("SELECT PATIENT_ID, COUNT(*) FROM HOSPITAL_ENCOUNTERS "
                "GROUP BY PATIENT_ID HAVING COUNT(*) >= 4")
        sk = compose_skeleton(frag, M)
        assert "4" in sk and "at least" in sk

    def test_or_is_not_flattened_to_and(self):
        """Decoy 3: the LDA lesson at composer grain — an OR rendered
        as two independent bullets silently changes meaning."""
        frag = ("SELECT PATIENT_ID FROM HOSPITAL_ENCOUNTERS WHERE "
                "ENCOUNTER_TYPE = 'ED' OR PATIENT_CLASS = 'INPATIENT'")
        sk = compose_skeleton(frag, M)
        joined = [ln for ln in sk.splitlines()
                  if "'ED'" in ln and "'INPATIENT'" in ln]
        assert joined, f"OR split across bullets:\n{sk}"
        assert " or " in joined[0].lower()

    def test_select_case_is_not_a_phantom_filter(self):
        """Decoy 4: CASE WHEN in the SELECT list is a projection
        choice; the regex composer claimed it filtered membership."""
        frag = ("SELECT PATIENT_ID, CASE WHEN DEPT_NAME = 'ICU' THEN 1 "
                "ELSE 0 END AS IS_ICU FROM HOSPITAL_ENCOUNTERS "
                "WHERE ADMIT_DATE IS NOT NULL")
        sk = compose_skeleton(frag, M)
        assert "'ICU'" not in sk, f"phantom filter:\n{sk}"


class TestGateRegex1:
    def test_the_composer_uses_no_regex_on_sql(self):
        """GATE-REGEX-1 (ruled with the re-cut, 7e506a5): parsing SQL
        with regex violates the native-parser law's spirit (spec:G2);
        the composer walks the ScriptDom tree."""
        src = inspect.getsource(compose_skeleton)
        assert "re." not in src and "findall" not in src
        import src.descriptions as d
        for banned in ("_IN_LIST", "_BETWEEN", "_COMPARISON", "_IS_NULL"):
            assert not hasattr(d, banned), f"{banned} still exists"
