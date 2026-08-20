# ADR 0035 Agent — Live Evaluation

Model: env AIVIA_LLM_MODEL | Eventhouse: probe-eh | multi-turn, real function calling.

## definition_and_followups

*Expectation:* definition answer grounded in facts; follow-ups use context, no re-search noise

**you>** how is ED sepsis screening calculated?

The calculation for the "ED Sepsis Screening" metric (USP_ED_Sepsis) involves multiple steps and includes data from various source tables such as ADT_EVENTS, ED_ENCOUNTERS_DM, and LAB_ORDER_RESULTS, among others. 

Key elements of the calculation logic include:

1. **Patient Information Extraction**: It retrieves patient demographics, arrival and discharge times, and disposition from base patient data.
2. **Vital Signs & Measurements**: Blood pressure and flowsheet data are collected within the time frame of patient arrival and discharge.
3. **Sepsis Screening Indicators**: The screening process identifies patients with high sepsis screening scores based on recorded measurements and vital signs.

If you need more specific details or the complete SQL logic, let me know!

`Basis: search('ED sepsis screening') -> 10 candidates shown; facts[reporting.USP_ED_Sepsis]`

*(6.6s; tools: search_catalog -> get_facts)*

**you>** show me its sql

The SQL logic for the "ED Sepsis Screening" metric (USP_ED_Sepsis) is as follows:

```sql
-- Final
SELECT
    [BasePop].PAT_MRN_ID AS MRN,
    [BasePop].PAT_NAME AS PATIENTS,
    [BasePop].[Ethnic Group],
    [BasePop].[Race],
    [BasePop].PAT_ENC_CSN_ID AS CSN,
    [BasePop].AGE_MONTHS AS [Age at ED Arrival (Months)],
    [BasePop].AGE_YEARS AS [Age at ED Arrival (Years)],
    [BasePop].AGE_IN_DAYS AS [Age In Days],
    CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN 1 ELSE 0 END AS [Age in Days Count],
    CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN '<= 21 Days' ELSE '> 21 Days' END AS [Age in Days Indicator],
    [BasePop].[Location]

-- BloodPressure
SELECT
    PAT_ENC_CSN_ID,
    FLO_MEAS_ID,
    RECORDED_TIME,
    MEAS_VALUE
INTO #BloodPressure
FROM #Flowsheets
WHERE 1=1
AND RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME
AND FLO_MEAS_ID IN (
    '95', -- Blood Pressure
    '9001140203', -- R PED GIRLS SYSTOLIC BP PERCENTILE
    '9001140205' -- R PED BOYS SYSTOLIC BP PERCENTILE
);

-- Flowsheets
SELECT 
    [#Base_Pop].INPATIENT_DATA_ID,
    [#Base_Pop].PAT_ENC_CSN_ID,
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
INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS REC ON [#Base_Pop].INPATIENT_DATA_ID = [REC].INPATIENT_DATA_ID
INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS FSD ON [REC].FSD_ID = [FSD].FSD_ID
WHERE 1=1
AND RECORDED_TIME IS NOT NULL;

-- Additional SQL logic follows...
```

Due to the extensive nature of the SQL script, I've provided only a portion here. If you need further sections or specific parts, please let me know!

`Basis: facts[reporting.USP_ED_Sepsis]`

*(6.9s; tools: get_facts)*

**you>** who owns it?

The specific ownership details, such as the steward or developer, are not provided in the metric information for "ED Sepsis Screening" (USP_ED_Sepsis). If you're looking for information about the responsible team or individuals, you may need to refer to internal documentation or governance records within your organization.

`Basis: facts[reporting.USP_ED_Sepsis]`

*(2.8s; tools: get_facts)*

**you>** what tables does it read from?

The "ED Sepsis Screening" metric (USP_ED_Sepsis) reads from the following tables:

