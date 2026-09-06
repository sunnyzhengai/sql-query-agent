



/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

Date			Who					Description 

------------------------------------------------------------------------------- 

2022/03/22		Developer B			TKT-004 PBI Conversion. SP created from [USP_IP_SEPSIS]

2022/05/22		V_DEV001			Expansion Phase III Location update

2023/04/19	    Developer C        Merged 3 stored procedures into one: reports.USP_IP_SEPSIS_REPORT, reports.USP_IP_SEPSIS_COMPLIANCE, reports.USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES

2023/12/12		Developer C		Subqueries to get Shift RN/CN was throwing an error due to value in DB being varchar and not int

2024/04/23		Developer C		Changed logic to look for nurses to look 35 minutes before Shift start to account for Nurses assigning themselves at 

										or during Report/hand off which is 30 minutes before shift starts

2025/02/21		Developer C		Changed logic to only look at Sepsis FLO documentation that occured in the same department.  This 

										will prevent positive scores in PICU appearing in non PICU units causing false positives. 

2026/05/13		Developer C		Added new TKT-013 Circular Dysfunction

===================================================================================== 

USAGE: 

exec [reporting].[USP_IP_SepsisScreeningAudit]

************************************************************************************/ 

CREATE   PROCEDURE [reporting].[USP_IP_SepsisScreeningAudit]

AS



SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table [reporting].[IP_SepsisScreeningAudit];



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

	enc.[PATENCENCID] ENCOUNTER_ID

	, enc.[PatientID] PATIENT_ID

	, enc.[PATIENTMRN] PATIENT_MRN

	, enc.[PatientName] PATIENT_NAME

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

CREATE INDEX IDX_Main ON #MainAdmDetails (ENCOUNTER_ID) 

/*SELECT * FROM #MainAdmDetails*/



/***********************************************************************

Finalize base table, one record for each unit a PATIENTS was in

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT 	

	[PATENCENCID] [ENCOUNTER_ID],

	[InDepartmentTime] [In Dept Date],

	[OutDepartmentTime] [Out Dept Date],

	[ADTDepartmentID] [ADT_DEPARTMENT_ID],

	[ADTDepartmentName] [ADT_DEPARTMENT_NAME],

	[PatientID] [PATIENT_ID], 

	[DepartmentRollup] [DEPARTMENT_ROLLUP],

	[InpatientDataID] [INPATIENT_DATA_ID], 

	[ENCORDER] [ENC_ID Order],

	[UniqueRow] [Unique Row]

INTO #Base_Pop

FROM #MainAdmDetails main

INNER JOIN [reporting].[IP_SepsisEncountersWLocations] loc ON loc.PATENCENCID = main.ENCOUNTER_ID

CREATE INDEX IDX_Base_Pop ON #Base_Pop (ENCOUNTER_ID) 

CREATE INDEX IDX_Base_Pop_Inp ON #Base_Pop (INPATIENT_DATA_ID) 

/*SELECT * FROM #Base_Pop*/



/*OD Score*/

