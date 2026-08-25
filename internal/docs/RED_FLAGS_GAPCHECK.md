# Red-flag sweep — gap-check output for Sunny (ADR 0054 acceptance)

Generated 2026-08-23 by dev from the RECORDED ED-sepsis corpus
(tests/fixtures/recorded — the same 28 parse results the tenant
pipeline holds), business names from data/demo/input_metric_names.csv.
The tenant store gets these rows from `320_red_flag_sweep` on the
combined rerun. Flags DISCLOSE, never gate.

## Conservation (total or lying)

    === GOVERNANCE RED FLAGS (ADR 0054 — flags disclose, never gate) ===
    swept 460 catalog items: 292 in flags, 162 clean, excluded {'no_fragment': 6}
      cousin_conflict/CONFLICT: 9 flag(s)
      misnomer/INFO: 74 flag(s)
      KPI unlabeled divergences: 83 (target: 0 via dispositions, never merges)

## The shapes you said you'd look for

### 1. The Base_Pop misnomer — INFO (proc-local, as ratified)

- `flag:misnomer:step:fa5397ff2e9f`
- 12 catalog steps named Base_Pop, **12 distinct logics** — every proc's base population differs
- blast: 12 (12 parent metric(s) share the step name)
- members (parent metric -> content key):
  - reporting.USP_ED_Sepsis -> `b5edc2393ecd360b`
  - reporting.USP_IP_SEPSIS -> `bceb252a02efa6f2`
  - reporting.USP_IP_SepsisDetails -> `2b9a649faefb0b87`
  - reporting.USP_IP_SepsisEncountersWLocations -> `433c378cb637d79d`
  - reporting.USP_IP_SepsisPatientDates -> `a926fdd5c068107c`
  - reporting.USP_IP_SepsisScreeningAudit -> `24c47264c04564a6`
  - reporting.USP_IP_SepsisShiftCompliance -> `b3b150e98994ce23`
  - reports.USP_ED_Sepsis -> `4c95f3315589f402`
  - reports.USP_IP_SEPSIS -> `0b71859858ea9096`
  - reports.USP_IP_SEPSIS_REPORT -> `b8cd9f684435cb93`
  - reports.USP_NonSevere_Sepsis -> `15f6b33dcb7d5816`
  - reports.USP_Severe_Sepsis -> `380bbb2c7374bb40`
- drill: `gov_red_flags | where flag_id == 'flag:misnomer:step:fa5397ff2e9f' | mv-expand member = todynamic(members)`

### 2. Cousin conflicts — 9 name families (Legacy-v1 class)

- **Inpatient Sepsis Details** (CONFLICT, 2 logics): Inpatient Sepsis Details [reporting.USP_IP_SepsisDetails]; Inpatient Sepsis Details (Legacy v1) [reporting.USP_IP_SepsisDetails_v1]
- **Sepsis Compliance (Regulatory)** (CONFLICT, 2 logics): Sepsis Compliance (Regulatory) [reports.USP_IP_SEPSIS_COMPLIANCE]; Sepsis Nursing Shift Compliance (Regulatory) [reports.USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES]
- **Sepsis Compliance by Shift** (CONFLICT, 2 logics): Sepsis Compliance by Shift [reporting.USP_IP_SepsisShiftComplianceByShift]; Sepsis Bundle Compliance by Shift [reporting.USP_IP_Sepsis_ComplianceByShift]
- **Sepsis Encounters** (CONFLICT, 4 logics): Sepsis Encounters [reporting.USP_IP_SepsisEncounters]; Sepsis Encounters by Location [reporting.USP_IP_SepsisEncountersWLocations]; Sepsis Encounters by Location (Legacy v1) [reporting.USP_IP_SepsisEncountersWLocations_v1]; Sepsis Case Encounters [reporting.USP_IP_Sepsis_Encounters]
- **Sepsis Encounters by Location** (CONFLICT, 2 logics): Sepsis Encounters by Location [reporting.USP_IP_SepsisEncountersWLocations]; Sepsis Encounters by Location (Legacy v1) [reporting.USP_IP_SepsisEncountersWLocations_v1]
- **Sepsis Patient Timeline** (CONFLICT, 2 logics): Sepsis Patient Timeline [reporting.USP_IP_SepsisPatientDates]; Sepsis Patient Timeline (Legacy v1) [reporting.USP_IP_SepsisPatientDates_v1]
- **Sepsis Screening Audit** (CONFLICT, 2 logics): Sepsis Screening Audit [reporting.USP_IP_SepsisScreeningAudit]; Sepsis Screening Audit (Legacy v1) [reporting.USP_IP_SepsisScreeningAudit_v1]
- **Sepsis Shift Compliance** (CONFLICT, 5 logics): Sepsis Shift Compliance [reporting.USP_IP_SepsisShiftCompliance]; Sepsis Compliance by Shift [reporting.USP_IP_SepsisShiftComplianceByShift]; Sepsis Shift Compliance Metrics [reporting.USP_IP_SepsisShiftComplianceMetrics]; Sepsis Bundle Compliance by Shift [reporting.USP_IP_Sepsis_ComplianceByShift]; Sepsis Nursing Shift Compliance (Regulatory) [reports.USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES]
- **Severe Sepsis Episodes** (CONFLICT, 2 logics): Non-Severe Sepsis Episodes [reports.USP_NonSevere_Sepsis]; Severe Sepsis Episodes [reports.USP_Severe_Sepsis]

### 3. Duplicates — 0 found

The corpus holds NO identical-hash pairs under different names —
stated per the acceptance ('at least one duplicate-hash pair IF
the corpus holds one'); the class is live and L0-tested, the
corpus simply has none.

### 4. Full step-misnomer inventory — 74 shared step names (all INFO)

| step name | procs | distinct logics |
|---|---|---|
| __final_select__ | 13 | 13 |
| Base_Pop | 12 | 12 |
| Base_Pop_OD_Scores | 8 | 7 |
| Hypotension | 7 | 7 |
| MainAdmDetails | 7 | 5 |
| SSOrderSet | 7 | 7 |
| BasePopABX | 6 | 6 |
| BasePopBolus | 6 | 6 |
| Base_Pop_ENC_Reason | 6 | 5 |
| Base_Pop_Severe_ED_Scores | 6 | 5 |
| BloodCultureValue | 6 | 6 |
| LacticAcid | 6 | 6 |
| Pressors | 6 | 6 |
| ALLCVLTime | 5 | 5 |
| ECMO | 5 | 5 |
| EncounterWeights | 5 | 4 |
| ETT | 5 | 5 |
| Procalcitonin | 5 | 5 |
| CSF | 4 | 4 |
| CVVH | 4 | 4 |
| Main | 4 | 4 |
| ODPressorPivot | 4 | 3 |
| ODPressorSummary | 4 | 3 |
| OX | 4 | 4 |
| PIV | 4 | 4 |
| … 49 more (all in gov_red_flags) | | |

## Gap-check guidance

- Anything you expected flagged that is NOT here = a sweep gap;
  anything here that should not be = a rule gap. Both become
  fixtures per the walk protocol.
- KPI on the admin surface: unlabeled divergences (currently
  83) -> 0 via dispositions, never merges.
