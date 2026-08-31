# P0-b — adversarial corpus over LIVE generation

**11 case(s)** · clean 6 · recovered 5 · salvaged 0 · emptied 0

clean = passed the gate first try · recovered = the corrective retry fixed it · salvaged = surgical fallback kept grounded lines · emptied = absence over fabrication

## Per class

- **aggregate** — clean 0 · recovered 1 · salvaged 0 · emptied 0 · first-pass violations: ungrounded filter claim
- **degenerate_empty** — clean 1 · recovered 0 · salvaged 0 · emptied 0
- **degenerate_literal** — clean 0 · recovered 1 · salvaged 0 · emptied 0 · first-pass violations: selected-not-filtered
- **exclusion** — clean 1 · recovered 0 · salvaged 0 · emptied 0
- **grain_patient** — clean 1 · recovered 0 · salvaged 0 · emptied 0
- **grain_visit** — clean 0 · recovered 1 · salvaged 0 · emptied 0 · first-pass violations: ungrounded filter claim
- **inclusion** — clean 1 · recovered 0 · salvaged 0 · emptied 0
- **multi_join** — clean 1 · recovered 0 · salvaged 0 · emptied 0
- **negation** — clean 0 · recovered 1 · salvaged 0 · emptied 0 · first-pass violations: ungrounded filter claim
- **threshold_ge** — clean 0 · recovered 1 · salvaged 0 · emptied 0 · first-pass violations: ungrounded filter claim
- **threshold_gt** — clean 1 · recovered 0 · salvaged 0 · emptied 0

## Samples (fragment → final description)

### aggregate · High_Utilizer
```
- This step selects the unique patient IDs from the ENCOUNTERS table along with the count of their associated encounter IDs.
- The condition for inclusion in this selection is that each patient must have at least four encounter records, as specified by the HAVING clause.
```
first pass: 1 violation(s)

### degenerate_empty · Passthrough
```
- This step selects all records from the DM_REGISTRY table, which contains essential data related to the organization's data management practices.
- Membership in this dataset is determined by the presence of valid entries in the DM_REGISTRY, ensuring that only relevant and certified data points are included for analysis.
- The selection process facilitates comprehensive insights into the data management landscape, supporting informed decision-making and strategic planning.
```

### degenerate_literal · Constant
```
- This SQL query selects a constant value of 1, labeled as "ALWAYS_TRUE," which serves as a placeholder to indicate a successful execution of the query.
- The condition for membership in this selection is universally satisfied, as it does not depend on any specific data or criteria from a database table.
- This step is often used in testing or validation scenarios to confirm that the SQL environment is functioning correctly without retrieving any actual data.
```
first pass: 1 violation(s)

### exclusion · Diabetic_Excl
```
- This step identifies unique patient IDs from the Encounter Diagnosis table, focusing on those diagnosed with Type 2 Diabetes Mellitus, as indicated by the diagnosis codes starting with 'E11'.
- It excludes any patient IDs associated with gestational diabetes, which is represented by diagnosis codes starting with 'O24.4', ensuring that the analysis is specific to non-gestational diabetes cases.
- The result provides a distinct list of patients for targeted healthcare initiatives, quality improvement programs, or further clinical analysis related to Type 2 Diabetes management.
```

### grain_patient · Patient_Grain
```
- This step identifies unique patients from the LAB_RESULTS dataset who have an HbA1c value of 6.5 or higher, indicating potential diabetes or poor glycemic control.
- The selection criteria focus on patients with elevated HbA1c levels, which are critical for assessing the effectiveness of diabetes management strategies.
- By filtering for distinct patient IDs, this step ensures that each patient is counted only once, providing a clear view of the population at risk.
```

### grain_visit · Visit_Grain
```
- This step selects the hospital encounter IDs and admission dates from the HOSPITAL_ENCOUNTERS table.
- The selection is filtered to include only encounters where the ENCOUNTER_TYPE is 'ED', indicating emergency department visits.
```
first pass: 1 violation(s)

### inclusion · Diabetic_Incl
```
- This step identifies unique patient IDs from the Encounter Diagnosis table, focusing on individuals diagnosed with specific conditions related to diabetes (E11%) and gestational diabetes (O24.4%).
- The selection criteria ensure that only patients with these relevant diagnosis codes are included, facilitating targeted analysis of healthcare outcomes for these conditions.
- By filtering for distinct patient IDs, this step helps in understanding the prevalence and management of diabetes-related diagnoses within the patient population.
```

### multi_join · Three_Table
```
- This step selects unique patient identifiers (PATIENT_ID) from the PATIENTS table who have been diagnosed with diabetes (ICD codes starting with 'E11') and have been prescribed specific medications, namely Metformin or Insulin Glargine.  
- The selection is based on the intersection of patients' diagnosis records and their medication orders, ensuring that only those meeting both criteria are included.  
- By focusing on these specific diagnoses and medications, the query aims to identify a targeted group of patients for further analysis or intervention strategies.
```

### negation · No_PCP
```
- This step selects the `PATIENT_ID` from the `ENCOUNTERS` table.
- The selection is based on the condition that there is no corresponding entry in the `PATIENT_PCP_ASSIGNMENT` table for the same `PATIENT_ID`.
```
first pass: 1 violation(s)

### threshold_ge · Threshold_GE
```
- This step selects the PATIENT_IDs from the LAB_RESULTS table.
- The selection is based on the condition that the HBA1C_VALUE must be greater than or equal to 6.5.
```
first pass: 1 violation(s)

### threshold_gt · Threshold_GT
```
- This step selects the unique identifiers of patients from the lab results database who have an HbA1c value exceeding 6.5, indicating potential issues with blood sugar control.
- The condition for inclusion in this selection is that the HbA1c value must be greater than 6.5, which is a critical threshold for assessing diabetes management.
- By identifying these patients, the business can target interventions and improve health outcomes for individuals at risk of diabetes-related complications.
```
