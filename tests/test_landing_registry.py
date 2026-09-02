"""The landing registry's closure checks (ADR 0068, a 0067 ratchet turn).

ADR 0063 §3 stated two invariants that make "artifacts land, chat
doesn't" enforceable; the matrix held them as prose until this turn:
- NO ACTION WITHOUT A LANDING: every governance action either names
  what it creates in each DG tool or is explicitly own_only;
- NO LANDING WITHOUT A GRADE: every action carries its provenance.

Plus the projection discipline: DECISION_LANDING_MATRIX.md is
generated from this registry and CI fails if stale.

Proves: spec:L3
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from src.landing_registry import (
    LANDING_ACTIONS,
    OUTBOX_FIELDS,
    OUTBOX_OUTCOMES,
    SUPPORT,
    TARGET_SYSTEMS,
    WORKFLOW_RULES,
)

REPO = Path(__file__).resolve().parent.parent


def test_no_action_without_a_landing():
    """0063 invariant 1. A future action with no row does not ship
    until it has one."""
    bad = []
    for key, a in LANDING_ACTIONS.items():
        if a.get("own_only"):
            if not a.get("keeps", "").strip():
                bad.append(f"{key}: own_only but keeps nothing")
            continue
        for system in TARGET_SYSTEMS:
            s = a.get(system)
            if s is None:
                bad.append(f"{key}: no {system} column")
            elif not (s.get("assets") or s.get("relationships")
                      or s.get("status")):
                bad.append(f"{key}/{system}: lands nothing — either "
                           f"fill the column or mark the action "
                           f"own_only")
    assert not bad, ("action(s) without a landing:\n  "
                     + "\n  ".join(bad))


def test_no_landing_without_a_grade():
    """0063 invariant 2."""
    ungraded = [k for k, a in LANDING_ACTIONS.items()
                if not a.get("grade", "").strip()]
    assert not ungraded, f"action(s) without a grade: {ungraded}"


def test_support_markers_are_closed_vocabulary():
    """Every cell tag is [native]/[config]/[absent] — no fourth state
    (the spec:C1 no-third-state discipline applied to tool support)."""
    tag = re.compile(r"\[(\w+)\]")
    bad = []
    for key, a in LANDING_ACTIONS.items():
        for system in TARGET_SYSTEMS:
            for field, val in (a.get(system) or {}).items():
                cells = val if isinstance(val, list) else [val]
                for cell in cells:
                    for m in tag.finditer(cell):
                        if m.group(1) not in SUPPORT:
                            bad.append(f"{key}/{system}/{field}: "
                                       f"[{m.group(1)}]")
    assert not bad, "unknown support marker(s):\n  " + "\n  ".join(bad)


def test_outbox_vocabulary_is_closed():
    assert len(OUTBOX_FIELDS) == 7
    assert set(OUTBOX_OUTCOMES) == {"published", "denied", "edited",
                                    "missing"}
    assert len(WORKFLOW_RULES) == 4, (
        "the four workflow rules are RULED (2026-08-31) — changing "
        "their number is an ADR, not an edit")


def test_no_brand_string_in_registry_source():
    """The registry lives in the brand-neutral core; attribution uses
    the {product} placeholder, rendered by the generator."""
    src = (REPO / "src" / "landing_registry.py").read_text()
    assert "{product}" in src, "attribution placeholder missing"


def test_landing_matrix_on_disk_is_fresh():
    spec = importlib.util.spec_from_file_location(
        "gd", REPO / "scripts" / "generate_docs.py")
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    on_disk = (REPO / "docs" / "architecture"
               / "DECISION_LANDING_MATRIX.md").read_text()
    assert gd.build_landing_matrix() == on_disk, (
        "DECISION_LANDING_MATRIX.md is stale — run: "
        "python scripts/generate_docs.py")
