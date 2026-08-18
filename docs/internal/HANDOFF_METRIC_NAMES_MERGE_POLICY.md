# Handoff — input_metric_names needs a merge policy (manual overrides survive)

**From:** dev session, 2026-08-18 (demo build; Sunny hit the collision
live and asked the right question: "who updated it? why do we need to
re-upload?"). **To:** dev session, post-demo.

## The collision

input_metric_names has TWO writers with overwrite semantics:
1. The manual route — a curated CSV (business names for all metrics,
   report_name + report_url) loaded by hand; `source = "manual"`.
2. 060's derivation — proc-keyed names from report lineage;
   `source = "pbi_report"`, report_url always empty.

Whichever runs last clobbers the other. Today's workaround is a
sequencing dance (060 → re-upload CSV → 300) that a customer admin
would never discover — the exact stdout-state/tribal-knowledge disease
the contracts exist to kill. Our own registry declares one owner per
table; this table quietly has two.

## Wanted

1. **Merge, don't overwrite.** 060 writes derived rows WITHOUT
   destroying manual rows: manual (`source = "manual"`) wins per
   metric_id; derived fills the rest. One pure function
   (merge_metric_names(manual_rows, derived_rows)) with tests; 060
   reads the existing table, merges, writes.
2. **report_url derivation** (kills most of the manual need): 060
   already knows workspace id + semantic model id per report; one
   REST call maps model -> bound report id -> URL. Derived rows then
   carry real links and the CSV shrinks to genuine curation.
3. A tiny manual-names route notebook (0xx family) so "upload the CSV"
   is a numbered route with a contract, not a scratch cell.
4. Registry: input_metric_names declares 060 owner + manual route as
   enricher (or vice versa) — the ground-truth tests then enforce
   whatever we decide is true.
