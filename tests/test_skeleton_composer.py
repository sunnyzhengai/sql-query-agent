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
        the composer walks the ScriptDom tree. Coverage: the WHOLE
        composer surface (helpers included), by AST — a substring scan
        false-positives on names like `bare.upper()` (found while
        answering Sunny's no-silent-fallback question, 09-02)."""
        import ast

        import src.descriptions as d
        surface = (compose_skeleton, d._leaf_phrase, d._render,
                   d._values_from, d.meaning_of, d.describe_step)
        for fn in surface:
            tree = ast.parse(inspect.getsource(fn).lstrip())
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "re"):
                    raise AssertionError(
                        f"{fn.__name__} uses re.{node.attr}")
        for banned in ("_IN_LIST", "_BETWEEN", "_COMPARISON", "_IS_NULL",
                       "_JOIN_KEYS"):
            assert not hasattr(d, banned), f"{banned} still exists"

    def test_no_silent_regex_fallback_exists(self):
        """Sunny's question, answered structurally: there is no code
        path from the composer to any regex parser — the regex
        composer was DELETED, not demoted to a fallback. The only
        degradation on parse failure is CLAIMS OMITTED (the lead line
        alone, grounded and true), never a different parser."""
        src = inspect.getsource(compose_skeleton)
        assert "sqlglot" not in src and "sqlparse" not in src
        sk = compose_skeleton("THIS IS NOT SQL AT ALL ((((")
        assert sk.startswith("This is a selection of")
        assert "\n-" not in sk, "an unparseable fragment produced claims"


class TestRegexFrontier:
    """Q1's lesson (Sunny, 09-02), mechanized: a ban is a FRONTIER plus
    a mechanism. The sloppy first ban checked a hand-picked function by
    substring; this check enumerates descriptions.py's ENTIRE regex
    surface as data, deny-by-default — a new function reaching for `re`
    fails CI until it is deliberately sanctioned or the debt list
    grows on the record (the capability-registry G2 pattern, applied
    at module grain)."""

    # English/identifier munging — regex on TEXT is legitimate here.
    # (The list grew 09-02 when the scanner learned to see
    # module-level compiled patterns — its own first blind spot.)
    SANCTIONED_TEXT_SIDE = {
        "_column_words", "readable_column", "_stem",
        "column_name_violations", "misattribution_violations",
        "grounding_violations", "_grain_violations",
        "_table_violations", "generate_descriptions",
        "metric_scope_violations", "placeholder_violations",
        "purpose_violations", "voice_violations",
        "_dict_meanings",   # parses '- NAME: desc' dictionary LINES
    }
    # Regex ON SQL: EMPTY since the gate recut (2026-09-02) —
    # parsed_grain / parsed_tables / parsed_columns / _condition_text
    # all consume tree.query_shape now; their regexes are deleted.
    # A new entry here requires its own recorded reason.
    DEBT_SQL_SIDE: "set[str]" = set()

    def test_the_regex_frontier_is_enumerated_and_closed(self):
        from pathlib import Path

        from tests.test_check_contract import regex_users  # G4: the
        # scanner is shared and META-TESTED (the tester is tested)
        src = (Path(__file__).resolve().parent.parent
               / "src" / "descriptions.py").read_text()
        users = regex_users(src)
        allowed = self.SANCTIONED_TEXT_SIDE | self.DEBT_SQL_SIDE
        new = sorted(users - allowed)
        assert not new, (
            f"NEW regex user(s) in descriptions.py: {new} — sanction "
            f"deliberately (text-side) or record as SQL-side debt; "
            f"never silently")
        gone = sorted(allowed - users)
        assert not gone, (
            f"frontier stale — no longer using re: {gone} (a debt item "
            f"retired? update the list so the record matches reality)")


