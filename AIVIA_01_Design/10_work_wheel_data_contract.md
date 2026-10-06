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
  - --dict: the three 02 extraction files (column/value/table)
  - the names asset beside the dictionary (03_chat_bot/) —
    optional; absence honest
  - OPENAI_API_KEY in the environment — optional; absence =
    the honest degrade (D4)
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

Definitions:
- THE REFUSAL (D8): deliver() runs the preflight first; any
  failure except the missing key raises with the full board —
  no paid call into a broken environment, a test not advice.
- THE ONE-WHEEL LAW (D9) and THE VERSION LADDER (D10) govern
  every environment this artifact enters.

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
