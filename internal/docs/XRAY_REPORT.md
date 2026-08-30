# SQL Intelligence Agent Estate X-Ray — AIVIA Demo Health
Generated 2026-08-30 18:16 UTC

## Your estate, in numbers

- certified metrics discovered: 37
- certified steps discovered: 65
- certified terms discovered: 0
- certified reports discovered: 1
- certified measures discovered: 0

## Governance red flags (26 found by the sweep)

### Diabetes Registry — cousin_conflict (CONFLICT)
3 metrics answer to 'Diabetes Registry' with 3 distinct definitions and no designated official — each may be a legitimate purpose awaiting its own label. [cousin_conflict (CONFLICT); flags disclose, never gate]
- members (3): USP_DM_Registry_Composite, USP_DM_Registry_MedDerived, USP_Diabetes_Registry_v1
- distinct logics: 3 · blast radius: 1 certified consumer(s)
- disposition: open

### Diabetic Patients — cousin_conflict (CONFLICT)
10 metrics answer to 'Diabetic Patients' with 10 distinct definitions and no designated official — each may be a legitimate purpose awaiting its own label. [cousin_conflict (CONFLICT); flags disclose, never gate]
- members (10): USP_Diabetic_InclGest, USP_Diabetic_Panel, USP_Diabetic_Patients_DX, USP_Diabetic_Patients_Lab, USP_Panel_ED_Visits, USP_Panel_NoShows, USP_Diabetic_Billing, USP_Diabetic_ExclGest, USP_Active_Diabetics (reporting.USP_Active_Diabetics), USP_Active_Diabetics (reports.USP_Active_Diabetics)
- distinct logics: 10 · blast radius: 0 certified consumer(s)
- disposition: open

### High ED Utilizers — cousin_conflict (CONFLICT)
2 metrics answer to 'High ED Utilizers' with 2 distinct definitions and no designated official — each may be a legitimate purpose awaiting its own label. [cousin_conflict (CONFLICT); flags disclose, never gate]
- members (2): USP_High_ED_Utilizers, USP_High_ED_NoPCP
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### Missed Appointments — cousin_conflict (CONFLICT)
2 metrics answer to 'Missed Appointments' with 2 distinct definitions and no designated official — each may be a legitimate purpose awaiting its own label. [cousin_conflict (CONFLICT); flags disclose, never gate]
- members (2): USP_Panel_NoShows, USP_Missed_Appointments
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### Diabetes Registry — grain_shift (CONFLICT)
'Diabetes Registry' computes at different output grains across its members — the numbers answer different questions under one name. [grain_shift (CONFLICT); flags disclose, never gate]
- members (2): USP_DM_Registry_MedDerived, USP_Diabetes_Registry
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### High ED Utilizers — grain_shift (CONFLICT)
'High ED Utilizers' computes at different output grains across its members — the numbers answer different questions under one name. [grain_shift (CONFLICT); flags disclose, never gate]
- members (2): USP_High_ED_Utilizers (reports.USP_High_ED_Utilizers), USP_High_ED_Utilizers (reporting.USP_High_ED_Utilizers)
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### Active Diabetic Patients — misnomer (CONFLICT)
2 procedures share the name 'Active Diabetic Patients' but compute 2 different logics — one name is doing 2 jobs. [misnomer (CONFLICT); flags disclose, never gate]
- members (2): USP_Active_Diabetics (reporting.USP_Active_Diabetics), USP_Active_Diabetics (reports.USP_Active_Diabetics)
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### Diabetes Registry — misnomer (CONFLICT)
2 procedures share the name 'Diabetes Registry' but compute 2 different logics — one name is doing 2 jobs. [misnomer (CONFLICT); flags disclose, never gate]
- members (2): USP_DM_Registry_MedDerived, USP_Diabetes_Registry
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### Diabetic Codeset — misnomer (CONFLICT)
2 procedures share the name 'Diabetic Codeset' but compute 2 different logics — one name is doing 2 jobs. [misnomer (CONFLICT); flags disclose, never gate]
- members (2): USP_Diabetic_CodesetA, USP_Diabetic_CodesetB
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### High ED Utilizers — misnomer (CONFLICT)
2 procedures share the name 'High ED Utilizers' but compute 2 different logics — one name is doing 2 jobs. [misnomer (CONFLICT); flags disclose, never gate]
- members (2): USP_High_ED_Utilizers (reports.USP_High_ED_Utilizers), USP_High_ED_Utilizers (reporting.USP_High_ED_Utilizers)
- distinct logics: 2 · blast radius: 0 certified consumer(s)
- disposition: open

