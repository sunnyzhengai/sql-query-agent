# The Delivery Bucket — everything a new tenant needs

This folder is the ONE catch-all for deploying the SQL
description engine on a customer's Microsoft Fabric tenant
(ruled 2026-10-06). One direction only: things are born here
or copied in at pack time; nothing a customer makes ever
lands back in it.

## What's in the bucket

| item | what it is |
|---|---|
| `work_wheel_runbook.md` | the step-by-step deployment runbook |
| `tenant_intake.md` | THE INTAKE SHEET — every value to gather, fillable; a blank = not ready to deploy |
| `dictionary_extraction/` | 4 shape-matched Clarity dictionary queries + the ZC value generator — run unscoped at the tenant |
| `tools/csv_to_json.py` | the zero-logic converter (copied in at pack time from the engine codebase) |
| `wheel/ai01_sqldesc-<newest>.whl` | the engine (copied in at pack time) |

## PACK STEP (before carrying this folder anywhere)

1. Copy the NEWEST `ai01_sqldesc-*.whl` into `wheel/` —
   exactly one.
2. Copy the current `csv_to_json.py` into `tools/`.
(The pack-time copies keep single sources of truth at home;
the hygiene lock sweeps this folder for brand strings, estate
values, and keys.)

## Prereqs at the tenant (collect BEFORE the first session)

FILL `tenant_intake.md` AS YOU GO — it is the one sheet of
every id, path, secret name, and sign-off; the checklist below
is the summary, the sheet is the record.

- [ ] A Fabric workspace with: a lakehouse, an Environment
      item, notebook rights
- [ ] The Environment: `openai` pinned (3.19.2) as a PUBLIC
      library (its dependency tree must resolve) + the ONE
      wheel from `wheel/` as a custom library; published
- [ ] An LLM API key, stored as a workspace/notebook SECRET —
      never in a cell, never in a file
- [ ] Read access to the Clarity dictionary tables (metadata
      only — the engine never reads patient data)
- [ ] The folder of `*.SemanticModel` (TMDL) folders for the
      Power BI reports in scope
- [ ] The `.sql` files to describe (names MUST end `.sql`)

Then follow `work_wheel_runbook.md` top to bottom — it begins
with a preflight that checks every one of these and names the
fix for anything missing.
