

/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

Date			Who					Description 

----------------------------------------------------------------------------------- 

12/01/2025		Developer C		Separated base query into multiple tables, one record for each shift a PATIENTS was in a unit 

===================================================================================== 

USAGE: 

exec [reportingDB].[reporting].[USP_IP_SepsisShiftCompliance]

************************************************************************************/ 

CREATE PROCEDURE [reporting].[USP_IP_SepsisShiftCompliance]

AS

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table reporting.[IP_SepsisShiftCompliance];



IF OBJECT_ID(N'tempdb..#ODScores') IS NOT NULL DROP TABLE #ODScores;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO #ODScores

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800006')

CREATE INDEX IDX_OdScores ON #ODScores (FLO_ID) 



IF OBJECT_ID(N'tempdb..#MainAdmDetails') IS NOT NULL DROP TABLE #MainAdmDetails;

/*list of admitted patients*/

SELECT DISTINCT

	enc.[PatEncCSNID] PAT_ENC_CSN_ID

	, enc.[PatID] PAT_ID

	, enc.[PatMRNID] PAT_MRN_ID

	, enc.[PatName] PAT_NAME

	, enc.[EthnicGroup] [Ethnic Group]

	, enc.[Race] [Race]

	, enc.[InpatientDataID] INPATIENT_DATA_ID

	, enc.[ADTArrivalTime] ADT_ARRIVAL_TIME

	, enc.[HospAdmsnTime] HOSP_ADMSN_TIME

	, enc.[HospDischTime] HOSP_DISCH_TIME

	, enc.[InpAdmDate] INP_ADM_DATE

	, enc.[EDDepartureTime] ED_DEPARTURE_TIME

	, enc.[Disposition] [Disposition]

	, enc.[Location] [Location]

	, enc.[LosHours] LOS_HRS

	, enc.[BirthDate] BIRTH_DATE

INTO #MainAdmDetails

FROM [reporting].[IP_SepsisEncounters] enc 

CREATE INDEX IDX_Main ON #MainAdmDetails (PAT_ENC_CSN_ID) 

/*SELECT * FROM #MainAdmDetails*/



/***********************************************************************

Get Encounters and a record for every shift a PATIENTS was in a department for Compliance reporting

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_PopTemp') IS NOT NULL DROP TABLE #Base_PopTemp;

WITH vaplh AS

(

	SELECT 

		enc.[PatEncCSNID] PAT_ENC_CSN_ID

		, enc.[InDepartmentTime] IN_DTTM

		, enc.[OutDepartmentTime] OUT_DTTM

		, enc.[ADTDepartmentID] ADT_DEPARTMENT_ID

		, enc.[ADTDepartmentName] ADT_DEPARTMENT_NAME

		, DATEADD(MI, 1140, DATEADD(DD, -1, DATEDIFF(DD, 0, CONVERT(DATE, enc.[InDepartmentTime])))) [In Previous PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, enc.[InDepartmentTime])))) [In Previous PM End]

		, DATEADD(MI, 420, DATEADD(DD, 0, DATEDIFF(DD, 0,  CONVERT(DATE, enc.[InDepartmentTime])))) [In AM Start]

		, DATEADD(MI, 1139, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, enc.[InDepartmentTime])))) [In AM End]

		, DATEADD(MI, 1140, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, enc.[InDepartmentTime])))) [In PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 1, DATEDIFF(DD, 0, CONVERT(DATE,enc.[InDepartmentTime])))) [In PM End]

		, DATEADD(MI, 1140, DATEADD(DD, -1, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(enc.[OutDepartmentTime],GETDATE()))))) [Out Previous PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(enc.[OutDepartmentTime],GETDATE()))))) [Out Previous PM End]

		, DATEADD(MI, 420, DATEADD(DD, 0, DATEDIFF(DD, 0,  CONVERT(DATE, COALESCE(enc.[OutDepartmentTime],GETDATE()))))) [Out AM Start]

		, DATEADD(MI, 1139, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(enc.[OutDepartmentTime],GETDATE()))))) [Out AM End]

		, DATEADD(MI, 1140, DATEADD(DD, 0, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(enc.[OutDepartmentTime],GETDATE()))))) [Out PM Start]

		, DATEADD(MI, 419, DATEADD(DD, 1, DATEDIFF(DD, 0, CONVERT(DATE, COALESCE(enc.[OutDepartmentTime],GETDATE()))))) [Out PM End]

		, enc.[UniqueRow] [Unique Row]

	FROM [reporting].[IP_SepsisEncountersWLocations] enc

)



SELECT DISTINCT

	main.PAT_ENC_CSN_ID

	, main.PAT_ID

	, vaplh.ADT_DEPARTMENT_ID

	, vaplh.ADT_DEPARTMENT_NAME

	, cvs.CODE_DESC AS DEPARTMENT_ROLLUP

	, vaplh.IN_DTTM

	, vaplh.OUT_DTTM

	, main.INPATIENT_DATA_ID

	, main.BIRTH_DATE

	, main.ADT_ARRIVAL_TIME

	, main.ED_DEPARTURE_TIME

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

	, ROW_NUMBER() OVER (PARTITION BY main.PAT_ENC_CSN_ID, vaplh.IN_DTTM ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM) [inDeptRN]

	, ROW_NUMBER() OVER (PARTITION BY main.PAT_ENC_CSN_ID ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM ) [CSN Order]

	, vaplh.[Unique Row]

INTO #Base_PopTemp

FROM #MainAdmDetails main

INNER JOIN  vaplh ON vaplh.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND vaplh.ADT_DEPARTMENT_ID IS NOT NULL /*[EMRDB].[dbo].V_PATIENT_LOCATION_HISTORY*/

