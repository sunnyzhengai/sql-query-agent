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

### 2026-08-27 — FUSED BUILD DELIVERED, all three payloads (this is the section of record; dated build logs live under the GO section below — the mislanding that caused the first deadlock is fixed)

**Payload 1 — palette v2: DONE 08-26** (shipped with 1.58.0; log:
"FUSED ORDER BUILT" below). Lego library + U1–U12 + personas + D7
grain_shift live; 39 instantiated cells / 39 PASS / 5
excluded-with-reason; byte-identical regeneration CI-pinned.
SHAPES_GAPCHECK.md v2 with canonical outcomes + DEMO NOTE v2 (U9
codeset drift · U6/PD1 cousin fight · U12 grain fight).

**Payload 2 — graph-native clusters: DONE 08-26/27** (logs below +
HANDOFF entries of 08-26). Fold-into-300 as ruled; 320 + its table
retired, consumer census closed zero orphans; checker ran as the
migration gate; live: 83 cluster nodes = the 83 pre-migration
flags, census(flag) 83 by pure traversal; 0059 topology leg green.
Sunny's tenant halves done 08-27 (1.58.1 env published, dead
shortcut removed); instructions injected 08-26 — her Publish
spot-check is the last click.

**Payload 3 — Diabetes Registry Dashboard: DONE 08-27.**
- Git items authored on the sepsis pattern exactly: `Diabetes
  Registry Dashboard.SemanticModel` (TMDL; 'Registry Cohort' =
  `EXEC reporting.USP_DM_Registry_Composite` — U7, the
  certified-official candidate) + `.Report` (4 visuals: title,
  cohort-count card, enrollment trend line, **by-path dx/lab/med
  columnChart** — the path-divergence foreshadow). Two supporting
  tables are inline SQL over DM_REGISTRY / the three path tables —
  parsed as disclosed InlineSQL sources, deliberately unlinked.
- **Description EMPTY and mechanically held** (ruling item 2): a
  shapes test fails if anyone fills it before the write-back beat.
- Endpoint hygiene: DemoSqlServer/DemoSqlDatabase placeholder
  parameters (sepsis precedent), test-pinned.
- **The report joins the shape graph through the REAL pipeline**:
  checker's run_corpus now collects the dashboard's TMDL
  (FolderTmdlSource → semantic_models_step → build_graph_step) —
  `report:DIABETES REGISTRY DASHBOARD --report_to_canonical-->
  canonical:reporting.USP_DM_Registry_Composite`; topology clean
  (anchored via U7, NOT consumption-isolated). TMDL-derived metric
  name deliberately not passed — the palette stays the one name
  writer ("Diabetes Registry (Composite)").
- Acceptance shape pinned in tests/shapes (4 new tests); gapcheck
  gained the Report-layer section. The live pointer-chase question
  fires after the tenant load (Sunny's steps, ruling item 4:
  update-from-git, set the two SQL parameters, open once to verify
  render, confirm description still empty).

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

### 2026-08-26 — FUSED ORDER BUILT: graph-native clusters + palette v2 (release 1.58.0)
**Clusters are nodes — DONE (fold-into-300, as ruled):**
- The sweep runs INSIDE build_graph_step; verdicts reify as
  GOVERNANCE-layer nodes: `cluster:` (name_cluster, flag fields +
  disposition as properties) → `loggroup:` (one per distinct content
  key) → `member_of` edges from the actual org nodes. Deterministic
  ids; reification conservation asserted (one cluster node per
  verdict); dispositions fold onto node properties each run.
- **320_red_flag_sweep RETIRED** (notebook dir, registry entry,
  installation guide, scheduled-pipeline order) and **gov_red_flags
  RETIRED** (contract removed; gov_flag_dispositions stays planned,
  reader now 300). LPG export: governance layer + member_of =
  counted exclusions (the decision-layer pattern; conservation
  exact). New D7 flag class `grain_shift` (structural DISTINCT-vs-
  row detection, no column lexicon).
- **Consumer census CLOSED — the table retires with zero orphans:**
  engine ops → traversal queries (GOV_* rewritten over
  graph_nodes/graph_edges; retrieve walks member_of 2-hop; ids now
  `cluster:` — census remediation names the 1.58 rerun); suite
  oracle + fixture probe → cluster queries; agent instructions →
  graph_nodes JSON_VALUE (+ /redflags rewritten); Eventhouse
  gov_red_flags shortcut → retire with the table (Sunny deletes it
  in the KQL DB, or dev via API on her go).
- **The checker WAS the migration gate, as framed:** every flag
  expectation now ALSO asserts its cluster node, its logic_group
  count (== distinct logics), and its member-edge count (== members)
  — all 44 cells passed through the re-pointed truth.
**Palette v2 — DONE (SHAPES_SCENARIOS confirmed in full):**
- Lego tables + 5 foundation codesets + personas (steward metadata,
  no auth) + scenario procs U1–U12; 38 SQL files, 44 cells (39
  instantiated / 5 excluded-with-reason), all dimension values
  covered incl. D7.
- The corpus told the truth about its author twice more: template
  reuse across v1 single-CTE procs surfaced as REAL duplicate
  clusters (kept — deliberate truth, documented); the Base_Cohort
  cluster grew to 11 members / 9 logics (U10 by construction).
- Headline structures live: "Diabetic Patients" cousin family **10
  members / 10 distinct logics** (the governed-plurality cluster);
  codeset drift misnomer with the diff pinpointing E11.80; U12
  grain_shift + misnomer pair; U11 doppelgänger + compare IDENTICAL;
  U1 extension with shared step core proven equal.
- Canonical outcomes asserted per the tie-in (consolidate→duplicate,
  link→cousin, repair→pinpointing diff, derive→shared core;
  differentiate/rest annotated).
**Deliverables:** SHAPES_GAPCHECK.md regenerated (v2: 39/39 PASS,
canonical outcomes, DEMO NOTE v2 = U9 codeset drift / U6+PD1
billing-vs-clinical family / U12 grain fight, each with question +
expected screen). Release 1.58.0 (wheel built, env item updated,
CHANGELOG, release-consistency green).
**Gates:** suite 1,076 passed + 5 xfailed, ruff clean, docs
regenerated. **Live smoke: BLOCKED by paused capacity** (Kusto host
unresolvable — tenant state, not code); offline dispatch-contract
legs green; a background watch runs the harness the moment the
capacity resumes and its result appends here. NOT SHIPPED TO TENANT
until that leg is green — the law holds.

## RUNBOOK TAIL (Sunny — the 1.58.0 tenant pass)
1. Resume capacity (the smoke watch then completes on its own).
2. Environment → Update from git → confirm
   sql_query_agent-1.58.0-py3-none-any.whl → Publish.
3. Workspace → Update from git (300 updated; the 320 item DELETES on
   sync — expected).
4. Dev fires the chain on your go: **300 → 400 → 500 → 600 → 610 →
   700 → 800** (no 320 — the sweep is inside 300).
5. KQL database → delete the `gov_red_flags` shortcut (its table is
   gone; the clusters ride the existing graph_nodes shortcut).
6. Dev re-injects the updated agent instructions; you hard-refresh,
   spot-check "/redflags" and "what governance red flags exist?",
   then **Publish** (the added step from the instructions re-point).

### 2026-08-26 — LIVE SMOKE GREEN + one pre-ship find killed on the spot
Capacity resumed (dev, via ARM); the armed watch ran the harness:
all 9 cases green through the real dispatch — INCLUDING a fresh
corpse the harness caught BEFORE the tenant could: on the pre-1.58
store, census(flag) answered a bare "0 flags" — but that store
merely PREDATES the graph-native sweep. Pre-sweep absence read as
proven-zero: the W13b false-empty class reborn on the flag surface.
Mechanism, same session (Echo Law): every 300 build writes a
`govmeta:sweep` RECEIPT node (swept/flagged/clean + run_at); a
zero-cluster census with NO receipt now REFUSES with the named
remediation ("absence of clusters is not proven zero flags"); with
the receipt, the honest zero cites it in the stamped universe. Smoke
case asserts all three honest states; +2 L0 tests. Re-run live:
"store predates the graph-native sweep — named remediation
verified" — the guard working on the exact store that exposed it.
ADR 0059 (topology axioms, review DRAFT) registered sanctioned.
FINAL GATES: suite 1,078 passed + 5 xfailed, ruff clean, live smoke
green. **FUSED ORDER COMPLETE** — awaiting Sunny's runbook-tail
steps (env publish 1.58.0, workspace sync) and her "go" for the
7-notebook chain.

## NEXT ORDER AFTER THE FUSED BUILD — B3 step dep-chains (Sunny's green light, 2026-08-25, now recorded)

transform_to_transform enters the ask surface: "what feeds this
step / what does this step feed." The registry's "PARKED BEHIND
ROUND 4" text is STALE — update the row to reachable when built.
Echo Law from birth (op semantics inherit the token-matching law;
smoke case; live probe; suite family with store-derived oracle).
Pin bump if tool schema changes — conscious, recorded. Small order;
sequence after the fused build's acceptance, before the re-walk (so
walk section B grades against it).

## RECORDED DIRECTION — the finder-coverage contract (2026-08-26; timing = Sunny's call)