class TestLeafVoicing:
    """DESC-LEAF-1 (ordered 09-02, extended by Sunny's hand-grade of
    the live corpus): the composer voices the full leaf frontier —
    {LIKE, NOT_LIKE, NOT_IN, NOT_BETWEEN} plus aggregate subjects —
    instead of degrading to placeholders. Pattern ancestor (spec:G4
    clause 3): the four decoy corpses above; these are the corpus
    run's three empties and one mush-pass, red-first."""

    DX = {"DX_CODE": "diagnosis code", "MED_NAME": "medication name",
          "ENCOUNTER_ID": "encounter id", "HBA1C_VALUE": "hba1c value"}

    def test_prefix_like_voices_starts_with(self):
        frag = ("SELECT PATIENT_ID FROM ENCOUNTER_DIAGNOSIS "
                "WHERE DX_CODE LIKE 'E11%'")
        sk = compose_skeleton(frag, self.DX)
        assert "diagnosis code starts with 'E11'" in sk
        assert "condition holds" not in sk and "`" not in sk

    def test_not_like_voices_the_negation(self):
        frag = ("SELECT PATIENT_ID FROM ENCOUNTER_DIAGNOSIS "
                "WHERE DX_CODE NOT LIKE 'O24.4%'")
        sk = compose_skeleton(frag, self.DX)
        assert "diagnosis code does not start with 'O24.4'" in sk

    def test_contains_and_ends_with_patterns(self):
        sk1 = compose_skeleton(
            "SELECT PATIENT_ID FROM ENCOUNTER_DIAGNOSIS "
            "WHERE DX_CODE LIKE '%KETO%'", self.DX)
        assert "diagnosis code contains 'KETO'" in sk1
        sk2 = compose_skeleton(
            "SELECT PATIENT_ID FROM ENCOUNTER_DIAGNOSIS "
            "WHERE DX_CODE LIKE '%.9'", self.DX)
        assert "diagnosis code ends with '.9'" in sk2

    def test_irregular_pattern_stays_verbatim(self):
        """A pattern with interior wildcards is voiced AS a pattern —
        never simplified into a claim the SQL does not make."""
        sk = compose_skeleton(
            "SELECT PATIENT_ID FROM ENCOUNTER_DIAGNOSIS "
            "WHERE DX_CODE LIKE 'E1_.3%'", self.DX)
        assert "diagnosis code matches the pattern 'E1_.3%'" in sk

    def test_not_in_voices_the_exclusion(self):
        frag = ("SELECT PATIENT_ID FROM MEDICATION_ORDERS "
                "WHERE MED_NAME NOT IN ('METFORMIN', 'INSULIN')")
        sk = compose_skeleton(frag, self.DX)
        assert "medication name is not 'METFORMIN', 'INSULIN'" in sk

    def test_not_between_voices_the_negation(self):
        frag = ("SELECT PATIENT_ID FROM LAB_RESULTS "
                "WHERE HBA1C_VALUE NOT BETWEEN 4 AND 5.6")
        sk = compose_skeleton(frag, self.DX)
        assert "hba1c value does not fall between 4 and 5.6" in sk

    def test_having_count_voices_the_counted_entity(self):
        """The High_Utilizer mush-pass: 'the value is at least 4'
        dropped the load-bearing content. The tree HAS the fact."""
        frag = ("SELECT E.PATIENT_ID, COUNT(E.ENCOUNTER_ID) AS V "
                "FROM ENCOUNTERS E GROUP BY E.PATIENT_ID "
                "HAVING COUNT(E.ENCOUNTER_ID) >= 4")
        sk = compose_skeleton(frag, self.DX)
        assert "the number of encounter id values is at least 4" in sk
        assert "the value" not in sk
        assert "after grouping" not in sk

    def test_count_star_and_distinct(self):
        sk1 = compose_skeleton(
            "SELECT PATIENT_ID FROM ENCOUNTERS "
            "GROUP BY PATIENT_ID HAVING COUNT(*) > 2", self.DX)
        assert "the number of records is more than 2" in sk1
        sk2 = compose_skeleton(
            "SELECT PATIENT_ID FROM ENCOUNTERS GROUP BY PATIENT_ID "
            "HAVING COUNT(DISTINCT ENCOUNTER_ID) > 2", self.DX)
        assert ("the number of distinct encounter id values "
                "is more than 2") in sk2

    def test_sum_and_meaning_preserving_wrappers(self):
        sk1 = compose_skeleton(
            "SELECT PATIENT_ID FROM CHARGES GROUP BY PATIENT_ID "
            "HAVING SUM(AMOUNT) > 1000", {"AMOUNT": "charge amount"})
        assert "the total charge amount is more than 1000" in sk1
        sk2 = compose_skeleton(
            "SELECT PATIENT_ID FROM ENCOUNTER_DIAGNOSIS "
            "WHERE UPPER(DX_CODE) = 'E11'", self.DX)
        assert "diagnosis code is 'E11'" in sk2


