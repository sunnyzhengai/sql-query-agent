# ED Sepsis Gap-Check Report (round 2 — the truth check)

*Generated 2026-09-06, pack 1.2 + floor grammar v1.1.0 (the
two-alias corpse from Sunny's finding 2 is fixed: multi-
instance reads voice per instance, dedup at predicate
identity). Finding 1 (code meanings) is OPEN — design options
with Sunny. DBA result tables in intake_result_tables/.*

## Intake report (as the DBA receives it)
```
AIVIA INTAKE REPORT
Registered db: aivia_demo_src (server SEPSISSERVER); sources: emr; DBA: role:emr-dba

[extract: emr] loaded 90 tables, 4380 columns; checks: pass
  counted missing: 90 table(s) with no declared grain (emr|dbo|ADT_EVENTS, emr|dbo|ALERT_ACTIONS, emr|dbo|ALERT_HISTORY, emr|dbo|BED_CONFIG, emr|dbo|CALENDAR_DATES, emr|dbo|CLINICAL_ALERTS, emr|dbo|CLINICAL_NOTES, emr|dbo|CONFIG_GROUPER_CATEGORIES, emr|reports|CONFIG_VALUE_SET, emr|dbo|DEPARTMENTS, emr|dbo|DIAGNOSES, emr|dbo|ED_ENCOUNTERS_DM, emr|dbo|ED_ENCOUNTERS_FACT, emr|dbo|ED_EVENT_INFO, emr|dbo|ED_EVENT_TEMPLATES, emr|dbo|ED_PATIENT_INFO, emr|dbo|EMPLOYEES, emr|dbo|ENCOUNTER_DIAGNOSES, emr|dbo|ENCOUNTER_VISIT_REASONS, emr|dbo|FLOWSHEET_MEASUREMENTS, emr|dbo|FLOWSHEET_RECORDS, emr|reports|FY_DATE_DIMENSION, emr|dbo|GROUPER_COMPILED_LIST, emr|dbo|GROUPER_GROUPS, emr|dbo|GROUPER_MED_RECORDS, emr|dbo|GROUPER_TERMINOLOGY, emr|dbo|HOSPITAL_ACCOUNTS, emr|dbo|HOSPITAL_ACCOUNTS_EXT, emr|dbo|HOSPITAL_ACCT_DIAGNOSES, emr|dbo|HOSPITAL_ENCOUNTERS, emr|dbo|HOSPITAL_TRANSACTIONS, emr|reporting|IP_SEPSIS, emr|reporting|IP_SepsisDetails, emr|reporting|IP_SepsisEncounters, emr|reporting|IP_SepsisEncountersWLocations, emr|reporting|IP_SepsisPatientDates, emr|reporting|IP_SepsisScreeningAudit, emr|reporting|IP_SepsisShiftCompliance, emr|dbo|LAB_COMPONENTS, emr|dbo|LAB_ORDER_RESULTS, emr|dbo|LINE_DEVICE_AIRWAY, emr|dbo|LOCATIONS, emr|dbo|MEDICATIONS, emr|dbo|MEDICATION_ORDERS, emr|dbo|MEDICATION_ORDERS_EXT, emr|dbo|MED_ADMIN_RECORDS, emr|dbo|MED_DETAILS_EXT, emr|dbo|MED_MIX_COMPONENTS, emr|reports|NON_SEVERE_SEPSIS_STAGING, emr|dbo|NOTE_ENCOUNTER_INFO, emr|dbo|NOTE_TEMPLATE_LIST_IDS, emr|dbo|NOTE_TEMPLATE_TEXT_IDS, emr|dbo|ORDER_DISPENSE_INFO, emr|dbo|ORDER_TRACKING_METRICS, emr|dbo|ORGANISMS, emr|dbo|PATIENTS, emr|dbo|PATIENT_DEMOGRAPHICS_RACE, emr|dbo|PATIENT_ENCOUNTERS, emr|dbo|PROCEDURES_CATALOG, emr|dbo|PROCEDURE_ORDERS, emr|dbo|PROCEDURE_ORDERS_EXT, emr|dbo|PROVIDERS, emr|dbo|REF_ALERT_ACTIONS, emr|dbo|REF_ALERT_OVERRIDE_REASONS, emr|dbo|REF_ALERT_STATUS, emr|dbo|REF_DISCHARGE_DISPOSITION, emr|dbo|REF_ED_DISPOSITION, emr|dbo|REF_ETHNIC_GROUP, emr|dbo|REF_GENERIC_MED, emr|dbo|REF_PATIENT_CLASS, emr|dbo|REF_PATIENT_RACE, emr|dbo|REF_SEX, emr|dbo|REF_SHOWN_PLACE, emr|dbo|RX_VERIFY_TRACE, emr|reports|SEVERE_SEPSIS_STAGING, emr|dbo|TREATMENT_TEAMS, emr|dbo|VISIT_REASONS, emr|dbo|V_HOSPITAL_TRANSACTIONS, emr|dbo|V_PATIENT_ENCOUNTERS, emr|dbo|V_PATIENT_LOCATION_HISTORY, emr|dbo|V_PHARMACY_DISPENSE, emr|dbo|V_PHARMACY_DISPENSE_ACTION, emr|dbo|V_PHARMACY_ORDER, emr|dbo|CLINICAL_NOTE_TEXT, emr|dbo|DIAGNOSES_CURRENT_ICD10, emr|dbo|HOSPITAL_ACCT_PX_LIST, emr|dbo|ICD_PROCEDURE_CODES, emr|dbo|PATIENT_OR_ADM_LINK, emr|dbo|V_OR_CASE_LOG, emr|dbo|ICU_STAY_SUMMARY)
  pending reference: fk group 52 -> emr|reporting|IP_SEPSISENCOUNTERSWLOCATIONS (target not yet registered; resolves on arrival, A8)
  pending reference: fk group 53 -> emr|reporting|IP_SEPSISPATIENTDATES (target not yet registered; resolves on arrival, A8)

[estate] acquired 28 file(s): reporting/USP_ED_SEPSIS.sql, reporting/USP_IP_SEPSIS.sql, reporting/USP_IP_SepsisDates.sql, reporting/USP_IP_SepsisDetails.sql, reporting/USP_IP_SepsisDetails_v1.sql, reporting/USP_IP_SepsisEncounters.sql, reporting/USP_IP_SepsisEncountersDetails.sql, reporting/USP_IP_SepsisEncountersWLocations.sql, reporting/USP_IP_SepsisEncountersWLocations_v1.sql, reporting/USP_IP_SepsisPatientDates.sql, reporting/USP_IP_SepsisPatientDates_v1.sql, reporting/USP_IP_SepsisScreeningAudit.sql, reporting/USP_IP_SepsisScreeningAudit_v1.sql, reporting/USP_IP_SepsisShiftCompliance.sql, reporting/USP_IP_SepsisShiftComplianceByShift.sql, reporting/USP_IP_SepsisShiftComplianceMetrics.sql, reporting/USP_IP_Sepsis_ComplianceByShift.sql, reporting/USP_IP_Sepsis_ComplianceMetrics.sql, reporting/USP_IP_Sepsis_Details.sql, reporting/USP_IP_Sepsis_Encounters.sql, reporting/USP_IP_Sepsis_ScreeningTool.sql, reports/USP_RPTS_ED_Sepsis.sql, reports/USP_RPTS_IP_SEPSIS.sql, reports/USP_RPTS_IP_SEPSIS_COMPLIANCE.sql, reports/USP_RPTS_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES.sql, reports/USP_RPTS_IP_SEPSIS_REPORT.sql, reports/USP_RPTS_NonSevere_Sepsis.sql, reports/USP_RPTS_Severe_Sepsis.sql
  unresolved reference: SEVERE.DATE_STAMP in reporting/USP_ED_SEPSIS.sql — not in the dictionary (counted, never guessed)
  unresolved reference: SEVERE.ENCOUNTER_ID in reporting/USP_ED_SEPSIS.sql — not in the dictionary (counted, never guessed)
  unresolved reference: NONSEVERE.DATE_STAMP in reporting/USP_ED_SEPSIS.sql — not in the dictionary (counted, never guessed)
  unresolved reference: NONSEVERE.ENCOUNTER_ID in reporting/USP_ED_SEPSIS.sql — not in the dictionary (counted, never guessed)
  unresolved reference: fyDate.HS_FY in reporting/USP_IP_SepsisDates.sql — not in the dictionary (counted, never guessed)
  unresolved reference: fyDate.HS_FY_MONTH_NUMBER in reporting/USP_IP_SepsisDates.sql — not in the dictionary (counted, never guessed)
  unresolved reference: fyDate.HS_FY in reporting/USP_IP_SepsisDates.sql — not in the dictionary (counted, never guessed)
  unresolved reference: SSS.ENCOUNTER_ID in reports/USP_RPTS_IP_SEPSIS.sql — not in the dictionary (counted, never guessed)
  unresolved reference: SSS.ENCOUNTER_ID in reports/USP_RPTS_IP_SEPSIS_REPORT.sql — not in the dictionary (counted, never guessed)
```

