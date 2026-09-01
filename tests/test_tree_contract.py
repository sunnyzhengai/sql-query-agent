"""The Tree Contract (ADR 0044) — checked in RED before implementation.

Every clause below is a strict xfail: pytest reports it as expected-to-
fail today, and CI FAILS the moment an implementation makes it pass
while the marker is still present. Removing a marker is that clause's
exit gate — the contract cannot be satisfied silently or partially.

API surface (extract.py SHIPPED in phase 1/1.26.0; the rest are
phase targets and do not exist yet):
    src/tree/extract.py    build_decision_tree(fragment) -> DecisionTree
    src/tree/translate.py  translate_tree(tree, dict_lines, describe),
                           build_fact_prompt(node, dict_lines)
    src/tree/verify.py     build_reconstruction_prompt(description, dict_lines)
    src/tree/diff.py       tree_diff(expected, reconstructed)
    src/tree/render.py     render_template(tree, dict_lines)
    src/tree/pipeline.py   verified_describe(...) -> (text, provenance)

Fixtures are real corpus constructs from [reporting].[USP_ED_Sepsis]
(the deep-trace proc): the OR-inside-AND device predicate, the systolic
CONVERT/LEFT/CHARINDEX expression, the NOT EXISTS exclusion. Fixtures
are real corpses — future field fabrications join them before their
fix ships.
"""

import ast as pyast
import inspect
from pathlib import Path

import pytest

from src.descriptions import grounding_violations

REPO_ROOT = Path(__file__).parent.parent
ADR = REPO_ROOT / "docs" / "decisions" / \
    "0044-tree-contract-round-trip-descriptions.md"


def clause(n: int, phase: int):
    """Strict xfail: passing with the marker present FAILS CI, which
    forces the marker removal that IS the clause's exit gate."""
    return pytest.mark.xfail(
        strict=True,
        reason=f"Tree Contract clause {n} — phase {phase} exit gate "
               f"(ADR 0044); remove this marker when the clause ships",
    )


# Real predicate shapes from the traced proc — each one a level of the
# coverage ceiling the tree must hold faithfully (ADR 0044 context).
GNARLY_FRAGMENT = (
    "SELECT EEF.ENCOUNTER_ID, FSD.MEAS_VALUE "
    "INTO #Devices "
    "FROM #Base_Pop EEF "
    "INNER JOIN FLOWSHEET_MEASUREMENTS FSD "
    "  ON EEF.ENCOUNTER_ID = FSD.ENCOUNTER_ID "
    "LEFT JOIN CLARITY_VALUE_SETS CVS ON FSD.FLO_MEAS_ID = CVS.MEAS_ID "
    "WHERE EEF.ADT_ARRIVAL_DATE BETWEEN @dStartDate AND @dEndDate "
    "AND ( FSD.FLO_MEAS_ID IN ('900112', '900111') "
    "      OR CVS.VALUE_SET_ID = 3022 ) "
    "AND CONVERT(INTEGER, LEFT(FSD.MEAS_VALUE, "
    "    CHARINDEX('/', FSD.MEAS_VALUE) - 1)) < 100 "
    "AND NOT EXISTS (SELECT 1 FROM #ED_PositiveScores PS "
    "                WHERE PS.ENCOUNTER_ID = EEF.ENCOUNTER_ID)"
)

DICT_LINES = [
    "- FLOWSHEET_MEASUREMENTS.FLO_MEAS_ID: flowsheet row identifier",
    "- FLOWSHEET_MEASUREMENTS.MEAS_VALUE: recorded measurement value",
    "- CLARITY_VALUE_SETS.VALUE_SET_ID: grouped clinical code set",
]