### Controlled Diabetes Rate — cousin_conflict (INFO)
2 metrics answer to 'Controlled Diabetes Rate' with 1 distinct definitions and no designated official — each may be a legitimate purpose awaiting its own label. [cousin_conflict (INFO); flags disclose, never gate]
- members (2): USP_Controlled_Diabetes, USP_Controlled_Diabetes_M
- distinct logics: 1 · blast radius: 0 certified consumer(s)
- disposition: open

### A1c_High / A1c_Tested / Base_Cohort / Lab_Draws — duplicate (INFO)
identical logic exists under 5 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (5): Lab_Draws (reporting.USP_Diabetic_Patients_DX:Lab_Draws), A1c_High, Base_Cohort, Lab_Draws (reporting.USP_Diabetic_Patients_Lab:Lab_Draws), A1c_Tested
- distinct logics: 1 · blast radius: 3 certified consumer(s)
- disposition: open

### Active Diabetic Patients / Diabetes Registry / Line-Ending Probe A / Line-Ending Probe B — duplicate (INFO)
identical logic exists under 4 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (4): USP_Diabetes_Registry, USP_Crlf_Probe_A, USP_Crlf_Probe_B, USP_Active_Diabetics
- distinct logics: 1 · blast radius: 0 certified consumer(s)
- disposition: open

### Active Diabetic Patients / Enrollment Snapshot — duplicate (INFO)
identical logic exists under 3 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (3): USP_Enrollment_Snapshot (reports.USP_Enrollment_Snapshot), USP_Active_Diabetics, USP_Enrollment_Snapshot (reporting.USP_Enrollment_Snapshot)
- distinct logics: 1 · blast radius: 0 certified consumer(s)
- disposition: open

### Active_Now / Base_Cohort / Cascade_A / Enrolled — duplicate (INFO)
identical logic exists under 5 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (5): Base_Cohort, enrolled, Cascade_A, Active_Now, Enrolled
- distinct logics: 1 · blast radius: 5 certified consumer(s)
- disposition: open

### Active_Now / Crlf_Cohort / Enc_Recent / Med_Orders_Cur — duplicate (INFO)
identical logic exists under 8 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (8): Enc_Recent, Med_Orders_Cur, enc_recent, Rx_Current, Reg_Core, Crlf_Cohort (reporting.USP_Crlf_Probe_A:Crlf_Cohort), Crlf_Cohort (reporting.USP_Crlf_Probe_B:Crlf_Cohort), Active_Now
- distinct logics: 1 · blast radius: 6 certified consumer(s)
- disposition: open

### Controlled Diabetes Rate / Controlled Diabetes Rate (Monthly) — duplicate (INFO)
identical logic exists under 2 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (2): USP_Controlled_Diabetes, USP_Controlled_Diabetes_M
- distinct logics: 1 · blast radius: 0 certified consumer(s)
- disposition: open

### DM Patient List / Diabetes Registry (Legacy v1) / Diabetic Patient Roster — duplicate (INFO)
identical logic exists under 3 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (3): USP_Diabetes_Registry_v1, USP_Diabetic_Roster, USP_DM_Patient_List
- distinct logics: 1 · blast radius: 0 certified consumer(s)
- disposition: open

### Missed Appointments / No-Show Panel — duplicate (INFO)
identical logic exists under 2 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (2): USP_Missed_Appointments, USP_No_Show_Panel
- distinct logics: 1 · blast radius: 0 certified consumer(s)
- disposition: open

### Panel_All / Reach_Base / Reg_Core_v1 — duplicate (INFO)
identical logic exists under 4 different names — consolidation or an alias would end the drift risk. [duplicate (INFO); flags disclose, never gate]
- members (4): Reg_Core_v1, Reach_Base, Panel_All (reporting.USP_Diabetic_Roster:Panel_All), Panel_All (reporting.USP_DM_Patient_List:Panel_All)
- distinct logics: 1 · blast radius: 4 certified consumer(s)
- disposition: open

