



/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

Date			Who					Description 

----------------------------------------------------------------------------------- 

2022/03/22		Developer B			TKT-004 PBI Conversion. SP created from [USP_IP_SEPSIS]

2022/05/22		V_DEV001			Expansion Phase III Location update

2023/04/19	    Developer C        Merged 3 stored procedures into one: reports.USP_IP_SEPSIS_REPORT, reports.USP_IP_SEPSIS_COMPLIANCE, reports.USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES

2023/12/12		Developer C		Subqueries to get Shift RN/CN was throwing an error due to value in DB being varchar and not int

2024/04/23		Developer C		Changed logic to look for nurses to look 35 minutes before Shift start to account for Nurses assigning themselves at 

										or during Report/hand off which is 30 minutes before shift starts

2025/02/21		Developer C		Changed logic to only look at Sepsis FLO documentation that occured in the same department.  This 

										will prevent positive scores in PICU appearing in non PICU units causing false positives. 

===================================================================================== 

USAGE: 

exec [reporting].[USP_IP_SEPSIS]

************************************************************************************/ 

CREATE    	PROCEDURE [reporting].[USP_IP_SEPSIS]

--DECLARE

@StartDate VARCHAR(20) = NULL,

@EndDate VARCHAR(20) = NULL



AS



SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table reporting.IP_SEPSIS;



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





IF OBJECT_ID(N'tempdb..#MARActions') IS NOT NULL DROP TABLE #MARActions;

	SELECT CAST(vcg.LIST_CAT_VALUE_CODE AS varchar) CAT_ID

	INTO #MARActions

	FROM [dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800007')

CREATE INDEX IDX_MARActions ON #MARActions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#RouteExclusions') IS NOT NULL DROP TABLE #RouteExclusions;

	SELECT vcg.LIST_CAT_VALUE_CODE CAT_ID

	INTO #RouteExclusions

	FROM [dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800008')

	UNION 

	SELECT '11' /*intravenous*/

CREATE INDEX IDX_RouteExclusions ON #RouteExclusions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#BolusMeds') IS NOT NULL DROP TABLE #BolusMeds;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID MED_ID

	INTO #BolusMeds

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'MEDS'

	AND vcg.BASE_GROUPER_ID IN ('800009')

CREATE INDEX IDX_BolusMeds ON #BolusMeds (MED_ID) 

	

IF OBJECT_ID(N'tempdb..#MedGroupers') IS NOT NULL DROP TABLE #MedGroupers;

	SELECT vcg.GROUPER_LIST VCG_ID

	INTO #MedGroupers

	FROM [dbo].[GROUPER_GROUPS] vcg

	WHERE vcg.GROUPER_ID IN ('800011')

CREATE INDEX IDX_MedGroupers ON #MedGroupers (VCG_ID) 



IF OBJECT_ID(N'tempdb..#LacticAcidLRR') IS NOT NULL DROP TABLE #LacticAcidLRR;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID LRR_ID

	INTO #LacticAcidLRR

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'LRR'

	AND vcg.BASE_GROUPER_ID IN ('800012')

CREATE INDEX IDX_Lactic ON #LacticAcidLRR (LRR_ID) 



IF OBJECT_ID(N'tempdb..#BloodCultures') IS NOT NULL DROP TABLE #BloodCultures;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID PROC_ID

	INTO #BloodCultures

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'PCAT'

	AND vcg.BASE_GROUPER_ID IN ('800013')

CREATE INDEX IDX_BloodCultures ON #BloodCultures (PROC_ID) 



IF OBJECT_ID(N'tempdb..#ProphylaxisFLO') IS NOT NULL DROP TABLE  #ProphylaxisFLO;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO  #ProphylaxisFLO

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800014')

CREATE INDEX IDX_ProphylaxisFLO ON #ProphylaxisFLO (FLO_ID) 



IF OBJECT_ID(N'tempdb..#CerebralOxFLO') IS NOT NULL DROP TABLE #CerebralOxFLO;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO  #CerebralOxFLO

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800015')

CREATE INDEX IDX_CerebralOxFLO ON #CerebralOxFLO (FLO_ID) 



IF OBJECT_ID(N'tempdb..#ODScores') IS NOT NULL DROP TABLE #ODScores;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO #ODScores

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800006')

CREATE INDEX IDX_OdScores ON #ODScores (FLO_ID) 



IF OBJECT_ID(N'tempdb..#MainAdmDetails') IS NOT NULL DROP TABLE #MainAdmDetails;

/*list of admitted patients*/

SELECT DISTINCT

	HE.ENCOUNTER_ID

	, HE.PATIENT_ID

	, pat.PATIENT_MRN

	, pat.PATIENT_NAME

	, REG.NAME AS [Ethnic Group]

	, RPR.NAME AS [Race]

	, HE.INPATIENT_DATA_ID

	, HE.ADT_ARRIVAL_TIME

	, HE.HOSP_ADMSN_TIME

	, HE.HOSP_DISCH_TIME

	, HE.INP_ADM_DATE

	, HE.ED_DEPARTURE_TIME

	, RDD.NAME AS [Disposition]

	, loc.LOCATION_ABBR [Location]

	, DATEDIFF(MM,pat.BIRTH_DATE,HE.HOSP_ADMSN_TIME) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,pat.BIRTH_DATE,HE.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,HE.HOSP_ADMSN_TIME)) + DATENAME(YEAR, CONVERT(DATE, HE.HOSP_ADMSN_TIME)) AS Admit_Date_stamp

	, DATENAME(month, CONVERT(DATE,HE.HOSP_DISCH_TIME)) + DATENAME(YEAR, CONVERT(DATE, HE.HOSP_DISCH_TIME)) AS Disch_Date_stamp

	, DATEDIFF(HH, HE.HOSP_ADMSN_TIME, HE.HOSP_DISCH_TIME) AS LOS_HRS

	, CONVERT(DATE, pat.BIRTH_DATE) BIRTH_DATE

INTO #MainAdmDetails

FROM [dbo].[HOSPITAL_TRANSACTIONS] htr

INNER JOIN [dbo].[CALENDAR_DATES] sd ON sd.CALENDAR_DT = CONVERT(DATE, htr.SERVICE_DATE)

INNER JOIN [dbo].[HOSPITAL_ENCOUNTERS] HE ON htr.ENCOUNTER_ID = HE.ENCOUNTER_ID

INNER JOIN [dbo].[PATIENTS] pat ON pat.PATIENT_ID = HE.PATIENT_ID

LEFT OUTER JOIN [dbo].[REF_DISCHARGE_DISPOSITION] RDD ON RDD.DISCH_DISP_CODE = HE.DISCH_DISP_CODE

LEFT OUTER JOIN [dbo].[REF_ETHNIC_GROUP] REG ON REG.ETHNIC_GROUP_CODE = pat.ETHNIC_GROUP_CODE

LEFT OUTER JOIN [dbo].[PATIENT_DEMOGRAPHICS_RACE] race ON race.PATIENT_ID = pat.PATIENT_ID AND race.LINE = 1

LEFT OUTER JOIN [dbo].[REF_PATIENT_RACE] RPR ON RPR.PATIENT_RACE_CODE = race.PATIENT_RACE_CODE

LEFT OUTER JOIN [dbo].[DEPARTMENTS] dep ON dep.DEPARTMENT_ID = HE.DEPARTMENT_ID

LEFT OUTER JOIN [dbo].[LOCATIONS] loc ON loc.LOC_ID = dep.REV_LOC_ID

WHERE HE.INP_ADM_DATE IS NOT NULL  /*date time of inpatient admission*/

AND sd.CALENDAR_DT BETWEEN @dStartDate AND @dEndDate /*Service data of a charge*/

CREATE INDEX IDX_Main ON #MainAdmDetails (ENCOUNTER_ID) 

/*SELECT * FROM #MainAdmDetails*/



/*CHIEF COMPLIANT*/

IF OBJECT_ID(N'tempdb..#Base_Pop_ENC_Reason') IS NOT NULL DROP TABLE #Base_Pop_ENC_Reason;

SELECT DISTINCT cat.ENCOUNTER_ID

	, STRING_AGG(DIAG.DX_NAME,  ' % ') AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM #MainAdmDetails cat

INNER JOIN [dbo].[ENCOUNTER_DIAGNOSES] EDX ON EDX.ENCOUNTER_ID = cat.ENCOUNTER_ID AND EDX.LINE > 1

INNER JOIN [dbo].[DIAGNOSES] DIAG ON DIAG.DX_ID = EDX.DX_ID

GROUP BY cat.ENCOUNTER_ID

CREATE INDEX IDX_EncReason ON #Base_Pop_ENC_Reason (ENCOUNTER_ID) 

/*SELECT * FROM #Base_Pop_ENC_Reason*/



/***********************************************************************

Get Encounters and a record for every shift a PATIENTS was in a department for Compliance reporting

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_PopTemp') IS NOT NULL DROP TABLE #Base_PopTemp;

WITH vaplh AS

(

	SELECT 

		adtIn.ENCOUNTER_ID

		, adtIn.EFFECTIVE_TIME AS IN_DTTM

		, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()) AS OUT_DTTM

		, adtIn.DEPARTMENT_ID AS ADT_DEPARTMENT_ID

		, CASE WHEN adtIn.DEPARTMENT_ID IS NULL THEN '*Department not specified'

			 WHEN dep.DEPARTMENT_ID IS NULL THEN '*Unknown department'

			 WHEN dep.DEPARTMENT_NAME IS NULL THEN '*Unnamed department'

			 ELSE dep.DEPARTMENT_NAME

		END AS ADT_DEPARTMENT_NAME

		, DATEADD(MI, 1140, DATEADD(DD, -1, DATEDIFF(DD, 0, CONVERT(DATE, adtIn.EFFECTIVE_TIME)))) [In Previous PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, adtIn.EFFECTIVE_TIME)))) [In Previous PM End]

		, DATEADD(MI, 420, DATEADD(DD, 0, DATEDIFF(DD, 0,  CONVERT(DATE, adtIn.EFFECTIVE_TIME)))) [In AM Start]

		, DATEADD(MI, 1139, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, adtIn.EFFECTIVE_TIME)))) [In AM End]

		, DATEADD(MI, 1140, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, adtIn.EFFECTIVE_TIME)))) [In PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 1, DATEDIFF(DD, 0, CONVERT(DATE, adtIn.EFFECTIVE_TIME)))) [In PM End]

		, DATEADD(MI, 1140, DATEADD(DD, -1, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()))))) [Out Previous PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()))))) [Out Previous PM End]

		, DATEADD(MI, 420, DATEADD(DD, 0, DATEDIFF(DD, 0,  CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()))))) [Out AM Start]

		, DATEADD(MI, 1139, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()))))) [Out AM End]

		, DATEADD(MI, 1140, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()))))) [Out PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 1, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(adtOut.EFFECTIVE_TIME,GETDATE()))))) [Out PM End]

	FROM #MainAdmDetails ENCS

	INNER JOIN [dbo].[HOSPITAL_ENCOUNTERS] HENC ON ENCS.ENCOUNTER_ID = HENC.ENCOUNTER_ID /*Developer C minimize to ENC_ID's we are looking at*/

	INNER JOIN [dbo].[ADT_EVENTS] adtIn ON adtIn.ENCOUNTER_ID = HENC.ENCOUNTER_ID

	LEFT OUTER JOIN [dbo].[ADT_EVENTS] adtOut ON adtIn.NEXT_OUT_EVENT_ID = adtOut.EVENT_ID

	LEFT OUTER JOIN [dbo].[DEPARTMENTS] dep ON adtIn.DEPARTMENT_ID = dep.DEPARTMENT_ID

	WHERE adtIn.EVENT_TYPE_CODE IN (1, 3, 99) /*Only look at "in" events (Admission and Transfer In, LOA Return)*/

	AND adtIn.EVENT_SUBTYPE_CODE <> 2 /*Exclude deleted/canceled events*/

)



SELECT DISTINCT

	HE.ENCOUNTER_ID

	, HE.PATIENT_ID

	, vaplh.ADT_DEPARTMENT_ID

	, vaplh.ADT_DEPARTMENT_NAME

	, cvs.CODE_DESC AS DEPARTMENT_ROLLUP

	, vaplh.IN_DTTM

	, vaplh.OUT_DTTM

	, HE.INPATIENT_DATA_ID

	, main.BIRTH_DATE

	, HE.ADT_ARRIVAL_TIME

	, HE.ED_DEPARTURE_TIME

	, CONVERT(DATE, vaplh.IN_DTTM) InDeptDate

	, CONVERT(DATE, vaplh.OUT_DTTM) OutDeptDate

	, CASE WHEN vaplh.IN_DTTM between vaplh.[In Previous PM Start] AND [In Previous PM End] THEN CONVERT(DATE, [In Previous PM Start])

		ELSE CONVERT(DATE, [In AM Start])

	END [In Shift Date]

	, CASE WHEN vaplh.IN_DTTM between [In AM Start] AND [In AM End] THEN 'AM'

		ELSE 'PM'

	END [In Shift]

	

	, CASE WHEN vaplh.OUT_DTTM between vaplh.[Out Previous PM Start] AND [Out Previous PM End] THEN CONVERT(DATE, [Out Previous PM Start])

		ELSE CONVERT(DATE, [Out AM Start])

	END [Out Shift Date]

	, CASE WHEN vaplh.OUT_DTTM between [Out AM Start] AND [Out AM End] THEN 'AM'

		ELSE 'PM'

	END [Out Shift]

	, [Out Previous PM Start]

	, [Out Previous PM End] 

	, ROW_NUMBER() OVER (PARTITION BY HE.ENCOUNTER_ID, vaplh.IN_DTTM ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM) [inDeptRN]

	, ROW_NUMBER() OVER (PARTITION BY HE.ENCOUNTER_ID ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM ) [ENC_ID Order]

INTO #Base_PopTemp

FROM #MainAdmDetails main

