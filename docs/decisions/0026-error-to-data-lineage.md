# 0026 — Every error names its data: error-to-data lineage

**Status:** Accepted
**Date:** 2026-08-06

## Context

The steward backlog (2026-08-02) flagged that error visibility and data
lineage don't meet: parse/error tables carry `metric_id` but mostly without
declared reference invariants back to `input_sql_sources`, and
`ops_installation_errors` records error *signatures* with no notion of
which objects a live failure touched. The operating requirement is
"supportable at a distance" (5-rule gate): when a customer reports "the
agent can't answer about metric X," support must be able to walk from the
symptom to the failing pipeline stage to the source rows — as a query, not
a log dive.

## Decision

**An error record is lineage: it must resolve to the data it blocks.**

1. **Reference invariants become mandatory on error tables.** Every
   contract in the registry whose rows are *about* a metric declares
   `{"kind": "reference", "column": "metric_id", "references":
   "input_sql_sources.metric_id"}` — `ops_error_log`, `ops_parse_errors`,
   `ops_parse_results`, `ops_extraction_inspection`. The gate then enforces
   what was previously convention: no orphan error rows, no error rows
   whose metric can't be found.
2. **Runtime failures record affected objects.** Installation/runtime
   error *events* gain an `affected_objects` field (JSON list of
   metric_ids or table names touched by the failing stage). The seeded
   signature catalog (`ops_installation_errors`) stays as the knowledge
   base of *kinds* of errors; a planned `ops_runtime_error_events` append
   log records *occurrences* with lineage — signature match, run_id,
   affected objects, stage. `/troubleshoot` then answers "what does this
   failure block?" not just "what is this failure?"
3. **The blast-radius query is the product surface:** given a failing
   metric_id, join error → parse status → graph presence → metric_logic
   presence to state exactly where in 02→07 the metric stopped and what
   certified answers are affected. This is a view over existing tables
   plus (1) and (2) — the design goal is that the joins are *declared*
   (invariants) so the view cannot silently rot.
4. **Direction of truth:** lineage points from error to source
   (`metric_id` outward), never by parsing error text. Error messages stay
   human debris; lineage lives in typed columns.

## Consequences

- `test_table_contracts` grows assertions the moment the invariants land —
  drift between error tables and sources becomes a red build, not a
  support surprise.
- `ops_error_log` is append-only across runs, so its reference invariant
  must tolerate metrics that have since left the corpus: the invariant
  binds within a run (`run_id`-scoped), the historical log keeps orphans
  as history. This scoping needs support in the invariant checker
  (currently whole-table) — small, and the checker is ours.
- The agent's admin commands (`/errors`, `/health`) upgrade from counts to
  blast radius ("2 parse failures, blocking 2 of 28 metrics: A, B").
- Composes with the flywheel (ADR 0023): an error blocking a high-usage
  metric outranks one blocking a never-asked metric in the support queue —
  usage weight is the triage function everywhere.
