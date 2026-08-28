# ADR 0060 experiment — CURRENT vs PROPOSED (the measurement that gates the build)

Walk paraphrases: 0 loaded — NOT YET EXTRACTED by review (disclosed; the corpus half runs regardless)

## u9_codeset_sameness
- Q: Are the two Diabetic Cohort (Coded) definitions the same?
  - PROPOSED: plan `retrieve→compare` — ORACLE MET; rows 5
  - CURRENT:  route `search→retrieve→retrieve→compare→compare` — ORACLE MET; rows 10 (primary 10)
- Q: Is Diabetic Cohort (Coded) defined the same way everywhere?
  - PROPOSED: plan `retrieve→compare→retrieve` — ORACLE MET; rows 7
  - CURRENT:  route `census→retrieve→retrieve→compare` — ORACLE MET; rows 7 (primary 7)

## u6_cousin_flags
- Q: What governance red flags exist for Diabetic Patients?
  - PROPOSED: plan `census` — ORACLE MET; rows 4
  - CURRENT:  route `census` — ORACLE MET; rows 4 (primary 4)
- Q: Any issues or conflicts with Diabetic Patients?
  - PROPOSED: plan `census` — ORACLE MET; rows 4
  - CURRENT:  route `census→census` — ORACLE MET; rows 30 (primary 30)

## u12_grain
- Q: Are the two High ED Utilizers definitions the same?
  - PROPOSED: plan `retrieve→compare` — ORACLE MET; rows 5
  - CURRENT:  route `search→search→retrieve→retrieve→compare→compare` — ORACLE MET; rows 21 (primary 21)

## billing_vs_composite
- Q: How is Diabetic Patients (Billing) different from Diabetes Registry (Composite)?
  - PROPOSED: plan `retrieve→compare` — ORACLE MET; rows 5
  - CURRENT:  route `search→search→retrieve→retrieve→lineage→lineage→lineage→lineage→lineage→lineage` — ORACLE MET; rows 36 (primary 36)

## refusal
- Q: write me a poem about the warehouse
  - PROPOSED: plan `(refused)` — ORACLE MET; refused: I could not map that question to the relation vocabulary. I can answer: same/dif; rows 0
  - CURRENT:  route `census` — oracle MISSED; rows 37 (primary 37)

## Scorecard (the ADR's five metrics)

1. Route consistency (multi-ask intents): PROPOSED 1/2, CURRENT 0/2
2. Oracle correctness: PROPOSED 7/7, CURRENT 6/7
3. Floor collapse: PROPOSED 0 (no author, by construction), CURRENT 0
4. Detour load: per-question rows above (PROPOSED displays only the plan's rows; CURRENT primary vs shown per RW-3 folds)
5. Refusal honesty: see the refusal intent above