## The centerpiece: ED sepsis floors

### `reporting/USP_ED_SEPSIS.sql::#ADT`
```
This is a selection of records.
- For the first adt events record read: the event record category is 4.
- For the first adt events record read: the category value that indicates if the event record has been modified or removed is not 2.
- For the first adt events record read: the unit associated with the event record at the time it became effective id is one of the values 200108022.
- For the second adt events record read: the event record category is 3.
- For the second adt events record read: the category value that indicates if the event record has been modified or removed is not 2.
- For the second adt events record read: the unit associated with the event record at the time it became effective id is one of the values 200108015, 200108016, 200108019, 200108001, 200108070, 200108115, 200108183, 200108008, 200108009, 200108010, 200108011, 200108012, 200108017, 200108018, 200108020, 200108021, 200108110.
```

### `reporting/USP_ED_SEPSIS.sql::#AllMeds`
```
This is a selection of records.
- It is not the case that the time designated by the user when the action occurred has no recorded value.
- The time designated by the user when the action occurred is before ed_departure_time.
- The med route code is 11.
- The mar action code is one of the values '1', '7', '102', '105', '113', '114', '115', '122', '124', '132', '143', '1604', '1605', '1607', '6', '99'.
```

### `reporting/USP_ED_SEPSIS.sql::#BPA`
```
This is a selection of records.
- The moment when the warning is dismissed following certain actions is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reporting/USP_ED_SEPSIS.sql::#BasePopABX`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::#BasePopBolus`
```
This step produces derived values; no source records are read.
- The taken time is between adt_arrival_time and ed_departure_time (inclusive).
- The hv discr freq id is '300902'.
- The convert(numeric, sig) exceeds 95.0.
- The medication id is one of the values 700001, 7000739, 700003, 7006331, 700002, 700004.
```

