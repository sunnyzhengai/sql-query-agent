# Handoff — business-name derivation should be proc-keyed, not report-keyed

**From:** review session, 2026-08-18 (first full-estate 12 run at work:
601 models, 1065 SQL sources, 3646 DAX expressions — but only 228 names
derived). **To:** dev session.

## Finding

Current rule: a report names a proc only when the REPORT maps to exactly
one SQL object. Multi-source dashboards (common: 2-6 procs per model)
therefore name nothing, even though each of their procs may be consumed
by ONLY that report.

## Wanted

Invert (or add) the uniqueness test: for each PROC, if exactly one report
consumes it (per input_report_sources), that report's title is the proc's
business name — regardless of how many other procs the report also reads.
Keep refuse-over-guess for procs consumed by multiple reports (list them,
name nothing). Expectation from the field data: substantially more than
228/601 derivable without guessing. The report→object edges are all
already captured in input_report_sources; this is derivation-only.