IF OBJECT_ID(N'tempdb..#FlwshtLst') IS NOT NULL DROP TABLE #FlwshtLst;

	SELECT main.ENCOUNTER_ID

		, meas.FLO_MEAS_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE

		, meas.FSD_ID

		, main.[In Dept Date] [IN_DTTM]

		, main.[Out Dept Date] [OUT_DTTM]

		, main.ADT_DEPARTMENT_ID [Documented Department ID]

		, main.ADT_DEPARTMENT_NAME [Documented Department]

		, CAST(meas.RECORDED_TIME AS DATE) AS [Score Date]

		, main.[ENC_ID Order]

		, ROW_NUMBER() OVER(PARTITION BY main.ENCOUNTER_ID ORDER BY main.[ENC_ID Order], RECORDED_TIME) AS [ENC_ID Overall Score Order]

		, main.[Unique Row]

	INTO #FlwshtLst

	FROM #Base_Pop main

	INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID IN (SELECT * FROM #ODScores)

	WHERE meas.RECORDED_TIME BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

CREATE INDEX IDX_FlwshtLst ON #FlwshtLst (ENCOUNTER_ID) 

CREATE INDEX IDX_FlwshtLstFSD ON #FlwshtLst (FSD_ID) 

/*SELECT * FROM #FlwshtLst WHERE ENCOUNTER_ID = '1060789013' ORDER BY ENCOUNTER_ID, RECORDED_TIME*/



/*****************************OD Huddle Flowsheet rows*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtLstHuddleODScore') IS NOT NULL DROP TABLE #FlwshtLstHuddleODScore;

SELECT main.ENCOUNTER_ID

	, meas.FSD_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME

	, meas.MEAS_VALUE

	, flo.[ENC_ID Overall Score Order]

	, main.[Unique Row]

INTO #FlwshtLstHuddleODScore

FROM #Base_Pop main

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000002705','9000002732','9000002733','9000002706','9000002734','9000002707')

	AND meas.MEAS_VALUE IS NOT NULL

OUTER APPLY 

(

	SELECT MAX(flo.[ENC_ID Overall Score Order]) [ENC_ID Overall Score Order]

	FROM #FlwshtLst flo 

	WHERE  flo.ENCOUNTER_ID = main.ENCOUNTER_ID 

	AND flo.RECORDED_TIME <= meas.RECORDED_TIME

) flo

WHERE meas.RECORDED_TIME BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

ORDER BY main.ENCOUNTER_ID, meas.RECORDED_TIME

CREATE INDEX IDX_FlwshtLstHuddleODScore ON #FlwshtLstHuddleODScore (ENCOUNTER_ID, FSD_ID) 

/*SELECT * FROM #FlwshtLstHuddleODScore ORDER BY ENCOUNTER_ID, RECORDED_TIME*/



/*****************************Flowsheet row for CLINICAL_ALERTS not activated*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtNoAlert') IS NOT NULL DROP TABLE #FlwshtNoAlert;

SELECT a.ENCOUNTER_ID

	, MAX(a.RECORDED_TIME) RECORDED_TIME

	, STRING_AGG([CLINICAL_ALERTS Not Activated Reason],  ' % ') [CLINICAL_ALERTS Not Activated Reason]

	, STRING_AGG([CLINICAL_ALERTS Not Activated Comment],  ' % ') [CLINICAL_ALERTS Not Activated Comment]

	, a.[ENC_ID Overall Score Order]

INTO #FlwshtNoAlert

FROM (

	SELECT main.ENCOUNTER_ID

		, rec.INPATIENT_DATA_ID

		, meas.FSD_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE AS [CLINICAL_ALERTS Not Activated Reason]

		, meas.MEAS_COMMENT as [CLINICAL_ALERTS Not Activated Comment]

		, flo.[ENC_ID Overall Score Order]

	FROM #Base_Pop main

	INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '9000003159'

	OUTER APPLY 

	(

		SELECT MAX(flo.[ENC_ID Overall Score Order]) [ENC_ID Overall Score Order]

		FROM #FlwshtLst flo 

		WHERE  flo.ENCOUNTER_ID = main.ENCOUNTER_ID 

		AND flo.RECORDED_TIME <= meas.RECORDED_TIME

	) flo

	WHERE meas.RECORDED_TIME BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

) a

GROUP BY a.ENCOUNTER_ID, a.[ENC_ID Overall Score Order]

CREATE INDEX IDX_FlwshtNoAlert ON #FlwshtNoAlert (ENCOUNTER_ID, [ENC_ID Overall Score Order]) 

/*SELECT * FROM #FlwshtNoAlert*/



IF OBJECT_ID(N'tempdb..#FlwshtAlert') IS NOT NULL DROP TABLE #FlwshtAlert;

SELECT a.ENCOUNTER_ID

	, a.ALT_ID

	, a.ALT_ACTION_INST

	, a.[CLINICAL_ALERTS Activated Comment]

	, a.[ENC_ID Overall Score Order]

	, a.[OPA TYPE]

INTO #FlwshtAlert

FROM (

	SELECT main.ENCOUNTER_ID

		, alt.ALT_ID

		, his.ALT_ACTION_INST

		, COALESCE(his.SPEC_OVR_CMNT,' ')+ rsn.[NAME] [CLINICAL_ALERTS Activated Comment]

		, alt.BPA_LOCATOR_ID 

		, flo.[ENC_ID Overall Score Order]

		, CASE WHEN alt.BPA_LOCATOR_ID = 900400001 THEN 'Non-PICU' ELSE 'PICU' END [OPA TYPE]

		, ROW_NUMBER() OVER(PARTITION BY main.ENCOUNTER_ID, flo.[ENC_ID Overall Score Order] ORDER BY flo.[ENC_ID Overall Score Order]) RowNum

	FROM #Base_Pop main

	INNER JOIN [dbo].[CLINICAL_ALERTS] alt ON alt.VISIT_ID = main.ENCOUNTER_ID AND alt.BPA_LOCATOR_ID in (900400001, 900400011) /*BASE 2019 HS OD SCORE SEPSIS >2 [900400001]*/

	INNER JOIN [dbo].[ALERT_HISTORY] his ON his.ALT_ID = alt.ALT_ID

	INNER JOIN [dbo].[REF_ALERT_OVERRIDE_REASONS] rsn ON rsn.ALRT_SP_OVR_RSN_CODE = his.SPEC_OVR_RSN_CODE

	OUTER APPLY 

	(

		SELECT MAX(flo.[ENC_ID Overall Score Order]) [ENC_ID Overall Score Order]

		FROM #FlwshtLst flo 

		WHERE  flo.ENCOUNTER_ID = main.ENCOUNTER_ID 

		AND flo.RECORDED_TIME <= his.ALT_ACTION_INST

	) flo

	WHERE his.ALT_ACTION_INST BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

) a

WHERE a.RowNum = 1

CREATE INDEX IDX_FlwshtAlert ON #FlwshtAlert (ENCOUNTER_ID) 

/*SELECT * FROM #FlwshtAlert*/



IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT bp.ENCOUNTER_ID

	, bp.ADT_DEPARTMENT_ID

	, bp.ADT_DEPARTMENT_NAME

	, bp.[In Dept Date]

	, bp.[Out Dept Date]

	, meas.MEAS_VALUE [OD Score]

	, meas.RECORDED_TIME [OD Score Time]

	, meas.[Score Date] [Score Day]

	, huddleNote.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP]

	, huddleNote.[Huddle Date]

	, huddleNote.[Huddle Time]

	, huddleNote.[PATIENTS Assessed by MD/PNP]

	, huddleNote.[Physician Name]

	, huddleNote.[Additional Orders Received/Placed by MD/PNP]

	, alertNotActivated.[CLINICAL_ALERTS Not Activated Reason]

	, alertNotActivated.[CLINICAL_ALERTS Not Activated Comment]

	, alertActivated.[CLINICAL_ALERTS Activated Comment]

	, meas.[ENC_ID Overall Score Order]

	, meas.[ENC_ID Order]

	, CASE WHEN meas.MEAS_VALUE >= 2 THEN 'Y' ELSE 'N' END [ShowComponents]

	, meas.FSD_ID

	, meas.[Unique Row]

