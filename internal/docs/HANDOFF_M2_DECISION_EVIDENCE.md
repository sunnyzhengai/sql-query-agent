# Handoff — M2 design pass: decision evidence rides the metric record

**From:** review session, 2026-08-21. **To:** dev session.
**Commission:** the anaphora residual's root design question — how a
metric record presents its decision evidence so the mind doesn't need
a hop it keeps declining — run as a §3b design pass. Recommendation
below; dev owns the mechanics.

## The diagnosis, typed

The humble-but-blind shape is an M2 problem (evidence presentation),
not M1 (loop) — the review note's instruction held and holds: no new
stamps, no second continuation, no prompt lines. The mind declines the
metric→step→site hop because each hop costs a round and the model is
round-frugal; no amount of pointing fixes a hop the mind won't take.

**The principle (ADR 0018, verbatim precedent):** when a question
shape matters and the mind is weak at it, MATERIALIZE the shape —
compile the hop away. USES_TABLE did this for metric→table depth;
decision evidence gets the same move. General law worth recording in
the design: retrieval surfaces are shaped to the question
distribution — high-traffic evidence rides the record at zero hops;
long-tail depth stays behind hops.

## Recommended design

1. **Materialize the metric→decision closure** (build-time, count-
   verified — the ADR 0018/0037 pattern): first-class edges from a
   metric to every decision site in its calculation chain, derived
   from existing step→site edges. Checkable-cache law applies:
   materialized count = live-traverse count, asserted.
2. **The metric record carries its decision evidence inline**:
   retrieve(metric) returns the decision-site summary — exact total
   (never capped), plus the top-k site rows (predicate, columns,
   redacted-at-rest expressions), cap DISCLOSED per B3, "show all"
   behavior per the 413-row-wall fold pattern. A drill-down or
   anaphora question then needs ZERO hops: the criteria are on the
   record the mind already retrieved.
3. **Optional, if cheap**: rank the inline sites by closeness to the
   turn's question phrase (the scored-census pattern at decision
   grain) so the k shown are the k asked about. Deterministic,
   complete-total-disclosed, no prompt involvement.
4. **Adjacency noted, not scope**: these closure edges are the same
   material ADR 0046's shape matching consumes — build them once,
   shaped for both consumers. Do not expand this pass into the 0046
   engine.

## §3b answers (the design's registry rows)

1. **Inventory:** which evidence rides which record — metric records
   carry the decision closure (total + top-k inline); step records
   keep their own sites (exists); reachability registry gains the
   rows; anything not inlined is reachable by the existing retrieve
   branches or carries an exclusion.
2. **Conservation:** inline_k ⊎ folded = total, total always exact
   and machine-stamped; the closure derivation itself conserves
   (sites_via_closure = Σ sites_via_steps, asserted).
3. **Drift:** materialized-vs-live count diff fails validation (the
   0037 consistency check); a metric record whose inline total
   disagrees with graph_decision_sites is a red run, not a support
   ticket.

## Acceptance

- Anaphora family stabilizes at/above bar with the prompt pin intact
  and zero new prompt/stamp/continuation machinery — the thesis test
  form: the fix is data-shaped or it has failed.
- The stamp-contradicting telemetry counter goes to zero (nothing
  left to contradict — the evidence is on the record).
- PHI: inline decision expressions are the redacted-at-rest exports —
  confirm the same gate covers the retrieve path.
- On stabilization, BOTH held conditions clear → the §7 receipts row
  (M5 continuation + this M2 materialization, one receipt, corpses
  noted) finally lands. Claim after measurement, as ever.

## Sequencing

Proceed now — anaphora is the last family below bar and this is the
walk's remaining blocker. Sunny's tenant republish for Round 4 runs in
parallel; if this pass changes exports (closure edges), say so BEFORE
she republishes so she runs the pipeline once, not twice.
