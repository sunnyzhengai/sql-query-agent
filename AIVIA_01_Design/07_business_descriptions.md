07_business_descriptions.md

Status: DESIGN RULED 2026-10-03 (Sunny: "go" — the ratification
section below carries all seven agenda rulings; the dry-run code
hold LIFTED the same word, round 5's outputs the accepted bar).
Sunny owns this doc; Claude scribes at her direction. Build
posture: pseudo first, her stamp, tests red first — the standing
process, unchanged.
Product phase: II — the ELOQUENT MACHINE (00_Architecture.md: the
business description; the second of the two machines).
Evidence: AIVIA_01_Design/dryruns/phase_II_uses_phase_I.md — the
executed dry run: 14 real gpt-5-mini calls, 5 rounds, convergence
at round 5 (3 of 3 grains gate-clean). Read it first.
Prior art (consult, never re-derive): Grammar_Floor R14/R15/R16 +
R5.b blessed names; aisql/flows/business_voice.py (proposer /
no-model gate / effective_sentence: blessed > gate-passed >
floor); Brief_Business_Voice (APPROVED 2026-09-20);
Brief_Description_Levels (the levels split).

Design description (draft):
- Phase II produces BUSINESS DESCRIPTIONS over Phase I's stored
  truth: an LLM PROPOSES, a NO-MODEL MECHANICAL GATE verifies
  every claim against stored rows, Sunny BLESSES. The floor (the
  06 technical sentence) ships whenever no blessed or gate-passed
  sentence exists — the system is allowed to be stiff, never
  allowed to lie.
- Audience: business users (report consumers, analysts,
  stewards) — THE layer that faces them (the 2026-10-03 audience
  law in 06: Phase I technical text never surfaces raw).
- Paid API calls only, per standing law. Dry-run cost evidence:
  convergence ≈ 3 rounds per grain at gpt-5-mini prices.

THE GOOD DESCRIPTION — RULED 2026-10-03 (Sunny, the debug01
sessions; supersedes where it conflicts with anything below):
A good report description answers FIVE questions, in order, as
five labeled lines:
  One row is:      what one row IS, in business meaning
  Who's in it:     the population — in and out, plainly
  Each row shows:  AT MOST 5 KINDS of information, never fields
  Time window:     the window + the as-of behavior, decoded
  Excludes:        the exclusions, named
Quality bars and their judges: TRUE (estate facts trace to
stored rows — the machine gate); PLAIN (natural complete
sentences, a human register — her eye); COMPLETE-FOR-PURPOSE
(the five questions; omission only by rule — must-say);
SCANNABLE (the template — the machine). The test of the whole:
a business user decides "is this the report I need, can I trust
this number" without opening the SQL.

GATE v2 — RULED 2026-10-03 (the Echo-law generator verdict +
the debug01/debug02 A/B evidence; Sunny: "narrow to fact-words"
then, on the evidence, further):
- THE WORD WHITELIST IS RETIRED (S9's appendix and its lexicon
  are SUPERSEDED — kept in this doc as history). Four
  recalibrations on one beat = wrong mechanism; the A/B run
  showed it was the gate-ese generator and its one famous catch
  (the semicolon) dies twice over without it.
- THE ESTATE BOUNDARY replaces it: every CUSTOMER-SPECIFIC fact
  (names, codes, values, filters, formats of THIS estate) must
  trace to the docket; GENERAL DOMAIN KNOWLEDGE IS FREE — "this
  is why we use LLM" (her ruling). Interpretation is the
  model's job; the gate polices truth boundary and register,
  never thinking.
- THE SURVIVING CHECKS (all precise, zero calibration debt)
  (2026-10-04, later same day — brief Q7/Q8: at the graph-walk
  reopen's build the RESOLVE-BACK CHECKER joins this gate as
  new named findings — room violation, conservation break,
  name violation — same objection-and-repair loop, budget 3;
  matching normalized-deterministic against short names,
  value-node names, parameter plain names, blessed names; an
  LLM linker EXCLUDED by ruling; the quoted-values check
  below is superseded there — grown to both directions; the
  pinned regressions stay forever; this passage stands as
  written until that build):
  quoted values + numbers must appear in the docket (an
  UNGROUNDED number fails AND lands a code sighting — S10
  narrowed: grounded numbers may speak); the never-list
  (format/purpose claim words — the lie taxonomy, ~15 words,
  grows only by her ruling); SQL vocabulary + @tokens banned;
  the five-line template; the kinds backstop (the Each-row-
  shows line over ~10 segments fails with "the full field list
  already lives in the technical appendix — name kinds");
  must-say (gap / window / excludes); the attachment anchor.
- WORD BUDGETS RETIRED (her "don't limit yet"); natural
  sentences; the kinds backstop replaces counting.
- S5 FLIPPED: provable logic IS decoded (inclusive date
  arithmetic, special-value multi-select, as-of replay);
  silence only for genuinely opaque expressions.
- MODEL SEAT: gpt-5.4 (her "don't use mini, use the large one");
  the production seat re-decides at the Fabric move under the
  parity law.
- THE PROMPT POSTURE (run-7 validated): understand first, then
  explain in own words; never mirror the technical phrasing;
  permission to omit (the appendix holds the complete detail).
- Evidence trail: debug01.md runs 1-7 — ungated ~90% accurate
  (the docket carries accuracy), run 7 PASS round 1 at gold
  parity. Residual variance between runs is sampling; her
  blessing picks.

S12-S14 + ONE-HOME — RULED 2026-10-04 (Sunny's six verbiage
findings on the 21/21 card; her case-by-case test applied: ZERO
new lists, zero gate growth — all four are PROMPT LAW, judgment
delegated to the model, her blessing the catch):
  S12 RELEVANCE RANKING: data-quality housekeeping (unlinked or
      incomplete records, record-entry timing) is summarized
      plainly in Excludes; business logic gets the prose. No
      column list — the model judges, she blesses.
  S13 PLAIN DICTION: plain connectors (in, with, during); never
      legal-ese (provided, passed, accepted, subject to).
      Prompt-only — NO word list, NO gate check; a list may be
      ruled later only on evidence of drift.
  S14 PROMPTS SPEAK AS CHOICES: multi-select parameters are
      "chosen when running the report"; a special value that
      makes the condition true for every row means "All" —
      provable semantics, one general sentence, every file.
  ONE-HOME-PER-FACT: each fact speaks once, on its ruled line
      (the as-of logic lives in Time window).
  THE LINE-OWNERSHIP LAW (RULED 2026-10-04, her "reads weird"
      find on Who's in it): Who's in it carries the POSITIVE
      population only — who + the window reference + ONE
      natural sentence for the run-time choices. EVERY negative
      (exclusions, "other than", housekeeping) lives ONLY in
      Excludes. Backed by a mechanical check: negative language
      on the Who's-in-it line fails, named (a shape rule, no
      content lists).
  THE TONE LAW (RULED 2026-10-04, superseding grammar
      micro-nudges — her words: "speak in a clinician's tone,
      instead of telling it about grammar"): cards and fact
      voices write in the voice of an experienced clinician
      explaining data to colleagues — plain, concrete, never
      the abstract voice of a systems document. A persona
      subsumes a pile of grammar rules; grammar nudges are not
      added to the prompt from here on.
  THE MUST-SURVIVE LAW (RULED 2026-10-04, demonstrated on the
      census SQL's nine WHERE conditions; full text in
      briefs/Brief_07_Graph_Grounded_Proposer.md Q3; binds the
      graph-walk reopen, test-locked at its build): as
      sentences compose upward, three MECHANICAL fact classes
      — assigned from where the predicate lives in the tree,
      never by judgment. (1) population-shaping: values intact
      every rung, landing on the owning card line (the
      line-ownership law is its landing map); (2) housekeeping:
      one plain clause, values not carried (S12 restated as a
      survival class); (3) plumbing (ON clauses, markers,
      split functions, special values as mechanisms): dies at
      its rung — the choice survives, its 0 dies. Enforced by
      VALUE CONSERVATION at the card, both directions (the
      voicing-ledger precedent). Branch scope: the population
      path only; fields never carry class-1 facts.

DOCKET v2 + THE FACT-VOICE LAYER — RULED 2026-10-04 (Sunny:
"fold it in... and let's implement"; born from the EMH OVERFLOW
poisoning find in debug02 and her how-to-leverage-LLM question):
(2026-10-04, later same day: THE ROOM LAW — brief Q5 —
supersedes the flat FACTS+CONTEXT docket AT THE GRAPH-WALK
REOPEN'S BUILD: one call per graph node, each rung's room
closed per the pinned table; docket v2 stands as written until
that build.)
- THE SPLIT: the docket has two parts. FACTS — assembled ONLY by
  the 05 resolver (never grep, never hand): sources with
  dictionary words, each population condition WITH its bound
  meaning on its own line, attachments, parameters, outputs.
  CONTEXT — the raw SQL + fuller dictionary prose, riding below
  as interpretation fuel ONLY.
- V-1 IS SCOPED TO FACTS: every value the card asserts must
  appear in the FACTS block — presence in CONTEXT grounds
  nothing. A value only enters FACTS through a parse-proven
  binding, so a wrong-purpose value (the EMH class) cannot
  enter, and a value lifted from the SQL without a binding
  FAILS.
- THE FACT-VOICE LAYER (her proposal, ruled): an LLM translates
  each machine fact into plain English ONCE — small scoped
  calls, each voice GATED (its values must be the fact's own;
  never-list; no SQL words), STORED in 07_fact_voices.json
  keyed by node + fact-text hash (delta-by-name: a changed fact
  re-proposes; an unchanged fact never re-pays), and BLESSABLE
  at the fact grain via the registry (blessed voice > gated
  proposed voice > the machine fact). The card writer composes
  from these vetted pieces — variance drops, her blessing gains
  its finest lever.
- HOMES AND LAWS: this layer is PHASE II territory — the 06
  floor stays zero-LLM (the two-machines ruling untouched).
  The per-file FACTS text (machine fact + voice side by side)
  lands TRACKED as <file_name>.facts.txt. Machine writes
  proposed voices only; blessing stays her RULING in the
  registry (THE RATIFY CLAUSE, 2026-10-04: the decision hers
  alone, the write machine-executed at her explicit ruling via
  the bless() door — full text in the 07 contract; amended for
  corpus scale, her words: hundreds of report files).
- SLICE SCOPE (this implement): the file grain's docket moves
  to v2; scope/field dockets follow in a later slice.
- FIELD DOCKET v2 (RULED 2026-10-04, the single-file deep
  track) — SUPERSEDED later the same day by THE ROOM LAW
  (brief Q5/Q6, Sunny's confirm after the conflicting-laws
  demonstration): at the graph-walk reopen's build, fields fly
  BLIND to population — the owning scope's filter lines leave
  the field's room entirely (the don't-restate instruction was
  advisory and line 27 was its bill: held for 16 fields, broke
  on the 17th); the dictionary description stays as
  context-only. The clause below stands as written ONLY until
  that build; its CI lock
  (test_field_docket_v2_named_and_inheriting) retires with it.
  Original clause: a field's docket.facts = its NAMED defining phrase
  (the 06 payload item rendered through the name overlay), its
  lineage when read through selections, and its owning scope's
  SHAPED filter lines — so a field sentence can say what the
  field means AND inherit the population truth. V-1 scoped as
  everywhere. The field FLOOR stays the 06 item verbatim
  (deterministic, ladder-free). Scope grain follows last.
- THE SCOPE MUST-SAYS (RULED 2026-10-04, brief Q4 — closes the
  "scope grain follows last" deferral above; binds the
  graph-walk reopen, test-locked at its build): a scope
  sentence owes (1) ONE ROW IS — always (the selection's
  grain); (2) KEEPS — only when the scope OWNS membership
  conditions in its own WHERE, voiced under the must-survive
  classes; honest silence when it owns none (R7 precedent) —
  a parameter-split selection is fully described by its grain
  sentence alone. Ownership boundary: a scope speaks only its
  own WHERE (EXISTS sub-conditions voice inline at the parent
  per THE FACTS SHAPE LAW, no double counting). Per-scope
  value conservation. FEEDS (the consumed side restating who
  uses it) REJECTED by one-home-per-fact — the consuming
  sentence owns the relationship; the chat serves "why does
  this exist" from the graph edge at read time.
- THE ROOM LAW + THE LINE SELECTORS (RULED 2026-10-04, brief
  Q5, full table there; bind the graph-walk reopen, built at
  its build): code walks the 05 graph bottom-up, ONE call per
  node, each rung's room closed — predicate (its columns'
  short names + bound values; dictionary words context-only),
  structure (child sentences only), scope (own structures +
  grain + payload), file card (scope sentences routed per
  selector), field (column + expression only; population
  facts NOT in the room). The LLM never walks; a fact outside
  the room cannot be spoken. The five card lines stay as the
  reader format — the graph decides CONTENT, the card decides
  PRESENTATION — each line a NAMED SELECTOR over the file
  subgraph (One row is <- delivery grain; Who's in it <-
  class-1 positives + choices; Each row shows <- payload
  kinds; Time window <- class-1 temporal; Excludes <- class-1
  negatives + class-2). Generation LINE BY LINE, five calls,
  per-line conservation and repair; code assembles the card.
- THE FACTS SHAPE LAW (RULED 2026-10-04, her 13-vs-9 find):
  WHO-IS-IN lists ONE line per TOP-LEVEL condition of the WHERE
  — an OR-group composes on ONE line (R3's shape law at the
  facts grain: splitting an OR silently makes it an AND); an
  EXISTS condition INLINES its sub-selection's own condition on
  its line ("a matching entry exists in <source> where ...") —
  the L03 floor-form deferral closes; sub-selection leaves are
  never listed as file filters (no double counting). The line
  count equals the SQL's top-level clause count, by test.
- RECORDEDNESS SPEAKS THE LADDER + LINKAGE (RULED 2026-10-04,
  her 'pat id' find): (a) the recordedness voice ("...is
  recorded") consults the name ladder like every other 07
  surface — "The patient id is recorded", never "pat id"; a
  07-side voice seat, the 06 floor's own R5.c law untouched.
  (b) VOICE LAW, prompt-only: recordedness of an IDENTIFIER
  means LINKAGE — "The event is linked to a patient." (her
  wording); recordedness of a data column stays "has a recorded
  <x>". The voicer judges which; her blessing catches.
- THE NAME LADDER (RULED 2026-10-04; the law lives in
  Design_Proprietary_Term_Assets.md — ONE naming asset, the 03
  abstracts; a 07-local name store was REJECTED): FACTS, fact
  voices and cards speak tables and columns through
  sunny_*/blessed > the asset's FIRST synonym > the R5
  description words. FACTS filter lines are RE-RENDERED through
  the importable 06 machinery with the name overlay — the 06
  floor itself stays dictionary-words, untouched.

THE STYLE GRAMMAR (S-rules) — RULED IN THE DRY RUN, Sunny's go
per round (2026-10-03); S2/S4/S6/S7(as five lines)/S10(narrowed)
/S11 stand; S1/S3 absorbed into the definition above; S5
FLIPPED, S8 budgets and S9's lexicon RETIRED per Gate v2:
  S1  THE SHAPE (file grain): labeled parts, never prose walls.
  S2  BANNED VOCABULARY: no SQL words (join, select, query,
      table, temp, column, procedure, parameter), no @tokens,
      no raw codes. Mechanical gate check.
  S3  NO INVENTORIES: never enumerate output fields or steps;
      name KINDS of information. (Round-4 lesson: 'mrn' creep.)
  S4  ATTACHMENT SPEECH: attached information is ADDED to rows,
      never phrased as restricting membership. (Round-1 failure;
      held from round 2 on.)
  S5  NO DECODING: system defaults speak as "a configurable
      window", never interpreted.
  S6  Plain present tense, active voice, everyday words.
  S7  THE MICRO-TEMPLATE (file grain; Sunny's readability ask):
      exactly four labeled lines —
        Who's in it: / Each row shows: / Time window: /
        Excludes:
      — scannable, never a paragraph. (Round-4/5 proven.)
  S8  BUDGETS: one claim per sentence; max 15 words per
      sentence; exclusions as plain phrases; at most one short
      parenthetical; no nesting.
  S9  PLAIN NAMES + JARGON DEFINED ONCE: entities speak through
      blessed vocabulary; a report's 2-3 domain terms get a
      one-line definition at first use, from the blessed
      glossary only.
  S10 UNBOUND CODES NEVER SURFACE: a code with no stored meaning
      speaks as "a specific recorded type/category"; the code
      stays in the technical appendix; THE SIGHTING LANDS IN THE
      DICTIONARY-GROWTH QUEUE (the business voice as a second
      value-meaning flywheel). (Round-4 find; round-5 proven.)
  S11 TRANSLATE, NEVER ECHO: plain words always; never copy
      uppercase tokens, abbreviations, or quoted literals;
      quoted plain words speak in normal casing. (The
      budget-echo tradeoff, round 4; round-5 proven.)

THE GATE (draft — the no-model mechanical build):
- LEXICAL WHITELIST: every content word / number / quoted value
  in a proposal must trace to the docket (the 06 sentences +
  05 rows + 02 words + the blessed vocabulary) — fails with the
  word NAMED. (Would have killed the round-1/2 semicolon
  fabrication both times.)
- S2 banned-word scan, S8 budget counts, S7 template shape:
  trivial mechanical checks.
- S4 check: membership claims must anchor to Population/WHERE
  rows; attachment words must anchor to on_class attachment
  rows.
- THE MUST-SAY CHECKLIST (omissions governed, not guessed): a
  dynamic-SQL gap file MUST say the gap; population-shaping
  parameters MUST surface as the window; existing exclusions
  MUST produce an Excludes line. Miss = named fail.
- THE LEVELS LAW: the business description is a SUMMARY BY RULE;
  completeness lives in the technical floor + appendix beneath
  it. An omission in a summary is not a lie; a must-say miss is.
- Verdict order (ported law): blessed > gate-passed proposal >
  THE FLOOR. Gate failures feed the repair loop with objections
  NAMED (R15; dry-run rounds 3-5 are the working example).

THE PRODUCTS (draft):
- 07_business_sheet: one row per described node — node_id,
  grain (file | scope | field | term), audience_text, status
  (proposed | gate_passed | blessed | floor), gate_findings,
  basis_version, the docket refs.
- THE BLESSING REGISTRY (G1): blessed names + blessed sentences,
  delta-by-name, Sunny's hand only; seeded from 03's
  sunny_synonyms.
- THE FIELD GRAIN (G2, recommendation from the dry run): Phase
  II mints per-field rows by calling the importable 06 renderers
  — 06 stays closed; no sixth grain reopen.
- The Collibra sync of R13's three-level field: this phase's
  shipping lane (scope to be ruled).

THE RATIFICATION — RULED 2026-10-03 (Sunny: "go", taking Claude's
recommendations as the rulings; the code hold LIFTED by the same
word — round 5's outputs are the accepted quality bar):
  1. S1-S11 RULED AS A SET — the style grammar is law; wording
     changes bump the 07 grammar constant and re-pin, never
     drift.
  2. THE GATE'S CHECKS ARE CONTRACT LAW: the lexical whitelist
     (fails with the word NAMED), S2 banned scan, S8 budgets,
     S7 template shape, S4 membership/attachment anchors, and
     the MUST-SAY checklist with exactly three members: the gap
     (dynamic-SQL files), the window (population-shaping
     parameters), the Excludes line (existing exclusions).
  3. PRODUCTS RULED: 07_business_sheet (grains file | scope |
     field; status proposed | gate_passed | blessed | floor;
     gate findings on the row) + THE BLESSING REGISTRY (Sunny's
     hand only, delta-by-name, seeded from 03 sunny_synonyms at
     her word) + per-file business texts as tracked build
     output. Term grain DEFERRED to the glossary milestone.
  4. G2 OPTION (a) CONFIRMED: field rows mint via the importable
     06 renderers; 06 stays closed.
  5. REPAIR BUDGET = 3 rounds (the dry-run evidence); after
     round 3 the floor stands and the last findings stay on the
     row for Sunny's eye.
  6. MODEL SEATS: local development = gpt-5-mini (the dry run's
     seat, the 03 precedent); production = gpt-5.4-mini on the
     aivia Azure endpoint (the M05 adoption); the parity law
     applies at the move.
  7. COLLIBRA SYNC DEFERRED to this phase's closing milestone —
     the voice is built and blessed first; the sync ships a
     field that already passed her eye. The report-layer
     cherry-pick stays Phase II-later (prior art R13 rider).

S9 APPENDIX — THE DESCRIBING VOCABULARY (RATIFIED 2026-10-03,
Sunny: "ratify the vocabulary" — ONE enumerated ruling replaces
drip-growth; the list below IS the lexicon; it never grows
case-by-case again. The words from the earlier dated growths
carry forward with their standing rulings: marked lacking apply
demographics context speaking entered about none begin):

  The law of the split: this list holds only GENERIC DESCRIBING
  ENGLISH — how any data is spoken about. CONTENT words (what
  THIS data is) must always trace to the file's own stored rows.
  A word's absence here is not a gap if the docket can supply it.

  verbs of showing:   shows lists holds carries contains
    includes covers combines groups counts adds attaches brings
    draws keeps returns records marks labels names identifies
    appears belongs derives applies matches links ties pairs
    gathers collects summarizes totals measures tracks reflects
    represents describes indicates means refers relates remains
    stays spans ranges starts begins ends stops
  nouns of shape:     row record field value list set group
    count total amount period range window date time day month
    year start end beginning source category type kind status
    flag detail details summary item entry text name label
    identifier description information selection report dataset
    data result
  qualifiers:         single multiple several separate combined
    related linked matching matched recorded available missing
    blank empty present absent active inactive current specific
    configurable optional defined stated listed shown included
    excluded grouped
  restriction words (lexicon-legal, but G-5 STILL requires a
    membership anchor): only limited restricted excluding
  connectives:        within during across together otherwise
    alongside plus without whether

  THE NEVER LIST (deliberately absent; documented so their
  absence is a ruling, not an oversight):
  - format-claim words: separator delimiter comma semicolon
    formatted (the round-2 fabrication class — only the docket
    may supply them)
  - purpose words: supports enables helps intended purpose
    (purpose is not stored anywhere; saying it is invention)
  - superlative/order claims: latest earliest first last primary
    verified (true only when the docket says so — the docket
    supplies them when true)
  - domain words: admission discharge transfer diagnosis etc. —
    all domain content comes from stored rows or blessed names,
    never from the gate's own vocabulary.

THE SINGLE-FILE PROBE (Sunny's call 2026-10-03: "take one medium
sized sql file and run it end to end" — Totals_SSRS, 21 nodes,
~17 min first pass, ~1 min/node, ≈2.4 calls/node):
- Calibration trajectory 9 -> 15 -> 16 of 21 gate-passed across
  three passes (probe fixes, then the ratified vocabulary);
  checkpoint seeding made every pass's survivors free.
- Fixes landed test-first en route: ruled-phrase words structural
  ('specific' — the gate no longer rejects obedience to S10);
  morphology-tolerant matching (location/located,
  creation/created, values/value — ONE matcher for docket,
  lexicon, registry); findings deduped; only_file scoping.
- THE PRINCIPLED RESIDUE (5 floors, all correct): the file grain
  wants admission/discharge/transfer — domain words no row
  stores; the fix is HER flywheel (a blessed name / table
  description for CLARITY_ADT), never the gate. The STRING_SPLIT
  mechanics scopes say 'comma' (stored only as punctuation);
  marginal targets, honest floors.
- AUTONOMY RULING (hers, same day): no per-file curation ever —
  class fixes + the one-time ratified vocabulary; a new SQL file
  runs unattended, floors ship honestly, her hand only RAISES
  quality (blessing, dictionary growth), never unblocks.

TEST POSTURE (ruled with the set): Claude's suite is
DETERMINISTIC — the gate, the docket builder, the prompt
constructor, the sheet and texts are all testable without a
model; the dry run's RECORDED REAL outputs (provenance: 14 paid
gpt-5-mini calls, 2026-10-03, verbatim in the dryruns doc) serve
as fixtures — recorded real speech replayed as data is not a
fake call. The proposer's live path is exercised by the build
command itself and accepted by Sunny's eye, the ED-sepsis law as
always.

Local build steps (pseudo first, red first, one code file —
business_descriptions.py):
    L01: data contract 07_business_descriptions_data_contract.md
         — complete and stamped BEFORE the first red test (the
         amendment law).
    L02: the blessing registry skeleton + the sunny_synonyms
         seed list staged FOR Sunny's ratifying hand (nothing
         blessed by machine, ever).
    L03: THE GATE (no-model): docket builder + the ruled checks;
         red tests = fabricated proposals + the dry run's real
         failures pinned as regressions (the semicolon dies in
         CI forever).
    L04: THE PROPOSER: the S-grammar prompt constructor
         (deterministic, byte-tested) + the paid-call seat + the
         repair loop (budget 3, objections named from gate
         findings).
    L05: the effective ladder (blessed > gate_passed > floor) +
         07_business_sheet lands + the field grain via the 06
         renderers.
         L03+L04+L05 BUILT 2026-10-03 (one slice, her "go" on
         the pseudo): business_descriptions.py — gate G-1..G-7
         live (the round-2 semicolon fabrication and the round-4
         'selects'/'language is 1' are pinned CI regressions;
         round-5's clean outputs pinned as passes), the
         plain-word lexicon seeded closed (one growth at green:
         'configurable', ruled S5 speech), prompt constructor
         deterministic + example-free, effective ladder,
         build07 with --no-llm floor path. 11 tests red then
         green; full suite 263; ruff clean. FLOOR-ONLY TRACKED
         BUILD LANDED: 151 rows (8 file + 36 scope + 107 field)
         over 8 files, all status=floor, registry untouched by
         byte-identity test.
    L06: the per-file business texts (tracked) + the live corpus
         run + Sunny's blessing pass — her eye is the
         acceptance.
    L07 (closing milestone, deferred): the Collibra sync.
