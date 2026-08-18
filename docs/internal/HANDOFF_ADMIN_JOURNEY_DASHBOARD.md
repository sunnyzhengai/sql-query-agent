# Handoff — admin journey dashboard: one table, the whole pipeline

**From:** review session, 2026-08-18 (Sunny's spec: simple and accurate —
a basic table + bar charts; sql files by type/source/schema; PBI reports
by workspace; SQL<->PBI ties visible incl. multi-proc-per-report; errors
after each notebook by type; ALL in one table so per-stage outcomes are
scannable). **To:** dev session. Realizes the UI half of
HANDOFF_FUNNEL_AND_FALLOUT; serves Question Map family G.

## Design

1. **ops_metric_journey** — one row per metric_id, columns = stages:
   type/schema/db (input_sql_sources) | loaded | parsed + error_type
   (ops_pipeline_validation + ops_parse_errors) | in_graph | card |
   described-status (07b: ok/rejected/pending) | report_count +
   report_names (input_report_sources) | published collibra/pbi
   (gov_publish_log). Row read left-to-right IS the pipeline.
2. **ops_report_journey** — one row per PBI report: workspace, model,
   proc_count + proc list, match kind (lineage-exact | heuristic |
   unmatched), published-where. The other side of the M:N tie.
3. **Visuals (exactly four):** the journey table (stage columns
   conditionally colored); stacked bar files by type x schema; bar
   reports by workspace; bar fell-off by stage colored by error_type
   (the funnel).
4. **Accuracy contract:** columns are joins over existing contract
   tables only — no dashboard-side computation; reconciliation tests
   pin loaded = parsed + errored (etc.) per stage so the dashboard
   cannot drift from the system of record.

## Open questions (SUNNY to answer before build)

(a) Materialize ops_metric_journey as a Delta table written by 06
    (review session leans yes: versioned, gate-checked, registry
    contract) vs semantic-model view only.
(b) Workspace NAMES need an id->name lookup added to 12's collection —
    worth the extra API call? (census currently has ids only)
(c) error_type taxonomy scope v1: parse errors only, or unified now
    with 07b rejections + publish failures (fallout-rows work will
    unify eventually regardless).
