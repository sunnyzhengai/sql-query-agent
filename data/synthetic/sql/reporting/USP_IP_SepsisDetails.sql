

/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

Date			Who					Description 

----------------------------------------------------------------------------------- 

12/01/2025		Developer C		Separated base query into multiple tables. 

===================================================================================== 

USAGE: 

exec [reporting].[USP_IP_SepsisDetails]

************************************************************************************/ 

CREATE PROCEDURE [reporting].[USP_IP_SepsisDetails]

--DECLARE

@StartDate VARCHAR(20) = NULL,

@EndDate VARCHAR(20) = NULL



AS

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table [reporting].[IP_SepsisDetails];



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

	 PATENCENCID ENCOUNTER_ID

	, PatientID PATIENT_ID

	, PATIENTMRN PATIENT_MRN

	, PatientName PATIENT_NAME

	, EthnicGroup [Ethnic Group]

	, Race [Race]

	, InpatientDataID INPATIENT_DATA_ID

	, ADTArrivalTime ADT_ARRIVAL_TIME

	, HospAdmsnTime HOSP_ADMSN_TIME

	, HospDischTime HOSP_DISCH_TIME

	, InpAdmDate INP_ADM_DATE

	, EDDepartureTime ED_DEPARTURE_TIME

	, Disposition [Disposition]

	, [Location] [Location]

	, AgeMonths [Age At Admission (M)]

	, AgeYears [Age at Admission (Y)]

	, LosHours LOS_HRS

	, BirthDate BIRTH_DATE

	, AllEncDx [AllEncReasons]

INTO #MainAdmDetails

FROM [reporting].[IP_SepsisEncounters]

CREATE INDEX IDX_Main ON #MainAdmDetails (ENCOUNTER_ID)

CREATE INDEX IDX_MainInpID ON #MainAdmDetails (INPATIENT_DATA_ID) 

/*SELECT * FROM #MainAdmDetails*/



/***********************************************************************

Get record for every date the PATIENTS was in a department

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT pd.PATENCENCID [ENCOUNTER_ID]

	, CAST(pd.InDepartmentTime AS DATE) [In Dept Date]

	, CAST(pd.OutDepartmentTime AS DATE) [Out Dept Date]

	, pd.SepsisPatientDate [Sepsis Pt Date]

	, pd.InDepartmentTime [In_DTTM]

	, pd.OutDepartmentTime [Out_DTTM]

	, pd.ADTDepartmentID [ADT_DEPARTMENT_ID]

	, pd.ADTDepartmentName [ADT_DEPARTMENT_NAME]

	, pd.PatientID [PATIENT_ID]

	, pd.DepartmentRollup [DEPARTMENT_ROLLUP]

	, pd.InpatientDataID [INPATIENT_DATA_ID]

	, pd.[AgeOnDateMonths] [AGE_MONTHS]

	, pd.[AgeOnDateYears] [AGE_YEARS]

	, pd.ENCORDER [ENC_ID Order]

	, pd.ENCOVERALLORDER [ENC_ID Overall Order]

	, pd.UnitOrder [Unit Order]

	, CAST(pd.PATENCENCID AS varchar(20)) + '-' + CAST(pd.ENCORDER AS VARCHAR(95)) [Unique Row]

INTO #Base_Pop

FROM [reporting].[IP_SepsisPatientDates] pd

INNER JOIN [reporting].[IP_SepsisEncounters] enc ON enc.PATENCENCID = pd.PATENCENCID

WHERE pd.SepsisPatientDate BETWEEN @dStartDate AND @dEndDate

CREATE INDEX IDX_Base_Pop ON #Base_Pop (ENCOUNTER_ID) 

CREATE INDEX IDX_Base_PopInpIDOnly ON #Base_Pop (INPATIENT_DATA_ID) 

CREATE INDEX IDX_Base_PopDate ON #Base_Pop ([Sepsis Pt Date]) 

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

		, dd.CALENDAR_DT [RecordDate]

		, meas.RECORDED_TIME

		, main.[ENC_ID Order]

		, main.[Unit Order]

		, main.[ENC_ID Overall Order]

		, main.[Sepsis Pt Date]

		, main.ADT_DEPARTMENT_ID

		, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, [ENC_ID Order], [Unit Order] ORDER BY [ENC_ID Order], [Unit Order], RECORDED_TIME) AS [Unit Order Row]

	FROM #Base_Pop main 

	INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '94'	

		AND meas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM

	INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

		AND dd.CALENDAR_DT = main.[Sepsis Pt Date]

) a

WHERE a.[Unit Order Row] = 1

CREATE INDEX IDX_FloEncWeight ON #FlwshtLstEncounterWts (ENCOUNTER_ID) 

--/*SELECT * FROM #FlwshtLstEncounterWts */



