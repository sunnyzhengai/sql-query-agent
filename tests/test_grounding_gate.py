"""The grounding gate — acceptance fixtures are the REAL production
fabrications from the 2026-08-18 deep trace (TRACE_USP_ED_SEPSIS.md),
captured live from the demo tenant. The gate must catch every one.

Proves: law:honesty-floor
"""

import json
from pathlib import Path

from src.descriptions import (
    enforce_grounding,
    grounding_violations,
)

_FX = json.load(open(Path(__file__).parent / "fixtures" / "grounding"
                     / "usp_ed_sepsis_fabrications.json"))
BASE_POP_FRAGMENT = _FX["base_pop_fragment"]
BASE_POP_GENERATED = _FX["base_pop_generated"]
LDA_FRAGMENT = _FX["lda_fragment"]
LDA_GENERATED = _FX["lda_generated"]


class TestRealFabricationsAreCaught:
    def test_base_pop_invented_filters_flagged(self):
        v = grounding_violations(BASE_POP_GENERATED, BASE_POP_FRAGMENT)
        text = " ".join(v).lower()
        assert "pending or cancelled" in text, v
        # triage columns are SELECTed, never filtered — the precise
        # mechanism the trace identified
        assert "triage" in text, v

    def test_lda_invented_codes_flagged(self):
        v = grounding_violations(LDA_GENERATED, LDA_FRAGMENT)
        joined = " ".join(v)
        assert any(code in joined for code in ("123", "456", "789", "101")), v

    def test_enforce_strips_fabricated_lines_keeps_grounded(self):
        cleaned, removed = enforce_grounding(
            BASE_POP_GENERATED, BASE_POP_FRAGMENT)
        assert removed, "the known fabrications must be removed"
        if cleaned:
            assert not grounding_violations(cleaned, BASE_POP_FRAGMENT)
            assert "pending or cancelled" not in cleaned


class TestGroundedTextPasses:
    def test_true_claims_with_real_values_pass(self):
        fragment = (
            "SELECT ENCOUNTER_ID, MEAS_VALUE, RECORDED_TIME "
            "INTO #Scores FROM #Flowsheets "
            "WHERE RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME "
            "AND FLO_MEAS_ID IN ('9000161709', '9000002613')"
        )
        good = (
            "This step produces sepsis screening scores recorded during "
            "the emergency stay.\n"
            "- Includes only scores recorded between arrival and departure.\n"
            "- Limited to screening score codes '9000161709' and '9000002613'."
        )
        assert grounding_violations(good, fragment) == []

    def test_invented_threshold_fails(self):
        fragment = "SELECT a FROM t WHERE score > 4"
        bad = "Produces scores.\n- Includes only scores above 40."
        assert grounding_violations(bad, fragment)

    def test_no_decision_lines_no_noise(self):
        fragment = "SELECT a, b FROM #prior"
        # DESC-VOICE-1: "columns" is developer vocabulary — the
        # steward voice says what carries forward, not how
        text = "This step carries forward the prior results."
        assert grounding_violations(text, fragment) == []


class TestDialectAwareness:
    """Field find (tenant 600 rerun, 2026-08-20): the selected-not-
    filtered heuristic reads SQL structure (WHERE/ON windows) and
    misfires on DAX and composed prose, stripping legitimate text
    until whole descriptions emptied."""

    DAX = ('CALCULATE(COUNTROWS(gov_feedback_events), '
           'gov_feedback_events[verdict] = "not_helpful")')
    CLAIM = ('- Filters on feedback events where the verdict equals '
             '"not_helpful."')

    def test_dax_filter_claim_misfires_under_sql_rules(self):
        # documents the misfire this class exists to prevent
        out = grounding_violations(self.CLAIM, self.DAX, None)
        assert any("selected-not-filtered" in v for v in out)

    def test_dax_dialect_accepts_calculate_filters(self):
        assert grounding_violations(self.CLAIM, self.DAX, None,
                                    dialect="dax") == []

    def test_dax_dialect_still_rejects_invented_values(self):
        out = grounding_violations(
            "- Filters on scores above 9000.", self.DAX, None, dialect="dax")
        assert any("9000" in v for v in out)

    def test_prose_dialect_grounds_prompt_supplied_step_count(self):
        text = "This metric is computed through 122 steps."
        roots_ground = "Counts qualifying encounters."
        assert any("122" in v for v in grounding_violations(
            text, roots_ground, None, dialect="prose"))
        assert grounding_violations(
            text, roots_ground, ["USP_Severe_Sepsis", "122", "FinalData"],
            dialect="prose") == []


# --- P0-a (DESC-GATE-2): TABLE + GRAIN claims, red-first per class ---

