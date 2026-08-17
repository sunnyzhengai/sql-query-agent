



/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023		Developer C		Developed TKT-006

07/24/2025		Developer C		Removed restrictionof ODScore >= 2, Stakeholder A wants them all to display TKT-008

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_Sepsis_ScreeningTool]

************************************************************************************/

CREATE     PROCEDURE [reporting].[USP_IP_Sepsis_ScreeningTool]



AS



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT [PatientName] [PATIENTS]

	, [PATIENTMRN] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location] 

	, [PATENCENCID] [ENC_ID]

	, [AgeMonths] [Age (M)]

	, [AgeYears] [Age (Y)]

	, [InpAdmDate] [Admit Time]

	, [HospDischTime] [Disch Time]

	, [Disposition]

	, [LosHours] [LOS (Hrs)]

	, [ShiftDate] [Shift Date]

	, [ShiftAMPM] [Shift AM/PM]

	, [ShiftStart] [Shift Start]

	, [ShiftEnd] [Shift End]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [In Department Time]

	, [OutDepartmentTime] [Out Department Time]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]



	, [SepsisPatientHuddleorAlertWithMDPNP] [Sepsis PATIENTS Huddle or CLINICAL_ALERTS With MD/PNP]

	, [HuddleDate] [Huddle Date]

	, [HuddleTime] [Huddle Time]

	, [PatientAssessedByMDPNP] [PATIENTS Assessed by MD/PNP]

	, [PhysicianName] [Physician Name]

	, [AddOrdersReceivedPlacedByMDPNP] [Additional Orders Received/Placed by MD/PNP]

	

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]



	, [Predisposition] [Predisposition?]

	, [InfectiousSymptoms] [Infectious Symptoms?]

	, [HematologicDysfunction] [Hematologic Dysfunction]

	, [RenalDysfunction] [Renal Dysfunction]

	, [NeurologicalDysfunction] [Neurological Dysfunction]

	, [RespiratoryDysfunction] [Respiratory Dysfunction]

	, [Pulse]

	, [Resp]

	, [BP]

	, [PerfusionWDL] [Perfusion (WDL)]

	, [RBrachialPulse] [R Brachial Pulse]

	, [LBrachialPulse] [L Brachial Pulse]

	, [RRadialPulse] [R Radial Pulse]

	, [LRadialPulse] [L Radial Pulse]

	, [RPosteriorTibialPulse] [R Posterior Tibial Pulse]

	, [LPosteriorTibialPulse] [L Posterior Tibial Pulse]

	, [RPedalPulse] [R Pedal Pulse]

	, [LPedalPulse] [L Pedal Pulse]

	, [CapillaryRefill] [Capillary Refill]

	, [SkinColor] [Skin Color]

	, [SkinConditionTemp] [Skin Condition/Temp]

	, [ExternalLactateResult] [External Lactate Result]

	, [ExternalCreatinine] [External Creatinine]

	, [ExternalPlatelets] [External Platelets]

	, [Notification]

	, CASE WHEN [ODScore] = 2 THEN 'Y' ELSE 'N' END [OD Score 2]

	, CASE WHEN [ODScore] >= 3 THEN 'Y' ELSE 'N' END [+ OD Score]

	, [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [FifteenthOrEOM] [15th or EOM]

	, [RefreshDate] [Refresh Date]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

  FROM [reportingDB].[reporting].[IP_SEPSIS] 

  --WHERE ODScore >= 2 --7/24/2025 Removing Score restriction