INNER JOIN [reportingDB].[reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = vaplh.ADT_DEPARTMENT_ID

			AND cvs.VALUE_SET_ID = 3031 /*DEPARTMENT ROLL UP*/

CREATE INDEX IDX_Base_PopTemp ON #Base_PopTemp (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Base_PopTemp*/



/***********************************************************************

Get Every day a PATIENTS should have had a Sepsis Screening

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

; WITH dateCTE AS

(

	SELECT PAT_ENC_CSN_ID

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

		, PAT_ID

		, DEPARTMENT_ROLLUP

		, INPATIENT_DATA_ID

		, BIRTH_DATE

		, 1 [In Record]

		, CASE WHEN [In Shift Date] = [Out Shift Date] THEN 1 ELSE 0 END [Out Record]

		, [CSN Order]

		, [Unique Row]

	FROM #Base_PopTemp

	WHERE inDeptRN = 1

	AND DEPARTMENT_ROLLUP NOT IN ('ER', 'P-ER')

	UNION ALL 

	SELECT PAT_ENC_CSN_ID

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

		, d.PAT_ID

		, d.DEPARTMENT_ROLLUP

		, d.INPATIENT_DATA_ID

		, BIRTH_DATE

		, CASE WHEN DATEADD(d, 1, d.[Expansion Date]) = d.[Expansion Start Date] THEN 1 ELSE 0 END  [In Record]

		, CASE WHEN DATEADD(d, 1, d.[Expansion Date]) = d.[Expansion End Date] THEN 1 ELSE 0 END [Out Record]

		, [CSN Order]

		, [Unique Row]

	FROM dateCTE d 

	WHERE DATEADD(d, 1, d.[Expansion Date]) <= d.[Expansion End Date]

)



/***********************************************************************

Finalize base table, one record for each shift a PATIENTS was in a unit

***********************************************************************/

SELECT * 

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID, [InDepartmentTime] ORDER BY [Score Date], [Shift AM/PM]) AS [Unit Order]

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY [InDepartmentTime], [Score Date], [Shift AM/PM]) AS [CSN Overall Order]

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID, [Shift Start] ORDER BY [Score Date], [Shift AM/PM]) AS [Shift Order]

INTO #Base_Pop

