06_technical_descriptions.md

Status: DESIGN CLOSED 2026-10-02 — all EIGHT decisions RULED (Sunny,
in the chat session, each stamped same day; decision 8 THE VISUAL
added and ruled after the close, same day). Sunny owns this doc;
Claude scribes drafts at her direction — document-as-we-go.
Build queue: (0) the D3 star_member resolver amendment in 05 —
BUILT 2026-10-02 (see 05_semantic_graph.md L07 log) — then L01
onward. NOTE: this doc's decisions 1-8 are ITS OWN list; the
"decision 8" in the phase-split line below is the 2026-10-01
sequencing ruling, a different list.
Product phase: I — Describe (00_Architecture.md: the TECHNICAL
description is Phase I's output; the BUSINESS description is Phase
II's and is NOT built here).
Phase split: RULED 2026-10-01 — 06 = technical descriptions, built
BOTTOM-UP (decision 8: meaning climbs back up — predicate sentences
compose into condition phrases, scope sentences, statement phrases,
the file floor).
Prior art (Sunny's standing directive — consult before designing
each piece, never re-derive): AIVIA_01_Design/briefs/
Brief_05_Prior_Art.md §3 — Grammar_Floor.md v2.16.0 (rules R1-R16,
each with its ruling), aisql/flows/produce.py (the renderers + the
L28-123 changelog of every bug the grammar fixed), the byte-exact
spec tests (test_scope_sentence.py, test_statement_render.py), and
USP_ED_SEPSIS_descriptions.txt as the quality bar.

Design description (draft):
- Every semantic node of a ruled grain gets its DETERMINISTIC
  technical description — exact, parse-traceable, zero LLM calls
  (the two-machines ruling in 00_Architecture.md: the technical
  description is rendered MECHANICALLY; phase 06 consumes no paid
  calls at all).
- Input: the eleven phase 05 sheets + the kind library + the 02
  dictionary sheets (for names and value meanings). Output: a
  description sheet + a per-file descriptions text for Sunny's eye.

THE DECISIONS (to rule, in discussion order):

1. WHICH GRAMMAR RULES PORT — RULED 2026-10-02 (Sunny): Option A —
   the full deterministic floor ports INCLUDING R13; the two-machines
   boundary stays sharp (Phase II holds only the LLM tier). Claude's
   proposal as ruled:
   PORT NOW (the deterministic floor):
   - R4 predicate voicings: one voice per closed kind ("is
     recorded", "is between X and Y (inclusive)", "is one of N
     values", "matches <pattern>"), negation folded per kind.
   - R5 operand words (names spoken as stored; NO blessed-name tier
     — that is Phase II vocabulary).
   - R6 degenerates never voiced / R7 the honest no-conditions
     sentence.
   - R8 annotations: a trailing same-line SQL comment rides its
     predicate's sentence (the corpus's --department comments).
   - R11 statement step sentences (closed Statement_Voicings).
   - R12 computed output: the Function_Voicings library, voiced
     inside-out (DATEDIFF, ROW_NUMBER, CASE...).
   - R10 the file floor: deliveries lead, the spine walks back to
     base selections, intermediates counted, census closes.
   - R13 the three-level technical definition (HEADLINE / PIPELINE
     / APPENDIX) — the stored governance field.
   NOT HERE (Phase II): R14 business-term sentence, R15 voicing
   repairs, R16 business voice tier, blessed names, the LLM
   proposer/gate (business_voice.py pattern).

2. DESCRIPTION GRAINS + THE SHEET — RULED 2026-10-02 (Sunny):
   approved as proposed.
   06_description_sheet.json: one row per described node —
   node_id (the 05 node it describes), grain (predicate | condition
   | scope | statement | file), sentence (the stored text),
   basis_version (the 06 grammar constant), evidence_refs. Grains
   ruled: every predicate leaf; every WHERE/HAVING/ON condition
   tree; every scope (the central sentence: lead -> joins ->
   filters -> kept-rule -> payload); every handled statement; every
   file. Operational statements and remainder-free mechanics stay
   silent BY RULE (R6), never by omission.

3. WHAT OUR ESTATE ADDS BEYOND THE PRIOR FLOOR — RULED 2026-10-02
   (Sunny): approved as amended — (c) carries the D3 reopen
   (star_member chains spoken, both union arms voiced); (d) quotes
   the parameter default VERBATIM (translation to plain time words
   is Phase II's eloquence, not 06's); (e) the gap sentence names
   the parse-visible shapers (the parameters fed into the string,
   conditional splices) and claims NOTHING from inside the
   unparsed string text; a no-holes constant dynamic string is a
   NAMED FUTURE CLASS (zero in corpus today — new decision if one
   arrives, per the placeholder law):
   a. VALUE MEANINGS: a bound literal speaks its meaning,
      MEANING-FIRST AND QUOTED (RULED 2026-10-03, Sunny: "rule the
      quoted form" — the quotes mark where the meaning text starts
      and stops): "department is 'CCMC EMERGENCY' (100108022)" —
      from the 05 value binds; an unbound literal stays a bare
      code, honestly. Grammar constant bumped 06.1.0 -> 06.2.0.
      AUDIENCE LAW (ruled same day, with Flag B): 06's sentences
      are the TECHNICAL register — consumed by Sunny's gap-check,
      Phase II's business machine (as grounded input) and Phase
      III structurally; never surfaced raw to end users. End-user
      phrasing ("caregiver languages, if populated") is Phase II's
      eloquent half.
   b. on_class obeys D4: lookup_shaping conditions voice as
      attachment rules ("each patient carries their first-listed
      race"), NEVER as population filters; join_pair conditions
      voice inside the join phrase; population_filter joins the
      membership bullets.
   c. MEMBER LINEAGE: a column read through a temp/CTE speaks its
      origin when FINE-bound ("out_a — built in #census_monthly");
      star_member reads (D3 as REOPENED 2026-10-02: stars over
      scopes expand through stored outputs, one origin per union
      arm) speak the walked chain — both arms voiced when the
      origin is dual; behind_star reads (star over a base table,
      the only remaining blind class) speak the scope only,
      honestly.
   d. PARAMETER VOICING: a parameter's default_text is quoted
      verbatim in the file floor when the parameter shapes the
      population (the @StartDate 24-month window surfaces).
   e. THE GAP SENTENCE: a dynamic_sql file's floor says plainly
      "part of this file's logic is built as a string at run time
      and is not described here" — decision 9's voicing half.
   f. SUPPLEMENTAL HONESTY: descriptions over SUPP:: metadata speak
      normally (the metadata's own text already declares its
      provenance). STRIP LAW (RULED 2026-10-03, gap-check item 3):
      the R5 noun-phrase render strips a leading "Supplemental:"
      tag — provenance lives in the SUPP:: id, never in prose.

   GAP-CHECK RULINGS 2026-10-03 (Sunny: "ratify all five as
   recommended"):
   1. SEVEN Function_Voicings rows added by her word (MAX, COUNT,
      SUM, CONCAT, FORMAT, CHAR, ROW_NUMBER-interim); the OVER
      amendment to 05 queued as its own post-06 ruling.
   2. The 28 column_words_gap rows ACCEPTED as the standing
      dictionary-growth queue (readable names voiced, counted);
      02 supplemental authoring batched later, her hand.
   3. The Supplemental: strip law (above, 3f).
   4. The temporal word test grows to the closed list date | time
      | instant (grammar constant bump).
   5. The head-word reorder awkwardness ("... row unique")
      ACCEPTED — wording repairs are R15, Phase II, by ruling.
   BUILT same day: library 26 rows (6 added + ROW_NUMBER interim
   re-templated), 6 tests red then green (+ MIN/MAX bare-article
   guard — "the earliest the visit date" can never render),
   grammar constant 06.2.0 -> 06.3.0; 06 suite 45, full 238,
   ruff clean. CORPUS AFTER: unvoiced_function 29 -> 0; counted
   floor = 28 column_words_gap (the accepted dictionary-growth
   queue) + 7 degenerates + 1 disagreement, all by rule.

4. VOICING VOCABULARIES PORT — RULED 2026-10-02 (Sunny): approved
   — one-time port at L02 at her word, closed lists + counted
   misses re-affirmed as 06 law. Statement_Voicings (4) and
   Function_Voicings (19, with estate counts) port from
   kg2_kind_library to the 05 kind library at Sunny's word, same
   one-time-port-then-her-hand law as before. The red-build spirit:
   a statement kind or function met in rendering with no voicing
   row and no ruled-silent row = a COUNTED unvoiced row, visible
   (the prior estate's choice: statement_phrase returns None,
   never invents).

5. CONSERVATION — THE VOICING LEDGER — RULED 2026-10-02 (Sunny):
   stamped — the equation is a TEST (voiced + counted == total,
   disjoint), seeded counted classes as listed, a red ledger does
   not ship. (The prior estate's deepest
   law, ported): every membership decision is VOICED or COUNTED;
   voiced + counted == total, disjoint, queryable, a test not
   advice. Counted classes seeded from the prior estate:
   outer-join lookup_shaping (voiced as attachment, counted apart
   from membership), operational statements, unvoiced-function
   remainders.

6. THE EYEBALL ARTIFACT — RULED 2026-10-02 (Sunny): approved —
   tracked build output in AIVIA_01_Data/06_technical_descriptions/
   (machine-rendered, same posture as the 05 sheets), the
   descriptions-in-the-loop law applies. The build regenerates
   AIVIA_01_Data/06_technical_descriptions/<file_name>.txt per
   corpus file (scope + statement + file-floor blocks, the
   USP_ED_SEPSIS format modernized) — TRACKED output of the build,
   not an untracked operator loop file (the prior estate's
   regeneration lesson: the harness died with the operator). The
   standing descriptions-in-the-loop law applies: every
   stored-text-changing build regenerates them and announces the
   top changed sentences.

7. BYTE-EXACT TESTS — RULED 2026-10-02 (Sunny): approved — pinned
   exact strings, fabricated estates + chosen real corpus
   sentences, red first; Claude's suites prove the machine, her
   eye is the acceptance. The prior estate's spec-by-example posture:
   Claude's tests pin EXACT sentence strings for fabricated
   estates and for chosen real corpus sentences (red first, as
   always); Sunny's cases md gap-checks the real files' rendered
   descriptions — her eye is the acceptance, per the standing
   ED-sepsis law.

8. THE VISUAL — RULED 2026-10-02 (Sunny, scribed as proposed): the
   build renders one DETERMINISTIC SVG per corpus file from the 05
   sheets — statements down the spine, scopes as boxes, structures
   and predicates nested, resolves edges drawn across (member
   chains, star_member fans with both arms, value binds, the
   dynamic-SQL gap marked visibly). LOCAL is the ruling: rendered
   by the committed build in plain Python (no libraries, no
   randomness — fixed ordering, byte-stable layout, pinnable like
   the sentences), TRACKED beside the description texts in
   AIVIA_01_Data/06_technical_descriptions/<file_name>.svg,
   regenerated every build (the 03 SVG map is the in-house prior
   art; the prior estate's untracked-harness lesson applies).
   Honesty law carries over: a node with no sheet row cannot
   appear; silence in the picture is the same counted silence as
   in the texts. FABRIC: deferred to the move phase as a plain
   file sync — the artifact moves, never the renderer (local
   stays truth; Fabric serves copies; no capacity-rendered,
   untestable visuals). Home in the ladder: L07, beside the
   texts — one gap-check moment, sentence and shape side by side.

Local build steps (draft, bottom-up per the 2026-10-01 phase-split
sequencing ruling — not this doc's decision 8):
    L01: data contract 06_technical_descriptions_data_contract.md.
         DRAFT SCRIBED 2026-10-02 (all eight decisions in contract
         form; file sheet fields, ledger classes, test posture,
         build command, authorship). AWAITING Sunny's ratification
         — no red test before her stamp (the amendment law).
    L02: port Statement_Voicings + Function_Voicings to the kind
         library (Sunny ratifies).
         PORTED 2026-10-02 at her word: rows verbatim from
         kg2_kind_library (4 + 19, _ruling rows included), library
         status carries the port line, 05 suite stayed green (52).
         AWAITING her ratification of the two sheets. Known
         corpus misses that will land as counted unvoiced_function
         rows at L06, by design: FORMAT, TRY_CONVERT, IIF, CONCAT
         (STRING_AGG is voiced).
    L03: predicate voicing — R4 kinds + negation + R8 annotations +
         value meanings (3a). Byte-exact tests red first.
         BUILT 2026-10-02: contract amended FIRST (two counted
         classes: column_words_gap, annotation_disagreement);
         pseudo approved (3a MEANING-FIRST confirmed: "Lucky (7)"
         supersedes the prior code-first form, uniformly); 15
         tests red then green + 1 added same session (the R5
         raw-token catch: column-vs-column comparands now speak
         words — "is the bed contact of the bed record serial",
         never "is bd.BED_CSN_ID"); ruff clean. CORPUS: 204
         sentences (211 preds - 7 degenerates), counted: 7
         degenerate_never_voiced + 3 annotation_disagreement
         (REAL steward finds: two department codes annotated with
         pre-repair names '1 Emergency'/'2 Emergency', one
         language-exclusion note vs Not English (22)).
         FOR SUNNY'S EYE (gap-check material, non-blocking):
         - SUPP:: columns leak the "Supplemental:" prefix into
           subject words ("The Supplemental: Y when...") — her 02
           descriptions are notes, not noun phrases; her call:
           reword the 02 rows or rule a 06 strip law.
         - noun-phrase reorder awkwardness as ratified
           (awkward-but-grounded): "benefit plan associated with
           the dates effective for this row unique" (head(X)
           drops 'ID'); R15 repairs stay Phase II.
         - join-pair predicate rows voice as full sentences at
           this grain; 3b moves them INTO join phrases at L05.
    L04: condition composition — boolean trees to prose (AND/OR/
         NOT), on_class routing (3b), the honest no-conditions.
         BUILT 2026-10-03: flags A+B RULED (A: all-degenerate tree
         = no row + counted, grain condition; B: ON trees voice
         neutral at this grain, routing exposed as partitioned
         phrases to L05 — with the AUDIENCE LAW: 06 = technical
         register, never raw to end users). QUOTED VALUE FORM
         ruled same day (3a amended, "'Lucky' (7)"), grammar
         constant 06.1.0 -> 06.2.0, 10 sentences re-pinned.
         8 tests red then green (24 total in the 06 suite); suite
         217; ruff clean. One field fix: contains positions like
         'sub1' (subquery edges) sort after numerics.
         CORPUS: 95 condition rows (24 WHERE + 71 JOIN trees);
         parts: 60 join_pair / 8 lookup_shaping / 4
         population_filter. The 2 CASE-expression predicates
         (PROJECTION expr trees) voice at the predicate grain and
         render with R12 computed outputs, not as clause trees —
         by structure, not omission.
         FOR SUNNY'S EYE (new, non-blocking):
         - temporal word-test miss: "the instant when the event
           was supposed to have happened is AT LEAST @StartDate"
           — the ruled test is the words date/time only; her
           call: add "instant" (a ruled word-list row) or accept.
         - ON self-identity reads odd at this grain ("The patient
           contact record unique is the patient contact record
           unique.") — honest; L05's matched-on phrasing is the
           readable home.
    L05: scope sentences — lead, join phrases, membership bullets,
         kept-rule, payload; member/behind_star phrasing (3c).
         BUILT 2026-10-03: flags C+D RULED (C: no grain metadata
         in our dictionary, the lead names sources as stored —
         "This is a selection from T1"; D: 05 does not capture
         OVER contents, so ROW_NUMBER/LAG/LEAD voice as the
         counted remainder — a measured 05 gap, future amendment
         candidate). 15 tests red then green + 1 added on a
         corpus find (below); 06 suite 40; full 233; ruff clean.
         R12 live: renderers for ALL 19 Function_Voicings rows
         (coverage-tested code == library), composites by rule
         (case derived-by-rule, cast transparent, unary sign
         fold, arithmetic words). 3b live in the sentence:
         preserved joins ATTACH ("attaching ZC_CAT (matched
         where ...; attachment rule: ...)"), inner joins join,
         population_filter ON leaves land in membership. 3c
         live: member chains ("out a (built in #t, from T1.ID)"),
         star_member duals ("read through #u, origins #a.NAME
         and #b.NAME"), behind_star honestly blind.
         FIELD FIX (JOIN pairing): joined sources live under
         FROM in declaration order — the k-th JOIN structure
         pairs with the (k+1)-th FROM source.
         CORPUS: 36 scope rows; counted: 29 unvoiced_function
         (MAX 8, CONCAT 6, COUNT 6, CHAR 4, ROW_NUMBER 2, SUM 2,
         FORMAT 1 — awaiting Sunny's words or ruled-silent) + 28
         column_words_gap + 7 degenerates + 1 disagreement.
         CORPUS FIND (fixed same session, test-locked): 02
         descriptions holding the literal string 'NULL'
         (ZC_PAT_SERVICE.HOSP_SERV_C) voiced as "the NULL" —
         now a words-gap by rule; the 28 gap rows are a REAL
         dictionary-quality census for Sunny's 02 estate.
    L06: statement phrases (R11) + the file floor (R10) + the gap
         sentence (3e) + parameter voicing (3d) + R13 three-level
         definition + THE VOICING LEDGER (decision 5).
         BUILT 2026-10-03: flags E+F RULED (E: the gap sentence
         speaks the gap statement's stored evidence fragment +
         counted arithmetic — the shaper list is a NAMED FUTURE
         CLASS on the 05 SET-capture amendment, contract amended
         same day; F: lookup_shaping_attachment rows are the
         apartness record, OUTSIDE the silence equation).
         7 tests red then green; 06 suite 52; full 245; ruff
         clean. render_statements (R11: builds/delivers/decision,
         CTE helpers prepared-first), render_files (three levels:
         Delivers-rewritten headline, Pipeline voiced lines,
         Presents/Population/Inner-joins appendix, verbatim
         parameter defaults, the amended gap sentence, the R10.3
         census close), render_all (one door, five grains, the
         ledger deduped by node+class; gap rows carry the READ's
         expression node so the queue counts every gap read).
         THE EQUATION IS A TEST on the real corpus: per file per
         grain, voiced + counted == total.
         CORPUS: rows 204 pred + 95 condition + 36 scope + 19
         statement + 8 file; ledger 36 operational + 28
         words-gap + 9 attachment-apart + 8 unvoiced SET
         (awaiting her words) + 7 degenerate + 3 disagreement +
         2 dynamic-gap. The Census Days floor says its gap
         plainly: 'it is executed by "EXEC (@SQL)". 1 of 6
         statements is in this gap.'
    L07: the per-file descriptions texts (decision 6) + the
         per-file SVGs (decision 8) + the description sheet lands;
         Sunny's gap-check pass — sentence and shape side by side.
         BUILT 2026-10-03: flag G (the text format: SELECTIONS /
         STEPS with silent steps loud in brackets / THE FILE)
         RULED with the pseudo. 6 tests red then green; 06 suite
         58; full 251; ruff clean. build06 + main live — the
         contract's build command works; FIRST TRACKED BUILD
         LANDED in AIVIA_01_Data/06_technical_descriptions/:
         06_description_sheet.json (362 rows), 06_voicing_ledger
         .json (93 rows), 8 texts, 8 SVGs (byte-stable, pinned).
         THE LADDER IS COMPLETE L01-L07. OPEN: Sunny's gap-check
         pass (the acceptance) + her cases in the sunny md (the
         commands are written there); the queued follow-ups: 05
         OVER amendment, 05 SET-capture amendment, the 8 SET
         statement words, the 28-column dictionary queue.
    Each step: pseudo code first, Sunny approves, tests red, then
    code — the standing process.
Data contract: TBD at L01, authored with the decisions.
