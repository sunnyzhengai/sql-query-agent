06_technical_descriptions_data_contract

Status: APPROVED 2026-10-02 (Sunny, in chat: "go"), same day as the
draft. Scribed by Claude from the eight ruled design decisions
(06_technical_descriptions.md, all RULED 2026-10-02). Per the standing
amendment law (contract-amendments-first, ruled today): this
contract is complete and stamped BEFORE the first red test of any
06 build step.

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- The eleven phase 05 sheets (AIVIA_01_Data/05_semantic_graph/) —
  read only, never written by this phase. The graph is the ONLY
  source of sentence content: every word traces to a stored row.
- The 05 kind library (05_kind_library.json) — the closed
  vocabularies, INCLUDING the two voicing sheets ported at L02
  (below). Authorship law unchanged from the 05 contract: grows by
  Sunny's hand only, one ruled row at a time, dated.
- The phase 02 dictionary sheets — read only; names as stored and
  VALUE MEANINGS (design decision 3a: a bound literal speaks its
  dictionary meaning; an unbound literal stays a bare code).
- The 8 corpus SQL files (AIVIA_01_Data/01_subject_sql_files/) —
  read only, for ONE purpose: R8 annotations (a trailing same-line
  SQL comment rides its predicate's sentence; the 05 evidence
  stores line/column, the comment text is read from the file at
  that line). No other sentence content may come from raw SQL.
- ZERO LLM CALLS (the two-machines ruling, 00_Architecture.md):
  phase 06 is fully deterministic — ScriptDom-derived sheets +
  plain Python. No API cost of any kind.

Where are these data files located for local development?
- /Users/sunnyzheng/sql-query-agent/AIVIA_01_Data/06_technical_descriptions/

Where are these data files located for production?
- Fabric lakehouse, AIVIA_01_LH/Files/Data/06_technical_descriptions/
  (plain file sync at the move phase — decision 8's law: the
  artifacts move, never the renderer).

L02 — THE VOICING PORT (design decision 4):
- Statement_Voicings (4 rows) and Function_Voicings (19 rows, with
  estate counts) port ONCE from the prior estate's
  kg2_kind_library into 05_kind_library.json at Sunny's word;
  Sunny ratifies; thereafter her hand only.
- The closed-list law: a statement kind or function met in
  rendering with NO voicing row and NO ruled-silent row is NEVER
  invented — it becomes a counted row in the voicing ledger
  (class unvoiced_statement_kind / unvoiced_function), visible,
  awaiting her ruling: give words or rule silent.

What is the output of this data contract?


THE RENAME AMENDMENT (2026-10-08, the naming law — step table in
10_work_wheel_data_contract.md; approved + built same day):
- 06_description_sheet.json -> 06_technical_descriptions_output.json
- 06_voicing_ledger.json    -> 06_technical_descriptions_voicing_output.json
Older passages below citing the pre-rename names read as the new
names. The per-file <name>.txt / <name>.svg KEEP their subject names (ruled: the step identity rides the folder; suffixing per-file artifacts adds noise, not truth).

