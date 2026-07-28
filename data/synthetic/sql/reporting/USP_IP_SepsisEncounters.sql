

/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

Date			Who					Description 

----------------------------------------------------------------------------------- 

12/01/2025		Developer C		Separated base query into multiple tables, one record per admission. Not all patients will necessarily have a Sepsis Score

===================================================================================== 

USAGE: 

exec [reportingDB].[reporting].[USP_IP_SepsisEncounters]

************************************************************************************/ 

CREATE PROCEDURE [reporting].[USP_IP_SepsisEncounters]

--DECLARE

@StartDate VARCHAR(20) = NULL,

@EndDate VARCHAR(20) = NULL



AS

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table reporting.[IP_SepsisEncounters];



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

	peh.PAT_ENC_CSN_ID

	, peh.PAT_ID

	, pat.PAT_MRN_ID

	, pat.PAT_NAME

	, zeg.NAME AS [Ethnic Group]

	, zpr.NAME AS [Race]

	, peh.INPATIENT_DATA_ID

	, peh.ADT_ARRIVAL_TIME

	, peh.HOSP_ADMSN_TIME

	, peh.HOSP_DISCH_TIME

	, peh.INP_ADM_DATE

	, peh.ED_DEPARTURE_TIME

	, zdd.NAME AS [Disposition]

	, loc.LOCATION_ABBR [Location]

	, DATEDIFF(MM,pat.BIRTH_DATE,peh.HOSP_ADMSN_TIME) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,pat.BIRTH_DATE,peh.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,peh.HOSP_ADMSN_TIME)) + DATENAME(YEAR, CONVERT(DATE, peh.HOSP_ADMSN_TIME)) AS Admit_Date_stamp

	, DATENAME(month, CONVERT(DATE,peh.HOSP_DISCH_TIME)) + DATENAME(YEAR, CONVERT(DATE, peh.HOSP_DISCH_TIME)) AS Disch_Date_stamp

	, DATEDIFF(HH, peh.HOSP_ADMSN_TIME, peh.HOSP_DISCH_TIME) AS LOS_HRS

	, CONVERT(DATE, pat.BIRTH_DATE) BIRTH_DATE

INTO #MainAdmDetails

FROM [EMRDB].[dbo].[HOSPITAL_TRANSACTIONS] htr

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] sd ON sd.CALENDAR_DT = CONVERT(DATE, htr.SERVICE_DATE)

INNER JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] peh ON htr.PAT_ENC_CSN_ID = peh.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PATIENTS] pat ON pat.PAT_ID = peh.PAT_ID

LEFT OUTER JOIN [EMRDB].[dbo].[REF_DISCHARGE_DISPOSITION] zdd ON zdd.DISCH_DISP_C = peh.DISCH_DISP_C

LEFT OUTER JOIN [EMRDB].[dbo].[REF_ETHNIC_GROUP] zeg ON zeg.ETHNIC_GROUP_C = pat.ETHNIC_GROUP_C

LEFT OUTER JOIN [EMRDB].[dbo].[PATIENT_DEMOGRAPHICS_RACE] race ON race.PAT_ID = pat.PAT_ID AND race.LINE = 1

LEFT OUTER JOIN [EMRDB].[dbo].[REF_PATIENT_RACE] zpr ON zpr.PATIENT_RACE_C = race.PATIENT_RACE_C

LEFT OUTER JOIN [EMRDB].[dbo].[DEPARTMENTS] dep ON dep.DEPARTMENT_ID = peh.DEPARTMENT_ID

LEFT OUTER JOIN [EMRDB].[dbo].[LOCATIONS] loc ON loc.LOC_ID = dep.REV_LOC_ID

WHERE peh.INP_ADM_DATE IS NOT NULL  /*date time of inpatient admission*/

AND sd.CALENDAR_DT BETWEEN @dStartDate AND @dEndDate /*Service data of a charge*/

AND loc.POS_TYPE IS NULL -- Exclude locations set up as Clinic/non-hospital

CREATE INDEX IDX_Main ON #MainAdmDetails (PAT_ENC_CSN_ID) 



/*SELECT * FROM #MainAdmDetails*/

/*CHIEF COMPLIANT*/

IF OBJECT_ID(N'tempdb..#Base_Pop_ENC_Reason') IS NOT NULL DROP TABLE #Base_Pop_ENC_Reason;

SELECT DISTINCT cat.PAT_ENC_CSN_ID

	, STRING_AGG(edg.DX_NAME,  ' % ') AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM #MainAdmDetails cat

INNER JOIN [EMRDB].[dbo].[ENCOUNTER_DIAGNOSES] ped ON ped.PAT_ENC_CSN_ID = cat.PAT_ENC_CSN_ID AND ped.LINE >= 1

INNER JOIN [EMRDB].[dbo].[DIAGNOSES] edg ON edg.DX_ID = ped.DX_ID

GROUP BY cat.PAT_ENC_CSN_ID

CREATE INDEX IDX_EncReason ON #Base_Pop_ENC_Reason (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Base_Pop_ENC_Reason*/



/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisEncounters]

	(

		[PatID], 

		[PatName],

		[PatMRNID],

		[EthnicGroup],

		[Race],

		[Location],

		[PatEncCSNID],

		[AgeMonths],

		[AgeYears],

		[InpAdmDate],

		[HospDischTime],

		[Disposition],

		[LosHours],

		[InpatientDataID], 

		[ADTArrivalTime], 

		[EDDepartureTime],

		[HospAdmsnTime],

		[BirthDate],

		[AllEncDx],

		[RefreshDate])

SELECT main.PAT_ID 

	, main.PAT_NAME [PATIENTS]

	, main.PAT_MRN_ID [MRN]

	, main.[Ethnic Group]

	, main.[Race]

	, main.[Location]

	, main.PAT_ENC_CSN_ID [CSN]

	, main.AGE_MONTHS [Age (M)]

	, main.AGE_YEARS[Age (Y)]

	, main.INP_ADM_DATE [Admit Time]

	, main.HOSP_DISCH_TIME [Disch Time]

	, main.Disposition

	, main.LOS_HRS [LOS (Hrs)]

	, main.INPATIENT_DATA_ID

	, main.ADT_ARRIVAL_TIME

	, main.ED_DEPARTURE_TIME

	, main.HOSP_ADMSN_TIME

	, main.BIRTH_DATE

	, enc.[AllEncReasons]

	, GETDATE()

FROM #MainAdmDetails main  

LEFT OUTER JOIN #Base_Pop_ENC_Reason enc ON enc.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID;

END 