### `reporting/USP_ED_SEPSIS.sql::#Base_Pop`
```
This is a selection of records.
- The date when the patient arrived is between the d start date parameter and the d end date parameter (inclusive).
```

### `reporting/USP_ED_SEPSIS.sql::#Base_Pop_ED_Readmit`
```
This is a selection of records.
- The first time line is 1.
```

### `reporting/USP_ED_SEPSIS.sql::#Base_Pop_ED_Readmit_All`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reporting/USP_ED_SEPSIS.sql::#Base_Pop_ENC_Reason`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::#Base_Pop_SepsisScores_ConCat`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::#Base_Pop_Severe_ED_Scores`
```
This step produces derived values; no source records are read.
- The recorded time is between adt_arrival_time and ed_departure_time (inclusive).
- The flo meas id is one of the values '9000161709', '9000002613'.
```

### `reporting/USP_ED_SEPSIS.sql::#BedEvents`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reporting/USP_ED_SEPSIS.sql::#BloodPressure`
```
This step produces derived values; no source records are read.
- The recorded time is between adt_arrival_time and ed_departure_time (inclusive).
- The flo meas id is one of the values '95', '9001140203', '9001140205'.
```

### `reporting/USP_ED_SEPSIS.sql::#Cultures`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::#ED2GEN`
```
This step produces derived values; no source records are read.
- The dept group is 'GenCare'.
```

### `reporting/USP_ED_SEPSIS.sql::#ED2HEMONC`
```
This step produces derived values; no source records are read.
- The dept group is 'HemOnc'.
```

### `reporting/USP_ED_SEPSIS.sql::#ED2ICU`
```
This step produces derived values; no source records are read.
- The dept group is 'ICU'.
```

### `reporting/USP_ED_SEPSIS.sql::#ED_BORDER`
```
This is a selection of records.
- A matching record exists in a separately defined selection.
- The this column represents the event template linked to the event record is one of the values '2600000007'.
```

### `reporting/USP_ED_SEPSIS.sql::#ED_NegativeScores`
```
This step produces derived values; no source records are read.
- The meas value is at most 4.
- It is not the case that a matching record exists in a separately defined selection.
```

### `reporting/USP_ED_SEPSIS.sql::#ED_PositiveScores`
```
This step produces derived values; no source records are read.
- The meas value exceeds 4.
```

### `reporting/USP_ED_SEPSIS.sql::#EncounterWeights`
```
This step produces derived values; no source records are read.
- The flo meas id is '94'.
```

### `reporting/USP_ED_SEPSIS.sql::#Final`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reporting/USP_ED_SEPSIS.sql::#FirstABXAdminTimeDetails`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reporting/USP_ED_SEPSIS.sql::#FirstPositiveOD_To_ABXAdminTime`
```
This step produces derived values; no source records are read.
- The myline is 1.
```

