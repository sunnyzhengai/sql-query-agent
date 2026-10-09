10_work_wheel_data_contract

Status: CONSOLIDATED 2026-10-06 (rides 10_work_wheel.md
D1-D10; the briefs' contract content folded in, superseded
pointers left behind). Sunny owns it.

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- The build (at home): AIVIA_01_Code module sources (staged
  copies brand-scrubbed, D5), libs/ ScriptDom DLL,
  05_kind_library.json (the ratified vocabulary — travels per
  the portability split; the canary lock verifies no customer
  rows).
- The run (any tenant) — ALL RUNTIME-OFFERED (D6):
  - a folder of *.sql files (names MUST end .sql)
  - a folder of *.SemanticModel folders (TMDL)
  - --dict: the 02 extraction files — FOUR, corrected
    2026-10-06 at the bag design (the engine reads column +
    value + table + join; join drives the value-meaning
    bridge). THE FULL-DICTIONARY RULING (her ask, same day):
    at work the dictionary is the FULL Clarity extraction,
    unscoped — run the 02 extraction SQL against their
    dictionary tables, raw output only. SLIM BY BIRTH: raw
    extraction carries NO embeddings (embeddings are the 02
    build's chat-side addition and never travel to the wheel);
    full-Clarity slim JSON is low hundreds of MB — fine for
    Fabric Files; slow load = declared debt, parquet later if
    it bites. Per-corpus scoping is RETIRED for work.
  - the names asset beside the dictionary (03_chat_bot/) —
    optional; absence honest
  - OPENAI_API_KEY in the environment — REQUIRED (ruled
    2026-10-08, supersedes the D4 degrade; effective wheel
    0.7.0): a missing or failed key is a blocking preflight
    FAIL — fix it, then proceed; no degraded delivery. Until
    0.7.0 ships, the old degrade text below stands in code.
  - a registry copy at <out>/07/07_blessing_registry.json —
    optional; blessings restore when present

What is the output of this data contract?
- THE ARTIFACT: ai01_sqldesc-<version>-py3-none-any.whl —
  contents == THE ALLOWLIST exactly (D2), machine-checked:
  scriptdom_loader.py · semantic_graph.py ·
  technical_descriptions.py · pbi_lineage.py ·
  business_descriptions.py · business_terms.py ·
  ai_delivery.py · sqldesc_cli.py ·
  ai_sqldesc_assets/{__init__.py, the DLL,
  05_kind_library.json, MANIFEST.txt}.
  Dependencies declared: pythonnet, openai (the environment
  installs them; at Fabric add openai as a PUBLIC library so
  its tree resolves — the httpx lesson, 2026-10-06).
- THE DELIVER RUN's outputs (in the runner's out dir):
  ai_delivery.json (the one delivery file — shape owned by
  the 09 contract) · 08_report_descriptions.txt (the human
  read view, voice labeled) · the 05/06/07 working folders.