class TestPassThroughFact:
    """The Passthrough grade: 'a collection of records' says nothing.
    Zero decision sites is itself a voicable, grounded fact."""

    def test_select_star_states_no_conditions(self):
        sk = compose_skeleton("SELECT * FROM DM_REGISTRY", None)
        assert "No filtering conditions are applied in this step." in sk

    def test_constant_select_states_no_source(self):
        sk = compose_skeleton("SELECT 1 AS ALWAYS_TRUE", None)
        assert ("No source records are read; this step produces "
                "derived values.") in sk

    def test_filtered_step_gets_no_passthrough_line(self):
        sk = compose_skeleton(
            "SELECT PATIENT_ID FROM LAB_RESULTS WHERE HBA1C_VALUE > 7",
            {"HBA1C_VALUE": "hba1c value"})
        assert "No filtering conditions" not in sk


class TestPlaceholderBan:
    """DESC-LEAF-1 part 2 — no placeholder ships uncounted. The gate
    learns the composer's own fallback strings, frontier AS DATA
    (spec:G4 clause 1); each entry is proven by injection here
    (clause 2, the pinned meta-test)."""

    def test_frontier_is_data_and_each_entry_fires(self):
        """Each pattern carries its own injection exemplar — the data
        proves itself (spec:G4 clause 2)."""
        from src.descriptions import _COMPOSER_PLACEHOLDERS, grounding_violations
        frag = "SELECT PATIENT_ID FROM ENCOUNTERS"
        assert _COMPOSER_PLACEHOLDERS  # deny-by-default: never empty
        for pat, exemplar in _COMPOSER_PLACEHOLDERS.items():
            v = grounding_violations(f"This step keeps records where "
                                     f"{exemplar}.", frag)
            assert any("placeholder" in x for x in v), pat

    def test_clean_prose_does_not_trip_the_ban(self):
        from src.descriptions import grounding_violations
        v = grounding_violations(
            "This is a selection of patients.\n"
            "- The hba1c value exceeds 6.5.",
            "SELECT PATIENT_ID FROM LAB_RESULTS WHERE HBA1C_VALUE > 6.5")
        assert not any("placeholder" in x for x in v)

    def test_unvoicable_leaf_is_a_counted_empty_not_mush(self):
        """The closed outcome, end to end: a leaf the composer cannot
        voice falls to the raw echo, and the gate REFUSES it — the
        step empties and is counted, never shipped as mush. (The
        original corpse here was a DATEDIFF comparison — EXPR-IR-1's
        compositional renderer now voices it, so the corpse advanced
        to a CASE-in-predicate, the ruled unrendered kind.)"""
        from src.descriptions import grounding_violations
        frag = ("SELECT PATIENT_ID FROM ENCOUNTERS WHERE "
                "CASE WHEN ADMIT_DATE > DISCHARGE_DATE THEN 1 "
                "ELSE 0 END = 1")
        sk = compose_skeleton(frag, None)
        assert "condition holds" in sk          # the honest last resort
        assert grounding_violations(sk, frag)   # ...and it cannot ship

    def test_exists_correlation_keys_dedupe(self):
        """P.PATIENT_ID = E.PATIENT_ID is ONE meaning — '(patient id,
        patient id)' read as a stutter in the live sample."""
        sk = compose_skeleton(
            "SELECT E.PATIENT_ID FROM ENCOUNTERS E WHERE NOT EXISTS "
            "(SELECT 1 FROM PCP P WHERE P.PATIENT_ID = E.PATIENT_ID)",
            None)
        assert "(patient id)" in sk
        assert "patient id, patient id" not in sk


