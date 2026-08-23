# Handoff — the design-review clause (three questions before first code)

**From:** Sunny via review session, 2026-08-21. **To:** dev session.

## Verdict (Sunny, 2026-08-21)

The recurring loop — *missing contract → testing reveals it → add a
registry* — is now converted from reactive to proactive. Mandate:
**every new artifact class answers the three questions BEFORE its
first line of code, and the answers become its registry rows.**

1. **Inventory (spec:C1 shape):** the complete frontier, enumerated as
   data, with exclusion rows for everything deliberately outside.
2. **Conservation (spec:C2 shape):** the equation proving nothing
   vanished (`handled ⊎ fallout = total`) and where fallout lands.
3. **Drift (STPA shape):** what MECHANICALLY fires when reality
   diverges from the declaration. "Someone would notice" = a missing
   feedback loop.

## Already written (review session; ratify, don't re-author)

- **SPEC.md §3b** — the clause, with enforcement language; version
  bumped 0.5 → 0.6, changelog entry added, header marked "pending dev
  ratification." Ratify it in the next ADR you write (the
  reachability ADR is the natural vehicle).
- **docs/METHODOLOGY.md — "The enforcement lineage"** — the prior-art
  map (Design by Contract, formal spec, dependency theory,
  traceability matrices, poka-yoke, SRE postmortems, Sculley 2015,
  eval-driven development, STPA) plus the two umbrella standards
  worth knowing for healthcare positioning: IEC 62304 and DO-178C.
  Whitepaper material — the machinery already exists; the names buy
  recognition with compliance reviewers.

## Immediate application (the acceptance test for the clause itself)

The in-flight **reachability work** is the first artifact class born
under the clause. Its design review must cite the three answers:

1. Inventory: the reachability contract — every (node kind, edge kind)
   × (searchable / retrievable / traversable) → named op or explicit
   exclusion row. (Your audit table, made permanent and CI-checked.)
2. Conservation: catalog coverage equations (e.g., 432 steps = 413 in
   catalog + 19 excluded-with-reason; 6,528 nodes = reachable ⊎
   excluded — no third bucket).
3. Drift: a new graph layer or edge kind landing without a
   reachability row fails CI; coverage regressions surface on the
   funnel/admin dashboard, not in a code walk.

If the clause is awkward to satisfy on its first real subsystem, that
finding goes in the ADR — the clause is new and gets calibrated by
use, loudly, like everything else.

## PARKED (for Sunny)

- Nothing new; existing parked items stand (Round-4 tenant steps,
  Marketplace claims, tier prerequisite ratification).