class TestClause1ConservationOfDecisionSites:
    def test_handled_plus_unextracted_equals_total(self):
        from src.tree.extract import build_decision_tree
        tree = build_decision_tree(GNARLY_FRAGMENT)
        assert tree.handled_count + len(tree.unextracted) == \
            tree.decision_sites_total
        # window filter, IN, =, computed <, NOT EXISTS, two join ONs
        assert tree.decision_sites_total >= 6

    def test_boolean_shape_is_preserved_never_flattened(self):
        # The OR-inside-AND: flattening it to two AND-bullets silently
        # changes meaning — the tree must keep an explicit OR node.
        from src.tree.extract import build_decision_tree
        tree = build_decision_tree(GNARLY_FRAGMENT)
        assert tree.has_or_node(within=["900112", "3022"])

    def test_unmodeled_constructs_are_counted_not_dropped(self):
        # Dynamic SQL has no static tree — it must land in unextracted
        # with a location, never vanish (the third-bucket ban).
        from src.tree.extract import build_decision_tree
        tree = build_decision_tree(
            "DECLARE @sql NVARCHAR(MAX) = "
            "'SELECT * FROM t WHERE ' + @filter; EXEC (@sql)")
        assert tree.unextracted, "dynamic SQL must be a counted gap"

    def test_unextracted_surfaces_on_fallout_and_checklist(self):
        # Sunny 2026-08-19: "dynamic sql can't be parsed, that's ok,
        # but we need to surface them into our admin table and PBI
        # dashboard." Never only an internal counter (ADR 0045 §3).
        from src.tree.extract import build_decision_tree, unextracted_fallout_rows
        tree = build_decision_tree(
            "DECLARE @sql NVARCHAR(MAX) = "
            "'SELECT * FROM t WHERE ' + @filter; EXEC (@sql)")
        rows = unextracted_fallout_rows(tree, metric_id="USP_X")
        assert rows and all(r["stage"] == "300_tree_unextracted" for r in rows)
        assert all(r["resolution"] == "escalated" for r in rows), \
            "novelty always escalates to the human checklist"


class TestClause2TranslatorBlindness:
    def test_translator_prompts_carry_facts_never_raw_sql(self):
        from src.tree.extract import build_decision_tree
        from src.tree.translate import translate_tree
        tree = build_decision_tree(GNARLY_FRAGMENT)
        prompts = []

        def capture(p):
            prompts.append(p)
            return "translated line"

        translate_tree(tree, DICT_LINES, capture)
        assert prompts
        for p in prompts:
            assert GNARLY_FRAGMENT not in p
            assert "SELECT EEF.ENCOUNTER_ID" not in p, \
                "raw statement text leaked into a translator prompt"

    def test_fact_prompt_builder_cannot_accept_a_fragment(self):
        # AST plank, the 0042 regex-ban pattern: the banned input has
        # no parameter to arrive through.
        from src.tree.translate import build_fact_prompt
        params = inspect.signature(build_fact_prompt).parameters
        assert "fragment" not in params and "sql" not in params


class TestClause3VerifierBlindness:
    def test_reconstruction_prompt_is_description_plus_dictionary_only(self):
        from src.tree.verify import build_reconstruction_prompt
        params = inspect.signature(build_reconstruction_prompt).parameters
        assert set(params) == {"description", "dict_lines"}, \
            "the verifier's only inputs are the description and the dictionary"
        description = (
            "Includes device rows for airway or intravenous placements, "
            "limited to systolic readings under one hundred.")
        p = build_reconstruction_prompt(description, DICT_LINES)
        assert description in p
        for sql_token in ("SELECT", "WHERE", "JOIN", "#Base_Pop"):
            assert sql_token not in p, \
                f"SQL leaked into the verifier prompt: {sql_token}"


class TestClause4TheJudgeIsNeverAnLLM:
    def test_diff_module_imports_no_llm_and_takes_no_callback(self):
        module = pyast.parse(
            (REPO_ROOT / "src" / "tree" / "diff.py").read_text())
        imported = {
            name.name
            for node in pyast.walk(module)
            if isinstance(node, pyast.Import)
            for name in node.names
        } | {
            node.module
            for node in pyast.walk(module)
            if isinstance(node, pyast.ImportFrom) and node.module
        }
        assert not any(
            "llm" in m or "openai" in m or "descriptions" in m
            for m in imported
        ), f"the judge must be deterministic code, found: {sorted(imported)}"
        from src.tree.diff import tree_diff
        params = inspect.signature(tree_diff).parameters
        assert "describe" not in params and "callback" not in params


class TestClause5EveryDecisionVoicedOrCounted:
    def test_ledger_balances_voiced_union_unvoiced_is_must_voice(self):
        from src.tree.extract import build_decision_tree
        from src.tree.translate import translate_tree
        tree = build_decision_tree(GNARLY_FRAGMENT)
        result = translate_tree(tree, DICT_LINES, lambda p: "line")
        voiced = set(result.ledger)
        unvoiced = set(result.unvoiced)
        must = {n.node_id for n in tree.nodes if n.must_voice}
        assert voiced | unvoiced == must, "silent omission — ledger leak"
        assert voiced.isdisjoint(unvoiced)


