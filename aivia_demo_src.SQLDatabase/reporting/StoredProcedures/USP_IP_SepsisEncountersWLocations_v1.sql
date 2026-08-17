
-- ==== reporting/USP_IP_SepsisEncountersWLocations_v1.sql ====
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

exec [reporting].[USP_IP_SepsisEncountersWLocations_v1]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisEncountersWLocations_v1]

AS

BEGIN

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT DISTINCT

	enc.[PatientName] [PATIENTS]

	, enc.[PATIENTMRN] [MRN]

	, enc.[EthnicGroup] [Ethnic Group]

	, enc.[Race]

	, enc.[Location]

	, enc.[PATENCENCID] [ENC_ID]

	, enc.[AgeMonths] [Age (M)]

	, enc.[AgeYears] [Age (Y)]

	, enc.[InpAdmDate] [Admit Time]

	, enc.[HospDischTime] [Disch Time]

	, enc.[AllEncDx] [Encounter Diagnosis]

	, loc.[ADTDepartmentName] [Department]

	, loc.[DepartmentRollup] [Department Rollup]

	, loc.[InDepartmentTime] [In Department Time]

	, loc.[OutDepartmentTime][Out Department Time]

	, loc.[ENCORDER] [ENC_ID Order]

	, loc.[UniqueRow] [Unique Row]

	FROM [reporting].[IP_SepsisEncounters] enc

	INNER JOIN [reporting].[IP_SepsisEncountersWLocations] loc ON loc.PATENCENCID = enc.PATENCENCID

  ORDER BY ENC_ID, ENCORDER

END

GO

