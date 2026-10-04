07_business_descriptions_data_contract

Status: APPROVED 2026-10-03 (Sunny's "go" ratified the design's
seven rulings and this contract rides them; scribed by Claude
same day). Per the contract-amendments-first law: complete
BEFORE the first red test; any reopen rewrites every touched
passage before new red.

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- The Phase I estate, read only: the 06 description sheet +
  voicing ledger (the docket's floor and the boundary of the
  known), the eleven 05 sheets (structural anchors: on_class,
  resolves, parameters), the 02 sheets (words, value meanings,
  table descriptions), the 05 kind library.
- The importable 06 renderers (technical_descriptions.py) — the
  field grain's defining phrases (design ruling 4 / G2a); 06 is
  never reopened by this phase.
- THE BLESSING REGISTRY (07_blessing_registry.json) — Sunny's
  hand only (schema below); machines read it, never write rows.
- The LLM seat: local dev gpt-5-mini; production gpt-5.4-mini on
  the aivia Azure endpoint (parity law at the move). PAID CALLS
  ONLY at build/run time; Claude's test suite is DETERMINISTIC —
  recorded real outputs (the dry run's 14 calls, provenance in
  dryruns/phase_II_uses_phase_I.md) replay as fixtures.

Where do these data files live?
- Local: /Users/sunnyzheng/sql-query-agent/AIVIA_01_Data/07_business_descriptions/
- Production: AIVIA_01_LH/Files/Data/07_business_descriptions/
  (plain file sync at the move phase; the renderer never moves).

What is the output of this data contract?

- 07_business_sheet.json — one row per described node:
  - node_id (the Phase I node), grain: file | scope | field
    (term grain deferred to the glossary milestone).
  - audience_text: the business description (S1-S11 govern its
    shape; file grain = the S7 four-line micro-template).
  - status: proposed | gate_passed | blessed | floor — the
    EFFECTIVE text ladder is blessed > gate_passed > floor; a
    floor row's audience_text IS the 06 sentence, verbatim.
  - gate_findings: the named objections (empty when clean);
    after the repair budget (3 rounds) the LAST findings stay
    on the row for Sunny's eye.
  - last_proposal (AMENDED 2026-10-03, Sunny's word): on floor
    rows, the final REJECTED card text — so she can see what
    the model wanted to say and spot which words to bless.
  - rounds_used, model, proposed_at: the call provenance.
  - basis_version: the 07 grammar constant; docket_refs: the
    Phase I rows the docket carried.
- 07_blessing_registry.json — SUNNY'S HAND ONLY:
  - names: [{node_id or term key, blessed_name, dated ruling}]
  - sentences: [{node_id, blessed_text, dated ruling}]
  - delta-by-name (the 03 reuse law); machine writes are a
    contract violation; the build READS it first in the
    effective ladder. Seed candidates staged from 03
    sunny_synonyms at L02, ratified by her before first use.
- 07_business_descriptions/<file_name>.txt — the per-file
  business text, TRACKED build output: the file's S7 template +
  per-scope and per-field lines with status marks; the
  descriptions-in-the-loop law applies.
- unbound-code sightings (S10) append to the standing
  dictionary-growth queue record: 07_code_sightings.json —
  table.column + code + the reading node; Sunny's 02 value
  growth consumes it.

THE LIVE-RUN HARNESS LAWS (AMENDED 2026-10-03, the first-failure
build per the Echo Law — the first live run hung 2h22m on a
wedged socket with zero CPU, nothing written, no progress):
- TIMEOUT: every API call carries an explicit timeout (120s) and
  bounded retries; a wedged socket can never hang the build.
- CHECKPOINT-PER-NODE (the 03 checkpoint-per-batch law carried):
  07_live_checkpoint.json is rewritten after EVERY node; a rerun
  RESUMES — completed nodes are never re-proposed, never
  re-paid. The checkpoint is transient: deleted when the sheet
  lands whole.
- PROGRESS: one line per node ([k/N] node -> status, rounds) so
  a live run is watchable.
- TEST POSTURE: the harness plumbing (checkpoint, resume, order,
  progress) is tested with a clearly-labeled deterministic
  stand-in proposer — plumbing tests, never fake LLM output
  presented as speech; the paid path stays build-only.

THE GATE (contract law, ruled; no model anywhere in it):
  G-1 LEXICAL WHITELIST: every content token in audience_text
      must trace to the docket (06 sentences + 05 rows + 02
      words + blessed vocabulary) or the plain-word closed list
      (function words); fail names the token.
  G-2 BANNED VOCABULARY (S2): join, select, query, table, temp,
      column, procedure, parameter, @tokens, raw codes.
  G-3 BUDGETS (S8): sentence count and per-sentence word caps
      by grain; one parenthetical max; no nesting.
  G-4 TEMPLATE (S7): file grain = exactly the four labeled
      lines.
  G-5 MEMBERSHIP/ATTACHMENT ANCHORS (S4): restriction claims
      anchor to Population/WHERE rows; attachment speech
      anchors to on_class attachment rows; cross-speaking
      fails.
  G-6 MUST-SAY (exactly three): the gap sentence's business
      echo for dynamic-SQL files; the window when parameters
      shape the population; the Excludes line when exclusions
      exist.
  G-7 S10: no unbound code appears; the sighting is RECORDED.
  A proposal passes only when every check passes. Repair budget
  3; then the floor stands, findings kept.

What are the tests?
- AIVIA_01_Test/test_07_business_descriptions_data_contract.py —
  Claude's suite, DETERMINISTIC end to end: the docket builder,
  every gate check (fixtures include the dry run's recorded
  REAL failures — the semicolon fabrication is a pinned
  regression forever), the prompt constructor (byte-exact), the
  effective ladder, the sheet and text shapes, registry
  read-only enforcement, S10 sighting capture.
- AIVIA_01_Test/test_07_business_descriptions_data_contract_sunny.md
  — her cases; Claude maintains the commands.
- The LIVE path (paid calls) runs in the build command only:
  /opt/homebrew/bin/python3.11 AIVIA_01_Code/business_descriptions.py
      AIVIA_01_Data/05_semantic_graph
      AIVIA_01_Data/06_technical_descriptions
      AIVIA_01_Data/07_business_descriptions
      AIVIA_01_Data/02_emr_data_dictionary
  (a --no-llm flag renders floor-only rows deterministically —
  the sheet exists and conserves even with zero calls).
- CONSERVATION: every docket node gets exactly one sheet row;
  status floor is never silent absence — the equation is a
  test, as always.

Who writes what (authorship)?
- 07_business_sheet.json, the texts, 07_code_sightings.json:
  machine-written by the build, whole-file.
- 07_blessing_registry.json: Sunny only, one dated ruling at a
  time; the L02 seed is staged by Claude and EMPTY of force
  until her ratifying hand.
- This contract: Sunny owns; amendments follow the
  contract-amendments-first law.