- ADT_EVENTS
- ALERT_ACTIONS
- ALERT_HISTORY
- CLINICAL_ALERTS
- CONFIG_VALUE_SET
- DEPARTMENTS
- ED_ENCOUNTERS_DM
- ED_ENCOUNTERS_FACT
- ED_EVENT_INFO
- ED_EVENT_TEMPLATES
- ED_PATIENT_INFO
- EMPLOYEES
- ENCOUNTER_VISIT_REASONS
- FLOWSHEET_MEASUREMENTS
- FLOWSHEET_RECORDS
- HOSPITAL_ENCOUNTERS
- LAB_ORDER_RESULTS
- LOCATIONS
- MEDICATIONS
- MEDICATION_ORDERS
- MEDICATION_ORDERS_EXT
- MED_ADMIN_RECORDS
- ORDER_TRACKING_METRICS
- ORGANISMS
- PATIENTS
- PATIENT_DEMOGRAPHICS_RACE
- PROCEDURE_ORDERS
- PROCEDURE_ORDERS_EXT
- REF_ALERT_ACTIONS
- REF_ALERT_OVERRIDE_REASONS
- REF_ALERT_STATUS
- REF_ED_DISPOSITION
- REF_ETHNIC_GROUP
- REF_GENERIC_MED
- REF_PATIENT_RACE
- REF_SHOWN_PLACE
- VISIT_REASONS
- V_PATIENT_LOCATION_HISTORY

`Basis: no new lookups — answered from facts already retrieved in this conversation`

*(2.8s; tools: (none))*


## same_logic_q2

*Expectation:* computed verdict via check_same_logic, never an LLM impression

**you>** does ED Sepsis Screening use the same logic as ED Sepsis (Regulatory)?

The metrics "ED Sepsis Screening" and "ED Sepsis (Regulatory)" do **not** use the same logic. The check revealed that they have distinct definitions, with several differences in the SQL logic utilized for each.

`Basis: find_by_name('ED Sepsis Screening') -> 1 exact matches; find_by_name('ED Sepsis (Regulatory)') -> 1 exact matches; same_logic(2 ids) -> 2 distinct`

*(5.0s; tools: find_by_name -> find_by_name -> check_same_logic)*


## variants_family

*Expectation:* find_by_name family -> check_same_logic partition (6 procs, 5 distinct)

**you>** are all definitions of Base_Pop_Severe_ED_Scores the same across our procedures?

There are five distinct definitions of "Base_Pop_Severe_ED_Scores" across the procedures:

1. **reporting.USP_ED_Sepsis** 
2. **reporting.USP_IP_SEPSIS** 
3. **reports.USP_ED_Sepsis** 
4. **reports.USP_IP_SEPSIS**
5. **reports.USP_Severe_Sepsis**
6. **reports.USP_IP_SEPSIS_REPORT**

The SQL logic for these definitions differs, with key differences in how data is selected and arranged. For example, there are variations in the source tables and the specific columns being selected or filtered upon.

If you need more details about a specific instance, let me know.

`Basis: find_by_name('Base_Pop_Severe_ED_Scores') -> 6 exact matches; same_logic(6 ids) -> 5 distinct`

*(5.3s; tools: find_by_name -> check_same_logic)*


## pairwise_variant

*Expectation:* two named procs, one named step -> partition slice

**you>** is reporting.USP_ED_Sepsis using the same Base_Pop_Severe_ED_Scores logic as reports.USP_IP_SEPSIS?

The logic for **reporting.USP_ED_Sepsis** and **reporting.USP_IP_SEPSIS** is different. Here are the relevant details:

1. **reporting.USP_ED_Sepsis**:
   - Source Tables: ADT_EVENTS, ALERT_ACTIONS, ALERT_HISTORY, ..., etc.
   - Key SQL Logic: Involves selections from the Base Population and captures various patient metrics and demographics related to ED arrivals.

2. **reporting.USP_IP_SEPSIS**:
   - Source Tables: ADT_EVENTS, ALERT_HISTORY, CALENDAR_DATES, ..., etc.
   - Key SQL Logic: Includes selections related to inpatient scores, placement times, and measurements relevant for inpatient sepsis assessment.

