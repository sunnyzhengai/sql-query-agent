# Dry run: Phase II consumes Phase I

Status: DRY-RUN EVIDENCE (requested by Sunny 2026-10-03, authored
by Claude at her word). NOT a design doc — nothing here is ruled;
this is the walk-through that informs the Phase II design session.
Example file: Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_
Detail_PBI (the richest of the 8: star expansion, attachments,
computed-member lineage, 98 predicates).

## 1. What Phase II builds (per the ruled prior art)

The eloquent machine — the second of the two machines
(00_Architecture.md). Prior art, all ruled in the prior estate:
R14 (business-term sentence), R15 (voicing repairs), R16 (business
voice tier + the meaning ladder), the blessed-name tier (R5.b),
and the hybrid loop: LLM PROPOSES a business sentence -> a
NO-MODEL MECHANICAL GATE checks named rules against stored rows ->
Sunny BLESSES or the floor ships (business_voice.py;
Brief_Business_Voice APPROVED 2026-09-20). Paid API calls, per
standing law. Its products, by grain:

| Phase II product                  | Grain      | Consumer |
|-----------------------------------|------------|----------|
| business description              | file       | Collibra sync; chat; end users |
| business description              | scope      | chat answers; the file sentence's parts |
| business names (blessed)          | scope/term | all business sentences |
| business term sentences (R14)     | term       | glossary; chat |
| Collibra sync of the R13 field    | file       | governance |

## 2. The walk — one file, end to end

### 2a. What the LLM proposer RECEIVES (all Phase I stored rows)

For the example file, Phase I hands the proposer a grounded
docket — every line below is quoted verbatim from the tracked
06/05 outputs of build 06.3.0:

- THE FILE FLOOR (06_description_sheet, grain file) — headline:
  "Delivers a selection from #combined_census, attaching
  #caregiver_languages (attachment rule: the patient associated
  with this patient day unique is the patient this patient
  contact is added to unique), attaching #coverage (attachment
  rule: ... the monthly census start date is the monthly census
  start date), attaching PATIENT (...)" + Pipeline (7 voiced
  steps) + Presents + Population + the census close.
- THE SCOPE SENTENCES (grain scope, 11 rows) — e.g.
  #caregiver_languages: "This is a selection from
  PAT_REL_LANGUAGES, joined with #caregivers, joined with
  ZC_LANGUAGE (matched where the patient contact language is the
  language c), attaching PAT_RELATIONSHIP_LIST_HX (...)".
- THE CONDITIONS AND PREDICATES (grains condition/predicate,
  44 + 98 rows) — e.g. "The patient's gender identity is 'Choose
  not to disclose' (6)." — value meanings already spoken.
- THE LEDGER (06_voicing_ledger) — what Phase I chose NOT to say
  and why (this file: its share of the 28 words-gaps, the
  attachment-apart rows). The proposer is told the boundary of
  the known, so it cannot "fill in" silence.
- THE GRAPH ITSELF (the 11 x 05 sheets) — for structural checks:
  lineage walks (star_member fans, member chains), parameter
  defaults, on_class, evidence down to line/column.
- THE DICTIONARY WORDS (02) — table + column descriptions and
  value meanings; table descriptions are UNUSED by Phase I's
  lead ("a selection from CLARITY_ADT") and available for Phase
  II's richer register.

### 2b. What the proposer might SAY (illustrative shape only —
### a real proposal is a paid call at build time, never canned)

A business headline proposal for this file would compress the
floor's truth into the end-user register — the kind of sentence
the audience law reserved for Phase II: who is in the data
(hospital + clinic census patients for the month), what attaches
(their caregivers and those caregivers' languages, their
coverage), what it is FOR (interpreter-services planning). Every
claim in such a sentence maps to a Phase I row quoted in 2a.

### 2c. What the GATE CHECKS (no model — stored rows only)