DX_FRAGMENT = """
SELECT DISTINCT DC.PATIENT_ID
FROM DIAGNOSIS_CODES DC
JOIN ENCOUNTERS E ON E.PATIENT_ID = DC.PATIENT_ID
WHERE DC.ICD_CODE LIKE 'E11%'
"""

# a TRUE visit-grain query: the row is the encounter, and no
# patient key is projected (a select carrying BOTH keys evidences
# both grains — the gate must not refuse a claim the SQL supports)
VISIT_FRAGMENT = """
SELECT E.ENCOUNTER_ID, E.DEPARTMENT
FROM ENCOUNTERS E
WHERE E.DEPARTMENT = 'ED'
"""


class TestTableClaims:
    """A description may name only tables the fragment reads —
    naming another invents provenance (P0-a)."""

    def test_ungrounded_table_is_a_violation(self):
        text = ("- Diabetic patients identified from DIAGNOSIS_CODES\n"
                "- joined to LAB_RESULTS for confirmation")
        v = grounding_violations(text, DX_FRAGMENT)
        assert any("ungrounded table claim" in x and "LAB_RESULTS" in x
                   for x in v), v

    def test_read_tables_pass(self):
        text = ("- Diabetic patients from DIAGNOSIS_CODES\n"
                "- joined to ENCOUNTERS")
        v = grounding_violations(text, DX_FRAGMENT)
        assert not any("ungrounded table claim" in x for x in v), v

    def test_a_cte_name_is_not_a_base_table(self):
        frag = ("WITH BASE_COHORT AS (SELECT PATIENT_ID FROM "
                "DIAGNOSIS_CODES) SELECT * FROM BASE_COHORT")
        # naming the CTE is fine (it is in the text); naming an
        # unrelated table is not
        assert not any("ungrounded table claim" in x for x in
                       grounding_violations("- from BASE_COHORT", frag))
        assert any("ungrounded table claim" in x for x in
                   grounding_violations("- from BILLING_CLAIMS", frag))

    def test_dictionary_named_tables_are_grounded(self):
        text = "- patients from DIAGNOSIS_CODES per PATIENT_ROSTER"
        v = grounding_violations(text, DX_FRAGMENT,
                                 dict_lines=["PATIENT_ROSTER: the panel"])
        assert not any("ungrounded table claim" in x for x in v), v


class TestGrainClaims:
    """The counted entity must match the parsed keys — a wrong grain
    claim reads fluent and is false (P0-a)."""

    def test_visit_grain_claimed_as_patients_is_a_violation(self):
        text = "- counts patients seen in the emergency department"
        v = grounding_violations(text, VISIT_FRAGMENT)
        assert any("grain claim" in x for x in v), v

    def test_matching_grain_passes(self):
        text = "- counts distinct patients with a diabetes diagnosis"
        v = grounding_violations(text, DX_FRAGMENT)
        assert not any("grain claim" in x for x in v), v

    def test_both_keys_projected_evidences_both_grains(self):
        """Honesty in the other direction: a select carrying
        ENCOUNTER_ID *and* PATIENT_ID supports either claim — the
        gate refuses only what the SQL contradicts."""
        both = ("SELECT E.ENCOUNTER_ID, E.PATIENT_ID "
                "FROM ENCOUNTERS E")
        for claim in ("- counts patients", "- counts visits"):
            v = grounding_violations(claim, both)
            assert not any("grain claim" in x for x in v), (claim, v)

    def test_unknown_grain_refuses_nothing(self):
        # no key columns to read → the gate must not guess
        frag = "SELECT 1 AS FLAG"
        text = "- counts patients"
        v = grounding_violations(text, frag)
        assert not any("grain claim" in x for x in v), v

    def test_dax_and_prose_skip_the_sql_only_classes(self):
        text = "- counts patients from LAB_RESULTS"
        for dialect in ("dax", "prose"):
            v = grounding_violations(text, VISIT_FRAGMENT,
                                     dialect=dialect)
            assert not any("grain claim" in x or "table claim" in x
                           for x in v), (dialect, v)


