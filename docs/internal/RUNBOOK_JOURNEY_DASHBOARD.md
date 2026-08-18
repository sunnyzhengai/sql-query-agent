# Runbook — build the admin journey dashboard (Power BI Desktop)

Data contract: everything below reads THREE tables 500_validate
materializes — `ops_metric_journey`, `ops_report_journey`, `ops_funnel`
— plus `ops_fallout` for drillthrough. The dashboard computes NOTHING
(accuracy contract); if a number looks wrong, the bug is in the
pipeline, never the report.

## Steps

1. Run the pipeline through `500_validate` at least once (it writes all
   three tables at the end of its run).
2. Open Power BI Desktop → **OneLake data hub** → your Lakehouse →
   connect (Import or DirectLake, either works).
3. Select tables: `ops_metric_journey`, `ops_report_journey`,
   `ops_funnel`, `ops_fallout`. Load.
4. Model view — create two relationships:
   a. `ops_funnel.stage` → `ops_fallout.stage` (many-to-many is fine;
      used only for drillthrough).
   b. No relationship between the two journey tables (different grains
      — filter through visuals instead).
5. Visual 1 — **the journey table** (Table visual):
   a. Fields, in order: `metric_id`, `source_type`, `source_schema`,
      `loaded`, `parsed`, `error_type`, `in_graph`, `card`,
      `described_status`, `report_count`, `report_names`,
      `published_collibra`, `published_pbi_writeback`.
   b. Conditional formatting: background color on each boolean stage
      column — rule: value = True → green, False → red; on
      `described_status` — ok → green, pending → yellow,
      rejected_by_agent → red.
6. Visual 2 — **files by type × schema** (Stacked bar):
   Axis `source_schema`, Legend `source_type`, Values = count of
   `metric_id` (from `ops_metric_journey`).
7. Visual 3 — **reports by workspace** (Bar):
   Axis `workspace_name`, Values = count of `report_name` (from
   `ops_report_journey`).
8. Visual 4 — **the funnel** (Stacked bar):
   Axis `stage`, Values = `fell_off` (from `ops_funnel`, filtered to
   the latest `run_at` — add a page filter: `run_at` = Top 1 by
   `run_at`). Tooltip: `reasons`. This is the fell-off-by-stage chart;
   reason detail is in the tooltip and in `ops_fallout` drillthrough.
9. Drillthrough page (optional): target `ops_fallout` — fields
   `entity_id`, `reason_code`, `reason_text`, `run_at`; set `stage` as
   the drillthrough field so right-clicking a funnel bar opens the
   backing rows.
10. SQL↔PBI tie check: click any row in Visual 1 with
    `report_count` ≥ 2 — `report_names` lists every consuming report
    (one row per metric, always). The reverse direction is Visual 3's
    table twin: `ops_report_journey.proc_names`.

## What the numbers must satisfy (spot-check after build)

- Visual 1 row count == `input_sql_sources` row count (every metric,
  exactly once).
- loaded = parsed + errored per the funnel's 200 stage.
- A metric with `published_collibra = True` has a success row in
  `gov_publish_log` with target `collibra`.
