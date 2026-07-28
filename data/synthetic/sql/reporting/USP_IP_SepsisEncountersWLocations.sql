

/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_MAIN_IP_SEPSIS]

Date			Who					Description 

----------------------------------------------------------------------------------- 

12/01/2025		Developer C		Separated base query into multiple tables, one record for each unit the PATIENTS was admitted

===================================================================================== 

USAGE: 

exec [reportingDB].[reporting].[USP_IP_SepsisEncountersWLocations]

************************************************************************************/ 

CREATE PROCEDURE [reporting].[USP_IP_SepsisEncountersWLocations]

--DECLARE

@StartDate VARCHAR(20) = NULL,

@EndDate VARCHAR(20) = NULL



AS

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table reporting.[IP_SepsisEncountersWLocations];



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

/*SELECT * FROM #MainAdmDetails*/



/***********************************************************************

Get Encounters and a record for every shift a PATIENTS was in a department for Compliance reporting

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT 

	adtIn.PAT_ENC_CSN_ID

	, csns.PAT_ID

	, adtIn.DEPARTMENT_ID AS ADT_DEPARTMENT_ID

	, CASE WHEN adtIn.DEPARTMENT_ID IS NULL THEN '*Department not specified'

			WHEN dep.DEPARTMENT_ID IS NULL THEN '*Unknown department'

			WHEN dep.DEPARTMENT_NAME IS NULL THEN '*Unnamed department'

			ELSE dep.DEPARTMENT_NAME

	END AS ADT_DEPARTMENT_NAME

	, cvs.CODE_DESC AS DEPARTMENT_ROLLUP

	, adtIn.EFFECTIVE_TIME AS IN_DTTM

	, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()) AS OUT_DTTM

	, csns.INPATIENT_DATA_ID

	, csns.BIRTH_DATE

	, csns.ADT_ARRIVAL_TIME

	, csns.ED_DEPARTURE_TIME

	, CONVERT(DATE, adtIn.EFFECTIVE_TIME) [InDeptDate]

	, CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE())) [OutDeptDate]

	, ROW_NUMBER() OVER (PARTITION BY csns.PAT_ENC_CSN_ID ORDER BY adtIn.EFFECTIVE_TIME, adtOut.EFFECTIVE_TIME ) [CSN Order]

INTO #Base_Pop

FROM #MainAdmDetails csns

INNER JOIN [EMRDB].[dbo].[ADT_EVENTS] adtIn ON adtIn.PAT_ENC_CSN_ID = csns.PAT_ENC_CSN_ID

LEFT OUTER JOIN [EMRDB].[dbo].[ADT_EVENTS] adtOut ON adtIn.NEXT_OUT_EVENT_ID = adtOut.EVENT_ID

LEFT OUTER JOIN [EMRDB].[dbo].[DEPARTMENTS] dep ON adtIn.DEPARTMENT_ID = dep.DEPARTMENT_ID

INNER JOIN [reportingDB].[reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = CONVERT(Varchar(100), adtIn.DEPARTMENT_ID)

			AND cvs.VALUE_SET_ID = 3031 /*DEPARTMENT ROLL UP*/

WHERE adtIn.EVENT_TYPE_C IN (1, 3, 99) /*Only look at "in" events (Admission and Transfer In, LOA Return)*/

AND adtIn.EVENT_SUBTYPE_C <> 2 /*Exclude deleted/canceled events*/

CREATE INDEX IDX_Base_Pop ON #Base_Pop (PAT_ENC_CSN_ID) 

/*SELECT * FROM ##Base_Pop*/



/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisEncountersWLocations]

	(

		[PatID], 

		[PatMRNID],

		[PatEncCSNID],

		[ADTDepartmentID],

		[ADTDepartmentName],

		[DepartmentRollup],

		[InDepartmentTime],

		[OutDepartmentTime],

		[CSNOrder], 

		[InpatientDataID], 

		[ADTArrivalTime], 

		[EDDepartureTime],

		[HospAdmsnTime],

		[BirthDate],

		[UniqueRow],

		[RefreshDate])

SELECT main.PAT_ID 

	, main.PAT_MRN_ID [MRN]

	, main.PAT_ENC_CSN_ID [CSN]

	, bp.ADT_DEPARTMENT_ID 

	, bp.ADT_DEPARTMENT_NAME [Department]

	, bp.DEPARTMENT_ROLLUP [Department Rollup]

	, bp.IN_DTTM [In Department Time]

	, bp.OUT_DTTM [Out Department Time]

	, bp.[CSN Order]

	, main.INPATIENT_DATA_ID

	, main.ADT_ARRIVAL_TIME

	, main.ED_DEPARTURE_TIME

	, main.HOSP_ADMSN_TIME

	, main.BIRTH_DATE

	, CAST(main.PAT_ENC_CSN_ID AS varchar(20)) + '-' + CAST(bp.[CSN Order] AS VARCHAR(95)) [Unique Row]

	, GETDATE()

FROM #MainAdmDetails main  

INNER JOIN #Base_Pop bp ON bp.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

ORDER BY bp.PAT_ENC_CSN_ID, bp.[CSN Order]

END

