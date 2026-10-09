08_pbi_lineage_data_contract

Status: DRAFT — rides the 08 design doc's decisions D1-D7;
complete BEFORE the first red test per the amendments-first law.
Scribed by Claude 2026-10-04; Sunny owns it.

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- A folder of <Name>.SemanticModel directories (TMDL as text:
  definition/tables/*.tmdl), from a DevOps checkout or a REST
  getDefinition dump. The folder path is a run parameter, never
  hardcoded; work-side folders never enter this repo.
- The 01 subject corpus: AIVIA_01_Data/01_subject_sql_files/
  *.sql — the resolution target (read only).

What is the output of this data contract?

THE RENAME AMENDMENT (2026-10-08, the naming law — step table in
10_work_wheel_data_contract.md; approved + built same day):
- 08_pbi_reports.json    -> 08_pbi_lineage_output.json
- 08_lineage_ledger.json -> 08_pbi_lineage_ledger_output.json
Older passages below citing the pre-rename names read as the new
names. Names only — the view-tie ruling (SELECT/Item binding)
is the 0.8.0 slice: RULED same day (10_work_wheel.md D15) —
build08 learns NativeQuery SELECT ... FROM <object> and
[Item="..."] table-import bindings so views reach their
reports (the first tenant's views are all reportless today);
binding kinds and the resolve law amend here at that build.

- AIVIA_01_Data/08_pbi_lineage/08_pbi_reports.json — one row
  per REAL semantic model (D3):
  - name: the model folder name without .SemanticModel
  - executes: [resolved .sql file names, deduped, ordered]
  - bound_fields: {sql_file: [imported sourceColumns, deduped]}
  - bindings: [{table, binding_kind: exec|entity|source,
    raw_target, resolved: sql_file|null}] — the full evidence
    trail, one row per table binding (D1/D2)
  - source: "tmdl (<folder>; plumbing excluded)"
- AIVIA_01_Data/08_pbi_lineage/08_lineage_ledger.json — the
  honesty ledger (D2/D3):
  - unresolved: [{model, table, binding_kind, raw_target}]
  - unconsumed_sql: [corpus files no model touches]
  - counts: {models, tables_read, plumbing_skipped, bindings,
    resolved, unresolved} — the conservation equation
    (bindings == resolved + unresolved) is a test.

Definitions:
- A BINDING is one table's one source reference (D1 kinds).
- RESOLUTION is case-insensitive, bracket-stripped, last-two-
  name-parts matching into the corpus (D2); a miss stays a
  counted row, never a guess.
- CONSERVATION: every non-plumbing table file read lands as
  >=1 binding row or is counted in a named skip class; the
  equation is a test, as always.

- RETIRED INTO ai_delivery.json (the consolidation ruling,
  2026-10-05, recorded in the 09 contract): the json below is
  superseded — the 08 step now writes reports[].report +
  .files (and reportless_files[]) in AIVIA_01_Data/
  ai_delivery.json; the OFFICIAL TXT below STAYS as the human
  read view, regenerated from ai_delivery.json (her ruling:
  "keep the per-files"). 08_pbi_reports.json and the ledger
  stay as the store. Historical shape, until the delivery
  build lands:
- AIVIA_01_Data/08_pbi_lineage/08_report_descriptions.json —
  the D8 end-to-end artifact (built on her personal Fabric by
  the wheel; the acceptance surface): one row per PBI report:
  - report: the model name
  - executes: the linked sql files
  - description: the deterministic (06) description of what
    feeds the report — the linked file's technical card; when a
    report executes several files, one description per file,
    keyed
  Her gap-check of THIS file is the phase acceptance (D8c).
- AIVIA_01_Data/08_pbi_lineage/08_report_descriptions.txt —
  THE OFFICIAL READ FILE (AMENDED 2026-10-04, her work-
  transition ask, wheel 0.4.0): one block per report x linked
  file — report name, sql file, the description — with the
  VOICE labeled: `voice: business` when a runtime-offered 07
  sheet carries the card, `voice: technical` otherwise; never
  a silent downgrade. The json stays the machine artifact;
  the txt is the read surface she collects at work.

Who writes what (authorship)?
- Both outputs: machine-written by the build, whole-file,
  re-runnable, deterministic (same inputs, same bytes).
- This contract and the design doc: Sunny owns; amendments
  follow the amendments-first law.
- No LLM anywhere in this phase; no paid calls; no network.
