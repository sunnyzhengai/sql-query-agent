# debug02_dictionary_direct — Sunny's comparison test (2026-10-04)

Setup: NO phase-06 technical description. Docket = the RAW SQL + the 02 dictionary descriptions directly (used tables, used described columns, bound value meanings). Same prompt law (S1-S14), same Gate v2, gpt-5.4.

Result: PASS after 1 round(s).

THE DICTIONARY-DIRECT CARD (verbatim):

> One row is: one inpatient census event for a patient, representing that patient’s counted hospital status at a specific effective time.
> 
> Who's in it: patients with a census event during the chosen date range, in the chosen service area and location selections when running the report. Choosing All for service area or location includes every value. The report leaves out activity from these departments: CCMC EMERGENCY, CCMC IR IMAGING, CCMC CATH LAB, CCMC MAIN OR, CCMC SPA OR, CCMC PHP PSYCHIATRY, CCMC CARDIOVASCULAR OR, DSC OR, and EMH OVERFLOW.
> 
> Each row shows: the patient tied to the census event, where the patient was assigned in the hospital, how the encounter was classified, the patient service, and identifying details for the event.
> 
> Time window: it includes census events with an effective time from the chosen start date through the chosen end date, including the full end date. It shows the data as it stood by the chosen as-of date, including only events entered by the end of that date. If an event was later canceled, it is still included when that cancellation did not happen until after the as-of date; if it had already been canceled by then, it is not included.
> 
> Excludes: records not linked to a patient, events outside the chosen date range, events entered after the as-of date, events already canceled by the as-of date, and records from the listed excluded departments.

(Claude's comparison vs the floor-based card and the golden standard follows in chat and is appended after her read.)
