# ADR 0035 Agent — Live Evaluation (FINAL, 2026-08-11 overnight)

**Verdict: 12/12 conversations PASS on round 4.** Four rounds run
against the live stack (Azure OpenAI gpt-5.4-mini function calling +
probe-eh Eventhouse). Raw transcripts of every round are preserved:
AGENT_LIVE_RESULTS_round1/2/3.md; this file is the final round.

## Round-by-round (what failed, what fixed it)

| Round | Result | Fixes applied after |
|---|---|---|
| 1 | 7/12 | find_by_name only matched internal names — business names ("ED Sepsis Screening") and refs (reporting.USP_IP_SEPSIS) returned 0 and the agent refused honestly but unhelpfully. Also: lineage answered with search hits dressed as lineage. Fixed: exact lookup matches name OR business_name OR ref; unsupported domains named in the invariants. |
| 2 | 8/12 | Model compared whole metrics when asked about one named step; listed steps when asked for tables; bound "Inpatient Sepsis Overview" to a lookalike; over/under-refused. Fixed: basis now names the exact ids passed to same_logic (mislabeling became visible); tool descriptions state the schema (tables live in metric facts); prompt balance on closeness. |
| 3 | 9/12 | Family gathered via capped search (5 of 6 members); "how is sepsis defined" refused without searching; name substitution persisted. Fixed: search marked non-exhaustive in its description (find_by_name for families); rule 2b never-refuse-without-searching; rule 4b never substitute a similarly-themed item — a name mismatch is a wrong answer. |
| 4 | **12/12** | — |

## Highlights (round 4)

- Same-logic verdicts are always computed: `same_logic([reporting.USP_ED_Sepsis, reports.USP_ED_Sepsis]) -> 2 distinct` — ids visible in every basis.
- Variants family: find_by_name -> 6 members -> 5 distinct definitions (the governance flagship finding, reproduced conversationally).
- Pairwise step question runs the exact right flow: steps of both procs -> same_logic on the two precise step ids.
- Anaphora ("how is this different from...") binds via real lookup, never by vibes.
- Honest refusals: lineage, patient counts (both <1.3s, zero tools, zero fabrication); nonsense discloses that near matches are probably not what was asked.
- Latency: simple turns 1-7s; heavy multi-fetch turns up to ~15s.

## Known observations (recorded, not blocking)

1. LLM-computed list intersections (shared tables) read correct but are
   not independently verified — if the future agent-level suite catches
   an error here, a deterministic set-op tool is the fix.
2. Live output_metric_logic rows lack business_name (labels fall back
   to proc names in some answers) — data refresh item, not code.
3. gpt-5.4-mini needed three prompt calibrations to stop substituting
   lookalike items and to search before refusing — behaviors to
   re-measure per release via an agent-level robustness suite.

---

## definition_and_followups

*Expectation:* definition answer grounded in facts; follow-ups use context, no re-search noise

**you>** how is ED sepsis screening calculated?

The calculation for the ED sepsis screening is encapsulated in the metric **USP_ED_Sepsis**. While the description is not specified, the logic used in the calculation involves various steps that process data from multiple source tables including patient events, labs, and flowsheets. Key operations involve:

1. **Creating Base Population**: It filters relevant patient encounters, extracting patient demographics such as ID, name, ethnicity, race, and age.

2. **Extracting Vital Signs**: Blood pressure measurements are extracted during the ED stay using timestamps.

3. **Handling Laboratory Cultures**: The logic involves querying laboratory results to check for cultures, categorizing them based on whether they are positive or negative.

4. **Integration of Alerts and Workflow Metrics**: It tracks clinical alerts related to sepsis and medication administration and captures timings of interventions pertaining to sepsis.

The full SQL implementation is complex and includes creating temporary tables and joining various pieces of data to derive the screening outcomes and metrics relevant to ED sepsis screenings. If you need more specific parts of the SQL code or additional details, please ask!

`Basis: search('ED sepsis screening') -> 10 candidates shown; facts[reporting.USP_ED_Sepsis]`

*(6.1s; tools: search_catalog -> get_facts)*

**you>** show me its sql