/*OD Score*/

IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT main.ENCOUNTER_ID

	, main.[ENC_ID Order]

	, main.[Unit Order]

	, main.[ENC_ID Overall Order]

	, CASE WHEN a.UniqueRow = main.[Unique Row] THEN 'Yes' ELSE 'No' END [+ OD Score in Dept]

	, main.[Sepsis Pt Date]

INTO #Base_Pop_OD_Scores

FROM #Base_Pop main

OUTER APPLY 

( 

	SELECT Distinct aud.UniqueRow 

	FROM [reporting].[IP_SepsisScreeningAudit] aud

	WHERE aud.PATENCENCID = main.ENCOUNTER_ID

	AND aud.PosODScore = 1

	AND aud.UniqueRow = main.[Unique Row]

) a

CREATE INDEX IDX_Base_Pop_OD_Scores ON #Base_Pop_OD_Scores (ENCOUNTER_ID) 

/*SELECT * FROM #Base_Pop_OD_Scores */



/*****************************Hypotension*****************************/

IF OBJECT_ID(N'tempdb..#FlwShtHypo') IS NOT NULL DROP TABLE #FlwShtHypo;

Select

	main.ENCOUNTER_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME [Hypotension Time] 

	, meas.MEAS_VALUE

	, meas.FSD_ID 

	, main.[AGE_MONTHS]

	, main.[AGE_YEARS]

	, main.[ENC_ID Overall Order]

	, bpMeas.MEAS_VALUE [BP Percentile]

	, main.[Sepsis Pt Date]

Into #FlwShtHypo 

FROM #Base_Pop main

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '95' AND meas.MEAS_VALUE IS NOT NULL

	AND meas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM

LEFT JOIN [dbo].[FLOWSHEET_MEASUREMENTS] bpMeas ON bpMeas.FSD_ID = rec.FSD_ID AND bpMeas.RECORDED_TIME = meas.RECORDED_TIME 

	AND bpMeas.FLO_MEAS_ID in ('9001140203', '9001140205') AND bpMeas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE  ( dd.CALENDAR_DT = main.[Sepsis Pt Date]

	AND meas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM )

CREATE INDEX IDX_FlwShtHypo ON #FlwShtHypo (ENCOUNTER_ID, [ENC_ID Overall Order])

/*SELECT * FROM #FlwShtHypo*/



IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;

SELECT    

	base.ENCOUNTER_ID

	, base.AGE_MONTHS

	, base.AGE_YEARS

	, base.In_DTTM InDepartmentTime    

	, hypo.[Hypotension Value]    

	, meas.[Hypotension Time]    

	, systolic.SYSTOLIC    

	, base.[ENC_ID Order]

	, base.[Unit Order]

	, base.[ENC_ID Overall Order]

	, base.[Sepsis Pt Date]

	, meas.[BP Percentile]

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[ENC_ID Order], base.[Unit Order] ORDER BY base.[ENC_ID Overall Order] ASC) AS TIME_LINE 

INTO #Hypotension 

FROM #Base_Pop base 

