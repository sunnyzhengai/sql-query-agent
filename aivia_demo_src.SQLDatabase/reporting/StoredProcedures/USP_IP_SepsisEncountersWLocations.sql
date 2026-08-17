
-- ==== reporting/USP_IP_SepsisEncountersWLocations.sql ====
/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

Date			Who					Description 

----------------------------------------------------------------------------------- 

12/01/2025		Developer C		Separated base query into multiple tables, one record for each unit the PATIENTS was admitted

===================================================================================== 

USAGE: 

exec [reporting].[USP_IP_SepsisEncountersWLocations]

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

	SET @dStartDate = [dbo].[fn_parse_date]('MB-12') /*('2018-01-01')*/

ELSE

	SET @dStartDate = [dbo].[fn_parse_date](@StartDate)

	

IF @EndDate IS NULL OR @EndDate = ''

	SET @dEndDate = [dbo].[fn_parse_date]('ME-1') /*DEFAULTING TO PREVIOUS MONTH*/

ELSE

	SET @dEndDate = [dbo].[fn_parse_date](@EndDate)



IF OBJECT_ID(N'tempdb..#MainAdmDetails') IS NOT NULL DROP TABLE #MainAdmDetails;

/*list of admitted patients*/

SELECT DISTINCT

	[PATENCENCID] ENCOUNTER_ID

	, [PatientID] PATIENT_ID

	, [PATIENTMRN] PATIENT_MRN

	, [PatientName] PATIENT_NAME

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

FROM [reporting].[IP_SepsisEncounters]

CREATE INDEX IDX_Main ON #MainAdmDetails (ENCOUNTER_ID) 

/*SELECT * FROM #MainAdmDetails*/



/***********************************************************************

Get Encounters and a record for every shift a PATIENTS was in a department for Compliance reporting

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT 

	adtIn.ENCOUNTER_ID

	, ENCS.PATIENT_ID

	, adtIn.DEPARTMENT_ID AS ADT_DEPARTMENT_ID

	, CASE WHEN adtIn.DEPARTMENT_ID IS NULL THEN '*Department not specified'

			WHEN dep.DEPARTMENT_ID IS NULL THEN '*Unknown department'

			WHEN dep.DEPARTMENT_NAME IS NULL THEN '*Unnamed department'

			ELSE dep.DEPARTMENT_NAME

	END AS ADT_DEPARTMENT_NAME

	, cvs.CODE_DESC AS DEPARTMENT_ROLLUP

	, adtIn.EFFECTIVE_TIME AS IN_DTTM

	, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()) AS OUT_DTTM

	, ENCS.INPATIENT_DATA_ID

	, ENCS.BIRTH_DATE

	, ENCS.ADT_ARRIVAL_TIME

	, ENCS.ED_DEPARTURE_TIME

	, CONVERT(DATE, adtIn.EFFECTIVE_TIME) [InDeptDate]

	, CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE())) [OutDeptDate]

	, ROW_NUMBER() OVER (PARTITION BY ENCS.ENCOUNTER_ID ORDER BY adtIn.EFFECTIVE_TIME, adtOut.EFFECTIVE_TIME ) [ENC_ID Order]

INTO #Base_Pop

FROM #MainAdmDetails ENCS

INNER JOIN [dbo].[ADT_EVENTS] adtIn ON adtIn.ENCOUNTER_ID = ENCS.ENCOUNTER_ID

LEFT OUTER JOIN [dbo].[ADT_EVENTS] adtOut ON adtIn.NEXT_OUT_EVENT_ID = adtOut.EVENT_ID

LEFT OUTER JOIN [dbo].[DEPARTMENTS] dep ON adtIn.DEPARTMENT_ID = dep.DEPARTMENT_ID

INNER JOIN [reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = CONVERT(Varchar(100), adtIn.DEPARTMENT_ID)

			AND cvs.VALUE_SET_ID = 3031 /*DEPARTMENT ROLL UP*/

WHERE adtIn.EVENT_TYPE_CODE IN (1, 3, 99) /*Only look at "in" events (Admission and Transfer In, LOA Return)*/

AND adtIn.EVENT_SUBTYPE_CODE <> 2 /*Exclude deleted/canceled events*/

CREATE INDEX IDX_Base_Pop ON #Base_Pop (ENCOUNTER_ID) 

/*SELECT * FROM ##Base_Pop*/



/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisEncountersWLocations]

	(

		[PatientID], 

		[PATIENTMRN],

		[PATENCENCID],

		[ADTDepartmentID],

		[ADTDepartmentName],

		[DepartmentRollup],

		[InDepartmentTime],

		[OutDepartmentTime],

		[ENCORDER], 

		[InpatientDataID], 

		[ADTArrivalTime], 

		[EDDepartureTime],

		[HospAdmsnTime],

		[BirthDate],

		[UniqueRow],

		[RefreshDate])

SELECT main.PATIENT_ID 

	, main.PATIENT_MRN [MRN]

	, main.ENCOUNTER_ID [ENC_ID]

	, bp.ADT_DEPARTMENT_ID 

	, bp.ADT_DEPARTMENT_NAME [Department]

	, bp.DEPARTMENT_ROLLUP [Department Rollup]

	, bp.IN_DTTM [In Department Time]

	, bp.OUT_DTTM [Out Department Time]

	, bp.[ENC_ID Order]

	, main.INPATIENT_DATA_ID

	, main.ADT_ARRIVAL_TIME

	, main.ED_DEPARTURE_TIME

	, main.HOSP_ADMSN_TIME

	, main.BIRTH_DATE

	, CAST(main.ENCOUNTER_ID AS varchar(20)) + '-' + CAST(bp.[ENC_ID Order] AS VARCHAR(95)) [Unique Row]

	, GETDATE()

FROM #MainAdmDetails main  

INNER JOIN #Base_Pop bp ON bp.ENCOUNTER_ID = main.ENCOUNTER_ID

ORDER BY bp.ENCOUNTER_ID, bp.[ENC_ID Order]

END

GO