INTO #Base_Pop_OD_Scores

FROM #Base_Pop bp 

INNER JOIN [dbo].[HOSPITAL_ENCOUNTERS] HE ON HE.ENCOUNTER_ID = bp.ENCOUNTER_ID

LEFT OUTER JOIN #FlwshtLst meas ON meas.ENCOUNTER_ID = bp.ENCOUNTER_ID AND meas.[ENC_ID Order] = bp.[ENC_ID Order]

LEFT OUTER JOIN #FlwshtNoAlert alertNotActivated on 

	(	

		alertNotActivated.ENCOUNTER_ID = bp.ENCOUNTER_ID 

		AND alertNotActivated.[ENC_ID Overall Score Order] = meas.[ENC_ID Overall Score Order]

	)

LEFT OUTER JOIN #FlwshtAlert alertActivated on 

	(	

		alertActivated.ENCOUNTER_ID = bp.ENCOUNTER_ID 

		AND alertActivated.[ENC_ID Overall Score Order] = meas.[ENC_ID Overall Score Order]

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

		WHERE DATEDIFF(MINUTE, meas.RECORDED_TIME, subMeas.RECORDED_TIME) BETWEEN -60 AND 180 /*WAS -120 UNTIL 03.01.2021 */

		AND subMeas.MEAS_VALUE IS NOT NULL

		AND subMeas.FSD_ID = meas.FSD_ID

	) a

	WHERE a.rownumber = 1

	GROUP BY a.INPATIENT_DATA_ID, a.OD_SCORE_RECORDED_TIME, a.FSD_ID

) huddleNote