INNER JOIN #FlwShtHypo meas ON meas.ENCOUNTER_ID = base.ENCOUNTER_ID AND meas.[ENC_ID Overall Order] = base.[ENC_ID Overall Order] AND meas.[Sepsis Pt Date] = base.[Sepsis Pt Date]

CROSS APPLY ( SELECT LEFT(meas.MEAS_VALUE, CHARINDEX('/', meas.MEAS_VALUE)-1) SYSTOLIC ) systolic 

CROSS APPLY (    

	SELECT CASE WHEN base.[Sepsis Pt Date] < '11/95/2025' THEN       

		CASE 

			WHEN            

				(base.AGE_MONTHS < 2 AND systolic.SYSTOLIC < 65)            

				OR ((base.AGE_MONTHS >= 2 AND base.AGE_MONTHS < 12) AND systolic.SYSTOLIC < 70)            

				OR ((base.AGE_YEARS >= 1 AND base.AGE_YEARS < 2) AND systolic.SYSTOLIC < 80)            

				OR ((base.AGE_YEARS >= 2 AND base.AGE_YEARS < 6) AND systolic.SYSTOLIC < 90)            

				OR ((base.AGE_YEARS >= 6 AND base.AGE_YEARS < 13) AND systolic.SYSTOLIC < 100)            

				OR (base.AGE_YEARS >= 13 AND systolic.SYSTOLIC < 110)        

			THEN meas.MEAS_VALUE    

			ELSE NULL    

			END 

		WHEN     -- After 11/95/2025        

			(base.AGE_MONTHS < 2 AND systolic.SYSTOLIC < 56)            

			OR ((base.AGE_MONTHS >= 2 AND base.AGE_YEARS < 6) AND systolic.SYSTOLIC < 65)  

			OR ((base.AGE_MONTHS >= 6 AND base.AGE_MONTHS < 12) AND systolic.SYSTOLIC < 70)            

			OR ( (base.AGE_YEARS >= 1 AND base.AGE_YEARS < 13) AND meas.[BP Percentile] < 10)  

			OR (base.AGE_YEARS >= 13 AND systolic.SYSTOLIC < 100)

		THEN meas.MEAS_VALUE    

		ELSE NULL

	END AS [Hypotension Value] ) 

hypo 

WHERE hypo.[Hypotension Value] IS NOT NULL -- Only show where PATIENTS is Hypotensive

CREATE INDEX IDX_ODHYPO ON #Hypotension (ENCOUNTER_ID) 

/*SELECT * FROM #Hypotension ORDER BY [ENC_ID Order], [ENC_ID Overall Order], TIME_LINE */

/*****************************END OF HYPO*****************************/



/*****************************ABX*****************************/

/*All encounters from #Base_pop where ABX was administered*/

IF OBJECT_ID(N'tempdb..#BasePopABX') IS NOT NULL DROP TABLE #BasePopABX;

SELECT

	MO.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, med.NAME

	, mar.TAKEN_TIME AS ABX_ADMIN_TIME

	, mar.SIG AS BOLUS_VOLUME

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

	, ROW_NUMBER() OVER(PARTITION BY MO.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY mar.TAKEN_TIME) TIME_LINE

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

AND (CAST(mar.TAKEN_TIME AS DATE) = base.[Sepsis Pt Date]

	AND mar.TAKEN_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_BasePopABX ON #BasePopABX (ENCOUNTER_ID) 

/*SELECT * FROM #BasePopABX*/



/*****************************ORDER SET*****************************/

/*All encounters from #Base_pop where Bolus was administered*/

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

SELECT DISTINCT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, MO.ORDER_DTTM

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY MO.ORDER_DTTM ASC) AS TIME_LINE

	, MO.PRL_ORDERSET_ID

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

INTO #SSOrderSet 

FROM #Base_Pop base

INNER JOIN [dbo].ORDER_TRACKING_METRICS MO ON MO.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(MO.ORDER_DTTM AS Date)