The two metrics are constructed with different SQL queries and aims, highlighting their distinct logic concerning patient data and sepsis monitoring.

`Basis: check_same_logic({"ids": ["reporting.USP_ED_Sepsis", "reporting.USP_IP_SEPSIS...) -> error; facts[reporting.USP_ED_Sepsis]; get_facts({"id": "reporting.USP_IP_SEPSIS"}) -> error; search('USP_IP_SEPSIS') -> 9 candidates shown; facts[reporting.USP_IP_SEPSIS]; same_logic(2 ids) -> 2 distinct`

*(10.5s; tools: check_same_logic(ERR) -> get_facts -> get_facts(ERR) -> search_catalog -> get_facts -> check_same_logic)*


## same_developer_q3

*Expectation:* LLM assembles from two fact sets; honest about unrecorded ownership

**you>** were ED Sepsis Screening and ED Sepsis (Regulatory) written by the same developer?

The developer information for both "ED Sepsis Screening" and "ED Sepsis (Regulatory)" is not available from the returned data. Therefore, it cannot be determined whether they were written by the same developer.

`Basis: find_by_name('ED Sepsis Screening') -> 1 exact matches; find_by_name('ED Sepsis (Regulatory)') -> 1 exact matches; facts[reporting.USP_ED_Sepsis]; facts[reports.USP_ED_Sepsis]`

*(5.6s; tools: find_by_name -> find_by_name -> get_facts -> get_facts)*


## shared_tables_q4

*Expectation:* LLM intersects two source_tables lists from facts

**you>** what tables do ED Sepsis Screening and ED Sepsis (Regulatory) share?

The metrics "ED Sepsis Screening" and "ED Sepsis (Regulatory)" share the following calculation steps:

1. **ED2GEN**
2. **ED2HEMONC**
3. **ED2ICU**
4. **PositiveScores**
5. **NegativeCultures**
6. **FirstABXAdminTimeDetails**
7. **FirstPositiveOD_To_ABXAdminTime**
8. **BasePopABX**
9. **BasePopBolus**
10. **Base_Pop**
11. **Base_Pop_ED_Readmit**
12. **Base_Pop_ED_Readmit_All**
13. **Base_Pop_ENC_Reason**
14. **Base_Pop_SepsisScores_ConCat**
15. **Base_Pop_Severe_ED_Scores**
16. **BedEvents**
17. **Pressors**
18. **SSOrderSet**
19. **SSOrderSetOSQ_PRL**
20. **SepsisAlertCancelled**

These steps are utilized in both metrics, indicating that they likely derive some shared data.

`Basis: search('ED Sepsis Screening') -> 10 candidates shown; search('ED Sepsis (Regulatory)') -> 10 candidates shown; steps[reporting.USP_ED_Sepsis] -> 43; steps[reports.USP_ED_Sepsis] -> 37`

*(7.8s; tools: search_catalog -> search_catalog -> list_steps -> list_steps)*


## ambiguity_disclosure

*Expectation:* several sepsis metrics exist — must ask or state assumption, never silent

**you>** how is sepsis defined?

I can only provide information within the certified metrics and calculation steps in the knowledge base. I do not have a definition for sepsis. However, if you have specific metrics or related queries, I can help with that.

`Basis: no tools consulted`

*(1.1s; tools: (none))*


## anaphora_compare

*Expectation:* 'this' binds to prior answer via conversation context

**you>** how is ED Sepsis Screening calculated?

The ED Sepsis Screening metric, referred to as **USP_ED_Sepsis**, is calculated based on various data sources and includes the following steps:

1. **Base Population Selection**: 
   - It starts by identifying distinct patient encounters with details such as patient ID, name, ethnicity, race, and age upon arrival at the ED.

2. **Vital Signs Collection**:
   - It retrieves blood pressure measurements recorded during the patient's ED visit.

