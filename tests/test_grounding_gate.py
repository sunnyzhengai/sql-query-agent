"""The grounding gate — acceptance fixtures are the REAL production
fabrications from the 2026-08-18 deep trace (TRACE_USP_ED_SEPSIS.md),
captured live from the demo tenant. The gate must catch every one.

Proves: law:honesty-floor
"""

import json
from pathlib import Path

import pytest

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


class TestDescVoice2:
    """DESC-VOICE-2 (Sunny's second read): "after reading the
    description, I have no idea what the SQL should look like."
    The gate stops LIES; this stops EMPTINESS. Say WHAT is
    included and on WHAT VALUES — never WHY."""

    FRAG = ("SELECT ENCOUNTER_ID FROM ORDERS "
            "WHERE ORDER_SET_ID IN (400002, 4001326025) "
            "AND CULTURE_TYPE IS NOT NULL")

    def test_her_specimen_lines_are_caught(self):
        """The SSOrderSetOSQ_PRL bullets she quoted."""
        text = ("- Encounters are included when the CULTURE_TYPE is "
                "specified, ensuring that only relevant cases are "
                "considered for analysis.\n"
                "- Encounters are included when they have an "
                "order-set ID, providing a clear link to the "
                "procedures performed.\n"
                "- critical for tracking treatment protocols")
        v = grounding_violations(text, self.FRAG)
        purpose = [x for x in v if "purpose speculation" in x]
        assert len(purpose) >= 3, v

    def test_concrete_values_pass(self):
        """Concreteness is SAFER than prose: values are already
        gate-grounded."""
        text = ("Encounters that had a sepsis order-set order.\n"
                "- one of 2 order-set IDs (400002, 4001326025)\n"
                "- a culture type is recorded")
        assert grounding_violations(text, self.FRAG) == [], \
            grounding_violations(text, self.FRAG)

    def test_source_stated_purpose_may_be_quoted(self):
        """If the SOURCE states a purpose in a comment, quoting it
        is grounded — the ban is on INVENTED purpose."""
        frag = (self.FRAG +
                " -- ensuring sepsis bundle compliance is tracked")
        text = "- ensuring sepsis bundle compliance is tracked"
        assert not [x for x in grounding_violations(text, frag)
                    if "purpose speculation" in x]

    def test_machine_floor_is_exempt(self):
        text = "- Rows where ORDER_SET_ID in (400002) ensuring x."
        assert not [x for x in
                    grounding_violations(text, self.FRAG,
                                         voice=False)
                    if "purpose speculation" in x]

    def test_prompt_placeholders_never_reach_a_steward(self):
        """P0-c find: the model echoed my own instruction's
        '<first_value>' into a description. An instruction leaking
        through as data is its own class."""
        v = grounding_violations(
            "- one of 7 IDs (first: <first_value>, last: "
            "<last_value>)", "SELECT X FROM T WHERE ID IN (1,2)")
        assert any("prompt placeholder echoed" in x for x in v), v

class TestDescWhole1Gap:
    """DESC-WHOLE-1 (found 2026-08-31, PARKED for Sunny): 13 of the
    28-proc corpus are single-SELECT report procs — no CTE, no temp
    staging. The step harvester finds nothing in them, so they get
    NO description at all. This test PINS the gap: it asserts the
    shape is real and currently unharvested, so the day someone
    builds whole-proc description it fails loudly and must be
    updated deliberately."""

    def test_single_select_procs_yield_no_steps(self):
        import glob
        import os
        import re

        from devtools.desc_live_run import harvest_steps

        corpus = sorted(glob.glob("data/synthetic/sql/**/*.sql",
                                  recursive=True))
        if not corpus:
            pytest.skip("synthetic corpus not present")
        described = {s["proc"] for s in harvest_steps()}
        silent = [p for p in corpus
                  if os.path.basename(p) not in described]
        # the gap is non-empty today
        assert silent, "whole-proc description may now be built"
        # and every silent proc is genuinely single-SELECT, i.e. the
        # harvester is not merely MISSING staged logic in them
        for path in silent:
            sql = open(path).read()
            assert not re.search(r"(?i)\bINTO\s+#", sql), path
            assert not re.search(r"(?i)\bINSERT\s+INTO\s+#", sql), path

class TestTempStepVoiceCost:
    """DESC-TEMP-1 live find (08-31, PARKED for Sunny's ruling):
    on temp-table staged steps the vocabulary rule fires on the
    bare word 'table' and empties descriptions that are otherwise
    TRUE and grounded. 3 of 11 empties in the stratified 60-step
    run had NO other violation. Whether 'table' should stay banned
    on a step that literally writes one is a VOICE ruling, not a
    dev call — this test pins the current behaviour so the ruling
    changes it deliberately."""

    def test_true_description_empties_on_the_word_table(self):
        sql = ("SELECT DISTINCT E.PATIENT_ID, E.ENCOUNTER_ID "
               "INTO #Base_Pop FROM HOSPITAL_ENCOUNTERS E "
               "WHERE E.ADMIT_DATE IS NOT NULL")
        honest = ("This is a table of encounters with a recorded "
                  "admission date.")
        v = grounding_violations(honest, sql)
        assert any("technical vocabulary" in x and "'table'" in x
                   for x in v), v
        # and the SAME sentence without the one word is clean
        clean = ("This is a selection of encounters with a recorded "
                 "admission date.")
        assert grounding_violations(clean, sql) == []

