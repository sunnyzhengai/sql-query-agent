"""Spec gates — strict-xfail exit gates for axioms whose enforcement
home doesn't exist yet (the ADR 0044 pattern, applied to Φ_AIVIA).

Each gated axiom is red by design; CI fails the moment an
implementation makes one pass while its marker remains. Removing the
marker (and flipping the spec status with a citation) is the exit gate.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
SPEC = REPO / "docs" / "architecture" / "SPEC.md"


def gate(axiom: str, lands_with: str):
    return pytest.mark.xfail(
        strict=True,
        reason=f"spec:{axiom} exit gate — lands with {lands_with}; "
               f"remove marker + flip spec status with citation",
    )


class TestE1PathEnumeration:
    # gate flipped 1.33.0: the deterministic PRIMITIVE shipped
    def test_paths_between_anchors_are_enumerated_deterministically(self):
        from src.discovery.paths import enumerate_paths
        joinable = [
            ("PATIENTS", "PATIENT_ID", "HOSPITAL_ENCOUNTERS", "PATIENT_ID"),
            ("HOSPITAL_ENCOUNTERS", "ENCOUNTER_ID",
             "ENCOUNTER_DIAGNOSES", "ENCOUNTER_ID"),
            ("ENCOUNTER_DIAGNOSES", "DX_ID", "DIAGNOSES", "DX_ID"),
        ]
        p1 = enumerate_paths({"PATIENTS", "DIAGNOSES"}, joinable, max_hops=4)
        p2 = enumerate_paths({"PATIENTS", "DIAGNOSES"}, joinable, max_hops=4)
        assert p1 == p2, "enumeration must be replay-deterministic (E2)"
        assert p1, "the 3-hop path is a fact waiting to be enumerated"
        # direction is meaning (ADR 0046): mirror paths are distinct
        assert all(isinstance(path, tuple) for path in p1)


class TestE5FilterGrounding:
    # gate flipped 1.33.0: the deterministic PRIMITIVE shipped
    def test_filter_values_come_only_from_sites_valuesets_or_human(self):
        from src.discovery.grounding import filter_values_grounded
        verdict = filter_values_grounded(
            proposed_filters=[("DX_CODE", "IN", ["E08", "E11"])],
            site_operands={"'E08'", "'E11'"},
            value_set_rows=[], human_inputs=[])
        assert verdict.grounded
        bad = filter_values_grounded(
            proposed_filters=[("DX_CODE", "IN", ["FROM_MODEL_MEMORY"])],
            site_operands=set(), value_set_rows=[], human_inputs=[])
        assert not bad.grounded and bad.ungrounded_values


class TestSpecIsLocked:
    """Green today — binds the gated axioms to the spec file."""

    def test_gated_axioms_exist_in_the_spec(self):
        text = SPEC.read_text()
        for axiom in ("E1", "E5"):
            assert f"**{axiom} —" in text or f"**{axiom} " in text, axiom

    def test_every_gate_here_is_strict(self):
        source = Path(__file__).read_text()
        assert "strict=True" in source
