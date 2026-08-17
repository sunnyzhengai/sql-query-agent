



/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reporting].[USP_IP_Sepsis_ComplianceMetrics]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_ComplianceMetrics]



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

	, [InpAdmDate] [IP Admit Time]

	, [HospDischTime] [Discharge Time]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [Department In Time]

	, [OutDepartmentTime] [Department Out Time]

	, [ShiftDate] [Shift Date]

	, [ShiftAMPM] [Shift AM/PM]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]

	, [FY] [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYMonthShortName] [FY Month Abrv]

	, [FYDate] [FY Date]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [Denominator]

	, [ShiftCompliance] [Numerator]

	, [FifteenthOrEOM] [15th or EOM]

	, [ShiftComplianceFlag] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [ShiftColorDisplay] [Shift Color Display]

	, CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END [Shift Non-Compliance]

	, [PositiveODScore] [Positive OD Score]

	, [UniqueRow] [Unique Row]

	,[RefreshDate]

FROM [reporting].[IP_SEPSIS]

ORDER BY ENC_ID, ENCOVERALLORDER

