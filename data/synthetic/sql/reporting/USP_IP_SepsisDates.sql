

/************************************************************************************

Author: Developer C 

Create date: Nov 2025

Description: HS FY Dates for the IP Sepsis Compliance Report

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Date			Who					Description

-------------------------------------------------------------------------------------

11/02/2025	Developer C		Developed

=====================================================================================

USAGE:

exec [reporting].[USP_IP_SepsisDates]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisDates]

AS

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;



DECLARE @dStartDate DATE

DECLARE @dEndDate DATE

	

SET @dStartDate = (SELECT MIN(SepsisPatientDate) FROM reporting.IP_SepsisPatientDates)

SET @dEndDate = ( SELECT MAX(SepsisPatientDate) FROM reporting.IP_SepsisPatientDates)



SELECT fyDate.CALENDAR_DT [FY Date] 

	, fyDate.HS_FY [FY]

	, fyDate.HS_FY_MONTH_NUMBER [FY Month #]

	, fyDate.MONTH_NAME [FY Month]

	, fyDate.HS_FY [FY Year]

	, LEFT(fyDate.MONTH_NAME, 3 ) AS [FY Month Short Name]

	, fyDate.DAY_OF_MONTH [FY Day of Month]



FROM [reports].[FY_DATE_DIMENSION] fyDate 

WHERE fyDate.CALENDAR_DT BETWEEN @dStartDate AND @dEndDate

END

