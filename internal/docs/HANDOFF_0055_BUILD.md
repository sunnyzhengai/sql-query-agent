# Handoff — ADR 0055 build: the designed shape corpus (overnight, both phases)

**From:** review session, 2026-08-24 (Sunny asleep; her rulings are
in the ADR; anything beyond them gets PARKED, never decided). **To:**
dev session. **Mode: build order — the ADR is the spec.**

## Sequencing (strict)

1. **FIRST: the caption batch already queued in HANDOFF_0054_BUILD**
   — W15 (compare verdict word + echo duty, PRE-CAPTURE), W17
   (column-lineage distinct counts — ECHO, mandatory), W16 (stamp
   folding), F1 (error-tile collapse). Small, and W17 is
   law-mandatory; do not let the shapes build leapfrog it.
2. Then ADR 0055, Phase 1 → Phase 2, one overnight run.
3. The three ops finds (shortcut create-then-verify, org_config
   referential integrity, probe-eh rename) slot wherever they fit;
   the rename can wait for Sunny's daytime (workspace UI).

## The 0055 build — key requirements beyond the ADR text

- **Palette separation is load-bearing:** cell definitions are
  domain-independent; names come from a palette file. PALETTE RULED
  BY SUNNY: **diabetic diagnosis cohort analytics** (fully
  synthetic). Suggested vocabulary — tables: PATIENTS, ENCOUNTERS,
  LAB_RESULTS, DIAGNOSIS_CODES, MEDICATION_ORDERS, PROBLEM_LIST;
  metrics/procs: "Diabetic Patients (Diagnosis Codes)" vs "Diabetic
  Patients (Lab Criteria)" — the same-concept-different-path
  conflict twin (ICD E11.x vs HbA1c >= 6.5 vs metformin/insulin
  orders vs problem list — each path is a REAL clinical
  identification route, so shape cells read as true clinical
  governance, not contrivance); "Diabetes Registry" + "(Legacy v1)"
  cousins; "Controlled Diabetes Rate", "A1c Testing Compliance";
  CTE misnomer seed: Base_Cohort / Diabetic_Pop across procs, each
  built by a different path. Retail VETOED; no retail or SaaS
  vocabulary. A palette swap must be a data-file change, no code.
