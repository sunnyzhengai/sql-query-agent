07_business_descriptions.md

Status: DRAFT (started 2026-10-03, scribed by Claude at Sunny's
word — "document these decisions in the design docs" — while she
napped). Sunny owns this doc. The S-rules below were RULED IN THE
DRY RUN (her explicit go per round, dated); everything else is
DRAFT awaiting her ratification at the design session. NO CODE
EXISTS — her standing word: "until i'm good with the output,
don't code."
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

OPEN FOR SUNNY'S RATIFICATION (the design session's agenda):
  1. The S-rules re-stamped as a set (S1-S11 above).
  2. The gate's check list as contract law (incl. the must-say
     checklist's exact members).
  3. The products + grains + the blessing registry's contract.
  4. G2 option (a) confirmed (renderer-import, no 06 reopen).
  5. The repair-loop budget (how many rounds before the floor
     stands; dry-run evidence: 3).
  6. Model seat (gpt-5-mini used in the dry run; gpt-5.4-mini is
     the adopted Azure production seat — parity law applies).
  7. The Collibra sync scope and the report-layer question.

Local build steps: TBD at the design session (ladder drafted
after the decisions are stamped; pseudo code first, tests red
first, as always). NO CODE until Sunny lifts her hold.
