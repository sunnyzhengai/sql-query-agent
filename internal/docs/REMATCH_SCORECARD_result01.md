***how many metrics are available
- graph agent: 
  -- 35 sec. query time
  -- answer: There are 28 business metrics available in the certified knowledge base.
- delta agent:
  -- 15 sec
  -- answer: There are 28 metrics available in the system. If you'd like to see a list of these metrics or learn more about what any of them measure, just let me know!


***give me 5 metrics about sepsis
- graph agent: 8 sec
  -- answer: I don't have any sepsis-related metrics in the certified knowledge base.
  -- 2nd try: 4 sec, Here are 5 metrics about sepsis from the certified knowledge base:
USP_ED_Sepsis
USP_IP_SEPSIS
USP_IP_SEPSIS_COMPLIANCE
USP_IP_SepsisDetails
USP_IP_SepsisEncounters
If you want more details or descriptions about any of these metrics, just let me know!
- delta agent:
  -- 9 sec
  -- answer: No metrics related to sepsis were found in the system. It's possible that sepsis metrics have not been added yet, are labeled differently, or the search term may need adjusting. If you have other keywords or specifics you'd like to search for, I can check those as well. Let me know how you'd like to proceed!


***list all 28 metrics
- graph agent: 12 sec
  -- answer: Here are all 28 business metrics available in the certified knowledge base (note: many relate to sepsis):

USP_ED_Sepsis
USP_IP_SEPSIS
USP_IP_SEPSIS_COMPLIANCE
USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES
USP_IP_SEPSIS_REPORT
USP_IP_SepsisDates
USP_IP_SepsisDetails
USP_IP_SepsisDetails_v1
USP_IP_SepsisEncounters
USP_IP_SepsisEncountersDetails
USP_IP_SepsisEncountersWLocations
USP_IP_SepsisEncountersWLocations_v1
USP_IP_SepsisPatientDates
USP_IP_SepsisPatientDates_v1
USP_IP_SepsisScreeningAudit
USP_IP_SepsisScreeningAudit_v1
USP_IP_SepsisShiftCompliance
USP_IP_SepsisShiftComplianceByShift
USP_IP_SepsisShiftComplianceMetrics
USP_IP_Sepsis_ComplianceByShift
USP_IP_Sepsis_ComplianceMetrics
USP_IP_Sepsis_Details
USP_IP_Sepsis_Encounters
USP_IP_Sepsis_ScreeningTool
USP_NonSevere_Sepsis
USP_Severe_Sepsis
Note: The descriptions were not provided for these metrics in the knowledge base. Most of these metrics are related to sepsis. If you need details on any specific metric, let me know!

***how is USP_ED_Sepsis calculated?
- graph agent: 17 sec
  -- answer: The USP_ED_Sepsis metric is calculated using information from several key hospital data tables. It incorporates medication, patient location, encounter, and clinical measurement data to identify and track sepsis cases in the Emergency Department.

The calculation is based on the following main sources and logic:

V_PHARMACY_ORDER: Used to obtain details of medication orders (such as antibiotics), including order date and time.
V_PHARMACY_DISPENSE: Supplies data on when medications were dispensed.
ORDER_DISPENSE_INFO: Provides additional information about medication dispensing events.
RX_VERIFY_TRACE: Tracks when medications are verified in the pharmacy queue.
EMPLOYEES: Contains information about staff (used for verified/dispensed actions).
VISIT_REASONS and ENCOUNTER_VISIT_REASONS: Identify reasons for visit that help define the population included.
HOSPITAL_ENCOUNTERS: Links hospital encounters, like Emergency Department visits.
FLOWSHEET_RECORDS and FLOWSHEET_MEASUREMENTS: Contain patient-specific clinical measurement data and records, such as sepsis alert documentation or physiological scores.
V_PATIENT_LOCATION_HISTORY: Determines the patient’s location in the hospital at specified times (to verify ED presence).
The process involves:

Identifying Emergency Department encounters with reasons or clinical indicators related to sepsis,
Linking those encounters to medication events (orders, verification, dispensing),
Using clinical measurement and flowsheet data to identify relevant clinical events (e.g., sepsis alerts, physiological scores),
Determining the precise timing of medication administration,
Incorporating patient demographic and staff assignment information where needed,
Ensuring that all relevant events occurred while the patient was in the ED, based on location history.
Grounded tables: V_PHARMACY_ORDER, V_PHARMACY_DISPENSE, ORDER_DISPENSE_INFO, RX_VERIFY_TRACE, EMPLOYEES, VISIT_REASONS, ENCOUNTER_VISIT_REASONS, HOSPITAL_ENCOUNTERS, FLOWSHEET_RECORDS, FLOWSHEET_MEASUREMENTS, V_PATIENT_LOCATION_HISTORY.

If you need more detail about a specific part of the calculation workflow, let me know!


***which tables does USP_ED_Sepsis use?
- graph agent: 4 sec
  -- answer: The USP_ED_Sepsis metric uses the following tables in its calculation:

V_PHARMACY_ORDER
V_PHARMACY_DISPENSE
ORDER_DISPENSE_INFO
RX_VERIFY_TRACE
EMPLOYEES
VISIT_REASONS
ENCOUNTER_VISIT_REASONS
HOSPITAL_ENCOUNTERS
FLOWSHEET_RECORDS
FLOWSHEET_MEASUREMENTS
V_PATIENT_LOCATION_HISTORY
These tables provide data on medication orders and dispensing, patient encounters, clinical measurements, reasons for visit, pharmacy verification, staff details, and patient location in the hospital.




***Which metrics read from the PAT_ENC_HSP table?
- graph agent: 38 sec
  -- answer: I don't have any metrics in the certified knowledge base that use the PAT_ENC_HSP table.
