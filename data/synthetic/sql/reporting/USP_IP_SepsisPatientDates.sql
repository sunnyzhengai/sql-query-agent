



/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_MAIN_IP_SEPSIS]

Date			Who					Description 

----------------------------------------------------------------------------------- 

12/01/2025		Developer C		Separated base query into multiple tables, one record for date and PATIENTS was admitted to a unit

===================================================================================== 

USAGE: 

exec [reportingDB].[reporting].[USP_IP_SepsisPatientDates]

************************************************************************************/ 

CREATE PROCEDURE [reporting].[USP_IP_SepsisPatientDates]

--DECLARE

@StartDate VARCHAR(20) = NULL,

@EndDate VARCHAR(20) = NULL



AS

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table reporting.[IP_SepsisPatientDates];



DECLARE @dStartDate DATE

DECLARE @dEndDate DATE

DECLARE @dTestRun BIT

	

IF @StartDate IS NULL OR @StartDate = ''

	SET @dStartDate = [EMRDB].[dbo].[fn_parse_date]('MB-12') /*('2018-01-01')*/

ELSE

	SET @dStartDate = [EMRDB].[dbo].[fn_parse_date](@StartDate)

	

IF @EndDate IS NULL OR @EndDate = ''

	SET @dEndDate = [EMRDB].[dbo].[fn_parse_date]('ME-1') /*DEFAULTING TO PREVIOUS MONTH*/

ELSE

	SET @dEndDate = [EMRDB].[dbo].[fn_parse_date](@EndDate)



IF OBJECT_ID(N'tempdb..#MainAdmDetails') IS NOT NULL DROP TABLE #MainAdmDetails;

/*list of admitted patients*/

SELECT DISTINCT

	[PatEncCSNID] PAT_ENC_CSN_ID

	, [PatID] PAT_ID

	, [PatMRNID] PAT_MRN_ID

	, [PatName] PAT_NAME

	, [EthnicGroup] [Ethnic Group]

	, [Race] [Race]

	, [InpatientDataID] INPATIENT_DATA_ID

	, [ADTArrivalTime] ADT_ARRIVAL_TIME

	, [HospAdmsnTime] HOSP_ADMSN_TIME

	, [HospDischTime] HOSP_DISCH_TIME

	, [InpAdmDate] INP_ADM_DATE

	, [EDDepartureTime] ED_DEPARTURE_TIME

	, [Disposition] [Disposition]

	, [Location] [Location]

	, [AgeMonths] AGE_MONTHS

	, [AgeYears] AGE_YEARS

	, [LosHours] LOS_HRS

	, [BirthDate] BIRTH_DATE

INTO #MainAdmDetails

FROM [reportingDB].[reporting].[IP_SepsisEncounters]

CREATE INDEX IDX_Main ON #MainAdmDetails (PAT_ENC_CSN_ID) 

CREATE INDEX IDX_MaininpDt ON #MainAdmDetails (INPATIENT_DATA_ID) 

/*SELECT * FROM #MainAdmDetails*/



/***********************************************************************

Get Encounters and a record for every shift a PATIENTS was in a department for Compliance reporting

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_PopTemp') IS NOT NULL DROP TABLE #Base_PopTemp;

SELECT DISTINCT

	main.[PatEncCSNID] PAT_ENC_CSN_ID

	, main.[PatID] PAT_ID

	, main.[InpatientDataID] INPATIENT_DATA_ID

	, main.InpatientDataID INP_ADM_DATE

	, main.[ADTDepartmentID] ADT_DEPARTMENT_ID

	, main.[ADTDepartmentName] ADT_DEPARTMENT_NAME

	, cvs.CODE_DESC AS DEPARTMENT_ROLLUP

	, main.[InDepartmentTime] IN_DTTM

	, main.[OutDepartmentTime] OUT_DTTM

	, main.BirthDate BIRTH_DATE

	, main.[ADTArrivalTime] ADT_ARRIVAL_TIME

	, main.[EDDepartureTime] ED_DEPARTURE_TIME

	, CONVERT(DATE, main.[InDepartmentTime]) InDeptDate

	, CONVERT(DATE, main.[OutDepartmentTime]) OutDeptDate

	, main.CSNOrder [CSN Order]

	, main.UniqueRow

INTO #Base_PopTemp

FROM [reportingDB].[reporting].[IP_SepsisEncountersWLocations] main

INNER JOIN [reportingDB].[reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = main.[ADTDepartmentID]

			AND cvs.VALUE_SET_ID = 3031 /*DEPARTMENT ROLL UP*/

