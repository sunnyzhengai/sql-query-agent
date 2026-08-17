
-- ==== reporting/USP_IP_SepsisPatientDates_v1.sql ====
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

exec [reporting].[USP_IP_SepsisPatientDates_v1]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_SepsisPatientDates_v1]

AS 

BEGIN

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT

	pd.[PATENCENCID] [ENC_ID]

	, pd.SepsisPatientDate [PATIENTS Date]

	, pd.DepartmentRollup [Department Roll-up]

	, pd.ADTDepartmentName	[Department Name]

	, pd.ADTDepartmentID [Department ID]

	, pd.InDepartmentTime [In DTTM]

	, pd.OutDepartmentTime [Out DTTM]

	, pd.InpatientDataID [Inp Data ID]

	, pd.ENCORDER [ENC_ID Order]

	, pd.UnitOrder [Unit Order]

	, pd.[ENCOVERALLORDER] [ENC_ID Overall Order]

	, pd.[RefreshDate] [Refresh Date]

	FROM [reporting].[IP_SepsisPatientDates] pd

END

GO