CREATE INDEX IDX_Base_Pop_OD_Scores ON #Base_Pop_OD_Scores (ENCOUNTER_ID) 

/*SELECT * FROM #Base_Pop_OD_Scores WHERE [OD Score] > 2 */



IF OBJECT_ID(N'tempdb..#SepsisAuditTemp') IS NOT NULL DROP TABLE #SepsisAuditTemp;

SELECT od.ENCOUNTER_ID, od.[ENC_ID Overall Score Order], od.[OD Score Time], meas.FLO_MEAS_ID, meas.MEAS_VALUE, meas.RECORDED_TIME

	, DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME) [Time since OD Score]

	, ABS(DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME)) [ABS Time since OD Score]

	, od.[Score Day]

INTO #SepsisAuditTemp

FROM #Base_Pop_OD_Scores od

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON od.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000161701', '9000161702', '9000161710', '9000161708', '9000161704', '9000002611'

			, '98', '99', '95', '9000800500', '900101', '900103', '900102', '900104', '900105', '900107', '900106'

			, '900108', '9000002702', '900109', '900110', '9000311801', '9000311802', '9000311803', '9000003157'

			, '9001140203', '9001140205', '9000012611')

WHERE meas.RECORDED_TIME BETWEEN od.[In Dept Date] AND od.[Out Dept Date]

AND od.ShowComponents = 'Y'

AND DATEDIFF(MINUTE, od.[OD Score Time], meas.RECORDED_TIME) BETWEEN -60 AND 180 /*WAS -120 UNTIL 03.01.2021 */



IF OBJECT_ID(N'tempdb..#FlwshtLstSepsisAudit') IS NOT NULL DROP TABLE #FlwshtLstSepsisAudit;

SELECT bp.ENCOUNTER_ID

	, bp.[Documented Department ID]

	, bp.[Documented Department]

	, bp.IN_DTTM

	, bp.OUT_DTTM

	, bp.MEAS_VALUE [OD Score]

	, bp.RECORDED_TIME [OD Score Time]

	, bp.[Score Date] [Score Day]

	, sepsisAudit.[Predisposition]

	, sepsisAudit.[Infectious Symptoms]

	, sepsisAudit.[Hematologic Dysfunction]

	, sepsisAudit.[Renal Dysfunction]

	, sepsisAudit.[Neurological Dysfunction]

	, sepsisAudit.[Respiratory Dysfunction]

	, sepsisAudit.[Circulatory Dysfunction]

	, sepsisAudit.[Pulse]

	, sepsisAudit.[Resp]

	, sepsisAudit.[BP]

	, sepsisAudit.[BP Girls Percentile]

	, sepsisAudit.[BP Boys Percentile]

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

	, bp.[ENC_ID Overall Score Order]

	, bp.[Unique Row]

INTO #FlwshtLstSepsisAudit

FROM #FlwshtLst bp 

OUTER APPLY 

(

	SELECT bp.ENCOUNTER_ID

		, bp.[ENC_ID Overall Score Order]

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

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9001140203' THEN a.MEAS_VALUE END) AS "BP Girls Percentile"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9001140205' THEN a.MEAS_VALUE END) AS "BP Boys Percentile"

		, MAX(CASE WHEN a.FLO_MEAS_ID = '9000012611' THEN a.MEAS_VALUE END) AS "Circulatory Dysfunction"

	FROM

	(

		SELECT 

			subMeas.ENCOUNTER_ID

			, subMeas.FLO_MEAS_ID

			, subMeas.RECORDED_TIME

			, subMeas.MEAS_VALUE

			, ROW_NUMBER() OVER (PARTITION BY subMeas.ENCOUNTER_ID, subMeas.[ENC_ID Overall Score Order], subMeas.FLO_MEAS_ID ORDER BY subMeas.[ABS Time since OD Score]) rownumber

			, subMeas.[ENC_ID Overall Score Order]

			, subMeas.[ABS Time since OD Score]

		FROM #SepsisAuditTemp subMeas

		WHERE subMeas.ENCOUNTER_ID = bp.ENCOUNTER_ID

		AND subMeas.[ENC_ID Overall Score Order] = bp.[ENC_ID Overall Score Order]

		AND subMeas.MEAS_VALUE IS NOT NULL

	) a

	WHERE a.rownumber = 1

	GROUP BY ENCOUNTER_ID, [ENC_ID Overall Score Order]

) sepsisAudit