| Gate check (prior art: check_sentence)        | Phase I row it checks against | Available? |
|-----------------------------------------------|-------------------------------|------------|
| every NUMBER in the proposal exists in rows   | predicate/value rows ('Choose not to disclose' (6); @StartDate default) | YES |
| every named ENTITY resolves                   | 05 resolves edges; scope sheet names; 02 words | YES |
| population claims match membership            | Population section rows; on_class (attachment never a filter) | YES |
| no speech about the unsaid                    | the ledger (words-gaps, dynamic gap, unvoiced) | YES |
| lineage claims match the walk                 | member / star_member / behind_star edges | YES |
| the floor ships when the gate fails           | the 06 sentences ARE the floor | YES |

### 2d. What Sunny BLESSES

Blessed names (scope + term) and gate-passed sentences, one ruled
row at a time — a NEW Phase II registry (see gap G1); the seed
vocabulary candidates already exist in 03's sunny_synonyms and
03_chat_abstract_names.json (sunny_* fields, preserved by law).

## 3. The input inventory — do we have everything?

| # | Phase II need                           | Phase I source                                   | Status |
|---|-----------------------------------------|--------------------------------------------------|--------|
| 1 | grounded technical sentences, 5 grains  | 06_description_sheet.json (362 rows, basis 06.3.0) | HAVE |
| 2 | the boundary of the known               | 06_voicing_ledger.json (93 rows, named classes)  | HAVE |
| 3 | the graph for structural gate checks    | the 11 x 05 sheets (evidence to line/column)     | HAVE |
| 4 | value meanings + column words           | 02 sheets (already spoken into sentences)        | HAVE |
| 5 | table-register words for richer leads   | 02 table descriptions (UNUSED by Phase I, ready) | HAVE |
| 6 | parameter defaults, verbatim            | 05_parameter_sheet + the file floor's line       | HAVE |
| 7 | deterministic re-render on demand       | technical_descriptions.py importable renderers   | HAVE |
| 8 | per-OUTPUT-COLUMN rows (report fields)  | payload items live INSIDE scope sentences only   | PARTIAL (G2) |
| 9 | rank/window meaning (most-recent-per-X) | ROW_NUMBER interim words; OVER not captured      | PARTIAL (queued 05 OVER amendment) |
| 10| dynamic-SQL content                     | the gap sentence (honest boundary)               | ABSENT BY RULE — Phase II must say the gap, never fill it; SET-capture amendment names the shapers later |
| 11| a blessing registry (names + sentences) | none — Phase II's OWN first output               | TO BUILD (G1) |
| 12| the LLM seat                            | .env keys; gpt-5.4-mini adopted (M05); paid-calls law | HAVE |
| 13| Collibra sync target for the R13 field  | the file rows carry the three levels             | HAVE (sync itself is Phase II scope) |

## 4. The gaps, named

- G1 — THE BLESSING REGISTRY (expected): Phase II's first data
  contract — blessed names + blessed sentences, delta-by-name,
  Sunny's hand only. Not a Phase I gap; it is Phase II's job.
  Seed candidates: 03's sunny_synonyms.
- G2 — PER-OUTPUT-COLUMN ROWS (the one real design question):
  end users ask about REPORT FIELDS ("Caregiver Languages",
  "Census Period"), and Phase II will want to propose/bless text
  per field. Phase I speaks every field inside the scope
  sentence's carrying-list but stores NO per-output row (the
  derived-column grain was deliberately out of 06's five grains).
  Options for the Phase II design session: (a) Phase II mints its
  own per-field rows by calling the importable 06 renderers
  (_payload_item et al.) — no 06 reopen; (b) reopen 06 decision 2
  to add a sixth grain. Claude's recommendation: (a) — the
  renderers are deterministic and tested; Phase II stores what it
  blesses, 06 stays closed.
