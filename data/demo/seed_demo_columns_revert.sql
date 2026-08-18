-- REVERT contaminated v1 patch columns (cross-proc + alias-rebind
-- contamination -> 'Ambiguous column name'). Idempotent; baseline
-- = the 428 columns applied live (commit e52fad9).

IF COL_LENGTH('dbo.adt_events', 'adt_DEPARTMENT_ID') IS NOT NULL
ALTER TABLE [dbo].[adt_events] DROP COLUMN [adt_DEPARTMENT_ID];
GO

IF COL_LENGTH('dbo.adt_events', 'ADT_DEPARTMENT_NAME') IS NOT NULL
ALTER TABLE [dbo].[adt_events] DROP COLUMN [ADT_DEPARTMENT_NAME];
GO

IF COL_LENGTH('dbo.adt_events', 'ED2ICUTime') IS NOT NULL
ALTER TABLE [dbo].[adt_events] DROP COLUMN [ED2ICUTime];
GO

IF COL_LENGTH('dbo.adt_events', 'IN_DTTM') IS NOT NULL
ALTER TABLE [dbo].[adt_events] DROP COLUMN [IN_DTTM];
GO

IF COL_LENGTH('dbo.adt_events', 'OUT_DTTM') IS NOT NULL
ALTER TABLE [dbo].[adt_events] DROP COLUMN [OUT_DTTM];
GO

IF COL_LENGTH('dbo.calendar_dates', 'ABXName') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [ABXName];
GO

IF COL_LENGTH('dbo.calendar_dates', 'ABXTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [ABXTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'ABXVolume') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [ABXVolume];
GO

IF COL_LENGTH('dbo.calendar_dates', 'BloodCultureOrderTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [BloodCultureOrderTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'BloodCultureProcedureOrdered') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [BloodCultureProcedureOrdered];
GO

IF COL_LENGTH('dbo.calendar_dates', 'BloodCultureResult') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [BloodCultureResult];
GO

IF COL_LENGTH('dbo.calendar_dates', 'Bolus') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [Bolus];
GO

IF COL_LENGTH('dbo.calendar_dates', 'BolusTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [BolusTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'BolusVolume') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [BolusVolume];
GO

IF COL_LENGTH('dbo.calendar_dates', 'BPPercentile') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [BPPercentile];
GO

IF COL_LENGTH('dbo.calendar_dates', 'CSFOrdered') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [CSFOrdered];
GO

IF COL_LENGTH('dbo.calendar_dates', 'CSFOrderTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [CSFOrderTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'CSFValue') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [CSFValue];
GO

IF COL_LENGTH('dbo.calendar_dates', 'CVVHYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [CVVHYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'DobutamineYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [DobutamineYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'DopamineYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [DopamineYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'ECMOYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [ECMOYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'EDLosHours') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [EDLosHours];
GO

IF COL_LENGTH('dbo.calendar_dates', 'EncounterWeight') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [EncounterWeight];
GO

IF COL_LENGTH('dbo.calendar_dates', 'ENCOVERALLORDER') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [ENCOVERALLORDER];
GO

IF COL_LENGTH('dbo.calendar_dates', 'EpinephrineYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [EpinephrineYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'FirstPositiveScoreInED') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [FirstPositiveScoreInED];
GO

IF COL_LENGTH('dbo.calendar_dates', 'FirstPositiveScoreTimeInED') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [FirstPositiveScoreTimeInED];
GO

IF COL_LENGTH('dbo.calendar_dates', 'HypotensionTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [HypotensionTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'HypotensionValue') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [HypotensionValue];
GO

IF COL_LENGTH('dbo.calendar_dates', 'IntubationTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [IntubationTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'IPSOSevereSepsisYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [IPSOSevereSepsisYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'LacticAcidOrderTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [LacticAcidOrderTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'LacticAcidResult') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [LacticAcidResult];
GO

IF COL_LENGTH('dbo.calendar_dates', 'MilrinoneYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [MilrinoneYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'NorepinephrineYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [NorepinephrineYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'OrderSetID') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [OrderSetID];
GO

IF COL_LENGTH('dbo.calendar_dates', 'OrderSetTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [OrderSetTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'OXYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [OXYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'PATENCENCID') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [PATENCENCID];
GO

IF COL_LENGTH('dbo.calendar_dates', 'PIVPlacementTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [PIVPlacementTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'PositiveODScore') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [PositiveODScore];
GO

IF COL_LENGTH('dbo.calendar_dates', 'PressorYN') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [PressorYN];
GO

IF COL_LENGTH('dbo.calendar_dates', 'ProcalcitoninOrderTime') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [ProcalcitoninOrderTime];
GO

IF COL_LENGTH('dbo.calendar_dates', 'ProcalcitoninResult') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [ProcalcitoninResult];
GO

IF COL_LENGTH('dbo.calendar_dates', 'RefreshDate') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [RefreshDate];
GO

IF COL_LENGTH('dbo.calendar_dates', 'SepsisDate') IS NOT NULL
ALTER TABLE [dbo].[calendar_dates] DROP COLUMN [SepsisDate];
GO

IF COL_LENGTH('dbo.config_grouper_categories', 'BASE_GROUPER_ID') IS NOT NULL
ALTER TABLE [dbo].[config_grouper_categories] DROP COLUMN [BASE_GROUPER_ID];
GO

IF COL_LENGTH('dbo.config_grouper_categories', 'CODE') IS NOT NULL
ALTER TABLE [dbo].[config_grouper_categories] DROP COLUMN [CODE];
GO

IF COL_LENGTH('dbo.config_grouper_categories', 'COMPILED_CONTEXT') IS NOT NULL
ALTER TABLE [dbo].[config_grouper_categories] DROP COLUMN [COMPILED_CONTEXT];
GO

IF COL_LENGTH('dbo.config_grouper_categories', 'GROUPER_LIST') IS NOT NULL
ALTER TABLE [dbo].[config_grouper_categories] DROP COLUMN [GROUPER_LIST];
GO

IF COL_LENGTH('dbo.config_grouper_categories', 'GROUPER_RECORDS_NUMERIC_ID') IS NOT NULL
ALTER TABLE [dbo].[config_grouper_categories] DROP COLUMN [GROUPER_RECORDS_NUMERIC_ID];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'ABX_ADMIN_TIME') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [ABX_ADMIN_TIME];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'ABX_LINE') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [ABX_LINE];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'ABX_ORDER_TIME') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [ABX_ORDER_TIME];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'ADT_ARRIVAL_TIME') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [ADT_ARRIVAL_TIME];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'AGE_MONTHS') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [AGE_MONTHS];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'AGE_YEARS') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [AGE_YEARS];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'AntibioticAdministeredTime_V60') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [AntibioticAdministeredTime_V60];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'AntibioticOrderedTime_V59') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [AntibioticOrderedTime_V59];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'BLOOD_CULTURE_ORDER_TIME') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [BLOOD_CULTURE_ORDER_TIME];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'BloodCultureOrderedTime_V61') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [BloodCultureOrderedTime_V61];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'DATE_STAMP') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [DATE_STAMP];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'ED_DEPARTURE_TIME') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [ED_DEPARTURE_TIME];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'ENCOUNTER_ID') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [ENCOUNTER_ID];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'FIRST_ABX_ADMIN_TIME') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [FIRST_ABX_ADMIN_TIME];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'FLO_MEAS_ID') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [FLO_MEAS_ID];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'FSD_ID') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [FSD_ID];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'INPATIENT_DATA_ID') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [INPATIENT_DATA_ID];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'RECORDED_TIME') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [RECORDED_TIME];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'REVIEWED') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [REVIEWED];
GO