### `reporting/USP_ED_SEPSIS.sql::#Flowsheets`
```
This is a selection of records.
- It is not the case that the recorded time has no recorded value.
- It is not the case that the meas value has no recorded value.
- The recorded time is on or before ed_departure_time.
- The flo meas id is one of the values '94', '95', '9001140203', '9001140205', '9001125002', '9000161709', '9000002613'.
```

### `reporting/USP_ED_SEPSIS.sql::#Hypotension`
```
This step produces derived values; no source records are read.
- The hypotension y is 'Y'.
```

### `reporting/USP_ED_SEPSIS.sql::#LDA`
```
This step produces derived values; no source records are read.
- The time line is 1.
```

### `reporting/USP_ED_SEPSIS.sql::#Labs`
```
This step produces derived values; no source records are read.
- The time line is 1.
```

### `reporting/USP_ED_SEPSIS.sql::#Labs_and_Cultures`
```
This is a selection of records.
- The date and time at which the procedure_order was submitted is between adt_arrival_time and ed_departure_time (inclusive).
- The unique identifier for each result component associated with every result is one of the values 5000001861, 5000000478, 5000000446, 5000000447, 5000000449, 500001 or The procedure record associated with this order, which can be used to reference procedures_catalog unique is one of the values 600003, 600004, 600011, 600012, 600001, 600007, 600008, 600009, 600010 or .
```

### `reporting/USP_ED_SEPSIS.sql::#PatientLocation`
```
This is a selection of records.
- It is not the case that the id number representing the department associated with the event record at the time it is effective has no recorded value.
- A matching record exists in a separately defined selection.
```

### `reporting/USP_ED_SEPSIS.sql::#Pressors`
```
This is a selection of records.
- The taken time is between adt_arrival_time and ed_departure_time (inclusive).
- The base grouper record is vcg-.1 unique is one of the values '8000100', '8000101', '8000102', '8000103', '8000104'.
```

### `reporting/USP_ED_SEPSIS.sql::#SSOrderSet`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::#SepsisAlertCancelled`
```
This step produces derived values; no source records are read.
- The flo meas id is '9001125002'.
- The recorded time is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reporting/USP_ED_SEPSIS.sql::ABX`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::AllCultures`
```
This is a selection of records.
- It is not the case that the culture type has no recorded value.
```

### `reporting/USP_ED_SEPSIS.sql::All_LDAs`
```
This is a selection of records.
- It is not the case that the placement instant has no recorded value.
- The placement instant is between adt_arrival_time and ed_departure_time (inclusive).
- The flo meas id is one of the values '900112', '900111' or The value set id is 3022.
```

### `reporting/USP_ED_SEPSIS.sql::NegativeCultures`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::OrderMetricIDs`
```
This is a selection of records.
- The date and time when the order was created is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reporting/USP_ED_SEPSIS.sql::PositiveCultures`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::SSOrderSetOSQ_PRL`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::Systolic`
```
This step produces derived values; no source records are read.
- The flo meas id is '95'.
- The recorded time is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reporting/USP_ED_SEPSIS.sql::TimeOrdered_LDAs`
```
This step produces derived values; no source records are read.
```

### `reporting/USP_ED_SEPSIS.sql::TimeOrdered_Labs`
```
This step produces derived values; no source records are read.
- It is not the case that the lab test type has no recorded value.
```

