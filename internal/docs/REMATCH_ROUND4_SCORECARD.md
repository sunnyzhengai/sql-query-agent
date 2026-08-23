# Rematch Round 4 — homegrown orchestrator vs Fabric Data Agent

Protocol: fixed questions, ONE run, oracles derived from the store (HANDOFF_REMATCH_ROUND4_GOAL). Homegrown honesty is typed-verdict cross-checked; Fabric honesty is forbidden-claim scanned only (no typed verdict exists on that surface).

Latency p50: homegrown 15.59s · fabric 21.08s

| family | homegrown | s | fabric | s | verdict |
|---|---|---|---|---|---|
| census | PASS | 19.73 | PASS | 14.85 | homegrown |
| definition | PASS | 21.14 | PASS | 21.08 | homegrown |
| bridge | PASS | 14.14 | miss | 21.8 | homegrown |
| bridge | PASS | 45.35 | PASS | 22.96 | homegrown |
| drilldown | PASS | 27.51 | PASS | 23.73 | homegrown |
| lineage | PASS | 15.59 | PASS | 22.03 | homegrown |
| lineage | PASS | 17.3 | miss | 14.49 | homegrown |
| topical_count | PASS | 11.38 | miss | 18.28 | homegrown |
| topical_count | PASS | 8.05 | miss | 12.1 | homegrown |
| sql_request | PASS | 15.59 | PASS | 14.7 | homegrown |
| anaphora | PASS | 11.92 | miss | 25.18 | homegrown |
| anaphora | PASS | 27.21 | PASS | 41.89 | homegrown |
| step_count | PASS | 3.4 | PASS | 13.57 | homegrown |

## Answers (verbatim, truncated 400)

### census — how many metrics are there
- homegrown: There are 28 metrics in the certified catalog. 

Verdict: answered — "28 row(s). Scope: every metric in the certified catalog — the count is exact."
- fabric: There are 28 metrics in the certified metric catalog.

Basis: Counted all rows in the certified metric catalog -> 1 row

### definition — how is Sepsis Case Encounters defined
- homegrown: "Sepsis Case Encounters" is defined by the metric **USP_IP_Sepsis_Encounters**, which measures the total number of inpatient encounters related to sepsis without applying any filtering decisions. 

### Business logic:
- The metric includes all inpatient encounters associated with sepsis.
- The calculation is based on data carried forward from the final selection step.
- There are no filtering or b
- fabric: "Sepsis Case Encounters" (metric ID: reporting.USP_IP_Sepsis_Encounters) is defined as the total number of inpatient encounters related to sepsis. This metric includes all inpatient encounters associated with sepsis, without applying any additional filters or business decision rules.

Key points:
- It counts every unique inpatient encounter where sepsis was indicated, with no further exclusion or 

### bridge — how is Sepsis Case defined
- homegrown: The term "Sepsis Case" is supported by two metrics:

1. **Sepsis Case Details (USP_IP_Sepsis_Details)**: This metric reports on the details of sepsis cases identified in inpatient settings. It includes all inpatient cases of sepsis without applying any filtering decisions, as the data is drawn from a step that carries data forward without filtering, and there are "0 filtering/branching decision si
- fabric: The "Inpatient Sepsis Overview" metric reports the incidence of sepsis in patients based on a comprehensive set of hospital encounter and clinical criteria.

Key points about the metric definition:
- It includes hospital encounters filtered by patient demographics, service dates, and specific clinical criteria.
- The time window is set by the hospital service date, constrained by a start and end d

### bridge — how is IP_SEPSIS defined
- homegrown: The term "IP_SEPSIS" is not defined as a standalone metric, but it refers to a source table read by several certified metrics. These metrics include:

1. **USP_IP_Sepsis_ComplianceMetrics**: Measures the compliance of patients with sepsis screening criteria during their hospital stay.
2. **USP_IP_Sepsis_ComplianceByShift**: Measures compliance with sepsis protocols across different shifts.
3. **US
- fabric: **IP_SEPSIS** refers to metrics used in your system to report and analyze inpatient sepsis incidence, criteria, and compliance. There are several closely related certified metrics using similar names, but the primary regulatory metric for “IP_SEPSIS” is:

