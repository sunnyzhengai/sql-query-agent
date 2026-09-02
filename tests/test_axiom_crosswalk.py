"""The framework <-> specification crosswalk (audited 2026-09-01).

docs/AI_VIA_AXIOMS.md is general law; docs/architecture/SPEC.md is that
law made mechanical for THIS codebase. Before this audit the two were
correlated only by claim: the framework named SPEC as its proof, and
SPEC never cited the framework.

These checks keep the correspondence honest in BOTH directions:
- no spec axiom may exist without a framework parent (this codebase
  asserts no law the framework does not authorize);
- no framework axiom may go quietly unimplemented — each is either
  mapped, or listed in AXM_UNMAPPED as meta (a law about having a
  spec, circular to implement) or gap (real law, enforced in code,
  never stated as an axiom — a finding against SPEC's own closure
  claim in section 1).
"""

import re
from pathlib import Path

from src.trace_registry import (
    AXM_AXIOMS,
    AXM_UNMAPPED,
    SPEC_AXIOMS,
    SPEC_TO_AXM,
)

REPO = Path(__file__).resolve().parent.parent
CROSSWALK = REPO / "docs" / "architecture" / "AXIOM_CROSSWALK.md"


def test_every_spec_axiom_has_a_framework_parent():
    """The upward edge. A spec axiom with no parent is either law the
    framework never authorized, or a missing crosswalk row."""
    orphans = sorted(SPEC_AXIOMS - set(SPEC_TO_AXM))
    assert not orphans, (
        f"spec axiom(s) with no framework parent: {orphans}. Either map "
        f"them in SPEC_TO_AXM or justify the new law in "
        f"docs/AI_VIA_AXIOMS.md first (the framework is the root tier)."
    )


def test_crosswalk_cites_only_real_axioms_on_both_sides():
    bad = []
    for spec_id, parents in SPEC_TO_AXM.items():
        if spec_id not in SPEC_AXIOMS:
            bad.append(f"{spec_id} is not a spec axiom")
        if not parents:
            bad.append(f"{spec_id} maps to nothing")
        for parent in parents:
            if parent not in AXM_AXIOMS:
                bad.append(f"{spec_id} -> axm:{parent} does not exist")
    assert not bad, "crosswalk defect(s):\n  " + "\n  ".join(bad)


def test_every_framework_axiom_is_mapped_or_explained():
    """The downward edge. A framework axiom must either be implemented
    by a spec axiom or carry a recorded reason why not — silence is the
    failure mode this check exists to prevent."""
    implemented = {p for parents in SPEC_TO_AXM.values() for p in parents}
    unaccounted = sorted(AXM_AXIOMS - implemented - set(AXM_UNMAPPED))
    assert not unaccounted, (
        f"framework axiom(s) neither implemented nor explained: "
        f"{unaccounted}. Add a spec axiom, or record it in AXM_UNMAPPED "
        f"as 'meta' or 'gap' with its reason."
    )


def test_unmapped_entries_are_well_formed_and_not_double_counted():
    bad = []
    for axiom, entry in AXM_UNMAPPED.items():
        if axiom not in AXM_AXIOMS:
            bad.append(f"axm:{axiom} is not a framework axiom")
        kind, reason = entry
        if kind not in ("meta", "gap"):
            bad.append(f"axm:{axiom}: kind {kind!r} must be meta or gap")
        if not reason.strip():
            bad.append(f"axm:{axiom}: no reason recorded")
    implemented = {p for parents in SPEC_TO_AXM.values() for p in parents}
    for axiom in AXM_UNMAPPED:
        if axiom in implemented:
            bad.append(
                f"axm:{axiom} is listed as unmapped but IS implemented — "
                f"remove it from AXM_UNMAPPED")
    assert not bad, "AXM_UNMAPPED defect(s):\n  " + "\n  ".join(bad)


def test_no_axiom_group_in_spec_escapes_the_registry():
    """Scope guard. The crosswalk covers NUMBERED axioms only, so a new
    group added to SPEC.md without being registered in SPEC_AXIOMS would
    silently fall outside every check above — which is exactly how Group
    P went unregistered from 2026-08-21 to 2026-09-01 (ratified,
    ENFORCED, and uncitable because its ids did not exist)."""
    spec = (REPO / "docs" / "architecture" / "SPEC.md").read_text()
    # Group headings look like "## 14h. Group L — ..." or "## 5. Group A — ..."
    declared = set(re.findall(r"^##\s+[\w.]+\.\s+Group\s+([A-Z])\b", spec,
                              re.M))
    registered = {a[0] for a in SPEC_AXIOMS}
    missing = sorted(declared - registered)
    assert not missing, (
        f"SPEC.md declares axiom group(s) {missing} that no id in "
        f"SPEC_AXIOMS belongs to. Register them in src/trace_registry.py "
        f"and map them in SPEC_TO_AXM — otherwise they are law that no "
        f"ADR can cite and no crosswalk check covers.")


def test_known_gaps_stay_visible_in_the_crosswalk_document():
    """The two real gaps (drift firing, the ledger) are findings against
    SPEC's closure claim. They must remain stated in the prose, so
    closing them is a deliberate act with an ADR — never a silent edit."""
    text = CROSSWALK.read_text()
    gaps = sorted(a for a, (kind, _) in AXM_UNMAPPED.items() if kind == "gap")
    missing = [a for a in gaps if f"axm:{a}" not in text]
    assert not missing, (
        f"gap(s) not documented in AXIOM_CROSSWALK.md: {missing}")