WHERE MO.PRL_ORDERSET_ID IN (400001) /*(40400100, 40400058, 40400196, 40400153, 4058600002, 400001) Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway*/

AND (CAST(MO.ORDER_DTTM AS DATE) = base.[Sepsis Pt Date]

	AND MO.ORDER_DTTM between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_SSOrderSet ON #SSOrderSet (ENCOUNTER_ID) 

/*SELECT * FROM #SSOrderSet*/



/*****************************BOLUS*****************************/

IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, mar.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, med.NAME AS Medication

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY mar.TAKEN_TIME ASC) TIME_LINE

	, mar.SIG AS BOLUS_VOLUME

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

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

AND (CAST(mar.TAKEN_TIME AS DATE) = base.[Sepsis Pt Date]

	AND mar.TAKEN_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_BasePopBolus ON #BasePopBolus (ENCOUNTER_ID) 

/*SELECT * FROM #BasePopBolus*/



/*****************************PRESSORS TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;

SELECT DISTINCT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, mar.TAKEN_TIME

	, gmr.GROUPER_ID

	, MEDS.NAME AS MEDICATION

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY mar.TAKEN_TIME) AS TIME_LINE

	, base.[Sepsis Pt Date]

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

AND (CAST(mar.TAKEN_TIME AS DATE) = base.[Sepsis Pt Date]

	AND mar.TAKEN_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_Pressors ON #Pressors (ENCOUNTER_ID) 

/*SELECT * FROM #Pressors*/



IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

SELECT p.ENCOUNTER_ID

	, p.[Sepsis Pt Date] [Sepsis_Date]

	, CASE WHEN p.GROUPER_ID = '8000100'   THEN 'EPINEPHRINE' /*HS RX EPINEPHRINE SEPSIS*/

		WHEN p.GROUPER_ID =  '8000101' THEN 'DOPAMINE'

		WHEN p.GROUPER_ID = '8000102'   THEN 'DOBUTAMINE'

		WHEN p.GROUPER_ID = '8000103'   THEN 'MILRINONE'

		WHEN p.GROUPER_ID = '8000104'   THEN 'NOREPINEPHRINE'

	END PRESSOR

	, COUNT(p.TAKEN_TIME) AS MYC

INTO #ODPressorSummary

FROM #Pressors p

GROUP BY p.ENCOUNTER_ID, p.GROUPER_ID, p.[Sepsis Pt Date]

CREATE INDEX IDX_ODPressorSummary ON #ODPressorSummary (ENCOUNTER_ID) 

/*SELECT * FROM #ODPressorSummary*/



IF OBJECT_ID ('TEMPDB..#ODPressorPivot') IS NOT NULL DROP TABLE #ODPressorPivot

SELECT ENCOUNTER_ID

	, Sepsis_Date

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



/*****************************LACTIC ACID TIMES*****************************/

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, PO.ORDER_PROC_ID

	, PO.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY PO.ORDER_TIME, base.IN_DTTM, ordR.RESULT_TIME ASC) AS TIME_LINE -- Developer C added Result time

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

INTO #LacticAcid

FROM #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] ordR ON ordR.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO ON PO.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID IN (SELECT * FROM #LacticAcidLRR)