IF COL_LENGTH('dbo.ed_event_templates', 'Sepsis_Episode_ID_V01') IS NOT NULL
ALTER TABLE [dbo].[ed_event_templates] DROP COLUMN [Sepsis_Episode_ID_V01];
GO

IF COL_LENGTH('dbo.encounter_diagnoses', 'HOSPITAL_ACCOUNT_ID') IS NOT NULL
ALTER TABLE [dbo].[encounter_diagnoses] DROP COLUMN [HOSPITAL_ACCOUNT_ID];
GO

IF COL_LENGTH('dbo.encounter_visit_reasons', 'AllEncReasons') IS NOT NULL
ALTER TABLE [dbo].[encounter_visit_reasons] DROP COLUMN [AllEncReasons];
GO

IF COL_LENGTH('dbo.encounter_visit_reasons', 'ALRT_SP_OVR_RSN_CODE') IS NOT NULL
ALTER TABLE [dbo].[encounter_visit_reasons] DROP COLUMN [ALRT_SP_OVR_RSN_CODE];
GO

IF COL_LENGTH('dbo.encounter_visit_reasons', 'NAME') IS NOT NULL
ALTER TABLE [dbo].[encounter_visit_reasons] DROP COLUMN [NAME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'ABX_ADMIN_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [ABX_ADMIN_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'ABX_LINE') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [ABX_LINE];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'ABX_ORDER_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [ABX_ORDER_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'ADT_ARRIVAL_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [ADT_ARRIVAL_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'AGE_MONTHS') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [AGE_MONTHS];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'AGE_YEARS') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [AGE_YEARS];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'AntibioticAdministeredTime_V60') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [AntibioticAdministeredTime_V60];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'AntibioticOrderedTime_V59') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [AntibioticOrderedTime_V59];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'BLOOD_CULTURE_ORDER_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [BLOOD_CULTURE_ORDER_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'BloodCultureOrderedTime_V61') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [BloodCultureOrderedTime_V61];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'BP') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [BP];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'DATE_STAMP') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [DATE_STAMP];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'ED_DEPARTURE_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [ED_DEPARTURE_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'ENC_ID') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [ENC_ID];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'ENCOUNTER_ID') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [ENCOUNTER_ID];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'FIRST_ABX_ADMIN_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [FIRST_ABX_ADMIN_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'Hypotension') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [Hypotension];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'INPATIENT_DATA_ID') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [INPATIENT_DATA_ID];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'RECORD_ID') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [RECORD_ID];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'RECORD_NAME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [RECORD_NAME];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'REVIEWED') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [REVIEWED];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'Score') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [Score];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'Sepsis') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [Sepsis];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'Sepsis_Episode_ID_V01') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [Sepsis_Episode_ID_V01];
GO