### A1c_High — misnomer (INFO)
2 procedures share the name 'A1c_High' but compute 2 different logics — one name is doing 2 jobs. [misnomer (INFO); flags disclose, never gate]
- members (2): A1c_High (reporting.USP_Diabetic_Patients_DX:A1c_High), A1c_High (reporting.USP_Diabetic_Patients_Lab:A1c_High)
- distinct logics: 2 · blast radius: 2 certified consumer(s)
- disposition: open

### Active_Now — misnomer (INFO)
2 procedures share the name 'Active_Now' but compute 2 different logics — one name is doing 2 jobs. [misnomer (INFO); flags disclose, never gate]
- members (2): Active_Now (reporting.USP_Active_Diabetics:Active_Now), Active_Now (reports.USP_Active_Diabetics:Active_Now)
- distinct logics: 2 · blast radius: 2 certified consumer(s)
- disposition: open

### Base_Cohort — misnomer (INFO)
11 procedures share the name 'Base_Cohort' but compute 9 different logics — one name is doing 9 jobs. [misnomer (INFO); flags disclose, never gate]
- members (11): Base_Cohort (reporting.USP_Diabetic_InclGest:Base_Cohort), Base_Cohort (reporting.USP_Diabetic_Panel:Base_Cohort), Base_Cohort (reporting.USP_Diabetic_Patients_DX:Base_Cohort), Base_Cohort (reporting.USP_Diabetic_Patients_Lab:Base_Cohort), Base_Cohort (reporting.USP_PreOp_Abnormal_Labs:Base_Cohort), Base_Cohort (reporting.USP_Panel_ED_Visits:Base_Cohort), Base_Cohort (reporting.USP_Panel_NoShows:Base_Cohort), Base_Cohort (reporting.USP_Diabetic_Billing:Base_Cohort), Base_Cohort (reporting.USP_Diabetic_ExclGest:Base_Cohort), Base_Cohort (reporting.USP_DM_Registry_MedDerived:Base_Cohort), Base_Cohort (reporting.USP_High_ED_NoPCP:Base_Cohort)
- distinct logics: 9 · blast radius: 11 certified consumer(s)
- disposition: open

### Coded_Cohort — misnomer (INFO)
2 procedures share the name 'Coded_Cohort' but compute 2 different logics — one name is doing 2 jobs. [misnomer (INFO); flags disclose, never gate]
- members (2): Coded_Cohort (reporting.USP_Diabetic_CodesetA:Coded_Cohort), Coded_Cohort (reports.USP_Diabetic_CodesetB:Coded_Cohort)
- distinct logics: 2 · blast radius: 2 certified consumer(s)
- disposition: open

### Dx_Events — misnomer (INFO)
2 procedures share the name 'Dx_Events' but compute 2 different logics — one name is doing 2 jobs. [misnomer (INFO); flags disclose, never gate]
- members (2): Dx_Events (reporting.USP_Panel_Refresh:Dx_Events), Dx_Events (reporting.USP_Ref_Forms_Probe:Dx_Events)
- distinct logics: 2 · blast radius: 2 certified consumer(s)
- disposition: open

### Utilizers — misnomer (INFO)
2 procedures share the name 'Utilizers' but compute 2 different logics — one name is doing 2 jobs. [misnomer (INFO); flags disclose, never gate]
- members (2): Utilizers (reports.USP_High_ED_Utilizers:Utilizers), Utilizers (reporting.USP_High_ED_Utilizers:Utilizers)
- distinct logics: 2 · blast radius: 2 certified consumer(s)
- disposition: open


## The AI-readiness verdict

**17 name(s) in this estate carry more than one meaning** (A1c_High, Active Diabetic Patients, Active_Now, Base_Cohort, Coded_Cohort, Controlled Diabetes Rate, …).
A name-grounded assistant answers differently depending on which definition it lands on — this is why a generic Copilot hallucinates on this estate. Every conflict above cites its members and their code-level basis; none of this is opinion.

**9 identical logic(s) live under different names** — duplicated maintenance and split usage signals.

VERDICT: NOT AI-READY as it stands — resolve or disclose the conflicting names first. The flags above are the exact work list.

## What happens next

Every number above came from SQL Intelligence Agent's deterministic parsers reading your actual code — no sampling, no opinion. The same engine that found these flags can keep your catalog true continuously: descriptions, proposed business terms, relationships, and steward alerts, every write approved by your people before it lands (SQL Intelligence Agent Bridge). You are not buying a new tool; you are buying the engine that makes your expensive catalog true.
