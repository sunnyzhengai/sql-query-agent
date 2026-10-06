# TEMP — The Fabric + Collibra Road, Step by Step

**Status:** TEMP working file (Sunny's ask, 2026-10-05).
Every box names its ARTIFACT (the thing that must exist) or its
ACTION (what was done when nothing is produced). Check boxes in
order; delete the file when Step 5 closes.

**THE IDS:** `AIVIA_01_Test/AIVIA_01_Production/
07_fabric_move_production_steps.md` — workspace / environment /
lakehouse id table + the ready-filled sync command.

**Decided already (2026-10-05, all ruled):** wheel carries the LLM
phases, key never rides · one delivery file `ai_delivery.json` ·
work seat = her OpenAI key, metadata only · 02 upload = 3 files ·
Collibra = five checks, sandbox first.

**The laws riding every step:** metadata boundary (LLM sees SQL
text + dictionaries, never query results) · the wall (work data
never comes home) · capacity law (her hand per run) · blessed-only
(no unblessed name reaches Collibra) · THE ONE-WHEEL LAW (one
sqldesc wheel in the environment, ever; stop the session after
every publish).

---

## STEP 0 — Build at home — CLOSED 2026-10-05

- [x] 0.1 The delivery writer.
      ARTIFACTS: `AIVIA_01_Code/ai_delivery.py` · local
      `AIVIA_01_Data/ai_delivery.json` (census terms, blessed: 1) ·
      15 locks green in `test_09_business_terms_data_contract.py`.
- [x] 0.2 The work wheel with the LLM seat.
      ARTIFACT: `AIVIA_01_Code/dist/ai01_sqldesc-0.5.1-py3-none-any.whl`
      (0.5.1 = env-first key fix; 0.5.0 superseded same day) ·
      9 packaging locks green · CLI `ai-describe --deliver`.
- [x] 0.3 Her eye on the census card + technical definition.
      ACTION: approved 2026-10-05 ("files approved for steps 0.3 0.4").
- [x] 0.4 The first blessing.
      ARTIFACTS: `terms` entry in `07_blessing_registry.json`
      (ruling verbatim) · `ai_delivery.json` counts.09 blessed: 1.
      Commits: 86dc10e + 6fa7f27 on dev.

## STEP 1 — Rehearsal on HER personal Fabric

- [x] 1.1 DONE 2026-10-05. ARTIFACT: the sync census —
      "1 uploaded (2,475 bytes), 31 skipped — 32 files total";
      the one upload was 07_blessing_registry.json (the census
      blessing riding up), everything else byte-identical.
      [x] side-check: the 8 sql files present in
          Files/Data/01_subject_sql_files (manual upload 9/27;
          not in the manifest, the sync never touches them).
      [x] the extension catch (2026-10-05): the 9/27 uploads WERE
          bare (no .sql) — she re-uploaded the 8 with .sql and
          removed the bare ones. LESSON for Step 4 at work: after
          any portal upload of sql files, verify the full name
          ends `.sql` — the run sweeps `*.sql` only.
- [x] 1.2 DONE 2026-10-05 ("wheel synched"): old sqldesc wheels
      deleted (0.4.0 + 0.5.0), 0.5.1 uploaded, published.
      ARTIFACT: AIVIA_01_ENV Custom libraries = ai01_sqldesc-0.5.1
      + aivia01-0.3.0 (chat, stays), publish Success.
- [x] 1.3 DONE 2026-10-06 ("it worked! ai_delivery.json is there") —
      on wheel 0.5.3, after the rehearsal-night ladder: 0.5.1
      env-first key, 0.5.2 names offer, 0.5.3 corpus offer; the
      repo-relative class closed by the parents[1] sweep.
      ARTIFACTS: Files/Data/ai_out/ai_delivery.json + the official
      txt, built on Fabric by her hand. Cells kept below for reruns.
      ARTIFACTS: `Files/Data/ai_out/ai_delivery.json` ·
      `Files/Data/ai_out/08_report_descriptions.txt` · the run's
      printed summary line ("ai_delivery.json: N report(s)...").

      THE CELLS (notebook 07_description, environment
      AIVIA_01_ENV, lakehouse AIVIA_01_LH attached as default):

      Cell 0 — THE PREFLIGHT (0.5.4, her ask after the httpx
      find): every prereq checked before any paid call; run
      AFTER Cell 1 sets the key, or expect the one key FAIL.
      Must end `... / 0 fail`:
      ```python
      import sqldesc_cli
      sqldesc_cli.preflight(
          "/lakehouse/default/Files/Data/08_pbi_lineage/tmdl",
          "/lakehouse/default/Files/Data/01_subject_sql_files",
          "/lakehouse/default/Files/Data/ai_out",
          dict_dir="/lakehouse/default/Files/Data/"
                   "02_emr_data_dictionary")
      ```

      Cell 1 — the key (must print `key loaded: True`):
      ```python
      import os
      key = notebookutils.credentials.getSecret(
          "https://aivia01-kv.vault.azure.net/",
          "aivia01-openai-key")
      os.environ["OPENAI_API_KEY"] = key
      print("key loaded:", bool(key))   # never print the key
      ```

      Cell 2 — carry the blessing registry into the run:
      ```python
      import shutil, os
      os.makedirs("/lakehouse/default/Files/Data/ai_out/07",
                  exist_ok=True)
      shutil.copy(
          "/lakehouse/default/Files/Data/07_business_descriptions/"
          "07_blessing_registry.json",
          "/lakehouse/default/Files/Data/ai_out/07/"
          "07_blessing_registry.json")
      ```

      Cell 3 — THE RUN (several quiet minutes is normal; the
      tmdl path found 2026-10-05: the phase 08 demo model
      Census_Totals_Demo_FAKE.SemanticModel lives at
      Files/Data/08_pbi_lineage/tmdl — expect "1 report(s)"):
      ```python
      import sqldesc_cli
      sqldesc_cli.deliver(
          "/lakehouse/default/Files/Data/08_pbi_lineage/tmdl",
          "/lakehouse/default/Files/Data/01_subject_sql_files",
          "/lakehouse/default/Files/Data/ai_out",
          dict_dir="/lakehouse/default/Files/Data/"
                   "02_emr_data_dictionary")
      ```
      NOTE for 1.5: the home blessing was keyed to the FILE name
      (report-less at home); on Fabric the census term sits
      under the report Census_Totals_Demo_FAKE — different key,
      no auto-restore. Blessing it fresh there IS step 1.5.

      Cell 4 — the first eye (feeds 1.4):
      ```python
      print(open("/lakehouse/default/Files/Data/ai_out/"
                 "08_report_descriptions.txt").read()[:4000])
      ```
- [ ] 1.4 Her eye on Fabric.
      ACTION: read the official txt + ai_delivery.json in the
      Files pane; check: reports tied (not all reportless), cards
      in clinician voice, term names worth blessing.
- [ ] 1.5 One blessing on Fabric.
      ACTION: bless one term from the notebook (bt.bless with the
      ai_out paths).
      ARTIFACTS: the term's row flips blessed in the Fabric
      ai_delivery.json · the registry on Fabric gains the entry.

## STEP 2 — Pack the work bag (before the first work session)

- [ ] 2.1 ARTIFACT in the bag: `ai01_sqldesc-0.5.1-py3-none-any.whl`
      (DLL rides inside).
- [ ] 2.2 ARTIFACTS in the bag: the 3 dictionary files
      (`...extraction_column.json`, `...extraction_value.json`,
      `...extraction_table.json`). NEVER: the 1.2 GB embeddings
      file, `02_sql_extraction.json`.
- [ ] 2.3 ACTION: her OpenAI key ready to enter as a notebook/
      workspace secret at work. NEVER pasted in a committed cell.
- [ ] 2.4 ARTIFACT: the Collibra id list written down — BT domain
      id · BT asset type id · description attribute id ·
      technical-definition attribute id (may need creating) ·
      PBI report asset type id · service-account token.
- [ ] 2.5 ARTIFACT: the two work paths written down — the DevOps
      TMDL folder · the SQL input folder.

## STEP 3 — First work session: three connectivity tests (10 min)

- [ ] 3.1 ACTION: one tiny call to api.openai.com from a work
      Fabric notebook. ARTIFACT: a model's one-line answer.
- [ ] 3.2 ACTION: one auth ping to the Collibra API.
      ARTIFACT: an HTTP 200 printed.
- [ ] 3.3 ACTION: open the TMDL checkout.
      ARTIFACT: `*.SemanticModel` folders listed by eye.
      (Any failure = IT conversation before anything else.)

## STEP 4 — Work sync and run

- [ ] 4.1 ACTION: create `Files/01_sql_input/`, `Files/02_dictionary/`,
      `Files/out/` in the work lakehouse.
- [ ] 4.2 ACTION: upload the 3 dictionary files + the work SQL
      files; install the wheel in the work environment (the
      one-wheel law; stop session after publish).
- [ ] 4.3 ACTION: run `ai-describe --deliver` over ALL files in
      `01_sql_input/` — her hand.
      ARTIFACTS: `Files/out/ai_delivery.json` ·
      `Files/out/08_report_descriptions.txt` · parse failures as
      counted rows in the output, never silent.
- [ ] 4.4 ACTION: gap-check the official txt (cards + technical
      definitions) with her eye.
- [ ] 4.5 ACTION: bless the keeper names.
      ARTIFACT: blessed rows in the work ai_delivery.json +
      the work-side registry.

## STEP 5 — Collibra publish (her notebook, outside this repo)

- [ ] 5.1 ACTION: spot-check 3 report names vs Collibra PBI assets,
      character for character. ARTIFACT: the 3 matches noted (or
      the mapping rule the notebook needs).
- [ ] 5.2 SANDBOX. ACTION: push ONE report description + ONE term
      to a test domain. ARTIFACT: the rendered Collibra page, line
      breaks intact (else switch to <br>/rich text).
- [ ] 5.3 ACTION: the notebook written — create-or-update BY NAME,
      re-runnable, reads ai_delivery.json, filters blessed itself.
      ARTIFACT: the notebook in her work workspace.
- [ ] 5.4 THE BATCH. ARTIFACT: the counted result printed —
      reports updated / terms created / terms updated / failures.
- [ ] 5.5 ACTION: her eye on 3 published Collibra pages.
      Then DELETE THIS FILE — the road is walked.