class TestEstateScaleCorpses:
    """The 09-03 store rerun (local 600, 450 steps of Clarity-shaped
    SQL): 124 empties, of which three classes were OUR machinery's
    bugs, pinned here from live node reproductions — not ruled voice
    kills."""

    def test_sentence_shaped_meaning_becomes_a_subject_phrase(self):
        """Steward dictionaries hold SENTENCES; splicing one in whole
        produced 'took place. is recorded' and defeated the
        misattribution checker. meaning_of must yield the first
        sentence, unterminated."""
        from src.descriptions import meaning_of
        m = {"TAKEN_TIME": "The user-specified time that the action "
                           "took place. Multiple actions may exist."}
        assert (meaning_of("TAKEN_TIME", m)
                == "The user-specified time that the action took place")
        sk = compose_skeleton(
            "SELECT ENCOUNTER_ID FROM MED_ADMIN WHERE TAKEN_TIME IS "
            "NOT NULL", m)
        assert "took place is recorded" in sk
        assert ". is recorded" not in sk

    def test_own_elision_count_is_not_an_ungrounded_value(self):
        """'is one of 25 values from X to Y' — the 25 is composed BY
        the composer from the SQL's own list; the value gate flagged
        it and emptied the step (SepsisAuditTemp, live)."""
        from src.descriptions import grounding_violations
        frag = ("SELECT A FROM T WHERE FLO_ID IN (" +
                ",".join(f"'{9000000000 + i}'" for i in range(25)) + ")")
        text = ("This is a selection of records.\n- The flowsheet group "
                "is one of 25 values from '9000000000' to '9000000024'.")
        v = grounding_violations(text, frag)
        assert not any("'25'" in x for x in v), v

    def test_value_set_is_not_the_value_placeholder(self):
        """FP corpse: the customer's own phrase 'the value set'
        tripped the mush ban and emptied All_LDAs. The ban must match
        the placeholder CLAIM (the value is/falls/...), not the two
        words wherever they occur."""
        from src.descriptions import grounding_violations
        frag = "SELECT A FROM T WHERE VALUE_SET_ID = 3022"
        ok = grounding_violations(
            "Unique identifier for the value set is 3022.", frag)
        assert not any("placeholder" in x for x in ok), ok
        bad = grounding_violations("The value is at least 3022.", frag)
        assert any("placeholder" in x for x in bad)


