# P0-b — adversarial corpus over LIVE generation (production acceptance, ADR 0074)

**11 case(s)** · gate_passed 11 · skeleton_floor 0 · emptied 0

gate_passed = smoothed prose cleared the gate · skeleton_floor = the grounded skeleton shipped (the smoothing catch, if any, is listed) · emptied = voice kill, absence over fabrication (0074 §5.3a). Dictionary-less leg: meanings fall back to readable column names.

## Per class

- **aggregate** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **degenerate_empty** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **degenerate_literal** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **exclusion** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **grain_patient** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **grain_visit** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **inclusion** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **multi_join** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **negation** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **threshold_ge** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **threshold_gt** — gate_passed 1 · skeleton_floor 0 · emptied 0

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

### exclusion · Diabetic_Excl
```
This is a selection of patients.
- The diagnosis code begins with 'E11'.
- The diagnosis code does not begin with 'O24.4'.
```

### grain_patient · Patient_Grain
```
This is a selection of patients.
- The HbA1c value is at least 6.5.
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

### threshold_ge · Threshold_GE
```
This is a selection of patients.
- The HbA1c value is at least 6.5.
```

### threshold_gt · Threshold_GT
```
This is a selection of patients.
- The HbA1c value is greater than 6.5.
```