INNER JOIN [dbo].[HOSPITAL_ENCOUNTERS] HE ON HE.ENCOUNTER_ID = main.ENCOUNTER_ID

INNER JOIN  vaplh ON vaplh.ENCOUNTER_ID = HE.ENCOUNTER_ID AND vaplh.ADT_DEPARTMENT_ID IS NOT NULL /*[dbo].V_PATIENT_LOCATION_HISTORY*/

INNER JOIN [reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = vaplh.ADT_DEPARTMENT_ID

			AND cvs.VALUE_SET_ID = 3031 /*DEPARTMENT ROLL UP*/

CREATE INDEX IDX_Base_PopTemp ON #Base_PopTemp (ENCOUNTER_ID) 

/*SELECT * FROM #Base_PopTemp*/



/***********************************************************************

Get Every day a PATIENTS should have had a Sepsis Screening

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

; WITH dateCTE AS

(

	SELECT ENCOUNTER_ID

		, [In Shift Date] [Expansion Start Date]

		, [In Shift] [Expansion Start Shift]

		, [Out Shift Date] [Expansion End Date]

		, [Out Shift] [Expansion End Shift]

		, [In Shift Date] [Expansion Date]

		, IN_DTTM [InDepartmentTime]

		, OUT_DTTM [OutDepartmentTime]

		, CASE WHEN [In Shift] = 'AM' AND [Out Shift Date] >= [In Shift Date] THEN 2

			ELSE 1

		END [Shifts per Day]

		, CASE WHEN [In Shift] = 'AM' AND [Out Shift Date] <> [In Shift Date] THEN 1

			ELSE 0

		END [AM Denom]

		, CASE WHEN [In Shift] = 'PM' THEN 1

			WHEN [In Shift Date] <> [Out Shift Date] THEN 1

			ELSE 0

		END [PM Denom]

		, ADT_DEPARTMENT_ID

		, ADT_DEPARTMENT_NAME

		, PATIENT_ID

		, DEPARTMENT_ROLLUP

		, INPATIENT_DATA_ID

		, BIRTH_DATE

		, 1 [In Record]

		, CASE WHEN [In Shift Date] = [Out Shift Date] THEN 1 ELSE 0 END [Out Record]

		, [ENC_ID Order]

	FROM #Base_PopTemp

	WHERE inDeptRN = 1

	AND DEPARTMENT_ROLLUP NOT IN ('ER', 'P-ER')

	UNION ALL 

	SELECT ENCOUNTER_ID

		, d.[Expansion Start Date]

		, d.[Expansion Start Shift]

		, d.[Expansion End Date]

		, d.[Expansion End Shift]

		, DATEADD(d, 1, d.[Expansion Date]) [Expansion Date]

		, d.[InDepartmentTime]

		, d.[OutDepartmentTime]

		, CASE WHEN DATEADD(d, 1, d.[Expansion Date]) = d.[Expansion End Date] AND d.[Expansion End Shift] = 'AM' THEN 1

			ELSE 2

		END [Shifts per Day]

		, CASE WHEN DATEADD(d, 1, d.[Expansion Date]) = d.[Expansion End Date] AND d.[Expansion End Shift] = 'AM' THEN 1

			WHEN DATEADD(d, 1, d.[Expansion Date]) BETWEEN d.[Expansion Start Date] AND d.[Expansion End Date] THEN 1

			ELSE 0

		END [AM Denom]

		, CASE WHEN DATEADD(d, 1, d.[Expansion Date]) = d.[Expansion End Date] AND d.[Expansion End Shift] = 'PM' THEN 1

			WHEN DATEADD(d, 1, d.[Expansion Date]) <> d.[Expansion End Date] THEN 1

			ELSE 0

		END [PM Denom]

		, d.ADT_DEPARTMENT_ID

		, d.ADT_DEPARTMENT_NAME

		, d.PATIENT_ID

		, d.DEPARTMENT_ROLLUP

		, d.INPATIENT_DATA_ID

		, BIRTH_DATE

		, CASE WHEN DATEADD(d, 1, d.[Expansion Date]) = d.[Expansion Start Date] THEN 1 ELSE 0 END  [In Record]

		, CASE WHEN DATEADD(d, 1, d.[Expansion Date]) = d.[Expansion End Date] THEN 1 ELSE 0 END [Out Record]

		, [ENC_ID Order]

	FROM dateCTE d 

	WHERE DATEADD(d, 1, d.[Expansion Date]) <= d.[Expansion End Date]

)



/***********************************************************************

Finalize base table, one record for each shift a PATIENTS was in a unit

***********************************************************************/

SELECT * 

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, [InDepartmentTime] ORDER BY [Score Date], [Shift AM/PM]) AS [Unit Order]

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY [InDepartmentTime], [Score Date], [Shift AM/PM]) AS [ENC_ID Overall Order]

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, [Shift Start] ORDER BY [Score Date], [Shift AM/PM]) AS [Shift Order]

INTO #Base_Pop

FROM (

	SELECT am.ENCOUNTER_ID

		, am.[Expansion Start Date] [In Dept Date]

		, am.[Expansion Start Shift] [In Dept Shift]

		, am.[Expansion End Date] [Out Dept Date]

		, am.[Expansion End Shift] [Out Dept Shift]

		, am.[Expansion Date] [Score Date]

		, am.[InDepartmentTime]

		, am.[OutDepartmentTime]

		, am.[Shifts per Day]

		, am.[AM Denom]

		, am.[PM Denom]

		, am.ADT_DEPARTMENT_ID

		, am.ADT_DEPARTMENT_NAME

		, am.PATIENT_ID

		, am.DEPARTMENT_ROLLUP

		, am.INPATIENT_DATA_ID

		, DATEDIFF(MM, BIRTH_DATE, a.[Shift Start]) AS AGE_MONTHS

		, FLOOR(DATEDIFF(DD, BIRTH_DATE, a.[Shift End])/365.25) AS AGE_YEARS

		, am.[In Record]

		, am.[Out Record]

		, [ENC_ID Order]

		, 'AM (Day Shift)' [Shift AM/PM]

		, a.[Shift Start]

		, a.[Shift End]

	FROM dateCTE am 

	CROSS APPLY ( 

		SELECT DATEADD(MI, 420, DATEADD(DD, 0, DATEDIFF(DD, 0, am.[Expansion Date]))) [Shift Start]

			, DATEADD(MI, 1139, DATEADD(DD, 0, DATEDIFF(DD, 0, am.[Expansion Date]))) [Shift End]

	) a

	WHERE [AM Denom] = 1 

	UNION ALL

	SELECT pm.ENCOUNTER_ID

		, pm.[Expansion Start Date]

		, pm.[Expansion Start Shift]

		, pm.[Expansion End Date]

		, pm.[Expansion End Shift]

		, pm.[Expansion Date]

		, pm.[InDepartmentTime]

		, pm.[OutDepartmentTime]

		, pm.[Shifts per Day]

		, pm.[AM Denom]

		, pm.[PM Denom]

		, pm.ADT_DEPARTMENT_ID

		, pm.ADT_DEPARTMENT_NAME

		, pm.PATIENT_ID

		, pm.DEPARTMENT_ROLLUP

		, pm.INPATIENT_DATA_ID

		, DATEDIFF(MM, BIRTH_DATE, a.[Shift Start]) AS AGE_MONTHS

		, FLOOR(DATEDIFF(DD, BIRTH_DATE, a.[Shift End])/365.25) AS AGE_YEARS

		, pm.[In Record]

		, pm.[Out Record]

		, [ENC_ID Order]

		, 'PM (Night Shift)' [Shift AM/PM]

		, a.[Shift Start]

		, a.[Shift End]

	FROM dateCTE pm 

	CROSS APPLY ( 

		SELECT DATEADD(MI, 1140, DATEADD(DD, 0, DATEDIFF(DD, 0, pm.[Expansion Date]))) [Shift Start]

			, DATEADD(MI, 419, DATEADD(DD, 1, DATEDIFF(DD, 0, pm.[Expansion Date]))) [Shift End]

	) a

	WHERE pm.[PM Denom] = 1

) a

OPTION (MAXRECURSION 8000);  /*default is 100*/

CREATE INDEX IDX_Base_Pop ON #Base_Pop (ENCOUNTER_ID) 

/*SELECT * FROM #Base_Pop*/



IF OBJECT_ID(N'tempdb..#FlwshtLstEncounterWts') IS NOT NULL DROP TABLE #FlwshtLstEncounterWts;

SELECT * , ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY [ENC_ID Order], [Unit Order], RECORDED_TIME) AS [Weight Row]

INTO #FlwshtLstEncounterWts

FROM 

(

	SELECT 

		main.ENCOUNTER_ID

		, meas.FSD_ID

		, meas.MEAS_VALUE

		, meas.RECORDED_TIME

		, main.[ENC_ID Order]

		, main.[Unit Order]

		, main.[ENC_ID Overall Order]

		, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, [ENC_ID Order], [Unit Order] ORDER BY [ENC_ID Order], [Unit Order], RECORDED_TIME) AS [Unit Order Row]

	FROM #Base_Pop main 

	INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '94'

	WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

) a

WHERE a.[Unit Order Row] = 1

CREATE INDEX IDX_FloEncWeight ON #FlwshtLstEncounterWts (ENCOUNTER_ID) 

/*SELECT * FROM #FlwshtLstEncounterWts */



IF OBJECT_ID(N'tempdb..#EncWeights') IS NOT NULL DROP TABLE #EncWeights;