IF COL_LENGTH('dbo.flowsheet_measurements', 'Unique') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_measurements] DROP COLUMN [Unique];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'ABX_ADMIN_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [ABX_ADMIN_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'ADT_ARRIVAL_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [ADT_ARRIVAL_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'ADT_DEPARTMENT_ID') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [ADT_DEPARTMENT_ID];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'ADT_DEPARTMENT_NAME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [ADT_DEPARTMENT_NAME];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'AGE_MONTHS') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [AGE_MONTHS];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'AGE_YEARS') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [AGE_YEARS];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'ED_DEPARTURE_TIME') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [ED_DEPARTURE_TIME];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'ENCOUNTER_ID') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [ENCOUNTER_ID];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'IN_DTTM') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [IN_DTTM];
GO

IF COL_LENGTH('dbo.flowsheet_records', 'OUT_DTTM') IS NOT NULL
ALTER TABLE [dbo].[flowsheet_records] DROP COLUMN [OUT_DTTM];
GO

IF COL_LENGTH('dbo.grouper_compiled_list', 'CODE') IS NOT NULL
ALTER TABLE [dbo].[grouper_compiled_list] DROP COLUMN [CODE];
GO

IF COL_LENGTH('dbo.grouper_compiled_list', 'GROUPER_ID') IS NOT NULL
ALTER TABLE [dbo].[grouper_compiled_list] DROP COLUMN [GROUPER_ID];
GO

IF COL_LENGTH('dbo.grouper_compiled_list', 'GROUPER_LIST') IS NOT NULL
ALTER TABLE [dbo].[grouper_compiled_list] DROP COLUMN [GROUPER_LIST];
GO

IF COL_LENGTH('dbo.grouper_compiled_list', 'LIST_CAT_VALUE_CODE') IS NOT NULL
ALTER TABLE [dbo].[grouper_compiled_list] DROP COLUMN [LIST_CAT_VALUE_CODE];
GO

IF COL_LENGTH('dbo.grouper_groups', 'BASE_GROUPER_ID') IS NOT NULL
ALTER TABLE [dbo].[grouper_groups] DROP COLUMN [BASE_GROUPER_ID];
GO

IF COL_LENGTH('dbo.grouper_groups', 'CODE') IS NOT NULL
ALTER TABLE [dbo].[grouper_groups] DROP COLUMN [CODE];
GO

IF COL_LENGTH('dbo.grouper_groups', 'COMPILED_CONTEXT') IS NOT NULL
ALTER TABLE [dbo].[grouper_groups] DROP COLUMN [COMPILED_CONTEXT];
GO

IF COL_LENGTH('dbo.grouper_groups', 'GROUPER_RECORDS_NUMERIC_ID') IS NOT NULL
ALTER TABLE [dbo].[grouper_groups] DROP COLUMN [GROUPER_RECORDS_NUMERIC_ID];
GO

IF COL_LENGTH('dbo.grouper_groups', 'LIST_CAT_VALUE_CODE') IS NOT NULL
ALTER TABLE [dbo].[grouper_groups] DROP COLUMN [LIST_CAT_VALUE_CODE];
GO

IF COL_LENGTH('dbo.grouper_med_records', 'COMPILED_CONTEXT') IS NOT NULL
ALTER TABLE [dbo].[grouper_med_records] DROP COLUMN [COMPILED_CONTEXT];
GO

IF COL_LENGTH('dbo.grouper_terminology', 'BASE_GROUPER_ID') IS NOT NULL
ALTER TABLE [dbo].[grouper_terminology] DROP COLUMN [BASE_GROUPER_ID];
GO

IF COL_LENGTH('dbo.grouper_terminology', 'COMPILED_CONTEXT') IS NOT NULL
ALTER TABLE [dbo].[grouper_terminology] DROP COLUMN [COMPILED_CONTEXT];
GO

IF COL_LENGTH('dbo.grouper_terminology', 'GROUPER_LIST') IS NOT NULL
ALTER TABLE [dbo].[grouper_terminology] DROP COLUMN [GROUPER_LIST];
GO

