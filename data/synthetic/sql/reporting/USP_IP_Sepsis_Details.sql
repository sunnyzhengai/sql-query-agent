



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

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_Sepsis_Details]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_Details]



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

	, [EncounterDiagnoses] [Encounter Diagnoses]

	, [LastHypotensionTime] [LAST Hypotension Time]

	, [LastHypotensionValue] [LAST Hypotension Value]

	, [LastHypotensionTakenInDeptYN] [LAST Hypotension Taken in Dept Y/N]

	, [FirstHypotensionTime] [FIRST Hypotension Time]

	, [FirstHypotensionValue] [FIRST Hypotension Value]

	, [FirstHypotensionTakenInDeptYN] [FIRST Hypotension Taken in Dept Y/N]

	, [EncounterWeight] [Weight]

	, [FirstPositiveScoreInED] [First Positive Score in ED]

	, [FirstPositiveScoreTimeInED] [First Positive Score Time in ED]

	, [EDLosHours] [ED LOS (Hrs)]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [In Department Time]

	, [OutDepartmentTime] [Out Department Time]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]

	, [ShiftComplianceFlag] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [SepsisPatientHuddleorAlertWithMDPNP] [Sepsis PATIENTS Huddle or CLINICAL_ALERTS With MD/PNP]

	, [HuddleDate] [Huddle Date]

	, [HuddleTime] [Huddle Time]

	, [PatientAssessedByMDPNP] [PATIENTS Assessed by MD/PNP]

	, [PhysicianName] [Physician Name]

	, [AddOrdersReceivedPlacedByMDPNP] [Additional Orders Received/Placed by MD/PNP]

	, [LastABXTime] [LAST ABX Time]

	, [LastABXName] [LAST ABX Name]

	, [LastABXToODScoreVolume] [LAST ABX Volume]

	, [LastABXToODScoreTime] [LAST ABX to OD Score Time]

	, [LastABXGivenInDeptYN] [LAST ABX Given in Dept Y/N]

	, [FirstABXTime] [FIRST ABX Time]

	, [FirstABXName] [FIRST ABX Name]

	, [FirstABXVolume] [FIRST ABX Volume]

	, [ODScoreToFirstABXTime] [OD Score to FIRST ABX Time]

	, [FirstABXGivenInDeptYN] [FIRST ABX Given in Dept Y/N]

	, [ABXYN] [ABX Y/N]

	, [LastBolusTime] [LAST Bolus Time]

	, [LastBolus] [LAST Bolus]

	, [LastBolusVolume][LAST Bolus Volume]

	, [LastBolusToScreenTime] [LAST Bolus to Screen Time]

	, [LastBolusGivenInDeptYN] [LAST Bolus Given in Dept Y/N]

	, [FirstBolusTime] [FIRST Bolus Time]

	, [FirstBolus] [FIRST Bolus]

	, [FirstBolusVolume] [FIRST Bolus Volume]

	, [ScreenTimeToFirstBolus] [Screen Time to FIRST Bolus]

	, [FirstBolusGivenInDeptYN] [FIRST Bolus Given in Dept Y/N]

	, [BolusYN] [Bolus Y/N]

	, [LastLacticAcidOrderTime] [LAST LacticAcid Order Time]

	, [LastLacticAcidResult] [LAST LacticAcid Result]

	, [LastLacticAcidInDeptYN] [LAST LacticAcid in Dept Y/N]

	, [FirstLacticAcidOrderTime] [FIRST LacticAcid Order Time]

	, [FirstLacticAcidResult] [FIRST LacticAcid Result]

	, [FirstLacticActidInDeptYN][FIRST LacticAcid in Dept Y/N]

	, [LacticAcidYN] [LacticAcid Y/N]

	, [LastOrderSetTime] [LAST OrderSet Time]

	, [LastOrderSetID] [LAST OrderSet ID]

	, [LastOrderSetInDeptYN] [LAST OrderSet in Dept Y/N]

	, [FirstOrderSetTime] [FIRST OrderSet Time]

	, [FirstOrderSetID] [FIRST OrderSet ID]

	, [FirstOrderSetInDeptYN] [FIRST OrderSet in Dept Y/N]

	, [LastCVLTime] [LAST CVL Time]

	, [LastCVLInDeptYN] [LAST CVL in Dept Y/N]

	, [FirstCVLTime] [FIRST CVL Time]

	, [FirstCVLInDeptYN] [FIRST CVL in Dept Y/N]

	, [CVLYN] [CVL Y/N]

	, [LastSVO2Time] [LAST SVO2 Time]

	, [LastSVO2InDeptYN] [LAST SVO2 in Dept Y/N]

	, [FirstSVO2Time] [FIRST SVO2 Time]

	, [FirstSVO2InDeptYN] [FIRST SVO2 in Dept Y/N]

	, [SVO2YN] [SVO2 Y/N]

	, [LastProcalcitoninOrderTime] [LAST Procalcitonin Order Time]

	, [LastProcalcitoninResult] [LAST Procalcitonin Result]

	, [LastProcalcitoninInDeptYN] [LAST Procalcitonin in Dept Y/N]

	, [FirstProcalcitoninOrderTime] [FIRST Procalcitonin Order Time]

	, [FirstProcalcitoninResult] [FIRST Procalcitonin Result]

	, [FirstProcalcitoninInDeptYN] [FIRST Procalcitonin in Dept Y/N]

	, [ProcalcitoninYN] [Procalcitonin Y/N]

	, [LastBloodCultureOrderTime] [LAST Blood Culture Order Time]

	, [LastBloodCultureProcedureOrdered] [LAST Blood Culture Procedure Ordered]

	, [LastBloodCultureResult] [LAST Blood Culture Result]

	, [LastBloodCultureInDeptYN] [LAST Blood Culture in Dept Y/N]

	, [FirstBloodCultureOrderTime] [FIRST Blood Culture Order Time]

	, [FirstBloodCultureProcedureOrdered] [FIRST Blood Culture Procedure Ordered]

	, [FirstBloodCultureResult] [FIRST Blood Culture Result]

	, [FirstBloodCultureInDeptYN] [FIRST Blood Culture in Dept Y/N]

	, [BloodCultureYN] [Blood Culture Y/N]

	, [LastCSFOrderTime] [LAST CSF Order Time]

	, [LastCSFOrdered] [LAST CSF Ordered]

	, [LastCSFInDeptYN] [LAST CSF in Dept Y/N]

	, [FirstCSFOrderTime] [FIRST CSF Order Time]

	, [FirstCSFOrdered] [FIRST CSF Ordered]

	, [FirstCSFInDeptYN] [FIRST CSF in Dept Y/N]

	, [CSFYN] [CSF Y/N]

	, [LastPIVBeforeScreen] [LAST PIV Before Screen]

	, [LastPIVInDeptYN] [LAST PIV in Dept Y/N]

	, [FirstPIVAfterScreen] [FIRST PIV After Screen]

	, [FirstPIVInDeptYN] [FIRST PIV in Dept Y/N]

	, [PIVYN] [PIV Y/N]

	, [LastIntubationTime] [LAST Intubation Time]

	, [LastETTInDeptYN] [LAST ETT in Dept Y/N]

	, [FirstIntubationTime] [FIRST Intubation Time]

	, [FirstETTInDeptYN] [FIRST ETT in Dept Y/N]

	, [ETTYN] [ETT Y/N]

	, [DobutamineYN] [Dobutamine Y/N]

	, [DopamineYN] [Dopamine Y/N]

	, [EpinephrineYN] [Epinephrine Y/N]

	, [MilrinoneYN] [Milrinone Y/N]

	, [NorepinephrineYN] [Norepinephrine Y/N]

	, [PressorYN] [Pressor Y/N]

	, [DvtprophylaxisYN] [Dvtprophylaxis Y/N]

	, [CVVHYN] [CVVH Y/N]

	, [OXYN] [OX Y/N]

	, [ECMOYN] [ECMO Y/N]

	, [IPSOSevereSepsisYN] [IPSO Severe Sepsis Y/N]

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]

	, [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYMonthShortName] [FY Month Short Name]

	, [FYDate] [FY Date]

	, [ShiftRNs] [Shift RNs]

	, [ShiftCNs] [Shift CNs]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [FifteenthOrEOM] [15th or EOM]

	, [PositiveODScore] [Positive OD Score]

	, [ENCORDER] [ENC_ID Order]

	, [UnitOrder] [Unit Order]

	, [ENCOVERALLORDER] [ENC_ID Overall Order]

	, [AMDenom] [AM Denom]

	, [PMDenom] [PM Denom]

	, [Denominator]

	, [InRecord] [In Record]

	, [OutRecord] [Out Record]

	, [RefreshDate] [Refresh Date]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

  FROM [reportingDB].[reporting].[IP_SEPSIS] 