class TestCompositionalRenderer:
    """EXPR-IR-1 (Sunny's ruling 09-03, first principles): interpret
    the AST the way it was built — structural recursion, one rule per
    GRAMMAR node type, never a rule per shape. The extractor CAPTURES
    the scalar subtree in the walk it already runs (the depth-1 cliff
    dies); the composer renders the captured record with the
    dictionary at composition time. Pattern ancestor (spec:G4):
    _convert/_render's boolean recursion — this extends it through
    the leaf it used to stop at."""

    M = {"TAKEN_TIME": "the antibiotic administration time",
         "BLOOD_CULTURE_ORDER_TIME": "the blood culture order time",
         "AMOUNT": "charge amount", "WEIGHT_KG": "weight in kilograms"}

    def test_the_36_empties_shape_renders_at_any_depth(self):
        """The live ABX corpse: depth-3 ABS(DATEDIFF)/60 <= 72 —
        raw-echoed and emptied under the depth-1 probes."""
        frag = ("SELECT ENCOUNTER_ID FROM MED_ADMIN MA WHERE "
                "(ABS(DATEDIFF(MI, MA.TAKEN_TIME, "
                "BC.BLOOD_CULTURE_ORDER_TIME)) / 60.00) <= 72.0")
        sk = compose_skeleton(frag, self.M)
        assert "condition holds" not in sk and "`" not in sk
        assert ("the absolute value of the minutes between the "
                "antibiotic administration time and the blood culture "
                "order time, divided by 60.00 is at most 72.0") in sk

    def test_arithmetic_composes_without_a_function(self):
        frag = ("SELECT PATIENT_ID FROM VITALS WHERE "
                "WEIGHT_KG * 2.2 > 300")
        sk = compose_skeleton(frag, self.M)
        assert ("weight in kilograms times 2.2 is more than 300") in sk

    def test_generic_function_rule_covers_the_unknown(self):
        """No SQUARE overlay exists and never will — the GENERIC rule
        must cover it (coverage by composition, quality by evidence)."""
        frag = "SELECT PATIENT_ID FROM VITALS WHERE SQUARE(AMOUNT) > 100"
        sk = compose_skeleton(frag, self.M)
        assert "the square of charge amount is more than 100" in sk
        assert "condition holds" not in sk

    def test_comparand_is_role_exact_not_first_flat_operand(self):
        """The wrong-number corpse: the flat operand list once put the
        DIVISOR where the threshold belongs ('at most 60.00'). The
        captured record keeps roles: the right side is the comparand."""
        frag = ("SELECT ENCOUNTER_ID FROM MED_ADMIN WHERE "
                "(ABS(DATEDIFF(MI, TAKEN_TIME, "
                "BLOOD_CULTURE_ORDER_TIME)) / 60.00) <= 72.0")
        sk = compose_skeleton(frag, self.M)
        assert "is at most 72.0" in sk
        assert "is at most 60.00" not in sk

    def test_unrenderable_kind_still_dies_counted(self):
        """CASE inside a predicate stays outside the rule table —
        closed outcomes: raw echo, gate-refused, counted."""
        from src.descriptions import grounding_violations
        frag = ("SELECT A FROM T WHERE "
                "CASE WHEN B > 1 THEN 1 ELSE 0 END = 1")
        sk = compose_skeleton(frag, None)
        assert "condition holds" in sk
        assert grounding_violations(sk, frag)

    def test_kind_frontier_is_data_and_total(self):
        """spec:G4: every capture kind the extractor can produce has a
        render rule or a recorded unrendered reason — both directions."""
        from src.descriptions import RENDERED_KINDS, UNRENDERED_KINDS
        from src.tree.extract import EXPR_KINDS
        covered = set(RENDERED_KINDS) | set(UNRENDERED_KINDS)
        assert set(EXPR_KINDS) == covered, (
            set(EXPR_KINDS) ^ covered)
        assert all(str(v).strip() for v in UNRENDERED_KINDS.values())


class TestCheckerMeaningsBridge:
    """The ~15 estate false kills: two checkers predate the meanings
    reframe — a TRUE claim voiced via a column's dictionary meaning
    was unrecognizable to them. The bridge: a deciding column's
    dictionary words count as naming it; a SELECT-only column's do
    not (role-faithful, not a loosening)."""

    def test_deciding_columns_meaning_grounds_a_filter_claim(self):
        from src.descriptions import grounding_violations
        frag = ("SELECT ENCOUNTER_ID FROM FLOWSHEET_RECORDED WHERE "
                "FLO_MEAS_ID IN (SELECT MEAS_ID FROM VALUE_SETS)")
        dl = ["- FLO_MEAS_ID: The unique ID for the flowsheet group "
              "associated with this reading."]
        text = ("This is a selection of encounters.\n"
                "- The unique ID for the flowsheet group associated "
                "with this reading is restricted to a separately "
                "selected set.")
        assert not grounding_violations(text, frag, dl)

    def test_select_only_columns_meaning_still_fails(self):
        from src.descriptions import grounding_violations
        frag = ("SELECT FLO_MEAS_ID FROM FLOWSHEET_RECORDED "
                "WHERE ENCOUNTER_TYPE = 'ED'")
        dl = ["- FLO_MEAS_ID: The unique ID for the flowsheet group "
              "associated with this reading."]
        text = ("- The unique ID for the flowsheet group associated "
                "with this reading is restricted to a separately "
                "selected set.")
        v = grounding_violations(text, frag, dl)
        assert any("selected-not-filtered" in x
                   or "ungrounded filter" in x for x in v), v

    def test_misattribution_accepts_the_meaning_as_subject(self):
        from src.descriptions import grounding_violations
        frag = ("SELECT A FROM T WHERE meas.RECORDED_TIME BETWEEN "
                "base.IN_DTTM AND base.OUT_DTTM")
        dl = ["- RECORDED_TIME: The instant the reading was taken."]
        text = ("- The instant the reading was taken falls between "
                "in dttm and out dttm.")
        assert not grounding_violations(text, frag, dl)
