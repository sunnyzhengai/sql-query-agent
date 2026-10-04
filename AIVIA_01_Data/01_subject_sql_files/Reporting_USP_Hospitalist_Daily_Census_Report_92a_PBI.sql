USE [CookClarity]
GO

/****** Object:  StoredProcedure [Reporting].[USP_Hospitalist_Daily_Census_Report_92a_PBI]    Script Date: 9/24/2026 7:04:15 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO





/* =============================================================================================
-- Author: Brian Dotts
-- Create date: 03/26/2026
-- Description:
	This report produces Patient Counts from those that are listed on a custom ERS record of 92a. PHM Manual All Patients [131235]


-- Use: EXEC [Reporting].[USP_Hospitalist_Daily_Census_Report_92a_PBI]
-- ==================================================================================
-- version	Date			Who						Description
-- -------	----------		-----------------		---------------------------------
-- 1.0.0	5/31/2026		Brian Dotts				Original
-- 1.0.1	6/17/2026		Brian Dotts				Updated to add WK # into the [Week] column
-- =============================================================================================*/

CREATE                   PROCEDURE [Reporting].[USP_Hospitalist_Daily_Census_Report_92a_PBI]


AS


SET NOCOUNT ON;



WITH ROWNUM AS
(
	SELECT
		[Run ID] = V_REPORT_RUN_FACT.RUN_ID
		,[Report ID] = V_REPORT_RUN_FACT.REPORT_INFO_ID
		,[Report Name] = V_REPORT_RUN_FACT.REPORT_INFO_NAME
		,[Run YYYYMM] = FORMAT(CONVERT(DATE, V_REPORT_RUN_FACT.RUN_DTTM), 'yyyyMM')
		,[Run Date] = CONVERT(DATE, V_REPORT_RUN_FACT.RUN_DTTM)
		,[Run DateTime] = V_REPORT_RUN_FACT.RUN_DTTM
		,[Run Year] = V_REPORT_RUN_FACT.RUN_YEAR
		,[Run Month] = V_REPORT_RUN_FACT.RUN_MONTH
		,[Run Length of Time] = V_REPORT_RUN_FACT.RUN_TIME
		,[Result Count] = V_REPORT_RUN_FACT.RESULT_COUNT
		,[Is From Batch? Y/N] = V_REPORT_RUN_FACT.IS_FROM_BATCH_YN
		,DATE_DIMENSION.WEEKEND_YN
		,[Year Month] = CONCAT(DATE_DIMENSION.MONTH_NAME, ' ', DATE_DIMENSION.YEAR)
		,[Week] = CONCAT('Wk #', ' ', DATE_DIMENSION.WEEK_NUMBER)
		,[ROW] = ROW_NUMBER()OVER(PARTITION BY V_REPORT_RUN_FACT.REPORT_INFO_ID, CONVERT(DATE, V_REPORT_RUN_FACT.RUN_DTTM) ORDER BY V_REPORT_RUN_FACT.RUN_DTTM)

	FROM Clarity.dbo.V_REPORT_RUN_FACT
		LEFT JOIN Clarity.dbo.DATE_DIMENSION
			ON CONVERT(DATE, V_REPORT_RUN_FACT.RUN_DTTM) = DATE_DIMENSION.CALENDAR_DT

	WHERE REPORT_INFO_ID = 2106260
		AND CONVERT(DATE, V_REPORT_RUN_FACT.RUN_DTTM) >= '2026-04-01'
)

SELECT *
FROM ROWNUM
WHERE [ROW] = 1
ORDER BY
	[Run DateTime]
;
GO


