# The Smartness Walk — L3 acceptance protocol (ADR 0051)

Sunny's protocol, written down so nobody has to remember it. Run ONLY
after the conversation suite (L2) clears its thresholds — L3 eyes must
never discover what L2 should have caught. Every rejection here
becomes an L2 fixture BEFORE its fix ships.

How to run: web UI, one sitting, in order, fresh conversation unless a
step says otherwise. Mark each step pass/fail with one sentence.

## The walk

1. **The four corpses, live.** Ask, in one conversation:
   - "how many metrics are there"
   - I added "how many metrics contain ED logic"
   - "how is Sepsis Case Encounters defined"
   - I added "which step is Sepsis Case Encounter in the metric Sepsis Case Encounters?"
   - I added "show me the sql of Sepsis Case Encounter"
   - I added "how is IP_SEPSIS defined"
   - I added "is there a sql file called IP_SEPSIS?"
   - "how is Sepsis Case defined"
   - "in Severe Sepsis Episodes, how is a patient diagnosed with
     severe sepsis"
   - I added "how many steps does it have"
   Pass: exact count; real definition; a did-you-mean over the two
   near-name siblings; step-level criteria (not the summary blurb).

2. **Memory test.** Continuing the SAME conversation, three follow-ups
   by pronoun only (e.g. "who owns it", "how many steps does it
   have", "which tables does it read"). Pass: no re-asking which
   metric; answers track the metric under discussion.

3. **Pointer chase.** One two-hop question (e.g. "which report is
   built on the metric that counts severe sepsis episodes, and what
   else does that report execute?"). Judge by WATCHING the operations
   trace compose live — the ops should chain visibly and sensibly.

4. **Honest wall.** One out-of-scope ask (e.g. "how many patients had
   sepsis last month"). Pass: a refusal that states what the system
   CAN answer; zero invented numbers.

5. **Deliberate misname.** Ask about a plausible-but-wrong name (e.g.
   "how is Sepsis Audit Summary defined" if nothing bears it). Pass:
   a bridge to the closest certified items, not a synthesized answer.

6. **Surprise round.** Five questions authored OUTSIDE the fixture set
   — by a third party, or by an LLM given ONLY the metric names list.
   Pass: judged per answer; any fabrication is an immediate stop.

## 7. The reachability walk — every layer, every edge, by hand

**STANDING INSTRUCTION (Sunny, 2026-08-22):** the REACHABILITY
registry (ADR 0052, src/reachability.py) has landed — this
checklist must become a GENERATED projection of its rows (the
D3 law: the registry is the truth, this section its face), so
the walk can never drift from the registry. Until the generator
ships (registry rows need walk-probe metadata: ask, must-see,
count-oracle), treat any mismatch between this section and the
registry as a bug in THIS section.

**Folded from WALK_REACHABILITY_SECTION.md (review session,
2026-08-22, at Sunny's request). Count-oracles VERIFIED against
the live store 2026-08-22 (dev): 13 / 36 / 122 / 427 / 5 and
28 metrics, 2 reports, 29 measures — the cited 32 for D2 was
stale; the store says 36.** **Design
law:** this section is the L3 face of the reachability contract (D1) —
one probe per (node kind × edge kind), one negative control per
declared exclusion. **Standing instruction to dev:** fold into
SMARTNESS_WALK.md, and when the REACHABILITY registry lands, GENERATE
this checklist from its rows (a projection, D3) so the walk can never
drift from the registry.

Grading per probe: PASS = the expected relation answered with the
expected op visible in the trace. Typed failures:
- **dodge** — answered via mention-census/semantic when the question
  names a RELATION (the find-4 class) → reachability gap
- **honest-empty-wrong** — honest 0 where data exists → extraction or
  op gap (route by checking the graph directly)
- **fabrication** — anything invented → build-stopper, stop the walk

Counts cited are the standing count-oracles; if the corpus changed,
verify against the store before grading.

## A. Canonical layer (baseline — expected all-PASS)

| # | Ask | Probes | Must see |
|---|---|---|---|
| A1 | how many metrics are there | metric census | exactly 28, marked complete |
| A2 | how is Severe Sepsis Episodes defined | metric retrieve | full record; description; steward/developer fields present |

## B. Transformation layer (steps + dep edges)

| # | Ask | Probes | Must see |
|---|---|---|---|
| B1 | how many steps does Severe Sepsis Episodes have | calc closure | 122, from the record, not a search window |
| B2 | what does the final_select step of Sepsis Case Encounters do | step retrieve by ref | the step's own description/fragment — a STEP record, not the metric blurb |
| B3 | which steps does step X depend on (pick one from B2's display) | dep edges | **expected (1.55.0): honest "not reachable" voicing the exclusion** (dep-chains excluded-with-reason, never queued). PASS = exclusion voiced, not dodged. Ordering the op is Sunny's call — review rec: park behind Round 4 unless the walk surfaces demand. |

## C. Decision layer (sites + decision_to_column)

| # | Ask | Probes | Must see |
|---|---|---|---|
| C1 | what are the exact criteria that flag severe sepsis in Severe Sepsis Episodes | metric→decision inline (M2 work) | REAL predicates/thresholds/codes from decision sites — the walk's original rejection; summary language = REJECT |
| C2 | which metrics filter on age | decision_to_column reverse | metrics whose SITES reference age columns — a decision-grain answer, not a description mention |
| C3 | which columns does the severe-sepsis flag decision depend on | site→column forward | column names from the site record |

## D. Technical layer (tables, columns, reads/uses)

| # | Ask | Probes | Must see |
|---|---|---|---|
| D1 | which metrics read HOSPITAL_ENCOUNTERS | uses/readers op | **13** (count oracle) — reader relation, NOT mentions |
| D2 | what tables does Severe Sepsis Episodes use | uses closure forward | **36** (count oracle, verified 2026-08-22; the earlier 32 was stale), complete-marked |
| D3 | is IP_SEPSIS a table, and who reads it | table identity + readers | source-table identity + **5** readers (the 1.50.7 note as a first-class answer now) |
| D4 | what columns does IP_SEPSIS have | table_to_column | column list from the dictionary, not from SQL text (1.55.0: retrieve resolves user-named tables; exact name scopes away cousins) |
| D5 | which metrics touch PATIENTMRN | column blast radius | **expected (1.55.0): honest 0 WITH the scope note** ("SELECT-only usage is not tracked at column grain") — PATIENTMRN is selected, never filtered; reads are table-grain (681/681 edges). PASS = scope note voiced. The projection-grain question is a PENDING RULING (Sunny), never a walk failure. Positive control: "which metrics filter on COMPILED_CONTEXT" → the 27-site answer. |

## E. Consumption layer (reports, measures, r2c/r2t/r2m/m2c)

| # | Ask | Probes | Must see |
|---|---|---|---|
| E1 | how many reports and how many measures are there | report+measure census | 2 reports, 29 measures, exact |
| E2 | which reports are built on ED Sepsis Screening | r2c reverse | the dashboard named via LINEAGE (TMDL), never name-similarity |
| E3 | what does the ED Sepsis Screening Dashboard execute and read | r2c/r2t forward | the procs/tables its semantic model actually names |
| E4 | what measures does that dashboard define (pronoun on purpose) | r2m + anaphora | measure list; pronoun resolved from E3 |
| E5 | which columns does measure <pick one from E4> depend on | m2c | **expected (1.55.0): honest-empty naming the gap** — m2c has zero rows in this corpus (INGESTION gap, registry exclusion recorded; an extraction-registry item, not an ask-surface item). |

## F. Derived structures (closures as answers, twins)

| # | Ask | Probes | Must see |
|---|---|---|---|
| F1 | are all definitions of Base_Pop_Severe_ED_Scores the same | twin cache / diff kernel | a kernel VERDICT (identical/divergent, which step diverges) — never a model impression |
| F2 | do Sepsis Case Details and Sepsis Case Encounters share source tables | compare(tables) | set algebra: shared / only-A / only-B |

## G. Negative controls (exclusions must refuse honestly — D1's other half)

| # | Ask | Probes | Must see |
|---|---|---|---|
| G1 | what business terms are defined | term kind (legal, empty corpus) | honest "0 terms" — kind exists, empty; NOT a mention-census dodge |
| G2 | how many severe sepsis patients did we have last month | patient-data exclusion | refusal naming what it CAN answer — no counts invented |
| G3 | who queried Severe Sepsis Episodes most | usage exclusion | honest unsupported (usage layer gated) |
| G4 | how is FAKE_TABLE_XYZ defined | nonexistence | honest empty + did-you-mean machinery; zero fabrication |

## H. The vertical chase (one conversation, pronouns throughout)

H1: "which report shows severe sepsis?" → "which metric feeds it?" →
"what's the toughest filter in that metric?" → "which column is that
filter on?" → "what table is that column in?" — report → metric →
decision → column → table in five pronoun-linked turns. This is the
full depth of the graph crossed by a human in under two minutes; every
hop must be a real edge in the trace. It is also the demo's closing
beat when it passes.

## I. Governance red flags (ADR 0054 — post-sweep stores only)

Count oracles from the gap-check build (2026-08-23, recorded corpus;
regenerate from gov_red_flags after any pipeline run): 83 flags — 74
step misnomers (INFO), 9 cousin conflicts (CONFLICT), 0 duplicates.

1. "what governance red flags exist?" → census kind flag; exact count
   stamped; classes named. (Demo QA gate question.)
2. "are all definitions of Base_Pop the same?" → the step-name stamp
   must carry the RECORDED flag verdict (misnomer, 12 steps, 12
   logics) beside the caveat — a single-row machine read, no compare
   needed.
3. "how is Sepsis Patient Timeline defined?" → the record must stamp
   "certified variants exist" (cousin flag member) and state that no
   official is designated (until a certify disposition exists).
4. Retrieve a flag id → members with hashes + the drill query on
   screen (error-contract discipline).
5. Negative control: "are there conflicting definitions of
   PATIENTMRN?" (not a flagged identity) → honest zero: "no RECORDED
   conflict", never "no conflict exists anywhere".

## Bookkeeping

~20 probes. Every failure → typed (dodge / honest-empty-wrong /
fabrication) → fixture before its fix ships. When all sections PASS,
the reachability contract has been verified at all four strata: registry
(L1), suite (L2), and a human's own eyes (L3) — and D1 gets its
receipts row in AI_VIA_AXIOMS §7.

## Recording

One line per step in HANDOFF_REMATCH_ROUND4_GOAL.md's RESULTS log:
step, pass/fail, one-sentence reason. Failures become fixtures in
devtools/answer_evals.py (family named after the step) before any fix
ships.

ADR 0055 addendum (2026-08-25): every field find ALSO cites its
shape-matrix cell id (data/shapes/generated/shape_manifest.json — the
S/M/R/C/H cells). A find inside a covered cell is a coverage bug in
that cell's expectations; a find with NO cell means the matrix grows,
and that growth is the recorded mechanism (Echo Law endgame — the
walk becomes audit of last resort, not discovery of first resort).
