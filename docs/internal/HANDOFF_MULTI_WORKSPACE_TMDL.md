# Handoff — 12's workspace profile must support multiple workspaces

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