- THE PREFLIGHT's outputs (D8): the printed BOARD (one line
  per check, PASS/FAIL with the fix named), the returned
  failure list (empty == go), the CLI exit code (0 pass /
  1 fail). The closed check set (amended 2026-10-06, the
  rehearsal): the DLL pointer stages FIRST (before any engine
  import — find #5) · engine modules import · DLL reachable
  (either ruled route) · openai imports AND the client
  CONSTRUCTS with a dummy key (zero network; never guess
  transport names — the httpx2 find) · key offered (presence
  only, never printed) · >=1 *.sql · >=1 *.SemanticModel ·
  the three dictionary files · out dir writable.

- THE DELIVERY BUCKET (ruled 2026-10-06, her ask: one
  catch-all for everything a new customer needs):
  AIVIA_01_Delivery/ — README_prereqs.md ·
  work_wheel_runbook.md (generalized; moved from the
  production folder) · dictionary_extraction/ (4 shape-matched
  UNSCOPED queries + the ZC value generator; SELECT aliases
  ARE the engine's json keys — test-locked) · tools/
  csv_to_json.py (zero-logic converter; SOURCE in
  AIVIA_01_Code, packed copy byte-identical — test-locked) ·
  wheel/ (exactly ONE wheel, packed). The bucket obeys the
  wheel's hygiene laws (no brand string, no census canary, no
  keys — test-locked, test_10_delivery_folder.py) and the
  wall: one direction, nothing customer-made returns.

Definitions:
- THE REFUSAL (D8, amended 2026-10-08): deliver() runs the
  preflight first; ANY failure raises with the full board —
  including the missing key (the exception retired with D4;
  effective wheel 0.7.0) — no paid call into a broken
  environment, a test not advice.
- THE ONE-WHEEL LAW (D9) and THE VERSION LADDER (D10) govern
  every environment this artifact enters.

THE STEP TABLE — the naming law (RULED 2026-10-08, Sunny):
One number, one meaning: a number names a step; the same
number appears on its runbook heading, the folder/file it
fills, and the design doc that defines it. Nothing is
unnumbered. Engine-made files end `_output`; a step with
several outputs names each `<step>_<content>_output`.
Uploaded inputs keep their real object names (no suffix).
Folder renames (03_tmdl, 04_run) are effective NOW (paths are
run-cell parameters); output FILE renames and the behavior
rulings below land together in WHEEL 0.7.0 (queued; the old
names stand in code until then).

| # | Step | Who runs it | Fills / writes | Output file(s) |
|---|------|-------------|----------------|----------------|
| 01 | sql_input | Sunny (upload) | Files/01_sql_input/ | the *.sql files (inputs, real object names) |
| 02 | dictionary | Sunny (SSMS + convert cell) | Files/02_dictionary/ | 02_dictionary_table_output.json · 02_dictionary_column_output.json · 02_dictionary_join_output.json · 02_dictionary_value_output.json |
| 03 | tmdl | Sunny (pull cell) | Files/03_tmdl/ | the *.SemanticModel folders (inputs, real model names) |
| 04 | run | the engine | Files/04_run/ (was out/) | the container for steps 05–12; delete it = clean slate, inputs untouched |
| 05 | semantic_graph | build cell (free, whole corpus) | 04_run/05_semantic_graph/ | 05_semantic_graph_<sheet>_output.json (one per sheet) |
| 06 | technical_descriptions | build cell | 04_run/ | 06_technical_descriptions_output.json |
| 07 | business_descriptions | describe cell (paid, batch) | 04_run/07_business_descriptions/ | 07_business_descriptions_output.json · 07_business_descriptions_blessings_output.json |
| 08 | pbi_lineage | build cell | 04_run/ | 08_pbi_lineage_output.json |
| 09 | business_terms | describe cell (paid, same batch) | — | no file of its own: terms are rows inside 07 and 12 (by design, not an orphan) |
| 10 | corpus_ledger | describe cell (bookkeeping) | 04_run/ | 10_corpus_ledger_output.json |
| 11 | construct_census | sweep cell (free) | 04_run/ | 11_construct_census_output.json |
| 12 | ai_delivery | describe cell (assembled last) | 04_run/ | 12_ai_delivery_output.json · 12_ai_delivery_output.txt (human twin) |
| 13 | build_stamp | build cell (bookkeeping) | 04_run/ | 13_build_stamp_output.json — hash of 01_sql_input at build time (ruled 2026-10-08) |

THE 2026-10-08 RULINGS (land in WHEEL 0.7.0, one build):
- THE SPLIT: the free whole-corpus work (05 + 06 + 08) moves
  to its own BUILD cell; the paid batch (07 + 09 + 10 + 12)
  stays in the DESCRIBE cell. deliver() survives as the
  one-call wrapper (build then describe; her ruling). The
  build cell stamps a content hash of 01_sql_input into
  13_build_stamp_output.json; the describe cell recomputes
  it FIRST and refuses on mismatch ("run the build cell
  first") — no paid call against a stale graph.
- DELIVERY = DELIVERED GOODS ONLY: 12_ai_delivery carries
  only files that had their paid turn (they are in the 10
  ledger). A gate-failed ledger file appears with technical
  voice + its failure status (processed, honest). Waiting
  files do NOT appear — the whole-corpus technical view lives
  in 06, not in the delivery. A PBI report appears as soon as
  ANY of its files is described, marked incomplete until all
  are (her ruling: Collibra publish waits for completion —
  her hand, her timing).
- THE KEY IS A BLOCKING CHECK: cells run in sequence; a
  failed prereq (key included) stops the sequence — fix,
  then proceed. The degrade path dies.

Who writes what (authorship)?
- The artifact: machine-built by build_sqldesc_wheel.py,
  whole-wheel, re-runnable; refused on any allowlist drift.
- The locks (AIVIA_01_Test/test_packaging_wheel.py — manifest
  equality, secret shapes + literal-key, census canary,
  no-aivia, version+dependency, preflight board, the refusal,
  deliver degrade, dict/business/official-txt behaviors):
  NEVER travel (D3); they prove the code at home, the
  preflight proves the environment at run.
- This contract and the design doc: Sunny owns; amendments
  follow the amendments-first law.
