"""The question-family records' closure checks (ADR 0070, ratchet turn 4).

QUESTION_MAP.md retired: layer 0 (Sunny-approved 2026-08-18) and the
shape/storage audit became FAMILY_RECORDS in the notebook registry.

Proves: spec:D1
"""

from __future__ import annotations

from src.notebook_registry import (
    FAMILY_RECORDS,
    NOTEBOOK_REGISTRY,
    QUESTION_FAMILIES,
)
from src.schemas import TABLE_REGISTRY


def test_every_family_record_is_complete():
    bad = []
    for fam, r in FAMILY_RECORDS.items():
        for field in ("title", "archetype", "asked_by", "shape",
                      "grounds", "status"):
            if not str(r.get(field, "")).strip():
                bad.append(f"{fam}.{field}")
    assert not bad, f"incomplete family record field(s): {bad}"


def test_family_storage_names_exist_in_the_table_registry():
    """The cross-registry check the prose version never had: a family
    claiming storage that no contract declares is a fabricated
    grounding."""
    ghosts = [f"{fam}: {t}" for fam, r in FAMILY_RECORDS.items()
              for t in r["storage_tables"] if t not in TABLE_REGISTRY]
    assert not ghosts, ("family storage table(s) with no contract:\n  "
                        + "\n  ".join(ghosts))


def test_every_family_is_served_by_at_least_one_notebook():
    """The traceability rule's REVERSE direction: ADR 0042 enforces
    every notebook serves >=1 family; this enforces every family is
    served — an unserved family is either dead doctrine or a missing
    notebook, and both deserve a red build."""
    served = {f for e in NOTEBOOK_REGISTRY.values() for f in e["serves"]}
    unserved = sorted(set(QUESTION_FAMILIES) - served)
    assert not unserved, f"family(ies) no notebook serves: {unserved}"


def test_families_derive_from_records():
    """One writer: the letters are the records' keys, never a second
    hand-maintained tuple."""
    assert QUESTION_FAMILIES == tuple(FAMILY_RECORDS)