FROM (

	SELECT am.PAT_ENC_CSN_ID

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

		, am.PAT_ID

		, am.DEPARTMENT_ROLLUP

		, am.INPATIENT_DATA_ID

		, DATEDIFF(MM, BIRTH_DATE, a.[Shift Start]) AS AGE_MONTHS

		, FLOOR(DATEDIFF(DD, BIRTH_DATE, a.[Shift End])/365.25) AS AGE_YEARS

		, am.[In Record]

		, am.[Out Record]

		, [CSN Order]

		, 'AM (Day Shift)' [Shift AM/PM]

		, a.[Shift Start]

		, a.[Shift End]

		, [Unique Row]

	FROM dateCTE am 

	CROSS APPLY ( 

		SELECT DATEADD(MI, 420, DATEADD(DD, 0, DATEDIFF(DD, 0, am.[Expansion Date]))) [Shift Start]

			, DATEADD(MI, 1139, DATEADD(DD, 0, DATEDIFF(DD, 0, am.[Expansion Date]))) [Shift End]

	) a

	WHERE [AM Denom] = 1 

	UNION ALL

	SELECT pm.PAT_ENC_CSN_ID

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

		, pm.PAT_ID

		, pm.DEPARTMENT_ROLLUP

		, pm.INPATIENT_DATA_ID

		, DATEDIFF(MM, BIRTH_DATE, a.[Shift Start]) AS AGE_MONTHS

		, FLOOR(DATEDIFF(DD, BIRTH_DATE, a.[Shift End])/365.25) AS AGE_YEARS

		, pm.[In Record]

		, pm.[Out Record]

		, [CSN Order]

		, 'PM (Night Shift)' [Shift AM/PM]

		, a.[Shift Start]

		, a.[Shift End]

		, [Unique Row]

	FROM dateCTE pm 

	CROSS APPLY ( 

		SELECT DATEADD(MI, 1140, DATEADD(DD, 0, DATEDIFF(DD, 0, pm.[Expansion Date]))) [Shift Start]

			, DATEADD(MI, 419, DATEADD(DD, 1, DATEDIFF(DD, 0, pm.[Expansion Date]))) [Shift End]

	) a

	WHERE pm.[PM Denom] = 1

) a

OPTION (MAXRECURSION 8000);  /*default is 100*/

CREATE INDEX IDX_Base_Pop ON #Base_Pop (PAT_ENC_CSN_ID) 

CREATE INDEX IDX_Base_Pop_Inp ON #Base_Pop (INPATIENT_DATA_ID) 

/*SELECT * FROM #Base_Pop*/



/*OD Score*/

IF OBJECT_ID(N'tempdb..#FlwshtLst') IS NOT NULL DROP TABLE #FlwshtLst;

SELECT PAT_ENC_CSN_ID, FLO_MEAS_ID, RECORDED_TIME, MEAS_VALUE, FSD_ID, [Documented Department ID], [Documented Department], [CSN Overall Order]

INTO #FlwshtLst