SELECT

	ENCOUNTER_ID

	, EncWeight

	, [ENC_ID Order]

	, [Unit Order]

	, [ENC_ID Overall Order]

	, [Weight Row]

	, CASE WHEN [Previous Weight Record] IS NULL THEN 1 ELSE [ENC_ID Overall Order] + 1 END AS [Start Weight Record]

	, CASE WHEN [Next Weight Record] IS NULL THEN 

		( SELECT MAX([ENC_ID Overall Order]) FROM #Base_Pop bp WHERE bp.ENCOUNTER_ID = a.ENCOUNTER_ID)

	ELSE [Next Weight Record] - 1 END AS [Next Weight Record]

INTO #EncWeights

FROM (

	SELECT

		encWt.ENCOUNTER_ID

		, CAST(ROUND(CONVERT(FLOAT, encWt.MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

		, [ENC_ID Order]

		, [Unit Order]

		, [ENC_ID Overall Order]

		, [Weight Row]

		, LAG([ENC_ID Overall Order], 1) OVER(PARTITION BY ENCOUNTER_ID ORDER BY ENCOUNTER_ID, [Weight Row]) AS [Previous Weight Record]

		, LEAD([ENC_ID Overall Order], 1) OVER(PARTITION BY ENCOUNTER_ID ORDER BY ENCOUNTER_ID, [Weight Row]) AS [Next Weight Record]

	FROM #FlwshtLstEncounterWts encWt

) a



IF OBJECT_ID(N'tempdb..#EncounterWeights') IS NOT NULL DROP TABLE #EncounterWeights;

	SELECT bp.ENCOUNTER_ID

		, bp.[ENC_ID Overall Order]

		, e.EncWeight

	INTO #EncounterWeights

	FROM #Base_Pop bp

	INNER JOIN #EncWeights e ON bp.ENCOUNTER_ID = e.ENCOUNTER_ID AND e.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

UNION 

	SELECT  bp.ENCOUNTER_ID

		, bp.[ENC_ID Overall Order]

		, e.EncWeight 

	FROM #Base_Pop bp

	INNER JOIN #EncWeights e ON bp.ENCOUNTER_ID = e.ENCOUNTER_ID AND bp.[ENC_ID Overall Order] between e.[Start Weight Record] AND e.[Next Weight Record]

CREATE INDEX IDX_EncounterWeights ON #EncounterWeights (ENCOUNTER_ID) 

/*SELECT * FROM #EncounterWeights*/



/*****************************POSITIVE ED SEPSIS SCORES & ED LOS*****************************/

IF OBJECT_ID(N'tempdb..#Base_Pop_Severe_ED_Scores') IS NOT NULL DROP TABLE #Base_Pop_Severe_ED_Scores;

SELECT main.ENCOUNTER_ID

	, CEILING(CONVERT(FLOAT,DATEDIFF(MI, main.ADT_ARRIVAL_TIME, main.ED_DEPARTURE_TIME))/60) HoursInED/*CHECK WITH STEPHANIE ON */

	, main.ADT_ARRIVAL_TIME

	, meas.MEAS_VALUE

	, meas.RECORDED_TIME

	, main.ED_DEPARTURE_TIME

	, ROW_NUMBER() OVER(PARTITION BY main.ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #Base_Pop_Severe_ED_Scores 

FROM #MainAdmDetails main 

INNER JOIN [dbo].[HOSPITAL_ENCOUNTERS] HE ON HE.ENCOUNTER_ID = main.ENCOUNTER_ID

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = HE.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID and

	meas.FLO_MEAS_ID IN ('9000161709','9000002613')/*SEPSIS SCORE ADDED NEW ED SEPSIS SCORE 9000002613 ON 10.01.2019*/

	and (meas.RECORDED_TIME <=  main.ED_DEPARTURE_TIME)

CREATE INDEX IDX_Pop_Severe_ED_Scores ON #Base_Pop_Severe_ED_Scores (ENCOUNTER_ID) 

/*Select * from #Base_Pop_Severe_ED_Scores*/



IF OBJECT_ID(N'tempdb..#EDPosScore_EDLOS') IS NOT NULL DROP TABLE #EDPosScore_EDLOS;

SELECT edScore.ENCOUNTER_ID

	, edScore.HoursInED

	, edScore.MEAS_VALUE

	, edScore.RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY edScore.ENCOUNTER_ID ORDER BY edScore.RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY edScore.ENCOUNTER_ID ORDER BY edScore.RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO #EDPosScore_EDLOS

FROM #Base_Pop_Severe_ED_Scores edScore

WHERE edScore.MEAS_VALUE > 4

CREATE INDEX IDX_EDPosScore_EDLOS ON #EDPosScore_EDLOS (ENCOUNTER_ID) 

/*SELECT * FROM #EDPosScore_EDLOS*/



/*OD Score*/

IF OBJECT_ID(N'tempdb..#FlwshtLst') IS NOT NULL DROP TABLE #FlwshtLst;

SELECT ENCOUNTER_ID, FLO_MEAS_ID, RECORDED_TIME, MEAS_VALUE, FSD_ID, [Documented Department ID], [Documented Department], [ENC_ID Overall Order]

INTO #FlwshtLst

FROM (

	SELECT main.ENCOUNTER_ID

		, meas.FLO_MEAS_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE

		, meas.FSD_ID

		, bpt.IN_DTTM

		, bpt.OUT_DTTM

		, bpt.ADT_DEPARTMENT_ID [Documented Department ID]

		, bpt.ADT_DEPARTMENT_NAME [Documented Department]

		, main.[ENC_ID Order]

		, main.[Unit Order]

		, main.[ENC_ID Overall Order]

		, ROW_NUMBER() OVER(PARTITION BY main.ENCOUNTER_ID, main.[ENC_ID Order], main.[Unit Order] ORDER BY [Shift Start], RECORDED_TIME) AS RowNum

	FROM #Base_Pop main

	INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID IN (SELECT * FROM #ODScores)

	INNER JOIN #Base_PopTemp bpt ON bpt.ENCOUNTER_ID = main.ENCOUNTER_ID AND meas.RECORDED_TIME BETWEEN bpt.IN_DTTM AND bpt.OUT_DTTM AND main.[ENC_ID Order] = bpt.[ENC_ID Order]

	WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

) a

WHERE a.RowNum = 1

CREATE INDEX IDX_FlwshtLst ON #FlwshtLst (ENCOUNTER_ID, FSD_ID) 

/*SELECT * FROM #FlwshtLst ORDER BY RECORDED_TIME*/



/*****************************OD Huddle Flowsheet rows*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtLstHuddleODScore') IS NOT NULL DROP TABLE #FlwshtLstHuddleODScore;

SELECT main.ENCOUNTER_ID

	, meas.FSD_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME

	, meas.MEAS_VALUE

	, main.[ENC_ID Overall Order]

INTO #FlwshtLstHuddleODScore

FROM #Base_Pop main

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000002705','9000002732','9000002733','9000002706','9000002734','9000002707')

	AND meas.MEAS_VALUE IS NOT NULL

WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

CREATE INDEX IDX_FlwshtLstHuddleODScore ON #FlwshtLstHuddleODScore (ENCOUNTER_ID, FSD_ID) 

/*SELECT * FROM #FlwshtLstHuddleODScore*/



/*****************************Flowsheet row for CLINICAL_ALERTS not activated*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtNoAlert') IS NOT NULL DROP TABLE #FlwshtNoAlert;

SELECT a.ENCOUNTER_ID

	, MAX(a.RECORDED_TIME) RECORDED_TIME

	, STRING_AGG([CLINICAL_ALERTS Not Activated Reason],  ' % ') [CLINICAL_ALERTS Not Activated Reason]

	, STRING_AGG([CLINICAL_ALERTS Not Activated Comment],  ' % ') [CLINICAL_ALERTS Not Activated Comment]

	, a.[ENC_ID Overall Order]

INTO #FlwshtNoAlert

FROM (

	SELECT main.ENCOUNTER_ID

		, rec.INPATIENT_DATA_ID

		, meas.FSD_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE AS [CLINICAL_ALERTS Not Activated Reason]

		, meas.MEAS_COMMENT as [CLINICAL_ALERTS Not Activated Comment]

		, main.[ENC_ID Overall Order]

	FROM #Base_Pop main

	INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '9000003159'

	WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

) a

GROUP BY a.ENCOUNTER_ID, a.[ENC_ID Overall Order]

CREATE INDEX IDX_FlwshtNoAlert ON #FlwshtNoAlert (ENCOUNTER_ID, [ENC_ID Overall Order]) 

/*SELECT * FROM #FlwshtNoAlert*/



IF OBJECT_ID(N'tempdb..#FlwshtAlert') IS NOT NULL DROP TABLE #FlwshtAlert;

SELECT a.ENCOUNTER_ID

	, a.ALT_ID

	, a.ALT_ACTION_INST

	, a.[CLINICAL_ALERTS Activated Comment]

	, a.[ENC_ID Overall Order]

INTO #FlwshtAlert

FROM (

	SELECT main.ENCOUNTER_ID

		, alt.ALT_ID

		, his.ALT_ACTION_INST

		, COALESCE(his.SPEC_OVR_CMNT,' ')+ rsn.[NAME] [CLINICAL_ALERTS Activated Comment]

		, main.[ENC_ID Overall Order]

		, ROW_NUMBER() OVER(PARTITION BY main.ENCOUNTER_ID, main.[ENC_ID Overall Order] ORDER BY main.[ENC_ID Overall Order]) RowNum

	FROM #Base_Pop main

	INNER JOIN [dbo].[CLINICAL_ALERTS] alt ON alt.VISIT_ID = main.ENCOUNTER_ID AND alt.BPA_LOCATOR_ID = 900400001 /*BASE 2019 HS OD SCORE SEPSIS >2 [900400001]*/

	INNER JOIN [dbo].[ALERT_HISTORY] his ON his.ALT_ID = alt.ALT_ID

	INNER JOIN [dbo].[REF_ALERT_OVERRIDE_REASONS] rsn ON rsn.ALRT_SP_OVR_RSN_CODE = his.SPEC_OVR_RSN_CODE

	WHERE his.ALT_ACTION_INST BETWEEN main.[Shift Start] AND main.[Shift End]

) a

WHERE a.RowNum = 1

CREATE INDEX IDX_FlwshtAlert ON #FlwshtAlert (ENCOUNTER_ID) 

/*SELECT * FROM #FlwshtAlert*/



IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT bp.ENCOUNTER_ID

	, bp.ADT_DEPARTMENT_ID

	, bp.ADT_DEPARTMENT_NAME

	, bp.InDepartmentTime

	, bp.OutDepartmentTime

	, meas.MEAS_VALUE [OD Score]

	, meas.RECORDED_TIME [OD Score Time]

	, bp.[Score Date] [Score Day]

	, huddleNote.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP]

	, huddleNote.[Huddle Date]

	, huddleNote.[Huddle Time]

	, huddleNote.[PATIENTS Assessed by MD/PNP]

	, huddleNote.[Physician Name]

	, huddleNote.[Additional Orders Received/Placed by MD/PNP]

	, alertNotActivated.[CLINICAL_ALERTS Not Activated Reason]

	, alertNotActivated.[CLINICAL_ALERTS Not Activated Comment]

	, alertActivated.[CLINICAL_ALERTS Activated Comment]

	, bp.[ENC_ID Overall Order]

	, CASE WHEN meas.MEAS_VALUE >= 2 THEN 'Y' ELSE 'N' END [ShowComponents]

	, meas.FSD_ID

INTO #Base_Pop_OD_Scores

FROM #Base_Pop bp 

INNER JOIN [dbo].[HOSPITAL_ENCOUNTERS] HE ON HE.ENCOUNTER_ID = bp.ENCOUNTER_ID

LEFT OUTER JOIN #FlwshtLst meas ON meas.ENCOUNTER_ID = bp.ENCOUNTER_ID AND meas.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #FlwshtNoAlert alertNotActivated on 

	(	

		alertNotActivated.ENCOUNTER_ID = bp.ENCOUNTER_ID 

		AND alertNotActivated.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

	)

LEFT OUTER JOIN #FlwshtAlert alertActivated on 

	(	

		alertActivated.ENCOUNTER_ID = bp.ENCOUNTER_ID 

		AND alertActivated.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

	)

OUTER APPLY 

(

	SELECT bp.INPATIENT_DATA_ID

		, a.OD_SCORE_RECORDED_TIME

		, a.FSD_ID

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002705' THEN a.MEAS_VALUE END) AS "Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002732' THEN TRY_CAST(DATEADD(DAY,TRY_CAST(a.MEAS_VALUE AS INT),'1840-12-31') AS DATE) END) AS "Huddle Date"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002733' THEN TRIM(RIGHT(TRY_CAST(DATEADD(SECOND,TRY_CAST(MEAS_VALUE AS INT),'1840-12-31') AS VARCHAR(20)),7)) END) AS "Huddle Time"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002706' THEN a.MEAS_VALUE END) AS "PATIENTS Assessed by MD/PNP"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002734' THEN a.MEAS_VALUE END) AS "Physician Name"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002707' THEN a.MEAS_VALUE END) AS "Additional Orders Received/Placed by MD/PNP"

	FROM

	(

		SELECT bp.INPATIENT_DATA_ID

			, meas.RECORDED_TIME as OD_SCORE_RECORDED_TIME

			, subMeas.FLO_MEAS_ID

			, subMeas.RECORDED_TIME

			, subMeas.MEAS_VALUE

			, subMeas.FSD_ID

			, ROW_NUMBER() OVER (PARTITION BY bp.INPATIENT_DATA_ID, meas.RECORDED_TIME, subMeas.FLO_MEAS_ID ORDER BY subMeas.RECORDED_TIME) rownumber

		FROM #FlwshtLstHuddleODScore subMeas

		WHERE DATEDIFF(MINUTE, meas.RECORDED_TIME, subMeas.RECORDED_TIME) BETWEEN -30 AND 180 /*WAS -120 UNTIL 03.01.2021 */

		AND subMeas.MEAS_VALUE IS NOT NULL

		AND subMeas.FSD_ID = meas.FSD_ID

	) a

	WHERE a.rownumber = 1

	GROUP BY a.INPATIENT_DATA_ID, a.OD_SCORE_RECORDED_TIME, a.FSD_ID

) huddleNote

CREATE INDEX IDX_Base_Pop_OD_Scores ON #Base_Pop_OD_Scores (ENCOUNTER_ID) 

/*SELECT * FROM #Base_Pop_OD_Scores */



IF OBJECT_ID(N'tempdb..#SepsisAuditTemp') IS NOT NULL DROP TABLE #SepsisAuditTemp;

SELECT main.ENCOUNTER_ID, main.[ENC_ID Overall Order], od.[OD Score Time], meas.FLO_MEAS_ID, meas.MEAS_VALUE, meas.RECORDED_TIME

	, DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME) [Time since OD Score]

	, ABS(DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME)) [ABS Time since OD Score]

INTO #SepsisAuditTemp

FROM #Base_Pop main

INNER JOIN #Base_Pop_OD_Scores od ON od.ENCOUNTER_ID = main.ENCOUNTER_ID AND od.[ENC_ID Overall Order] = main.[ENC_ID Overall Order]

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON od.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000161701', '9000161702', '9000161710', '9000161708', '9000161704', '9000002611'

			, '98', '99', '95', '9000800500', '900101', '900103', '900102', '900104', '900105', '900107', '900106'

			, '900108', '9000002702', '900109', '900110', '9000311801', '9000311802', '9000311803', '9000003157')

WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

AND od.ShowComponents = 'Y'

AND DATEDIFF(MINUTE, od.[OD Score Time], meas.RECORDED_TIME) BETWEEN -30 AND 180 /*WAS -120 UNTIL 03.01.2021 */



IF OBJECT_ID(N'tempdb..#FlwshtLstSepsisAudit') IS NOT NULL DROP TABLE #FlwshtLstSepsisAudit;

SELECT bp.ENCOUNTER_ID

	, bp.ADT_DEPARTMENT_ID

	, bp.ADT_DEPARTMENT_NAME

	, bp.InDepartmentTime

	, bp.OutDepartmentTime

	, meas.MEAS_VALUE [OD Score]

	, meas.RECORDED_TIME [OD Score Time]

	, bp.[Score Date] [Score Day]

	, sepsisAudit.[Predisposition]

	, sepsisAudit.[Infectious Symptoms]

	, sepsisAudit.[Hematologic Dysfunction]

	, sepsisAudit.[Renal Dysfunction]

	, sepsisAudit.[Neurological Dysfunction]

	, sepsisAudit.[Respiratory Dysfunction]

	, sepsisAudit.[Pulse]

	, sepsisAudit.[Resp]

	, sepsisAudit.[BP]

	, sepsisAudit.[Perfusion (WDL)]

	, sepsisAudit.[R Brachial Pulse]

	, sepsisAudit.[L Brachial Pulse]

	, sepsisAudit.[R Radial Pulse]

	, sepsisAudit.[L Radial Pulse]

	, sepsisAudit.[R Posterior Tibial Pulse]

	, sepsisAudit.[L Posterior Tibial Pulse]

	, sepsisAudit.[R Pedal Pulse]

	, sepsisAudit.[L Pedal Pulse]

	, sepsisAudit.[Capillary Refill]

	, sepsisAudit.[Skin Color]

	, sepsisAudit.[Skin Condition/Temp]

	, sepsisAudit.[External Lactate Result (mmol/L)]

	, sepsisAudit.[External Creatinine (mg/dL)]

	, sepsisAudit.[External Platelets (x 1000/uL)]

	, sepsisAudit.[Notification]

	, bp.[ENC_ID Overall Order]

INTO #FlwshtLstSepsisAudit

FROM #Base_Pop bp 

INNER JOIN [dbo].[HOSPITAL_ENCOUNTERS] HE ON HE.ENCOUNTER_ID = bp.ENCOUNTER_ID

LEFT OUTER JOIN #FlwshtLst meas ON meas.ENCOUNTER_ID = bp.ENCOUNTER_ID AND meas.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

OUTER APPLY 

