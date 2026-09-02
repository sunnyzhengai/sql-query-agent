# P0-b — adversarial corpus over LIVE generation (production acceptance, ADR 0074)

**11 case(s)** · gate_passed 8 · skeleton_floor 0 · emptied 3

gate_passed = smoothed prose cleared the gate · skeleton_floor = the grounded skeleton shipped (the smoothing catch, if any, is listed) · emptied = voice kill, absence over fabrication (0074 §5.3a). Dictionary-less leg: meanings fall back to readable column names.

## Per class

- **aggregate** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **degenerate_empty** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **degenerate_literal** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **exclusion** — gate_passed 0 · skeleton_floor 0 · emptied 1 · smoothing catch: column name in a business description
- **grain_patient** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **grain_visit** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **inclusion** — gate_passed 0 · skeleton_floor 0 · emptied 1 · smoothing catch: column name in a business description
- **multi_join** — gate_passed 0 · skeleton_floor 0 · emptied 1 · smoothing catch: column name in a business description
- **negation** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **threshold_ge** — gate_passed 1 · skeleton_floor 0 · emptied 0
- **threshold_gt** — gate_passed 1 · skeleton_floor 0 · emptied 0

## Samples (fragment → final description)

### aggregate · High_Utilizer
```
This is a selection of patients.  
- After grouping, the value is no less than 4.
```

### degenerate_empty · Passthrough
```
This is a collection of records.
```

### degenerate_literal · Constant
```
This is a collection of records.
```

### exclusion · Diabetic_Excl
```
(emptied)
```
smoothing catch: 2 violation(s) — the skeleton shipped instead

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
(emptied)
```
smoothing catch: 2 violation(s) — the skeleton shipped instead

### multi_join · Three_Table
```
(emptied)
```
smoothing catch: 2 violation(s) — the skeleton shipped instead

### negation · No_PCP
```
This is a selection of patients.
- No matching record exists (patient id, patient id).
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
