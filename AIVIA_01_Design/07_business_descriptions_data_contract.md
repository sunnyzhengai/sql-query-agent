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
  grounds nothing. SCOPE dockets keep the 10-03 shape (their
  06 sentence + Sources lines). FIELD dockets moved to v2 the
  same day (built, CI-locked): named defining phrase, lineage,
  owning scope's shaped filter lines — v2's inheritance is
  itself SUPERSEDED at the walk build (fields fly blind, brief
  Q6); this sentence said "keep the 10-03 shape until a later
  slice" until 2026-10-04 — the slice had landed without the
  contract learning; aligned in the Q6 sweep.
  (2026-10-04, later same day: THE ROOM LAW — brief Q5 —
  supersedes this flat docket AT THE GRAPH-WALK REOPEN'S
  BUILD: one call per graph node, each rung's room closed per
  the pinned table; this clause stands as written until then.)
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
  RULING only. THE RATIFY CLAUSE (AMENDED 2026-10-04, Sunny in
  chat: "i need this step to be automated. because i'll run the
  job on hundreds of report files"): the blessing DECISION stays
  hers alone — machines never originate a blessing — but the
  registry WRITE is machine-executed at her explicit ruling:
  bless() in business_walk.py is the ONE write door; it refuses
  any write without a nonempty ruling string carrying her name
  and date, records her ruling verbatim on the row, and applies
  delta-by-name (a newer dated ruling on the same node_id
  supersedes). An unruled write remains a contract violation,
  test-locked. (Before this amendment: her hand only, machines
  read-never-write — the manual flow died at corpus scale.)
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
- 07_blessing_registry.json — SUNNY'S RULING ONLY (writes via
  the bless() door per THE RATIFY CLAUSE above):
  - names: [{node_id or term key, blessed_name, dated ruling}]
  - sentences: [{node_id, blessed_text, dated ruling}]
  - delta-by-name (the 03 reuse law); an UNRULED machine write
    is a contract violation (the bless() door enforces); the
    build READS it first in the effective ladder. Seed candidates staged from 03
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
      (SUPERSEDED AT THE GRAPH-WALK REOPEN'S BUILD — brief
      Q7/Q8: grows to the RESOLVE-BACK CHECKER, both
      directions — specific claims (quoted values, proper
      nouns, numbers) resolve to the room, must-says appear;
      matching normalized-deterministic over short names,
      value-node names, parameter plain names, blessed names;
      LLM linker excluded by ruling; joins the gate as named
      findings, budget 3; pinned regressions stay. V-1 stands
      as written until that build.)
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
      SCOPE arm (RULED 2026-10-04, THE SCOPE MUST-SAYS, brief
      Q4; the check lands at the graph-walk reopen's build —
      the current free-form scope grain stands until then):
      ONE ROW IS always; KEEPS only where the scope owns
      membership conditions, honest silence otherwise; a scope
      speaks only its own WHERE; per-scope value conservation.
      CARD arm (RULED 2026-10-04, THE ROOM LAW + LINE
      SELECTORS, brief Q5; lands at the walk build — the
      one-call card stands until then): the five lines keep
      their names and order as the reader format, but each
      line is generated in ITS OWN call from a named selector
      over the file subgraph, with per-line conservation and
      per-line repair; code assembles the card. The flat
      FACTS+CONTEXT docket is superseded by per-node rooms at
      that build (rider on the docket v2 clause).
  V-5 THE KINDS BACKSTOP: the Each-row-shows line over ~10
      segments (parentheticals stripped) fails with the named
      objection — the complete field list already lives in the
      technical appendix.
  V-6 MUST-SAY (exactly three): the gap echo (dynamic-SQL
      files), the window (population-shaping parameters), the
      Excludes line (existing exclusions). (2026-10-04: the
      must-survive law's value-conservation check supersedes
      V-6's presence-checks AT THE WALK REOPEN'S BUILD —
      presence grows to per-value accounting, both directions;
      V-6 stands as written until that build.)
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
  VALUE-CONSERVATION rider (RULED 2026-10-04, THE MUST-SURVIVE
  LAW — brief Q3; lands as a check at the graph-walk reopen's
  build): every population-shaping value on the card traces to
  a predicate AND every population-shaping predicate value
  appears on the card, both directions; housekeeping arrives
  as one plain clause; plumbing values (markers, split
  functions, special values as mechanisms) never arrive.

Who writes what (authorship)?
- 07_business_sheet.json, the texts, 07_code_sightings.json:
  machine-written by the build, whole-file.
- 07_blessing_registry.json: Sunny only, one dated ruling at a
  time; the L02 seed is staged by Claude and EMPTY of force
  until her ratifying hand.
- This contract: Sunny owns; amendments follow the
  contract-amendments-first law.

====================================================================
THE WALK CONTRACT (REWRITTEN 2026-10-04 — the graph-walk reopen,
brief Q1–Q9 all ruled in one sitting; drafted and STAMPED by Sunny
the same day). At the reopen's build this section REPLACES every clause
above that carries a superseded-at-the-walk-build rider (the
docket clause, V-1, V-6's presence form, the field-docket-v2
inheritance, the name-ladder rung-3 speech). Until that build, the
clauses above remain the enforced law of the running pipeline.
====================================================================