(

	SELECT bp.ENCOUNTER_ID

		, bp.[ENC_ID Overall Order]

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900101' THEN a.MEAS_VALUE END) AS "R Brachial Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900102' THEN a.MEAS_VALUE END) AS "R Radial Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900103' THEN a.MEAS_VALUE END) AS "L Brachial Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900104' THEN a.MEAS_VALUE END) AS "L Radial Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900105' THEN a.MEAS_VALUE END) AS "R Posterior Tibial Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900106' THEN a.MEAS_VALUE END) AS "R Pedal Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900107' THEN a.MEAS_VALUE END) AS "L Posterior Tibial Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900108' THEN a.MEAS_VALUE END) AS "L Pedal Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900109' THEN a.MEAS_VALUE END) AS "Skin Color"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '900110' THEN a.MEAS_VALUE END) AS "Skin Condition/Temp"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002611' THEN a.MEAS_VALUE END) AS "Respiratory Dysfunction"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000002702' THEN a.MEAS_VALUE END) AS "Capillary Refill"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000003157' THEN a.MEAS_VALUE END) AS "Notification"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000311801' THEN a.MEAS_VALUE END) AS "External Lactate Result (mmol/L)"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000311802' THEN a.MEAS_VALUE END) AS "External Creatinine (mg/dL)"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000311803' THEN a.MEAS_VALUE END) AS "External Platelets (x 1000/uL)"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000161701' THEN a.MEAS_VALUE END) AS "Predisposition"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000161702' THEN a.MEAS_VALUE END) AS "Infectious Symptoms"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000161704' THEN a.MEAS_VALUE END) AS "Neurological Dysfunction"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000161708' THEN a.MEAS_VALUE END) AS "Renal Dysfunction"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000161710' THEN a.MEAS_VALUE END) AS "Hematologic Dysfunction"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000800500' THEN a.MEAS_VALUE END) AS "Perfusion (WDL)"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '95' THEN a.MEAS_VALUE END) AS "BP"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '98' THEN a.MEAS_VALUE END) AS "Pulse"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '99' THEN a.MEAS_VALUE END) AS "Resp"

	FROM

	(

		SELECT 

			subMeas.ENCOUNTER_ID

			, subMeas.FLO_MEAS_ID

			, subMeas.RECORDED_TIME

			, subMeas.MEAS_VALUE

			, ROW_NUMBER() OVER (PARTITION BY subMeas.ENCOUNTER_ID, subMeas.[ENC_ID Overall Order], subMeas.FLO_MEAS_ID ORDER BY subMeas.[ABS Time since OD Score]) rownumber

			, subMeas.[ENC_ID Overall Order]

			, subMeas.[ABS Time since OD Score]

		FROM #SepsisAuditTemp subMeas

		WHERE subMeas.ENCOUNTER_ID = bp.ENCOUNTER_ID

		AND subMeas.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

		AND subMeas.MEAS_VALUE IS NOT NULL

	) a

	WHERE a.rownumber = 1

	GROUP BY ENCOUNTER_ID, [ENC_ID Overall Order]

) sepsisAudit



/*****************************Hypotension*****************************/

IF OBJECT_ID(N'tempdb..#FlwShtHypo') IS NOT NULL DROP TABLE #FlwShtHypo;

Select

	main.ENCOUNTER_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME [Hypotension Time] 

	, meas.MEAS_VALUE

	, meas.FSD_ID 

	, main.AGE_MONTHS /*Age at shift start*/

	, main.AGE_YEARS /*Age at shift start*/

	, main.[ENC_ID Overall Order]

Into #FlwShtHypo 

FROM #Base_Pop main

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '95' AND meas.MEAS_VALUE IS NOT NULL

WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

CREATE INDEX IDX_FlwShtHypo ON #FlwShtHypo (ENCOUNTER_ID, [ENC_ID Overall Order])

/*SELECT * FROM #FlwShtHypo*/



IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;

SELECT    

	base.ENCOUNTER_ID

	, base.AGE_MONTHS

	, base.AGE_YEARS

	, CASE WHEN meas.[Hypotension Time] BETWEEN base.InDepartmentTime AND base.OutDepartmentTime THEN 'Y' ELSE 'N' END [In Dept]

	, base.InDepartmentTime    

	, hypo.[Hypotension Value]    

	, meas.[Hypotension Time]    

	, systolic.SYSTOLIC    

	, base.[ENC_ID Order]

	, base.[Unit Order]

	, base.[ENC_ID Overall Order]

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[ENC_ID Order], base.[Unit Order] ORDER BY base.[ENC_ID Overall Order] ASC) AS TIME_LINE 

INTO #Hypotension 

FROM #Base_Pop base 

INNER JOIN #FlwShtHypo meas ON meas.ENCOUNTER_ID = base.ENCOUNTER_ID AND meas.[ENC_ID Overall Order] = base.[ENC_ID Overall Order]

CROSS APPLY ( SELECT LEFT(meas.MEAS_VALUE, CHARINDEX('/', meas.MEAS_VALUE)-1) SYSTOLIC ) systolic 

CROSS APPLY (    

	SELECT CASE        

		WHEN            

			(base.AGE_MONTHS < 2 AND systolic.SYSTOLIC < 65)            

			OR ((base.AGE_MONTHS >= 2 AND base.AGE_MONTHS < 12) AND systolic.SYSTOLIC < 70)            

			OR ((base.AGE_YEARS >= 1 AND base.AGE_YEARS < 2) AND systolic.SYSTOLIC < 80)            

			OR ((base.AGE_YEARS >= 2 AND base.AGE_YEARS < 6) AND systolic.SYSTOLIC < 90)            

			OR ((base.AGE_YEARS >= 6 AND base.AGE_YEARS < 13) AND systolic.SYSTOLIC < 100)            

			OR (base.AGE_YEARS >= 13 AND systolic.SYSTOLIC < 110)        

		THEN meas.MEAS_VALUE        

		ELSE NULL    

	END AS [Hypotension Value] ) 

hypo 

/*SELECT * FROM #Hypotension */



IF OBJECT_ID(N'tempdb..#ODHYPO') IS NOT NULL DROP TABLE #ODHYPO;

SELECT 

CASE WHEN lastHypo.[Hypotension Value] IS NOT NULL THEN lastHypo.[Hypotension Time] ELSE NULL END [LAST Hypotension Time]

	, lastHypo.[Hypotension Value] [LAST Hypotension Value]

	, CASE WHEN lastHypo.[Hypotension Value] IS NOT NULL THEN lastHypo.[In Dept] ELSE 'N' END AS [LAST Hypotension taken in Dept Y/N]

	, a.*

	, CASE WHEN firstHypo.[Hypotension Value] IS NOT NULL THEN firstHypo.[Hypotension Time] ELSE NULL END [FIRST Hypotension Time]

	, firstHypo.[Hypotension Value] [FIRST Hypotension Value]

	, CASE WHEN firstHypo.[Hypotension Value] IS NOT NULL THEN firstHypo.[In Dept] ELSE 'N' END AS [FIRST Hypotension taken in Dept Y/N]

INTO #ODHYPO

FROM #Base_Pop_OD_Scores a

OUTER APPLY

(

	SELECT TOP 1 hypo.[Hypotension Time], hypo.[Hypotension Value], hypo.[In Dept] 

	FROM #Hypotension hypo

	WHERE hypo.ENCOUNTER_ID = a.ENCOUNTER_ID 

	AND hypo.[Hypotension Time] < a.[OD Score Time]

	ORDER BY HYPO.[Hypotension Time] DESC

)lastHypo

OUTER APPLY

(

	SELECT TOP 1 hypo.[Hypotension Time], hypo.[Hypotension Value], hypo.[In Dept]

	FROM #Hypotension hypo

	WHERE hypo.ENCOUNTER_ID = a.ENCOUNTER_ID 

	AND hypo.[Hypotension Time] >= a.[OD Score Time]

	ORDER BY hypo.[Hypotension Time] ASC

)firstHypo

CREATE INDEX IDX_ODHYPO ON #ODHYPO (ENCOUNTER_ID) 

/*SELECT * FROM #ODHYPO*/

/*****************************END OF HYPO*****************************/



/*****************************Clean up tables*****************************/

IF OBJECT_ID(N'tempdb..#Base_Pop_Severe_ED_Scores') IS NOT NULL DROP TABLE #Base_Pop_Severe_ED_Scores;

IF OBJECT_ID(N'tempdb..#FlwshtLstEncounterWts') IS NOT NULL DROP TABLE #FlwshtLstEncounterWts;

IF OBJECT_ID(N'tempdb..#FlwshtLstHuddleODScore') IS NOT NULL DROP TABLE #FlwshtLstHuddleODScore;

IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;



/*****************************ABX*****************************/

/*All encounters from #Base_pop where ABX was administered*/

IF OBJECT_ID(N'tempdb..#BasePopABX') IS NOT NULL DROP TABLE #BasePopABX;

SELECT

	MO.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, med.NAME

	, mar.TAKEN_TIME AS ABX_ADMIN_TIME

	, mar.SIG AS BOLUS_VOLUME

	, CASE WHEN mar.TAKEN_TIME BETWEEN base.[Shift Start] AND base.[Shift End] THEN base.[ENC_ID Overall Order] ELSE NULL END [In Shift]

	, ROW_NUMBER() OVER(PARTITION BY MO.ENCOUNTER_ID ORDER BY mar.TAKEN_TIME) TIME_LINE

INTO #BasePopABX

FROM #Base_Pop base

INNER JOIN [dbo].[MEDICATION_ORDERS] MO	ON MO.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[MEDICATIONS] med ON med.MEDICATION_ID = MO.MEDICATION_ID AND med.THERA_CLASS_CODE = 11 /*Antibiotics*/

INNER JOIN [dbo].MED_DETAILS_EXT med2 ON med2.MEDICATION_ID = med.MEDICATION_ID /*Developer C Adding to be able to exclude ADMIN_ROUTE_CODE instead of text*/

INNER JOIN [dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = MO.ORDER_MED_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE) /*Developer C Change to Date to search for action*/

WHERE mar.TAKEN_TIME IS NOT NULL /*ADMINISTERED ABX ONLY*/

AND mar.MAR_ACTION_CODE IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

/*VALUES BELOW ADDED TO THE CODE ON STEPHANIE'S REQUEST DURING VALIDATION.*/

AND med2.ADMIN_ROUTE_CODE NOT IN (SELECT * FROM #RouteExclusions)

CREATE INDEX IDX_BasePopABX ON #BasePopABX (ENCOUNTER_ID) 

/*SELECT * FROM #BasePopABX*/



IF OBJECT_ID(N'tempdb..#ODABX') IS NOT NULL DROP TABLE #ODABX;

SELECT lastAbx.ABX_ADMIN_TIME LASTABX_TIME

	, lastAbx.NAME LASTABX_NAME

	, lastAbx.BOLUS_VOLUME AS [LAST ABX Volume]

	, lastAbx.[Last ABX to OD Score Time]

	, CASE WHEN lastAbx.ABX_ADMIN_TIME BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST ABX Given in Dept Y/N]

	, scores.*

	, firstAbx.ABX_ADMIN_TIME FIRSTABX_TIME

	, firstAbx.NAME FIRSTABX_NAME

	, firstAbx.BOLUS_VOLUME AS [FIRST ABX Volume]

	, firstAbx.[OD Score to First ABX Time]

	, CASE WHEN firstAbx.ABX_ADMIN_TIME BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST ABX Given in Dept Y/N]

INTO #ODABX

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 abx.ABX_ADMIN_TIME

		, abx.ADT_DEPARTMENT_ID

		, abx.InDepartmentTime

		, abx.OutDepartmentTime

		, abx.NAME

		, abx.ENCOUNTER_ID

		, abx.ADT_DEPARTMENT_NAME

		, abx.BOLUS_VOLUME

		, DATEDIFF(MI, abx.ABX_ADMIN_TIME, scores.[OD Score Time]) AS [Last ABX to OD Score Time] 

		, TIME_LINE

	FROM #BasePopABX abx

	WHERE abx.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND abx.ABX_ADMIN_TIME < scores.[OD Score Time]

	ORDER BY abx.ABX_ADMIN_TIME DESC

) lastAbx

OUTER APPLY

(

	SELECT TOP 1 abx.ABX_ADMIN_TIME

		, abx.ADT_DEPARTMENT_ID

		, abx.InDepartmentTime

		, abx.OutDepartmentTime

		, abx.NAME

		, abx.ENCOUNTER_ID

		, abx.ADT_DEPARTMENT_NAME

		, abx.BOLUS_VOLUME

		, DATEDIFF(MI, scores.[OD Score Time], abx.ABX_ADMIN_TIME) AS [OD Score to First ABX Time] 

		, TIME_LINE

	FROM #BasePopABX abx

	WHERE abx.ENCOUNTER_ID = scores.ENCOUNTER_ID AND abx.ABX_ADMIN_TIME >= scores.[OD Score Time]

	ORDER BY abx.ABX_ADMIN_TIME ASC

) firstAbx

CREATE INDEX IDX_ODABX ON #ODABX (ENCOUNTER_ID) 

/*SELECT * FROM #ODABX*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#BasePopABX') IS NOT NULL DROP TABLE #BasePopABX;

/*****************************END OF ABX*****************************/



/*****************************ORDER SET*****************************/

/*All encounters from #Base_pop where Bolus was administered*/

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

SELECT DISTINCT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, MO.ORDER_DTTM

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY MO.ORDER_DTTM ASC) AS TIME_LINE

	, MO.PRL_ORDERSET_ID

INTO #SSOrderSet 

FROM #Base_Pop base

INNER JOIN [dbo].ORDER_TRACKING_METRICS MO ON MO.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(MO.ORDER_DTTM AS Date)

WHERE MO.PRL_ORDERSET_ID IN (400001) /*(40400100, 40400058, 40400196, 40400153, 4058600002, 400001) Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway*/

CREATE INDEX IDX_SSOrderSet ON #SSOrderSet (ENCOUNTER_ID) 

/*SELECT * FROM #SSOrderSet*/



IF OBJECT_ID(N'tempdb..#ODORDSET') IS NOT NULL DROP TABLE #ODORDSET;

