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

## RESULTS (dev appends)
