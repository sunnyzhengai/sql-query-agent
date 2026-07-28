



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

exec [reportingDB].[reporting].[USP_IP_SepsisEncountersDetails]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisEncountersDetails]

AS

BEGIN



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT DISTINCT

	[PatName] [PATIENTS]

	, [PatID] [Pat ID]

	, [PatMRNID] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location]

	, [PatEncCSNID] [CSN]

	, [AgeMonths] [Age at Admission (M)]

	, [AgeYears] [Age at Admission (Y)]

	, [InpAdmDate] [IP Admit Time]

	, [HospAdmsnTime] [Admit Time]

	, [HospDischTime] [Disch Time]

	, [Disposition] [Disposition]

	, [LosHours] [LOS Hours]

	, [BirthDate] [Birth Date]

	, [AllEncDx] [Encounter DX]

	, [RefreshDate] [Refresh Date]

	FROM [reportingDB].[reporting].[IP_SepsisEncounters] enc

  ORDER BY CSN

END 

