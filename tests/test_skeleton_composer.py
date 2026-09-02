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
    SANCTIONED_TEXT_SIDE = {
        "_column_words", "readable_column", "_stem",
        "column_name_violations", "misattribution_violations",
        "grounding_violations",
    }
    # Regex ON SQL — NAMED DEBT (the gate-side re-cut, orderable now
    # that DecisionSite carries scope): approximate deciding-windows
    # and text-derived grain/tables instead of tree sites. Includes a
    # find from this enumeration: parsed_grain's docstring says "the
    # parser decides" while the code regexes the fragment.
    DEBT_SQL_SIDE = {"parsed_grain", "_table_violations",
                     "_condition_text"}

    def test_the_regex_frontier_is_enumerated_and_closed(self):
        import ast as _ast
        from pathlib import Path
        src = (Path(__file__).resolve().parent.parent
               / "src" / "descriptions.py").read_text()
        users = set()
        for fn in _ast.walk(_ast.parse(src)):
            if isinstance(fn, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                if any(isinstance(n, _ast.Attribute)
                       and isinstance(n.value, _ast.Name)
                       and n.value.id == "re" for n in _ast.walk(fn)):
                    users.add(fn.name)
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