### `reporting/USP_ED_SEPSIS.sql::delivery`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#ALLCVLTime`
```
This is a selection of records.
- The this item records the exact moment the record was placed is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#BPA`
```
This is a selection of records.
- The moment when the warning is dismissed following certain actions is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#BasePopABX`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#BasePopBolus`
```
This is a selection of records.
- It is not the case that the time designated by the user when the action occurred has no recorded value.
- The time designated by the user when the action occurred is between adt_arrival_time and ed_departure_time (inclusive).
- The medication record linked to this order unique is one of the values 700001, 7000739, 700003, 7006331, 700002 or .
- The mar_action_category_number linked to this administration is one of the values '1', '7', '102', '105', '113', '114', '115', '122', '124', '132', '143', '1604', '1605', '1607', '6'.
- The convert(numeric, ma.sig ) exceeds 95.0.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop`
```
This is a selection of records.
- The date when the patient arrived is between the d start date parameter and the d end date parameter (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop_ED_Readmit`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop_ED_Readmit_All`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop_ENC_Reason`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop_SepsisScores_ConCat`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Base_Pop_Severe_ED_Scores`
```
This is a selection of records.
- The flowsheet group or row linked to this reading unique is one of the values '9000161709', '9000002613'.
- The exact moment when the reading was recorded is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#BedEvents`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#BloodCultureValue`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#CsfCultureValue`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#ED2GEN`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#ED2HEMONC`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#ED2ICU`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#ED_PositiveScores`
```
This step produces derived values; no source records are read.
- The meas value exceeds 4.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#ETT`
```
This is a selection of records.
- The this item contains the flowsheet id that specifies the structure of this record is '900112'.
- It is not the case that the this item records the exact moment the record was placed has no recorded value.
- The this item records the exact moment the record was placed is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#EncounterWeights`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#FirstABXAdminTimeDetails`
```
This is a selection of records.
- No membership conditions are applied in this selection.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#FirstPositiveOD_To_ABXAdminTime`
```
This step produces derived values; no source records are read.
- The myline is 1.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Hypotension`
```
This is a selection of records.
- The flowsheet group or row linked to this reading unique is '95'.
- It is not the case that the exact moment when the reading was recorded has no recorded value.
- The exact moment when the reading was recorded is between adt_arrival_time and ed_departure_time (inclusive).
- It is not the case that the flowsheet reading real has no recorded value.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#IV`
```
This is a selection of records.
- The this item contains the flowsheet id that specifies the structure of this record is '900111'.
- It is not the case that the this item records the exact moment the record was placed has no recorded value.
- The this item records the exact moment the record was placed is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#LacticAcid`
```
This is a selection of records.
- The unique identifier for each result component associated with every result is one of the values 5000000446, 5000000447, 5000000449.
- The date and time at which the procedure_order was submitted is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Pressors`
```
This is a selection of records.
- The base grouper record is vcg-.1 unique is one of the values '8000100', '8000101', '8000102', '8000103', '8000104'.
- The mar_action_category_number linked to this administration is one of the values '1', '7', '102', '105', '113', '114', '115', '122', '124', '132', '143', '1604', '1605', '1607', '6'.
- The route_category_number linked to this administration is 11.
- The time designated by the user when the action occurred is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#Procalcitonin`
```
This is a selection of records.
- The unique identifier for each result component associated with every result is 500001.
- The date and time at which the procedure_order was submitted is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#SSOrderSet`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#SSOrderSetOSQ_PRL`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#SVO2`
```
This is a selection of records.
- The unique identifier for each result component associated with every result is one of the values 5000001861, 5000000478.
- The date and time at which the procedure_order was submitted is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::#SepsisAlertCancelled`
```
This is a selection of records.
- The flowsheet group or row linked to this reading unique is '9001125002'.
- It is not the case that the exact moment when the reading was recorded has no recorded value.
- The exact moment when the reading was recorded is between adt_arrival_time and ed_departure_time (inclusive).
- It is not the case that the flowsheet reading real has no recorded value.
```

### `reports/USP_RPTS_ED_Sepsis.sql::#UrineCultureValue`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::ABX`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::BloodCultureResults`
```
This is a selection of records.
- The date and time at which the procedure_order was submitted is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::CsfCultureResults`
```
This is a selection of records.
- The date and time at which the procedure_order was submitted is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::NegativeCultures`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::NegativeCultures#2`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::NegativeCultures#3`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::PositiveCultures`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::PositiveCultures#2`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::PositiveCultures#3`
```
This step produces derived values; no source records are read.
```

### `reports/USP_RPTS_ED_Sepsis.sql::UrineCultureResults`
```
This is a selection of records.
- The date and time at which the procedure_order was submitted is between adt_arrival_time and ed_departure_time (inclusive).
```

### `reports/USP_RPTS_ED_Sepsis.sql::delivery`
```
This step produces derived values; no source records are read.
```

## Findings
- READER/WRITER DRIFT (silently-failing-report class): 9 refs, 7 distinct: NONSEVERE.DATE_STAMP, NONSEVERE.ENCOUNTER_ID, SEVERE.DATE_STAMP, SEVERE.ENCOUNTER_ID, SSS.ENCOUNTER_ID, fyDate.HS_FY, fyDate.HS_FY_MONTH_NUMBER
- undocumented org-catalog columns (counted): 242
- join compliance: 10 violations, 203 compliant, 461 not judged (lineage-derived declarations — near-vacuous, see pack caveat)
- working set: 63 of 90 dictionary tables touched
- descriptions produced: 303 scopes, all skeleton_floor, grammar v1.1.0 in every basis
