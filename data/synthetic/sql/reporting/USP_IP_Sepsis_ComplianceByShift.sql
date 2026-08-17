



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

exec [reporting].[USP_IP_Sepsis_ComplianceByShift]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_ComplianceByShift]



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

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [In Department Time]

	, [OutDepartmentTime][Out Department Time]

	, [ShiftDate] [Shift Date]

	, [ShiftStart] [Shift Start]

	, [ShiftEnd] [Shift End]

	, [ShiftAMPM] [Shift AM/PM]

	, [ScoreTime] [Shift Score Time]

	, [ODScore] [Shift Score]

	  

	, [FY] [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYDate] [FY Date]

	, [ShiftRNs] [Shift RNs]

	, [ShiftCNs] [Shift CNs]

	, [ShiftCompliance] [Shift Numerator]

	  

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN [ShiftComplianceFlag] ELSE NULL END [Shift 1 Compliance Y/N]

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN [ShiftCompliance] ELSE NULL END [Shift 1 Compliance]

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN [ShiftColor] ELSE NULL END [Shift 1 Color]

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN

		CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END

	ELSE NULL 

	END [Shift 1 Non-Compliance]



	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN [ShiftComplianceFlag] ELSE NULL END [Shift 2 Compliance Y/N]

	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN [ShiftCompliance] ELSE NULL END [Shift 2 Compliance]

	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN [ShiftColor] ELSE NULL END [Shift 2 Color]

	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN

		CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END

	ELSE NULL 

	END [Shift 2 Non-Compliance]



	, [ShiftCompliance] [Numerator]

	, CASE WHEN [ShiftAMPM] like 'AM%' THEN [AMDenom] ELSE [PMDenom] END [Denominator]

	, [ShiftComplianceFlag] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END [Shift Non-Compliance]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

	FROM [reporting].[IP_SEPSIS]



  ORDER BY ENC_ID, ENCOVERALLORDER