- 06_description_sheet.json — one row per VOICED node:
  - node_id: the 05 node the sentence describes (join key into
    the graph; the sheet never mints its own nodes).
  - grain: predicate | condition | scope | statement | file
    (closed set, design decision 2):
      predicate — every predicate leaf (05_predicate_sheet).
      condition — every WHERE / HAVING / ON condition tree
        (the owning clause structure node).
      scope — every scope (the central sentence: lead → joins →
        filters → kept-rule → payload).
      statement — every handled statement with a ruled voicing.
      file — every file; its sentence is R13's three-level
        technical definition (HEADLINE / PIPELINE / APPENDIX),
        the gap sentence included when the file carries a
        dynamic_sql gap (decision 3e).
        GAP-SENTENCE AMENDMENT (2026-10-03, at L06 scribing, for
        Sunny's stamp with the L06 pseudo): 05 stores no
        expression trees for SET assembly statements (handled,
        scope-less — measured on the Census Days file), so the
        gap sentence CANNOT name the parameters fed into the
        string from stored rows. Amended shape: the gap sentence
        speaks the gap statement's stored evidence fragment and
        the counted gap arithmetic ("it is executed by
        \"EXEC (@SQL)\"; k of n statements are in this gap").
        Naming the fed parameters is a NAMED FUTURE CLASS,
        contingent on a 05 SET-capture amendment (same family as
        the queued OVER amendment) — never a raw-SQL read here.
  - sentence: the stored text, byte-exact, rendered only from
    stored rows (decisions 1 and 3 name the grammar: R4-R8,
    R10-R13 ported; value meanings; on_class obeyed —
    lookup_shaping voices as attachment, never filter; member
    lineage — member chains spoken, star_member dual origins BOTH
    voiced, behind_star speaks the scope only; parameter defaults
    quoted VERBATIM; SUPP:: metadata speaks normally).
  - basis_version: the 06 grammar constant (a version string in
    the code, bumped on any wording law change) — stale sentences
    are findable by version.
  - evidence_refs: the 05 node_ids the sentence was built from
    (list; every claim traceable to its rows).

- 06_voicing_ledger.json — THE CONSERVATION LEDGER (decision 5):
  one row per COUNTED node (voiced nodes ARE the description
  sheet rows — disjoint by construction):
  - node_id, grain, class, basis_version.
  - The closed counted classes (seeded; growth = a ruled row):
      operational_statement (SET / DROP / DECLARE mechanics),
      dynamic_sql_gap (the EXEC-of-string statement),
      lookup_shaping_attachment (voiced as attachment in the
        scope sentence but counted APART from membership — never
        inflates "what decides who is in"),
      degenerate_never_voiced (R6 mechanics),
      unvoiced_statement_kind, unvoiced_function (the L02
        closed-list misses, awaiting ruling),
      column_words_gap (AMENDED 2026-10-02 at L03 scribing, with
        the pseudo code, per R5: a column with no dictionary
        description voices as the readable form of its name AND
        is counted — never silent),
      annotation_disagreement (AMENDED 2026-10-02 at L03
        scribing; PRECEDENCE FLIPPED 2026-10-08, her ruling
        "use the inline comment as the first choice": the
        COMMENT is voiced first, a disagreeing declared meaning
        is counted here — still a steward's finding, read the
        other way. The comment is READ from the SQL at build
        time and stored NOWHERE else — no side dictionary, ever
        (her ruling; high-occurrence numbers may earn one
        later, a recorded future option). Effective at the
        0.8.0 build.)
  - THE EQUATION, a test not advice: per grain and per file,
    description rows + ledger rows == the grain's node total in
    the 05 sheets. A node in neither place has no constructible
    path; a red ledger does not ship.

- 06_technical_descriptions/<file_name>.txt — the eyeball texts
  (decision 6): one per corpus file, reading order (scope
  sentences, statement steps, the file floor with the three-level
  definition) — TRACKED build output, regenerated every build;
  the descriptions-in-the-loop law applies (announce top changed
  sentences).

- 06_technical_descriptions/<file_name>.svg — the visuals
  (decision 8): one DETERMINISTIC SVG per corpus file from the 05
  sheets — statements down the spine, scopes as boxes, structures
  and predicates nested, resolves edges across (member chains,
  star_member fans with both arms, value binds, the dynamic-SQL
  gap marked). Plain Python, no libraries, fixed ordering, no
  randomness — byte-stable, pinnable. A node with no sheet row
  cannot appear.

What are the tests?
- AIVIA_01_Test/test_06_technical_descriptions_data_contract.py —
  Claude's suite: byte-exact pinned sentence strings (decision 7)
  on fabricated estates (one rule isolated per test) and on chosen
  real corpus sentences; the conservation equation per grain and
  per file; the closed-set checks (grains, counted classes); SVG
  determinism (two builds, identical bytes).
- AIVIA_01_Test/test_06_technical_descriptions_data_contract_sunny.md
  — Sunny's hand-written cases; Claude adds the run command after
  build. Her eye on the texts and SVGs is the acceptance (the
  standing ED-sepsis law).
- Red first, always. The build command (fixed at L03):
  /opt/homebrew/bin/python3.11 AIVIA_01_Code/technical_descriptions.py
      AIVIA_01_Data/05_semantic_graph
      AIVIA_01_Data/06_technical_descriptions
      AIVIA_01_Data/02_emr_data_dictionary
      AIVIA_01_Data/01_subject_sql_files

Who writes what (authorship)?
- All 06_* outputs: machine-written by the committed build, every
  run, whole-file. No hand edits, no sunny_* fields in this phase
  (wording rulings land in the kind library's voicing sheets or
  the grammar constant's code, never in output files).
- 05_kind_library.json: Sunny only (the L02 port is Claude's one
  write at her word; her ratification seals it).
- This contract: Sunny owns; amendments follow the
  contract-amendments-first law — every touched passage rewritten
  and agreed before any red test.
