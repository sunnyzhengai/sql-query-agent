"""OP-FRONTIER-1 — the enum-anchored totality check (spec:G4
clause 1, ordered by Sunny 2026-09-03).

The three-owner law made data: Microsoft owns WHICH operators exist
(the ScriptDom enums, reflected here — the denominator is never
hand-maintained); the extractor's emit-set and the composer's
phrase-set are DATA, reconciled against the enum and against each
other in both directions. A new operator, an unmapped enum value, or
an unvoiced op is a red build the day it is born — not a corpus
discovery (DESC-LEAF-1's four holes were exactly this class, found
at run time because this check did not exist).

Pattern ancestors (spec:G4 clause 3): spec:G2's whole-surface
inclusion (Uses \\ Sanctioned = 0), TestRegexFrontier's
sanctioned-plus-debt form, and the 0067 registries (the list IS the
law; prose never carries the frontier).

Proves: spec:G4
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.descriptions import UNVOICED_OPS, VOICED_OPS, _leaf_phrase
from src.tree.extract import (
    _COMPARISON_OPS,
    DEFERRED_COMPARISONS,
    EMITTED_OPS,
    DecisionNode,
    parse_tsql,
)

REPO = Path(__file__).resolve().parent.parent
EXTRACT_SRC = (REPO / "src" / "tree" / "extract.py").read_text()


def _scriptdom_comparison_enum() -> "set[str]":
    """The denominator, from Microsoft by reflection — never typed."""
    parse_tsql("SELECT 1")  # force the coreclr + DLL load
    import System
    from Microsoft.SqlServer.TransactSql import ScriptDom
    return set(System.Enum.GetNames(ScriptDom.BooleanComparisonType))


def _ops_emitted_in_source() -> "set[str]":
    """Every op literal the extractor can emit, read from its OWN
    source by AST (the G2 inclusion form): string constants assigned
    to `op` (including via conditional expressions) and `op=...`
    keyword arguments. Never a hand-list."""
    found: "set[str]" = set()

    def constants(node) -> "list[str]":
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value]
        if isinstance(node, ast.IfExp):
            return constants(node.body) + constants(node.orelse)
        return []

    for node in ast.walk(ast.parse(EXTRACT_SRC)):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "op"
                   for t in node.targets):
                found.update(constants(node.value))
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "op":
                    found.update(constants(kw.value))
    return found | set(_COMPARISON_OPS.values())


class TestEnumAnchor:
    def test_every_enum_value_is_mapped_or_deferred_with_reason(self):
        """Totality against Microsoft's list, both directions."""
        enum = _scriptdom_comparison_enum()
        ours = set(_COMPARISON_OPS) | set(DEFERRED_COMPARISONS)
        unruled = sorted(enum - ours)
        assert not unruled, (
            f"ScriptDom comparison type(s) with no ruling: {unruled} — "
            "map each to an op or record a deferral with its reason")
        stale = sorted(ours - enum)
        assert not stale, (
            f"mapped/deferred comparison type(s) not in the enum: "
            f"{stale} — the record no longer matches Microsoft's list")

    def test_every_deferral_records_its_reason(self):
        silent = [k for k, v in DEFERRED_COMPARISONS.items()
                  if not str(v).strip()]
        assert not silent, f"deferral(s) without a reason: {silent}"


class TestEmitVoiceSeam:
    def test_emit_set_matches_source_both_directions(self):
        """EMITTED_OPS is data; the extractor's source is scanned so
        the data cannot drift from the code (staleness law)."""
        in_source = _ops_emitted_in_source()
        unlisted = sorted(in_source - set(EMITTED_OPS))
        assert not unlisted, (
            f"op(s) emitted in extract.py but absent from EMITTED_OPS: "
            f"{unlisted}")
        phantom = sorted(set(EMITTED_OPS) - in_source)
        assert not phantom, (
            f"EMITTED_OPS entr(ies) no source path emits: {phantom}")

    def test_every_emitted_op_is_voiced_or_unvoiced_with_reason(self):
        """THE SEAM — the check DESC-LEAF-1 lacked. Two owners, one
        reconciliation: emit = voice ⊎ recorded-unvoiced."""
        covered = set(VOICED_OPS) | set(UNVOICED_OPS)
        unvoiced = sorted(set(EMITTED_OPS) - covered)
        assert not unvoiced, (
            f"op(s) the extractor emits and the composer cannot voice: "
            f"{unvoiced} — add the phrase or record the unvoiced "
            "reason; a silent gap ships counted empties")
        stale = sorted(covered - set(EMITTED_OPS))
        assert not stale, (
            f"voiced/unvoiced op(s) nothing emits: {stale}")

    def test_unvoiced_ops_record_reasons(self):
        silent = [k for k, v in UNVOICED_OPS.items() if not str(v).strip()]
        assert not silent, f"unvoiced op(s) without a reason: {silent}"


