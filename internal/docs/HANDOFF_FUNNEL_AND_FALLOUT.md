# Handoff — pipeline funnel + fallout capture (the error graph's foundation)

> **Status update (2026-08-18, later): the VIEW landed in 1.21.0.** ops_funnel (registry-declared, 06-owned): per run per stage in/out/fell-off with aggregated reason codes; unexplained drops named loudly. 02's error rows and 07b's rejected rows are folded into the same view; 08's unmatched reports now write no_collibra_match fallout rows (matcher retrofit complete). Agent instructions teach funnel-first health answers. Remaining: the admin DASHBOARD page reading ops_funnel (report work, not plumbing) and errors-as-graph-nodes (ADR 0039 follow-up).
> **Status (2026-08-18, dev session): implemented in 1.17.0.**
> ops_fallout is a registry-declared contract table (append; run_at/stage/entity_id/reason_code/reason_text/contract_id) and 12 — the worst offender — is retrofitted end to end: partition-parse drops, naming refusals, and collector skips all land as rows; the notebook prints a per-run funnel (files -> sources -> fallout by reason). Remaining scope, deliberately deferred: the admin-dashboard funnel page, folding 02's error rows / 07b's rejected rows into one funnel VIEW, and errors-as-graph-nodes (ADR 0039 follow-up) — those want the dashboard work, not more plumbing.

**From:** review session, 2026-08-18 (Sunny, mid-diagnosis of the 12 run:
"each error is gold and needs to be captured and tied back to the root
cause" + "admin dashboard: each step, how many come through vs fell off").
**To:** dev session. Extends ADR 0039's follow-up (ops_runtime_error_events,
errors as graph nodes).

## Field indictment

12's name-derivation dropped 373/601 reports and recorded the reasons in
STDOUT ONLY ([i] lines) — the stdout-state disease, recommitted by the
newest step. Same for parser fallout distribution (which models yielded
zero SQL sources and why is currently unknowable by query).

## Wanted — one mechanism, two views

1. **Fallout rows (the gold):** every stage that drops an entity writes a
   row: run_at, stage, entity_id (report/model/metric), reason_code
   (machine), reason_text (human), contract_id where applicable. One
   contract table (e.g. ops_fallout) or per-family; registry-declared;
   gates enforce as usual. Reason codes make root-cause aggregation a
   GROUP BY — including across customers later (the product-signal
   flywheel from the error-contract philosophy).
2. **Funnel view (the dashboard):** per run, per stage: in_count,
   out_count, fell_off (derivable from fallout rows + stage outputs).
   Admin telemetry report gets a funnel page; each fell-off number links
   to its fallout rows. ops_build_summary already carries some counts —
   extend, don't duplicate.
3. Retrofit the worst offenders first: 12 (derivation skips, parser
   zero-SQL models, collector skips), 02 (already good — error rows exist;
   fold into the same funnel view), 07b (status=rejected already lands —
   same view), matcher (unmatched reports with reason).
4. Errors-as-graph-nodes (ADR 0039 follow-up) can then hang off fallout
   rows — entity ids are graph node ids; the chain error → contract →
   data becomes walkable as designed.