- G3 — QUEUED AMENDMENTS THAT UPGRADE PHASE II INPUTS (already
  recorded, not blockers): the 05 OVER capture (#9) and the 05
  SET-capture (#10's shaper names).

## 5. THE EXECUTED DRY RUN — the outputs after each step
## (added 2026-10-03 at Sunny's ask: "so i can see after each
## step, what description is generated")

Three REAL proposer calls were made (gpt-5-mini, paid, one per
grain, 2026-10-03) over the Phase I rows of the example file.
The gate was then executed BY HAND by Claude — each named check
against the stored rows it cites (the mechanical gate is Phase
II's build; the checks below are what it will automate). Nothing
below is canned: the proposals are verbatim model output.

### Grain FILE

STEP 0 — THE FLOOR (Phase I, stored): the three-level definition
in 06_description_sheet.json (headline + 7-step pipeline +
Presents + Population + Inner joins + the verbatim parameter
defaults + the census close).

STEP 1 — THE PROPOSAL (verbatim model output):
> "This procedure produces a monthly patient roster by combining
> the monthly census and clinic data and attaching
> caregiver-language information, active insurance coverage, and
> patient records, and returns for each row the reporting period
> and dates, location and department details, caregiver languages
> [... the full field walk ...]. The output is restricted to
> patients whose caregiver languages do not include English (or
> where caregiver language is missing and the patient language is
> not recorded as English), includes only primary verified
> coverage effective for the census start date (filing order = 1
> and verified/in-effect statuses), and is shaped by @startDate
> and @endDate (which have default values defined in the
> procedure)."

STEP 2 — THE GATE (by hand, against stored rows):

| Check | Evidence row | Verdict |
|---|---|---|
| English-exclusion population claim | Population, "In the delivery: the caregiver languages does not contain 'ENGLISH' (annotated 'exclude patients with an english-speaking caregiver' ...)" | PASS |
| parameter-defaults claim | "Parameters shaping the population: @endDate (default \"[Clarity].EPIC_UTIL.EFN_DIN(COALESCE(@i_vEND_DATE,'ME-1'))\"); @startDate (...)" | PASS |
| field-list claims | Presents (spot-checked; the automated gate checks every item) | PASS |
| "includes ONLY primary verified coverage" | #coverage is ATTACHED (LeftOuter; on_class attachment) — its filing-order filter picks WHICH coverage row attaches, it removes NO patients | AMBIGUOUS -> FAIL (reads as a population restriction; the attachment-never-filter check) |

STEP 3 — THE EFFECTIVE SENTENCE: the gate failed one check ->
THE FLOOR SHIPS. The proposal goes back with the named reason
(rephrase to "where coverage is attached, only the primary
verified row attaches"); a repaired pass would then await
Sunny's blessing.

### Grain SCOPE (#caregiver_languages)

STEP 0 — THE FLOOR (stored): "This is a selection from
PAT_REL_LANGUAGES, joined with #caregivers, joined with
ZC_LANGUAGE (matched where the patient contact language is the
language c), attaching ... : either the date the patient
contact's relation to the patient started is on or before
@EndDate (annotated 'Relationship ended after report start but
was active during ' in the source) and ... ; carrying ..."

STEP 1 — THE PROPOSAL (verbatim model output):
> "For each patient, produce the spoken languages of patient
> contacts that are marked as emergency relationships and that
> were active at some point overlapping the specified start/end
> dates (active means: started on or before the report end and
> ended on or after the report start; or started on or before
> the report end and has no end date; or both start and end
> dates are missing). The output includes the patient identifier
> and a semicolon-separated list of caregiver language names."

STEP 2 — THE GATE:

| Check | Evidence row | Verdict |
|---|---|---|
| the date-overlap membership walk | the scope's membership ORs, verbatim (incl. the no-end-date arm) | PASS — a faithful, even elegant, translation |
| "marked as emergency relationships" | ZC_EMERG_PAT_REL is ATTACHED (lookup); no membership row restricts to emergency | FAIL (an attachment spoken as a restriction) |
| "semicolon-separated list" | NO stored row says the separator; the scope sentence says only "joined into one list"; the SQL's actual separator is CHAR(10)+CHAR(13) — a LINE BREAK | HARD FAIL — a confident fabrication, and factually wrong |

STEP 3 — THE EFFECTIVE SENTENCE: THE FLOOR SHIPS. This is the
dry run's sharpest exhibit: the model wrote a plausible,
professional sentence containing an invented delimiter — exactly
the class of lie the no-model gate exists to kill.

### Grain FIELD ("Caregiver Languages")

STEP 1 — THE PROPOSAL (verbatim model output):
> "Caregiver Languages: For each patient, this field lists the
> spoken languages recorded for caregivers designated in the
> Emergency relationship category who were active during the
> report date range (or who have no end date or have no dates
> recorded). Multiple languages for a patient are combined into
> a single semicolon-separated list and the values are tied to
> the patient's record ID."

STEP 2/3 — the same two failures ride in (the Emergency
designation as restriction; the semicolon fabrication) -> THE
FLOOR SHIPS.

### ROUND 2 — THE STYLED PROPOSALS (added 2026-10-03 at Sunny's
### ask: style must be intentional for a business user)

Round 1 ran with truth rules only. Round 2 adds A DRAFT STYLE
GRAMMAR to the proposer prompt — the candidate rulings for the
Phase II design session:

| # | Draft style rule (enforced in the prompt; the gate re-checks) |
|---|---|
| S1 | THE SHAPE — a file speaks two labeled parts: HEADLINE (what it delivers, who is in it, the window; max 2 sentences / 40 words) and DETAIL (what attaches to each row, key exclusions; max 3 sentences) |
| S2 | BANNED VOCABULARY — no SQL words (join, select, query, table, temp, column, procedure, parameter), no @tokens, no raw codes |
| S3 | NO INVENTORIES — never enumerate output fields or step counts; name KINDS of information, not lists |
| S4 | ATTACHMENT SPEECH — attached information is ADDED to rows, never phrased as restricting who is in the data |
| S5 | NO DECODING — system default expressions are named as "a configurable window", never interpreted |
| S6 | plain present tense, active voice, everyday words |

Round 2 verbatim outputs (real calls, gpt-5-mini):

FILE — HEADLINE: "Monthly patient census rows for patients in the
combined census whose caregiver languages are not English (or
missing while patient language is missing or not English), for a
configurable monthly census window defined by start and end
date." DETAIL: "Each row combines a monthly census patient day
with linked caregiver-language and patient demographic/contact
records plus the payor coverage effective on the monthly census
start date; when payor details are missing the row shows
Self-Pay. The dataset derives age, age group, race/ethnicity and
other demographic flags such as interpreter need, foster coverage
and insurance coverage status. It excludes patients with an
English-speaking caregiver and excludes cases where caregiver
language is blank but the patient's language is recorded as
English; the monthly window is controlled by configurable start
and end date parameters."

SCOPE: "This selection returns patient-contact language records
for contacts whose relationship to the patient overlaps the
report's configured start/end window, or where the relationship
has no end date recorded, or where both start and end dates have
no recorded value; it includes only contacts marked as spoken
language. Rows are grouped by patient and carry the patient
identifier from the caregivers source, and each row also adds
relationship-history details, the emergency-relationship
category, and caregiver languages combined into a single text
list."

FIELD: "For each patient, Caregiver Languages shows the spoken
languages recorded for that patient's caregiver contacts whose
relationship either overlaps the report's configurable date
window or has no dates entered. When multiple languages apply,
the values combine into a single text list with ';' as the
separator."

ROUND 2 GATE: the attachment failure from round 1 is GONE (S4
held). 'Self-pay', 'foster', 'spoken' were challenged and all
three ARE grounded (stored floor text carries each). Verdicts:
SCOPE — PASS, the dry run's first gate-clean business sentence.
FILE — truth PASS, style FAIL twice: the banned word
"parameters" (S2) and a field-inventory drift (S3).
FIELD — HARD FAIL: "';' as the separator" FABRICATED A SECOND
TIME (the stored text says only "joined into one list"; the
real separator is a line break). The same plausible lie
resisted an explicit rule — the gate cannot be advisory.

### ROUND 3 — THE REPAIR LOOP (R15's territory: the gate's
### objections feed the re-proposal, named)

FILE (repaired, verbatim) — HEADLINE: "Monthly patient-day
census for patients whose caregiver language is not English, or
whose caregiver language is blank while the patient's language
is blank or not English, within a configurable monthly reporting
window." DETAIL: "Each row represents a monthly census patient
day and attaches site/room/bed context, caregiver-language, the
primary verified payor coverage effective on the monthly census
start date (or \"Self-Pay\" when missing), and patient
demographics. The dataset derives classifications such as age
group, race/ethnicity, interpreter need, gender identity, and
foster/insurance coverage status. Caregiver-language records are
limited to contacts active during the reporting window, and the
dataset excludes patients with an English-speaking caregiver or
where caregiver language is blank while the patient's recorded
language is English."

FIELD (repaired, verbatim): "For each patient, Caregiver
Languages shows the spoken languages recorded for that patient's
caregiver contacts that are active during the report's date
window or that have no relationship dates entered. When multiple
languages apply to a patient, the values combine into a single
text list."

ROUND 3 GATE: FIELD — PASS (the fabrication is gone; the list
claim now says exactly what is stored). FILE — one residual soft
objection: "site" is not a stored word (the floor says
location); room/bed/location/gender-identity all grounded. One
more repair round would close it; recorded here instead so the
convergence cost stays measured: 1 unstyled round + 1 styled
round + 1 repair round ≈ a clean grain.

### ROUND 4 — THE READABILITY RULES (Sunny's ask 2026-10-03:
### three suggestions, ruled in: S7 the labeled micro-template
### [Who's in it / Each row shows / Time window / Excludes]; S8
### one claim per sentence, max 15 words, exclusions as plain
### phrases; S9 plain names, jargon defined once)

Verbatim outputs (real calls, gpt-5-mini):

FILE:
> Who's in it: Rows are about patient days from the combined
> monthly census.
> Each row shows: Monthly census dates, location, caregiver
> languages, coverage, mrn, patient name, legal sex.
> Time window: monthly census start date to monthly census end
> date
> Excludes: Caregiver languages contains 'ENGLISH'; No caregiver
> languages and patient language is 'English'

SCOPE:
> Grain is one selection inside the dataset build.
> It selects patient contacts where patient contact language is 1.
> It includes relationships with dates overlapping a configurable
> window or with no dates.

FIELD:
> Caregiver Languages lists caregiver language names joined into
> one text list.
> It includes contacts with language 1 and relationships active
> in a configurable window.

ROUND 4 GATE AND THE NEW FINDING:
- THE TEMPLATE WORKS: the FILE output is scannable at a glance —
  the shape Sunny asked for, delivered by rule.
- THE BUDGET-ECHO TRADEOFF (the round's discovery): squeezing
  the word budget pushed the model from FLUENT INVENTION (rounds
  1-2) to TECHNICAL ECHO — it copied floor tokens verbatim
  instead of translating: "contains 'ENGLISH'" (caps echo),
  "mrn" (a field inventory creeping back), and — worst — "where
  patient contact language is 1" and "contacts with language 1":
  RAW CODES in business prose, plus the banned word "selects".
  The gate catches all of it mechanically (banned vocabulary,
  raw-code check, inventory check) — but the cause is upstream.
- THE UNBOUND-CODE LESSON (feeds the dictionary flywheel): the
  model exposed code 1 because Phase I honestly says "is 1" —
  that value has NO meaning row in the 02 dictionary. The
  business layer cannot translate what Phase I does not know.
  Candidate rule S10: an UNBOUND code speaks as "a specific
  recorded category" in business prose (the code stays in the
  technical appendix), AND the unbound-code sighting lands in
  the dictionary-growth queue — the business voice becomes a
  second engine for Sunny's value-meaning growth.
- Convergence state after round 4: the recipe is template (S7)
  + budgets (S8) + plain names (S9) + the no-echo/unbound-code
  rule (S10) + the repair loop. Each round's failure became a
  named, mechanical rule — exactly how the grammar floor grew
  in the prior estate.

### ROUND 5 — S10 + TRANSLATE-NEVER-ECHO (Sunny: "run round 5
### with S10"; executed 2026-10-03 while she napped)

Rules added: S10 (an unbound code never appears — "a specific
recorded type" stands in) and S11 TRANSLATE-NEVER-ECHO (plain
words always; never copy uppercase tokens, abbreviations or
quoted literals; a quoted plain word speaks as a plain word).

Verbatim outputs (real calls, gpt-5-mini):

FILE:
> Who's in it: Patients present in the combined monthly census
> and clinic monthly selections.
> Each row shows: demographics, caregiver languages, coverage
> and payor, age, and census context.
> Time window: a configurable date window
> Excludes: patients with an English-speaking caregiver;
> patients with no recorded caregiver language when the patient
> language is English

SCOPE:
> Each row represents one patient contact added to a patient
> record.
> The contact relation is active during a configurable window or
> lacks start or end dates.
> Rows carry spoken contact language, relationship history,
> emergency category, patient identifier, and caregiver
> languages.

FIELD:
> Caregiver Languages lists languages recorded for each
> patient's caregiver contact marked as spoken language.
> It includes caregiver contacts active during the report window
> or lacking relationship dates.

ROUND 5 GATE: 3 of 3 PASS — the dry run's CONVERGENCE POINT.
Every claim traces to stored text ("spoken", "added to",
"emergency category", the English exclusions, the window); zero
raw codes (S10 held — the unbound language-type code vanished
into "marked as spoken language", which IS stored text); zero
echo; zero banned words; every sentence inside budget; the
template scannable. These three outputs are the quality bar
candidates for Sunny's blessing when Phase II builds.

### What the executed run proves (14 real calls, 5 rounds)

1. The loop runs TODAY on Phase I outputs alone — docket in,
   proposal out, every gate check answerable from a stored row.
2. The gate is NOT optional: round 1's 3 fluent proposals all
   carried ungrounded claims, and the "semicolon" fabrication
   SURVIVED an explicit prompt rule into round 2 — only the
   named objection killed it. Style rules in the prompt shape
   the voice; only the mechanical gate guarantees it.
3. The draft style grammar (S1-S6) WORKS: round 2 fixed the
   attachment phrasing and produced the first gate-clean
   sentence (SCOPE); round 3's repairs converged FIELD and left
   FILE one soft word from clean.
4. Convergence cost is small and measurable: unstyled -> styled
   -> one named-objection repair ≈ a clean grain, at gpt-5-mini
   prices.
5. The floor shipped at every failure — at no point could a lie
   reach a business surface.

## 6. Verdict

Phase I's outputs are SUFFICIENT to design and build Phase II's
core loop today: the proposer has grounded sentences and the
boundary of the known; the gate has stored rows for every named
check; the floor exists to ship on any gate failure. The two
PARTIALs are quality upgrades riding already-queued 05
amendments, not blockers. The one genuine design decision for
the Phase II session is G2 (per-field rows), with option (a)
recommended. Nothing in Phase I needs reopening to start
Phase II.

And the loop has now RUN (section 5): three real proposals over
real Phase I rows, each gate check answered by a stored row, the
floor shipping on every failure. The dry run's one-line summary:
the proposer is fluent, the gate is necessary, and Phase I's
floor already guarantees the system cannot lie while Phase II
learns to speak.