SELECT lastOs.ORDER_DTTM [LAST OrderSet Time]

	, lastOs.PRL_ORDERSET_ID [LAST OrderSet ID]

	, CASE WHEN lastOs.ORDER_DTTM BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST OrderSet in Dept Y/N]

	, scores.*

	, firstOs.ORDER_DTTM [FIRST OrderSet Time]

	, firstOs.PRL_ORDERSET_ID [FIRST OrderSet ID]

	, CASE WHEN firstOs.ORDER_DTTM BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST OrderSet in Dept Y/N]

INTO #ODORDSET

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 sos.ORDER_DTTM

		, sos.PRL_ORDERSET_ID 

	FROM #SSOrderSet sos

	WHERE sos.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND sos.ORDER_DTTM < scores.[OD Score Time]

	ORDER BY sos.ORDER_DTTM DESC

)lastOs

OUTER APPLY

(

	SELECT TOP 1 sos.ORDER_DTTM

		, sos.PRL_ORDERSET_ID 

	FROM #SSOrderSet sos

	WHERE sos.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND sos.ORDER_DTTM >= scores.[OD Score Time]

	ORDER BY sos.ORDER_DTTM ASC

)firstOs

CREATE INDEX IDX_ODORDSET ON #ODORDSET (ENCOUNTER_ID) 

/*SELECT * FROM #ODORDSET*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

/*****************************END OF ORDER SET*****************************/



/*****************************BOLUS*****************************/

IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, mar.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, med.NAME AS Medication

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY mar.TAKEN_TIME ASC) TIME_LINE

	, mar.SIG AS BOLUS_VOLUME

INTO #BasePopBolus 

FROM #Base_Pop base

INNER JOIN [dbo].[MEDICATION_ORDERS] MO ON MO.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[MEDICATIONS] med ON med.MEDICATION_ID = MO.MEDICATION_ID

INNER JOIN [dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = MO.ORDER_MED_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE)

WHERE mar.TAKEN_TIME IS NOT NULL /*ADMINISTERED BOLUS ONLY*/

/*Developer C VCG Grouper 800009  Added 700004 */

AND (MO.MEDICATION_ID IN (SELECT * FROM #BolusMeds)

	OR (MO.MEDICATION_ID = 700004)

AND MO.HV_DISCR_FREQ_ID = '300902') /*FREQUENCY = ONCE*/

/*Developer C VCG Grouper 1222252*/

AND mar.MAR_ACTION_CODE IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

AND CONVERT(NUMERIC, mar.SIG ) > 95.0

CREATE INDEX IDX_BasePopBolus ON #BasePopBolus (ENCOUNTER_ID) 

/*SELECT * FROM #BasePopBolus*/



IF OBJECT_ID(N'tempdb..#OdboL') IS NOT NULL DROP TABLE #OdboL;

SELECT lastBol.BOLUS_ADMIN_TIME [LAST Bolus Time]

	, lastBol.Medication [LAST Bolus]

	, lastBol.BOLUS_VOLUME AS [LAST Bolus Volume]

	, lastBol.[Last Bolus to Screen Time]

	, CASE WHEN lastBol.BOLUS_ADMIN_TIME BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST Bolus Given in Dept Y/N]

	, scores.*

	, firstBol.BOLUS_ADMIN_TIME [FIRST Bolus Time]

	, firstBol.Medication [FIRST Bolus]

	, firstBol.BOLUS_VOLUME AS [FIRST Bolus Volume]

	, firstBol.[Screen Time to First Bolus]

	, CASE WHEN firstBol.BOLUS_ADMIN_TIME BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST Bolus Given in Dept Y/N]

INTO #OdboL

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 bol.BOLUS_ADMIN_TIME

		, bol.BOLUS_VOLUME

		, bol.Medication

		, DATEDIFF(MI, BOLUS_ADMIN_TIME,scores.[OD Score Time]) AS [Last Bolus to Screen Time] 

	FROM #BasePopBolus bol

	WHERE bol.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND bol.BOLUS_ADMIN_TIME < scores.[OD Score Time]

	ORDER BY bol.BOLUS_ADMIN_TIME DESC

)lastBol

OUTER APPLY

(

	SELECT TOP 1 bol.BOLUS_ADMIN_TIME

		, bol.BOLUS_VOLUME

		, bol.Medication

		, DATEDIFF(MI, scores.[OD Score Time],BOLUS_ADMIN_TIME) AS [Screen Time to First Bolus] 

	FROM #BasePopBolus bol

	WHERE bol.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND bol.BOLUS_ADMIN_TIME >= scores.[OD Score Time]

	ORDER BY bol.BOLUS_ADMIN_TIME ASC

)firstBol

CREATE INDEX IDX_OdboL ON #OdboL (ENCOUNTER_ID) 

/*SELECT * FROM #OdboL*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

/*****************************END OF BOLUS*****************************/



/*****************************CVL TIMES*****************************/

/*CVL TIME - TEST ENCOUNTER 5550010001*/

IF OBJECT_ID(N'tempdb..#ALLCVLTime') IS NOT NULL DROP TABLE #ALLCVLTime;

SELECT DISTINCT

	b.ENCOUNTER_ID

	, b.ADT_DEPARTMENT_ID

	, b.ADT_DEPARTMENT_NAME

	, b.InDepartmentTime

	, b.OutDepartmentTime

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY b.ENCOUNTER_ID, b.ADT_DEPARTMENT_ID, b.InDepartmentTime ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

INTO #ALLCVLTime

FROM #Base_Pop b

INNER JOIN [dbo].[LINE_DEVICE_AIRWAY] lda ON lda.ENCOUNTER_ID = b.ENCOUNTER_ID 

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

/*Developer C Replace this with VCG 800010*/

INNER JOIN [reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = lda.FLO_MEAS_ID

			AND cvs.VALUE_SET_ID = 3022 /*CVL CODES*/

CREATE INDEX IDX_ALLCVLTime ON #ALLCVLTime (ENCOUNTER_ID) 

/*SELECT * FROM #ALLCVLTime*/



IF OBJECT_ID(N'tempdb..#ODCVL') IS NOT NULL DROP TABLE #ODCVL;

SELECT lastCvl.PLACEMENT_INSTANT [LAST CVL Time]

	, CASE WHEN lastCvl.PLACEMENT_INSTANT BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST CVL in Dept Y/N]

	, scores.*

	, firstCVL.PLACEMENT_INSTANT [FIRST CVL Time]

	, CASE WHEN firstCVL.PLACEMENT_INSTANT BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST CVL in Dept Y/N]

INTO #ODCVL

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 cvl.PLACEMENT_INSTANT 

	FROM #ALLCVLTime cvl

	WHERE cvl.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND cvl.PLACEMENT_INSTANT < scores.[OD Score Time]

	ORDER BY cvl.PLACEMENT_INSTANT DESC

)lastCvl

OUTER APPLY

(

	SELECT TOP 1 cvl.PLACEMENT_INSTANT 

	FROM #ALLCVLTime cvl

	WHERE cvl.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND cvl.PLACEMENT_INSTANT >= scores.[OD Score Time]

	ORDER BY cvl.PLACEMENT_INSTANT ASC

)firstCVL

CREATE INDEX IDX_ODCVL ON #ODCVL (ENCOUNTER_ID) 

/*SELECT * FROM #ODCVL*/



/*****************************clean up table*****************************/

	IF OBJECT_ID(N'tempdb..#ALLCVLTime') IS NOT NULL DROP TABLE #ALLCVLTime;

/*****************************END OF CVL TIMES*****************************/



/*****************************PRESSORS TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;

SELECT DISTINCT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, mar.TAKEN_TIME

	, gmr.GROUPER_ID

	, MEDS.NAME AS MEDICATION

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY mar.TAKEN_TIME) AS TIME_LINE

INTO #Pressors 

FROM #Base_Pop base

LEFT JOIN [dbo].[MEDICATION_ORDERS] MO ON MO.ENCOUNTER_ID = base.ENCOUNTER_ID

LEFT JOIN [dbo].[MEDICATIONS] MEDS ON MEDS.MEDICATION_ID = MO.MEDICATION_ID

LEFT JOIN [dbo].GROUPER_MED_RECORDS gmr ON gmr.EXP_MEDS_LIST_ID = MEDS.MEDICATION_ID

LEFT JOIN [dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = MO.ORDER_MED_ID

LEFT JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE)

LEFT JOIN [dbo].[HOSPITAL_ENCOUNTERS] HE ON HE.ENCOUNTER_ID = base.ENCOUNTER_ID

WHERE

gmr.GROUPER_ID IN (SELECT * FROM #MedGroupers)

AND mar.MAR_ACTION_CODE IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

AND mar.ROUTE_CODE = 11 /*INTRAVENOUS*/

CREATE INDEX IDX_Pressors ON #Pressors (ENCOUNTER_ID) 

/*SELECT * FROM #Pressors*/



IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

SELECT p.ENCOUNTER_ID

	, CASE WHEN p.GROUPER_ID = '8000100'   THEN 'EPINEPHRINE' /*HS RX EPINEPHRINE SEPSIS*/

		WHEN p.GROUPER_ID =  '8000101' THEN 'DOPAMINE'

		WHEN p.GROUPER_ID = '8000102'   THEN 'DOBUTAMINE'

		WHEN p.GROUPER_ID = '8000103'   THEN 'MILRINONE'

		WHEN p.GROUPER_ID = '8000104'   THEN 'NOREPINEPHRINE'

	END PRESSOR

	, COUNT(p.TAKEN_TIME) AS MYC

INTO #ODPressorSummary

FROM #Pressors p

GROUP BY p.ENCOUNTER_ID, p.GROUPER_ID

CREATE INDEX IDX_ODPressorSummary ON #ODPressorSummary (ENCOUNTER_ID) 

/*SELECT * FROM #ODPressorSummary*/

	

/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;



IF OBJECT_ID ('TEMPDB..#ODPressorPivot') IS NOT NULL DROP TABLE #ODPressorPivot

SELECT ENCOUNTER_ID

	, pvt.[EPINEPHRINE] AS [EPINEPHRINE]

	, pvt.[DOPAMINE] AS [DOPAMINE]

	, pvt.[DOBUTAMINE] AS [DOBUTAMINE]

	, pvt.[MILRINONE] AS [MILRINONE]

	, pvt.[NOREPINEPHRINE] AS [NOREPINEPHRINE]

INTO #ODPressorPivot

FROM #ODPressorSummary p

PIVOT( MAX(myc)

FOR PRESSOR IN ([EPINEPHRINE],[DOPAMINE],[DOBUTAMINE],[MILRINONE],[NOREPINEPHRINE])) AS pvt

CREATE INDEX IDX_ODPressorPivot ON #ODPressorPivot (ENCOUNTER_ID) 

/*SELECT * FROM #ODPressorPivot*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

/*****************************END OF PRESSORS TIMES*****************************/



/*****************************SVO2 TIMES*****************************/

IF OBJECT_ID(N'tempdb..#SVO2') IS NOT NULL DROP TABLE #SVO2;

SELECT base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, PO.ORDER_TIME AS SVO2OrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY PO.ORDER_TIME ASC) AS TIME_LINE

	, ordR.ORDER_PROC_ID

INTO #SVO2

FROM #Base_Pop base

	INNER JOIN [dbo].[LAB_ORDER_RESULTS] ordR ON base.ENCOUNTER_ID = ordR.ENCOUNTER_ID

	INNER JOIN [dbo].[PROCEDURE_ORDERS] PO ON PO.ORDER_PROC_ID = ordR.ORDER_PROC_ID

WHERE ordR.COMPONENT_ID IN (5000001861, 5000000478)

CREATE INDEX IDX_SVO2 ON #SVO2 (ENCOUNTER_ID) 

/*SELECT * FROM #SVO2*/



IF OBJECT_ID(N'tempdb..#ODSVO2') IS NOT NULL DROP TABLE #ODSVO2;

SELECT lastSVO2.SVO2OrderTime [LAST SVO2 Time]

	, CASE WHEN lastSVO2.SVO2OrderTime BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST SVO2 in Dept Y/N]

	, scores.*

	, firstSVO2.SVO2OrderTime [FIRST SVO2 Time]

	, CASE WHEN firstSVO2.SVO2OrderTime BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST SVO2 in Dept Y/N]

INTO #ODSVO2

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 SVO2.SVO2OrderTime 

	FROM #SVO2 SVO2

	WHERE SVO2.ENCOUNTER_ID = scores.ENCOUNTER_ID AND SVO2.SVO2OrderTime < scores.[OD Score Time]

	ORDER BY SVO2.SVO2OrderTime DESC

) lastSVO2

OUTER APPLY

(

	SELECT TOP 1 SVO2.SVO2OrderTime FROM #SVO2 SVO2

	WHERE SVO2.ENCOUNTER_ID = scores.ENCOUNTER_ID AND SVO2.SVO2OrderTime >= scores.[OD Score Time]

	ORDER BY SVO2.SVO2OrderTime ASC

)firstSVO2

CREATE INDEX IDX_ODSVO2 ON #ODSVO2 (ENCOUNTER_ID) 

/*SELECT * FROM #ODSVO2*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#SVO2') IS NOT NULL DROP TABLE #SVO2;

/*****************************END OF SVO2 TIMES*****************************/



/*****************************LACTIC ACID TIMES*****************************/

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, PO.ORDER_PROC_ID

	, PO.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY PO.ORDER_TIME, base.InDepartmentTime, ordR.RESULT_TIME ASC) AS TIME_LINE -- Developer C added Result time

INTO #LacticAcid

FROM #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] ordR ON ordR.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO ON PO.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID IN (SELECT * FROM #LacticAcidLRR)

CREATE INDEX IDX_LacticAcid ON #LacticAcid (ENCOUNTER_ID) 

/*SELECT * FROM #LacticAcid */