_NODE_RECIPES = {
    "EQ": dict(column="TEST_COL", operands=["5"]),
    "NEQ": dict(column="TEST_COL", operands=["5"]),
    "GT": dict(column="TEST_COL", operands=["5"]),
    "LT": dict(column="TEST_COL", operands=["5"]),
    "GTE": dict(column="TEST_COL", operands=["5"]),
    "LTE": dict(column="TEST_COL", operands=["5"]),
    "IN": dict(column="TEST_COL", operands=["'A'", "'B'"]),
    "NOT_IN": dict(column="TEST_COL", operands=["'A'", "'B'"]),
    "BETWEEN": dict(column="TEST_COL", operands=["1", "2"]),
    "NOT_BETWEEN": dict(column="TEST_COL", operands=["1", "2"]),
    "LIKE": dict(column="TEST_COL", operands=["'X%'"]),
    "NOT_LIKE": dict(column="TEST_COL", operands=["'X%'"]),
    "IS": dict(column="TEST_COL"),
    "IS_NOT": dict(column="TEST_COL"),
    "EXISTS": dict(columns=["A_ID", "B_ID"]),
    "PARAMETER_DEFAULT": dict(operands=["@TestParam", "'2024-01-01'"]),
}


class TestVoicedOpsFire:
    def test_every_voiced_op_produces_prose_on_a_synthetic_node(self):
        """Injection proof per entry (spec:G4 clause 2): membership in
        VOICED_OPS is not trusted — each op must actually voice a
        representative node without falling to the raw echo."""
        missing = sorted(set(VOICED_OPS) - set(_NODE_RECIPES))
        assert not missing, (
            f"voiced op(s) with no synthetic recipe here: {missing} — "
            "add the recipe; an unproven entry is an unproven claim")
        for op in sorted(VOICED_OPS):
            n = DecisionNode(node_id="t", kind="predicate", context="where",
                            expression_sql="TEST", op=op, must_voice=True,
                            **_NODE_RECIPES[op])
            ph = _leaf_phrase(n, None)
            assert ph and "condition holds" not in ph, (
                f"{op}: listed as voiced but fell to the raw echo")


class TestBehaviourTheCheckOrdered:
    """The two live holes the frontier work flushed out red-first."""

    def test_trivial_tautology_is_not_voiced(self):
        """WHERE 1=1 scaffolding decides nothing (must_voice=False
        since 08-20) — the composer must SKIP it, not raw-echo it
        into a gate kill that empties the whole step."""
        from src.descriptions import compose_skeleton, grounding_violations
        frag = ("SELECT PATIENT_ID FROM ENCOUNTERS "
                "WHERE 1=1 AND ENCOUNTER_TYPE = 'ED'")
        sk = compose_skeleton(frag, {"ENCOUNTER_TYPE": "encounter type"})
        assert "encounter type is 'ED'" in sk
        assert "condition holds" not in sk
        assert not grounding_violations(sk, frag)

    def test_parameter_default_is_voiced(self):
        """Sunny's 08-19 ruling said these sites exist SO DESCRIPTIONS
        CAN VOICE THEM — until now they raw-echoed. The @-name voices
        camel-split (the recorded 'dstartdate' find)."""
        from src.descriptions import compose_skeleton, grounding_violations
        frag = ("IF @StartDate IS NULL SET @StartDate = '2024-01-01'\n"
                "SELECT PATIENT_ID FROM ENCOUNTERS "
                "WHERE ADMIT_DATE >= @StartDate")
        sk = compose_skeleton(frag, {"ADMIT_DATE": "admission date"})
        assert ("start date defaults to '2024-01-01' when no value "
                "is supplied") in sk
        assert "condition holds" not in sk
        assert not grounding_violations(sk, frag)
