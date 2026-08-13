"""OPERATIONS ARE THE PRODUCT — mechanical enforcement (ADR 0036).

These tests inspect the CODE (AST-level) for the failure mode this
project hit three times: pattern predefinition returning to the
control path in a new disguise. They are the methodology's teeth —
the same architecture-as-tests mechanism as test_table_contracts,
which has already caught its own author once.

If one of these fails, the fix is NEVER to edit src/methodology.py to
make it pass — that is a silent amendment (forbidden). The fix is to
remove the pattern, or to bring the change to Sunny as an explicit
methodology amendment with an ADR.
"""

import ast
import re
from pathlib import Path

from src.methodology import (
    CONTROL_PATH_FILES,
    OBSERVATION_FILES,
    PRIMITIVES,
    PROMPT_LINE_BUDGET,
    PROMPT_QUOTED_EXAMPLES_BUDGET,
    SYSTEM_VOCAB,
)

ROOT = Path(__file__).resolve().parents[1]


def _literal_str_collections(tree: ast.AST):
    """Yield (lineno, [elements]) for every literal tuple/list/set of
    3+ strings — the raw material of every lexicon we ever built."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            elems = [e.value for e in node.elts
                     if isinstance(e, ast.Constant) and
                     isinstance(e.value, str)]
            if len(elems) >= 3 and len(elems) == len(node.elts):
                yield node.lineno, elems


class TestNoUserEnglishInControlPath:
    """Control-path literal string collections must be SYSTEM vocabulary
    (names of our ops/modes/fields), never user-English lexicons.
    Multi-word phrases are banned outright; single-word collections
    must be registered in SYSTEM_VOCAB. This test would have caught
    _FILLER, DETAIL_COMMANDS keywords, and the quantifier lexicon."""

    def test_control_files_hold_no_language_patterns(self):
        violations = []
        for rel in CONTROL_PATH_FILES:
            tree = ast.parse((ROOT / rel).read_text())
            for lineno, elems in _literal_str_collections(tree):
                phrases = [e for e in elems if " " in e.strip()]
                if phrases:
                    violations.append(
                        f"{rel}:{lineno} multi-word phrase lexicon "
                        f"{phrases[:3]} — pattern predefinition")
                    continue
                unregistered = [e for e in elems
                                if e not in SYSTEM_VOCAB and
                                not re.fullmatch(r"[A-Z0-9_:.|-]+", e)]
                if unregistered:
                    violations.append(
                        f"{rel}:{lineno} unregistered vocabulary "
                        f"{unregistered[:5]} — register as SYSTEM vocab "
                        "(amendment) or remove the pattern")
        assert not violations, "\n".join(violations)

    def test_observation_lexicons_stay_in_observation_files(self):
        """decision_shape's lexicon is legal ONLY because it watches.
        This asserts the allowed locations are exactly the declared
        ones — moving a lexicon 'somewhere new' is loud."""
        for rel in OBSERVATION_FILES:
            assert (ROOT / rel).exists(), f"declared observer missing: {rel}"


class TestClosedOperationRegistry:
    def test_every_control_op_is_registered_and_justified(self):
        """Any op_* function in the control path must exist in the
        PRIMITIVES registry with a data-shaped justification and an
        ADR — additions are loud by construction."""
        found = set()
        for rel in CONTROL_PATH_FILES:
            tree = ast.parse((ROOT / rel).read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("op_"):
                        found.add(node.name)
        unregistered = found - set(PRIMITIVES)
        assert not unregistered, (
            f"unregistered operations {sorted(unregistered)} — register "
            "in src/methodology.py PRIMITIVES with data_shaped_because "
            "+ adr (a methodology amendment), or do not add them")
        for name, entry in PRIMITIVES.items():
            assert entry.get("data_shaped_because", "").strip(), (
                f"{name}: missing data-shaped justification")
            assert entry.get("adr", "").strip(), f"{name}: missing ADR"

    def test_question_shaped_names_are_banned_in_control_path(self):
        """Function names that encode question shapes (the compare_X /
        handle_Y disease) may not appear in control files."""
        banned_prefixes = ("compare_metrics", "compare_tables",
                           "compare_columns", "handle_", "variants_",
                           "detail_", "match_detail")
        hits = []
        for rel in CONTROL_PATH_FILES:
            tree = ast.parse((ROOT / rel).read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(node.name.startswith(p) for p in banned_prefixes):
                        hits.append(f"{rel}: {node.name}")
        assert not hits, f"question-shaped functions in control path: {hits}"


class TestPromptBudget:
    """Instruction creep is pattern predefinition in prose. The budget
    forces trade-offs; raising it is an amendment, not an edit."""

    def test_system_prompt_within_budget(self):
        from src.orchestrator.agent import SYSTEM_PROMPT
        lines = SYSTEM_PROMPT.count("\n") + 1
        assert lines <= PROMPT_LINE_BUDGET, (
            f"system prompt is {lines} lines (budget "
            f"{PROMPT_LINE_BUDGET}) — remove instructions or bring a "
            "methodology amendment to Sunny")

    def test_quoted_example_phrasings_capped(self):
        from src.orchestrator.agent import SYSTEM_PROMPT
        quoted = re.findall(r"'[^']{3,60}'", SYSTEM_PROMPT)
        assert len(quoted) <= PROMPT_QUOTED_EXAMPLES_BUDGET, (
            f"{len(quoted)} quoted example phrasings in the prompt "
            f"(budget {PROMPT_QUOTED_EXAMPLES_BUDGET}) — examples "
            "steer, casebooks predict")


class TestManifestIntegrity:
    def test_four_lines_present_and_uncorrupted(self):
        from src.methodology import FOUR_LINES
        for anchor in ("translates", "regulates", "caption",
                       "search (semantic|exact)"):
            assert anchor in FOUR_LINES

    def test_control_files_exist(self):
        for rel in CONTROL_PATH_FILES:
            assert (ROOT / rel).exists(), f"declared control file missing: {rel}"
