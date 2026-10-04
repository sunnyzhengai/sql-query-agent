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

THE STYLE GRAMMAR (S-rules) — RULED IN THE DRY RUN, Sunny's go
per round (2026-10-03); to be re-stamped as a set at the design
session:
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