IF COL_LENGTH('dbo.grouper_terminology', 'GROUPER_RECORDS_NUMERIC_ID') IS NOT NULL
ALTER TABLE [dbo].[grouper_terminology] DROP COLUMN [GROUPER_RECORDS_NUMERIC_ID];
GO

IF COL_LENGTH('dbo.grouper_terminology', 'LIST_CAT_VALUE_CODE') IS NOT NULL
ALTER TABLE [dbo].[grouper_terminology] DROP COLUMN [LIST_CAT_VALUE_CODE];
GO

IF COL_LENGTH('dbo.hospital_acct_diagnoses', 'ENCOUNTER_ID') IS NOT NULL
ALTER TABLE [dbo].[hospital_acct_diagnoses] DROP COLUMN [ENCOUNTER_ID];
GO

IF COL_LENGTH('dbo.lab_components', 'LRR_ID') IS NOT NULL
ALTER TABLE [dbo].[lab_components] DROP COLUMN [LRR_ID];
GO

IF COL_LENGTH('dbo.lab_order_results', 'ORDER_MED_ID') IS NOT NULL
ALTER TABLE [dbo].[lab_order_results] DROP COLUMN [ORDER_MED_ID];
GO

IF COL_LENGTH('dbo.locations', 'ADTDepartmentName') IS NOT NULL
ALTER TABLE [dbo].[locations] DROP COLUMN [ADTDepartmentName];
GO

IF COL_LENGTH('dbo.locations', 'DepartmentRollup') IS NOT NULL
ALTER TABLE [dbo].[locations] DROP COLUMN [DepartmentRollup];
GO

IF COL_LENGTH('dbo.locations', 'ENCORDER') IS NOT NULL
ALTER TABLE [dbo].[locations] DROP COLUMN [ENCORDER];
GO

IF COL_LENGTH('dbo.locations', 'InDepartmentTime') IS NOT NULL
ALTER TABLE [dbo].[locations] DROP COLUMN [InDepartmentTime];
GO

IF COL_LENGTH('dbo.locations', 'OutDepartmentTime') IS NOT NULL
ALTER TABLE [dbo].[locations] DROP COLUMN [OutDepartmentTime];
GO

IF COL_LENGTH('dbo.locations', 'PATENCENCID') IS NOT NULL
ALTER TABLE [dbo].[locations] DROP COLUMN [PATENCENCID];
GO

IF COL_LENGTH('dbo.locations', 'UniqueRow') IS NOT NULL
ALTER TABLE [dbo].[locations] DROP COLUMN [UniqueRow];
GO

IF COL_LENGTH('dbo.medication_orders', 'ORDER_DTTM') IS NOT NULL
ALTER TABLE [dbo].[medication_orders] DROP COLUMN [ORDER_DTTM];
GO

IF COL_LENGTH('dbo.medication_orders', 'ORDER_ID') IS NOT NULL
ALTER TABLE [dbo].[medication_orders] DROP COLUMN [ORDER_ID];
GO

IF COL_LENGTH('dbo.medication_orders', 'PRL_ORDERSET_ID') IS NOT NULL
ALTER TABLE [dbo].[medication_orders] DROP COLUMN [PRL_ORDERSET_ID];
GO

IF COL_LENGTH('dbo.medications', 'ERX_ID') IS NOT NULL
ALTER TABLE [dbo].[medications] DROP COLUMN [ERX_ID];
GO

IF COL_LENGTH('dbo.order_tracking_metrics', 'HV_DISCR_FREQ_ID') IS NOT NULL
ALTER TABLE [dbo].[order_tracking_metrics] DROP COLUMN [HV_DISCR_FREQ_ID];
GO

IF COL_LENGTH('dbo.order_tracking_metrics', 'MED_ROUTE_CODE') IS NOT NULL
ALTER TABLE [dbo].[order_tracking_metrics] DROP COLUMN [MED_ROUTE_CODE];
GO

IF COL_LENGTH('dbo.order_tracking_metrics', 'MEDICATION_ID') IS NOT NULL
ALTER TABLE [dbo].[order_tracking_metrics] DROP COLUMN [MEDICATION_ID];
GO

IF COL_LENGTH('dbo.order_tracking_metrics', 'ORDER_INST') IS NOT NULL
ALTER TABLE [dbo].[order_tracking_metrics] DROP COLUMN [ORDER_INST];
GO

IF COL_LENGTH('dbo.order_tracking_metrics', 'ORDER_MED_ID') IS NOT NULL
ALTER TABLE [dbo].[order_tracking_metrics] DROP COLUMN [ORDER_MED_ID];
GO

IF COL_LENGTH('dbo.patient_encounters', 'ADTArrivalTime') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [ADTArrivalTime];
GO

IF COL_LENGTH('dbo.patient_encounters', 'ADTDepartmentID') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [ADTDepartmentID];
GO

