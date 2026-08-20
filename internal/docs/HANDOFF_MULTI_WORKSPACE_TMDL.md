# Handoff — 12's workspace profile must support multiple workspaces

> **Status (2026-08-18, dev session): items 1–4 implemented in 1.16.0.**
> semantic_models.workspace_ids: list[str] (workspace_id stays as
> single-value sugar; empty everything = current workspace) with
> resolved_workspace_ids(); collect_from_workspaces gathers all ids in
> ONE pass and 12 does ONE write; per-workspace counts print in the run
> report. Item 3 verdict: the existing first-report-names-it rule is
> PROMOTED to contract — workspace_ids ORDER is the naming priority for
> a metric shared across workspaces, every other report stays listed in
> report_name (never silently deduped); expressed in the config
> comment, the input_metric_names contract description, and a test.
> The field patch shape is now product — it dies on next sync.

**From:** review session, 2026-08-18 (work deployment: reports live across
4–5 PBI workspaces; config takes ONE workspace_id — true at 1.13 and at
HEAD). **To:** dev session.

## Wanted

1. `semantic_models.workspace_ids: list[str]` (keep workspace_id as
   single-value sugar; empty list + empty id = current workspace).
   Collect across all ids in ONE run and ONE write — sequential per-
   workspace runs would clobber each other under overwrite semantics
   (same clobber class as the metric-name manual-curation note).
2. Per-workspace collection counts in the run report (field patch prints
   them; keep that).
3. Decide the cross-workspace duplicate rule: two reports in different
   workspaces EXECing the same proc → duplicate metric_id in
   input_metric_names. Options: primary-report rule (first/configured
   priority), or one-to-many report_sources with a chosen display name.
   Let the contract express the decision, not dedupe silently.
4. Field patch (pasted-notebook, work): loop over raw-yaml workspace_ids —
   fold the shape into the product so the patch dies on next sync.
