# Estate before/after — the 09-03 rebuild, hand-gradable

Grade like an L3 walk: is each sentence TRUE of its SQL, and would
a steward learn the membership conditions? 'Before' = the fate of
the same node on the first v7 store run (09-03 morning, from the
run log). Store: 461 descriptions | emptied 124 -> 17 | failed 2 -> 0.

## reports.USP_Severe_Sepsis:ABX

**Before:** EMPTIED — placeholder: the ABS(DATEDIFF)/60 <= 72 window raw-echoed

**Now (gate_passed):**
```
This is a selection of encounters.  
- The user-specified time that the action took place is recorded.  
- The category number for the route of administration of a medication is 11.  
- The MAR action category number associated with this administration is restricted to a separately selected set.  
- The unique ID of the medication record is restricted to a separately selected set.  
- The absolute value of the minutes between the user-specified time that the action took place and blood culture order time, divided by 60.00, is at most 72.0.  
- The ID of the category associated with the therapeutic class that indicates the accepted purpose of the drug, such as “antibiotic” or “antipsychotic,” is 11.
```

## reporting.USP_IP_SepsisDetails:CVVH

**Before:** EMPTIED — misattributed-predicate FALSE KILL (the claim was true)

**Now (skeleton_floor):**
```
This is a selection of encounters.
- The date in normal date format is The instant the reading was taken.
- The unique ID of the flowsheet template (FLT) which was used to enter the data in this cell is '9000001359'.
- The instant the reading was taken falls between in dttm and out dttm.
```

## reporting.USP_IP_SEPSIS:SepsisAuditTemp

**Before:** EMPTIED — the gate flagged the composer's own '25 values' count

**Now (gate_passed):**
```
This is a selection of encounters.  
- The unique ID for the flowsheet group/row associated with this reading is one of 25 values from '9000161701' to '9000003157'.  
- The instant the reading was taken falls between shift start and shift end.  
- Show components is 'Y'.  
- The minutes between od score time and the instant the reading was taken falls between negative 30 and 180.
```

## reporting.USP_ED_Sepsis:All_LDAs

**Before:** EMPTIED — 'the value set' tripped the placeholder ban (false kill)

**Now (gate_passed):**
```
This is a selection of encounters.  
- This item stores the placement instant of the record.  
- This item stores the placement instant of the record that falls between adt arrival time and ed departure time.  
- This item stores the Flowsheet ID that defines the structure of this record as '900112', '900111', or the Unique identifier for the value set as 3022.
```

## reporting.USP_IP_SEPSIS:Base_Pop

**Before:** EMPTIED — placeholder: unvoiced leaves raw-echoed

**Now (gate_passed):**
```
This is a selection of patients.  
- in dept rn is 1.  
- department rollup is not 'ER', 'P-ER'.  
- the dateadd of d, 1, expansion date is at most expansion end date.
```

## reporting.USP_IP_SEPSIS:dateCTE

**Before:** EMPTIED — placeholder: parameter-default logic raw-echoed

**Now (gate_passed):**
```
This is a selection of patients.  
- in dept rn is 1.  
- department rollup is not 'ER', 'P-ER'.  
- the dateadd of d, 1, expansion date is at most expansion end date.
```

## reporting.USP_ED_Sepsis:Base_Pop

**Before:** SHIPPED MUSH pre-ban — 'the line number ... is 1' era prose

**Now (gate_passed):**
```
This is a selection of patients.  
- The line number for the information associated with this record is 1.  
- The date of the PATIENTS's arrival is between d start date and d end date.
```

## reports.USP_Severe_Sepsis:Hypotension

**Before:** EMPTIED — column name in a business description (MEAS_VALUE)

**Now (gate_passed):**
```
This is a selection of encounters.  
- The unique ID for the flowsheet group/row associated with this reading is '95'.  
- The instant the reading was taken is recorded.  
- The actual value of the flowsheet reading is recorded.  
- The instant the reading was taken falls between the dateadd of HH, negative 24, ftz and the dateadd of HH, 24, ftz.  
- Age months is less than 2 or the left of the actual value of the flowsheet reading and the charindex of '/' and the actual value of the flowsheet reading, minus 1 is less than 65 or age months is at least 2 or age months is less than 12 or the left of the actual value of the flowsheet reading and the charindex of '/' and the actual value of the flowsheet reading, minus 1 is less than 70 or age years is at least 1 or age years is less than 2 or the left of the actual value of the flowsheet reading and the charindex of '/' and the actual value of the flowsheet reading, minus 1 is less than 80 or age years is at least 2 or age years is less than 6 or the left of the actual value of the flowsheet reading and the charindex of '/' and the actual value of the flowsheet reading, minus 1 is less than 90 or age years is at least 6 or age years is less than 13 or the left of the actual value of the flowsheet reading and the charindex of '/' and the actual value of the flowsheet reading, minus 1 is less than 100 or age years is at least 13 or the left of the actual value of the flowsheet reading and the charindex of '/' and the actual value of the flowsheet reading, minus 1 is less than 110.
```