IF COL_LENGTH('dbo.patient_encounters', 'ADTDepartmentName') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [ADTDepartmentName];
GO

IF COL_LENGTH('dbo.patient_encounters', 'AgeMonths') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [AgeMonths];
GO

IF COL_LENGTH('dbo.patient_encounters', 'AgeYears') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [AgeYears];
GO

IF COL_LENGTH('dbo.patient_encounters', 'AllEncDx') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [AllEncDx];
GO

IF COL_LENGTH('dbo.patient_encounters', 'AllEncReasons') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [AllEncReasons];
GO

IF COL_LENGTH('dbo.patient_encounters', 'BirthDate') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [BirthDate];
GO

IF COL_LENGTH('dbo.patient_encounters', 'Disposition') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [Disposition];
GO

IF COL_LENGTH('dbo.patient_encounters', 'EDDepartureTime') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [EDDepartureTime];
GO

IF COL_LENGTH('dbo.patient_encounters', 'EthnicGroup') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [EthnicGroup];
GO

IF COL_LENGTH('dbo.patient_encounters', 'HospAdmsnTime') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [HospAdmsnTime];
GO

IF COL_LENGTH('dbo.patient_encounters', 'HospDischTime') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [HospDischTime];
GO

IF COL_LENGTH('dbo.patient_encounters', 'InDepartmentTime') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [InDepartmentTime];
GO

IF COL_LENGTH('dbo.patient_encounters', 'InpAdmDate') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [InpAdmDate];
GO

IF COL_LENGTH('dbo.patient_encounters', 'InpatientDataID') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [InpatientDataID];
GO

IF COL_LENGTH('dbo.patient_encounters', 'Location') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [Location];
GO

IF COL_LENGTH('dbo.patient_encounters', 'LosHours') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [LosHours];
GO

IF COL_LENGTH('dbo.patient_encounters', 'OutDepartmentTime') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [OutDepartmentTime];
GO

IF COL_LENGTH('dbo.patient_encounters', 'PATENCENCID') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [PATENCENCID];
GO

IF COL_LENGTH('dbo.patient_encounters', 'PatientID') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [PatientID];
GO

IF COL_LENGTH('dbo.patient_encounters', 'PATIENTMRN') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [PATIENTMRN];
GO

IF COL_LENGTH('dbo.patient_encounters', 'PatientName') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [PatientName];
GO

IF COL_LENGTH('dbo.patient_encounters', 'Race') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [Race];
GO

IF COL_LENGTH('dbo.patient_encounters', 'UniqueRow') IS NOT NULL
ALTER TABLE [dbo].[patient_encounters] DROP COLUMN [UniqueRow];
GO

IF COL_LENGTH('dbo.ref_alert_override_reasons', 'AllEncReasons') IS NOT NULL
ALTER TABLE [dbo].[ref_alert_override_reasons] DROP COLUMN [AllEncReasons];
GO

IF COL_LENGTH('dbo.ref_alert_override_reasons', 'ENC_REASON_ID') IS NOT NULL
ALTER TABLE [dbo].[ref_alert_override_reasons] DROP COLUMN [ENC_REASON_ID];
GO

IF COL_LENGTH('dbo.ref_alert_override_reasons', 'ENCOUNTER_ID') IS NOT NULL
ALTER TABLE [dbo].[ref_alert_override_reasons] DROP COLUMN [ENCOUNTER_ID];
GO

IF COL_LENGTH('dbo.ref_alert_override_reasons', 'LINE') IS NOT NULL
ALTER TABLE [dbo].[ref_alert_override_reasons] DROP COLUMN [LINE];
GO

IF COL_LENGTH('dbo.treatment_teams', 'MEAS_VALUE') IS NOT NULL
ALTER TABLE [dbo].[treatment_teams] DROP COLUMN [MEAS_VALUE];
GO

IF COL_LENGTH('reports.config_value_set', 'AGENT') IS NOT NULL
ALTER TABLE [reports].[config_value_set] DROP COLUMN [AGENT];
GO

IF COL_LENGTH('reports.config_value_set', 'AGENT_GROUP') IS NOT NULL
ALTER TABLE [reports].[config_value_set] DROP COLUMN [AGENT_GROUP];
GO

