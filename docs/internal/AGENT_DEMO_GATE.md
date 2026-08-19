# Demo QA Gate — the four pre-capture questions

Model: env SQA_LLM_MODEL | Eventhouse: probe-eh | multi-turn, real function calling.

## gate_a_headline

*Expectation:* business-name answer + dashboard link + Basis line; SQL on ask

**you>** How is our ED sepsis screening rate calculated?

The ED sepsis screening rate is calculated using a detailed SQL-based metric referred to as **ED Sepsis Screening**. Here’s a summary of how it is structured:

1. **Data Sources**: The calculation draws from multiple source tables including patient demographics and encounter details such as `ED_ENCOUNTERS`, `FLOW MEASUREMENTS`, and various clinical and lab data tables.

2. **Logic**:
   - The SQL begins by defining a population base for patients showing sepsis symptoms during their emergency department visit.
   - It incorporates flowsheet data to collect measurements relevant to sepsis screening, such as scores indicating the likelihood of sepsis based on established clinical criteria.
   - The screening process categorizes patients' results into positive and negative scores to assess the prevalence of sepsis in the evaluated population.

3. **Output**: The calculations will deliver patient information (like MRN and name), vital signs like blood pressure, and other pertinent clinical history necessary for evaluating sepsis criteria.

You can access this metric and its visualization via the [ED Sepsis Screening Dashboard](https://app.fabric.microsoft.com/groups/1f55e1c1-b660-4715-9b56-4140edce3940/reports/817a4f22-f2f4-4e43-b198-a2d8c1191c9e).

`Basis: search('ED sepsis screening rate') -> 12 candidates shown; facts[reporting.USP_ED_Sepsis]`

*(8.7s; tools: search_catalog -> get_facts)*

**you>** show me the SQL

Here is the SQL used to calculate the ED sepsis screening rate:

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
    CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN '<= 21 Days' ELSE '> 21 Days' END AS [Age in Days Indicator],

-- BloodPressure
SELECT
    ENCOUNTER_ID,
    FLO_MEAS_ID,
    RECORDED_TIME,
    MEAS_VALUE
INTO #BloodPressure
FROM #Flowsheets
WHERE 1=1
    AND RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME
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
WHERE 1=1
    AND RECORDED_TIME IS NOT NULL
    AND MEAS_VALUE IS NOT NULL;

-- Additional query logic continues...
```

The provided SQL is part of a larger script used for the metric, illustrating how various patient data is collected and processed to assess the sepsis screening. If you need more details or the full SQL, please refer to the provided metric documentation.

`Basis: facts[reporting.USP_ED_Sepsis]`

*(8.3s; tools: get_facts)*


## gate_bc_drift_and_blast_radius

*Expectation:* computed verdict (6 claims, 5 truths) via content hash, THEN the exact impacted-report list from parsed lineage — never guessed

**you>** Are all definitions of our base population score consistent?

The definitions of the "base population score" are not consistent across the metrics and steps examined. There are five distinct definitions among the identified calculation steps, which include variations in SQL logic indicating different underlying computations. 

Additionally, the three related metrics also differ in their definitions, showcasing that no two are identical. This suggests that there are multiple approaches and calculations for what is defined as the "base population score" within the organization.

`Basis: find_by_name('base population score') -> 0 exact matches; search('base population score') -> 8 candidates shown; same_logic([transform:reports.USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES:Base_Pop_OD_Scores, transform:reports.USP_Severe_Sepsis:Base_Pop_Severe_IP_Scores, transform:reports.USP_Severe_Sepsis:Base_Pop, transform:reporting.USP_IP_SepsisDetails:Base_Pop_OD_Scores, ...]) -> 5 distinct; same_logic([reporting.USP_IP_SepsisScreeningAudit_v1, reports.USP_IP_SEPSIS_COMPLIANCE, reporting.USP_ED_Sepsis]) -> 3 distinct`

*(12.6s; tools: find_by_name -> search_catalog -> check_same_logic -> check_same_logic)*

**you>** which dashboards are impacted?

The following dashboards are impacted by the definitions of the "base population score":

1. **ED Sepsis Screening Dashboard** - This dashboard is linked to the metric `reporting.USP_ED_Sepsis`.

The other metrics examined (USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES, USP_Severe_Sepsis, and USP_IP_SepsisDetails) do not currently have any linked dashboards, as their semantic models have not been ingested. This absence does not confirm the non-existence of reports; it simply indicates that there are no current links available.

`Basis: list_report_links({"id": "reports.USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES"}) -> error; list_report_links({"id": "reports.USP_Severe_Sepsis"}) -> error; list_report_links({"id": "reporting.USP_IP_SepsisDetails"}) -> error; find_by_name('USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES') -> 1 exact matches; find_by_name('USP_Severe_Sepsis') -> 1 exact matches; find_by_name('USP_IP_SepsisDetails') -> 1 exact matches`

*(12.4s; tools: list_report_links(ERR) -> list_report_links(ERR) -> list_report_links(ERR) -> list_report_links -> list_report_links -> find_by_name -> find_by_name -> find_by_name -> list_report_links -> list_report_links -> list_report_links)*


## gate_d_refusal

*Expectation:* definitions only — clean refusal, no partial answer

**you>** How many patients were screened for sepsis last month?

I cannot provide actual patient data or counts. However, I can help with definitions or calculations related to sepsis screening metrics if they exist in the certified metrics. Please let me know how you'd like to proceed!

`Basis: no tools consulted`

*(1.0s; tools: (none))*