FROM (

	SELECT main.PAT_ENC_CSN_ID

		, meas.FLO_MEAS_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE

		, meas.FSD_ID

		, bpt.IN_DTTM

		, bpt.OUT_DTTM

		, bpt.ADT_DEPARTMENT_ID [Documented Department ID]

		, bpt.ADT_DEPARTMENT_NAME [Documented Department]

		, main.[CSN Order]

		, main.[Unit Order]

		, main.[CSN Overall Order]

		, ROW_NUMBER() OVER(PARTITION BY main.PAT_ENC_CSN_ID, main.[CSN Order], main.[Unit Order] ORDER BY [Shift Start], RECORDED_TIME) AS RowNum

	FROM #Base_Pop main

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID IN (SELECT * FROM #ODScores)

	INNER JOIN #Base_PopTemp bpt ON bpt.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND meas.RECORDED_TIME BETWEEN bpt.IN_DTTM AND bpt.OUT_DTTM AND main.[CSN Order] = bpt.[CSN Order]

	WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

) a

WHERE a.RowNum = 1

CREATE INDEX IDX_FlwshtLst ON #FlwshtLst (PAT_ENC_CSN_ID, FSD_ID) 

/*SELECT * FROM #FlwshtLst ORDER BY RECORDED_TIME*/



/*****************************OD Huddle Flowsheet rows*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtLstHuddleODScore') IS NOT NULL DROP TABLE #FlwshtLstHuddleODScore;

SELECT main.PAT_ENC_CSN_ID

	, meas.FSD_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME

	, meas.MEAS_VALUE

	, main.[CSN Overall Order]

INTO #FlwshtLstHuddleODScore

FROM #Base_Pop main

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000002705','9000002732','9000002733','9000002706','9000002734','9000002707')

	AND meas.MEAS_VALUE IS NOT NULL

WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

CREATE INDEX IDX_FlwshtLstHuddleODScore ON #FlwshtLstHuddleODScore (PAT_ENC_CSN_ID, FSD_ID) 

/*SELECT * FROM #FlwshtLstHuddleODScore*/



/*****************************Flowsheet row for CLINICAL_ALERTS not activated*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtNoAlert') IS NOT NULL DROP TABLE #FlwshtNoAlert;

SELECT a.PAT_ENC_CSN_ID

	, MAX(a.RECORDED_TIME) RECORDED_TIME

	, STRING_AGG([CLINICAL_ALERTS Not Activated Reason],  ' % ') [CLINICAL_ALERTS Not Activated Reason]

	, STRING_AGG([CLINICAL_ALERTS Not Activated Comment],  ' % ') [CLINICAL_ALERTS Not Activated Comment]

	, a.[CSN Overall Order]

INTO #FlwshtNoAlert

FROM (

	SELECT main.PAT_ENC_CSN_ID

		, rec.INPATIENT_DATA_ID

		, meas.FSD_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE AS [CLINICAL_ALERTS Not Activated Reason]

		, meas.MEAS_COMMENT as [CLINICAL_ALERTS Not Activated Comment]

		, main.[CSN Overall Order]

	FROM #Base_Pop main

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '9000003159'

	WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

) a

GROUP BY a.PAT_ENC_CSN_ID, a.[CSN Overall Order]

CREATE INDEX IDX_FlwshtNoAlert ON #FlwshtNoAlert (PAT_ENC_CSN_ID, [CSN Overall Order]) 

/*SELECT * FROM #FlwshtNoAlert*/



IF OBJECT_ID(N'tempdb..#FlwshtAlert') IS NOT NULL DROP TABLE #FlwshtAlert;

SELECT a.PAT_ENC_CSN_ID

	, a.ALT_ID

	, a.ALT_ACTION_INST

	, a.[CLINICAL_ALERTS Activated Comment]

	, a.[CSN Overall Order]

INTO #FlwshtAlert

FROM (

	SELECT main.PAT_ENC_CSN_ID

		, alt.ALT_ID

		, his.ALT_ACTION_INST

		, COALESCE(his.SPEC_OVR_CMNT,' ')+ rsn.[NAME] [CLINICAL_ALERTS Activated Comment]

		, main.[CSN Overall Order]

		, ROW_NUMBER() OVER(PARTITION BY main.PAT_ENC_CSN_ID, main.[CSN Overall Order] ORDER BY main.[CSN Overall Order]) RowNum

	FROM #Base_Pop main

	INNER JOIN [EMRDB].[dbo].[CLINICAL_ALERTS] alt ON alt.PAT_CSN = main.PAT_ENC_CSN_ID AND alt.BPA_LOCATOR_ID = 900400001 /*BASE 2019 HS OD SCORE SEPSIS >2 [900400001]*/

	INNER JOIN [EMRDB].[dbo].[ALERT_HISTORY] his ON his.ALT_ID = alt.ALT_ID

	INNER JOIN [EMRDB].[dbo].[REF_ALERT_OVERRIDE_REASONS] rsn ON rsn.ALRT_SP_OVR_RSN_C = his.SPEC_OVR_RSN_C

	WHERE his.ALT_ACTION_INST BETWEEN main.[Shift Start] AND main.[Shift End]

) a

WHERE a.RowNum = 1

CREATE INDEX IDX_FlwshtAlert ON #FlwshtAlert (PAT_ENC_CSN_ID) 

/*SELECT * FROM #FlwshtAlert*/



IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT bp.PAT_ENC_CSN_ID

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

	, bp.[CSN Overall Order]

	, CASE WHEN meas.MEAS_VALUE >= 2 THEN 'Y' ELSE 'N' END [ShowComponents]

	, meas.FSD_ID

INTO #Base_Pop_OD_Scores

FROM #Base_Pop bp 

INNER JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] peh ON peh.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