---

### **Inpatient Sepsis (Regulatory)**  
**Metric ID:** `reports.USP_IP_SEPSIS`  
**Business Name:** *Inpatient Sepsis (Regulatory)*

#### *

### drilldown — in Severe Sepsis Episodes, how is a patient diagnosed with severe sepsis
- homegrown: Results as displayed. R1: search for 'Severe Sepsis Episodes' (semantic) — 13 row(s). Scope: closest matches by meaning (top 13 of 97 above the similarity floor) plus every name-containment match — NOT an exhaustive list. Not exhaustive. R2: retrieve — 1 row(s). Scope: full certified records for the requested ids. The record(s) list 122 calculation step id(s) — criteria live in the step records, n
- fabric: A patient is diagnosed with severe sepsis in the "Severe Sepsis Episodes" metric when their hospital episode meets a precise set of clinical criteria reflecting both infection and organ dysfunction. The logic involves a complex sequence of steps that check patient records for the presence and timing of key indicators. Specifically:

- Patients must have evidence of infection (such as IV antibiotic

### lineage — which metrics use the IP_SEPSIS table?
- homegrown: Results as displayed. R1: lineage — 5 row(s). Scope: every certified metric whose calculation reads the table 'IP_SEPSIS' — from parsed SQL lineage edges, never name mentions; the count is exact. 5 distinct metric(s): Sepsis Bundle Compliance Metrics, Sepsis Bundle Compliance by Shift, Sepsis Case Details, Sepsis Case Encounters, Sepsis Screening Tool Results. lineage: lineage with identical param
- fabric: The following certified metrics use the IP_SEPSIS table:

- Sepsis Shift Compliance (reporting.USP_IP_SepsisShiftCompliance)
- Sepsis Shift Compliance Metrics (reporting.USP_IP_SepsisShiftComplianceMetrics)
- Sepsis Case Encounters (reporting.USP_IP_Sepsis_Encounters)
- Sepsis Patient Timeline (Legacy v1) (reporting.USP_IP_SepsisPatientDates_v1)
- Sepsis Encounters by Location (Legacy v1) (reporti

### lineage — which metrics filter on the COMPILED_CONTEXT column?
- homegrown: Results as displayed. R1: lineage — 5 row(s). Scope: every certified metric that FILTERS on (decision_to_column) or SELECTS (transform_to_column) the column 'COMPILED_CONTEXT' — parsed lineage edges, never name mentions; counts are exact over recorded edges. Filters on 'COMPILED_CONTEXT': Inpatient Sepsis Details, Inpatient Sepsis Overview, Sepsis Screening Audit, Sepsis Shift Compliance, Severe S
- fabric: No certified metrics in the knowledge base currently filter on the COMPILED_CONTEXT column. This means none of the defined metrics use this column as a filtering criterion.

Basis: Lakehouse search for metrics filtering on COMPILED_CONTEXT → 0 rows

### topical_count — how many metrics are about sepsis
- homegrown: There are 28 metrics related to sepsis in the certified catalog, as confirmed by the result: "R2: census of kind 'metric' — 28 row(s). Scope: every metric in the certified catalog — the count is exact."
- fabric: There are 8 certified metrics specifically about sepsis in the catalog. These cover both inpatient and emergency department (ED) sepsis, compliance, screening, and regulatory reporting.

Here are the main sepsis-related metric categories:
- Inpatient Sepsis Overview
- Inpatient Sepsis Details
- ED Sepsis (Regulatory and Screening)
- Sepsis Shift Compliance Metrics
- Sepsis Summary Report (Regulato

### topical_count — how many metrics contain ED logic
- homegrown: There are 2 metrics that contain "ED" in their definitions. 

The metrics are:
1. **USP_ED_Sepsis** (Business Name: ED Sepsis Screening)
2. **USP_ED_Sepsis** (Business Name: ED Sepsis (Regulatory))

These metrics are related to emergency department encounters for sepsis-related criteria and reporting.
- fabric: There are no certified metrics that mention "ED" or "emergency department" in their metric name, business name, calculation logic, or description.

Basis: Searched for metrics mentioning "ED" or "emergency department" in key fields -> 0 rows

### sql_request — show me the sql of Sepsis Case Encounters
- homegrown: The SQL for the Sepsis Case Encounters metric (USP_IP_Sepsis_Encounters), which reads from the IP_SEPSIS table, has been confirmed as follows:

```sql
-- __final_select__
SELECT DISTINCT
[PatientName] [PATIENTS]
, [PATIENTMRN] [MRN]
, [EthnicGroup] [Ethnic Group]
, [Race]
, [Location]
, [PATENCENCID] [ENC_ID]
, [AgeMonths] [Age (M)]
, [AgeYears] [Age (Y)]
, [InpAdmDate] [Admit Time]
, [HospDischTi
- fabric: Here is the SQL calculation logic for the certified metric Sepsis Case Encounters (business name: Sepsis Case Encounters):

-- __final_select__
SELECT DISTINCT
[PatientName] [PATIENTS],
[PatientMRN] [MRN],
[EthnicGroup] [Ethnic Group],
[Race],
[Location],
[PATENCENCID] [ENC_ID],
[AgeMonths] [Age (M)],
[AgeYears] [Age (Y)],
[InpAdmDate] [Admit Time],
[HospDischTime] [Disch Time],
[ADTDepartmentName

### anaphora — how many steps does it have
- homegrown: The metric "Severe Sepsis Episodes" consists of **122 calculation steps** involved in its analysis and reporting.
- fabric: I need the name of the metric you're asking about to answer how many steps it has. Could you please specify which metric you want to know about? Basis: No metric specified, so could not execute a search. 0 rows.

### anaphora — in this metric, how is a patient diagnosed with severe sepsis
- homegrown: A patient is diagnosed with severe sepsis in the "Severe Sepsis Episodes" metric through a comprehensive assessment involving multiple criteria defined across various decision sites in the calculation process. The specific diagnostic criteria for severe sepsis include but are not limited to:

1. **Presence of Severe Organ Dysfunction**: This is often indicated by the criteria for organ dysfunction
- fabric: A patient is diagnosed with severe sepsis in the USP_Severe_Sepsis metric through a comprehensive data assembly process designed to ensure clinical accuracy:

- The metric uses 122 calculation steps and considers 427 distinct filtering or decision points to determine if a patient meets criteria.
- Severe sepsis is identified based on clinical indicators extracted from multiple clinical systems (in

### step_count — how many calculation steps does Severe Sepsis Episodes have
- homegrown: Severe Sepsis Episodes, identified as the metric "USP_Severe_Sepsis," includes patients identified through **122 calculation steps**.
- fabric: There are multiple certified metrics related to "Severe Sepsis Episodes," each with a different number of calculation steps: one has 122 steps, and another has 11 steps. If you want to know more about these specific metrics (such as which business definition or report each belongs to), let me know and I can provide more detail.

Basis: How many calculation steps does the Severe Sepsis Episodes met

## Record audit appendix (2026-08-22, hand-added — REVIEW_ROUND4_RECORD_AUDIT.md)

- Fabric's five misses per the machine table: bridge("how is Sepsis
  Case defined"), lineage(COMPILED_CONTEXT false-empty),
  topical_count ×2, anaphora #1. The anaphora miss is
  protocol-shaped: the API adapter has no session, so the pronoun
  arrived without antecedent; the clarification request is good
  behavior scored as a miss.
- The lineage(IP_SEPSIS) row is a Fabric PASS on the 2-of-5
  name-overlap bar. All five names it listed are real certified
  metrics, but 4/5 are not IP_SEPSIS readers per parsed lineage —
  name-cousin association, NOT invention. Sunny's manual UI run of
  the same question routed to GQL and returned the correct 5:
  routing varies run to run.
- Rulers: the Fabric honesty column is a forbidden-claim scan only;
  facts bars are overlap thresholds, not full-list checks. Both
  coarse rulers cut Fabric slack — the asymmetry favors Fabric, so
  the homegrown margin is a floor, not a ceiling.
- This round predates the raw log; answers here are 400-char
  truncations and the untruncated originals were not persisted.
  Future rounds write REMATCH_ROUND4_RAW.jsonl and machine-emit the
  miss characterization.
