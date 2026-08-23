# Walk verdicts — Sunny live on the workbench (engine 1.56.1/1.56.2), 2026-08-23

Recording per protocol: verdict the moment made; failures typed;
fixtures before fixes. Questions are Sunny's modified walk set.

## Q1 — "what metrics are there" (census family)

**VERDICT: PASS (honest), with two recorded finds.** Correct 28-metric
table; final answer was the HONESTY FLOOR — the model's caption
invented a number ('9' appears in no displayed result), the gate
caught it and rendered the stamped headlines. The machinery held on
camera.

- **FIND W1 (behavior + presentation): answer repetition.** Causes,
  stacked: (1) the floored caption re-prints stamped headlines that
  are already on screen above each table; (2) the model ran an
  UNNECESSARY round 2 — retrieved 11 full records (384 step ids,
  1662 decision sites) for a question the census alone answers —
  adding a second headline, second table, and most of the latency;
  (3) commentary duplicates on-screen stamps even in normal turns.
  Remedy direction (display-only, pin untouched, grading surface
  unchanged): floor renders pointer-style ("the results above are
  the answer — 28 metrics, count exact"); commentary collapses
  visually when it equals displayed stamps (same class as the 30-row
  fold). The unneeded retrieve is a capability observation — record,
  don't band-aid; candidate telemetry: rounds-beyond-sufficient.
- **FIND W2 (UX): no progress indication while the engine runs** —
  blank screen until the full trail renders. Remedy direction:
  stream the trail live (SSE from /api/ask; webapp renders each
  round's chip + headline as dispatch happens, then verdict/gate
  stages). Honest by construction — named ops mean the status shown
  IS the operation running, not a spinner. Also upgrades walk step 3
  (judge by watching ops compose) and the demo's VO-3 beat.
  Boundary/display machinery only — zero prompt/tool changes.

## Q2 — "how many metrics contain ED logic" (topical family; the 08-21 substring-bug fixture, live)

**VERDICT: PASS (clean).** One round, whole-token census
({"kind":"metric","contains":"ED"}) → exactly 2 rows (ED Sepsis
Screening, ED Sepsis (Regulatory)); composed commentary names both;
verdict answered, evidence = the stamped headline quoted verbatim
(the 1.53.1 quotable-headlines fix visibly working). No floor needed.
The question that said "28" two days ago now says 2.

- **FIND W3 (presentation nits, batch with W1):** (a) both metrics
  display as bare "USP_ED_Sepsis" — they differ only by schema
  (reporting. vs reports.), which the commentary omits, so the two
  list entries look identical; commentary should carry the
  schema-qualified id when display names collide. (b) model-written
  markdown (**bold**) renders as raw asterisks in the commentary
  block — render or strip. (c) the verdict line quotes the full R3
  headline already on screen — correct per the gate (quote machine
  truth); the DISPLAY can style the quote as a compact citation,
  same dedupe direction as W1.

## Q3 — "How is ED Sepsis Screening defined" (definition family)

**VERDICT: PASS.** One retrieve round; full certified record; headline
carries 43 steps / 256 decision sites with the top-12 inline (M2
work visible); composed definition voices the v6 business-logic
bullets; report name + URL surfaced from parsed TMDL lineage (Sunny
verified the URL resolves to the right dashboard); verdict answered,
evidence verified.

- **FIND W4 (display, DEMO-REQUIRED): report links render as raw
  markdown, not hyperlinks.** Same root cause as W3(b): the
  commentary block is plain text, so "[View Report](https://…)"
  shows as source. Remedy: render commentary as SANITIZED markdown
  (links clickable, new tab; bold/lists render). Display-only.
  Priority note: VO-3's demo beat is "ending with a live link to the
  dashboard" — this must be clickable before capture day.

## Q4 — "what's the base population of ED Sepsis Screening Dashboard"

**VERDICT: REJECTED (register), content correct.** One round, right
step record (Base_Pop), honest content — but the commentary pasted
the SQL fragment verbatim and voiced the stored description's join
mechanics, for a question that never asked for SQL. AIVIA's default
audience is non-technical (Sunny's standing rule).

- **FIND W5 (register violation — the stochastic-rule class, again):**
  SYSTEM_PROMPT rule 5 ALREADY SAYS "Translate SQL into business
  language in answers; show raw SQL only when asked" — the model
  ignored it. Rule-in-prompt ≠ enforcement (the M5 lesson applied to
  register). Two sources, two remedies:
  (a) SQL fence in commentary → render COLLAPSED behind a "show SQL"
  expander, unconditionally (display-shaped, M4-clean — no lexicon,
  no intent guessing, no pin change; sql_request UX unaffected).
  (b) The join-clause bullets are the STORED step description's
  mechanics tail — a description-pipeline register question. Depth
  per the drilldown ruling means CRITERIA words (codes, thresholds,
  time windows), never join plumbing; the business lead + criteria
  is the voice. Data-layer design item, adjacent to the v6 scope
  rule — record, design deliberately, don't band-aid.
  **FIXTURE FIRST (protocol):** register family — default-audience
  question, answer must contain no SQL code fence; sql_request
  questions exempt. Structural check (fence detection), not a
  lexicon.

## Q5 — "is another metric using the same base population?" (anaphora + sameness)

**VERDICT: FAILED — HONESTY CLASS (the walk's build-stopper find).**
Trail was honest to the last step: R6 lineage(column='Base_Pop') → 0
rows, honest-empty, correctly stamped; R7 census mentions-scan → 2
rows, honestly scoped as MENTIONS. Then the commentary declared "Yes,
two other metrics use the same base population" — a sameness claim
the displayed evidence never made. Verdict quoted R7's mention-scope
headline as evidence for an equivalence claim: quote valid, claim
beyond scope. Calibration-3 type: claim beyond declared evidence =
DISHONEST. Gate blind spot: invented-number and quote-validity checks
pass; no scope-vs-claim check exists.

**Ground truth (review session, from seed source):** the claim is
FALSE, not merely unproven — NINE procs build #Base_Pop; the three
compared (USP_ED_Sepsis / USP_IP_SEPSIS / USP_IP_SepsisPatientDates)
define materially different populations (arrival-based ED encounters
vs department-day expansion with PM denominators vs per-shift
expansion rows). Same name, different logic — Sunny's predicted false
positive, live. The inverse (different name, same logic) is equally
invisible to mention scans. Also: "2" reflects description-mentions
only; the step-name universe is 9.

- **FIND W6 (honesty corpse → FIXTURE FIRST, per the law):** sameness
  question answered from mention evidence. Fixture family: sameness —
  "is another metric using the same base population?" passes ONLY via
  (a) a compare-op verdict on screen, or (b) an honest "step-name
  matches found; logic NOT compared." Any equivalence claim without a
  compare result types dishonest.
- **FIND W7 (capability + gate design):** op_compare (ADR 0036
  kernels) IS an engine tool and was never called. Remedy directions,
  M4-bounds respected (no lexicons): (1) data-shaped stamp — when a
  census/mention scan matches a phrase that is a STEP name, the
  headline stamps "N procs have a step NAMED 'X' — a name match is
  not logic sameness; compare for a verdict" (proven bridge-stamp
  pattern: stamp the caveat, gate its presence); (2) census for
  step-name phrases should surface the step-name universe (9), not
  only description mentions; (3) grader: the sameness fixture above.
  DEMO IMPACT: this question shape IS the VO-4 drift beat (the input
  box placeholder is "are all definitions of Base_Pop_Severe_ED_Scores
  the same?") — the workbench compare path must be reliable before
  capture; add the drift question to the workbench QA gate.

## Q6 — "Is ED Sepsis (Regulatory)'s base population different from ED Sepsis Screening's?"

**VERDICT: FAILED — W6 class, difference direction (answer TRUE by
luck, method wrong).** Ground truth verified in source: the two
Base_Pop projections genuinely differ (regulatory: disposition/
location/age-in-days/date-stamp; screening: triage/demographics). But
the model declared "different" from DESCRIPTIONS, never calling
compare — descriptions can differ while logic matches, so the method
fails both directions. Trail quality improved vs Q5: retrieved BOTH
full records, anti-flail correctly refused a repeated lineage call.
Corpse #2 for the sameness fixture family (covers same-claim AND
different-claim: both require a compare verdict or the honest
caveat).

- **FIND W8 (Sunny's directive → the systematic design): GOVERNANCE
  RED-FLAG SWEEP — a pipeline artifact, and the data-shaped fix for
  W6/W7.** Governance over thousands of SQL files means misnomers
  and conflicting/duplicated definitions at scale; per-question
  vigilance cannot police them. Three flag classes from existing
  machinery (normalized fragments, content hashes, twin verdicts):
  (1) MISNOMERS — same step name, differing hashes across procs
  ("Base_Pop: 9 procs, N distinct logics");
  (2) DUPLICATES/TWINS — same hash under different names;
  (3) CONFLICTING COUSINS — near-name families with divergent hashes.
  Output: red-flags table, error-contract discipline (each row
  carries its drill query); surfaced in the admin dashboard AND as an
  agent-readable data surface, so sameness questions become
  single-row reads of machine verdicts (ADR 0020 — closes W6
  systematically, no prompt rules). Registry rows per ADR 0052;
  fixtures first. DEMO: generalizes the VO-4 drift beat to
  estate-wide ("N red flags found").

## Q7 — "in ED Sepsis Screening metric, how is a patient diagnosed with severe sepsis" (drilldown)

**VERDICT: FAILED — capability, the STANDING M2 residual, live
specimen (no new find; confirms the open design item).** One round,
correct record, headline stamped "256 decision sites — the top 12 are
ON THIS RECORD." Commentary answered from the summary, claimed the
criteria "aren't individually detailed in the current results" —
FALSE, contradicting the stamp (the typed stamp-contradiction signal,
telemetry's counter class) — and filed verdict=answered while
simultaneously saying further examination would be necessary. Under
the suite's grain gate this is the 0.33 drilldown failure, witnessed
live. Calibration-3 type: DUMB (partial facts, humble-but-blind),
not dishonest; the gate rightly did not floor it.

Specimen value for HANDOFF_M2_DECISION_EVIDENCE: retrieval is NOT
the problem (sites were inline on the displayed record); evidence
PRESENTATION is. Also for gate design: "answered + admits
insufficiency + stamp says material is on screen" is a mechanically
recognizable self-contradiction the continuation currently cannot
act on (verdict said answered). Demo note: keep this question shape
off camera until M2 lands — as already flagged in
REVIEW_DEMO_READINESS.

## Q8 — "how many steps does it have" (anaphora + step count)

**VERDICT: PASS (clean).** Pronoun resolved across the turn boundary
(it = ED Sepsis Screening), one round, 43 steps from the machine
stamp, concise (no row dump — the fold lesson holding), verdict
evidence-verified. Nits for the display batch: verdict quotes the
headline under its prior-turn label ("R12") while based_on says R13
(citation label mismatch, W3 family); re-retrieved a record already
on screen instead of answering from displayed history (W1
rounds-beyond-sufficient shape).

---

# SESSION TALLY (8 questions, Sunny live, 2026-08-23)

- **PASS: 4** — census (floored honestly), topical ED (the resurrected
  fixture), definition (with report link), anaphora step-count.
- **REJECTED (register): 1** — Q4 SQL-in-answer (rule 5 ignored; the
  stochastic-rule class).
- **FAILED (honesty class): 2** — Q5/Q6 sameness claims without a
  compare verdict (fixture family defined; Q6's answer true by luck).
- **FAILED (standing capability): 1** — Q7 drilldown, the known M2
  humble-but-blind residual, live specimen captured.
- **Honesty gate live saves: 1** (Q1 invented '9' floored on screen).
- **New directive: W8** governance red-flag sweep (misnomers /
  duplicates / conflicting cousins) — the data-shaped systematic
  answer to W6/W7 and the estate-wide generalization of the VO-4
  drift beat.
- Walk steps still open for a future session: pointer chase, honest
  wall, deliberate misname, surprise round.

Work order: HANDOFF_WALK_1562_FINDS.md.
