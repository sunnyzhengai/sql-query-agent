# 07_fabric_move — production runbook

Sunny's manual runbook for moving the 05/06/07/08 estate to her
personal Fabric and running the D8 end-to-end proof (the wheel,
her reports, the descriptions file). Every file name and command
exact. Written by Claude 2026-10-04; grows as steps land.

> **Status:** DRAFT — no step has run yet. Step 0 is a BUILD ITEM
> (needs her go before any shipping). Golden counts land after
> each step's first clean run, same as the 04 runbook.

---

## Prerequisites — check once

- [x] The 04 runbook's estate stands: workspace, environment
  **AIVIA_01_ENV**, lakehouse **AIVIA_01_LH** (ids below, from 04).

  | item | id |
  |---|---|
  | workspace | `23112b57-368a-46ed-941b-c10e3baad392` |
  | environment | `1b87c0e2-f56c-4253-9933-fb7a60db181d` |
  | lakehouse | `891d75cb-c87e-4096-9383-9cd7df9d6ef3` |
  | Census Totals Demo (FAKE) — semantic model | `8d901a4b-63ae-4897-9f08-cc09c6d07282` |
  | Census Totals Demo Report (FAKE) | `10100484-4bcc-438f-b32c-23ffad258d53` |

- [x] The D8 target exists (created 2026-10-04, her sign-ins):
  the FAKE demo model's TMDL carries the 17 census
  sourceColumns + `EXEC dbo.COOK_RPT_USP_CCHCS_ADT_MONTHLY_
  INPATIENT_CENSUS_TOTALS_SSRS` (named to the corpus file so
  the D8 run shows a RESOLVED link). Never refresh it — it is
  TMDL truth only. Step C's simplest route for THIS model:
  REST getDefinition (format TMDL) into the lakehouse tmdl
  folder; git sync works too.

- [x] The work wheel exists:
  `AIVIA_01_Code/dist/aivia01_sqldesc-0.1.0-py3-none-any.whl`
  (payload manifest-locked; test_packaging_wheel.py green).
- [ ] Local suite green first (the standing gate):

  ```
  /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v
  ```

- [ ] All commands from the repo root:
  `cd /Users/sunnyzheng/sql-query-agent`
- Capacity law: every Fabric-touching step is HER hand, one at a
  time; publish and notebook runs spend capacity — the scripts
  ask before spending.

---

## Step 0 — BUILD ITEM (her go required; red test first)

`sync_files.py`'s SYNC_FILES constant lists exactly the eight
02/03 contract files. Shipping the 05/06/07 artifacts needs that
constant extended per the 07 contract's production home
(`Files/Data/07_business_descriptions/` etc.). Per the process:
her go -> the contract's file list amended -> red test -> code.
The files to add (census scope — the corpus is paused by her
word):

- 05_semantic_graph/: the twelve 05 sheets (kind library included)
- 06_technical_descriptions/: 06_description_sheet.json,
  06_voicing_ledger.json, the census .txt + .svg
- 07_business_descriptions/: 07_business_sheet.json,
  07_blessing_registry.json, 07_fact_voices.json,
  07_code_sightings.json, 07_walk_trace.json,
  07_naming_gaps.json, the census .txt + .facts.txt
- 08_pbi_lineage/: ships AFTER the D8 run creates it (step D)

## Step A — ship the files (after step 0 lands)

```
/opt/homebrew/bin/python3.11 AIVIA_01_Code/sync_files.py --workspace 23112b57-368a-46ed-941b-c10e3baad392 --lakehouse 891d75cb-c87e-4096-9383-9cd7df9d6ef3
```

Paste as ONE line (the 2026-09-30 zsh lesson). Unchanged files
skip; `--force` re-uploads. Success: the printed shipped/skipped
equation matches the extended SYNC_FILES count.

## Step B — the work wheel into the environment (portal, her hand)

The sqldesc wheel is a CUSTOM LIBRARY (sync_wheel.py ships
aivia01, not this one — portal route until ruled otherwise):

1. Portal -> workspace -> **AIVIA_01_ENV** -> Libraries ->
   Custom libraries -> Upload ->
   `aivia01_sqldesc-0.1.0-py3-none-any.whl`.
2. **Publish** (capacity — several minutes; her word to spend).
3. Success: publish state `success`; `aivia01-sqldesc 0.1.0`
   listed next to `openai 3.19.2` and `aivia01 0.3.0`.

## Step C — her reports' TMDL into the lakehouse

The D8 input is the TMDL of HER personal workspace's semantic
models:

1. Portal -> workspace settings -> **Git integration** -> connect
   her repo (GitHub or DevOps) -> sync. The workspace lands as
   folders; each model is `<Name>.SemanticModel/definition/
   tables/*.tmdl`.
2. Clone/pull that repo locally, then upload the
   `*.SemanticModel` folders to the lakehouse:
   `Files/Data/08_pbi_lineage/tmdl/` (portal upload-folder, or
   OneLake file explorer — her choice).
3. The SQL corpus the reports should resolve against goes to
   `Files/Data/08_pbi_lineage/sql/` (the .sql files her models
   execute — from her own repo/export; work SQL never enters
   THIS repo, the wall law).

## Step D — the D8 run (a Fabric notebook, the wheel's proof)

New notebook on **AIVIA_01_ENV**, one cell; run = capacity, her
hand:

```python
import sqldesc_cli
rows = sqldesc_cli.report_descriptions(
    "/lakehouse/default/Files/Data/08_pbi_lineage/tmdl",
    "/lakehouse/default/Files/Data/08_pbi_lineage/sql",
    "/lakehouse/default/Files/Data/08_pbi_lineage/out")
print(len(rows), "reports described")
```

- The loader finds the DLL inside the wheel (SCRIPTDOM_DLL is
  set by the CLI from the packaged assets); Fabric's dotnet
  serves the runtime (the old estate's proven route).
- Output: `Files/Data/08_pbi_lineage/out/`:
  `08_pbi_reports.json`, `08_lineage_ledger.json`,
  `08_report_descriptions.json` + the per-file 06 texts.
- The printed conservation equation (bindings == resolved +
  unresolved) is the step's green.

## Step E — her gap-check (THE ACCEPTANCE, D8c)

Open `08_report_descriptions.json`. Per report: the name is
hers, the executes list is right, each linked file's
description reads true against the SQL she knows. Her clean
read CLOSES phase 08; findings return here as rows and the
loop repeats.

---

## After acceptance

- Record golden counts in this runbook's Status line (reports,
  bindings, resolved/unresolved) — the rerun baseline.
- The corpus run (the other 7 files + her hundreds) stays at
  her word; this runbook's steps A/D rerun unchanged for every
  future batch.