IF OBJECT_ID(N'tempdb..#ODLA') IS NOT NULL DROP TABLE #ODLA;

SELECT lastLA.MBOrderTime [LAST LacticAcid Order Time]

	, lastLA.ORD_VALUE AS [LAST LacticAcid Result]

	, CASE WHEN lastLA.MBOrderTime BETWEEN base.InDepartmentTime AND base.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST LacticAcid in Dept Y/N]

	, base.*

	, firstLA.MBOrderTime [FIRST LacticAcid Order Time]

	, firstLA.ORD_VALUE AS [FIRST LacticAcid Result]

	, CASE WHEN firstLA.MBOrderTime BETWEEN base.InDepartmentTime AND base.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST LacticAcid in Dept Y/N]

INTO #ODLA

FROM #Base_Pop_OD_Scores base

OUTER APPLY

(

	SELECT TOP 1 lacA.MBOrderTime

		, lacA.ORD_VALUE 

	FROM #LacticAcid lacA

	WHERE lacA.ENCOUNTER_ID = base.ENCOUNTER_ID 

	AND lacA.MBOrderTime < base.[OD Score Time]

	ORDER BY lacA.RESULT_TIME DESC

)lastLA

OUTER APPLY

(

	SELECT TOP 1 lacA.MBOrderTime

		, lacA.ORD_VALUE 

	FROM #LacticAcid lacA

	WHERE lacA.ENCOUNTER_ID = base.ENCOUNTER_ID 

	AND lacA.MBOrderTime >= base.[OD Score Time]

	ORDER BY lacA.RESULT_TIME ASC

)firstLA

CREATE INDEX IDX_ODLA ON #ODLA(ENCOUNTER_ID)

/*SELECT * FROM #ODLA ORDER BY TIME_LINE*/

 

/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

/*****************************END OF LACTIC ACID TIMES*****************************/



/*****************************PROCALCITONIN TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, PO.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY PO.ORDER_TIME ASC) AS TIME_LINE

	, ordR.ORDER_PROC_ID

INTO #Procalcitonin

FROM  #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] ordR ON ordR.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO ON PO.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID = 500001 /*COULD USE PROC CODE ALSO.... LAB014*/

CREATE INDEX IDX_Procalcitonin ON #Procalcitonin (ENCOUNTER_ID) 

/*SELECT * FROM #Procalcitonin*/



IF OBJECT_ID(N'tempdb..#ODPROCAL') IS NOT NULL DROP TABLE #ODPROCAL;

SELECT lastPro.MBOrderTime [LAST Procalcitonin Order Time]

	, lastPro.ORD_VALUE AS [LAST Procalcitonin Result]

	, CASE WHEN lastPro.MBOrderTime BETWEEN base.InDepartmentTime AND base.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST Procalcitonin in Dept Y/N]

	, base.*

	, firstPro.MBOrderTime [FIRST Procalcitonin Order Time]

	, firstPro.ORD_VALUE AS [FIRST Procalcitonin Result]

	, CASE WHEN firstPro.MBOrderTime BETWEEN base.InDepartmentTime AND base.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST Procalcitonin in Dept Y/N]

INTO #ODPROCAL

FROM #Base_Pop_OD_Scores base

OUTER APPLY

(

	SELECT TOP 1 procal.MBOrderTime

		, procal.ORD_VALUE 

	FROM #Procalcitonin procal

	WHERE procal.ENCOUNTER_ID = base.ENCOUNTER_ID 

	AND procal.MBOrderTime < base.[OD Score Time]

	ORDER BY procal.MBOrderTime DESC

)lastPro

OUTER APPLY

(

	SELECT TOP 1 procal.MBOrderTime

		, procal.ORD_VALUE 

	FROM #Procalcitonin procal

	WHERE procal.ENCOUNTER_ID = base.ENCOUNTER_ID 

	AND procal.MBOrderTime >= base.[OD Score Time]

	ORDER BY procal.MBOrderTime ASC

)firstPro

CREATE INDEX IDX_ODPROCAL ON #ODPROCAL (ENCOUNTER_ID) 

/*SELECT * FROM #ODPROCAL*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

/*****************************END OF PROCALCITONIN TIMES*****************************/



/*****************************BLOOD CULTURE TIMES*****************************/

/*Blood Culture*/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

SELECT base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, PO.ORDER_PROC_ID

	, PCAT.PROC_CODE AS [Blood Culture Procedure Ordered]

	, PO.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY PO.ORDER_TIME, res.RESULT_TIME ASC) AS TIME_LINE

INTO #BloodCultureValue 

FROM #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] res ON base.ENCOUNTER_ID = res.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO  ON res.ORDER_PROC_ID = PO.ORDER_PROC_ID 

			AND PO.PROC_ID IN (SELECT * FROM #BloodCultures)

INNER JOIN [dbo].[PROCEDURES_CATALOG] PCAT ON PCAT.PROC_ID = PO.PROC_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

CREATE INDEX IDX_BloodCultureValue ON #BloodCultureValue (ENCOUNTER_ID) 

/*SELECT * FROM #BloodCultureValue*/



IF OBJECT_ID(N'tempdb..#ODBC') IS NOT NULL DROP TABLE #ODBC;

SELECT lastbc.MBOrderTime [LAST Blood Culture Order Time]

	, lastbc.[Blood Culture Procedure Ordered] AS [LAST Blood Culture Procedure Ordered]

	, lastbc.ORD_VALUE [LAST Blood Culture Result]

	, CASE WHEN lastbc.MBOrderTime BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST Blood Culture in Dept Y/N]

	, scores.*

	, firstbc.MBOrderTime [FIRST Blood Culture Order Time]

	, firstbc.[Blood Culture Procedure Ordered] AS [FIRST Blood Culture Procedure Ordered]

	, firstbc.ORD_VALUE [FIRST Blood Culture Result]

	, CASE WHEN firstbc.MBOrderTime BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST Blood Culture in Dept Y/N]

INTO #ODBC

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 bc.[Blood Culture Procedure Ordered]

		, bc.MBOrderTime

		, bc.ORD_VALUE 

	FROM #BloodCultureValue bc

	WHERE bc.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND bc.RESULT_TIME < scores.[OD Score Time]

	ORDER BY bc.MBOrderTime DESC, bc.RESULT_TIME DESC

)lastbc

OUTER APPLY

(

	SELECT TOP 1 bc.[Blood Culture Procedure Ordered]

		, bc.MBOrderTime

		, bc.ORD_VALUE 

	FROM #BloodCultureValue bc

	WHERE bc.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND bc.RESULT_TIME >= scores.[OD Score Time]

	ORDER BY bc.MBOrderTime ASC, bc.RESULT_TIME ASC

)firstbc

CREATE INDEX IDX_ODBC ON #ODBC (ENCOUNTER_ID) 

/*SELECT * FROM #ODBC*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

/*****************************END OF BLOOD CULTURE TIMES*****************************/



/*****************************CSF TIMES*****************************/

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, PO.ORDER_PROC_ID

	, PCAT.PROC_CODE as [CSF Procedure Ordered]

	, PO.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY PO.ORDER_TIME ASC) AS TIME_LINE

INTO #CSF 

FROM #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] res ON base.ENCOUNTER_ID = res.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO  ON res.ORDER_PROC_ID = PO.ORDER_PROC_ID

			AND PROC_ID IN (600005, 600006) AND PO.SPECIMEN_SOURCE_CODE = 304

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

INNER JOIN [dbo].[PROCEDURES_CATALOG] PCAT ON PCAT.PROC_ID = PO.PROC_ID

CREATE INDEX IDX_CSF ON #CSF (ENCOUNTER_ID) 

/*SELECT * FROM #CSF*/



IF OBJECT_ID(N'tempdb..#ODCSF') IS NOT NULL DROP TABLE #ODCSF;

SELECT lastCF.MBOrderTime [LAST CSF Order Time]

	, lastCF.[CSF Procedure Ordered] AS [LAST CSF Ordered]

	, CASE WHEN lastCF.MBOrderTime BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST CSF in Dept Y/N]

	, scores.*

	, firstCF.MBOrderTime [FIRST CSF Order Time]

	, firstCF.[CSF Procedure Ordered] AS [FIRST CSF Ordered]

	, CASE WHEN firstCF.MBOrderTime BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST CSF in Dept Y/N]

INTO #ODCSF

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 csf.[CSF Procedure Ordered]

		, csf.MBOrderTime 

	FROM #CSF csf

	WHERE csf.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND csf.MBOrderTime < scores.[OD Score Time]

	ORDER BY csf.MBOrderTime DESC

)lastCF

OUTER APPLY

(

	SELECT TOP 1 csf.[CSF Procedure Ordered]

		, csf.MBOrderTime 

		FROM #CSF csf

	WHERE csf.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND csf.MBOrderTime >= scores.[OD Score Time]

	ORDER BY csf.MBOrderTime ASC

)firstCF

CREATE INDEX IDX_ODCSF ON #ODCSF (ENCOUNTER_ID) 

/*SELECT * FROM #ODCSF*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

/*****************************END OF CSF TIMES*****************************/



/*****************************ETT TIMES*****************************/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

SELECT base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

INTO #ETT

FROM #Base_Pop base

INNER JOIN [dbo].[LINE_DEVICE_AIRWAY] lda ON lda.ENCOUNTER_ID = base.ENCOUNTER_ID AND lda.FLO_MEAS_ID = '900112' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

CREATE INDEX IDX_ETT ON #ETT (ENCOUNTER_ID) 

/*SELECT * FROM #ETT WHERE TIME_LINE = 1*/



IF OBJECT_ID(N'tempdb..#ODETT') IS NOT NULL DROP TABLE #ODETT;

SELECT lastETT.PLACEMENT_INSTANT [LAST Intubation Time]

	, CASE WHEN lastETT.PLACEMENT_INSTANT BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST ETT in Dept Y/N]

	, scores.*

	, firstETT.PLACEMENT_INSTANT [FIRST Intubation Time]

	, CASE WHEN firstETT.PLACEMENT_INSTANT BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST ETT in Dept Y/N]

INTO #ODETT

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 ett.PLACEMENT_INSTANT 

	FROM #ETT ett

	WHERE ett.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND ett.PLACEMENT_INSTANT < scores.[OD Score Time]

	ORDER BY ett.PLACEMENT_INSTANT DESC

)lastETT

OUTER APPLY

(

	SELECT TOP 1 ett.PLACEMENT_INSTANT 

	FROM #ETT ett

	WHERE ett.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND ett.PLACEMENT_INSTANT >= scores.[OD Score Time]

	ORDER BY ett.PLACEMENT_INSTANT ASC

)firstETT

CREATE INDEX IDX_ODETT ON #ODETT (ENCOUNTER_ID) 

/*SELECT * FROM #ODETT*/



/*****************************clean up temp table*****************************/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

/*****************************END OF ETT TIMES*****************************/



/*****************************PIV TIMES*****************************/

IF OBJECT_ID(N'tempdb..#PIV') IS NOT NULL DROP TABLE #PIV;

SELECT base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

INTO #PIV

FROM #Base_Pop base

INNER JOIN [dbo].[LINE_DEVICE_AIRWAY] lda ON lda.ENCOUNTER_ID = base.ENCOUNTER_ID AND lda.FLO_MEAS_ID='900111' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

CREATE INDEX IDX_PIV ON #PIV (ENCOUNTER_ID) 

/*SELECT * FROM #PIV WHERE TIME_LINE = 1*/



IF OBJECT_ID(N'tempdb..#ODPIV') IS NOT NULL DROP TABLE #ODPIV;

SELECT lastPIV.PLACEMENT_INSTANT [LAST PIV Before Screen]

	, CASE WHEN lastPIV.PLACEMENT_INSTANT BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [LAST PIV in Dept Y/N]

	, scores.*

	, firstPIV.PLACEMENT_INSTANT [FIRST PIV After Screen]

	, CASE WHEN firstPIV.PLACEMENT_INSTANT BETWEEN scores.InDepartmentTime AND scores.OutDepartmentTime THEN 'Y' ELSE 'N' END AS [FIRST PIV in Dept Y/N]

INTO #ODPIV

FROM #Base_Pop_OD_Scores scores

OUTER APPLY

(

	SELECT TOP 1 piv.PLACEMENT_INSTANT 

	FROM #PIV piv

	WHERE piv.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND piv.PLACEMENT_INSTANT < scores.[OD Score Time]

	ORDER BY PIV.PLACEMENT_INSTANT DESC

)lastPIV

OUTER APPLY

(

	SELECT TOP 1 PIV.PLACEMENT_INSTANT 

	FROM #PIV piv

	WHERE piv.ENCOUNTER_ID = scores.ENCOUNTER_ID 

	AND piv.PLACEMENT_INSTANT >= scores.[OD Score Time]

	ORDER BY PIV.PLACEMENT_INSTANT ASC

)firstPIV

CREATE INDEX IDX_ODPIV ON #ODPIV (ENCOUNTER_ID) 

/*SELECT * FROM #ODPIV */



/*****************************clean up temp table*****************************/

IF OBJECT_ID(N'tempdb..#PIV') IS NOT NULL DROP TABLE #PIV;

/*****************************END OF PIV TIMES*****************************/



/*****************************PROPHYLAXIS*****************************/

IF OBJECT_ID(N'tempdb..#PROPHYLAXIS') IS NOT NULL DROP TABLE #PROPHYLAXIS;

WITH FlwshtProp AS

(

SELECT meas.FSD_ID

	, meas.Recorded_Time

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID

/*Developer C VCG Grouper 800014 (SELECT * FROM #ProphylaxisFLO)*/

WHERE FLO_MEAS_ID IN ('9000613042','9000613043','9000613044','9000613045','9000613047','9000613048','9000613050')

AND RECORDED_TIME IS NOT NULL

)

/*SELECT * FROM FlwshtProp*/