AND (CAST(PO.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND PO.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_LacticAcid ON #LacticAcid (ENCOUNTER_ID) 

/*SELECT * FROM #LacticAcid */



/*****************************PROCALCITONIN TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, PO.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY PO.ORDER_TIME ASC) AS TIME_LINE

	, ordR.ORDER_PROC_ID

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

INTO #Procalcitonin

FROM  #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] ordR ON ordR.ENCOUNTER_ID = base.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO ON PO.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID = 500001 /*COULD USE PROC CODE ALSO.... LAB014*/

AND (CAST(PO.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND PO.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_Procalcitonin ON #Procalcitonin (ENCOUNTER_ID) 

/*SELECT * FROM #Procalcitonin*/



/*****************************BLOOD CULTURE TIMES*****************************/

/*Blood Culture*/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

SELECT base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, PO.ORDER_PROC_ID

	, PCAT.PROC_CODE AS [Blood Culture Procedure Ordered]

	, PO.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, CASE WHEN res.ORD_VALUE LIKE '%No growth%' THEN 'Negative' ELSE 'Positive' END [Order Result]

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY PO.ORDER_TIME, res.RESULT_TIME ASC) AS TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

INTO #BloodCultureValue 

FROM #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] res ON base.ENCOUNTER_ID = res.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO  ON res.ORDER_PROC_ID = PO.ORDER_PROC_ID 

			AND PO.PROC_ID IN (SELECT * FROM #BloodCultures)

INNER JOIN [dbo].[PROCEDURES_CATALOG] PCAT ON PCAT.PROC_ID = PO.PROC_ID

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

WHERE (CAST(PO.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND PO.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_BloodCultureValue ON #BloodCultureValue (ENCOUNTER_ID) 

/*SELECT * FROM #BloodCultureValue*/



/*****************************CSF TIMES*****************************/

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

SELECT

	base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, PO.ORDER_PROC_ID

	, PCAT.PROC_CODE as [CSF Procedure Ordered]

	, PO.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY PO.ORDER_TIME ASC) AS TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

INTO #CSF 

FROM #Base_Pop base

INNER JOIN [dbo].[LAB_ORDER_RESULTS] res ON base.ENCOUNTER_ID = res.ENCOUNTER_ID

INNER JOIN [dbo].[PROCEDURE_ORDERS] PO  ON res.ORDER_PROC_ID = PO.ORDER_PROC_ID

			AND PROC_ID IN (600005, 600006) AND PO.SPECIMEN_SOURCE_CODE = 304

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(PO.ORDER_TIME AS DATE)

INNER JOIN [dbo].[PROCEDURES_CATALOG] PCAT ON PCAT.PROC_ID = PO.PROC_ID

WHERE (CAST(PO.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND PO.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_CSF ON #CSF (ENCOUNTER_ID) 

/*SELECT * FROM #CSF*/



/*****************************ETT TIMES*****************************/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

SELECT base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

INTO #ETT

FROM #Base_Pop base

INNER JOIN [dbo].[LINE_DEVICE_AIRWAY] lda ON lda.ENCOUNTER_ID = base.ENCOUNTER_ID AND lda.FLO_MEAS_ID = '900112' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

WHERE (CAST(lda.PLACEMENT_INSTANT AS DATE) = base.[Sepsis Pt Date]

	AND lda.PLACEMENT_INSTANT between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_ETT ON #ETT (ENCOUNTER_ID) 

/*SELECT * FROM #ETT WHERE TIME_LINE = 1*/



/*****************************PIV TIMES*****************************/

IF OBJECT_ID(N'tempdb..#PIV') IS NOT NULL DROP TABLE #PIV;

SELECT base.ENCOUNTER_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.ENCOUNTER_ID, base.[Sepsis Pt Date] ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[ENC_ID Overall Order]

INTO #PIV

FROM #Base_Pop base

INNER JOIN [dbo].[LINE_DEVICE_AIRWAY] lda ON lda.ENCOUNTER_ID = base.ENCOUNTER_ID AND lda.FLO_MEAS_ID='900111' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

WHERE (CAST(lda.PLACEMENT_INSTANT AS DATE) = base.[Sepsis Pt Date]

	AND lda.PLACEMENT_INSTANT between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_PIV ON #PIV (ENCOUNTER_ID) 

/*SELECT * FROM #PIV WHERE TIME_LINE = 1*/



/*****************************CVVH*****************************/

IF OBJECT_ID(N'tempdb..#CVVH') IS NOT NULL DROP TABLE #CVVH;

SELECT base.ENCOUNTER_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS CVVH_FLAG

	, base.[ENC_ID Overall Order]

	, base.[Sepsis Pt Date]

INTO #CVVH

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID AND meas.FLT_ID='9000001359'--ANY FLOWSHEET FROM THIS TEMPLATE IS A CANDIDATE

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE (dd.CALENDAR_DT = base.[Sepsis Pt Date]

	AND meas.RECORDED_TIME between base.In_DTTM AND base.Out_DTTM

	)

GROUP BY base.ENCOUNTER_ID, base.[ENC_ID Overall Order], base.[Sepsis Pt Date]

CREATE INDEX IDX_CVVH ON #CVVH (ENCOUNTER_ID) 

/*SELECT * FROM #CVVH*/

/*****************************END OF CVVH*****************************/



/*****************************CEREBRAL OX MONITORING*****************************/

IF OBJECT_ID(N'tempdb..#OX') IS NOT NULL DROP TABLE #OX;

SELECT base.ENCOUNTER_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS OX_FLAG

	, base.[ENC_ID Overall Order]

	, base.[Sepsis Pt Date]

INTO #OX

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

/* Developer C VCG Grouper 800015*/

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

AND meas.FLO_MEAS_ID IN ('900201', '900202', '900203', '9000001977') /*(SELECT * FROM #CerebralOxFLO)*/

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE (dd.CALENDAR_DT = base.[Sepsis Pt Date]

	AND meas.RECORDED_TIME between base.In_DTTM AND base.Out_DTTM

	)

GROUP BY base.ENCOUNTER_ID, base.[ENC_ID Overall Order], base.[Sepsis Pt Date]

CREATE INDEX IDX_OX ON #OX (ENCOUNTER_ID) 

/*SELECT * FROM #OX*/

/*****************************END OF CEREBRAL OX MONITORING*****************************/



/*****************************ECMO*****************************/

IF OBJECT_ID(N'tempdb..#ECMO') IS NOT NULL DROP TABLE #ECMO;

SELECT base.ENCOUNTER_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS ECMO_FLAG

	, base.[ENC_ID Overall Order]

	, base.[Sepsis Pt Date]

INTO #ECMO

FROM #Base_Pop base

INNER JOIN [dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

	AND meas.FLO_MEAS_ID ='9000101014' /*9000101014	R ECMO ON/OFF*/

INNER JOIN [dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE (dd.CALENDAR_DT = base.[Sepsis Pt Date]

	AND meas.RECORDED_TIME between base.In_DTTM AND base.Out_DTTM

	)

GROUP BY base.ENCOUNTER_ID, base.[ENC_ID Overall Order], base.[Sepsis Pt Date]

CREATE INDEX IDX_ECMO ON #ECMO (ENCOUNTER_ID) 

/*SELECT * FROM #ECMO*/

/*****************************END OF ECMO*****************************/



----/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisDetails]

	( [PATENCENCID],

	[SepsisDate],

	[HypotensionTime],

	[HypotensionValue],

	[BPPercentile],

	[EncounterWeight],

	[PositiveODScore],

	[ABXVolume],

 	[ABXTime],

	[ABXName],

	[Bolus],

	[BolusVolume],

	[BolusTime],

	[LacticAcidOrderTime],

	[LacticAcidResult],

	[OrderSetTime],

	[OrderSetID],

	[ProcalcitoninOrderTime],

	[ProcalcitoninResult],

	[BloodCultureOrderTime],

	[BloodCultureProcedureOrdered],

	[BloodCultureResult],

	[CSFOrderTime],

	[CSFOrdered],

	[CSFValue],

	[PIVPlacementTime],

	[IntubationTime],

	[DobutamineYN],

	[DopamineYN],

	[EpinephrineYN],

	[MilrinoneYN],

	[NorepinephrineYN],

	[PressorYN],

	[CVVHYN],

	[OXYN],

	[ECMOYN],

	[IPSOSevereSepsisYN],

	[ENCORDER],

	[UnitOrder],

	[ENCOVERALLORDER],

	[UniqueRow],

	[RefreshDate]

	)

SELECT main.ENCOUNTER_ID [ENC_ID]

	, bp.[Sepsis Pt Date] [Sepsis PATIENTS Date]

	, hypo.[Hypotension Time]

	, hypo.[Hypotension Value]

	, hypo.[BP Percentile]

	, wght.MEAS_VALUE [Enc Weight]

	, scores.[+ OD Score in Dept] [Positive OD Score]



	, abx.BOLUS_VOLUME [ABX Volume]

	, abx.ABX_ADMIN_TIME [ABX TIme]

	, abx.NAME [ABX Name]

	, bol.Medication [Bolus Medication]

	, bol.BOLUS_VOLUME [Bolus Volume]

	, bol.BOLUS_ADMIN_TIME [Bolus Time]

	, la.MBOrderTime [Lactic Acid Order Time]

	, la.ORD_VALUE [Lactic Acid Result]

	, ordSet.ORDER_DTTM [Order Set Time]

	, ordSet.PRL_ORDERSET_ID [Order Set ID]



	, proCal.MBOrderTime [Procalcitonin Order Time]

	, proCal.ORD_VALUE [Procalcitonin Result]

	, bc.MBOrderTime [Blood Culture Order Time]

	, bc.[Blood Culture Procedure Ordered] [Blood Culture Procedure Ordered]

	, bc.ORD_VALUE [Blood Culture Result]

	, csf.MBOrderTime [CSF Order Time]

	, csf.[CSF Procedure Ordered] [CSF Ordered]

	, csf.ORD_VALUE [CSF Value]

	, piv.PLACEMENT_INSTANT [PIV Placement Time]

	, ett.PLACEMENT_INSTANT [Intubation Time]

	, CASE WHEN pressor.DOBUTAMINE IS NOT NULL THEN 'Y' END DOBUTAMINE

	, CASE WHEN pressor.DOPAMINE IS NOT NULL THEN 'Y' END DOPAMINE

	, CASE WHEN pressor.EPINEPHRINE IS NOT NULL THEN 'Y' END EPINEPHRINE

	, CASE WHEN pressor.MILRINONE IS NOT NULL THEN 'Y' END MILRINONE

	, CASE WHEN pressor.NOREPINEPHRINE IS NOT NULL THEN 'Y' END NOREPINEPHRINE

	, CASE WHEN (

				pressor.DOBUTAMINE IS NOT NULL OR

				pressor.DOPAMINE IS NOT NULL OR

				pressor.EPINEPHRINE IS NOT NULL OR

				pressor.MILRINONE IS NOT NULL OR

				pressor.NOREPINEPHRINE IS NOT NULL) THEN 'Y'END AS [PRESSOR Y/N]

	, cvvh.CVVH_FLAG AS [CVVH Y/N]

	, ox.OX_FLAG AS [OX Y/N]

	, ecmo.ECMO_FLAG AS [ECMO Y/N]



	, CASE WHEN SSS.ENCOUNTER_ID IS NULL THEN 'N' ELSE 'Y' END SEVERE_SEPSIS_STAGING

	, bp.[ENC_ID Order]

	, bp.[Unit Order]

	, bp.[ENC_ID Overall Order]

	, CAST(bp.ENCOUNTER_ID AS varchar(20)) + '-' + CAST(bp.[ENC_ID Order] AS VARCHAR(95)) [Unique Row]

	, GETDATE()

FROM #Base_Pop bp -- reporting.IP_SepsisPatientDates pd

INNER JOIN #MainAdmDetails main ON main.ENCOUNTER_ID = bp.ENCOUNTER_ID

INNER JOIN #Base_Pop_OD_Scores scores ON scores.ENCOUNTER_ID = bp.ENCOUNTER_ID AND scores.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

INNER JOIN reports.FY_DATE_DIMENSION fyDate ON fyDate.CALENDAR_DT = bp.[Sepsis Pt Date]

LEFT OUTER JOIN #FlwshtLstEncounterWts wght ON wght.ENCOUNTER_ID = bp.ENCOUNTER_ID AND wght.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND wght.[Unit Order] = 1

LEFT OUTER JOIN #Hypotension hypo ON hypo.ENCOUNTER_ID = bp.ENCOUNTER_ID AND hypo.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND hypo.TIME_LINE = 1

LEFT OUTER JOIN #BasePopABX abx ON abx.ENCOUNTER_ID = bp.ENCOUNTER_ID AND abx.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND abx.TIME_LINE = 1

LEFT OUTER JOIN #BasePopBolus bol ON bol.ENCOUNTER_ID = bp.ENCOUNTER_ID AND bol.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND bol.TIME_LINE = 1

LEFT OUTER JOIN #LacticAcid la ON la.ENCOUNTER_ID = bp.ENCOUNTER_ID AND la.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND la.TIME_LINE = 1

LEFT OUTER JOIN #SSOrderSet ordSet ON ordSet.ENCOUNTER_ID = bp.ENCOUNTER_ID AND ordSet.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND ordSet.TIME_LINE = 1

LEFT OUTER JOIN #ODPressorPivot pressor ON pressor.ENCOUNTER_ID = scores.ENCOUNTER_ID AND bp.[Sepsis Pt Date] = pressor.Sepsis_Date 

LEFT OUTER JOIN #Procalcitonin proCal ON proCal.ENCOUNTER_ID = bp.ENCOUNTER_ID AND proCal.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND proCal.TIME_LINE = 1

LEFT OUTER JOIN #BloodCultureValue bc ON bc.ENCOUNTER_ID = bp.ENCOUNTER_ID AND bc.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND bc.TIME_LINE = 1

LEFT OUTER JOIN #CSF csf ON csf.ENCOUNTER_ID = bp.ENCOUNTER_ID AND csf.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND csf.TIME_LINE = 1

LEFT OUTER JOIN #PIV piv ON piv.ENCOUNTER_ID = bp.ENCOUNTER_ID AND piv.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND piv.TIME_LINE = 1

LEFT OUTER JOIN #ETT ett ON ett.ENCOUNTER_ID = bp.ENCOUNTER_ID AND ett.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order] AND ett.TIME_LINE = 1

LEFT OUTER JOIN #CVVH cvvh ON cvvh.ENCOUNTER_ID = scores.ENCOUNTER_ID AND cvvh.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #OX ox ON ox.ENCOUNTER_ID = scores.ENCOUNTER_ID AND ox.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN #ECMO ecmo ON ecmo.ENCOUNTER_ID = bp.ENCOUNTER_ID AND ecmo.[ENC_ID Overall Order] = bp.[ENC_ID Overall Order]

LEFT OUTER JOIN [reports].[SEVERE_SEPSIS_STAGING] SSS ON SSS.ENCOUNTER_ID = main.ENCOUNTER_ID



WHERE ( scores.[+ OD Score in Dept] = 'Y'

	OR wght.[Unit Order] = 1

	OR hypo.TIME_LINE = 1

	OR abx.TIME_LINE = 1

	OR bol.TIME_LINE = 1

	OR la.TIME_LINE = 1

	OR ordSet.TIME_LINE = 1

	OR pressor.ENCOUNTER_ID IS NOT NULL

	OR proCal.TIME_LINE = 1

	OR bc.TIME_LINE = 1

	OR csf.TIME_LINE = 1

	OR piv.TIME_LINE = 1

	OR ett.TIME_LINE = 1

	OR cvvh.ENCOUNTER_ID IS NOT NULL

	OR ox.ENCOUNTER_ID IS NOT NULL

	OR ecmo.ENCOUNTER_ID IS NOT NULL

)

ORDER BY bp.ENCOUNTER_ID, bp.[Sepsis Pt Date], bp.[ENC_ID Overall Order]

END 

