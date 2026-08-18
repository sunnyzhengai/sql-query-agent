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

## Decisions — ALL RESOLVED (Sunny, 2026-08-18): BUILD-READY

(a) **Materialize via 06.** ops_metric_journey and ops_report_journey
    are Delta tables written by 06, registry contracts, gate-checked —
    no dashboard-side computation, ever.
(b) **Workspace names: yes.** 12's collection adds the id->name lookup
    (one API call per workspace per run); both journey tables and all
    chart axes use names.
(c) **Error taxonomy: unified now.** One error_type vocabulary across
    parse errors, 07b rejections, and publish failures from day one
    (aligns with the fallout-rows reason-code work — share the codes).

## Grain rules (settled with Sunny, same day)

- View 1 (ops_metric_journey) is PROC/METRIC-GRAIN and drives the
  funnel: pipeline stages happen to metrics, so stage columns live here.
  ONE ROW PER METRIC, always — a proc feeding 2 reports gets
  report_count=2 and a '; '-joined report_names (input_metric_names
  convention), NEVER two rows. Grain integrity: a junction may not
  multiply the driving grain, or funnel totals stop reconciling.
- View 2 (ops_report_journey) is REPORT-GRAIN (one PBI report uses many
  procs — the common direction): proc_count + proc list per report.
  Exploded (proc, report) pairs stay in input_report_sources (the
  junction). Clickthrough: journey row -> View 2 filtered by proc.
- Publish flags named published_collibra / published_pbi_writeback
  (08 / 13 respectively).
