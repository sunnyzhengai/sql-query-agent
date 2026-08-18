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

## Amendment (same day, code-read + field output): two more name-thieves

1. **Distinctness key unnormalized**: keyed on raw (schema_name,
   sql_object) — the same proc spelled differently across a model's
   partitions (case, schema alias) counts as 2 distinct and wrongly
   refuses ("Coding Productivity: 2 distinct"). Fold case (and consider
   schema-alias mapping) before counting.
2. **Kind filter drops view-as-Table navigations**: connectors commonly
   reach VIEWS as Kind="Table"; sources typed Table are excluded, so
   reports with real SQL lineage print "0 distinct SQL objects"
   ("CCHCS Telemedicine Report"). Replace the TMDL-Kind test with the
   authoritative membership test: sql_object (schema-qualified, folded)
   ∈ input_sql_sources.metric_id → it can name metrics; DirectLake
   lakehouse tables self-exclude by not matching the corpus.

Field expectation: 228/601 derived is a floor produced by three fixable
conservatisms (direction, normalization, kind-trust) — not estate shape.
Diagnostic queries used at work are in the session log if needed.
