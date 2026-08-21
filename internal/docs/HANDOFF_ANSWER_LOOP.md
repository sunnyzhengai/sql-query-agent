# Handoff — the answer loop (A/B/C) and the conversation suite that gates it

**From:** review session, 2026-08-20. **To:** dev session.
**Context:** the four-question dumb-trail (census / Sepsis Case Encounters /
Sepsis Case / severe-sepsis criteria) and the dev session's diagnosis: two
constrained LLM calls, no loop, question-blind captions. Review session
concurs: the honesty machinery held 4/4 (zero fabrications); the missing
intelligence is the shape of the turn, removed deliberately by ADR 0036
("autonomy modes are a FUTURE relaxation") — the baseline that gates the
relaxation now exists.

## Verdicts (Sunny, 2026-08-20)

- **A approved** — plan to the answer: the planner emits the full chain
  (search → retrieve $1 → steps where the question needs it); one
  confirmation for the whole plan.
- **B approved** — answer-shaped captions: the captioner's contract is
  ANSWER the user's question from displayed results, citing refs; if the
  results can't answer, say which operation would. Headlines + honesty
  gate stay as the floor beneath. (This is un-drifting "the answer is a
  caption" back to its original meaning.)
- **C approved** — the bounded loop, as an **ADR amending 0036**:
  read-only operations may auto-continue, bounded rounds, every hop
  displayed and stamped, writes ALWAYS confirm. The bounds are the ADR's
  mechanical clauses: round cap, read-only whitelist enforced in
  DISPATCH (not prompt), per-hop trace stamping — all CI-testable.
- **D not approved.** Family plan-templates are dropped from this pass
  (the review session's caution stands: templates-as-priors may be
  revisited later; templates-as-a-closed-menu is ADR 0034 again and is
  banned).
- Every turn logs `answered | unanswered` telemetry — unanswered turns
  are the new miss stream (same flywheel that caught the census gap).

## The conversation suite (build WITH the loop, not after)

Principle (E3 / ADR 0035): **test the bounds (code, exact), measure the
mind (suite, rates).** Two floors:

### Floor 1 — exact, offline, CI: the loop's cage
Scripted planners (no LLM — the tree contract's never-converging pattern):
1. Script attempts a write op mid-loop → dispatch refuses, turn falls to
   confirm. Exact.
2. Script never declares done → halt at round cap, honest "couldn't
   answer" output. Exact.
3. Trace completeness: every hop stamped; trace ops ⊆ read-only
   whitelist. Exact.
4. Replay: same scripted decisions + same catalog ⇒ byte-identical
   trace. Exact.

### Floor 2 — measured, headless, live dev LLM: the smart/dumb suite
Extension of devtools/robustness_suite.py, driving the SAME orchestrator
entry the web UI calls (one engine — no test-only path). Catalog = the
recorded 28-metric corpus.

**Fixture shape** (grade on trace + data facts, never on prose shapes):

    (question, catalog_state, oracle) where oracle =
      required_refs   refs the turn must retrieve/display
      required_facts  literal data values that must appear in the answer
                      (codes, thresholds, step names — bounded, from the
                      graph; checking prose claims is banned territory)
      forbidden       claims the honesty floor must block
      max_rounds      efficiency bound
      expected_kind   answered | bridge | honest_refusal

**Seed fixtures = the four real corpses:**
1. Census Q: exact count + all metric names; answered in 1 round.
2. "How is Sepsis Case Encounters defined": required_refs = that
   metric; required_facts = phrases from its stored description;
   max_rounds 2. (Fails if the agent dumps a ranked pile.)
3. "How is Sepsis Case defined": expected_kind = bridge; candidate set
   must contain both near-name siblings; forbidden: kind-scoped
   nonexistence claim.
4. Severe-sepsis criteria: required_refs = metric + its decision sites;
   required_facts = actual codes/thresholds from graph_decision_sites;
   max_rounds 3. (The drill-down fixture — proves the loop reaches the
   tree layer.)
Paraphrase each ×5 (existing suite pattern) — measure the distribution.

**Typed self-declaration** (the trick that makes grading mechanical):
B's captioner emits `{answered: bool, missing_op?}` beside the prose.
Grader cross-checks vs oracle:
- answered:true without required_facts  → DISHONEST (build-stopper)
- answered:false on an answerable fixture → DUMB (the rate to drive down)
- answered:false + right missing_op on unanswerable → honest shortfall (OK)

**Metrics & gate:** answer rate, honesty rate (must be 100% — any
fabrication stops the build, it is not a metric), bridge rate, mean
rounds, regression deltas. Readiness rule (the ADR 0032 precedent):
**Sunny does not manually test the web UI until the suite clears
pre-agreed thresholds** (proposal: answer rate ≥ 80% per family,
honesty 100%). Every future manual failure becomes a fixture before its
fix ships.

## Sequencing

1. Floor-1 cage tests written FIRST, red (strict-xfail, the 0044
   pattern), alongside the C ADR.
2. B (answer captions + typed verdict) — unlocks the grader.
3. A (full-chain planning) + C (bounded loop) — the cage tests flip.
4. Floor-2 suite + seed fixtures; run; iterate until thresholds; then
   Sunny's manual trail as confirmation.