--SELECT * FROM #FlwshtLstSepsisAudit WHERE [Circulatory Dysfunction] IS NOT NULL

--/*****************************Clean up tables*****************************/

--IF OBJECT_ID(N'tempdb..#FlwshtLstHuddleODScore') IS NOT NULL DROP TABLE #FlwshtLstHuddleODScore;





/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisScreeningAudit]

	(

		[PATENCENCID],

		[ScoreDate],

		[ODScore],

		[ScoreTime],

		[SepsisPatientHuddleorAlertWithMDPNP],

		[HuddleDate],

		[HuddleTime],

		[PatientAssessedByMDPNP],

		[PhysicianName],

		[AddOrdersReceivedPlacedByMDPNP],

		[AlertNotActivatedReason],

		[AlertNotActivatedComment],

		[AlertActivatedComment],

		[Predisposition],

		[InfectiousSymptoms],

		[HematologicDysfunction],

		[RenalDysfunction],

		[NeurologicalDysfunction],

		[RespiratoryDysfunction],

		[CirculatoryDysfunction],

		[Pulse],

		[Resp],

		[BP],

		[BPGirlsPercentile], 

		[BPBoysPercentile],

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

		[ODScoreIs2],

		[PosODScore],	

		[NoteAuthor],

		[NoteCreatedTime],

		[FifteenthOrEOM],

		[ShiftColorDisplay],

		[UniqueRow],

		[RefreshDate])

SELECT  

	main.ENCOUNTER_ID [ENC_ID]

	, scores.[Score Day]

	, scores.[OD Score]

	, scores.[OD Score Time]

	, scores.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP]

	, scores.[Huddle Date]

	, scores.[Huddle Time]

	, scores.[PATIENTS Assessed by MD/PNP]

	, scores.[Physician Name]

	, scores.[Additional Orders Received/Placed by MD/PNP]

	, scores.[CLINICAL_ALERTS Not Activated Reason]

	, scores.[CLINICAL_ALERTS Not Activated Comment]

	, scores.[CLINICAL_ALERTS Activated Comment]

	, sepsisAudit.[Predisposition]

	, sepsisAudit.[Infectious Symptoms]

	, sepsisAudit.[Hematologic Dysfunction]

	, sepsisAudit.[Renal Dysfunction]

	, sepsisAudit.[Neurological Dysfunction]

	, sepsisAudit.[Respiratory Dysfunction]

	, sepsisAudit.[Circulatory Dysfunction]

	, sepsisAudit.[Pulse]

	, sepsisAudit.[Resp]

	, sepsisAudit.[BP]

	, sepsisAudit.[BP Girls Percentile]

	, sepsisAudit.[BP Boys Percentile]

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

	, CASE WHEN scores.[OD Score] = 2 THEN 1 ELSE 0 END [OD Score 2]

	, CASE WHEN scores.[OD Score] >= 3 THEN 1 ELSE 0 END [+ OD Score]

	, sepsisAlert.[Note Author]

	, sepsisAlert.[Note Created Time]

	, CASE WHEN fyDate.DAY_OF_MONTH = 15 OR fyDate.MONTH_END_DT = scores.[Score Day] THEN 'True' ELSE 'False' END AS [15th or EOM]

	, CASE WHEN scores.[OD Score] IS NULL THEN '#FD625E' ELSE '#73B761' END [Shift Color Display]

	, bp.[Unique Row]

	, GETDATE()

FROM #MainAdmDetails main  

INNER JOIN #Base_Pop bp ON bp.ENCOUNTER_ID = main.ENCOUNTER_ID

INNER JOIN #Base_Pop_OD_Scores scores ON scores.ENCOUNTER_ID = main.ENCOUNTER_ID AND scores.[ENC_ID Order] = bp.[ENC_ID Order]

INNER JOIN reports.FY_DATE_DIMENSION fyDate ON fyDate.CALENDAR_DT = scores.[Score Day]

LEFT OUTER JOIN #FlwshtLstSepsisAudit sepsisAudit ON sepsisAudit.ENCOUNTER_ID = main.ENCOUNTER_ID AND sepsisAudit.[ENC_ID Overall Score Order] = scores.[ENC_ID Overall Score Order]

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

ORDER BY main.ENCOUNTER_ID, scores.[ENC_ID Overall Score Order]

