# Shape corpus scenarios — palette v2 (diabetic), FOR SUNNY'S REVIEW

**Status: DRAFT by review session 2026-08-25, built on Sunny's
workflow enrichment. Sunny red-pens; dev implements as palette v2
(data-file change; existing cells/oracles stable; new cells only
where marked NEW).**

## The two-axis clinical model (Sunny's enrichment, formalized)

**Axis 1 — care-setting workflow** (each with its own tables, joins,
granularity):
| workflow | reaches patient via | characteristic tables |
|---|---|---|
| Outpatient/PCP visit | encounter dx, flowsheets, labs, meds, problem list | OP_ENCOUNTERS, ENCOUNTER_DX, FLOWSHEET_ROWS, LAB_RESULTS, MED_ORDERS, PROBLEM_LIST |
| ED visit | ED dx, problem list, labs, meds | ED_ENCOUNTERS, ED_DX, LAB_RESULTS, MED_ORDERS |
| Inpatient stay | inpatient dx + all | IP_ENCOUNTERS, IP_DX, LAB_RESULTS, MED_ORDERS, PROBLEM_LIST |
| Surgery | pre-op labs, questionnaires + all | SURG_CASES, PREOP_LABS, PREOP_QUESTIONNAIRES |
| Problem list (standalone) | problem list direct | PROBLEM_LIST |
| Patient registry | curated registry membership | DM_REGISTRY |

**Axis 2 — evidence type**: diagnosis code (ICD-10 E08–E13) ·
problem-list entry · lab (HbA1c ≥ 6.5 / FPG ≥ 126 / random ≥ 200 w/
symptoms) · medication (insulin/orals; METFORMIN CAVEAT: also
prediabetes/PCOS → over-count) · questionnaire self-report ·
gestational exclusion nuance (O24.4x counted vs excluded).

## Personas (metadata only — steward/developer columns; NO auth)

- Dr. Patel — PCP, primary care (outpatient definitions)
- Dr. Okafor — ED medical director (ED definitions)
- Surgical Services (team) — pre-op screening definitions
- Quality & Registry team — DM_REGISTRY steward (the certifying
  steward in the disposition story)
- Finance/Population Health analyst — the encounter-grain
  double-counter (scenario N3)

## Proposed NEW dimension [SUNNY RATIFIES]

**D7 grain**: patient-distinct · encounter-grain · event-grain.
The classic fight: "Diabetic Patients" that actually counts
encounters. Machine-detectable (DISTINCT patient key vs not);
candidate new flag class or compare aspect. 2–3 new cells.

## Scenario catalog (each names its cells)

- **N1 "Diabetic Patients (Registry)"** — DM_REGISTRY membership;
  steward: Quality team. The eventual OFFICIAL in the disposition
  demo. [M-family anchor]
- **N2 "Diabetic Patients (Coded)"** — encounter dx E08–E13 across
  OP+ED+IP unions; developer: Dr. Patel. Same business concept as
  N1, different logic → conflict twin. [M1 cell, enriched]
- **N3 "Diabetic Patients (Utilization)"** — SAME name as N2 in a
  different schema, encounter-grain (no DISTINCT) — the
  double-counter; persona: Finance analyst. [M1 + NEW D7 cell]
- **N4 "Diabetic Patients (Lab Criteria)"** — HbA1c/FPG thresholds
  via LAB_RESULTS joined through OP + preop paths; finds the
  undiagnosed. [M2 cousin family]
- **N5 "Diabetic Patients (Med-Derived)"** — MED_ORDERS
  insulin/orals; carries the metformin over-count IN ITS LOGIC (no
  exclusion) — the deliberately-flawed variant the demo interrogates.
  [M2/M5]
- **N6 "DM Registry (Legacy v1)"** — N1's outdated cousin, pre-2023
  criteria (no O24.4x exclusion). [M3 legacy-cousin cell]
- **N7 gestational nuance pair** — "Diabetes Prevalence (Incl.
  Gestational)" vs "(Excl. Gestational)": O24.4x counted vs
  excluded; both LEGITIMATE → the accept/label-variant disposition
  beat (plurality, not error). [M-family, D2 genuinely-different]
- **N8 Base_Cohort misnomer** — every workflow's proc opens with a
  `Base_Cohort` CTE built its own way (PCP: attributed panel; ED:
  arrival window; Surg: scheduled cases) — the S-family misnomer
  seed, now clinically motivated. [S4/S5]
- **N9 pre-op path** — "Pre-Op Diabetes Screening" reads
  PREOP_LABS + PREOP_QUESTIONNAIRES (questionnaire self-report as
  evidence) — exercises R-family reference forms through a distinct
  join topology; developer: Surgical Services. [R2/R3]
- **N10 semantic-equivalence boundary** — two byte-different,
  logically-identical A1c filters (IN-list vs OR-chain) — D2
  disclosure cell, clinical skin. [S3/M8-class]

## What stays fixed

Cell ids, oracle mechanism, manifest format, isolation from the
realism corpus, deterministic generation. Palette v2 = names, table
vocab, persona rows, and the marked NEW cells (D7 + N3, subject to
ratification).

## SUNNY'S REVIEW CHECKLIST

1. Clinical corrections to paths/thresholds/tables (anything wrong?)
2. Ratify D7 (grain) as a dimension + N3.
3. Persona names/roles OK? (Synthetic, no real names.)
4. Anything missing from the workflow list (e.g., telehealth,
   home-health) worth a scenario — or explicitly excluded-with-reason?