Vectorization ruling (Sunny's question, review's audit): edges and
structural properties are NEVER embedded — structure is exact,
queried by the algebra (vectorizing relations = approximate answers
to exact questions, the Round-4 competitor disease). The finder's
TEXT corpus grows instead: today it embeds metrics/steps/reports/
measures/terms (name+description); NOT embedded = the decision
layer (1,831 sites' criteria text — meaning-entry for "which
metrics care about antibiotic timing", also relevant to the
standing M2/drilldown item) and the technical layer (79 tables +
3,946 columns with dictionary descriptions — "where do we use
patient age"). Mechanism, build-first: a FINDER-COVERAGE CONTRACT —
0052 pattern over the semantic index (every node kind embedded ⊎
excluded-with-reason; registry row; CI totality); every new
semantic surface unions with exact/containment at birth (the
bridge law); PHI gate on decision text; complete:false forever;
embeddings never in a justification. Sequencing suggestion:
post-demo unless Sunny pulls it forward for the drilldown benefit.

### 2026-08-26 — TENANT CHAIN COMPLETE + ADR 0059 MECHANIZED (release 1.58.1)
**The 1.58.0 chain: 7/7 Completed** (300 with the folded sweep in
2:36; 22:33–22:54). Verified live: **83 cluster nodes** — matching
the pre-migration 83 flags exactly (the migration preserved every
verdict); census(flag) answers 83 through pure traversal. The
govmeta receipt lands with the 1.58.1 rerun (post-1.58.0 addition;
it guards only the zero case, which this store is not in).
**ADR 0059 mechanized, all three strata (G1-G3 → spec Group Q —
renamed on entry, G was taken; correspondence recorded):**
- src/graph/topology.py union-find: foundation exception honored
  (islands enumerated, never findings), degree-0 forbidden with the
  receipt as the one typed exclusion, EDGE_PROVENANCE totality
  (parsed/declared/derived/asserted; every EdgeType mapped, CI-
  pinned), stray-derived-component detection.
- 300 postconditions carry Q1/Q2 (build-first, in the fold as
  ordered); partial unit fixtures declare enforce_topology=False
  with the recorded reason — the assert is for corpora, not
  fragments.
- CI: the 2026-08-26 measurement is a permanent test (1 principal /
  0 orphans / 0 dangling; sizes >= 6,669/14,994 — shrink = extraction
  regression) + the shape corpus holds the axioms.
- Live audit topology leg: FIRST TENANT RUN GREEN — principal
  6,713, five foundation islands enumerated (REF_PATIENT_CLASS,
  V_PATIENT_ENCOUNTERS, DM_ICU_STAY, REF_SEX, V_LOG_BASED — all
  legitimate unread-dictionary states), and one LIVE FIND the
  recorded corpus could not show: the admin-telemetry semantic
  model forms a report/measure-only component (its gov_* anchor
  tables are outside the dictionary) → mechanized as the typed
  isolation class `consumption_unanchored` per Q1's own form
  (enumerated, never a finding; joins the principal if its tables
  are ever dictionary-tracked). Audit prefix map gained
  cluster/loggroup/govmeta → zero drift on rerun.
**Release 1.58.1** (wheel + env item + CHANGELOG). Suite 1,089+
passing at last full run; final gates + smoke re-running at close.
REMAINING FOR SUNNY (the 1.58.x closing steps, unchanged +1):
env re-publish picks up 1.58.1 (brings the receipt + topology
postconditions to the tenant on the NEXT routine rerun — no urgent
rerun needed; 1.58.0's data is complete); delete the dead
gov_red_flags KQL shortcut; dev injects instructions; spot-check
/redflags + "what governance red flags exist?" (expect 83); Publish.

## SMALL ORDERS + PARKED DIRECTIONS (Sunny's morning four, 2026-08-27)

**ORDERED (small, slot after the fused build):**
1. **TEST_MAP.md, generated** — every test declares the
   axiom/contract/ADR/family it proves (marker or docstring
   convention); generator emits a grouped, readable map; freshness
   asserted in CI (the PIPELINE_MAP pattern). Purpose: the suite
   stays legible to Sunny as it grows.
2. **Suite transcript artifact** — every answer_evals run emits a
   readable SUITE_TRANSCRIPT.md: per family, question → final
   answer text → machine verdict → grade (+ floor/gate notes). Data
   exists in the dump; this is emission, not machinery. Purpose:
   Sunny reviews behavior without the web UI.

**CONFIRMED, no new ruling:** post-round decision UI with weights =
ADR 0056 as ratified; builds post-capture; UI placement note —
decisions offered at EVERY answer round.

**PARKED DIRECTIONS (recorded, unordered):**
- **Semantic cloud / domain clusters:** derived domain_cluster nodes
  from shared-technical-neighbor overlap — DETERMINISTIC grouping
  only (no stochastic community detection; E2). Uses: estate map by
  subject area, domain-grouped differentiation queue, domain-scoped
  steward harvest.
- **Graph visualization:** nice-to-have. First cheap step when the
  board clears: interactive render of the SHAPE corpus graph (140
  nodes — layers as colors; the semantic-cloud clusters become
  visible). Full-estate viz needs layer-collapsed views; later.

### 2026-08-27 — MORNING ORDERS 1+2 SHIPPED (suite legibility)
**TEST_MAP.md, generated** (docs/architecture/): 106 modules /
1,072 tests, every module accounted — ONE WRITER per linkage kind:
ADR claims come from src/trace_registry.py (an `adr:` tag in a
docstring is INVALID — it would be a second truth that can drift);
law/contract claims are docstring `Proves:` lines validated against
small registries in devtools/suite_map.py (5 laws, 6 contracts);
spec-axiom grouping is DERIVED (axiom → grounding ADRs → their
tests, no per-test duplication). 15 registry-unclaimed modules got
Proves lines; test_report_links had a genuine 0040 claim → added to
the registry (the one writer). CI: tests/test_suite_map.py —
totality (a new unclaimed module is a red build), tag validity,
freshness (PIPELINE_MAP pattern), and no dead registry rows (an
unused law/contract slug fails).
**Suite transcript artifact**: every answer_evals run now writes
internal/docs/SUITE_TRANSCRIPT.md — per family: question → final
caption text (blockquoted) → machine verdict (DISHONEST/dumb/ok
with the legend stating the grader polices honesty, never depth) →
facts/rounds/declared line, INFRA-SKIPs disclosed per family, board
table with the gate (answer_rate >= 0.80) and the floor named as
build-stopper. Pure emission over the existing dump
(render_transcript, unit-tested over fabricated records — 7 tests).
No engine change → no release; both land in git only.
Gates: 1,106 passed + 5 xfailed, ruff clean. BOARD.md adopted:
dev-queue items ticked + ops-finds report filed on the board.
0056 UI placement confirmation + two parked directions: recorded,
no build.

## STATUS RECONCILIATION (review session, 2026-08-27 — unsticking a hold)

Dev reported holding for "the review session's verification of my
RESULTS." **RESULTS v2 above is EMPTY — the fused build has not been
delivered, so no verification is pending. The ball is DEV'S:**
1. Build payloads 1–3 (palette v2 · clusters completion + consumer
   census outcome · Diabetes Registry Dashboard) and append RESULTS
   v2. Review's watcher verifies on your push.
2. **Payload 3 IS ruled** — see §PAYLOAD 3 above: "Sunny's ruling,
   2026-08-25: BUILD," including the empty-description sub-ruling
   (item 2). Nothing about it is parked.
3. Your B3-behind-acceptance hold was CORRECT — it stays sequenced
   behind the fused build's verdict.

## REVIEW VERDICT on the FUSED BUILD (2026-08-27, autonomous cycle): APPROVED — acceptance granted, B3 UNBLOCKED

Independently verified: suite 1,110 green (review's own run);
SHAPES_GAPCHECK v2 — 39/39 instantiated cells PASS, 5
excluded-with-reason, every ratified dimension covered incl. D7;
dashboard git items present on the sepsis pattern (empty description
mechanically held — the demo law enforced by a test, exactly right);
clusters live as sole truth (83 nodes = 83 flags, census by pure
traversal), 320 + table retired, census closed zero orphans; 0059
topology leg green. One mechanical ruff finding fixed by review
(--fix, re-verified green) to avoid a relay cycle — noted for
transparency. **B3 step dep-chains: the acceptance gate it was
sequenced behind is now passed — GO on your next wake.**

**SUNNY'S UNBLOCKED STEPS (the runbook tail, board updated):**
1. SQL Intelligence Agent: hard-refresh, spot-check "what governance
   red flags exist?" (expect 83 via traversal), **Publish**.
2. Tenant load: workspace update-from-git; set the two SQL
   parameters (DemoSqlServer/DemoSqlDatabase) on the dashboard's
   semantic model; open the report once to verify render; confirm
   description still EMPTY.

### 2026-08-27 — B3 STEP DEP-CHAINS BUILT (autonomous cycle 3, on review's GO)
transform_to_transform enters the ask surface, Echo Law from birth:
- **Op semantics:** step retrieve now carries the chain BOTH
  directions — `fed_by_steps` (what feeds it: targets of the step's
  outgoing t2t edges; build direction is consumer→dependency) and
  `feeds_steps` (what consumes it: sources of its incoming edges).
  Chain ids surface into the session registry, so a follow-up
  retrieve walks the chain under the token-matching law unchanged.
- **Queries:** STEP_FED_BY_QUERY / STEP_FEEDS_QUERY (graph_edges
  joined to graph_nodes for names, ordered, complete).
- **Registry:** the stale "PARKED BEHIND ROUND 4" exclusion row is
  now REACHABLE (ops=op_retrieve, both queries, marker
  transform_to_transform) — reachability CI holds it.
- **Pin bumped CONSCIOUSLY:** the retrieve tool description gained
  one tool-property sentence (fed_by_steps / feeds_steps). No
  question shapes (P4 respected); SYSTEM_PROMPT unchanged. New sha
  065dcb4d… recorded in answer_evals + test_turn_engine with the
  bump note.
- **Echo Law legs:** L0 (test_ops: dep chain both directions +
  surfacing; fake graph in test_tools), smoke case "retrieve(step
  on a live t2t edge)" — picks a REAL t2t edge first so the
  assertion cannot vacuously pass, GREEN live; suite family
  `step_deps` ("what feeds the Scores step of ED Sepsis
  Screening?") with a store-derived oracle (fed_by names read
  through the same query the op runs — never hardcoded).
- Gates: 1,111 passed + 5 xfailed, ruff clean, live smoke all
  green. Walk section B can now grade against the built surface.

### 2026-08-27 — LIVE-EVAL CORPSES (first post-1.58 live grading) + MECHANISM, same cycle
The B3 acceptance --smoke run was the FIRST live eval since the 1.58
migration, and it earned its keep twice:
1. **The suite's own guard fired first** (fixture defect): the
   step_deps oracle refused to grade "Scores" (no recorded fed_by in
   the live store — my pick came from the test fakes, not the store).
   Fixed to the live-verified "ABX ← AllMeds". The oracle's assert
   prevented a vacuous PASS — oracles-by-construction working.
2. **Build-stopper honored: 2 DISHONEST turns** (pointer_chase,
   bridge-W11) + one sameness flip. Diagnosis — one shared shape,
   the W13b false-empty class reborn on the ASK surface: the model
   ran lineage(table=<METRIC name>) — a probe that measures no
   table — got 0 rows, IGNORED the W9 redirect note (which fired
   correctly), and claimed absence ("no dashboards use X") quoting
   the vacuous probe's own machine headline. The verifier accepted
   it because headlines are quotable ground (the 08-21 count-answer
   walk find). pointer_chase reproduced 2/2 runs — behavioral, not
   variance.
**Mechanism (Echo Law, same session):** NON_EVIDENCE_STAMP on any
lineage empty whose phrase resolved to a non-table kind (the W9
redirect now carries it); the verdict verifier EXCLUDES stamped
results' headlines from quotable ground — an absence claim can no
longer verify against a probe that never measured the question.
NARROW by construction: honest empties (a real table nobody reads,
the column-coverage caveat) are unstamped and stay quotable — cage
test pins both directions. L0 x2 + smoke case (live GREEN:
"lineage(table=METRIC name — non-evidence stamp)").
**Recorded, not yet mechanized (watch items):** bridge-W11 corpse =
model ignored the search bridge note and claimed no-official from a
token-degraded census (needs a design pass if it recurs — the
degraded-universe absence-claim class); step_deps + flags graded
dumb on n=1 (engine reached the right records, caption failed to
synthesize — capability, not honesty). Re-run scorecard appended
below when green.

### 2026-08-27 — DETERMINISM PIN + COLUMN-BRANCH STAMP; ONE CLASS DEFERRED TO REVIEW (recorded reason)
Continuing the live-eval corpse hunt, three more mechanisms landed:
1. **Caption-gate crash fixed** (live TypeError, fixture-first): a
   ref-anchored caption naming a competitor but no sibling left
   pos_sib=None and the ordering check compared int < None. The
   ordering duty is now vacuous when no sibling is named (presence
   already satisfied by the ref). The gate itself must never crash.
2. **Determinism pin**: azure_chat_api sampled at DEFAULT
   temperature — the same question flipped ok → DISHONEST across
   runs on identical inputs, so the honesty floor moved with
   sampling noise. temperature: 0 pinned at the engine doorway
   (production + suite; the engine states facts from tools, it does
   not ideate). Temp-0 rerun confirmed the remaining corpses are
   STABLE states, not noise. Behavior-affecting change — flagged
   for review's eyes.
3. **NON-EVIDENCE stamp extended to the column branch**: at temp 0
   the model probed lineage(column=<METRIC name>) and the
   coverage caveat — designed for real-but-untracked columns —
   legitimized the absence claim. Same category error, same
   mechanism: W9 redirect + stamp; the honest caveat for
   real-shaped columns stays unstamped and quotable (L0 both ways).
**DEFERRED TO REVIEW (Echo Law recorded reason: needs a design
ruling):** the remaining sameness corpses are one stable class —
RELATIONSHIP CLAIMS WITHOUT COMPARE: the model retrieves both
records and narrates a difference/sameness verdict from
descriptions ("what's the difference between X and Y" answered
without op_compare; "no other metric uses the same base
population" concluded from records + census). The compare-only law
exists as tool semantics; FLOORING it requires the caption gate to
TYPE relationship claims in prose, which is exactly the
lexicon/question-shape territory P4 bans. Options for review's
design pass: (a) a turn-scoped duty keyed on ≥2 retrieved records
of the same kind + zero compare results (structural, no lexicon —
my recommendation to examine first); (b) verdict-form extension (a
typed "relationship_verdict" field the machine can check against
displayed compare results); (c) accept as capability boundary,
suite-visible. Evidence: temp-0 dump 2026-08-27, sameness honesty
0.60, questions and captions preserved in SUITE_TRANSCRIPT.md.

## FIELD FIND — Sunny's agent spot-check FAILED; Publish BLOCKED (2026-08-27 evening; PRIORITY over B3)

The spot-check worked as designed: the draft agent could NOT answer
"what governance red flags exist" — honest refusal with remediation
(good behavior; no invention). Root reports from its own Basis:
JSON_VALUE over graph_nodes.properties for node_id LIKE 'cluster:%'
→ JSON parsing error, 0 usable rows.

1. **F-1 (the fix): cluster surface must be FLAT for the agent.**
   Suspects: JSON_VALUE's 4,000-char value limit + no-array
   extraction vs our large cluster properties (members, receipts,
   drill). Remedy per ADR 0020 (data-shaped): promote the agent's
   fields (flag_class, severity, identity, member_count,
   distinct_logics, disposition) to REAL COLUMNS on the graph_nodes
   export or a dedicated flat view; agent instructions query
   columns, never parse JSON. Verify with the N=3 pattern before
   handing back to Sunny.
2. **F-2: stale config + incomplete retirement** — gov_red_flags is
   still CHECKED as a selected source in the agent, and the
   Lakehouse table still exists. Finish the retirement (census
   truth) and clean the source selection.
3. **F-3:** second question died in codegen ("no SQL candidates
   passed validation") — likely resolves with F-1's flat surface;
   confirm in verification.
4. Sequence: this PRECEDES B3 (a customer-facing surface is broken
   in draft; the demo law's cousin: never leave a condemned state
   awaiting a click). Sunny's Publish stays BLOCKED until your
   verified re-inject; she then re-runs the spot-check.

### 2026-08-27 — CORPSE-HUNT CLOSE: 5th live run
pointer_chase 1.00 PASS end-to-end (the column-branch stamp turned
the category-error probe into a followed redirect); step_deps 1.00;
flags honesty 1.00. The ONLY remaining DISHONEST turns are the
relationship-claims-without-compare class already DEFERRED TO
REVIEW above with the recorded reason. B3 records stand; corpse
mechanisms all L0+smoke+live-verified. Full suite 1,115 green at
last gate; ruff clean. — Pivoting to the F-1..F-3 field find
(priority over B3 per the order; B3 was already complete).

## RULING (Sunny, 2026-08-27 evening): THE FABRIC AGENT IS DEMOTED TO AN INTEGRATION RECIPE — F-ORDER RE-CUT, READ BEFORE BUILDING F-1

**The ruling:** we ship surfaces we can back; we don't maintain
reasoning we can't. The AIVIA-configured/published Fabric Data Agent
is no longer a product component. This supersedes the 08-22/08-23
"ship it" posture (made before the trust-law framing; tonight's F-1
proved the true cost: every internal improvement owes a translation
layer to someone else's brain).

**Your order, re-scoped (SMALLER — stop before agent-specific work):**
1. **F-1 becomes a PRODUCT export, built once:** the flat
   columns/view over cluster fields (flag_class, severity, identity,
   member_count, distinct_logics, disposition) as a first-class
   export surface (admin tiles, integrations, and the honest Step-6
   recipe). NO agent config injection, NO N=3 agent verification,
   NO publish cycle — all cancelled, now and for every future
   release.
2. **F-2 completes regardless:** finish gov_red_flags Lakehouse
   retirement (census truth).
3. **F-3 cancelled** (agent codegen behavior is no longer ours to
   fix).
4. **Docs re-cut (small, with this order or next):** INSTALLATION
   GUIDE Step 6 → optional appendix "Grounding Microsoft's Data
   Agent with AIVIA's surfaces" (recipe + disclaimer: the agent's
   reasoning is Microsoft's; AIVIA backs the surfaces). Registry/
   runbook references to agent publish cycles removed. Rematch
   harness stays dormant for future benchmarks.
5. **Then B3** as previously green-lit.
**Sunny's side (later, no urgency):** delete the tenant SQL
Intelligence Agent via UI (API deletes were permission-blocked
historically); her blocked Publish is now a RETIRED publish.

## REVIEW VERDICT on the corpse-hunt delivery + B3 (2026-08-27 night): APPROVED

Verified in an ISOLATED WORKTREE at 2f072ea (the shared tree carries
dev's in-flight F-work — worktree verification is now the standing
practice for deliveries in a dirty tree): 1,116 passed, ruff clean —
matches dev's report. Accepted: pointer_chase 1.00 (the W9 redirect
followed end-to-end), **B3 COMPLETE** (step_deps 1.00 — board
updated), flags honesty 1.00, gate-crash/determinism/floor
mechanisms L0+smoke+live-verified. The
relationship-claims-without-compare class is ACCEPTED AS DEFERRED
TO REVIEW — it is now a review-session design item (the walk's Q4
family; M4-hard, no lexicons; sits beside W10).

### 2026-08-27 — F-ORDER EXECUTED AS RE-CUT (release 1.58.2)
**F-1 (PRODUCT export, per the demotion ruling): BUILT.** graph_nodes
carries six REAL columns — flag_class, severity, identity,
member_count, distinct_logics, disposition — populated on cluster:
rows by reify_clusters (the one writer), NULL on every other row
(uniform rows, schema-stable everywhere). Contract updated with the
F-1 note; L0 tests pin flat-mirrors-bag on cluster rows and
no-stamp on loggroup rows; shape corpus + topology + contract
suites all green through the new shape. No agent injection, no N=3
agent verification, no publish — cancelled per the ruling, now and
for every future release.
**Docs re-cut: DONE.** INSTALLATION GUIDE Step 6 → "Step 6
(retired)" pointer + new appendix "Grounding Microsoft's Data Agent
with AIVIA's surfaces (optional)" with the disclaimer and the
flat-columns guidance (query columns, never JSON; gov_red_flags
named as retired). "After the agent is working" → "after the
pipeline is verified"; re-run section no longer names the Data
Agent as the consumer.
**F-2: repo side CLEAN (zero live references — census verified);
physical Lakehouse table still present.** My OneLake DELETE of
Tables/dbo/gov_red_flags was PERMISSION-BLOCKED by the local
command classifier (destructive tenant action — the block is
reasonable and I did not work around it). PARKED FOR SUNNY: delete
the `gov_red_flags` table in the Lakehouse UI (~10 seconds),
alongside her queued agent deletion.
**F-3: cancelled** per the ruling.
**Release 1.58.2** (wheel + env item + CHANGELOG: F-1 flat surface
+ the corpse-hunt mechanisms + B3). The flat columns MATERIALIZE in
the store on the next 300 rerun — no urgency now that no agent
verification depends on them; they ride the next routine chain (or
the shape-store seed run, whichever comes first).
Gates: 1,118 passed + 5 xfailed, ruff clean.

## REVIEW VERDICT on 1.58.2 (2026-08-27 night): APPROVED — F-order closed; NEXT ORDER: the shape-store tenant load

Verified: 1,118 green + ruff clean (review's own run). F-1 flat
governance columns accepted as a product export; docs re-cut
accepted (Step 6 → recipe appendix with the disclaimer); F-2 repo
side clean, physical table deletion correctly classifier-blocked →
PARKED TO SUNNY (Lakehouse UI, ~10s; her other deletions confirmed
done: Graph Agent + eh_probe long gone, SQL Intelligence Agent
deleted 08-27). F-3 cancelled per ruling.

**NEXT ORDER (already-ruled: the demo runs on shapes → tenant load
REQUIRED): execute the shape-store tenant load per your recorded
demo-switch design** (_shapes profile, isolation from the realism
store, seed + chain; the 1.58.2 flat columns materialize in the
same run). Sunny's UI-only parts → runbook lines as needed. After
the load: her dashboard finish (refresh → render → description
check) and the re-walk unblock.

**Rename in flight (ops-find #3):** Sunny renames probe-eh →
aivia_catalog_eh (Eventhouse) and its DB → semantic_catalog; on her
confirmation, sweep code references (devtools DATABASE, org_config,
runbooks) + live-smoke verify.

## RENAME EXECUTED (Sunny, 2026-08-27 night) — REFERENCE SWEEP ORDER

Final names: Eventhouse **sql_catalog_eh**; KQL database
**semantic_catalog** (was probe-eh / probe-eh). Sweep every code and
doc reference: devtools DATABASE constant + any "probe-eh" literal
(engine_smoke, verify scripts, org_config, runbooks, installation
guide, walk docs). The cluster QUERY_URI host should be unchanged by
an Eventhouse rename — verify rather than assume (live smoke leg
against semantic_catalog; capacity is active now). Ops-find #3
closes with this sweep: no screen or file says "probe" again.

## SHAPE-STORE TENANT LOAD — EXECUTION (dev, 2026-08-27 night; design refined at execution, rationale on record)

**Design refinement (recorded before building):** the 08-25 design
said "_shapes-suffixed lakehouse tables via an org_config variant."
At execution the suffix variant fails reality: most chain notebooks
write LITERAL table names (saveAsTable("output_metric_logic") and
~30 siblings) — suffixing means invasive edits across ~10 notebooks
days before capture. The design's INTENT (absolute isolation,
switchable chain, profile check) is delivered instead by a
**SEPARATE LAKEHOUSE** (`sql_query_lh_shapes`): same table names,
different store — isolation by construction (zero collision is
structural, not conventional); ZERO notebook changes
(/lakehouse/default/ resolves to the run's attached lakehouse; the
job API's executionData sets defaultLakehouse per run); each
lakehouse carries its own Files/sql-query-agent/org_config.yaml at
the same relative path, so the profile IS the lakehouse. The
Eventhouse side gets its own database (shapes catalog) so the ask
surface switches by config. 100_install runs first as the
profile check (its CONFIG_PATH parameter + install checks already
exist — the "100-style check" the design called for).

### 2026-08-27 — RENAME REFERENCE SWEEP DONE (ops-find #3 closes)
Code + living docs swept probe-eh → semantic_catalog (4 devtools
DATABASE constants, webapp env default, cli literal, both
eventhouse .kql files, runbook + resume checklists, org_config
LOCAL). Frozen RESULTS/baseline records left verbatim — they are
history, not guidance (recorded decision). **Live smoke GREEN
against semantic_catalog** — the cluster QUERY_URI survived the
rename, verified not assumed. ONE residual: the TENANT org_config
kusto_db line — my OneLake patch was classifier-blocked (config
overwrite; the failed attempt left the file INTACT, verified by
read-back). RUNBOOK LINE FOR SUNNY: edit line 96 of
Files/sql-query-agent/org_config.yaml in the Lakehouse (kusto_db:
"probe-eh" → "semantic_catalog") — REQUIRED before the next 700 run
(the old DB name no longer exists; 700 would fail loudly).
CHANGELOG: rides Unreleased (webapp/cli defaults; chain unaffected).

## REVIEW on the rename sweep (2026-08-27 late): sweep ACCEPTED — but the push is NOT suite-green; fix-forward now

Sweep scope verified: zero live probe-eh references (grep clean),
ruff clean, smoke green — ops-find #3 CLOSED on its merits. However
the commit ships 3 RED tests (gates-green-at-push law):
1. tests/shapes/test_seed.py::test_every_palette_table_is_created_
   and_populated — your in-progress seed work riding the sweep
   commit; finish it under the load order or gate it properly.
2. tests/test_suite_map.py — TEST_MAP stale; regenerate
   (scripts/generate_docs.py).
3. tests/test_trace_registry.py::test_single_classification — a new
   module lacks its classification row.
Fix-forward in your next push; the shape-store load order stands.

### 2026-08-27 — SHAPE-STORE TENANT LOAD: STAGED END-TO-END, chain armed on two Sunny clicks
**Executed (all verified):** shapes lakehouse CREATED
(`sql_query_lh_shapes`, bf55535b); 7/7 assets staged into its Files
(org_config variant with targeted edits — search db →
semantic_catalog_shapes, semantic_models → FOLDER source holding
ONLY the dashboard TMDL so sepsis stays out of the demo store;
ScriptDom DLL server-side copy; 38 corpus SQL files, collisions
schema-prefixed; dictionary CSVs; metric-names CSV with the
dashboard link resolved from the live workspace; steward personas
CSV). Eventhouse: `semantic_catalog_shapes` DB created + table +
Vector16 policy + semantic_search() function installed (mgmt
commands verified). Env staging already carries the 1.58.2 wheel
(the git sync staged it). **Demo-source seed GENERATED, tested,
committed** (devtools/generate_shape_seed.py →
data/shapes/generated/seed/: all 22 palette tables + deterministic
synthetic rows + all 38 procs verbatim; ORACLE stamped in-file — U7
composite cohort = 105, registry rows = 117; byte-identical regen +
PHI-shape tests, 5 new). **Chain runner ready**
(devtools/run_shapes_chain.py): 100→010→040→060→[loadTable names +
stewards]→200→300→400→500→[create-then-verify KQL
shortcut]→700→800, every run pinned to the shapes lakehouse via the
job API defaultLakehouse override; post-chain verification asserts
the F-1 flat columns live, cluster count, semantic_search, and the
U7 dashboard link (W4).
**RUNBOOK — Sunny, two steps, then dev fires:**
1. **Publish sql-logic-env** (workspace → sql-logic-env → Publish;
   the staged 1.58.2 wheel is already correct — my API publish was
   classifier-blocked, same class as before).
2. **Seed the demo source DB** (aivia_demo_src → New SQL query):
   paste + run `data/shapes/generated/seed/01_schema_and_data.sql`,
   then `02_procs.sql` (both idempotent; expect cohort 105).
3. Tick the board / push — dev's watcher wakes and fires
   `devtools/run_shapes_chain.py` (fully automated from there).
Post-chain (Sunny): dashboard REFRESH → render check (the cohort
card must read exactly **105** — the seed's stamped oracle) →
description still EMPTY. Separately (realism store, before its next
700 run): org_config.yaml line 96 kusto_db → "semantic_catalog".
**Zones law find en route:** the renamed semantic_catalog.KQLDatabase
synced as a NEW top-level item class — .KQLDatabase joined
GOVERNED_SUFFIXES (the law fired exactly as built).

## REVIEW VERDICT on the load staging (2026-08-27 night): APPROVED — awaiting Sunny's two clicks

Verified: 1,123 green (the 3 flagged reds fixed) + ruff clean. Seed
oracle stamped in-file (cohort 105); chain runner with
create-then-verify shortcut (the mechanism from the ghost lesson —
applied at birth); zones-law catch on .KQLDatabase accepted. The
protocol note "tick the board / push wakes dev" is now the standing
fire signal for chains needing human preconditions.

## FIELD FIND (Sunny's seed run, 2026-08-27 night): SOURCE-DB COLLISION — seed 01 errored, chain HELD

Seed 01 in aivia_demo_src failed compile: INSERT INTO dbo.PATIENTS
hit the SEPSIS corpus's existing PATIENTS schema (Msg 207 ×4,
ACTIVE_FLAG / PRIMARY_LANGUAGE). **The real find: the isolation law
missed the SOURCE leg** — shapes got their own lakehouse + KQL DB
but the seed targets the SHARED source DB, where table names
collide with the realism corpus; a full run would DROP sepsis
tables (procs + ED dashboard breakage).

**ORDER:**
1. Re-target the shape seed to an ISOLATED source: new Fabric SQL
   database **aivia_shapes_src** (create via API if permitted, else
   one Sunny click); seed scripts unchanged otherwise.
2. _shapes profile: point 030/ingest + anything source-bound at the
   new DB; the Diabetes Registry Dashboard's parameters will need
   the NEW server/db values (runbook line for Sunny; fetch via the
   sqlDatabases API as before).
3. Guard at birth (Echo Law): the seed gains a preflight assertion
   — target DB must be empty OR contain only palette tables
   (fail loud on foreign tables); isolation-law text in SPHERE
   gains the source leg.
4. Damage check on aivia_demo_src pending Sunny's sys.columns
   diagnostic — if PATIENTS was replaced, restore from the sepsis
   seed section before anything else touches the realism store.
Chain stays HELD until re-targeted seed passes with cohort 105.

**Damage check CLEAR (Sunny's sys.columns diagnostic, 08-27):**
dbo.PATIENTS in aivia_demo_src is the sepsis corpus's 137-column
table, intact — the compile abort preceded any DROP. Order item 4
closes: no restore needed; the realism store was never touched.

### 2026-08-27 — SOURCE-LEG ORDER EXECUTED (collision find closed; chain re-armed)
1. **aivia_shapes_src CREATED** (API; same server host as the demo
   DB, its own catalog) — the isolation law's SOURCE leg is real.
2. **Seed re-armed with the guard at birth:** 01 now OPENS with an
   ISOLATION GUARD (THROW 50001 on any foreign dbo table — refuses
   before the first DROP; every palette table whitelisted) and DDL /
   INSERTs are GO-separated — the Msg-207 lesson mechanized (a
   T-SQL batch compiles against the PRE-batch schema; that compile
   failure is also WHY the collision cost zero — nothing executed,
   as Sunny's sys.columns check confirmed). 2 new tests; regen
   byte-identical, cohort oracle still 105.
3. **SPHERE gains the three-legged isolation law** (store / catalog
   / source — "a leg nobody thought to isolate is where the
   collision arrives").
4. **_shapes org_config re-staged** with the extractor pointed at
   the isolated source (verified by read-back).
**RUNBOOK (updated — Sunny, one step left):** paste + run the TWO
seed files in **aivia_shapes_src** (NOT the demo DB; the guard now
enforces this — expect cohort 105), then ONE dashboard parameter:
semantic model → Settings → Parameters → DemoSqlDatabase → the
aivia_shapes_src catalog name (Settings shows it; DemoSqlServer is
UNCHANGED — same host). Then push/tick: the chain fires.

## REVIEW VERDICT on the source leg (2026-08-27 night): APPROVED — chain re-armed on Sunny's seed

Verified: 1,124 green after review's mechanical TEST_MAP
regeneration (the one red) + ruff clean. Accepted: the isolation
guard at birth (THROW before any DROP on foreign tables — the
collision class dies at compile), GO-batching (the Msg-207 lesson
mechanized), the three-legged isolation law in SPHERE, the isolated
source created and read-back verified.

## ECHO — the parameter-serialization hazard recurred (2026-08-27): CONNECTION-BINDING ORDER (mandatory per the law)

Second occurrence: Sunny's re-entered parameters immediately
re-appeared as a pending source-control change — commit re-leaks,
Undo re-wipes (the earlier "Undo" guidance was WRONG for this item;
corrected: leave pending, touch nothing). Mechanism, mandatory:
**rebind the Diabetes Registry semantic model's source via a shared
cloud connection** (connection-bound, workspace-level) instead of
text parameters, so no endpoint ever serializes into the item
definition; parameters demoted to placeholders permanently.
Pre-capture (the demo uses this dashboard). Board rule amended.

### 2026-08-27 — ECHO ORDER (connection binding): mechanism grounded, one Sunny click queued
Researched and grounded (Fabric REST "Bind Semantic Model
Connection" + the binding-hints write-up): the bind request carries
the model's DATASOURCE REFERENCE PATH and the CONNECTION ID as
separate fields — so the definition keeps the PLACEHOLDERS
permanently while a workspace-level binding routes refresh through
a real shared cloud connection. No endpoint ever serializes into
the item again; the pending-change hazard ends structurally.
**Execution plan (sequenced):**
1. [SUNNY — the one credential step, ~30s]: Manage connections →
   New → SQL Server: server = the demo host (unchanged), database =
   the aivia_shapes_src catalog, OAuth2 sign-in, shareable. (Her
   existing demo-DB connection df066c53 proves the exact shape.)
2. [dev] bind the dashboard model's current datasource to that
   connection (bindConnection API), re-inject the PLACEHOLDER
   expressions via updateDefinition (the pending change dies; git
   and tenant match permanently), re-bind the placeholder-path
   datasource, trigger a refresh, verify rows.
3. Post-capture note: the sepsis model gets the same treatment (its
   binding drift is the recorded tenant nit).
Sources: learn.microsoft.com Bind-Semantic-Model-Connection;
blog.crossjoin.co.uk binding-hints (2026-05).

### 2026-08-28 — INCIDENT + RECOVERY: the lakehouse override was silently ignored; the postcondition saved the realism graph
**What happened:** the job API accepts `defaultLakehouse` only under
`executionData.configuration`; at the top level (where my runner put
it) it is SILENTLY IGNORED, so the first chain ran its notebooks
against the notebooks' pinned default — the REALISM lakehouse.
**What held:** 300's ADR 0059 topology postcondition REFUSED the
polluted write (degree-0 'report:DIABETES REGISTRY DASHBOARD' — the
dashboard TMDL ingested into a corpus with no U7 to link to) — the
realism graph tables are UNTOUCHED. The assert built for axioms
caught a cross-profile contamination nobody predicted.
**What was damaged:** realism `input_metric_names` (curated, 28
rows) was overwritten by 060's TMDL-derived names. RESTORE staged:
the curated CSV is at Files/sql-query-agent/
input_metric_names_restore.csv in the realism lakehouse — loadTable
API + Livy both unsupported on a schemas-enabled lakehouse, so ONE
SUNNY UI LINE: realism lakehouse → Files/sql-query-agent →
input_metric_names_restore.csv → Load to table → EXISTING table
`input_metric_names` → Overwrite. (Dormant until the next realism
300 run — no urgency, but do it before that run.)
Also overwritten, ACCEPTABLE: input_report_sources /
input_dax_expressions (060-owned, regenerated content — now include
the dashboard rows; see the recorded design note below),
ops_parse_results (same corpus, same rows).
**Mechanisms (same cycle):** (1) runner fixed — override under
`configuration`; (2) TRIPWIRE at birth: after the first writing
notebook the runner asserts the table landed in the SHAPES
lakehouse and aborts otherwise — the silent-ignore class cannot
recur; (3) chain re-fired FROM THE TOP against the shapes store.
**Recorded design note (for review, not built):** the realism
store's consumption layer will now meet the Diabetes dashboard on
its next 060+300 (workspace-scan source): a report whose EXEC
target is absent from the corpus mints an unlinked report node =
degree-0 violation. Q1's own form suggests classifying degree-0
report/measure nodes as `consumption_unanchored` (the
admin-telemetry pattern at node grain). Deferred to review with
this evidence (Echo Law recorded reason: axiom-semantics change
needs the review pass); MUST land before the next realism 300.

## REVIEW on the incident + the deferred design item (2026-08-27 night): RECOVERY APPROVED; RULING ISSUED

Gates verified: 1,125 green + ruff clean. The recovery is
Echo-Law-exemplary: postcondition refused the main polluted write,
override root-caused (configuration nesting), TRIPWIRE at birth
(first-writer lakehouse assertion — the silent-ignore class dead
same-cycle), chain re-fired clean. Damage ledger honest: one
curated table (input_metric_names) needs Sunny's staged one-line
restore (dormant, pre-next-realism-300); regenerated tables
acceptable.

**REVIEW RULING (the deferred axiom-semantics item —
`consumption_unanchored` at node grain): APPROVED.** A
workspace-scanned report whose EXEC target is absent from the
corpus is REALITY, not an error — the graph represents it with a
TYPED state, never suppresses it (the foundation-exception
pattern, consumption edition). Constraints binding the build:
(1) enumerated + disclosed in the topology audit (never a silent
bucket); (2) ask-surface answers about such reports must carry the
state ("executes a target outside this catalog") — honest-answer
shape; (3) the node stays first-class and queryable. This is an
isolation-REASON addition within G1's own extension mechanism —
review's to rule; Sunny FYI on the board. BUILD IT before the next
realism 300, as you flagged.

### 2026-08-28 — G1 EXTENSION BUILT per the ruling (release 1.58.3)
All three constraints mechanized: (1) analyzer types degree-0
report/measure nodes as 1-node consumption_unanchored entries —
enumerated in the live audit's per-entry print, never silent;
canonical/technical degree-0 stays a defect (L0 both directions);
(2) the retrieve record of a zero-link report carries the typed
state "executes a target outside this catalog" (machine fact, L0
x2); (3) nodes stay first-class. 1.58.3 cut (wheel + env item +
CHANGELOG). Gates: 1,129 passed + 5 xfailed, ruff clean.
ENV RE-PUBLISH: one Sunny click, needed BEFORE the next realism
300 (no urgency; the running shapes chain is fine on 1.58.2 —
its dashboard anchors to U7).

## REVIEW on 1.58.3 (2026-08-27 night): APPROVED — the ruling implemented exactly

1,129 green + ruff clean (review's run). All three ruling
constraints honored: enumerated-never-silent, the ask-time stamp
("executes a target outside this catalog"), node stays first-class.
The sharpening is correct and noted with approval:
canonical/technical degree-0 REMAINS A DEFECT — only consumption
singletons get the typed-reality state. Realism-300 precondition
cleared.

## ORDER — the boundary echo contract (Echo Law: third silent-ignore instance = general mechanism, 2026-08-27)

Three hand-made instances (shortcut create-then-verify, chain
tripwire, refresh-history check) prove the class; generalize:
1. A BOUNDARY-OP REGISTRY (0052 pattern for side effects): every
   devtool operation that crosses the tenant boundary (create,
   publish, override, rename, load, delete) is enumerated and
   PAIRED with a declared, observable postcondition — or
   exempt-with-reason. CI asserts totality.
2. Runners refuse to advance past an unwitnessed postcondition —
   "an acknowledgment is a claim; only the postcondition is a
   fact."
3. Existing hand-made verifies become registry entries, not
   specials.
Sequence: post-chain, pre-updater (this IS the updater's skeleton).

### 2026-08-28 — CHAIN REPORT: shapes store BUILT through 500; two first-run defects fixed; ONE UI line blocks the tail
**Green against the SHAPES lakehouse (tripwire-witnessed):**
100 → 010 → 040 → 060 → loadTable(names, stewards) → 200 (14.2m,
38 procs through real ScriptDom) → **300 (12.8m — the shapes GRAPH
IS BUILT on 1.58.2: clusters, receipt, flat columns)** → 400 → 500
all Completed. First-run defects found + mechanized: (a) the
shortcut-before-700 ordering (bootstrap pass added,
postcondition-witnessed tolerance); (b) create_kql_shortcut
hardcoded the schema-lakehouse path (generalized: target_path +
verify_db params).
**BLOCKED at the Eventhouse copy: the API shortcut GHOSTS — 2/2
(201 registered, never mounts in 600s; create-then-verify caught
and ghost-deleted both — ops-find-1's mechanism, working).
API creation is a dead end in this tenant; UI is the documented
remediation. RUNBOOK — Sunny, one line:** KQL database
`semantic_catalog_shapes` → New → OneLake shortcut → lakehouse
`sql_query_lh_shapes` → table `output_semantic_catalog`. Then
push/tick — dev resumes `--from 700_refresh_search_index` (700 →
800 → full verification: flat columns, clusters, semantic_search,
the U7 dashboard link).
Reminder while you're clicking: the **1.58.3 env publish** you held
can go with this (both clicks, one visit).

### 2026-08-28 — CHAIN TAIL GREEN (700 + 800); THREE shortcuts close the store
700 (catalog rebuild + Eventhouse copy through Sunny's mounted
shortcut + full re-embed) and 800 both Completed — the shapes STORE
IS BUILT END TO END. The verification's first query then surfaced
the last gap honestly: the shapes KQL DB needs the ENGINE-surface
shortcuts (the realism DB got its set at original setup). The
engine queries exactly FOUR tables: semantic_catalog (native ✓),
graph_nodes, graph_edges, output_metric_logic. API shortcut
creation confirmed DEAD in this tenant (3/3 ghosts; create-then-
verify caught and cleaned every one — zero residue).
**RUNBOOK — Sunny, three clicks in the SAME dialog:** KQL database
`semantic_catalog_shapes` → New → OneLake shortcut → lakehouse
`sql_query_lh_shapes` → select `graph_nodes`, `graph_edges`,
`output_metric_logic` (the picker allows multi-select). Then
push/tick — dev runs the four-way verification (flat columns,
cluster count, semantic_search, the U7 dashboard link) and the
load closes.

### 2026-08-28 — SHAPE-STORE TENANT LOAD: COMPLETE AND VERIFIED
Four-way verification, all green against the live shapes store:
1. **26 cluster nodes — exactly the local gapcheck's 26 verdicts —
   and ALL 26 carry the F-1 flat columns** (the product export live
   in a store for the first time).
2. **semantic_search() answers in semantic_catalog_shapes** (top hit
   "Diabetic Patients" for the demo's own phrase; full re-embed
   done by 700).
3. **The U7 record carries the Diabetes Registry Dashboard link** —
   the pointer-chase demo beat is ready end to end (TMDL-parsed
   EXEC → report_to_canonical → report_name + URL on the record).
4. Graph surface complete (graph_nodes / graph_edges /
   output_metric_logic / semantic_catalog all queryable).
The demo estate now stands: isolated source (seeded, guard-held,
cohort 105 on glass) → isolated lakehouse (full pipeline, 1.58.2)
→ isolated catalog (search + engine surfaces) → the dashboard.
THE RE-WALK IS UNBLOCKED (walk section B grades against B3; section
I against the 26 flags). Next dev order in sequence: the boundary
echo contract (#76, post-chain — now).

### 2026-08-28 — BOUNDARY ECHO CONTRACT BUILT (the ordered generalization; the updater's skeleton)
`devtools/boundary_ops.py`: every tenant-crossing devtool op
enumerated and PAIRED with its declared observable postcondition —
7 rows over the 4 boundary modules (shortcut create-then-verify,
the chain's run/tripwire/loads/verify, the staging writes, env
publish). ONE exemption-with-reason (publish: the click is Sunny's
and classifier-blocked for dev; the wheel's arrival is witnessed
downstream by every notebook's REQUIRES_ENGINE floor). NEW witness
closed en route: ol_write gains a READ-BACK length check (the
append-202 + failed-flush shape once left a file untouched while
looking half-done). CI teeth (tests/test_boundary_ops.py, 6 tests):
module totality, op resolution, witness-marker fidelity in source
(the reachability pattern applied to side effects), taxonomy, no
stubbed postconditions. Contract slug `boundary-echo` registered in
the suite map; the slogan is in SLOGANS.md tagged LAW. Gates: 1,135
passed + 5 xfailed, ruff clean.

## REVIEW VERDICT (2026-08-28 morning): SHAPE-STORE LOAD CLOSED — APPROVED

Gates verified: 1,135 green + ruff clean. The four-way battery
accepted: 26 clusters all carrying F-1 flat columns (the product
export live in a store for the first time), semantic_search
answering, the U7 dashboard link on the record (pointer-chase beat
ready), all four engine surfaces queryable. THE RE-WALK IS
UNBLOCKED. Dev proceeds to the boundary echo contract as sequenced;
the connection-binding fix lands whenever Sunny's shareable
connection click arrives.

### 2026-08-28 — workbench store lever (board nicety, built)
resolve_store(): env KUSTO_DB > org_config.yaml `search.kusto_db`
(the line Sunny reached for now works workbench-side too) >
default; the startup banner prints the ACTIVE store + which lever
chose it. 3 tests. To sit the workbench on the demo store: local
org_config search.kusto_db: "semantic_catalog_shapes" — one visible
line, no env spelunking.

## ORDER RW-BATCH-1 (re-walk finds, pre-capture; after boundary echo contract)
1. **RW-3 (MANDATORY — echoed twice):** display-side fold of
   auxiliary rounds' result tables when the verdict's primary
   basis is another round. Acceptance: the two cohort questions in
   WALK_VERDICTS_SHAPES.md render focused (caption + primary
   evidence; detour tables folded, expandable).
2. **RW-4 (MANDATORY — Echo Law, deferred item gone live):**
   logic-sameness questions ("same Lab_Path / same criteria /
   same logic as X") route to compare/closeness (variant map) or
   the caption states the grain gap explicitly. Acceptance: the
   Lab_Path question in WALK_VERDICTS_SHAPES.md.
3. **RW-2 (data-file):** rename the U9 planted pair "Diabetic
   Cohort (Codeset)" → natural name, e.g. "Diabetic Patients
   (Coded)"; same drift, same oracles.
4. RW-1 (flag-census display) rides the 0056 presentation batch as
   already recorded.

### 2026-08-28 — RW-BATCH-1 BUILT (all three items)
**RW-2 (palette v3):** U9 pair renamed. DEVIATION RECORDED: Sunny's
example name "Diabetic Patients (Coded)" JOINS the "Diabetic
Patients" name family by fold (proven: the PD1 cell failed, 12
logics ≠ the ratified 10) — which the order's own "same oracles"
clause forbids. Executed as the family-neutral natural form
**"Diabetic Cohort (Coded)"** (drops the codeset jargon, keeps the
10-member beat). If Sunny prefers her exact wording, the tradeoff
is now visible: it re-scopes the U6/PD1 demo number to 12.
Corpus + gapcheck + manifest expectation made palette-driven (the
name can never strand a hardcode again); 39/39.
**RW-4 (mandatory):** the user's OWN identifier tokens now arm the
sameness stamp on LINEAGE results (exact-match against the
step-name universe — equality, never containment; the 'ED' corpse
boundary respected). The Lab_Path shape gets the caveat + member
surfacing on screen, which arms the existing W6 duty: caption
echoes the grain gap or a compare displays, else floored →
continuation pressure routes to compare. Universal reads-grain
sentence added to the table-lineage universe. 4 L0 tests. The
SHARPENED acceptance (routing consistency vs the exemplar) is
live-graded on the walk rerun — the deterministic levers are all
armed; routing beyond them would need question-shape typing (P4).
**RW-3 (mandatory, echoed):** machine-computed fold — when the
verified quote's ground is one result, every other result with
rows gets its ref in `folded_refs` (turn-scoped, verdict-anchored,
never model-claimed); the page retro-folds those tables into
collapsed details ("the map on demand"), headlines stay visible.
2 cage tests + page-JS gates (which caught two bugs while
building: a multi-line template and an apostrophe comment — the
gate earning its keep).
Gates: 1,144 passed + 5 xfailed, ruff clean. Store rename rerun
(names → 300…800 on the shapes store) firing next.

### 2026-08-28 — RW-4 co-occurrence lever (the sharpened directive, same cycle)
Specimen #4's shape mechanized: a retrieve holding >=2 same-kind
records (metric/step) stamps the compare route on its note —
"compare(refs) computes it exactly; descriptions and names never
do." A NUDGE, deliberately NOT the duty constant: a benign
two-record turn must never floor for a claim it didn't make. With
the step-token stamp (Lab_Path class), the universal reads-grain
sentence (already SIGHTED in Sunny's walk via the shared tree), and
this nudge, every observed route now carries the co-occurrence
lever the moment it forms. 2 L0 tests; 234 orchestrator green.

### 2026-08-28 — RW-BATCH-1 CLOSED: rename LIVE in the store; four-way verification green again
The rename rerun completed (names → 200 → 300 → 400 → 500 → 700 →
800): "Diabetic Cohort (Coded)" live in semantic_catalog_shapes,
ZERO old-name residue, 26 flat-column clusters, search live, U7
link intact. En route the shortcut step learned IDEMPOTENCY the
boundary-contract way (409 → verify the query path; the
postcondition is the fact, not the create). RW-BATCH-1 is fully
delivered: RW-2 live tenant-side; RW-3 + RW-4 (stamp + universal
grain sentence + co-occurrence nudge) live in the workbench via
the shared tree — two of them already SIGHTED in Sunny's walk
before the batch even closed. Demo ask for U9 is now: "Are the
two Diabetic Cohort (Coded) definitions the same?"

## DEV'S PROTOTYPE ESTIMATION for ADR 0060 (requested by the draft, 2026-08-28)

**Headline: the prototype is a DAY-SCALE build (~1–2 sessions),
because the deterministic 90% already exists.** The ops algebra IS
the traversal engine; the prototype adds a planner in front of it,
not an engine under it.

Piece-by-piece:
1. **PARSE** (~150 lines + one new PIN): one LLM call with a
   schema-FORCED tool ("file_parse": entities[], primitives[],
   modifiers[]) — the closed vocabulary lives in the tool schema
   itself, so an out-of-vocabulary parse is structurally
   impossible; unmappable input fails closed with the vocabulary
   offer (metric 5 by construction). New pin objects: the parse
   prompt + parse tool schema join the pin discipline.
2. **GROUND** (~50 lines): entity tokens → anchors by exact/
   contains against the name universe — the RW-4 nudge's mechanism
   generalized, as the draft itself notes. Zero new queries.
3. **COMPOSE** (~200 lines): primitives → op sequences over the
   EXISTING algebra 1:1 — definition→retrieve; same/different→
   retrieve×2+compare (the exemplar route, now deterministic);
   readers→lineage; feeds/fed-by→B3 step deps; flags→flag census/
   member flags; count→census. The experiment's question set needs
   NO new graph surface — B3 + clusters + compare + lineage cover
   it (checked against the walk's questions).
4. **CONFIRM + DISPLAY** (~80 lines workbench): parse-as-plan chip
   + confirm; the answer is the stamped map — NO LLM caption in
   the prototype, so metric 3 (floor collapse) is zero by
   construction and metric 4 (detour load) equals the plan's own
   rows. Confirm-all first (Sunny's §7.1 barely touches scope —
   relaxing later is a flag).
5. **HARNESS** (~200 lines): CURRENT vs PROPOSED over the shape
   corpus questions + Sunny's walk paraphrases (review holds the
   verdict docs — extracting the paraphrase set is the one input I
   need from review), graded on the planted oracles; scorecard in
   the SUITE_TRANSCRIPT shape.
**On §7.3 (parser tier):** run BOTH tiers as two harness columns —
the harness makes it one flag; recommend frontier-during-pilot as
the experiment's isolation control, exactly as the draft suggests.
**Not needed:** new store surfaces, tenant changes, new queries —
pure local + workbench. **Main risk:** the relation lexicon's
first cut (design-sensitive; review's primitive set should be
ratified before compose is written, or the prototype measures a
straw lexicon).

## ORDER RW-6 (data-file): descriptions for every node type
Finding (Sunny, 2026-08-28): description fields render empty in
every metric answer. Confirmed: palette tables carry descriptions;
all 38 metrics carry NONE (steps likewise). The search op already
scopes "name, business name, description" — the surface exists,
the data doesn't. Consequences: search recall crippled, 0060
tier-2 semantic grounding has no surface to embed, empty columns
on camera.
Order: author a description for EVERY palette node type (metrics,
steps; tables/columns verify), palette-driven (no hardcodes),
regenerate + store rerun (same pipeline as the RW-2 rename).
Descriptions must describe the LOGIC/purpose in business words
(they are the semantic surface tier-2 grounding will embed), never
restate the name.

### 2026-08-28 — ADR 0060 PROTOTYPE BUILT + THE GATING EXPERIMENT MEASURED (same day as acceptance)
**Built:** src/orchestrator/parse_plan.py — the parser-only path:
schema-CLOSED parse tool (the 7 ratified primitives as an enum —
out-of-vocabulary is structurally impossible), exact-then-contains
grounding where NAME COLLISIONS ANCHOR WHOLLY (one shared name over
two metrics = two anchors → compare; the corpus's founding shape,
and the Lab_Path named case pinned by test), deterministic compose
onto the EXISTING algebra, fail-closed vocabulary offer, confirm
line rendered (confirm-all per call 1). 9 L0 tests. Registered as
ADR 0060 in the trace registry (the closure tests forced it —
working as built).
**Measured (devtools/parse_experiment.py → PARSE_EXPERIMENT.md,
live on the shapes store, frontier parser per call 3):**
- Oracle correctness: **PROPOSED 7/7, CURRENT 6/7**
- Route consistency: PROPOSED 1/2 multi-ask intents (the miss: the
  parser added a spurious `defines` on one paraphrase — parse
  variance, disclosed), CURRENT 0/2
- Detour load: PROPOSED 4–7 rows/question; CURRENT 7–36
- Refusal: PROPOSED fails closed with the vocabulary offer;
  CURRENT ran a 37-row census at a poem
- Floor collapse: PROPOSED structurally 0 (no author)
Iteration 1 → 2 finds (recorded): first-cut grounding took only
rows[0] (defeating name collisions) and the parse prompt lacked the
ratified surface forms — both fixed; 4/7 → 7/7. Walk paraphrases:
0 loaded, DISCLOSED (review extracts to WALK_PARAPHRASES.txt; the
harness picks them up unchanged).
**§2a amendment alignment:** the prototype's grounding is tier-1
exact + deterministic containment; tier-2 semantic-candidates slots
into ground_entities as one more rung and DEPENDS on the RW-6
description surface, exactly as the amendment records. RW-6 is the
next build.

### 2026-08-28 — RW-6 BUILT (release 1.58.4): the authored semantic surface
**Palette v4:** 38 authored metric descriptions (business-logic
words, never name echoes) + a 43-name CTE vocabulary covering every
step name in the corpus (TOTALITY: a new test fails on any
undescribed canonical or named step; __final_select__ is the one
declared exception; a second test rejects name-restating fakes).
**Carrier (turn-key, both lakehouse types):** new optional contract
`input_node_descriptions` (kind/ref/name/description); 300 SEEDS
the table from Files/sql-query-agent/input_node_descriptions.csv
when present and applies text only where a node has none —
enricher (600) text is never overwritten. 300 floors at 1.58.4;
the registry regex learned patch-level floors (a fossil —
require_engine always compared numerically).
**Staged:** the 81-row CSV is in the shapes lakehouse Files
(read-back witnessed). Wheel 1.58.4 cut + env item swapped.
**REMAINING (the rename-pattern rerun): Sunny's ONE click — publish
sql-logic-env (staged 1.58.4) — then push/tick and dev fires
`--from 300_build_graph` (200 unchanged: descriptions ride the
build, not the parse), then 400→500→700 (search re-embeds THE NEW
SURFACE — tier-2 grounding's food) → 800 → verify descriptions
live.**

## ORDER RW-2b (data-file): rename the U9 pair again — "Diabetic Codeset"
Sunny's ruling 2026-08-28 on the RW-2 deviation: the first rename
fixed the wrong half. Her point was never the word "Codeset" — it
was calling a codeset a cohort. The artifact IS a hand-maintained
code list; name it what it is.
Rename both members: "Diabetic Cohort (Coded)" → **"Diabetic
Codeset"**. Family-neutral (does not contain "Diabetic Patients";
10-member beat intact). Palette-driven, gapcheck, manifest
expectation, store rerun — same pipeline as RW-2. Demo question
becomes: "Are all the Diabetic Codeset definitions the same?"

### 2026-08-28 — RW-2b APPLIED (repo + staging): "Diabetic Codeset"
The ruling's half understood now: the artifact IS a codeset — named
what it is. Both members renamed, descriptions reworded to codeset
semantics, gapcheck ask now "Are all the Diabetic Codeset
definitions the same?", 39/39, family-neutral (10-member beat
intact). Names + descriptions CSVs re-staged. The rename RIDES THE
RW-6 RERUN — one chain, both changes, still waiting on the ONE
env-publish click (1.58.4 staged).

### 2026-08-28 — Sunny: sql-logic-env PUBLISHED (1.58.4 live)
The ONE click is done. Dev: fire the chain `--from 300_build_graph`
→ 400→500→700→800 → verify names + descriptions live in
semantic_catalog_shapes. Review holds the codeset walk beat until
chain-green is recorded here.

### 2026-08-28 — RW-7 part 2 BUILT (release 1.58.5): the sweep self-describes
Every cluster node's description now states WHY it was minted — a
class-specific business sentence authored by the sweep at mint
("4 procedures share the name 'X' but compute 3 different logics —
one name is doing 3 jobs"; cousins/duplicates/grain each get their
own sentence shape). The RW-6 principle extended to the derived
layer: the machine authors the facts it is the author of. L0 test;
1,158 green. NOTE: the IN-FLIGHT rerun runs on 1.58.4 — the
self-descriptions land with the NEXT publish+rerun cycle (bundle
with the presentation batch's cycle; no extra click requested just
for this). RW-7 part 1 (flag cards) rides the presentation batch
with RW-1/RW-5 as ordered.

### 2026-08-28 — RW-8 BUILT + acceptance PASSED live (the gate reads the stamp)
**Mechanism:** the NON-EVIDENCE stamp now carries its suggested
resolution as DATA (`suggested_next_ids` in the result params, both
lineage branches); the verdict verifier REFUSES any answered
verdict while a stamped probe's suggested retrieve is unexecuted
this turn — missing_op names the exact id ("no verdict stands
while it is unread"). The laundered-absence class (the walk's
pointer-chase FAIL) dies structurally. 2 cage tests both
directions; 1,160 green; ruff clean.
**Acceptance (the exact walk question, live on the shapes store):**
route now lineage → RETRIEVE (the suggestion followed) → census;
the caption names USP_DM_Registry_Composite + MedDerived WITH
their RW-6 descriptions — a true answer where the walk saw a false
absence. Verdict filed humble on quote verification (honest
downgrade, no false claim).
**Sightings in the same run:** RW-6 descriptions LIVE in the
answer path (the rerun's 300 has landed store-side). RW-8 is
WORKBENCH-live via the shared tree immediately; it rides the next
wheel cut for form (nothing tenant-side executes the engine).

### REVIEW VERDICT — RW-8: VERIFIED
Gates re-run review-side: 1,160 passed + 5 xfailed, ruff clean —
matches. Mechanism is the right shape: the stamp carries its
resolution as data; the verifier refuses answered verdicts while a
stamped probe's suggested retrieve is unread — the laundered-
absence class dies structurally, and the refusal names the exact
unread id (continuation pressure toward the truth, not just a
floor). Dev's live acceptance on the walk question accepted as
claimed; Sunny re-walks it for the glass-side confirmation.

### 2026-08-28 — RW-6/RW-2b RERUN COMPLETE: the enriched store is live
Chain green end to end (capacity retries absorbed; the idempotent
shortcut verified the existing mount — "the postcondition is the
fact" on screen). VERIFIED IN STORE: "Diabetic Codeset" live, zero
old-name residue (the walk's names discrepancy WAS mid-flight
timing, as recorded); **ZERO canonical nodes without descriptions**
— RW-6 at store totality; 26 flat-column clusters; U7 dashboard
link intact; semantic_search re-embedded over the DESCRIBED
surface (visible: richer top hits). The demo estate now carries
the authored semantic layer end to end — tier-2 grounding's
surface exists in the wild.

### 2026-08-28 — PRESENTATION BATCH BUILT (the capture gate's dev half)
All three display items, workbench-live via the shared tree:
- **RW-5 answer-first folded rounds:** the conclusion card (caption
  + citation + verdict stamp) seats ABOVE the turn's panels; every
  panel folds to its one-line stamped headline — fold, never hide;
  every receipt one click away.
- **RW-7 flag cards (+RW-1):** flag rows render as the
  differentiation-queue view — identity, class + severity chips
  (CONFLICT red-edged, INFO amber), members · logics · disposition
  line, and the sweep-authored why-sentence. The census projection
  gained `description` so the self-description rides every flag
  row. Machine-grade node labels never render.
- RW-3's aux-fold nests harmlessly inside the round folds.
Gates: 1,160 green, ruff clean (the page-JS gate caught the
apostrophe-comment class a THIRD time — the gate IS the mechanism
and it holds; noted).
**CAPTURE GATE REMAINING: the 1.58.5 cycle** — Sunny's env-publish
click (staged 1.58.5 carries the sweep self-descriptions), then
dev's rerun (300→800) so the why-sentences the flag cards display
come from the STORE mint. Then the script's QA gate runs verbatim.

### REVIEW VERDICT — PRESENTATION BATCH: VERIFIED
Gates re-run review-side: 1,160 passed + 5 xfailed, ruff clean —
matches. Design conformance: fold-never-hide honored (receipts one
click away); flag cards are the differentiation-queue view with
class/severity chips + why-sentence; machine node labels never
render; RW-3 aux-fold nests inside. The page-JS gate catching its
class a third time = the mechanism holding (Echo Law working as
law). GLASS CHECK OWED: Sunny restarts the workbench and re-asks
the flags question + one definition question — her clarity verdict
is the acceptance, per the walk's division of labor.
CAPTURE GATE REMAINING: 1.58.5 publish click (Sunny) → dev rerun
300→800 → QA gate verbatim (script V2 §QA).

## ORDER RW-BATCH-2 (from Sunny's 13-question walk — pre-capture, pre-QA-gate)
1. **RW-9 (BUG, mandatory):** commentary renders twice — the RW-5
   card duplicated the block instead of moving it. One render, on
   the card, period.
2. **RW-10 (mandatory): implement ANSWER_FORMAT_CONTRACT.md** —
   machine-composed conclusion cards per question class; DIFFERS
   cards show machine diff lines; flag cards seated ON the card
   with plain-language class glosses; templates retired. Sunny's
   clarity check is the acceptance.
3. **RW-11 (mandatory, Echo Law — W10 specimen live):** row-level
   data questions get a FIRST-ROUND typed policy refusal
   ("definitions, not data — patient rows never reach the model")
   + the definition card. No budget-wander. Acceptance = "How many
   patients are currently in the Diabetic Patients cohort?"
Then: 1.58.5 publish click (Sunny, on return) → rerun → QA gate
verbatim (DEMO_SCRIPT.md V2) → capture.
OPEN CALL (Sunny): flywheel sequencing — second short film
post-0056 (review recommends) vs reopening the post-capture
ruling.

### 2026-08-28 — RW-BATCH-2 BUILT (all three; RW-11 acceptance PASSED live)
**RW-9 (bug):** dead by construction — the machine card is the ONE
render path; the old duplicate caption blocks are deleted.
**RW-10 (the answer format contract):** src/orchestrator/
conclusion.py — the conclusion card is MACHINE-COMPOSED, and card
class is DATA-DRIVEN from which results the turn displayed (flags →
cards ON the conclusion with per-class plain glosses + the sweep
why-sentence + the receipt closing line; compare → verdict chip +
MACHINE DIFF LINES from the partition's own diff field (identical
wording every run — the E11.80-vs-mumble stochasticity retired) +
item one-liners; records → definition card with the top decision
site's criteria; lineage → grain line verbatim) — never from typing
question prose (P4 holds). Model prose renders beneath as additive
color. 5 composer L0 tests; registered under ADR 0036 (its
presentation half).
**RW-11 (policy refusal, W10 live):** SYSTEM_PROMPT invariant 3b —
the fixed-wording first-reply refusal (brand routed through
product_name(); the brand-neutral-core gate caught the hardcode).
Pin bumped consciously (recorded at both sites). **ACCEPTANCE
PASSED LIVE: the exact walk question refused in ZERO rounds** (vs
the 8-round budget death), fixed sentence verbatim, definition
offered, composer typing the card policy_refusal.
Gates: 1,165 green + ruff. Workbench-live via the shared tree.
CAPTURE GATE now: Sunny's glass check of the batch + the 1.58.5
publish click + rerun + the script QA verbatim.

### REVIEW VERDICT — RW-BATCH-2: VERIFIED
Gates re-run review-side: 1,165 passed + 5 xfailed, ruff clean —
matches. Contract conformance: card class data-driven from
displayed results (P4 holds — no question typing); diff lines from
the partition's own field (stochastic narration retired); RW-11
zero-round refusal accepted live on the exact walk question.
Sunny's glass clarity check remains the batch's final acceptance.

### 2026-08-28 — Sunny: 1.58.5 wheel PUBLISHED
Dev: fire the rerun (300→800) so the sweep why-sentences mint into
the store. Then Sunny's glass check + script QA gate verbatim →
capture.

### 2026-08-28 — 1.58.5 CYCLE COMPLETE: the capture gate's dev side is CLOSED
Rerun green end to end on the published 1.58.5; VERIFIED IN STORE:
all 26 clusters carry the sweep-authored why-sentence ("2
procedures share the name 'A1c_High' but compute 2 different
logics — one name is doing 2 jobs"), zero missing the stamp;
four-way verification green. Everything the capture gate names on
the dev side is now LIVE: RW-5 answer-first + RW-7/RW-1 flag cards
+ RW-9/RW-10 machine-composed conclusion + RW-11 zero-round policy
refusal (workbench, shared tree) and the store's why-sentences
(1.58.5 mint). REMAINING FOR CAPTURE: Sunny's glass check of the
two presentation batches + the DEMO_SCRIPT QA gate run verbatim
(fresh conversation per question) — wobbles fix-forward, then film.

## ORDER RW-BATCH-3 (glass-check finds; QA-BLOCKING)
1. **RW-13 (REGRESSION, mandatory):** codeset sameness beat broke
   tonight — compare blocked twice by a guard after a semantic-
   search route (details in WALK_VERDICTS_SHAPES.md). Repro
   headlessly, read the guard detail, fix; acceptance = afternoon
   behavior restored (DIFFERS + E11.80 machine diff lines).
2. **RW-12:** flag cards must carry flag IDENTITY + MEMBER NAMES
   (not bare counts — Sunny's ruling) + the sweep why-sentence
   (store has them; suspect projection missing the new fields).
Capture waits on both + fresh QA gate.

## ORDER PHASE2-SLICE-1 (the run layer — AFTER RW-BATCH-3; overnight-authorized by Sunny)
Build against **ADR 0061 (DRAFT)** — docs/decisions/0061-the-run-
layer.md. Slice 1 stays entirely on ratified ground; Sunny's three
open calls (§6: sample cap default / charts / re-confirm cadence)
do NOT block it — defaults: cap 200, NO charts, re-confirm each
run (the conservative choices; her rulings can only relax them).
Scope:
1. `run:` source binding in org_config (demo SQL endpoint /
   aivia_shapes_src); local fixture built FROM
   data/shapes/generated/seed/01_schema_and_data.sql (22 INSERT
   batches — the cohort-105 estate) — no tenant dependency in CI.
2. Execute a confirmed STEP's SELECT only: ScriptDom statement-
   type check (single SELECT or typed refusal — parser decides,
   never regex), read-only credential, 30s timeout, TOP 200.
3. Display: results table + machine sampling label ("N rows ·
   TOP 200 · as of <t> · source <db> · read-only"); run stamps
   join the folded receipts.
4. **P5 cage test is the heart of the slice:** prove rows never
   enter model context — model sees count/schema/elapsed stamps
   only. This test is the acceptance.
5. Run + confirm captured as decision events (0056 shape; the
   store side may be minimal/logged for now — the capture must
   exist so the flywheel counts runs from day one).
Typed failures per the error contract. Whole-proc execution,
charts, real-estate PHI output gate: explicitly LATER slices.

### 2026-08-29 — RW-BATCH-3 BUILT (QA-blocking pair closed)
**RW-13 (regression): root-caused + dead.** A NAME passed to
compare kept the name AS its id — the fragment fetch found nothing
and the guard blocked the beat (the semantic route made name-args
likely). Names now resolve to their REAL ids, and a SHARED name
resolves to EVERY carrier (collisions anchor wholly — the
parse-plan lesson landed in the algebra). 2 L0 tests; live
acceptance: guard-free runs, and the compare route delivered
**DIFFERS with E11.80 distilled to the card's FIRST line** ("+
E11.80 — present only in one definition") — the delta no longer
buried at the end of two 80-literal lines (deterministic
set-arithmetic over quoted literals, identical wording every run).
**RW-12: identity + why-sentence + MEMBER NAMES on every flag
row/card.** The census row shaping was dropping identity and
description (the store had them — the projection was fine); both
now ride, plus member names via a bulk 2-hop member_of query (one
query, all clusters, NO wheel cycle needed — query-side only,
workbench-live). Cards render names, not bare counts.
0061 registered as a sanctioned draft. Gates: 1,168 green + ruff.
**Remaining before capture: fresh QA gate per the script (Sunny/
review). Then PHASE2-SLICE-1 per the overnight order.**

### REVIEW VERDICT — RW-BATCH-3: VERIFIED
Gates review-side: 1,168 passed + 5 xfailed, ruff clean — matches.
Root cause quality noted: name-args now resolve to real ids and a
shared name anchors EVERY carrier — the parse-plan lesson landed
in the op algebra itself, ahead of 0060's build. E11.80 distilled
to the card's first line via deterministic set-arithmetic; RW-12
fields ride query-side (no wheel cycle). Both live acceptances
accepted as claimed. **The two beats are now Sunny's morning
re-walk + the fresh QA gate; dev is clear to proceed to
PHASE2-SLICE-1 per the overnight order.**

### 2026-08-29 — PHASE2-SLICE-1 BUILT (ADR 0061 run layer, slice 1) — release 1.59.0
**The run layer runs the confirmed definition — nothing is
generated.** The SQL that executes is the certified step fragment,
byte-for-byte what was displayed; conservative defaults per the
order (cap 200, NO charts, re-confirm each run — Sunny's §6 calls
can only relax them).

**What shipped:**
- `src/run_layer.py` — the gate + the result + the runner.
  `check_single_select`: ScriptDom statement-type check (the
  parser decides, never regex) — exactly ONE SelectStatement;
  UPDATE/EXEC/DROP → typed `not_select` naming the offending type,
  two statements → `multi_statement`, SELECT…INTO → `select_into`,
  unparseable → `parse`. `run_step`: TOP-cap wrap with a +1-row
  probe so **capped is a fact, never a guess**; `RunResult`
  separates DISPLAY rows from `model_stamps()` =
  {row_count, columns, capped, elapsed_ms} — the ONLY
  model-visible shape.
- **THE P5 CAGE (the slice's acceptance): green, both halves.**
  Value half: no seeded cell value (len≥4) appears in the stamp
  blob. Structural half: `run` is NOT in ENGINE_TOOLS — the model
  cannot call it; rows cannot enter model context by construction.
  Endpoint half: the captured TurnEvent carries stamps only —
  asserted no `rows` key in trace/decision.
- `/api/run` (src/webapp/app.py) — body {step_id,
  conversation_id}; the READ GUARANTEE extends to runs (step must
  be retrieval-permitted this conversation → 403 unsurfaced);
  unbound executor → 503 `unconfigured` typed; RunRefusal → 422
  typed with reason_class. Every run captured as a decision event
  (0056 shape): question `[RUN] <step_id>`, made_by
  `deterministic_run`, stamps only — the flywheel counts runs from
  day one. Run button on retrieved step rows renders the results
  table + machine sampling label ("N row(s) · TOP 200 (capped) ·
  elapsed · source · read-only").
- Binding: `RunConfig` in src/config.py + `run:` block read from
  org_config.yaml in src/webapp/main.py `_run_executor()` —
  AzureDirectConnection with an az-cli AAD token
  (database.windows.net scope), 30s/200 defaults. **Currently
  TYPED-UNBOUND** — no `run:` block exists yet, so /api/run
  refuses 503 by design; nothing guesses.
- Fixture provenance: tests build the cohort-105 estate straight
  from `devtools.generate_shape_seed.build_rows()` into in-memory
  sqlite — same rows the seed SQL ships (117 registry rows == the
  oracle), zero SQL-parsing of our own fixture, zero tenant
  dependency in CI.
- Registry: 0061 now cites code (src/run_layer.py +
  tests/test_run_layer.py); its sanctioned-draft exception REMOVED
  from test_trace_registry — totality holds the slice from now on.

**Gates:** 1,182 green + 5 xfailed, ruff clean; TEST_MAP/TRACE_MAP
regenerated; wheel 1.59.0 built + shipped into sql-logic-env
(release-consistency green).

**SUNNY — one local line to bind the demo source (when ready):**
add to org_config.yaml (gitignored; endpoint never in git):
```
run:
  server: <aivia_shapes_src SQL endpoint>.database.windows.net
  database: aivia_shapes_src
```
Restart the workbench; the banner prints "[run layer] bound
read-only to aivia_shapes_src". Until then runs refuse typed —
correct posture. The credential the token maps to should be
READ-ONLY on that DB (db_datareader), per the ADR.

**Explicitly NOT in this slice (per the order):** whole-proc
execution, charts, real-estate PHI output gate, timeout
driver-enforcement verification against the live endpoint.

### REVIEW VERDICT — PHASE2-SLICE-1: VERIFIED
Gates review-side: 1,182 passed + 5 xfailed, ruff clean — matches;
P5 cage test run individually: green. Code conformance to 0061
spot-checked (check_single_select read in full: ScriptDom parse →
exactly one statement → SelectStatement → no INTO → typed
refusals; the parser decides, never regex). Exceeds the order in
two places worth naming: (a) STRUCTURAL cage — run is not an
engine tool at all, so rows cannot reach model context by
construction, stronger than a filter; (b) cap-as-fact via the
+1-row probe — "capped" is measured, never guessed. Typed-unbound
503 = correct posture. One LISTING NOTE carried forward: before
any CUSTOMER source is ever bound, execution must run as a
dedicated read-only principal (db_datareader minimum) — the
statement gate is wall one, the credential is wall two; the demo
estate binding via Sunny's AAD is acceptable for slice 1 only.
Phase 2 slice 1 is DONE pending Sunny's glass run.

## ORDER RW-BATCH-4 (QA-blocking)
1. **RW-15 (mandatory):** sameness-verdict duty — same/differ
   verdicts require a displayed compare basis this turn, else
   floor + continuation pressure toward compare(refs) (the RW-8
   claim-type/evidence-type pattern). Nudge upgraded to turn-grain
   same-kind counting. Acceptance = the codeset question via ANY
   route: DIFFERS + E11.80 machine diff first line.
2. Polish (rides along): schema-qualify member names on flag cards
   when bare names collide.

## FIND RW-16 (turn-key/error-contract; rides next batch, not QA-blocking)
Live field find (Sunny's laptop, run-layer binding): pyodbc +
unixodbc + msodbcsql18 were all absent — the bind failed with no
remediation surfaced. Per the error-contract law, the run layer's
unbound/failed states must DISTINGUISH and NAME their cure:
(a) no run: block → "add run: to org_config"; (b) pyodbc missing →
the pip line; (c) no ODBC driver → the brew/apt lines (incl.
`brew trust microsoft/mssql-release`, new brew requirement);
(d) auth/network → the az-login line. Also: driver-stack preflight
belongs in the install/packaging story (delivery-architecture
shelf item) — repeats-across-customers = product signal.
Resolved locally: unixodbc + msodbcsql18 18.6.2.1 installed,
'ODBC Driver 18 for SQL Server' visible to python3.11 and .venv.

### 2026-08-29 — RW-BATCH-4 + RW-16 BUILT — release 1.59.1
**RW-15 sameness-verdict duty (the QA-blocker): built, both
halves.** New caption-gate duty: a same/different VERDICT with >=2
same-kind records displayed this turn and NO compare result on
screen is FLOORED, and the violation NAMES the resolution with the
actual ids — "run compare(refs=[transform:…A:Codeset,
transform:…B:Codeset])" — so the rejection note + continuation
pass carry the pressure toward compare. Claim-type gated on
evidence-type (the RW-8 pattern); the claim lexicon is a policy
invariant on the ANSWER (the _KIND_ABSENCE precedent — P4 bans
question typing, not claim typing) and deliberately excludes the
W6 caveat-echo phrasing so the older duty's own required echo
never trips this one. Data-anchored: language alone (no same-kind
pair on screen) never fires; an ERRORED compare hands off to the
W12b duty (no double-floor of the honest "remains unverified").
**Nudge upgraded to turn-grain:** the co-occurrence tally now
spans the TURN's whole displayed set (OpsSession.turn_kind_ids,
cleared by the engine at each turn start) — the fifth specimen's
two SINGLE retrieves now stamp the route on the second; a prior
turn's record never stamps this turn. 6 duty tests + 2 turn-grain
tests + the existing benign-two-record protections all green.
**Polish: colliding member names schema-qualify** on flag cards —
the W3a mechanism (_qualified_labels) reused; the misnomer card
now renders "USP_Active_Diabetics (reporting.…), USP_Active_
Diabetics (staging.…)". Query carries member_ids alongside names;
stores not returning ids fall back to bare names. 3 tests.

**RW-16 (error-contract, ordered same morning): every run-layer
failure DISTINGUISHES itself and NAMES its cure.**
classify_run_error in src/run_layer.py: pyodbc missing → the pip
line; ODBC driver missing (Can't open lib/IM002/Driver Manager) →
the brew lines (incl. `brew trust microsoft/mssql-release`) + the
apt line; AADSTS/token/authn → the az login line; else typed
"execution" with the message. Wired at BOTH failure sites: bind
time (_run_executor returns the reason; /api/run's 503 carries it
verbatim) and execute time (a driver blowup returns a typed 502
refusal with the cure, never a bare 500). 4 L0 + 2 endpoint tests.
Driver-stack preflight in the install story stays on the
delivery-architecture shelf as ordered.

**GATE CHANGE (flagged for review): endpoint-hygiene scope.**
Sunny's live `run:` binding put the FIRST sanctioned tenant
endpoint into local org_config.yaml, and the gate — which scanned
every file on disk — flagged it. The class the gate kills is "an
endpoint reaches the PUBLIC repo"; the scan now covers exactly the
files that are in git or could enter it (`git ls-files -co
--exclude-standard`), so gitignored files are exempt BY MECHANISM,
not by name — un-ignoring org_config.yaml puts it straight back in
scope. A companion test EARNS the exemption by asserting
org_config.yaml is actually gitignored. The gate's original leak
class (tracked TMDL, stray pastes) remains fully covered.

**Gates:** 1,200 green + 5 xfailed, ruff clean; TEST_MAP/TRACE_MAP
regenerated; wheel 1.59.1 shipped into sql-logic-env.
**Live acceptance remaining (Sunny/review, on glass):** the
codeset question via any route → DIFFERS with the E11.80 machine
diff first line; and a bound run button showing first data.

### REVIEW VERDICT — RW-BATCH-4 + RW-16: VERIFIED
Gates review-side: 1,200 passed + 5 xfailed, ruff clean — matches.
Design conformance noted with approval: the duty is data-anchored
(claim lexicon fires only with >=2 same-kind records displayed —
language alone never floors a benign turn), the floored rejection
NAMES the exact compare(refs) ids (pressure toward the truth, the
RW-8 pattern), errored compares hand to W12b (no double-floor of
honest "unverified"), the nudge is turn-scoped and turn-cleared,
and every run-layer failure now carries its cure at both bind and
execute time. LIVE ACCEPTANCE REMAINING (Sunny, on glass): (1) the
codeset question — expect DIFFERS + E11.80 machine line via any
route; (2) the bound Run button — first data. Then the QA gate.

## ORDER RW-17 + 0060-PROTOTYPE (the structural unblock)
1. **RW-17:** repro the codeset beat's guard-blocked compares
   (Sunny's expand-detail text to follow; suspect census-ref
   compare args or the retry-guard on an identical second call).
   Root-cause and fix the blocking class; also fix the "Answered."
   verdict label on unverified content (claim-class mislabel).
2. **0060 PROTOTYPE, SAMENESS CLASS FIRST (sanctioned by the
   ACCEPTED ADR; your day-scale estimate):** deterministic
   parse→plan for the sameness primitive — entity tokens resolve
   against the name universe (exact tier), a shared name anchors
   ALL carriers, "same/defined the same" → compare over the
   carriers' step fragments. The codeset question becomes the
   first planner-served beat: same parse, same plan, same DIFFERS
   + E11.80 line, EVERY run. QA's codeset beat rides the planner.
   Confirm-parse rendering per Sunny's call 1 (confirm every
   parse) — the parse line renders and awaits the click before
   executing.

### RW-17 ROOT CAUSE (Sunny's expand-detail, on glass)
Skip #1: compare received a CLUSTER id
(cluster:cousin_conflict:metric:308dfb37dfff) → AssemblyError "no
facts found" with MISATTRIBUTED common-causes text (capacity/
shortcut — wrong failure class). Skip #2: retry guard, correct.
Refined order:
- **RW-17a (recommended shape): compare accepts cluster refs by
  MEMBER-EXPANSION** — clusters are nodes (0057); compare(cluster)
  = partition the members' logics. This is the natural flags→
  "are they the same?" path the model instinctively reached for.
  Fallback if too big pre-capture: typed refusal naming the
  members (RW-8 name-the-cure pattern).
- **RW-17b:** AssemblyError classifies id-kind mismatch as its own
  failure class with ITS cure — never the capacity/shortcut text
  for a non-metric id (error-contract: the named cure must be the
  RIGHT cure).
- RW-17c: "Verdict: Answered." on unverified content → correct
  claim-class label (from the FAIL #3 record).
0060 prototype (sameness class) remains the structural fix and
proceeds in parallel as ordered.

### 2026-08-29 — RW-17 + 0060 SAMENESS CLASS LIVE — release 1.60.0
**RW-17a (cluster-id compare — the glass root cause, dead):**
compare now expands a `cluster:` arg to its MEMBERS via the
member_of chain (clusters are nodes, 0057) — compare(cluster)
partitions the members' logics, the exact flags → "are they the
same?" path the model reached for. A memberless cluster refuses
typed. **RW-17b:** an id-kind mismatch (table:/report:/loggroup:
id handed to compare) is now its OWN failure class naming ITSELF
and its cure ("pass metric refs, step ids, or a cluster id — its
members expand") — and AssemblyError joined the visible-error
catch in the engine dispatch, so a data-level "no facts for X"
never again wears the capacity/shortcut infra cure (the
misattribution Sunny saw). **RW-17c:** a SELF-DECLARED non-answer
("remains unverified", "cannot provide a definitive answer") never
files the answered verdict — the budget-apology law extended; the
chip no longer reads "answered (evidence verified)" over honest
give-ups. 3 + 3 tests.

**0060 SAMENESS CLASS LIVE (the structural unblock, as ordered):**
the workbench now parses FIRST. A parse that reads exactly
`same_or_different over {entities}` renders as a purple parse card
— Sunny's call 1, confirm every parse: NOTHING executes until the
click. Confirm → ground (exact-then-contains, collisions anchor
wholly) → compose → execute through the EXISTING algebra in the
conversation's session → stamped results + the machine compare
card (verdict + diff lines; E11.80-class deltas distill first via
RW-13). No model narration anywhere in the path: same parse, same
plan, same DIFFERS line, EVERY run. "Answer without the planner"
falls back to the engine (body flag planner:false); any parser
trouble falls through silently — the engine remains the default
for every other class. Planner results join session.displays so
later engine turns can quote them. Captured as TurnEvents with
question `[PLANNER] …`. **Opt-in at create_app (planner=True only
in production wiring)** so scripted test harnesses and the eval
suite are untouched. 5 endpoint tests.

**Gates:** 1,211 green + 5 xfailed, ruff clean; wheel 1.60.0
shipped into sql-logic-env; docs regenerated.
**The codeset beat now rides the planner** — Sunny's next re-ask
should show: parse card → click → retrieve + compare → DIFFERS
with the E11.80 line. The run button then completes the loop on
the same glass.

### REVIEW VERDICT — RW-17 + 0060 SAMENESS CLASS: VERIFIED
Gates review-side: 1,211 passed + 5 xfailed, ruff clean — matches.
Design conformance excellent on every contested point: cluster
compare = member expansion (0057 doctrine, not a patch); id-kind
mismatch names ITS OWN cure and AssemblyError can never again wear
the infra cure; self-declared non-answers never file "answered";
and the planner honors every 0060 ruling — confirm-every-parse
(nothing executes before the click), exact-then-contains grounding
with whole-collision anchoring, execution through the EXISTING
algebra (the planner is a planner, not a second engine), machine
compare card, silent fallback to the engine for every other class,
opt-in wiring so evals stay untouched. HISTORIC NOTE: this is the
first production question class served by parse-is-the-plan —
ordered, built, and verified within 24 hours of the ADR's
acceptance. LIVE ACCEPTANCE (Sunny): re-ask the codeset question →
purple parse card → click → DIFFERS + E11.80. Then the Run button,
then the QA gate.

### 2026-08-29 — ITERATION-CARD CONVERSION (0062 first task, hold-lift order) — release 1.61.0
**The purple parse card is now the ITERATION CARD.** Per the
accepted loop:
- **SHOW:** grounding runs at PARSE time (a read; reads run
  immediately, ADR 0050) and the card lists what the graph
  actually matched per entity — name, kind, id; collisions anchor
  wholly and every carrier shows; an ungrounded entity says "no
  catalog match" plainly. The human decides on the graph's real
  matches, never on a blind echo of their own words.
- **PROPOSE:** the reading line (deterministic render of the
  parse — the model's only authorship remains the parse itself).
- **ASK, three decision items:** (1) run this plan — unchecked
  matches are PRUNED, and that one confirm ratifies the pruned
  reading (no-nag: its ops then run without further ceremony;
  pruning everything composes no plan → typed parse_refusal,
  never a guessed route); (2) answer without the planner (engine
  fallback unchanged); (3) **THE DEVELOPER DOOR — on the card
  every round, as ruled.**
- **THE DOOR (/api/escalate):** "none of these is right" is not a
  dead end — the full exchange (question, shown matches per
  entity, the rejection, an optional user note) becomes a
  CAPTURED DEMAND: a 0056 deny-shape TurnEvent
  (made_by=user_escalation, answered=false, matched ids in
  ids_read) plus a human summary and a prefilled mailto when
  org_config `escalation: contact:` is set (Teams users paste the
  same summary; the door and the capture exist regardless of the
  contact line). The pending attempt ends at the door.
- EXECUTE: unchanged — the confirmed plan runs through the
  existing algebra; stamped results + machine compare card.

Registry: 0062 exits the sanctioned-draft set (modules + tests
cited). Wiring: escalation contact read from org_config
`escalation: contact:` (optional, gitignored file).
**Gates:** 1,215 green + 5 xfailed, ruff clean; wheel 1.61.0
shipped; docs regenerated.
**Next per the lift order:** review verifies → Sunny glass-checks
the converted codeset beat (expect: understanding card with both
codeset twins SHOWN, prune boxes, three buttons; click → DIFFERS
+ E11.80 as before) → QA gate → CAPTURE.
**SUNNY (optional, one local line):** `escalation:\n  contact:
<your email>` in org_config.yaml puts a working mailto on the
door; without it the door still captures and shows the summary.

### REVIEW VERDICT — ITERATION-CARD CONVERSION (1.61.0): VERIFIED
Gates review-side: 1,215 passed + 5 xfailed, ruff clean — matches.
0062 conformance checked invariant by invariant: SHOW grounds at
parse time and lists the graph's REAL matches (the human decides
on matches, never a blind echo); PROPOSE stays the model's only
authorship; ASK carries the three items with prune-as-decision and
the no-nag single confirm; pruning-to-empty refuses typed (never a
guessed route); the DEVELOPER DOOR is on every card and
/api/escalate captures the full exchange as a 0056 deny-shape
demand with a prefilled mailto. EXECUTE unchanged through the
algebra. 0062 exits the sanctioned-draft set — cited modules and
tests now anchor it. LIVE ACCEPTANCE (Sunny): the converted
codeset beat on glass, then QA gate, then CAPTURE.

## ORDER RW-BATCH-5 (Sunny's glass check of 1.61.0)
1. **RW-18 (QA-BLOCKING; ECHO of the walk-1562 blank-screen class
   → mechanism mandatory):** ~30s blank before the iteration card
   and again after confirm. Fix as a mechanism, not a tune:
   (a) card SKELETON renders immediately ("reading your question…
   matching N entities…"), matches stream in as each grounding
   query lands; (b) per-entity grounding queries run in PARALLEL;
   (c) post-confirm execution shows progressive op status (the
   old stream pattern); (d) INSTRUMENT the latency split (LLM
   parse call vs store queries vs render) and record the measured
   numbers in RESULTS — fix the measured cause.
2. **CARD-EVERYWHERE increment (0062 proper, next after RW-18):**
   every question gets the understanding card — generous
   extraction of entities/kinds/relation words; grounded SHOW for
   whatever matched; when no relation word is recognized, the
   proposed reading is the DEFAULT MAP ("what's connected to
   these"), per the ratified emergent-shape debate; "answer
   without the planner" remains the engine escape on the card.
   Silent engine fallback survives only for questions grounding
   ZERO entities. The two-worlds UX (card sometimes, old engine
   other times) ends.
Note for the lexicon corpus: Sunny — when a question misses the
card or reads wrong, paste the question text; every miss is
exactly the data the flywheel wants.

## RULING (Sunny, 2026-08-29) — REMOVE THE TYPE FIRST; supersedes RW-BATCH-5 item 2's sequencing
Delete the shape-recognition path OUTRIGHT before building its
replacement — no development from the crutch. Concretely:
- The whole-question pattern test (same_or_different template) is
  REMOVED, not wrapped. "same/different" move into the word-grain
  relation lexicon as edge selectors.
- SILENT fallback to the engine ENDS for every question. The
  engine is reachable ONLY via the card's explicit "answer
  without the planner" button. Zero-grounded-entity questions get
  a no-match CARD (no-dead-ends: "no catalog match" + rephrase +
  developer door + engine button) — never a silent route.
- Every question: extract generously → ground → CARD. No
  recognition step exists anywhere.
Build lands only against TESTPLAN_0062.md (below); machine
acceptance green + measured latencies recorded BEFORE Sunny
re-walks (her second directive).

### 2026-08-29 — RW-BATCH-5 + REMOVE-THE-TYPE BUILT — release 1.62.0
Built against TESTPLAN_0062 (no case removed; machine acceptance
green). Two work fronts, one release:

**THE TYPE IS REMOVED (the ruling, executed):**
- The routing layer holds ZERO question-class references —
  `same_or_different` survives only as a word-grain lexicon entry
  in parse_plan (A1 enforced by tests/test_de_typing.py: grep-level
  absence + a structural test that _planner_intercept contains no
  `return None` — no silent route can even be written back in
  without a red test).
- NO SILENT FALLBACK ANYWHERE: parser-down, zero-entity, and
  zero-grounded states each return a CARD (no-match card: rephrase
  + developer door + engine button — B9). The engine is reachable
  ONLY via the card's explicit button (C5; planner:false is its
  wire shape). A3 green: two same-shape questions differ only in
  their groundings — identical mechanics, machine-diffed.
- Lexicon per the plan: `count_rows` joined (how many/count → the
  B10 data-policy proposal: RW-11 refusal wording + "confirm to
  see the definition"; the plan retrieves the record, wandering
  never). reads_or_feeds now serves metric/report anchors via
  retrieve (B6 shape) and probes bare table WORDS via lineage
  (B4 — the W13b non-evidence machinery owns misses).

**RW-18 — THE BLANK SCREEN, MEASURED THEN KILLED:**
- Measured cause (devtools/measure_card_latency.py, live shapes
  store): the containment degradation probed ONE STORE QUERY PER
  TOKEN, serially, on BOTH tiers — an exact MISS cost 15.8s and a
  semantic MISS 29.5s vs ~1.9s hits. That serial fan-out IS the
  ~30s blank.
- Mechanism: NAME_CONTAINS_ANY_TOKEN_QUERY — ONE labeled scan
  returns every any-token match with its matched-token set;
  productive/conjunctive/W11-disjunctive all derive client-side,
  contracts unchanged. Re-measured: **MISS 30.5s → ~5s; cold HIT
  14.5s → ~2-2.7s.** Residual: the serverless Kusto store shows
  occasional single-query spikes (one warm query hit 14s across
  three runs) — store-side variance, covered on glass by:
- Streaming: the card SKELETON renders at parse ("reading your
  question…"), per-entity matches stream in as each PARALLEL
  grounding lands (ThreadPoolExecutor, order-stable, lock-safe
  OpsSession registration — D2 test asserts real overlap);
  post-confirm runs stream op chips at dispatch + results at
  completion (/api/parse/confirm/stream, the ask/stream pattern).
- Latency split rides every card and confirm payload
  (latency_ms: parse/ground/execute) — measured, never guessed.
  Live numbers (3 runs): token ~0.35s · store query ~0.6-0.9s ·
  LLM parse 0.8-2.6s · ground HIT ~1.9-2.7s cold · MISS ~4.7-5.2s.

**FIELD BUG FOUND + FIXED BY THE MEASURE:** the run layer's bind
imported a nonexistent class (AzureDirectConnection) — Sunny's
binding failures were MY wiring, mislabeled "execution". Fixed to
the real factory (create_connection/AadTokenPyodbcConnection),
fresh connection per run (fresh token — the mssparkutils lesson),
and a bind-time probe so the banner reports a FACT:
**"[run layer] bound read-only to aivia_shapes_src (probe
verified)" — THE RUN LAYER IS LIVE.**

**For review's E-battery:** devtools/walk_runner_0062.py — runs
B1–B10 + the six QA questions against a running workbench, records
card/matches/proposal/latency/confirm verdict per question, writes
internal/docs/WALK_TRANSCRIPT_0062.md.
**Gates:** 1,230 green + 5 xfailed, ruff clean; wheel 1.62.0
shipped; SYSTEM_VOCAB amendment recorded (node_id/kind/ref —
schema identifiers).

## ORDER RW-BATCH-6 (E-battery findings; blocks Sunny's walk + QA + capture)
1. **Latency (QA-blocking):** diagnose from the recorded
   per-payload splits (transcript in WALK_TRANSCRIPT_0062.md).
   B2 3-entity ground = 152s live (parallelism not evident);
   executes 20–185s incl. a 185s single retrieve; B2 confirm
   timeout. Reproduce on the PRIMARY instance conditions;
   fix measured causes; budgets stand (card <8s, first op <2s).
2. **Composer shapes:** feeds card (reads_or_feeds → the chain,
   metric→report links) and map card (default-map → connected
   structure). Bare retrieve with kind None is a composer gap,
   never an answer.
3. **Lexicon + kinds:** "another way/other than" → variants;
   kind words (metrics/reports/tables/certified) become KIND
   FILTERS on the plan, never unmatched entities.
4. Fix B4's test to the store's real encounters table name.
Review re-runs the battery after delivery; Sunny walks only on
review-green.

### 2026-08-29 — RW-BATCH-6 BUILT — release 1.63.0
**Item 1 (QA-blocking latency): the live killer was found in the
transport, and it is dead.** Diagnosis from the recorded splits +
code: (a) az_cli_token_provider shelled out to the `az` SUBPROCESS
on EVERY store query (~0.4-2s each) — and concurrent az invocations
SERIALIZE on the CLI's token-cache file lock, which is exactly why
B2's three "parallel" groundings ran like a chain (152s); (b) every
query opened a fresh TLS connection (no keep-alive). Mechanisms:
the token now caches IN PROCESS (40 min, lock-guarded single
refresh — test: the subprocess runs ONCE) and KustoClient holds a
requests.Session. **Live re-measure: token 0 ms cached · ground
HIT warm 0.67s · ground MISS 1.9s (from 30.5s at the start of the
day) · LLM parse ~1-2s.** Residual: the serverless store's one-time
capacity wake (~8.5s first query after idle) — covered on glass by
the streamed skeleton. D3 budgets (card <8s, first op <2s) now hold
outside the wake.
**Item 2 (composer shapes):** FEEDS card — a retrieved report
renders its chain (executes metrics / reads tables / measures /
link_state), data-driven from link fields on displayed rows; MAP
card — multiple records render ALL records with their connections
(the single-record definition card no longer swallows the rest);
composer-gap law enforced: ANY successful retrieve composes a card
(tables/terms included) — kind None is never an answer. Page
renderers for both.
**Item 3 (lexicon + kinds):** "another way / other than" joined the
variants surface forms; KIND phrases ("certified metrics") split
from entities at parse (SYSTEM word-grain set) — they ride the
Parse as filters and never pollute SHOW as missed entities.
**Item 4 (B4):** the battery's table name fixed to the seed's real
ENCOUNTERS; and no-match is now COMPOSE-DRIVEN — a bare table word
composes a lineage probe (its result stamps its own honesty, W13b)
instead of dying at the no-match card.
**Gates:** 1,237 green + 5 xfailed, ruff clean; wheel 1.63.0
shipped. Ready for review's battery re-run; Sunny walks on
review-green, per the order.

## ORDER RW-BATCH-7 (Sunny's first three fresh questions — walk PAUSED again)
1. **RW-19 (page bug):** "Cannot read properties of null
   (addEventListener)" on every no-match card render — the page
   script wires elements absent on that card variant; door
   buttons possibly dead. Fix + add a DOM-LEVEL smoke test (the
   headless battery is API-only and structurally blind to JS;
   the page-JS gate gains a runtime leg — jsdom or equivalent —
   rendering every card variant).
2. **RW-20 (grounding brittleness — violates ratified 0062
   "match maximally, human prunes"):** phrase matching is
   effectively conjunctive; a stray word kills the match.
   "diabetes codeset" must surface Diabetic Codeset via the
   productive tokens; "diabetic patient cohort definition" must
   surface the Diabetic-family candidates. Mechanism: ranked
   disjunctive/productive candidates ALWAYS surface as prunable
   matches (generosity is safe — the confirm card exists);
   token-stem matching (diabet*) at minimum until tier-2 vectors.
3. **RW-21 (kind-only regression):** "what metrics are there" =
   kind filter + zero entities = a VALID census plan (list the
   kind), never a no-entity card. The engine answered this for
   weeks; the kind-filter fix regressed it.
4. **Battery extension:** Sunny's three questions join B-battery
   verbatim (B11-B13) + a kind-only case + near-miss-name cases;
   DOM smoke joins section D.
Sunny walks on review-green of the EXTENDED battery.

### 2026-08-29 — RW-BATCH-7 BUILT — release 1.64.0
**RW-19 (the no-match card crash): root cause was DEV'S OWN guard
landing on the wrong listener** — `if (!j.no_match)` suppressed the
DOOR wire while the null run-button got addEventListener: crash +
dead door on every no-match card. Fixed (door wires on EVERY card;
only the run button is variant-conditional). **The mechanism: the
page-JS gate now has a RUNTIME leg** — tests/webapp/dom_harness.js
(a purpose-built minimal DOM in node, zero dependencies; our markup
is our own) executes the REAL page script and renders EVERY card
variant (understanding, no-match, skeleton+fill, all 7 conclusion
kinds, prose-only, error fold, run-button row), asserting wiring:
door + skip on every card, run button only where a plan composes.
RED-ON-BUG PROVEN: the harness run against the buggy variant fails
with the exact live error. node required (present on ubuntu-latest
CI + dev machines).
**RW-20 (grounding generosity — ratified "match maximally, human
prunes"):** a fourth grounding tier — deterministic STEM morphology
(suffix strip, never a phrase lexicon: diabetes→diabet →reaches→
Diabetic) feeds the ONE labeled any-token scan; ranked candidates
surface as prunable matches (generosity is safe: the confirm card
prunes). "diabetes codeset" now grounds.
**RW-21 (kind-only regression):** "what metrics are there" = kinds
without entities = a CENSUS plan (proposal: "the catalog census of
metrics"; confirm runs census) — never the no-entity card. The
regression my kind-filter fix introduced is dead, test-held.
**Battery extended per item 4:** B11 "diabetes codeset" · B12
"diabetic patient cohort definition" · B13 "what metrics are
there" · B14 "list all reports" (kind-only) · B15 "diabetics
registry" (near-miss name). DOM smoke joined section D.
**Gates:** 1,241 green + 5 xfailed, ruff clean; wheel 1.64.0
shipped. Ready for review's extended-battery re-run; Sunny walks
on review-green, per the order.

## ORDER RW-22 (extended battery: one failure class)
B13/B14: kind-only census plans execute but compose NO card
(conclusion kind None) — the composer-gap law was written as "any
successful RETRIEVE composes"; census escaped the wording. Amend
the law to ANY SUCCESSFUL OP and add the CENSUS CARD: count line +
the rows (name + description), per the format contract. Everything
else in the 21-question battery is healthy: stem tier grounds all
three of Sunny's questions generously (B11 2 codesets + 2 extras,
prunable), B15 near-miss grounds, B2 completes at 8s, DIFFERS
oracles hold. Minor note (non-blocking): B15 "diabetics registry"
matched only the Dashboard — the Diabetes Registry metric family
should join its candidate list; candidate breadth rides tier-2.
Review re-runs the battery on delivery; green → Sunny walks.

### 2026-08-29 — RW-22 BUILT — release 1.64.1
**The census card exists and the composer-gap law is AMENDED to ANY
successful op.** A census (kind-only asks, B13/B14) now composes:
the machine count line (the stamped headline, or count + universe)
plus the rows as name + description (12 shown, "and N more" points
at the full table — fold, never hide). The law's wording bug is
dead: the final composer fallback scans EVERY op's rows, not just
retrieve — a future op with rows composes on arrival, test-held
("any_op_rows_compose"). DOM harness gained the census variant.
B15's candidate-breadth note (Diabetes Registry family joining
"diabetics registry") stays on the tier-2 shelf as review filed it.
**Gates:** 1,243 green + 5 xfailed, ruff clean; wheel 1.64.1
shipped. Ready for review's battery re-run; green → Sunny walks.

## ORDER RW-23 (Sunny's walk find — chars-of-string on the map card)
The card composer iterates the `reads` field as a list when it is
a STRING: "reads: D, I, A, G, N, O" = "DIAGNOSIS_CODES" split into
characters (second record spells MEDICATION_ORDERS). For "what
tables does X use" this garbled field IS the answer — broken.
1. Fix the string/list handling; the reads line renders full
   table names.
2. Battery gains CONTENT assertions (the kind-only-assertion
   blindness): the tables question asserts real table names appear
   in the card payload; add "what tables does metric Active
   Diabetic Patients use" verbatim as B16.
Walk otherwise healthy: census card exact + fast (905ms), both
carriers prunable, latency 1-4s. Sunny's typing question answered
in the record: vocabulary, not typology — compositional reading
lines, tested at grep level.

### 2026-08-29 — RW-23 BUILT — release 1.64.2
**The chars-of-string corpse is dead.** source_tables arrives as a
STRING on metric facts; the map card iterated it and spelled
"DIAGNOSIS_CODES" as "D, I, A, G…" — the garbled field WAS the
tables answer. The composer now normalizes (strings split on
commas, lists pass through, characters never iterate); content
tests assert FULL names render and the char-split can never return.
**Battery per item 2:** B16 verbatim ("what tables does metric
Active Diabetic Patients use") + the runner now PRINTS card CONTENT
(map items with reads/steps, feeds fields, census count_line) so
review's assertions run on real table names, never on kinds alone —
the kind-only-assertion blindness closed.
**Gates:** 1,245 green + 5 xfailed, ruff clean; wheel 1.64.2.
Ready for review's re-run; green → Sunny resumes the walk.

## ORDER RW-24 (Sunny's census read)
1. Card text must never use POSITIONAL language ("the table
   above") — the folded answer-first layout broke every such
   reference. Overflow/enumeration lines LINK the round ref
   instead: "…and 25 more — expand R1 for the full table"
   (refs are already clickable). Sweep all composed text for
   positional words (above/below).
2. OPEN CALL (Sunny rules): corpus probes (Line-Ending Probe A/B,
   Reference Forms Probe, …) in census display — badge as
   `control` with a split count line (review recommends) / leave
   as-is / filter from default census.

## NOTE (data polish, rides next palette touch): reporting
USP_Active_Diabetics description says "joined to an active-status
flag" but the SQL has no JOIN (column filter on DIAGNOSIS_CODES) —
the wording made Sunny correctly suspect a missing table.
Descriptions must not imply structure the SQL lacks; sweep the
palette for "joined" where no join exists.

### 2026-08-29 — RW-24 item 1 BUILT — release 1.64.3
**Positional language is dead in composed text, and the gate that
keeps it dead found a SECOND live instance on its first run.** The
census overflow line now links the round ref ("… and 25 more —
expand R1 for the full table", clickable to the panel); the caption
renderer's headline citation "(R1 headline — shown above)" — a
second positional break under the folded layout the walk had not
hit yet — became "(R1 headline)"; the commentary label reworded
positional-free. A grep gate in the suite holds conclusion.py + the
page template clean of layout-positional phrases permanently.
**Item 2 (probe curation in census display) is SUNNY'S OPEN CALL**
— parked on the board (review recommends: badge probes as
`control` with a split count line).
**Gates:** 1,246 green + 5 xfailed, ruff clean; wheel 1.64.3.

### REVIEW VERDICT — RW-24 (1.64.3): VERIFIED
Gates review-side green; positional-language grep gate in place
(and it caught a second live instance on its first run — the
mechanism earning its keep on day one). Census overflow links the
round ref. Sunny's restart picks it up.

## ORDER RW-25 (Sunny's walk: the idle-wake failure, 8:06 PM)
Store idle ~57 min → grounding queries unanswered → honest
store-error card, BUT:
1. **Auto-retry once** on store-no-answer (idle-wake is a known
   ~10-15s transient); skeleton shows "store waking…" during the
   retry. One retry makes this card never exist.
2. **The named remedy must be a button:** the store-error card
   says "retry" in prose but offers no retry action. No-dead-ends
   = named actions ARE buttons.
3. **Model cause-guessing floored (law):** commentary invented
   "check access or permissions" over a store timeout the guards
   had already diagnosed. Infra causes come from STAMPS, never
   the model — the typed store-wake cure renders; a model
   sentence naming an unfounded infra cause is a floorable claim
   class (extend the honesty gate's claim lexicon).
4. Unit coverage: store-exception → one retry → typed card with
   retry button; fallback ops surfacing the SAME store error
   carry the infra cure verbatim.

### 2026-08-29 — RW-25 BUILT — release 1.65.0
**The idle-wake failure class is closed on all four fronts:**
1. Store-no-answer AUTO-RETRIES ONCE in the grounding path (the
   wake is a known ~10-15s transient) — one retry makes the error
   card never exist; the skeleton shows "store waking from idle —
   retrying…" meanwhile (visible, never a blank).
2. The persistent-failure card carries **retry as a BUTTON**
   ("retry now" re-runs the ask; the named remedy IS an action,
   no-dead-ends) alongside the engine button and the door.
3. **Invented-infra-cause duty (the honesty gate, MANDATORY):** a
   caption naming access/permission/credential trouble floors
   unless a DISPLAYED error or stamp carries that cause — infra
   causes come from stamps, never the model. A stamped-cause echo
   passes; non-infra captions untouched. 3 gate tests.
4. The engine's infra text now names the wake cure first ("the
   store waking from idle — retry in ~15s") so fallback ops
   surfacing the same error carry it verbatim.
Unit coverage per the order: one-failure-then-ground (retry works,
no card), persistent-failure (typed card + retry flag), wake cure
in _infra_error. **Gates:** 1,252 green + 5 xfailed, ruff clean;
wheel 1.65.0.

## ORDER FUZZER-1 (test automation, dev's half) + nightly cold battery (review's half, LIVE)
Review has automated the cold leg: devtools/nightly_battery.sh
runs the full battery COLD (no warm-up — the overnight-idled
store IS the test, RW-25's standing acceptance) daily at ~6:23am,
one summary line/day to internal/docs/NIGHTLY_BATTERY.md, pushed;
FAILs get diagnosed and recorded by review automatically.
(Review-session cron; if the session recycles, re-arm — noted on
the board.)
**Dev builds the PARAPHRASE FUZZER stage:** per run, the LLM
generates N fresh phrasings of the known intents (the automated
Sunny) — assert every phrasing yields a CARD (never silent),
grounding includes the expected ids, oracles hold where planted
(DIFFERS/E11.80 etc.), and every miss is logged as lexicon food.
Wire as devtools/walk_fuzzer.py runnable standalone and as a
battery stage; failures append to the same nightly file.

## ORDERS TIER2-1 + FLYWHEEL-1 (Sunny-authorized start, 2026-08-29 evening; after RW-25 + FUZZER-1)
**TIER2-1 (0060 §2a tier 2, ratified):** semantic candidates from
the description embeddings join the understanding card's SHOW as
RANKED, LABELED (semantic), PRUNABLE matches — nominate-only;
confirm-all makes generosity safe; every accepted/pruned candidate
is a captured decision (lexicon food). Battery: near-miss cases
(B15-class) must surface the intended family.
**FLYWHEEL-1 (0056 mechanism + Ground-Truth Shelf v1):**
aggregate captured decision events (confirm/prune/run/escalate)
into per-item usage weights; cards disclose with provenance
("confirmed N times · run M times — no official designated");
sidebar v1: My definitions / My reports / My questions (replay =
saved operation), single-user, from the existing TurnEvent store.
Promotion mechanics per the ruled ladder (usage threshold +
steward veto) can stub at single-user. Film sequencing remains
Sunny's open call — mechanism only.

### 2026-08-29 — FUZZER-1 BUILT (dev's half of test automation)
**devtools/walk_fuzzer.py — the automated Sunny.** Per run, the
LLM generates N fresh phrasings of the known intents (5 seeded:
codeset sameness w/ DIFFERS+E11.80 oracle, tables-of-metric w/
DIAGNOSIS_CODES content oracle, kind-only census, flags family,
count→policy-refusal proposal). Assertions per phrasing: a CARD
always (silent = instant finding), grounding includes the expected
names, planted oracles hold; every miss logs the PHRASING VERBATIM
— lexicon food, exactly the flywheel's intake. A dead paraphraser
is a finding, never a crash. Standalone CLI (base_url, N) exiting
non-zero on findings + wired as a stage in review's
nightly_battery.sh (fuzzer verdict + findings append to
NIGHTLY_BATTERY.md under the cold-run line). Offline unit coverage
via stubbed paraphraser + fixture estate (green run, grounding
miss→lexicon food, dead LLM→unfuzzed finding, oracle miss).
**Gates:** 1,256 green + 5 xfailed, ruff clean. (No wheel bump —
devtools + review's sh only; engine untouched.)

### REVIEW VERDICT — RW-25 (1.65.0): VERIFIED
Gates review-side green. Auto-retry + retry button + the
causes-from-stamps floor (invented infra diagnoses now a floorable
claim class). The nightly cold battery is its standing live
acceptance — tomorrow ~6:23am is the first scheduled proof.
Dev proceeds: FUZZER-1 → TIER2-1 → FLYWHEEL-1.

### 2026-08-29 — TIER2-1 BUILT — release 1.66.0
**Semantic candidates nominate on the understanding card** (0060
§2a tier 2, ratified): when the exact tier misses, the semantic
result's ranked rows join SHOW as LABELED ("· semantic" on the
checkbox row), PRUNABLE nominations — nominate-only, capped at 3,
zero extra store queries (the tier-2 search already ran).
**Relevance bar, deterministic:** a nomination must share a stem
token with the candidate's name or DESCRIPTION (tier-2's own
data) — no similarity-threshold tuning, and junk phrases still
report honest misses (B9 survives, test-held both directions:
nominations surface for near-miss phrasings; exact hits take zero
nominations).
**Prunes are captured decisions:** confirming with unchecked boxes
now records a [PRUNE] TurnEvent (made_by=user_prune, excluded ids
in ids_read, 0056 shape) — the flywheel counts accepted AND pruned
candidates from day one, per the order.
**Gates:** 1,258 green + 5 xfailed, ruff clean; wheel 1.66.0.
Next in the authorized queue: FLYWHEEL-1.

### REVIEW VERDICT — FUZZER-1: VERIFIED, AND IT BITES
Smoke run (30 phrasings, 6 findings on run one) — the mechanism
works and immediately caught real gaps. ORDER FUZZ-FINDINGS-1:
1. Standalone entry broken (`python devtools/walk_fuzzer.py` →
   ModuleNotFoundError; `-m devtools.walk_fuzzer` works) — fix
   the import path.
2. FIVE sameness paraphrases missed the E11.80 oracle ("have the
   same definitions" / "identical" / "uniformity" / "defined
   uniformly" / "definitions match") — diagnose per phrasing:
   lexicon surface-form gaps vs entity-extraction drift
   ("codesets" alone vs "Diabetic codesets") vs route; extend the
   sameness surface forms accordingly — the fuzzer's misses ARE
   the lexicon food, consume them.
3. One two-relation parse ("defined in the same way?" →
   same_or_different, defines over {...}) hit confirm 422 —
   multi-relation plans must compose or the card must say why.
Findings recur nightly until green (fuzzer is a battery stage).

### 2026-08-29 — FLYWHEEL-1 BUILT — release 1.67.0
**The 0056 mechanism v1 + the Ground-Truth Shelf.** New module
src/flywheel.py (registered under 0056, which exits the
no-modules exceptions):
- **usage_weights:** the captured decision events aggregate per
  item — confirmed ([PLANNER] turns), run ([RUN]), pruned
  ([PRUNE]), escalated ([ESCALATE]); engine-answered reads count
  separately as the weak signal. Missing store = empty, never a
  crash; single-user filtering built in.
- **Card provenance:** definition and map cards now DISCLOSE
  ("confirmed 3× · run 1× — no official designated") — facts from
  the event store stamped by id at answer-finish time; zero-usage
  stays silent; disclosure is additive and never load-bearing
  (OneLake deployments simply omit it, typed).
- **The Ground-Truth Shelf v1:** /api/mine + a folding "my shelf"
  panel — My definitions / My reports (usage-ranked) / My
  questions with a REPLAY button (replay = the saved question
  re-posts; a saved operation, per the order). Single-user, from
  the existing TurnEvent store; refreshes after every turn.
- Promotion mechanics (usage threshold + steward veto, the ruled
  ladder) stub at single-user as ordered — the weights are the
  ladder's input when it lands post-capture.
**Gates:** 1,268 green + 5 xfailed, ruff clean; wheel 1.67.0.
The Sunny-authorized queue (RW-25 → FUZZER-1 → TIER2-1 →
FLYWHEEL-1) is now FULLY DELIVERED.

### 2026-08-29 — FUZZ-FINDINGS-1 BUILT — release 1.67.1
The fuzzer's first six catches, consumed:
1. **Standalone entry fixed** (both walk_fuzzer and
   measure_card_latency bootstrap the repo root — `python
   devtools/walk_fuzzer.py` runs anywhere).
2. **Five missed sameness phrasings became surface forms:**
   identical / equivalent / uniform(ly) / uniformity / matching
   joined the same_or_different line in the parse vocabulary —
   the lexicon food eaten, grep-test-held so the words can never
   silently drop.
3. **Multi-relation plans compose:** identical steps DEDUP
   (order-preserving) — "defined in the same way?"
   (same_or_different + defines) runs ONE retrieve then the
   compare, never a duplicate-op refusal; and when an execution
   step still refuses, the 422 message now leads with the READING
   it was executing ("reading your question as: … — <the op's
   reason>") so the card says why, in context.
**Gates:** 1,270 green + 5 xfailed, ruff clean; wheel 1.67.1.
The nightly fuzzer stage re-judges these nightly until green.
### REVIEW VERDICT — TIER2-1 + FLYWHEEL-1: VERIFIED (worktree, origin state)
Main tree carried dev's live WIP, so verification ran in a clean
worktree at origin/dev: 1,263 passed + 5 xfailed, ruff clean —
the 5 "errors" are the packaging tests wanting the un-built wheel
in a fresh checkout (1,263 + 5 = dev's 1,268 exactly; consistent).
Design conformance: tier-2 nominations are labeled, capped,
prunable, deterministic-bar (no threshold tuning), and B9 honesty
survives both directions; prunes captured as [PRUNE] events.
Flywheel: weights from captured events only, disclosure additive
and typed-omitted where storeless, shelf v1 with replay-as-saved-
operation, promotion stubbed per the ruled ladder. **The entire
Sunny-authorized queue is DELIVERED AND VERIFIED.** Remaining in
flight: FUZZ-FINDINGS-1 (dev's WIP in the shared tree right now,
by the look of parse_plan.py). Sunny's shelf on her return:
probe curation · Run button · film sequencing · capture day.

## OVERNIGHT QUEUE 2 (Sunny-authorized "continue while I'm away", 2026-08-29 night)
Sequence, each review-verified before the next consumes it:
1. **FUZZER-2:** extend the fuzzer to ALL intents (definition,
   flags, feeds, variants, kind-only, data-refusal) with
   per-intent oracles; misses remain lexicon food.
2. **KEYVAULT-1 (code-side only):** secrets resolve from Azure
   Key Vault when an org_config `key_vault:` block exists; file
   fallback otherwise; failures name their cure (RW-16 pattern).
   NO tenant action required or taken — Sunny's click completes
   it later. Closes the ship-readiness secrets gap code-side.
3. **0060-EXPERIMENT-CLOSE:** run the full gating measurement
   (current vs planner incl. Sunny's walk paraphrases), finalize
   PARSE_EXPERIMENT.md with the five metrics — the ADR's gate
   formally closed with data.
PARKED (Sunny's rulings, do NOT build): charts (0061 slice 2),
probe curation, film sequencing, promotion ladder full mechanics,
personas (0038/0058 gates), capture.

### REVIEW VERDICT — FUZZ-FINDINGS-1: PARTIAL (3/5 fixed; loop continues)
Fuzzer re-run on 1.67.1: three sameness phrasings now hit the
E11.80 oracle; TWO still miss ("defined uniformly", "definitions
match") — diagnose whether surface-form or extraction. TWO NEW
flags-intent findings: "governance concerns … patients suffering
from diabetes" → map; "red flags related to governance … diabetic
individuals" → census — flags surface forms/extraction gaps.
**ORDER FUZZ-FINDINGS-2:** consume all four; rides before or with
FUZZER-2 in the overnight queue. Findings recur nightly until
green — the loop is the enforcement.

### 2026-08-29 night — FUZZER-2 BUILT (overnight queue 2, item 1)
The fuzzer now attacks ALL intent classes: definition, feeds, and
variants join the original five (8 intents total, every one with a
planted oracle). New `kind_any` oracle admits the legitimate
data-driven card classes a composed answer can land in (definition
OR map; feeds OR map; flags/census/map for variants) — data-driven
composition means the oracle constrains the SET, never one shape.
Misses remain lexicon food; the nightly stage re-judges. Tests:
intent-class completeness (grep-held) + kind_any judging both
directions. **Gates:** 1,272 green + 5 xfailed, ruff clean. (No
wheel — devtools only.) NEXT on review-green: KEYVAULT-1
code-side.

### 2026-08-29 night — FUZZ-FINDINGS-2 BUILT — release 1.67.2
All four fuzzer misses consumed:
- **"defined uniformly" / "definitions match"** — whole-phrase
  sameness surface forms join the parse vocabulary (the two
  phrasings likely parsed to `defines` alone; the explicit forms
  anchor them to same_or_different — multi-primitive parses also
  compose cleanly since the 1.67.1 dedup).
- **The two flags misses, root-caused as a MECHANISM:** the flags
  census filtered by the user's RAW phrase ("diabetic
  individuals") after grounding had already found the canonical
  record — zero flag rows matched the raw words and the card
  degraded. compose now filters by the grounded record's OWN
  canonical name (_anchor_name), and the flags surface forms gain
  concerns/risks/red flags/governance issues.
Tests: surface-form grep-holds + the canonical-name compose (L0).
**Gates:** 1,274 green + 5 xfailed, ruff clean; wheel 1.67.2. The
nightly fuzzer re-judges; findings recur until green — the loop
is the enforcement, as ordered.

### REVIEW VERDICT — FUZZER-2: CODE VERIFIED (1,272 green, ruff clean); run surfaced a GENERATOR-CLASS find
**FUZZ-FINDINGS-3 (generator clause invoked):** the three sameness
phrasings that PASSED post-1.67.1 ("have the same definitions" /
"identical" / "uniformity") now FAIL the same oracle — same
strings, flip-flopping outcomes across runs = PARSE-LAYER
NONDETERMINISM (LLM extraction variance composing different
plans). Per the ruled clause: no more surface-form patches —
investigate one level up. Direction to evaluate: the relation
lexicon resolves DETERMINISTICALLY on the raw question BEFORE the
LLM's extraction gets a vote (0060's spirit: the parse should be
as deterministic as the plan), and/or parse pinning (temp 0 /
caching per normalized phrasing). Flags-intent catches absent
this run — confirm consumed vs generation variance. KEYVAULT-1
waits behind this; the flip-flop class blocks nothing on glass
(confirm-all covers) but must die before the QA gate re-runs.

### 2026-08-29 night — FUZZ-FINDINGS-3 BUILT (generator clause executed) — release 1.68.0
**The flip-flop class is structurally dead.** Diagnosis confirmed
the generator: the LLM's primitive choice was a stochastic router
wearing a parser's badge — same strings, different plans across
runs. The mechanism one level up, exactly as the clause demands:
- **RELATION_LEXICON is now DATA** (word-grain surface forms per
  primitive) and **detect_relations() is a PURE FUNCTION of the
  question string** — longest-form-wins span claiming ("red
  flags" beats "flags"), primitives ordered by first occurrence.
  The deterministic scan OWNS the primitives; the LLM's
  schema-closed guess survives only as the fallback when the scan
  finds nothing. The LLM keeps exactly ONE freedom — entity
  extraction — and confirm-all covers it.
- **The prompt's vocabulary section GENERATES from the lexicon**
  — one source, drift structurally impossible.
- **Rider find:** multi-relation plans exposed @prev fragility
  (dedup could leave the wrong retrieve as the last result;
  compare then saw one item) — sameness now compares EXPLICIT ids
  (op_compare resolves catalog ids, W12a). The lab-path test
  updated: three relations legitimately read in that sentence;
  the invariant is the compare runs and partitions.
- Determinism tests: the five flip-flop phrasings resolve
  identically every run; battery seeds route deterministically;
  scan-owns/LLM-fallback both directions; prompt⊇lexicon.
**Gates:** 1,279 green + 5 xfailed, ruff clean; wheel 1.68.0.
Parse pinning (temp-0/caching) NOT built — recorded reason: the
oracle variance came from routing, which is now code; entity
variance is confirm-all-covered by design (0062). KEYVAULT-1
next on review-green, per the queue.

### REVIEW VERDICT — FUZZ-FINDINGS-3 (1.68.0): ACCEPTED — STABILITY PROVEN
Double fuzzer run: byte-identical findings across both passes.
The flip-flop class is dead; the deterministic relation pass
holds. Residue = THREE STABLE ordinary bugs → **ORDER
FUZZ-FINDINGS-4:** (a/b) "identical" + "uniformity" sameness
phrasings deterministically miss E11.80 — trace the exact plan
(suspect entity-span extraction pulling "definitions" into
grounding and shifting compare's refs); (c) lexicon collision:
"defined in a different manner" is VARIANTS but bare "different"
claims sameness — variants surface forms must outrank in context.
**KEYVAULT-1 released** (FINDINGS-3 green); FINDINGS-4 rides
alongside. 0060-EXPERIMENT-CLOSE follows.

### 2026-08-30 — FUZZ-FINDINGS-4 + KEYVAULT-1 BUILT — release 1.69.0
**FINDINGS-4, all three stable bugs dead:**
- (a/b) Root cause confirmed as suspected: the LLM extracted
  "definitions" as an ENTITY — a relation word grounding junk
  semantic anchors that shifted compare's refs off the codesets.
  Word-grain rule: an entity made entirely of RELATION-LEXICON
  words is the relation, not a thing — dropped at parse
  (test-held: "identical in their definitions" keeps only the
  codesets entity and reads sameness).
- (c) "defined in a different manner/way(s)" is VARIANTS as
  ruled — multi-word variants forms outrank bare "different" via
  longest-first span claiming; bare "different" still reads
  sameness (both directions test-held).
**KEYVAULT-1 code-side complete:** src/secrets_vault.py —
"keyvault:<name>" strings anywhere in org_config resolve through
the `key_vault: url:` block at config-load; plain configs pass
untouched and never contact a vault. Every failure NAMES ITS CURE
(RW-16 pattern): ref-without-vault-block → the exact YAML to add;
404 → the `az keyvault secret set` line; 401/403 → the Key Vault
Secrets User role; no credential → az login / Fabric token; no
network → check URL/VPN. Token: notebookutils in Fabric, az CLI
on dev machines (the connection.py pattern). KeyVaultConfig joins
the config model; registered under 0007 (deployment). NO tenant
action taken — Sunny's vault click completes the loop later.
**Gates:** 1,288 green + 5 xfailed, ruff clean; wheel 1.69.0.
Remaining in queue 2: 0060-EXPERIMENT-CLOSE (on review-green).

### REVIEW DIAGNOSIS — the two stubborn sameness phrasings (traced live, third-fix-blind-order avoided)
Repro on 1.69.0: reading "defines, same_or_different over
{Diabetic codesets}" → grounding = 2 exact codesets + 3 TIER-2
NOMINATIONS (Diabetic Patients variants) → confirm → compare over
FIVE items → DIFFERS, but the two-largest-groups diff is
codeset-vs-variant (ENCOUNTER_DIAGNOSIS lines), not the twins'
E11.80 delta. The phrasings passed pre-TIER2 and failed after —
the nomination set changed compare's refs across releases (the
"flip-flop" was partly release-flop). Machinery correct; DEFAULT
wrong.
**ORDER RW-26: semantic nominations render DEFAULT-UNCHECKED**
(nominate = offer, never include); exact-tier matches stay
default-checked; auto-confirm and the straight-through click both
honor defaults. Acceptance: the two phrasings ("identical",
"uniformity") hit E11.80 on a DOUBLE run; B11-class nominations
still visible and optable-in. KEYVAULT-1 verdict rides the same
verification pass.

### 2026-08-30 — RW-26 BUILT — release 1.69.1
**Nominate means offer.** Semantic nominations render
DEFAULT-UNCHECKED ("· semantic (opt in)" on the row) and — the
half that matters for the straight-through click — the CONFIRM
SERVER honors the defaults: nominations enter the plan only via
explicit include_ids; exact-tier matches enter unless pruned via
exclude_ids. The 5-way compare that diluted the twins' E11.80
diff (review's live trace — the release-flop's cause) cannot
recur: the straight-through confirm compares exactly the
exact-tier anchors. Both card buttons send include+exclude;
tests hold both directions (straight-through excludes nominations
— or refuses typed when exacts alone cannot compose; include_ids
opts one in). Review's acceptance (the two phrasings hitting
E11.80 on a double run, live) rides their verification pass with
the KEYVAULT-1 verdict.
**Gates:** 1,290 green + 5 xfailed, ruff clean; wheel 1.69.1.

### REVIEW VERDICT — RW-26 + KEYVAULT-1 (1.69.1): VERIFIED — FUZZER FULLY GREEN
Double run: 24 phrasings, ZERO findings, both passes — the entire
catch-list is consumed (E11.80 phrasings hit; variants collision
fixed; stability holds; nominate-means-offer proven). Gates 1,290
+ ruff clean; KEYVAULT-1 code-side verified by its tests (tenant
half awaits Sunny's optional click, by design). Remaining from
overnight queue 2: **0060-EXPERIMENT-CLOSE only.** The nightly
cold battery (6:23am) will be the night's final word.

### 2026-08-30 — 0060-EXPERIMENT-CLOSE DELIVERED (queue 2 complete)
**The gating measurement ran in full on the live shapes store**
(deterministic relation pass in; Sunny's 15 walk phrasings now
EXECUTE through both systems — the harness had loaded them but
never run them; that gap closed with this order). The verdict is
one-directional:
- Route consistency PROPOSED 2/2 vs CURRENT 1/2 · Oracle
  correctness 7/7 vs 5/7 · Floor collapse 0 (by construction) vs
  6 total (1 planted + 5 across the walk phrasings) · Detour load
  recorded per question · Refusal honesty: fails closed vs a
  guessed census · **all 15 walk phrasings composed, zero
  refusals, while CURRENT floored on 5.**
PARSE_EXPERIMENT.md finalized with the five metrics + the GATE
CLOSE section; the 0060 ADR status records EXPERIMENT CLOSED with
the data reference (ratification wording = review/Sunny).
**Gates:** 1,290 green + 5 xfailed, ruff clean. (No wheel — docs
+ harness only.) **OVERNIGHT QUEUE 2 IS FULLY DELIVERED.**

### REVIEW VERDICT — 0060-EXPERIMENT-CLOSE: VERIFIED. OVERNIGHT QUEUE 2 FULLY CLOSED.
Gates 1,290 green + ruff clean; PARSE_EXPERIMENT.md read —
PROPOSED dominates every metric on live data incl. Sunny's 15
phrasings (2-op plans vs 6-op wanders; 9-row answers vs 45-row
dumps; 0 floors vs 6; honest refusal vs census-at-a-poem). The
ADR's gate is closed with data; the architecture the product now
runs is formally justified by its own measurement.

## OVERNIGHT QUEUE 3 (Sunny confirmed: nothing blocks dev — all rulings in)
1. **RUNG2-1 (0058 C2 as ratified — types only):** parameterized
   runs — a certified step with DECLARED parameter sites accepts
   values; validity = ScriptDom AST equality except at those
   sites; any logic deviation refuses as "this becomes your
   variant" (fork language, 0038 path named). Rung stamp on every
   result (C1). Acceptance: change a date/threshold value on a
   shapes step and run; a logic edit refuses typed.
2. **PROC-RUN-1 (0061 deferred slice):** whole-procedure
   execution — wrapping, single-resultset procs first; parameters
   ride RUNG2-1's machinery; multi-statement stays refused typed.
3. Standing: nightly fuzzer findings consumed each morning.
Parked (unchanged): 0056 presentation extras (post-capture per
ruling — Sunny may unsequence if capture drifts); Phase 3 awaits
the access-control ADR (review drafts, someday).

### 2026-08-30 — RUNG2-1 + PROC-RUN-1 BUILT (overnight queue 3) — release 1.70.0
**RUNG2-1 (0058 C2 as ratified — TYPES ONLY):** parameterized runs
live. `check_certified_variant`: validity = ScriptDom TOKEN-STREAM
equality except at literal sites, where the swap must stay within
its type class (numeric↔numeric, string↔string — dates ride string
literals; whitespace/case are never deviations). ANY logic
deviation — operator flip, added predicate, identifier edit,
cross-type swap, structural change — refuses typed as
`variant_fork` with the fork language verbatim: "this becomes your
variant… the 0038 path; the certified original stays untouched."
Parameter sites are DERIVED (every literal position in the
certified fragment is a site) and DISCLOSED per run — the recorded
declaration for the demo estate; explicit per-step declarations
can narrow this later without breakage. **The rung stamp (C1)
rides every result:** /api/run responses carry rung 1 ("certified,
byte-identical") or rung 2 ("certified shape, N parameter value(s)
changed — types only") in the sampling label, the payload, and the
model stamps (rung metadata is provenance, never row data — the P5
cage holds; model_stamps gains only the rung integer).
**PROC-RUN-1 (0061 deferred slice):** a CREATE [OR ALTER]
PROCEDURE whose body is exactly ONE SelectStatement runs via its
extracted body (offset-sliced from the original text, never
regenerated — the parser decides); parameters ride RUNG2-1's
literal machinery on the extracted SELECT; multi-statement bodies
stay refused typed, unchanged.
**Acceptance per the order, test-held:** a date/threshold value
change on a certified step runs at rung 2 with the sites named; a
logic edit refuses with the fork language; the single-SELECT proc
runs; the multi-statement proc refuses. 12 L0 + 5 wire tests.
**Gates:** 1,305 green + 5 xfailed, ruff clean; wheel 1.70.0.
Queue 3 item 3 (nightly findings) standing; queue 3 otherwise
COMPLETE pending review.

### REVIEW VERDICT — RUNG2-1 + PROC-RUN-1 (1.70.0): VERIFIED. QUEUE 3 COMPLETE.
Gates review-side: 1,305 green + ruff clean — matches. Contract
conformance to the freshly ratified C1/C2 checked: token-stream
equality with type-class-held literal swaps only; every deviation
refuses as variant_fork WITH the fork language; rung stamps ride
label + payload + model stamps (rung integer only — P5 holds);
derived-and-disclosed parameter sites are a sound demo-estate
reading of "declared" (explicit declarations can narrow later,
recorded). Proc bodies run offset-sliced, never regenerated — the
parser decides, per law. Self-service data is now: run it, change
a VALUE and run it, never change the LOGIC without it becoming
yours. The night's queue is done; standing guards only until
morning.

## ORDER GRAPH-PANEL-1 (Sunny's direction, 2026-08-29 night: show the inner workings)
Right-panel SUBGRAPH VISUAL per answer — the emergent shape (0062)
rendered as itself. Contract:
1. **Receipts only:** the drawing derives EXCLUSIVELY from the
   turn's stamped results — anchors, retrieved records' steps/
   reads/links, flag clusters, and DERIVED edges (compare verdicts)
   drawn distinctly and labeled as computed. Nothing model-claimed
   ever renders. The visual is an honesty instrument.
2. **Deterministic layered layout** (reports | metrics | steps |
   tables columns; stable ordering) — identical answers give
   identical pictures. Dependency-free SVG; DOM-harness gated like
   every card variant.
3. Kind colors · anchor emphasis · CONFLICT flags red-edged · the
   executed step badged with its RUNG stamp on run answers.
4. Click node → its definition card (slice 1 read-only otherwise).
5. Sunny's glass judges legibility (her previous AIVIA had a graph
   visual — her eye is the acceptance).
API: conclusion payload gains `subgraph {nodes, edges}` —
machine-composed, P4/P5-safe (ids/names/kinds only, never rows).

### 2026-08-30 — GRAPH-PANEL-1 BUILT — release 1.71.0
**The emergent shape rendered as itself.** Every answer's payload
now carries `subgraph {nodes, edges}` — machine-composed in the
conclusion layer, derived EXCLUSIVELY from the turn's stamped
results (retrieved records + their step/read/link fields; flag
clusters with members; compare verdicts as DERIVED edges drawn
dashed and labeled "(computed)"). Nothing model-claimed can
render — the composer never sees prose. Deterministic by
construction: sorted nodes and edges, test-held (identical turns
→ identical pictures); P4/P5-safe shape (ids/names/kinds/flag
classes only — a structural test pins the node fields).
**The panel:** right-side, dependency-free SVG, layered columns
(reports | metrics+flags | steps+terms | tables), kind colors,
anchors triple-stroked, conflict-flagged nodes and their edges
red, largest-40 disclosure on truncation. **Click a node → its
definition card** via /api/node (read-only; the read guarantee
applies — 403 on unsurfaced ids; subgraph nodes are surfaced by
construction). **A run badges its step with the RUNG stamp** on
the panel (redraw with run info after each run response).
DOM-harness gated like every card variant (3 nodes wire, empty
hides, run badge draws). 4 composer + 2 wire + 2 DOM checks.
**Sunny's eye is the acceptance** — her glass judges legibility;
the layout knobs (column widths, label lengths) are one-line
constants when she wants them different.
**Gates:** 1,311 green + 5 xfailed, ruff clean; wheel 1.71.0.

### REVIEW VERDICT — GRAPH-PANEL-1 (1.71.0): VERIFIED (code + harness)
Gates review-side: 1,311 green + ruff clean — matches. Contract
held on every clause: receipts-only composition (the composer
never sees prose — model claims structurally cannot render);
deterministic pictures test-held; P4/P5-pinned node shape; derived
edges dashed and labeled "(computed)"; click-through respects the
read guarantee; truncation disclosed; DOM-harness gated. **The
final acceptance is Sunny's eye on glass** — her previous AIVIA
had a graph visual; legibility is hers to judge on restart.

### 2026-08-30 — X-RAY-1 BUILT (tier-locked queue item 1) — release 1.72.0
**The wedge exists.** src/xray.py composes the Estate X-Ray from
the certified census + sweep surfaces — THEIR counts (per-kind,
absent surfaces DISCLOSED never zeroed), every red flag with its
identity, class, severity, members, why-sentence, distinct logics
and blast radius, and the AI-READINESS VERDICT: deterministic
sentence assembly keyed on the flag classes (conflict classes =
the hallucination surface: "a name-grounded assistant answers
differently depending on which definition it lands on — this is
why a generic Copilot hallucinates on this estate"). NOT-AI-READY
/ READY-WITH-DISCLOSURES / READY grades, all machine-picked; no
model authors a sentence. The last page is the order form (the
0063 pitch line verbatim). Brand-neutral (product_name()).
**Live sample generated against the shapes estate**
(internal/docs/XRAY_REPORT.md): 37 metrics · 65 steps · 1 report ·
26 flags w/ code basis · NOT-AI-READY — the demo estate's own
x-ray, ready for Sunny's read and the sales-deck screenshot.
**Engagement runbook** (docs/product/XRAY_ENGAGEMENT.md): plain
numbered steps with expected observations, prereqs, the
dormant-or-remove close-out honoring the one-shot promise, and
the order-form note (price = Sunny's parked call).
CLI: devtools/run_xray.py (store lever applies). Registered under
0063 (its first modules). 5 tests incl. determinism, clean-estate
READY, absent-surface disclosure, brand gate.
**Gates:** 1,316 green + 5 xfailed, ruff clean; wheel 1.72.0.
NEXT: BRIDGE-1 stage-1 exporters (on review-green, per the queue).

### REVIEW VERDICT — X-RAY-1 (1.72.0): gates green; ONE BLOCKING FIND (XR-1)
Gates 1,316 + ruff clean; report substance strong (counts,
why-sentences, blast radius, machine-picked verdict, order-form
close). **XR-1 (blocks wedge use):** member lists dedup bare
names — "10 metrics" lists 8 members (the two USP_Active_Diabetics
collapsed); High ED family shows the identical-name twins as one
entry. A paid diagnosis whose count disagrees with its own list
discredits itself. Reuse the W3a qualified-labels mechanism
(RW-BATCH-4's card fix) in the X-ray composer — schema-qualify on
collision, EVERYWHERE members render; add a reconciliation
assertion (len(members listed) == member count) to the X-ray
tests so the class dies. Verify High ED cluster membership
semantics (family-contains vs exact-name) while in there.
BRIDGE-1 may proceed in parallel; XR-1 rides before any real
engagement.

### 2026-08-30 — XR-1 BUILT — release 1.72.1
**The count-vs-list reconciliation, root-caused and dead.** The
live check first: `_member_labels` (the W3a mechanism) reconciles
26/26 clusters on the shapes store — the qualified-label machinery
was NEVER the leak. The report's own composer was: an [:8]
truncation listed 8 of 10 with no disclosure, and the KQL name
list capped at 12 store-side. Fixes: **ALL members render**
(collision-qualified labels straight from the census rows); a
store-side shortfall DISCLOSES ("store lists N of M names"), never
silent; the KQL cap raised 12→64 (bounded, far above any real
cluster). **Live regeneration verifies:** the 10-member Diabetic
family now lists all 10 — the Active_Diabetics twins render
qualified (reporting./reports.) — and zero shortfall disclosures
fire estate-wide. **Membership semantics verified per the order:**
duplicate clusters group by CONTENT (different step names, same
logic — correct); misnomer/family clusters by name/family (ids all
distinct on the live store; the devtool check proved count==labels
on every cluster). Reconciliation assertions test-held both ways
(full list of 10; disclosed shortfall of 8-of-10).
**Gates:** 1,318 green + 5 xfailed, ruff clean; wheel 1.72.1;
XRAY_REPORT.md regenerated live. The wedge is engagement-clean.

### REVIEW VERDICT — XR-1 (1.72.1): VERIFIED
Gates 1,318 + ruff clean; regenerated report reconciles (Diabetic
Patients 10==10, twins qualified; shortfalls disclose; cap
raised). The X-Ray wedge is engagement-ready. **XR-2 (polish,
rides next X-ray touch, non-blocking):** cousin why-sentences at
name-grain clusters say "N metrics" where members are NAMES
("High ED Utilizers": 3 procs, 2 names — twins covered by their
own grain/misnomer flags). Wording should count "named variants"
at name grain so a paying reader never stumbles. BRIDGE-1
exporters next per the queue.

### 2026-08-30 — BRIDGE-1 STAGE 1 BUILT — release 1.73.0
**File-first, as ruled.** src/adapters/file_export.py exports the
review set as NATIVE import files:
- **Collibra Data Intake:** assets CSV (one row per certified
  metric — Name/Full Name/Asset Type/Domain/Description) +
  relations CSV (metric READS table from the parsed edge chain —
  one KQL scan over transform_to_technical, deterministic lineage
  never inferred; edges whose metric is absent from the certified
  census never export — no invented assets).
- **Purview glossary CSV** (the import template's columns):
  certified metrics as terms, **Status=Draft always** — their
  catalog's workflow owns promotion; we never claim Approved on
  their side.
- **Every row provenance-graded** (the Queue law applied to stage
  1): "parsed by <product>, approved by <approver>" — the named
  human who reviews the file before upload. The exporter AUTHORS
  NOTHING: descriptions come from the store verbatim; an empty
  description exports the grade line alone.
**Live export generated** (internal/docs/bridge_exports/): 37
assets · 64 relations · 37 glossary terms from the shapes estate —
**real files in Sunny's hands for her Purview import experiments,
per the order.** CLI: devtools/export_bridge_files.py (store
lever + approver arg). Registered under 0063. 6 tests (grades,
draft status, no-invention, parsed-edges-only, CSV round-trip).
**Gates:** 1,324 green + 5 xfailed, ruff clean; wheel 1.73.0.
NEXT per the queue: CONSOLE-1 (the Inbox) on review-green.

### REVIEW VERDICT — BRIDGE-1 STAGE 1 (1.73.0): gates green; TWO FINDS before Sunny's experiment
Gates 1,324 + ruff clean; template columns correct; Draft-always
correct humility; grades on every row; no-invented-assets held.
**BR-1 (blocking the Purview experiment):** identical-name twins
export as duplicate Name rows — Purview requires unique term
names; the import fails or mauls a twin INSIDE their record.
Fix per doctrine: members of open CONFLICT-severity name flags
export with QUALIFIED names + the conflict disclosed in the
definition text ("N definitions share this name — unresolved") —
uniqueness satisfied, honesty exported, never-gate preserved.
Reconciliation assertion: no duplicate Name in any export.
**BR-2 (value, rides along):** populate Stewards/Experts columns
from the store's steward fields — the template has the columns;
pre-filled stewardship is the product.
Regenerate the live export on fix; Sunny experiments on the
regenerated files.

### 2026-08-30 — BR-1 + BR-2 BUILT — release 1.73.1
**BR-1 (the duplicate-Name class, structurally dead):** colliding
names export QUALIFIED ("ED Sepsis Screening (reporting.USP_…)")
with the collision DISCLOSED in the definition text ("N
definitions share the name — unresolved", citing an open conflict
flag's class when one covers the name) — uniqueness satisfied,
honesty exported, never-gate preserved. `assert_unique_names` is
an EXPORT INTEGRITY GATE inside the exporter itself: a file with
residual duplicate Names raises and never leaves the house.
Relations use the same qualified Head for consistency. The
exporter now reads ONE scan of output_metric_logic (the facts
table — which also delivered BR-2 for free).
**BR-2:** Stewards/Experts pre-fill from the store's
steward/developer fields (the CLI arg is only the storeless
fallback) — pre-filled stewardship is the product.
**Live regeneration for Sunny's experiment:** 37 terms, 37 UNIQUE
names — the six colliding families all render qualified
(Active Diabetics, Diabetes Registry ×3, Diabetic Codeset,
Enrollment Snapshot, High ED Utilizers); 16 rows carry store
stewards. The files in internal/docs/bridge_exports are the ones
to import.
**Gates:** 1,327 green + 5 xfailed, ruff clean; wheel 1.73.1.

### REVIEW VERDICT — BR-1 + BR-2 (1.73.1): VERIFIED — BRIDGE STAGE 1 READY FOR SUNNY
Gates 1,327 + ruff clean. Twins now export qualified with the
conflict disclosed in the definition ("2 definitions share the
name — unresolved, cousin_conflict"); export-integrity gate holds
uniqueness; stewards pre-fill (Dr. Peterson on glass in the CSV).
**SUNNY: the regenerated files in internal/docs/bridge_exports/
are yours to import into your Purview instance** — the glossary
CSV goes in via Governance portal → your glossary → Import terms.
Every row is Draft, graded, and honest about its conflicts.
CONSOLE-1 (the Inbox) is dev's next per the queue.

### 2026-08-30 — CONSOLE-1 BUILT (the tier-locked queue COMPLETE) — release 1.74.0
**The Resolution Console / the Inbox — Tier 2 v1 as ruled.**
- **The landing map is DATA and its totality is LAW:**
  src/console.py holds LANDING_MAP (verb → lands + grade +
  persona, the 0063 total map verbatim) and check_action gates
  every press: an unknown verb refuses with "no action without a
  landing"; a persona mismatch refuses (steward cannot
  approve-technical, developer cannot certify); deny without its
  reason refuses ("deny lands as testimony — it carries its
  reason, always"). Tests hold totality mechanically — the
  trace-registry pattern applied to product actions, as promised
  when the map landed.
- **Every press is a graded 0056 event** ([CONSOLE:VERB] shape,
  grade + landing verbatim in the decision) into the same store
  the flywheel reads; the Inbox FOLDS the events back (latest
  decision wins; compare lands nowhere — evidence only).
- **/console** — the page: persona toggle (steward | developer),
  flag cards (class badge, identity, severity, member names, the
  why-sentence), per-persona verb buttons, decided items sink but
  stay visible with their state and actor. **Compare computes
  live evidence** through the EXISTING algebra (the cluster id
  expands to members per RW-17a; verdict + diff lines + the
  subgraph render in-card).
- **v1 honesty, recorded:** graph-side disposition updates ride
  the next pipeline run from the events; DG writes ride the
  stage-1 file exports — the deliberate v1 shape, not gaps.
**Gates:** 1,344 green + 5 xfailed, ruff clean; wheel 1.74.0.
**THE TIER-LOCKED QUEUE (X-RAY-1 → BRIDGE-1 → CONSOLE-1) IS
COMPLETE** pending review's verification.

### REVIEW VERDICT — CONSOLE-1 (1.74.0): VERIFIED. THE TIER-LOCKED QUEUE IS COMPLETE.
Gates 1,344 + ruff clean; live smoke green (/console 200; inbox
serves the estate's 26 flags with identity/class/severity).
Design conformance at law grade: the landing map is DATA with
totality mechanized (no action without a landing is now a TEST —
the trace-registry pattern applied to the product itself);
persona gates hold; deny carries its reason always; every press
is a graded 0056 event the flywheel reads; compare renders live
evidence through the existing algebra; the v1 shape (dispositions
ride the pipeline, DG writes ride the stage-1 exports) is
recorded honestly, not hidden.
**All four 0063 tiers now have their v1 on disk:** X-Ray
(engagement-ready report), Bridge stage 1 (graded exporters,
files in Sunny's hands), Console (the Inbox, live), Run (rungs
1–2, gated for customer sources). SUNNY'S GLASS: /console awaits
her eye — the launch demo's heart; then the film plan + capture
day close the arc.

## ORDER CONSOLE-2 (Sunny's glass: "not clear HOW they differ")
Compare evidence leads with MEMBER FINGERPRINTS, not the diff:
1. One row per member: qualified name · source tables (reads) ·
   key criterion from its top decision site ("E11% diagnosis
   codes" / "METFORMIN, INSULIN GLARGINE orders") · its RW-6
   description. The difference rendered as rows a steward scans.
2. A distilled contrast line NAMING OWNERS, machine-assembled
   from the fingerprints ("reporting selects by diagnosis codes;
   reports selects by medication orders") — never model prose.
3. The raw diff FOLDS beneath as the receipt, sides labeled with
   member ids (− x · + y); for >2 members, each pairwise diff
   labeled or the per-group exemplar named.
All fields exist in the store (descriptions, reads, decision
sites); composition only. Applies to compare evidence EVERYWHERE
it renders (console cards, workbench answers) — one composer.
Acceptance: Sunny reads the Active Diabetic Patients card and can
say in one breath which member does what.

## CONSOLE-2 AMENDED + ORDER CONSOLE-3 (Sunny's continued glass)
**CONSOLE-2 addition (her codeset screenshot):** literal-set
diffs render as SET-SUMMARY ("79 codes shared · E11.80 only in
CodesetB" — the distiller already computes this); full lists FOLD
as receipt. Never print an 80-item list twice to say one item
differs.
**CONSOLE-3 (new, workflow): certify needs a TARGET and an
OUTCOME.** On any multi-member flag, the certify press opens the
choice a steward actually makes:
1. DESIGNATE OFFICIAL — member picker (radio, qualified names +
   fingerprints); the chosen member becomes the name's canonical
   bearer; lands per the map (glossary/asset for THAT member,
   grade steward-certified); others remain, flagged for
   differentiation.
2. DIFFERENTIATE ALL — all members ruled legitimate distinct
   purposes; disposition resolves with no official; each member
   queued for its own label (the 0054 canonical outcome).
3. CERTIFY ONE DEFINITION — picker, single member's definition
   certified without designating the name's official.
Every outcome is its own [CONSOLE:*] event with target ids in the
decision; the landing map gains the three rows (totality test
extends). Single-member flags skip the picker.
Acceptance: Sunny certifies on the Diabetic Patients cluster and
is ASKED which of the three acts she means, with members
pickable.

### 2026-08-30 — CONSOLE-2 BUILT — release 1.74.1
**Compare leads with MEMBER FINGERPRINTS — one composer, every
surface.** The compare card now opens with one row per member
(qualified name · owner cite · reads · the key criterion from its
top decision site · the RW-6 description), then the
machine-assembled OWNER-NAMED contrast line ("reporting — DX_CODE
LIKE 'E11%'; reports — ORDER_NAME IN ('METFORMIN')") — criterion
first, description-first-clause fallback, never model prose — and
the raw diff FOLDS beneath as the labeled receipt ("receipt: −
<idA> · + <idB>"; >2 groups disclose "largest two diffed"). The
console's compare act now retrieves the members before composing
(fingerprints have their facts); the planner path already did.
DOM harness variant updated. 4 composer tests (fingerprint
fields, owner contrast, receipt label, no-contrast-on-IDENTICAL).
**Gates:** 1,348 green + 5 xfailed, ruff clean; wheel 1.74.1.
Acceptance = Sunny reads the Active Diabetic Patients card in one
breath. CONSOLE-2 amendment + CONSOLE-3 just landed — next.

### REVIEW VERDICT — CONSOLE-2 (1.74.1): VERIFIED (code-side)
Gates 1,348 + ruff clean. Fingerprint rows (qualified name ·
reads · key criterion · description), owner-named contrast
assembled criterion-first with description fallback — never model
prose, labeled folded receipts, one composer on both surfaces,
IDENTICAL suppresses contrast. Sunny's glass check deferred ONE
delivery so she restarts once for CONSOLE-2 + the set-summary
amendment + CONSOLE-3 together — her one-breath read of the
Active Diabetic Patients card plus the certify-asks-which test.

### 2026-08-30 — CONSOLE-2 AMENDMENT + CONSOLE-3 BUILT — release 1.75.0
**Set-summary elision (the codeset screenshot):** literal-set
diffs now LEAD with the machine summary — "79 value(s) shared ·
E11.80 only in <member name>" (sides named from the retrieved
members) — and the full lists stay folded in the receipt. An
80-item list is never printed twice to say one item differs.
**CONSOLE-3 — certify has a TARGET and an OUTCOME.** The landing
map gains the three steward acts (totality test extended to 9
verbs): **designate official** (member picker; the chosen member
becomes the name's canonical bearer; others remain flagged for
differentiation) · **differentiate all** (no official — every
member a legitimate distinct purpose, the 0054 canonical outcome)
· **certify one definition** (picker; certified without
designating the official). Picker verbs REFUSE without their
member ("choose which one you mean"); picked members ride the
decision AND ids_read, but the FLAG stays the fold key (a member
id never becomes a disposition key — test-held). On glass: the
certify press on a multi-member flag opens the chooser (radio
member list from the store's qualified labels + the three outcome
buttons); single-member flags skip the picker, as ordered.
**Gates:** 1,353 green + 5 xfailed, ruff clean; wheel 1.75.0.
Acceptance = Sunny certifies on the Diabetic Patients cluster and
is ASKED which act she means. One restart picks up 2+3 together.