SELECT base.ENCOUNTER_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS PROPHYLAXIS_FLAG

	, base.[ENC_ID Overall Order]

INTO #PROPHYLAXIS

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN FlwshtProp meas ON meas.FSD_ID = rec.FSD_ID

GROUP BY base.ENCOUNTER_ID, base.[ENC_ID Overall Order]

CREATE INDEX IDX_PROPHYLAXIS ON #PROPHYLAXIS (ENCOUNTER_ID) 

/*SELECT * FROM #PROPHYLAXIS*/

/*****************************END OF PROPHYLAXIS*****************************/



/*****************************CVVH*****************************/

IF OBJECT_ID(N'tempdb..#CVVH') IS NOT NULL DROP TABLE #CVVH;

SELECT base.ENCOUNTER_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS CVVH_FLAG

	, base.[ENC_ID Overall Order]

INTO #CVVH

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID AND meas.FLT_ID='9000001359'--ANY FLOWSHEET FROM THIS TEMPLATE IS A CANDIDATE

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

GROUP BY base.ENCOUNTER_ID, base.[ENC_ID Overall Order]

CREATE INDEX IDX_CVVH ON #CVVH (ENCOUNTER_ID) 

/*SELECT * FROM #CVVH*/

/*****************************END OF CVVH*****************************/



/*****************************CEREBRAL OX MONITORING*****************************/

IF OBJECT_ID(N'tempdb..#OX') IS NOT NULL DROP TABLE #OX;

SELECT base.ENCOUNTER_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS OX_FLAG

	, base.[ENC_ID Overall Order]

INTO #OX

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

/* Developer C VCG Grouper 800015*/

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

AND meas.FLO_MEAS_ID IN ('900201', '900202', '900203', '9000001977') /*(SELECT * FROM #CerebralOxFLO)*/

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

GROUP BY base.ENCOUNTER_ID, base.[ENC_ID Overall Order]

CREATE INDEX IDX_OX ON #OX (ENCOUNTER_ID) 

/*SELECT * FROM #OX*/

/*****************************END OF CEREBRAL OX MONITORING*****************************/



/*****************************ECMO*****************************/

IF OBJECT_ID(N'tempdb..#ECMO') IS NOT NULL DROP TABLE #ECMO;

SELECT base.ENCOUNTER_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS ECMO_FLAG

	, base.[ENC_ID Overall Order]

INTO #ECMO

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

	AND meas.FLO_MEAS_ID ='9000101014' /*9000101014	R ECMO ON/OFF*/

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

GROUP BY base.ENCOUNTER_ID, base.[ENC_ID Overall Order]

CREATE INDEX IDX_ECMO ON #ECMO (ENCOUNTER_ID) 

/*SELECT * FROM #ECMO*/

/*****************************END OF ECMO*****************************/



/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SEPSIS]

	(

		[PatientName],

		[PATIENTMRN],

		[EthnicGroup],

		[Race],

		[Location],

		[PATENCENCID],

		[AgeMonths],

		[AgeYears],

		[InpAdmDate],

		[HospDischTime],

		[Disposition],

		[LosHours],

		[ShiftDate],

		[ShiftAMPM],

		[ShiftStart], 

		[ShiftEnd],

		[EncounterDiagnoses],

		[LastHypotensionTime],

		[LastHypotensionValue],

		[LastHypotensionTakenInDeptYN],

		[FirstHypotensionTime],

		[FirstHypotensionValue],

		[FirstHypotensionTakenInDeptYN],

		[EncounterWeight],

		[FirstPositiveScoreInED],

		[FirstPositiveScoreTimeInED],

		[EDLosHours],

		[ADTDepartmentName],

		[DepartmentRollup],

		[InDepartmentTime],

		[OutDepartmentTime],

		[ODScore],

		[ScoreTime],

		[ShiftComplianceFlag],

		[ShiftCompliance],

		[ShiftColor],

		[ShiftColorDisplay],

		[SepsisPatientHuddleorAlertWithMDPNP],

		[HuddleDate],

		[HuddleTime],

		[PatientAssessedByMDPNP],

		[PhysicianName],

		[AddOrdersReceivedPlacedByMDPNP],

		[LastABXTime],

		[LastABXName],

		[LastABXToODScoreVolume],

		[LastABXToODScoreTime],

		[LastABXGivenInDeptYN],

		[FirstABXTime],

		[FirstABXName],

		[FirstABXVolume],

		[ODScoreToFirstABXTime],

		[FirstABXGivenInDeptYN],

		[ABXYN],

		[LastBolusTime],

		[LastBolus],

		[LastBolusVolume],

		[LastBolusToScreenTime],

		[LastBolusGivenInDeptYN],

		[FirstBolusTime],

		[FirstBolus],

		[FirstBolusVolume],

		[ScreenTimeToFirstBolus],

		[FirstBolusGivenInDeptYN],

		[BolusYN],

		[LastLacticAcidOrderTime],

		[LastLacticAcidResult],

		[LastLacticAcidInDeptYN],

		[FirstLacticAcidOrderTime],

		[FirstLacticAcidResult],

		[FirstLacticActidInDeptYN],

		[LacticAcidYN],

		[LastOrderSetTime],

		[LastOrderSetID],

		[LastOrderSetInDeptYN],

		[FirstOrderSetTime],

		[FirstOrderSetID],

		[FirstOrderSetInDeptYN],

		[LastCVLTime],

		[LastCVLInDeptYN],

		[FirstCVLTime],

		[FirstCVLInDeptYN],

		[CVLYN],

		[LastSVO2Time],

		[LastSVO2InDeptYN],

		[FirstSVO2Time],

		[FirstSVO2InDeptYN],

		[SVO2YN],

		[LastProcalcitoninOrderTime],

		[LastProcalcitoninResult],

		[LastProcalcitoninInDeptYN],

		[FirstProcalcitoninOrderTime],

		[FirstProcalcitoninResult],

		[FirstProcalcitoninInDeptYN],

		[ProcalcitoninYN],

		[LastBloodCultureOrderTime],

		[LastBloodCultureProcedureOrdered],

		[LastBloodCultureResult],

		[LastBloodCultureInDeptYN],

		[FirstBloodCultureOrderTime],

		[FirstBloodCultureProcedureOrdered],

		[FirstBloodCultureResult],

		[FirstBloodCultureInDeptYN],

		[BloodCultureYN],

		[LastCSFOrderTime],

		[LastCSFOrdered],

		[LastCSFInDeptYN],

		[FirstCSFOrderTime],

		[FirstCSFOrdered],

		[FirstCSFInDeptYN],

		[CSFYN],

		[LastPIVBeforeScreen],

		[LastPIVInDeptYN],

		[FirstPIVAfterScreen],

		[FirstPIVInDeptYN],

		[PIVYN],

		[LastIntubationTime],

		[LastETTInDeptYN],

		[FirstIntubationTime],

		[FirstETTInDeptYN],

		[ETTYN],

		[DobutamineYN],

		[DopamineYN],

		[EpinephrineYN],

		[MilrinoneYN],

		[NorepinephrineYN],

		[PressorYN],

		[DvtprophylaxisYN],

		[CVVHYN],

		[OXYN],

		[ECMOYN],

		[IPSOSevereSepsisYN],

		[AlertNotActivatedReason],

		[AlertNotActivatedComment],

		[AlertActivatedComment],

		[FY],

		[FYMonthNumber],

		[FYMonthName],

		[FYYear],

		[FYMonthShortName],

		[FYDate],

		[ShiftRNs],

		[ShiftCNs],

		[NoteAuthor],

		[NoteCreatedTime],

		[FifteenthOrEOM],

		[PositiveODScore],

		[ENCORDER], 

		[UnitOrder], 

		[ENCOVERALLORDER],

		[AMDenom],

		[PMDenom],

		[Denominator],

		[InRecord],

		[OutRecord],

		[Predisposition],

		[InfectiousSymptoms],

		[HematologicDysfunction],

		[RenalDysfunction],

		[NeurologicalDysfunction],

		[RespiratoryDysfunction],

		[Pulse],

		[Resp],

		[BP],

		[PerfusionWDL],

		[RBrachialPulse],

		[LBrachialPulse],

		[RRadialPulse],

		[LRadialPulse],

		[RPosteriorTibialPulse],

		[LPosteriorTibialPulse],

		[RPedalPulse],

		[LPedalPulse],

		[CapillaryRefill],

		[SkinColor],

		[SkinConditionTemp],

		[ExternalLactateResult],

		[ExternalCreatinine],

		[ExternalPlatelets],

		[Notification],

		[UniqueRow],

		[RefreshDate])

