# 0040 — The consumption layer: reports and measures get a home

**Status:** Accepted
**Date:** 2026-08-16

## Context

Business logic splits across TWO layers in every customer environment:
SQL (procs/views — on-prem heavy) and DAX (measures and calculated
columns — Fabric-native heavy). Both native parsers exist (ScriptDom for
SQL; the TMDL parser in `src/extractor/devops_tmdl.py`, library-grade
with byte-exact fixtures), but the graph has no report or measure node
types — the DAX half was extracted and discarded. Meanwhile the graph
model has carried a DIMENSION layer since inception whose producer
(`add_dimension_node`) has ZERO callers: `graph_dimension` and
`graph_edge_tech2dim` export as permanently empty tables and pollute the
NL2GQL surface with dead vocabulary (HANDOFF_PBI_SEMANTIC_LAYER, audit
2026-08-16).

## Decision

**The graph gains a consumption layer above canonical; the ghost
dimension layer is removed.**

1. **Two new node layers.** `report` — a Power BI report (identity:
   report name from the .SemanticModel folder). `measure` — a DAX
   measure or calculated column (identity: `report/table[name]`), its
   expression stored on the node the same way transformations store SQL
   fragments. DAX is business logic and gets the same treatment as SQL:
   parsed natively, held in the graph, described by 07.
2. **Four new edge types, all deterministic.**
   - `report_to_canonical`: from TMDL partition lineage (the M
     expression names the proc/view it executes). Resolution follows
     ADR 0016 folding: qualified `schema.object` or unambiguous bare
     name; ambiguous names are SKIPPED and reported, never guessed
     (ADR 0005).
   - `report_to_technical`: DirectLake partitions (the Fabric-native
     default; TMDL pattern 5 — `mode: directLake`, `entityName`) name a
     warehouse TABLE, not a proc, so the report attaches to the
     technical layer. A DirectLake table absent from the dictionary is
     skipped with a reason.
   - `report_to_measure`: ownership — the measure lives in that report's
     semantic model.
   - `measure_to_column`: DAX column references (`'Table'[Col]` /
     `Table[Col]`), resolved only when the referenced PBI table's
     partition source is a known graph object AND the column exists as a
     technical node under it. Unresolvable references are skipped and
     counted, never guessed.
3. **Dimension layer removed** — `NodeLayer.DIMENSION`,
   `EdgeType.TECHNICAL_TO_DIMENSION`, `add_dimension_node`, the
   `graph_dimension` / `graph_edge_tech2dim` exports and their registry
   contracts. The ghost rule (zero-caller code may not keep existing by
   default) applies to model vocabulary as much as to code. Filtering
   semantics, if ever needed, are a property of technical column nodes,
   not a fourth layer. Existing deployments drop the two empty Delta
   tables at upgrade (resume checklist).
4. **Landing tables, contract-first.** `input_report_sources` (partition
   lineage rows) and `input_dax_expressions` (measures + calc columns)
   are written by notebook `12_ingest_semantic_models` and consumed by
   03 as optional inputs (setup-completeness records apply, ADR 0039
   machinery). `input_metric_names` flips planned→active with 12 as its
   owner: a report that EXECs exactly one proc names that metric
   (`source=pbi_report`).
5. **Semantic-model source profiles** mirror the extractor's
   (HANDOFF_TO_DEV_EXTRACTOR item 6): `devops_git` (PAT read from Key
   Vault at run time — never in config or code) and `folder` (git-synced
   workspace folders / uploaded Files — no DevOps dependency; this is
   the Fabric-native path).
6. **`fabric_pbi.py` verdict: WIRED, not deleted** — description
   write-back onto PBI reports is the enrichment-out story ("the answer
   is a caption" applied to the report itself), published by notebook
   `13_publish_pbi`. Its name-similarity matcher is deleted and replaced
   with lineage-exact matching over `report_to_canonical` edges —
   publishing onto a guessed report is worse than not publishing.

## Consequences

- Exports gain `graph_report`, `graph_measure`,
  `graph_edge_report2canonical`, `graph_edge_report2measure`,
  `graph_edge_measure2column` (camelCase columns, ADR/NL2GQL
  convention); lose the two dimension tables. Agent instructions grow
  "which reports use metric M" / "what DAX depends on column C"
  traversals.
- 07 will see measure nodes with DAX fragments; the PHI gate applies to
  DAX exactly as to SQL before any prompt is built (ADR 0025 — DAX can
  embed literals too).
- The blast-radius query (ADR 0026) extends one hop up: a failing metric
  now names the REPORTS it feeds — support can say "this outage affects
  these two dashboards".
- Scope: **decided by Sunny (2026-08-16) — the PBI layer IS v1
  Marketplace scope.** Customers ask about REPORTS, not procs/views; the
  report layer is the customer-facing entry point, so this work precedes
  launch hardening. The dbt manifest parser (third layer of the parser
  federation) stays out of v1 unless a design partner needs it.