class TestDescVoice3Misattributed:
    """DESC-VOICE-3.1 (ordered 08-31 from Sunny's read #3 on
    USP_ED_SEPSIS · #BPA): the MISATTRIBUTED PREDICATE class.
    The description used the right VALUES against the wrong
    SUBJECT — "Encounter IDs must match the ADT_ARRIVAL_TIME and
    ED_DEPARTURE_TIME" when the SQL constrains ALT_ACTION_INST
    BETWEEN those two. It passed the old gate because the gate
    asked whether facts were PRESENT, never what they were
    PREDICATED OF. Red-first from the exact specimen."""

    SPECIMEN = (
        "SELECT B.ENCOUNTER_ID, AH.ALT_ACTION_INST INTO #BPA "
        "FROM #Base_Pop B "
        "INNER JOIN ALERT_HISTORY AH ON AH.ALT_ID = B.ALT_ID "
        "WHERE AH.ALT_ACTION_INST BETWEEN B.ADT_ARRIVAL_TIME "
        "AND B.ED_DEPARTURE_TIME")

    def test_wrong_subject_is_caught(self):
        bad = ("Encounter IDs must match the arrival time and the "
               "departure time.")
        v = grounding_violations(bad, self.SPECIMEN)
        assert any("misattributed" in x.lower() for x in v), v

    @pytest.mark.parametrize("line", [
        "The alert action time must be between the arrival time and "
        "the departure time.",
        "Alerts are kept only when acted on between arrival and "
        "departure times.",
        "Encounters where the alert was acted on between arrival and "
        "departure.",
        "This is a selection of alerts.",
        "- Includes encounters from the emergency department.",
    ])
    def test_honest_phrasings_do_not_fire(self, line):
        """This class can EMPTY a true description, so it is probed
        adversarially in both directions (the Row_Number
        false-positive lesson: never trust a single passing draft)."""
        v = [x for x in grounding_violations(line, self.SPECIMEN)
             if "misattributed" in x.lower()]
        assert v == [], v

    @pytest.mark.parametrize("line", [
        "Encounter IDs must match the arrival time and the departure "
        "time.",
        "Patients must be between the arrival time and the departure "
        "time.",
    ])
    def test_wrong_subjects_fire(self, line):
        v = [x for x in grounding_violations(line, self.SPECIMEN)
             if "misattributed" in x.lower()]
        assert v, line

    def test_right_subject_passes(self):
        good = ("The time the alert was acted on must fall between "
                "the arrival time and the departure time.")
        v = [x for x in grounding_violations(good, self.SPECIMEN)
             if "misattributed" in x.lower()]
        assert v == [], v

class TestDescVoice3NoColumnNames:
    """DESC-VOICE-3.2 (same order): raw COLUMN names are developer
    tokens and must not reach a steward's field — the table rule at
    column grain. BPA_LOCATOR_ID / ADT_ARRIVAL_TIME / ALT_ACTION_INST
    are the specimen's offenders. Where a column HAS a dictionary
    entry the model writes from that; where it does not, Sunny's
    ruling is a readable form of the name AND a recorded coverage
    gap — missing entries become a REPORTED Tier-1 asset, never a
    silent degradation."""

    # every flagged column must be one the fragment REFERENCES —
    # an unreferenced name is not this gate's business (fixture
    # corrected after ADT_ARRIVAL_TIME was asserted against a
    # specimen that never mentioned it)
    SPECIMEN = ("SELECT ALT.BPA_LOCATOR_ID, AH.ALT_ACTION_INST "
                "FROM ALERT_HISTORY AH JOIN #Base_Pop B "
                "ON B.ENCOUNTER_ID = AH.VISIT_ID "
                "WHERE AH.ALT_ACTION_INST >= B.ADT_ARRIVAL_TIME")

    @pytest.mark.parametrize("col", [
        "BPA_LOCATOR_ID", "ADT_ARRIVAL_TIME", "ALT_ACTION_INST",
    ])
    def test_raw_column_name_is_caught(self, col):
        bad = f"Encounters are filtered on {col} being recorded."
        v = grounding_violations(bad, self.SPECIMEN)
        assert any("column name" in x.lower() for x in v), (col, v)

    def test_business_wording_passes(self):
        good = ("Alerts are included when the time the alert was "
                "acted on is recorded.")
        v = [x for x in grounding_violations(good, self.SPECIMEN)
             if "column name" in x.lower()]
        assert v == [], v

    def test_undocumented_columns_are_reported_not_silent(self):
        """The fallback ruling: no dictionary entry => readable name
        AND a coverage gap the caller can report."""
        from src.descriptions import undocumented_columns

        gaps = undocumented_columns(self.SPECIMEN, dict_lines=[
            "  - ALT_ACTION_INST: the time the alert was acted on"])
        assert "BPA_LOCATOR_ID" in gaps
        assert "ALT_ACTION_INST" not in gaps