IF COL_LENGTH('reports.config_value_set', 'DOT_MONITORING') IS NOT NULL
ALTER TABLE [reports].[config_value_set] DROP COLUMN [DOT_MONITORING];
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'GROUPER_ID') IS NOT NULL
ALTER TABLE [reports].[severe_sepsis_staging] DROP COLUMN [GROUPER_ID];
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ORDER_DTTM') IS NOT NULL
ALTER TABLE [reports].[severe_sepsis_staging] DROP COLUMN [ORDER_DTTM];
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'PRESSOR_START_TIME') IS NOT NULL
ALTER TABLE [reports].[severe_sepsis_staging] DROP COLUMN [PRESSOR_START_TIME];
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ScreenTime') IS NOT NULL
ALTER TABLE [reports].[severe_sepsis_staging] DROP COLUMN [ScreenTime];
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Sepsis') IS NOT NULL
ALTER TABLE [reports].[severe_sepsis_staging] DROP COLUMN [Sepsis];
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'SS_LINE') IS NOT NULL
ALTER TABLE [reports].[severe_sepsis_staging] DROP COLUMN [SS_LINE];
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'TAKEN_TIME') IS NOT NULL
ALTER TABLE [reports].[severe_sepsis_staging] DROP COLUMN [TAKEN_TIME];
GO