class TestClause6FailurePolarityFloor:
    def test_never_converging_loop_degrades_to_grounded_template(self):
        from src.tree.extract import build_decision_tree
        from src.tree.pipeline import verified_describe
        tree = build_decision_tree(GNARLY_FRAGMENT)

        def fabricating_translator(prompt):
            return "Excludes pending or cancelled encounters over 40."

        def honest_reconstructor(prompt):
            return "{}"  # reconstructs nothing — round trip never matches

        text, provenance = verified_describe(
            tree, DICT_LINES,
            translator=fabricating_translator,
            reconstructor=honest_reconstructor,
            max_rounds=3,
        )
        assert provenance == "template_fallback"
        # the floor is stilted truth, never hope: fully grounded output
        # the floor is MACHINE-composed stilted truth, not a business
        # description — voice rules (DESC-VOICE-1) do not police it
        assert grounding_violations(text, GNARLY_FRAGMENT,
                                    voice=False) == []
        assert "pending or cancelled" not in text

    def test_version_binding_tree_contract_version_changes_cache_keys(self):
        import src.tree as tree_pkg
        from src.tree.extract import build_decision_tree, tree_content_hash
        tree = build_decision_tree(GNARLY_FRAGMENT)
        before = tree_content_hash(tree, DICT_LINES)
        original = tree_pkg.TREE_CONTRACT_VERSION
        try:
            tree_pkg.TREE_CONTRACT_VERSION = original + "-next"
            assert tree_content_hash(tree, DICT_LINES) != before, \
                "a stricter contract must regenerate everything it governs"
        finally:
            tree_pkg.TREE_CONTRACT_VERSION = original


class TestContractIsLocked:
    """Green today — the lock on the lock. These bind the ADR's clause
    table to this file so neither can drift from the other."""

    def test_adr_0044_exists_and_states_all_six_clauses(self):
        text = ADR.read_text()
        for anchor in (
            "Conservation of decision sites",
            "Translator blindness",
            "Verifier blindness",
            "never an LLM",
            "voiced or counted",
            "Failure-polarity floor",
        ):
            assert anchor in text, f"ADR 0044 lost clause anchor: {anchor}"

    def test_every_clause_has_a_strict_exit_gate_in_this_file(self):
        # A clause is either SHIPPED (marker removed, tests run green —
        # the exit-gate flip) or still gated by a strict-xfail marker.
        shipped = {1, 2, 3, 4, 5, 6}  # all six: extractor 1.26/1.28; translator 1.31; round trip 1.32
        source = Path(__file__).read_text()
        for n in range(1, 7):
            if n in shipped:
                assert f"clause({n}, phase=" not in source, \
                    f"clause {n} shipped — its exit-gate marker must be gone"
            else:
                assert f"clause({n}, phase=" in source, \
                    f"clause {n} has no exit-gate skeleton"
        assert "strict=True" in source, \
            "exit gates must be strict xfail — passing silently is drift"

class TestDictionaryIsSubstitutionNotGlossary:
    """DESC-VOICE-3.2 live find (08-31): supplying the dictionary is
    NOT enough. Framed as a GLOSSARY ("translate identifiers using
    these") the model treats it as vocabulary to CITE and copies the
    dictionary's KEYS into the description — raw column names, the
    exact thing the order bans. Framed as SUBSTITUTIONS ("when you
    mean X, write Y; the identifier must never appear") it writes the
    VALUES instead. Measured live: 10 column-name violations across
    6 steps under glossary framing, 0 under substitution framing.
    This pins the framing so it cannot silently regress."""

    def test_prompt_frames_dictionary_as_substitution(self):
        from src.tree.translate import build_fact_prompt

        prompt = build_fact_prompt(
            "#BPA", [], [],
            dict_lines=["  - ALT_ACTION_INST: the time the alert "
                        "was acted on"])
        low = prompt.lower()
        assert "never appear" in low or "must not appear" in low, (
            "the dictionary block must forbid the identifier itself, "
            "not merely offer a translation")
        assert "the time the alert was acted on" in prompt
