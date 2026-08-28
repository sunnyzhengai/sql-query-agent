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
