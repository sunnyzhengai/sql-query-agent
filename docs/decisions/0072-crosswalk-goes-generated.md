# ADR 0072 — The crosswalk goes generated (ratchet turn 6)

**Status:** ACCEPTED 2026-09-02 — Sunny's "proceed" on the ratchet
(ADR 0067).

## Decision

`AXIOM_CROSSWALK.md` becomes a **generated projection**: Direction 1
derives from `spec_registry` (each record gained a `parent_note` — the
one-line *why* of its mapping, now data beside the mapping it
explains); Direction 2 derives from `AXM_UNMAPPED`; grounding ADRs
derive from the trace registry. The doc can no longer disagree with
the ledger, because it IS the ledger, rendered.

This closes a loop opened in turn 1: the mappings became data on
2026-09-02 morning, but the doc stayed hand-prose — two homes for one
truth, the exact dual state the invariant forbids. Six hours was an
acceptable half-life for it; permanence would not have been.

## What moved to history (the ADRs, per the invariant)

The hand-written crosswalk's narrative — how the audit found the two
systems correlated only by claim, the five original unmapped axioms,
the closure of the two real gaps — lives in ADRs 0064/0065/0067 and
this file's git history. The generated doc keeps a one-line pointer.

## Consequences

- `docs/architecture/`: **10 files — 3 authored + 7 generated.**
- Crosswalk stamp → 0072; freshness CI-checked
  (`test_crosswalk_doc_on_disk_is_fresh`).
- The remaining authored three: SPEC (the big final turn),
  ARCHITECTURE (stays authored by design), REFERENCE_ARCHITECTURE
  (slim candidate).

## Relations

0067 (the ratchet) · 0064/0065 (the history the prose held) · turn 1
(the ledger this projects).