-- VERIFICATION: expect an EMPTY result (none of these remain).
SELECT v.tbl, v.col FROM (VALUES
    ('dbo.adt_events', 'adt_DEPARTMENT_ID'),
    ('dbo.adt_events', 'ADT_DEPARTMENT_NAME'),
    ('dbo.adt_events', 'ED2ICUTime'),
    ('dbo.adt_events', 'IN_DTTM'),
    ('dbo.adt_events', 'OUT_DTTM'),
    ('dbo.calendar_dates', 'ABXName'),
    ('dbo.calendar_dates', 'ABXTime'),
    ('dbo.calendar_dates', 'ABXVolume'),
    ('dbo.calendar_dates', 'BloodCultureOrderTime'),
    ('dbo.calendar_dates', 'BloodCultureProcedureOrdered'),
    ('dbo.calendar_dates', 'BloodCultureResult'),
    ('dbo.calendar_dates', 'Bolus'),
    ('dbo.calendar_dates', 'BolusTime'),
    ('dbo.calendar_dates', 'BolusVolume'),
    ('dbo.calendar_dates', 'BPPercentile'),
    ('dbo.calendar_dates', 'CSFOrdered'),
    ('dbo.calendar_dates', 'CSFOrderTime'),
    ('dbo.calendar_dates', 'CSFValue'),
    ('dbo.calendar_dates', 'CVVHYN'),
    ('dbo.calendar_dates', 'DobutamineYN'),
    ('dbo.calendar_dates', 'DopamineYN'),
    ('dbo.calendar_dates', 'ECMOYN'),
    ('dbo.calendar_dates', 'EDLosHours'),
    ('dbo.calendar_dates', 'EncounterWeight'),
    ('dbo.calendar_dates', 'ENCOVERALLORDER'),
    ('dbo.calendar_dates', 'EpinephrineYN'),
    ('dbo.calendar_dates', 'FirstPositiveScoreInED'),
    ('dbo.calendar_dates', 'FirstPositiveScoreTimeInED'),
    ('dbo.calendar_dates', 'HypotensionTime'),
    ('dbo.calendar_dates', 'HypotensionValue'),
    ('dbo.calendar_dates', 'IntubationTime'),
    ('dbo.calendar_dates', 'IPSOSevereSepsisYN'),
    ('dbo.calendar_dates', 'LacticAcidOrderTime'),
    ('dbo.calendar_dates', 'LacticAcidResult'),
    ('dbo.calendar_dates', 'MilrinoneYN'),
    ('dbo.calendar_dates', 'NorepinephrineYN'),
    ('dbo.calendar_dates', 'OrderSetID'),
    ('dbo.calendar_dates', 'OrderSetTime'),
    ('dbo.calendar_dates', 'OXYN'),
    ('dbo.calendar_dates', 'PATENCENCID'),
    ('dbo.calendar_dates', 'PIVPlacementTime'),
    ('dbo.calendar_dates', 'PositiveODScore'),
    ('dbo.calendar_dates', 'PressorYN'),
    ('dbo.calendar_dates', 'ProcalcitoninOrderTime'),
    ('dbo.calendar_dates', 'ProcalcitoninResult'),
    ('dbo.calendar_dates', 'RefreshDate'),
    ('dbo.calendar_dates', 'SepsisDate'),
    ('dbo.config_grouper_categories', 'BASE_GROUPER_ID'),
    ('dbo.config_grouper_categories', 'CODE'),
    ('dbo.config_grouper_categories', 'COMPILED_CONTEXT'),
    ('dbo.config_grouper_categories', 'GROUPER_LIST'),
    ('dbo.config_grouper_categories', 'GROUPER_RECORDS_NUMERIC_ID'),
    ('dbo.ed_event_templates', 'ABX_ADMIN_TIME'),
    ('dbo.ed_event_templates', 'ABX_LINE'),
    ('dbo.ed_event_templates', 'ABX_ORDER_TIME'),
    ('dbo.ed_event_templates', 'ADT_ARRIVAL_TIME'),
    ('dbo.ed_event_templates', 'AGE_MONTHS'),
    ('dbo.ed_event_templates', 'AGE_YEARS'),
    ('dbo.ed_event_templates', 'AntibioticAdministeredTime_V60'),
    ('dbo.ed_event_templates', 'AntibioticOrderedTime_V59'),
    ('dbo.ed_event_templates', 'BLOOD_CULTURE_ORDER_TIME'),
    ('dbo.ed_event_templates', 'BloodCultureOrderedTime_V61'),
    ('dbo.ed_event_templates', 'DATE_STAMP'),
    ('dbo.ed_event_templates', 'ED_DEPARTURE_TIME'),
    ('dbo.ed_event_templates', 'ENCOUNTER_ID'),
    ('dbo.ed_event_templates', 'FIRST_ABX_ADMIN_TIME'),
    ('dbo.ed_event_templates', 'FLO_MEAS_ID'),
    ('dbo.ed_event_templates', 'FSD_ID'),
    ('dbo.ed_event_templates', 'INPATIENT_DATA_ID'),
    ('dbo.ed_event_templates', 'RECORDED_TIME'),
    ('dbo.ed_event_templates', 'REVIEWED'),
    ('dbo.ed_event_templates', 'Sepsis_Episode_ID_V01'),
    ('dbo.encounter_diagnoses', 'HOSPITAL_ACCOUNT_ID'),
    ('dbo.encounter_visit_reasons', 'AllEncReasons'),
    ('dbo.encounter_visit_reasons', 'ALRT_SP_OVR_RSN_CODE'),
    ('dbo.encounter_visit_reasons', 'NAME'),
    ('dbo.flowsheet_measurements', 'ABX_ADMIN_TIME'),
    ('dbo.flowsheet_measurements', 'ABX_LINE'),
    ('dbo.flowsheet_measurements', 'ABX_ORDER_TIME'),
    ('dbo.flowsheet_measurements', 'ADT_ARRIVAL_TIME'),
    ('dbo.flowsheet_measurements', 'AGE_MONTHS'),
    ('dbo.flowsheet_measurements', 'AGE_YEARS'),
    ('dbo.flowsheet_measurements', 'AntibioticAdministeredTime_V60'),
    ('dbo.flowsheet_measurements', 'AntibioticOrderedTime_V59'),
    ('dbo.flowsheet_measurements', 'BLOOD_CULTURE_ORDER_TIME'),
    ('dbo.flowsheet_measurements', 'BloodCultureOrderedTime_V61'),
    ('dbo.flowsheet_measurements', 'BP'),
    ('dbo.flowsheet_measurements', 'DATE_STAMP'),
    ('dbo.flowsheet_measurements', 'ED_DEPARTURE_TIME'),
    ('dbo.flowsheet_measurements', 'ENC_ID'),
    ('dbo.flowsheet_measurements', 'ENCOUNTER_ID'),
    ('dbo.flowsheet_measurements', 'FIRST_ABX_ADMIN_TIME'),
    ('dbo.flowsheet_measurements', 'Hypotension'),
    ('dbo.flowsheet_measurements', 'INPATIENT_DATA_ID'),
    ('dbo.flowsheet_measurements', 'RECORD_ID'),
    ('dbo.flowsheet_measurements', 'RECORD_NAME'),
    ('dbo.flowsheet_measurements', 'REVIEWED'),
    ('dbo.flowsheet_measurements', 'Score'),
    ('dbo.flowsheet_measurements', 'Sepsis'),
    ('dbo.flowsheet_measurements', 'Sepsis_Episode_ID_V01'),
    ('dbo.flowsheet_measurements', 'Unique'),
    ('dbo.flowsheet_records', 'ABX_ADMIN_TIME'),
    ('dbo.flowsheet_records', 'ADT_ARRIVAL_TIME'),
    ('dbo.flowsheet_records', 'ADT_DEPARTMENT_ID'),
    ('dbo.flowsheet_records', 'ADT_DEPARTMENT_NAME'),
    ('dbo.flowsheet_records', 'AGE_MONTHS'),
    ('dbo.flowsheet_records', 'AGE_YEARS'),
    ('dbo.flowsheet_records', 'ED_DEPARTURE_TIME'),
    ('dbo.flowsheet_records', 'ENCOUNTER_ID'),
    ('dbo.flowsheet_records', 'IN_DTTM'),
    ('dbo.flowsheet_records', 'OUT_DTTM'),
    ('dbo.grouper_compiled_list', 'CODE'),
    ('dbo.grouper_compiled_list', 'GROUPER_ID'),
    ('dbo.grouper_compiled_list', 'GROUPER_LIST'),
    ('dbo.grouper_compiled_list', 'LIST_CAT_VALUE_CODE'),
    ('dbo.grouper_groups', 'BASE_GROUPER_ID'),
    ('dbo.grouper_groups', 'CODE'),
    ('dbo.grouper_groups', 'COMPILED_CONTEXT'),
    ('dbo.grouper_groups', 'GROUPER_RECORDS_NUMERIC_ID'),
    ('dbo.grouper_groups', 'LIST_CAT_VALUE_CODE'),
    ('dbo.grouper_med_records', 'COMPILED_CONTEXT'),
    ('dbo.grouper_terminology', 'BASE_GROUPER_ID'),
    ('dbo.grouper_terminology', 'COMPILED_CONTEXT'),
    ('dbo.grouper_terminology', 'GROUPER_LIST'),
    ('dbo.grouper_terminology', 'GROUPER_RECORDS_NUMERIC_ID'),
    ('dbo.grouper_terminology', 'LIST_CAT_VALUE_CODE'),
    ('dbo.hospital_acct_diagnoses', 'ENCOUNTER_ID'),
    ('dbo.lab_components', 'LRR_ID'),
    ('dbo.lab_order_results', 'ORDER_MED_ID'),
    ('dbo.locations', 'ADTDepartmentName'),
    ('dbo.locations', 'DepartmentRollup'),
    ('dbo.locations', 'ENCORDER'),
    ('dbo.locations', 'InDepartmentTime'),
    ('dbo.locations', 'OutDepartmentTime'),
    ('dbo.locations', 'PATENCENCID'),
    ('dbo.locations', 'UniqueRow'),
    ('dbo.medication_orders', 'ORDER_DTTM'),
    ('dbo.medication_orders', 'ORDER_ID'),
    ('dbo.medication_orders', 'PRL_ORDERSET_ID'),
    ('dbo.medications', 'ERX_ID'),
    ('dbo.order_tracking_metrics', 'HV_DISCR_FREQ_ID'),
    ('dbo.order_tracking_metrics', 'MED_ROUTE_CODE'),
    ('dbo.order_tracking_metrics', 'MEDICATION_ID'),
    ('dbo.order_tracking_metrics', 'ORDER_INST'),
    ('dbo.order_tracking_metrics', 'ORDER_MED_ID'),
    ('dbo.patient_encounters', 'ADTArrivalTime'),
    ('dbo.patient_encounters', 'ADTDepartmentID'),
    ('dbo.patient_encounters', 'ADTDepartmentName'),
    ('dbo.patient_encounters', 'AgeMonths'),
    ('dbo.patient_encounters', 'AgeYears'),
    ('dbo.patient_encounters', 'AllEncDx'),
    ('dbo.patient_encounters', 'AllEncReasons'),
    ('dbo.patient_encounters', 'BirthDate'),
    ('dbo.patient_encounters', 'Disposition'),
    ('dbo.patient_encounters', 'EDDepartureTime'),
    ('dbo.patient_encounters', 'EthnicGroup'),
    ('dbo.patient_encounters', 'HospAdmsnTime'),
    ('dbo.patient_encounters', 'HospDischTime'),
    ('dbo.patient_encounters', 'InDepartmentTime'),
    ('dbo.patient_encounters', 'InpAdmDate'),
    ('dbo.patient_encounters', 'InpatientDataID'),
    ('dbo.patient_encounters', 'Location'),
    ('dbo.patient_encounters', 'LosHours'),
    ('dbo.patient_encounters', 'OutDepartmentTime'),
    ('dbo.patient_encounters', 'PATENCENCID'),
    ('dbo.patient_encounters', 'PatientID'),
    ('dbo.patient_encounters', 'PATIENTMRN'),
    ('dbo.patient_encounters', 'PatientName'),
    ('dbo.patient_encounters', 'Race'),
    ('dbo.patient_encounters', 'UniqueRow'),
    ('dbo.ref_alert_override_reasons', 'AllEncReasons'),
    ('dbo.ref_alert_override_reasons', 'ENC_REASON_ID'),
    ('dbo.ref_alert_override_reasons', 'ENCOUNTER_ID'),
    ('dbo.ref_alert_override_reasons', 'LINE'),
    ('dbo.treatment_teams', 'MEAS_VALUE'),
    ('reports.config_value_set', 'AGENT'),
    ('reports.config_value_set', 'AGENT_GROUP'),
    ('reports.config_value_set', 'DOT_MONITORING'),
    ('reports.severe_sepsis_staging', 'GROUPER_ID'),
    ('reports.severe_sepsis_staging', 'ORDER_DTTM'),
    ('reports.severe_sepsis_staging', 'PRESSOR_START_TIME'),
    ('reports.severe_sepsis_staging', 'ScreenTime'),
    ('reports.severe_sepsis_staging', 'Sepsis'),
    ('reports.severe_sepsis_staging', 'SS_LINE'),
    ('reports.severe_sepsis_staging', 'TAKEN_TIME')
) v(tbl, col) WHERE COL_LENGTH(v.tbl, v.col) IS NOT NULL;
GO
