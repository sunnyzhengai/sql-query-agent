# TESTPLAN 0062 — machine acceptance BEFORE Sunny's glass

**Review-authored 2026-08-29 per Sunny's directive: design tests,
test machine-side (dev implements + runs; review re-runs and runs
the headless battery), and only THEN Sunny re-walks — her glass
time is for clarity judgment, never for what a test could catch.**

Every question below uses Sunny's REAL phrasings from the walks
(the flywheel's first harvest). Dev may add cases; dev may not
remove any.

## A. De-typing proof (the ruling's teeth)

- A1: the shape-recognition module/function is DELETED — its
  import fails; grep-level absence of the whole-question template.
- A2: EVERY question in batteries B–E produces a CARD response
  (or the no-match card) — zero silent engine routes. Assert the
  response type, not the content.
- A3: behavior varies ONLY with which words ground to which nodes
  — two same-shape questions with different entities produce
  different groundings, same mechanics; no code path branches on
  question classification. (Sunny's own acceptance sentence.)

## B. Extraction + grounding (per question: expected entities, ids, relation words)

- B1 "Are all the Diabetic codesets defined the same?" →
  entities: Diabetic Codeset ×2 (both carriers anchor); relation:
  same → compare selector.
- B2 "are these 3 metrics using the same definition: High ED
  Utilizers Without PCP High ED Utilizers (reporting.USP_High_ED_
  Utilizers) High ED Utilizers (reports.USP_High_ED_Utilizers)" →
  3 entities incl. parenthetical ids; same → compare.
- B3 "what does Active Diabetic Patients (reporting.USP_Active_
  Diabetics) use to define the patient cohort" → 1 entity exact;
  relation: define/criteria → definition selector.
- B4 "which metrics use ED_ENCOUNTERS?" (Sunny's canonical
  example) → kind: metrics; entity: table ED_ENCOUNTERS (verify
  actual table name in store); relation: use → reads/lineage
  selector.
- B5 "What governance red flags exist for Diabetic Patients?" →
  entity: Diabetic Patients (family); relation: red flags → flag
  selector.
- B6 "Which certified metrics feed the Diabetes Registry
  dashboard?" → kind: metrics; entity: dashboard; relation:
  feed → lineage-to-report selector.
- B7 "is there another way of defining diabetic patient cohort
  other than the logic in the Dx_Path, Lab_Path, Med_Path…" →
  entities incl. STEP names (Lab_Path grounds to the step node —
  the old Lab_Path failure becomes a named test); relation:
  another way → variants selector.
- B8 bare entity, no relation word: "Diabetic Codeset" → card
  proposes the DEFAULT MAP ("what's connected"). Never an error,
  never engine.
- B9 zero-entity: "what is the weather today" → no-match card:
  "no catalog match" + rephrase + developer door + engine button.
- B10 row-data: "How many patients are currently in the Diabetic
  Patients cohort?" → grounding fine; proposal = policy refusal
  (RW-11 wording) + definition offer. No wandering.

## C. Loop mechanics

- C1 prune-to-empty → typed parse_refusal; nothing executes.
- C2 prune 15 matches down to 2 → composed plan covers exactly
  the 2; capture records the prunes as decisions.
- C3 confirm on B1 → retrieve×2 + compare; DIFFERS + "+ E11.80"
  machine line (the standing oracle).
- C4 developer door on EVERY card (assert presence in B1–B10
  responses); /api/escalate captures the 0056 deny-shape event
  with matched ids + note.
- C5 "answer without the planner" present and functional (the
  ONLY road to the engine).

## D. Latency (RW-18 — measured, not guessed; budgets are the acceptance)

- D1 card SKELETON first byte < 1s after submit (streaming
  contract: skeleton precedes grounding completion).
- D2 per-entity grounding queries issued CONCURRENTLY (mock store
  asserts overlap).
- D3 full card (all matches) < 8s on the live shapes store;
  post-confirm first op status < 2s. Regression-guarded with
  generous CI margins on the mock; LIVE numbers measured and
  RECORDED in RESULTS (parse-call ms / store-queries ms /
  render ms).

## E. Headless glass battery (review runs this AFTER dev's green, BEFORE Sunny)

The walk-runner: B1–B10 + the six DEMO_SCRIPT V2 QA questions
executed against the LIVE shapes store via the API; per question
record: card contents (matches, proposal, doors), post-confirm
verdict, latency split. Review diffs against this plan's
expectations and posts the transcript + verdict table in
WALK_VERDICTS_SHAPES.md. Sunny re-walks ONLY after review's
battery is green — and then only the beats she wants to feel on
glass.

## Starting relation lexicon (small, closed, word-grain — grows by flywheel only)

same/different/identical/match → compare · use/read/depend →
lineage(reads) · feed/impact → lineage(to-report) · flag/wrong/
issue/conflict → flags · define/criteria/logic → definition ·
variant/way/version → family census + flags · how many/count/rows
→ data-policy refusal. (No entry = default map. Entries are
words, never question shapes.)
