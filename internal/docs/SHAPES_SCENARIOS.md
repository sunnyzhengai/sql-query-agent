# Shape corpus scenarios — palette v2 (diabetic), v2 STRUCTURE per Sunny's design order

**Process (Sunny, 2026-08-25): shapes first → lego paths second →
use cases built from legos to instantiate shapes. Status: shapes +
legos + catalog laid out by review; AWAITING SUNNY'S CONFIRMATION,
then this is dev's palette-v2 build order.**

Theme rationale (Sunny): diabetic was chosen BECAUSE each requesting
persona is specialized in their own workflow — the many ways to
define "diabetic patients" are structural, not contrived.

## 1. THE SHAPES (abstract; each SQL pair instantiates one; suite asserts the machine verdict)

| shape | pattern | required machine verdict |
|---|---|---|
| Twin | same CTE name, same logic | NO flag (consistency isn't a crime — false-positive control) |
| Impostor | same CTE name, different logic | misnomer flag; compare DIFFERS |
| Doppelgänger | different names, identical logic | duplicate flag; compare IDENTICAL |
| Cosmetic twin | logic differs only in whitespace/case/CRLF | normalizes IDENTICAL (control) |
| Paraphrase | semantically same, syntactically different | "differs by normalized hash" disclosure — never a semantic claim (boundary cell) |
| Cousins | near-names, divergent logic (Legacy class) | cousin CONFLICT |
| **Codeset drift** (NEW) | same path + structure, different code LIST (80 vs 81 ICD) | compare DIFFERS; diff pinpoints the missing code (steward-story seed) |
| **Path divergence** (NEW) | same concept via different JOIN PATHS (dx/lab/billing/med/proc) | concept-level conflict flags; governed plurality — each variant legitimate per persona/use |
| Extension | B = A + extra filters | metric-grain DIFFERS; STEP-grain hash matches the shared core (reuse inside divergence) |
| Grain shift (D7) | same name; patient-distinct vs encounter/event grain | grain flag — "counts visits vs counts patients" |
| Reference forms | aliased / temp-projection / unqualified-ambiguous / wrong-kind | resolver cells (existing, re-skinned) |
| Chains | linear / diamond / self-ref / cross-schema twins | existing cells, re-skinned |

## 2. THE LEGO LIBRARY (Sunny's EMR paths, formalized)

| persona | path |
|---|---|
| PCP | PATIENTS → ENCOUNTERS → ENCOUNTER_DIAGNOSIS → DIAGNOSIS_CODESET |
| PCP (alt) | PATIENTS → PROBLEM_LIST → DIAGNOSIS_CODESET |
| ED doc | PATIENTS → HOSPITAL_ENCOUNTERS[type=ED] → HOSPITAL_DIAGNOSIS → DIAGNOSIS_CODESET |
| ED doc (labs) | PATIENTS → HOSPITAL_ENCOUNTERS → LAB_ORDERS → LAB_RESULTS → LAB_CODESET |
| OBGyn | PATIENTS → ENCOUNTERS → ENCOUNTER_DIAGNOSIS → DIAGNOSIS_CODESET (O24.4x gestational nuance) |
| Finance | PATIENTS → PROFESSIONAL_BILLING → CPT_CODES → CPT_CODESET |
| Surgeon | PATIENTS → OR_CASES → PROCEDURE_ORDERS[diabetes procs] → PROC_CODESET |
| Surgeon (meds) | PATIENTS → MED_ORDERS → MED_CODESET |
| Scheduling (support) | PATIENTS → APPOINTMENTS (status: completed/cancelled/no-show) |
| Attribution (support) | PATIENTS → PATIENT_PCP_ASSIGNMENT |

Codesets are foundation-layer reference tables (DIAGNOSIS_CODESET
carries ICD-10 incl. E08–E13 + O24.4x; LAB_CODESET the A1c/glucose
tests + thresholds context; MED_CODESET insulin/orals incl.
metformin; CPT/PROC codesets). Reference-vocabulary flags (future
class, ADR 0057) get their seed data here.

## 3. USE-CASE CATALOG (procs dev writes; shapes instantiated in brackets)

Personas: Dr. Peterson (PCP) · Dr. Sullivan (surgeon) · ED medical
director · OBGyn · Finance analyst · Quality & Registry team
(certifying steward). All synthetic.

- **U1 (Sunny):** Dr. Peterson's diabetic patients who cancelled/
  no-showed PCP appointments, last 6 months. [Extension over a
  diabetic base + scheduling lego; patient grain]
- **U2 (Sunny):** Dr. Peterson's diabetic patients with ED visits
  for diabetic-related symptoms, last year. [Path divergence in one
  proc: PCP panel ∩ ED path; SYMPTOM codeset distinct from diabetes
  codeset]
- **U3 (Sunny):** Dr. Sullivan's patients with abnormal pre-op
  diabetes labs. [Path divergence: lab-evidence definition;
  surgeon + lab legos, thresholds]
- **U4 (Sunny):** High ED utilizers, diabetic, no PCP assigned.
  [Grain shift (visit counts per patient) + attribution absence +
  composition]
- **U5:** Gestational pair — "Diabetic Patients (incl. gestational)"
  vs "(excl. gestational)", OBGyn path. [Cousins; BOTH legitimate →
  the accept/label-variant disposition beat]
- **U6:** Finance's diabetic panel from billing (CPT path). [Path
  divergence at its sharpest — the billing-vs-clinical cohort fight]
