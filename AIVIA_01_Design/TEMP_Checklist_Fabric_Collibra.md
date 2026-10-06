# TEMP — The Fabric + Collibra Road, Step by Step

**Status:** TEMP working file (Sunny's ask, 2026-10-05).
Check boxes off in order; delete the file when Step 5 closes.

**Decided already (2026-10-05, all ruled, no open questions):**
- Wheel 0.5.0 adds the LLM phases (07 cards + 09 terms); key never inside the wheel.
- One delivery file: `ai_delivery.json` — each step updates its part.
- Work LLM seat: her personal OpenAI key, work-approved, **metadata only**.
- 02 dictionary goes to work: exactly three files.
- Collibra path: five checks at work, then sandbox, then batch.

**The laws that ride along every step:**
- Metadata boundary: the LLM sees only text from SQL files + dictionaries — never query results.
- The wall: work SQL and work outputs never come back to this repo.
- Capacity law: Fabric runs happen by her hand, one at a time.
- Blessed-only: no term name reaches Collibra before she blesses it.

---

## STEP 0 — Build at home (Claude builds, Sunny validates)

- [x] 0.1 DONE 2026-10-05: the delivery writer (`ai_delivery.py`) — 15 locks
      red then green; local `AIVIA_01_Data/ai_delivery.json` built (census
      terms replayed, zero new paid calls); the three retired 09 files deleted.
- [x] 0.2 DONE 2026-10-05: wheel 0.5.0 built (`AIVIA_01_Code/dist/
      ai01_sqldesc-0.5.0-py3-none-any.whl`) — LLM modules in, openai a
      declared dependency, key read from `OPENAI_API_KEY` at run time, new
      CLI: `ai-describe --deliver <tmdl> <sql> <out> [--dict <d02>]`
      (no key = honest degrade: technical voice, no terms); 23 packaging +
      09 locks green.
- [x] 0.3 DONE 2026-10-05 (her word: "files approved for steps 0.3 0.4").
- [x] 0.4 DONE 2026-10-05: the census term blessed, her ruling recorded
      verbatim in the 07 registry; ai_delivery.json shows blessed: 1.
      STEP 0 CLOSED. (Wheel renamed ai01-sqldesc same day, her ask.)

## STEP 1 — Rehearsal on HER personal Fabric (proves the whole chain)

- [ ] 1.1 Run the sync (existing manifest): 05 + 06 + 07 estate, the SQL files,
      the 02 dictionary, the blessing registry.
- [ ] 1.2 Upload the wheel to the Fabric environment — 0.5.1
      (the env-first key fix, built at the rehearsal).
      THE ONE-WHEEL LAW (learned here 2026-10-05): exactly ONE
      sqldesc wheel in the environment, ever — two versions
      under different package names silently fight over the
      same module files and the loser's modules vanish with no
      install error. Delete old sqldesc wheels before Publish;
      the aivia01 chat wheel may stay (no shared modules).
      After Publish: STOP the session — only a fresh session
      sees the new environment.
- [ ] 1.3 Notebook: read the key from `aivia01-kv / aivia01-azure-openai-key`
      (or the OpenAI key), run: parse -> 06 -> 07 cards -> 09 terms ->
      `ai_delivery.json`.
- [ ] 1.4 Eyeball `ai_delivery.json` + the official txt on Fabric.
- [ ] 1.5 Bless on Fabric (proves blessing works away from the laptop).
      Mind the >1 hour token-cache limit on long runs.

## STEP 2 — Pack the work bag (collect BEFORE the first work session)

- [ ] 2.1 The wheel file: `ai01_sqldesc-0.5.0-py3-none-any.whl`
      (the ScriptDom DLL rides inside it — nothing separate to carry).
- [ ] 2.2 The three dictionary files:
      `02_emr_data_dictionary_extraction_column.json`,
      `..._extraction_value.json`, `..._extraction_table.json`.
      **Never**: the 1.2 GB embeddings file, or `02_sql_extraction.json`.
- [ ] 2.3 Her OpenAI key — goes in as a workspace secret / notebook secret,
      **never pasted into a committed notebook cell**.
- [ ] 2.4 The Collibra id list (ask the Collibra admin, or look up as admin):
      BT domain id · BT asset type id · description attribute id ·
      technical-definition attribute id (confirm one exists — may need creating) ·
      PBI report asset type id · a service account / API token.
- [ ] 2.5 Locations at work: the DevOps folder of `*.SemanticModel` (TMDL),
      and which SQL files go in the input folder.

## STEP 3 — First work session: the three connectivity tests (10 minutes)

- [ ] 3.1 From a work Fabric notebook: one tiny call to `api.openai.com`
      with her key — does it answer?
- [ ] 3.2 One authentication ping to the Collibra API — reachable?
- [ ] 3.3 Open the TMDL checkout — are the `*.SemanticModel` folders there?
      (Any "no" = an IT conversation before anything else is built.)

## STEP 4 — Work sync and run

- [ ] 4.1 Create the lakehouse folders: `Files/01_sql_input/`,
      `Files/02_dictionary/`, `Files/out/`.
- [ ] 4.2 Upload: the three dictionary files; the work SQL files into
      `01_sql_input/`; install the wheel in the environment.
- [ ] 4.3 Run the chain on ALL files in `01_sql_input/`:
      parse -> 06 -> 07 cards -> 09 terms -> `ai_delivery.json`
      (+ the official txt). Parse failures are counted rows, never silent.
- [ ] 4.4 Read the official txt; gap-check cards and technical definitions.
- [ ] 4.5 Bless the term names (nothing unblessed goes further).

## STEP 5 — Collibra publish (her notebook, outside this repo)

- [ ] 5.1 Spot-check 3 report names: our report names vs the Collibra
      PBI assets — match character for character? (Mismatch = add a
      name-mapping step to the notebook.)
- [ ] 5.2 SANDBOX: push ONE report description + ONE Business Term into a
      test domain. Look at the rendering — do the line breaks between the
      labeled lines survive? (If flattened: switch to `<br>` / rich text.)
- [ ] 5.3 The notebook law: create-or-update **by name** — re-runs update,
      never duplicate; reads `ai_delivery.json`; filters blessed itself.
- [ ] 5.4 The batch. Print the counted result: reports updated, terms
      created, terms updated, failures.
- [ ] 5.5 Her eye on 3 published pages in Collibra. Done — delete this file.