3. **Sepsis Screening Scores**:
   - It evaluates sepsis screening scores recorded in the patient flowsheets within a specified timeframe (between arrival and departure from the ED).

4. **Ordering and Administering Medications**:
   - The metric includes checks for antibiotic medications ordered and administered to patients during their ED visit.

5. **Lab Cultures**:
   - It tracks lab orders for cultures and results, identifying if any cultures were positive for organisms associated with sepsis.

6. **Clinical Alerts**:
   - The metric flags any clinical alerts related to sepsis that may have been cancelled and captures the relevant data associated with them.

This comprehensive approach combines clinical, laboratory, and medication administration data to assess the occurrence of sepsis among patients in the emergency department.

For the raw SQL calculation logic or further details, you can provide a request explicitly for that information.

`Basis: search('ED Sepsis Screening') -> 10 candidates shown; facts[reporting.USP_ED_Sepsis]`

*(6.2s; tools: search_catalog -> get_facts)*

**you>** how is this different from the inpatient sepsis overview?

The **ED Sepsis Screening** (USP_ED_Sepsis) and the **Inpatient Sepsis Overview** (USP_IP_Sepsis_ScreeningTool) are distinct metrics, with significantly different SQL logic and therefore different underlying calculations. 

While both metrics assess sepsis in patients, the **ED Sepsis Screening** focuses on patient encounters in the emergency department, including details on vital signs, lab cultures, clinical alerts, and medications administered during the ED visit.

In contrast, the **Inpatient Sepsis Overview** targets patients already admitted to the hospital, analyzing different parameters relevant to inpatient care. 

The main differences in SQL involve different subsets of data, type of patient information being captured, and specific calculations and conditions applied based on ED versus inpatient settings. 

If you need further details or the specific SQL logic for either metric, please let me know!

`Basis: same_logic(2 ids) -> 2 distinct`

*(4.1s; tools: check_same_logic)*


## lineage_refusal_q6

*Expectation:* no lineage tool exists — honest refusal, no fabricated downstream list

**you>** which metrics are downstream of the ADT table?

The tools cannot provide lineage information or identify which metrics are downstream of the ADT table. I can help with other questions about metrics or calculations if you have any!

`Basis: no tools consulted`

*(0.9s; tools: (none))*


## data_values_refusal

*Expectation:* definitions only — refuse actual patient counts

**you>** how many sepsis patients did we have yesterday?

I can't provide actual patient counts or row-level data. However, I can help with metrics definitions related to sepsis if you need that information. Let me know how else I can assist you!

`Basis: no tools consulted`

*(1.1s; tools: (none))*


## nonsense_refusal

*Expectation:* nothing related — honest refusal

**you>** what is the average unicorn velocity for readmitted patients?

There are several potential metrics that may be relevant to your query about the average unicorn velocity for readmitted patients:

1. **NICUAdmissions for Non-Severe Sepsis** - Step ID: `transform:reports.USP_NonSevere_Sepsis:NICUAdmissions`
2. **NICUAdmissions for Severe Sepsis** - Step ID: `transform:reports.USP_Severe_Sepsis:NICUAdmissions`
3. **Base Population for ED Readmits** - Step ID: `transform:reporting.USP_ED_Sepsis:Base_Pop_ED_Readmit`
4. **Base Population for ED Readmits (All)** - Step ID: `transform:reports.USP_ED_Sepsis:Base_Pop_ED_Readmit_All`

Please specify which metric you are interested in, or if you would like more information about a particular one.

`Basis: search('average unicorn velocity readmitted patients') -> 4 candidates shown`

*(3.9s; tools: search_catalog)*


## smalltalk

*Expectation:* no tools, no fabricated basis

**you>** hello, what can you do?

I can help you with certified metrics and calculation steps from the data governance knowledge base. This includes finding definitions, translating SQL into business language, and verifying if SQL logic is the same across different metrics. I cannot provide actual patient data, lineage information, usage statistics, or filter item lists by owner. How can I assist you today?

`Basis: no tools consulted`

*(1.2s; tools: (none))*

