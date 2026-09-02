# ADR 0073 — SPEC v1.0: the spec becomes a projection of its own ledger (the final ratchet turn)

**Status:** ACCEPTED 2026-09-02 — Sunny's order ("do the final SPEC
turn"), completing the ADR 0067 sequence.

## Decision

Every axiom's **law formula, gloss, origin, status, and stated gap**
join the ledger (`src/spec_registry.py`) as fields beside the parents,
notes and checks that arrived in turns 1 and 6. `SPEC.md` is now
**generated**: the frame prose (§1–§4, §3b, the Σ signature, the
model-checking frame, honest limits, the frozen changelog) lives in
`scripts/spec_frame.md`; each axiom renders uniformly from its record
— law, gloss, origin, framework grounds (the crosswalk now visible
inline), checks, status. The thirteen groups' three different formats
(prose axioms, 4-column tables, the 6-column T table) become one.

**Fidelity method:** fields were extracted MECHANICALLY from SPEC.md
v0.9 (48/48; four stragglers — F, E6, H1, L3 — patched by hand from
their known text) and the frame template was cut from the same file,
verified to zero leftover axiom markers and 48 placeholder ids with
no duplicates. The status vocabulary closed at four: ENFORCED,
PARTIAL, GATED, and **JUDGED** — extraction surfaced T3's status as a
legitimate fourth value the §3 vocabulary never listed.

## The changelog freezes

§1 has said it since v0.1: *"the ADRs are the changelog of this
theory."* At v1.0 that becomes literal — spec changes are ADRs, the
changelog section is preserved history. The amendment rule stands
unchanged: an axiom change requires an ADR; a status flip is a ledger
edit citing its check.

## Consequences

- Statuses are queryable data (32 ENFORCED · 13 PARTIAL · 2 GATED ·
  1 JUDGED) — "what is our enforcement debt?" is now one expression.
- Hand-editing SPEC.md is a red build (freshness CI); the doc cannot
  disagree with the ledger.
- `docs/architecture/`: **10 files — 2 authored (ARCHITECTURE,
  REFERENCE_ARCHITECTURE) + 8 generated.** Sunny's clean-slate target
  (AXIOMS + PROTOCOL + one architecture page + decisions/ +
  projections) is, within REFERENCE_ARCHITECTURE, the actual state.

## Relations

0067 (the ratchet, completed) · 0047/§16 (the amendment rule, intact)
· 0065 (JUDGED's origin) · turns 1–6 (the practice runs for this).