A. INPUT — THE ROOMS (replaces the flat FACTS+CONTEXT docket).
   Code walks the 05 graph bottom-up through ONE read surface
   (the read_api precedent; only the read surface touches the
   store — structural lock). One LLM call per node. Each rung's
   room, closed:
   - PREDICATE: speakable = its columns' ladder names + its
     bound values spoken by their value-node names; context-only
     = the dictionary descriptions (verbatim, never voiced);
     absent = everything else.
   - STRUCTURE (WHERE/AND/OR/JOIN/GROUP): speakable = its child
     predicates' and child structures' FINISHED sentences;
     nothing else exists. ON-clause structures are class-3:
     voiced locally, die at the rung.
   - SCOPE: speakable = its own structures' finished sentences +
     its grain + its payload kinds; absent = any other scope's
     conditions.
   - FILE CARD LINE (five rooms): speakable = its NAMED
     SELECTOR's results over the file subgraph (D below);
     absent = raw predicates, raw SQL, the other lines' facts.
   - FIELD: speakable = its column's ladder name + its
     expression; context-only = the dictionary description;
     absent = ALL population facts (the inheriting docket is
     retired here with its CI lock).
   Context-only material appearing in output = a named finding.

B. NAMES (the naming law + the Q2 riders, primary form).
   Every table and column speaks through the ladder: sunny_* /
   blessed > the 03 asset's short name. Rung 3 (description
   words) serves FLOOR rows only — it never speaks in LLM
   prose. COVERAGE duty: before the build's first live call, the
   naming pass covers every column and table the walk will
   speak; gaps stage for Sunny's eye, never fall through. The
   checker fails prose naming a thing any other way. One naming
   home stands (03 asset); no graph-node name property.

C. CONTENT LAWS (primary form).
   - WORDS FREE, FACTS CLOSED (Q1): world knowledge may decode,
     phrase, and explain in general terms what a room element
     IS; every specific value, name, and number must be a room
     element. No example values from the model's memory, even
     industry-true. Loosening, if her eye ever wants it, goes
     ONE notch: examples where the 02 dictionary stores the
     values as graph elements — never further.
   - THE MUST-SURVIVE CLASSES (Q3), assigned mechanically from
     the tree position: class 1 population-shaping — values
     intact every rung to its owning card line; class 2
     housekeeping — one plain clause, values not carried;
     class 3 plumbing — dies at its rung. Branch scope: the
     population path only; fields never carry class-1 facts.
   - SCOPE MUST-SAYS (Q4): ONE ROW IS always; KEEPS only where
     the scope owns membership conditions, voiced under the
     classes; honest silence where it owns none; EXISTS
     sub-conditions voice inline at the parent, no double
     counting; FEEDS stays rejected (one-home-per-fact).

D. GENERATION (Q5).
   Bottom-up, each node written from its room only. The file
   card is FIVE CALLS, one per line, each from its named
   selector: One row is <- delivery grain; Who's in it <-
   class-1 positives + run-time choice edges; Each row shows <-
   payload kinds; Time window <- class-1 temporal; Excludes <-
   class-1 negatives + class-2 clauses. Code assembles the
   card; a failed line repairs ALONE. The tone law rides every
   call; the graph decides content, the card decides
   presentation.

E. THE CHECKER (replaces V-1; Q7/Q8).
   Deterministic, both directions, per node: every SPECIFIC
   CLAIM — quoted value, proper noun, number — resolves to a
   room element; every must-say element appears; class-1 value
   conservation holds per scope and per card line. Matching:
   normalized deterministic (case fold, punctuation strip,
   simple plural fold) against FOUR lists — short names,
   value-node names, parameter plain names, blessed names. An
   LLM linker is EXCLUDED by ruling. Findings — room violation,
   conservation break, name violation — join the gate's
   objection-and-repair loop, budget 3. Ungrounded finds still
   land code sightings. The pinned CI regressions stay forever.
   Surviving unchanged from the old gate: the shape checks
   (five lines, the scope must-says' shape, SQL vocabulary +
   @token ban, the never-list), S10's grounded-numbers
   narrowing, the kinds backstop.

F. OUTPUTS (unchanged shapes).
   07_business_sheet.json rows, per-file texts, the facts
   files, sightings, and the blessing registry keep their
   shapes and authorship. Statuses and the effective ladder
   stand: blessed > gate_passed > floor. --no-llm renders
   floor-only, conserving, registry untouched.

G. TESTS OWED, RED FIRST (the locks the build must fail before
   its first green):
   1. seeded memory-invention in a sentence -> checker fails it
   2. seeded omission (7 of 8 departments) -> conservation fails
   3. paraphrased column name -> name violation
   4. filler KEEPS on a condition-less scope -> shape fails
   5. foreign condition in a scope's text -> ownership fails
   6. population fact in a field's room output -> room fails
   7. plumbing value (marker, split, special value) on the
      card -> class-3 climb fails
   Retirements at the same build: the inheriting field-docket
   lock; the S15–S18 prompt locks where the checker makes them
   mechanical (prompt text may keep the laws; the locks move).

H. ACCEPTANCE (unchanged from the brief): the census totals
   file is the proving file; the reopen is accepted when a full
   bottom-up regeneration reads clean to Sunny with no new leak
   classes AND the fabricated-proposal tests prove the checker
   — not her eye — catches every seeded invention.
