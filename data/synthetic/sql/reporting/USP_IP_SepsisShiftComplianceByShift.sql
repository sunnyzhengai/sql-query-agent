

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

exec [reportingDB].[reporting].[USP_IP_SepsisShiftComplianceByShift]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_SepsisShiftComplianceByShift]

AS

BEGIN 



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT 

	[PATENCENCID] [ENC_ID]

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

	  

	, [Shift1ComplianceYN] [Shift 1 Compliance Y/N]

	, [Shift1Compliance] [Shift 1 Compliance]

	, [Shift1Color] [Shift 1 Color]

	, [Shift1NonCompliance] [Shift 1 Non-Compliance]



	, [Shift2ComplianceYN] [Shift 2 Compliance Y/N]

	, [Shift2Compliance] [Shift 2 Compliance]

	, [Shift2Color] [Shift 2 Color]

	, [Shift2NonCompliance] [Shift 2 Non-Compliance]



	, [ShiftCompliance] [Numerator]

	, CASE WHEN [ShiftAMPM] like 'AM%' THEN [AMDenom] ELSE [PMDenom] END [Denominator]

	, [ShiftComplianceFlag] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [ShiftNonCompliance] [Shift Non-Compliance]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

	FROM [reportingDB].reporting.[IP_SepsisShiftCompliance]

  ORDER BY ENC_ID, ENCOVERALLORDER

END 