- **U7:** The Registry rebuild — Quality team's composite any-2-of-3
  (dx, lab, med). [Path divergence resolved by governance; the
  certified-official candidate]
- **U8:** Med-derived cohort, metformin over-count uncorrected.
  [Impostor vs the registry; the deliberately flawed variant the
  demo interrogates]
- **U9:** Codeset-drift pair — two PCP-path procs, 80 vs 81 codes.
  [Codeset drift; the meaning-leads-code demo seed]
- **U10:** Base_Cohort everywhere — each persona's proc opens a
  Base_Cohort CTE from THEIR lego. [Impostor at scale]
- **U11:** "Missed_Appointments" vs "No_Show_Panel" — two
  departments, identical logic, different names. [Doppelgänger]
- **U12:** "High ED Utilizers" twice — patients vs visits under one
  name. [Grain shift as its own conflict]
- **Controls:** one Cosmetic-twin pair and one Paraphrase pair that
  must NOT flag (silence is the assertion).

## The canonical tie-in (Sunny's coherence check, recorded)

Shapes are the BIRTH PATTERNS of the canonical layer: each describes
how name-claims cluster at extraction, and each flag invites a
canonical ACT, never a correction — rest (twins/controls: healthy,
no work), differentiate (impostor/path-divergence/grain: one name
carrying N purposes → labeled variants, officials per scope),
consolidate (doppelgänger: synonyms), link (cousins: family trees),
derive (extension: bottom-up concept hierarchy via step-grain core
matching), repair (codeset drift ONLY — the one cell where
right-vs-wrong exists, routed by the deny grounds). Manifest
expectations therefore assert the CANONICAL OUTCOME per cell
(concept count, claim structure, invited disposition class), not
just the flag. "The sweep doesn't find errors; it finds unlabeled
purposes."

## Build rules for dev (unchanged from v1 where not superseded)

- Palette is a swappable data file; cells/oracles from the built
  matrix stay stable; NEW cells only for D7 (grain — pending
  Sunny's ratification below), Codeset drift, Path divergence, and
  Extension (step-grain core matching).
- Isolation from the realism corpus; oracles by construction in the
  manifest; Echo Law from birth; D2 boundary asserts disclosure.
- SHAPES_GAPCHECK v2 for Sunny + updated demo note (best demo
  cells likely: U9 codeset drift, U6 billing-vs-clinical, U12 grain).

## SUNNY'S CONFIRMATION CHECKLIST

1. Shapes table — complete? anything you've seen in the wild that's
   missing?
2. Lego table names — rename anything that rings false.
3. D7 grain ratified? (U4/U12 depend on it.)
4. Use cases U5–U12 — approve/cut/amend; add any.
5. Persona roster OK?
