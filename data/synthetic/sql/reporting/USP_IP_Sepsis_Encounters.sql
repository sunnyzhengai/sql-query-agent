



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

exec [reportingDB].[reporting].[USP_IP_Sepsis_Encounters]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_Encounters]



AS

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT DISTINCT

	[PatientName] [PATIENTS]

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

	, [ENCORDER] [ENC_ID Order]

	, [UniqueRow] [Unique Row]

	FROM [reportingDB].[reporting].[IP_SEPSIS]

  ORDER BY ENC_ID, ENCORDER

