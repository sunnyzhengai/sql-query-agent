"""The axiom ledger's closure checks (ADR 0067, turn 1).

The ledger (src/spec_registry.py) is the single writer for axiom ids,
framework parents, and declared checks. These tests keep it locked to
SPEC.md at the id level — the Group-P failure class (an axiom ratified
in prose but unregistered as data for 11 days) becomes impossible in
either direction.

Proves: spec:L3
"""

from __future__ import annotations

import re
from pathlib import Path

from src.spec_registry import GROUPS, SPEC_REGISTRY
from src.trace_registry import AXM_AXIOMS

REPO = Path(__file__).resolve().parent.parent
SPEC = (REPO / "docs" / "architecture" / "SPEC.md").read_text()


def _ids_in_spec() -> "set[str]":
    """Axiom ids as SPEC.md renders them: bold prose axioms, table
    rows, and the two single-letter equation-block groups."""
    ids = set(re.findall(r"\*\*([A-Z][0-9]{1,2}) —", SPEC))
    ids |= set(re.findall(r"^\| ([A-Z][0-9]) ", SPEC, re.M))
    ids |= set(re.findall(r"^\| \*\*([A-Z][0-9])\*\* ", SPEC, re.M))
    for letter in ("F",):  # stated as one equation block, no numbered id
        if re.search(rf"## .*Group {letter} —", SPEC):
            ids.add(letter)
    return ids


def test_totality_every_record_appears_in_spec_and_vice_versa():
    """A new axiom cannot exist in only one place."""
    in_spec, in_ledger = _ids_in_spec(), set(SPEC_REGISTRY)
    only_spec = sorted(in_spec - in_ledger)
    only_ledger = sorted(in_ledger - in_spec)
    assert not only_spec, (
        f"axiom(s) in SPEC.md with no ledger record: {only_spec} — "
        f"the Group-P failure class; add the record to spec_registry")
    assert not only_ledger, (
        f"ledger record(s) with no axiom in SPEC.md: {only_ledger} — "
        f"either write the axiom (an ADR, SPEC section 16) or delete "
        f"the record")


def test_every_declared_check_exists():
    dangling = [f"{ax}: {p}" for ax, rec in SPEC_REGISTRY.items()
                for p in rec["checks"] if not (REPO / p).exists()]
    assert not dangling, ("declared check(s) do not exist:\n  "
                          + "\n  ".join(dangling))


def test_every_parent_is_a_framework_axiom():
    bad = [f"{ax}: {p}" for ax, rec in SPEC_REGISTRY.items()
           for p in rec["parents"] if p not in AXM_AXIOMS]
    assert not bad, "unknown parent(s):\n  " + "\n  ".join(bad)
    orphans = [ax for ax, rec in SPEC_REGISTRY.items()
               if not rec["parents"]]
    assert not orphans, f"record(s) with no framework parent: {orphans}"


def test_every_record_has_checks_or_a_reason():
    """No silent unbound: an axiom either names its check files or
    states, in SPEC's own words, why it cannot yet."""
    silent = [ax for ax, rec in SPEC_REGISTRY.items()
              if not rec["checks"]
              and not rec.get("checks_note", "").strip()
              and not rec.get("status_note", "").strip()]
    assert not silent, (
        f"axiom(s) with neither checks nor a recorded reason: {silent}")


def test_status_vocabulary_is_closed():
    from src.spec_registry import STATUSES
    bad = [(ax, r["status"]) for ax, r in SPEC_REGISTRY.items()
           if r["status"] not in STATUSES]
    assert not bad, f"status outside the closed vocabulary: {bad}"


def test_every_record_carries_its_law():
    lawless = [ax for ax, r in SPEC_REGISTRY.items()
               if not r.get("law", "").strip()]
    assert not lawless, f"record(s) without a law: {lawless}"


def test_groups_are_closed_and_every_record_belongs_to_one():
    bad = [ax for ax in SPEC_REGISTRY
           if (ax[0] if ax != "F" else "F") not in GROUPS]
    assert not bad, f"record(s) outside the declared groups: {bad}"


def test_spec_doc_on_disk_is_fresh():
    """ADR 0073: SPEC.md is the ledger rendered into its frame —
    regeneration must produce zero diff. Hand-editing the doc is a
    red build; axioms change via the ledger + an ADR."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gd", REPO / "scripts" / "generate_docs.py")
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    on_disk = (REPO / "docs" / "architecture" / "SPEC.md").read_text()
    assert gd.build_spec() == on_disk, (
        "SPEC.md is stale — run: python scripts/generate_docs.py")
