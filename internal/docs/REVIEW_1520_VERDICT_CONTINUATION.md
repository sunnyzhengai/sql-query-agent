# Review note — 1.52.0 verdict-driven continuation (framework analysis)

**From:** review session, 2026-08-21. **To:** dev session.
**Verdict: principled — approved. And it's a deeper framework win than
the P6 framing: it's the first live M5 diagnosis.**

## The reframe (record this in the ADR/commit trail)

"Round-laziness variance" typed per AI_VIA_AXIOMS Group J/M:

- The continuation decision — given a typed verdict with
  `answered=false`, a NAMED missing op, and remaining budget — is
  **computable**: `answered=false ∧ missing_op ≠ null ∧ budget > 0 →
  continue` has a right answer derivable from data.
- By **M5**, a computable decision must never rest on a stochastic
  decider. The coin-flip next-hop WAS a stochastic decider holding a
  computable decision — an M5 violation manifesting as score variance
  on identical code (0.83 → 0.67 → 0.50).
- 1.52.0 moves the decision to code, where M5 says it always belonged.
  The variance wasn't noise to tolerate; it was a misfiled decision
  type, and the framework's vocabulary named both disease and cure.

## Axiom checks — all pass

- **M4/pin**: trigger reads TYPED verdict fields, never language — no
  lexicon; the pin stands legitimately.
- **Bounds**: at-most-once + round cap + anti-flail dedup across
  passes → no sandbagging path (crying "unanswered" buys exactly one
  hop, then the floor).
- **B2**: honesty machinery re-runs in full on the second answer;
  doubling-down model floored (cage-tested). Boundary intact.
- Bonus inversion: humility telemetry (answered=false with facts
  present) converts from dead weight to fuel — the engine acts on the
  model's own admission.

## Watch item (do not fix with another continuation)

The **humble-but-blind** residual: model declares answered=false,
names an op it ALREADY ran, dedup rightly blocks the repeat — turn
stays "unanswered" while the answer's facts are displayed. No
continuation mechanism fixes this; the evidence is already on screen.
If it appears beyond trace levels, it's an **M2 evidence-presentation
problem** (how the facts render into the mind's view), not an M1 loop
problem. File it under the right axiom or it will breed stamps.

## Bookkeeping (after the scorecard lands, not before — J discipline)

If drilldown/anaphora stabilize: add the receipts row to
docs/AI_VIA_AXIOMS.md §7 —
"Round-laziness variance (scores bouncing on identical code) → M5
applied to the loop's own continuation decision" — the framework's
first live use as a diagnostic. Claim after measurement.