- **Isolation constraint (Sunny's ruling 3):** the 28-file realism
  store, its census (28), and every existing oracle remain
  UNTOUCHED. Shapes load as an isolated source/catalog the demo can
  switch to; design the mechanism (separate config profile /
  source set / store) and record it. CI runs shapes through the
  recorded-fixture path — no tenant required for the suite.
- **Oracles by construction:** shape_manifest.json carries expected
  flags/edges/verdicts per cell; the `shapes` suite family asserts
  manifest vs actual end-to-end (parse → graph → sweep → ask). The
  D2 boundary cell (semantically-same, syntactically-different)
  asserts DISCLOSURE ("differs by normalized hash"), never
  detection.
- **Echo Law from birth:** every new query/op/stamp ships with L0 +
  smoke case + live probe; matrix registry totality in CI (a cell
  is instantiated ⊎ excluded-with-reason).
- Pin discipline as always; any tool change is a conscious bump.

## Acceptance (for Sunny's morning read)

- `internal/docs/SHAPES_GAPCHECK.md`: the cell matrix (instantiated
  vs excluded-with-reason), and per-cell expected vs actual from a
  full local run — every planted sin found, none invented, boundary
  cells disclosed honestly.
- Full suite green incl. the new `shapes` family; ruff clean;
  honesty 1.00 standing law.
- A short DEMO NOTE: the 3 most demoable cells (e.g., the Active
  Users conflict, the Churn Legacy cousin, the Base_Users misnomer)
  with the question to ask and the expected on-screen answer.

## PARKED for Sunny (morning)

- Palette veto/rename (swap is cheap by construction).
- Whether the shape store gets its own tenant load before capture
  (the demo-switch mechanism dev designs tonight determines the
  runbook).

## REVIEW VERDICT (2026-08-25): APPROVED — both orders closed

Independently verified: 1,076 green + ruff clean (review's own run);
SHAPES_GAPCHECK well-formed — 26/26 instantiated cells PASS, 5
exclusions each with defensible recorded reasons (S8/S9 = honest v1
sweep-scope follow-ups; M7/M8 non-additive; R6 ask-surface, covered
by walk + live leg); dimension totality CI-asserted; deterministic
regeneration. Committed 27dbfcd. Remaining are Sunny's two parked
calls: palette confirmation and tenant-load-before-capture (the
demo ask-leg rides on it).

## RULINGS UPDATE (Sunny, 2026-08-25 morning)

1. **Palette CONFIRMED: diabetic.** Clinical truth layer to be
   blessed by Sunny (review drafted the five diagnosis paths — ICD
   E08–E13, problem list, labs incl. HbA1c ≥ 6.5, medications with
   the metformin/prediabetes-PCOS over-count caveat, gestational
   O24.4x exclusion nuance); once blessed, dev applies as PALETTE
   v2 — data-file change only, cells and oracles unchanged.
2. **THE DEMO RUNS ON THE SHAPE QUESTIONS** (M1/M2/S4 + the shape
   store) — sepsis retires from camera, remains the realism/
   regression cohort. Consequences: (a) tenant-load of the shape
   store is now REQUIRED pre-capture (the _shapes profile becomes a
   runbook item); (b) OPEN GAP for Sunny: the report layer — the
   shape corpus has no semantic model/report; the clickable-link
   and write-back demo beats need a small "Diabetes Registry
   Dashboard" (sepsis pattern), or those beats trim. Review
   recommends building it.

## RESULTS (dev appends)

### 2026-08-25 — BOTH PHASES BUILT overnight; 26/26 cells pass; SHAPES_GAPCHECK.md + demo note delivered
**Phase 0 (sequencing note 1): the caption batch was already shipped**
(W15/W16/W17/F1 — recorded in HANDOFF_0054_BUILD RESULTS) before any
shapes work began.
**The corpus** (diabetic-diagnosis palette, Sunny's ruling; palette =
data/shapes/palette_diabetes.json — swap re-skins everything, no
code): 22 generated SQL files, 31 matrix cells — 26 instantiated, 5
excluded-with-reason (step-grain cousins, schema-object scope, M7/M8
duplicate-coverage exclusions, R6 ask-leg) — every ratified dimension
value covered (CI totality test).
**Full local pipeline run (REAL ScriptDom parse → graph → sweep):
26/26 instantiated cells PASS — every planted sin found, none
invented, controls clean:** Base_Cohort misnomer (2 logics, INFO),
Active Diabetic Patients metric CONFLICT + compare DIFFERS, Diabetes
Registry Legacy-v1 cousin CONFLICT, Controlled-Diabetes cousin INFO
(aligned), roster/DM-list duplicates + compare IDENTICAL, ws/case and
CRLF normalization controls unflagged, the S3 D2-boundary disclosed
(normalized-hash difference, no semantic claim), all five D4
reference forms (incl. the temp-projection chase minting via_step and
the ambiguous bare ref dropping), chains linear/diamond/recursive
building clean, dynamic SQL classified no_query (the declared path),
PHI literal yielding a redact finding.
**Iteration finds while building (recorded):** (a) my ref-forms temp
initially reused #Base_Cohort and the S4 cell caught the third
member — the matrix caught its own author; (b) R5's first expectation
was over-broad (qualified join refs legitimately mint; the DROP
bucket is the assertion); (c) dynamic-SQL-only procs RAISE from
parse_sql and the 200 classifier types them no_query — the checker
now mirrors the pipeline grain (classified = declared, UNCLASSIFIED
= defect).
**Deliverables:** src/shapes/{generator,matrix,checker}.py;
devtools/generate_shapes.py (corpus of record under
data/shapes/generated/, regen byte-identical, CI-asserted);
devtools/shapes_gapcheck.py → internal/docs/SHAPES_GAPCHECK.md
(matrix, expected-vs-actual, dimension coverage, DEMO NOTE with the
three demoable cells: M1 conflict / M2 Legacy cousin / S4 Base_Cohort
misnomer, each with the question and expected on-screen answer);
tests/shapes/test_shapes.py (12 tests: totality, corpus-of-record,
L0 compose styles, end-to-end, isolation, seeded property leg —
seeded rng, spec:E2); walk addendum (field finds cite cell ids); ADR
0055 registry entry filled + TRACE_MAP regenerated.
**Isolation (Sunny's ruling 3) honored and designed:** the realism
corpus, its census, and every existing oracle are untouched (CI
asserts zero metric-id collision); shapes run locally through the
checker. The demo-switch mechanism DESIGN: a source profile = an
org_config variant with _shapes-suffixed lakehouse tables (+ its own
catalog tables); one small notebook change (config path as a run
parameter, default unchanged) makes any chain run against either
profile. EXECUTION PARKED with Sunny's tenant-load decision — if she
rules pre-capture load, dev wires the param + a
100_install-style profile check in that order.
**PARKED for Sunny (morning):** palette veto/rename; tenant load
pre-capture vs post; the ask-leg (R6 + the three demo questions
live) rides the tenant-load ruling.
Gates: full suite **1,076 passed** + 5 xfailed, ruff clean; no
engine/ops/tools changes in the shapes build (no pin motion, no
smoke-relevant surface touched — the harness ran green in the
caption batch that preceded it).

### 2026-08-25 — ARMED ORDER EXPANDED (Sunny's demo law): palette v2 + graph-native clusters fire TOGETHER on the scenario red-pen
Acknowledged and armed; nothing builds until the red-pen lands.
Scope on trigger (SPHERE.md "Clusters are nodes" is the spec):
1. **Palette v2** per the red-penned SHAPES_SCENARIOS (D7 grain +
   N-scenarios + personas; data-file change, existing cells stable).
2. **Clusters go graph-native as sole flag truth:** the sweep emits
   reified nodes — name_cluster → logic_group (the content-hash
   partition) → member_of edges — deterministic ids (E2), 0052
   registry rows, deterministic detection only (fold-name,
   content-hash, token containment; never stochastic).
3. **Re-point census(flag)/retrieve(flag) to graph traversal**; the
   shape corpus is the safety net — its 26 cells' flag expectations
   must pass UNCHANGED through the re-pointed path before anything
   retires (the checker asserts against the new truth).
4. **Consumer census on gov_red_flags**, then re-point-or-justify
   each declared consumer; retire table + contract if the list
   empties. Pre-census reading of the declared list: data_agent
   (instructions SQL → graph_nodes export or a generated view), the
   engine's GOV_* queries (→ traversal), the flags suite oracle
   (→ graph query), the Eventhouse shortcut (retire with the table).
READINESS NOTE (design tension to resolve at build, flagged now):
single-writer law — graph_nodes/graph_edges are owned by
300_build_graph; cluster nodes joining the graph means either the
sweep folds INTO 300 (320 retires with its table) or the graph
tables gain a second declared writer. Leaning fold-into-300 (one
writer, one truth); decide against SPHERE + the notebook contract
when the order fires. Echo Law from birth on every new
query/op/stamp.

## PALETTE V2 + GRAPH-NATIVE CLUSTERS — the combined pre-capture order (2026-08-25, Sunny's full confirmation)

**Specs of record:** internal/docs/SHAPES_SCENARIOS.md (CONFIRMED IN
FULL — shapes, lego library, U1–U12, personas, D7 grain ratified)
and docs/architecture/SPHERE.md ("Clusters are nodes" + the demo
law). One order, two payloads, both pre-capture:

**Payload 1 — palette v2 (the shapes v2 corpus):**
- New shapes: Codeset drift, Path divergence, Extension (step-grain
  core matching), Grain (D7 — new dimension, 2–3 cells). Existing
  cells re-skin; new cells only for these.
- The lego library becomes the foundation vocabulary (tables +
  join paths per persona, incl. APPOINTMENTS and
  PATIENT_PCP_ASSIGNMENT supports; codesets as foundation reference
  tables seeding the future vocabulary-flag class).
- Use cases U1–U12 + the two silent controls, personas as
  steward/developer metadata (Dr. Peterson, Dr. Sullivan, ED
  medical director, OBGyn, Finance analyst, Quality & Registry
  team).
- Manifest expectations assert CANONICAL OUTCOMES per cell (concept
  count, claim structure, invited disposition class), not just
  flags.

**Payload 2 — graph-native clusters (the demo law: never capture a
condemned surface):**
- Sweep emits reified cluster nodes: name_cluster → logic_group →
  member_of edges; deterministic detection only; 0052 registry
  rows; receipts on the cluster nodes.
- Flag census/retrieve re-point to graph traversal (storage change;
  if any tool DESCRIPTION text changes, that is a conscious pin
  bump, recorded).
- Consumer census on gov_red_flags NOW: re-point every declared
  consumer to the graph (cluster nodes are KQL-queryable via the
  graph_nodes export) or justify a generated view; zero consumers →
  retire contract + table. Record the outcome.

**Acceptance:** SHAPES_GAPCHECK v2 (matrix incl. D7 + new shapes,
expected-vs-actual, canonical outcomes) + updated DEMO NOTE (likely
best cells: U9 codeset drift, U6 billing-vs-clinical, U12 grain
twin); full suite green + ruff; honesty 1.00 standing; Echo Law from
birth on every new query/op/stamp; deterministic regeneration
byte-identical.

## RESULTS v2 (dev appends)

## PAYLOAD 3 — the Diabetes Registry Dashboard (Sunny's ruling, 2026-08-25: BUILD)

Closes the report-layer gap for the demo (clickable-link + write-back
beats). Follow the ED Sepsis Screening Dashboard pattern exactly:

1. Author as GIT WORKSPACE ITEMS (the sepsis precedent): a
   "Diabetes Registry Dashboard" semantic model (TMDL) executing the
   shape store's Registry proc (U7 — the Quality team's composite,
   the certified-official candidate), displayName matching the model
   name, plus a minimal report bound to it. Keep visuals minimal but
   plausible: registry cohort count, trend, and a by-path breakdown
   (dx/lab/med) — the by-path visual foreshadows the path-divergence
   demo beat.
2. **Report description field left EMPTY** — it is the write-back
   beat's stage (the demo publishes the certified definition onto
   it live).
3. Wire into the _shapes config profile so 060 ingests it: TMDL
   links parsed → the report joins the shape graph → report_name +
   URL land on the Registry metric record → the clickable link
   appears in answers (the W4 machinery).
4. Sequencing: after/with palette v2 (needs the shape store's proc
   names), before the tenant load. Sunny's tenant steps at the
   tail: workspace update-from-git, open the report once to verify
   it renders, confirm description still empty.
5. Acceptance: the pointer-chase question ("which report is built on
   the Diabetes Registry, and what else does that report use?")
   answers with the dashboard + its TMDL links — the walk step-3
   shape, now on the demo corpus.

## GO + BUILD-TIME RULINGS (review session, 2026-08-25 night — the file IS the relay)

- **GO.** Sunny's red-pen is COMPLETE (SHAPES_SCENARIOS confirmed in
  full: lego library, U1–U12, personas, D7 grain ratified). The
  fused order fires: payload 1 (palette v2) + payload 2
  (graph-native clusters + consumer census) + payload 3 (Diabetes
  Registry Dashboard).
- **Single-writer tension RULED: fold-into-300.** Clusters are
  derived structures — the ADR 0018 precedent (closures/twins built
  in the graph build); the sweep has no independent cadence.
  320_red_flag_sweep retires with its table (chain shortens to
  300→400…; runbook + installation guide + scheduled-pipeline order
  update; conservation asserts move into 300's postconditions + the
  live audit). The demo law smiles: no condemned notebook on camera.
- **Checker-as-migration-gate ENDORSED** as you framed it: the 26
  cells' flag expectations pass unchanged through the re-pointed
  traversal before the table retires.
- **Consumer census reading endorsed** (agent SQL / engine GOV_*
  queries / flags suite oracle / Eventhouse shortcut). Note: the
  agent-instructions re-point = one more updateDefinition → a
  SUNNY PUBLISH step at the runbook tail; write the runbook
  accordingly.
- Acceptance unchanged: SHAPES_GAPCHECK v2 with canonical outcomes,
  updated demo note, suite green + ruff, honesty 1.00, Echo Law
  from birth, byte-identical regeneration.
- Also new on dev's horizon (context, not order): ADR 0058 DRAFT
  (self-service contracts, contracts-first for Pro — builds with
  Pro, awaiting Sunny's ratification) and REVIEWER_DECK_THEMES.