SELECT main.PATIENT_NAME [PATIENTS]

	, main.PATIENT_MRN [MRN]

	, main.[Ethnic Group]

	, main.[Race]

	, main.[Location]

	, main.ENCOUNTER_ID [ENC_ID]

	, main.AGE_MONTHS [Age (M)]

	, main.AGE_YEARS[Age (Y)]

	, main.INP_ADM_DATE [Admit Time]

	, main.HOSP_DISCH_TIME [Disch Time]

	, main.Disposition

	, main.LOS_HRS [LOS (Hrs)]

	, bp.[Score Date]

	, bp.[Shift AM/PM]

	, bp.[Shift Start]

	, bp.[Shift End]

	, encRsn.AllEncReasons AS [Encounter Diagnoses]

	, hypo.[LAST Hypotension Time]

	, hypo.[LAST Hypotension Value]

	, hypo.[LAST Hypotension taken in Dept Y/N]

	, hypo.[FIRST Hypotension Time]

	, hypo.[FIRST Hypotension Value]

	, hypo.[FIRST Hypotension taken in Dept Y/N]

	, wght.EncWeight

	, edLOS.MEAS_VALUE [First Positive Score in ED]

	, edLOS.RECORDED_TIME AS [First Positive Score Time in ED]

	, edLOS.HoursInED AS [ED LOS (Hrs)]

	, bp.ADT_DEPARTMENT_NAME [Department]

	, bp.DEPARTMENT_ROLLUP [Department Rollup]

	, bp.InDepartmentTime [In Department Time]

	, bp.OutDepartmentTime [Out Department Time]

	, scores.[OD Score]

	, scores.[OD Score Time]



	, CASE WHEN scores.[OD Score] IS NULL THEN 'N' ELSE 'Y' END [Shift Compliance Y/N]

	, CASE WHEN scores.[OD Score] IS NULL THEN 0 ELSE 1 END [Shift Compliance]

	, CASE WHEN scores.[OD Score] IS NULL THEN 'RED' ELSE 'GREEN' END [Shift Color]

	, CASE WHEN scores.[OD Score] IS NULL THEN '#FD625E' ELSE '#73B761' END [Shift Color Display]



	, scores.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP]

	, scores.[Huddle Date]

	, scores.[Huddle Time]

	, scores.[PATIENTS Assessed by MD/PNP]

	, scores.[Physician Name]

	, scores.[Additional Orders Received/Placed by MD/PNP]

	, abx.LASTABX_TIME [LAST ABX Time]

	, abx.LASTABX_NAME [LAST ABX Name]

	, abx.[LAST ABX Volume]

	, abx.[Last ABX to OD Score Time]

	, abx.[LAST ABX Given in Dept Y/N]

	, abx.FIRSTABX_TIME [FIRST ABX Time]

	, abx.FIRSTABX_NAME [FIRST ABX Name]

	, abx.[FIRST ABX Volume]

	, abx.[OD Score to First ABX Time]

	, abx.[FIRST ABX Given in Dept Y/N]

	, CASE WHEN (abx.LASTABX_TIME IS NOT NULL OR abx.FIRSTABX_TIME IS NOT NULL) THEN 'Y' ELSE 'N' END AS [ABX Y/N]

	, bol.[LAST Bolus Time]

	, bol.[LAST Bolus]

	, bol.[LAST Bolus Volume]

	, bol.[Last Bolus to Screen Time]

	, bol.[LAST Bolus Given in Dept Y/N]

	, bol.[FIRST Bolus Time]

	, bol.[FIRST Bolus]

	, bol.[FIRST Bolus Volume]

	, bol.[Screen Time to First Bolus]

	, bol.[FIRST Bolus Given in Dept Y/N]

	, CASE WHEN (bol.[LAST Bolus Time] IS NOT NULL OR bol.[FIRST Bolus Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [BOLUS Y/N]

	, la.[LAST LacticAcid Order Time]

	, la.[LAST LacticAcid Result]

	, la.[LAST LacticAcid in Dept Y/N]

	, la.[FIRST LacticAcid Order Time]

	, la.[FIRST LacticAcid Result]

	, la.[FIRST LacticAcid in Dept Y/N]

	, CASE WHEN (la.[LAST LacticAcid Order Time] IS NOT NULL OR la.[FIRST LacticAcid Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS LACTICACID_FLAG

	, ordSet.[LAST OrderSet Time]

	, ordSet.[LAST OrderSet ID]

	, ordSet.[LAST OrderSet in Dept Y/N]

	, ordSet.[FIRST OrderSet Time]

	, ordSet.[FIRST OrderSet ID]

	, ordSet.[FIRST OrderSet in Dept Y/N]

	, cvl.[LAST CVL Time]

	, cvl.[LAST CVL in Dept Y/N]

	, cvl.[FIRST CVL Time]

	, cvl.[FIRST CVL in Dept Y/N]

	, CASE WHEN (cvl.[LAST CVL Time] IS NOT NULL OR cvl.[FIRST CVL Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [CVL Y/N]

	, svo2.[LAST SVO2 Time]

	, svo2.[LAST SVO2 in Dept Y/N]

	, svo2.[FIRST SVO2 Time]

	, svo2.[FIRST SVO2 in Dept Y/N]

	, CASE WHEN (svo2.[LAST SVO2 Time] IS NOT NULL OR svo2.[FIRST SVO2 Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [SVO2 Y/N]

	, proCal.[LAST Procalcitonin Order Time]

	, proCal.[LAST Procalcitonin Result]

	, proCal.[LAST Procalcitonin in Dept Y/N]

	, proCal.[FIRST Procalcitonin Order Time]

	, proCal.[FIRST Procalcitonin Result]

	, proCal.[FIRST Procalcitonin in Dept Y/N]

	, CASE WHEN (proCal.[LAST Procalcitonin Order Time] IS NOT NULL OR proCal.[FIRST Procalcitonin Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [Procalcitonin Y/N]

	, bc.[LAST Blood Culture Order Time]

	, bc.[LAST Blood Culture Procedure Ordered]

	, bc.[LAST Blood Culture Result]

	, bc.[LAST Blood Culture in Dept Y/N]

	, bc.[FIRST Blood Culture Order Time]

	, bc.[FIRST Blood Culture Procedure Ordered]

	, bc.[FIRST Blood Culture Result]

	, bc.[FIRST Blood Culture in Dept Y/N]

	, CASE WHEN (bc.[LAST Blood Culture Order Time] IS NOT NULL OR bc.[FIRST Blood Culture Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [BloodCulture Y/N]

	, csf.[LAST CSF Order Time]

	, csf.[LAST CSF Ordered]

	, csf.[LAST CSF in Dept Y/N]

	, csf.[FIRST CSF Order Time]

	, csf.[FIRST CSF Ordered]

	, csf.[FIRST CSF in Dept Y/N]

	, CASE WHEN (csf.[LAST CSF Order Time] IS NOT NULL OR csf.[FIRST CSF Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [CSF Y/N]

	, piv.[LAST PIV Before Screen]

	, piv.[LAST PIV in Dept Y/N]

	, piv.[FIRST PIV After Screen]

	, piv.[FIRST PIV in Dept Y/N]

	, CASE WHEN (piv.[LAST PIV Before Screen] IS NOT NULL OR piv.[FIRST PIV After Screen] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [PIV Y/N]

	, ett.[LAST Intubation Time]

	, ett.[LAST ETT in Dept Y/N]

	, ett.[FIRST Intubation Time]

	, ett.[FIRST ETT in Dept Y/N]

	, CASE WHEN (ett.[LAST Intubation Time] IS NOT NULL OR ett.[FIRST Intubation Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS [ETT Y/N]

	, CASE WHEN pressor.DOBUTAMINE IS NULL THEN 'N' ELSE 'Y' END DOBUTAMINE

	, CASE WHEN pressor.DOPAMINE IS NULL THEN 'N' ELSE 'Y' END DOPAMINE

	, CASE WHEN pressor.EPINEPHRINE IS NULL THEN 'N' ELSE 'Y' END EPINEPHRINE

	, CASE WHEN pressor.MILRINONE IS NULL THEN 'N' ELSE 'Y' END MILRINONE

	, CASE WHEN pressor.NOREPINEPHRINE IS NULL THEN 'N' ELSE 'Y' END NOREPINEPHRINE

	, CASE WHEN (

				pressor.DOBUTAMINE IS NOT NULL OR

				pressor.DOPAMINE IS NOT NULL OR

				pressor.EPINEPHRINE IS NOT NULL OR

				pressor.MILRINONE IS NOT NULL OR

				pressor.NOREPINEPHRINE IS NOT NULL) THEN 'Y' ELSE 'N' END AS [PRESSOR Y/N]

	, COALESCE(prophy.PROPHYLAXIS_FLAG,'N') AS [DVTPROPHYLAXIS Y/N]

	, COALESCE(cvvh.CVVH_FLAG,'N') AS [CVVH Y/N]

	, COALESCE(ox.OX_FLAG,'N') AS [OX Y/N]

	, COALESCE(ecmo.ECMO_FLAG,'N') AS [ECMO Y/N]



	, CASE WHEN SSS.ENCOUNTER_ID IS NULL THEN 'N' ELSE 'Y' END SEVERE_SEPSIS_STAGING

	

	, scores.[CLINICAL_ALERTS Not Activated Reason]

	, scores.[CLINICAL_ALERTS Not Activated Comment]

	, scores.[CLINICAL_ALERTS Activated Comment]



	, fyDate.HS_FY [FY]

	, fyDate.HS_FY_MONTH_NUMBER [FY Month #]

	, fyDate.MONTH_NAME [FY Month]

	, fyDate.HS_FY [FY Year]

	, LEFT(fyDate.MONTH_NAME, 3 ) AS [FY Month Short Name]

	, fyDate.CALENDAR_DT [FY Date]

	, ShiftRNs.[Shift RNs]

	, ShiftCNs.[Shift CNs]

	, sepsisAlert.[Note Author]

	, sepsisAlert.[Note Created Time]

	, CASE WHEN fyDate.DAY_OF_MONTH = 15 OR fyDate.MONTH_END_DT = scores.[Score Day] THEN 'True' ELSE 'False' END AS [15th or EOM]

	, CASE WHEN scores.[OD Score] > 2 THEN 1 ELSE 0 END [Positive OD Score]

	, bp.[ENC_ID Order]

	, bp.[Unit Order]

	, bp.[ENC_ID Overall Order]

	, bp.[AM Denom]

	, bp.[PM Denom]

	, CASE WHEN [Shift AM/PM] like 'AM%' THEN [AM Denom] ELSE [PM Denom] END [Denominator]

	, bp.[In Record]

	, bp.[Out Record]

	, sepsisAudit.[Predisposition]

	, sepsisAudit.[Infectious Symptoms]

	, sepsisAudit.[Hematologic Dysfunction]

	, sepsisAudit.[Renal Dysfunction]

	, sepsisAudit.[Neurological Dysfunction]

	, sepsisAudit.[Respiratory Dysfunction]

	, sepsisAudit.[Pulse]

	, sepsisAudit.[Resp]

	, sepsisAudit.[BP]

	, sepsisAudit.[Perfusion (WDL)]

	, sepsisAudit.[R Brachial Pulse]

	, sepsisAudit.[L Brachial Pulse]

	, sepsisAudit.[R Radial Pulse]

	, sepsisAudit.[L Radial Pulse]

	, sepsisAudit.[R Posterior Tibial Pulse]

	, sepsisAudit.[L Posterior Tibial Pulse]

	, sepsisAudit.[R Pedal Pulse]

	, sepsisAudit.[L Pedal Pulse]

	, sepsisAudit.[Capillary Refill]

	, sepsisAudit.[Skin Color]

	, sepsisAudit.[Skin Condition/Temp]

	, sepsisAudit.[External Lactate Result (mmol/L)]

	, sepsisAudit.[External Creatinine (mg/dL)]

	, sepsisAudit.[External Platelets (x 1000/uL)]

	, sepsisAudit.[Notification]

	, CAST(bp.ENCOUNTER_ID AS varchar(20)) + '-' + CAST(bp.[ENC_ID Order] AS VARCHAR(95)) [Unique Row]

	, GETDATE()

FROM #MainAdmDetails main  

INNER JOIN #Base_Pop bp ON bp.ENCOUNTER_ID = main.ENCOUNTER_ID

INNER JOIN #Base_Pop_OD_Scores scores ON scores.ENCOUNTER_ID = bp.ENCOUNTER_ID AND scores.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

INNER JOIN reports.FY_DATE_DIMENSION fyDate ON fyDate.CALENDAR_DT = bp.[Score Date] 

LEFT OUTER JOIN #Base_Pop_ENC_Reason encRsn ON encRsn.ENCOUNTER_ID = main.ENCOUNTER_ID

LEFT OUTER JOIN #EncounterWeights wght ON wght.ENCOUNTER_ID = main.ENCOUNTER_ID AND wght.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODHYPO hypo ON hypo.ENCOUNTER_ID = scores.ENCOUNTER_ID AND hypo.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODABX abx ON abx.ENCOUNTER_ID = scores.ENCOUNTER_ID AND abx.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND abx.InDepartmentTime = scores.InDepartmentTime AND abx.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #OdboL bol ON bol.ENCOUNTER_ID = scores.ENCOUNTER_ID AND bol.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND bol.InDepartmentTime = scores.InDepartmentTime AND bol.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODLA la ON la.ENCOUNTER_ID = scores.ENCOUNTER_ID AND la.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND la.InDepartmentTime = scores.InDepartmentTime AND la.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODORDSET ordSet ON ordSet.ENCOUNTER_ID = scores.ENCOUNTER_ID AND ordSet.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND ordSet.InDepartmentTime = scores.InDepartmentTime AND ordSet.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODCVL cvl ON cvl.ENCOUNTER_ID = scores.ENCOUNTER_ID AND cvl.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND cvl.InDepartmentTime = scores.InDepartmentTime AND cvl.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODPressorPivot pressor ON pressor.ENCOUNTER_ID = scores.ENCOUNTER_ID

LEFT OUTER JOIN #ODSVO2 svo2 ON svo2.ENCOUNTER_ID = scores.ENCOUNTER_ID AND svo2.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND svo2.InDepartmentTime = scores.InDepartmentTime AND svo2.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODPROCAL proCal ON proCal.ENCOUNTER_ID = scores.ENCOUNTER_ID AND proCal.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND proCal.InDepartmentTime = scores.InDepartmentTime AND proCal.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODBC bc ON bc.ENCOUNTER_ID = scores.ENCOUNTER_ID AND bc.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND bc.InDepartmentTime = scores.InDepartmentTime AND bc.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODCSF csf ON csf.ENCOUNTER_ID = scores.ENCOUNTER_ID AND csf.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND csf.InDepartmentTime = scores.InDepartmentTime AND csf.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODPIV piv ON piv.ENCOUNTER_ID = scores.ENCOUNTER_ID AND piv.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND piv.InDepartmentTime = scores.InDepartmentTime AND piv.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ODETT ett ON ett.ENCOUNTER_ID = scores.ENCOUNTER_ID AND ett.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND ett.InDepartmentTime = scores.InDepartmentTime AND ett.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #PROPHYLAXIS prophy ON prophy.ENCOUNTER_ID = scores.ENCOUNTER_ID AND prophy.[ENC_ID Overall Order] = scores.[ENC_ID Overall Order]

LEFT OUTER JOIN #CVVH cvvh ON cvvh.ENCOUNTER_ID = scores.ENCOUNTER_ID AND cvvh.[ENC_ID Overall Order] = scores.[ENC_ID Overall Order]

LEFT OUTER JOIN #OX ox ON ox.ENCOUNTER_ID = scores.ENCOUNTER_ID AND ox.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ECMO ecmo ON ecmo.ENCOUNTER_ID = scores.ENCOUNTER_ID AND ecmo.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #EDPosScore_EDLOS edLOS ON edLOS.ENCOUNTER_ID = main.ENCOUNTER_ID AND edLOS.FIRST_TIME_LINE = 1

LEFT OUTER JOIN #FlwshtLstSepsisAudit sepsisAudit ON sepsisAudit.ENCOUNTER_ID = main.ENCOUNTER_ID AND sepsisAudit.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

/*Register Nurse*/

OUTER APPLY 

(	

	SELECT STRING_AGG(PRV.PROV_NAME, '; ') [Shift RNs]

	FROM [dbo].[TREATMENT_TEAMS] tTeam 

	INNER JOIN [dbo].[PROVIDERS] PRV ON PRV.PROV_ID = tTeam.PROV_ID

	WHERE tTeam.ENCOUNTER_ID = bp.ENCOUNTER_ID

	AND (tTeam.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(N,-35, bp.[Shift Start]) AND bp.[Shift End])

	AND tTeam.TRTMNT_TEAM_REL_CODE = '2' /*Registered Nurse*/

) ShiftRNs

/*CHARGE Nurse*/

OUTER APPLY 

(	

	SELECT STRING_AGG(PRV.PROV_NAME, '; ') [Shift CNs]

	FROM [dbo].[TREATMENT_TEAMS] tTeam 

	INNER JOIN [dbo].[PROVIDERS] PRV ON PRV.PROV_ID = tTeam.PROV_ID

	WHERE tTeam.ENCOUNTER_ID = bp.ENCOUNTER_ID

	AND (tTeam.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(N,-35, bp.[Shift Start]) AND bp.[Shift End])

	AND tTeam.TRTMNT_TEAM_REL_CODE = '99' /*Charge Nurse*/

) ShiftCNs



OUTER APPLY

(

	SELECT TOP 1  emp.NAME AS [Note Author]

		, CNOTE.CRT_INST_LOCAL_DTTM AS [Note Created Time]

	FROM dbo.CLINICAL_NOTES CNOTE

		LEFT JOIN dbo.NOTE_TEMPLATE_TEXT_IDS etx ON etx.NOTE_ID = CNOTE.NOTE_ID

		LEFT JOIN dbo.NOTE_TEMPLATE_LIST_IDS lis ON lis.NOTE_ID = CNOTE.NOTE_ID

		INNER JOIN dbo.NOTE_ENCOUNTER_INFO hnoEnc ON hnoEnc.NOTE_ID = CNOTE.NOTE_ID

		INNER JOIN dbo.EMPLOYEES emp ON emp.USER_ID = hnoEnc.AUTHOR_USER_ID

	WHERE

		CNOTE.ENCOUNTER_ID = main.ENCOUNTER_ID

		AND (CNOTE.CRT_INST_LOCAL_DTTM BETWEEN scores.[OD Score Time] AND DATEADD(MI, 180, scores.[OD Score Time])) /*within one hour from OD SCORE*/

		AND (etx.SMARTTEXTS_ID = '40440015' OR lis.SMARTLISTS_ID = '46214') /*HS IP SEPSIS HUDDLE NOTE or Sepsis Eval SmartList*/

	ORDER BY CNOTE.CRT_INST_LOCAL_DTTM 

) sepsisAlert

LEFT OUTER JOIN [reports].[SEVERE_SEPSIS_STAGING] SSS ON SSS.ENCOUNTER_ID = main.ENCOUNTER_ID

ORDER BY bp.ENCOUNTER_ID, bp.[ENC_ID Overall Order]