class TestP0bCorpusFindings:
    """P0-b live-run findings, pinned as fixtures so the classes the
    corpus exposed cannot regress."""

    def test_interpretive_tail_is_caught(self):
        """The live generator's characteristic failure: an accurate
        description followed by a CLINICAL INFERENCE the SQL does
        not support ("helps identify patients who may require
        outreach"). Caught as an ungrounded filter claim; the
        corrective retry removed it in every live case."""
        frag = ("SELECT LR.PATIENT_ID FROM LAB_RESULTS LR "
                "WHERE LR.HBA1C_VALUE >= 6.5")
        text = ("- selects PATIENT_ID from LAB_RESULTS\n"
                "- the selection requires HBA1C_VALUE of at least "
                "6.5\n"
                "- By filtering on this threshold, the query helps "
                "in targeting individuals who may require further "
                "medical evaluation or intervention.")
        v = grounding_violations(text, frag)
        assert any("targeting individuals" in x for x in v), v

    def test_alias_does_not_leak_into_grain(self):
        """Dry-run find: FROM ENCOUNTER_DIAGNOSIS ED made every
        column look encounter-grained, so a patient claim wrongly
        violated. Keys are read from KEY COLUMNS, not table names."""
        from src.descriptions import parsed_grain
        frag = ("SELECT DISTINCT ED.PATIENT_ID FROM "
                "ENCOUNTER_DIAGNOSIS ED WHERE ED.DX_CODE "
                "LIKE 'E11%'")
        assert parsed_grain(frag) == {"patient"}
        v = grounding_violations("- counts patients", frag)
        assert not any("grain claim" in x for x in v), v

    def test_encounter_shaped_keys_are_visit_grain(self):
        from src.descriptions import parsed_grain
        frag = ("SELECT HE.HOSP_ENC_ID, HE.ADMIT_DATE FROM "
                "HOSPITAL_ENCOUNTERS HE WHERE "
                "HE.ENCOUNTER_TYPE = 'ED'")
        assert parsed_grain(frag) == {"visit"}
        assert any("grain claim" in x for x in
                   grounding_violations("- counts patients", frag))


class TestDescVoice1:
    """DESC-VOICE-1 (Sunny's grading, 2026-08-31): her verdict on
    ACCURACY was clean — these are VOICE rules. A steward's field
    must not carry a developer's sentence."""

    CULTURES = ("SELECT ENCOUNTER_ID FROM #Labs_and_Cultures L "
                "JOIN ORGANISMS O ON O.ID = L.ORG_ID "
                "WHERE L.RESULT = 'POSITIVE'")

    def test_her_exact_examples_are_caught(self):
        """The two sentences she flagged in the P0-c sample."""
        v = grounding_violations(
            "- This step selects from the temporary table "
            "#Labs_and_Cultures\n"
            "- the join with the ORGANISMS table enriches the "
            "dataset", self.CULTURES)
        joined = " ".join(v)
        assert "#Labs_and_Cultures" in joined
        assert "'temporary table'" in joined
        assert "'join'" in joined
        assert "'dataset'" in joined

    def test_the_steward_voice_passes(self):
        """Her 'All_LDAs' example — the model already doing it
        right — must not be floored."""
        v = grounding_violations(
            "- encounters are included when a culture result is "
            "positive", self.CULTURES)
        assert v == [], v

    def test_subject_comes_from_parsed_grain(self):
        from src.descriptions import subject_for
        assert subject_for(self.CULTURES) == "encounters"
        assert subject_for("SELECT DISTINCT PATIENT_ID FROM T") == \
            "patients"
        assert subject_for("SELECT ORDER_MED_ID FROM MEDS") == \
            "medication orders"
        # unknown grain falls back to 'records' — a signal, not a
        # default we are comfortable with
        assert subject_for("SELECT 1 AS FLAG") == "records"

    def test_acronym_expansion_must_be_grounded(self):
        frag = "CASE WHEN LINE_TYPE = 'ETT' THEN 1 END -- ETT lines"
        bad = grounding_violations(
            "- endotracheal tubes (ETT) are counted", frag)
        assert any("ungrounded acronym expansion" in x for x in bad)
        # the acronym alone is fine — it is what the source wrote
        assert grounding_violations("- ETT lines are counted",
                                    frag) == []
        # and a dictionary expansion IS grounded
        assert grounding_violations(
            "- endotracheal tubes (ETT) are counted", frag,
            dict_lines=["ETT: endotracheal tube"]) == []

    def test_machine_composed_text_is_not_voice_policed(self):
        """The template floor is stilted truth by design — policing
        its voice would floor the floor."""
        machine = "Rows from #Staging where STATUS = 'A'."
        assert grounding_violations(machine, "SELECT * FROM #Staging "
                                    "WHERE STATUS = 'A'",
                                    voice=False) == []
        assert grounding_violations(machine, "SELECT * FROM #Staging "
                                    "WHERE STATUS = 'A'") != []

    def test_row_number_is_a_computation_not_developer_voice(self):
        """P0-c variance find: 'Row_Number' names a real ranking the
        SQL computes; flooring it emptied an otherwise-honest
        description. 'the rows', as a subject, stays caught."""
        frag = "SELECT ROW_NUMBER() OVER (ORDER BY IN_DTTM) FROM X"
        assert grounding_violations(
            "- Row_Number orders each stay by arrival time",
            frag) == []
        assert any("'rows'" in x for x in grounding_violations(
            "- the rows are filtered to positives", frag))
