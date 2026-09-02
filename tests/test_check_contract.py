"""spec:G4 — the check contract (ADR 0075): checks are claims.

Clause 2's exemplar lives here: the regex-frontier SCANNER is a pure
helper, meta-tested on fixtures with a PLANTED violation — the tester
is tested, permanently, not as a session anecdote.

Pattern ancestor (clause 3): spec:G2's `Uses ∖ S = ∅` AST inclusion.

Proves: spec:G4
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def regex_users(source: str) -> "set[str]":
    """Every function in `source` whose body references `re.*` — the
    frontier scanner, factored pure so it can be tested on fixtures."""
    users: "set[str]" = set()
    for fn in ast.walk(ast.parse(source)):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(isinstance(n, ast.Attribute)
                   and isinstance(n.value, ast.Name)
                   and n.value.id == "re" for n in ast.walk(fn)):
                users.add(fn.name)
    return users


class TestTheTesterIsTested:
    """G4 clause 2: an injected violation, pinned."""

    PLANTED = '''
import re

def innocent(x):
    return x.upper()

def planted_violation(sql):
    return re.findall(r"WHERE (.*)", sql)

def false_positive_bait(bare):
    return bare.upper()   # contains the substring "re." — must NOT hit
'''

    def test_scanner_catches_the_planted_violation(self):
        assert regex_users(self.PLANTED) == {"planted_violation"}, (
            "the scanner missed the plant or false-positived on "
            "`bare.upper()` — the substring-scan defect, pinned")

    def test_scanner_reports_nothing_on_a_clean_module(self):
        assert regex_users("def f(x):\n    return x + 1\n") == set()


class TestTheContractIsCarried:
    def test_the_design_protocol_carries_the_check_contract(self):
        """G4 travels with the process doc a session actually reads."""
        index = (REPO / "docs" / "INDEX.md").read_text()
        assert "spec:G4" in index and "frontier enumerated as data" in index

    def test_g4_is_law_in_the_ledger(self):
        from src.spec_registry import SPEC_REGISTRY
        rec = SPEC_REGISTRY["G4"]
        assert "deny-by-default" in rec["law"]
        assert rec["status"] == "ENFORCED"
