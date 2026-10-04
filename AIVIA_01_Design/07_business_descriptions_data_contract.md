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
  DOCKET v2 (REWRITTEN 2026-10-04, superseding the 10-03 docket
  amendment; the EMH OVERFLOW find is the evidence): the FILE
  grain's docket is TWO PARTS. FACTS — assembled only by the 05
  resolver: sources + dictionary words, each population
  condition with its bound meaning, attachments, parameters,
  outputs; THE GATE'S V-1 REFERENCE IS FACTS ALONE. CONTEXT —
  the raw SQL + dictionary prose, interpretation fuel only,
  grounds nothing. Scope/field dockets keep the 10-03 shape
  (their 06 sentence + Sources lines) until a later slice.
  THE FACT-VOICE LAYER (ruled same day): each machine fact gains
  a stored plain-English voice — one scoped LLM call per NEW
  fact, gated (the voice's values must be the fact's own;
  never-list; no SQL words; no @tokens), persisted in
  07_fact_voices.json keyed by node_id + fact-text hash
  (delta-by-name: changed fact re-proposes, unchanged never
  re-pays), blessable per fact in the registry. Voice ladder:
  blessed > gated proposed > the machine fact. --no-llm builds
  skip voicing and stay deterministic.
- THE 03 NAMING ASSET (03_chat_abstract_names.json) — read
  only; the name ladder's source (Design_Proprietary_Term_
  Assets.md THE NAMING LAW, 2026-10-04): sunny_*/blessed >
  first synonym > R5 words. FACTS/voices/cards consume it; no
  07 naming store exists.
- The importable 06 renderers (technical_descriptions.py) — the
  field grain's defining phrases (design ruling 4 / G2a); 06 is
  never reopened by this phase.
- THE BLESSING REGISTRY (07_blessing_registry.json) — Sunny's
  hand only (schema below); machines read it, never write rows.
- The LLM seat: gpt-5.4 (Sunny 2026-10-03: 'don't use mini, use
  the large one'); the production seat re-decides at the move on
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
    shape; file grain = the FIVE-line card, One row is: leading (2026-10-03)).
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
- 07_fact_voices.json (DOCKET v2, 2026-10-04) — machine-written
  PROPOSED voices only: {fact_key (node_id + fact hash),
  machine_fact, voice, status: proposed, model, basis_version}.
  Blessing a voice is HER registry row (fact_key in sentences);
  the build reads blessed first. Reuse law: unchanged fact_key
  never re-proposes.
- <file_name>.facts.txt — the TRACKED per-file FACTS artifact
  (machine fact + effective voice side by side): the proposer's
  grounding half, the gate's V-1 reference, and her audit
  surface — three readers, one artifact, regenerated every
  build.

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

THE GATE v2 (contract law, REWRITTEN WHOLE 2026-10-03 per the
debug01/debug02 rulings; no model anywhere in it; the lexical
whitelist is RETIRED — see the design doc's Gate v2 section):
  THE ESTATE BOUNDARY: customer-specific facts (names, codes,
  values, filters, formats of this estate) must trace to the
  docket; general domain knowledge is FREE — the gate polices
  the truth boundary and the register, never interpretation.
  V-1 GROUNDED VALUES (SCOPED 2026-10-04): every quoted value
      and every number in audience_text must appear in the
      docket's FACTS part — CONTEXT grounds nothing; an
      ungrounded number fails AND lands a code sighting (S10
      narrowed: grounded numbers may speak).
  V-2 THE NEVER-LIST: format/purpose claim words (separator,
      delimiter, comma, semicolon, formatted, supports,
      enables, helps, intended, purpose) — the lie taxonomy;
      grows only by Sunny's ruling.
  V-3 REGISTER: no SQL vocabulary (join, select, query, table,
      temp, column, procedure, parameter), no @tokens.
  V-4 TEMPLATE: file grain = exactly the FIVE labeled lines
      (One row is / Who's in it / Each row shows / Time window
      / Excludes). FIELD arm (2026-10-04): one short plain
      paragraph — no markdown, no labels, no line breaks.
      LINE-OWNERSHIP arm (2026-10-04): the Who's-in-it line
      carries no negative language ("other than", "excluded",
      "not ...") — negatives live only in Excludes.
  V-5 THE KINDS BACKSTOP: the Each-row-shows line over ~10
      segments (parentheticals stripped) fails with the named
      objection — the complete field list already lives in the
      technical appendix.
  V-6 MUST-SAY (exactly three): the gap echo (dynamic-SQL
      files), the window (population-shaping parameters), the
      Excludes line (existing exclusions).
  V-7 ATTACHMENT ANCHOR: restriction speech requires a
      membership row to anchor it.
  No word budgets (retired). A proposal passes only when every
  check passes. Repair budget 3; then the floor stands,
  findings and last_proposal kept.

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