LEFT OUTER JOIN #FlwshtLst meas ON meas.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND meas.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #FlwshtNoAlert alertNotActivated on 

	(	

		alertNotActivated.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID 

		AND alertNotActivated.[CSN Overall Order] = bp.[CSN Overall Order]

	)

LEFT OUTER JOIN #FlwshtAlert alertActivated on 

	(	

		alertActivated.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID 

		AND alertActivated.[CSN Overall Order] = bp.[CSN Overall Order]

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

CREATE INDEX IDX_Base_Pop_OD_Scores ON #Base_Pop_OD_Scores (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Base_Pop_OD_Scores */



/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisShiftCompliance]

	(

		[PatEncCSNID],

		[ShiftDate],

		[ShiftAMPM],

		[ShiftStart], 

		[ShiftEnd],

		[ODScore],

		[ScoreTime],



		[ShiftComplianceYN],

		[ShiftCompliance],

		[ShiftNonCompliance],

		

		[Shift1ComplianceYN],

		[Shift1Compliance],

		[Shift1NonCompliance],

		[Shift1Color],



		[Shift2ComplianceYN],

		[Shift2Compliance],

		[Shift2NonCompliance],

		[Shift2Color],

		

		[ShiftColor],

		[ShiftColorDisplay],

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

		[CSNOrder],

		[UnitOrder],

		[CSNOverallOrder],

		[AMDenom],

		[PMDenom],

		[Denominator],

		[UniqueRow],

		[RefreshDate])



SELECT 

	main.PAT_ENC_CSN_ID [CSN]

	, bp.[Score Date]

	, bp.[Shift AM/PM]

	, bp.[Shift Start]

	, bp.[Shift End]

	, scores.[OD Score]

	, scores.[OD Score Time]



	, [ShiftComplianceYN] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END [Shift Non-Compliance]



	, CASE WHEN bp.[Shift AM/PM] = 'AM (Day Shift)' THEN [ShiftComplianceYN] ELSE NULL END [Shift 1 Compliance Y/N]

	, CASE WHEN bp.[Shift AM/PM] = 'AM (Day Shift)' THEN [ShiftCompliance] ELSE NULL END [Shift 1 Compliance]

	, CASE WHEN bp.[Shift AM/PM] = 'AM (Day Shift)' THEN

		CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END

	ELSE NULL 

	END [Shift 1 Non-Compliance]

	, CASE WHEN bp.[Shift AM/PM] = 'AM (Day Shift)' THEN [ShiftColor] ELSE NULL END [Shift 1 Color]

	

	, CASE WHEN bp.[Shift AM/PM] = 'PM (Night Shift)' THEN [ShiftComplianceYN] ELSE NULL END [Shift 2 Compliance Y/N]

	, CASE WHEN bp.[Shift AM/PM] = 'PM (Night Shift)' THEN [ShiftCompliance] ELSE NULL END [Shift 2 Compliance]

	, CASE WHEN bp.[Shift AM/PM] = 'PM (Night Shift)' THEN

		CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END

	ELSE NULL 

	END [Shift 2 Non-Compliance]

	, CASE WHEN bp.[Shift AM/PM] = 'PM (Night Shift)' THEN [ShiftColor] ELSE NULL END [Shift 2 Color]

	



	, [ShiftColor] [Shift Color]

	, CASE WHEN scores.[OD Score] IS NULL THEN '#FD625E' ELSE '#73B761' END [Shift Color Display]



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

	, bp.[CSN Order]

	, bp.[Unit Order]

	, bp.[CSN Overall Order]

	, bp.[AM Denom]

	, bp.[PM Denom]

	, CASE WHEN [Shift AM/PM] like 'AM%' THEN [AM Denom] ELSE [PM Denom] END [Denominator]

	, bp.[Unique Row] [Unique Row]

	, GETDATE()