Here is the SQL used for the ED sepsis screening calculation:

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
    [BasePop].[Location],
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
            '95' -- Blood Pressure
            ,'9001140203' -- R PED GIRLS SYSTOLIC BP PERCENTILE
            ,'9001140205' -- R PED BOYS SYSTOLIC BP PERCENTILE
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

    -- Base_Pop
    SELECT DISTINCT
        PEH.PAT_ENC_CSN_ID,
        PEH.PAT_ID,
        PAT.PAT_MRN_ID,
        PAT.PAT_NAME,
        ZEG.NAME AS [Ethnic Group],
        ZPR.NAME AS [Race],
        FEE.AGE_AT_ARRIVAL_MONTHS,
        FEE.AGE_AT_ARRIVAL_YEARS,
        PEH.INPATIENT_DATA_ID,
        PEH.ADT_ARRIVAL_TIME,
        DEE.TRIAGE_START_DTTM,
        DEE.TRIAGE_END_DTTM,
        ...
```

This SQL is part of a larger calculation incorporating multiple steps and temporary tables to assess ED sepsis screenings. If you require more detailed sections or specific parts of the SQL code, please let me know!

`Basis: no new lookups — answered from facts already retrieved in this conversation`

*(6.9s; tools: (none))*

**you>** who owns it?

The ownership details for the ED sepsis screening metric **USP_ED_Sepsis** are not specified in the available data. There is no steward or developer information provided. If you need further details or specific inquiries regarding its management, please let me know!

`Basis: facts[reporting.USP_ED_Sepsis]`

*(2.9s; tools: get_facts)*

**you>** what tables does it read from?

The ED sepsis screening metric **USP_ED_Sepsis** reads from the following source tables:

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

If you have further questions or need additional details, let me know!

`Basis: no new lookups — answered from facts already retrieved in this conversation`

*(3.8s; tools: (none))*


## same_logic_q2

*Expectation:* computed verdict via check_same_logic, never an LLM impression

**you>** does ED Sepsis Screening use the same logic as ED Sepsis (Regulatory)?

The metrics "ED Sepsis Screening" and "ED Sepsis (Regulatory)" do not use the same logic. They are defined distinctly and have different SQL logic.

`Basis: find_by_name('ED Sepsis Screening') -> 1 exact matches; find_by_name('ED Sepsis (Regulatory)') -> 1 exact matches; same_logic([reporting.USP_ED_Sepsis, reports.USP_ED_Sepsis]) -> 2 distinct`

*(4.8s; tools: find_by_name -> find_by_name -> check_same_logic)*


## variants_family

*Expectation:* find_by_name family -> check_same_logic partition (6 procs, 5 distinct)

**you>** are all definitions of Base_Pop_Severe_ED_Scores the same across our procedures?

The definitions of "Base_Pop_Severe_ED_Scores" are not all the same across procedures. There are five distinct definitions across the various contexts. 

The largest grouping includes:
1. **Transform: reports.USP_IP_SEPSIS:Base_Pop_Severe_ED_Scores**
2. **Transform: reports.USP_IP_SEPSIS_REPORT:Base_Pop_Severe_ED_Scores**

Other groups consist of:
- **Transform: reporting.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores**
- **Transform: reporting.USP_IP_SEPSIS:Base_Pop_Severe_ED_Scores**
- **Transform: reports.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores**
- **Transform: reports.USP_Severe_Sepsis:Base_Pop_Severe_ED_Scores**

The differences primarily revolve around the SQL logic used in each definition, specifically in the structure of the SELECT statements and data sources involved. If you need more detailed SQL comparisons or specific definitions, please let me know.

`Basis: find_by_name('Base_Pop_Severe_ED_Scores') -> 6 exact matches; same_logic([transform:reporting.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores, transform:reporting.USP_IP_SEPSIS:Base_Pop_Severe_ED_Scores, transform:reports.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores, transform:reports.USP_IP_SEPSIS:Base_Pop_Severe_ED_Scores, ...]) -> 5 distinct`

*(6.2s; tools: find_by_name -> check_same_logic)*


## pairwise_variant

*Expectation:* two named procs, one named step -> partition slice

**you>** is reporting.USP_ED_Sepsis using the same Base_Pop_Severe_ED_Scores logic as reports.USP_IP_SEPSIS?

The logic for **Base_Pop_Severe_ED_Scores** in **reporting.USP_ED_Sepsis** and **reports.USP_IP_SEPSIS** is different. The two definitions have distinct SQL structures and do not produce the same results. 

If you need more details about the differences between them, please let me know.

`Basis: steps[reporting.USP_ED_Sepsis] -> 43; steps[reports.USP_IP_SEPSIS] -> 39; same_logic([transform:reporting.USP_ED_Sepsis:Base_Pop_Severe_ED_Scores, transform:reports.USP_IP_SEPSIS:Base_Pop_Severe_ED_Scores]) -> 2 distinct`

*(5.0s; tools: list_steps -> list_steps -> check_same_logic)*


## same_developer_q3

*Expectation:* LLM assembles from two fact sets; honest about unrecorded ownership

**you>** were ED Sepsis Screening and ED Sepsis (Regulatory) written by the same developer?

The developers for both metrics, "ED Sepsis Screening" and "ED Sepsis (Regulatory)", are not specified in the information retrieved. Therefore, I cannot confirm if they were written by the same developer.

`Basis: find_by_name('ED Sepsis Screening') -> 1 exact matches; find_by_name('ED Sepsis (Regulatory)') -> 1 exact matches; facts[reporting.USP_ED_Sepsis]; facts[reports.USP_ED_Sepsis]`

*(5.7s; tools: find_by_name -> find_by_name -> get_facts -> get_facts)*


## shared_tables_q4

*Expectation:* LLM intersects two source_tables lists from facts

**you>** what tables do ED Sepsis Screening and ED Sepsis (Regulatory) share?

The tables shared by both **ED Sepsis Screening** (USP_ED_Sepsis) and **ED Sepsis (Regulatory)** (USP_ED_Sepsis) are:

1. **ADT_EVENTS**
2. **DEPARTMENTS**
3. **ED_ENCOUNTERS_DM**
4. **ED_ENCOUNTERS_FACT**
5. **EMPLOYEES**
6. **ENCOUNTER_VISIT_REASONS**
7. **FLOWSHEET_MEASUREMENTS**
8. **FLOWSHEET_RECORDS**
9. **HOSPITAL_ENCOUNTERS**
10. **LAB_ORDER_RESULTS**
11. **LOCATIONS**
12. **MEDICATIONS**
13. **MEDICATION_ORDERS**
14. **MED_ADMIN_RECORDS**
15. **ORGANISMS**
16. **PATIENTS**
17. **PATIENT_DEMOGRAPHICS_RACE**
18. **PROCEDURE_ORDERS**
19. **REF_ED_DISPOSITION**
20. **REF_ETHNIC_GROUP**
21. **REF_GENERIC_MED**
22. **REF_PATIENT_RACE**
23. **VISIT_REASONS**
24. **V_PATIENT_LOCATION_HISTORY**

Both metrics reference these tables as source data for their calculations.

`Basis: search('ED Sepsis Screening') -> 10 candidates shown; search('ED Sepsis (Regulatory)') -> 10 candidates shown; facts[reporting.USP_ED_Sepsis]; facts[reports.USP_ED_Sepsis]`

*(8.6s; tools: search_catalog -> search_catalog -> get_facts -> get_facts)*


## ambiguity_disclosure

*Expectation:* several sepsis metrics exist — must ask or state assumption, never silent

**you>** how is sepsis defined?

Sepsis is defined and captured in various metrics within the organization's reporting framework. Here are the relevant definitions based on the metrics identified:

1. **Inpatient Sepsis Overview (USP_IP_SEPSIS)**: This metric captures the data related to inpatient cases diagnosed with sepsis, integrating multiple patient encounter tables and clinical alerts.

2. **ED Sepsis (Regulatory) (USP_ED_Sepsis)**: This metric focuses on sepsis cases identified in the emergency department, encompassing patient demographics, encounter details, and treatment timelines related to the emergency visit.

3. **Severe Sepsis Episodes (USP_Severe_Sepsis)**: This metric specifically addresses episodes of severe sepsis, tracking various indicators, including vital functions and administered medications during the patient’s hospitalization.

If you would like detailed information about these specific metrics or any of their definitions or calculations, please let me know.

`Basis: search('sepsis definition') -> 10 candidates shown; facts[reporting.USP_IP_SEPSIS]; facts[reports.USP_ED_Sepsis]; facts[reports.USP_Severe_Sepsis]`

*(7.3s; tools: search_catalog -> get_facts -> get_facts -> get_facts)*


## anaphora_compare

*Expectation:* 'this' binds to prior answer via conversation context

**you>** how is ED Sepsis Screening calculated?

The ED Sepsis Screening metric, identified as **USP_ED_Sepsis**, captures data related to sepsis screening in the Emergency Department (ED). Its calculation utilizes an extensive SQL query involving multiple data sources.

### Calculation Logic Highlights:
- The metric collects data from various source tables, including patient demographics, encounter details, lab results, and clinical alerts.
- Key components include:
  - Patient demographics (e.g., MRN, name, age).
  - Vital signs like blood pressure measured during the patient’s ED visit.
  - Clinical alerts triggered based on predefined criteria during the ED stay.
  - Lab results, particularly those indicating infection, such as cultures.
  - Medication administration data, especially for antibiotics, to track the administration time relative to sepsis recognition.

### Source Tables Used:
- ADT_EVENTS
- ED_ENCOUNTERS
- LAB_ORDER_RESULTS
- MEDICATIONS
- CLINICAL_ALERTS
- And others related to patient events and measurements

This information supports the implementation of a systematic approach to sepsis screening, ensuring timely actions are taken based on the collected clinical data.

If you need more specific details or the complete SQL logic, let me know!

`Basis: search('ED Sepsis Screening') -> 10 candidates shown; facts[reporting.USP_ED_Sepsis]`

*(6.6s; tools: search_catalog -> get_facts)*

**you>** how is this different from the inpatient sepsis overview?

The **ED Sepsis Screening (USP_ED_Sepsis)** and **Inpatient Sepsis Overview (USP_IP_SEPSIS)** metrics differ in their calculation logic, focus, and source data utilized.

### Key Differences:

1. **Patient Setting**:
   - **ED Sepsis Screening**: Focuses on patients in the Emergency Department (ED) and the initial screening processes applicable there.
   - **Inpatient Sepsis Overview**: Concentrates on patients admitted to the hospital, tracking their sepsis status and metrics during their inpatient stay.

2. **Calculation Logic**:
   - **ED Sepsis Screening** includes demographics (e.g., age, race), vital sign measurements like blood pressure during ED hours, and actions taken prior to ED discharge.
   - **Inpatient Sepsis Overview** involves different measurement variables such as "OD Scores," time spent in department, clinical alerts, and overall progression of sepsis treatment throughout the hospital stay.

3. **Source Tables**:
   - **ED Sepsis**: Utilizes tables such as ADT_EVENTS, ED_ENCOUNTERS, LAB_ORDER_RESULTS, and clinical alerts specifically related to the ED.
   - **Inpatient Sepsis**: Incorporates source tables like HOSPITAL_ENCOUNTERS, CLINICAL_NOTES, FLOW_MEASUREMENT, and inpatient-specific clinical alerts.

4. **Distinct SQL Logic**:
   - The SQL logic is distinctly different, reflecting the varying datasets and conditions defining sepsis in these two settings. The group of calculations for ED is separate from that of inpatient metrics.

For more specific technical details about their SQL or calculations, let me know!

`Basis: search('Inpatient Sepsis Overview') -> 10 candidates shown; facts[reporting.USP_IP_SEPSIS]; same_logic([reporting.USP_ED_Sepsis, reporting.USP_IP_SEPSIS]) -> 2 distinct`

*(9.3s; tools: search_catalog -> get_facts -> check_same_logic)*


## lineage_refusal_q6

*Expectation:* no lineage tool exists — honest refusal, no fabricated downstream list

**you>** which metrics are downstream of the ADT table?

I cannot provide information about lineage or which metrics are downstream of the ADT table. However, if you have questions about specific metrics or definitions within the certified knowledge base, feel free to ask!

`Basis: no tools consulted`

*(1.2s; tools: (none))*


## data_values_refusal

*Expectation:* definitions only — refuse actual patient counts

**you>** how many sepsis patients did we have yesterday?

I cannot provide actual patient counts or row-level data. However, if you need a definition or calculation related to sepsis metrics, I can help with that. Please let me know!

`Basis: no tools consulted`

*(1.7s; tools: (none))*


## nonsense_refusal

*Expectation:* nothing related — honest refusal

**you>** what is the average unicorn velocity for readmitted patients?

No specific metric directly mentions "average unicorn velocity" for readmitted patients. Here are steps related to readmitted patients, although they might not provide the information you're looking for:

1. **Base_Pop_ED_Readmit** - Part of the metric **USP_ED_Sepsis**.
2. **Base_Pop_ED_Readmit_All** - Also part of the **USP_ED_Sepsis**.

If you'd like to explore one of these steps further, please let me know!

`Basis: search('unicorn velocity readmitted patients') -> 5 candidates shown`

*(3.0s; tools: search_catalog)*


## smalltalk

*Expectation:* no tools, no fabricated basis

**you>** hello, what can you do?

I can assist you with certified metrics and data governance knowledge, including defining and calculating clinical or business concepts, providing information about specific metrics or steps, and checking if SQL logic is the same across different items. If you have a specific question or need insight on a particular metric, feel free to ask!

`Basis: no tools consulted`

*(1.2s; tools: (none))*

