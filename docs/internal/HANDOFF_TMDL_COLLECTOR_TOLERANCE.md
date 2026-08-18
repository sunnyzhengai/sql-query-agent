# Handoff — workspace TMDL collector needs per-model failure tolerance

> **Status (2026-08-18, dev session): implemented in 1.16.1.**
> collect() is record-and-continue per model; skips classified (404=not-exportable/expected, 403=permission/actionable, timeout, error) and surfaced in 12's per-workspace skip report. 1.16.0 did NOT have this (verified — collect raised through); the field patch shape is now product.

**From:** review session, 2026-08-18 (work deployment, live failure).
**To:** dev session. Addendum to the multi-workspace work (1.16.0) —
verify whether collect_from_workspaces already has this; 1.13's collect()
did not.

## Field failure

FabricWorkspaceTmdlSource.collect() dies on the FIRST model whose
getDefinition 404s. Real workspaces are full of models that can't export
TMDL (default semantic models auto-created for lakehouses/warehouses,
legacy datasets) — one of them crashed the entire 5-workspace collection
at work.

## Wanted

Per-model record-and-continue (the parse_step policy): try
get_definition_parts per model, collect failures as (model, reason),
print a visible skip report, never die on one model. Skips should be
distinguishable by class where possible (404 = not exportable/expected;
403 = permissions/actionable; timeout = retry later). Field patch doing
exactly this is in Sunny's pasted work notebook — fold in, kill the patch.
