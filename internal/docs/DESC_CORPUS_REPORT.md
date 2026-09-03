# P0-b — adversarial corpus over LIVE generation (production acceptance, ADR 0074)

**21 case(s)** · gate_passed 20 · skeleton_floor 0 · emptied 1

gate_passed = smoothed prose cleared the gate · skeleton_floor = the grounded skeleton shipped (the smoothing catch, if any, is listed) · emptied = voice kill, absence over fabrication (0074 §5.3a). Dictionary-less leg: meanings fall back to readable column names.

## Per class

- **aggregate** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **degenerate_empty** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **degenerate_literal** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **dict_sentence** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **elision** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **exclusion** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **expr_arith** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **expr_depth** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **grain_patient** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **grain_visit** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **inclusion** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **multi_join** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **negation** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **not_between** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **not_in** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **param_default** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **placeholder_fp** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **tautology** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **threshold_ge** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **threshold_gt** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **unrenderable** — gate_passed 0 · skeleton_floor 0 · emptied 1 · smoothing catch: column name in a business description, composer placeholder in a business description

## Samples (fragment → final description)

### aggregate · High_Utilizer
```
This is a selection of patients.
- The number of encounter ID values is a minimum of 4.
```

### degenerate_empty · Passthrough
```
This is a selection of records.  
- In this step, no filtering conditions are applied.
```

### degenerate_literal · Constant
```
This is a selection of records.  
- No source records are read; this step generates derived values.
```

### dict_sentence · Steward_Prose
```
This is a selection of encounters.
- The time specified by the user when the action occurred is documented.
```

### elision · Long_Code_List
```
This is a selection of encounters.
- The flowsheet measure consists of one of the 8 values ranging from 'A1' to 'A8'.
```

### exclusion · Diabetic_Excl
```
This is a selection of patients.
- The diagnosis code begins with 'E11'.
- The diagnosis code does not begin with 'O24.4'.
```

### expr_arith · Weight_Convert
```
This is a selection of patients.
- The weight in kilograms multiplied by 2.2 exceeds 300.
```

### expr_depth · Abx_Window
```
This is a selection of encounters.
- The absolute value of the minutes between the antibiotic administration time and the blood culture order time, divided by 60.00, is no greater than 72.0.
```

### grain_patient · Patient_Grain
```
This is a selection of patients.
- The hba1c value is a minimum of 6.5.
```

### grain_visit · Visit_Grain
```
This is a selection of encounters.
- The encounter type is 'ED'.
```

### inclusion · Diabetic_Incl
```
This is a selection of patients.
- The diagnosis code begins with 'E11' or the diagnosis code begins with 'O24.4'.
```

### multi_join · Three_Table
```
This is a selection of patients.
- The ICD code begins with 'E11'.
- The medication name is 'METFORMIN' or 'INSULIN GLARGINE'.
```

### negation · No_PCP
```
This is a selection of patients.
- No matching record exists for the patient ID.
```

### not_between · A1c_Abnormal
```
This is a selection of patients.
- The hba1c value does not fall within the range of 4 to 5.6.
```

### not_in · Med_Exclusion
```
This is a selection of patients.
- The medication name is not 'METFORMIN' or 'INSULIN'.
```

### param_default · Reporting_Window
```
This is a selection of patients.
- The start date defaults to '2024-01-01' when no value is provided.
- The admission date must be on or after the start date.
```

### placeholder_fp · Value_Set
```
This is a selection of patients.  
- The unique identifier for the value set is 3022.
```

### tautology · Scaffolding
```
This is a selection of patients.  
- The encounter type is 'ED'.
```

### threshold_ge · Threshold_GE
```
This is a selection of patients.
- The hba1c value is a minimum of 6.5.
```

### threshold_gt · Threshold_GT
```
This is a selection of patients.
- The hba1c value exceeds 6.5.
```

### unrenderable · Case_Predicate
```
(emptied)
```
smoothing catch: 6 violation(s) — the skeleton shipped instead