FROM #MainAdmDetails main  

INNER JOIN #Base_Pop bp ON bp.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

INNER JOIN #Base_Pop_OD_Scores scores ON scores.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND scores.[CSN Overall Order] = bp.[CSN Overall Order]

INNER JOIN reports.FY_DATE_DIMENSION fyDate ON fyDate.CALENDAR_DT = bp.[Score Date] 

CROSS APPLY 

(

	SELECT CASE WHEN scores.[OD Score] IS NULL THEN 0 ELSE 1 END [ShiftCompliance]

	, CASE WHEN scores.[OD Score] IS NULL THEN 'RED' ELSE 'GREEN' END [ShiftColor]

	, CASE WHEN scores.[OD Score] IS NULL THEN 'N' ELSE 'Y' END [ShiftComplianceYN]

) scomp

/*Register Nurse*/

OUTER APPLY 

(	

	SELECT STRING_AGG(ser.PROV_NAME, '; ') [Shift RNs]

	FROM [EMRDB].[dbo].[TREATMENT_TEAMS] tTeam 

	INNER JOIN [EMRDB].[dbo].[PROVIDERS] ser ON SER.PROV_ID = tTeam.PROV_ID

	WHERE tTeam.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

	AND (tTeam.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(N,-35, bp.[Shift Start]) AND bp.[Shift End])

	AND tTeam.TRTMNT_TEAM_REL_C = '2' /*Registered Nurse*/

) ShiftRNs

/*CHARGE Nurse*/

OUTER APPLY 

(	

	SELECT STRING_AGG(ser.PROV_NAME, '; ') [Shift CNs]

	FROM [EMRDB].[dbo].[TREATMENT_TEAMS] tTeam 

	INNER JOIN [EMRDB].[dbo].[PROVIDERS] ser ON SER.PROV_ID = tTeam.PROV_ID

	WHERE tTeam.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

	AND (tTeam.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(N,-35, bp.[Shift Start]) AND bp.[Shift End])

	AND tTeam.TRTMNT_TEAM_REL_C = '99' /*Charge Nurse*/

) ShiftCNs



OUTER APPLY

(

	SELECT TOP 1  emp.NAME AS [Note Author]

		, hno.CRT_INST_LOCAL_DTTM AS [Note Created Time]

	FROM EMRDB.dbo.CLINICAL_NOTES hno

		LEFT JOIN EMRDB.dbo.NOTE_TEMPLATE_TEXT_IDS etx ON etx.NOTE_ID = hno.NOTE_ID

		LEFT JOIN EMRDB.dbo.NOTE_TEMPLATE_LIST_IDS lis ON lis.NOTE_ID = hno.NOTE_ID

		INNER JOIN EMRDB.dbo.NOTE_ENCOUNTER_INFO hnoEnc ON hnoEnc.NOTE_ID = hno.NOTE_ID

		INNER JOIN EMRDB.dbo.EMPLOYEES emp ON emp.USER_ID = hnoEnc.AUTHOR_USER_ID

	WHERE

		hno.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

		AND (hno.CRT_INST_LOCAL_DTTM BETWEEN scores.[OD Score Time] AND DATEADD(MI, 180, scores.[OD Score Time])) /*within one hour from OD SCORE*/

		AND (etx.SMARTTEXTS_ID = '40440015' OR lis.SMARTLISTS_ID = '46214') /*HS IP SEPSIS HUDDLE NOTE or Sepsis Eval SmartList*/

	ORDER BY HNO.CRT_INST_LOCAL_DTTM 

) sepsisAlert

--LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING] IPSO ON IPSO.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

ORDER BY bp.PAT_ENC_CSN_ID, bp.[CSN Overall Order]

END 

