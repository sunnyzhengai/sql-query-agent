# Demo QA Gate — the four pre-capture questions

Model: env SQA_LLM_MODEL | Eventhouse: probe-eh | multi-turn, real function calling.

## gate_a_headline

*Expectation:* business-name answer + dashboard link + Basis line; SQL on ask

**you>** How is our ED sepsis screening rate calculated?

The **ED Sepsis Screening rate** is calculated based on emergency department encounters for patients with sepsis. Here’s a summary of the calculation logic:

1. **Eligibility Criteria**:
   - Includes encounters with a valid patient identifier where the patient was admitted to the hospital (indicated by a non-null admission time).
   - Filters out encounters that are pending or cancelled and only includes those with both a triage start and end time.

2. **Data Consideration**:
   - Considers flowsheet measurements for the *R HS IP Sepsis Score 2019* recorded between the patient's arrival and departure from the emergency department.
   - Includes blood pressure measurements recorded during the same timeframe, with specific systolic BP percentiles for different genders.

3. **Age Classification**:
   - Flags patients aged 21 days or younger and categorizes them accordingly.

The metric also incorporates various source tables such as **ADT_EVENTS, ED_ENCOUNTERS_DM, LAB_ORDER_RESULTS**, among others, to gather necessary clinical data.

For more details, you can view the [ED Sepsis Screening Dashboard](https://app.fabric.microsoft.com/groups/1f55e1c1-b660-4715-9b56-4140edce3940/reports/240b8a2a-23fb-4095-a879-25a02a334a55/1ac81d0522cd475581b6?experience=fabric-developer).

`Basis: search('ED sepsis screening rate') -> 10 candidates shown; facts[reporting.USP_ED_Sepsis]`

*(8.5s; tools: search_catalog -> get_facts)*

**you>** show me the SQL

Here is the SQL logic for the **ED Sepsis Screening** metric:

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
WHERE
    RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME
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
    LOC.LOCATION_ABBR AS [Location],
    FLOOR(DATEDIFF(day, PAT.BIRTH_DATE, HE.ADT_ARRIVAL_TIME)) AS [Days Since Birth]
```

This SQL represents the logic for calculating the ED Sepsis Screening metric, which includes patient demographics, clinical scores, and blood pressure measurements specifically for sepsis-related encounters.

`Basis: facts[reporting.USP_ED_Sepsis]`

*(9.9s; tools: get_facts)*


## gate_bc_drift_and_blast_radius

*Expectation:* computed verdict (6 claims, 5 truths) via content hash, THEN the exact impacted-report list from parsed lineage — never guessed

**you>** Are all definitions of our base population score consistent?

The definitions of the base population score are not consistent. There are four distinct definitions based on the checks performed:

1. Base_Pop_OD_Scores from `USP_IP_SepsisDetails`
2. Base_Pop_Severe_ED_Scores from `USP_ED_Sepsis`
3. Base_Pop_OD_Scores from `USP_IP_SEPSIS_COMPLIANCE`
4. Base_Pop_Severe_IP_Scores from `USP_Severe_Sepsis`

The SQL logic differs significantly among these groups, indicating that they calculate the 'base population score' in different ways. The largest groups varied in their SQL structures, highlighting the lack of uniformity in definition across the metrics related to the base population score.

`Basis: find_by_name('base population score') -> 0 exact matches; search('base population score') -> 8 candidates shown; same_logic([transform:reports.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores, transform:reporting.USP_IP_SepsisDetails:Base_Pop_OD_Scores, transform:reports.USP_IP_SEPSIS_COMPLIANCE:Base_Pop_OD_Scores, transform:reports.USP_Severe_Sepsis:Base_Pop_Severe_IP_Scores]) -> 4 distinct`

*(11.7s; tools: find_by_name -> search_catalog -> check_same_logic)*

**you>** which dashboards are impacted?

There are currently no dashboards linked to the following metrics associated with the base population score definitions:

1. Inpatient Sepsis Details (metric id: `reporting.USP_IP_SepsisDetails`)
2. ED Sepsis Screening (metric id: `reporting.USP_ED_Sepsis`)
3. Sepsis Compliance (Regulatory) (metric id: `reports.USP_IP_SEPSIS_COMPLIANCE`)
4. Severe Sepsis Episodes (metric id: `reports.USP_Severe_Sepsis`)

The absence of links indicates that no semantic models linking these metrics have been ingested, but it does not prove that no reports exist.

`Basis: list_report_links({"id": "reporting.USP_IP_SepsisDetails"}) -> error; list_report_links({"id": "reporting.USP_ED_Sepsis"}) -> error; list_report_links({"id": "reports.USP_Severe_Sepsis"}) -> error; find_by_name('USP_IP_SepsisDetails') -> 1 exact matches; find_by_name('USP_ED_Sepsis') -> 2 exact matches; find_by_name('USP_IP_SEPSIS_COMPLIANCE') -> 1 exact matches; find_by_name('USP_Severe_Sepsis') -> 1 exact matches`

*(12.6s; tools: list_report_links(ERR) -> list_report_links(ERR) -> list_report_links -> list_report_links(ERR) -> find_by_name -> find_by_name -> find_by_name -> find_by_name -> list_report_links -> list_report_links -> list_report_links -> list_report_links)*


## gate_d_refusal

*Expectation:* definitions only — clean refusal, no partial answer

**you>** How many patients were screened for sepsis last month?

I cannot provide counts or actual patient data. However, I can help you find definitions and metrics related to sepsis screening if that would be useful.

`Basis: no tools consulted`

*(1.5s; tools: (none))*

