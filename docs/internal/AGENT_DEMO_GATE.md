# Demo QA Gate — the four pre-capture questions

Model: env SQA_LLM_MODEL | Eventhouse: probe-eh | multi-turn, real function calling.

## gate_a_headline

*Expectation:* business-name answer + dashboard link + Basis line; SQL on ask

**you>** How is our ED sepsis screening rate calculated?

The ED sepsis screening rate is calculated as part of the "ED Sepsis Screening" metric. Here are the key components of how it is determined:

- The metric includes emergency department encounters for patients with sepsis and collects detailed patient demographics, clinical scores, and blood pressure measurements.
- Only encounters with a valid patient identifier and an admission to the hospital (indicated by a non-null admission time) are included.
- Encounters that are pending or canceled are excluded.
- It considers flowsheet measurements for the R HS IP Sepsis Score 2019 recorded between the patient's arrival and departure from the emergency department.
- Only blood pressure measurements recorded during the patient's visit are included, with specific systolic BP percentiles for the relevant age groups.
- Patients aged 21 days or younger are flagged appropriately.

For more detailed information or to see how these elements come together, you can visit the report: [ED Sepsis Screening Dashboard](https://app.fabric.microsoft.com/groups/1f55e1c1-b660-4715-9b56-4140edce3940/reports/817a4f22-f2f4-4e43-b198-a2d8c1191c9e).

`Basis: search('ED sepsis screening rate') -> 12 candidates shown; facts[reporting.USP_ED_Sepsis]`

*(7.8s; tools: search_catalog -> get_facts)*

**you>** show me the SQL

Here is the SQL for the ED sepsis screening metric:

```sql
-- Final
SELECT
    [BasePop].PATIENT_MRN AS MRN,
    [BasePop].PATIENT_NAME AS PATIENTS,
    [BasePop].[Ethnic Group],
    [BasePop].[Race],
    [BasePop].ENCOUNTER_ID AS ENC_ID,
    [BasePop].AGE_MONTHS AS [Age at ED Arrival (Months)],
    [BasePop].AGE_YEARS AS [Age at ED Arrival (Years)],
    [BasePop].AGE_IN_DAYS AS [Age In Days],
    CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN 1 ELSE 0 END AS [Age in Days Count],
    CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN '<= 21 Days' ELSE '> 21 Days' END AS [Age in Days Indicator]

-- BloodPressure
SELECT
    ENCOUNTER_ID,
    FLO_MEAS_ID,
    RECORDED_TIME,
    MEAS_VALUE
INTO #BloodPressure
FROM #Flowsheets
WHERE RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME
AND FLO_MEAS_ID IN (
    '95', -- Blood Pressure
    '9001140203', -- R EDX GIRLS SYSTOLIC BP PERCENTILE
    '9001140205' -- R EDX BOYS SYSTOLIC BP PERCENTILE
);

-- Flowsheets
SELECT
    [#Base_Pop].INPATIENT_DATA_ID,
    [#Base_Pop].ENCOUNTER_ID,
    [#Base_Pop].ADT_ARRIVAL_TIME,
    [#Base_Pop].ED_DEPARTURE_TIME,
    [#Base_Pop].AGE_MONTHS,
    [#Base_Pop].AGE_YEARS,
    FLO_MEAS_ID,
    RECORDED_TIME,
    MEAS_VALUE,
    MEAS_COMMENT
INTO #Flowsheets
FROM #Base_Pop
INNER JOIN [dbo].FLOWSHEET_RECORDS REC ON [#Base_Pop].INPATIENT_DATA_ID = [REC].INPATIENT_DATA_ID
INNER JOIN [dbo].FLOWSHEET_MEASUREMENTS FSD ON [REC].FSD_ID = [FSD].FSD_ID
WHERE RECORDED_TIME IS NOT NULL AND MEAS_VALUE IS NOT NULL;

-- Base_Pop
SELECT DISTINCT
    HE.ENCOUNTER_ID,
    HE.PATIENT_ID,
    PAT.PATIENT_MRN,
    PAT.PATIENT_NAME,
    REG.NAME AS [Ethnic Group],
    RPR.NAME AS [Race],
    EEF.AGE_AT_ARRIVAL_MONTHS,
    EEF.AGE_AT_ARRIVAL_YEARS,
    HE.INPATIENT_DATA_ID,
    HE.ADT_ARRIVAL_TIME,
    EED.TRIAGE_START_DTTM,
    EED.TRIAGE_END_DTTM,
    HE.HOSP_ADMSN_TIME,
    HE.HOSP_DISCH_TIME,
    HE.INP_ADM_DATE,
    HE.ED_DEPARTURE_TIME,
    HE.ED_DISPOSITION_CODE,
    REDI.NAME AS [Disposition],
    LOC.LOCATION_ABBR AS [Location]
FROM ...;  -- base population query continues here
```

This SQL snippet shows the structure used to compute data related to the ED sepsis screening metric. Note that this is a portion of the complete SQL, which is extensive and may contain additional queries and logic beyond this initial example. If you need further details or specific parts of the SQL, please let me know!

`Basis: facts[reporting.USP_ED_Sepsis]`

*(9.7s; tools: get_facts)*


## gate_bc_drift_and_blast_radius

*Expectation:* computed verdict (6 claims, 5 truths) via content hash, THEN the exact impacted-report list from parsed lineage — never guessed

**you>** Are all definitions of our base population score consistent?

The definitions of the base population score are **not consistent** across the various metrics and calculation steps. Here's a summary:

### Definitions
1. **Distinct Definitions**: There are **5 distinct definitions** for the base population score.
2. **Groups of Definitions**: These definitions fall into separate groups, indicating differing SQL logic:
   - Each group contains steps or metrics that have been defined with different SQL logic.
   - For example, one group has logic for the ED Sepsis Screening Dashboard, while others are related to inpatient sepsis compliance.

### Closer Examination
- The difference between the largest groups of definitions highlights substantial variations in their underlying SQL code, indicating that they are calculated differently.

The inconsistency suggests that the base population score is defined using differing criteria or methodologies across the metrics. Further standardization may be necessary if a unified definition is desired.

`Basis: find_by_name('base population score') -> 0 exact matches; search('base population score') -> 8 candidates shown; same_logic([transform:reports.USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES:Base_Pop_OD_Scores, transform:reports.USP_Severe_Sepsis:Base_Pop_Severe_IP_Scores, transform:reports.USP_Severe_Sepsis:Base_Pop, transform:reporting.USP_IP_SepsisDetails:Base_Pop_OD_Scores, ...]) -> 5 distinct; same_logic([reporting.USP_IP_SepsisScreeningAudit_v1, reports.USP_IP_SEPSIS_COMPLIANCE, reporting.USP_ED_Sepsis]) -> 3 distinct`

*(10.3s; tools: find_by_name -> search_catalog -> check_same_logic -> check_same_logic)*

**you>** which dashboards are impacted?

The following dashboards are impacted by the definitions of the base population score:

1. **ED Sepsis Screening Dashboard**
   - **Report ID**: `report:ED SEPSIS SCREENING DASHBOARD`
   - **Metric**: Associated with the `reporting.USP_ED_Sepsis` metric.

The other metrics, `reporting.USP_IP_SepsisScreeningAudit_v1` and `reports.USP_IP_SEPSIS_COMPLIANCE`, currently do not have any linked dashboards in the semantic model, meaning no reports are directly associated with them at this time.

`Basis: no new lookups — answered from facts already retrieved in this conversation`

*(5.9s; tools: list_report_links -> list_report_links -> list_report_links)*


## gate_d_refusal

*Expectation:* definitions only — clean refusal, no partial answer

**you>** How many patients were screened for sepsis last month?

I cannot provide actual patient counts or row-level data. However, if you have questions about how sepsis screening is defined or calculated within the organization's metrics, I can help with that.

`Basis: no tools consulted`

*(1.1s; tools: (none))*