CREATE INDEX IDX_Base_PopTemp ON #Base_PopTemp (PAT_ENC_CSN_ID) 

--/*SELECT * FROM #Base_PopTemp*/



/***********************************************************************

Get Every day a PATIENTS should have had a Sepsis Screening

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

; WITH dateCTE AS

(

	SELECT PAT_ENC_CSN_ID

		, InDeptDate [Expansion Date]

		, OutDeptDate [Expansion End Date]

		, IN_DTTM [InDepartmentTime]

		, OUT_DTTM [OutDepartmentTime]

		, ADT_DEPARTMENT_ID

		, ADT_DEPARTMENT_NAME

		, PAT_ID

		, DEPARTMENT_ROLLUP

		, INPATIENT_DATA_ID

		, BIRTH_DATE

		, [CSN Order]

	FROM #Base_PopTemp

	WHERE DEPARTMENT_ROLLUP NOT IN ('ER', 'P-ER')

	UNION ALL 

	SELECT PAT_ENC_CSN_ID

		, DATEADD(d, 1, d.[Expansion Date]) [Expansion Date]

		, d.[Expansion End Date]

		, d.[InDepartmentTime]

		, d.[OutDepartmentTime]

		, d.ADT_DEPARTMENT_ID

		, d.ADT_DEPARTMENT_NAME

		, d.PAT_ID

		, d.DEPARTMENT_ROLLUP

		, d.INPATIENT_DATA_ID

		, BIRTH_DATE

		, [CSN Order]

	FROM dateCTE d 

	WHERE DATEADD(d, 1, d.[Expansion Date]) <= d.[Expansion End Date]

)



/***********************************************************************

Finalize base table, one record for each shift a PATIENTS was in a unit

--***********************************************************************/

SELECT * 

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID, InDepartmentTime ORDER BY [Service Date]) [Unit Order]

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY InDepartmentTime, [Service Date]) AS [CSN Overall Order]

INTO #Base_Pop

FROM (

	SELECT PAT_ENC_CSN_ID

		, [Expansion Date] [Service Date]

		, [InDepartmentTime]

		, [OutDepartmentTime]

		, ADT_DEPARTMENT_ID

		, ADT_DEPARTMENT_NAME

		, PAT_ID

		, DEPARTMENT_ROLLUP

		, INPATIENT_DATA_ID

		, [CSN Order]

		, DATEDIFF(MM, BIRTH_DATE, [Expansion Date]) [AGE_MONTHS]

		, FLOOR(DATEDIFF(DD, BIRTH_DATE, [Expansion Date])/365.25) AS AGE_YEARS

	FROM dateCTE 

	WHERE [Expansion Date] BETWEEN @dStartDate and @dEndDate

) a

OPTION (MAXRECURSION 8000);  /*default is 100*/

CREATE INDEX IDX_Base_Pop ON #Base_Pop (PAT_ENC_CSN_ID) 

--/*SELECT * FROM #Base_Pop */



/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisPatientDates]

	(

		[PatID],

		[PatEncCSNID],

		[SepsisPatientDate],

		[ADTDepartmentID],

		[ADTDepartmentName],

		[DepartmentRollup],

		[InDepartmentTime],

		[OutDepartmentTime],

		[InpatientDataID],

		[AgeOnDateMonths],

		[AgeOnDateYears],

		[CSNOrder], 

		[UnitOrder], 

		[CSNOverallOrder],

		[UniqueRow],

		[RefreshDate])

SELECT main.PAT_ID

	, main.PAT_ENC_CSN_ID [CSN]

	, main.[Service Date] [Sepsis PATIENTS Date]

	, main.ADT_DEPARTMENT_ID [Department ID]

	, main.ADT_DEPARTMENT_NAME [Department]

	, main.DEPARTMENT_ROLLUP [Department Rollup]

	, main.InDepartmentTime [In Department Time]

	, main.OutDepartmentTime [Out Department Time]

	, main.INPATIENT_DATA_ID [Inpatient Data ID]

	, main.AGE_MONTHS [Age on Date (M)]

	, main.AGE_YEARS [Age on Date (Y)]

	, main.[CSN Order]

	, main.[Unit Order]

	, main.[CSN Overall Order]

	, CAST(main.PAT_ENC_CSN_ID AS varchar(20)) + '-' + CAST(main.[CSN Order] AS VARCHAR(95)) [Unique Row]

	, GETDATE()

FROM #Base_Pop main  

ORDER BY main.PAT_ENC_CSN_ID, main.[CSN Overall Order]

END 

