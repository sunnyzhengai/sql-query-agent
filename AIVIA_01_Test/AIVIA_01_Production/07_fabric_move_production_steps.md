# 07_fabric_move — production runbook

Sunny's manual runbook for moving the 05/06/07/08 estate to her
personal Fabric and running the D8 end-to-end proof (the wheel,
her reports, the descriptions file). Every file name and command
exact. Written by Claude 2026-10-04; grows as steps land.

> **Status:** Step 0 BUILT 2026-10-04 (her "go, build step 0":
> 04 contract amended -> lock red -> SYNC_FILES +24, census
> scope -> 26/26 green). Step A RAN CLEAN 2026-10-04 (Sunny),
> golden verbatim: `sync census: 31 uploaded (1,473,548,271
> bytes), 1 skipped — 32 files total` (a rerun's expectation:
> 0 uploaded, 32 skipped). Step B GREEN 2026-10-04 (her portal
> eye): both wheels Success in AIVIA_01_ENV custom libraries —
> aivia01_sqldesc-0.1.0 beside aivia01-0.3.0 (DIFFERENT
> packages, disjoint module names; the one-wheel law governs
> versions of the SAME package). Shipped via the sync_wheel
> machinery, scratchpad runner. Step C GREEN 2026-10-04
> (scratchpad runner, her two sign-ins), golden verbatim:
> `step C done: 5 tmdl files + 1 sql ->
> Files/Data/08_pbi_lineage/` — the demo model's TMDL round-
> tripped via getDefinition into tmdl/Census_Totals_Demo_FAKE
> .SemanticModel/, the census .sql into sql/. Step D GREEN
> 2026-10-04 (her notebook run; one pool fix on the way — the
> env's SAVED executor count was 2 from a bigger pool, dynamic
> allocation off + instances 1 = 16/112 exactly, published).
> Golden verbatim: `08 lineage: 1 report(s); conservation 1
> bindings == 1 resolved + 0 unresolved` · parse matched local
> to the digit (2 statements, 3 scopes, 19 predicates, 83
> expressions) — ScriptDom ran IN FABRIC from the wheel's DLL ·
> the 7 clarity tables landed in the UNKNOWN-TABLES human
> queue (the empty-dictionary degraded mode, as designed) ·
> `1 reports described`. Step E PASSED 2026-10-04 (Sunny: "a
> passes" — the deterministic card read true against the SQL;
> PHASE 08 ACCEPTED, D8c). Rider built same day at her word:
> wheel 0.2.0 adds dict_dir (a runtime-offered dictionary
> speaks names); rerun of step D with the dict cell is
> OPTIONAL — the named-voice variant, after 0.2.0 replaces
> 0.1.0 in the environment.

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

## Step 0 — BUILT 2026-10-04 (the standing order held)

04 contract amended first, the list lock red second, the
constant third; 26/26 green. SYNC_FILES now ships 32 files.
The files added (census scope — the corpus stays paused by her
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
    "/lakehouse/default/Files/Data/08_pbi_lineage/out",
    dict_dir="/lakehouse/default/Files/Data/"
             "02_emr_data_dictionary",
    business_dir="/lakehouse/default/Files/Data/"
                 "07_business_descriptions")
for r in rows:
    print("REPORT:", r["report"])
    for f, card in r.get("business", {}).items():
        print("  feeds from:", f)
        print(" ", card)
```

(dict_dir — 0.2.0: her dictionary speaks — 'Census' (6), the
departments by name. business_dir — 0.3.0: the report row
carries the CLINICIAN CARD from her shipped 07 sheet, blessed
lines riding. Omit both for the pure work-mode voice. Needs
aivia01-sqldesc 0.3.0 published, replacing the prior version —
one version of the same package at a time, the one-wheel law.)

- The loader finds the DLL inside the wheel (SCRIPTDOM_DLL is
  set by the CLI from the packaged assets); Fabric's dotnet
  serves the runtime (the old estate's proven route).
- Output: `Files/Data/08_pbi_lineage/out/`:
  `08_pbi_reports.json`, `08_lineage_ledger.json`,
  `08_report_descriptions.json` + the per-file 06 texts +
  **`08_report_descriptions.txt` — THE OFFICIAL READ FILE**
  (0.4.0): report, sql file, description, `voice:` labeled
  business|technical (never a silent downgrade) — the one
  file she collects at work.
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
