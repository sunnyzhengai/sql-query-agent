# ADR 0060 experiment — CURRENT vs PROPOSED (the measurement that gates the build)

Walk paraphrases: 15 loaded

## u9_codeset_sameness
- Q: Are the two Diabetic Cohort (Coded) definitions the same?
  - PROPOSED: plan `retrieve→compare` — ORACLE MET; rows 9
  - CURRENT:  route `search→search→census→census→compare→retrieve` — ORACLE MET; FLOORED; rows 45 (primary 45)
- Q: Is Diabetic Cohort (Coded) defined the same way everywhere?
  - PROPOSED: plan `retrieve→compare` — ORACLE MET; rows 9
  - CURRENT:  route `search→census→lineage→retrieve` — oracle MISSED; rows 2 (primary 2)

## u6_cousin_flags
- Q: What governance red flags exist for Diabetic Patients?
  - PROPOSED: plan `census` — ORACLE MET; rows 4
  - CURRENT:  route `census` — ORACLE MET; rows 4 (primary 4)
- Q: Any issues or conflicts with Diabetic Patients?
  - PROPOSED: plan `census` — ORACLE MET; rows 4
  - CURRENT:  route `census` — ORACLE MET; rows 4 (primary 4)

## u12_grain
- Q: Are the two High ED Utilizers definitions the same?
  - PROPOSED: plan `retrieve→compare` — ORACLE MET; rows 9
  - CURRENT:  route `search→search→retrieve→compare→compare→lineage` — ORACLE MET; rows 22 (primary 22)

## billing_vs_composite
- Q: How is Diabetic Patients (Billing) different from Diabetes Registry (Composite)?
  - PROPOSED: plan `retrieve→compare` — ORACLE MET; rows 5
  - CURRENT:  route `search→search→compare` — ORACLE MET; rows 5 (primary 5)

## refusal
- Q: write me a poem about the warehouse
  - PROPOSED: plan `(refused)` — ORACLE MET; refused: I could not map that question to the relation vocabulary. I can answer: same/dif; rows 0
  - CURRENT:  route `census` — oracle MISSED; rows 37 (primary 37)

## walk_paraphrases (Sunny's real phrasings — observational)
- Q: Are all the Diabetic codesets defined the same?
  - PROPOSED: plan `retrieve→compare`; rows 9
  - CURRENT:  route `census→search→retrieve→compare→census`; rows 9
- Q: are these 3 metrics using the same definition: High ED Utilizers Without PCP High ED Utilizers (reporting.USP_High_ED_Utilizers) High ED Utilizers (reports.USP_High_ED_Utilizers)
  - PROPOSED: plan `retrieve→compare`; rows 8
  - CURRENT:  route `retrieve→retrieve→retrieve→compare`; rows 5
- Q: what does Active Diabetic Patients (reporting.USP_Active_Diabetics) use to define the patient cohort
  - PROPOSED: plan `retrieve`; rows 3
  - CURRENT:  route `retrieve→lineage`; rows 9
- Q: which metrics use ENCOUNTERS?
  - PROPOSED: plan `retrieve`; rows 1
  - CURRENT:  route `lineage→compare`; rows 11
- Q: What governance red flags exist for Diabetic Patients?
  - PROPOSED: plan `census`; rows 4
  - CURRENT:  route `census`; rows 4
- Q: Which certified metrics feed the Diabetes Registry dashboard?
  - PROPOSED: plan `retrieve`; rows 1
  - CURRENT:  route `lineage→retrieve`; rows 1
- Q: is there another way of defining diabetic patient cohort other than the logic in the Dx_Path, Lab_Path, Med_Path
  - PROPOSED: plan `census`; rows 0
  - CURRENT:  route `search→census→census→census→compare`; FLOORED; rows 38
- Q: Diabetic Codeset
  - PROPOSED: plan `retrieve`; rows 2
  - CURRENT:  route `search→compare`; rows 16
- Q: How many patients are currently in the Diabetic Patients cohort?
  - PROPOSED: plan `retrieve`; rows 4
  - CURRENT:  route ``; rows 0
- Q: diabetes codeset
  - PROPOSED: plan `retrieve`; rows 4
  - CURRENT:  route `search`; FLOORED; rows 13
- Q: diabetic patient cohort definition
  - PROPOSED: plan `retrieve`; rows 4
  - CURRENT:  route `search→compare`; FLOORED; rows 38
- Q: what metrics are there
  - PROPOSED: plan `census`; rows 37
  - CURRENT:  route `census`; FLOORED; rows 37
- Q: what tables does metric Active Diabetic Patients use
  - PROPOSED: plan `retrieve`; rows 2
  - CURRENT:  route `lineage→retrieve`; rows 1
- Q: How is the Diabetic Patients cohort defined?
  - PROPOSED: plan `retrieve`; rows 4
  - CURRENT:  route `search`; rows 16
- Q: Which reports read the Diabetes Registry?
  - PROPOSED: plan `retrieve`; rows 2
  - CURRENT:  route `lineage→retrieve`; FLOORED; rows 1

## Scorecard (the ADR's five metrics)

1. Route consistency (multi-ask intents): PROPOSED 2/2, CURRENT 1/2
2. Oracle correctness: PROPOSED 7/7, CURRENT 5/7
3. Floor collapse: PROPOSED 0 (no author, by construction), CURRENT 1
4. Detour load: per-question rows above (PROPOSED displays only the plan's rows; CURRENT primary vs shown per RW-3 folds)
5. Refusal honesty: see the refusal intent above

Walk paraphrases (15): PROPOSED refusals 0, CURRENT floors 5 — full per-phrasing record above

## GATE CLOSE (0060-EXPERIMENT-CLOSE, overnight queue 2 — 2026-08-30)

Full run on the live shapes store, deterministic relation pass in
(1.69.1), Sunny's 15 walk phrasings EXECUTED through both systems:

- **Route consistency: PROPOSED 2/2, CURRENT 1/2** — the planner's
  plans are identical across paraphrases of an intent; the engine's
  routes are not.
- **Oracle correctness: PROPOSED 7/7, CURRENT 5/7.**
- **Floor collapse: PROPOSED 0 by construction, CURRENT 1 planted
  + 5 floors across the walk phrasings** — six stochastic-author
  corrections the planner cannot need.
- **Detour load:** the planner displays only its plan's rows on
  every question (per-question record above).
- **Refusal honesty: PROPOSED fails closed with the vocabulary
  offer; CURRENT guessed a census at the unmappable question.**
- **Walk phrasings: PROPOSED composed ALL 15 (zero refusals);
  CURRENT floored on 5.**

The measurement the ADR demanded is complete and one-directional:
the parse-is-the-plan path dominates on every metric with data
from the live estate. The experiment that began as a prototype
gate ends with the planner already serving production (0062
card-everywhere) — this record is the ADR's formal closing
evidence. Ratification wording: review/Sunny.
