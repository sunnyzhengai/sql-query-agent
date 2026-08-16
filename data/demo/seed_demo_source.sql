-- Seed script for the demo source database (aivia_demo_src)
-- Generated from data/synthetic/sql (28 anonymized procs).
-- Run in the Fabric SQL database query editor (or SSMS).

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'reporting')
    EXEC('CREATE SCHEMA reporting');
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'reports')
    EXEC('CREATE SCHEMA reports');
GO

-- ==== reporting/USP_ED_Sepsis.sql ====
/**********************************************************************************************************

Author: <Unknown>

Create date:  <Unknown>

Description:  

Report Name: BI-Health System --> Quality --> ED Sepsis

==========================================================================================================

Revision Detail 



Date			Who						Description 

----------------------------------------------------------------------------------------------------------

2019.05.16		V_DEV001				[PROCEDURE_ORDERS].PROC_CODE is deprecated as of april 2019; Replacing it with PROC_ID.

2019.07.19		V_DEV001				MAR_ACTION_C changed data type from INT to VARCHAR.

2019.10.01		V_DEV001				Added new Sepsis Score Flowsheet ID '9000002613'

2019.11.07		V_DEV001				Added Quick Set/ OrdersetS OSQ: 

											- ED Sepsis Panel - OSQ 400002

											- Sepsis Antimicrobials Unknown Source - OSQ 400007

											- Neo Fever Panel - OSQ 400003

											- Oncology with Fever Panel - OSQ 400004

2019.11.08		V_DEV001				Updated calculation to include Triage Stop Time instead of Triage Start Time

2019.12.11		V_DEV001				Added First ABX Order and its related Pharmacy times

2020.04.10		V_DEV001				Added First and Last Blood Pressure information and ED Border Flag

2020.09.21		V_DEV001				Added Compliance for (FPS + ABX/ Bolus/ Rescreen):

											- Rescreen One Hour before Transfer/ Discharge

											- ED 2 PICU/ ED 2 Floor and then ICU

											- ED IP Bed assignment to IP Transfer Metric

											- ABX given only in ED setting

2020.10.29		V_DEV001				Set TRANSACTION ISOLATION LEVEL READ UNCOMMITTED

2020.11.17		V_DEV001				Set end date to T-1

2021.02.03		V_DEV001				Added first sepsis score day/night shift

2021.03.24		V_DEV001				Added PATIENTS's race and ethnic group info

2023.06.15		V_DEV003				Added age in days for 21 days or less age filter, and modified months age to include FLOOR



2025.08.06		V_DEV004				Added #SepsisAlertCancelled columns

2025.08.26		V_DEV004				Added Urine Culture Results, Organism name to Blood/CSF, and corrected Blood/CSF code

2025.10.06		V_DEV004				Added BP percentile Flowsheets [9001140203, 9001140205] (per TKT-009)

2025.12.07		V_DEV004				Added [Septic Shock] and [Blood Culture First Order Time] columns

2025.01.13		V_DEV004				Re-factored, added [Any BP During ED Stay?], [Last BP to First Negative Score Time], [First Negative Score Time to First BP]

											and changed existing BP-logic to pull first BP timing/value regardless of test result (TKT-010)

2026.04.10		V_DEV004				Added PRL [4001326023] and OSQs [400005, 400006, 4001326025] to the existing lists referenced (TKT-011)

==========================================================================================================

USAGE: 

	exec [reportingDB].[reporting].[USP_ED_Sepsis] 'MB-1', 'ME-1' 

**********************************************************************************************************/ 





CREATE         PROCEDURE [reporting].[USP_ED_Sepsis] (

	@StartDate VARCHAR(20) = NULL,

	@EndDate VARCHAR(20) = NULL

)



AS



SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

DECLARE @dStartDate DATE;

DECLARE @dEndDate DATE;



	

IF @StartDate IS NULL OR @StartDate = ''

	SET @dStartDate = EMRDB.[dbo].[fn_parse_date]('MB-12')

ELSE

	SET @dStartDate = EMRDB.[dbo].[fn_parse_date](@StartDate)

	

IF @EndDate IS NULL OR @EndDate = ''

	SET @dEndDate = EMRDB.[dbo].[fn_parse_date]('T-1')

ELSE

	SET @dEndDate = EMRDB.[dbo].[fn_parse_date](@EndDate)





--SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

--SET NOCOUNT ON;



--DECLARE @dStartDate DATE = '2025-01-01';

--DECLARE @dEndDate DATE = '2025-12-31';





/* ************** */

/* Base ED Visits */

/* ************** */

DROP TABLE IF EXISTS #Base_Pop;



SELECT DISTINCT

	PEH.PAT_ENC_CSN_ID

	, PEH.PAT_ID

	, PAT.PAT_MRN_ID

	, PAT.PAT_NAME

	, ZEG.NAME AS [Ethnic Group]

	, ZPR.NAME AS [Race]

	, FEE.AGE_AT_ARRIVAL_MONTHS

	, FEE.AGE_AT_ARRIVAL_YEARS

	, PEH.INPATIENT_DATA_ID

	, PEH.ADT_ARRIVAL_TIME

	, DEE.TRIAGE_START_DTTM

	, DEE.TRIAGE_END_DTTM

	, PEH.HOSP_ADMSN_TIME

	, PEH.HOSP_DISCH_TIME

	, PEH.INP_ADM_DATE

	, PEH.ED_DEPARTURE_TIME

	, PEH.ED_DISPOSITION_C

	, ZED.NAME AS [Disposition]

	, LOC.LOCATION_ABBR [Location]

	, FLOOR(DATEDIFF(day,PAT.BIRTH_DATE,PEH.ADT_ARRIVAL_TIME)) AS AGE_IN_DAYS ---ADDED V_DEV003 6/15/2023 TKT-007 

	, FLOOR(DATEDIFF(MM,PAT.BIRTH_DATE,COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.ADT_ARRIVAL_TIME)) ) AS AGE_MONTHS  ---ADDED V_DEV003 6/15/2023 TKT-007  (AGE IN MONTHS IS SHOWING AS 1 WHEN ITS ONLY 2 WEEKS, ETC.)

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.ADT_ARRIVAL_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,PEH.ADT_ARRIVAL_TIME)) + DATENAME(YEAR, CONVERT(DATE, PEH.ADT_ARRIVAL_TIME)) AS DATE_STAMP



INTO #Base_Pop



FROM [EMRDB].[dbo].ED_ENCOUNTERS_FACT FEE



	INNER JOIN [EMRDB].[dbo].HOSPITAL_ENCOUNTERS PEH ON FEE.PAT_ENC_CSN_ID = PEH.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PAT_ENC_CSN_ID = FEE.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ED_DISPOSITION ZED ON ZED.ED_DISPOSITION_C = PEH.ED_DISPOSITION_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ETHNIC_GROUP ZEG ON ZEG.ETHNIC_GROUP_C = PAT.ETHNIC_GROUP_C

	LEFT OUTER JOIN [EMRDB].[dbo].PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PAT_ID = PAT.PAT_ID AND RACE.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].REF_PATIENT_RACE ZPR ON ZPR.PATIENT_RACE_C = RACE.PATIENT_RACE_C

	LEFT OUTER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = PEH.DEPARTMENT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].LOCATIONS LOC ON LOC.LOC_ID = DEP.REV_LOC_ID



WHERE FEE.ADT_ARRIVAL_DATE BETWEEN @dStartDate AND @dEndDate

;



CREATE NONCLUSTERED INDEX INX_Base_Pop_CSN ON #Base_Pop ([PAT_ENC_CSN_ID]);









/* ****************************************************************************************************************



													MEDICATIONS



******************************************************************************************************************/



-- All (intravenous) medications given prior to ED departure (used for Abx, Bolus, Pressors tables)

SELECT

	OM.PAT_ENC_CSN_ID

	, OM.ORDER_MED_ID

	, MAI.TAKEN_TIME

	, [ERX].[NAME] AS MEDICATION_NAME

	, [ERX].THERA_CLASS_C

	, OM.MED_ROUTE_C

	, MAI.MAR_ACTION_C

	, OM.MEDICATION_ID

	, OM.HV_DISCR_FREQ_ID

	, MAI.SIG

	, B.ADT_ARRIVAL_TIME

	, B.ED_DEPARTURE_TIME



INTO #AllMeds



FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.MEDICATIONS ERX ON [ERX].MEDICATION_ID = OM.MEDICATION_ID

	INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID



WHERE 1=1

	AND MAI.TAKEN_TIME IS NOT NULL

	AND MAI.TAKEN_TIME < B.ED_DEPARTURE_TIME	-- while in ED

	AND MED_ROUTE_C = 11 -- intravenous

	AND MAR_ACTION_C IN ('1'		--GIVEN

						, '7'		--RESTARTED

						, '102'		--GIVEN BY OTHER

						, '105'		--NEW CARTRIDGE

						, '113'		--GIVEN DURING DOWNTIME

						, '114'		--STARTED DURING DOWNTIME

						, '115'		--MEDICATION APPLIED

						, '122'		--CONTINUED FROM OR

						, '124'		--SELF ADMINISTERED VIA PUMP

						, '132'		--CONTINUED FROM PREVIOUS ORDER

						, '143'		--REDOSE

						, '1604'	--INFUSION GREATER THAN 15 MIN

						, '1605'	--INFUSION LESS THAN 15 MIN

						, '1607'	--NEW CARTRIDGE

						, '6'		--NEW BAG

						, '99'		--RATE CHANGE

						)

;





/* ******************************** */

/* Encounters with ABX administered */

/* ******************************** */

-- All encounters from where ABX was administered

DROP TABLE IF EXISTS #BasePopABX;



WITH ABX AS 

(

	SELECT

		PAT_ENC_CSN_ID

		, ORDER_MED_ID

		, TAKEN_TIME AS ABX_ADMIN_TIME

		, MEDICATION_NAME



	FROM #AllMeds



	WHERE 1=1

		AND TAKEN_TIME < ED_DEPARTURE_TIME	-- including prior to "Arrival"

		AND MEDICATION_ID IN 

			(

				-- mixtures with antibiotics

				select medlist.MEDICATION_ID

					from

						(

							SELECT 

								erx.MEDICATION_ID

								--,erx.NAME

								--,cntl.VALUE_SET_DISPLAY as AGENT

								--,case when CHARINDEX('^',cntl.VALUE_SET_ABBR)>0 then SUBSTRING(cntl.VALUE_SET_ABBR,0,CHARINDEX('^',cntl.VALUE_SET_ABBR)) else cntl.VALUE_SET_ABBR end as AGENT_GROUP

								--,case when cntl.VALUE_SET_ABBR like '%^Y' then 1 else 0 end as DOT_MONITORING

								--,gen.TITLE

								,ROW_NUMBER() OVER(PARTITION BY erx.MEDICATION_ID ORDER BY [cntl].VALUE_SET_ABBR, [cntl].VALUE_SET_DISPLAY ASC) AS AGENT_ORDER



							FROM [EMRDB].[dbo].MEDICATIONS erx

								OUTER APPLY (

									--Get the main medication's simple generic if its a mixture

									SELECT TOP 1 

										mix.DRUG_ID,

										comp.SIMPLE_GENERIC_C 

									FROM [EMRDB].[dbo].MED_MIX_COMPONENTS mix

										INNER JOIN [EMRDB].[dbo].MEDICATIONS comp ON mix.DRUG_ID = comp.MEDICATION_ID

									WHERE 1=1

										AND mix.TYPE_C = 3 -- Medications 

										AND mix.MEDICATION_ID = erx.MEDICATION_ID

									ORDER BY

										mix.LINE

								) mixture



								INNER JOIN [EMRDB].[dbo].REF_GENERIC_MED		gen ON gen.SIMPLE_GENERIC_C = COALESCE(erx.SIMPLE_GENERIC_C, mixture.SIMPLE_GENERIC_C)

								INNER JOIN [reportingDB].[reports].CONFIG_VALUE_SET cntl ON cntl.VALUE_SET_ID=3016 AND cntl.CODE = gen.SIMPLE_GENERIC_C

						) medlist

					WHERE

						medlist.AGENT_ORDER=1						

			)



	UNION



	SELECT DISTINCT

		PAT_ENC_CSN_ID

		, ORDER_MED_ID

		, TAKEN_TIME AS ABX_ADMIN_TIME

		, MEDICATION_NAME



	FROM #AllMeds



	WHERE 1=1

		AND THERA_CLASS_C = 11 --Antibiotics

		AND TAKEN_TIME < ED_DEPARTURE_TIME	-- including prior to "Arrival"

)



SELECT

	PAT_ENC_CSN_ID

	,ORDER_MED_ID

	,MEDICATION_NAME

	,ABX_ADMIN_TIME

	,ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY ABX_ADMIN_TIME) TIME_LINE



INTO #BasePopABX

FROM ABX						

;





/* ******************* */

/* Bolus               */

/* ******************* */

DROP TABLE IF EXISTS #BasePopBolus;



SELECT

	PAT_ENC_CSN_ID

	, TAKEN_TIME AS BOLUS_ADMIN_TIME

	, CASE	WHEN MEDICATION_ID IN (700001, 700002) THEN 'SODIUM CHLORIDE 0.99%'

			ELSE MEDICATION_NAME

	  END AS Medication

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY TAKEN_TIME ASC) AS TIME_LINE

	, SIG AS BOLUS_VOLUME



INTO #BasePopBolus 

FROM #AllMeds

WHERE 1=1

	AND TAKEN_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

	AND HV_DISCR_FREQ_ID = '300902'	-- EFQ .1 (frequency = once)

	AND CONVERT(NUMERIC, SIG) > 95.0

	AND MEDICATION_ID IN (700001	--SODIUM CHLORIDE 0.99 % IV BOLUS

						, 7000739	--LACTATED RINGERS IV BOLUS

						, 700003		--ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION

						, 7006331	--ELECTROLYE-A IV Bolus (PLASMALYTE)

						, 700002		--SODIUM CHLORIDE 0.99 % INJECTION SYRINGE

						, 700004		--SODIUM CHLORIDE 0.99 % INJECTION SOLUTION 

						)

GROUP BY

	PAT_ENC_CSN_ID

	, TAKEN_TIME

	, SIG

	, MEDICATION_ID

	, MEDICATION_NAME

;





/* ******************* */

/* Presssors           */

/* ******************* */

DROP TABLE IF EXISTS #Pressors;



SELECT DISTINCT	-- reduce cardinality

	PAT_ENC_CSN_ID

	, TAKEN_TIME

	, MEDICATION_NAME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY TAKEN_TIME) AS TIME_LINE

INTO #Pressors 

FROM #AllMeds

	INNER JOIN [EMRDB].[dbo].GROUPER_MED_RECORDS VCG ON [#AllMeds].MEDICATION_ID = [VCG].EXP_MEDS_LIST_ID

WHERE 1=1

	AND TAKEN_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

	AND [VCG].GROUPER_ID IN ('8000100'		-- HS RX EPINEPHRINE SEPSIS

							, '8000101'		-- HS RX DOPAMINE SEPSIS

							, '8000102'		-- HS RX DOBUTAMINE SEPSIS

							, '8000103'		-- HS RX MILRINONE SEPSIS

							, '8000104'		-- HS RX NOREPINEPHRINE SEPSIS

						)

;





/* ******************************** */

/* First Abx Order and Time Details */

/* ******************************** */

DROP TABLE IF EXISTS #FirstABXAdminTimeDetails;



SELECT

	A.PAT_ENC_CSN_ID

	, ORD.ORDER_MED_ID "Order ID"

	, ORD.ORDERING_DTTM "Order date and time"

	, TRACE.RXQ_INSTANT [In VERIFY Queue Time]

	, TRACE.RX_VERIFY_INSTANT [Verified in Queue Time]

	, TRACE.[Queue Verified by]

	, VERIFY.ACTION_INSTANT " Order VERIFY date and time"

	, DISPENSE.ACTION_INSTANT "Order Dispense date and time"

	, ACT.ACTION_DTTM "Rx Dispense Sent Time"



INTO #FirstABXAdminTimeDetails



FROM #BasePopABX A



	/* Order */

	INNER JOIN [EMRDB].[dbo].V_PHARMACY_ORDER ORD on ORD.ORDER_MED_ID = A.ORDER_MED_ID AND A.TIME_LINE = 1 --LOOK FOR FIRST ANTIBIOTIC ADMINISTRATION ONLY



	INNER JOIN

		(

			SELECT	ORDER_MED_ID, ACTION_INSTANT, CONTACT_DATE_REAL, ROW_NUMBER() OVER(PARTITION BY ORDER_MED_ID ORDER BY ACTION_INSTANT ASC) AS MYLINE

			FROM	[EMRDB].[dbo].ORDER_DISPENSE_INFO

			WHERE	ORD_CNTCT_TYPE_C = 4 --VERIFY

		) VERIFY ON ord.ORDER_MED_ID = VERIFY.ORDER_MED_ID AND VERIFY.MYLINE = 1



	INNER JOIN

		(

			SELECT	ORDER_MED_ID, ACTION_INSTANT, VERIFY_CONTDATREAL, CONTACT_DATE_REAL, CONTACT_DATE, ROW_NUMBER() OVER(PARTITION BY ORDER_MED_ID ORDER BY ACTION_INSTANT ASC) AS MYLINE

			FROM	[EMRDB].[dbo].ORDER_DISPENSE_INFO

			WHERE	ORD_CNTCT_TYPE_C = 95 --DISPENSE

		) DISPENSE ON ord.ORDER_MED_ID = DISPENSE.ORDER_MED_ID AND DISPENSE.MYLINE = 1

					AND VERIFY.CONTACT_DATE_REAL = DISPENSE.VERIFY_CONTDATREAL

					AND DISPENSE.ACTION_INSTANT<A.ABX_ADMIN_TIME --MAKE SURE WE ARE LOOKING AT THE RIGHT MEDICATION ADMIN TIME. A MEDICATION ORDER COULD HAVE MULTIPLE DISPENSES

	

	/* Dispense */

	LEFT OUTER JOIN [EMRDB].[dbo].V_PHARMACY_DISPENSE disp on DISPENSE.ORDER_MED_ID = disp.ORDER_MED_ID and DISPENSE.CONTACT_DATE_REAL = disp.CONTACT_DATE_REAL



	LEFT OUTER JOIN 

		(

			SELECT	ACTION_ID, ACTION_DTTM, ROW_NUMBER() OVER(PARTITION BY ACTION_ID ORDER BY ACTION_DTTM ASC) AS MYLINE 

			FROM	[EMRDB].[dbo].V_PHARMACY_DISPENSE_ACTION

			WHERE	ACTION_TYPE_C=270

		) ACT on disp.ACTION_ID = ACT.ACTION_ID AND ACT.MYLINE = 1



	LEFT OUTER JOIN 

		(

			SELECT	ORDER_MED_ID, RXQ_INSTANT, RX_VERIFY_INSTANT, RX_VER_USER_ID, EMP.[NAME] AS [Queue Verified by], ROW_NUMBER() OVER(PARTITION BY ORDER_MED_ID ORDER BY LINE DESC) AS MYLINE

			FROM	[EMRDB].[dbo].RX_VERIFY_TRACE ORT1

				LEFT OUTER JOIN [EMRDB].[dbo].EMPLOYEES EMP ON EMP.[USER_ID] = ORT1.RX_VER_USER_ID

		) TRACE ON TRACE.ORDER_MED_ID = ord.ORDER_MED_ID AND TRACE.MYLINE = 1

;







/*****************************************************************************************************************



												Flowsheets



******************************************************************************************************************/



SELECT

	[#Base_Pop].INPATIENT_DATA_ID

	, [#Base_Pop].PAT_ENC_CSN_ID

	, [#Base_Pop].ADT_ARRIVAL_TIME

	, [#Base_Pop].ED_DEPARTURE_TIME

	, [#Base_Pop].AGE_MONTHS

	, [#Base_Pop].AGE_YEARS

	, FLO_MEAS_ID

	, RECORDED_TIME

	, MEAS_VALUE

	, MEAS_COMMENT



INTO #Flowsheets

FROM #Base_Pop

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS REC ON [#Base_Pop].INPATIENT_DATA_ID = [REC].INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS FSD ON [REC].FSD_ID = [FSD].FSD_ID 

WHERE 1=1

	AND RECORDED_TIME IS NOT NULL 

	AND MEAS_VALUE IS NOT NULL 

	AND RECORDED_TIME <= ED_DEPARTURE_TIME

	AND FLO_MEAS_ID IN ('94'			-- Weight

						,'95'			-- Blood pressure

						,'9001140203'	-- R PED GIRLS SYSTOLIC BP PERCENTILE

						,'9001140205'	-- R PED BOYS SYSTOLIC BP PERCENTILE 

						,'9001125002'	-- R HS ED SEPSIS CLINICAL_ALERTS CANCELLED

						,'9000161709'	-- SEPSIS SCREENING SCORE (RETIRED)

						,'9000002613'	-- R HS IP SEPSIS SCORE 2019

						)

;





/* ******************* */

/* Encounter Weight    */

/* ******************* */

DROP TABLE IF EXISTS #EncounterWeights;



SELECT

	PAT_ENC_CSN_ID

	, CAST(ROUND(CONVERT(FLOAT, MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #EncounterWeights

FROM #Flowsheets

WHERE FLO_MEAS_ID='94'	-- Weight

;



/* ******************* */

/* Hypotension         */

/* ******************* */

DROP TABLE IF EXISTS #Hypotension;



WITH Systolic AS

(

	SELECT

		PAT_ENC_CSN_ID

		, RECORDED_TIME



		, TRY_CONVERT(INTEGER, LEFT(MEAS_VALUE, CHARINDEX('/', MEAS_VALUE)-1)) AS HYPOTENSIVE_SYSTOLIC_BP



		-- policy as of 2025-11-05 per Stakeholder A

		, CASE	WHEN AGE_MONTHS < 2 AND CONVERT(INTEGER, LEFT(MEAS_VALUE, CHARINDEX('/', MEAS_VALUE)-1)) < 56 THEN 'Y'

				WHEN AGE_MONTHS < 6 AND CONVERT(INTEGER, LEFT(MEAS_VALUE, CHARINDEX('/', MEAS_VALUE)-1)) < 65 THEN 'Y'

				WHEN AGE_MONTHS < 12 AND CONVERT(INTEGER, LEFT(MEAS_VALUE, CHARINDEX('/', MEAS_VALUE)-1)) < 70 THEN 'Y'

				WHEN AGE_YEARS <= 13 AND CONVERT(INTEGER, LEFT(MEAS_VALUE, CHARINDEX('/', MEAS_VALUE)-1)) < 70 THEN 'See BP percentile'

				WHEN AGE_YEARS > 13 AND CONVERT(INTEGER, LEFT(MEAS_VALUE, CHARINDEX('/', MEAS_VALUE)-1)) < 100 THEN 'Y'

		 END AS HYPOTENSION_Y



	FROM #Flowsheets

	WHERE 1=1

		AND FLO_MEAS_ID = '95'	-- Blood pressure

		AND RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

)



SELECT *

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #Hypotension 

FROM Systolic

WHERE HYPOTENSION_Y = 'Y'

;



/* ************** */

/* Blood Pressure */

/* ************** */

SELECT 

	PAT_ENC_CSN_ID

	, FLO_MEAS_ID

	, RECORDED_TIME

	, MEAS_VALUE



INTO #BloodPressure

FROM #Flowsheets

WHERE 1=1

	AND RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

	AND FLO_MEAS_ID IN (

		'95'				-- Blood Pressure

		,'9001140203'	-- R PED GIRLS SYSTOLIC BP PERCENTILE

		,'9001140205'	-- R PED BOYS SYSTOLIC BP PERCENTILE 

	)

;	



CREATE NONCLUSTERED INDEX INX_BLD_MMHG_CSN ON #Base_Pop ([PAT_ENC_CSN_ID]);





/* ********************** */

/* Sepsis CLINICAL_ALERTS Cancelled */

/* ********************** */

DROP TABLE IF EXISTS #SepsisAlertCancelled;



SELECT 

	PAT_ENC_CSN_ID

	, RECORDED_TIME	AS SEPSIS_ALERT_CANC_TIME

	, 'Y'			AS SEPSIS_ALERT_CANC_YN

	, MEAS_COMMENT	AS SEPSIS_ALERT_CANC_BY		-- Free text

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #SepsisAlertCancelled 

FROM #Flowsheets

WHERE 1=1

	AND FLO_MEAS_ID = '9001125002'	-- R HS ED SEPSIS CLINICAL_ALERTS CANCELLED

	AND RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

;



/* ******************* */

/* Severe Sepsis       */

/* ******************* */

DROP TABLE IF EXISTS #Base_Pop_Severe_ED_Scores;



SELECT

	PAT_ENC_CSN_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #Base_Pop_Severe_ED_Scores 

FROM #Flowsheets

WHERE 1=1

	AND RECORDED_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

	AND FLO_MEAS_ID IN (

				'9000161709'	-- SEPSIS SCREENING SCORE (RETIRED)

				,'9000002613'	-- R HS IP SEPSIS SCORE 2019

		)

;



/* ******************* */

/* Positive Sepsis     */

/* ******************* */

DROP TABLE IF EXISTS #ED_PositiveScores;



SELECT

	PAT_ENC_CSN_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO #ED_PositiveScores

FROM #Base_Pop_Severe_ED_Scores

WHERE MEAS_VALUE > 4

;



/* ******************* */

/* Negative Sepsis     */

/* ******************* */

DROP TABLE IF EXISTS #ED_NegativeScores;



SELECT

	PAT_ENC_CSN_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO #ED_NegativeScores

FROM #Base_Pop_Severe_ED_Scores

WHERE 1=1

	AND MEAS_VALUE <= 4

	AND NOT EXISTS (SELECT 1 FROM #ED_PositiveScores WHERE #ED_PositiveScores.PAT_ENC_CSN_ID = #Base_Pop_Severe_ED_Scores.PAT_ENC_CSN_ID)

;



/* ************************ */

/* Severe + Positive Sepsis */

/* ************************ */

DROP TABLE IF EXISTS #Base_Pop_SepsisScores_ConCat;



SELECT DISTINCT 

	[CAT].PAT_ENC_CSN_ID

    , STUFF((

				SELECT ',' + CONVERT(VARCHAR,SUB.MEAS_VALUE)

				FROM #Base_Pop_Severe_ED_Scores SUB

				WHERE SUB.PAT_ENC_CSN_ID = [CAT].PAT_ENC_CSN_ID

				ORDER BY RECORDED_TIME

				FOR XML PATH('')

				), 1, 1, '' 

			)

    AS [AllSepsis_Scores]

INTO #Base_Pop_SepsisScores_ConCat

FROM  #Base_Pop_Severe_ED_Scores CAT

;







/*****************************************************************************************************************



													LDAs



******************************************************************************************************************/

WITH All_LDAs AS

(

	SELECT

		[#Base_Pop].PAT_ENC_CSN_ID

		, IP_LDA_ID

		, FLO_MEAS_ID

		, PLACEMENT_INSTANT

		, [CVS].VALUE_SET_ID



		, CASE

			WHEN FLO_MEAS_ID IN ('900112') THEN 'ETT'

			WHEN FLO_MEAS_ID IN ('900111') THEN 'IV'

			WHEN [CVS].VALUE_SET_ID IN (3022) THEN 'CVL'

		  END AS LDA_PLACEMENT_TYPE



	FROM #Base_Pop

		INNER JOIN [EMRDB].[dbo].LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = [#Base_Pop].PAT_ENC_CSN_ID

		LEFT JOIN (

			SELECT DISTINCT VALUE_SET_ID, CODE

			FROM [reportingDB].[reports].CONFIG_VALUE_SET

			WHERE VALUE_SET_ID = 3022	-- SEPSIS_CVL_PLACEMENT [3022]

		) CVS ON ILN.FLO_MEAS_ID = [CVS].CODE



	WHERE 1=1

		AND PLACEMENT_INSTANT IS NOT NULL

		AND PLACEMENT_INSTANT BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

		AND (

				FLO_MEAS_ID IN ('900112'	-- LDA HS IP ETT

								,'900111'	-- LDA HS IP PERIPHERAL IV

								)

				OR [CVS].VALUE_SET_ID = 3022	-- SEPSIS_CVL_PLACEMENT



			)

)



, TimeOrdered_LDAs AS

(



SELECT *

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID, LDA_PLACEMENT_TYPE ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

FROM All_LDAs

)



SELECT *

INTO #LDA

FROM TimeOrdered_LDAs

WHERE TIME_LINE = 1

;





--/* ******************* */

--/* ETT                 */

--/* ******************* */

--DROP TABLE IF EXISTS #ETT;



--SELECT

--	PAT_ENC_CSN_ID,

--	IP_LDA_ID,

--	PLACEMENT_INSTANT,

--	ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

--INTO #ETT

--FROM #LDAs

--WHERE FLO_MEAS_ID = '900112' -- LDA HS IP ETT

--;





--/* ******************* */

--/* IV Placement        */

--/* ******************* */

--DROP TABLE IF EXISTS #IV;



--SELECT

--	PAT_ENC_CSN_ID,

--	IP_LDA_ID,

--	PLACEMENT_INSTANT,

--	ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

--INTO #IV

--FROM #LDAs

--WHERE FLO_MEAS_ID = '900111' --LDA HS IP PERIPHERAL IV

--;





--/* ******************* */

--/* CVL Time            */

--/* ******************* */

--DROP TABLE IF EXISTS #ALLCVLTime;



--SELECT DISTINCT

--	PAT_ENC_CSN_ID

--	, PLACEMENT_INSTANT

--	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

--INTO #ALLCVLTime

--FROM #LDAs

--WHERE VALUE_SET_ID = 3022	-- SEPSIS_CVL_PLACEMENT

--;







/* ****************************************************************************************************************



													Labs



******************************************************************************************************************/



SELECT

	[#Base_Pop].PAT_ENC_CSN_ID

	, OP.PROC_ID

	, OP.ORDER_TIME AS MBOrderTime

	, OP.SPECIMEN_SOURCE_C

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	--, ROW_NUMBER() OVER(PARTITION BY [#Base_Pop].PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID

	, LAB_ORDER_RESULTS.COMPONENT_ID

	, LAB_ORDER_RESULTS.RESULT_FLAG_C

	, CASE WHEN LAB_ORDER_RESULTS.RESULT_FLAG_C IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01 -- Abnormal or Critical

	, LAB_ORDER_RESULTS.LRR_BASED_ORGAN_ID



	, CASE

		WHEN PROC_ID IN (600003, 600004, 600011, 600012) THEN 'Blood'

		WHEN PROC_ID IN (600001, 600007, 600008, 600009, 600010) THEN 'Urine'

		WHEN PROC_ID IN (600005, 600006, 600002) THEN 'CSF'

		END AS CULTURE_TYPE



	, CASE

		WHEN COMPONENT_ID IN (5000001861, 5000000478) THEN 'O2 Saturation'

		WHEN COMPONENT_ID IN (5000000446, 5000000447, 5000000449) THEN 'Lactic Acid'

		WHEN COMPONENT_ID IN (500001) THEN 'Procalcitonin'

		END AS LAB_TEST_TYPE



INTO #Labs_and_Cultures

FROM #Base_Pop

	INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS ON [#Base_Pop].PAT_ENC_CSN_ID = LAB_ORDER_RESULTS.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE 1=1

	AND (OP.ORDER_TIME BETWEEN [#Base_Pop].ADT_ARRIVAL_TIME AND [#Base_Pop].ED_DEPARTURE_TIME)

	AND (

			LAB_ORDER_RESULTS.COMPONENT_ID IN (

				5000001861		-- O2 SATURATION VENOUS, GEM CALC

				, 5000000478	-- O2 SATURATION VENOUS

				, 5000000446	-- LACTIC ACID ISTAT

				, 5000000447	-- LACTIC ACID, GEM RESPIRATORY

				, 5000000449	-- LACTIC ACID LEVEL

				, 500001			-- PROCALCITONIN

				)

			OR

			OP.PROC_ID IN (

				600003		-- BLOOD CULTURE

				, 600004	-- SEND BLOOD CULTURE IF TEMP

				, 600011	-- BLOOD CULTURE, QUEST

				, 600012	-- BLOOD CULTURE, LABCORP



				, 600001		-- URINE CULTURE

				, 600007	-- REFLEXIVE URINE CULTURE, QUEST

				, 600008	-- REFLEXIVE URINE CULTURE, QUEST

				, 600009	-- URINE CULTURE COMPREHENSIVE, LABCORP

				, 600010	-- HS POCT URINE CULTURE

				)

			OR (

				OP.SPECIMEN_SOURCE_C = 304	-- Lumber puncture

				AND

				OP.PROC_ID IN (

					600005		-- BODY FLUID CULTURE, AEROBE AND GRAM STAIN

					, 600006	-- BODY FLUID CULTURE, AEROBE, ANAEROBE, AND GRAM STAIN

					, 600002		-- CSF CULTURE AND GRAM STAIN

					)

				)

		)

;





/* ********** */

/* Labs       */

/* ********** */

WITH TimeOrdered_Labs AS

(

	SELECT *

		, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID, LAB_TEST_TYPE ORDER BY MBOrderTime ASC) AS TIME_LINE

	FROM #Labs_and_Cultures

	WHERE LAB_TEST_TYPE IS NOT NULL

)



SELECT *

INTO #Labs

FROM TimeOrdered_Labs

WHERE TIME_LINE = 1

;







/* ************** */

/* Cultures       */

/* ************** */

DROP TABLE IF EXISTS #Cultures;



WITH AllCultures AS

(

	SELECT

		PAT_ENC_CSN_ID

		, ORDER_PROC_ID

		, MBOrderTime

		, RESULT_TIME

		, CollectionTime

		, ORD_VALUE

		, CRITICAL_VALUE_01

		, CULTURE_TYPE

		, LRR_BASED_ORGAN_ID

		, [ORGANISMS].EXTERNAL_NAME AS [OrganismName]

		

	FROM #Labs_and_Cultures

		LEFT JOIN [EMRDB].[dbo].ORGANISMS ON [#Labs_and_Cultures].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE CULTURE_TYPE IS NOT NULL

)



, PositiveCultures AS

(

	SELECT

		PAT_ENC_CSN_ID

		, CULTURE_TYPE



		, MIN(MBOrderTime)		AS [MBOrderTime]

		, MIN(CollectionTime)	AS [CollectionTime]



		, COALESCE(STRING_AGG(OrganismName, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM AllCultures

	GROUP BY PAT_ENC_CSN_ID, CULTURE_TYPE

	HAVING MAX(CRITICAL_VALUE_01) = 1	-- any positives

)



, NegativeCultures AS

(

	SELECT

		PAT_ENC_CSN_ID

		, CULTURE_TYPE



		, MIN(MBOrderTime)		AS [MBOrderTime]

		, MIN(CollectionTime)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]



	FROM AllCultures

	GROUP BY PAT_ENC_CSN_ID, CULTURE_TYPE

	HAVING MAX(CRITICAL_VALUE_01) = 0	-- only where no positives

)





SELECT * 

INTO #Cultures

FROM PositiveCultures

UNION

SELECT * FROM NegativeCultures

;







/* ****************************************************************************************************************



											DEPARTMENT TRANSFERS



******************************************************************************************************************/



SELECT

	[#Base_Pop].PAT_ENC_CSN_ID

	, [ADT01].EFFECTIVE_TIME

	, [ADT02].DEPARTMENT_ID

	, [DEP].DEPARTMENT_NAME	-- transferred to



	, CASE

		WHEN [ADT02].DEPARTMENT_ID IN (200108015, 200108016, 200108019)				THEN 'HemOnc'

		WHEN [ADT02].DEPARTMENT_ID IN (200108001, 200108070, 200108115, 200108183)	THEN 'ICU'

		WHEN [ADT02].DEPARTMENT_ID IN ( 200108008, 200108009, 200108010, 200108011, 200108012

									  , 200108017, 200108018, 200108020, 200108021, 200108110)	THEN 'GenCare'

	  END AS DEPT_GROUP

INTO #ADT

FROM #Base_Pop

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS ADT01 ON [ADT01].PAT_ENC_CSN_ID =  [#Base_Pop].PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS ADT02 ON [ADT01].XFER_IN_EVENT_ID = [ADT02].EVENT_ID

	INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON [DEP].DEPARTMENT_ID = [ADT02].DEPARTMENT_ID



WHERE 1=1

	-- Transferred out of Emergency

	AND [ADT01].EVENT_TYPE_C = 4		--TRANSFER OUT

	AND [ADT01].EVENT_SUBTYPE_C <> 2	--CANCELED

	AND [ADT01].DEPARTMENT_ID IN (200108022) -- Emergency 



	-- Transferred into XXX

	AND [ADT02].EVENT_TYPE_C = 3		--TRANSFER IN

	AND [ADT02].EVENT_SUBTYPE_C <> 2	--CANCELED

	AND [ADT02].DEPARTMENT_ID IN (

			-- Hem/Oncology

			200108015	--MAIN 95 TOWER EAST

			,200108016	--MAIN 95 TOWER WEST

			,200108019	--MAIN 95 PAVILION



			-- ICU

			--, 20101116		--EAST ICU

			--, 20101124		--EAST CARDIAC ICU

			--, 20101126		--EAST NEURO ICU

			--, 20101127		--EAST PEDIATRIC ICU

			--, 20101128		--EAST SURGICAL ICU

			--, 20101165		--EAST REMOTE ICU

			--, 20120106		--WEST CARDIAC ICU

			--, 20120121		--WEST ICU							

			, 200108001			--MAIN 2 PAVILION PICU

			, 200108070			--MAIN 3 CICU

			, 200108115			--MAIN 2 PICU NEURO

			, 200108183			--MAIN 2 TOWER PICU



			-- Gen Care

			, 200108008		--MAIN 3 NORTH

			, 200108009		--MAIN 3 PAVILION

			, 200108010		--MAIN 4 NORTH

			, 200108011		--MAIN 4 SOUTH

			, 200108012		--MAIN 4 PAVILION

			, 200108017		--MAIN 95 NORTH

			, 200108018		--MAIN 95 SOUTH

			, 200108020		--MAIN 6 NORTH

			, 200108021		--MAIN 6 SOUTH

			, 200108110		--MAIN 4 PAVILION EMU

		) 

;







/* ******************* */

/* Hem/Oncology        */

/* ******************* */

DROP TABLE IF EXISTS #ED2HEMONC;



SELECT

	PAT_ENC_CSN_ID

	, DEPARTMENT_NAME

	, EFFECTIVE_TIME AS ED2HemoncTime

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY EFFECTIVE_TIME ASC) AS TIME_LINE

INTO #ED2HEMONC

FROM #ADT

WHERE DEPT_GROUP = 'HemOnc'

;



/* ******************* */

/* ICU                 */

/* ******************* */

DROP TABLE IF EXISTS #ED2ICU;



SELECT

	PAT_ENC_CSN_ID

	, DEPARTMENT_NAME

	, EFFECTIVE_TIME AS ED2ICUTime

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY EFFECTIVE_TIME ASC) AS TIME_LINE

INTO #ED2ICU

FROM #ADT

WHERE DEPT_GROUP = 'ICU'

;





/* ******************* */

/* Gen Care            */

/* ******************* */

DROP TABLE IF EXISTS #ED2GEN;



SELECT

	PAT_ENC_CSN_ID

	, [#ADT].DEPARTMENT_NAME

	, [#ADT].EFFECTIVE_TIME AS ED2GENTime

	, [GEN2ICU].EFFECTIVE_TIME AS [Gen Back To ICU Time]

	, [GEN2ICU].DEPARTMENT_NAME AS [Gen Back To ICU Department]



	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY [#ADT].EFFECTIVE_TIME ASC) AS TIME_LINE



INTO #ED2GEN

FROM #ADT



	OUTER APPLY	--09.09.2020 V_DEV001 added this to check for PATIENTS who went from ED --> Gen Care and then back to ICU within 24 hours

	(

		SELECT TOP 1 ICU.EFFECTIVE_TIME, DEP.DEPARTMENT_NAME

		FROM #ADT ICU

			INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = ICU.DEPARTMENT_ID

		WHERE 1=1

			AND [#ADT].PAT_ENC_CSN_ID = [ICU].PAT_ENC_CSN_ID

			AND [ICU].EFFECTIVE_TIME BETWEEN [#ADT].EFFECTIVE_TIME AND DATEADD(HH, 24, [#ADT].EFFECTIVE_TIME)

			AND [ICU].DEPT_GROUP = 'ICU'

		ORDER BY [ICU].EFFECTIVE_TIME ASC

	) GEN2ICU



WHERE DEPT_GROUP = 'GenCare'

;







/* ****************************************************************************************************************



												MISCELLANEOUS



******************************************************************************************************************/



/* ******************* */

/* BPA                 */

/* ******************* */

DROP TABLE IF EXISTS #BPA;



SELECT

	B.PAT_ENC_CSN_ID,

	ALT.ALT_ID,

	AH.ALT_ACTION_INST,

	ZAS.[NAME] AS ALERT_STATUS,

	ZSP.[NAME] AS ALERT_SHOWN_PLACE,

	ZAAT.[NAME] AS ACTION_TAKE,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY AH.ALT_ACTION_INST) AS TIME_LINE,

	ZASOR.[NAME] AS OVERRIDDEN,

	ah.SPEC_OVR_CMNT,

	EMP.[NAME]

INTO #BPA

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].CLINICAL_ALERTS ALT ON ALT.PAT_CSN = B.PAT_ENC_CSN_ID AND ALT.BPA_LOCATOR_ID = '900130001'

	INNER JOIN [EMRDB].[dbo].ALERT_HISTORY AH ON AH.ALT_ID = ALT.ALT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].ALERT_ACTIONS ACA ON ACA.ALT_CSN_ID = AH.ALT_CSN_ID AND ACA.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_ACTIONS ZAAT ON ZAAT.ALT_ACTION_TAKEN_C = ACA.ACTION_TAKEN_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_OVERRIDE_REASONS ZASOR ON ZASOR.ALRT_SP_OVR_RSN_C = AH.SPEC_OVR_RSN_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_STATUS ZAS ON ZAS.ALT_STATUS_C = AH.ALT_STATUS_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_SHOWN_PLACE ZSP ON ZSP.SHOWN_PLACE_C = AH.SHOWN_PLACE_C

	LEFT OUTER JOIN [EMRDB].[dbo].EMPLOYEES EMP ON EMP.[USER_ID] = AH.[USER_ID]

WHERE AH.ALT_ACTION_INST BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME

;



/* ********** */

/* Bed Events */

/* ********** */

DROP TABLE IF EXISTS #BedEvents;



SELECT

	B.PAT_ENC_CSN_ID, C.RECORD_NAME AS [EVENT], EIEI.EVENT_TYPE AS [EVENT ID],EIEI.EVENT_TIME,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY EIEI.EVENT_TIME ) AS TIME_LINE,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID, EIEI.EVENT_TYPe ORDER BY EIEI.EVENT_TIME ) AS REQ_LINE --JUST IN CASE IF THERE IS MORE THAN ONE EVENT OF THE SAME EVENT_TYPE.

INTO #BedEvents

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].ED_PATIENT_INFO EIPI ON EIPI.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].ED_EVENT_INFO EIEI ON EIEI.EVENT_ID = EIPI.EVENT_ID AND EIEI.EVENT_TYPE IN ('2600000347','2600000346')

	INNER JOIN [EMRDB].[dbo].ED_EVENT_TEMPLATES C ON EIEI.EVENT_TYPE = C.RECORD_ID

;



/* ************ */

/* Readmissions */

/* ************ */

DROP TABLE IF EXISTS #Base_Pop_ED_Readmit_All;



SELECT DISTINCT [#Base_Pop].PAT_ENC_CSN_ID

INTO #Base_Pop_ED_Readmit_All

FROM #Base_Pop

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PAT_ID = [#Base_Pop].PAT_ID 

											AND DEE.ARRIVAL_DTTM BETWEEN ED_DEPARTURE_TIME AND DATEADD(HH, 24, ED_DEPARTURE_TIME)

;



/* *********************************** */

/* Readmissions (positive sepsis only) */

/* *********************************** */

DROP TABLE IF EXISTS #Base_Pop_ED_Readmit;



SELECT DISTINCT [#Base_Pop].PAT_ENC_CSN_ID

INTO #Base_Pop_ED_Readmit

FROM #ED_PositiveScores

	INNER JOIN #Base_Pop ON [#ED_PositiveScores].PAT_ENC_CSN_ID = [#Base_Pop].PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PAT_ID = [#Base_Pop].PAT_ID 

											AND DEE.ARRIVAL_DTTM BETWEEN [#Base_Pop].ED_DEPARTURE_TIME AND DATEADD(HH, 24, [#Base_Pop].ED_DEPARTURE_TIME)

WHERE [#ED_PositiveScores].FIRST_TIME_LINE= 1 

;



/* **************** */

/* PATIENTS Location */

/* **************** */

SELECT 

	PAT_ENC_CSN

	, IN_DTTM

	, ADT_DEPARTMENT_NAME

INTO #PatientLocation

FROM [EMRDB].[dbo].V_PATIENT_LOCATION_HISTORY

WHERE 1=1

	AND [V_PATIENT_LOCATION_HISTORY].ADT_DEPARTMENT_ID IS NOT NULL

	AND EXISTS (SELECT 1 FROM #Base_Pop WHERE [#Base_Pop].PAT_ENC_CSN_ID = [V_PATIENT_LOCATION_HISTORY].PAT_ENC_CSN)

;



CREATE NONCLUSTERED INDEX INX_ADT_LOC ON #PatientLocation (PAT_ENC_CSN);



/* ******************************************* */

/* Time from First Positive Score -> First Abx */

/* ******************************************* */

DROP TABLE IF EXISTS #FirstPositiveOD_To_ABXAdminTime;



SELECT

	[subQ].PAT_ENC_CSN_ID

	,[subQ].MEDICATION

	,[subQ].ABX_ADMIN_TIME

	,[subQ].RECORDED_TIME,

	DATEDIFF(MI, [subQ].RECORDED_TIME, [subQ].ABX_ADMIN_TIME) AS POSOD2ABX



INTO #FirstPositiveOD_To_ABXAdminTime



FROM 

	(

		SELECT 

			[#BasePopABX].PAT_ENC_CSN_ID

			, [#BasePopABX].MEDICATION_NAME AS MEDICATION

			, [#BasePopABX].ABX_ADMIN_TIME

			, [#ED_PositiveScores].MEAS_VALUE

			, [#ED_PositiveScores].RECORDED_TIME

			, ROW_NUMBER() OVER(PARTITION BY [#BasePopABX].PAT_ENC_CSN_ID ORDER BY [#BasePopABX].ABX_ADMIN_TIME ASC) AS MYLINE

		FROM #BasePopABX

			INNER JOIN #ED_PositiveScores ON [#BasePopABX].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

										AND [#ED_PositiveScores].RECORDED_TIME < [#BasePopABX].ABX_ADMIN_TIME

										AND [#ED_PositiveScores].FIRST_TIME_LINE=1

	) subQ

WHERE [subQ].MYLINE=1

;



/* ********************** */

/* Chief Complaints (all) */

/* ********************** */

DROP TABLE IF EXISTS #Base_Pop_ENC_Reason;



SELECT DISTINCT   CAT.PAT_ENC_CSN_ID,

        STUFF((	SELECT ';' + CONVERT(VARCHAR,CRFV.REASON_VISIT_NAME)-- AS [text()]

                FROM #Base_Pop SUB

					INNER JOIN [EMRDB].[dbo].ENCOUNTER_VISIT_REASONS RSN ON RSN.PAT_ENC_CSN_ID = SUB.PAT_ENC_CSN_ID AND RSN.LINE>1

					INNER JOIN [EMRDB].[dbo].VISIT_REASONS CRFV ON CRFV.REASON_VISIT_ID = RSN.ENC_REASON_ID

				WHERE

                    SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

				ORDER BY LINE

                    FOR XML PATH('')

               ), 1, 1, '' )

            AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM  #Base_Pop CAT

;



/* ********************** */

/* ED boarder PATIENTS     */

/* ********************** */

DROP TABLE IF EXISTS #ED_BORDER;



SELECT DISTINCT PAT_ENC_CSN_ID

INTO #ED_BORDER

FROM [EMRDB].[dbo].ED_PATIENT_INFO

	INNER JOIN [EMRDB].[dbo].ED_EVENT_INFO	 ON [ED_EVENT_INFO].EVENT_ID = [ED_PATIENT_INFO].EVENT_ID

WHERE 1=1

	AND EXISTS (SELECT 1 FROM #Base_Pop WHERE [#Base_Pop].PAT_ENC_CSN_ID = [ED_PATIENT_INFO].PAT_ENC_CSN_ID)

	AND [ED_EVENT_INFO].EVENT_TYPE IN ('2600000007')--ED BOARDER PATIENTS

;



/* ******************* */

/* Order Set           */

/* ******************* */

DROP TABLE IF EXISTS #SSOrderSet;



WITH OrderMetricIDs AS

(

	SELECT

		[#Base_Pop].PAT_ENC_CSN_ID

		, ORDER_ID

		, ORDER_DTTM

		, PRL_ORDERSET_ID

	FROM #Base_Pop

		INNER JOIN [EMRDB].[dbo].ORDER_TRACKING_METRICS ON [ORDER_TRACKING_METRICS].PAT_ENC_CSN_ID = [#Base_Pop].PAT_ENC_CSN_ID

	WHERE [ORDER_TRACKING_METRICS].ORDER_DTTM BETWEEN [#Base_Pop].ADT_ARRIVAL_TIME AND [#Base_Pop].ED_DEPARTURE_TIME

)



, SSOrderSetOSQ_PRL AS

(

	-- OSQ

	SELECT

		[OrderMetricIDs].PAT_ENC_CSN_ID

		, [OrderMetricIDs].ORDER_DTTM

		, [MEDICATION_ORDERS_EXT].ORD_OSQ_ID AS PRL_ORDERSET_ID

	FROM OrderMetricIDs

		INNER JOIN [EMRDB].[dbo].MEDICATION_ORDERS_EXT ON [OrderMetricIDs].ORDER_ID = [MEDICATION_ORDERS_EXT].ORDER_ID AND [MEDICATION_ORDERS_EXT].ORD_OSQ_ID IN (400002,400007,400003,400004,400006,400005,4001326025)



	UNION



		SELECT

			[OrderMetricIDs].PAT_ENC_CSN_ID

			, [OrderMetricIDs].ORDER_DTTM

			, [PROCEDURE_ORDERS_EXT].ORD_OSQ_ID AS PRL_ORDERSET_ID

		FROM OrderMetricIDs

			INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS_EXT ON [OrderMetricIDs].ORDER_ID =  [PROCEDURE_ORDERS_EXT].ORDER_ID AND [PROCEDURE_ORDERS_EXT].ORD_OSQ_ID IN (400002,400007,400003,400004,400006,400005,4001326025)



	UNION



		SELECT

			[OrderMetricIDs].PAT_ENC_CSN_ID

			, [OrderMetricIDs].ORDER_DTTM

			, [OrderMetricIDs].PRL_ORDERSET_ID

		FROM OrderMetricIDs

		-- see VCG 800018 -- HS BI SEPSIS PRL ORDERSETS (the entire Grouper is used by IPSO Severe Sepsis; ED Sepsis only uses ED-specific PRLs)

		WHERE [OrderMetricIDs].PRL_ORDERSET_ID IN (400001, 4001326023) -- Sepsis Pathway [400001]; HS ED ONCOLOGY SEPSIS RN PROTOCOL OPA [4001326023]

)



SELECT

	PAT_ENC_CSN_ID

	, ORDER_DTTM

	, PRL_ORDERSET_ID

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY ORDER_DTTM ASC) AS TIME_LINE

INTO #SSOrderSet 

FROM SSOrderSetOSQ_PRL

;



-- @99:48 mins





/* ****************************************************************************************************************



												FINAL QUERY



******************************************************************************************************************/

SELECT

	[BasePop].PAT_MRN_ID		AS MRN

	,[BasePop].PAT_NAME			AS PATIENTS

	,[BasePop].[Ethnic Group]

	,[BasePop].[Race]

	,[BasePop].PAT_ENC_CSN_ID	AS CSN

	,[BasePop].AGE_MONTHS		AS [Age at ED Arrival (Months)]

	,[BasePop].AGE_YEARS		AS [Age at ED Arrival (Years)]

	,[BasePop].AGE_IN_DAYS		AS [Age In Days]



	,CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN 1 ELSE 0 END						AS [Age in Days Count]

	,CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN '<= 21 Days' ELSE '> 21 Days' END	AS [Age in Days Indicator]



	,[BasePop].[Location]

	,[BasePop].DATE_STAMP

	,[BasePop].ADT_ARRIVAL_TIME		AS [ED Arrival Time]

	,[BasePop].TRIAGE_START_DTTM	AS [Traige Start Time]

	,[BasePop].TRIAGE_END_DTTM		AS [Traige Stop Time]



	,CONVERT(DATE, [BasePop].ADT_ARRIVAL_TIME)		AS [ED Arrival Date]	-- for PBI DateTable



	,CRFV.REASON_VISIT_NAME			AS [Chief Complaint]

	,RSN.AllEncReasons				AS [Other Visit Reasons]

	,[BasePop].ED_DEPARTURE_TIME	AS [ED Departure Time]

	,[BasePop].HOSP_ADMSN_TIME		AS [HOSP Admit Time]

	,[BasePop].HOSP_DISCH_TIME		AS [HOSP Discharge Time]

	,[BasePop].Disposition			AS [ED Disposition]



	--,CASE WHEN SepsisScreened.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END AS [Sepsis Screened 01]	-- Why is this needed?

	,CASE	WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL THEN 1

			WHEN [#ED_NegativeScores].MEAS_VALUE IS NOT NULL THEN 0

	 END AS [Screened Positive 01]



	,CASE	WHEN [#ED_PositiveScores].RECORDED_TIME IS NOT NULL

			THEN CASE	WHEN DATEPART(HOUR,[#ED_PositiveScores].RECORDED_TIME) >= 7 and DATEPART(HOUR,[#ED_PositiveScores].RECORDED_TIME) < 19 

						THEN 'AM (Day Shift)'

						ELSE 'PM (Night Shift)'

			END

	  END AS [First Positive Score AM/PM]



	,[#ED_PositiveScores].RECORDED_TIME		AS [First Positive Score Time]

	,[#ED_PositiveScores].MEAS_VALUE		AS [First Positive Score]

	,[#ED_NegativeScores].RECORDED_TIME		AS [First Negative Score Time]	-- only if never positive

	,[#ED_NegativeScores].MEAS_VALUE		AS [First Negative Score]

	,ALLSCORES.AllSepsis_Scores				AS [All Sepsis Scores]



	,ABXTimes.[Order date and time]

	,ABXTimes.[In VERIFY Queue Time]

	,ABXTimes.[Verified in Queue Time]

	,ABXTimes.[Queue Verified by]

	,ABXTimes.[Order Dispense date and time]

	,ABXTimes.[Rx Dispense Sent Time]



	/* Antibiotic (1st) */

	, ABX1.ABX_ADMIN_TIME	AS [First ABX Admin Time]

	, ABX1.MEDICATION_NAME	AS [First ABX Name]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, ABX1.ABX_ADMIN_TIME)				AS [Arrival To First ABX Admin Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, ABX1.ABX_ADMIN_TIME)				AS [Triage To First ABX Admin Time]

	, DATEDIFF(MI, [#ED_PositiveScores]. RECORDED_TIME,ABX1.ABX_ADMIN_TIME)		AS [First Positive Screen To First ABX Time]



	/* Antibiotic (2nd) */

	, ABX2.ABX_ADMIN_TIME	AS [Second ABX Admin Time]

	, ABX2.MEDICATION_NAME	AS [Second ABX Name]



	, DATEDIFF(MI, ABX1.ABX_ADMIN_TIME, ABX2.ABX_ADMIN_TIME)					AS [First ABX To Second ABX Admin Time]

	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, ABX2.ABX_ADMIN_TIME)		AS [First Positive Screen To Second ABX Time]

	

	/* OrderSet */

	, [#SSOrderSet].ORDER_DTTM AS [Order Set Time]

	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#SSOrderSet].ORDER_DTTM)	AS [Arrival To Order Set Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#SSOrderSet].ORDER_DTTM)	AS [Triage To Order Set Time]



	/* Bolus (1st) */

	, BPB1.BOLUS_ADMIN_TIME AS [Bolus 1 Admin Time]

	, BPB1.BOLUS_VOLUME		AS [Bolus 1 Volume]

	, CASE	WHEN BPB1.Medication = 'ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION' THEN 'Albumin 95%' ELSE BPB1.Medication END	AS [Bolus 1 Administered]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, BPB1.BOLUS_ADMIN_TIME) AS [Arrival To First Bolus Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, BPB1.BOLUS_ADMIN_TIME) AS [Triage To First Bolus Time]

	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, BPB1.BOLUS_ADMIN_TIME) AS [First Positive Screen To First Bolus Time]

	

	/* Bolus (2nd) */

	, BPB2.BOLUS_ADMIN_TIME AS [Bolus 2 Admin Time]

	, BPB2.BOLUS_VOLUME		AS [Bolus 2 Volume]

	, CASE	WHEN BPB2.Medication = 'ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION' THEN 'Albumin 95%' ELSE BPB2.Medication	END AS [Bolus 2 Administered]



	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, BPB2.BOLUS_ADMIN_TIME)	AS [First Positive Screen To Second Bolus Time]

	, DATEDIFF(MI, BPB1.BOLUS_ADMIN_TIME, BPB2.BOLUS_ADMIN_TIME)				AS [First Bolus To Second Bolus Time]

	

	/* Bolus (3rd) */

	, BPB3.BOLUS_ADMIN_TIME AS [Bolus 3 Admin Time]

	, BPB3.BOLUS_VOLUME		AS [Bolus 3 Volume]

	, CASE	WHEN BPB3.Medication = 'ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION' THEN 'Albumin 95%' ELSE BPB3.Medication	END AS [Bolus 3 Administered]



	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, BPB3.BOLUS_ADMIN_TIME)	AS [First Positive Screen To Third Bolus Time]

	, DATEDIFF(MI, BPB2.BOLUS_ADMIN_TIME, BPB3.BOLUS_ADMIN_TIME)				AS [Second Bolus To Third Bolus Time]



	, EW.EncWeight AS [PATIENTS Weight]



	/* Hypotension */

	, [#Hypotension].RECORDED_TIME				AS [First Hypotension Recorded Time]

	, [#Hypotension].HYPOTENSIVE_SYSTOLIC_BP	AS [First Hypotension Value]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#Hypotension].RECORDED_TIME)	AS [Arrival To First Hypotension Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#Hypotension].RECORDED_TIME)	AS [Triage To First Hypotension Time]



	/* CVL Placement */

	, CVL.PLACEMENT_INSTANT AS [CVL Placement Time]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, CVL.PLACEMENT_INSTANT)	AS [Arrival To CLV Placement Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, CVL.PLACEMENT_INSTANT)	AS [Triage To CLV Placement Time]



	/* Presssors */

	, [#Pressors].TAKEN_TIME		AS [Vasopressor Admin Time]

	, [#Pressors].MEDICATION_NAME	AS [Vasopressor Administered]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#Pressors].TAKEN_TIME)			AS [Arrival To Vasopressor Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#Pressors].TAKEN_TIME)			AS [Triage To Vasopressor Time]

	, DATEDIFF(MI,[#ED_PositiveScores].RECORDED_TIME, [#Pressors].TAKEN_TIME)	AS [First Positive Screen To Vasopressor Time]



	/* SVO2 */

	, [SPO2].MBOrderTime		AS [SVO2 Order Time]

	, [SPO2].CollectionTime		AS [SVO2 Order Collection Time]

	, [SPO2].ORD_VALUE			AS [SVO2 Lab Result]

	

	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [SPO2].MBOrderTime)		AS [Arrival To SVO2 Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [SPO2].MBOrderTime)		AS [Triage To SVO2 Order Time]



	/* Lactic Acid */

	, [LAC].MBOrderTime		AS [Lactic Acid Order Time]

	, [LAC].CollectionTime	AS [Lactic Acid Order Collection Time]

	, [LAC].ORD_VALUE		AS [Lactic Acid Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [LAC].MBOrderTime)		AS [Arrival To Lactic Acid Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [LAC].MBOrderTime)		AS [Triage To Lactic Acid Order Time]



	/* Procalcitonin */

	, [PCT].MBOrderTime		AS [Procalcitonin Order Time]

	, [PCT].CollectionTime	AS [Procalcitonin Order Collection Time]

	, [PCT].ORD_VALUE		AS [Procalcitonin Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [PCT].MBOrderTime)	AS [Arrival To PRO Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [PCT].MBOrderTime)	AS [Triage To PRO Order Time]



	/* Blood Culture */

	, [BLD].MBOrderTime		AS [Blood Culture Order Time]

	, [BLD].CollectionTime	AS [Blood Culture Order Collection Time]

	, [BLD].OrganismList		AS [Blood Culture Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [BLD].MBOrderTime)	AS [Arrival To Blood Culture Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [BLD].MBOrderTime)	AS [Triage To Blood Culture Order Time]



	/* Urine Culture */

	, [URN].MBOrderTime		AS [Urine Culture Order Time]

	, [URN].CollectionTime	AS [Urine Culture Order Collection Time]

	, [URN].OrganismList		AS [Urine Culture Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [URN].MBOrderTime)	AS [Arrival To Urine Culture Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [URN].MBOrderTime)	AS [Triage To Urine Culture Order Time]



	/* CSF Culture */

	, [CSF].MBOrderTime			AS [CSF Order Time]

	, [CSF].CollectionTime		AS [CSF Order Collection Time]

	, [CSF].OrganismList		AS [CSF Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [CSF].MBOrderTime)	AS [Arrival To CSF Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [CSF].MBOrderTime)	AS [Triage To CSF Order Time]



	/* LDA */

	, [ETT].PLACEMENT_INSTANT AS [First ETT Placement Time]

	, [IV].PLACEMENT_INSTANT AS [First PIV Placement Time]

	, DATEDIFF(MI,[#ED_PositiveScores].RECORDED_TIME, [IV].PLACEMENT_INSTANT) AS [First Positive Screen To First PIV Placement]



	/* Transfers */

	, [#ED2HEMONC].ED2HemoncTime

	, ICU.ED2ICUTime

	, GEN.ED2GENTime

	, GEN.[Gen Back To ICU Time]

	, GEN.[Gen Back To ICU Department]



	/* BPA */

	, [#BPA].ALT_ACTION_INST	AS [First BPA CLINICAL_ALERTS/Action Time]

	, [#BPA].ACTION_TAKE		AS [Action Taken]

	, [#BPA].OVERRIDDEN			AS [BPA Overridden]

	, [#BPA].SPEC_OVR_CMNT		AS [BPA Overridden Comment]

	, [#BPA].[NAME]				AS [BPA Action User]



	, [#SepsisAlertCancelled].SEPSIS_ALERT_CANC_TIME

	, [#SepsisAlertCancelled].SEPSIS_ALERT_CANC_BY

	, CASE WHEN [#BPA].ALT_ACTION_INST IS NOT NULL THEN ISNULL([#SepsisAlertCancelled].SEPSIS_ALERT_CANC_YN, 'N') END AS [SEPSIS_ALERT_CANC_YN]



	/* Blood pressure */

	, CASE WHEN EXISTS (SELECT 1 FROM #BloodPressure WHERE [#BloodPressure].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [#BloodPressure].FLO_MEAS_ID = '95') THEN 'Y' ELSE 'N' END AS [Any BP During ED Stay?]



	, BE1.EVENT_TIME AS [ED IP Bed Requested Time]

	, BE2.EVENT_TIME AS [ED IP Bed Assigned Time]

	, DATEDIFF(MI,BE1.EVENT_TIME,BE2.EVENT_TIME) AS [Bed Request to Bed Assigned Time]

	, DATEDIFF(MI,BE1.EVENT_TIME, ICU.ED2ICUTime) AS [IP Bed Request to PICU Transfer Time]



	, CASE WHEN EXISTS (SELECT 1 FROM #ED_BORDER WHERE [#ED_BORDER].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID) THEN 'Y' ELSE 'N' END	AS [ED Border PATIENTS]

	, CASE WHEN READMIT.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END	AS [Sepsis Pos ED Readmit in 24Hrs]

	, CASE WHEN READMITALL.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END AS [ED Readmit in 24Hrs]

	, CASE WHEN SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END		AS [IPSO Severe Sepsis Criteria Met]

	, CASE WHEN NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END	AS [IPSO Non Severe Sepsis Criteria Met]

 

	/* Positive sepsis screen */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL THEN 1 ELSE 0 END	AS [Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL THEN 1 ELSE 0 END		AS [Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END		AS [Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL THEN 1 ELSE 0 END			AS [Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END		AS [Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL THEN 1 ELSE 0 END			AS [Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL THEN 1 ELSE 0 END				AS [Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NULL THEN 1 ELSE 0 END					AS [Positive Sepsis and Blood Culture NOT Ordered]



	/* Negative sepsis screen */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL THEN 1 ELSE 0 END	AS [Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL THEN 1 ELSE 0 END		AS [Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END			AS [Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL THEN 1 ELSE 0 END				AS [Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END		AS [Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL THEN 1 ELSE 0 END			AS [Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL THEN 1 ELSE 0 END				AS [Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NULL THEN 1 ELSE 0 END					AS [Negative Sepsis and Blood Culture NOT Ordered]



	/* IPSO severe (+) and Sepsis (+) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END					AS [IPSO SEVERE and Positive Sepsis and Blood Culture NOT Ordered]



	/* IPSO non-severe (+) and Sepsis (+) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO NON SEVERE and Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO NON SEVERE and Positive Sepsis and Blood Culture NOT Ordered]



	/* IPSO severe (+) and Sepsis (neg) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO SEVERE and Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Negative Sepsis and Blood Culture NOT Ordered]



	/* IPSO non-severe (+) and Sepsis (neg) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO NON SEVERE and Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO NON SEVERE and Negative Sepsis and Blood Culture NOT Ordered]



	/* Added 2025.11.24 V_DEV004 */

	-- Septic Shock criteria; Logic from [reports].USP_Severe_Sepsis for consistency

	, CASE

		WHEN DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [ABX1].ABX_ADMIN_TIME) <= 6*60

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB1].BOLUS_ADMIN_TIME) <= 6*60

			AND ( DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB2].BOLUS_ADMIN_TIME) <= 6*60

					OR

				  DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [#Pressors].TAKEN_TIME) <= 6*60

				)

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BLD].MBOrderTime) <= 72*60

			AND ( [BPB3].BOLUS_ADMIN_TIME IS NOT NULL

					OR

				  [#Pressors].TAKEN_TIME IS NOT NULL

				)



		THEN 'Septic Shock'

		

		WHEN DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [ABX1].ABX_ADMIN_TIME) <= 6*60

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB1].BOLUS_ADMIN_TIME) <= 6*60

			AND ( DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB2].BOLUS_ADMIN_TIME) <= 6*60

					OR

				  DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [#Pressors].TAKEN_TIME) <= 6*60

				)

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BLD].MBOrderTime) <= 72*60



		THEN 'Potential Septic Shock' 

		--ELSE 99	-- "Un-treated"

	  END AS [Septic Shock]



INTO #Final



FROM #Base_Pop BasePop



	LEFT OUTER JOIN [EMRDB].[dbo].ENCOUNTER_VISIT_REASONS	CHIEF_CMPLNT	ON CHIEF_CMPLNT.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND CHIEF_CMPLNT.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].VISIT_REASONS	CRFV			ON CRFV.REASON_VISIT_ID = CHIEF_CMPLNT.ENC_REASON_ID



	LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING]		SEVERE		ON SEVERE.DATE_STAMP = [BasePop].DATE_STAMP AND SEVERE.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN [reportingDB].[reports].[NON_SEVERE_SEPSIS_STAGING]	NONSEVERE	ON NONSEVERE.DATE_STAMP = [BasePop].DATE_STAMP AND NONSEVERE.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID



	LEFT OUTER JOIN #Base_Pop_SepsisScores_ConCat	ALLSCORES		ON ALLSCORES.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #Base_Pop_Severe_ED_Scores		SepsisScreened	ON SepsisScreened.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID and SepsisScreened.TIME_LINE=1



	LEFT OUTER JOIN #ED_PositiveScores							ON [#ED_PositiveScores].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [#ED_PositiveScores].FIRST_TIME_LINE=1

	LEFT OUTER JOIN #ED_NegativeScores							ON [#ED_NegativeScores].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [#ED_NegativeScores].FIRST_TIME_LINE=1



	-- Medications

	LEFT OUTER JOIN #BasePopABX						abx1		ON [BasePop].PAT_ENC_CSN_ID = ABX1.PAT_ENC_CSN_ID AND ABX1.TIME_LINE=1

	LEFT OUTER JOIN #BasePopABX						abx2		ON [BasePop].PAT_ENC_CSN_ID = ABX2.PAT_ENC_CSN_ID AND ABX2.TIME_LINE=2

	LEFT OUTER JOIN #BasePopBolus					BPB1		ON [BasePop].PAT_ENC_CSN_ID = BPB1.PAT_ENC_CSN_ID AND BPB1.TIME_LINE=1

	LEFT OUTER JOIN #BasePopBolus					BPB2		ON [BasePop].PAT_ENC_CSN_ID = BPB2.PAT_ENC_CSN_ID AND BPB2.TIME_LINE=2

	LEFT OUTER JOIN #BasePopBolus					BPB3		ON [BasePop].PAT_ENC_CSN_ID = BPB3.PAT_ENC_CSN_ID AND BPB3.TIME_LINE=3

	LEFT OUTER JOIN #Pressors									ON [BasePop].PAT_ENC_CSN_ID = [#Pressors].PAT_ENC_CSN_ID AND [#Pressors].TIME_LINE=1

	LEFT OUTER JOIN #FirstABXAdminTimeDetails		ABXTimes	ON ABXTimes.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID



	-- Flowsheets

	LEFT OUTER JOIN #EncounterWeights				EW			ON [BasePop].PAT_ENC_CSN_ID = EW.PAT_ENC_CSN_ID AND EW.TIME_LINE=1

	LEFT OUTER JOIN #Hypotension								ON [BasePop].PAT_ENC_CSN_ID = [#Hypotension].PAT_ENC_CSN_ID AND [#Hypotension].TIME_LINE=1



	-- LDAs

	LEFT OUTER JOIN #LDA							ETT			ON [BasePop].PAT_ENC_CSN_ID = [ETT].PAT_ENC_CSN_ID AND [ETT].LDA_PLACEMENT_TYPE = 'ETT'

	LEFT OUTER JOIN #LDA							IV			ON [BasePop].PAT_ENC_CSN_ID = [IV].PAT_ENC_CSN_ID AND [IV].LDA_PLACEMENT_TYPE = 'IV'

	LEFT OUTER JOIN #LDA							CVL			ON [BasePop].PAT_ENC_CSN_ID = [CVL].PAT_ENC_CSN_ID AND [CVL].LDA_PLACEMENT_TYPE = 'CVL'



	-- Labs and Cultures

	LEFT OUTER JOIN #Labs							SPO2		ON [BasePop].PAT_ENC_CSN_ID = [SPO2].PAT_ENC_CSN_ID AND [SPO2].LAB_TEST_TYPE = 'O2 Saturation'

	LEFT OUTER JOIN #Labs							LAC			ON [BasePop].PAT_ENC_CSN_ID = [LAC].PAT_ENC_CSN_ID AND [LAC].LAB_TEST_TYPE = 'Lactic Acid'

	LEFT OUTER JOIN #Labs							PCT			ON [BasePop].PAT_ENC_CSN_ID = [PCT].PAT_ENC_CSN_ID AND [PCT].LAB_TEST_TYPE = 'Procalcitonin'

	LEFT OUTER JOIN #Cultures						BLD			ON [BasePop].PAT_ENC_CSN_ID = [BLD].PAT_ENC_CSN_ID AND [BLD].CULTURE_TYPE = 'Blood' 

	LEFT OUTER JOIN #Cultures						URN			ON [BasePop].PAT_ENC_CSN_ID = [URN].PAT_ENC_CSN_ID AND [URN].CULTURE_TYPE = 'Urine' 

	LEFT OUTER JOIN #Cultures						CSF			ON [BasePop].PAT_ENC_CSN_ID = [CSF].PAT_ENC_CSN_ID AND [CSF].CULTURE_TYPE = 'CSF' 



	-- Transfers

	LEFT OUTER JOIN #ED2HEMONC									ON [BasePop].PAT_ENC_CSN_ID = [#ED2HEMONC].PAT_ENC_CSN_ID AND [#ED2HEMONC].TIME_LINE=1

	LEFT OUTER JOIN #ED2ICU							ICU			ON [BasePop].PAT_ENC_CSN_ID = [ICU].PAT_ENC_CSN_ID AND [ICU].TIME_LINE=1

	LEFT OUTER JOIN #ED2GEN							GEN			ON [BasePop].PAT_ENC_CSN_ID = [GEN].PAT_ENC_CSN_ID AND [GEN].TIME_LINE=1



	-- Miscellaneous

	LEFT OUTER JOIN #BPA										ON [BasePop].PAT_ENC_CSN_ID = [#BPA].PAT_ENC_CSN_ID AND [#BPA].TIME_LINE=1

	LEFT OUTER JOIN #Base_Pop_ED_Readmit_All		READMITALL	ON [READMITALL].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #Base_Pop_ED_Readmit			READMIT		ON [READMIT].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #Base_Pop_ENC_Reason			RSN			ON [RSN].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #FirstPositiveOD_To_ABXAdminTime OD2ABX		ON OD2ABX.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #SSOrderSet									ON [BasePop].PAT_ENC_CSN_ID = [#SSOrderSet].PAT_ENC_CSN_ID AND [#SSOrderSet].TIME_LINE=1

	LEFT OUTER JOIN #SepsisAlertCancelled						ON [BasePop].PAT_ENC_CSN_ID = [#SepsisAlertCancelled].PAT_ENC_CSN_ID AND [#SepsisAlertCancelled].TIME_LINE=1

	LEFT OUTER JOIN #BedEvents						BE1			ON [BE1].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [BE1].REQ_LINE=1 AND [BE1].TIME_LINE=1--BED REQUESTED

	LEFT OUTER JOIN #BedEvents						BE2			ON [BE2].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [BE2].REQ_LINE=1 AND [BE2].TIME_LINE=2--BED ASSIGNED







-- 2026-01-16 V_DEV004 pulled out (and simpplified) OUTER APPLYs to help the optimizer.

SELECT *



	,[FIRST_ADMIT_DEPARTMENT].ADT_DEPARTMENT_NAME AS [First IP Department]



	/* Blood pressure */

	-- remaining BP columns are all "within 30 mins of pos/neg"

	, [LAST_BP].RECORDED_TIME AS [Last Blood Pressure Time]

	, [LAST_BP].MEAS_VALUE AS [Last Blood Pressure Value]

	, DATEDIFF(MI,[LAST_BP].RECORDED_TIME, [First Positive Score Time]) AS [Last BP to First Positive Score Time]

	, DATEDIFF(MI,[LAST_BP].RECORDED_TIME, [First Positive Score Time]) AS [Last BP to First Negative Score Time]

	, [FIRST_BP].RECORDED_TIME AS [First Blood Pressure Time]

	, [FIRST_BP].MEAS_VALUE AS [First Blood Pressure Value]

	, DATEDIFF(MI, [First Positive Score Time], [FIRST_BP].RECORDED_TIME) AS [First Positive Score Time to First BP]

	, DATEDIFF(MI, [First Positive Score Time], [FIRST_BP].RECORDED_TIME) AS [First Negative Score Time to First BP]



	, [LAST_BP_PERCENTILE].RECORDED_TIME	AS [Last BP Percentile Time]

	, [LAST_BP_PERCENTILE].MEAS_VALUE		AS [Last BP Percentile Value]

	, [FIRST_BP_PERCENTILE].RECORDED_TIME	AS [First BP Percentile Time]

	, [FIRST_BP_PERCENTILE].MEAS_VALUE		AS [First BP Percentile Value]





	,[RESCREEN].RECORDED_TIME AS [ReScreen After FPS]

	,[REPEATSCREEN].RECORDED_TIME AS [Repeat Screen before ED Departure]





	,CASE	WHEN DATEDIFF(MI, [First Positive Score Time], [First ABX Admin Time]) <=60

				AND DATEDIFF(MI, [First Positive Score Time], [Bolus 1 Admin Time]) <=20

				AND [RESCREEN].RECORDED_TIME IS NOT NULL

			THEN 1 

			ELSE 0 

	  END AS [FPS Bolus ABX ReScreen Compliance]





from #Final



	OUTER APPLY

	(

		SELECT TOP 1 RECORDED_TIME

		FROM #Base_Pop_Severe_ED_Scores

		WHERE 1=1

			--AND [#Base_Pop_Severe_ED_Scores].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

			--AND [#ED_PositiveScores].FIRST_TIME_LINE = 1

			AND [#Base_Pop_Severe_ED_Scores].PAT_ENC_CSN_ID = [#Final].CSN

			AND (RECORDED_TIME > [First Positive Score Time] AND RECORDED_TIME <= DATEADD(MI, 90, [First Positive Score Time]))

		ORDER BY [First Positive Score Time] DESC

	) RESCREEN



	OUTER APPLY

	(

		SELECT TOP 1 RECORDED_TIME

		FROM #Base_Pop_Severe_ED_Scores

		WHERE 1=1

			AND [#Base_Pop_Severe_ED_Scores].PAT_ENC_CSN_ID = [#Final].CSN

			AND (RECORDED_TIME >  DATEADD(MI, -60, [ED Departure Time]) AND RECORDED_TIME < [ED Departure Time])

		ORDER BY RECORDED_TIME DESC

	) REPEATSCREEN



	OUTER APPLY

	(

		SELECT TOP 1 ADT_DEPARTMENT_NAME

		FROM #PatientLocation

		WHERE 1=1

			AND [#PatientLocation].PAT_ENC_CSN = [#Final].CSN 

			AND [#PatientLocation].IN_DTTM >= [ED Departure Time]

		ORDER BY [#PatientLocation].IN_DTTM ASC

	) FIRST_ADMIT_DEPARTMENT





	/* Previous blood pressure (up to 30 minutes prior to positive/negative screen) */

	OUTER APPLY

	(

		SELECT TOP 1 RECORDED_TIME, MEAS_VALUE

		FROM #BloodPressure

		WHERE 1=1

			AND FLO_MEAS_ID = '95'	-- Blood Pressure

			AND [#BloodPressure].PAT_ENC_CSN_ID = [#Final].CSN

			AND (

					RECORDED_TIME BETWEEN DATEADD(MI, -30, [First Positive Score Time]) AND [First Positive Score Time]

					OR

					-- first negative screen ONLY if encounter was never positive (so each CSN has either Pos or Neg, but not both)

					RECORDED_TIME BETWEEN DATEADD(MI, -30, [First Negative Score Time]) AND [First Negative Score Time]

				)

		ORDER BY RECORDED_TIME DESC	

	) LAST_BP



	/* Previous blood pressure percentile (up to 30 minutes prior to positive/negative screen) */

	OUTER APPLY

	(

		SELECT TOP 1 RECORDED_TIME, MEAS_VALUE

		FROM #BloodPressure

		WHERE 1=1

			AND FLO_MEAS_ID IN (

					'9001140203'	-- R PED GIRLS SYSTOLIC BP PERCENTILE

					,'9001140205'	-- R PED BOYS SYSTOLIC BP PERCENTILE 

				)

			AND [#BloodPressure].PAT_ENC_CSN_ID = [#Final].CSN

			AND (

					RECORDED_TIME BETWEEN DATEADD(MI, -30, [First Positive Score Time]) AND [First Positive Score Time]

					OR

					-- first negative screen ONLY if encounter was never positive (so each CSN has either Pos or Neg, but not both)

					RECORDED_TIME BETWEEN DATEADD(MI, -30, [First Negative Score Time]) AND [First Negative Score Time]

				)

		ORDER BY RECORDED_TIME DESC	

	) LAST_BP_PERCENTILE





	/* First blood pressure (up to 30 minutes after first positive/negative screen) */

	OUTER APPLY

	(

		SELECT TOP 1 RECORDED_TIME, MEAS_VALUE

		FROM #BloodPressure

		WHERE 1=1

			AND FLO_MEAS_ID = '95'	-- Blood Pressure

			AND [#BloodPressure].PAT_ENC_CSN_ID = [#Final].CSN

			AND (

					RECORDED_TIME BETWEEN [First Positive Score Time] AND DATEADD(MI, 30, [First Positive Score Time])

					OR

					-- first negative screen ONLY if encounter was never positive (so each CSN has either Pos or Neg, but not both)

					RECORDED_TIME BETWEEN [First Negative Score Time] AND DATEADD(MI, 30, [First Negative Score Time])

				)

		ORDER BY RECORDED_TIME DESC			

	) FIRST_BP



	/* First blood pressure (up to 30 minutes after first positive/negative screen) */

	OUTER APPLY

	(

		SELECT TOP 1 RECORDED_TIME, MEAS_VALUE

		FROM #BloodPressure

		WHERE 1=1

			AND FLO_MEAS_ID IN (

				'9001140203'	-- R PED GIRLS SYSTOLIC BP PERCENTILE

				,'9001140205'	-- R PED BOYS SYSTOLIC BP PERCENTILE 

				)

			AND [#BloodPressure].PAT_ENC_CSN_ID = [#Final].CSN

			AND (

					RECORDED_TIME BETWEEN [First Positive Score Time] AND DATEADD(MI, 30, [First Positive Score Time])

					OR

					-- first negative screen ONLY if encounter was never positive (so each CSN has either Pos or Neg, but not both)

					RECORDED_TIME BETWEEN [First Negative Score Time] AND DATEADD(MI, 30, [First Negative Score Time])

				)

		ORDER BY RECORDED_TIME DESC			

	) FIRST_BP_PERCENTILE



;
GO

-- ==== reporting/USP_IP_SEPSIS.sql ====
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

exec [reportingDB].[reporting].[USP_IP_SEPSIS]

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

	SET @dStartDate = [EMRDB].[dbo].[fn_parse_date]('MB-12') /*('2018-01-01')*/

ELSE

	SET @dStartDate = [EMRDB].[dbo].[fn_parse_date](@StartDate)

	

IF @EndDate IS NULL OR @EndDate = ''

	SET @dEndDate = [EMRDB].[dbo].[fn_parse_date]('ME-1') /*DEFAULTING TO PREVIOUS MONTH*/

ELSE

	SET @dEndDate = [EMRDB].[dbo].[fn_parse_date](@EndDate)





IF OBJECT_ID(N'tempdb..#MARActions') IS NOT NULL DROP TABLE #MARActions;

	SELECT CAST(vcg.LIST_CAT_VALUE_C AS varchar) CAT_ID

	INTO #MARActions

	FROM [EMRDB].[dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800007')

CREATE INDEX IDX_MARActions ON #MARActions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#RouteExclusions') IS NOT NULL DROP TABLE #RouteExclusions;

	SELECT vcg.LIST_CAT_VALUE_C CAT_ID

	INTO #RouteExclusions

	FROM [EMRDB].[dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800008')

	UNION 

	SELECT '11' /*intravenous*/

CREATE INDEX IDX_RouteExclusions ON #RouteExclusions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#BolusMeds') IS NOT NULL DROP TABLE #BolusMeds;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID MED_ID

	INTO #BolusMeds

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'ERX'

	AND vcg.BASE_GROUPER_ID IN ('800009')

CREATE INDEX IDX_BolusMeds ON #BolusMeds (MED_ID) 

	

IF OBJECT_ID(N'tempdb..#MedGroupers') IS NOT NULL DROP TABLE #MedGroupers;

	SELECT vcg.GROUPER_LIST VCG_ID

	INTO #MedGroupers

	FROM [EMRDB].[dbo].[GROUPER_GROUPS] vcg

	WHERE vcg.GROUPER_ID IN ('800011')

CREATE INDEX IDX_MedGroupers ON #MedGroupers (VCG_ID) 



IF OBJECT_ID(N'tempdb..#LacticAcidLRR') IS NOT NULL DROP TABLE #LacticAcidLRR;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID LRR_ID

	INTO #LacticAcidLRR

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'LRR'

	AND vcg.BASE_GROUPER_ID IN ('800012')

CREATE INDEX IDX_Lactic ON #LacticAcidLRR (LRR_ID) 



IF OBJECT_ID(N'tempdb..#BloodCultures') IS NOT NULL DROP TABLE #BloodCultures;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID PROC_ID

	INTO #BloodCultures

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'EAP'

	AND vcg.BASE_GROUPER_ID IN ('800013')

CREATE INDEX IDX_BloodCultures ON #BloodCultures (PROC_ID) 



IF OBJECT_ID(N'tempdb..#ProphylaxisFLO') IS NOT NULL DROP TABLE  #ProphylaxisFLO;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO  #ProphylaxisFLO

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800014')

CREATE INDEX IDX_ProphylaxisFLO ON #ProphylaxisFLO (FLO_ID) 



IF OBJECT_ID(N'tempdb..#CerebralOxFLO') IS NOT NULL DROP TABLE #CerebralOxFLO;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO  #CerebralOxFLO

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800015')

CREATE INDEX IDX_CerebralOxFLO ON #CerebralOxFLO (FLO_ID) 



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

CREATE INDEX IDX_Main ON #MainAdmDetails (PAT_ENC_CSN_ID) 

/*SELECT * FROM #MainAdmDetails*/



/*CHIEF COMPLIANT*/

IF OBJECT_ID(N'tempdb..#Base_Pop_ENC_Reason') IS NOT NULL DROP TABLE #Base_Pop_ENC_Reason;

SELECT DISTINCT cat.PAT_ENC_CSN_ID

	, STRING_AGG(edg.DX_NAME,  ' % ') AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM #MainAdmDetails cat

INNER JOIN [EMRDB].[dbo].[ENCOUNTER_DIAGNOSES] ped ON ped.PAT_ENC_CSN_ID = cat.PAT_ENC_CSN_ID AND ped.LINE > 1

INNER JOIN [EMRDB].[dbo].[DIAGNOSES] edg ON edg.DX_ID = ped.DX_ID

GROUP BY cat.PAT_ENC_CSN_ID

CREATE INDEX IDX_EncReason ON #Base_Pop_ENC_Reason (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Base_Pop_ENC_Reason*/



/***********************************************************************

Get Encounters and a record for every shift a PATIENTS was in a department for Compliance reporting

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_PopTemp') IS NOT NULL DROP TABLE #Base_PopTemp;

WITH vaplh AS

(

	SELECT 

		adtIn.PAT_ENC_CSN_ID

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

	FROM #MainAdmDetails csns

	INNER JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] hsp ON csns.PAT_ENC_CSN_ID = hsp.PAT_ENC_CSN_ID /*Developer C minimize to csn's we are looking at*/

	INNER JOIN [EMRDB].[dbo].[ADT_EVENTS] adtIn ON adtIn.PAT_ENC_CSN_ID = hsp.PAT_ENC_CSN_ID

	LEFT OUTER JOIN [EMRDB].[dbo].[ADT_EVENTS] adtOut ON adtIn.NEXT_OUT_EVENT_ID = adtOut.EVENT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].[DEPARTMENTS] dep ON adtIn.DEPARTMENT_ID = dep.DEPARTMENT_ID

	WHERE adtIn.EVENT_TYPE_C IN (1, 3, 99) /*Only look at "in" events (Admission and Transfer In, LOA Return)*/

	AND adtIn.EVENT_SUBTYPE_C <> 2 /*Exclude deleted/canceled events*/

)



SELECT DISTINCT

	peh.PAT_ENC_CSN_ID

	, peh.PAT_ID

	, vaplh.ADT_DEPARTMENT_ID

	, vaplh.ADT_DEPARTMENT_NAME

	, cvs.CODE_DESC AS DEPARTMENT_ROLLUP

	, vaplh.IN_DTTM

	, vaplh.OUT_DTTM

	, peh.INPATIENT_DATA_ID

	, main.BIRTH_DATE

	, peh.ADT_ARRIVAL_TIME

	, peh.ED_DEPARTURE_TIME

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

	, ROW_NUMBER() OVER (PARTITION BY peh.PAT_ENC_CSN_ID, vaplh.IN_DTTM ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM) [inDeptRN]

	, ROW_NUMBER() OVER (PARTITION BY peh.PAT_ENC_CSN_ID ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM ) [CSN Order]

INTO #Base_PopTemp

FROM #MainAdmDetails main

INNER JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] peh ON peh.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

INNER JOIN  vaplh ON vaplh.PAT_ENC_CSN_ID = peh.PAT_ENC_CSN_ID AND vaplh.ADT_DEPARTMENT_ID IS NOT NULL /*[EMRDB].[dbo].V_PATIENT_LOCATION_HISTORY*/

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

	FROM dateCTE pm 

	CROSS APPLY ( 

		SELECT DATEADD(MI, 1140, DATEADD(DD, 0, DATEDIFF(DD, 0, pm.[Expansion Date]))) [Shift Start]

			, DATEADD(MI, 419, DATEADD(DD, 1, DATEDIFF(DD, 0, pm.[Expansion Date]))) [Shift End]

	) a

	WHERE pm.[PM Denom] = 1

) a

OPTION (MAXRECURSION 8000);  /*default is 100*/

CREATE INDEX IDX_Base_Pop ON #Base_Pop (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Base_Pop*/



IF OBJECT_ID(N'tempdb..#FlwshtLstEncounterWts') IS NOT NULL DROP TABLE #FlwshtLstEncounterWts;

SELECT * , ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY [CSN Order], [Unit Order], RECORDED_TIME) AS [Weight Row]

INTO #FlwshtLstEncounterWts

FROM 

(

	SELECT 

		main.PAT_ENC_CSN_ID

		, meas.FSD_ID

		, meas.MEAS_VALUE

		, meas.RECORDED_TIME

		, main.[CSN Order]

		, main.[Unit Order]

		, main.[CSN Overall Order]

		, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID, [CSN Order], [Unit Order] ORDER BY [CSN Order], [Unit Order], RECORDED_TIME) AS [Unit Order Row]

	FROM #Base_Pop main 

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '94'

	WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

) a

WHERE a.[Unit Order Row] = 1

CREATE INDEX IDX_FloEncWeight ON #FlwshtLstEncounterWts (PAT_ENC_CSN_ID) 

/*SELECT * FROM #FlwshtLstEncounterWts */



IF OBJECT_ID(N'tempdb..#EncWeights') IS NOT NULL DROP TABLE #EncWeights;

SELECT

	PAT_ENC_CSN_ID

	, EncWeight

	, [CSN Order]

	, [Unit Order]

	, [CSN Overall Order]

	, [Weight Row]

	, CASE WHEN [Previous Weight Record] IS NULL THEN 1 ELSE [CSN Overall Order] + 1 END AS [Start Weight Record]

	, CASE WHEN [Next Weight Record] IS NULL THEN 

		( SELECT MAX([CSN Overall Order]) FROM #Base_Pop bp WHERE bp.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID)

	ELSE [Next Weight Record] - 1 END AS [Next Weight Record]

INTO #EncWeights

FROM (

	SELECT

		encWt.PAT_ENC_CSN_ID

		, CAST(ROUND(CONVERT(FLOAT, encWt.MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

		, [CSN Order]

		, [Unit Order]

		, [CSN Overall Order]

		, [Weight Row]

		, LAG([CSN Overall Order], 1) OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY PAT_ENC_CSN_ID, [Weight Row]) AS [Previous Weight Record]

		, LEAD([CSN Overall Order], 1) OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY PAT_ENC_CSN_ID, [Weight Row]) AS [Next Weight Record]

	FROM #FlwshtLstEncounterWts encWt

) a



IF OBJECT_ID(N'tempdb..#EncounterWeights') IS NOT NULL DROP TABLE #EncounterWeights;

	SELECT bp.PAT_ENC_CSN_ID

		, bp.[CSN Overall Order]

		, e.EncWeight

	INTO #EncounterWeights

	FROM #Base_Pop bp

	INNER JOIN #EncWeights e ON bp.PAT_ENC_CSN_ID = e.PAT_ENC_CSN_ID AND e.[CSN Overall Order] = bp.[CSN Overall Order]

UNION 

	SELECT  bp.PAT_ENC_CSN_ID

		, bp.[CSN Overall Order]

		, e.EncWeight 

	FROM #Base_Pop bp

	INNER JOIN #EncWeights e ON bp.PAT_ENC_CSN_ID = e.PAT_ENC_CSN_ID AND bp.[CSN Overall Order] between e.[Start Weight Record] AND e.[Next Weight Record]

CREATE INDEX IDX_EncounterWeights ON #EncounterWeights (PAT_ENC_CSN_ID) 

/*SELECT * FROM #EncounterWeights*/



/*****************************POSITIVE ED SEPSIS SCORES & ED LOS*****************************/

IF OBJECT_ID(N'tempdb..#Base_Pop_Severe_ED_Scores') IS NOT NULL DROP TABLE #Base_Pop_Severe_ED_Scores;

SELECT main.PAT_ENC_CSN_ID

	, CEILING(CONVERT(FLOAT,DATEDIFF(MI, main.ADT_ARRIVAL_TIME, main.ED_DEPARTURE_TIME))/60) HoursInED/*CHECK WITH STEPHANIE ON */

	, main.ADT_ARRIVAL_TIME

	, meas.MEAS_VALUE

	, meas.RECORDED_TIME

	, main.ED_DEPARTURE_TIME

	, ROW_NUMBER() OVER(PARTITION BY main.PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #Base_Pop_Severe_ED_Scores 

FROM #MainAdmDetails main 

INNER JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] PEH ON PEH.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = PEH.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID and

	meas.FLO_MEAS_ID IN ('9000161709','9000002613')/*SEPSIS SCORE ADDED NEW ED SEPSIS SCORE 9000002613 ON 10.01.2019*/

	and (meas.RECORDED_TIME <=  main.ED_DEPARTURE_TIME)

CREATE INDEX IDX_Pop_Severe_ED_Scores ON #Base_Pop_Severe_ED_Scores (PAT_ENC_CSN_ID) 

/*Select * from #Base_Pop_Severe_ED_Scores*/



IF OBJECT_ID(N'tempdb..#EDPosScore_EDLOS') IS NOT NULL DROP TABLE #EDPosScore_EDLOS;

SELECT edScore.PAT_ENC_CSN_ID

	, edScore.HoursInED

	, edScore.MEAS_VALUE

	, edScore.RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY edScore.PAT_ENC_CSN_ID ORDER BY edScore.RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY edScore.PAT_ENC_CSN_ID ORDER BY edScore.RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO #EDPosScore_EDLOS

FROM #Base_Pop_Severe_ED_Scores edScore

WHERE edScore.MEAS_VALUE > 4

CREATE INDEX IDX_EDPosScore_EDLOS ON #EDPosScore_EDLOS (PAT_ENC_CSN_ID) 

/*SELECT * FROM #EDPosScore_EDLOS*/



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



IF OBJECT_ID(N'tempdb..#SepsisAuditTemp') IS NOT NULL DROP TABLE #SepsisAuditTemp;

SELECT main.PAT_ENC_CSN_ID, main.[CSN Overall Order], od.[OD Score Time], meas.FLO_MEAS_ID, meas.MEAS_VALUE, meas.RECORDED_TIME

	, DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME) [Time since OD Score]

	, ABS(DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME)) [ABS Time since OD Score]

INTO #SepsisAuditTemp

FROM #Base_Pop main

INNER JOIN #Base_Pop_OD_Scores od ON od.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND od.[CSN Overall Order] = main.[CSN Overall Order]

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON od.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000161701', '9000161702', '9000161710', '9000161708', '9000161704', '9000002611'

			, '98', '99', '95', '9000800500', '900101', '900103', '900102', '900104', '900105', '900107', '900106'

			, '900108', '9000002702', '900109', '900110', '9000311801', '9000311802', '9000311803', '9000003157')

WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

AND od.ShowComponents = 'Y'

AND DATEDIFF(MINUTE, od.[OD Score Time], meas.RECORDED_TIME) BETWEEN -30 AND 180 /*WAS -120 UNTIL 03.01.2021 */



IF OBJECT_ID(N'tempdb..#FlwshtLstSepsisAudit') IS NOT NULL DROP TABLE #FlwshtLstSepsisAudit;

SELECT bp.PAT_ENC_CSN_ID

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

	, bp.[CSN Overall Order]

INTO #FlwshtLstSepsisAudit

FROM #Base_Pop bp 

INNER JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] peh ON peh.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

LEFT OUTER JOIN #FlwshtLst meas ON meas.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND meas.[CSN Overall Order] = bp.[CSN Overall Order]

OUTER APPLY 

(

	SELECT bp.PAT_ENC_CSN_ID

		, bp.[CSN Overall Order]

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

			subMeas.PAT_ENC_CSN_ID

			, subMeas.FLO_MEAS_ID

			, subMeas.RECORDED_TIME

			, subMeas.MEAS_VALUE

			, ROW_NUMBER() OVER (PARTITION BY subMeas.PAT_ENC_CSN_ID, subMeas.[CSN Overall Order], subMeas.FLO_MEAS_ID ORDER BY subMeas.[ABS Time since OD Score]) rownumber

			, subMeas.[CSN Overall Order]

			, subMeas.[ABS Time since OD Score]

		FROM #SepsisAuditTemp subMeas

		WHERE subMeas.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

		AND subMeas.[CSN Overall Order] = bp.[CSN Overall Order]

		AND subMeas.MEAS_VALUE IS NOT NULL

	) a

	WHERE a.rownumber = 1

	GROUP BY PAT_ENC_CSN_ID, [CSN Overall Order]

) sepsisAudit



/*****************************Hypotension*****************************/

IF OBJECT_ID(N'tempdb..#FlwShtHypo') IS NOT NULL DROP TABLE #FlwShtHypo;

Select

	main.PAT_ENC_CSN_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME [Hypotension Time] 

	, meas.MEAS_VALUE

	, meas.FSD_ID 

	, main.AGE_MONTHS /*Age at shift start*/

	, main.AGE_YEARS /*Age at shift start*/

	, main.[CSN Overall Order]

Into #FlwShtHypo 

FROM #Base_Pop main

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '95' AND meas.MEAS_VALUE IS NOT NULL

WHERE meas.RECORDED_TIME BETWEEN main.[Shift Start] AND main.[Shift End]

CREATE INDEX IDX_FlwShtHypo ON #FlwShtHypo (PAT_ENC_CSN_ID, [CSN Overall Order])

/*SELECT * FROM #FlwShtHypo*/



IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;

SELECT    

	base.PAT_ENC_CSN_ID

	, base.AGE_MONTHS

	, base.AGE_YEARS

	, CASE WHEN meas.[Hypotension Time] BETWEEN base.InDepartmentTime AND base.OutDepartmentTime THEN 'Y' ELSE 'N' END [In Dept]

	, base.InDepartmentTime    

	, hypo.[Hypotension Value]    

	, meas.[Hypotension Time]    

	, systolic.SYSTOLIC    

	, base.[CSN Order]

	, base.[Unit Order]

	, base.[CSN Overall Order]

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[CSN Order], base.[Unit Order] ORDER BY base.[CSN Overall Order] ASC) AS TIME_LINE 

INTO #Hypotension 

FROM #Base_Pop base 

INNER JOIN #FlwShtHypo meas ON meas.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID AND meas.[CSN Overall Order] = base.[CSN Overall Order]

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

	WHERE hypo.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID 

	AND hypo.[Hypotension Time] < a.[OD Score Time]

	ORDER BY HYPO.[Hypotension Time] DESC

)lastHypo

OUTER APPLY

(

	SELECT TOP 1 hypo.[Hypotension Time], hypo.[Hypotension Value], hypo.[In Dept]

	FROM #Hypotension hypo

	WHERE hypo.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID 

	AND hypo.[Hypotension Time] >= a.[OD Score Time]

	ORDER BY hypo.[Hypotension Time] ASC

)firstHypo

CREATE INDEX IDX_ODHYPO ON #ODHYPO (PAT_ENC_CSN_ID) 

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

	om.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, med.NAME

	, mar.TAKEN_TIME AS ABX_ADMIN_TIME

	, mar.SIG AS BOLUS_VOLUME

	, CASE WHEN mar.TAKEN_TIME BETWEEN base.[Shift Start] AND base.[Shift End] THEN base.[CSN Overall Order] ELSE NULL END [In Shift]

	, ROW_NUMBER() OVER(PARTITION BY om.PAT_ENC_CSN_ID ORDER BY mar.TAKEN_TIME) TIME_LINE

INTO #BasePopABX

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[MEDICATION_ORDERS] om	ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[MEDICATIONS] med ON med.MEDICATION_ID = om.MEDICATION_ID AND med.THERA_CLASS_C = 11 /*Antibiotics*/

INNER JOIN [EMRDB].[dbo].MED_DETAILS_EXT med2 ON med2.MEDICATION_ID = med.MEDICATION_ID /*Developer C Adding to be able to exclude ADMIN_ROUTE_C instead of text*/

INNER JOIN [EMRDB].[dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = om.ORDER_MED_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE) /*Developer C Change to Date to search for action*/

WHERE mar.TAKEN_TIME IS NOT NULL /*ADMINISTERED ABX ONLY*/

AND mar.MAR_ACTION_C IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

/*VALUES BELOW ADDED TO THE CODE ON STEPHANIE'S REQUEST DURING VALIDATION.*/

AND med2.ADMIN_ROUTE_C NOT IN (SELECT * FROM #RouteExclusions)

CREATE INDEX IDX_BasePopABX ON #BasePopABX (PAT_ENC_CSN_ID) 

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

		, abx.PAT_ENC_CSN_ID

		, abx.ADT_DEPARTMENT_NAME

		, abx.BOLUS_VOLUME

		, DATEDIFF(MI, abx.ABX_ADMIN_TIME, scores.[OD Score Time]) AS [Last ABX to OD Score Time] 

		, TIME_LINE

	FROM #BasePopABX abx

	WHERE abx.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

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

		, abx.PAT_ENC_CSN_ID

		, abx.ADT_DEPARTMENT_NAME

		, abx.BOLUS_VOLUME

		, DATEDIFF(MI, scores.[OD Score Time], abx.ABX_ADMIN_TIME) AS [OD Score to First ABX Time] 

		, TIME_LINE

	FROM #BasePopABX abx

	WHERE abx.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND abx.ABX_ADMIN_TIME >= scores.[OD Score Time]

	ORDER BY abx.ABX_ADMIN_TIME ASC

) firstAbx

CREATE INDEX IDX_ODABX ON #ODABX (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODABX*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#BasePopABX') IS NOT NULL DROP TABLE #BasePopABX;

/*****************************END OF ABX*****************************/



/*****************************ORDER SET*****************************/

/*All encounters from #Base_pop where Bolus was administered*/

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

SELECT DISTINCT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, om.ORDER_DTTM

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY om.ORDER_DTTM ASC) AS TIME_LINE

	, om.PRL_ORDERSET_ID

INTO #SSOrderSet 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].ORDER_TRACKING_METRICS om ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(om.ORDER_DTTM AS Date)

WHERE om.PRL_ORDERSET_ID IN (400001) /*(40400100, 40400058, 40400196, 40400153, 4058600002, 400001) Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway*/

CREATE INDEX IDX_SSOrderSet ON #SSOrderSet (PAT_ENC_CSN_ID) 

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

	WHERE sos.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND sos.ORDER_DTTM < scores.[OD Score Time]

	ORDER BY sos.ORDER_DTTM DESC

)lastOs

OUTER APPLY

(

	SELECT TOP 1 sos.ORDER_DTTM

		, sos.PRL_ORDERSET_ID 

	FROM #SSOrderSet sos

	WHERE sos.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND sos.ORDER_DTTM >= scores.[OD Score Time]

	ORDER BY sos.ORDER_DTTM ASC

)firstOs

CREATE INDEX IDX_ODORDSET ON #ODORDSET (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODORDSET*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

/*****************************END OF ORDER SET*****************************/



/*****************************BOLUS*****************************/

IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, mar.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, med.NAME AS Medication

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY mar.TAKEN_TIME ASC) TIME_LINE

	, mar.SIG AS BOLUS_VOLUME

INTO #BasePopBolus 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[MEDICATION_ORDERS] om ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[MEDICATIONS] med ON med.MEDICATION_ID = om.MEDICATION_ID

INNER JOIN [EMRDB].[dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = om.ORDER_MED_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE)

WHERE mar.TAKEN_TIME IS NOT NULL /*ADMINISTERED BOLUS ONLY*/

/*Developer C VCG Grouper 800009  Added 700004 */

AND (om.MEDICATION_ID IN (SELECT * FROM #BolusMeds)

	OR (om.MEDICATION_ID = 700004)

AND om.HV_DISCR_FREQ_ID = '300902') /*FREQUENCY = ONCE*/

/*Developer C VCG Grouper 1222252*/

AND mar.MAR_ACTION_C IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

AND CONVERT(NUMERIC, mar.SIG ) > 95.0

CREATE INDEX IDX_BasePopBolus ON #BasePopBolus (PAT_ENC_CSN_ID) 

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

	WHERE bol.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

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

	WHERE bol.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND bol.BOLUS_ADMIN_TIME >= scores.[OD Score Time]

	ORDER BY bol.BOLUS_ADMIN_TIME ASC

)firstBol

CREATE INDEX IDX_OdboL ON #OdboL (PAT_ENC_CSN_ID) 

/*SELECT * FROM #OdboL*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

/*****************************END OF BOLUS*****************************/



/*****************************CVL TIMES*****************************/

/*CVL TIME - TEST CSN 1016010350*/

IF OBJECT_ID(N'tempdb..#ALLCVLTime') IS NOT NULL DROP TABLE #ALLCVLTime;

SELECT DISTINCT

	b.PAT_ENC_CSN_ID

	, b.ADT_DEPARTMENT_ID

	, b.ADT_DEPARTMENT_NAME

	, b.InDepartmentTime

	, b.OutDepartmentTime

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY b.PAT_ENC_CSN_ID, b.ADT_DEPARTMENT_ID, b.InDepartmentTime ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

INTO #ALLCVLTime

FROM #Base_Pop b

INNER JOIN [EMRDB].[dbo].[LINE_DEVICE_AIRWAY] lda ON lda.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID 

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

/*Developer C Replace this with VCG 800010*/

INNER JOIN [reportingDB].[reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = lda.FLO_MEAS_ID

			AND cvs.VALUE_SET_ID = 3022 /*CVL CODES*/

CREATE INDEX IDX_ALLCVLTime ON #ALLCVLTime (PAT_ENC_CSN_ID) 

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

	WHERE cvl.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND cvl.PLACEMENT_INSTANT < scores.[OD Score Time]

	ORDER BY cvl.PLACEMENT_INSTANT DESC

)lastCvl

OUTER APPLY

(

	SELECT TOP 1 cvl.PLACEMENT_INSTANT 

	FROM #ALLCVLTime cvl

	WHERE cvl.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND cvl.PLACEMENT_INSTANT >= scores.[OD Score Time]

	ORDER BY cvl.PLACEMENT_INSTANT ASC

)firstCVL

CREATE INDEX IDX_ODCVL ON #ODCVL (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODCVL*/



/*****************************clean up table*****************************/

	IF OBJECT_ID(N'tempdb..#ALLCVLTime') IS NOT NULL DROP TABLE #ALLCVLTime;

/*****************************END OF CVL TIMES*****************************/



/*****************************PRESSORS TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;

SELECT DISTINCT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, mar.TAKEN_TIME

	, gmr.GROUPER_ID

	, cm.NAME AS MEDICATION

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY mar.TAKEN_TIME) AS TIME_LINE

INTO #Pressors 

FROM #Base_Pop base

LEFT JOIN [EMRDB].[dbo].[MEDICATION_ORDERS] om ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

LEFT JOIN [EMRDB].[dbo].[MEDICATIONS] cm ON cm.MEDICATION_ID = om.MEDICATION_ID

LEFT JOIN [EMRDB].[dbo].GROUPER_MED_RECORDS gmr ON gmr.EXP_MEDS_LIST_ID = cm.MEDICATION_ID

LEFT JOIN [EMRDB].[dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = om.ORDER_MED_ID

LEFT JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE)

LEFT JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] peh ON peh.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

WHERE

gmr.GROUPER_ID IN (SELECT * FROM #MedGroupers)

AND mar.MAR_ACTION_C IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

AND mar.ROUTE_C = 11 /*INTRAVENOUS*/

CREATE INDEX IDX_Pressors ON #Pressors (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Pressors*/



IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

SELECT p.PAT_ENC_CSN_ID

	, CASE WHEN p.GROUPER_ID = '8000100'   THEN 'EPINEPHRINE' /*HS RX EPINEPHRINE SEPSIS*/

		WHEN p.GROUPER_ID =  '8000101' THEN 'DOPAMINE'

		WHEN p.GROUPER_ID = '8000102'   THEN 'DOBUTAMINE'

		WHEN p.GROUPER_ID = '8000103'   THEN 'MILRINONE'

		WHEN p.GROUPER_ID = '8000104'   THEN 'NOREPINEPHRINE'

	END PRESSOR

	, COUNT(p.TAKEN_TIME) AS MYC

INTO #ODPressorSummary

FROM #Pressors p

GROUP BY p.PAT_ENC_CSN_ID, p.GROUPER_ID

CREATE INDEX IDX_ODPressorSummary ON #ODPressorSummary (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODPressorSummary*/

	

/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;



IF OBJECT_ID ('TEMPDB..#ODPressorPivot') IS NOT NULL DROP TABLE #ODPressorPivot

SELECT PAT_ENC_CSN_ID

	, pvt.[EPINEPHRINE] AS [EPINEPHRINE]

	, pvt.[DOPAMINE] AS [DOPAMINE]

	, pvt.[DOBUTAMINE] AS [DOBUTAMINE]

	, pvt.[MILRINONE] AS [MILRINONE]

	, pvt.[NOREPINEPHRINE] AS [NOREPINEPHRINE]

INTO #ODPressorPivot

FROM #ODPressorSummary p

PIVOT( MAX(myc)

FOR PRESSOR IN ([EPINEPHRINE],[DOPAMINE],[DOBUTAMINE],[MILRINONE],[NOREPINEPHRINE])) AS pvt

CREATE INDEX IDX_ODPressorPivot ON #ODPressorPivot (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODPressorPivot*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

/*****************************END OF PRESSORS TIMES*****************************/



/*****************************SVO2 TIMES*****************************/

IF OBJECT_ID(N'tempdb..#SVO2') IS NOT NULL DROP TABLE #SVO2;

SELECT base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, op.ORDER_TIME AS SVO2OrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY op.ORDER_TIME ASC) AS TIME_LINE

	, ordR.ORDER_PROC_ID

INTO #SVO2

FROM #Base_Pop base

	INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] ordR ON base.PAT_ENC_CSN_ID = ordR.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op ON op.ORDER_PROC_ID = ordR.ORDER_PROC_ID

WHERE ordR.COMPONENT_ID IN (5000001861, 5000000478)

CREATE INDEX IDX_SVO2 ON #SVO2 (PAT_ENC_CSN_ID) 

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

	WHERE SVO2.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND SVO2.SVO2OrderTime < scores.[OD Score Time]

	ORDER BY SVO2.SVO2OrderTime DESC

) lastSVO2

OUTER APPLY

(

	SELECT TOP 1 SVO2.SVO2OrderTime FROM #SVO2 SVO2

	WHERE SVO2.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND SVO2.SVO2OrderTime >= scores.[OD Score Time]

	ORDER BY SVO2.SVO2OrderTime ASC

)firstSVO2

CREATE INDEX IDX_ODSVO2 ON #ODSVO2 (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODSVO2*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#SVO2') IS NOT NULL DROP TABLE #SVO2;

/*****************************END OF SVO2 TIMES*****************************/



/*****************************LACTIC ACID TIMES*****************************/

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, op.ORDER_PROC_ID

	, op.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY op.ORDER_TIME, base.InDepartmentTime, ordR.RESULT_TIME ASC) AS TIME_LINE -- Developer C added Result time

INTO #LacticAcid

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] ordR ON ordR.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op ON op.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID IN (SELECT * FROM #LacticAcidLRR)

CREATE INDEX IDX_LacticAcid ON #LacticAcid (PAT_ENC_CSN_ID) 

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

	WHERE lacA.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID 

	AND lacA.MBOrderTime < base.[OD Score Time]

	ORDER BY lacA.RESULT_TIME DESC

)lastLA

OUTER APPLY

(

	SELECT TOP 1 lacA.MBOrderTime

		, lacA.ORD_VALUE 

	FROM #LacticAcid lacA

	WHERE lacA.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID 

	AND lacA.MBOrderTime >= base.[OD Score Time]

	ORDER BY lacA.RESULT_TIME ASC

)firstLA

CREATE INDEX IDX_ODLA ON #ODLA(PAT_ENC_CSN_ID)

/*SELECT * FROM #ODLA ORDER BY TIME_LINE*/

 

/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

/*****************************END OF LACTIC ACID TIMES*****************************/



/*****************************PROCALCITONIN TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, op.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY op.ORDER_TIME ASC) AS TIME_LINE

	, ordR.ORDER_PROC_ID

INTO #Procalcitonin

FROM  #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] ordR ON ordR.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op ON op.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID = 500001 /*COULD USE PROC CODE ALSO.... LAB014*/

CREATE INDEX IDX_Procalcitonin ON #Procalcitonin (PAT_ENC_CSN_ID) 

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

	WHERE procal.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID 

	AND procal.MBOrderTime < base.[OD Score Time]

	ORDER BY procal.MBOrderTime DESC

)lastPro

OUTER APPLY

(

	SELECT TOP 1 procal.MBOrderTime

		, procal.ORD_VALUE 

	FROM #Procalcitonin procal

	WHERE procal.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID 

	AND procal.MBOrderTime >= base.[OD Score Time]

	ORDER BY procal.MBOrderTime ASC

)firstPro

CREATE INDEX IDX_ODPROCAL ON #ODPROCAL (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODPROCAL*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

/*****************************END OF PROCALCITONIN TIMES*****************************/



/*****************************BLOOD CULTURE TIMES*****************************/

/*Blood Culture*/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

SELECT base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, op.ORDER_PROC_ID

	, eap.PROC_CODE AS [Blood Culture Procedure Ordered]

	, op.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY op.ORDER_TIME, res.RESULT_TIME ASC) AS TIME_LINE

INTO #BloodCultureValue 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] res ON base.PAT_ENC_CSN_ID = res.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op  ON res.ORDER_PROC_ID = op.ORDER_PROC_ID 

			AND op.PROC_ID IN (SELECT * FROM #BloodCultures)

INNER JOIN [EMRDB].[dbo].[PROCEDURES_CATALOG] eap ON eap.PROC_ID = op.PROC_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

CREATE INDEX IDX_BloodCultureValue ON #BloodCultureValue (PAT_ENC_CSN_ID) 

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

	WHERE bc.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND bc.RESULT_TIME < scores.[OD Score Time]

	ORDER BY bc.MBOrderTime DESC, bc.RESULT_TIME DESC

)lastbc

OUTER APPLY

(

	SELECT TOP 1 bc.[Blood Culture Procedure Ordered]

		, bc.MBOrderTime

		, bc.ORD_VALUE 

	FROM #BloodCultureValue bc

	WHERE bc.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND bc.RESULT_TIME >= scores.[OD Score Time]

	ORDER BY bc.MBOrderTime ASC, bc.RESULT_TIME ASC

)firstbc

CREATE INDEX IDX_ODBC ON #ODBC (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODBC*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

/*****************************END OF BLOOD CULTURE TIMES*****************************/



/*****************************CSF TIMES*****************************/

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, op.ORDER_PROC_ID

	, eap.PROC_CODE as [CSF Procedure Ordered]

	, op.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY op.ORDER_TIME ASC) AS TIME_LINE

INTO #CSF 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] res ON base.PAT_ENC_CSN_ID = res.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op  ON res.ORDER_PROC_ID = op.ORDER_PROC_ID

			AND PROC_ID IN (600005, 600006) AND op.SPECIMEN_SOURCE_C = 304

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

INNER JOIN [EMRDB].[dbo].[PROCEDURES_CATALOG] eap ON eap.PROC_ID = op.PROC_ID

CREATE INDEX IDX_CSF ON #CSF (PAT_ENC_CSN_ID) 

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

	WHERE csf.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND csf.MBOrderTime < scores.[OD Score Time]

	ORDER BY csf.MBOrderTime DESC

)lastCF

OUTER APPLY

(

	SELECT TOP 1 csf.[CSF Procedure Ordered]

		, csf.MBOrderTime 

		FROM #CSF csf

	WHERE csf.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND csf.MBOrderTime >= scores.[OD Score Time]

	ORDER BY csf.MBOrderTime ASC

)firstCF

CREATE INDEX IDX_ODCSF ON #ODCSF (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODCSF*/



/*****************************clean up table*****************************/

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

/*****************************END OF CSF TIMES*****************************/



/*****************************ETT TIMES*****************************/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

SELECT base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

INTO #ETT

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LINE_DEVICE_AIRWAY] lda ON lda.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID AND lda.FLO_MEAS_ID = '900112' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

CREATE INDEX IDX_ETT ON #ETT (PAT_ENC_CSN_ID) 

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

	WHERE ett.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND ett.PLACEMENT_INSTANT < scores.[OD Score Time]

	ORDER BY ett.PLACEMENT_INSTANT DESC

)lastETT

OUTER APPLY

(

	SELECT TOP 1 ett.PLACEMENT_INSTANT 

	FROM #ETT ett

	WHERE ett.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND ett.PLACEMENT_INSTANT >= scores.[OD Score Time]

	ORDER BY ett.PLACEMENT_INSTANT ASC

)firstETT

CREATE INDEX IDX_ODETT ON #ODETT (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODETT*/



/*****************************clean up temp table*****************************/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

/*****************************END OF ETT TIMES*****************************/



/*****************************PIV TIMES*****************************/

IF OBJECT_ID(N'tempdb..#PIV') IS NOT NULL DROP TABLE #PIV;

SELECT base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.InDepartmentTime

	, base.OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

INTO #PIV

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LINE_DEVICE_AIRWAY] lda ON lda.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID AND lda.FLO_MEAS_ID='900111' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

CREATE INDEX IDX_PIV ON #PIV (PAT_ENC_CSN_ID) 

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

	WHERE piv.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND piv.PLACEMENT_INSTANT < scores.[OD Score Time]

	ORDER BY PIV.PLACEMENT_INSTANT DESC

)lastPIV

OUTER APPLY

(

	SELECT TOP 1 PIV.PLACEMENT_INSTANT 

	FROM #PIV piv

	WHERE piv.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID 

	AND piv.PLACEMENT_INSTANT >= scores.[OD Score Time]

	ORDER BY PIV.PLACEMENT_INSTANT ASC

)firstPIV

CREATE INDEX IDX_ODPIV ON #ODPIV (PAT_ENC_CSN_ID) 

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

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID

/*Developer C VCG Grouper 800014 (SELECT * FROM #ProphylaxisFLO)*/

WHERE FLO_MEAS_ID IN ('9000613042','9000613043','9000613044','9000613045','9000613047','9000613048','9000613050')

AND RECORDED_TIME IS NOT NULL

)

/*SELECT * FROM FlwshtProp*/



SELECT base.PAT_ENC_CSN_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS PROPHYLAXIS_YN

	, base.[CSN Overall Order]

INTO #PROPHYLAXIS

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN FlwshtProp meas ON meas.FSD_ID = rec.FSD_ID

GROUP BY base.PAT_ENC_CSN_ID, base.[CSN Overall Order]

CREATE INDEX IDX_PROPHYLAXIS ON #PROPHYLAXIS (PAT_ENC_CSN_ID) 

/*SELECT * FROM #PROPHYLAXIS*/

/*****************************END OF PROPHYLAXIS*****************************/



/*****************************CVVH*****************************/

IF OBJECT_ID(N'tempdb..#CVVH') IS NOT NULL DROP TABLE #CVVH;

SELECT base.PAT_ENC_CSN_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS CVVH_YN

	, base.[CSN Overall Order]

INTO #CVVH

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID AND meas.FLT_ID='9000001359'--ANY FLOWSHEET FROM THIS TEMPLATE IS A CANDIDATE

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

GROUP BY base.PAT_ENC_CSN_ID, base.[CSN Overall Order]

CREATE INDEX IDX_CVVH ON #CVVH (PAT_ENC_CSN_ID) 

/*SELECT * FROM #CVVH*/

/*****************************END OF CVVH*****************************/



/*****************************CEREBRAL OX MONITORING*****************************/

IF OBJECT_ID(N'tempdb..#OX') IS NOT NULL DROP TABLE #OX;

SELECT base.PAT_ENC_CSN_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS OX_YN

	, base.[CSN Overall Order]

INTO #OX

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

/* Developer C VCG Grouper 800015*/

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

AND meas.FLO_MEAS_ID IN ('900201', '900202', '900203', '9000001977') /*(SELECT * FROM #CerebralOxFLO)*/

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

GROUP BY base.PAT_ENC_CSN_ID, base.[CSN Overall Order]

CREATE INDEX IDX_OX ON #OX (PAT_ENC_CSN_ID) 

/*SELECT * FROM #OX*/

/*****************************END OF CEREBRAL OX MONITORING*****************************/



/*****************************ECMO*****************************/

IF OBJECT_ID(N'tempdb..#ECMO') IS NOT NULL DROP TABLE #ECMO;

SELECT base.PAT_ENC_CSN_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS ECMO_YN

	, base.[CSN Overall Order]

INTO #ECMO

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

	AND meas.FLO_MEAS_ID ='9000101014' /*9000101014	R ECMO ON/OFF*/

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

GROUP BY base.PAT_ENC_CSN_ID, base.[CSN Overall Order]

CREATE INDEX IDX_ECMO ON #ECMO (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ECMO*/

/*****************************END OF ECMO*****************************/



/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SEPSIS]

	(

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

		[ShiftComplianceYN],

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

		[CSNOrder], 

		[UnitOrder], 

		[CSNOverallOrder],

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

SELECT main.PAT_NAME [PATIENTS]

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

	, CASE WHEN (la.[LAST LacticAcid Order Time] IS NOT NULL OR la.[FIRST LacticAcid Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS LacticAcid_YN

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

	, COALESCE(prophy.PROPHYLAXIS_YN,'N') AS [DVTPROPHYLAXIS Y/N]

	, COALESCE(cvvh.CVVH_YN,'N') AS [CVVH Y/N]

	, COALESCE(ox.OX_YN,'N') AS [OX Y/N]

	, COALESCE(ecmo.ECMO_YN,'N') AS [ECMO Y/N]



	, CASE WHEN IPSO.PAT_ENC_CSN_ID IS NULL THEN 'N' ELSE 'Y' END SEVERE_SEPSIS_STAGING

	

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

	, CAST(bp.PAT_ENC_CSN_ID AS varchar(20)) + '-' + CAST(bp.[CSN Order] AS VARCHAR(95)) [Unique Row]

	, GETDATE()

FROM #MainAdmDetails main  

INNER JOIN #Base_Pop bp ON bp.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

INNER JOIN #Base_Pop_OD_Scores scores ON scores.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND scores.[CSN Overall Order] = bp.[CSN Overall Order]

INNER JOIN reports.FY_DATE_DIMENSION fyDate ON fyDate.CALENDAR_DT = bp.[Score Date] 

LEFT OUTER JOIN #Base_Pop_ENC_Reason encRsn ON encRsn.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

LEFT OUTER JOIN #EncounterWeights wght ON wght.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND wght.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODHYPO hypo ON hypo.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND hypo.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODABX abx ON abx.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND abx.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND abx.InDepartmentTime = scores.InDepartmentTime AND abx.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #OdboL bol ON bol.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND bol.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND bol.InDepartmentTime = scores.InDepartmentTime AND bol.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODLA la ON la.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND la.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND la.InDepartmentTime = scores.InDepartmentTime AND la.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODORDSET ordSet ON ordSet.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND ordSet.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND ordSet.InDepartmentTime = scores.InDepartmentTime AND ordSet.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODCVL cvl ON cvl.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND cvl.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND cvl.InDepartmentTime = scores.InDepartmentTime AND cvl.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODPressorPivot pressor ON pressor.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID

LEFT OUTER JOIN #ODSVO2 svo2 ON svo2.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND svo2.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND svo2.InDepartmentTime = scores.InDepartmentTime AND svo2.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODPROCAL proCal ON proCal.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND proCal.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND proCal.InDepartmentTime = scores.InDepartmentTime AND proCal.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODBC bc ON bc.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND bc.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND bc.InDepartmentTime = scores.InDepartmentTime AND bc.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODCSF csf ON csf.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND csf.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND csf.InDepartmentTime = scores.InDepartmentTime AND csf.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODPIV piv ON piv.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND piv.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND piv.InDepartmentTime = scores.InDepartmentTime AND piv.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ODETT ett ON ett.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND ett.ADT_DEPARTMENT_ID = scores.ADT_DEPARTMENT_ID AND ett.InDepartmentTime = scores.InDepartmentTime AND ett.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #PROPHYLAXIS prophy ON prophy.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND prophy.[CSN Overall Order] = scores.[CSN Overall Order]

LEFT OUTER JOIN #CVVH cvvh ON cvvh.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND cvvh.[CSN Overall Order] = scores.[CSN Overall Order]

LEFT OUTER JOIN #OX ox ON ox.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND ox.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ECMO ecmo ON ecmo.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND ecmo.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #EDPosScore_EDLOS edLOS ON edLOS.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND edLOS.FIRST_TIME_LINE = 1

LEFT OUTER JOIN #FlwshtLstSepsisAudit sepsisAudit ON sepsisAudit.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND sepsisAudit.[CSN Overall Order] = bp.[CSN Overall Order]

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

LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING] IPSO ON IPSO.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

ORDER BY bp.PAT_ENC_CSN_ID, bp.[CSN Overall Order]
GO

-- ==== reporting/USP_IP_SepsisDates.sql ====
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

exec [reportingDB].[reporting].[USP_IP_SepsisDates]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisDates]

AS

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;



DECLARE @dStartDate DATE

DECLARE @dEndDate DATE

	

SET @dStartDate = (SELECT MIN(SepsisPatientDate) FROM reportingDB.reporting.IP_SepsisPatientDates)

SET @dEndDate = ( SELECT MAX(SepsisPatientDate) FROM reportingDB.reporting.IP_SepsisPatientDates)



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
GO

-- ==== reporting/USP_IP_SepsisDetails.sql ====
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

exec [reportingDB].[reporting].[USP_IP_SepsisDetails]

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

	SET @dStartDate = [EMRDB].[dbo].[fn_parse_date]('MB-12') /*('2018-01-01')*/

ELSE

	SET @dStartDate = [EMRDB].[dbo].[fn_parse_date](@StartDate)

	

IF @EndDate IS NULL OR @EndDate = ''

	SET @dEndDate = [EMRDB].[dbo].[fn_parse_date]('ME-1') /*DEFAULTING TO PREVIOUS MONTH*/

ELSE

	SET @dEndDate = [EMRDB].[dbo].[fn_parse_date](@EndDate)





IF OBJECT_ID(N'tempdb..#MARActions') IS NOT NULL DROP TABLE #MARActions;

	SELECT CAST(vcg.LIST_CAT_VALUE_C AS varchar) CAT_ID

	INTO #MARActions

	FROM [EMRDB].[dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800007')

CREATE INDEX IDX_MARActions ON #MARActions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#RouteExclusions') IS NOT NULL DROP TABLE #RouteExclusions;

	SELECT vcg.LIST_CAT_VALUE_C CAT_ID

	INTO #RouteExclusions

	FROM [EMRDB].[dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800008')

	UNION 

	SELECT '11' /*intravenous*/

CREATE INDEX IDX_RouteExclusions ON #RouteExclusions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#BolusMeds') IS NOT NULL DROP TABLE #BolusMeds;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID MED_ID

	INTO #BolusMeds

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'ERX'

	AND vcg.BASE_GROUPER_ID IN ('800009')

CREATE INDEX IDX_BolusMeds ON #BolusMeds (MED_ID) 

	

IF OBJECT_ID(N'tempdb..#MedGroupers') IS NOT NULL DROP TABLE #MedGroupers;

	SELECT vcg.GROUPER_LIST VCG_ID

	INTO #MedGroupers

	FROM [EMRDB].[dbo].[GROUPER_GROUPS] vcg

	WHERE vcg.GROUPER_ID IN ('800011')

CREATE INDEX IDX_MedGroupers ON #MedGroupers (VCG_ID) 



IF OBJECT_ID(N'tempdb..#LacticAcidLRR') IS NOT NULL DROP TABLE #LacticAcidLRR;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID LRR_ID

	INTO #LacticAcidLRR

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'LRR'

	AND vcg.BASE_GROUPER_ID IN ('800012')

CREATE INDEX IDX_Lactic ON #LacticAcidLRR (LRR_ID) 



IF OBJECT_ID(N'tempdb..#BloodCultures') IS NOT NULL DROP TABLE #BloodCultures;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID PROC_ID

	INTO #BloodCultures

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'EAP'

	AND vcg.BASE_GROUPER_ID IN ('800013')

CREATE INDEX IDX_BloodCultures ON #BloodCultures (PROC_ID) 



IF OBJECT_ID(N'tempdb..#CerebralOxFLO') IS NOT NULL DROP TABLE #CerebralOxFLO;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO  #CerebralOxFLO

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800015')

CREATE INDEX IDX_CerebralOxFLO ON #CerebralOxFLO (FLO_ID) 



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

	 PatEncCSNID PAT_ENC_CSN_ID

	, PatID PAT_ID

	, PatMRNID PAT_MRN_ID

	, PatName PAT_NAME

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

FROM [reportingDB].[reporting].[IP_SepsisEncounters]

CREATE INDEX IDX_Main ON #MainAdmDetails (PAT_ENC_CSN_ID)

CREATE INDEX IDX_MainInpID ON #MainAdmDetails (INPATIENT_DATA_ID) 

/*SELECT * FROM #MainAdmDetails*/



/***********************************************************************

Get record for every date the PATIENTS was in a department

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT pd.PatEncCSNID [PAT_ENC_CSN_ID]

	, CAST(pd.InDepartmentTime AS DATE) [In Dept Date]

	, CAST(pd.OutDepartmentTime AS DATE) [Out Dept Date]

	, pd.SepsisPatientDate [Sepsis Pt Date]

	, pd.InDepartmentTime [In_DTTM]

	, pd.OutDepartmentTime [Out_DTTM]

	, pd.ADTDepartmentID [ADT_DEPARTMENT_ID]

	, pd.ADTDepartmentName [ADT_DEPARTMENT_NAME]

	, pd.PatID [PAT_ID]

	, pd.DepartmentRollup [DEPARTMENT_ROLLUP]

	, pd.InpatientDataID [INPATIENT_DATA_ID]

	, pd.[AgeOnDateMonths] [AGE_MONTHS]

	, pd.[AgeOnDateYears] [AGE_YEARS]

	, pd.CSNOrder [CSN Order]

	, pd.CSNOverallOrder [CSN Overall Order]

	, pd.UnitOrder [Unit Order]

	, CAST(pd.PatEncCSNID AS varchar(20)) + '-' + CAST(pd.CSNOrder AS VARCHAR(95)) [Unique Row]

INTO #Base_Pop

FROM [reportingDB].[reporting].[IP_SepsisPatientDates] pd

INNER JOIN [reportingDB].[reporting].[IP_SepsisEncounters] enc ON enc.PatEncCSNID = pd.PatEncCSNID

WHERE pd.SepsisPatientDate BETWEEN @dStartDate AND @dEndDate

CREATE INDEX IDX_Base_Pop ON #Base_Pop (PAT_ENC_CSN_ID) 

CREATE INDEX IDX_Base_PopInpIDOnly ON #Base_Pop (INPATIENT_DATA_ID) 

CREATE INDEX IDX_Base_PopDate ON #Base_Pop ([Sepsis Pt Date]) 

/*SELECT * FROM #Base_Pop*/



IF OBJECT_ID(N'tempdb..#FlwshtLstEncounterWts') IS NOT NULL DROP TABLE #FlwshtLstEncounterWts;

SELECT * , ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY [CSN Order], [Unit Order], RECORDED_TIME) AS [Weight Row]

INTO #FlwshtLstEncounterWts

FROM 

(

	SELECT 

		main.PAT_ENC_CSN_ID

		, meas.FSD_ID

		, meas.MEAS_VALUE

		, dd.CALENDAR_DT [RecordDate]

		, meas.RECORDED_TIME

		, main.[CSN Order]

		, main.[Unit Order]

		, main.[CSN Overall Order]

		, main.[Sepsis Pt Date]

		, main.ADT_DEPARTMENT_ID

		, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID, [CSN Order], [Unit Order] ORDER BY [CSN Order], [Unit Order], RECORDED_TIME) AS [Unit Order Row]

	FROM #Base_Pop main 

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '94'	

		AND meas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM

	INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

		AND dd.CALENDAR_DT = main.[Sepsis Pt Date]

) a

WHERE a.[Unit Order Row] = 1

CREATE INDEX IDX_FloEncWeight ON #FlwshtLstEncounterWts (PAT_ENC_CSN_ID) 

--/*SELECT * FROM #FlwshtLstEncounterWts */



/*OD Score*/

IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT main.PAT_ENC_CSN_ID

	, main.[CSN Order]

	, main.[Unit Order]

	, main.[CSN Overall Order]

	, CASE WHEN a.UniqueRow = main.[Unique Row] THEN 'Yes' ELSE 'No' END [+ OD Score in Dept]

	, main.[Sepsis Pt Date]

INTO #Base_Pop_OD_Scores

FROM #Base_Pop main

OUTER APPLY 

( 

	SELECT Distinct aud.UniqueRow 

	FROM [reportingDB].[reporting].[IP_SepsisScreeningAudit] aud

	WHERE aud.PatEncCSNID = main.PAT_ENC_CSN_ID

	AND aud.PosODScore = 1

	AND aud.UniqueRow = main.[Unique Row]

) a

CREATE INDEX IDX_Base_Pop_OD_Scores ON #Base_Pop_OD_Scores (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Base_Pop_OD_Scores */



/*****************************Hypotension*****************************/

IF OBJECT_ID(N'tempdb..#FlwShtHypo') IS NOT NULL DROP TABLE #FlwShtHypo;

Select

	main.PAT_ENC_CSN_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME [Hypotension Time] 

	, meas.MEAS_VALUE

	, meas.FSD_ID 

	, main.[AGE_MONTHS]

	, main.[AGE_YEARS]

	, main.[CSN Overall Order]

	, bpMeas.MEAS_VALUE [BP Percentile]

	, main.[Sepsis Pt Date]

Into #FlwShtHypo 

FROM #Base_Pop main

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '95' AND meas.MEAS_VALUE IS NOT NULL

	AND meas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM

LEFT JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] bpMeas ON bpMeas.FSD_ID = rec.FSD_ID AND bpMeas.RECORDED_TIME = meas.RECORDED_TIME 

	AND bpMeas.FLO_MEAS_ID in ('9001140203', '9001140205') AND bpMeas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE  ( dd.CALENDAR_DT = main.[Sepsis Pt Date]

	AND meas.RECORDED_TIME BETWEEN main.In_DTTM AND main.Out_DTTM )

CREATE INDEX IDX_FlwShtHypo ON #FlwShtHypo (PAT_ENC_CSN_ID, [CSN Overall Order])

/*SELECT * FROM #FlwShtHypo*/



IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;

SELECT    

	base.PAT_ENC_CSN_ID

	, base.AGE_MONTHS

	, base.AGE_YEARS

	, base.In_DTTM InDepartmentTime    

	, hypo.[Hypotension Value]    

	, meas.[Hypotension Time]    

	, systolic.SYSTOLIC    

	, base.[CSN Order]

	, base.[Unit Order]

	, base.[CSN Overall Order]

	, base.[Sepsis Pt Date]

	, meas.[BP Percentile]

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[CSN Order], base.[Unit Order] ORDER BY base.[CSN Overall Order] ASC) AS TIME_LINE 

INTO #Hypotension 

FROM #Base_Pop base 

INNER JOIN #FlwShtHypo meas ON meas.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID AND meas.[CSN Overall Order] = base.[CSN Overall Order] AND meas.[Sepsis Pt Date] = base.[Sepsis Pt Date]

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

CREATE INDEX IDX_ODHYPO ON #Hypotension (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Hypotension ORDER BY [CSN Order], [CSN Overall Order], TIME_LINE */

/*****************************END OF HYPO*****************************/



/*****************************ABX*****************************/

/*All encounters from #Base_pop where ABX was administered*/

IF OBJECT_ID(N'tempdb..#BasePopABX') IS NOT NULL DROP TABLE #BasePopABX;

SELECT

	om.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, med.NAME

	, mar.TAKEN_TIME AS ABX_ADMIN_TIME

	, mar.SIG AS BOLUS_VOLUME

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

	, ROW_NUMBER() OVER(PARTITION BY om.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY mar.TAKEN_TIME) TIME_LINE

INTO #BasePopABX

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[MEDICATION_ORDERS] om	ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[MEDICATIONS] med ON med.MEDICATION_ID = om.MEDICATION_ID AND med.THERA_CLASS_C = 11 /*Antibiotics*/

INNER JOIN [EMRDB].[dbo].MED_DETAILS_EXT med2 ON med2.MEDICATION_ID = med.MEDICATION_ID /*Developer C Adding to be able to exclude ADMIN_ROUTE_C instead of text*/

INNER JOIN [EMRDB].[dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = om.ORDER_MED_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE) /*Developer C Change to Date to search for action*/

WHERE mar.TAKEN_TIME IS NOT NULL /*ADMINISTERED ABX ONLY*/

AND mar.MAR_ACTION_C IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

/*VALUES BELOW ADDED TO THE CODE ON STEPHANIE'S REQUEST DURING VALIDATION.*/

AND med2.ADMIN_ROUTE_C NOT IN (SELECT * FROM #RouteExclusions)

AND (CAST(mar.TAKEN_TIME AS DATE) = base.[Sepsis Pt Date]

	AND mar.TAKEN_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_BasePopABX ON #BasePopABX (PAT_ENC_CSN_ID) 

/*SELECT * FROM #BasePopABX*/



/*****************************ORDER SET*****************************/

/*All encounters from #Base_pop where Bolus was administered*/

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

SELECT DISTINCT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, om.ORDER_DTTM

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY om.ORDER_DTTM ASC) AS TIME_LINE

	, om.PRL_ORDERSET_ID

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #SSOrderSet 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].ORDER_TRACKING_METRICS om ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(om.ORDER_DTTM AS Date)

WHERE om.PRL_ORDERSET_ID IN (400001) /*(40400100, 40400058, 40400196, 40400153, 4058600002, 400001) Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway*/

AND (CAST(om.ORDER_DTTM AS DATE) = base.[Sepsis Pt Date]

	AND om.ORDER_DTTM between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_SSOrderSet ON #SSOrderSet (PAT_ENC_CSN_ID) 

/*SELECT * FROM #SSOrderSet*/



/*****************************BOLUS*****************************/

IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, mar.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, med.NAME AS Medication

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY mar.TAKEN_TIME ASC) TIME_LINE

	, mar.SIG AS BOLUS_VOLUME

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #BasePopBolus 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[MEDICATION_ORDERS] om ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[MEDICATIONS] med ON med.MEDICATION_ID = om.MEDICATION_ID

INNER JOIN [EMRDB].[dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = om.ORDER_MED_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE)

WHERE mar.TAKEN_TIME IS NOT NULL /*ADMINISTERED BOLUS ONLY*/

/*Developer C VCG Grouper 800009  Added 700004 */

AND (om.MEDICATION_ID IN (SELECT * FROM #BolusMeds)

	OR (om.MEDICATION_ID = 700004)

AND om.HV_DISCR_FREQ_ID = '300902') /*FREQUENCY = ONCE*/

/*Developer C VCG Grouper 1222252*/

AND mar.MAR_ACTION_C IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

AND CONVERT(NUMERIC, mar.SIG ) > 95.0

AND (CAST(mar.TAKEN_TIME AS DATE) = base.[Sepsis Pt Date]

	AND mar.TAKEN_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_BasePopBolus ON #BasePopBolus (PAT_ENC_CSN_ID) 

/*SELECT * FROM #BasePopBolus*/



/*****************************PRESSORS TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;

SELECT DISTINCT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, mar.TAKEN_TIME

	, gmr.GROUPER_ID

	, cm.NAME AS MEDICATION

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY mar.TAKEN_TIME) AS TIME_LINE

	, base.[Sepsis Pt Date]

INTO #Pressors 

FROM #Base_Pop base

LEFT JOIN [EMRDB].[dbo].[MEDICATION_ORDERS] om ON om.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

LEFT JOIN [EMRDB].[dbo].[MEDICATIONS] cm ON cm.MEDICATION_ID = om.MEDICATION_ID

LEFT JOIN [EMRDB].[dbo].GROUPER_MED_RECORDS gmr ON gmr.EXP_MEDS_LIST_ID = cm.MEDICATION_ID

LEFT JOIN [EMRDB].[dbo].[MED_ADMIN_RECORDS] mar ON mar.ORDER_MED_ID = om.ORDER_MED_ID

LEFT JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(mar.TAKEN_TIME AS DATE)

LEFT JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] peh ON peh.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

WHERE

gmr.GROUPER_ID IN (SELECT * FROM #MedGroupers)

AND mar.MAR_ACTION_C IN ( SELECT CAT_ID FROM #MARActions WHERE CAT_ID <> '99')

AND mar.ROUTE_C = 11 /*INTRAVENOUS*/

AND (CAST(mar.TAKEN_TIME AS DATE) = base.[Sepsis Pt Date]

	AND mar.TAKEN_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_Pressors ON #Pressors (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Pressors*/



IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

SELECT p.PAT_ENC_CSN_ID

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

GROUP BY p.PAT_ENC_CSN_ID, p.GROUPER_ID, p.[Sepsis Pt Date]

CREATE INDEX IDX_ODPressorSummary ON #ODPressorSummary (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODPressorSummary*/



IF OBJECT_ID ('TEMPDB..#ODPressorPivot') IS NOT NULL DROP TABLE #ODPressorPivot

SELECT PAT_ENC_CSN_ID

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

CREATE INDEX IDX_ODPressorPivot ON #ODPressorPivot (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ODPressorPivot*/



/*****************************LACTIC ACID TIMES*****************************/

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, op.ORDER_PROC_ID

	, op.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY op.ORDER_TIME, base.IN_DTTM, ordR.RESULT_TIME ASC) AS TIME_LINE -- Developer C added Result time

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #LacticAcid

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] ordR ON ordR.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op ON op.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID IN (SELECT * FROM #LacticAcidLRR)

AND (CAST(op.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND op.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_LacticAcid ON #LacticAcid (PAT_ENC_CSN_ID) 

/*SELECT * FROM #LacticAcid */



/*****************************PROCALCITONIN TIMES*****************************/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, op.ORDER_TIME AS MBOrderTime

	, ordR.RESULT_TIME

	, ordR.COMP_OBS_INST_TM AS CollectionTime

	, ordR.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY op.ORDER_TIME ASC) AS TIME_LINE

	, ordR.ORDER_PROC_ID

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #Procalcitonin

FROM  #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] ordR ON ordR.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op ON op.ORDER_PROC_ID = ordR.ORDER_PROC_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

WHERE ordR.COMPONENT_ID = 500001 /*COULD USE PROC CODE ALSO.... LAB014*/

AND (CAST(op.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND op.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_Procalcitonin ON #Procalcitonin (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Procalcitonin*/



/*****************************BLOOD CULTURE TIMES*****************************/

/*Blood Culture*/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

SELECT base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, op.ORDER_PROC_ID

	, eap.PROC_CODE AS [Blood Culture Procedure Ordered]

	, op.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, CASE WHEN res.ORD_VALUE LIKE '%No growth%' THEN 'Negative' ELSE 'Positive' END [Order Result]

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY op.ORDER_TIME, res.RESULT_TIME ASC) AS TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #BloodCultureValue 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] res ON base.PAT_ENC_CSN_ID = res.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op  ON res.ORDER_PROC_ID = op.ORDER_PROC_ID 

			AND op.PROC_ID IN (SELECT * FROM #BloodCultures)

INNER JOIN [EMRDB].[dbo].[PROCEDURES_CATALOG] eap ON eap.PROC_ID = op.PROC_ID

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

WHERE (CAST(op.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND op.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_BloodCultureValue ON #BloodCultureValue (PAT_ENC_CSN_ID) 

/*SELECT * FROM #BloodCultureValue*/



/*****************************CSF TIMES*****************************/

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

SELECT

	base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, op.ORDER_PROC_ID

	, eap.PROC_CODE as [CSF Procedure Ordered]

	, op.ORDER_TIME AS MBOrderTime

	, res.RESULT_TIME

	, res.COMP_OBS_INST_TM AS CollectionTime

	, res.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY op.ORDER_TIME ASC) AS TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #CSF 

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LAB_ORDER_RESULTS] res ON base.PAT_ENC_CSN_ID = res.PAT_ENC_CSN_ID

INNER JOIN [EMRDB].[dbo].[PROCEDURE_ORDERS] op  ON res.ORDER_PROC_ID = op.ORDER_PROC_ID

			AND PROC_ID IN (600005, 600006) AND op.SPECIMEN_SOURCE_C = 304

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(op.ORDER_TIME AS DATE)

INNER JOIN [EMRDB].[dbo].[PROCEDURES_CATALOG] eap ON eap.PROC_ID = op.PROC_ID

WHERE (CAST(op.ORDER_TIME AS DATE) = base.[Sepsis Pt Date]

	AND op.ORDER_TIME between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_CSF ON #CSF (PAT_ENC_CSN_ID) 

/*SELECT * FROM #CSF*/



/*****************************ETT TIMES*****************************/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

SELECT base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #ETT

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LINE_DEVICE_AIRWAY] lda ON lda.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID AND lda.FLO_MEAS_ID = '900112' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

WHERE (CAST(lda.PLACEMENT_INSTANT AS DATE) = base.[Sepsis Pt Date]

	AND lda.PLACEMENT_INSTANT between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_ETT ON #ETT (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ETT WHERE TIME_LINE = 1*/



/*****************************PIV TIMES*****************************/

IF OBJECT_ID(N'tempdb..#PIV') IS NOT NULL DROP TABLE #PIV;

SELECT base.PAT_ENC_CSN_ID

	, base.ADT_DEPARTMENT_ID

	, base.ADT_DEPARTMENT_NAME

	, base.In_DTTM InDepartmentTime

	, base.Out_DTTM OutDepartmentTime

	, lda.IP_LDA_ID

	, lda.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY base.PAT_ENC_CSN_ID, base.[Sepsis Pt Date] ORDER BY lda.PLACEMENT_INSTANT) TIME_LINE

	, base.[Sepsis Pt Date]

	, base.[CSN Overall Order]

INTO #PIV

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[LINE_DEVICE_AIRWAY] lda ON lda.PAT_ENC_CSN_ID = base.PAT_ENC_CSN_ID AND lda.FLO_MEAS_ID='900111' AND lda.PLACEMENT_INSTANT IS NOT NULL

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(lda.PLACEMENT_INSTANT AS DATE)

WHERE (CAST(lda.PLACEMENT_INSTANT AS DATE) = base.[Sepsis Pt Date]

	AND lda.PLACEMENT_INSTANT between base.In_DTTM AND base.Out_DTTM

	)

CREATE INDEX IDX_PIV ON #PIV (PAT_ENC_CSN_ID) 

/*SELECT * FROM #PIV WHERE TIME_LINE = 1*/



/*****************************CVVH*****************************/

IF OBJECT_ID(N'tempdb..#CVVH') IS NOT NULL DROP TABLE #CVVH;

SELECT base.PAT_ENC_CSN_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS CVVH_YN

	, base.[CSN Overall Order]

	, base.[Sepsis Pt Date]

INTO #CVVH

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID AND meas.FLT_ID='9000001359'--ANY FLOWSHEET FROM THIS TEMPLATE IS A CANDIDATE

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE (dd.CALENDAR_DT = base.[Sepsis Pt Date]

	AND meas.RECORDED_TIME between base.In_DTTM AND base.Out_DTTM

	)

GROUP BY base.PAT_ENC_CSN_ID, base.[CSN Overall Order], base.[Sepsis Pt Date]

CREATE INDEX IDX_CVVH ON #CVVH (PAT_ENC_CSN_ID) 

/*SELECT * FROM #CVVH*/

/*****************************END OF CVVH*****************************/



/*****************************CEREBRAL OX MONITORING*****************************/

IF OBJECT_ID(N'tempdb..#OX') IS NOT NULL DROP TABLE #OX;

SELECT base.PAT_ENC_CSN_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS OX_YN

	, base.[CSN Overall Order]

	, base.[Sepsis Pt Date]

INTO #OX

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

/* Developer C VCG Grouper 800015*/

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

AND meas.FLO_MEAS_ID IN ('900201', '900202', '900203', '9000001977') /*(SELECT * FROM #CerebralOxFLO)*/

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE (dd.CALENDAR_DT = base.[Sepsis Pt Date]

	AND meas.RECORDED_TIME between base.In_DTTM AND base.Out_DTTM

	)

GROUP BY base.PAT_ENC_CSN_ID, base.[CSN Overall Order], base.[Sepsis Pt Date]

CREATE INDEX IDX_OX ON #OX (PAT_ENC_CSN_ID) 

/*SELECT * FROM #OX*/

/*****************************END OF CEREBRAL OX MONITORING*****************************/



/*****************************ECMO*****************************/

IF OBJECT_ID(N'tempdb..#ECMO') IS NOT NULL DROP TABLE #ECMO;

SELECT base.PAT_ENC_CSN_ID

	, CASE WHEN COUNT(meas.RECORDED_TIME) > 0 THEN 'Y' ELSE 'N' END AS ECMO_YN

	, base.[CSN Overall Order]

	, base.[Sepsis Pt Date]

INTO #ECMO

FROM #Base_Pop base

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON rec.INPATIENT_DATA_ID = base.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON meas.FSD_ID = rec.FSD_ID 

	AND meas.FLO_MEAS_ID ='9000101014' /*9000101014	R ECMO ON/OFF*/

INNER JOIN [EMRDB].[dbo].[CALENDAR_DATES] dd ON dd.CALENDAR_DT = CAST(meas.RECORDED_TIME AS DATE)

WHERE (dd.CALENDAR_DT = base.[Sepsis Pt Date]

	AND meas.RECORDED_TIME between base.In_DTTM AND base.Out_DTTM

	)

GROUP BY base.PAT_ENC_CSN_ID, base.[CSN Overall Order], base.[Sepsis Pt Date]

CREATE INDEX IDX_ECMO ON #ECMO (PAT_ENC_CSN_ID) 

/*SELECT * FROM #ECMO*/

/*****************************END OF ECMO*****************************/



----/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisDetails]

	( [PatEncCSNID],

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

	[CSNOrder],

	[UnitOrder],

	[CSNOverallOrder],

	[UniqueRow],

	[RefreshDate]

	)

SELECT main.PAT_ENC_CSN_ID [CSN]

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

	, cvvh.CVVH_YN AS [CVVH Y/N]

	, ox.OX_YN AS [OX Y/N]

	, ecmo.ECMO_YN AS [ECMO Y/N]



	, CASE WHEN IPSO.PAT_ENC_CSN_ID IS NULL THEN 'N' ELSE 'Y' END SEVERE_SEPSIS_STAGING

	, bp.[CSN Order]

	, bp.[Unit Order]

	, bp.[CSN Overall Order]

	, CAST(bp.PAT_ENC_CSN_ID AS varchar(20)) + '-' + CAST(bp.[CSN Order] AS VARCHAR(95)) [Unique Row]

	, GETDATE()

FROM #Base_Pop bp -- reportingDB.reporting.IP_SepsisPatientDates pd

INNER JOIN #MainAdmDetails main ON main.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

INNER JOIN #Base_Pop_OD_Scores scores ON scores.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND scores.[CSN Overall Order] = bp.[CSN Overall Order]

INNER JOIN reports.FY_DATE_DIMENSION fyDate ON fyDate.CALENDAR_DT = bp.[Sepsis Pt Date]

LEFT OUTER JOIN #FlwshtLstEncounterWts wght ON wght.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND wght.[CSN Overall Order] = bp.[CSN Overall Order] AND wght.[Unit Order] = 1

LEFT OUTER JOIN #Hypotension hypo ON hypo.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND hypo.[CSN Overall Order] = bp.[CSN Overall Order] AND hypo.TIME_LINE = 1

LEFT OUTER JOIN #BasePopABX abx ON abx.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND abx.[CSN Overall Order] = bp.[CSN Overall Order] AND abx.TIME_LINE = 1

LEFT OUTER JOIN #BasePopBolus bol ON bol.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND bol.[CSN Overall Order] = bp.[CSN Overall Order] AND bol.TIME_LINE = 1

LEFT OUTER JOIN #LacticAcid la ON la.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND la.[CSN Overall Order] = bp.[CSN Overall Order] AND la.TIME_LINE = 1

LEFT OUTER JOIN #SSOrderSet ordSet ON ordSet.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND ordSet.[CSN Overall Order] = bp.[CSN Overall Order] AND ordSet.TIME_LINE = 1

LEFT OUTER JOIN #ODPressorPivot pressor ON pressor.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND bp.[Sepsis Pt Date] = pressor.Sepsis_Date 

LEFT OUTER JOIN #Procalcitonin proCal ON proCal.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND proCal.[CSN Overall Order] = bp.[CSN Overall Order] AND proCal.TIME_LINE = 1

LEFT OUTER JOIN #BloodCultureValue bc ON bc.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND bc.[CSN Overall Order] = bp.[CSN Overall Order] AND bc.TIME_LINE = 1

LEFT OUTER JOIN #CSF csf ON csf.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND csf.[CSN Overall Order] = bp.[CSN Overall Order] AND csf.TIME_LINE = 1

LEFT OUTER JOIN #PIV piv ON piv.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND piv.[CSN Overall Order] = bp.[CSN Overall Order] AND piv.TIME_LINE = 1

LEFT OUTER JOIN #ETT ett ON ett.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND ett.[CSN Overall Order] = bp.[CSN Overall Order] AND ett.TIME_LINE = 1

LEFT OUTER JOIN #CVVH cvvh ON cvvh.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND cvvh.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #OX ox ON ox.PAT_ENC_CSN_ID = scores.PAT_ENC_CSN_ID AND ox.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN #ECMO ecmo ON ecmo.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND ecmo.[CSN Overall Order] = bp.[CSN Overall Order]

LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING] IPSO ON IPSO.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID



WHERE ( scores.[+ OD Score in Dept] = 'Y'

	OR wght.[Unit Order] = 1

	OR hypo.TIME_LINE = 1

	OR abx.TIME_LINE = 1

	OR bol.TIME_LINE = 1

	OR la.TIME_LINE = 1

	OR ordSet.TIME_LINE = 1

	OR pressor.PAT_ENC_CSN_ID IS NOT NULL

	OR proCal.TIME_LINE = 1

	OR bc.TIME_LINE = 1

	OR csf.TIME_LINE = 1

	OR piv.TIME_LINE = 1

	OR ett.TIME_LINE = 1

	OR cvvh.PAT_ENC_CSN_ID IS NOT NULL

	OR ox.PAT_ENC_CSN_ID IS NOT NULL

	OR ecmo.PAT_ENC_CSN_ID IS NOT NULL

)

ORDER BY bp.PAT_ENC_CSN_ID, bp.[Sepsis Pt Date], bp.[CSN Overall Order]

END
GO

-- ==== reporting/USP_IP_SepsisDetails_v1.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisDetails_v1]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisDetails_v1]

AS 

BEGIN

	

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT

	sd.[PatEncCSNID] [CSN]

	, sd.[SepsisDate] [Sepsis Date]

	, sd.[HypotensionTime] [Hyptension Time]

	, sd.[HypotensionValue] [Hypotension Value]

	, sd.[BPPercentile] [BP Percentile]

	, sd.[EncounterWeight] [Weight]

	, sd.[FirstPositiveScoreInED] [First Positive Score in ED]

	, sd.[FirstPositiveScoreTimeInED] [First Positive Score Time in ED]

	, sd.[EDLosHours] [ED LOS Hours]

	, sd.[PositiveODScore] [Positive OD Score in Department]

	, sd.[ABXVolume] [ABX Volume]

 	, sd.[ABXTime] [ABX Time]

	, sd.[ABXName] [ABX Name]

	, sd.[Bolus] [Bolus]

	, sd.[BolusVolume] [Bolus Volume]

	, sd.[BolusTime] [Bolus Time]

	, sd.[LacticAcidOrderTime] [Lactic Acid Order Time]

	, sd.[LacticAcidResult] [Lactic Acid Result]

	, sd.[OrderSetTime] [Order Set Time]

	, sd.[OrderSetID] [Order Set ID]

	, sd.[ProcalcitoninOrderTime] [Procalcitonin Order Time]

	, sd.[ProcalcitoninResult] [Procalcitonin Result]

	, sd.[BloodCultureOrderTime] [Blood Culture Order Time]

	, sd.[BloodCultureProcedureOrdered] [Blood Culture Procedure Ordered]

	, sd.[BloodCultureResult] [Blood Culture Result]

	, sd.[CSFOrderTime] [CSF Order Time]

	, sd.[CSFOrdered] [CSF Ordered]

	, sd.[CSFValue] [CSF Value]

	, sd.[PIVPlacementTime] [PIV Placement Time]

	, sd.[IntubationTime] [Intubation Time]

	, sd.[DobutamineYN] [Dobutamine Y/N]

	, sd.[DopamineYN] [Dopamine Y/N]

	, sd.[EpinephrineYN] [Epinephrine Y/N]

	, sd.[MilrinoneYN] [Milrinone Y/N]

	, sd.[NorepinephrineYN] [Norepinephrine Y/N]

	, sd.[PressorYN] [Pressor Y/N]

	, sd.[CVVHYN] [CVVH Y/N]

	, sd.[OXYN] [OX Y/N]

	, sd.[ECMOYN] [ECMO Y/N]

	, sd.[IPSOSevereSepsisYN] [IPSO Severe Sepsis Y/N]

	, sd.[CSNOverallOrder] [CSN Overall Order]

	, sd.[RefreshDate] [Refresh Date]

	FROM [reportingDB].[reporting].[IP_SepsisDetails] sd

	ORDER BY sd.PatEncCSNID, sd.CSNOverallOrder

END
GO

-- ==== reporting/USP_IP_SepsisEncounters.sql ====
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
GO

-- ==== reporting/USP_IP_SepsisEncountersDetails.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisEncountersDetails]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisEncountersDetails]

AS

BEGIN



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT DISTINCT

	[PatName] [PATIENTS]

	, [PatID] [Pat ID]

	, [PatMRNID] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location]

	, [PatEncCSNID] [CSN]

	, [AgeMonths] [Age at Admission (M)]

	, [AgeYears] [Age at Admission (Y)]

	, [InpAdmDate] [IP Admit Time]

	, [HospAdmsnTime] [Admit Time]

	, [HospDischTime] [Disch Time]

	, [Disposition] [Disposition]

	, [LosHours] [LOS Hours]

	, [BirthDate] [Birth Date]

	, [AllEncDx] [Encounter DX]

	, [RefreshDate] [Refresh Date]

	FROM [reportingDB].[reporting].[IP_SepsisEncounters] enc

  ORDER BY CSN

END
GO

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
GO

-- ==== reporting/USP_IP_SepsisEncountersWLocations_v1.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisEncountersWLocations_v1]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisEncountersWLocations_v1]

AS

BEGIN

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT DISTINCT

	enc.[PatName] [PATIENTS]

	, enc.[PatMRNID] [MRN]

	, enc.[EthnicGroup] [Ethnic Group]

	, enc.[Race]

	, enc.[Location]

	, enc.[PatEncCSNID] [CSN]

	, enc.[AgeMonths] [Age (M)]

	, enc.[AgeYears] [Age (Y)]

	, enc.[InpAdmDate] [Admit Time]

	, enc.[HospDischTime] [Disch Time]

	, enc.[AllEncDx] [Encounter Diagnosis]

	, loc.[ADTDepartmentName] [Department]

	, loc.[DepartmentRollup] [Department Rollup]

	, loc.[InDepartmentTime] [In Department Time]

	, loc.[OutDepartmentTime][Out Department Time]

	, loc.[CSNOrder] [CSN Order]

	, loc.[UniqueRow] [Unique Row]

	FROM [reportingDB].[reporting].[IP_SepsisEncounters] enc

	INNER JOIN [reportingDB].[reporting].[IP_SepsisEncountersWLocations] loc ON loc.PatEncCSNID = enc.PatEncCSNID

  ORDER BY CSN, CSNOrder

END
GO

-- ==== reporting/USP_IP_SepsisPatientDates.sql ====
/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

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
GO

-- ==== reporting/USP_IP_SepsisPatientDates_v1.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisPatientDates_v1]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_SepsisPatientDates_v1]

AS 

BEGIN

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT

	pd.[PatEncCSNID] [CSN]

	, pd.SepsisPatientDate [PATIENTS Date]

	, pd.DepartmentRollup [Department Roll-up]

	, pd.ADTDepartmentName	[Department Name]

	, pd.ADTDepartmentID [Department ID]

	, pd.InDepartmentTime [In DTTM]

	, pd.OutDepartmentTime [Out DTTM]

	, pd.InpatientDataID [Inp Data ID]

	, pd.CSNOrder [CSN Order]

	, pd.UnitOrder [Unit Order]

	, pd.[CSNOverallOrder] [CSN Overall Order]

	, pd.[RefreshDate] [Refresh Date]

	FROM [reportingDB].[reporting].[IP_SepsisPatientDates] pd

END
GO

-- ==== reporting/USP_IP_SepsisScreeningAudit.sql ====
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

exec [reportingDB].[reporting].[USP_IP_SepsisScreeningAudit]

************************************************************************************/ 

CREATE   PROCEDURE [reporting].[USP_IP_SepsisScreeningAudit]

AS



SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

Truncate Table [reporting].[IP_SepsisScreeningAudit];



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

Finalize base table, one record for each unit a PATIENTS was in

***********************************************************************/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT 	

	[PatEncCSNID] [PAT_ENC_CSN_ID],

	[InDepartmentTime] [In Dept Date],

	[OutDepartmentTime] [Out Dept Date],

	[ADTDepartmentID] [ADT_DEPARTMENT_ID],

	[ADTDepartmentName] [ADT_DEPARTMENT_NAME],

	[PatID] [PAT_ID], 

	[DepartmentRollup] [DEPARTMENT_ROLLUP],

	[InpatientDataID] [INPATIENT_DATA_ID], 

	[CSNOrder] [CSN Order],

	[UniqueRow] [Unique Row]

INTO #Base_Pop

FROM #MainAdmDetails main

INNER JOIN [reporting].[IP_SepsisEncountersWLocations] loc ON loc.PatEncCSNID = main.PAT_ENC_CSN_ID

CREATE INDEX IDX_Base_Pop ON #Base_Pop (PAT_ENC_CSN_ID) 

CREATE INDEX IDX_Base_Pop_Inp ON #Base_Pop (INPATIENT_DATA_ID) 

/*SELECT * FROM #Base_Pop*/



/*OD Score*/

IF OBJECT_ID(N'tempdb..#FlwshtLst') IS NOT NULL DROP TABLE #FlwshtLst;

	SELECT main.PAT_ENC_CSN_ID

		, meas.FLO_MEAS_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE

		, meas.FSD_ID

		, main.[In Dept Date] [IN_DTTM]

		, main.[Out Dept Date] [OUT_DTTM]

		, main.ADT_DEPARTMENT_ID [Documented Department ID]

		, main.ADT_DEPARTMENT_NAME [Documented Department]

		, CAST(meas.RECORDED_TIME AS DATE) AS [Score Date]

		, main.[CSN Order]

		, ROW_NUMBER() OVER(PARTITION BY main.PAT_ENC_CSN_ID ORDER BY main.[CSN Order], RECORDED_TIME) AS [CSN Overall Score Order]

		, main.[Unique Row]

	INTO #FlwshtLst

	FROM #Base_Pop main

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID IN (SELECT * FROM #ODScores)

	WHERE meas.RECORDED_TIME BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

CREATE INDEX IDX_FlwshtLst ON #FlwshtLst (PAT_ENC_CSN_ID) 

CREATE INDEX IDX_FlwshtLstFSD ON #FlwshtLst (FSD_ID) 

/*SELECT * FROM #FlwshtLst WHERE PAT_ENC_CSN_ID = '1060789013' ORDER BY PAT_ENC_CSN_ID, RECORDED_TIME*/



/*****************************OD Huddle Flowsheet rows*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtLstHuddleODScore') IS NOT NULL DROP TABLE #FlwshtLstHuddleODScore;

SELECT main.PAT_ENC_CSN_ID

	, meas.FSD_ID

	, meas.FLO_MEAS_ID

	, meas.RECORDED_TIME

	, meas.MEAS_VALUE

	, flo.[CSN Overall Score Order]

	, main.[Unique Row]

INTO #FlwshtLstHuddleODScore

FROM #Base_Pop main

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000002705','9000002732','9000002733','9000002706','9000002734','9000002707')

	AND meas.MEAS_VALUE IS NOT NULL

OUTER APPLY 

(

	SELECT MAX(flo.[CSN Overall Score Order]) [CSN Overall Score Order]

	FROM #FlwshtLst flo 

	WHERE  flo.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID 

	AND flo.RECORDED_TIME <= meas.RECORDED_TIME

) flo

WHERE meas.RECORDED_TIME BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

ORDER BY main.PAT_ENC_CSN_ID, meas.RECORDED_TIME

CREATE INDEX IDX_FlwshtLstHuddleODScore ON #FlwshtLstHuddleODScore (PAT_ENC_CSN_ID, FSD_ID) 

/*SELECT * FROM #FlwshtLstHuddleODScore ORDER BY PAT_ENC_CSN_ID, RECORDED_TIME*/



/*****************************Flowsheet row for CLINICAL_ALERTS not activated*****************************/

IF OBJECT_ID(N'tempdb..#FlwshtNoAlert') IS NOT NULL DROP TABLE #FlwshtNoAlert;

SELECT a.PAT_ENC_CSN_ID

	, MAX(a.RECORDED_TIME) RECORDED_TIME

	, STRING_AGG([CLINICAL_ALERTS Not Activated Reason],  ' % ') [CLINICAL_ALERTS Not Activated Reason]

	, STRING_AGG([CLINICAL_ALERTS Not Activated Comment],  ' % ') [CLINICAL_ALERTS Not Activated Comment]

	, a.[CSN Overall Score Order]

INTO #FlwshtNoAlert

FROM (

	SELECT main.PAT_ENC_CSN_ID

		, rec.INPATIENT_DATA_ID

		, meas.FSD_ID

		, meas.RECORDED_TIME

		, meas.MEAS_VALUE AS [CLINICAL_ALERTS Not Activated Reason]

		, meas.MEAS_COMMENT as [CLINICAL_ALERTS Not Activated Comment]

		, flo.[CSN Overall Score Order]

	FROM #Base_Pop main

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_RECORDS] rec ON main.INPATIENT_DATA_ID = rec.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON rec.FSD_ID = meas.FSD_ID AND meas.FLO_MEAS_ID = '9000003159'

	OUTER APPLY 

	(

		SELECT MAX(flo.[CSN Overall Score Order]) [CSN Overall Score Order]

		FROM #FlwshtLst flo 

		WHERE  flo.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID 

		AND flo.RECORDED_TIME <= meas.RECORDED_TIME

	) flo

	WHERE meas.RECORDED_TIME BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

) a

GROUP BY a.PAT_ENC_CSN_ID, a.[CSN Overall Score Order]

CREATE INDEX IDX_FlwshtNoAlert ON #FlwshtNoAlert (PAT_ENC_CSN_ID, [CSN Overall Score Order]) 

/*SELECT * FROM #FlwshtNoAlert*/



IF OBJECT_ID(N'tempdb..#FlwshtAlert') IS NOT NULL DROP TABLE #FlwshtAlert;

SELECT a.PAT_ENC_CSN_ID

	, a.ALT_ID

	, a.ALT_ACTION_INST

	, a.[CLINICAL_ALERTS Activated Comment]

	, a.[CSN Overall Score Order]

	, a.[OPA TYPE]

INTO #FlwshtAlert

FROM (

	SELECT main.PAT_ENC_CSN_ID

		, alt.ALT_ID

		, his.ALT_ACTION_INST

		, COALESCE(his.SPEC_OVR_CMNT,' ')+ rsn.[NAME] [CLINICAL_ALERTS Activated Comment]

		, alt.BPA_LOCATOR_ID 

		, flo.[CSN Overall Score Order]

		, CASE WHEN alt.BPA_LOCATOR_ID = 900400001 THEN 'Non-PICU' ELSE 'PICU' END [OPA TYPE]

		, ROW_NUMBER() OVER(PARTITION BY main.PAT_ENC_CSN_ID, flo.[CSN Overall Score Order] ORDER BY flo.[CSN Overall Score Order]) RowNum

	FROM #Base_Pop main

	INNER JOIN [EMRDB].[dbo].[CLINICAL_ALERTS] alt ON alt.PAT_CSN = main.PAT_ENC_CSN_ID AND alt.BPA_LOCATOR_ID in (900400001, 900400011) /*BASE 2019 HS OD SCORE SEPSIS >2 [900400001]*/

	INNER JOIN [EMRDB].[dbo].[ALERT_HISTORY] his ON his.ALT_ID = alt.ALT_ID

	INNER JOIN [EMRDB].[dbo].[REF_ALERT_OVERRIDE_REASONS] rsn ON rsn.ALRT_SP_OVR_RSN_C = his.SPEC_OVR_RSN_C

	OUTER APPLY 

	(

		SELECT MAX(flo.[CSN Overall Score Order]) [CSN Overall Score Order]

		FROM #FlwshtLst flo 

		WHERE  flo.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID 

		AND flo.RECORDED_TIME <= his.ALT_ACTION_INST

	) flo

	WHERE his.ALT_ACTION_INST BETWEEN main.[In Dept Date] AND main.[Out Dept Date]

) a

WHERE a.RowNum = 1

CREATE INDEX IDX_FlwshtAlert ON #FlwshtAlert (PAT_ENC_CSN_ID) 

/*SELECT * FROM #FlwshtAlert*/



IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT bp.PAT_ENC_CSN_ID

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

	, meas.[CSN Overall Score Order]

	, meas.[CSN Order]

	, CASE WHEN meas.MEAS_VALUE >= 2 THEN 'Y' ELSE 'N' END [ShowComponents]

	, meas.FSD_ID

	, meas.[Unique Row]

INTO #Base_Pop_OD_Scores

FROM #Base_Pop bp 

INNER JOIN [EMRDB].[dbo].[HOSPITAL_ENCOUNTERS] peh ON peh.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

LEFT OUTER JOIN #FlwshtLst meas ON meas.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID AND meas.[CSN Order] = bp.[CSN Order]

LEFT OUTER JOIN #FlwshtNoAlert alertNotActivated on 

	(	

		alertNotActivated.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID 

		AND alertNotActivated.[CSN Overall Score Order] = meas.[CSN Overall Score Order]

	)

LEFT OUTER JOIN #FlwshtAlert alertActivated on 

	(	

		alertActivated.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID 

		AND alertActivated.[CSN Overall Score Order] = meas.[CSN Overall Score Order]

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

CREATE INDEX IDX_Base_Pop_OD_Scores ON #Base_Pop_OD_Scores (PAT_ENC_CSN_ID) 

/*SELECT * FROM #Base_Pop_OD_Scores WHERE [OD Score] > 2 */



IF OBJECT_ID(N'tempdb..#SepsisAuditTemp') IS NOT NULL DROP TABLE #SepsisAuditTemp;

SELECT od.PAT_ENC_CSN_ID, od.[CSN Overall Score Order], od.[OD Score Time], meas.FLO_MEAS_ID, meas.MEAS_VALUE, meas.RECORDED_TIME

	, DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME) [Time since OD Score]

	, ABS(DATEDIFF(n, od.[OD Score Time], meas.RECORDED_TIME)) [ABS Time since OD Score]

	, od.[Score Day]

INTO #SepsisAuditTemp

FROM #Base_Pop_OD_Scores od

INNER JOIN [EMRDB].[dbo].[FLOWSHEET_MEASUREMENTS] meas ON od.FSD_ID = meas.FSD_ID 

	AND meas.FLO_MEAS_ID in ('9000161701', '9000161702', '9000161710', '9000161708', '9000161704', '9000002611'

			, '98', '99', '95', '9000800500', '900101', '900103', '900102', '900104', '900105', '900107', '900106'

			, '900108', '9000002702', '900109', '900110', '9000311801', '9000311802', '9000311803', '9000003157'

			, '9001140203', '9001140205', '9000012611')

WHERE meas.RECORDED_TIME BETWEEN od.[In Dept Date] AND od.[Out Dept Date]

AND od.ShowComponents = 'Y'

AND DATEDIFF(MINUTE, od.[OD Score Time], meas.RECORDED_TIME) BETWEEN -60 AND 180 /*WAS -120 UNTIL 03.01.2021 */



IF OBJECT_ID(N'tempdb..#FlwshtLstSepsisAudit') IS NOT NULL DROP TABLE #FlwshtLstSepsisAudit;

SELECT bp.PAT_ENC_CSN_ID

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

	, bp.[CSN Overall Score Order]

	, bp.[Unique Row]

INTO #FlwshtLstSepsisAudit

FROM #FlwshtLst bp 

OUTER APPLY 

(

	SELECT bp.PAT_ENC_CSN_ID

		, bp.[CSN Overall Score Order]

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

			subMeas.PAT_ENC_CSN_ID

			, subMeas.FLO_MEAS_ID

			, subMeas.RECORDED_TIME

			, subMeas.MEAS_VALUE

			, ROW_NUMBER() OVER (PARTITION BY subMeas.PAT_ENC_CSN_ID, subMeas.[CSN Overall Score Order], subMeas.FLO_MEAS_ID ORDER BY subMeas.[ABS Time since OD Score]) rownumber

			, subMeas.[CSN Overall Score Order]

			, subMeas.[ABS Time since OD Score]

		FROM #SepsisAuditTemp subMeas

		WHERE subMeas.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

		AND subMeas.[CSN Overall Score Order] = bp.[CSN Overall Score Order]

		AND subMeas.MEAS_VALUE IS NOT NULL

	) a

	WHERE a.rownumber = 1

	GROUP BY PAT_ENC_CSN_ID, [CSN Overall Score Order]

) sepsisAudit



--SELECT * FROM #FlwshtLstSepsisAudit WHERE [Circulatory Dysfunction] IS NOT NULL

--/*****************************Clean up tables*****************************/

--IF OBJECT_ID(N'tempdb..#FlwshtLstHuddleODScore') IS NOT NULL DROP TABLE #FlwshtLstHuddleODScore;





/*****************************FINAL RESULT*****************************/

INSERT INTO [reporting].[IP_SepsisScreeningAudit]

	(

		[PatEncCSNID],

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

	main.PAT_ENC_CSN_ID [CSN]

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

INNER JOIN #Base_Pop bp ON bp.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID

INNER JOIN #Base_Pop_OD_Scores scores ON scores.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND scores.[CSN Order] = bp.[CSN Order]

INNER JOIN reports.FY_DATE_DIMENSION fyDate ON fyDate.CALENDAR_DT = scores.[Score Day]

LEFT OUTER JOIN #FlwshtLstSepsisAudit sepsisAudit ON sepsisAudit.PAT_ENC_CSN_ID = main.PAT_ENC_CSN_ID AND sepsisAudit.[CSN Overall Score Order] = scores.[CSN Overall Score Order]

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

ORDER BY main.PAT_ENC_CSN_ID, scores.[CSN Overall Score Order]
GO

-- ==== reporting/USP_IP_SepsisScreeningAudit_v1.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023		Developer C		Developed TKT-006

07/24/2025		Developer C		Removed restrictionof ODScore >= 2, Stakeholder A wants them all to display TKT-008

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisScreeningAudit_v1]

************************************************************************************/

CREATE       PROCEDURE [reporting].[USP_IP_SepsisScreeningAudit_v1]



AS



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT 

	[PatEncCSNID] [CSN],

	[ScoreDate] [Score Date],

	[ODScore] [OD Score],

	[ScoreTime] [OD Score Time],

	[SepsisPatientHuddleorAlertWithMDPNP] [Sepsis PATIENTS Huddle or CLINICAL_ALERTS With MD/PNP],

	[HuddleDate] [Huddle Date],

	[HuddleTime] [Huddle Time],

	[PatientAssessedByMDPNP] [PATIENTS Assessed by MD/PNP],

	[PhysicianName] [Physician Name],

	[AddOrdersReceivedPlacedByMDPNP] [Additional Orders Received/Placed by MD/PNP],

	[AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason],

	[AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment],

	[AlertActivatedComment] [CLINICAL_ALERTS Activated Comment],

	[Predisposition] [Predisposition?],

	[InfectiousSymptoms] [Infectious Symptoms?],

	[HematologicDysfunction] [Hematologic Dysfunction],

	[RenalDysfunction] [Renal Dysfunction],

	[NeurologicalDysfunction] [Neurological Dysfunction],

	[RespiratoryDysfunction] [Respiratory Dysfunction],

	[CirculatoryDysfunction] [Circulatory Dysfunction],

	[Pulse],

	[Resp],

	[BP],

	[BPGirlsPercentile] [BP Girls Percentile],

	[BPBoysPercentile] [BP Boys Percentile],

	[PerfusionWDL] [Perfusion (WDL)],

	[RBrachialPulse] [R Brachial Pulse],

	[LBrachialPulse] [L Brachial Pulse],

	[RRadialPulse] [R Radial Pulse],

	[LRadialPulse] [L Radial Pulse],

	[RPosteriorTibialPulse] [R Posterior Tibial Pulse],

	[LPosteriorTibialPulse] [L Posterior Tibial Pulse],

	[RPedalPulse] [R Pedal Pulse],

	[LPedalPulse] [L Pedal Pulse],

	[CapillaryRefill] [Capillary Refill],

	[SkinColor] [Skin Color],



	[SkinConditionTemp] [Skin Condition/Temp],

	[ExternalLactateResult] [External Lactate Result],

	[ExternalCreatinine] [External Creatinine],

	[ExternalPlatelets] [External Platelets],

	[Notification],

	[ODScoreIs2] [OD Score 2],

	[PosODScore] [+ OD Score],

	CASE WHEN [ODScoreIs2] = 1 THEN 'Yes' ELSE 'No' END [OD Score = 2?],

	CASE WHEN [PosODScore] = 1 THEN 'Yes' ELSE 'No' END  [+ OD Score?],

	[NoteAuthor] [Note Author],

	[NoteCreatedTime] [Note Created Time],

	[FifteenthOrEOM] [15th or EOM],

	[ShiftColorDisplay] [Shift Color Display],

	[UniqueRow] [Unique Row],

	[RefreshDate] [Refresh Date]

	, CASE WHEN [ODScore] IS NOT NULL THEN 1 ELSE 0 END [Screened]

	FROM [reportingDB].[reporting].[IP_SepsisScreeningAudit]
GO

-- ==== reporting/USP_IP_SepsisShiftCompliance.sql ====
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
GO

-- ==== reporting/USP_IP_SepsisShiftComplianceByShift.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisShiftComplianceByShift]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_SepsisShiftComplianceByShift]

AS

BEGIN 



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT 

	[PatEncCSNID] [CSN]

	, [ShiftDate] [Shift Date]

	, [ShiftStart] [Shift Start]

	, [ShiftEnd] [Shift End]

	, [ShiftAMPM] [Shift AM/PM]

	, [ScoreTime] [Shift Score Time]

	, [ODScore] [Shift Score]

	  

	, [FY] [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYDate] [FY Date]

	, [ShiftRNs] [Shift RNs]

	, [ShiftCNs] [Shift CNs]

	, [ShiftCompliance] [Shift Numerator]

	  

	, [Shift1ComplianceYN] [Shift 1 Compliance Y/N]

	, [Shift1Compliance] [Shift 1 Compliance]

	, [Shift1Color] [Shift 1 Color]

	, [Shift1NonCompliance] [Shift 1 Non-Compliance]



	, [Shift2ComplianceYN] [Shift 2 Compliance Y/N]

	, [Shift2Compliance] [Shift 2 Compliance]

	, [Shift2Color] [Shift 2 Color]

	, [Shift2NonCompliance] [Shift 2 Non-Compliance]



	, [ShiftCompliance] [Numerator]

	, CASE WHEN [ShiftAMPM] like 'AM%' THEN [AMDenom] ELSE [PMDenom] END [Denominator]

	, [ShiftComplianceYN] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [ShiftNonCompliance] [Shift Non-Compliance]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

	FROM [reportingDB].reporting.[IP_SepsisShiftCompliance]

  ORDER BY CSN, CSNOverallOrder

END
GO

-- ==== reporting/USP_IP_SepsisShiftComplianceMetrics.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisShifComplianceMetrics_PBI]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisShiftComplianceMetrics]

AS

BEGIN

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT [PatEncCSNID] [CSN]

	, [ShiftDate] [Shift Date]

	, [ShiftAMPM] [Shift AM/PM]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]

	, [FY] [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYMonthShortName] [FY Month Abrv]

	, [FYDate] [FY Date]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [Denominator]

	, [ShiftCompliance] [Numerator]

	, [FifteenthOrEOM] [15th or EOM]

	, [ShiftComplianceYN] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [ShiftColorDisplay] [Shift Color Display]

	, [ShiftCompliance] [Shift Non-Compliance]

	, [PositiveODScore] [Positive OD Score]

	, [UniqueRow] [Unique Row]

	,[RefreshDate]

FROM [reportingDB].reporting.[IP_SepsisShiftCompliance]

ORDER BY CSN, CSNOverallOrder

END
GO

-- ==== reporting/USP_IP_Sepsis_ComplianceByShift.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_Sepsis_ComplianceByShift]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_ComplianceByShift]



AS

	

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT [PatName] [PATIENTS]

	, [PatMRNID] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location]

	, [PatEncCSNID] [CSN]

	, [AgeMonths] [Age (M)]

	, [AgeYears] [Age (Y)]

	, [InpAdmDate] [Admit Time]

	, [HospDischTime] [Disch Time]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [In Department Time]

	, [OutDepartmentTime][Out Department Time]

	, [ShiftDate] [Shift Date]

	, [ShiftStart] [Shift Start]

	, [ShiftEnd] [Shift End]

	, [ShiftAMPM] [Shift AM/PM]

	, [ScoreTime] [Shift Score Time]

	, [ODScore] [Shift Score]

	  

	, [FY] [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYDate] [FY Date]

	, [ShiftRNs] [Shift RNs]

	, [ShiftCNs] [Shift CNs]

	, [ShiftCompliance] [Shift Numerator]

	  

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN [ShiftComplianceYN] ELSE NULL END [Shift 1 Compliance Y/N]

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN [ShiftCompliance] ELSE NULL END [Shift 1 Compliance]

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN [ShiftColor] ELSE NULL END [Shift 1 Color]

	, CASE WHEN [ShiftAMPM] = 'AM (Day Shift)' THEN

		CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END

	ELSE NULL 

	END [Shift 1 Non-Compliance]



	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN [ShiftComplianceYN] ELSE NULL END [Shift 2 Compliance Y/N]

	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN [ShiftCompliance] ELSE NULL END [Shift 2 Compliance]

	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN [ShiftColor] ELSE NULL END [Shift 2 Color]

	, CASE WHEN [ShiftAMPM] = 'PM (Night Shift)' THEN

		CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END

	ELSE NULL 

	END [Shift 2 Non-Compliance]



	, [ShiftCompliance] [Numerator]

	, CASE WHEN [ShiftAMPM] like 'AM%' THEN [AMDenom] ELSE [PMDenom] END [Denominator]

	, [ShiftComplianceYN] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END [Shift Non-Compliance]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

	FROM [reportingDB].[reporting].[IP_SEPSIS]



  ORDER BY CSN, CSNOverallOrder
GO

-- ==== reporting/USP_IP_Sepsis_ComplianceMetrics.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_Sepsis_ComplianceMetrics]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_ComplianceMetrics]



AS

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT [PatName] [PATIENTS]

	, [PatMRNID] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location]

	, [PatEncCSNID] [CSN]

	, [AgeMonths] [Age (M)]

	, [AgeYears] [Age (Y)]

	, [InpAdmDate] [IP Admit Time]

	, [HospDischTime] [Discharge Time]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [Department In Time]

	, [OutDepartmentTime] [Department Out Time]

	, [ShiftDate] [Shift Date]

	, [ShiftAMPM] [Shift AM/PM]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]

	, [FY] [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYMonthShortName] [FY Month Abrv]

	, [FYDate] [FY Date]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [Denominator]

	, [ShiftCompliance] [Numerator]

	, [FifteenthOrEOM] [15th or EOM]

	, [ShiftComplianceYN] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [ShiftColorDisplay] [Shift Color Display]

	, CASE WHEN [ShiftCompliance] = 1 THEN 0 ELSE 1 END [Shift Non-Compliance]

	, [PositiveODScore] [Positive OD Score]

	, [UniqueRow] [Unique Row]

	,[RefreshDate]

FROM [reportingDB].[reporting].[IP_SEPSIS]

ORDER BY CSN, CSNOverallOrder
GO

-- ==== reporting/USP_IP_Sepsis_Details.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_Sepsis_Details]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_Details]



AS	

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT [PatName] [PATIENTS]

	, [PatMRNID] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location] 

	, [PatEncCSNID] [CSN]

	, [AgeMonths] [Age (M)]

	, [AgeYears] [Age (Y)]

	, [InpAdmDate] [Admit Time]

	, [HospDischTime] [Disch Time]

	, [Disposition]

	, [LosHours] [LOS (Hrs)]

	, [ShiftDate] [Shift Date]

	, [ShiftAMPM] [Shift AM/PM]

	, [ShiftStart] [Shift Start]

	, [ShiftEnd] [Shift End]

	, [EncounterDiagnoses] [Encounter Diagnoses]

	, [LastHypotensionTime] [LAST Hypotension Time]

	, [LastHypotensionValue] [LAST Hypotension Value]

	, [LastHypotensionTakenInDeptYN] [LAST Hypotension Taken in Dept Y/N]

	, [FirstHypotensionTime] [FIRST Hypotension Time]

	, [FirstHypotensionValue] [FIRST Hypotension Value]

	, [FirstHypotensionTakenInDeptYN] [FIRST Hypotension Taken in Dept Y/N]

	, [EncounterWeight] [Weight]

	, [FirstPositiveScoreInED] [First Positive Score in ED]

	, [FirstPositiveScoreTimeInED] [First Positive Score Time in ED]

	, [EDLosHours] [ED LOS (Hrs)]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [In Department Time]

	, [OutDepartmentTime] [Out Department Time]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]

	, [ShiftComplianceYN] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [SepsisPatientHuddleorAlertWithMDPNP] [Sepsis PATIENTS Huddle or CLINICAL_ALERTS With MD/PNP]

	, [HuddleDate] [Huddle Date]

	, [HuddleTime] [Huddle Time]

	, [PatientAssessedByMDPNP] [PATIENTS Assessed by MD/PNP]

	, [PhysicianName] [Physician Name]

	, [AddOrdersReceivedPlacedByMDPNP] [Additional Orders Received/Placed by MD/PNP]

	, [LastABXTime] [LAST ABX Time]

	, [LastABXName] [LAST ABX Name]

	, [LastABXToODScoreVolume] [LAST ABX Volume]

	, [LastABXToODScoreTime] [LAST ABX to OD Score Time]

	, [LastABXGivenInDeptYN] [LAST ABX Given in Dept Y/N]

	, [FirstABXTime] [FIRST ABX Time]

	, [FirstABXName] [FIRST ABX Name]

	, [FirstABXVolume] [FIRST ABX Volume]

	, [ODScoreToFirstABXTime] [OD Score to FIRST ABX Time]

	, [FirstABXGivenInDeptYN] [FIRST ABX Given in Dept Y/N]

	, [ABXYN] [ABX Y/N]

	, [LastBolusTime] [LAST Bolus Time]

	, [LastBolus] [LAST Bolus]

	, [LastBolusVolume][LAST Bolus Volume]

	, [LastBolusToScreenTime] [LAST Bolus to Screen Time]

	, [LastBolusGivenInDeptYN] [LAST Bolus Given in Dept Y/N]

	, [FirstBolusTime] [FIRST Bolus Time]

	, [FirstBolus] [FIRST Bolus]

	, [FirstBolusVolume] [FIRST Bolus Volume]

	, [ScreenTimeToFirstBolus] [Screen Time to FIRST Bolus]

	, [FirstBolusGivenInDeptYN] [FIRST Bolus Given in Dept Y/N]

	, [BolusYN] [Bolus Y/N]

	, [LastLacticAcidOrderTime] [LAST LacticAcid Order Time]

	, [LastLacticAcidResult] [LAST LacticAcid Result]

	, [LastLacticAcidInDeptYN] [LAST LacticAcid in Dept Y/N]

	, [FirstLacticAcidOrderTime] [FIRST LacticAcid Order Time]

	, [FirstLacticAcidResult] [FIRST LacticAcid Result]

	, [FirstLacticActidInDeptYN][FIRST LacticAcid in Dept Y/N]

	, [LacticAcidYN] [LacticAcid Y/N]

	, [LastOrderSetTime] [LAST OrderSet Time]

	, [LastOrderSetID] [LAST OrderSet ID]

	, [LastOrderSetInDeptYN] [LAST OrderSet in Dept Y/N]

	, [FirstOrderSetTime] [FIRST OrderSet Time]

	, [FirstOrderSetID] [FIRST OrderSet ID]

	, [FirstOrderSetInDeptYN] [FIRST OrderSet in Dept Y/N]

	, [LastCVLTime] [LAST CVL Time]

	, [LastCVLInDeptYN] [LAST CVL in Dept Y/N]

	, [FirstCVLTime] [FIRST CVL Time]

	, [FirstCVLInDeptYN] [FIRST CVL in Dept Y/N]

	, [CVLYN] [CVL Y/N]

	, [LastSVO2Time] [LAST SVO2 Time]

	, [LastSVO2InDeptYN] [LAST SVO2 in Dept Y/N]

	, [FirstSVO2Time] [FIRST SVO2 Time]

	, [FirstSVO2InDeptYN] [FIRST SVO2 in Dept Y/N]

	, [SVO2YN] [SVO2 Y/N]

	, [LastProcalcitoninOrderTime] [LAST Procalcitonin Order Time]

	, [LastProcalcitoninResult] [LAST Procalcitonin Result]

	, [LastProcalcitoninInDeptYN] [LAST Procalcitonin in Dept Y/N]

	, [FirstProcalcitoninOrderTime] [FIRST Procalcitonin Order Time]

	, [FirstProcalcitoninResult] [FIRST Procalcitonin Result]

	, [FirstProcalcitoninInDeptYN] [FIRST Procalcitonin in Dept Y/N]

	, [ProcalcitoninYN] [Procalcitonin Y/N]

	, [LastBloodCultureOrderTime] [LAST Blood Culture Order Time]

	, [LastBloodCultureProcedureOrdered] [LAST Blood Culture Procedure Ordered]

	, [LastBloodCultureResult] [LAST Blood Culture Result]

	, [LastBloodCultureInDeptYN] [LAST Blood Culture in Dept Y/N]

	, [FirstBloodCultureOrderTime] [FIRST Blood Culture Order Time]

	, [FirstBloodCultureProcedureOrdered] [FIRST Blood Culture Procedure Ordered]

	, [FirstBloodCultureResult] [FIRST Blood Culture Result]

	, [FirstBloodCultureInDeptYN] [FIRST Blood Culture in Dept Y/N]

	, [BloodCultureYN] [Blood Culture Y/N]

	, [LastCSFOrderTime] [LAST CSF Order Time]

	, [LastCSFOrdered] [LAST CSF Ordered]

	, [LastCSFInDeptYN] [LAST CSF in Dept Y/N]

	, [FirstCSFOrderTime] [FIRST CSF Order Time]

	, [FirstCSFOrdered] [FIRST CSF Ordered]

	, [FirstCSFInDeptYN] [FIRST CSF in Dept Y/N]

	, [CSFYN] [CSF Y/N]

	, [LastPIVBeforeScreen] [LAST PIV Before Screen]

	, [LastPIVInDeptYN] [LAST PIV in Dept Y/N]

	, [FirstPIVAfterScreen] [FIRST PIV After Screen]

	, [FirstPIVInDeptYN] [FIRST PIV in Dept Y/N]

	, [PIVYN] [PIV Y/N]

	, [LastIntubationTime] [LAST Intubation Time]

	, [LastETTInDeptYN] [LAST ETT in Dept Y/N]

	, [FirstIntubationTime] [FIRST Intubation Time]

	, [FirstETTInDeptYN] [FIRST ETT in Dept Y/N]

	, [ETTYN] [ETT Y/N]

	, [DobutamineYN] [Dobutamine Y/N]

	, [DopamineYN] [Dopamine Y/N]

	, [EpinephrineYN] [Epinephrine Y/N]

	, [MilrinoneYN] [Milrinone Y/N]

	, [NorepinephrineYN] [Norepinephrine Y/N]

	, [PressorYN] [Pressor Y/N]

	, [DvtprophylaxisYN] [Dvtprophylaxis Y/N]

	, [CVVHYN] [CVVH Y/N]

	, [OXYN] [OX Y/N]

	, [ECMOYN] [ECMO Y/N]

	, [IPSOSevereSepsisYN] [IPSO Severe Sepsis Y/N]

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]

	, [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYMonthShortName] [FY Month Short Name]

	, [FYDate] [FY Date]

	, [ShiftRNs] [Shift RNs]

	, [ShiftCNs] [Shift CNs]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [FifteenthOrEOM] [15th or EOM]

	, [PositiveODScore] [Positive OD Score]

	, [CSNOrder] [CSN Order]

	, [UnitOrder] [Unit Order]

	, [CSNOverallOrder] [CSN Overall Order]

	, [AMDenom] [AM Denom]

	, [PMDenom] [PM Denom]

	, [Denominator]

	, [InRecord] [In Record]

	, [OutRecord] [Out Record]

	, [RefreshDate] [Refresh Date]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

  FROM [reportingDB].[reporting].[IP_SEPSIS]
GO

-- ==== reporting/USP_IP_Sepsis_Encounters.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_Sepsis_Encounters]

************************************************************************************/

CREATE   PROCEDURE [reporting].[USP_IP_Sepsis_Encounters]



AS

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT DISTINCT

	[PatName] [PATIENTS]

	, [PatMRNID] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location]

	, [PatEncCSNID] [CSN]

	, [AgeMonths] [Age (M)]

	, [AgeYears] [Age (Y)]

	, [InpAdmDate] [Admit Time]

	, [HospDischTime] [Disch Time]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [In Department Time]

	, [OutDepartmentTime][Out Department Time]

	, [CSNOrder] [CSN Order]

	, [UniqueRow] [Unique Row]

	FROM [reportingDB].[reporting].[IP_SEPSIS]

  ORDER BY CSN, CSNOrder
GO

-- ==== reporting/USP_IP_Sepsis_ScreeningTool.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023		Developer C		Developed TKT-006

07/24/2025		Developer C		Removed restrictionof ODScore >= 2, Stakeholder A wants them all to display TKT-008

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_Sepsis_ScreeningTool]

************************************************************************************/

CREATE     PROCEDURE [reporting].[USP_IP_Sepsis_ScreeningTool]



AS



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT [PatName] [PATIENTS]

	, [PatMRNID] [MRN]

	, [EthnicGroup] [Ethnic Group]

	, [Race]

	, [Location] 

	, [PatEncCSNID] [CSN]

	, [AgeMonths] [Age (M)]

	, [AgeYears] [Age (Y)]

	, [InpAdmDate] [Admit Time]

	, [HospDischTime] [Disch Time]

	, [Disposition]

	, [LosHours] [LOS (Hrs)]

	, [ShiftDate] [Shift Date]

	, [ShiftAMPM] [Shift AM/PM]

	, [ShiftStart] [Shift Start]

	, [ShiftEnd] [Shift End]

	, [ADTDepartmentName] [Department]

	, [DepartmentRollup] [Department Rollup]

	, [InDepartmentTime] [In Department Time]

	, [OutDepartmentTime] [Out Department Time]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]



	, [SepsisPatientHuddleorAlertWithMDPNP] [Sepsis PATIENTS Huddle or CLINICAL_ALERTS With MD/PNP]

	, [HuddleDate] [Huddle Date]

	, [HuddleTime] [Huddle Time]

	, [PatientAssessedByMDPNP] [PATIENTS Assessed by MD/PNP]

	, [PhysicianName] [Physician Name]

	, [AddOrdersReceivedPlacedByMDPNP] [Additional Orders Received/Placed by MD/PNP]

	

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]



	, [Predisposition] [Predisposition?]

	, [InfectiousSymptoms] [Infectious Symptoms?]

	, [HematologicDysfunction] [Hematologic Dysfunction]

	, [RenalDysfunction] [Renal Dysfunction]

	, [NeurologicalDysfunction] [Neurological Dysfunction]

	, [RespiratoryDysfunction] [Respiratory Dysfunction]

	, [Pulse]

	, [Resp]

	, [BP]

	, [PerfusionWDL] [Perfusion (WDL)]

	, [RBrachialPulse] [R Brachial Pulse]

	, [LBrachialPulse] [L Brachial Pulse]

	, [RRadialPulse] [R Radial Pulse]

	, [LRadialPulse] [L Radial Pulse]

	, [RPosteriorTibialPulse] [R Posterior Tibial Pulse]

	, [LPosteriorTibialPulse] [L Posterior Tibial Pulse]

	, [RPedalPulse] [R Pedal Pulse]

	, [LPedalPulse] [L Pedal Pulse]

	, [CapillaryRefill] [Capillary Refill]

	, [SkinColor] [Skin Color]

	, [SkinConditionTemp] [Skin Condition/Temp]

	, [ExternalLactateResult] [External Lactate Result]

	, [ExternalCreatinine] [External Creatinine]

	, [ExternalPlatelets] [External Platelets]

	, [Notification]

	, CASE WHEN [ODScore] = 2 THEN 'Y' ELSE 'N' END [OD Score 2]

	, CASE WHEN [ODScore] >= 3 THEN 'Y' ELSE 'N' END [+ OD Score]

	, [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [FifteenthOrEOM] [15th or EOM]

	, [RefreshDate] [Refresh Date]

	, [ShiftColorDisplay] [Shift Color Display]

	, [UniqueRow] [Unique Row]

  FROM [reportingDB].[reporting].[IP_SEPSIS] 

  --WHERE ODScore >= 2 --7/24/2025 Removing Score restriction
GO

-- ==== reports/USP_RPTS_ED_Sepsis.sql ====
/**********************************************************************************************************

Author: <Unknown>

Create date:  <Unknown>

Description:  

Report Name: BI-Health System --> Quality --> ED Sepsis

==========================================================================================================

Revision Detail 



Date			Who						Description 

----------------------------------------------------------------------------------------------------------

2019.05.16		V_DEV001				[PROCEDURE_ORDERS].PROC_CODE is deprecated as of april 2019; Replacing it with PROC_ID.

2019.07.19		V_DEV001				MAR_ACTION_C changed data type from INT to VARCHAR.

2019.10.01		V_DEV001				Added new Sepsis Score Flowsheet ID '9000002613'

2019.11.07		V_DEV001				Added Quick Set/ OrdersetS OSQ: 

											- ED Sepsis Panel - OSQ 400002

											- Sepsis Antimicrobials Unknown Source - OSQ 400007

											- Neo Fever Panel - OSQ 400003

											- Oncology with Fever Panel - OSQ 400004

2019.11.08		V_DEV001				Updated calculation to include Triage Stop Time instead of Triage Start Time

2019.12.11		V_DEV001				Added First ABX Order and its related Pharmacy times

2020.04.10		V_DEV001				Added First and Last Blood Pressure information and ED Border Flag

2020.09.21		V_DEV001				Added Compliance for (FPS + ABX/ Bolus/ Rescreen):

											- Rescreen One Hour before Transfer/ Discharge

											- ED 2 PICU/ ED 2 Floor and then ICU

											- ED IP Bed assignment to IP Transfer Metric

											- ABX given only in ED setting

2020.10.29		V_DEV001				Set TRANSACTION ISOLATION LEVEL READ UNCOMMITTED

2020.11.17		V_DEV001				Set end date to T-1

2021.02.03		V_DEV001				Added first sepsis score day/night shift

2021.03.24		V_DEV001				Added PATIENTS's race and ethnic group info

2023.06.15		V_DEV003				Added age in days for 21 days or less age filter, and modified months age to include FLOOR



2025.08.06		V_DEV004				Added #SepsisAlertCancelled columns

2025.08.26		V_DEV004				Added Urine Culture Results, Organism name to Blood/CSF, and corrected Blood/CSF code

2025.10.06		V_DEV004				Added BP percentile Flowsheets [9001140203, 9001140205] (per TKT-009)

2025.12.07		V_DEV004				Added [Septic Shock] and [Blood Culture First Order Time] columns

==========================================================================================================

USAGE: 

	exec [reportingDB].[reports].[USP_ED_Sepsis] 'MB-1', 'ME-1' 

**********************************************************************************************************/ 





CREATE       PROCEDURE [reports].[USP_ED_Sepsis] (

	@StartDate VARCHAR(20) = NULL,

	@EndDate VARCHAR(20) = NULL

)



AS



SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;

	

DECLARE @dStartDate DATE;

DECLARE @dEndDate DATE;



	

IF @StartDate IS NULL OR @StartDate = ''

	SET @dStartDate = EMRDB.[dbo].[fn_parse_date]('MB-12')

ELSE

	SET @dStartDate = EMRDB.[dbo].[fn_parse_date](@StartDate)

	

IF @EndDate IS NULL OR @EndDate = ''

	SET @dEndDate = EMRDB.[dbo].[fn_parse_date]('T-1')

ELSE

	SET @dEndDate = EMRDB.[dbo].[fn_parse_date](@EndDate)





--SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

--SET NOCOUNT ON;



--DECLARE @dStartDate DATE = '2025-11-01';

--DECLARE @dEndDate DATE = '2025-11-30';





/* ************** */

/* Base ED Visits */

/* ************** */

DROP TABLE IF EXISTS #Base_Pop;



SELECT DISTINCT

	PEH.PAT_ENC_CSN_ID

	, PEH.PAT_ID

	, PAT.PAT_MRN_ID

	, PAT.PAT_NAME

	, ZEG.NAME AS [Ethnic Group]

	, ZPR.NAME AS [Race]

	, FEE.AGE_AT_ARRIVAL_MONTHS

	, FEE.AGE_AT_ARRIVAL_YEARS

	, PEH.INPATIENT_DATA_ID

	, PEH.ADT_ARRIVAL_TIME

	, DEE.TRIAGE_START_DTTM

	, DEE.TRIAGE_END_DTTM

	, PEH.HOSP_ADMSN_TIME

	, PEH.HOSP_DISCH_TIME

	, PEH.INP_ADM_DATE

	, PEH.ED_DEPARTURE_TIME

	, PEH.ED_DISPOSITION_C

	, ZED.NAME AS [Disposition]

	, LOC.LOCATION_ABBR [Location]

	, FLOOR(DATEDIFF(day,PAT.BIRTH_DATE,PEH.ADT_ARRIVAL_TIME)) AS AGE_IN_DAYS ---ADDED V_DEV003 6/15/2023 TKT-007 

	, FLOOR(DATEDIFF(MM,PAT.BIRTH_DATE,COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.ADT_ARRIVAL_TIME)) ) AS AGE_MONTHS  ---ADDED V_DEV003 6/15/2023 TKT-007  (AGE IN MONTHS IS SHOWING AS 1 WHEN ITS ONLY 2 WEEKS, ETC.)

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.ADT_ARRIVAL_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,PEH.ADT_ARRIVAL_TIME)) + DATENAME(YEAR, CONVERT(DATE, PEH.ADT_ARRIVAL_TIME)) AS DATE_STAMP



INTO #Base_Pop



FROM [EMRDB].[dbo].ED_ENCOUNTERS_FACT FEE



	INNER JOIN [EMRDB].[dbo].HOSPITAL_ENCOUNTERS PEH ON FEE.PAT_ENC_CSN_ID = PEH.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PAT_ENC_CSN_ID = FEE.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ED_DISPOSITION ZED ON ZED.ED_DISPOSITION_C = PEH.ED_DISPOSITION_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ETHNIC_GROUP ZEG ON ZEG.ETHNIC_GROUP_C = PAT.ETHNIC_GROUP_C

	LEFT OUTER JOIN [EMRDB].[dbo].PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PAT_ID = PAT.PAT_ID AND RACE.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].REF_PATIENT_RACE ZPR ON ZPR.PATIENT_RACE_C = RACE.PATIENT_RACE_C

	LEFT OUTER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = PEH.DEPARTMENT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].LOCATIONS LOC ON LOC.LOC_ID = DEP.REV_LOC_ID



WHERE 1=1

	AND FEE.ADT_ARRIVAL_DATE BETWEEN @dStartDate AND @dEndDate

;



CREATE CLUSTERED INDEX INX_Base_Pop_CSN ON #Base_Pop ([PAT_ENC_CSN_ID]);





/* ******************** */

/* Treatment Plan Begin */

/* ******************** */



-- All encounters from #Base_pop where ABX was administered

DROP TABLE IF EXISTS #BasePopABX;



WITH ABX AS

(

SELECT

		OM.PAT_ENC_CSN_ID

		, OM.ORDER_MED_ID

		, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

		, cm.[NAME]



	FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID --AND CM.THERA_CLASS_C = 11 --Antibiotics

		INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID



	WHERE 1=1

		AND MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND MAI.TAKEN_TIME < B.ED_DEPARTURE_TIME--09.23.2020; MAKE SURE THE Antibiotics WERE GIVEN IN ED

		AND OM.MED_ROUTE_C=11--IV ONLY

		AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

								, '7'			--RESTARTED

								, '102'		--GIVEN BY OTHER

								, '105'		--NEW CARTRIDGE

								, '113'		--GIVEN DURING DOWNTIME

								, '114'		--STARTED DURING DOWNTIME

								, '115'		--MEDICATION APPLIED

								, '122'		--CONTINUED FROM OR

								, '124'		--SELF ADMINISTERED VIA PUMP

								, '132'		--CONTINUED FROM PREVIOUS ORDER

								, '143'		--REDOSE

								, '1604'		--INFUSION GREATER THAN 15 MIN

								, '1605'		--INFUSION LESS THAN 15 MIN

								, '1607'		--NEW CARTRIDGE

								, '6'			--NEW BAG

								, '99'			--RATE CHANGE

								)

		AND OM.MEDICATION_ID IN 

			(



				select 

						medlist.MEDICATION_ID

					from

						(

							SELECT 

								erx.MEDICATION_ID,

								erx.NAME,

								cntl.VALUE_SET_DISPLAY as AGENT,

								case when CHARINDEX('^',cntl.VALUE_SET_ABBR)>0 then SUBSTRING(cntl.VALUE_SET_ABBR,0,CHARINDEX('^',cntl.VALUE_SET_ABBR)) else cntl.VALUE_SET_ABBR end as AGENT_GROUP,

								case when cntl.VALUE_SET_ABBR like '%^Y' then 1 else 0 end as DOT_MONITORING,

								gen.TITLE,

								ROW_NUMBER() over(partition by erx.MEDICATION_ID order by cntl.VALUE_SET_ABBR,cntl.VALUE_SET_DISPLAY asc) as AGENT_ORDER



							FROM

								EMRDB.dbo.MEDICATIONS erx

								OUTER APPLY(

									--Get the main medication's simple generic if its a mixture

									SELECT TOP 1 

										mix.DRUG_ID,

										comp.SIMPLE_GENERIC_C 

									FROM EMRDB.dbo.MED_MIX_COMPONENTS mix

										INNER JOIN EMRDB.dbo.MEDICATIONS comp on mix.DRUG_ID=comp.MEDICATION_ID

									WHERE 1=1

										AND mix.TYPE_C=3		--3 - Medications 

										AND mix.MEDICATION_ID=erx.MEDICATION_ID

									ORDER BY

										mix.LINE

								) mixture

								INNER JOIN EMRDB.dbo.REF_GENERIC_MED gen on gen.SIMPLE_GENERIC_C=coalesce(erx.SIMPLE_GENERIC_C,mixture.SIMPLE_GENERIC_C)

								INNER JOIN reportingDB.reports.CONFIG_VALUE_SET cntl on cntl.VALUE_SET_ID=3016 and cntl.CODE=gen.SIMPLE_GENERIC_C -- and cntl.VALUE_SET_ABBR='Antibacterial'

						) medlist

					where

						medlist.AGENT_ORDER=1						

			)



	UNION



	SELECT DISTINCT

		OM.PAT_ENC_CSN_ID

		, OM.ORDER_MED_ID

		, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

		, cm.NAME



	FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE



		INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID AND CM.THERA_CLASS_C = 11 --Antibiotics

		INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID



	WHERE 1=1

		AND MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND MAI.TAKEN_TIME < B.ED_DEPARTURE_TIME--09.23.2020; MAKE SURE THE Antibiotics WERE GIVEN IN ED

		AND OM.MED_ROUTE_C=11--IV ONLY

		AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

								, '7'			--RESTARTED

								, '102'		--GIVEN BY OTHER

								, '105'		--NEW CARTRIDGE

								, '113'		--GIVEN DURING DOWNTIME

								, '114'		--STARTED DURING DOWNTIME

								, '115'		--MEDICATION APPLIED

								, '122'		--CONTINUED FROM OR

								, '124'		--SELF ADMINISTERED VIA PUMP

								, '132'		--CONTINUED FROM PREVIOUS ORDER

								, '143'		--REDOSE

								, '1604'		--INFUSION GREATER THAN 15 MIN

								, '1605'		--INFUSION LESS THAN 15 MIN

								, '1607'		--NEW CARTRIDGE

								, '6'			--NEW BAG

								, '99'			--RATE CHANGE

								)

)



SELECT

	ABX.PAT_ENC_CSN_ID

	,ABX.ORDER_MED_ID

	,ABX.NAME

	,ABX.ABX_ADMIN_TIME

	,ROW_NUMBER() OVER(PARTITION BY ABX.PAT_ENC_CSN_ID ORDER BY ABX.ABX_ADMIN_TIME) TIME_LINE



INTO #BasePopABX

FROM ABX						

;





/* *************** */

/* Chief Complaint */

/* *************** */

DROP TABLE IF EXISTS #Base_Pop_ENC_Reason;



SELECT DISTINCT   CAT.PAT_ENC_CSN_ID,

        STUFF((	SELECT ';' + CONVERT(VARCHAR,CRFV.REASON_VISIT_NAME)-- AS [text()]

                FROM #Base_Pop SUB

					INNER JOIN [EMRDB].[dbo].ENCOUNTER_VISIT_REASONS RSN ON RSN.PAT_ENC_CSN_ID = SUB.PAT_ENC_CSN_ID AND RSN.LINE>1

					INNER JOIN [EMRDB].[dbo].VISIT_REASONS CRFV ON CRFV.REASON_VISIT_ID = RSN.ENC_REASON_ID

				WHERE

                    SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

				ORDER BY LINE

                    FOR XML PATH('')

               ), 1, 1, '' )

            AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM  #Base_Pop CAT

;





/* ************* */

/* Order Set OSQ */

/* ************* */

DROP TABLE IF EXISTS #SSOrderSetOSQ_PRL;



	SELECT

		B.PAT_ENC_CSN_ID

		, OM.ORDER_DTTM

		, OM2.ORD_OSQ_ID AS PRL_ORDERSET_ID

	INTO #SSOrderSetOSQ_PRL

	FROM #Base_Pop B

		INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN [EMRDB].[dbo].MEDICATION_ORDERS_EXT OM2 ON OM2.ORDER_ID = OM.ORDER_ID AND OM2.ORD_OSQ_ID IN (400002,400007,400003,400004)

	WHERE OM.ORDER_DTTM BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME



UNION



	SELECT

		B.PAT_ENC_CSN_ID

		, OM.ORDER_DTTM

		, OM2.ORD_OSQ_ID AS PRL_ORDERSET_ID

	FROM #Base_Pop B

		INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS_EXT OM2 ON OM2.ORDER_ID = OM.ORDER_ID AND OM2.ORD_OSQ_ID IN (400002,400007,400003,400004)

	WHERE

		OM.ORDER_DTTM BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME



UNION



	SELECT

		B.PAT_ENC_CSN_ID

		, OM.ORDER_DTTM

		, OM.PRL_ORDERSET_ID

	FROM #Base_Pop B

		INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	WHERE

		OM.PRL_ORDERSET_ID IN (400001)-- (40400100, 40400058, 40400196, 40400153, 4058600002, 400001) --Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway

		AND OM.ORDER_DTTM BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME

;





/* ******************* */

/* Order Set           */

/* ******************* */

DROP TABLE IF EXISTS #SSOrderSet;



SELECT

	PAT_ENC_CSN_ID

	, ORDER_DTTM

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY ORDER_DTTM ASC) AS TIME_LINE

	, PRL_ORDERSET_ID

INTO #SSOrderSet 

FROM #SSOrderSetOSQ_PRL

;





/* ******************* */

/* Bolus               */

/* ******************* */

DROP TABLE IF EXISTS #BasePopBolus;



SELECT

	B.PAT_ENC_CSN_ID

	, MAI.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, CASE	WHEN OM.MEDICATION_ID IN (700001, 700002) THEN 'SODIUM CHLORIDE 0.99%'

			ELSE CM.[NAME]

	  END AS Medication

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY MAI.TAKEN_TIME ASC) TIME_LINE

	, MAI.SIG AS BOLUS_VOLUME



INTO #BasePopBolus 

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

	INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID



WHERE 1=1

	AND MAI.TAKEN_TIME IS NOT NULL --ADMINISTERED BOLUS ONLY

	AND MAI.TAKEN_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME

	AND (OM.MEDICATION_ID IN (700001  --SODIUM CHLORIDE 0.99 % IV BOLUS

							, 7000739 --LACTATED RINGERS IV BOLUS

							, 700003    --ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION

							, 7006331 --ELECTROLYE-A IV Bolus (PLASMALYTE)

							, 700002	--SODIUM CHLORIDE 0.99 % INJECTION SYRINGE--ADDED ON 04.02.2019

							)

		OR (OM.MEDICATION_ID = 700004)

	AND OM.HV_DISCR_FREQ_ID = '300902') -- FREQUENCY = ONCE 

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

	AND CONVERT(NUMERIC, MAI.SIG ) > 95.0

GROUP BY

	B.PAT_ENC_CSN_ID

	, MAI.TAKEN_TIME

	, MAI.SIG

	, OM.MEDICATION_ID

	, CM.NAME

	--select * from #BasePopBolus WHERE TIME_LINE=1

	/*PATIENTS Weight*/

;





/* ******************* */

/* Encounter Weight    */

/* ******************* */

DROP TABLE IF EXISTS #EncounterWeights;



SELECT

	A.PAT_ENC_CSN_ID

	, CAST(ROUND(CONVERT(FLOAT, MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

	, ROW_NUMBER() OVER(PARTITION BY A.PAT_ENC_CSN_ID ORDER BY C.RECORDED_TIME ASC) AS TIME_LINE

INTO #EncounterWeights

FROM #Base_Pop A

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS B ON A.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS C ON B.FSD_ID = C.FSD_ID AND  C.FLO_MEAS_ID='94'

;





/* ******************* */

/* Hypotension         */

/* ******************* */

DROP TABLE IF EXISTS #Hypotension;



SELECT

	C.PAT_ENC_CSN_ID

	, IFM.RECORDED_TIME

	, C.AGE_MONTHS

	, C.AGE_YEARS

	, LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) AS SYSTOLIC

	, IFM.MEAS_VALUE

	, ROW_NUMBER() OVER(PARTITION BY C.PAT_ENC_CSN_ID ORDER BY IFM.RECORDED_TIME ASC) AS TIME_LINE

INTO #Hypotension 

FROM #Base_Pop C 

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = C.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

WHERE 1=1

	AND IFM.FLO_MEAS_ID = '95'

	AND IFM.RECORDED_TIME IS NOT NULL 

	AND IFM.RECORDED_TIME BETWEEN C.ADT_ARRIVAL_TIME AND C.ED_DEPARTURE_TIME

	AND IFM.MEAS_VALUE IS NOT NULL

;







/* ********************** */

/* Sepsis CLINICAL_ALERTS Cancelled */

/* ********************** */

DROP TABLE IF EXISTS #SepsisAlertCancelled;



SELECT 

	C.PAT_ENC_CSN_ID

	, IFM.RECORDED_TIME	AS SEPSIS_ALERT_CANC_TIME

	, C.AGE_MONTHS

	, C.AGE_YEARS

	, 'Y'				AS SEPSIS_ALERT_CANC_YN

	, IFM.MEAS_COMMENT	AS SEPSIS_ALERT_CANC_BY		-- Free text

	, ROW_NUMBER() OVER(PARTITION BY C.PAT_ENC_CSN_ID ORDER BY IFM.RECORDED_TIME ASC) AS TIME_LINE

INTO #SepsisAlertCancelled 

FROM #Base_Pop C 

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = C.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

WHERE 1=1

	AND IFM.FLO_MEAS_ID = '9001125002'	-- R HS ED SEPSIS CLINICAL_ALERTS CANCELLED

	AND IFM.RECORDED_TIME IS NOT NULL 

	AND IFM.RECORDED_TIME BETWEEN C.ADT_ARRIVAL_TIME AND C.ED_DEPARTURE_TIME

	AND IFM.MEAS_VALUE IS NOT NULL

;







/* ******************* */

/* CVL Time            */

/* ******************* */

DROP TABLE IF EXISTS #ALLCVLTime;



SELECT DISTINCT

	C.PAT_ENC_CSN_ID

	, ILN.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY C.PAT_ENC_CSN_ID ORDER BY ILN.PLACEMENT_INSTANT) TIME_LINE

INTO #ALLCVLTime

FROM #Base_Pop C

	INNER JOIN [EMRDB].[dbo].LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID 

	INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = ILN.FLO_MEAS_ID

		AND CVS.VALUE_SET_ID = 3022 --CVL CODES

WHERE ILN.PLACEMENT_INSTANT BETWEEN C.ADT_ARRIVAL_TIME AND C.ED_DEPARTURE_TIME

;





/* ******************* */

/* Presssors           */

/* ******************* */

DROP TABLE IF EXISTS #Pressors;



SELECT DISTINCT

	B.PAT_ENC_CSN_ID

	, MAI.TAKEN_TIME

	, CM.NAME AS MEDICATION

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY MAI.TAKEN_TIME) AS TIME_LINE

INTO #Pressors 

FROM #Base_Pop B

	LEFT JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	LEFT JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

	LEFT JOIN EMRDB.dbo.GROUPER_MED_RECORDS GMR ON GMR.EXP_MEDS_LIST_ID = CM.MEDICATION_ID

	LEFT JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

	LEFT JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE 1=1

	AND GMR.GROUPER_ID IN ('8000100'    -- HS RX EPINEPHRINE SEPSIS

							, '8000101' -- HS RX DOPAMINE SEPSIS

							, '8000102' -- HS RX DOBUTAMINE SEPSIS

							, '8000103' -- HS RX MILRINONE SEPSIS

							, '8000104' -- HS RX NOREPINEPHRINE SEPSIS

						)

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

	AND MAI.ROUTE_C = 11 --INTRAVENOUS

	AND (MAI.TAKEN_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

;







/* ******************* */

/* SV02                */

/* ******************* */

DROP TABLE IF EXISTS #SVO2;



SELECT

	B.PAT_ENC_CSN_ID

	, OP.ORDER_TIME AS MBOrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID

INTO #SVO2

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS ON B.PAT_ENC_CSN_ID = LAB_ORDER_RESULTS.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE 1=1

	AND LAB_ORDER_RESULTS.COMPONENT_ID IN (5000001861, 5000000478)

	AND (OP.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

;







/* ******************* */

/* Lactic Acid         */

/* ******************* */

DROP TABLE IF EXISTS #LacticAcid;



SELECT

	B.PAT_ENC_CSN_ID

	, OP.ORDER_PROC_ID

	, OP.ORDER_TIME AS MBOrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

INTO #LacticAcid

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS ON LAB_ORDER_RESULTS.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID IN (5000000446, 5000000447, 5000000449)

	AND (OP.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

;







/* ******************* */

/* Procalcitonin       */

/* ******************* */

DROP TABLE IF EXISTS #Procalcitonin;



SELECT

	B.PAT_ENC_CSN_ID

	, OP.ORDER_TIME AS MBOrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID

INTO #Procalcitonin

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS ON LAB_ORDER_RESULTS.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE 1=1

	AND LAB_ORDER_RESULTS.COMPONENT_ID = 500001	-- 'LAB014'

	AND (OP.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

;





/* ******************* */

/* Blood Culture       */

/* ******************* */

DROP TABLE IF EXISTS #BloodCultureValue;



WITH BloodCultureResults AS

(

	SELECT

		B.PAT_ENC_CSN_ID

		, OP.ORDER_PROC_ID

		, OP.ORDER_TIME

		, RESULTS.RESULT_TIME

		, RESULTS.COMP_OBS_INST_TM

		, RESULTS.ORD_VALUE

		, CASE WHEN RESULTS.RESULT_FLAG_C IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01		-- Abnormal or Critical

		, RESULTS.LRR_BASED_ORGAN_ID

		, [ORGANISMS].EXTERNAL_NAME



	FROM #Base_Pop B



		INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS RESULTS ON B.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

		INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS	 OP		 ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID 

														AND OP.PROC_ID IN (600003,600004,600011,600012)	-- 'LAB001', 'NUR001', 'LAB012', 'LAB011'



		LEFT JOIN [EMRDB].[dbo].ORGANISMS ON [RESULTS].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE (OP.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

)



, PositiveCultures AS

(

	SELECT

		PAT_ENC_CSN_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, COALESCE(STRING_AGG(EXTERNAL_NAME, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM BloodCultureResults

	GROUP BY PAT_ENC_CSN_ID

	HAVING MAX(CRITICAL_VALUE_01) = 1

)



, NegativeCultures AS

(

	SELECT

		PAT_ENC_CSN_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]



	FROM BloodCultureResults

	GROUP BY PAT_ENC_CSN_ID

	HAVING MAX(CRITICAL_VALUE_01) = 0

)



SELECT * 

INTO #BloodCultureValue

FROM PositiveCultures

UNION

SELECT * FROM NegativeCultures

;







/* ******************* */

/* Urine Culture       */

/* ******************* */

DROP TABLE IF EXISTS #UrineCultureValue;



WITH UrineCultureResults AS 

(

	SELECT

		B.PAT_ENC_CSN_ID

		, OP.ORDER_PROC_ID

		, OP.ORDER_TIME

		, RESULTS.RESULT_TIME

		, RESULTS.COMP_OBS_INST_TM

		, RESULTS.ORD_VALUE

		, RESULTS.RESULT_FLAG_C

		, CASE WHEN RESULTS.RESULT_FLAG_C IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01		-- Abnormal or Critical

		, RESULTS.LRR_BASED_ORGAN_ID

		, [ORGANISMS].EXTERNAL_NAME



	FROM #Base_Pop B



		INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS RESULTS ON B.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

		INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS	 OP		 ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID 

														AND OP.PROC_ID IN (600001, 600007, 600008, 600009, 600010)	-- 'LAB002', 'LAB008', 'LAB009', 'LAB010', 'POC001'



		LEFT JOIN [EMRDB].[dbo].ORGANISMS ON [RESULTS].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE (OP.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)



)



, PositiveCultures AS

(

	SELECT

		PAT_ENC_CSN_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, COALESCE(STRING_AGG(EXTERNAL_NAME, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM UrineCultureResults

	GROUP BY PAT_ENC_CSN_ID

	HAVING MAX(CRITICAL_VALUE_01) = 1

)



, NegativeCultures AS

(

	SELECT

		PAT_ENC_CSN_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]		-- 'No Growth' or contamination with normal flora



	FROM UrineCultureResults

	GROUP BY PAT_ENC_CSN_ID

	HAVING MAX(CRITICAL_VALUE_01) = 0

)



SELECT * 

INTO #UrineCultureValue

FROM PositiveCultures

UNION

SELECT * FROM NegativeCultures

;







/* ******************* */

/* CSF Culture         */

/* ******************* */

DROP TABLE IF EXISTS #CsfCultureValue;



WITH CsfCultureResults AS 

(

	SELECT

		B.PAT_ENC_CSN_ID

		, op.ORDER_PROC_ID

		, OP.ORDER_TIME

		, RESULTS.RESULT_TIME

		, RESULTS.COMP_OBS_INST_TM

		, RESULTS.ORD_VALUE

		, RESULTS.RESULT_FLAG_C

		, CASE WHEN RESULTS.RESULT_FLAG_C IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01		-- Abnormal or Critical

		, RESULTS.LRR_BASED_ORGAN_ID

		, [ORGANISMS].EXTERNAL_NAME



	FROM #Base_Pop B

		INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS RESULTS ON B.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

		INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS	 OP		 ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID

														AND OP.PROC_ID IN (600005,600006, 600002)		-- 'LAB006', 'LAB007', 'LAB003'

														AND OP.SPECIMEN_SOURCE_C=304				-- Lumber puncture



		LEFT JOIN [EMRDB].[dbo].ORGANISMS ON [RESULTS].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE (OP.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

)



, PositiveCultures AS

(

	SELECT

		PAT_ENC_CSN_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, COALESCE(STRING_AGG(EXTERNAL_NAME, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM CsfCultureResults

	GROUP BY PAT_ENC_CSN_ID

	HAVING MAX(CRITICAL_VALUE_01) = 1

)



, NegativeCultures AS

(

	SELECT

		PAT_ENC_CSN_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]



	FROM CsfCultureResults

	GROUP BY PAT_ENC_CSN_ID

	HAVING MAX(CRITICAL_VALUE_01) = 0

)



SELECT * 

INTO #CsfCultureValue

FROM PositiveCultures

UNION

SELECT * FROM NegativeCultures

;





/* ******************* */

/* ETT                 */

/* ******************* */

DROP TABLE IF EXISTS #ETT;

SELECT

	B.PAT_ENC_CSN_ID,

	ILN.IP_LDA_ID,

	ILN.PLACEMENT_INSTANT,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY ILN.PLACEMENT_INSTANT) TIME_LINE

INTO #ETT

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE 1=1

	AND ILN.FLO_MEAS_ID='900112'

	AND ILN.PLACEMENT_INSTANT IS NOT NULL

	AND (ILN.PLACEMENT_INSTANT BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

;







/* ******************* */

/* IV Placement        */

/* ******************* */

DROP TABLE IF EXISTS #IV;



SELECT

	B.PAT_ENC_CSN_ID,

	ILN.IP_LDA_ID,

	ILN.PLACEMENT_INSTANT,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY ILN.PLACEMENT_INSTANT) TIME_LINE

INTO #IV

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE 1=1

	AND ILN.FLO_MEAS_ID='900111'

	AND ILN.PLACEMENT_INSTANT IS NOT NULL

	AND (ILN.PLACEMENT_INSTANT BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

;







/* ******************* */

/* Hem/Oncology        */

/* ******************* */

DROP TABLE IF EXISTS #ED2HEMONC;



SELECT

	B.PAT_ENC_CSN_ID

	, DEP.DEPARTMENT_NAME

	, EMRDB_ADT_ED.EFFECTIVE_TIME AS ED2HemoncTime

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY EMRDB_ADT_ED.EFFECTIVE_TIME ASC) AS TIME_LINE

INTO #ED2HEMONC

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS EMRDB_ADT_ED 

			ON EMRDB_ADT_ED.PAT_ENC_CSN_ID =  B.PAT_ENC_CSN_ID

				AND EMRDB_ADT_ED.DEPARTMENT_ID IN (200108022) 

				AND EMRDB_ADT_ED.EVENT_TYPE_C = 4 --TRANSFER OUT

				AND EMRDB_ADT_ED.EVENT_SUBTYPE_C <> 2 --CANCELED

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS EMRDB_ADT_GENCARE 

			ON EMRDB_ADT_ED.XFER_IN_EVENT_ID = EMRDB_ADT_GENCARE.EVENT_ID

				AND EMRDB_ADT_GENCARE.DEPARTMENT_ID IN (200108001, 200108115, 20120106, 20101124, 20108007) 

				AND EMRDB_ADT_GENCARE.EVENT_TYPE_C = 3 --TRANSFER IN

				AND EMRDB_ADT_GENCARE.EVENT_SUBTYPE_C <> 2 --CANCELED

	INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = EMRDB_ADT_GENCARE.DEPARTMENT_ID

;







/* ******************* */

/* ICU                 */

/* ******************* */

DROP TABLE IF EXISTS #ED2ICU;



SELECT

	B.PAT_ENC_CSN_ID

	, DEP.DEPARTMENT_NAME

	, EMRDB_ADT_ED.EFFECTIVE_TIME AS ED2ICUTime

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY EMRDB_ADT_ED.EFFECTIVE_TIME ASC) AS TIME_LINE

INTO #ED2ICU

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS EMRDB_ADT_ED ON EMRDB_ADT_ED.PAT_ENC_CSN_ID =  B.PAT_ENC_CSN_ID

				AND EMRDB_ADT_ED.DEPARTMENT_ID IN (200108022) 

				AND EMRDB_ADT_ED.EVENT_TYPE_C = 4 --TRANSFER OUT

				AND EMRDB_ADT_ED.EVENT_SUBTYPE_C <> 2 --CANCELED

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS EMRDB_ADT_GENCARE ON EMRDB_ADT_ED.XFER_IN_EVENT_ID = EMRDB_ADT_GENCARE.EVENT_ID

				AND EMRDB_ADT_GENCARE.DEPARTMENT_ID IN (20101116			--EAST ICU

														, 20101124			--EAST CARDIAC ICU

														, 20101126			--EAST NEURO ICU

														, 20101127			--EAST PEDIATRIC ICU

														, 20101128			--EAST SURGICAL ICU

														, 20101165			--EAST REMOTE ICU

														, 20120106			--WEST CARDIAC ICU

														, 20120121			--WEST ICU							

														, 200108001			--MAIN 2 PAVILION PICU

														, 200108070			--MAIN 3 CICU

														, 200108115			--MAIN 2 PICU NEURO

														, 200108147			--MAIN PHARMACY ICU

														) 

				AND EMRDB_ADT_GENCARE.EVENT_TYPE_C = 3 --TRANSFER IN

				AND EMRDB_ADT_GENCARE.EVENT_SUBTYPE_C <> 2 --CANCELED

	INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = EMRDB_ADT_GENCARE.DEPARTMENT_ID

;







/* ******************* */

/* Gen Care            */

/* ******************* */

DROP TABLE IF EXISTS #ED2GEN;



SELECT

	B.PAT_ENC_CSN_ID

	, DEP.DEPARTMENT_NAME

	, EMRDB_ADT_ED.EFFECTIVE_TIME AS ED2GENTime

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY EMRDB_ADT_ED.EFFECTIVE_TIME ASC) AS TIME_LINE

	, GEN2ICU.EFFECTIVE_TIME AS [Gen Back To ICU Time]

	, GEN2ICU.DEPARTMENT_NAME AS [Gen Back To ICU Department]

INTO #ED2GEN

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS EMRDB_ADT_ED 

			ON EMRDB_ADT_ED.PAT_ENC_CSN_ID =  B.PAT_ENC_CSN_ID

				AND EMRDB_ADT_ED.DEPARTMENT_ID IN (200108022) 

				AND EMRDB_ADT_ED.EVENT_TYPE_C = 4 --TRANSFER OUT

				AND EMRDB_ADT_ED.EVENT_SUBTYPE_C <> 2 --CANCELED

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS EMRDB_ADT_GENCARE 

			ON EMRDB_ADT_ED.XFER_IN_EVENT_ID = EMRDB_ADT_GENCARE.EVENT_ID

				AND EMRDB_ADT_GENCARE.DEPARTMENT_ID IN (200108021, 200108020, 200108018, 200108017, 200108110, 200108012, 200108011, 200108010, 200108009, 200108008) 

				AND EMRDB_ADT_GENCARE.EVENT_TYPE_C = 3 --TRANSFER IN

				AND EMRDB_ADT_GENCARE.EVENT_SUBTYPE_C <> 2 --CANCELED

	INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = EMRDB_ADT_GENCARE.DEPARTMENT_ID	

	OUTER APPLY--09.09.2020 V_DEV001 added this to check for PATIENTS who went from ED --> Gen Care and then back to ICU within 24 hours

	(

		SELECT TOP 1 ICU.EFFECTIVE_TIME, DEP.DEPARTMENT_NAME

		FROM [EMRDB].[dbo].ADT_EVENTS ICU

		INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = ICU.DEPARTMENT_ID

		WHERE ICU.PAT_ENC_CSN_ID = EMRDB_ADT_GENCARE.PAT_ENC_CSN_ID

			AND (ICU.EFFECTIVE_TIME BETWEEN EMRDB_ADT_GENCARE.EFFECTIVE_TIME AND DATEADD(HH,24,EMRDB_ADT_GENCARE.EFFECTIVE_TIME) )

			AND ICU.DEPARTMENT_ID IN (20101116			--EAST ICU

									, 20101124			--EAST CARDIAC ICU

									, 20101126			--EAST NEURO ICU

									, 20101127			--EAST PEDIATRIC ICU

									, 20101128			--EAST SURGICAL ICU

									, 20101165			--EAST REMOTE ICU

									, 20120106			--WEST CARDIAC ICU

									, 20120121			--WEST ICU							

									, 200108001			--MAIN 2 PAVILION PICU

									, 200108070			--MAIN 3 CICU

									, 200108115			--MAIN 2 PICU NEURO

									, 200108147			--MAIN PHARMACY ICU

									) 

			AND ICU.EVENT_TYPE_C = 3 --TRANSFER IN

			AND ICU.EVENT_SUBTYPE_C <> 2 --CANCELED

		ORDER BY ICU.EFFECTIVE_TIME ASC

	) GEN2ICU

;





/* ******************* */

/* BPA                 */

/* ******************* */

DROP TABLE IF EXISTS #BPA;



SELECT

	B.PAT_ENC_CSN_ID,

	ALT.ALT_ID,

	AH.ALT_ACTION_INST,

	ZAS.NAME AS ALERT_STATUS,

	ZSP.NAME AS ALERT_SHOWN_PLACE,

	ZAAT.NAME AS ACTION_TAKE,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY AH.ALT_ACTION_INST) AS TIME_LINE,

	ZASOR.NAME AS OVERRIDDEN,

	ah.SPEC_OVR_CMNT,

	EMP.NAME

INTO #BPA

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].CLINICAL_ALERTS ALT ON ALT.PAT_CSN = B.PAT_ENC_CSN_ID AND ALT.BPA_LOCATOR_ID = '900130001'

	INNER JOIN [EMRDB].[dbo].ALERT_HISTORY AH ON AH.ALT_ID = ALT.ALT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].ALERT_ACTIONS ACA ON ACA.ALT_CSN_ID = AH.ALT_CSN_ID AND ACA.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_ACTIONS ZAAT ON ZAAT.ALT_ACTION_TAKEN_C = ACA.ACTION_TAKEN_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_OVERRIDE_REASONS ZASOR ON ZASOR.ALRT_SP_OVR_RSN_C = AH.SPEC_OVR_RSN_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_STATUS ZAS ON ZAS.ALT_STATUS_C = AH.ALT_STATUS_C

	LEFT OUTER JOIN [EMRDB].[dbo].REF_SHOWN_PLACE ZSP ON ZSP.SHOWN_PLACE_C = AH.SHOWN_PLACE_C

	LEFT OUTER JOIN [EMRDB].[dbo].EMPLOYEES EMP ON EMP.USER_ID = AH.USER_ID

WHERE AH.ALT_ACTION_INST BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME

;







/* ******************* */

/* Severe Sepsis       */

/* ******************* */

DROP TABLE IF EXISTS #Base_Pop_Severe_ED_Scores;



SELECT

	BP.PAT_ENC_CSN_ID

	, IFM.MEAS_VALUE

	, IFM.RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY BP.PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #Base_Pop_Severe_ED_Scores 

FROM #Base_Pop BP 

	INNER JOIN [EMRDB].[dbo].HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS IFR ON PEH.INPATIENT_DATA_ID = IFR.INPATIENT_DATA_ID

	INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

WHERE 1=1

	AND IFM.FLO_MEAS_ID IN ('9000161709','9000002613')--SEPSIS SCORE--ADDED NEW ED SEPSIS SCORE 9000002613 ON 10.01.2019

	and IFM.RECORDED_TIME BETWEEN BP.ADT_ARRIVAL_TIME AND BP.ED_DEPARTURE_TIME

;





/* ******************* */

/* Positive Sepsis     */

/* ******************* */

DROP TABLE IF EXISTS #ED_PositiveScores;



SELECT

	PAT_ENC_CSN_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO #ED_PositiveScores

FROM #Base_Pop_Severe_ED_Scores

WHERE MEAS_VALUE > 4

;





/* ************************ */

/* Severe + Positive Sepsis */

/* ************************ */

DROP TABLE IF EXISTS #Base_Pop_SepsisScores_ConCat;



SELECT DISTINCT CAT.PAT_ENC_CSN_ID,

        STUFF(( SELECT ',' + CONVERT(VARCHAR,SUB.MEAS_VALUE)-- AS [text()]

                FROM #Base_Pop_Severe_ED_Scores SUB

				WHERE SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

				ORDER BY RECORDED_TIME

                FOR XML PATH('')

                ), 1, 1, '' )

        AS [AllSepsis_Scores]

INTO #Base_Pop_SepsisScores_ConCat

FROM  #Base_Pop_Severe_ED_Scores CAT





/* ******************************************* */

/* Time from First Positive Score -> First Abx */

/* ******************************************* */

DROP TABLE IF EXISTS #FirstPositiveOD_To_ABXAdminTime;



SELECT

	[subQ].PAT_ENC_CSN_ID

	,[subQ].MEDICATION

	,[subQ].ABX_ADMIN_TIME

	,[subQ].RECORDED_TIME,

	DATEDIFF(MI, [subQ].RECORDED_TIME, [subQ].ABX_ADMIN_TIME) AS POSOD2ABX



INTO #FirstPositiveOD_To_ABXAdminTime



FROM 

	(

		SELECT 

			[#BasePopABX].PAT_ENC_CSN_ID

			, [#BasePopABX].[NAME] AS MEDICATION

			, [#BasePopABX].ABX_ADMIN_TIME

			, [#ED_PositiveScores].MEAS_VALUE

			, [#ED_PositiveScores].RECORDED_TIME

			, ROW_NUMBER() OVER(PARTITION BY [#BasePopABX].PAT_ENC_CSN_ID ORDER BY [#BasePopABX].ABX_ADMIN_TIME ASC) MYLINE

		FROM #BasePopABX

		INNER JOIN #ED_PositiveScores ON [#BasePopABX].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

			AND [#ED_PositiveScores].RECORDED_TIME < [#BasePopABX].ABX_ADMIN_TIME

			AND [#ED_PositiveScores].FIRST_TIME_LINE=1

	) subQ

WHERE [subQ].MYLINE=1

;





/* ******************************** */

/* First Abx Order and Time Details */

/* ******************************** */

DROP TABLE IF EXISTS #FirstABXAdminTimeDetails;



SELECT

	A.PAT_ENC_CSN_ID

	, ORD.ORDER_MED_ID "Order ID"

	, ORD.ORDERING_DTTM "Order date and time"

	, ORT.RXQ_INSTANT [In VERIFY Queue Time]

	, ORT.RX_VERIFY_INSTANT [Verified in Queue Time]

	, ORT.[Queue Verified by]

	, VERIFY.ACTION_INSTANT " Order VERIFY date and time"

	, DISPENSE.ACTION_INSTANT "Order Dispense date and time"

	, ACTION.ACTION_DTTM "Rx Dispense Sent Time"



INTO #FirstABXAdminTimeDetails



FROM #BasePopABX A

	INNER JOIN [EMRDB].[dbo].V_PHARMACY_ORDER ORD on ORD.ORDER_MED_ID = A.ORDER_MED_ID AND A.TIME_LINE=1--LOOK FOR FIRST ANTIBIOTIC ADMINISTRATION ONLY

	INNER JOIN

		(

			SELECT

				ODI.ORDER_MED_ID, ODI.ACTION_INSTANT,ODI.CONTACT_DATE_REAL, ROW_NUMBER()OVER(PARTITION BY ODI.ORDER_MED_ID ORDER BY ACTION_INSTANT ASC) AS MYLINE

			FROM

			[EMRDB].[dbo].ORDER_DISPENSE_INFO  ODI WHERE ODI.ORD_CNTCT_TYPE_C = 4--VERIFY

		)VERIFY on ord.ORDER_MED_ID = VERIFY.ORDER_MED_ID AND VERIFY.MYLINE=1

	INNER JOIN

		(

			SELECT

				ODI.ORDER_MED_ID, ODI.ACTION_INSTANT,ODI.VERIFY_CONTDATREAL,ODI.CONTACT_DATE_REAL,ODI.CONTACT_DATE, ROW_NUMBER()OVER(PARTITION BY ODI.ORDER_MED_ID ORDER BY ACTION_INSTANT ASC) AS MYLINE

			FROM

			[EMRDB].[dbo].ORDER_DISPENSE_INFO  ODI WHERE ODI.ORD_CNTCT_TYPE_C = 95--DISPENSE

		)DISPENSE ON ord.ORDER_MED_ID = DISPENSE.ORDER_MED_ID AND DISPENSE.MYLINE=1

			AND VERIFY.CONTACT_DATE_REAL = DISPENSE.VERIFY_CONTDATREAL

			AND DISPENSE.ACTION_INSTANT<A.ABX_ADMIN_TIME--MAKE SURE WE ARE LOOKING AT THE RIGHT MEDICATION ADMINT TIME. A MEDICATION ORDER COULD HAVE MULTIPLE DISPENSES

	LEFT OUTER JOIN [EMRDB].[dbo].V_PHARMACY_DISPENSE disp on DISPENSE.ORDER_MED_ID = disp.ORDER_MED_ID and DISPENSE.CONTACT_DATE_REAL = disp.CONTACT_DATE_REAL

	LEFT OUTER JOIN 

		(

			SELECT VRDA.ACTION_ID, VRDA.ACTION_DTTM, ROW_NUMBER()OVER(PARTITION BY VRDA.ACTION_ID ORDER BY VRDA.ACTION_DTTM ASC) AS MYLINE FROM 

			[EMRDB].[dbo].V_PHARMACY_DISPENSE_ACTION VRDA WHERE VRDA.ACTION_TYPE_C=270

		)action on disp.ACTION_ID = action.ACTION_ID AND ACTION.MYLINE=1

	LEFT OUTER JOIN 

		(

			SELECT ORT1.ORDER_MED_ID,ORT1.RXQ_INSTANT, ORT1.RX_VERIFY_INSTANT, ORT1.RX_VER_USER_ID, EMP.NAME AS [Queue Verified by],

				ROW_NUMBER()OVER(PARTITION BY ORT1.ORDER_MED_ID ORDER BY LINE DESC) MYLINE

			FROM [EMRDB].[dbo].RX_VERIFY_TRACE ORT1

			LEFT OUTER JOIN [EMRDB].[dbo].EMPLOYEES EMP ON EMP.USER_ID = ORT1.RX_VER_USER_ID

		)ORT ON ORT.ORDER_MED_ID = ord.ORDER_MED_ID AND ORT.MYLINE=1

;



/* ********** */

/* Bed Events */

/* ********** */

DROP TABLE IF EXISTS #BedEvents;



SELECT

	B.PAT_ENC_CSN_ID, C.RECORD_NAME AS [EVENT], EIEI.EVENT_TYPE AS [EVENT ID],EIEI.EVENT_TIME,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY EIEI.EVENT_TIME ) AS TIME_LINE,

	ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID, EIEI.EVENT_TYPe ORDER BY EIEI.EVENT_TIME ) AS REQ_LINE--JUST IN CASE IF THERE IS MORE THAN ONE EVENT OF THE SAME EVENT_TYPE.

INTO #BedEvents

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].ED_PATIENT_INFO EIPI ON EIPI.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN [EMRDB].[dbo].ED_EVENT_INFO EIEI ON EIEI.EVENT_ID = EIPI.EVENT_ID AND EIEI.EVENT_TYPE IN ('2600000347','2600000346')

	INNER JOIN [EMRDB].[dbo].ED_EVENT_TEMPLATES C ON EIEI.EVENT_TYPE = C.RECORD_ID

;



/* ************ */

/* Readmissions */

/* ************ */

DROP TABLE IF EXISTS #Base_Pop_ED_Readmit_All;



SELECT DISTINCT BP.PAT_ENC_CSN_ID

INTO #Base_Pop_ED_Readmit_All

FROM #Base_Pop BP

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PAT_ID = BP.PAT_ID AND (DEE.ARRIVAL_DTTM BETWEEN BP.ED_DEPARTURE_TIME AND DATEADD(HH,24,BP.ED_DEPARTURE_TIME))

;



/* *********************************** */

/* Readmissions (positive sepsis only) */

/* *********************************** */

DROP TABLE IF EXISTS #Base_Pop_ED_Readmit;



SELECT DISTINCT BP.PAT_ENC_CSN_ID

INTO #Base_Pop_ED_Readmit

FROM #ED_PositiveScores EPS

	INNER JOIN #Base_Pop BP ON EPS.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID AND EPS.FIRST_TIME_LINE=1

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PAT_ID = BP.PAT_ID AND (DEE.ARRIVAL_DTTM BETWEEN BP.ED_DEPARTURE_TIME AND DATEADD(HH,24,BP.ED_DEPARTURE_TIME))

;





/* *********** */

/* Final Query */

/* *********** */

SELECT

	[BasePop].PAT_MRN_ID		AS MRN

	,[BasePop].PAT_NAME			AS PATIENTS

	,[BasePop].[Ethnic Group]

	,[BasePop].[Race]

	,[BasePop].PAT_ENC_CSN_ID	AS CSN

	,[BasePop].AGE_MONTHS		AS [Age at ED Arrival (Months)]

	,[BasePop].AGE_YEARS		AS [Age at ED Arrival (Years)]

	,[BasePop].AGE_IN_DAYS		AS [Age In Days]



	,CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN 1 ELSE 0 END						AS [Age in Days Count]

	,CASE WHEN [BasePop].AGE_IN_DAYS <= 21 THEN '<= 21 Days' ELSE '> 21 Days' END	AS [Age in Days Indicator]



	,[BasePop].[Location]

	,[BasePop].DATE_STAMP

	,[BasePop].ADT_ARRIVAL_TIME		AS [ED Arrival Time]

	,[BasePop].TRIAGE_START_DTTM	AS [Traige Start Time]

	,[BasePop].TRIAGE_END_DTTM		AS [Traige Stop Time]



	,CONVERT(DATE, [BasePop].ADT_ARRIVAL_TIME)		AS [ED Arrival Date]	-- for PBI DateTable



	,CRFV.REASON_VISIT_NAME			AS [Chief Complaint]

	,RSN.AllEncReasons				AS [Other Visit Reasons]

	,[BasePop].ED_DEPARTURE_TIME	AS [ED Departure Time]

	,[BasePop].HOSP_ADMSN_TIME		AS [HOSP Admit Time]

	,[BasePop].HOSP_DISCH_TIME		AS [HOSP Discharge Time]

	,[BasePop].Disposition			AS [ED Disposition]



	,FIRST_ADMIT_DEPARTMENT.ADT_DEPARTMENT_NAME AS [First IP Department]



	,CASE WHEN SepsisScreened.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END AS [Sepsis Screened]



	,CASE	WHEN [#ED_PositiveScores].RECORDED_TIME IS NOT NULL

			THEN CASE	WHEN DATEPART(HOUR,[#ED_PositiveScores].RECORDED_TIME) >= 7 and DATEPART(HOUR,[#ED_PositiveScores].RECORDED_TIME) < 19 

						THEN 'AM (Day Shift)'

						ELSE 'PM (Night Shift)'

			END

	  END AS [First Positive Score AM/PM]



	,[#ED_PositiveScores].RECORDED_TIME		AS [First Positive Score Time]

	,[#ED_PositiveScores].MEAS_VALUE		AS [First Positive Score]

	,ALLSCORES.AllSepsis_Scores				AS [All Sepsis Scores]



	,ABXTimes.[Order date and time]

	,ABXTimes.[In VERIFY Queue Time]

	,ABXTimes.[Verified in Queue Time]

	,ABXTimes.[Queue Verified by]

	,ABXTimes.[Order Dispense date and time]

	,ABXTimes.[Rx Dispense Sent Time]



	/* Antibiotic (1st) */

	, ABX1.ABX_ADMIN_TIME	AS [First ABX Admin Time]

	, ABX1.[NAME]			AS [First ABX Name]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, ABX1.ABX_ADMIN_TIME)				AS [Arrival To First ABX Admin Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, ABX1.ABX_ADMIN_TIME)				AS [Triage To First ABX Admin Time]

	, DATEDIFF(MI, [#ED_PositiveScores]. RECORDED_TIME,ABX1.ABX_ADMIN_TIME)		AS [First Positive Screen To First ABX Time]



	/* Antibiotic (2nd) */

	, ABX2.ABX_ADMIN_TIME	AS [Second ABX Admin Time]

	, ABX2.[NAME]			AS [Second ABX Name]



	, DATEDIFF(MI, ABX1.ABX_ADMIN_TIME, ABX2.ABX_ADMIN_TIME)					AS [First ABX To Second ABX Admin Time]

	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, ABX2.ABX_ADMIN_TIME)		AS [First Positive Screen To Second ABX Time]

	

	/* OrderSet */

	, [#SSOrderSet].ORDER_DTTM AS [Order Set Time]

	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#SSOrderSet].ORDER_DTTM)	AS [Arrival To Order Set Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#SSOrderSet].ORDER_DTTM)	AS [Triage To Order Set Time]



	/* Bolus (1st) */

	, BPB1.BOLUS_ADMIN_TIME AS [Bolus 1 Admin Time]

	, BPB1.BOLUS_VOLUME		AS [Bolus 1 Volume]

	, CASE	WHEN BPB1.Medication = 'ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION' THEN 'Albumin 95%' ELSE BPB1.Medication END	AS [Bolus 1 Administered]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, BPB1.BOLUS_ADMIN_TIME) AS [Arrival To First Bolus Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, BPB1.BOLUS_ADMIN_TIME) AS [Triage To First Bolus Time]

	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, BPB1.BOLUS_ADMIN_TIME) AS [First Positive Screen To First Bolus Time]

	

	/* Bolus (2nd) */

	, BPB2.BOLUS_ADMIN_TIME AS [Bolus 2 Admin Time]

	, BPB2.BOLUS_VOLUME		AS [Bolus 2 Volume]

	, CASE	WHEN BPB2.Medication = 'ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION' THEN 'Albumin 95%' ELSE BPB2.Medication	END AS [Bolus 2 Administered]



	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, BPB2.BOLUS_ADMIN_TIME)	AS [First Positive Screen To Second Bolus Time]

	, DATEDIFF(MI, BPB1.BOLUS_ADMIN_TIME, BPB2.BOLUS_ADMIN_TIME)				AS [First Bolus To Second Bolus Time]

	

	/* Bolus (3rd) */

	, BPB3.BOLUS_ADMIN_TIME AS [Bolus 3 Admin Time]

	, BPB3.BOLUS_VOLUME		AS [Bolus 3 Volume]

	, CASE	WHEN BPB3.Medication = 'ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION' THEN 'Albumin 95%' ELSE BPB3.Medication	END AS [Bolus 3 Administered]



	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, BPB3.BOLUS_ADMIN_TIME)	AS [First Positive Screen To Third Bolus Time]

	, DATEDIFF(MI, BPB2.BOLUS_ADMIN_TIME, BPB3.BOLUS_ADMIN_TIME)				AS [Second Bolus To Third Bolus Time]



	, EW.EncWeight AS [PATIENTS Weight]



	/* Hypotension */

	, [#Hypotension].RECORDED_TIME	AS [First Hypotension Recorded Time]

	, [#Hypotension].MEAS_VALUE		AS [First Hypotension Value]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#Hypotension].RECORDED_TIME)	AS [Arrival To First Hypotension Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#Hypotension].RECORDED_TIME)	AS [Triage To First Hypotension Time]



	/* CVL Placement */

	, CVL.PLACEMENT_INSTANT AS [CVL Placement Time]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, CVL.PLACEMENT_INSTANT)	AS [Arrival To CLV Placement Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, CVL.PLACEMENT_INSTANT)	AS [Triage To CLV Placement Time]



	/* Presssors */

	, [#Pressors].TAKEN_TIME AS [Vasopressor Admin Time]

	, [#Pressors].MEDICATION AS [Vasopressor Administered]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#Pressors].TAKEN_TIME)					AS [Arrival To Vasopressor Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#Pressors].TAKEN_TIME)					AS [Triage To Vasopressor Time]

	, DATEDIFF(MI,[#ED_PositiveScores].RECORDED_TIME, [#Pressors].TAKEN_TIME)	AS [First Positive Screen To Vasopressor Time]



	/* SVO2 */

	, [#SVO2].MBOrderTime		AS [SVO2 Order Time]

	, [#SVO2].CollectionTime	AS [SVO2 Order Collection Time]

	, [#SVO2].ORD_VALUE			AS [SVO2 Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#SVO2].MBOrderTime)	AS [Arrival To SVO2 Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#SVO2].MBOrderTime)		AS [Triage To SVO2 Order Time]



	/* Lactic Acid */

	, [#LacticAcid].MBOrderTime		AS [Lactic Acid Order Time]

	, [#LacticAcid].CollectionTime	AS [Lactic Acid Order Collection Time]

	, [#LacticAcid].ORD_VALUE		AS [Lactic Acid Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#LacticAcid].MBOrderTime)	AS [Arrival To Lactic Acid Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#LacticAcid].MBOrderTime)		AS [Triage To Lactic Acid Order Time]



	/* Procalcitonin */

	, [#Procalcitonin].MBOrderTime		AS [Procalcitonin Order Time]

	, [#Procalcitonin].CollectionTime	AS [Procalcitonin Order Collection Time]

	, [#Procalcitonin].ORD_VALUE		AS [Procalcitonin Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [#Procalcitonin].MBOrderTime) AS [Arrival To PRO Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [#Procalcitonin].MBOrderTime)	AS [Triage To PRO Order Time]



	/* Blood Culture */

	, [BC].MBOrderTime		AS [Blood Culture Order Time]

	, [BC].CollectionTime	AS [Blood Culture Order Collection Time]

	, [BC].OrganismList		AS [Blood Culture Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [BC].MBOrderTime)	AS [Arrival To Blood Culture Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [BC].MBOrderTime)		AS [Triage To Blood Culture Order Time]



	/* Urine Culture */

	, [UC].MBOrderTime		AS [Urine Culture Order Time]

	, [UC].CollectionTime	AS [Urine Culture Order Collection Time]

	, [UC].OrganismList		AS [Urine Culture Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [UC].MBOrderTime)	AS [Arrival To Urine Culture Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [UC].MBOrderTime)		AS [Triage To Urine Culture Order Time]



	/* CSF Culture */

	, [CSF].MBOrderTime			AS [CSF Order Time]

	, [CSF].CollectionTime		AS [CSF Order Collection Time]

	, [CSF].OrganismList		AS [CSF Lab Result]



	, DATEDIFF(MI, [BasePop].ADT_ARRIVAL_TIME, [CSF].MBOrderTime)	AS [Arrival To CSF Order Time]

	, DATEDIFF(MI, [BasePop].TRIAGE_END_DTTM, [CSF].MBOrderTime)	AS [Triage To CSF Order Time]



	, [#ETT].PLACEMENT_INSTANT AS [First ETT Placement Time]

	, [#IV].PLACEMENT_INSTANT AS [First PIV Placement Time]

	, DATEDIFF(MI,[#ED_PositiveScores].RECORDED_TIME, [#IV].PLACEMENT_INSTANT) AS [First Positive Screen To First PIV Placement]

	, BE1.EVENT_TIME AS [ED IP Bed Requested Time]

	, BE2.EVENT_TIME AS [ED IP Bed Assigned Time]

	, DATEDIFF(MI,BE1.EVENT_TIME,BE2.EVENT_TIME) AS [Bed Request to Bed Assigned Time]

	, DATEDIFF(MI,BE1.EVENT_TIME, ICU.ED2ICUTime) AS [IP Bed Request to PICU Transfer Time]

	, [#ED2HEMONC].ED2HemoncTime

	, ICU.ED2ICUTime

	, GEN.ED2GENTime



	/* BPA */

	, [#BPA].ALT_ACTION_INST	AS [First BPA CLINICAL_ALERTS/Action Time]

	, [#BPA].ACTION_TAKE		AS [Action Taken]

	, [#BPA].OVERRIDDEN			AS [BPA Overridden]

	, [#BPA].SPEC_OVR_CMNT		AS [BPA Overridden Comment]

	, [#BPA].[NAME]				AS [BPA Action User]



	, [#SepsisAlertCancelled].SEPSIS_ALERT_CANC_TIME

	, [#SepsisAlertCancelled].SEPSIS_ALERT_CANC_BY

	, CASE WHEN [#BPA].ALT_ACTION_INST IS NOT NULL THEN ISNULL([#SepsisAlertCancelled].SEPSIS_ALERT_CANC_YN, 'N') END AS [SEPSIS_ALERT_CANC_YN]



	/* Blood pressure */

	, LAST_BP.RECORDED_TIME AS [Last Blood Pressure Time]

	, LAST_BP.MEAS_VALUE AS [Last Blood Pressure Value]

	, DATEDIFF(MI,LAST_BP.RECORDED_TIME, [#ED_PositiveScores].RECORDED_TIME) AS [Last BP to First Positive Score Time]

	, FIRST_BP.RECORDED_TIME AS [First Blood Pressure Time]

	, FIRST_BP.MEAS_VALUE AS [First Blood Pressure Value]

	, DATEDIFF(MI, [#ED_PositiveScores].RECORDED_TIME, FIRST_BP.RECORDED_TIME) AS [First Positive Score Time to First BP]



	, [LAST_BP_PERCENTILE].RECORDED_TIME	AS [Last BP Percentile Time]

	, [LAST_BP_PERCENTILE].MEAS_VALUE		AS [Last BP Percentile Value]

	, [FIRST_BP_PERCENTILE].RECORDED_TIME	AS [First BP Percentile Time]

	, [FIRST_BP_PERCENTILE].MEAS_VALUE		AS [First BP Percentile Value]



	, CASE WHEN ED_BORDER.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END	AS [ED Border PATIENTS]

	, CASE WHEN READMIT.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END	AS [Sepsis Pos ED Readmit in 24Hrs]

	, CASE WHEN READMITALL.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END AS [ED Readmit in 24Hrs]

	, CASE WHEN SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END		AS [IPSO Severe Sepsis Criteria Met]

	, CASE WHEN NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 'Y' ELSE 'N' END	AS [IPSO Non Severe Sepsis Criteria Met]

 

	/* Positive sepsis screen */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL THEN 1 ELSE 0 END	AS [Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL THEN 1 ELSE 0 END		AS [Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END		AS [Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL THEN 1 ELSE 0 END			AS [Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END		AS [Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL THEN 1 ELSE 0 END			AS [Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BC.MBOrderTime IS NOT NULL THEN 1 ELSE 0 END				AS [Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BC.MBOrderTime IS NULL THEN 1 ELSE 0 END					AS [Positive Sepsis and Blood Culture NOT Ordered]



	/* Negative sepsis screen */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL THEN 1 ELSE 0 END	AS [Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL THEN 1 ELSE 0 END		AS [Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END			AS [Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL THEN 1 ELSE 0 END				AS [Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL THEN 1 ELSE 0 END		AS [Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL THEN 1 ELSE 0 END			AS [Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BC.MBOrderTime IS NOT NULL THEN 1 ELSE 0 END				AS [Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BC.MBOrderTime IS NULL THEN 1 ELSE 0 END					AS [Negative Sepsis and Blood Culture NOT Ordered]



	/* IPSO severe (+) and Sepsis (+) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BC.MBOrderTime IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BC.MBOrderTime IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END					AS [IPSO SEVERE and Positive Sepsis and Blood Culture NOT Ordered]



	/* IPSO non-severe (+) and Sepsis (+) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO NON SEVERE and Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BC.MBOrderTime IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BC.MBOrderTime IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO NON SEVERE and Positive Sepsis and Blood Culture NOT Ordered]



	/* IPSO severe (+) and Sepsis (neg) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO SEVERE and Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BC.MBOrderTime IS NOT NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BC.MBOrderTime IS NULL AND SEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Negative Sepsis and Blood Culture NOT Ordered]



	/* IPSO non-severe (+) and Sepsis (neg) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO NON SEVERE and Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BC.MBOrderTime IS NOT NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO NON SEVERE and Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BC.MBOrderTime IS NULL AND NONSEVERE.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END					AS [IPSO NON SEVERE and Negative Sepsis and Blood Culture NOT Ordered]



	,RESCREEN.RECORDED_TIME AS [ReScreen After FPS]



	,CASE	WHEN DATEDIFF(MI,[#ED_PositiveScores].RECORDED_TIME,ABX1.ABX_ADMIN_TIME) <=60

				AND DATEDIFF(MI,[#ED_PositiveScores].RECORDED_TIME,BPB1.BOLUS_ADMIN_TIME) <=20

				AND RESCREEN.RECORDED_TIME IS NOT NULL

			THEN 1 

			ELSE 0 

	  END AS [FPS Bolus ABX ReScreen Compliance]



	,REPEATSCREEN.RECORDED_TIME AS [Repeat Screen before ED Departure]

	,GEN.[Gen Back To ICU Time]

	,GEN.[Gen Back To ICU Department]



	/* Added 2025.11.24 V_DEV004 */

	-- Septic Shock criteria; Logic from [reports].USP_Severe_Sepsis for consistency

	, CASE

		WHEN DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [ABX1].ABX_ADMIN_TIME) <= 6*60

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB1].BOLUS_ADMIN_TIME) <= 6*60

			AND ( DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB2].BOLUS_ADMIN_TIME) <= 6*60

					OR

				  DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [#Pressors].TAKEN_TIME) <= 6*60

				)

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [bcx_order01].[Blood Culture First Order Time]) <= 72*60

			AND ( [BPB3].BOLUS_ADMIN_TIME IS NOT NULL

					OR

				  [#Pressors].TAKEN_TIME IS NOT NULL

				)



		THEN 'Septic Shock'

		

		WHEN DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [ABX1].ABX_ADMIN_TIME) <= 6*60

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB1].BOLUS_ADMIN_TIME) <= 6*60

			AND ( DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [BPB2].BOLUS_ADMIN_TIME) <= 6*60

					OR

				  DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [#Pressors].TAKEN_TIME) <= 6*60

				)

			AND DATEDIFF(MINUTE, [BasePop].ADT_ARRIVAL_TIME, [bcx_order01].[Blood Culture First Order Time]) <= 72*60



		THEN 'Potential Septic Shock' 

		--ELSE 99	-- "Un-treated"

	  END AS [Septic Shock]



FROM #Base_Pop BasePop



	LEFT OUTER JOIN [EMRDB].[dbo].ENCOUNTER_VISIT_REASONS	CHIEF_CMPLNT	ON CHIEF_CMPLNT.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND CHIEF_CMPLNT.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].VISIT_REASONS	CRFV			ON CRFV.REASON_VISIT_ID = CHIEF_CMPLNT.ENC_REASON_ID



	LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING]		SEVERE		ON SEVERE.DATE_STAMP = [BasePop].DATE_STAMP AND SEVERE.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN [reportingDB].[reports].[NON_SEVERE_SEPSIS_STAGING]	NONSEVERE	ON NONSEVERE.DATE_STAMP = [BasePop].DATE_STAMP AND NONSEVERE.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID



	LEFT OUTER JOIN #Base_Pop_SepsisScores_ConCat	ALLSCORES		ON ALLSCORES.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #Base_Pop_Severe_ED_Scores		SepsisScreened	ON SepsisScreened.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID and SepsisScreened.TIME_LINE=1



	LEFT OUTER JOIN #ED_PositiveScores							ON [#ED_PositiveScores].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [#ED_PositiveScores].FIRST_TIME_LINE=1

	LEFT OUTER JOIN #BasePopABX						abx1		ON [BasePop].PAT_ENC_CSN_ID = ABX1.PAT_ENC_CSN_ID AND ABX1.TIME_LINE=1

	LEFT OUTER JOIN #BasePopABX						abx2		ON [BasePop].PAT_ENC_CSN_ID = ABX2.PAT_ENC_CSN_ID AND ABX2.TIME_LINE=2

	LEFT OUTER JOIN #SSOrderSet									ON [BasePop].PAT_ENC_CSN_ID = [#SSOrderSet].PAT_ENC_CSN_ID AND [#SSOrderSet].TIME_LINE=1

	LEFT OUTER JOIN #BasePopBolus					BPB1		ON [BasePop].PAT_ENC_CSN_ID = BPB1.PAT_ENC_CSN_ID AND BPB1.TIME_LINE=1

	LEFT OUTER JOIN #BasePopBolus					BPB2		ON [BasePop].PAT_ENC_CSN_ID = BPB2.PAT_ENC_CSN_ID AND BPB2.TIME_LINE=2

	LEFT OUTER JOIN #BasePopBolus					BPB3		ON [BasePop].PAT_ENC_CSN_ID = BPB3.PAT_ENC_CSN_ID AND BPB3.TIME_LINE=3

	LEFT OUTER JOIN #EncounterWeights				EW			ON [BasePop].PAT_ENC_CSN_ID = EW.PAT_ENC_CSN_ID AND EW.TIME_LINE=1

	LEFT OUTER JOIN #Hypotension								ON [BasePop].PAT_ENC_CSN_ID = [#Hypotension].PAT_ENC_CSN_ID AND [#Hypotension].TIME_LINE=1

	LEFT OUTER JOIN #ALLCVLTime						CVL			ON [BasePop].PAT_ENC_CSN_ID = CVL.PAT_ENC_CSN_ID AND CVL.TIME_LINE=1

	LEFT OUTER JOIN #Pressors									ON [BasePop].PAT_ENC_CSN_ID = [#Pressors].PAT_ENC_CSN_ID AND [#Pressors].TIME_LINE=1

	LEFT OUTER JOIN #SVO2										ON [BasePop].PAT_ENC_CSN_ID = [#SVO2].PAT_ENC_CSN_ID AND [#SVO2].TIME_LINE=1

	LEFT OUTER JOIN #LacticAcid									ON [BasePop].PAT_ENC_CSN_ID = [#LacticAcid].PAT_ENC_CSN_ID AND [#LacticAcid].TIME_LINE=1

	LEFT OUTER JOIN #Procalcitonin								ON [BasePop].PAT_ENC_CSN_ID = [#Procalcitonin].PAT_ENC_CSN_ID AND [#Procalcitonin].TIME_LINE=1

	LEFT OUTER JOIN #BloodCultureValue				BC			ON [BasePop].PAT_ENC_CSN_ID = [BC].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #UrineCultureValue				UC			ON [BasePop].PAT_ENC_CSN_ID = [UC].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #CsfCultureValue				CSF			ON [BasePop].PAT_ENC_CSN_ID = [CSF].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #ETT										ON [BasePop].PAT_ENC_CSN_ID = [#ETT].PAT_ENC_CSN_ID AND [#ETT].TIME_LINE=1

	LEFT OUTER JOIN #IV											ON [BasePop].PAT_ENC_CSN_ID = [#IV].PAT_ENC_CSN_ID AND [#IV].TIME_LINE=1

	LEFT OUTER JOIN #ED2HEMONC									ON [BasePop].PAT_ENC_CSN_ID = [#ED2HEMONC].PAT_ENC_CSN_ID AND [#ED2HEMONC].TIME_LINE=1

	LEFT OUTER JOIN #ED2ICU							ICU			ON [BasePop].PAT_ENC_CSN_ID = [ICU].PAT_ENC_CSN_ID AND [ICU].TIME_LINE=1

	LEFT OUTER JOIN #ED2GEN							GEN			ON [BasePop].PAT_ENC_CSN_ID = [GEN].PAT_ENC_CSN_ID AND [GEN].TIME_LINE=1

	LEFT OUTER JOIN #BPA										ON [BasePop].PAT_ENC_CSN_ID = [#BPA].PAT_ENC_CSN_ID AND [#BPA].TIME_LINE=1



	LEFT OUTER JOIN #BedEvents						BE1			ON [BE1].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [BE1].REQ_LINE=1 AND [BE1].TIME_LINE=1--BED REQUESTED

	LEFT OUTER JOIN #BedEvents						BE2			ON [BE2].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID AND [BE2].REQ_LINE=1 AND [BE2].TIME_LINE=2--BED ASSIGNED

	LEFT OUTER JOIN #Base_Pop_ED_Readmit_All		READMITALL	ON [READMITALL].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #Base_Pop_ED_Readmit			READMIT		ON [READMIT].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #Base_Pop_ENC_Reason			RSN			ON [RSN].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID



	LEFT OUTER JOIN #FirstPositiveOD_To_ABXAdminTime OD2ABX		ON OD2ABX.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #FirstABXAdminTimeDetails		ABXTimes	ON ABXTimes.PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

	LEFT OUTER JOIN #SepsisAlertCancelled						ON [BasePop].PAT_ENC_CSN_ID = [#SepsisAlertCancelled].PAT_ENC_CSN_ID AND [#SepsisAlertCancelled].TIME_LINE=1



	LEFT OUTER JOIN (

		SELECT PAT_ENC_CSN_ID, min(MBOrderTime) AS [Blood Culture First Order Time]

		FROM #BloodCultureValue

		GROUP BY PAT_ENC_CSN_ID

	) bcx_order01 ON [BasePop].PAT_ENC_CSN_ID = [bcx_order01].PAT_ENC_CSN_ID



	OUTER APPLY

	(

		SELECT TOP 1 [#Base_Pop_Severe_ED_Scores].RECORDED_TIME

		FROM #Base_Pop_Severe_ED_Scores

		WHERE 1=1

			AND [#Base_Pop_Severe_ED_Scores].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

			AND [#ED_PositiveScores].FIRST_TIME_LINE = 1

			AND ([#Base_Pop_Severe_ED_Scores].RECORDED_TIME > [#ED_PositiveScores].RECORDED_TIME AND [#Base_Pop_Severe_ED_Scores].RECORDED_TIME <= DATEADD(MI, 90, [#ED_PositiveScores].RECORDED_TIME))

		ORDER BY [#ED_PositiveScores].RECORDED_TIME DESC

	) RESCREEN



	OUTER APPLY

	(

		SELECT TOP 1 [#Base_Pop_Severe_ED_Scores].RECORDED_TIME

		FROM #Base_Pop_Severe_ED_Scores

		WHERE 1=1

			AND [#Base_Pop_Severe_ED_Scores].PAT_ENC_CSN_ID = [BasePop].PAT_ENC_CSN_ID

			AND ([#Base_Pop_Severe_ED_Scores].RECORDED_TIME >  DATEADD(MI, -60, [BasePop].ED_DEPARTURE_TIME) AND [#Base_Pop_Severe_ED_Scores].RECORDED_TIME < [BasePop].ED_DEPARTURE_TIME)

		ORDER BY [#Base_Pop_Severe_ED_Scores].RECORDED_TIME DESC

	) REPEATSCREEN



	OUTER APPLY

	(

		SELECT TOP 1 [V_PATIENT_LOCATION_HISTORY].ADT_DEPARTMENT_NAME

		FROM [EMRDB].[dbo].V_PATIENT_LOCATION_HISTORY

		WHERE 1=1

			AND [V_PATIENT_LOCATION_HISTORY].ADT_DEPARTMENT_ID IS NOT NULL

			AND [V_PATIENT_LOCATION_HISTORY].PAT_ENC_CSN = [BasePop].PAT_ENC_CSN_ID 

			AND [V_PATIENT_LOCATION_HISTORY].IN_DTTM >= [BasePop].ED_DEPARTURE_TIME

		ORDER BY [V_PATIENT_LOCATION_HISTORY].IN_DTTM ASC

	) FIRST_ADMIT_DEPARTMENT



	/* Previous blood pressure (up to 30 minutes prior to positive screen) */

	OUTER APPLY

	(

		SELECT TOP 1 

			[FLOWSHEET_MEASUREMENTS].RECORDED_TIME

			, [FLOWSHEET_MEASUREMENTS].MEAS_VALUE

			, [FLOWSHEET_MEASUREMENTS].FLO_MEAS_ID

		FROM [EMRDB].[dbo].HOSPITAL_ENCOUNTERS

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS	ON [HOSPITAL_ENCOUNTERS].INPATIENT_DATA_ID = [FLOWSHEET_RECORDS].INPATIENT_DATA_ID

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS	ON [FLOWSHEET_RECORDS].FSD_ID = [FLOWSHEET_MEASUREMENTS].FSD_ID	



		WHERE 1=1

			AND [HOSPITAL_ENCOUNTERS].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

			AND [FLOWSHEET_MEASUREMENTS].FLO_MEAS_ID = '95'	-- Blood Pressure

			AND [FLOWSHEET_MEASUREMENTS].RECORDED_TIME BETWEEN DATEADD(MI, -30, [#ED_PositiveScores].RECORDED_TIME) AND [#ED_PositiveScores].RECORDED_TIME

		ORDER BY [FLOWSHEET_MEASUREMENTS].RECORDED_TIME DESC	

	) LAST_BP



	/* Previous blood pressure percentile (up to 30 minutes prior to positive screen) */

	OUTER APPLY

	(

		SELECT TOP 1 

			[FLOWSHEET_MEASUREMENTS].RECORDED_TIME

			, [FLOWSHEET_MEASUREMENTS].MEAS_VALUE

		FROM [EMRDB].[dbo].HOSPITAL_ENCOUNTERS

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS	ON [HOSPITAL_ENCOUNTERS].INPATIENT_DATA_ID = [FLOWSHEET_RECORDS].INPATIENT_DATA_ID

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS	ON [FLOWSHEET_RECORDS].FSD_ID = [FLOWSHEET_MEASUREMENTS].FSD_ID	

		WHERE 1=1

			AND [HOSPITAL_ENCOUNTERS].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

			AND [FLOWSHEET_MEASUREMENTS].FLO_MEAS_ID IN (

				'9001140203'	-- R PED GIRLS SYSTOLIC BP PERCENTILE

				,'9001140205'	-- R PED BOYS SYSTOLIC BP PERCENTILE 

				)

			AND [FLOWSHEET_MEASUREMENTS].RECORDED_TIME BETWEEN DATEADD(MI, -30, [#ED_PositiveScores].RECORDED_TIME) AND [#ED_PositiveScores].RECORDED_TIME

		ORDER BY [FLOWSHEET_MEASUREMENTS].RECORDED_TIME DESC	

	) LAST_BP_PERCENTILE



	/* First blood pressure (up to 30 minutes after positive screen) */

	OUTER APPLY

	(

		SELECT TOP 1 

			[FLOWSHEET_MEASUREMENTS].RECORDED_TIME

			, [FLOWSHEET_MEASUREMENTS].MEAS_VALUE

		FROM [EMRDB].[dbo].HOSPITAL_ENCOUNTERS

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS	ON [HOSPITAL_ENCOUNTERS].INPATIENT_DATA_ID = [FLOWSHEET_RECORDS].INPATIENT_DATA_ID

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS	ON [FLOWSHEET_RECORDS].FSD_ID = [FLOWSHEET_MEASUREMENTS].FSD_ID	

		WHERE 1=1

			AND [HOSPITAL_ENCOUNTERS].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

			AND [FLOWSHEET_MEASUREMENTS].FLO_MEAS_ID = '95'	-- Blood Pressure

			AND [FLOWSHEET_MEASUREMENTS].RECORDED_TIME BETWEEN [#ED_PositiveScores].RECORDED_TIME AND DATEADD(MI, 30, [#ED_PositiveScores].RECORDED_TIME)

		ORDER BY [FLOWSHEET_MEASUREMENTS].RECORDED_TIME DESC			

	) FIRST_BP



	/* First blood pressure (up to 30 minutes after positive screen) */

	OUTER APPLY

	(

		SELECT TOP 1 

			[FLOWSHEET_MEASUREMENTS].RECORDED_TIME

			, [FLOWSHEET_MEASUREMENTS].MEAS_VALUE

		FROM [EMRDB].[dbo].HOSPITAL_ENCOUNTERS

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_RECORDS	ON [HOSPITAL_ENCOUNTERS].INPATIENT_DATA_ID = [FLOWSHEET_RECORDS].INPATIENT_DATA_ID

			INNER JOIN [EMRDB].[dbo].FLOWSHEET_MEASUREMENTS	ON [FLOWSHEET_RECORDS].FSD_ID = [FLOWSHEET_MEASUREMENTS].FSD_ID	

		WHERE 1=1

			AND [HOSPITAL_ENCOUNTERS].PAT_ENC_CSN_ID = [#ED_PositiveScores].PAT_ENC_CSN_ID

			AND [FLOWSHEET_MEASUREMENTS].FLO_MEAS_ID IN (

				'9001140203'	-- R PED GIRLS SYSTOLIC BP PERCENTILE

				,'9001140205'	-- R PED BOYS SYSTOLIC BP PERCENTILE 

				)

			AND [FLOWSHEET_MEASUREMENTS].RECORDED_TIME BETWEEN [#ED_PositiveScores].RECORDED_TIME AND DATEADD(MI, 30, [#ED_PositiveScores].RECORDED_TIME)

		ORDER BY [FLOWSHEET_MEASUREMENTS].RECORDED_TIME DESC			

	) FIRST_BP_PERCENTILE



	/* ED boarder PATIENTS */

	LEFT OUTER JOIN

	(

		SELECT DISTINCT [HOSPITAL_ENCOUNTERS].PAT_ENC_CSN_ID

		FROM [EMRDB].[dbo].HOSPITAL_ENCOUNTERS

			INNER JOIN [EMRDB].[dbo].ED_PATIENT_INFO		 ON [ED_PATIENT_INFO].PAT_ENC_CSN_ID = [HOSPITAL_ENCOUNTERS].PAT_ENC_CSN_ID

			INNER JOIN [EMRDB].[dbo].ED_EVENT_INFO	 ON [ED_EVENT_INFO].EVENT_ID = [ED_PATIENT_INFO].EVENT_ID 

															AND [ED_EVENT_INFO].EVENT_TYPE IN ('2600000007')--ED BOARDER PATIENTS

	) ED_BORDER ON [BasePop].PAT_ENC_CSN_ID = ED_BORDER.PAT_ENC_CSN_ID

;
GO

-- ==== reports/USP_RPTS_IP_SEPSIS.sql ====
/*

MODIFICATION DATE: 05.16.2019

MODIFIED BY: V_DEV001

MODIFICATION: PROCEDURE_ORDERS.PROC_CODE IS DEPRICATED AS OF APRIL 2019. REPLACING IT WITH PROCEDURE IDS.

	--OP.PROC_CODE DEPRICATED AS OF 04.15.2019--REPLACING WITH THE PROC IDS INSTEAD IN THE LINE BELOW

	--AND OP.PROC_CODE IN ('LAB006','LAB007') AND OP.SPECIMEN_SOURCE_C=304 



MODIFICATION DATE: 08.08.2019

MODIFIED BY: V_DEV001

MODIFICATION: MAR_ACTION_C changed from int to varchar



MODIFICATION DATE:10.01.2019

MODIFIED BY: V_DEV001

MODIFICATION: Added new Sepsis Organ Dysfunction Score Flowsheet ID '9000002644'



MODIFICATION DATE:11.25.2019

MODIFIED BY: V_DEV002

MODIFICATION: Added Sepsis Huddle Note 



MODIFICATION DATE:12.09.2019

MODIFIED BY: V_DEV001

MODIFICATION: Added ED First Positive Score, ED LOS & Took care of the duplicate entries. Duplicate entries were becasue of the time filter we used for OD Scores. Instead of OD Scores being captured between @StartDate and @EndDate, modified to the score time to check Department's IN_DTTM and OUT_DTTM.



MODIFICATION DATE:02.06.2020

MODIFIED BY: V_DEV001

MODIFICATION: Add a flag to check if the PATIENTS is IPSO Severe Sepsis PATIENTS



MODIFICATION DATE:10.29.2020

MODIFIED BY: V_DEV001

MODIFICATION: SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;



MODIFICATION DATE:2.3.2021

MODIFIED BY: V_DEV002

MODIFICATION: TKT-001 -- add Sepsis Score day/night shift



MODIFICATION DATE:03.01.2021

MODIFIED BY: V_DEV001

MODIFICATION: Change Hudlle time from -30 to 120 TO -30 to 180



MODIFICATION DATE:03.24.2021

MODIFIED BY: V_DEV001

MODIFICATION: TKT-003 -- add PATIENTS's race and ethnic group info



MODIFICATION DATE:11.16.2021

MODIFIED BY: V_DEV001

MODIFICATION: TKT-002 -- add Sepsis CLINICAL_ALERTS Activation and related documentation



MODIFICATION DATE:06.20.2022

MODIFIED BY: V_DEV001

MODIFICATION: Address transfers due to NEW_UNIT

*/

--EXEC [reports].[USP_IP_Sepsis]'MB-3','ME-3'



CREATE   PROCEDURE [reports].[USP_IP_SEPSIS]

@StartDate VARCHAR(20) = NULL,

@EndDate VARCHAR(20) = NULL



AS



SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

	--BEGIN TRY

	SET NOCOUNT ON;

	

	DECLARE @dStartDate DATE

	DECLARE @dEndDate DATE

	DECLARE @dTestRun BIT

	

	IF @StartDate IS NULL OR @StartDate = ''

		--SET @dStartDate = EMRDB.[dbo].[fn_parse_date]('mb-95') --('MB-12')--DEFAULTING TO PREVIOUS MONTH

		SET @dStartDate = EMRDB.[dbo].[fn_parse_date]('2018-01-01') --('MB-12')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @dStartDate = EMRDB.[dbo].[fn_parse_date](@StartDate)

	

	IF @EndDate IS NULL OR @EndDate = ''

		--SET @dEndDate = EMRDB.[dbo].[fn_parse_date]('ME-95')--DEFAULTING TO PREVIOUS MONTH

		SET @dEndDate = EMRDB.[dbo].[fn_parse_date]('ME-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @dEndDate = EMRDB.[dbo].[fn_parse_date](@EndDate)





IF OBJECT_ID(N'tempdb..#Main') IS NOT NULL DROP TABLE #Main;

SELECT DISTINCT

	PEH.PAT_ENC_CSN_ID

	, PEH.PAT_ID

	, PAT.PAT_MRN_ID

	, PAT.PAT_NAME

	, ZEG.NAME AS [Ethnic Group]

	, ZPR.NAME AS [Race]

	, PEH.INPATIENT_DATA_ID

	, PEH.ADT_ARRIVAL_TIME

	, PEH.HOSP_ADMSN_TIME

	, PEH.HOSP_DISCH_TIME

	, PEH.INP_ADM_DATE

	, PEH.ED_DEPARTURE_TIME

	, ZDD.NAME AS [Disposition]

	, DATEDIFF(MM,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,PEH.HOSP_ADMSN_TIME)) + DATENAME(YEAR, CONVERT(DATE, PEH.HOSP_ADMSN_TIME)) AS DATE_STAMP

	, DATEDIFF(HH, PEH.HOSP_ADMSN_TIME, PEH.HOSP_DISCH_TIME) AS LOS_HRS

INTO 

	#Main

FROM EMRDB.dbo.V_HOSPITAL_TRANSACTIONS HTR

	INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON HTR.PAT_ENC_CSN_ID = PEH.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

	LEFT OUTER JOIN EMRDB.dbo.REF_DISCHARGE_DISPOSITION ZDD ON ZDD.DISCH_DISP_C = PEH.DISCH_DISP_C

	LEFT OUTER JOIN EMRDB.dbo.REF_ETHNIC_GROUP ZEG ON ZEG.ETHNIC_GROUP_C = PAT.ETHNIC_GROUP_C

	LEFT OUTER JOIN EMRDB.dbo.PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PAT_ID = PAT.PAT_ID AND RACE.LINE=1

	LEFT OUTER JOIN EMRDB.dbo.REF_PATIENT_RACE ZPR ON ZPR.PATIENT_RACE_C = RACE.PATIENT_RACE_C

	LEFT OUTER JOIN EMRDB.dbo.REF_ED_DISPOSITION ZED ON ZED.ED_DISPOSITION_C = peh.ED_DISPOSITION_C

WHERE

	PEH.INP_ADM_DATE IS NOT NULL

	AND CONVERT(DATE,HTR.SERVICE_DATE) BETWEEN @dStartDate AND @dEndDate



CREATE NONCLUSTERED INDEX IX_InpDataID  ON #Main (INPATIENT_DATA_ID);

CREATE NONCLUSTERED INDEX IX_PatID  ON #Main (PAT_ID);



--CHIEF COMPLIANT

IF OBJECT_ID(N'tempdb..#Base_Pop_ENC_Reason') IS NOT NULL DROP TABLE #Base_Pop_ENC_Reason;

SELECT

	sub.PAT_ENC_CSN_ID,

	string_agg(EDG.DX_NAME,'% ') AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM  #Main sub

	INNER JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES PED ON PED.PAT_ENC_CSN_ID = SUB.PAT_ENC_CSN_ID AND PED.LINE>1

	INNER JOIN EMRDB.dbo.DIAGNOSES EDG ON EDG.DX_ID = PED.DX_ID

group by sub.PAT_ENC_CSN_ID





--SELECT * FROM #Base_Pop_ENC_Reason

IF OBJECT_ID(N'tempdb..#EncounterWeights') IS NOT NULL DROP TABLE #EncounterWeights;

SELECT

	A.PAT_ENC_CSN_ID

	, CAST(ROUND(CONVERT(FLOAT, MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

	, ROW_NUMBER() OVER(PARTITION BY A.PAT_ENC_CSN_ID ORDER BY C.RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#EncounterWeights

FROM #Main A

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS B ON A.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS C ON B.FSD_ID = C.FSD_ID AND  C.FLO_MEAS_ID='94'



/*GETTING ENCOUNTERS WITHIN GIVEN DATE RANGES SO WE DON'T HAVE TO QUERY ON WHOLE DATABASE FOR EACH CRITERIA*/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT 

	#Main.PAT_ENC_CSN_ID

	, #Main.PAT_ID

	, ADT.ADT_DEPARTMENT_ID

	, ADT.ADT_DEPARTMENT_NAME

	, CVS.CODE_DESC AS DEPARTMENT_ROLLUP

	, ADT.IN_DTTM

	, ADT.OUT_DTTM

	, #Main.INPATIENT_DATA_ID

	, #Main.AGE_MONTHS

	, #Main.AGE_YEARS

	, #Main.ADT_ARRIVAL_TIME

	, #Main.ED_DEPARTURE_TIME

INTO 

	#Base_Pop

FROM #Main

INNER JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = #Main.PAT_ID

cross apply (

			SELECT

				ADTIN.PAT_ENC_CSN_ID,

				ADTIN.EFFECTIVE_TIME AS IN_DTTM,

				COALESCE(ADTOUT.EFFECTIVE_TIME,GETDATE()) AS OUT_DTTM,

				case when (CONVERT(DATE,ADTIN.EFFECTIVE_TIME) between '2022-03-29' and '2022-06-09')/*******************************************************************

																			NEW_UNIT construction 4/4-6/3:

																			NEW_UNIT patients moved to TCU; TCU patients moved to NICU C BED 1-10

																			*******************************************************************/

						and bed.bed_id in ( '20010800423011',

								'20010800423021',

								'20010800423031',

								'20010800423041',

								'20010800423051',

								'20010800423061',

								'20010800423071',

								'20010800423081',

								'20010800423091',

								'20010800423101'

								)

					then 200108013 else ADTIN.DEPARTMENT_ID end AS ADT_DEPARTMENT_ID,

				case when (CONVERT(DATE,ADTIN.EFFECTIVE_TIME) between '2022-03-29' and '2022-06-09')

						and bed.bed_id in ( '20010800423011',

								'20010800423021',

								'20010800423031',

								'20010800423041',

								'20010800423051',

								'20010800423061',

								'20010800423071',

								'20010800423081',

								'20010800423091',

								'20010800423101'

								)

					then 'MAIN 4 TOWER EAST' else DEP.DEPARTMENT_NAME end ADT_DEPARTMENT_NAME

			FROM

				EMRDB..HOSPITAL_ENCOUNTERS HSP

				INNER JOIN EMRDB..ADT_EVENTS ADTIN ON ADTIN.PAT_ENC_CSN_ID = HSP.PAT_ENC_CSN_ID

				LEFT OUTER JOIN EMRDB..ADT_EVENTS ADTOUT ON ADTIN.NEXT_OUT_EVENT_ID = ADTOUT.EVENT_ID

				LEFT OUTER JOIN EMRDB..DEPARTMENTS DEP ON ADTIN.DEPARTMENT_ID = DEP.DEPARTMENT_ID

				left outer join EMRDB..BED_CONFIG bed on bed.BED_CSN_ID = adtin.BED_CSN_ID

			WHERE

				HSP.PAT_ENC_CSN_ID = #Main.PAT_ENC_CSN_ID

				and ADTIN.EVENT_TYPE_C IN (1, 3) --Only look at "in" events (Admission and Transfer In, LOA Return)

				AND ADTIN.EVENT_SUBTYPE_C <> 2 --Exclude deleted/canceled events

)ADT

INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = ADT.adt_DEPARTMENT_ID

			AND CVS.VALUE_SET_ID = 3031 --DEPARTMENT ROLL UP



--POSITIVE ED SEPSIS SCORES & ED LOS

IF OBJECT_ID(N'tempdb..#Base_Pop_Severe_ED_Scores') IS NOT NULL DROP TABLE #Base_Pop_Severe_ED_Scores;

SELECT

	BP.PAT_ENC_CSN_ID

	, CEILING(CONVERT(FLOAT,DATEDIFF(MI, BP.ADT_ARRIVAL_TIME,BP.ED_DEPARTURE_TIME))/60) HoursInED--CHECK WITH STEPHANIE ON 

	, BP.ADT_ARRIVAL_TIME

	, IFM.MEAS_VALUE

	, IFM.RECORDED_TIME

	, BP.ED_DEPARTURE_TIME

	, ROW_NUMBER() OVER(PARTITION BY BP.PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#Base_Pop_Severe_ED_Scores 

FROM #Main BP 

	INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID --and bp.PAT_ENC_CSN_ID=1016405505 

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = PEH.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID and

		IFM.FLO_MEAS_ID IN ('9000161709','9000002613')--SEPSIS SCORE--ADDED NEW ED SEPSIS SCORE 9000002613 ON 10.01.2019

		and (IFM.RECORDED_TIME <=  BP.ED_DEPARTURE_TIME)



IF OBJECT_ID(N'tempdb..#EDPosScore_EDLOS') IS NOT NULL DROP TABLE #EDPosScore_EDLOS;

SELECT

	PAT_ENC_CSN_ID

	, HoursInED

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO 

	#EDPosScore_EDLOS

FROM 

	#Base_Pop_Severe_ED_Scores

WHERE

	MEAS_VALUE > 4

--POSITIVE SEPSIS SCORES

IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT

	BP.PAT_ENC_CSN_ID

	, BP.ADT_DEPARTMENT_ID

	, BP.ADT_DEPARTMENT_NAME

	, BP.IN_DTTM

	, BP.OUT_DTTM

	, IFM.MEAS_VALUE

	, IFM.RECORDED_TIME

	, Huddle_Note.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP]

	, Huddle_Note.[Huddle Date]

	, Huddle_Note.[Huddle Time]

	, Huddle_Note.[PATIENTS Assessed by MD/PNP]

	, Huddle_Note.[Physician Name]

	, Huddle_Note.[Additional Orders Received/Placed by MD/PNP]

	, ALERTNOTACTIVATED.[CLINICAL_ALERTS Not Activated Reason]

	, ALERTNOTACTIVATED.[CLINICAL_ALERTS Not Activated Comment]

	, ALERTACTIVATED.[CLINICAL_ALERTS Activated Comment]

	, ROW_NUMBER() OVER(PARTITION BY BP.PAT_ENC_CSN_ID, BP.ADT_DEPARTMENT_ID, BP.IN_DTTM ORDER BY ifm.RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#Base_Pop_OD_Scores 

FROM #Base_Pop BP 

	INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON PEH.INPATIENT_DATA_ID = IFR.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

	LEFT OUTER JOIN

		(

			SELECT

				IFR.INPATIENT_DATA_ID, IFM_ALERTNOTACTIVATED.FSD_ID, IFM_ALERTNOTACTIVATED.RECORDED_TIME, IFM_ALERTNOTACTIVATED.MEAS_VALUE AS [CLINICAL_ALERTS Not Activated Reason], IFM_ALERTNOTACTIVATED.MEAS_COMMENT as [CLINICAL_ALERTS Not Activated Comment]

			FROM EMRDB.dbo.FLOWSHEET_RECORDS IFR

				INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM_ALERTNOTACTIVATED ON IFM_ALERTNOTACTIVATED.FSD_ID = IFR.FSD_ID

			WHERE

				IFM_ALERTNOTACTIVATED.FLO_MEAS_ID='9000003159'

		)ALERTNOTACTIVATED ON ALERTNOTACTIVATED.INPATIENT_DATA_ID = IFR.INPATIENT_DATA_ID

			AND ALERTNOTACTIVATED.FSD_ID = IFR.FSD_ID

			AND ALERTNOTACTIVATED.RECORDED_TIME = IFM.RECORDED_TIME

		LEFT OUTER JOIN

		(

			SELECT

				ALT.ALT_ID,

				ALT.PAT_CSN,

				HIS.ALT_ACTION_INST,

				COALESCE(HIS.SPEC_OVR_CMNT,' ')+ RSN.NAME [CLINICAL_ALERTS Activated Comment]

			FROM EMRDB.dbo.CLINICAL_ALERTS ALT

				INNER JOIN EMRDB.dbo.ALERT_HISTORY HIS ON HIS.ALT_ID = ALT.ALT_ID

				INNER JOIN EMRDB.dbo.REF_ALERT_OVERRIDE_REASONS RSN ON RSN.ALRT_SP_OVR_RSN_C = HIS.SPEC_OVR_RSN_C

			WHERE ALT.BPA_LOCATOR_ID=900400001--BASE 2019 HS OD SCORE SEPSIS >2 [900400001]

		)ALERTACTIVATED ON ALERTACTIVATED.PAT_CSN = PEH.PAT_ENC_CSN_ID

			AND ALERTACTIVATED.ALT_ACTION_INST = IFM.RECORDED_TIME

	--huddle notes within 30 minutes before or 120 minutes after OD Score

	outer apply

		(select a.INPATIENT_DATA_ID

			,a.OD_SCORE_RECORDED_TIME

			,max(case WHEN a.FLO_MEAS_ID = '9000002705' THEN a.MEAS_VALUE end) as "Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP"

			,max(CASE WHEN a.FLO_MEAS_ID = '9000002732' THEN try_cast(DATEADD(day,try_cast(a.MEAS_VALUE as int),'1840-12-31') as date) end) as "Huddle Date"

			,max(case WHEN a.FLO_MEAS_ID = '9000002733' THEN try_cast(DATEADD(second,try_cast(a.MEAS_VALUE as int),'1840-12-31') as time) end) as "Huddle Time"

			,max(case WHEN a.FLO_MEAS_ID = '9000002706' THEN a.MEAS_VALUE end) as "PATIENTS Assessed by MD/PNP"

			,max(case WHEN a.FLO_MEAS_ID = '9000002734' THEN a.MEAS_VALUE end) as "Physician Name"

			,max(case WHEN a.FLO_MEAS_ID = '9000002707' THEN a.MEAS_VALUE end) as "Additional Orders Received/Placed by MD/PNP"

			from

			(

			select IFR.INPATIENT_DATA_ID

			,IFM.RECORDED_TIME as OD_SCORE_RECORDED_TIME

			,FLOWSHEET_MEASUREMENTS.FLO_MEAS_ID

			,FLOWSHEET_MEASUREMENTS.RECORDED_TIME

			,FLOWSHEET_MEASUREMENTS.MEAS_VALUE

			,row_number() over (partition by FLOWSHEET_RECORDS.INPATIENT_DATA_ID, IFM.RECORDED_TIME, FLOWSHEET_MEASUREMENTS.FLO_MEAS_ID order by FLOWSHEET_MEASUREMENTS.RECORDED_TIME) rownumber

				from  EMRDB.dbo.FLOWSHEET_RECORDS

				INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS ON FLOWSHEET_RECORDS.FSD_ID = FLOWSHEET_MEASUREMENTS.FSD_ID

				where FLOWSHEET_RECORDS.INPATIENT_DATA_ID = IFR.INPATIENT_DATA_ID

				and datediff(minute,IFM.RECORDED_TIME,FLOWSHEET_MEASUREMENTS.RECORDED_TIME) between -30 and 180--WAS -120 UNTIL 03.01.2021 

				and FLOWSHEET_MEASUREMENTS.FLO_MEAS_ID in ('9000002705','9000002732','9000002733','9000002706','9000002734','9000002707')

				and FLOWSHEET_MEASUREMENTS.MEAS_VALUE is not null

			) a

			where a.rownumber = 1

			group by a.INPATIENT_DATA_ID, a.OD_SCORE_RECORDED_TIME

		) Huddle_Note

WHERE 

	IFM.FLO_MEAS_ID IN ('9000161711','9000002644') --ORGAN DYSFUNCTION SCORE

	--and IFM.RECORDED_TIME BETWEEN @dStartDate AND @dEndDate--BP.IN_DTTM AND BP.OUT_DTTM--this is because a paitient's IN DTTM could be in the current month and out DTTM could be in next month. Per Stakeholder A, we want to look for scores documented in the same time frame.

	AND IFM.RECORDED_TIME BETWEEN BP.IN_DTTM AND COALESCE(BP.OUT_DTTM,GETDATE())





IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, CASE

		WHEN 

			B.AGE_MONTHS < 2 AND Syst.SYSTOLIC < 65

			OR

			(B.AGE_MONTHS >= 2 AND B.AGE_MONTHS < 12) AND Syst.SYSTOLIC < 70

			OR

			(B.AGE_YEARS >= 1 AND B.AGE_YEARS < 2) AND Syst.SYSTOLIC < 80

			OR

			(B.AGE_YEARS >= 2 AND B.AGE_YEARS < 6) AND Syst.SYSTOLIC < 90

			OR

			(B.AGE_YEARS >= 6 AND B.AGE_YEARS < 13) AND Syst.SYSTOLIC < 100

			OR

			B.AGE_YEARS >= 13 AND Syst.SYSTOLIC < 110

		THEN Syst.MEAS_VALUE--IFM.RECORDED_TIME

		ELSE NULL

	END AS MEAS_VALUE

	, Syst.RECORDED_TIME

	, Syst.SYSTOLIC

INTO 

	#Hypotension 

FROM

	#Base_Pop B

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	cross apply

	(

		select ifm.fsd_id, try_cast(LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) as int) AS SYSTOLIC, IFM.MEAS_VALUE, ifm.RECORDED_TIME

		from 

		EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM 

		where IFM.FSD_ID = IFR.FSD_ID AND IFM.FLO_MEAS_ID = '95' 

		AND IFM.MEAS_VALUE IS NOT NULL

		and IFM.RECORDED_TIME IS NOT NULL

	)Syst





IF OBJECT_ID(N'tempdb..#ODHYPO') IS NOT NULL DROP TABLE #ODHYPO;

SELECT

	CASE WHEN LASTHYPO.MEAS_VALUE IS NOT NULL THEN LASTHYPO.RECORDED_TIME ELSE NULL END [LAST Hypotension Time],

	LASTHYPO.MEAS_VALUE [LAST Hypotension Value],

	CASE WHEN LASTHYPO.MEAS_VALUE IS NOT NULL AND (LASTHYPO.RECORDED_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM) THEN 'Y' ELSE 'N' END AS [LAST Hypotension taken in Dept Y/N],

	A.*,

	CASE WHEN FIRSTHYPO.MEAS_VALUE IS NOT NULL THEN FIRSTHYPO.RECORDED_TIME ELSE NULL END [FIRST Hypotension Time],

	FIRSTHYPO.MEAS_VALUE [FIRST Hypotension Value],

	CASE WHEN FIRSTHYPO.MEAS_VALUE IS NOT NULL AND (FIRSTHYPO.RECORDED_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM) THEN 'Y' ELSE 'N' END AS [FIRST Hypotension taken in Dept Y/N]

INTO #ODHYPO

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 HYPO.RECORDED_TIME, HYPO.MEAS_VALUE FROM #Hypotension HYPO

		WHERE HYPO.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND HYPO.RECORDED_TIME<A.RECORDED_TIME

		ORDER BY HYPO.RECORDED_TIME DESC

	)LASTHYPO

	OUTER APPLY

	(

		SELECT TOP 1 HYPO.RECORDED_TIME, HYPO.MEAS_VALUE FROM #Hypotension HYPO

		WHERE HYPO.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND HYPO.RECORDED_TIME>=A.RECORDED_TIME

		ORDER BY HYPO.RECORDED_TIME ASC

	)FIRSTHYPO



------------------------------------------------------END OF HYPO------------------------------------------------------------------

------------------------------------------------------ABX------------------------------------------------------------------

-- All encounters from #Base_pop where ABX was administered

IF OBJECT_ID(N'tempdb..#BasePopABX') IS NOT NULL DROP TABLE #BasePopABX;

SELECT

	OM.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, CM.NAME

	, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

	, MAI.SIG AS BOLUS_VOLUME

INTO

	#BasePopABX

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM	ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID AND CM.THERA_CLASS_C = 11 --Antibiotics

	INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

WHERE

	MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

--VALUES BELOW ADDED TO THE CODE ON STEPHANIE'S REQUEST DURING VALIDATION.

	AND CM.ROUTE NOT IN ('intratympanic'

						, 'intraocular'

						, 'Apply externally'

						, 'ophthalmic'

						, 'oral'

						, 'Topical'

						, 'nasal'

						, 'intramuscular'

						, 'otic'

						, 'intravitreal'

						, 'vaginal'

						, 'inhalation'

						, 'intravenous'

						)							



IF OBJECT_ID(N'tempdb..#ODABX') IS NOT NULL DROP TABLE #ODABX;

SELECT

	LASTABX.ABX_ADMIN_TIME LASTABX_TIME,

	LASTABX.NAME LASTABX_NAME,

	LASTABX.BOLUS_VOLUME AS [LAST ABX Volume],

	LASTABX.[Last ABX to OD Score Time],

	CASE WHEN LASTABX.ABX_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST ABX Given in Dept Y/N],

	A.*,

	FIRSTABX.ABX_ADMIN_TIME FIRSTABX_TIME,

	FIRSTABX.NAME FIRSTABX_NAME,

	FIRSTABX.BOLUS_VOLUME AS [FIRST ABX Volume],

	FIRSTABX.[OD Score to First ABX Time],

	CASE WHEN FIRSTABX.ABX_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST ABX Given in Dept Y/N]

INTO #ODABX

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 ABX.ABX_ADMIN_TIME, ABX.ADT_DEPARTMENT_ID, ABX.IN_DTTM, ABX.OUT_DTTM, ABX.NAME, ABX.PAT_ENC_CSN_ID, ABX.ADT_DEPARTMENT_NAME, ABX.BOLUS_VOLUME, DATEDIFF(MI,ABX_ADMIN_TIME,A.RECORDED_TIME) AS [Last ABX to OD Score Time] FROM #BasePopABX ABX

		WHERE ABX.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ABX.ABX_ADMIN_TIME<A.RECORDED_TIME

		ORDER BY ABX.ABX_ADMIN_TIME DESC

	)LASTABX

	OUTER APPLY

	(

		SELECT TOP 1 ABX.ABX_ADMIN_TIME, ABX.ADT_DEPARTMENT_ID, ABX.IN_DTTM, ABX.OUT_DTTM, ABX.NAME, ABX.PAT_ENC_CSN_ID, ABX.ADT_DEPARTMENT_NAME, ABX.BOLUS_VOLUME, DATEDIFF(MI,A.RECORDED_TIME,ABX_ADMIN_TIME) AS [OD Score to First ABX Time] FROM #BasePopABX ABX

		WHERE ABX.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ABX.ABX_ADMIN_TIME>=A.RECORDED_TIME

		ORDER BY ABX.ABX_ADMIN_TIME ASC

	)FIRSTABX

------------------------------------------------------END OF ABX------------------------------------------------------------------



------------------------------------------------------ORDER SET------------------------------------------------------------------

-- All encounters from #Base_pop where Bolus was administered

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OM.ORDER_DTTM

	, OM.PRL_ORDERSET_ID

INTO

	#SSOrderSet 

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE

	OM.PRL_ORDERSET_ID IN (400001)-- (40400100, 40400058, 40400196, 40400153, 4058600002, 400001) --Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway





IF OBJECT_ID(N'tempdb..#ODORDSET') IS NOT NULL DROP TABLE #ODORDSET;

SELECT

	LASTOS.ORDER_DTTM [LAST OrderSet Time],

	LASTOS.PRL_ORDERSET_ID [LAST OrderSet ID],

	CASE WHEN LASTOS.ORDER_DTTM BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST OrderSet in Dept Y/N],

	A.*,

	FIRSTOS.ORDER_DTTM [FIRST OrderSet Time],

	FIRSTOS.PRL_ORDERSET_ID [FIRST OrderSet ID],

	CASE WHEN FIRSTOS.ORDER_DTTM BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST OrderSet in Dept Y/N]

INTO #ODORDSET

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 SOS.ORDER_DTTM, SOS.PRL_ORDERSET_ID FROM #SSOrderSet SOS

		WHERE SOS.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SOS.ORDER_DTTM<A.RECORDED_TIME

		ORDER BY SOS.ORDER_DTTM DESC

	)LASTOS

	OUTER APPLY

	(

		SELECT TOP 1 SOS.ORDER_DTTM, SOS.PRL_ORDERSET_ID FROM #SSOrderSet SOS

		WHERE SOS.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SOS.ORDER_DTTM>=A.RECORDED_TIME

		ORDER BY SOS.ORDER_DTTM ASC

	)FIRSTOS

------------------------------------------------------END OF ORDER SET------------------------------------------------------------------



------------------------------------------------------BOLUS------------------------------------------------------------------



IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	,B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, MAI.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, CM.NAME AS Medication

	, MAI.SIG AS BOLUS_VOLUME

INTO

	#BasePopBolus 

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

	INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

WHERE

	MAI.TAKEN_TIME IS NOT NULL --ADMINISTERED BOLUS ONLY

	AND (OM.MEDICATION_ID IN (700001  --SODIUM CHLORIDE 0.99 % IV BOLUS

							, 7000739 --LACTATED RINGERS IV BOLUS

							, 700003    --ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION

							, 7006331 --ELECTROLYE-A IV Bolus (PLASMALYTE)

							, 700002	--SODIUM CHLORIDE 0.99 % INJECTION SYRINGE

							)

		OR (OM.MEDICATION_ID = 700004)

	AND OM.HV_DISCR_FREQ_ID = '300902') -- FREQUENCY = ONCE 

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

	AND CONVERT(NUMERIC, MAI.SIG ) > 95.0



IF OBJECT_ID(N'tempdb..#OdboL') IS NOT NULL DROP TABLE #OdboL;

SELECT

	LASTBOL.BOLUS_ADMIN_TIME [LAST Bolus Time],

	LASTBOL.Medication [LAST Bolus],

	LASTBOL.BOLUS_VOLUME AS [LAST Bolus Volume],

	LASTBOL.[Last Bolus to Screen Time],

	CASE WHEN LASTBOL.BOLUS_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST Bolus Given in Dept Y/N],

	A.*,

	FIRSTBOL.BOLUS_ADMIN_TIME [FIRST Bolus Time],

	FIRSTBOL.Medication [FIRST Bolus],

	FIRSTBOL.BOLUS_VOLUME AS [FIRST Bolus Volume],

	FIRSTBOL.[Screen Time to First Bolus],

	CASE WHEN FIRSTBOL.BOLUS_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST Bolus Given in Dept Y/N]

INTO #OdboL

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 BOL.BOLUS_ADMIN_TIME, BOL.BOLUS_VOLUME, BOL.Medication, DATEDIFF(MI, BOLUS_ADMIN_TIME,A.RECORDED_TIME) AS [Last Bolus to Screen Time] FROM #BasePopBolus BOL

		WHERE BOL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BOL.BOLUS_ADMIN_TIME<A.RECORDED_TIME

		ORDER BY BOL.BOLUS_ADMIN_TIME DESC

	)LASTBOL

	OUTER APPLY

	(

		SELECT TOP 1 BOL.BOLUS_ADMIN_TIME, BOL.BOLUS_VOLUME, BOL.Medication, DATEDIFF(MI, A.RECORDED_TIME,BOLUS_ADMIN_TIME) AS [Screen Time to First Bolus] FROM #BasePopBolus BOL

		WHERE BOL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BOL.BOLUS_ADMIN_TIME>=A.RECORDED_TIME

		ORDER BY BOL.BOLUS_ADMIN_TIME ASC

	)FIRSTBOL



------------------------------------------------------END OF BOLUS------------------------------------------------------------------

------------------------------------------------------CVL TIMES------------------------------------------------------------------



/*CVL TIME - TEST CSN 1016010350*/

IF OBJECT_ID(N'tempdb..#ALLCVLTime') IS NOT NULL DROP TABLE #ALLCVLTime;

SELECT DISTINCT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, ILN.PLACEMENT_INSTANT

INTO 

	#ALLCVLTime

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID 

	INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = ILN.FLO_MEAS_ID

			AND CVS.VALUE_SET_ID = 3022 --CVL CODES



IF OBJECT_ID(N'tempdb..#ODCVL') IS NOT NULL DROP TABLE #ODCVL;

SELECT

	LASTCVL.PLACEMENT_INSTANT [LAST CVL Time],

	CASE WHEN LASTCVL.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST CVL in Dept Y/N],

	A.*,

	FIRSTCVL.PLACEMENT_INSTANT [FIRST CVL Time],

	CASE WHEN FIRSTCVL.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST CVL in Dept Y/N]

INTO #ODCVL

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 CVL.PLACEMENT_INSTANT FROM #ALLCVLTime CVL

		WHERE CVL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CVL.PLACEMENT_INSTANT<A.RECORDED_TIME

		ORDER BY CVL.PLACEMENT_INSTANT DESC

	)LASTCVL

	OUTER APPLY

	(

		SELECT TOP 1 CVL.PLACEMENT_INSTANT FROM #ALLCVLTime CVL

		WHERE CVL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CVL.PLACEMENT_INSTANT>=A.RECORDED_TIME

		ORDER BY CVL.PLACEMENT_INSTANT ASC

	)FIRSTCVL



------------------------------------------------------END OF CVL TIMES------------------------------------------------------------------



------------------------------------------------------PRESSORS TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;

SELECT DISTINCT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, MAI.TAKEN_TIME

	, GMR.GROUPER_ID

	, CM.NAME AS MEDICATION

INTO

	#Pressors 

FROM #Base_Pop B

	LEFT JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	LEFT JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

	LEFT JOIN EMRDB.dbo.GROUPER_MED_RECORDS GMR ON GMR.EXP_MEDS_LIST_ID = CM.MEDICATION_ID

	LEFT JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

	LEFT JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE

	GMR.GROUPER_ID IN ('8000100'    -- HS RX EPINEPHRINE SEPSIS

							, '8000101' -- HS RX DOPAMINE SEPSIS

							, '8000102' -- HS RX DOBUTAMINE SEPSIS

							, '8000103' -- HS RX MILRINONE SEPSIS

							, '8000104' -- HS RX NOREPINEPHRINE SEPSIS

						)

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

	AND MAI.ROUTE_C = 11 --INTRAVENOUS





IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

SELECT

PAT_ENC_CSN_ID,

CASE WHEN GROUPER_ID = '8000100'   THEN 'EPINEPHRINE' -- HS RX EPINEPHRINE SEPSIS

	WHEN GROUPER_ID =  '8000101' THEN 'DOPAMINE'

	WHEN GROUPER_ID = '8000102'   THEN 'DOBUTAMINE'

	WHEN GROUPER_ID = '8000103'   THEN 'MILRINONE'

	WHEN GROUPER_ID = '8000104'   THEN 'NOREPINEPHRINE'

	END PRESSOR,

	COUNT(TAKEN_TIME) AS MYC

INTO #ODPressorSummary

FROM #Pressors

GROUP BY PAT_ENC_CSN_ID, GROUPER_ID



IF OBJECT_ID ('TEMPDB..#ODPressorPivot') IS NOT NULL DROP TABLE #ODPressorPivot



SELECT

	PAT_ENC_CSN_ID, PVT.[EPINEPHRINE] AS [EPINEPHRINE], PVT.[DOPAMINE] AS [DOPAMINE], PVT.[DOBUTAMINE] AS [DOBUTAMINE],

	PVT.[MILRINONE] AS [MILRINONE], PVT.[NOREPINEPHRINE] AS [NOREPINEPHRINE]

INTO #ODPressorPivot

FROM #ODPressorSummary

	PIVOT( MAX(myc)

	FOR PRESSOR IN ([EPINEPHRINE],[DOPAMINE],[DOBUTAMINE],[MILRINONE],[NOREPINEPHRINE])) AS PVT

--select * from #ODPressorPivot

------------------------------------------------------END OF PRESSORS TIMES------------------------------------------------------------------

------------------------------------------------------SVO2 TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#SVO2') IS NOT NULL DROP TABLE #SVO2;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_TIME AS SVO2OrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID

INTO 

	#SVO2

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS ON B.PAT_ENC_CSN_ID = LAB_ORDER_RESULTS.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID IN (5000001861, 5000000478)



IF OBJECT_ID(N'tempdb..#ODSVO2') IS NOT NULL DROP TABLE #ODSVO2;

SELECT

	LASTSVO2.SVO2OrderTime [LAST SVO2 Time],

	CASE WHEN LASTSVO2.SVO2OrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST SVO2 in Dept Y/N],

	A.*,

	FIRSTSVO2.SVO2OrderTime [FIRST SVO2 Time],

	CASE WHEN FIRSTSVO2.SVO2OrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST SVO2 in Dept Y/N]

INTO #ODSVO2

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 SVO2.SVO2OrderTime FROM #SVO2 SVO2

		WHERE SVO2.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SVO2.SVO2OrderTime<A.RECORDED_TIME

		ORDER BY SVO2.SVO2OrderTime DESC

	)LASTSVO2

	OUTER APPLY

	(

		SELECT TOP 1 SVO2.SVO2OrderTime FROM #SVO2 SVO2

		WHERE SVO2.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SVO2.SVO2OrderTime>=A.RECORDED_TIME

		ORDER BY SVO2.SVO2OrderTime ASC

	)FIRSTSVO2

------------------------------------------------------END OF SVO2 TIMES------------------------------------------------------------------



------------------------------------------------------LACTIC ACID TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_PROC_ID

	, OP.ORDER_TIME AS MBOrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

INTO 

	#LacticAcid

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS ON LAB_ORDER_RESULTS.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID IN (5000000446, 5000000447, 5000000449)



IF OBJECT_ID(N'tempdb..#ODLA') IS NOT NULL DROP TABLE #ODLA;

SELECT

	LASTLA.MBOrderTime [LAST LacticAcid Order Time],

	LASTLA.ORD_VALUE AS [LAST LacticAcid Result],

	CASE WHEN LASTLA.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST LacticAcid in Dept Y/N],

	A.*,

	FIRSTLA.MBOrderTime [FIRST LacticAcid Order Time],

	LASTLA.ORD_VALUE AS [FIRST LacticAcid Result],

	CASE WHEN FIRSTLA.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST LacticAcid in Dept Y/N]

INTO #ODLA

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 LA.MBOrderTime, LA.ORD_VALUE FROM #LacticAcid LA

		WHERE LA.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND LA.MBOrderTime<A.RECORDED_TIME

		ORDER BY LA.MBOrderTime DESC

	)LASTLA

	OUTER APPLY

	(

		SELECT TOP 1 LA.MBOrderTime, LA.ORD_VALUE FROM #LacticAcid LA

		WHERE LA.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND LA.MBOrderTime>=A.RECORDED_TIME

		ORDER BY LA.MBOrderTime ASC

	)FIRSTLA

--SELECT * FROM #ODLA

------------------------------------------------------END OF LACTIC ACID TIMES------------------------------------------------------------------



------------------------------------------------------PROCALCITONIN TIMES------------------------------------------------------------------

/*PROCALCITONIN*/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_TIME AS MBOrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID



INTO 

	#Procalcitonin

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS ON LAB_ORDER_RESULTS.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID = 500001 --COULD USE PROC CODE ALSO.... LAB014

IF OBJECT_ID(N'tempdb..#ODPROCAL') IS NOT NULL DROP TABLE #ODPROCAL;

SELECT

	LASTPRO.MBOrderTime [LAST Procalcitonin Order Time],

	LASTPRO.ORD_VALUE AS [LAST Procalcitonin Result],

	CASE WHEN LASTPRO.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST Procalcitonin in Dept Y/N],

	A.*,

	FIRSTPRO.MBOrderTime [FIRST Procalcitonin Order Time],

	FIRSTPRO.ORD_VALUE AS [FIRST Procalcitonin Result],

	CASE WHEN FIRSTPRO.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST Procalcitonin in Dept Y/N]

INTO #ODPROCAL

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 PROCAL.MBOrderTime, PROCAL.ORD_VALUE FROM #Procalcitonin PROCAL

		WHERE PROCAL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PROCAL.MBOrderTime<A.RECORDED_TIME

		ORDER BY PROCAL.MBOrderTime DESC

	)LASTPRO

	OUTER APPLY

	(

		SELECT TOP 1 PROCAL.MBOrderTime, PROCAL.ORD_VALUE FROM #Procalcitonin PROCAL

		WHERE PROCAL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PROCAL.MBOrderTime>=A.RECORDED_TIME

		ORDER BY PROCAL.MBOrderTime ASC

	)FIRSTPRO

------------------------------------------------------END OF PROCALCITONIN TIMES------------------------------------------------------------------



------------------------------------------------------BLOOD CULTURE TIMES------------------------------------------------------------------

/*Blood Culture*/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_PROC_ID

	, EAP.PROC_CODE AS [Blood Culture Procedure Ordered]

	, OP.ORDER_TIME AS MBOrderTime

	, RESULTS.RESULT_TIME

	, RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, RESULTS.ORD_VALUE

INTO 

	#BloodCultureValue 

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS RESULTS ON B.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP  ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID 

				AND OP.PROC_ID IN (600003,600004,600011,600012)

	INNER JOIN EMRDB.dbo.PROCEDURES_CATALOG EAP ON EAP.PROC_ID = OP.PROC_ID



IF OBJECT_ID(N'tempdb..#ODBC') IS NOT NULL DROP TABLE #ODBC;

SELECT

	LASTBC.MBOrderTime [LAST Blood Culture Order Time],

	LASTBC.[Blood Culture Procedure Ordered] AS [LAST Blood Culture Procedure Ordered],

	LASTBC.ORD_VALUE [LAST Blood Culture Result],

	CASE WHEN LASTBC.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST Blood Culture in Dept Y/N],

	A.*,

	FIRSTBC.MBOrderTime [FIRST Blood Culture Order Time],

	FIRSTBC.[Blood Culture Procedure Ordered] AS [FIRST Blood Culture Procedure Ordered],

	FIRSTBC.ORD_VALUE [FIRST Blood Culture Result],

	CASE WHEN FIRSTBC.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST Blood Culture in Dept Y/N]

INTO #ODBC

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 BC.[Blood Culture Procedure Ordered], BC.MBOrderTime, BC.ORD_VALUE FROM #BloodCultureValue BC

		WHERE BC.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BC.MBOrderTime<A.RECORDED_TIME

		ORDER BY BC.MBOrderTime DESC

	)LASTBC

	OUTER APPLY

	(

		SELECT TOP 1 BC.[Blood Culture Procedure Ordered], BC.MBOrderTime, BC.ORD_VALUE FROM #BloodCultureValue BC

		WHERE BC.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BC.MBOrderTime>=A.RECORDED_TIME

		ORDER BY BC.MBOrderTime ASC

	)FIRSTBC

--SELECT * FROM #ODBC



------------------------------------------------------END OF BLOOD CULTURE TIMES------------------------------------------------------------------



------------------------------------------------------CSF TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, op.ORDER_PROC_ID

	, EAP.PROC_CODE as [CSF Procedure Ordered]

	, OP.ORDER_TIME AS MBOrderTime

	, RESULTS.RESULT_TIME

	, RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, RESULTS.ORD_VALUE

INTO 

	#CSF 

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS RESULTS ON B.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP  ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID

				--AND OP.PROC_CODE IN ('LAB006','LAB007') AND OP.SPECIMEN_SOURCE_C=304 --PER STEPHANIE, USE THOSE LAB CODES WITH SPECIMEN SOURCE AS LUMBAR PUNCTURE--('LAB005','LAB013','LAB004')

				AND PROC_ID IN (600005,600006) AND OP.SPECIMEN_SOURCE_C=304

	INNER JOIN EMRDB.dbo.PROCEDURES_CATALOG EAP ON EAP.PROC_ID = OP.PROC_ID





--SELECT * FROM #CSF

IF OBJECT_ID(N'tempdb..#ODCSF') IS NOT NULL DROP TABLE #ODCSF;

SELECT

	LASTCSF.MBOrderTime [LAST CSF Order Time],

	LASTCSF.[CSF Procedure Ordered] AS [LAST CSF Ordered],

	CASE WHEN LASTCSF.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST CSF in Dept Y/N],

	A.*,

	FIRSTCSF.MBOrderTime [FIRST CSF Order Time],

	FIRSTCSF.[CSF Procedure Ordered] AS [FIRST CSF Ordered],

	CASE WHEN FIRSTCSF.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST CSF in Dept Y/N]

INTO #ODCSF

FROM #Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 CSF.[CSF Procedure Ordered], CSF.MBOrderTime FROM #CSF CSF

		WHERE CSF.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CSF.MBOrderTime<A.RECORDED_TIME

		ORDER BY CSF.MBOrderTime DESC

	)LASTCSF

	OUTER APPLY

	(

		SELECT TOP 1 CSF.[CSF Procedure Ordered], CSF.MBOrderTime FROM #CSF CSF

		WHERE CSF.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CSF.MBOrderTime>=A.RECORDED_TIME

		ORDER BY CSF.MBOrderTime ASC

	)FIRSTCSF



------------------------------------------------------END OF CSF TIMES------------------------------------------------------------------



------------------------------------------------------ETT TIMES------------------------------------------------------------------

/*ETT*/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

SELECT

	B.PAT_ENC_CSN_ID,

	B.ADT_DEPARTMENT_ID,

	B.ADT_DEPARTMENT_NAME,

	B.IN_DTTM,

	B.OUT_DTTM,

	ILN.IP_LDA_ID,

	ILN.PLACEMENT_INSTANT

INTO #ETT

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID AND ILN.FLO_MEAS_ID='900112' AND ILN.PLACEMENT_INSTANT IS NOT NULL





IF OBJECT_ID(N'tempdb..#ODETT') IS NOT NULL DROP TABLE #ODETT;

SELECT

	LASTETT.PLACEMENT_INSTANT [LAST Intubation Time],

	CASE WHEN LASTETT.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST ETT in Dept Y/N],

	A.*,

	FIRSTETT.PLACEMENT_INSTANT [FIRST Intubation Time],

	CASE WHEN FIRSTETT.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST ETT in Dept Y/N]

INTO #ODETT

FROM

	#Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 ETT.PLACEMENT_INSTANT FROM #ETT ETT

		WHERE ETT.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ETT.PLACEMENT_INSTANT<A.RECORDED_TIME

		ORDER BY ETT.PLACEMENT_INSTANT DESC

	)LASTETT

	OUTER APPLY

	(

		SELECT TOP 1 ETT.PLACEMENT_INSTANT FROM #ETT ETT

		WHERE ETT.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ETT.PLACEMENT_INSTANT>=A.RECORDED_TIME

		ORDER BY ETT.PLACEMENT_INSTANT ASC

	)FIRSTETT





------------------------------------------------------END OF ETT TIMES------------------------------------------------------------------



------------------------------------------------------PIV TIMES------------------------------------------------------------------

/*PIV*/

IF OBJECT_ID(N'tempdb..#PIV') IS NOT NULL DROP TABLE #PIV;

SELECT

	B.PAT_ENC_CSN_ID,

	B.ADT_DEPARTMENT_ID,

	B.ADT_DEPARTMENT_NAME,

	B.IN_DTTM,

	B.OUT_DTTM,

	ILN.IP_LDA_ID,

	ILN.PLACEMENT_INSTANT

INTO #PIV

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID AND ILN.FLO_MEAS_ID='900111' AND ILN.PLACEMENT_INSTANT IS NOT NULL



IF OBJECT_ID(N'tempdb..#ODPIV') IS NOT NULL DROP TABLE #ODPIV;

SELECT

	LASTPIV.PLACEMENT_INSTANT [LAST PIV Before Screen],

	CASE WHEN LASTPIV.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST PIV in Dept Y/N],

	A.*,

	FIRSTPIV.PLACEMENT_INSTANT [FIRST PIV After Screen],

	CASE WHEN FIRSTPIV.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST PIV in Dept Y/N]

INTO #ODPIV

FROM

	#Base_Pop_OD_Scores A

	OUTER APPLY

	(

		SELECT TOP 1 PIV.PLACEMENT_INSTANT FROM #PIV PIV

		WHERE PIV.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PIV.PLACEMENT_INSTANT<A.RECORDED_TIME

		ORDER BY PIV.PLACEMENT_INSTANT DESC

	)LASTPIV

	OUTER APPLY

	(

		SELECT TOP 1 PIV.PLACEMENT_INSTANT FROM #PIV PIV

		WHERE PIV.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PIV.PLACEMENT_INSTANT>=A.RECORDED_TIME

		ORDER BY PIV.PLACEMENT_INSTANT ASC

	)FIRSTPIV



------------------------------------------------------END OF PIV TIMES------------------------------------------------------------------



------------------------------------------------------ PROPHYLAXIS ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#PROPHYLAXIS') IS NOT NULL DROP TABLE #PROPHYLAXIS;

SELECT

	B.PAT_ENC_CSN_ID,

	CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS PROPHYLAXIS_YN

INTO #PROPHYLAXIS

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID AND IFM.RECORDED_TIME IS NOT NULL

		AND IFM.FLO_MEAS_ID IN ('9000613042','9000613043','9000613044','9000613045','9000613047','9000613048','9000613050')

		--9000613042	R HS IP VTE AMBULATION ACTION

		--9000613043	R HS IP VTE SCD ACTION

		--9000613044	R HS IP VTE BOOTS ACTION

		--9000613045	R HS IP VTE HEMATOLOGY ACTION

		--9000613047	R HS IP VTE COUMADIN ACTION

		--9000613048	R HS IP VTE HEPARIN ACTION

	--9000613050	R HS IP VTE COMPLICATION ACTIONS

GROUP BY B.PAT_ENC_CSN_ID



------------------------------------------------------END OF PROPHYLAXIS------------------------------------------------------------------



------------------------------------------------------ CVVH ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#CVVH') IS NOT NULL DROP TABLE #CVVH;

SELECT

	B.PAT_ENC_CSN_ID,

	CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS CVVH_YN

INTO #CVVH

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID 

		AND IFM.FLT_ID='9000001359'--ANY FLOWSHEET FROM THIS TEMPLATE IS A CANDIDATE

	--9000001359	T HS IP INPATIENT CVVH	Inpatient CVVH	



GROUP BY B.PAT_ENC_CSN_ID



------------------------------------------------------END OF CVVH------------------------------------------------------------------

------------------------------------------------------ CEREBRAL OX MONITORING ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#OX') IS NOT NULL DROP TABLE #OX;

SELECT

	B.PAT_ENC_CSN_ID,

	CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS OX_YN

INTO #OX

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID 

		AND IFM.FLO_MEAS_ID IN ('900201','900202','900203','9000001977')

	--FLO   900201		R AN NEAR-INFRARED SPECTROSCOPY LEFT CEREBRAL	(Cerebral Oximetry)

	--FLO   900202		R AN NEAR-INFRARED SPECTROSCOPY RIGHT CEREBRAL	(Cerebral Oximetry)

	--FLO   900203		R AN NEAR-INFRARED SPECTROSCOPY RENAL			(Cerebral Oximetry)

	--FLO   9000001977  R HS IP NEAR-INFRARED SPECTROSCOPY CEREBRAL		(Cerebral Oximetry)

GROUP BY B.PAT_ENC_CSN_ID



------------------------------------------------------END OF CEREBRAL OX MONITORING------------------------------------------------------------------

------------------------------------------------------ ECMO ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#ECMO') IS NOT NULL DROP TABLE #ECMO;

SELECT

	B.PAT_ENC_CSN_ID,

	CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS ECMO_YN

INTO #ECMO

FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID 

		AND IFM.FLO_MEAS_ID ='9000101014'

	--9000101014	R ECMO ON/OFF

GROUP BY B.PAT_ENC_CSN_ID



------------------------------------------------------END OF ECMO------------------------------------------------------------------



IF OBJECT_ID(N'tempdb..#FINAL') IS NOT NULL DROP TABLE #FINAL;

SELECT

	Main.PAT_NAME,

	Main.PAT_MRN_ID,

	Main.[Ethnic Group],

	Main.[Race],

	Main.PAT_ENC_CSN_ID,

	Main.AGE_MONTHS,

	Main.AGE_YEARS,

	Main.INP_ADM_DATE,

	Main.HOSP_DISCH_TIME,

	Main.Disposition,

	Main.LOS_HRS,

	ENC_RSN.AllEncReasons AS [Encounter Diagnoses],

	HYPO.[LAST Hypotension Time],

	HYPO.[LAST Hypotension Value],

	HYPO.[LAST Hypotension taken in Dept Y/N],

	HYPO.[FIRST Hypotension Time],

	HYPO.[FIRST Hypotension Value],

	HYPO.[FIRST Hypotension taken in Dept Y/N],

	WT.EncWeight,

	EDLOS.MEAS_VALUE [First Positive Score in ED],

	EDLOS.RECORDED_TIME AS [First Positive Score Time in ED],

	EDLOS.HoursInED AS [ED LOS (Hrs)],

	BP.ADT_DEPARTMENT_NAME,

	BP.DEPARTMENT_ROLLUP,

	BP.IN_DTTM [In Department Time],

	BP.OUT_DTTM [Out Department Time],

	SCORES.MEAS_VALUE AS OD_SCORE,

	SCORES.RECORDED_TIME as [Score Time],

	CASE WHEN SCORES.RECORDED_TIME IS NOT NULL

			THEN CASE WHEN DATEPART(HOUR,SCORES.RECORDED_TIME) >= 7 and DATEPART(HOUR,SCORES.RECORDED_TIME) < 19 then 'AM (Day Shift)'

						ELSE 'PM (Night Shift)'

					END

	END AS [OD Score AM/PM],

	SCORES.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP],

	SCORES.[Huddle Date],

	SCORES.[Huddle Time],

	SCORES.[PATIENTS Assessed by MD/PNP],

	SCORES.[Physician Name],

	SCORES.[Additional Orders Received/Placed by MD/PNP],

	ABX.LASTABX_TIME [LAST ABX Time],

	ABX.LASTABX_NAME [LAST ABX Name],

	ABX.[LAST ABX Volume],

	ABX.[Last ABX to OD Score Time],

	ABX.[LAST ABX Given in Dept Y/N],

	ABX.FIRSTABX_TIME [FIRST ABX Time],

	ABX.FIRSTABX_NAME [FIRST ABX Name],

	ABX.[FIRST ABX Volume],

	ABX.[OD Score to First ABX Time],

	ABX.[FIRST ABX Given in Dept Y/N],

	CASE WHEN (ABX.LASTABX_TIME IS NOT NULL OR ABX.FIRSTABX_TIME IS NOT NULL) THEN 'Y' ELSE 'N' END AS ABX_YN,

	BOL.[LAST Bolus Time],

	BOL.[LAST Bolus],

	BOL.[LAST Bolus Volume],

	BOL.[Last Bolus to Screen Time],

	BOL.[LAST Bolus Given in Dept Y/N],

	BOL.[FIRST Bolus Time],

	BOL.[FIRST Bolus],

	BOL.[FIRST Bolus Volume],

	BOL.[Screen Time to First Bolus],

	BOL.[FIRST Bolus Given in Dept Y/N],

	CASE WHEN (BOL.[LAST Bolus Time] IS NOT NULL OR BOL.[FIRST Bolus Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS BOLUS_YN,

	LA.[LAST LacticAcid Order Time],

	LA.[LAST LacticAcid Result],

	LA.[LAST LacticAcid in Dept Y/N],

	LA.[FIRST LacticAcid Order Time],

	LA.[FIRST LacticAcid Result],

	LA.[FIRST LacticAcid in Dept Y/N],

	CASE WHEN (LA.[LAST LacticAcid Order Time] IS NOT NULL OR LA.[FIRST LacticAcid Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS LacticAcid_YN,

	ORDS.[LAST OrderSet Time],

	ORDS.[LAST OrderSet ID],

	ORDS.[LAST OrderSet in Dept Y/N],

	ORDS.[FIRST OrderSet Time],

	ORDS.[FIRST OrderSet ID],

	ORDS.[FIRST OrderSet in Dept Y/N],

	CVL.[LAST CVL Time],

	CVL.[LAST CVL in Dept Y/N],

	CVL.[FIRST CVL Time],

	CVL.[FIRST CVL in Dept Y/N],

	CASE WHEN (CVL.[LAST CVL Time] IS NOT NULL OR CVL.[FIRST CVL Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS CVL_YN,

	SVO2.[LAST SVO2 Time],

	SVO2.[LAST SVO2 in Dept Y/N],

	SVO2.[FIRST SVO2 Time],

	SVO2.[FIRST SVO2 in Dept Y/N],

	CASE WHEN (SVO2.[LAST SVO2 Time] IS NOT NULL OR SVO2.[FIRST SVO2 Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS SVO2_YN,

	PROCAL.[LAST Procalcitonin Order Time],

	PROCAL.[LAST Procalcitonin Result],

	PROCAL.[LAST Procalcitonin in Dept Y/N],

	PROCAL.[FIRST Procalcitonin Order Time],

	PROCAL.[FIRST Procalcitonin Result],

	PROCAL.[FIRST Procalcitonin in Dept Y/N],

	CASE WHEN (PROCAL.[LAST Procalcitonin Order Time] IS NOT NULL OR PROCAL.[FIRST Procalcitonin Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS Procalcitonin_YN,

	BC.[LAST Blood Culture Order Time],

	BC.[LAST Blood Culture Procedure Ordered],

	BC.[LAST Blood Culture Result],

	BC.[LAST Blood Culture in Dept Y/N],

	BC.[FIRST Blood Culture Order Time],

	BC.[FIRST Blood Culture Procedure Ordered],

	BC.[FIRST Blood Culture Result],

	BC.[FIRST Blood Culture in Dept Y/N],

	CASE WHEN (BC.[LAST Blood Culture Order Time] IS NOT NULL OR BC.[FIRST Blood Culture Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS BloodCulture_YN,

	CSF.[LAST CSF Order Time],

	CSF.[LAST CSF Ordered],

	CSF.[LAST CSF in Dept Y/N],

	CSF.[FIRST CSF Order Time],

	CSF.[FIRST CSF Ordered],

	CSF.[FIRST CSF in Dept Y/N],

	CASE WHEN (CSF.[LAST CSF Order Time] IS NOT NULL OR CSF.[FIRST CSF Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS CSF_YN,

	PIV.[LAST PIV Before Screen],

	PIV.[LAST PIV in Dept Y/N],

	PIV.[FIRST PIV After Screen],

	PIV.[FIRST PIV in Dept Y/N],

	CASE WHEN (PIV.[LAST PIV Before Screen] IS NOT NULL OR PIV.[FIRST PIV After Screen] IS NOT NULL) THEN 'Y' ELSE 'N' END AS PIV_YN,

	ETT.[LAST Intubation Time],

	ETT.[LAST ETT in Dept Y/N],

	ETT.[FIRST Intubation Time],

	ETT.[FIRST ETT in Dept Y/N],

	CASE WHEN (ETT.[LAST Intubation Time] IS NOT NULL OR ETT.[FIRST Intubation Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS ETT_YN,

	CASE WHEN PRESSOR.DOBUTAMINE IS NULL THEN 'N' ELSE 'Y' END DOBUTAMINE,

	CASE WHEN PRESSOR.DOPAMINE IS NULL THEN 'N' ELSE 'Y' END DOPAMINE,

	CASE WHEN PRESSOR.EPINEPHRINE IS NULL THEN 'N' ELSE 'Y' END EPINEPHRINE,

	CASE WHEN PRESSOR.MILRINONE IS NULL THEN 'N' ELSE 'Y' END MILRINONE,

	CASE WHEN PRESSOR.NOREPINEPHRINE IS NULL THEN 'N' ELSE 'Y' END NOREPINEPHRINE,

	CASE WHEN (

				PRESSOR.DOBUTAMINE IS NOT NULL OR

				PRESSOR.DOPAMINE IS NOT NULL OR

				PRESSOR.EPINEPHRINE IS NOT NULL OR

				PRESSOR.MILRINONE IS NOT NULL OR

				PRESSOR.NOREPINEPHRINE IS NOT NULL) THEN 'Y' ELSE 'N' END AS PRESSOR_YN,

	COALESCE(PROPHY.PROPHYLAXIS_YN,'N') AS DVTPROPHYLAXIS_YN,

	COALESCE(CVVH.CVVH_YN,'N') AS CVVH_YN,

	COALESCE(OX.OX_YN,'N') AS OX_YN,

	COALESCE(ECMO.ECMO_YN,'N') AS ECMO_YN,

	CASE WHEN IPSO.PAT_ENC_CSN_ID IS NULL THEN 'N' ELSE 'Y' END SEVERE_SEPSIS_STAGING,

	SCORES.[CLINICAL_ALERTS Not Activated Reason],

	SCORES.[CLINICAL_ALERTS Not Activated Comment],

	SCORES.[CLINICAL_ALERTS Activated Comment],

	GETDATE() AS [Refresh Time]

INTO #FINAL

FROM #Main Main

	INNER JOIN #Base_Pop BP ON BP.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID

	INNER JOIN #Base_Pop_OD_Scores SCORES ON SCORES.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID AND SCORES.ADT_DEPARTMENT_ID = BP.ADT_DEPARTMENT_ID AND SCORES.IN_DTTM = BP.IN_DTTM

	LEFT OUTER JOIN #Base_Pop_ENC_Reason ENC_RSN ON ENC_RSN.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID

	LEFT OUTER JOIN #EncounterWeights WT ON WT.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID AND WT.TIME_LINE=1

	LEFT OUTER JOIN #ODHYPO HYPO ON HYPO.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND HYPO.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND HYPO.IN_DTTM = SCORES.IN_DTTM AND HYPO.TIME_LINE=1

	LEFT OUTER JOIN #ODABX ABX ON ABX.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND ABX.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND ABX.IN_DTTM = SCORES.IN_DTTM AND ABX.TIME_LINE=1

	LEFT OUTER JOIN #OdboL BOL ON BOL.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND BOL.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND BOL.IN_DTTM = SCORES.IN_DTTM AND BOL.TIME_LINE=1

	LEFT OUTER JOIN #ODLA LA ON LA.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND LA.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND LA.IN_DTTM = SCORES.IN_DTTM AND LA.TIME_LINE=1

	LEFT OUTER JOIN #ODORDSET ORDS ON ORDS.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND ORDS.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND ORDS.IN_DTTM = SCORES.IN_DTTM AND ORDS.TIME_LINE=1

	LEFT OUTER JOIN #ODCVL CVL ON CVL.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND CVL.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND CVL.IN_DTTM = SCORES.IN_DTTM AND CVL.TIME_LINE=1

	LEFT OUTER JOIN #ODPressorPivot PRESSOR ON PRESSOR.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1--CHECK THIS AGAIN

	LEFT OUTER JOIN #ODSVO2 SVO2 ON SVO2.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SVO2.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND SVO2.IN_DTTM = SCORES.IN_DTTM AND SVO2.TIME_LINE=1

	LEFT OUTER JOIN #ODPROCAL PROCAL ON PROCAL.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND PROCAL.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND PROCAL.IN_DTTM = SCORES.IN_DTTM AND PROCAL.TIME_LINE=1

	LEFT OUTER JOIN #ODBC BC ON BC.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND BC.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND BC.IN_DTTM = SCORES.IN_DTTM AND BC.TIME_LINE=1

	LEFT OUTER JOIN #ODCSF CSF ON CSF.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND CSF.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND CSF.IN_DTTM = SCORES.IN_DTTM AND CSF.TIME_LINE=1

	LEFT OUTER JOIN #ODPIV PIV ON PIV.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND PIV.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND PIV.IN_DTTM = SCORES.IN_DTTM AND PIV.TIME_LINE=1

	LEFT OUTER JOIN #ODETT ETT ON ETT.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND ETT.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND ETT.IN_DTTM = SCORES.IN_DTTM AND ETT.TIME_LINE=1

	LEFT OUTER JOIN #PROPHYLAXIS PROPHY ON PROPHY.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

	LEFT OUTER JOIN #CVVH CVVH ON CVVH.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

	LEFT OUTER JOIN #OX OX ON OX.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

	LEFT OUTER JOIN #ECMO ECMO ON ECMO.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

	LEFT OUTER JOIN #EDPosScore_EDLOS EDLOS ON EDLOS.PAT_ENC_CSN_ID = MAIN.PAT_ENC_CSN_ID AND EDLOS.FIRST_TIME_LINE=1

	LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING] IPSO ON IPSO.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID





DROP INDEX  IX_InpDataID  ON #Main , IX_PatID  ON #Main;



SELECT * FROM #FINAL order by PAT_ENC_CSN_ID
GO

-- ==== reports/USP_RPTS_IP_SEPSIS_COMPLIANCE.sql ====
/*

/*********************************************************************************

	TITLE:		 Sepsis Compliance

	PURPOSE:	 Sepsis Scoring compliance report by unit

	AUTHOR:		 V_DEV001



	REVISION HISTORY:

				11.16.2021 V_DEV001 - Original version

				05.22.2022 V_DEV001 - Location  update for Expansion Phase III



*********************************************************************************

	USAGE:

		EXEC [reports].[USP_IP_SEPSIS_COMPLIANCE] '09/01/2021','09/30/2021',0

*********************************************************************************/

*/

CREATE   PROCEDURE [reports].[USP_IP_SEPSIS_COMPLIANCE](

@i_vRelativeStartDate DATE = NULL

	, @i_vRelativeEndDate DATE = NULL

	--, @i_vRelative15OREOM bit = null 

)

AS

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;	

BEGIN



	--BEGIN TRY

	SET NOCOUNT ON;

	

	DECLARE @dStartDate DATE

	DECLARE @dEndDate DATE

	DECLARE @dTestRun BIT

	

	IF @i_vRelativeStartDate IS NULL OR @i_vRelativeStartDate = ''

		SET @dStartDate = EMRDB.dbo.fn_parse_date('MB-3')

						

	ELSE

		SET @dStartDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeStartDate)



	IF @i_vRelativeEndDate IS NULL OR @i_vRelativeEndDate = ''

		SET @dEndDate = EMRDB.[dbo].[fn_parse_date]('ME-1')

	ELSE

		SET @dEndDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeEndDate)	

	/*

	IF @i_vRelative15OREOM IS NULL OR @i_vRelative15OREOM = ''

		set @dTestRun = 0

		else 	set @dTestRun = 1

	*/



IF OBJECT_ID(N'tempdb..#Main') IS NOT NULL DROP TABLE #Main;

SELECT

	PAT.PAT_MRN_ID AS MRN

	, PAT.PAT_NAME AS [PATIENTS]

	, PEH.PAT_ENC_CSN_ID

	, PEH.INP_ADM_DATE AS [IP Admit Time]

	, PEH.INPATIENT_DATA_ID

	, VPALH.ADT_DEPARTMENT_ID

	, VPALH.ADT_DEPARTMENT_NAME

	, loc.LOC_NAME [Location]

	, VPALH.IN_DTTM

	, VPALH.OUT_DTTM

	, DT.CALENDAR_DT

	, DT.MONTH_END_DT

	, DT.DAY_OF_MONTH

	, PEH.HOSP_DISCH_TIME

INTO 

	#Main

FROM 

EMRDB.dbo.V_PATIENT_LOCATION_HISTORY VPALH

	INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = VPALH.PAT_ENC_CSN

	INNER JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

	INNER JOIN EMRDB.dbo.CALENDAR_DATES DT ON (DT.CALENDAR_DT BETWEEN CONVERT(DATE,VPALH.IN_DTTM) AND CONVERT(DATE,VPALH.OUT_DTTM))

	left outer join EMRDB.dbo.DEPARTMENTS dep on dep.DEPARTMENT_ID = VPALH.ADT_DEPARTMENT_ID

	left outer join EMRDB.dbo.LOCATIONS loc on loc.loc_id = dep.REV_LOC_ID

WHERE

	VPALH.ADT_DEPARTMENT_ID IS NOT NULL AND

	PEH.INP_ADM_DATE IS NOT NULL

	AND (CONVERT(DATE,DT.CALENDAR_DT) BETWEEN @dStartDate AND @dEndDate)



IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT

	PD.[PATIENTS]

	, PD.[MRN]

	, PD.PAT_ENC_CSN_ID

	, PD.[IP Admit Time]

	, COALESCE(CVS.CODE_DESC,'Rollup Not Available') AS DEPARTMENT_ROLLUP

	, PD.ADT_DEPARTMENT_ID

	, PD.ADT_DEPARTMENT_NAME

	, PD.[Location]

	, PD.IN_DTTM

	, PD.OUT_DTTM

	, SEPSIS.MEAS_VALUE

	, SEPSIS.RECORDED_TIME AS [OD Score Time]

	, ALERTNOTACTIVATED.[CLINICAL_ALERTS Not Activated Reason]

	, ALERTNOTACTIVATED.[CLINICAL_ALERTS Not Activated Comment]

	, ALERTACTIVATED.[CLINICAL_ALERTS Activated Comment]

	, DATEADD(MI,420,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AS SHIFT1_START

	, DATEADD(MI,1139,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AS SHIFT1_END

	, DATEADD(MI,419,DATEADD(DD, 1, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AS SHIFT2_END

	, CASE WHEN CAST (SEPSIS.RECORDED_TIME AS TIME) BETWEEN CAST ('00:01:00.0000000' AS TIME) AND CAST ('06:59:00.0000000' AS TIME) THEN 

		DATEADD(DD,-1,CONVERT(DATE,SEPSIS.RECORDED_TIME)) ELSE CALENDAR_DT  END AS CALENDAR_DT

	, SepsisAlert.*

	, ROW_NUMBER() OVER(PARTITION BY PD.PAT_ENC_CSN_ID ORDER BY SEPSIS.RECORDED_TIME ASC) AS TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY PD.PAT_ENC_CSN_ID, PD.IN_DTTM,PD.OUT_DTTM ORDER BY SEPSIS.RECORDED_TIME ASC) AS DEPT_TIME_LINE

	, PD.HOSP_DISCH_TIME AS [Discharge Time]

	, PD.DAY_OF_MONTH

	, PD.MONTH_END_DT

INTO 

	#Base_Pop_OD_Scores 

FROM #Main PD

	LEFT OUTER JOIN

	(

		SELECT

			IFR.INPATIENT_DATA_ID, IFR.FSD_ID, IFM.MEAS_VALUE, IFM.RECORDED_TIME

		FROM EMRDB.dbo.FLOWSHEET_RECORDS IFR

			INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

		WHERE IFM.FLO_MEAS_ID IN ('9000161711','9000002644') --ORGAN DYSFUNCTION SCORE

	)SEPSIS ON SEPSIS.INPATIENT_DATA_ID = PD.INPATIENT_DATA_ID

			AND (SEPSIS.RECORDED_TIME BETWEEN PD.IN_DTTM AND PD.OUT_DTTM)

			AND CONVERT(DATE,SEPSIS.RECORDED_TIME) = PD.CALENDAR_DT

	LEFT OUTER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = PD.ADT_DEPARTMENT_ID

				AND CVS.VALUE_SET_ID = 3031 --DEPARTMENT ROLL UP

	OUTER APPLY

	(

		SELECT

			TOP 1  EMP.NAME AS [Note Author], HNO.CRT_INST_LOCAL_DTTM AS [Note Created Time]

		FROM EMRDB.dbo.CLINICAL_NOTES HNO

			LEFT JOIN EMRDB.dbo.NOTE_TEMPLATE_TEXT_IDS ETX ON ETX.NOTE_ID = HNO.NOTE_ID

			LEFT JOIN EMRDB.dbo.NOTE_TEMPLATE_LIST_IDS LIS ON LIS.NOTE_ID = HNO.NOTE_ID

			INNER JOIN EMRDB.dbo.NOTE_ENCOUNTER_INFO HNOENC ON HNOENC.NOTE_ID = HNO.NOTE_ID

			INNER JOIN EMRDB.dbo.EMPLOYEES EMP ON EMP.USER_ID = HNOENC.AUTHOR_USER_ID

		WHERE

			HNO.PAT_ENC_CSN_ID = PD.PAT_ENC_CSN_ID

			AND (HNO.CRT_INST_LOCAL_DTTM BETWEEN SEPSIS.RECORDED_TIME AND DATEADD(MI, 180, SEPSIS.RECORDED_TIME))--within one hour from OD SCORE

			AND (ETX.SMARTTEXTS_ID='40440015' OR LIS.SMARTLISTS_ID='46214') --HS IP SEPSIS HUDDLE NOTE or Sepsis Eval SmartList

		ORDER BY HNO.CRT_INST_LOCAL_DTTM 

	)SepsisAlert

	LEFT OUTER JOIN

	(

		SELECT

			IFR.INPATIENT_DATA_ID, IFM_ALERTNOTACTIVATED.FSD_ID, IFM_ALERTNOTACTIVATED.RECORDED_TIME, IFM_ALERTNOTACTIVATED.MEAS_VALUE AS [CLINICAL_ALERTS Not Activated Reason], IFM_ALERTNOTACTIVATED.MEAS_COMMENT as [CLINICAL_ALERTS Not Activated Comment]

		FROM EMRDB.dbo.FLOWSHEET_RECORDS IFR

			INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM_ALERTNOTACTIVATED ON IFM_ALERTNOTACTIVATED.FSD_ID = IFR.FSD_ID

		WHERE

			IFM_ALERTNOTACTIVATED.FLO_MEAS_ID='9000003159'

	)ALERTNOTACTIVATED ON ALERTNOTACTIVATED.INPATIENT_DATA_ID = SEPSIS.INPATIENT_DATA_ID

		AND ALERTNOTACTIVATED.FSD_ID = SEPSIS.FSD_ID

		AND ALERTNOTACTIVATED.RECORDED_TIME = SEPSIS.RECORDED_TIME

	LEFT OUTER JOIN

	(

		SELECT

			ALT.ALT_ID,

			ALT.PAT_CSN,

			HIS.ALT_ACTION_INST,

			--COALESCE(HIS.SPEC_OVR_CMNT,' ')+ RSN.NAME [CLINICAL_ALERTS Activated Comment]

			HIS.SPEC_OVR_CMNT [CLINICAL_ALERTS Activated Comment]

		FROM EMRDB.dbo.CLINICAL_ALERTS ALT

			INNER JOIN EMRDB.dbo.ALERT_HISTORY HIS ON HIS.ALT_ID = ALT.ALT_ID

			INNER JOIN EMRDB.dbo.REF_ALERT_OVERRIDE_REASONS RSN ON RSN.ALRT_SP_OVR_RSN_C = HIS.SPEC_OVR_RSN_C

		WHERE ALT.BPA_LOCATOR_ID=900400001--BASE 2019 HS OD SCORE SEPSIS >2 [900400001]

	)ALERTACTIVATED ON ALERTACTIVATED.PAT_CSN = PD.PAT_ENC_CSN_ID

		AND ALERTACTIVATED.ALT_ACTION_INST = SEPSIS.RECORDED_TIME



IF OBJECT_ID(N'tempdb..#SepsisSummary') IS NOT NULL DROP TABLE #SepsisSummary;

SELECT

	PAT_ENC_CSN_ID,

	ADT_DEPARTMENT_ID,

	DEPARTMENT_ROLLUP,

	IN_DTTM,

	OUT_DTTM,

	ScoreDay,

	CASE WHEN (

			CASE WHEN SUM([Shift 1 Score])>=1 THEN 1 ELSE 0 END + 

			CASE WHEN sum([Shift 2 Score])>=1 THEN 1 ELSE 0 END )>1 THEN 'y' ELSE 'n'

	END AS ScoreCompliant_YN

INTO #SepsisSummary

FROM

(

	SELECT

		[PATIENTS]

		,[MRN]

		,PAT_ENC_CSN_ID

		,[IP Admit Time]

		,DEPARTMENT_ROLLUP

		,ADT_DEPARTMENT_ID

		,ADT_DEPARTMENT_NAME

		,IN_DTTM

		,OUT_DTTM

		,MEAS_VALUE

		,[OD Score Time]

		,CONVERT(DATE,CALENDAR_DT) as ScoreDay

		,CASE

			WHEN [OD Score Time] IS NULL THEN 0	

			WHEN --CHECK IF IP ADMIT DATE IS THE FIRST DAY OF SCORE

				CONVERT(DATE,[OD Score Time]) = CONVERT(DATE,[IP Admit Time])

				AND [IP Admit Time]  >= SHIFT1_END THEN 1

			WHEN --CHECK IF IP ADMIT DATE IS THE FIRST DAY OF SCORE

				CONVERT(DATE,[OD Score Time]) = CONVERT(DATE,IN_DTTM)

				AND IN_DTTM  >= SHIFT1_END THEN 1

			WHEN

				[OD Score Time] BETWEEN SHIFT1_START AND SHIFT1_END THEN 1

			ELSE 0

			END AS [Shift 1 Score]

		,CASE

			WHEN [OD Score Time] IS NULL THEN 0	

			WHEN --CHECK IF IP ADMIT DATE IS THE FIRST DAY OF SCORE

				CONVERT(DATE,[OD Score Time]) = CONVERT(DATE, [Discharge Time])

				AND [Discharge Time] <= SHIFT1_END THEN 1

			WHEN --CHECK IF IP ADMIT DATE IS THE FIRST DAY OF SCORE

				CONVERT(DATE,[OD Score Time]) = CONVERT(DATE, OUT_DTTM)

				AND OUT_DTTM <= SHIFT1_END THEN 1

			WHEN [OD Score Time] > SHIFT1_END AND [OD Score Time] <=SHIFT2_END THEN 1

			ELSE 0

			END AS [Shift 2 Score]

		,[Note Author]

		,[Note Created Time]

		,TIME_LINE

		,DEPT_TIME_LINE

		,[Discharge Time]

		,DAY_OF_MONTH

		,MONTH_END_DT

	FROM #Base_Pop_OD_Scores

) A

GROUP BY PAT_ENC_CSN_ID, DEPARTMENT_ROLLUP, ADT_DEPARTMENT_ID, IN_DTTM, OUT_DTTM, ScoreDay--,DAY_OF_MONTH,MONTH_END_DT

ORDER BY PAT_ENC_CSN_ID, ScoreDay



SELECT

	BASE.PATIENTS,

	BASE.MRN,

	BASE.PAT_ENC_CSN_ID AS [CSN],

	BASE.[IP Admit Time],

	CASE WHEN BASE.DEPARTMENT_ROLLUP IS NULL THEN 'Rollup Not Available' ELSE BASE.DEPARTMENT_ROLLUP END AS DEPARTMENT_ROLLUP,

	BASE.ADT_DEPARTMENT_NAME AS [Department],

	BASE.Location,

	BASE.IN_DTTM AS [Department In Time],

	BASE.OUT_DTTM AS [Department Out Time],

	BASE.CALENDAR_DT AS ScoreDay,

	TRY_CAST(BASE.MEAS_VALUE AS INT) AS [OD Score],

	BASE.[OD Score Time],

	BASE.[CLINICAL_ALERTS Not Activated Reason],

	BASE.[CLINICAL_ALERTS Not Activated Comment],

	BASE.[CLINICAL_ALERTS Activated Comment],

	BASE.[Note Author],

	BASE.[Note Created Time],

	CASE WHEN BASE.DEPT_TIME_LINE=1 AND SUMMARY.PAT_ENC_CSN_ID IS NOT NULL THEN 'N' 

	WHEN BASE.DEPT_TIME_LINE=1 AND SUMMARY.PAT_ENC_CSN_ID IS NULL THEN 'Y' 

	ELSE NULL END AS ScoreCompliant_YN,

	[Discharge Time],

	BASE.DEPT_TIME_LINE,

	BASE.TIME_LINE,

	case when BASE.DAY_OF_MONTH = 15 OR BASE.MONTH_END_DT = CONVERT(DATE,BASE.[OD Score Time]) then 'True' else 'False' end as [15th or EOM]

FROM #Base_Pop_OD_Scores BASE

	LEFT OUTER JOIN--CHECK IF THERE IS AT LEAST ONE 'N' FOR A GIVEN CALENDAR DATE

	(

		SELECT

			SUMMARY.PAT_ENC_CSN_ID, SUMMARY.IN_DTTM,SUMMARY.ScoreDay

			,ROW_NUMBER()OVER(PARTITION BY SUMMARY.PAT_ENC_CSN_ID,SUMMARY.IN_DTTM ORDER BY SUMMARY.ScoreDay) AS MYLINE

		FROM #SepsisSummary SUMMARY

		WHERE

			 SUMMARY.ScoreCompliant_YN='N'

	)SUMMARY ON SUMMARY.PAT_ENC_CSN_ID = BASE.PAT_ENC_CSN_ID

			AND SUMMARY.IN_DTTM = BASE.IN_DTTM

			AND BASE.DEPT_TIME_LINE=1

			AND SUMMARY.MYLINE=1

WHERE

	BASE.DEPARTMENT_ROLLUP not in ('Rollup Not Available','ER')

	/*AND	(

			(@dTestRun = 1 and

				(

					BASE.DAY_OF_MONTH = 15

					OR BASE.MONTH_END_DT = CONVERT(DATE,BASE.[OD Score Time])

				)

			) 

			

			or  @dTestRun = 0

		)*/

ORDER BY BASE.PAT_ENC_CSN_ID,BASE.CALENDAR_DT, [OD Score Time]

END
GO

-- ==== reports/USP_RPTS_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES.sql ====
/*********************************************************************************

	TITLE:		 [USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES]

	PURPOSE:	 Report to Sepsis Score documentation compliance by shift Nurses

	AUTHOR:		 V_DEV001



	REVISION HISTORY:

				05.11.2021					V_DEV001					Original version				

				05.23.2022					V_DEV001					Expansion Phase III Location update

*********************************************************************************

	USAGE:

		EXEC [reports].[USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES]

*********************************************************************************/



CREATE   PROCEDURE [reports].[USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES]

	@i_vRelativeStartDate DATE = NULL

	, @i_vRelativeEndDate DATE = NULL

AS

	

BEGIN

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED



	

	DECLARE @dStartDate DATE

	DECLARE @dEndDate DATE

	

	IF @i_vRelativeStartDate IS NULL OR @i_vRelativeStartDate = ''

		--SET @dStartDate = EMRDB.dbo.fn_parse_date('{?StartDate}');--EMRDB.[dbo].[fn_parse_date]('05/01/2020')--DEFAULTING TO PREVIOUS MONTH

		SET @dStartDate = EMRDB.[dbo].[fn_parse_date]('MB-6')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @dStartDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeStartDate)

	

	IF @i_vRelativeEndDate IS NULL OR @i_vRelativeEndDate = ''

		--SET @dEndDate =  EMRDB.dbo.fn_parse_date('{?EndDate}');--EMRDB.[dbo].[fn_parse_date]('05/31/2020')--DEFAULTING TO PREVIOUS MONTH

		SET @dEndDate = EMRDB.[dbo].[fn_parse_date]('ME-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @dEndDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeEndDate)	

		

IF OBJECT_ID(N'tempdb..#Main') IS NOT NULL DROP TABLE #Main;

SELECT

	PAT.PAT_MRN_ID AS MRN

	, PAT.PAT_NAME AS [PATIENTS]

	, PEH.PAT_ENC_CSN_ID

	, PEH.INP_ADM_DATE AS [IP Admit Time]

	, PEH.INPATIENT_DATA_ID

	, VPALH.ADT_DEPARTMENT_ID

	, VPALH.ADT_DEPARTMENT_NAME

	, LOC.LOC_NAME [Location]

	, VPALH.IN_DTTM

	, VPALH.OUT_DTTM

	, DT.CALENDAR_DT

	, PEH.HOSP_DISCH_TIME

INTO 

	#Main

FROM 

EMRDB.dbo.V_PATIENT_LOCATION_HISTORY VPALH

	INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = VPALH.PAT_ENC_CSN

	INNER JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

	INNER JOIN EMRDB.dbo.CALENDAR_DATES DT ON (DT.CALENDAR_DT BETWEEN CONVERT(DATE,VPALH.IN_DTTM) AND CONVERT(DATE,VPALH.OUT_DTTM))

	LEFT OUTER JOIN EMRDB.dbo.DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = PEH.DEPARTMENT_ID

	LEFT OUTER JOIN EMRDB.dbo.LOCATIONS LOC ON LOC.LOC_ID = DEP.REV_LOC_ID

WHERE

	VPALH.ADT_DEPARTMENT_ID IS NOT NULL AND

	VPALH.ADT_DEPARTMENT_ID IN (200108013,200108014)

	AND PEH.INP_ADM_DATE IS NOT NULL

	AND (CONVERT(DATE,DT.CALENDAR_DT) BETWEEN @dStartDate AND @dEndDate)



IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT

	PD.[PATIENTS]

	, PD.[MRN]

	, PD.PAT_ENC_CSN_ID

	, PD.[IP Admit Time]

	, COALESCE(CVS.CODE_DESC,'Rollup Not Available') AS DEPARTMENT_ROLLUP

	, PD.ADT_DEPARTMENT_ID

	, PD.ADT_DEPARTMENT_NAME

	, PD.Location

	, PD.IN_DTTM

	, PD.OUT_DTTM

	, SEPSIS_1sC0RE.RECORDED_TIME as [Shift 1 Score Time]

	, SEPSIS_2sC0RE.RECORDED_TIME as [Shift 2 Score Time]	

	, SEPSIS_1sC0RE.MEAS_VALUE as [Shift 1 Score]

	, SEPSIS_2sC0RE.MEAS_VALUE as [Shift 2 Score]	

	, DATEADD(MI,420,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AS SHIFT1_START

	, DATEADD(MI,1139,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AS SHIFT1_END

	, DATEADD(MI,419,DATEADD(DD, 1, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AS SHIFT2_END

	, PD.CALENDAR_DT

	, FYDD.HS_FY

	, FYDD.HS_FY_MONTH_NUMBER

	, FYDD.MONTH_NAME

	, FYDD.YEAR

	, LEFT(FYDD.MONTH_NAME, 3 ) AS [Month Short Name]

	, PD.HOSP_DISCH_TIME AS [Discharge Time]

	, DATEADD(MI,719,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) as shift1time

	, DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) as shift2time

	, Shift1_RNs.Shift1_RNs

	, Shift2_RNs.Shift2_RNs

	, Shift1_CNs.Shift1_CNs

	, Shift2_CNs.Shift2_CNs

	, ROW_NUMBER() OVER(PARTITION BY PD.PAT_ENC_CSN_ID, PD.IN_DTTM,PD.OUT_DTTM ORDER BY SEPSIS_1sC0RE.RECORDED_TIME ASC) AS DEPT_TIME_LINE

INTO 

	#Base_Pop_OD_Scores 

FROM #Main PD

	INNER JOIN reports.FY_DATE_DIMENSION FYDD ON FYDD.CALENDAR_DT = PD.CALENDAR_DT

	OUTER APPLY

	(

		SELECT

			TOP 1 IFM.RECORDED_TIME, IFM.MEAS_VALUE

		FROM EMRDB.dbo.FLOWSHEET_RECORDS IFR

			INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

		WHERE IFM.FLO_MEAS_ID IN ('9000161711','9000002644') --ORGAN DYSFUNCTION SCORE

			AND IFR.INPATIENT_DATA_ID= PD.INPATIENT_DATA_ID

			AND (IFM.RECORDED_TIME BETWEEN DATEADD(MI,420,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1139,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

			AND CONVERT(DATE,IFM.RECORDED_TIME) = PD.CALENDAR_DT

	)SEPSIS_1sC0RE

	OUTER APPLY

	(

		SELECT

			TOP 1 IFM.RECORDED_TIME, IFM.MEAS_VALUE

		FROM EMRDB.dbo.FLOWSHEET_RECORDS IFR

			INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

		WHERE IFM.FLO_MEAS_ID IN ('9000161711','9000002644') --ORGAN DYSFUNCTION SCORE

			AND IFR.INPATIENT_DATA_ID= PD.INPATIENT_DATA_ID

			AND (IFM.RECORDED_TIME BETWEEN DATEADD(MI,1140,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,419,DATEADD(DD, 1, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

			AND CONVERT(DATE,IFM.RECORDED_TIME) = PD.CALENDAR_DT

	)SEPSIS_2sC0RE

	

	LEFT OUTER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = PD.ADT_DEPARTMENT_ID

				AND CVS.VALUE_SET_ID = 3031 --DEPARTMENT ROLL UP

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +SER.PROV_NAME-- AS [text()]

                        FROM EMRDB.dbo.TREATMENT_TEAMS SUB

						INNER JOIN EMRDB.dbo.PROVIDERS SER ON SER.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

						AND (SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

						AND SUB.TRTMNT_TEAM_REL_C=2

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift1_RNs]	

	FROM  EMRDB.dbo.TREATMENT_TEAMS CAT where CAT.PAT_ENC_CSN_ID = PD.PAT_ENC_CSN_ID

	AND CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = PD.CALENDAR_DT

	AND (CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

	AND cat.TRTMNT_TEAM_REL_C=2--Registered Nurse

	group by cat.PAT_ENC_CSN_ID

	)Shift1_RNs

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +SER.PROV_NAME-- AS [text()]

                        FROM EMRDB.dbo.TREATMENT_TEAMS SUB

						INNER JOIN EMRDB.dbo.PROVIDERS SER ON SER.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

						AND (

								(CONVERT(DATE, SUB.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

								and

								(SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

							)

						AND SUB.TRTMNT_TEAM_REL_C=2

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift2_RNs]	

	FROM  EMRDB.dbo.TREATMENT_TEAMS CAT where CAT.PAT_ENC_CSN_ID = PD.PAT_ENC_CSN_ID

	AND (

			(CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

			and

			(CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

		)	

	AND cat.TRTMNT_TEAM_REL_C=2--Registered Nurse

	group by cat.PAT_ENC_CSN_ID

	)Shift2_RNs

	--CHARGE NURSE

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +SER.PROV_NAME-- AS [text()]

                        FROM EMRDB.dbo.TREATMENT_TEAMS SUB

						INNER JOIN EMRDB.dbo.PROVIDERS SER ON SER.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

						AND (SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

						AND SUB.TRTMNT_TEAM_REL_C=99--Charge Nurse

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift1_CNs]	

	FROM  EMRDB.dbo.TREATMENT_TEAMS CAT where CAT.PAT_ENC_CSN_ID = PD.PAT_ENC_CSN_ID

	AND CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = PD.CALENDAR_DT

	AND (CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

	AND cat.TRTMNT_TEAM_REL_C=99--Charge Nurse

	group by cat.PAT_ENC_CSN_ID

	)Shift1_CNs

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +SER.PROV_NAME-- AS [text()]

                        FROM EMRDB.dbo.TREATMENT_TEAMS SUB

						INNER JOIN EMRDB.dbo.PROVIDERS SER ON SER.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

						AND (

								(CONVERT(DATE, SUB.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

								and

								(SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

							)

						AND SUB.TRTMNT_TEAM_REL_C=99--Charge Nurse

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift2_CNs]	

	FROM  EMRDB.dbo.TREATMENT_TEAMS CAT where CAT.PAT_ENC_CSN_ID = PD.PAT_ENC_CSN_ID

	AND (

			(CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

			and

			(CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

		)	

	AND cat.TRTMNT_TEAM_REL_C=99--Charge Nurse

	group by cat.PAT_ENC_CSN_ID

	)Shift2_CNs

--where PAT_ENC_CSN_ID=1021422990

--SELECT * FROM #Main

SELECT

	[PATIENTS]

	, [MRN]

	, PAT_ENC_CSN_ID [CSN]

	, [IP Admit Time]

	, DEPARTMENT_ROLLUP

	, ADT_DEPARTMENT_ID [Department ID]

	, ADT_DEPARTMENT_NAME [Department]

	, Location

	, IN_DTTM [Department IN Time]

	, OUT_DTTM [Department OUT Time]

	, [Shift 1 Score Time]

	, [Shift 2 Score Time]	

	, [Shift 1 Score]

	, [Shift 2 Score]	

	, CALENDAR_DT

	, HS_FY

	, HS_FY_MONTH_NUMBER

	, MONTH_NAME

	, YEAR

	, LEFT(MONTH_NAME, 3 ) AS [Month Short Name]

	, [Discharge Time]

	, Shift1_RNs [Shift 1 RNs]

	, Shift2_RNs [Shift 2 RNs]

	, Shift1_CNs [Shift 1 CNs]

	, Shift2_CNs [Shift 2 CNs]

, CASE

	WHEN [Shift 2 Score Time] IS NOT NULL THEN 'GREEN'

	WHEN (CONVERT(DATE,OUT_DTTM) = CALENDAR_DT) AND 

		(OUT_DTTM<=SHIFT1_END) AND [Shift 2 Score Time] IS NULL THEN 'GREEN'	

	ELSE 'RED'

END AS SHIFT_2_COLOR

, CASE

	WHEN [Shift 1 Score Time] IS NOT NULL THEN 'GREEN'

	WHEN (CONVERT(DATE,IN_DTTM) = CALENDAR_DT) AND 

		(IN_DTTM>=SHIFT1_END) AND [Shift 1 Score Time] IS NULL THEN 'GREEN'	

	ELSE 'RED'

END AS SHIFT_1_COLOR

FROM #Base_Pop_OD_Scores-- WHERE PAT_ENC_CSN_ID=1021129982--1021422990

where ADT_DEPARTMENT_ID not in (

200108002,--	MAIN 2 NICU A

200108003,--	MAIN 2 NICU B

200108004,--	MAIN 2 NICU C

200108005,--	MAIN 3 NICU D

200108006,--	MAIN 3 NICU E

200108070,--	MAIN 3 CICU

200108118,--	MAIN CARDIOVASCULAR OR

200108049--	MAIN OR

)

order by pat_enc_csn_id, in_dttm, CALENDAR_DT



END
GO

-- ==== reports/USP_RPTS_IP_SEPSIS_REPORT.sql ====
CREATE     PROCEDURE [reports].[USP_IP_SEPSIS_REPORT]

@StartDate VARCHAR(20) = NULL,

@EndDate VARCHAR(20) = NULL



AS



/************************************************************************************ 

Author: Developer A/Developer B

Create date:  3/2/2022

Description: Used by PBI IP Sepsis Dashboard

===================================================================================== 

Revision Detail 

Created From: [USP_IP_SEPSIS]

Date			Who					Description 

------------------------------------------------------------------------------------- 

2022/3/2		Developer B			TKT-004 PBI Conversion. SP created from [USP_IP_SEPSIS]

2022/05/22		V_DEV001			Expansion Phase III Location update

2022/12/06		Developer B			TKT-005 change default start date to MB-12

===================================================================================== 

USAGE: 

exec [reportingDB].[reports].[USP_IP_SEPSIS_REPORT]

************************************************************************************/ 



SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

SET NOCOUNT ON;



	

DECLARE @dStartDate DATE

DECLARE @dEndDate DATE

DECLARE @dTestRun BIT

	

IF @StartDate IS NULL OR @StartDate = ''

	SET @dStartDate = EMRDB.[dbo].[fn_parse_date]('MB-12')

ELSE

	SET @dStartDate = EMRDB.[dbo].[fn_parse_date](@StartDate)

	

IF @EndDate IS NULL OR @EndDate = ''

	SET @dEndDate = EMRDB.[dbo].[fn_parse_date]('ME-1')--DEFAULTING TO PREVIOUS MONTH

ELSE

	SET @dEndDate = EMRDB.[dbo].[fn_parse_date](@EndDate)



IF OBJECT_ID(N'tempdb..#Main') IS NOT NULL DROP TABLE #Main;



SELECT DISTINCT

	PEH.PAT_ENC_CSN_ID

	, PEH.PAT_ID

	, PAT.PAT_MRN_ID

	, PAT.PAT_NAME

	, ZEG.NAME AS [Ethnic Group]

	, ZPR.NAME AS [Race]

	--, FEE.AGE_AT_ARRIVAL_MONTHS

	--, FEE.AGE_AT_ARRIVAL_YEARS

	, PEH.INPATIENT_DATA_ID

	, PEH.ADT_ARRIVAL_TIME

	, PEH.HOSP_ADMSN_TIME

	, PEH.HOSP_DISCH_TIME

	, PEH.INP_ADM_DATE

	, PEH.ED_DEPARTURE_TIME

	, ZDD.NAME AS [Disposition]

	, LOC.LOC_NAME [Location]

	, DATEDIFF(MM,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,PEH.HOSP_ADMSN_TIME)) + DATENAME(YEAR, CONVERT(DATE, PEH.HOSP_ADMSN_TIME)) AS DATE_STAMP

	, DATEDIFF(HH, PEH.HOSP_ADMSN_TIME, PEH.HOSP_DISCH_TIME) AS LOS_HRS

INTO 

	#Main

FROM 

EMRDB.dbo.V_HOSPITAL_TRANSACTIONS HTR

INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON HTR.PAT_ENC_CSN_ID = PEH.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

LEFT OUTER JOIN EMRDB.dbo.REF_DISCHARGE_DISPOSITION ZDD ON ZDD.DISCH_DISP_C = PEH.DISCH_DISP_C

LEFT OUTER JOIN EMRDB.dbo.REF_ETHNIC_GROUP ZEG ON ZEG.ETHNIC_GROUP_C = PAT.ETHNIC_GROUP_C

LEFT OUTER JOIN EMRDB.dbo.PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PAT_ID = PAT.PAT_ID AND RACE.LINE=1

LEFT OUTER JOIN EMRDB.dbo.REF_PATIENT_RACE ZPR ON ZPR.PATIENT_RACE_C = RACE.PATIENT_RACE_C

LEFT OUTER JOIN EMRDB.dbo.DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = PEH.DEPARTMENT_ID

LEFT OUTER JOIN EMRDB.dbo.LOCATIONS LOC ON LOC.LOC_ID = DEP.REV_LOC_ID

WHERE

PEH.INP_ADM_DATE IS NOT NULL

AND CONVERT(DATE,HTR.SERVICE_DATE) BETWEEN @dStartDate AND @dEndDate



--CHIEF COMPLIANT

IF OBJECT_ID(N'tempdb..#Base_Pop_ENC_Reason') IS NOT NULL DROP TABLE #Base_Pop_ENC_Reason;

SELECT  DISTINCT   CAT.PAT_ENC_CSN_ID,

            STUFF((    SELECT '% ' +EDG.DX_NAME-- AS [text()]

                        FROM #Main SUB

						INNER JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES PED ON PED.PAT_ENC_CSN_ID = SUB.PAT_ENC_CSN_ID AND PED.LINE>1

						INNER JOIN EMRDB.dbo.DIAGNOSES EDG ON EDG.DX_ID = PED.DX_ID

						WHERE

                        SUB.PAT_ENC_CSN_ID = CAT.PAT_ENC_CSN_ID

						ORDER BY LINE

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM  #Main CAT





--SELECT * FROM #Base_Pop_ENC_Reason

IF OBJECT_ID(N'tempdb..#EncounterWeights') IS NOT NULL DROP TABLE #EncounterWeights;

SELECT

	A.PAT_ENC_CSN_ID

	, CAST(ROUND(CONVERT(FLOAT, MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

	, ROW_NUMBER() OVER(PARTITION BY A.PAT_ENC_CSN_ID ORDER BY C.RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#EncounterWeights

FROM 

	#Main A

INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS B ON A.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS C ON B.FSD_ID = C.FSD_ID AND  C.FLO_MEAS_ID='94'



/*GETTING ENCOUNTERS WITHIN GIVEN DATE RANGES SO WE DON'T HAVE TO QUERY ON WHOLE DATABASE FOR EACH CRITERIA*/

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;



SELECT DISTINCT

	PEH.PAT_ENC_CSN_ID

	, PEH.PAT_ID

	, VAPLH.ADT_DEPARTMENT_ID

	, VAPLH.ADT_DEPARTMENT_NAME

	, CVS.CODE_DESC AS DEPARTMENT_ROLLUP

	, VAPLH.IN_DTTM

	, VAPLH.OUT_DTTM

	, PEH.INPATIENT_DATA_ID

	, #Main.AGE_MONTHS

	, #Main.AGE_YEARS

	, PEH.ADT_ARRIVAL_TIME

	--, PEH.HOSP_ADMSN_TIME

	--, PEH.HOSP_DISCH_TIME

	--, PEH.INP_ADM_DATE

	, PEH.ED_DEPARTURE_TIME

	--, PEH.ED_DISPOSITION_C

	--, ZED.NAME AS [Disposition]

	--, DATEDIFF(MM,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME) AS AGE_MONTHS

	--, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	--, DATENAME(month, CONVERT(DATE,PEH.HOSP_ADMSN_TIME)) + DATENAME(YEAR, CONVERT(DATE, PEH.HOSP_ADMSN_TIME)) AS DATE_STAMP

	--, DATEDIFF(HH, PEH.HOSP_ADMSN_TIME, PEH.HOSP_DISCH_TIME) AS LOS_HRS



INTO 

	#Base_Pop



FROM #Main

INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = #Main.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

INNER JOIN EMRDB.dbo.V_PATIENT_LOCATION_HISTORY VAPLH ON VAPLH.PAT_ENC_CSN = PEH.PAT_ENC_CSN_ID AND VAPLH.ADT_DEPARTMENT_ID IS NOT NULL

INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = VAPLH.ADT_DEPARTMENT_ID

			AND CVS.VALUE_SET_ID = 3031 --DEPARTMENT ROLL UP

LEFT OUTER JOIN EMRDB.dbo.REF_ED_DISPOSITION ZED ON ZED.ED_DISPOSITION_C = PEH.ED_DISPOSITION_C

--SELECT * FROM #Base_Pop



--POSITIVE ED SEPSIS SCORES & ED LOS

IF OBJECT_ID(N'tempdb..#Base_Pop_Severe_ED_Scores') IS NOT NULL DROP TABLE #Base_Pop_Severe_ED_Scores;

SELECT

	BP.PAT_ENC_CSN_ID

	, CEILING(CONVERT(FLOAT,DATEDIFF(MI, BP.ADT_ARRIVAL_TIME,BP.ED_DEPARTURE_TIME))/60) HoursInED--CHECK WITH STEPHANIE ON 

	, BP.ADT_ARRIVAL_TIME

	, IFM.MEAS_VALUE

	, IFM.RECORDED_TIME

	, BP.ED_DEPARTURE_TIME

	, ROW_NUMBER() OVER(PARTITION BY BP.PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#Base_Pop_Severe_ED_Scores 

FROM

	#Main BP 

INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID --and bp.PAT_ENC_CSN_ID=1016405505 

INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = PEH.INPATIENT_DATA_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID and

	IFM.FLO_MEAS_ID IN ('9000161709','9000002613')--SEPSIS SCORE--ADDED NEW ED SEPSIS SCORE 9000002613 ON 10.01.2019

	and (IFM.RECORDED_TIME <=  BP.ED_DEPARTURE_TIME)



IF OBJECT_ID(N'tempdb..#EDPosScore_EDLOS') IS NOT NULL DROP TABLE #EDPosScore_EDLOS;

SELECT

	PAT_ENC_CSN_ID

	, HoursInED

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO 

	#EDPosScore_EDLOS

FROM 

	#Base_Pop_Severe_ED_Scores

WHERE

	MEAS_VALUE > 4

--POSITIVE SEPSIS SCORES

IF OBJECT_ID(N'tempdb..#Base_Pop_OD_Scores') IS NOT NULL DROP TABLE #Base_Pop_OD_Scores;

SELECT

	BP.PAT_ENC_CSN_ID

	, BP.ADT_DEPARTMENT_ID

	, BP.ADT_DEPARTMENT_NAME

	, BP.IN_DTTM

	, BP.OUT_DTTM

	, IFM.MEAS_VALUE

	, IFM.RECORDED_TIME

	, Huddle_Note.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP]

	, Huddle_Note.[Huddle Date]

	, Huddle_Note.[Huddle Time]

	, Huddle_Note.[PATIENTS Assessed by MD/PNP]

	, Huddle_Note.[Physician Name]

	, Huddle_Note.[Additional Orders Received/Placed by MD/PNP]

	, ALERTNOTACTIVATED.[CLINICAL_ALERTS Not Activated Reason]

	, ALERTNOTACTIVATED.[CLINICAL_ALERTS Not Activated Comment]

	, ALERTACTIVATED.[CLINICAL_ALERTS Activated Comment]

	, ROW_NUMBER() OVER(PARTITION BY BP.PAT_ENC_CSN_ID, BP.ADT_DEPARTMENT_ID, BP.IN_DTTM ORDER BY ifm.RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#Base_Pop_OD_Scores 

FROM

	#Base_Pop BP 

INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON PEH.INPATIENT_DATA_ID = IFR.INPATIENT_DATA_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

LEFT OUTER JOIN

	(

		SELECT

			IFR.INPATIENT_DATA_ID, IFM_ALERTNOTACTIVATED.FSD_ID, IFM_ALERTNOTACTIVATED.RECORDED_TIME, IFM_ALERTNOTACTIVATED.MEAS_VALUE AS [CLINICAL_ALERTS Not Activated Reason], IFM_ALERTNOTACTIVATED.MEAS_COMMENT as [CLINICAL_ALERTS Not Activated Comment]

		FROM EMRDB.dbo.FLOWSHEET_RECORDS IFR

			INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM_ALERTNOTACTIVATED ON IFM_ALERTNOTACTIVATED.FSD_ID = IFR.FSD_ID

		WHERE

			IFM_ALERTNOTACTIVATED.FLO_MEAS_ID='9000003159'

	)ALERTNOTACTIVATED ON ALERTNOTACTIVATED.INPATIENT_DATA_ID = IFR.INPATIENT_DATA_ID

		AND ALERTNOTACTIVATED.FSD_ID = IFR.FSD_ID

		AND ALERTNOTACTIVATED.RECORDED_TIME = IFM.RECORDED_TIME

	LEFT OUTER JOIN

	(

		SELECT

			ALT.ALT_ID,

			ALT.PAT_CSN,

			HIS.ALT_ACTION_INST,

			COALESCE(HIS.SPEC_OVR_CMNT,' ')+ RSN.NAME [CLINICAL_ALERTS Activated Comment]

		FROM EMRDB.dbo.CLINICAL_ALERTS ALT

			INNER JOIN EMRDB.dbo.ALERT_HISTORY HIS ON HIS.ALT_ID = ALT.ALT_ID

			INNER JOIN EMRDB.dbo.REF_ALERT_OVERRIDE_REASONS RSN ON RSN.ALRT_SP_OVR_RSN_C = HIS.SPEC_OVR_RSN_C

		WHERE ALT.BPA_LOCATOR_ID=900400001--BASE 2019 HS OD SCORE SEPSIS >2 [900400001]

	)ALERTACTIVATED ON ALERTACTIVATED.PAT_CSN = PEH.PAT_ENC_CSN_ID

		AND ALERTACTIVATED.ALT_ACTION_INST = IFM.RECORDED_TIME

--huddle notes within 30 minutes before or 120 minutes after OD Score

outer apply (select a.INPATIENT_DATA_ID

			 ,a.OD_SCORE_RECORDED_TIME

			 ,max(case WHEN a.FLO_MEAS_ID = '9000002705' THEN a.MEAS_VALUE end) as "Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP"

			 ,max(CASE WHEN a.FLO_MEAS_ID = '9000002732' THEN try_cast(DATEADD(day,try_cast(a.MEAS_VALUE as int),'1840-12-31') as date) end) as "Huddle Date"

			 --,max(case WHEN a.FLO_MEAS_ID = '9000002733' THEN try_cast(DATEADD(second,try_cast(a.MEAS_VALUE as int),'1840-12-31') as time) end) as "Huddle Time" -- time column doesn't work in power bi 

			 ,max(case WHEN a.FLO_MEAS_ID = '9000002733' THEN trim(right(try_cast(DATEADD(second,try_cast(MEAS_VALUE as int),'1840-12-31') as varchar(20)),7)) end) as "Huddle Time"

			 ,max(case WHEN a.FLO_MEAS_ID = '9000002706' THEN a.MEAS_VALUE end) as "PATIENTS Assessed by MD/PNP"

			 ,max(case WHEN a.FLO_MEAS_ID = '9000002734' THEN a.MEAS_VALUE end) as "Physician Name"

			 ,max(case WHEN a.FLO_MEAS_ID = '9000002707' THEN a.MEAS_VALUE end) as "Additional Orders Received/Placed by MD/PNP"

			 from

			 (

				select IFR.INPATIENT_DATA_ID

				,IFM.RECORDED_TIME as OD_SCORE_RECORDED_TIME

				,FLOWSHEET_MEASUREMENTS.FLO_MEAS_ID

				,FLOWSHEET_MEASUREMENTS.RECORDED_TIME

				,FLOWSHEET_MEASUREMENTS.MEAS_VALUE

				,row_number() over (partition by FLOWSHEET_RECORDS.INPATIENT_DATA_ID, IFM.RECORDED_TIME, FLOWSHEET_MEASUREMENTS.FLO_MEAS_ID order by FLOWSHEET_MEASUREMENTS.RECORDED_TIME) rownumber

				 from  EMRDB.dbo.FLOWSHEET_RECORDS

				 INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS ON FLOWSHEET_RECORDS.FSD_ID = FLOWSHEET_MEASUREMENTS.FSD_ID

				 where FLOWSHEET_RECORDS.INPATIENT_DATA_ID = IFR.INPATIENT_DATA_ID

				 and datediff(minute,IFM.RECORDED_TIME,FLOWSHEET_MEASUREMENTS.RECORDED_TIME) between -30 and 180--WAS -120 UNTIL 03.01.2021 

				 and FLOWSHEET_MEASUREMENTS.FLO_MEAS_ID in ('9000002705','9000002732','9000002733','9000002706','9000002734','9000002707')

				 and FLOWSHEET_MEASUREMENTS.MEAS_VALUE is not null

			 ) a

			 where a.rownumber = 1

			 group by a.INPATIENT_DATA_ID, a.OD_SCORE_RECORDED_TIME

			 ) Huddle_Note

WHERE 

	IFM.FLO_MEAS_ID IN ('9000161711','9000002644') --ORGAN DYSFUNCTION SCORE

	--and IFM.RECORDED_TIME BETWEEN @dStartDate AND @dEndDate--BP.IN_DTTM AND BP.OUT_DTTM--this is because a paitient's IN DTTM could be in the current month and out DTTM could be in next month. Per Stakeholder A, we want to look for scores documented in the same time frame.

	AND IFM.RECORDED_TIME BETWEEN BP.IN_DTTM AND COALESCE(BP.OUT_DTTM,GETDATE())

--SELECT * FROM #Base_Pop_OD_Scores





IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	--, IFM.RECORDED_TIME

	, CASE

		WHEN 

			B.AGE_MONTHS < 2 AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 65

			OR

			(B.AGE_MONTHS >= 2 AND B.AGE_MONTHS < 12) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 70

			OR

			(B.AGE_YEARS >= 1 AND B.AGE_YEARS < 2) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 80

			OR

			(B.AGE_YEARS >= 2 AND B.AGE_YEARS < 6) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 90

			OR

			(B.AGE_YEARS >= 6 AND B.AGE_YEARS < 13) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 100

			OR

			B.AGE_YEARS >= 13 AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 110

		THEN IFM.MEAS_VALUE--IFM.RECORDED_TIME

		ELSE NULL

	END AS MEAS_VALUE

	, IFM.RECORDED_TIME

	, LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) AS SYSTOLIC

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY IFM.RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#Hypotension 

FROM

	#Base_Pop B

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID AND IFM.FLO_MEAS_ID = '95' 

WHERE 

	IFM.RECORDED_TIME IS NOT NULL

	AND (IFM.RECORDED_TIME BETWEEN @dStartDate AND @dEndDate)

	AND IFM.MEAS_VALUE IS NOT NULL

--SELECT * FROM #Hypotension WHERE TIME_LINE=1



IF OBJECT_ID(N'tempdb..#ODHYPO') IS NOT NULL DROP TABLE #ODHYPO;

SELECT

CASE WHEN LASTHYPO.MEAS_VALUE IS NOT NULL THEN LASTHYPO.RECORDED_TIME ELSE NULL END [LAST Hypotension Time],

LASTHYPO.MEAS_VALUE [LAST Hypotension Value],

CASE WHEN LASTHYPO.MEAS_VALUE IS NOT NULL AND (LASTHYPO.RECORDED_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM) THEN 'Y' ELSE 'N' END AS [LAST Hypotension taken in Dept Y/N],

A.*,

CASE WHEN FIRSTHYPO.MEAS_VALUE IS NOT NULL THEN FIRSTHYPO.RECORDED_TIME ELSE NULL END [FIRST Hypotension Time],

FIRSTHYPO.MEAS_VALUE [FIRST Hypotension Value],

CASE WHEN FIRSTHYPO.MEAS_VALUE IS NOT NULL AND (FIRSTHYPO.RECORDED_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM) THEN 'Y' ELSE 'N' END AS [FIRST Hypotension taken in Dept Y/N]

INTO #ODHYPO

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 HYPO.RECORDED_TIME, HYPO.MEAS_VALUE FROM #Hypotension HYPO

	WHERE HYPO.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND HYPO.RECORDED_TIME<A.RECORDED_TIME

	ORDER BY HYPO.RECORDED_TIME DESC

)LASTHYPO

OUTER APPLY

(

	SELECT TOP 1 HYPO.RECORDED_TIME, HYPO.MEAS_VALUE FROM #Hypotension HYPO

	WHERE HYPO.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND HYPO.RECORDED_TIME>=A.RECORDED_TIME

	ORDER BY HYPO.RECORDED_TIME ASC

)FIRSTHYPO



------------------------------------------------------END OF HYPO------------------------------------------------------------------

------------------------------------------------------ABX------------------------------------------------------------------

-- All encounters from #Base_pop where ABX was administered

IF OBJECT_ID(N'tempdb..#BasePopABX') IS NOT NULL DROP TABLE #BasePopABX;

SELECT

	OM.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, CM.NAME

	, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

	, MAI.SIG AS BOLUS_VOLUME

	, ROW_NUMBER() OVER(PARTITION BY OM.PAT_ENC_CSN_ID ORDER BY MAI.TAKEN_TIME) TIME_LINE

INTO

	#BasePopABX

FROM

	#Base_Pop B

INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM	ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID AND CM.THERA_CLASS_C = 11 --Antibiotics

INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

WHERE

	MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

	AND (MAI.TAKEN_TIME BETWEEN @dStartDate AND @dEndDate)

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

--VALUES BELOW ADDED TO THE CODE ON STEPHANIE'S REQUEST DURING VALIDATION.

	AND CM.ROUTE NOT IN ('intratympanic'

						, 'intraocular'

						, 'Apply externally'

						, 'ophthalmic'

						, 'oral'

						, 'Topical'

						, 'nasal'

						, 'intramuscular'

						, 'otic'

						, 'intravitreal'

						, 'vaginal'

						, 'inhalation'

						, 'intravenous'

						)							



--SELECT * FROM #BasePopABX where PAT_ENC_CSN_ID=1016093600--1015370131



--SELECT * FROM #BasePopABX where PAT_ENC_CSN_ID=1016093600--1015370131

--select * from #Base_Pop_OD_Scores where PAT_ENC_CSN_ID=1016093600

IF OBJECT_ID(N'tempdb..#ODABX') IS NOT NULL DROP TABLE #ODABX;

SELECT

LASTABX.ABX_ADMIN_TIME LASTABX_TIME,

LASTABX.NAME LASTABX_NAME,

LASTABX.BOLUS_VOLUME AS [LAST ABX Volume],

LASTABX.[Last ABX to OD Score Time],

CASE WHEN LASTABX.ABX_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST ABX Given in Dept Y/N],

A.*,

FIRSTABX.ABX_ADMIN_TIME FIRSTABX_TIME,

FIRSTABX.NAME FIRSTABX_NAME,

FIRSTABX.BOLUS_VOLUME AS [FIRST ABX Volume],

FIRSTABX.[OD Score to First ABX Time],

CASE WHEN FIRSTABX.ABX_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST ABX Given in Dept Y/N]

INTO #ODABX

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 ABX.ABX_ADMIN_TIME, ABX.ADT_DEPARTMENT_ID, ABX.IN_DTTM, ABX.OUT_DTTM, ABX.NAME, ABX.PAT_ENC_CSN_ID, ABX.ADT_DEPARTMENT_NAME, ABX.BOLUS_VOLUME, DATEDIFF(MI,ABX_ADMIN_TIME,A.RECORDED_TIME) AS [Last ABX to OD Score Time] FROM #BasePopABX ABX

	WHERE ABX.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ABX.ABX_ADMIN_TIME<A.RECORDED_TIME

	ORDER BY ABX.ABX_ADMIN_TIME DESC

)LASTABX

OUTER APPLY

(

	SELECT TOP 1 ABX.ABX_ADMIN_TIME, ABX.ADT_DEPARTMENT_ID, ABX.IN_DTTM, ABX.OUT_DTTM, ABX.NAME, ABX.PAT_ENC_CSN_ID, ABX.ADT_DEPARTMENT_NAME, ABX.BOLUS_VOLUME, DATEDIFF(MI,A.RECORDED_TIME,ABX_ADMIN_TIME) AS [OD Score to First ABX Time] FROM #BasePopABX ABX

	WHERE ABX.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ABX.ABX_ADMIN_TIME>=A.RECORDED_TIME

	ORDER BY ABX.ABX_ADMIN_TIME ASC

)FIRSTABX

------------------------------------------------------END OF ABX------------------------------------------------------------------



------------------------------------------------------ORDER SET------------------------------------------------------------------

-- All encounters from #Base_pop where Bolus was administered

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OM.ORDER_DTTM

	--, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID, B.ADT_DEPARTMENT_ID, B.IN_DTTM ORDER BY OM.ORDER_DTTM ASC) AS TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OM.ORDER_DTTM ASC) AS TIME_LINE

	, OM.PRL_ORDERSET_ID

INTO

	#SSOrderSet 

FROM

	#Base_Pop B

INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE

	OM.PRL_ORDERSET_ID IN (400001)-- (40400100, 40400058, 40400196, 40400153, 4058600002, 400001) --Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway

	AND (OM.ORDER_DTTM BETWEEN @dStartDate AND @dEndDate)

	--AND OM.ORDER_DTTM BETWEEN B.IN_DTTM AND B.OUT_DTTM

--SELECT * FROM #SSOrderSet



IF OBJECT_ID(N'tempdb..#ODORDSET') IS NOT NULL DROP TABLE #ODORDSET;

SELECT

LASTOS.ORDER_DTTM [LAST OrderSet Time],

LASTOS.PRL_ORDERSET_ID [LAST OrderSet ID],

CASE WHEN LASTOS.ORDER_DTTM BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST OrderSet in Dept Y/N],

A.*,

FIRSTOS.ORDER_DTTM [FIRST OrderSet Time],

FIRSTOS.PRL_ORDERSET_ID [FIRST OrderSet ID],

CASE WHEN FIRSTOS.ORDER_DTTM BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST OrderSet in Dept Y/N]

INTO #ODORDSET

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 SOS.ORDER_DTTM, SOS.PRL_ORDERSET_ID FROM #SSOrderSet SOS

	WHERE SOS.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SOS.ORDER_DTTM<A.RECORDED_TIME

	ORDER BY SOS.ORDER_DTTM DESC

)LASTOS

OUTER APPLY

(

	SELECT TOP 1 SOS.ORDER_DTTM, SOS.PRL_ORDERSET_ID FROM #SSOrderSet SOS

	WHERE SOS.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SOS.ORDER_DTTM>=A.RECORDED_TIME

	ORDER BY SOS.ORDER_DTTM ASC

)FIRSTOS

------------------------------------------------------END OF ORDER SET------------------------------------------------------------------



------------------------------------------------------BOLUS------------------------------------------------------------------



IF OBJECT_ID(N'tempdb..#BasePopBolus') IS NOT NULL DROP TABLE #BasePopBolus;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	,B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, MAI.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, CM.NAME AS Medication

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY MAI.TAKEN_TIME ASC) TIME_LINE

	, MAI.SIG AS BOLUS_VOLUME

INTO

	#BasePopBolus 

FROM

	#Base_Pop B

INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

WHERE

	MAI.TAKEN_TIME IS NOT NULL --ADMINISTERED BOLUS ONLY

	AND (MAI.TAKEN_TIME BETWEEN @dStartDate AND @dEndDate)

	AND (OM.MEDICATION_ID IN (700001  --SODIUM CHLORIDE 0.99 % IV BOLUS

							, 7000739 --LACTATED RINGERS IV BOLUS

							, 700003    --ALBUMIN, HUMAN 95 % INTRAVENOUS SOLUTION

							, 7006331 --ELECTROLYE-A IV Bolus (PLASMALYTE)

							, 700002	--SODIUM CHLORIDE 0.99 % INJECTION SYRINGE

							)

		OR (OM.MEDICATION_ID = 700004)

	AND OM.HV_DISCR_FREQ_ID = '300902') -- FREQUENCY = ONCE 

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

	AND CONVERT(NUMERIC, MAI.SIG ) > 95.0

--SELECT * FROM #BasePopBolus

IF OBJECT_ID(N'tempdb..#OdboL') IS NOT NULL DROP TABLE #OdboL;

SELECT

LASTBOL.BOLUS_ADMIN_TIME [LAST Bolus Time],

LASTBOL.Medication [LAST Bolus],

LASTBOL.BOLUS_VOLUME AS [LAST Bolus Volume],

LASTBOL.[Last Bolus to Screen Time],

CASE WHEN LASTBOL.BOLUS_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST Bolus Given in Dept Y/N],

A.*,

FIRSTBOL.BOLUS_ADMIN_TIME [FIRST Bolus Time],

FIRSTBOL.Medication [FIRST Bolus],

FIRSTBOL.BOLUS_VOLUME AS [FIRST Bolus Volume],

FIRSTBOL.[Screen Time to First Bolus],

CASE WHEN FIRSTBOL.BOLUS_ADMIN_TIME BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST Bolus Given in Dept Y/N]

INTO #OdboL

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 BOL.BOLUS_ADMIN_TIME, BOL.BOLUS_VOLUME, BOL.Medication, DATEDIFF(MI, BOLUS_ADMIN_TIME,A.RECORDED_TIME) AS [Last Bolus to Screen Time] FROM #BasePopBolus BOL

	WHERE BOL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BOL.BOLUS_ADMIN_TIME<A.RECORDED_TIME

	ORDER BY BOL.BOLUS_ADMIN_TIME DESC

)LASTBOL

OUTER APPLY

(

	SELECT TOP 1 BOL.BOLUS_ADMIN_TIME, BOL.BOLUS_VOLUME, BOL.Medication, DATEDIFF(MI, A.RECORDED_TIME,BOLUS_ADMIN_TIME) AS [Screen Time to First Bolus] FROM #BasePopBolus BOL

	WHERE BOL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BOL.BOLUS_ADMIN_TIME>=A.RECORDED_TIME

	ORDER BY BOL.BOLUS_ADMIN_TIME ASC

)FIRSTBOL



------------------------------------------------------END OF BOLUS------------------------------------------------------------------

------------------------------------------------------CVL TIMES------------------------------------------------------------------



/*CVL TIME - TEST CSN 1016010350*/

IF OBJECT_ID(N'tempdb..#ALLCVLTime') IS NOT NULL DROP TABLE #ALLCVLTime;

SELECT DISTINCT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, ILN.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID, B.ADT_DEPARTMENT_ID, B.IN_DTTM ORDER BY ILN.PLACEMENT_INSTANT) TIME_LINE

INTO 

	#ALLCVLTime

FROM 

	#Base_Pop B

INNER JOIN EMRDB.dbo.LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID 

INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = ILN.FLO_MEAS_ID

			AND CVS.VALUE_SET_ID = 3022 --CVL CODES

WHERE (ILN.PLACEMENT_INSTANT BETWEEN @dStartDate AND @dEndDate)

--WHERE ILN.PLACEMENT_INSTANT BETWEEN B.IN_DTTM AND B.OUT_DTTM



--SELECT * FROM #ALLCVLTime

IF OBJECT_ID(N'tempdb..#ODCVL') IS NOT NULL DROP TABLE #ODCVL;

SELECT

LASTCVL.PLACEMENT_INSTANT [LAST CVL Time],

CASE WHEN LASTCVL.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST CVL in Dept Y/N],

A.*,

FIRSTCVL.PLACEMENT_INSTANT [FIRST CVL Time],

CASE WHEN FIRSTCVL.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST CVL in Dept Y/N]

INTO #ODCVL

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 CVL.PLACEMENT_INSTANT FROM #ALLCVLTime CVL

	WHERE CVL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CVL.PLACEMENT_INSTANT<A.RECORDED_TIME

	ORDER BY CVL.PLACEMENT_INSTANT DESC

)LASTCVL

OUTER APPLY

(

	SELECT TOP 1 CVL.PLACEMENT_INSTANT FROM #ALLCVLTime CVL

	WHERE CVL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CVL.PLACEMENT_INSTANT>=A.RECORDED_TIME

	ORDER BY CVL.PLACEMENT_INSTANT ASC

)FIRSTCVL



------------------------------------------------------END OF CVL TIMES------------------------------------------------------------------



------------------------------------------------------PRESSORS TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#Pressors') IS NOT NULL DROP TABLE #Pressors;

SELECT DISTINCT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, MAI.TAKEN_TIME

	, GMR.GROUPER_ID

	, CM.NAME AS MEDICATION

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY MAI.TAKEN_TIME) AS TIME_LINE

INTO

	#Pressors 

FROM

	#Base_Pop B

LEFT JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

LEFT JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

LEFT JOIN EMRDB.dbo.GROUPER_MED_RECORDS GMR ON GMR.EXP_MEDS_LIST_ID = CM.MEDICATION_ID

LEFT JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

LEFT JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE

	GMR.GROUPER_ID IN ('8000100'    -- HS RX EPINEPHRINE SEPSIS

							, '8000101' -- HS RX DOPAMINE SEPSIS

							, '8000102' -- HS RX DOBUTAMINE SEPSIS

							, '8000103' -- HS RX MILRINONE SEPSIS

							, '8000104' -- HS RX NOREPINEPHRINE SEPSIS

						)

	AND (MAI.TAKEN_TIME BETWEEN @dStartDate AND @dEndDate)

	AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

							, '7'			--RESTARTED

							, '102'		--GIVEN BY OTHER

							, '105'		--NEW CARTRIDGE

							, '113'		--GIVEN DURING DOWNTIME

							, '114'		--STARTED DURING DOWNTIME

							, '115'		--MEDICATION APPLIED

							, '122'		--CONTINUED FROM OR

							, '124'		--SELF ADMINISTERED VIA PUMP

							, '132'		--CONTINUED FROM PREVIOUS ORDER

							, '143'		--REDOSE

							, '1604'		--INFUSION GREATER THAN 15 MIN

							, '1605'		--INFUSION LESS THAN 15 MIN

							, '1607'		--NEW CARTRIDGE

							, '6'			--NEW BAG

							)

	AND MAI.ROUTE_C = 11 --INTRAVENOUS

--SELECT * FROM #Pressors



IF OBJECT_ID(N'tempdb..#ODPressorSummary') IS NOT NULL DROP TABLE #ODPressorSummary;

SELECT

PAT_ENC_CSN_ID,

CASE WHEN GROUPER_ID = '8000100'   THEN 'EPINEPHRINE' -- HS RX EPINEPHRINE SEPSIS

	WHEN GROUPER_ID =  '8000101' THEN 'DOPAMINE'

	WHEN GROUPER_ID = '8000102'   THEN 'DOBUTAMINE'

	WHEN GROUPER_ID = '8000103'   THEN 'MILRINONE'

	WHEN GROUPER_ID = '8000104'   THEN 'NOREPINEPHRINE'

	END PRESSOR,

	COUNT(TAKEN_TIME) AS MYC

INTO #ODPressorSummary

FROM #Pressors

GROUP BY PAT_ENC_CSN_ID, GROUPER_ID



IF OBJECT_ID ('TEMPDB..#ODPressorPivot') IS NOT NULL DROP TABLE #ODPressorPivot



SELECT



	PAT_ENC_CSN_ID, PVT.[EPINEPHRINE] AS [EPINEPHRINE], PVT.[DOPAMINE] AS [DOPAMINE], PVT.[DOBUTAMINE] AS [DOBUTAMINE],

	PVT.[MILRINONE] AS [MILRINONE], PVT.[NOREPINEPHRINE] AS [NOREPINEPHRINE]

	INTO #ODPressorPivot

	FROM #ODPressorSummary

	PIVOT( MAX(myc)

	FOR PRESSOR IN ([EPINEPHRINE],[DOPAMINE],[DOBUTAMINE],[MILRINONE],[NOREPINEPHRINE])) AS PVT

--select * from #ODPressorPivot

------------------------------------------------------END OF PRESSORS TIMES------------------------------------------------------------------

------------------------------------------------------SVO2 TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#SVO2') IS NOT NULL DROP TABLE #SVO2;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_TIME AS SVO2OrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID

INTO 

	#SVO2

FROM 

	#Base_Pop B

	INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS ON B.PAT_ENC_CSN_ID = LAB_ORDER_RESULTS.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID IN (5000001861, 5000000478)

AND (OP.ORDER_TIME BETWEEN @dStartDate AND @dEndDate)

--SELECT * FROM #SVO2

IF OBJECT_ID(N'tempdb..#ODSVO2') IS NOT NULL DROP TABLE #ODSVO2;

SELECT

LASTSVO2.SVO2OrderTime [LAST SVO2 Time],

CASE WHEN LASTSVO2.SVO2OrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST SVO2 in Dept Y/N],

A.*,

FIRSTSVO2.SVO2OrderTime [FIRST SVO2 Time],

CASE WHEN FIRSTSVO2.SVO2OrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST SVO2 in Dept Y/N]

INTO #ODSVO2

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 SVO2.SVO2OrderTime FROM #SVO2 SVO2

	WHERE SVO2.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SVO2.SVO2OrderTime<A.RECORDED_TIME

	ORDER BY SVO2.SVO2OrderTime DESC

)LASTSVO2

OUTER APPLY

(

	SELECT TOP 1 SVO2.SVO2OrderTime FROM #SVO2 SVO2

	WHERE SVO2.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND SVO2.SVO2OrderTime>=A.RECORDED_TIME

	ORDER BY SVO2.SVO2OrderTime ASC

)FIRSTSVO2

------------------------------------------------------END OF SVO2 TIMES------------------------------------------------------------------



------------------------------------------------------LACTIC ACID TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_PROC_ID

	, OP.ORDER_TIME AS MBOrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

INTO 

	#LacticAcid

FROM 

	#Base_Pop B

INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS ON LAB_ORDER_RESULTS.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID IN (5000000446, 5000000447, 5000000449)

AND (OP.ORDER_TIME BETWEEN @dStartDate AND @dEndDate)

--SELECT * FROM #LacticAcid WHERE TIME_LINE=1 AND MBOrderTime=RESULT_TIME

IF OBJECT_ID(N'tempdb..#ODLA') IS NOT NULL DROP TABLE #ODLA;

SELECT

LASTLA.MBOrderTime [LAST LacticAcid Order Time],

LASTLA.ORD_VALUE AS [LAST LacticAcid Result],

CASE WHEN LASTLA.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST LacticAcid in Dept Y/N],

A.*,

FIRSTLA.MBOrderTime [FIRST LacticAcid Order Time],

LASTLA.ORD_VALUE AS [FIRST LacticAcid Result],

CASE WHEN FIRSTLA.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST LacticAcid in Dept Y/N]

INTO #ODLA

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 LA.MBOrderTime, LA.ORD_VALUE FROM #LacticAcid LA

	WHERE LA.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND LA.MBOrderTime<A.RECORDED_TIME

	ORDER BY LA.MBOrderTime DESC

)LASTLA

OUTER APPLY

(

	SELECT TOP 1 LA.MBOrderTime, LA.ORD_VALUE FROM #LacticAcid LA

	WHERE LA.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND LA.MBOrderTime>=A.RECORDED_TIME

	ORDER BY LA.MBOrderTime ASC

)FIRSTLA

--SELECT * FROM #ODLA

------------------------------------------------------END OF LACTIC ACID TIMES------------------------------------------------------------------



------------------------------------------------------PROCALCITONIN TIMES------------------------------------------------------------------

/*PROCALCITONIN*/

IF OBJECT_ID(N'tempdb..#Procalcitonin') IS NOT NULL DROP TABLE #Procalcitonin;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_TIME AS MBOrderTime

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID



INTO 

	#Procalcitonin

FROM 

	#Base_Pop B

INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS ON LAB_ORDER_RESULTS.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON OP.ORDER_PROC_ID = LAB_ORDER_RESULTS.ORDER_PROC_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID = 500001 --COULD USE PROC CODE ALSO.... LAB014

AND (OP.ORDER_TIME BETWEEN @dStartDate AND @dEndDate)

--SELECT * FROM #Procalcitonin

IF OBJECT_ID(N'tempdb..#ODPROCAL') IS NOT NULL DROP TABLE #ODPROCAL;

SELECT

LASTPRO.MBOrderTime [LAST Procalcitonin Order Time],

LASTPRO.ORD_VALUE AS [LAST Procalcitonin Result],

CASE WHEN LASTPRO.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST Procalcitonin in Dept Y/N],

A.*,

FIRSTPRO.MBOrderTime [FIRST Procalcitonin Order Time],

FIRSTPRO.ORD_VALUE AS [FIRST Procalcitonin Result],

CASE WHEN FIRSTPRO.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST Procalcitonin in Dept Y/N]

INTO #ODPROCAL

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 PROCAL.MBOrderTime, PROCAL.ORD_VALUE FROM #Procalcitonin PROCAL

	WHERE PROCAL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PROCAL.MBOrderTime<A.RECORDED_TIME

	ORDER BY PROCAL.MBOrderTime DESC

)LASTPRO

OUTER APPLY

(

	SELECT TOP 1 PROCAL.MBOrderTime, PROCAL.ORD_VALUE FROM #Procalcitonin PROCAL

	WHERE PROCAL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PROCAL.MBOrderTime>=A.RECORDED_TIME

	ORDER BY PROCAL.MBOrderTime ASC

)FIRSTPRO

------------------------------------------------------END OF PROCALCITONIN TIMES------------------------------------------------------------------



------------------------------------------------------BLOOD CULTURE TIMES------------------------------------------------------------------

/*Blood Culture*/

IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, OP.ORDER_PROC_ID

	--, OP.PROC_CODE AS [Blood Culture Procedure Ordered]--PROCEDURE_ORDERS.PROC_CODE IS DEPRICATED

	, EAP.PROC_CODE AS [Blood Culture Procedure Ordered]

	, OP.ORDER_TIME AS MBOrderTime

	, RESULTS.RESULT_TIME

	, RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

INTO 

	#BloodCultureValue 

FROM 

	#Base_Pop B

INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS RESULTS ON B.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP  ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID 

			--AND OP.PROC_CODE in ('LAB001', 'lab6219', 'nur13204', 'lab6218')

			AND OP.PROC_ID IN (600003,600004,600011,600012)

INNER JOIN EMRDB.dbo.PROCEDURES_CATALOG EAP ON EAP.PROC_ID = OP.PROC_ID

WHERE (OP.ORDER_TIME BETWEEN @dStartDate AND @dEndDate)

--SELECT * FROM #BloodCultureValue

IF OBJECT_ID(N'tempdb..#ODBC') IS NOT NULL DROP TABLE #ODBC;

SELECT

LASTBC.MBOrderTime [LAST Blood Culture Order Time],

LASTBC.[Blood Culture Procedure Ordered] AS [LAST Blood Culture Procedure Ordered],

LASTBC.ORD_VALUE [LAST Blood Culture Result],

CASE WHEN LASTBC.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST Blood Culture in Dept Y/N],

A.*,

FIRSTBC.MBOrderTime [FIRST Blood Culture Order Time],

FIRSTBC.[Blood Culture Procedure Ordered] AS [FIRST Blood Culture Procedure Ordered],

FIRSTBC.ORD_VALUE [FIRST Blood Culture Result],

CASE WHEN FIRSTBC.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST Blood Culture in Dept Y/N]

INTO #ODBC

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 BC.[Blood Culture Procedure Ordered], BC.MBOrderTime, BC.ORD_VALUE FROM #BloodCultureValue BC

	WHERE BC.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BC.MBOrderTime<A.RECORDED_TIME

	ORDER BY BC.MBOrderTime DESC

)LASTBC

OUTER APPLY

(

	SELECT TOP 1 BC.[Blood Culture Procedure Ordered], BC.MBOrderTime, BC.ORD_VALUE FROM #BloodCultureValue BC

	WHERE BC.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND BC.MBOrderTime>=A.RECORDED_TIME

	ORDER BY BC.MBOrderTime ASC

)FIRSTBC

--SELECT * FROM #ODBC



------------------------------------------------------END OF BLOOD CULTURE TIMES------------------------------------------------------------------



------------------------------------------------------CSF TIMES------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#CSF') IS NOT NULL DROP TABLE #CSF;

SELECT

	B.PAT_ENC_CSN_ID

	, B.ADT_DEPARTMENT_ID

	, B.ADT_DEPARTMENT_NAME

	, B.IN_DTTM

	, B.OUT_DTTM

	, op.ORDER_PROC_ID

	--, OP.PROC_CODE as [CSF Procedure Ordered]--PROCEDURE_ORDERS.PROC_CODE DEPRICATED

	, EAP.PROC_CODE as [CSF Procedure Ordered]

	, OP.ORDER_TIME AS MBOrderTime

	, RESULTS.RESULT_TIME

	, RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

INTO 

	#CSF 

FROM 

	#Base_Pop B

INNER JOIN EMRDB.dbo.LAB_ORDER_RESULTS RESULTS ON B.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS OP  ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID

			--AND OP.PROC_CODE IN ('LAB006','LAB007') AND OP.SPECIMEN_SOURCE_C=304 --PER STEPHANIE, USE THOSE LAB CODES WITH SPECIMEN SOURCE AS LUMBAR PUNCTURE--('LAB005','LAB013','LAB004')

			AND PROC_ID IN (600005,600006) AND OP.SPECIMEN_SOURCE_C=304

INNER JOIN EMRDB.dbo.PROCEDURES_CATALOG EAP ON EAP.PROC_ID = OP.PROC_ID

WHERE (OP.ORDER_TIME BETWEEN @dStartDate AND @dEndDate)



--SELECT * FROM #CSF

IF OBJECT_ID(N'tempdb..#ODCSF') IS NOT NULL DROP TABLE #ODCSF;

SELECT

LASTCSF.MBOrderTime [LAST CSF Order Time],

LASTCSF.[CSF Procedure Ordered] AS [LAST CSF Ordered],

CASE WHEN LASTCSF.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST CSF in Dept Y/N],

A.*,

FIRSTCSF.MBOrderTime [FIRST CSF Order Time],

FIRSTCSF.[CSF Procedure Ordered] AS [FIRST CSF Ordered],

CASE WHEN FIRSTCSF.MBOrderTime BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST CSF in Dept Y/N]

INTO #ODCSF

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 CSF.[CSF Procedure Ordered], CSF.MBOrderTime FROM #CSF CSF

	WHERE CSF.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CSF.MBOrderTime<A.RECORDED_TIME

	ORDER BY CSF.MBOrderTime DESC

)LASTCSF

OUTER APPLY

(

	SELECT TOP 1 CSF.[CSF Procedure Ordered], CSF.MBOrderTime FROM #CSF CSF

	WHERE CSF.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND CSF.MBOrderTime>=A.RECORDED_TIME

	ORDER BY CSF.MBOrderTime ASC

)FIRSTCSF



------------------------------------------------------END OF CSF TIMES------------------------------------------------------------------



------------------------------------------------------ETT TIMES------------------------------------------------------------------

/*ETT*/

IF OBJECT_ID(N'tempdb..#ETT') IS NOT NULL DROP TABLE #ETT;

SELECT

B.PAT_ENC_CSN_ID,

B.ADT_DEPARTMENT_ID,

B.ADT_DEPARTMENT_NAME,

B.IN_DTTM,

B.OUT_DTTM,

ILN.IP_LDA_ID,

ILN.PLACEMENT_INSTANT,

ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY ILN.PLACEMENT_INSTANT) TIME_LINE

INTO #ETT

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID AND ILN.FLO_MEAS_ID='900112' AND ILN.PLACEMENT_INSTANT IS NOT NULL

WHERE ILN.PLACEMENT_INSTANT BETWEEN @dStartDate AND @dEndDate

--WHERE (ILN.PLACEMENT_INSTANT BETWEEN B.IN_DTTM AND B.OUT_DTTM)

--SELECT * FROM #ETT WHERE TIME_LINE=1



IF OBJECT_ID(N'tempdb..#ODETT') IS NOT NULL DROP TABLE #ODETT;

SELECT

LASTETT.PLACEMENT_INSTANT [LAST Intubation Time],

CASE WHEN LASTETT.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST ETT in Dept Y/N],

A.*,

FIRSTETT.PLACEMENT_INSTANT [FIRST Intubation Time],

CASE WHEN FIRSTETT.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST ETT in Dept Y/N]

INTO #ODETT

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 ETT.PLACEMENT_INSTANT FROM #ETT ETT

	WHERE ETT.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ETT.PLACEMENT_INSTANT<A.RECORDED_TIME

	ORDER BY ETT.PLACEMENT_INSTANT DESC

)LASTETT

OUTER APPLY

(

	SELECT TOP 1 ETT.PLACEMENT_INSTANT FROM #ETT ETT

	WHERE ETT.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND ETT.PLACEMENT_INSTANT>=A.RECORDED_TIME

	ORDER BY ETT.PLACEMENT_INSTANT ASC

)FIRSTETT



--SELECT * FROM #ODLASTETT  WHERE OD_ETT_LINE=1

------------------------------------------------------END OF ETT TIMES------------------------------------------------------------------



------------------------------------------------------PIV TIMES------------------------------------------------------------------

/*PIV*/

IF OBJECT_ID(N'tempdb..#PIV') IS NOT NULL DROP TABLE #PIV;

SELECT

B.PAT_ENC_CSN_ID,

B.ADT_DEPARTMENT_ID,

B.ADT_DEPARTMENT_NAME,

B.IN_DTTM,

B.OUT_DTTM,

ILN.IP_LDA_ID,

ILN.PLACEMENT_INSTANT,

ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY ILN.PLACEMENT_INSTANT) TIME_LINE

INTO #PIV

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.LINE_DEVICE_AIRWAY ILN ON ILN.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID AND ILN.FLO_MEAS_ID='900111' AND ILN.PLACEMENT_INSTANT IS NOT NULL

WHERE (ILN.PLACEMENT_INSTANT BETWEEN @dStartDate AND @dEndDate)

--SELECT * FROM #PIV WHERE TIME_LINE=1

IF OBJECT_ID(N'tempdb..#ODPIV') IS NOT NULL DROP TABLE #ODPIV;

SELECT

LASTPIV.PLACEMENT_INSTANT [LAST PIV Before Screen],

CASE WHEN LASTPIV.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [LAST PIV in Dept Y/N],

A.*,

FIRSTPIV.PLACEMENT_INSTANT [FIRST PIV After Screen],

CASE WHEN FIRSTPIV.PLACEMENT_INSTANT BETWEEN A.IN_DTTM AND A.OUT_DTTM THEN 'Y' ELSE 'N' END AS [FIRST PIV in Dept Y/N]

INTO #ODPIV

FROM

#Base_Pop_OD_Scores A

OUTER APPLY

(

	SELECT TOP 1 PIV.PLACEMENT_INSTANT FROM #PIV PIV

	WHERE PIV.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PIV.PLACEMENT_INSTANT<A.RECORDED_TIME

	ORDER BY PIV.PLACEMENT_INSTANT DESC

)LASTPIV

OUTER APPLY

(

	SELECT TOP 1 PIV.PLACEMENT_INSTANT FROM #PIV PIV

	WHERE PIV.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID AND PIV.PLACEMENT_INSTANT>=A.RECORDED_TIME

	ORDER BY PIV.PLACEMENT_INSTANT ASC

)FIRSTPIV



------------------------------------------------------END OF PIV TIMES------------------------------------------------------------------



------------------------------------------------------ PROPHYLAXIS ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#PROPHYLAXIS') IS NOT NULL DROP TABLE #PROPHYLAXIS;

SELECT

B.PAT_ENC_CSN_ID,

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM,

CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS PROPHYLAXIS_YN

INTO #PROPHYLAXIS

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID AND IFM.RECORDED_TIME IS NOT NULL

	AND IFM.FLO_MEAS_ID IN ('9000613042','9000613043','9000613044','9000613045','9000613047','9000613048','9000613050')

	--9000613042	R HS IP VTE AMBULATION ACTION

	--9000613043	R HS IP VTE SCD ACTION

	--9000613044	R HS IP VTE BOOTS ACTION

	--9000613045	R HS IP VTE HEMATOLOGY ACTION

	--9000613047	R HS IP VTE COUMADIN ACTION

	--9000613048	R HS IP VTE HEPARIN ACTION

	--9000613050	R HS IP VTE COMPLICATION ACTIONS

	--AND (IFM.RECORDED_TIME BETWEEN B.IN_DTTM AND B.OUT_DTTM)

WHERE (IFM.RECORDED_TIME BETWEEN @dStartDate AND @dEndDate)

GROUP BY B.PAT_ENC_CSN_ID

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM



------------------------------------------------------END OF PROPHYLAXIS------------------------------------------------------------------



------------------------------------------------------ CVVH ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#CVVH') IS NOT NULL DROP TABLE #CVVH;

SELECT

B.PAT_ENC_CSN_ID,

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM,

CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS CVVH_YN

INTO #CVVH

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID 

	AND IFM.FLT_ID='9000001359'--ANY FLOWSHEET FROM THIS TEMPLATE IS A CANDIDATE

--9000001359	T HS IP INPATIENT CVVH	Inpatient CVVH	

	--AND (IFM.RECORDED_TIME BETWEEN B.IN_DTTM AND B.OUT_DTTM)

WHERE (IFM.RECORDED_TIME BETWEEN @dStartDate AND @dEndDate)

GROUP BY B.PAT_ENC_CSN_ID

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM



------------------------------------------------------END OF CVVH------------------------------------------------------------------

------------------------------------------------------ CEREBRAL OX MONITORING ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#OX') IS NOT NULL DROP TABLE #OX;

SELECT

B.PAT_ENC_CSN_ID,

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM,

CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS OX_YN

INTO #OX

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID 

	AND IFM.FLO_MEAS_ID IN ('900201','900202','900203','9000001977')

--FLO   900201		R AN NEAR-INFRARED SPECTROSCOPY LEFT CEREBRAL	(Cerebral Oximetry)

--FLO   900202		R AN NEAR-INFRARED SPECTROSCOPY RIGHT CEREBRAL	(Cerebral Oximetry)

--FLO   900203		R AN NEAR-INFRARED SPECTROSCOPY RENAL			(Cerebral Oximetry)

--FLO   9000001977  R HS IP NEAR-INFRARED SPECTROSCOPY CEREBRAL		(Cerebral Oximetry)



	--AND (IFM.RECORDED_TIME BETWEEN B.IN_DTTM AND B.OUT_DTTM)

WHERE (IFM.RECORDED_TIME BETWEEN @dStartDate AND @dEndDate)

GROUP BY B.PAT_ENC_CSN_ID

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM

------------------------------------------------------END OF CEREBRAL OX MONITORING------------------------------------------------------------------

------------------------------------------------------ ECMO ------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#ECMO') IS NOT NULL DROP TABLE #ECMO;

SELECT

B.PAT_ENC_CSN_ID,

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM,

CASE WHEN COUNT(IFM.RECORDED_TIME)>0 THEN 'Y' ELSE 'N' END AS ECMO_YN

INTO #ECMO

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID 

	AND IFM.FLO_MEAS_ID ='9000101014'

--9000101014	R ECMO ON/OFF

	--AND (IFM.RECORDED_TIME BETWEEN B.IN_DTTM AND B.OUT_DTTM)

WHERE (IFM.RECORDED_TIME BETWEEN @dStartDate AND @dEndDate)

GROUP BY B.PAT_ENC_CSN_ID

--B.ADT_DEPARTMENT_ID,

--B.ADT_DEPARTMENT_NAME,

--B.IN_DTTM

------------------------------------------------------END OF ECMO------------------------------------------------------------------



IF OBJECT_ID(N'tempdb..#FINAL') IS NOT NULL DROP TABLE #FINAL;

SELECT

Main.PAT_NAME,

Main.PAT_MRN_ID,

Main.[Ethnic Group],

Main.[Race],

Main.Location,

Main.PAT_ENC_CSN_ID,

Main.AGE_MONTHS,

Main.AGE_YEARS,

Main.INP_ADM_DATE,

Main.HOSP_DISCH_TIME,

Main.Disposition,

Main.LOS_HRS,

ENC_RSN.AllEncReasons AS [Encounter Diagnoses],

HYPO.[LAST Hypotension Time],

HYPO.[LAST Hypotension Value],

HYPO.[LAST Hypotension taken in Dept Y/N],

HYPO.[FIRST Hypotension Time],

HYPO.[FIRST Hypotension Value],

HYPO.[FIRST Hypotension taken in Dept Y/N],

WT.EncWeight,

EDLOS.MEAS_VALUE [First Positive Score in ED],

EDLOS.RECORDED_TIME AS [First Positive Score Time in ED],

EDLOS.HoursInED AS [ED LOS (Hrs)],

--BP.ADT_DEPARTMENT_ID,

BP.ADT_DEPARTMENT_NAME,

BP.DEPARTMENT_ROLLUP,

BP.IN_DTTM [In Department Time],

BP.OUT_DTTM [Out Department Time],

SCORES.MEAS_VALUE AS OD_SCORE,

SCORES.RECORDED_TIME as [Score Time],

CASE WHEN SCORES.RECORDED_TIME IS NOT NULL

		THEN CASE WHEN DATEPART(HOUR,SCORES.RECORDED_TIME) >= 7 and DATEPART(HOUR,SCORES.RECORDED_TIME) < 19 then 'AM (Day Shift)'

					ELSE 'PM (Night Shift)'

				END

END AS [OD Score AM/PM],

SCORES.[Sepsis PATIENTS Huddle or Sepis CLINICAL_ALERTS Called//Performed with a MD/PNP],

SCORES.[Huddle Date],

SCORES.[Huddle Time],

SCORES.[PATIENTS Assessed by MD/PNP],

SCORES.[Physician Name],

SCORES.[Additional Orders Received/Placed by MD/PNP],

ABX.LASTABX_TIME [LAST ABX Time],

ABX.LASTABX_NAME [LAST ABX Name],

ABX.[LAST ABX Volume],

ABX.[Last ABX to OD Score Time],

ABX.[LAST ABX Given in Dept Y/N],

ABX.FIRSTABX_TIME [FIRST ABX Time],

ABX.FIRSTABX_NAME [FIRST ABX Name],

ABX.[FIRST ABX Volume],

ABX.[OD Score to First ABX Time],

ABX.[FIRST ABX Given in Dept Y/N],

CASE WHEN (ABX.LASTABX_TIME IS NOT NULL OR ABX.FIRSTABX_TIME IS NOT NULL) THEN 'Y' ELSE 'N' END AS ABX_YN,

BOL.[LAST Bolus Time],

BOL.[LAST Bolus],

BOL.[LAST Bolus Volume],

BOL.[Last Bolus to Screen Time],

BOL.[LAST Bolus Given in Dept Y/N],

BOL.[FIRST Bolus Time],

BOL.[FIRST Bolus],

BOL.[FIRST Bolus Volume],

BOL.[Screen Time to First Bolus],

BOL.[FIRST Bolus Given in Dept Y/N],

CASE WHEN (BOL.[LAST Bolus Time] IS NOT NULL OR BOL.[FIRST Bolus Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS BOLUS_YN,

LA.[LAST LacticAcid Order Time],

LA.[LAST LacticAcid Result],

LA.[LAST LacticAcid in Dept Y/N],

LA.[FIRST LacticAcid Order Time],

LA.[FIRST LacticAcid Result],

LA.[FIRST LacticAcid in Dept Y/N],

CASE WHEN (LA.[LAST LacticAcid Order Time] IS NOT NULL OR LA.[FIRST LacticAcid Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS LacticAcid_YN,

ORDS.[LAST OrderSet Time],

ORDS.[LAST OrderSet ID],

ORDS.[LAST OrderSet in Dept Y/N],

ORDS.[FIRST OrderSet Time],

ORDS.[FIRST OrderSet ID],

ORDS.[FIRST OrderSet in Dept Y/N],

CVL.[LAST CVL Time],

CVL.[LAST CVL in Dept Y/N],

CVL.[FIRST CVL Time],

CVL.[FIRST CVL in Dept Y/N],

CASE WHEN (CVL.[LAST CVL Time] IS NOT NULL OR CVL.[FIRST CVL Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS CVL_YN,

SVO2.[LAST SVO2 Time],

SVO2.[LAST SVO2 in Dept Y/N],

SVO2.[FIRST SVO2 Time],

SVO2.[FIRST SVO2 in Dept Y/N],

CASE WHEN (SVO2.[LAST SVO2 Time] IS NOT NULL OR SVO2.[FIRST SVO2 Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS SVO2_YN,

PROCAL.[LAST Procalcitonin Order Time],

PROCAL.[LAST Procalcitonin Result],

PROCAL.[LAST Procalcitonin in Dept Y/N],

PROCAL.[FIRST Procalcitonin Order Time],

PROCAL.[FIRST Procalcitonin Result],

PROCAL.[FIRST Procalcitonin in Dept Y/N],

CASE WHEN (PROCAL.[LAST Procalcitonin Order Time] IS NOT NULL OR PROCAL.[FIRST Procalcitonin Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS Procalcitonin_YN,

BC.[LAST Blood Culture Order Time],

BC.[LAST Blood Culture Procedure Ordered],

BC.[LAST Blood Culture Result],

BC.[LAST Blood Culture in Dept Y/N],

BC.[FIRST Blood Culture Order Time],

BC.[FIRST Blood Culture Procedure Ordered],

BC.[FIRST Blood Culture Result],

BC.[FIRST Blood Culture in Dept Y/N],

CASE WHEN (BC.[LAST Blood Culture Order Time] IS NOT NULL OR BC.[FIRST Blood Culture Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS BloodCulture_YN,

CSF.[LAST CSF Order Time],

CSF.[LAST CSF Ordered],

CSF.[LAST CSF in Dept Y/N],

CSF.[FIRST CSF Order Time],

CSF.[FIRST CSF Ordered],

CSF.[FIRST CSF in Dept Y/N],

CASE WHEN (CSF.[LAST CSF Order Time] IS NOT NULL OR CSF.[FIRST CSF Order Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS CSF_YN,

PIV.[LAST PIV Before Screen],

PIV.[LAST PIV in Dept Y/N],

PIV.[FIRST PIV After Screen],

PIV.[FIRST PIV in Dept Y/N],

CASE WHEN (PIV.[LAST PIV Before Screen] IS NOT NULL OR PIV.[FIRST PIV After Screen] IS NOT NULL) THEN 'Y' ELSE 'N' END AS PIV_YN,

ETT.[LAST Intubation Time],

ETT.[LAST ETT in Dept Y/N],

ETT.[FIRST Intubation Time],

ETT.[FIRST ETT in Dept Y/N],

CASE WHEN (ETT.[LAST Intubation Time] IS NOT NULL OR ETT.[FIRST Intubation Time] IS NOT NULL) THEN 'Y' ELSE 'N' END AS ETT_YN,

CASE WHEN PRESSOR.DOBUTAMINE IS NULL THEN 'N' ELSE 'Y' END DOBUTAMINE,

CASE WHEN PRESSOR.DOPAMINE IS NULL THEN 'N' ELSE 'Y' END DOPAMINE,

CASE WHEN PRESSOR.EPINEPHRINE IS NULL THEN 'N' ELSE 'Y' END EPINEPHRINE,

CASE WHEN PRESSOR.MILRINONE IS NULL THEN 'N' ELSE 'Y' END MILRINONE,

CASE WHEN PRESSOR.NOREPINEPHRINE IS NULL THEN 'N' ELSE 'Y' END NOREPINEPHRINE,

CASE WHEN (

			PRESSOR.DOBUTAMINE IS NOT NULL OR

			PRESSOR.DOPAMINE IS NOT NULL OR

			PRESSOR.EPINEPHRINE IS NOT NULL OR

			PRESSOR.MILRINONE IS NOT NULL OR

			PRESSOR.NOREPINEPHRINE IS NOT NULL) THEN 'Y' ELSE 'N' END AS PRESSOR_YN,

COALESCE(PROPHY.PROPHYLAXIS_YN,'N') AS DVTPROPHYLAXIS_YN,

COALESCE(CVVH.CVVH_YN,'N') AS CVVH_YN,

COALESCE(OX.OX_YN,'N') AS OX_YN,

COALESCE(ECMO.ECMO_YN,'N') AS ECMO_YN,

CASE WHEN IPSO.PAT_ENC_CSN_ID IS NULL THEN 'N' ELSE 'Y' END SEVERE_SEPSIS_STAGING,

SCORES.[CLINICAL_ALERTS Not Activated Reason],

SCORES.[CLINICAL_ALERTS Not Activated Comment],

SCORES.[CLINICAL_ALERTS Activated Comment],

GETDATE() AS [Refresh Time]



FROM #Main Main

INNER JOIN #Base_Pop BP ON BP.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID

INNER JOIN #Base_Pop_OD_Scores SCORES ON SCORES.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID AND SCORES.ADT_DEPARTMENT_ID = BP.ADT_DEPARTMENT_ID AND SCORES.IN_DTTM = BP.IN_DTTM

LEFT OUTER JOIN #Base_Pop_ENC_Reason ENC_RSN ON ENC_RSN.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID

LEFT OUTER JOIN #EncounterWeights WT ON WT.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID AND WT.TIME_LINE=1

LEFT OUTER JOIN #ODHYPO HYPO ON HYPO.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND HYPO.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND HYPO.IN_DTTM = SCORES.IN_DTTM AND HYPO.TIME_LINE=1

LEFT OUTER JOIN #ODABX ABX ON ABX.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND ABX.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND ABX.IN_DTTM = SCORES.IN_DTTM AND ABX.TIME_LINE=1

LEFT OUTER JOIN #OdboL BOL ON BOL.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND BOL.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND BOL.IN_DTTM = SCORES.IN_DTTM AND BOL.TIME_LINE=1

LEFT OUTER JOIN #ODLA LA ON LA.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND LA.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND LA.IN_DTTM = SCORES.IN_DTTM AND LA.TIME_LINE=1

LEFT OUTER JOIN #ODORDSET ORDS ON ORDS.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND ORDS.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND ORDS.IN_DTTM = SCORES.IN_DTTM AND ORDS.TIME_LINE=1

LEFT OUTER JOIN #ODCVL CVL ON CVL.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND CVL.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND CVL.IN_DTTM = SCORES.IN_DTTM AND CVL.TIME_LINE=1

LEFT OUTER JOIN #ODPressorPivot PRESSOR ON PRESSOR.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1--CHECK THIS AGAIN

LEFT OUTER JOIN #ODSVO2 SVO2 ON SVO2.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SVO2.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND SVO2.IN_DTTM = SCORES.IN_DTTM AND SVO2.TIME_LINE=1

LEFT OUTER JOIN #ODPROCAL PROCAL ON PROCAL.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND PROCAL.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND PROCAL.IN_DTTM = SCORES.IN_DTTM AND PROCAL.TIME_LINE=1

LEFT OUTER JOIN #ODBC BC ON BC.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND BC.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND BC.IN_DTTM = SCORES.IN_DTTM AND BC.TIME_LINE=1

LEFT OUTER JOIN #ODCSF CSF ON CSF.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND CSF.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND CSF.IN_DTTM = SCORES.IN_DTTM AND CSF.TIME_LINE=1

LEFT OUTER JOIN #ODPIV PIV ON PIV.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND PIV.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND PIV.IN_DTTM = SCORES.IN_DTTM AND PIV.TIME_LINE=1

LEFT OUTER JOIN #ODETT ETT ON ETT.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND ETT.ADT_DEPARTMENT_ID = SCORES.ADT_DEPARTMENT_ID AND ETT.IN_DTTM = SCORES.IN_DTTM AND ETT.TIME_LINE=1

LEFT OUTER JOIN #PROPHYLAXIS PROPHY ON PROPHY.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

LEFT OUTER JOIN #CVVH CVVH ON CVVH.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

LEFT OUTER JOIN #OX OX ON OX.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

LEFT OUTER JOIN #ECMO ECMO ON ECMO.PAT_ENC_CSN_ID = SCORES.PAT_ENC_CSN_ID AND SCORES.TIME_LINE=1

LEFT OUTER JOIN #EDPosScore_EDLOS EDLOS ON EDLOS.PAT_ENC_CSN_ID = MAIN.PAT_ENC_CSN_ID AND EDLOS.FIRST_TIME_LINE=1

LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING] IPSO ON IPSO.PAT_ENC_CSN_ID = Main.PAT_ENC_CSN_ID
GO

-- ==== reports/USP_RPTS_NonSevere_Sepsis.sql ====
CREATE PROCEDURE [reports].[USP_NonSevere_Sepsis] 



	@i_vRelativeStartDate VARCHAR(20) = NULL

	, @i_vRelativeEndDate VARCHAR(20) = NULL

	, @i_vRelativeTest VARCHAR(20) = NULL

	, @i_vRelativeOW VARCHAR(20) = NULL



AS



BEGIN



	DECLARE @StartDate DATE

	DECLARE @EndDate DATE

	DECLARE @TEST INT

	DECLARE @OW INT



 -- ========================================================================================================================================================

 -- Author:		          Developer D

 -- Create date:          10/12/2018

 -- Description:          IPSO NON SEVERE SEPSIS. THIS CODE MUST BE RAN FOR FULL MONTH.

 -- Sample Call:          EXEC [reports].[USP_NonSevere_Sepsis] '09-01-2018', '09-30-2018', '0', ''   --TO WRITE DATA TO ARCHIVE TABLE. ******USE THIS COMMAND FOR BATCH******

 --						  EXEC [reports].[USP_NonSevere_Sepsis] '', '', '0', '0'	--TO OVERWRITE THE DATA IN THE ARCHIVE TABLE IF THE DATA ALREADY EXISTS

 -- Change log: 

 -- =========================================================================================================================================================

 --    Date                By:                        Description

 --    ============        ====================       ========================================================================================================

 --    2018-12-04          Developer D         CREATE STORED PROC

 --    05.16.2019			V_DEV001					CHANGED PROCEDURE_ORDERS.PROC_CODE TO PROCEDURE_ORDERS.PROC_ID AS PROC_CODE IS DEPRICATED IN PROCEDURE_ORDERS TABLE

 --		08.15.2019			V_DEV001					Changed the logic around ABX (to follow whats in Severe Sepsis) and also limit the ABX/ BC searches prior to @EndDate

 --==========================================================================================================================================================



	IF @i_vRelativeStartDate IS NULL OR @i_vRelativeStartDate = ''

		SET @StartDate = EMRDB.[dbo].[fn_parse_date]('MB-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @StartDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeStartDate)



	IF @i_vRelativeEndDate IS NULL OR @i_vRelativeEndDate = ''

		SET @EndDate = EMRDB.[dbo].[fn_parse_date]('ME-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @EndDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeEndDate)	



	IF @i_vRelativeTest IS NULL OR @i_vRelativeTest = '' OR @i_vRelativeTest <> 0

		SET @TEST = 1

	ELSE

		SET @TEST = @i_vRelativeTest



	IF @i_vRelativeOW IS NULL OR @i_vRelativeOW = '' OR @i_vRelativeOW <> 0

		SET @OW = 1

	ELSE

		SET @OW = @i_vRelativeOW



-----------------------------------------------------------------------------------------------------------------------------------------------------

/* CHECK IF OVERWRITE FLAG IS ON */

-----------------------------------------------------------------------------------------------------------------------------------------------------

WHILE @OW = 0



BEGIN

	DELETE FROM [reportingDB].[reports].[NON_SEVERE_SEPSIS_STAGING]



	WHERE

		Reviewed = 0

		AND DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate));

		PRINT('EXISTING DATA DELETED... RUNNING CODE FOR NEW DATA')



	GOTO MAIN



END



-----------------------------------------------------------------------------------------------------------------------------------------------------

/* CHECK IF DATA EXISTS */

-----------------------------------------------------------------------------------------------------------------------------------------------------

IF 

	EXISTS( SELECT 

				*



			FROM 

				[reportingDB].[reports].[NON_SEVERE_SEPSIS_STAGING]



			WHERE 

				DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate))

				AND @TEST = 0

			)

		PRINT('Data for given time range already exists in [reports].[NON_SEVERE_SEPSIS_STAGING]. USE EXEC COMMAND WITH 0 AS 4TH PARAMETER TO OVERWRITE THE DATA');

		

ELSE

		BEGIN



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

MAIN:

-----------------------------------------------------------------------------------------------------------------------------------------------------1

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* DEFINING BASE POPULATION */

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*GETTING ENCOUNTERS WITHIN GIVEN DATE RANGES SO WE DON'T HAVE TO QUERY ON WHOLE DATABASE FOR EACH CRITERIA*/

IF OBJECT_ID(N'tempdb..#Base_Pop_1') IS NOT NULL 

DROP TABLE #Base_Pop_1;



SELECT DISTINCT

	PEH.PAT_ENC_CSN_ID

	, PEH.INPATIENT_DATA_ID

	, DATEDIFF(MM,PAT.BIRTH_DATE,COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.HOSP_ADMSN_TIME)) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS



INTO 

	#Base_Pop_1



FROM 

	EMRDB.dbo.V_HOSPITAL_TRANSACTIONS HTR

	JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH 

		ON HTR.PAT_ENC_CSN_ID = PEH.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.PATIENTS PAT 

		ON PAT.PAT_ID = PEH.PAT_ID



WHERE

	HTR.SERVICE_DATE BETWEEN @StartDate AND @EndDate 

	--and PEH.PAT_ENC_CSN_ID=1018379064

	AND (PEH.INP_ADM_DATE IS NOT NULL --PATIENTS UST BE ADMITTED

		OR PEH.ED_DISPOSITION_C = 3 --ADMITTED

		or PEH.ADT_PAT_CLASS_C IN (101, 104)) 



/* LIST OF ENCOUNTER ADMITTED DIRECTLY TO NICU BEGIN */

IF OBJECT_ID(N'tempdb..#NICUAdmissions') IS NOT NULL 

DROP TABLE #NICUAdmissions;



SELECT DISTINCT 

	ADT.PAT_ENC_CSN_ID 



INTO 

	#NICUAdmissions



FROM

	#Base_Pop_1 B

	JOIN EMRDB.dbo.ADT_EVENTS ADT

		ON ADT.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID



WHERE 

	ADT.EVENT_TYPE_C = 1 --ADMISSION

	AND ADT.EVENT_SUBTYPE_C <> 2 --CANCELLED

	AND ADT.DEPARTMENT_ID IN (200108002, 200108003, 200108004, 200108005, 200108006) --NICU DEPARTMENTS

/* LIST OF ENCOUNTER ADMITTED DIRECTLY TO NICU END */



--Final Base Population -- ALL ENCOUNTERS FROM PREVIOUS MONTH WHERE PATIENTS WAS ADMITTED (NOT DISCHARGED FROM ED). EXCLUDING PATIENTS WHO WERE ADMITTED TO NICU DIRECTLY

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL 

DROP TABLE #Base_Pop;



SELECT 

	FP.*



INTO 

	#Base_Pop



FROM 

	#Base_Pop_1 FP

	LEFT JOIN #NICUAdmissions NA 

		ON NA.PAT_ENC_CSN_ID = FP.PAT_ENC_CSN_ID



WHERE 

	NA.PAT_ENC_CSN_ID IS NULL



--Getting List of Encounters where a ABX was ordered. 

IF OBJECT_ID(N'tempdb..#ABXORDER_TIMES') IS NOT NULL DROP TABLE #ABXORDER_TIMES;

SELECT

	B.PAT_ENC_CSN_ID

	, OM.ORDER_INST AS ABX_ORDER_TIME

	, MIN(MAI.TAKEN_TIME) AS FIRST_ABX_ADMIN_TIME

	--, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OM.ORDER_INST ASC) LINE

INTO

	#ABXORDER_TIMES	

FROM

		#Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID --AND CM.THERA_CLASS_C = 11 --Antibiotics

		INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

	WHERE

		MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND MAI.TAKEN_TIME < @EndDate

		AND OM.MED_ROUTE_C=11--IV ONLY

		AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

								, '7'			--RESTARTED

								, '102'		--GIVEN BY OTHER

								, '105'		--NEW CARTRIDGE

								, '113'		--GIVEN DURING DOWNTIME

								, '114'		--STARTED DURING DOWNTIME

								, '115'		--MEDICATION APPLIED

								, '122'		--CONTINUED FROM OR

								, '124'		--SELF ADMINISTERED VIA PUMP

								, '132'		--CONTINUED FROM PREVIOUS ORDER

								, '143'		--REDOSE

								, '1604'		--INFUSION GREATER THAN 15 MIN

								, '1605'		--INFUSION LESS THAN 15 MIN

								, '1607'		--NEW CARTRIDGE

								, '6'			--NEW BAG

								, '99'			--RATE CHANGE

								)

		AND OM.MEDICATION_ID IN 

			(



				select 

						medlist.MEDICATION_ID

					from

						(

							SELECT 

								erx.MEDICATION_ID,

								erx.NAME,

								cntl.VALUE_SET_DISPLAY as AGENT,

								case when CHARINDEX('^',cntl.VALUE_SET_ABBR)>0 then SUBSTRING(cntl.VALUE_SET_ABBR,0,CHARINDEX('^',cntl.VALUE_SET_ABBR)) else cntl.VALUE_SET_ABBR end as AGENT_GROUP,

								case when cntl.VALUE_SET_ABBR like '%^Y' then 1 else 0 end as DOT_MONITORING,

								gen.TITLE,

								ROW_NUMBER() over(partition by erx.MEDICATION_ID order by cntl.VALUE_SET_ABBR,cntl.VALUE_SET_DISPLAY asc) as AGENT_ORDER



							FROM

								EMRDB.dbo.MEDICATIONS erx

								OUTER APPLY(

									--Get the main medication's simple generic if its a mixture

									SELECT TOP 1 

										mix.DRUG_ID,

										comp.SIMPLE_GENERIC_C 

									FROM

										EMRDB.dbo.MED_MIX_COMPONENTS mix

										INNER JOIN EMRDB.dbo.MEDICATIONS comp on mix.DRUG_ID=comp.MEDICATION_ID

									WHERE

										mix.TYPE_C=3		--3 - Medications 

										AND mix.MEDICATION_ID=erx.MEDICATION_ID

									ORDER BY

										mix.LINE

								) mixture

								INNER JOIN EMRDB.dbo.REF_GENERIC_MED gen on gen.SIMPLE_GENERIC_C=coalesce(erx.SIMPLE_GENERIC_C,mixture.SIMPLE_GENERIC_C)

								INNER JOIN reportingDB.reports.CONFIG_VALUE_SET cntl on cntl.VALUE_SET_ID=3016 and cntl.CODE=gen.SIMPLE_GENERIC_C -- and cntl.VALUE_SET_ABBR='Antibacterial'

						) medlist

					where

						medlist.AGENT_ORDER=1						

			)

GROUP BY

	B.PAT_ENC_CSN_ID

	, OM.ORDER_INST		

	UNION

	SELECT

		DISTINCT

		B.PAT_ENC_CSN_ID

		, OM.ORDER_INST AS ABX_ORDER_TIME

		, MIN(MAI.TAKEN_TIME) AS FIRST_ABX_ADMIN_TIME

		--, cm.NAME

	FROM

		#Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID AND CM.THERA_CLASS_C = 11 --Antibiotics

		INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

	WHERE

		MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND OM.MED_ROUTE_C=11--IV ONLY

		AND MAI.MAR_ACTION_C IN ('1'			--GIVEN

								, '7'			--RESTARTED

								, '102'		--GIVEN BY OTHER

								, '105'		--NEW CARTRIDGE

								, '113'		--GIVEN DURING DOWNTIME

								, '114'		--STARTED DURING DOWNTIME

								, '115'		--MEDICATION APPLIED

								, '122'		--CONTINUED FROM OR

								, '124'		--SELF ADMINISTERED VIA PUMP

								, '132'		--CONTINUED FROM PREVIOUS ORDER

								, '143'		--REDOSE

								, '1604'		--INFUSION GREATER THAN 15 MIN

								, '1605'		--INFUSION LESS THAN 15 MIN

								, '1607'		--NEW CARTRIDGE

								, '6'			--NEW BAG

								, '99'			--RATE CHANGE

								)

GROUP BY

	B.PAT_ENC_CSN_ID

	, OM.ORDER_INST



IF OBJECT_ID(N'tempdb..#ABXORDER') IS NOT NULL DROP TABLE #ABXORDER;				

SELECT *

, ROW_NUMBER() OVER(PARTITION BY A.PAT_ENC_CSN_ID ORDER BY A.ABX_ORDER_TIME ASC) LINE

INTO #ABXORDER

FROM #ABXORDER_TIMES A



--Getting List of Encounters where a Blood Culture was ordered. this is the 2nd pat of treatment plan

IF OBJECT_ID(N'tempdb..#TP2') IS NOT NULL DROP TABLE #TP2;



SELECT

	B.PAT_ENC_CSN_ID

	, OP.ORDER_INST AS BLOOD_CULTURE_ORDER_TIME

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY OP.ORDER_INST ASC) LINE



INTO

	#TP2



FROM

	#Base_Pop B

	JOIN EMRDB.dbo.PROCEDURE_ORDERS OP

		ON OP.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

			AND OP.PROC_ID IN (600003,600004,600011,600012)  --BLOOD CULTURE

			AND ORDER_STATUS_C <> 4  --CANCELED

	WHERE OP.ORDER_INST < @EndDate



--GETTING LIST OF ALL ENCOUNTERS WHERE AN ABX AND BLOOD CULTURE WERE ORDERED WITHIN 24 HOURS OF EACH OTHER

IF OBJECT_ID(N'tempdb..#Base_Popmed') IS NOT NULL 

DROP TABLE #Base_Popmed;



SELECT DISTINCT

	B.PAT_ENC_CSN_ID

	, B.INPATIENT_DATA_ID

	, A.ABX_ORDER_TIME 

	, A.FIRST_ABX_ADMIN_TIME

	, A.LINE AS ABX_LINE

	, #TP2.BLOOD_CULTURE_ORDER_TIME

	, #TP2.LINE AS BC_LINE

	

INTO

	#Base_Popmed 



FROM

	#Base_Pop B

	JOIN #ABXORDER A

		ON A.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	JOIN #TP2

		ON #TP2.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID



WHERE

	ABS(DATEDIFF(HH, A.ABX_ORDER_TIME, #TP2.BLOOD_CULTURE_ORDER_TIME)) <= 24



--CHECKING TO SEE IF ANY OF THE ENCOUTERS WERE SUBMITTED FOR SEVERE SEPSIS

IF OBJECT_ID(N'tempdb..#COHORT') IS NOT NULL 

DROP TABLE #COHORT;

SELECT DISTINCT

	B.*



INTO

	#COHORT



FROM 

	#Base_Popmed B

WHERE

	B.PAT_ENC_CSN_ID NOT IN (SELECT DISTINCT PAT_ENC_CSN_ID FROM reportingDB.reports.[NON_SEVERE_SEPSIS_STAGING] )--08.12.2019 make sure we are not includiung already submitted encounters

	AND  B.PAT_ENC_CSN_ID NOT IN  (SELECT DISTINCT PAT_ENC_CSN_ID FROM reportingDB.reports.[SEVERE_SEPSIS_STAGING] )--08.12.2019 make sure we are not includiung already submitted encounters



IF OBJECT_ID(N'tempdb..#FINAL') IS NOT NULL 

DROP TABLE #FINAL;



SELECT

	CONVERT(VARCHAR, C.INPATIENT_DATA_ID) + CONVERT(VARCHAR, YEAR(DATEADD(MM,-1,GETDATE()))) + CONVERT(VARCHAR, MONTH(DATEADD(MM, -1, GETDATE()))) AS Sepsis_Episode_ID_V01

	, C.ABX_ORDER_TIME AS AntibioticOrderedTime_V59

	, C.FIRST_ABX_ADMIN_TIME AS AntibioticAdministeredTime_V60

	, C.BLOOD_CULTURE_ORDER_TIME AS BloodCultureOrderedTime_V61

	, C.PAT_ENC_CSN_ID 

	, DATENAME(month, DATEADD(MM,-1,getdate()))+DATENAME(YEAR, DATEADD(MM,-1,getdate())) AS DATE_STAMP

	, 0 AS REVIEWED



INTO

	#FINAL



FROM

	#COHORT C



WHERE

	C.ABX_LINE = (SELECT MIN(C2.ABX_LINE)

				FROM #COHORT C2

				WHERE C2.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID)

	AND BC_LINE = (SELECT MIN(C2.BC_LINE)

				FROM #COHORT C2

				WHERE C2.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID)



ORDER BY PAT_ENC_CSN_ID



--FINDING PATIENTS WHO WENT TO CARDIAC UNITS



IF OBJECT_ID(N'tempdb..#CARDIAC') IS NOT NULL 

DROP TABLE #CARDIAC;



SELECT 

	C.PAT_ENC_CSN_ID

	, V.IN_DTTM

	, V.OUT_DTTM



INTO

	#CARDIAC



FROM

	#COHORT C

	JOIN EMRDB..V_PATIENT_LOCATION_HISTORY V

		ON V.PAT_ENC_CSN = C.PAT_ENC_CSN_ID



WHERE

	V.ADT_DEPARTMENT_ID IN (20101124, 20101500, 20101501, 20120105, 20120106, 20120107, 200108131, 200108070, 200108007) --CARDIAC UNITS

	

--FINAL ENCOUNTER LIST WITHOUT THE CARDIAC ENCOUNTERS

IF OBJECT_ID(N'tempdb..#FinalData') IS NOT NULL 

DROP TABLE #FinalData;



SELECT

	CONVERT(numeric, C.Sepsis_Episode_ID_V01) AS Sepsis_Episode_ID_V01

	, CONVERT(datetime2(0), C.AntibioticOrderedTime_V59) AS AntibioticOrderedTime_V59

	, CONVERT(datetime2(0), C.AntibioticAdministeredTime_V60) AS AntibioticAdministeredTime_V60

	, CONVERT(datetime2(0), C.BloodCultureOrderedTime_V61) AS BloodCultureOrderedTime_V61

	, CONVERT(varchar, C.PAT_ENC_CSN_ID) AS PAT_ENC_CSN_ID

	, CONVERT(varchar, C.DATE_STAMP) AS DATE_STAMP

	, CONVERT(bit, C.REVIEWED) AS REVIEWED



INTO

	#FinalData 



FROM

	#FINAL C

	LEFT JOIN #CARDIAC A

		ON A.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID



WHERE

	A.PAT_ENC_CSN_ID IS NULL



-------------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

IF @TEST = 0

	BEGIN

		INSERT INTO reportingDB.[reports].[NON_SEVERE_SEPSIS_STAGING]

			([Sepsis_Episode_ID_V01]

			, [AntibioticOrderedTime_V59]

			, [AntibioticAdministeredTime_V60]

			, [BloodCultureOrderedTime_V61]

			, [PAT_ENC_CSN_ID]

			, [DATE_STAMP]

			, [Reviewed])



		SELECT 

			* 

		FROM

			#FinalData



		SELECT 

			*



		FROM

			reportingDB.[reports].[NON_SEVERE_SEPSIS_STAGING]



		WHERE

			DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate))

	END;

ELSE

	BEGIN

		SELECT 

			[Sepsis_Episode_ID_V01]

			, [AntibioticOrderedTime_V59]

			, [AntibioticAdministeredTime_V60]

			, [BloodCultureOrderedTime_V61]

			, [PAT_ENC_CSN_ID]



		FROM

			reportingDB.[reports].[NON_SEVERE_SEPSIS_STAGING]



		WHERE

			DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate))

	END;

-------------------------------------------------------------------------------------------------------------------------------------------------------

END;

END;

-------------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------END---------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------
GO

-- ==== reports/USP_RPTS_Severe_Sepsis.sql ====
CREATE         PROCEDURE [reports].[USP_Severe_Sepsis] 

--DECLARE

	@i_vRelativeStartDate VARCHAR(20) = NULL

	, @i_vRelativeEndDate VARCHAR(20) = NULL

	, @i_vRelativeTest VARCHAR(20) = NULL

	, @i_vRelativeOW VARCHAR(20) = NULL

	, @i_vHospitals INT = 1 -- 1 = MAIN Only, 2 = WEST Only, 3 = Both

AS



BEGIN

	DECLARE @StartDate DATE

	DECLARE @EndDate DATE

	DECLARE @TEST INT

	DECLARE @OW INT

	DECLARE @Hospitals INT;

/*

========================================================================================================================================================

Author:			Developer D

Create date:	10/12/2018

Description:	IPSO SEVERE SEPSIS. THIS CODE MUST BE RAN FOR FULL MONTH.

Sample Call:	EXEC [reportingDB].[reports].[USP_Severe_Sepsis] '', '', '0', '', 1   --TO WRITE DATA TO ARCHIVE TABLE. ******USE THIS COMMAND FOR BATCH******

				EXEC [reportingDB].[reports].[USP_Severe_Sepsis] '', '', '0', '0', 1	--TO OVERWRITE THE DATA IN THE ARCHIVE TABLE IF THE DATA ALREADY EXISTS

				EXEC [reportingDB].[reports].[USP_Severe_Sepsis] '', '', '1', '', 1

Change log: 

=========================================================================================================================================================

    Date                By:                        Description

    ============        ====================       ========================================================================================================

    2018-10-12          Developer D         CREATE STORED PROC

 	2018-12-04			Developer D			ADDED REVIED FILE CHECK LOGIC

    04.02.2019			V_DEV001					ADDED MEDICATION FOR BOLUS (, 700002	--SODIUM CHLORIDE 0.99 % INJECTION SYRINGE)

    05.16.2019			V_DEV001					CHANGED PROCEDURE_ORDERS.PROC_CODE TO PROCEDURE_ORDERS.PROC_ID AS PROC_CODE IS DEPRICATED IN PROCEDURE_ORDERS TABLE

 	08.08.2019			V_DEV001					33 CHANGES MADE TO THE ORIGINAL CODE BY Developer D. PLEASE SEE THE WORD DOCUMENT

 	08.16.2019			V_DEV001					Added 200108013 to GenCare departments

 	Developer D'S CODE		N:\BusinessIntelligenceTeam\Project Documentation\Quality Initiatives\Sepsis ETL\TKT-012\Code\USP_Severe_Sepsis_Prior_To_Change_On_08092019.doc

 	CODE CHANGES		N:\BusinessIntelligenceTeam\Project Documentation\Quality Initiatives\Sepsis ETL\TKT-012\Code\IPSO CHANGES.DOCX

 	CODE CHANGES		http://extranet.samplehealth.org/teams/bi/pmo/QualityInitiatives/Shared%20Documents/Report%20Requirements/2-%20Sepsis-Severe/IPSO%20Changes.docx

 	10.01.2019			V_DEV001					Added new ED Sepsis Score -R HS IP SEPSIS SCORE 2019 [9000002613]  and New Organ Dysfunction Score - R HS IP SEPSIS ODS 2019 [9000002644] 

 	12.06.2019			V_DEV001					MODIFICATION: Added code to include Quick Set/ Orderset OSQ 

													ED Sepsis Panel - OSQ 400002

													Sepsis Antimicrobials Unknown Source - OSQ 400007

													Neo Fever Panel - OSQ 400003

													Oncology with Fever Panel - OSQ 400004

	02.11.2020			V_DEV001					MODIFICATION: to #Base_Pop_1, Added code to include only Admit Conf Statuses 1(confirmed) & 2(complete) AND CHECK IF HOSP ADMIT TIME IS NOT NULL (ALTHOUG BOTH SHOULD DO THE SAME)

													REPLACE V_ICU_STAY_METRICS(DEPRICATED) WITH DM_ICU_STAY

	04.08.2020			V_DEV001					MODIFICATION: Added Huddle Time calculation logic and reporting data point. Huddle Time calculation for only IP OD Scores - since there is no huddle time for ED Sepsis scores

	06.19.2020			V_DEV001					MODIFICATION: Per Stakeholder A's request changing the defaul huddle time from '1900-01-02 00:00:00' TO '1900-01-01 00:00:00'

	10.12.2020			V_DEV001					MODIFICATION: Changed CONVERT(FLOAT to TRY_CAST(...as FLOAT)--> LacticAcidValue & Weight_v16--https://samplehealth.zendesk.com/agent/tickets/1133719

	01.21.2022			V_DEV001					MODIFICATION: Added 95 ST department to the list of GEN Floor departments

	02.12.2024			V_DEV005					Modifying from IPSO program to CHA and PHIS

	12.10.2024			V_DEV005					Modifying to remove accounts where primary plan is ORGANDONOR to prevent duplicate encounters for organ donor patients

 --==========================================================================================================================================================

 */

	IF @i_vRelativeStartDate IS NULL OR @i_vRelativeStartDate = ''

		SET @StartDate = EMRDB.[dbo].[fn_parse_date]('MB-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @StartDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeStartDate)



	IF @i_vRelativeEndDate IS NULL OR @i_vRelativeEndDate = ''

		SET @EndDate = EMRDB.[dbo].[fn_parse_date]('ME-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @EndDate = EMRDB.[dbo].[fn_parse_date](@i_vRelativeEndDate)	



	IF @i_vRelativeTest IS NULL OR @i_vRelativeTest = '' OR @i_vRelativeTest <> 0

		SET @TEST = 1

	ELSE

		SET @TEST = @i_vRelativeTest



	IF @i_vRelativeOW IS NULL OR @i_vRelativeOW = '' OR @i_vRelativeOW <> 0

		SET @OW = 1

	ELSE

		SET @OW = @i_vRelativeOW

		

	IF @i_vHospitals IS NULL OR @i_vHospitals = '' OR @i_vHospitals = 0 -- 1 = MAIN Only, 2 = WEST Only, 3 = Both

		SET @Hospitals = 1

	ELSE

		SET @Hospitals = @i_vHospitals

---------------------------------------------------------------------------------------------------------------------------------------------------

/* CHECK IF OVERWRITE FLAG IS ON */

---------------------------------------------------------------------------------------------------------------------------------------------------

WHILE @OW = 0



BEGIN

	DELETE FROM [reportingDB].[reports].[SEVERE_SEPSIS_STAGING]



	WHERE

		Reviewed = 0

		AND DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate));

		PRINT('EXISTING DATA DELETED... RUNNING CODE FOR NEW DATA')

	GOTO MAIN

END

---------------------------------------------------------------------------------------------------------------------------------------------------

/* CHECK IF DATA EXISTS */

---------------------------------------------------------------------------------------------------------------------------------------------------

IF 

	EXISTS( SELECT *

			FROM [reportingDB].[reports].[SEVERE_SEPSIS_STAGING]

			WHERE DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate))

			AND @TEST = 0

			)

		PRINT('Data for given time range already exists in [reports].[SEVERE_SEPSIS_STAGING]. USE EXEC COMMAND WITH 0 AS 4TH PARAMETER TO OVERWRITE THE DATA');

ELSE

		BEGIN

---------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------------------------------------

MAIN:

-------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------

/* Temp tables to for data used in subqueries */

IF OBJECT_ID(N'tempdb..#NICUCICUDept') IS NOT NULL DROP TABLE #NICUCICUDept;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEPARTMENT_ID

	INTO #NICUCICUDept

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800001', '800002', '800003')

CREATE INDEX IDX_NICICUDept ON #NICUCICUDept (DEPARTMENT_ID) 



IF OBJECT_ID(N'tempdb..#AllICUDept') IS NOT NULL DROP TABLE #AllICUDept;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEPARTMENT_ID

	INTO #AllICUDept

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800016') --HS BI IP ALL ICU UNITS

CREATE INDEX IDX_AllICUDept ON #AllICUDept (DEPARTMENT_ID) 

	

IF OBJECT_ID(N'tempdb..#MedDept') IS NOT NULL DROP TABLE #MedDept;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEPARTMENT_ID

	INTO #MedDept

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800004')

CREATE INDEX IDX_MedSurgDept ON #MedDept (DEPARTMENT_ID) 



IF OBJECT_ID(N'tempdb..#ODScores') IS NOT NULL DROP TABLE #ODScores;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO #ODScores

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800006')

CREATE INDEX IDX_OdScores ON #ODScores (FLO_ID) 



IF OBJECT_ID(N'tempdb..#BloodCultures') IS NOT NULL DROP TABLE #BloodCultures;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID PROC_ID

	INTO #BloodCultures

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'EAP'

	AND vcg.BASE_GROUPER_ID IN ('800013')

CREATE INDEX IDX_BloodCultures ON #BloodCultures (PROC_ID) 

	

IF OBJECT_ID(N'tempdb..#BolusMeds') IS NOT NULL DROP TABLE #BolusMeds;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID MED_ID

	INTO #BolusMeds

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'ERX'

	AND vcg.BASE_GROUPER_ID IN ('800009')

CREATE INDEX IDX_BolusMeds ON #BolusMeds (MED_ID) 

	

IF OBJECT_ID(N'tempdb..#BolusMedsOnce') IS NOT NULL DROP TABLE #BolusMedsOnce;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID MED_ID

	INTO #BolusMedsOnce

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'ERX'

	AND vcg.BASE_GROUPER_ID IN ('800017')

CREATE INDEX IDX_BolusMedOnce ON #BolusMedsOnce (MED_ID) 

	

IF OBJECT_ID(N'tempdb..#MedGroupers') IS NOT NULL DROP TABLE #MedGroupers;

	SELECT vcg.GROUPER_LIST VCG_ID

	INTO #MedGroupers

	FROM [EMRDB].[dbo].[GROUPER_GROUPS] vcg

	WHERE vcg.GROUPER_ID IN ('800011')

CREATE INDEX IDX_MedGroupers ON #MedGroupers (VCG_ID) 



IF OBJECT_ID(N'tempdb..#MedGroupersERX') IS NOT NULL DROP TABLE #MedGroupersERX;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID ERX_ID

	INTO #MedGroupersERX

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE VCG.COMPILED_CONTEXT = 'ERX'

	AND vcg.BASE_GROUPER_ID IN ('800011')

CREATE INDEX IDX_MedGroupersERX ON #MedGroupersERX (ERX_ID) 



IF OBJECT_ID(N'tempdb..#MARActions') IS NOT NULL DROP TABLE #MARActions;

	SELECT CAST(vcg.LIST_CAT_VALUE_C AS varchar) CAT_ID

	INTO #MARActions

	FROM [EMRDB].[dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800007')

CREATE INDEX IDX_MARActions ON #MARActions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#RouteExclusions') IS NOT NULL DROP TABLE #RouteExclusions;

	SELECT vcg.LIST_CAT_VALUE_C CAT_ID

	INTO #RouteExclusions

	FROM [EMRDB].[dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800008')

CREATE INDEX IDX_RouteExclusions ON #RouteExclusions (CAT_ID) 



IF OBJECT_ID(N'tempdb..#CVLFlo') IS NOT NULL DROP TABLE #CVLFlo;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO #CVLFlo

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800010')

CREATE INDEX IDX_CVLFlo ON #CVLFlo (FLO_ID) 

	

IF OBJECT_ID(N'tempdb..#SepsisScoreFlo') IS NOT NULL DROP TABLE #SepsisScoreFlo;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO #SepsisScoreFlo

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800005')

CREATE INDEX IDX_SepsisScoreFlo ON #SepsisScoreFlo (FLO_ID) 

	

IF OBJECT_ID(N'tempdb..#LacticAcidLRR') IS NOT NULL DROP TABLE #LacticAcidLRR;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID LRR_ID

	INTO #LacticAcidLRR

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'LRR'

	AND vcg.BASE_GROUPER_ID IN ('800012')

CREATE INDEX IDX_Lactic ON #LacticAcidLRR (LRR_ID) 



IF OBJECT_ID(N'tempdb..#LacticAcidLRRByName') IS NOT NULL DROP TABLE #LacticAcidLRRByName;

	SELECT cc.COMPONENT_ID LRR_ID

	INTO #LacticAcidLRRByName

	FROM [EMRDB].[dbo].[LAB_COMPONENTS] cc

	WHERE cc.NAME LIKE '%LACTIC ACID%'

CREATE INDEX IDX_Lacticacidbyname ON #LacticAcidLRRByName (LRR_ID) 



IF OBJECT_ID(N'tempdb..#Ordersets') IS NOT NULL DROP TABLE #Ordersets;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID PRL_ID

	INTO #Ordersets

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'PRL'

	AND vcg.BASE_GROUPER_ID IN ('800018')

CREATE INDEX IDX_ordersets ON #Ordersets (PRL_ID) 

	

IF OBJECT_ID(N'tempdb..#DXSepticShock') IS NOT NULL DROP TABLE #DXSepticShock;

	SELECT vcg.CODE EDG_ID

	INTO #DXSepticShock

	FROM [EMRDB].[dbo].[GROUPER_TERMINOLOGY] vcg

	WHERE vcg.GROUPER_ID IN ('800019')

CREATE INDEX IDX_septicshock ON #DXSepticShock (EDG_ID) 

	

IF OBJECT_ID(N'tempdb..#DXSepsis') IS NOT NULL DROP TABLE #DXSepsis;

	SELECT vcg.CODE EDG_ID

	INTO #DXSepsis

	FROM [EMRDB].[dbo].[GROUPER_TERMINOLOGY] vcg

	WHERE vcg.GROUPER_ID IN ('800020')

CREATE INDEX IDX_Sepsis ON #DXSepsis (EDG_ID) 

	

IF OBJECT_ID(N'tempdb..#EDDepts') IS NOT NULL DROP TABLE #EDDepts;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEP_ID

	INTO #EDDepts

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800021')

CREATE INDEX IDX_EDDepts ON #EDDepts (DEP_ID) 

	

IF OBJECT_ID(N'tempdb..#HemOncBMTDepts') IS NOT NULL DROP TABLE #HemOncBMTDepts;

	SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEP_ID

	INTO #HemOncBMTDepts

	FROM [EMRDB].[dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800022')

CREATE INDEX IDX_HOBMTDepts ON #HemOncBMTDepts (DEP_ID) 



IF OBJECT_ID(N'tempdb..#DXIDCebrealPalsy') IS NOT NULL DROP TABLE #DXIDCebrealPalsy;

	SELECT vcg.CODE EDG_ID

	INTO #DXIDCebrealPalsy

	FROM [EMRDB].[dbo].[GROUPER_TERMINOLOGY] vcg

	WHERE vcg.GROUPER_ID IN ('800023')

CREATE INDEX IDX_exidcebrealpalsy ON #DXIDCebrealPalsy (EDG_ID) 



IF OBJECT_ID(N'tempdb..#DXTrachDependent') IS NOT NULL DROP TABLE #DXTrachDependent;

	SELECT vcg.CODE EDG_ID

	INTO #DXTrachDependent

	FROM [EMRDB].[dbo].[GROUPER_TERMINOLOGY] vcg

	WHERE vcg.GROUPER_ID IN ('800024')

CREATE INDEX IDX_dxtrachdep ON  #DXTrachDependent(EDG_ID) 



IF OBJECT_ID(N'tempdb..#ERXAntimicrobial') IS NOT NULL DROP TABLE #ERXAntimicrobial;

	SELECT cntl.CODE 

	, cntl.VALUE_SET_DISPLAY as AGENT

	, case when CHARINDEX('^',cntl.VALUE_SET_ABBR)>0 then SUBSTRING(cntl.VALUE_SET_ABBR,0,CHARINDEX('^',cntl.VALUE_SET_ABBR)) else cntl.VALUE_SET_ABBR end as AGENT_GROUP

	, case when cntl.VALUE_SET_ABBR like '%^Y' then 1 else 0 end as DOT_MONITORING

	INTO #ERXAntimicrobial

	FROM reportingDB.reports.CONFIG_VALUE_SET cntl 

	WHERE cntl.VALUE_SET_ID = 3016

CREATE INDEX IDX_ERXAntimicrobial ON  #ERXAntimicrobial(CODE) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

/* DEFINING BASE POPULATION */

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*GETTING ENCOUNTERS WITHIN GIVEN DATE RANGES SO WE DON'T HAVE TO QUERY ON WHOLE DATABASE FOR EACH CRITERIA*/

IF OBJECT_ID(N'tempdb..#Base_Pop_1') IS NOT NULL DROP TABLE #Base_Pop_1;

SELECT DISTINCT

	PEH.PAT_ID

	, PEH.PAT_ENC_CSN_ID

	, HTR.HSP_ACCOUNT_ID

	, PEH.INPATIENT_DATA_ID

	, PEH.ADT_ARRIVAL_TIME

	, PEH.HOSP_ADMSN_TIME

	, PEH.ADMIT_SOURCE_C

	, PEH.INP_ADM_DATE

	, PEH.HOSP_DISCH_TIME

	, PEH.DISCH_DISP_C

	, DATEDIFF(MM,PAT.BIRTH_DATE,COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.HOSP_ADMSN_TIME)) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	, HTR.REVENUE_LOC_ID

INTO #Base_Pop_1

FROM EMRDB.dbo.V_HOSPITAL_TRANSACTIONS HTR

INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON HTR.PAT_ENC_CSN_ID = PEH.PAT_ENC_CSN_ID AND PEH.ADMIT_CONF_STAT_C IN (1,4) AND PEH.HOSP_ADMSN_TIME IS NOT NULL AND PEH.ADT_PAT_CLASS_C <> 102

INNER JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

INNER JOIN EMRDB.dbo.HOSPITAL_ACCOUNTS HAR ON HAR.HSP_ACCOUNT_ID = HTR.HSP_ACCOUNT_ID

INNER JOIN EMRDB.dbo.CALENDAR_DATES dd ON dd.CALENDAR_DT = CAST(PEH.HOSP_DISCH_TIME AS DATE)

WHERE HTR.SERVICE_DATE BETWEEN @StartDate AND @EndDate 

AND (

	HAR.ACCT_BASECLS_HA_C IN (1,3)--EXCLUDE OUTPATIENTS

	OR

	HAR.ACCT_CLASS_HA_C = 104--BUT INCLUDE OBSERVATION PATIENTS

)

AND HTR.TX_TYPE_HA_C = 1

AND HAR.ACCT_BILLSTS_HA_C <> 99 --Combined HAR (Not the primary)

AND dd.CALENDAR_DT BETWEEN @StartDate AND @EndDate

AND ( -- Developer C - Added to restrict datas by hospital location

		(@Hospitals = 1 AND HTR.REVENUE_LOC_ID IN ('200108', '200999')) -- MAIN ONLY

	OR	(@Hospitals = 2 AND HTR.REVENUE_LOC_ID IN ('200200', '200299')) -- WEST Only

	OR	(@Hospitals = 3 AND htr.REVENUE_LOC_ID IS NOT NULL) -- Any hospital

)

AND htr.HSP_ACCOUNT_ID NOT IN (SELECT HSP_ACCOUNT_ID FROM EMRDB.dbo.HOSPITAL_ACCOUNTS_EXT WHERE AT_BILLING_PRIM_PAYER_ID = 2109) 

	-- Exclude Hospital Accounts where PATIENTS is on ORGANDONOR insurance (organ donations)

CREATE INDEX IDX_BasePop1 ON #Base_Pop_1 (PAT_ENC_CSN_ID) 

-- SELECT * FROM #Base_Pop_1



/* LIST OF ENCOUNTER ADMITTED DIRECTLY TO NICU BEGIN */

IF OBJECT_ID(N'tempdb..#NICUAdmissions') IS NOT NULL DROP TABLE #NICUAdmissions;

SELECT DISTINCT ADT.PAT_ENC_CSN_ID 

INTO #NICUAdmissions

FROM #Base_Pop_1 B

INNER JOIN EMRDB.dbo.ADT_EVENTS ADT ON ADT.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE ADT.EVENT_TYPE_C = 1 --ADMISSION

AND ADT.EVENT_SUBTYPE_C <> 2 --CANCELLED

AND ADT.DEPARTMENT_ID IN ( SELECT * FROM #NICUCICUDept)

/* LIST OF ENCOUNTER ADMITTED DIRECTLY TO NICU END */



--Final Base Population -- ALL ENCOUNTERS FROM PREVIOUS MONTH WHERE PATIENTS WAS ADMITTED (NOT DISCHARGED FROM ED). EXCLUDING PATIENTS WHO WERE ADMITTED TO NICU DIRECTLY

IF OBJECT_ID(N'tempdb..#Base_Pop') IS NOT NULL DROP TABLE #Base_Pop;

SELECT FP.*

INTO #Base_Pop

FROM #Base_Pop_1 FP

WHERE FP.PAT_ENC_CSN_ID NOT IN (SELECT PAT_ENC_CSN_ID FROM #NICUAdmissions)--EXCLUDE NICU ADMISSIONS

AND FP.PAT_ENC_CSN_ID  NOT IN (SELECT DISTINCT PAT_ENC_CSN_ID FROM reportingDB.reports.SEVERE_SEPSIS_STAGING)--make sure we are not includiung already submitted encounters

	-- Developer C moved from #Base_Pop_1 to #Base_Pop for reporting on a month that's already been submitted

CREATE INDEX IDX_BasePopPat ON #Base_Pop (PAT_ENC_CSN_ID) 

CREATE INDEX IDX_BasePopFLO ON #Base_Pop (INPATIENT_DATA_ID) 



--SELECT * FROM #Base_Pop WHERE HSP_ACCOUNT_ID = '6003056042'

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* Treatment Plan Begin*/

-- All encounters from #Base_pop where ABX was administered

IF OBJECT_ID(N'tempdb..#TreatPlanABX') IS NOT NULL DROP TABLE #TreatPlanABX; --SELECT * FROM #TreatPlanABX

SELECT om.PAT_ENC_CSN_ID

	, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

	, cm.NAME

INTO #TreatPlanABX

FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

INNER JOIN EMRDB.dbo.MEDICATION_ORDERS om ON om.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = om.MEDICATION_ID --AND CM.THERA_CLASS_C = 11 --Antibiotics

INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = om.ORDER_MED_ID

WHERE MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

AND om.MED_ROUTE_C = 11--IV ONLY

AND MAI.MAR_ACTION_C IN (SELECT * FROM #MARActions)

AND om.MEDICATION_ID IN 

	(	

		SELECT medlist.MEDICATION_ID

		FROM (

			SELECT erx.MEDICATION_ID

				, erx.NAME

				, cntl.AGENT

				, cntl.AGENT_GROUP

				, cntl.DOT_MONITORING

				, gen.TITLE

				, ROW_NUMBER() over(partition by erx.MEDICATION_ID order by cntl.DOT_MONITORING, cntl.AGENT asc) as AGENT_ORDER

			FROM EMRDB.dbo.MEDICATIONS erx

			OUTER APPLY( --Get the main medication's simple generic if its a mixture

				SELECT TOP 1 

					mix.DRUG_ID

					, comp.SIMPLE_GENERIC_C 

				FROM EMRDB.dbo.MED_MIX_COMPONENTS mix

				INNER JOIN EMRDB.dbo.MEDICATIONS comp on mix.DRUG_ID = comp.MEDICATION_ID

				WHERE mix.TYPE_C = 3		--3 - Medications 

				AND mix.MEDICATION_ID = erx.MEDICATION_ID

				ORDER BY mix.LINE

			) mixture

			INNER JOIN EMRDB.dbo.REF_GENERIC_MED gen on gen.SIMPLE_GENERIC_C = coalesce(erx.SIMPLE_GENERIC_C,mixture.SIMPLE_GENERIC_C)

			INNER JOIN #ERXAntimicrobial cntl ON cntl.CODE = gen.SIMPLE_GENERIC_C

		) medlist

		WHERE medlist.AGENT_ORDER=1						

	)

UNION

	SELECT DISTINCT

		om.PAT_ENC_CSN_ID

		, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

		, cm.NAME

	FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS om ON om.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = om.MEDICATION_ID AND CM.THERA_CLASS_C = 11 --Antibiotics

	INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = om.ORDER_MED_ID

	WHERE MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

	AND om.MED_ROUTE_C = 11--IV ONLY

	AND MAI.MAR_ACTION_C IN (SELECT * FROM #MARActions)

CREATE INDEX IDX_TreatPlan ON #TreatPlanABX (PAT_ENC_CSN_ID) 

	--SELECT * FROM #TreatPlanABX 



-- All encounters from #Base_pop where Bolus was administered

IF OBJECT_ID(N'tempdb..#TreatPlanBolus') IS NOT NULL DROP TABLE #TreatPlanBolus;

SELECT b.PAT_ENC_CSN_ID

	, mai.TAKEN_TIME AS BOLUS_ADMIN_TIME

	, ROW_NUMBER() OVER(PARTITION BY b.PAT_ENC_CSN_ID ORDER BY mai.TAKEN_TIME ASC) BOLUS_NUM

	, mai.SIG AS BOLUS_VOLUME

INTO #TreatPlanBolus

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.MEDICATION_ORDERS om ON om.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.MEDICATIONS cm ON cm.MEDICATION_ID = om.MEDICATION_ID

INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS mai ON mai.ORDER_MED_ID = om.ORDER_MED_ID

WHERE MAI.TAKEN_TIME IS NOT NULL --ADMINISTERED BOLUS ONLY

AND ( om.MEDICATION_ID IN (SELECT * FROM #BolusMeds) 

	OR (om.MEDICATION_ID IN (SELECT * FROM #BolusMedsOnce) AND om.HV_DISCR_FREQ_ID = '300902')

) -- FREQUENCY = ONCE 

AND (mai.MAR_ACTION_C IN (SELECT * FROM #MARActions) AND mai.MAR_ACTION_C <> '99') --3/18/24 - Original code didn't have Rate Change action Stakeholder A believes there was a specific reason so leaving as it was 

AND CONVERT(NUMERIC, mai.SIG ) > 95.0

GROUP BY b.PAT_ENC_CSN_ID

	, mai.TAKEN_TIME

	, mai.SIG

CREATE INDEX IDX_TreatPlanBolus ON #TreatPlanBolus (PAT_ENC_CSN_ID) 



-- All encounters with 2 bolusus within 6 hours

IF OBJECT_ID(N'tempdb..#BOL22') IS NOT NULL DROP TABLE #BOL22

SELECT PAT_ENC_CSN_ID

	, BOLUS_ADMIN_TIME AS FIRST_BOLUS_TIME

	, LEAD(BOLUS_ADMIN_TIME,1,NULL) OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY BOLUS_ADMIN_TIME) AS SECOND_BOLUS_TIME

	, ABS(DATEDIFF(MI,BOLUS_ADMIN_TIME, LEAD(BOLUS_ADMIN_TIME,1,NULL) OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY BOLUS_ADMIN_TIME)))/60.0 AS BOL12_TIME

INTO #BOL22 

FROM #TreatPlanBolus

CREATE INDEX IDX_Bol22 ON #BOL22 (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#TPTwoBolus') IS NOT NULL DROP TABLE #TPTwoBolus;	

SELECT B1.PAT_ENC_CSN_ID

	,B1.FIRST_BOLUS_TIME

	, B1.SECOND_BOLUS_TIME

INTO #TPTwoBolus

FROM #BOL22 B1

WHERE B1.BOL12_TIME <= 6.0

--CREATE INDEX IDX_TPTwoBolus ON #TPTwoBolus (PAT_ENC_CSN_ID) 



-- All encounters from #Base_pop where Pressor was administered

IF OBJECT_ID(N'tempdb..#TreatPlanPres') IS NOT NULL DROP TABLE #TreatPlanPres;

SELECT B.PAT_ENC_CSN_ID

	, MAI.MAR_ACTION_C

	, MAI.TAKEN_TIME AS PRESSOR_START_TIME

	, ROW_NUMBER() OVER(PARTITION BY B.PAT_ENC_CSN_ID ORDER BY MAI.TAKEN_TIME ASC) AS SS_LINE

	, GMR.GROUPER_ID

INTO #TreatPlanPres 

FROM #Base_Pop B

INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

INNER JOIN EMRDB.dbo.GROUPER_MED_RECORDS GMR ON GMR.EXP_MEDS_LIST_ID = CM.MEDICATION_ID

INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

		AND MAI.ROUTE_C = 11  --INTRAVENOUS		

WHERE GMR.GROUPER_ID IN (SELECT * FROM #MedGroupers)

CREATE INDEX IDX_TreatPlanPres ON #TreatPlanPres (PAT_ENC_CSN_ID) 



-- All encounters with a bolus and a pressor within 6 hours

IF OBJECT_ID(N'tempdb..#TPBolusPressor') IS NOT NULL DROP TABLE #TPBolusPressor;

SELECT b.PAT_ENC_CSN_ID

	, b.BOLUS_ADMIN_TIME AS BOLUS_TIME

	, p.PRESSOR_START_TIME AS PRESSOR_TIME

INTO #TPBolusPressor

FROM #TreatPlanBolus b

INNER JOIN #TreatPlanPres p ON b.PAT_ENC_CSN_ID = p.PAT_ENC_CSN_ID

WHERE ABS(DATEDIFF(MI, b.BOLUS_ADMIN_TIME, p.PRESSOR_START_TIME))/60.0 <= 6.0 --BOLUS AND PRESSOR WITHIN 6 HOURS

--CREATE INDEX IDX_TPBolusPres ON #TPBolusPressor (PAT_ENC_CSN_ID) 

	

-- All encounters with 2 bolusus and abx within 6 hours

IF OBJECT_ID(N'tempdb..#TPAbx2Bolus') IS NOT NULL DROP TABLE #TPAbx2Bolus;	

SELECT tpa.PAT_ENC_CSN_ID

	, tpa.ABX_ADMIN_TIME

	, tpb.FIRST_BOLUS_TIME

	, tpb.SECOND_BOLUS_TIME

INTO #TPAbx2Bolus

FROM #TreatPlanABX tpa

JOIN #TPTwoBolus tpb ON tpb.PAT_ENC_CSN_ID = tpa.PAT_ENC_CSN_ID

WHERE ABS(DATEDIFF(MI, tpa.ABX_ADMIN_TIME, tpb.FIRST_BOLUS_TIME))/60.0 <= 6 --ABX AND BOLUS WITHIN 6 HOURS

AND ABS(DATEDIFF(MI, tpa.ABX_ADMIN_TIME, tpb.SECOND_BOLUS_TIME))/60.0 <= 6 --ABX AND SECOND BOLUS WITHIN 6 HOURS

--CREATE INDEX IDX_TPAbx2Bolus ON #TPAbx2Bolus (PAT_ENC_CSN_ID) 



-- All encounters with a bolus, a pressor and abx within 6 hours

IF OBJECT_ID(N'tempdb..#TPAbxBolusPressor') IS NOT NULL DROP TABLE #TPAbxBolusPressor;	

SELECT tpa.PAT_ENC_CSN_ID

	, tpa.ABX_ADMIN_TIME

	, tpbp.BOLUS_TIME

	, tpbp.PRESSOR_TIME

INTO #TPAbxBolusPressor

FROM #TreatPlanABX tpa

JOIN #TPBolusPressor tpbp ON tpbp.PAT_ENC_CSN_ID = tpa.PAT_ENC_CSN_ID

WHERE ABS(DATEDIFF(MI, tpa.ABX_ADMIN_TIME, tpbp.BOLUS_TIME))/60.0 <= 6 --ABX AND BOLUS WITHIN 6 HOURS 

AND ABS(DATEDIFF(MI, tpa.ABX_ADMIN_TIME, tpbp.PRESSOR_TIME))/60.0 <= 6 --ABX AND SECOND BOLUS WITHIN 6 HOURS	

--CREATE INDEX IDX_TPAbxBolusPressor ON #TPAbxBolusPressor (PAT_ENC_CSN_ID) 

	

-- Merging them into one table for the first part of treatment plan i.e., abx + (2 boluses or (1 bolus + pressor))

IF OBJECT_ID(N'tempdb..#TP1') IS NOT NULL DROP TABLE #TP1;

	SELECT  PAT_ENC_CSN_ID

		, ABX_ADMIN_TIME

		, FIRST_BOLUS_TIME

		, SECOND_BOLUS_TIME

		, NULL AS PRESSOR_START_TIME

	INTO #TP1

	FROM #TPAbx2Bolus

UNION ALL

	SELECT PAT_ENC_CSN_ID

		, ABX_ADMIN_TIME

		, BOLUS_TIME AS FIRST_BOLUS_TIME

		, NULL AS SECOND_BOLUS_TIME

		, PRESSOR_TIME

	FROM #TPAbxBolusPressor

--CREATE INDEX IDX_TP1 ON #TP1 (PAT_ENC_CSN_ID) 



--Getting List of Encounters where a Blood Culture was ordered. this is the 2nd pat of treatment plan

IF OBJECT_ID(N'tempdb..#TP2') IS NOT NULL DROP TABLE #TP2;

SELECT b.PAT_ENC_CSN_ID

	, op.ORDER_INST AS BLOOD_CULTURE_ORDER_TIME

INTO #TP2

FROM #Base_Pop b

INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS op ON op.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	AND op.PROC_ID IN (SELECT * FROM #BloodCultures)  --BLOOD CULTURE

	AND op.INSTANTIATED_TIME IS NOT NULL 

	AND op.FUTURE_OR_STAND IS NULL

--CREATE INDEX IDX_TP2 ON #TP2 (PAT_ENC_CSN_ID) 



--COMBINING BOTH PARTS OF TREATMENT PLAN INTO ONE

IF OBJECT_ID(N'tempdb..#Treatment') IS NOT NULL DROP TABLE #Treatment;

SELECT p1.*

	, p2.BLOOD_CULTURE_ORDER_TIME

INTO #Treatment 

FROM #TP1 p1

INNER JOIN #TP2 p2 ON p2.PAT_ENC_CSN_ID = p1.PAT_ENC_CSN_ID

WHERE p2.BLOOD_CULTURE_ORDER_TIME BETWEEN DATEADD(HH, -72, p1.ABX_ADMIN_TIME) AND DATEADD(HH, 72, p1.ABX_ADMIN_TIME) --BLOOD CULTURE ORDERED 72 HOURS BEFORE OF AFTER ABX ADMINISTERED TIME

AND p2.BLOOD_CULTURE_ORDER_TIME BETWEEN DATEADD(HH, -72, P1.FIRST_BOLUS_TIME) AND DATEADD(HH, 72, p1.FIRST_BOLUS_TIME) --BLOOD CULTURE ORDERED 72 HOURS BEFORE OF AFTER FIRST BOLUS ADMINISTERED TIME

AND p2.BLOOD_CULTURE_ORDER_TIME BETWEEN DATEADD(HH, -72, COALESCE(p1.SECOND_BOLUS_TIME, p1.PRESSOR_START_TIME)) AND DATEADD(HH, 72, COALESCE(p1.SECOND_BOLUS_TIME, p1.PRESSOR_START_TIME)) --BLOOD CULTURE ORDERED 72 HOURS BEFORE OF AFTER SECONF BOLUS OR PRESSOR ADMINISTERED TIME

CREATE INDEX IDX_Treatment ON #Treatment (PAT_ENC_CSN_ID) 

/* Treatment Plan End */

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*SEVERE SEPSIS CRITERIA 1 BEGIN*/

/*1. ER SEPSIS SCORE >= 95 OR OD SCORE >= 3

AND 2. TREAMENT*/



--POSITIVE SEPSIS SCORES

IF OBJECT_ID(N'tempdb..#Base_Pop_Severe_ED_Scores') IS NOT NULL DROP TABLE #Base_Pop_Severe_ED_Scores;

SELECT BP.PAT_ENC_CSN_ID

	, IFM.MEAS_VALUE

	, IFM.RECORDED_TIME

	, BP.ADT_ARRIVAL_TIME

	, BP.INP_ADM_DATE

INTO  #Base_Pop_Severe_ED_Scores 

FROM #Base_Pop BP 

INNER JOIN EMRDB.dbo.PATIENT_ENCOUNTERS enc on enc.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

--INNER JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = BP.PAT_ENC_CSN_ID AND PEH.ADT_ARRIVAL_TIME IS NOT NULL--MAKE SURE ITS AN ED ARRIVAL--Arrival Time Filter addedd on 07.30.2019

JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = enc.INPATIENT_DATA_ID

JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

WHERE IFM.FLO_MEAS_ID IN (SELECT * FROM #SepsisScoreFlo)

AND IFM.RECORDED_TIME < COALESCE(BP.INP_ADM_DATE, BP.HOSP_DISCH_TIME) --since ED Sepsis Score is also documented in IP setting but can't be counted towards Positive Sepsis Score, making sure that it is before the PATIENTS departed ED--addedd on 07.30.2019

CREATE INDEX IDX_BPEDScore ON #Base_Pop_Severe_ED_Scores (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#ED_PositiveScores') IS NOT NULL DROP TABLE #ED_PositiveScores;

SELECT PAT_ENC_CSN_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS SS_LINE

INTO #ED_PositiveScores

FROM #Base_Pop_Severe_ED_Scores

WHERE MEAS_VALUE > 4

ORDER BY PAT_ENC_CSN_ID

--CREATE INDEX IDX_EDPosScores ON #ED_PositiveScores (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#Base_Pop_Severe_IP_Scores') IS NOT NULL DROP TABLE #Base_Pop_Severe_IP_Scores;

SELECT BP.PAT_ENC_CSN_ID

	, IFM.MEAS_VALUE

	, IFM.RECORDED_TIME

INTO #Base_Pop_Severe_IP_Scores

FROM #Base_Pop BP 

INNER JOIN EMRDB.dbo.PATIENT_ENCOUNTERS enc on enc.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = enc.INPATIENT_DATA_ID

JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

WHERE IFM.FLO_MEAS_ID IN (SELECT * FROM #ODScores)

AND IFM.RECORDED_TIME > COALESCE(BP.INP_ADM_DATE,BP.HOSP_ADMSN_TIME) --WE WANT OD SCORES AFTER THE PATIENTS'S STATUS WAS CHANGED TO IP 

--CREATE INDEX IDX_BPIPScores ON #Base_Pop_Severe_IP_Scores (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#IP_PositiveScores') IS NOT NULL DROP TABLE #IP_PositiveScores;

SELECT PAT_ENC_CSN_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY RECORDED_TIME ASC) AS SS_LINE	

INTO #IP_PositiveScores

FROM #Base_Pop_Severe_IP_Scores

WHERE MEAS_VALUE > 2 --OD SCORES >=3 IS A POSITIVE SCORE

ORDER BY PAT_ENC_CSN_ID

--CREATE INDEX IDX_IPPosScore ON #IP_PositiveScores (PAT_ENC_CSN_ID) 

	

-- GETTING SCORE INFO FOR EACH ENCOUNTER

IF OBJECT_ID(N'tempdb..#ScoresAll') IS NOT NULL DROP TABLE #ScoresAll;

	SELECT IP.PAT_ENC_CSN_ID

		, MEAS_VALUE AS SCORE

		, IP.RECORDED_TIME AS SCORE_TIME

	INTO #ScoresAll

	FROM #IP_PositiveScores IP

UNION

	SELECT ED.PAT_ENC_CSN_ID

		, MEAS_VALUE AS SCORE

		, ED.RECORDED_TIME AS SCORE_TIME

	FROM #ED_PositiveScores ED

--CREATE INDEX IDX_ScoresAll ON #ScoresAll (PAT_ENC_CSN_ID) 



-- Ranking the scores 

IF OBJECT_ID(N'tempdb..#Scores') IS NOT NULL DROP TABLE #Scores;

SELECT *

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY SCORE_TIME ASC) AS SS_LINE

INTO #Scores 

FROM #ScoresAll

GROUP BY PAT_ENC_CSN_ID

	, SCORE_TIME

	, SCORE

CREATE INDEX IDX_Scores ON #Scores (PAT_ENC_CSN_ID) 



--ADDING TREATMENT PLAN CRITERIA

IF OBJECT_ID(N'tempdb..#SSTP') IS NOT NULL DROP TABLE #SSTP;

SELECT S.PAT_ENC_CSN_ID

	, S.SCORE_TIME

	, TP1.ABX_ADMIN_TIME AS TREATMENT_ABX_ADMIN_TIME

	, TP1.FIRST_BOLUS_TIME AS TREATMENT_FIRST_BOLUS_TIME

	, TP1.SECOND_BOLUS_TIME AS TREATMENT_SECOND_BOLUS_TIME

	, TP1.PRESSOR_START_TIME AS TREATMENT_PRESSOR_START_TIME

	, TP1.BLOOD_CULTURE_ORDER_TIME AS TREATMENT_BLOOD_CULTURE_TIME

INTO #SSTP

FROM #Scores S

INNER JOIN #Treatment TP1 ON S.PAT_ENC_CSN_ID = TP1.PAT_ENC_CSN_ID	

WHERE TP1.ABX_ADMIN_TIME BETWEEN DATEADD(HH, -24, S.SCORE_TIME) AND DATEADD(HH, 24, S.SCORE_TIME) --ABX ADMINISTERED TIME 24 HOURS BEFORE OF AFTER +ve SEPSIS SCORE TIME

AND TP1.FIRST_BOLUS_TIME BETWEEN DATEADD(HH, -24, S.SCORE_TIME) AND DATEADD(HH, 24, S.SCORE_TIME) --FIRST BOLUS ADMINISTERED TIME 24 HOURS BEFORE OF AFTER +ve SEPSIS SCORE TIME

AND COALESCE(TP1.SECOND_BOLUS_TIME, TP1.PRESSOR_START_TIME) BETWEEN DATEADD(HH, -24, S.SCORE_TIME) AND DATEADD(HH, 24, S.SCORE_TIME) --SECOND BOLUS ADMINISTERED TIME OR PRESSOR TIME 24 HOURS BEFORE OF AFTER +ve SEPSIS SCORE TIME

ORDER BY S.PAT_ENC_CSN_ID

	, S.SCORE_TIME

	, TP1.ABX_ADMIN_TIME

	, TP1.FIRST_BOLUS_TIME

	, TP1.SECOND_BOLUS_TIME

	, TP1.PRESSOR_START_TIME

	, TP1.BLOOD_CULTURE_ORDER_TIME

--CREATE INDEX IDX_sstp ON #SSTP (PAT_ENC_CSN_ID) 	

-- GETTING DISTINCT ENCOUNTERS THAT SATISFY CRITERIA 1



/*CRITERIA 2 DOESN'T APPLY*/

-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* Criteria 3. Orderset and Treatment  Begin*/

/* MEDICATION/ PROCEDURES ORDERS FROM OSQ's ARE ALSO CONSIDERED AS ORDERSET USAGE */

IF OBJECT_ID(N'tempdb..#SSOrderSetOSQ_PRL') IS NOT NULL DROP TABLE #SSOrderSetOSQ_PRL;

	SELECT b.PAT_ENC_CSN_ID

		, om.ORDER_DTTM

		, om2.ORD_OSQ_ID AS PRL_ORDERSET_ID

	INTO #SSOrderSetOSQ_PRL

	FROM #Base_Pop b

	INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS om ON om.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS_EXT om2 ON om2.ORDER_ID = om.ORDER_ID 

		AND om2.ORD_OSQ_ID IN (400002,400007,400003,400004)

UNION

	SELECT b.PAT_ENC_CSN_ID

		, om.ORDER_DTTM

		, om2.ORD_OSQ_ID AS PRL_ORDERSET_ID

	FROM #Base_Pop b

	INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS om ON om.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS_EXT om2 ON om2.ORDER_ID = om.ORDER_ID 

		AND om2.ORD_OSQ_ID IN (400002,400007,400003,400004)

UNION

	SELECT b.PAT_ENC_CSN_ID

		, om.ORDER_DTTM

		, om.PRL_ORDERSET_ID

	FROM #Base_Pop b

	INNER JOIN EMRDB.dbo.ORDER_TRACKING_METRICS om ON om.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	WHERE om.PRL_ORDERSET_ID IN (SELECT * FROM #Ordersets)--Severe Sepsis, Short Stay – Sepsis, H/O – Sepsis CLINICAL_ALERTS, ID – Staph Aureus Sepsis, H/O Sepsis CLINICAL_ALERTS in Clinic, Sepsis Pathway

--CREATE INDEX IDX_SSOrdSetPRL ON #SSOrderSetOSQ_PRL (PAT_ENC_CSN_ID) 

	

IF OBJECT_ID(N'tempdb..#SSOrderSet') IS NOT NULL DROP TABLE #SSOrderSet;

SELECT PAT_ENC_CSN_ID

	, ORDER_DTTM

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY ORDER_DTTM ASC) AS SS_LINE

	, PRL_ORDERSET_ID

INTO #SSOrderSet 

FROM #SSOrderSetOSQ_PRL

CREATE INDEX IDX_SSOrdSet ON #SSOrderSet (PAT_ENC_CSN_ID) 



--ADDING TREATMENT PLAN CRITERIA

IF OBJECT_ID(N'tempdb..#OSTP') IS NOT NULL DROP TABLE #OSTP;

SELECT s.PAT_ENC_CSN_ID

	, s.ORDER_DTTM

	, tp1.ABX_ADMIN_TIME AS TREATMENT_ABX_ADMIN_TIME

	, tp1.FIRST_BOLUS_TIME AS TREATMENT_FIRST_BOLUS_TIME

	, tp1.SECOND_BOLUS_TIME AS TREATMENT_SECOND_BOLUS_TIME

	, tp1.PRESSOR_START_TIME AS TREATMENT_PRESSOR_START_TIME

	, tp1.BLOOD_CULTURE_ORDER_TIME AS TREATMENT_BLOOD_CULTURE_TIME

	, ROW_NUMBER() OVER(PARTITION BY s.PAT_ENC_CSN_ID ORDER BY s.ORDER_DTTM ASC) AS SS_LINE

INTO #OSTP

FROM #SSOrderSet s

INNER JOIN #Treatment TP1 ON s.PAT_ENC_CSN_ID = tp1.PAT_ENC_CSN_ID	

WHERE tp1.ABX_ADMIN_TIME BETWEEN DATEADD(HH, -24, s.ORDER_DTTM) AND DATEADD(HH, 24, s.ORDER_DTTM) --ABX ADMINISTERED TIME 24 HOURS BEFORE OF AFTER SEPSIS ORDERSET TIME

AND tp1.FIRST_BOLUS_TIME BETWEEN DATEADD(HH, -24, s.ORDER_DTTM) AND DATEADD(HH, 24, s.ORDER_DTTM) --FIRST BOLUS ADMINISTERED TIME 24 HOURS BEFORE OF AFTER SEPSIS ORDERSET TIME

AND COALESCE(tp1.SECOND_BOLUS_TIME, tp1.PRESSOR_START_TIME) BETWEEN DATEADD(HH, -24, s.ORDER_DTTM) AND DATEADD(HH, 24, s.ORDER_DTTM) --SECOND BOLUS ADMINISTERED TIME OR PRESSOR TIME 24 HOURS BEFORE OF AFTER SEPSIS ORDERSET TIME

ORDER BY s.PAT_ENC_CSN_ID

	, s.ORDER_DTTM

	, tp1.ABX_ADMIN_TIME

	, tp1.FIRST_BOLUS_TIME

	, tp1.SECOND_BOLUS_TIME

	, tp1.PRESSOR_START_TIME

	, tp1.BLOOD_CULTURE_ORDER_TIME

--CREATE INDEX IDX_OSTP ON #OSTP (PAT_ENC_CSN_ID) 



/* GETTING DISTINCT ENCOUNTERS THAT SATISFY CRITERIA 3 */

/*---------------------------------------------------------------------------------------------------------------------------------------------------

	ESTANBLISHING PATIENTS QUALIFIED FOR CRITERIA 1-98----Developer A 07.08.2019

-----------------------------------------------------------------------------------------------------------------------------------------------------*/

/*TREATMENT PLAN*/

		--BLOOD CULTURE

		IF OBJECT_ID(N'tempdb..#BC') IS NOT NULL DROP TABLE #BC

		SELECT DISTINCT B.PAT_ENC_CSN_ID

			,OP.ORDER_INST AS BLOOD_CULTURE_ORDER_TIME

		INTO #BC

		FROM #Base_Pop B --ONLY LOOKIN FOR BLOOD CULTURE FOR THOSE PATIENTS WHO HAD A POSITIVE SCORE

		JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON OP.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

				AND OP.PROC_ID IN (SELECT * FROM #BloodCultures)

				AND OP.INSTANTIATED_TIME IS NOT NULL AND OP.FUTURE_OR_STAND IS NULL

		CREATE INDEX IDX_BC ON #BC (PAT_ENC_CSN_ID) 



		--ANTIBIOTICS

		IF OBJECT_ID(N'tempdb..#ABX') IS NOT NULL DROP TABLE #ABX

		SELECT DISTINCT

			OM.PAT_ENC_CSN_ID

			, BC.BLOOD_CULTURE_ORDER_TIME

			, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

		INTO #ABX

		FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN #BC BC ON BC.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID--SINCE ABX SHOULD ALWAYS HAVE A BLOOD CULTURE WITH IN 72 HOURS

		INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID --AND CM.THERA_CLASS_C = 11 --Antibiotics

		INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

		WHERE MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

			AND OM.MED_ROUTE_C=11--IV ONLY

			AND MAI.MAR_ACTION_C IN (SELECT * FROM #MARActions)

			AND OM.MEDICATION_ID IN 

				(

					SELECT medlist.MEDICATION_ID

					FROM (

						SELECT erx.MEDICATION_ID

							, erx.NAME

							, cntl.AGENT

							, cntl.AGENT_GROUP

							, cntl.DOT_MONITORING

							, gen.TITLE

							, ROW_NUMBER() over(partition by erx.MEDICATION_ID order by cntl.DOT_MONITORING,cntl.AGENT asc) as AGENT_ORDER

						FROM EMRDB.dbo.MEDICATIONS erx

						OUTER APPLY ( --Get the main medication's simple generic if its a mixture

							SELECT TOP 1 mix.DRUG_ID

								, comp.SIMPLE_GENERIC_C 

							FROM EMRDB.dbo.MED_MIX_COMPONENTS mix

							INNER JOIN EMRDB.dbo.MEDICATIONS comp on mix.DRUG_ID = comp.MEDICATION_ID

							WHERE mix.TYPE_C = 3		--3 - Medications 

							AND mix.MEDICATION_ID = erx.MEDICATION_ID

							ORDER BY mix.LINE

						) mixture

						INNER JOIN EMRDB.dbo.REF_GENERIC_MED gen on gen.SIMPLE_GENERIC_C=coalesce(erx.SIMPLE_GENERIC_C,mixture.SIMPLE_GENERIC_C)

						INNER JOIN #ERXAntimicrobial cntl ON cntl.CODE = gen.SIMPLE_GENERIC_C

						--reportingDB.reports.CONFIG_VALUE_SET cntl on cntl.VALUE_SET_ID = 3016 and cntl.CODE = gen.SIMPLE_GENERIC_C -- and cntl.VALUE_SET_ABBR='Antibacterial'

					) medlist

					WHERE medlist.AGENT_ORDER = 1

				)

			AND (ABS(DATEDIFF(MI,MAI.TAKEN_TIME,BC.BLOOD_CULTURE_ORDER_TIME))/60.00) <= 72.0

		UNION

		SELECT DISTINCT OM.PAT_ENC_CSN_ID

			, BC.BLOOD_CULTURE_ORDER_TIME

			, MAI.TAKEN_TIME AS ABX_ADMIN_TIME

		FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN #BC BC ON BC.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID--SINCE ABX SHOULD ALWAYS HAVE A BLOOD CULTURE WITH IN 72 HOURS

		INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID AND CM.THERA_CLASS_C = 11 --Antibiotics

		INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

		WHERE MAI.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND OM.MED_ROUTE_C = 11--IV ONLY

		AND MAI.MAR_ACTION_C IN (SELECT * FROM #MARActions)

		AND (ABS(DATEDIFF(MI,MAI.TAKEN_TIME,BC.BLOOD_CULTURE_ORDER_TIME))/60.00) <= 72.0

		CREATE INDEX IDX_abx ON #ABX (PAT_ENC_CSN_ID) 



		IF OBJECT_ID(N'tempdb..#BOL1') IS NOT NULL DROP TABLE #BOL1

		SELECT DISTINCT

			OM.PAT_ENC_CSN_ID

			, MAI.TAKEN_TIME AS FIRST_BOLUS_TIME

		INTO #BOL1

		FROM #Base_Pop C

		INNER JOIN #ABX ABX ON ABX.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID--SINCE A BOLUS IS ALWAYS NEEDED WITH ANTIBIOTIC

		INNER JOIN #BC BC ON BC.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID--SINCE A BOLUS IS ALWAYS NEEDED WITH ANTIBIOTIC AND A BLOOD CULTURE

		JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

		JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

		JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

		WHERE MAI.TAKEN_TIME IS NOT NULL --ADMINISTERED BOLUS ONLY

		AND (

			OM.MEDICATION_ID IN (SELECT * FROM #BolusMeds)

			OR (OM.MEDICATION_ID IN (SELECT * FROM #BolusMedsOnce) AND OM.HV_DISCR_FREQ_ID = '300902')

		) -- FREQUENCY = ONCE 

		AND MAI.MAR_ACTION_C IN (SELECT * FROM #MARActions)

		AND CONVERT(NUMERIC, MAI.SIG ) > 95.0--AT LEAST 95 ML

		AND (ABS(DATEDIFF(MI,MAI.TAKEN_TIME,BC.BLOOD_CULTURE_ORDER_TIME))/60.00) <= 72.0--BOLUS WITHIN 72 HOURS OF BLOODCULTURE

		AND (ABS(DATEDIFF(MI,MAI.TAKEN_TIME,ABX.ABX_ADMIN_TIME))/60.00) <= 6.0--BOLUS WITHIN 6 HOURS OF ABX

		--CREATE INDEX IDX_Bol1 ON #BOL1 (PAT_ENC_CSN_ID) 



		--2 BOLUSES

		IF OBJECT_ID(N'tempdb..#BOL2') IS NOT NULL DROP TABLE #BOL2

		SELECT PAT_ENC_CSN_ID

			, FIRST_BOLUS_TIME

			, LEAD(FIRST_BOLUS_TIME,1,NULL) OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY FIRST_BOLUS_TIME) AS SECOND_BOLUS_TIME

			, ABS(DATEDIFF(MI,FIRST_BOLUS_TIME, LEAD(FIRST_BOLUS_TIME,1,NULL) OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY FIRST_BOLUS_TIME)))/60.0 AS BOL12_TIME

		INTO #BOL2 

		FROM #BOL1

		CREATE INDEX IDX_bol2 ON #BOL2 (PAT_ENC_CSN_ID) 

		

		--PRESSORS

		IF OBJECT_ID(N'tempdb..#PRESS') IS NOT NULL DROP TABLE #PRESS

		SELECT DISTINCT

			BC.PAT_ENC_CSN_ID

			, BOL.FIRST_BOLUS_TIME

			, MAI.TAKEN_TIME AS PRESSOR_START_TIME

			, ABS(DATEDIFF(MI,FIRST_BOLUS_TIME,MAI.TAKEN_TIME))/60.00 AS PRESS_BOL_TIME 

			, ABS(DATEDIFF(MI,BC.BLOOD_CULTURE_ORDER_TIME,MAI.TAKEN_TIME))/60.00 AS PRESS_BC_TIME

		INTO #PRESS

		FROM #Base_Pop SC

		INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = SC.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

		INNER JOIN #MedGroupersERX erx ON erx.ERX_ID = cm.MEDICATION_ID

		--INNER JOIN EMRDB.dbo.GROUPER_MED_RECORDS GMR ON GMR.EXP_MEDS_LIST_ID = CM.MEDICATION_ID 	AND

		--	GMR.GROUPER_ID IN (SELECT * FROM #MedGroupers)

		INNER JOIN #ABX ABX ON ABX.PAT_ENC_CSN_ID = OM.PAT_ENC_CSN_ID

		INNER JOIN #BC BC ON BC.PAT_ENC_CSN_ID = OM.PAT_ENC_CSN_ID

		INNER JOIN #BOL2 BOL ON BOL.PAT_ENC_CSN_ID = OM.PAT_ENC_CSN_ID

		INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID AND MAI.ROUTE_C = 11  --INTRAVENOUS

			AND (ABS(DATEDIFF(MI,MAI.TAKEN_TIME,BC.BLOOD_CULTURE_ORDER_TIME))/60.00) <= 72.0 --PRESSOR BC TIME

			AND (ABS(DATEDIFF(MI,MAI.TAKEN_TIME,BOL.FIRST_BOLUS_TIME))/60.00) <= 6.0--PRESSOR BOLUS TIME

			AND (ABS(DATEDIFF(MI,MAI.TAKEN_TIME,ABX.ABX_ADMIN_TIME))/60.00) <= 6.0--PRESSOR ABX TIME

		CREATE INDEX IDX_Press ON #PRESS (PAT_ENC_CSN_ID) 

/*END OF TREATMENT PLAN*/





/*CRITERIA 1*/

--GET ALL THE POSITIVE SEPSIS SCORES

IF OBJECT_ID(N'tempdb..#C1') IS NOT NULL DROP TABLE #C1

	SELECT DISTINCT A.PAT_ENC_CSN_ID, '1' AS CRITERIA

	INTO #C1

	FROM #Scores A

	INNER JOIN #ABX B ON A.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID 

		AND (ABS(DATEDIFF(MI,A.SCORE_TIME,B.ABX_ADMIN_TIME))/60.00) <= 24.0

	INNER JOIN #PRESS PRESS ON PRESS.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID 

		AND (ABS(DATEDIFF(MI,PRESS.PRESSOR_START_TIME,A.SCORE_TIME))/60.00) <= 24.0--PRESSOR SCORE TIME

UNION

	SELECT DISTINCT A.PAT_ENC_CSN_ID, '1' AS CRITERIA 

	FROM #Scores A

	INNER JOIN #BC B ON A.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	INNER JOIN #ABX C ON A.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

		AND (ABS(DATEDIFF(MI,A.SCORE_TIME,C.ABX_ADMIN_TIME))/60.00) <= 24.0

	INNER JOIN #BOL2 BOL ON BOL.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID 

		AND BOL.SECOND_BOLUS_TIME IS NOT NULL 

		AND (BOL.FIRST_BOLUS_TIME <> BOL.SECOND_BOLUS_TIME)

		AND (ABS(DATEDIFF(MI,BOL.FIRST_BOLUS_TIME,A.SCORE_TIME))/60.00) <= 24.0

		AND (ABS(DATEDIFF(MI,BOL.SECOND_BOLUS_TIME,A.SCORE_TIME))/60.00) <= 24.0

		AND BOL.BOL12_TIME <= 6.0

CREATE INDEX IDX_C1 ON #C1 (PAT_ENC_CSN_ID) 



/*END OF CRITERIA 1*/



/*CRITERIA 3 ORDER SET*/

--GET ALL THE POSITIVE SEPSIS SCORES

IF OBJECT_ID(N'tempdb..#OSET') IS NOT NULL DROP TABLE #OSET

SELECT b.PAT_ENC_CSN_ID

	, om.ORDER_ID

	, om.ORDER_DTTM AS OSET_TIME

	, op.ORDER_STATUS_C

	, ROW_NUMBER() OVER(PARTITION BY b.PAT_ENC_CSN_ID ORDER BY om.ORDER_DTTM ASC) AS SS_LINE

	, om.PRL_ORDERSET_ID

INTO #OSET 

FROM #Base_Pop b

INNER JOIN EMRDB.dbo.PROCEDURE_ORDERS op ON op.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

JOIN EMRDB.dbo.ORDER_TRACKING_METRICS om ON om.ORDER_ID = op.ORDER_PROC_ID --AND OP.ORDER_STATUS_C<>4-- AND OP.INSTANTIATED_TIME IS NOT NULL AND OP.FUTURE_OR_STAND IS NULL-- PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

WHERE om.PRL_ORDERSET_ID IN (SELECT * FROM #Ordersets)

--CREATE INDEX IDX_Oset ON #OSET (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#C3') IS NOT NULL DROP TABLE #C3

	SELECT DISTINCT a.PAT_ENC_CSN_ID, '3' AS CRITERIA

	INTO #C3

	FROM #OSET a

	INNER JOIN #BC bc ON a.PAT_ENC_CSN_ID = bc.PAT_ENC_CSN_ID

	INNER JOIN #ABX b ON a.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID 

		AND (ABS(DATEDIFF(MI,a.OSET_TIME,b.ABX_ADMIN_TIME))/60.00) <= 24.0

	INNER JOIN #PRESS press ON press.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID 

		AND (ABS(DATEDIFF(MI,press.PRESSOR_START_TIME,a.OSET_TIME))/60.00) <= 24.0--PRESSOR SCORE TIME

UNION

	SELECT DISTINCT a.PAT_ENC_CSN_ID, '3' AS CRITERIA 

	FROM #OSET a

	INNER JOIN #BC b ON a.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	INNER JOIN #ABX c ON a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID  

		AND (ABS(DATEDIFF(MI,a.OSET_TIME,c.ABX_ADMIN_TIME))/60.00) <= 24.0

	INNER JOIN #BOL2 bol ON bol.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID 

		AND bol.SECOND_BOLUS_TIME IS NOT NULL 

		AND (bol.FIRST_BOLUS_TIME <> bol.SECOND_BOLUS_TIME)

		AND (ABS(DATEDIFF(MI,bol.FIRST_BOLUS_TIME,a.OSET_TIME))/60.00) <= 24.0

		AND (ABS(DATEDIFF(MI,bol.SECOND_BOLUS_TIME,a.OSET_TIME))/60.00) <= 24.0

		AND (ABS(DATEDIFF(MI,bol.FIRST_BOLUS_TIME,c.ABX_ADMIN_TIME))/60.00) <= 24.0

		AND BOL.BOL12_TIME <= 6.0

CREATE INDEX IDX_C3 ON #C3 (PAT_ENC_CSN_ID) 

/*END OF CRITERIA 3*/



/*CRITERIA 4*/

	IF OBJECT_ID(N'tempdb..#ICU') IS NOT NULL DROP TABLE #ICU

	SELECT vpalh.PAT_ENC_CSN AS PAT_ENC_CSN_ID

		, vpalh.IN_DTTM

		, CASE WHEN vpalh.OUT_DTTM > DATEADD(YY,10,vpalh.IN_DTTM) THEN @EndDate ELSE vpalh.OUT_DTTM END AS OUT_DTTM -- IN CASE THERE ARE ANY PATIENTS STILL IN THE ICU THE OUT_DTTM IS DEFAULTED TO 2200-12-31 00:00:00.000

		, DATEDIFF(MI,vpalh.IN_DTTM, vpalh.OUT_DTTM) AS MYDIF

	INTO #ICU

	FROM #Base_Pop b

	INNER JOIN EMRDB.dbo.V_PATIENT_LOCATION_HISTORY vpalh ON vpalh.PAT_ENC_CSN = b.PAT_ENC_CSN_ID

	WHERE vpalh.EVENT_TYPE_C in (1, 3) --ADMISSION AND TRANSFER-IN

	AND vpalh.ADT_DEPARTMENT_ID IN (20101116			--EAST ICU

		, 20101124			--EAST CARDIAC ICU

		, 20101126			--EAST NEURO ICU

		, 20101127			--EAST PEDIATRIC ICU

		, 20101128			--EAST SURGICAL ICU

		, 20101165			--EAST REMOTE ICU

		, 20120106			--WEST CARDIAC ICU

		, 20120121			--WEST ICU

		, 200108001			--MAIN 2 PAVILION PICU

		, 200108070			--MAIN 3 CICU

		, 200108115			--MAIN 2 PICU NEURO

		, 200108147			--MAIN PHARMACY ICU

	)	

	--CREATE INDEX IDX_ICU ON #ICU (PAT_ENC_CSN_ID) 

	

	IF OBJECT_ID(N'tempdb..#C4') IS NOT NULL DROP TABLE #C4

		SELECT DISTINCT a.PAT_ENC_CSN_ID, '4' AS CRITERIA

		INTO #C4

		FROM #ICU a

		INNER JOIN #BC bc ON a.PAT_ENC_CSN_ID = bc.PAT_ENC_CSN_ID

		INNER JOIN #ABX b ON a.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

			AND 

			(

				(	b.ABX_ADMIN_TIME < a.IN_DTTM 

					AND ((ABS(DATEDIFF(MI,b.ABX_ADMIN_TIME,a.IN_DTTM))/60.00) <= 24.0)--LESS THAN 24 HOURS BEFORE THE PICU IN TIME

				)

				OR

				(CONVERT(DATE,b.ABX_ADMIN_TIME) BETWEEN a.IN_DTTM AND a.OUT_DTTM)--OR BETWEEN PICU TIMES WITHIN THE MEASUREMENT PERIOD

			)

		INNER JOIN #PRESS PRESS ON press.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID

			AND --PRESSOR AND ICU TIMES

			(

				(	press.PRESSOR_START_TIME < a.IN_DTTM 

					AND ((ABS(DATEDIFF(MI,press.PRESSOR_START_TIME,a.IN_DTTM))/60.00) <= 24.0) --LESS THAN 24 HOURS BEFORE THE PICU IN TIME

				)

				OR

				(CONVERT(DATE,press.PRESSOR_START_TIME) BETWEEN a.IN_DTTM AND a.OUT_DTTM)--OR BETWEEN PICU TIMES WITHIN THE MEASUREMENT PERIOD

			)

	UNION

		SELECT DISTINCT a.PAT_ENC_CSN_ID,'4' AS CRITERIA 

		FROM #ICU a

		INNER JOIN #BC b ON a.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

		INNER JOIN #ABX c ON a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

			AND 

			(

				(	c.ABX_ADMIN_TIME < a.IN_DTTM 

					AND ((ABS(DATEDIFF(MI,c.ABX_ADMIN_TIME,a.IN_DTTM))/60.00) <= 24.0)--LESS THAN 24 HOURS BEFORE THE PICU IN TIME

				)

				OR

				(CONVERT(DATE,c.ABX_ADMIN_TIME) BETWEEN a.IN_DTTM AND a.OUT_DTTM)--OR BETWEEN PICU TIMES WITHIN THE MEASUREMENT PERIOD

			)

		INNER JOIN #BOL2 bol ON bol.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID 

			AND bol.SECOND_BOLUS_TIME IS NOT NULL 

			AND (bol.FIRST_BOLUS_TIME <> bol.SECOND_BOLUS_TIME)

			AND 

			(

				(	bol.FIRST_BOLUS_TIME < a.IN_DTTM 

					AND ((ABS(DATEDIFF(MI,bol.FIRST_BOLUS_TIME,a.IN_DTTM))/60.00) <= 24.0) --LESS THAN 24 HOURS BEFORE THE PICU IN TIME

				)

				OR

				(CONVERT(DATE,bol.FIRST_BOLUS_TIME) BETWEEN a.IN_DTTM AND a.OUT_DTTM)--OR BETWEEN PICU TIMES WITHIN THE MEASUREMENT PERIOD

			)

			AND bol.BOL12_TIME <= 6.0 

	CREATE INDEX IDX_C4 ON #C4 (PAT_ENC_CSN_ID) 

/*END OF CRITERIA 4*/



/*CRITERIA 95 LACTIC ACID*/

IF OBJECT_ID(N'tempdb..#LACID') IS NOT NULL DROP TABLE #LACID

SELECT DISTINCT bp.PAT_ENC_CSN_ID

	, op.ORDER_TIME AS LACID_TIME

INTO #LACID

FROM #Base_Pop bp

JOIN EMRDB.dbo.PROCEDURE_ORDERS op ON bp.PAT_ENC_CSN_ID = op.PAT_ENC_CSN_ID

	AND op.INSTANTIATED_TIME IS NOT NULL AND op.FUTURE_OR_STAND IS NULL

JOIN EMRDB.dbo.LAB_ORDER_RESULTS res ON op.ORDER_PROC_ID = res.ORDER_PROC_ID

INNER JOIN #LacticAcidLRRByName cc ON cc.LRR_ID = res.COMPONENT_ID

CREATE INDEX IDX_lacid ON #LACID (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#C95') IS NOT NULL DROP TABLE #C95

	SELECT DISTINCT a.PAT_ENC_CSN_ID, '95' AS CRITERIA

	INTO #C95

	FROM #LACID a

	INNER JOIN #BC bc ON a.PAT_ENC_CSN_ID = bc.PAT_ENC_CSN_ID

	INNER JOIN #ABX b ON a.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID 

		AND (ABS(DATEDIFF(MI,a.LACID_TIME,b.ABX_ADMIN_TIME))/60.00) <= 24.0

	INNER JOIN #PRESS press ON a.PAT_ENC_CSN_ID = press.PAT_ENC_CSN_ID

		AND (ABS(DATEDIFF(MI,press.PRESSOR_START_TIME,a.LACID_TIME))/60.00) <= 24.0--PRESSOR SCORE TIME

UNION

	SELECT DISTINCT a.PAT_ENC_CSN_ID, '95' AS CRITERIA 

	FROM #LACID a

	INNER JOIN #BC b ON a.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	INNER JOIN #ABX c ON a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID  

		AND (ABS(DATEDIFF(MI,a.LACID_TIME,c.ABX_ADMIN_TIME))/60.00) <= 24.0

	INNER JOIN #BOL2 bol ON bol.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID 

		AND bol.SECOND_BOLUS_TIME IS NOT NULL 

		AND (bol.FIRST_BOLUS_TIME <> bol.SECOND_BOLUS_TIME)

		AND (ABS(DATEDIFF(MI,bol.FIRST_BOLUS_TIME,a.LACID_TIME))/60.00) <= 24.0

		AND (ABS(DATEDIFF(MI,bol.SECOND_BOLUS_TIME,a.LACID_TIME))/60.00) <= 24.0

		AND (ABS(DATEDIFF(MI,bol.FIRST_BOLUS_TIME,c.ABX_ADMIN_TIME))/60.00) <= 24.0

		AND bol.BOL12_TIME <= 6.0 

CREATE INDEX IDX_C95 ON #C95 (PAT_ENC_CSN_ID) 



/*END OF CRITERIA 95 LACTIC ACID*/



/*CRITERIA 6 PRESSORS*/

	IF OBJECT_ID(N'tempdb..#PRESS61') IS NOT NULL DROP TABLE #PRESS61

	SELECT DISTINCT b.PAT_ENC_CSN_ID

		, mai.TAKEN_TIME AS PRESS_TIME

	INTO #PRESS61

	FROM #Base_Pop b

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS om ON om.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.MEDICATIONS cm ON cm.MEDICATION_ID = om.MEDICATION_ID

	INNER JOIN EMRDB.dbo.GROUPER_MED_RECORDS gmr ON gmr.EXP_MEDS_LIST_ID = cm.MEDICATION_ID

		AND gmr.GROUPER_ID IN (SELECT * FROM #MedGroupers)

	INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS mai ON mai.ORDER_MED_ID = om.ORDER_MED_ID AND mai.ROUTE_C = 11  --INTRAVENOUS	

	--CREATE INDEX IDX_PRESS61 ON #PRESS61 (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#C6') IS NOT NULL DROP TABLE #C6

	SELECT DISTINCT press.PAT_ENC_CSN_ID

		,'6' AS CRITERIA

	INTO #C6

	FROM #PRESS61 press

	INNER JOIN #ABX abx ON abx.PAT_ENC_CSN_ID = press.PAT_ENC_CSN_ID 

		AND press.PRESS_TIME < abx.ABX_ADMIN_TIME 

		AND (ABS(DATEDIFF(MI,abx.ABX_ADMIN_TIME,press.PRESS_TIME))/60.00) <= 24.0

	INNER JOIN #BOL2 bol ON bol.PAT_ENC_CSN_ID = abx.PAT_ENC_CSN_ID 

		AND bol.FIRST_BOLUS_TIME < press.PRESS_TIME 

		AND (ABS(DATEDIFF(MI,bol.FIRST_BOLUS_TIME,press.PRESS_TIME))/60.00) <= 24.0

	INNER JOIN #PRESS press6 ON press6.PAT_ENC_CSN_ID = press.PAT_ENC_CSN_ID 

		AND press6.PRESSOR_START_TIME < press.PRESS_TIME 

		AND (ABS(DATEDIFF(MI,press6.PRESSOR_START_TIME,press.PRESS_TIME))/60.00) <= 24.0

UNION

	SELECT DISTINCT press.PAT_ENC_CSN_ID,'6' AS CRITERIA

	FROM #PRESS61 press

	INNER JOIN #ABX abx ON abx.PAT_ENC_CSN_ID = press.PAT_ENC_CSN_ID 

		AND press.PRESS_TIME < abx.ABX_ADMIN_TIME 

		AND (ABS(DATEDIFF(MI,abx.ABX_ADMIN_TIME,press.PRESS_TIME))/60.00) <= 24.0

	INNER JOIN #BOL2 bol ON bol.PAT_ENC_CSN_ID = abx.PAT_ENC_CSN_ID 

		AND bol.SECOND_BOLUS_TIME IS NOT NULL 

		AND (bol.FIRST_BOLUS_TIME <> bol.SECOND_BOLUS_TIME)

		AND bol.FIRST_BOLUS_TIME < press.PRESS_TIME

		AND (ABS(DATEDIFF(MI,bol.FIRST_BOLUS_TIME,press.PRESS_TIME))/60.00) <= 24.0		

		AND (ABS(DATEDIFF(MI,bol.SECOND_BOLUS_TIME,press.PRESS_TIME))/60.00) <= 24.0

		AND bol.BOL12_TIME <= 6.0

CREATE INDEX IDX_C6 ON #C6 (PAT_ENC_CSN_ID) 

/*END OF CRITERIA 6 PRESSORS*/



/*CRITERIA 7 SEPTIC SHOCK DIAGNOSIS*/

IF OBJECT_ID(N'tempdb..#C7') IS NOT NULL DROP TABLE #C7;

	SELECT bp.PAT_ENC_CSN_ID, '7' AS CRITERIA	

	INTO #C7

	FROM #Base_Pop bp

	JOIN EMRDB.dbo.HOSPITAL_ACCT_DIAGNOSES dx ON dx.HSP_ACCOUNT_ID = bp.HSP_ACCOUNT_ID

	JOIN EMRDB.dbo.DIAGNOSES edg ON edg.DX_ID = dx.DX_ID 

		AND COALESCE(edg.REF_BILL_CODE, edg.CURRENT_ICD10_LIST) IN (SELECT * FROM #DXSepticShock)

UNION

	SELECT bp.PAT_ENC_CSN_ID, '7' AS CRITERIA

	FROM  #Base_Pop bp

	JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES dx ON dx.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.DIAGNOSES edg ON edg.DX_ID = dx.DX_ID 

		AND COALESCE(edg.REF_BILL_CODE, edg.CURRENT_ICD10_LIST) IN (SELECT * FROM #DXSepticShock)

CREATE INDEX IDX_C7 ON #C7 (PAT_ENC_CSN_ID) 

/*END OF CRITERIA 7*/



/*CRITERIA 98 SEPSIS DIAGNOSIS CODES*/

IF OBJECT_ID(N'tempdb..#SDX') IS NOT NULL DROP TABLE #SDX

	SELECT bp.PAT_ENC_CSN_ID

	INTO #SDX

	FROM  #Base_Pop bp

	JOIN EMRDB.dbo.HOSPITAL_ACCT_DIAGNOSES dx ON dx.HSP_ACCOUNT_ID = bp.HSP_ACCOUNT_ID

	JOIN EMRDB.dbo.DIAGNOSES edg ON edg.DX_ID = dx.DX_ID 

		AND COALESCE(edg.REF_BILL_CODE, edg.CURRENT_ICD10_LIST) IN (SELECT * FROM #DXSepsis) 

UNION

	SELECT bp.PAT_ENC_CSN_ID

	FROM #Base_Pop bp

	JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES dx ON dx.PAT_ENC_CSN_ID = bp.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.DIAGNOSES edg ON edg.DX_ID = dx.DX_ID 

		AND COALESCE(edg.REF_BILL_CODE, edg.CURRENT_ICD10_LIST) IN (SELECT * FROM #DXSepsis)

--CREATE INDEX IDX_SDX ON #SDX (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#C98') IS NOT NULL DROP TABLE #C98

	SELECT DISTINCT a.PAT_ENC_CSN_ID, '98' AS CRITERIA

	INTO #C98

	FROM #SDX a

	INNER JOIN #ABX b ON a.PAT_ENC_CSN_ID = b.PAT_ENC_CSN_ID

	INNER JOIN #PRESS press ON press.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID		

UNION

	SELECT DISTINCT a.PAT_ENC_CSN_ID, '98' AS CRITERIA 

	FROM #SDX a

	INNER JOIN #ABX c ON a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID 

	INNER JOIN #BOL2 bol ON bol.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID 

		AND bol.SECOND_BOLUS_TIME IS NOT NULL 

		AND (bol.FIRST_BOLUS_TIME <> bol.SECOND_BOLUS_TIME)

		AND bol.BOL12_TIME <= 6.0

CREATE INDEX IDX_C98 ON #C98 (PAT_ENC_CSN_ID) 

-----------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

/* PUTTING ALL THE CRITERIA'S TOGETHER */

IF OBJECT_ID(N'tempdb..#ENC_COND') IS NOT NULL DROP TABLE #ENC_COND;

SELECT * 

INTO

	#ENC_COND	

FROM 

	#C1 

UNION

	SELECT * FROM #C3

UNION

	SELECT * FROM #C4

UNION

	SELECT * FROM #C95

UNION

	SELECT * FROM #C6

UNION

	SELECT * FROM #C7

UNION

	SELECT * FROM #C98

--CREATE INDEX IDX_EncCond ON #ENC_COND (PAT_ENC_CSN_ID) 



--Developer A ADDED #C7_R65_ONLY ON 08.01.2019... TO ADDRESS THE ISSUE WHERE THERE IS ONLY R65/CRITERIA 7 - IN THIS CASE THE FTZ WILL BE THE EARLIEST OF SCREENTIME OR OSET TIME OR ABX TIME ETC...

IF OBJECT_ID(N'tempdb..#C7_R65_ONLY') IS NOT NULL DROP TABLE #C7_R65_ONLY;

SELECT

	DISTINCT PAT_ENC_CSN_ID 

INTO #C7_R65_ONLY

FROM #C7 A

WHERE A.PAT_ENC_CSN_ID NOT IN 

(

	SELECT PAT_ENC_CSN_ID FROM 	#C1 

	UNION

	SELECT PAT_ENC_CSN_ID FROM  #C3

	UNION

	SELECT PAT_ENC_CSN_ID FROM  #C4

	UNION

	SELECT PAT_ENC_CSN_ID FROM  #C95

	UNION

	SELECT PAT_ENC_CSN_ID FROM  #C6

	UNION

	SELECT PAT_ENC_CSN_ID FROM  #C98

)

--CREATE INDEX IDX_C76r65 ON #C7_R65_ONLY (PAT_ENC_CSN_ID) 



/* CREATING A TABLE TO SEE WHICH ENCOUNTER SATISFIEST WHICH CRITERIA*/

IF OBJECT_ID(N'tempdb..#ENC_CONDL') IS NOT NULL DROP TABLE #ENC_CONDL;

SELECT *

	, ROW_NUMBER() OVER(PARTITION BY PAT_ENC_CSN_ID ORDER BY CRITERIA ASC) LINE 

INTO #ENC_CONDL

FROM #ENC_COND

--CREATE INDEX IDX_EncCondl ON #ENC_CONDL (PAT_ENC_CSN_ID) 



/* CREATING A LIST OF ENCOUNTERS AND THE INCLUSION CRITERIA # THAT THE ENCOUNTER SATISFIES*/

IF OBJECT_ID(N'tempdb..#CLIST') IS NOT NULL DROP TABLE #CLIST;

SELECT DISTINCT PAT_ENC_CSN_ID

	, INCLUSION_CRITERIA = STUFF((SELECT ', ' + CRITERIA

								FROM #ENC_CONDL

								WHERE PAT_ENC_CSN_ID = x.PAT_ENC_CSN_ID

								ORDER BY LINE

								FOR XML PATH(''), TYPE

								).value('.[1]', 'nvarchar(max)'), 1, 2, ''

								)

INTO #CLIST

FROM #ENC_COND x

--CREATE INDEX IDX_CList ON #CLIST (PAT_ENC_CSN_ID) 

--END



--Delete all records from BASE_POP where they didn't meet criteria

DELETE FROM #Base_Pop where PAT_ENC_CSN_ID NOT IN (SELECT PAT_ENC_CSN_ID FROM #CLIST)

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*FINAL BASE POPULATION */

-- WE NEED TO CHECK IF THE PATIENTS WERE ALREADY REPORTED IN PRIOR MONTHS. IF THEY WERE REPORTED PREVIOUSLY THEN WE SHOULDN'T REPORT THEM AGAIN

IF OBJECT_ID(N'tempdb..#COHORT') IS NOT NULL DROP TABLE #COHORT;

SELECT  b.PAT_ENC_CSN_ID

	, c.INCLUSION_CRITERIA 

	, b.INPATIENT_DATA_ID

	, b.AGE_MONTHS

	, b.AGE_YEARS

INTO #COHORT 

FROM #CLIST c   

LEFT JOIN #Base_Pop b ON b.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING] p ON p.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID AND p.Reviewed = 1

WHERE p.PAT_ENC_CSN_ID IS NULL

CREATE INDEX IDX_cohort ON #COHORT (PAT_ENC_CSN_ID) 

-----------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

--/*DISPLAY COLUMNS*/

-------------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

/*Screen Time

Variable ID – V06

Time of initial screening process to identify possible severe sepsis in PATIENTS, where screen was positive. Note:

The initial screening process may consist of an electronic CLINICAL_ALERTS, a checklist, PEWS scores (absolute value and/or change), 

bedside nursing screens, or other identification tools. The initial screening process may use paper-based tools or electronic tools.

For more details on initial screening processes, refer to the document “Sepsis Bundles, Bundle 2: Recognition”.

For MAIN purposes this should be a sepsis score of 95 or greater in the ED and an Organ dysfunction score of 3 or greater for in house.

*/



IF OBJECT_ID(N'tempdb..#ScreenTime') IS NOT NULL DROP TABLE #ScreenTime;

SELECT a.PAT_ENC_CSN_ID

	--, COALESCE(MIN(#SSTP.SCORE_TIME),'1900-01-02 00:00:00') AS ScreenTime_V06--Developer A COMMENTED ON 07.16.2019

	, MIN(sstp.SCORE_TIME) AS ScreenTime_V06

	, MIN(sstp.SCORE_TIME) AS ScreenTime	

INTO #ScreenTime

FROM #COHORT a

	--LEFT JOIN #Scores  ON #Scores.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID --Developer A CHANGED THIS ON 07.11.2019

LEFT JOIN #SSTP sstp ON sstp.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID	

GROUP BY a.PAT_ENC_CSN_ID

CREATE INDEX IDX_ScreenTime ON #ScreenTime (PAT_ENC_CSN_ID) 

-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* Funtional Time Zero */

/*FUNCTIONAL TIME ZERO IS CALCULATED AS FOLLOWS:

THE FIRST POSITIVE SEPSIS SCORE IN ED	

THE FIRST POSITIVE ORGAN DYSFUNCTION SCORE ON FLOOR

If no positict Sepsis/OD scores then First OrderSet time

If no Orderset time then the closest Abx time to the satistfied criteria (if more than one criteria satisfied then the first abx time among them)

If not Abx time then the closest Bolus time to the satisfied criteria (if more than one criteria satisfied then the first bolus time among them)

*/



/* Finding Closest ABX time to Score time and  orderset time*/

--C1 - +VE SCORE 

IF OBJECT_ID(N'tempdb..#C1ABXS') IS NOT NULL DROP TABLE #C1ABXS;

SELECT s.pat_enc_csn_id

	, s.screentime

	, abx.ABX_ADMIN_TIME

	, ABS(DATEDIFF(MI, s.SCREENTIME, abx.ABX_ADMIN_TIME)) AS DIFF

INTO #C1ABXS

FROM #C1 c1

INNER JOIN #ScreenTime s ON s.PAT_ENC_CSN_ID = c1.PAT_ENC_CSN_ID

INNER JOIN #TreatPlanABX abx ON abx.PAT_ENC_CSN_ID = s.PAT_ENC_CSN_ID 

WHERE abx.ABX_ADMIN_TIME BETWEEN DATEADD(HH, -6, s.ScreenTime) AND DATEADD(HH, 24, s.ScreenTime)

--CREATE INDEX IDX_C1abxs ON #C1ABXS (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#C1ABX1') IS NOT NULL DROP TABLE #C1ABX1;

SELECT c1abxs.*

INTO #C1ABX1	

FROM #C1ABXS c1abxs

WHERE DIFF = (SELECT MIN(a.DIFF)

				FROM #C1ABXS a

				WHERE a.PAT_ENC_CSN_ID = c1abxs.PAT_ENC_CSN_ID

	)

--CREATE INDEX IDX_C1abx1 ON #C1ABX1 (PAT_ENC_CSN_ID) 



--C3 - ORDERSET TIME		

IF OBJECT_ID(N'tempdb..#C3ABXS') IS NOT NULL DROP TABLE #C3ABXS;

SELECT  ostp.PAT_ENC_CSN_ID 

	, ostp.TREATMENT_ABX_ADMIN_TIME AS ABX_ADMIN_TIME

	, ABS(DATEDIFF(MI, ostp.ORDER_DTTM, ostp.TREATMENT_ABX_ADMIN_TIME)) AS DIFF	

INTO #C3ABXS	

FROM #OSTP ostp

WHERE ostp.TREATMENT_ABX_ADMIN_TIME BETWEEN DATEADD(HH, -6, ostp.ORDER_DTTM) AND DATEADD(HH, 24, ostp.ORDER_DTTM)

--CREATE INDEX IDX_c3abxs ON #C3ABXS (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#C3ABX1') IS NOT NULL DROP TABLE #C3ABX1;

SELECT c3abxs.*

INTO #C3ABX1	

FROM #C3ABXS c3abxs

WHERE DIFF = (SELECT MIN(a.DIFF)

				FROM #C3ABXS a

				WHERE a.PAT_ENC_CSN_ID = c3abxs.PAT_ENC_CSN_ID

	)

--CREATE INDEX IDX_C3abx1 ON #C3ABX1 (PAT_ENC_CSN_ID) 



-- EARLIEST ABX TIME (PART OF TREATMENT) WHERE THE ECOUNTERS DONT HAVE +VE SCORE AND ORDERSET PLACE.

--FINDING LIST OF ENCOUNTERS WHICH ARE NOT A PART OF CRITERIA 1 AND CRITERIA 3



IF OBJECT_ID(N'tempdb..#ENC') IS NOT NULL DROP TABLE #ENC;

SELECT DISTINCT c.PAT_ENC_CSN_ID

INTO #ENC

FROM #COHORT c

LEFT JOIN #C1 c1 ON c1.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN #C3 c3 ON c3.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

WHERE c1.PAT_ENC_CSN_ID IS NULL

AND c3.PAT_ENC_CSN_ID IS NULL

--CREATE INDEX IDX_enc ON #ENC (PAT_ENC_CSN_ID) 



--FINDING THE EARLIEST ABX (PART OF TREATMENT PLAN) FOR THE ENCOUNTERS WHICH ARE NOT A PART OF CRITERIA 1 AND CRITERIA 3

IF OBJECT_ID(N'tempdb..#C45678ABX1') IS NOT NULL DROP TABLE #C45678ABX1;

SELECT enc.PAT_ENC_CSN_ID

	, t.ABX_ADMIN_TIME 

INTO #C45678ABX1

FROM  #ENC enc

INNER JOIN #Treatment t ON t.PAT_ENC_CSN_ID = enc.PAT_ENC_CSN_ID

--CREATE INDEX IDX_C45678ax1 ON #C45678ABX1 (PAT_ENC_CSN_ID) 



--PUTTING ALL THE ABX TIMES TOGETHER TO FIND THE FIRST ABX TIME FOR AN ENCOUNTER BASED ON WHICH CRITERIA THEY SATISFIED

IF OBJECT_ID(N'tempdb..#ABXTIMES') IS NOT NULL DROP TABLE #ABXTIMES;

	SELECT PAT_ENC_CSN_ID

		, ABX_ADMIN_TIME

	INTO #ABXTIMES

	FROM #C1ABX1

UNION

	SELECT PAT_ENC_CSN_ID

		, ABX_ADMIN_TIME

	FROM #C3ABX1

UNION

	SELECT PAT_ENC_CSN_ID

		, ABX_ADMIN_TIME

	FROM #C45678ABX1

--CREATE INDEX IDX_AbxTimes ON #ABXTIMES (PAT_ENC_CSN_ID) 

	

IF OBJECT_ID(N'tempdb..#FirstABXTime') IS NOT NULL DROP TABLE #FirstABXTime;

SELECT PAT_ENC_CSN_ID

	, MIN(ABX_ADMIN_TIME) AS FIRST_ABX_TIME

INTO #FirstABXTime

FROM #ABXTIMES

GROUP BY PAT_ENC_CSN_ID 

--CREATE INDEX IDX_FirstAbxTime ON #FirstABXTime (PAT_ENC_CSN_ID) 



/* FINDING THE CLOSEST BOLUS TIME FOR EACH CRITERIA INVOLVING TREATMENT */

--C1



IF OBJECT_ID(N'tempdb..#C1BOLUS') IS NOT NULL DROP TABLE #C1BOLUS;

SELECT  s.PAT_ENC_CSN_ID

	, s.ScreenTime

	, abx.BOLUS_ADMIN_TIME

	, ABS(DATEDIFF(MI, s.SCREENTIME, abx.BOLUS_ADMIN_TIME)) AS DIFF

	, abx.BOLUS_NUM

INTO #C1BOLUS

FROM #C1 c

INNER JOIN #ScreenTime s ON s.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

INNER JOIN #TreatPlanBolus abx ON abx.PAT_ENC_CSN_ID = s.PAT_ENC_CSN_ID 

WHERE abx.BOLUS_ADMIN_TIME BETWEEN DATEADD(HH, -6, s.ScreenTime) AND DATEADD(HH, 6, s.ScreenTime)

--CREATE INDEX IDX_C1bolus ON #C1BOLUS (PAT_ENC_CSN_ID) 

	

IF OBJECT_ID(N'tempdb..#C1BOLUS1') IS NOT NULL DROP TABLE #C1BOLUS1;

SELECT c.*

INTO #C1BOLUS1 	

FROM #C1BOLUS c

WHERE DIFF = (SELECT MIN(a.DIFF)

				FROM #C1BOLUS a

				WHERE a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

	)

--CREATE INDEX IDX_C1Bolus1 ON #C1BOLUS1 (PAT_ENC_CSN_ID) 



--C3		

IF OBJECT_ID(N'tempdb..#C3BOLUS') IS NOT NULL DROP TABLE #C3BOLUS;	

SELECT s.* 

	, abx.BOLUS_ADMIN_TIME

	, ABS(DATEDIFF(MI, s.ORDER_DTTM, abx.BOLUS_ADMIN_TIME)) AS DIFF

	, abx.BOLUS_NUM

INTO #C3BOLUS	

FROM #C3 c3

	INNER JOIN #SSOrderSet s ON s.PAT_ENC_CSN_ID = c3.PAT_ENC_CSN_ID

	INNER JOIN #TreatPlanBolus abx ON abx.PAT_ENC_CSN_ID = s.PAT_ENC_CSN_ID AND s.SS_LINE = 1

WHERE abx.BOLUS_ADMIN_TIME BETWEEN DATEADD(HH, -6, s.ORDER_DTTM) AND DATEADD(HH, 6, s.ORDER_DTTM)

--CREATE INDEX IDX_C3Bolus ON #C3BOLUS (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#C3BOLUS1') IS NOT NULL DROP TABLE #C3BOLUS1;

SELECT c3.*

INTO #C3BOLUS1	

FROM #C3BOLUS c3

WHERE DIFF = (SELECT MIN(a.DIFF)

				FROM #C3BOLUS a

				WHERE a.PAT_ENC_CSN_ID = c3.PAT_ENC_CSN_ID

	)

--CREATE INDEX IDX_C3Bolus1 ON #C3BOLUS1 (PAT_ENC_CSN_ID) 

	

--FINDING EARLIEST BOLUS (PART OF TREATMENT PLAN) FOR THE ENCOUNTERS THAT ARE NOT A PART OF CRITERIA 1 AND CRITERIA 3

IF OBJECT_ID(N'tempdb..#C45678BOLUS1') IS NOT NULL DROP TABLE #C45678BOLUS1;

SELECT t.PAT_ENC_CSN_ID

	, t.FIRST_BOLUS_TIME AS BOLUS_ADMIN_TIME

	, MIN(tb.BOLUS_NUM) AS BOLUS_NUM

INTO  #C45678BOLUS1

FROM #ENC enc

INNER JOIN #Treatment t ON t.PAT_ENC_CSN_ID = enc.PAT_ENC_CSN_ID

LEFT JOIN #TreatPlanBolus tb ON tb.PAT_ENC_CSN_ID = t.PAT_ENC_CSN_ID AND tb.BOLUS_ADMIN_TIME = t.FIRST_BOLUS_TIME

GROUP BY t.PAT_ENC_CSN_ID

	, t.FIRST_BOLUS_TIME

--CREATE INDEX IDX_C45678Bolus1 ON #C45678BOLUS1 (PAT_ENC_CSN_ID) 



--PUTTING ALL THE BOLUS TIMES TOGETHER TO FIND THE FIRST BOLUS TIME FOR AN ENCOUNTER BASED ON WHICH CRITERIA THEY SATISFIED

IF OBJECT_ID(N'tempdb..#BOLUSTIMES') IS NOT NULL DROP TABLE #BOLUSTIMES;

	SELECT PAT_ENC_CSN_ID

		, BOLUS_ADMIN_TIME

		, BOLUS_NUM

	INTO #BOLUSTIMES

	FROM #C1BOLUS1

UNION

	SELECT PAT_ENC_CSN_ID

		, BOLUS_ADMIN_TIME

		, BOLUS_NUM

	FROM #C3BOLUS1

UNION

	SELECT PAT_ENC_CSN_ID

		, BOLUS_ADMIN_TIME

		, BOLUS_NUM

	FROM #C45678BOLUS1

--CREATE INDEX IDX_BolusTimes ON #BOLUSTIMES (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#FBT') IS NOT NULL DROP TABLE #FBT;

SELECT b.PAT_ENC_CSN_ID

	, MIN(b.BOLUS_ADMIN_TIME) AS FIRST_BOLUS_TIME

INTO #FBT

FROM #BOLUSTIMES b

GROUP BY b.PAT_ENC_CSN_ID  

--CREATE INDEX IDX_Fbt ON #FBT (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#FirstBolusTime') IS NOT NULL DROP TABLE #FirstBolusTime;

SELECT fbt.PAT_ENC_CSN_ID

	, fbt.FIRST_BOLUS_TIME

	, MIN(t.BOLUS_NUM) AS BOLUS_NUM

INTO #FirstBolusTime

FROM #FBT fbt

INNER JOIN #BOLUSTIMES t ON t.PAT_ENC_CSN_ID = fbt.PAT_ENC_CSN_ID AND t.BOLUS_ADMIN_TIME = fbt.FIRST_BOLUS_TIME

GROUP BY fbt.PAT_ENC_CSN_ID

	, fbt.FIRST_BOLUS_TIME 

--CREATE INDEX IDX_FirstBolusTime ON #FirstBolusTime (PAT_ENC_CSN_ID) 

	

IF OBJECT_ID(N'tempdb..#FTZ') IS NOT NULL DROP TABLE #FTZ;

SELECT c.PAT_ENC_CSN_ID

	, CASE WHEN c7.PAT_ENC_CSN_ID IS NOT NULL THEN 

		COALESCE(

				DefaultScreenTime.DefaultScreenTime

				, DefaultOSetTime.DefaultOSetTime

				, CASE 

					WHEN(DefaultABXTime.DefaultABXTime <= DefaultBolTime.DefaultBolTime) 

						THEN DefaultABXTime.DefaultABXTime 

					ELSE DefaultBolTime.DefaultBolTime

				END

		) 

	ELSE

		COALESCE(st.ScreenTime

				, ssos.ORDER_DTTM

				, CASE WHEN(ABXT.FIRST_ABX_TIME <= FBT.FIRST_BOLUS_TIME) 

						THEN ABXT.FIRST_ABX_TIME 

					ELSE FBT.FIRST_BOLUS_TIME  END

				, DefaultScreenTime.DefaultScreenTime

				, DefaultOSetTime.DefaultOSetTime

				, CASE  WHEN(DefaultABXTime.DefaultABXTime <= DefaultBolTime.DefaultBolTime) 

						THEN DefaultABXTime.DefaultABXTime 

					ELSE DefaultBolTime.DefaultBolTime

				END

		) 

	END AS ftz

	, CASE WHEN c7.PAT_ENC_CSN_ID IS NOT NULL THEN

		CASE WHEN DefaultScreenTime.DefaultScreenTime IS NOT NULL THEN 1

			WHEN DefaultOSetTime.DefaultOSetTime IS NOT NULL THEN 3

			WHEN (DefaultABXTime.DefaultABXTime <= DefaultBolTime.DefaultBolTime) THEN 4

			WHEN (DefaultBolTime.DefaultBolTime < DefaultABXTime.DefaultABXTime) THEN 95

			ELSE 6

		END

	ELSE 

		CASE 

		WHEN st.ScreenTime IS NOT NULL THEN 1

		WHEN ssos.ORDER_DTTM IS NOT NULL THEN 3

		WHEN (abxt.FIRST_ABX_TIME <= fbt.FIRST_BOLUS_TIME) THEN 4

		WHEN (fbt.FIRST_BOLUS_TIME < abxt.FIRST_ABX_TIME) THEN 95

		ELSE 6 END

	END AS FunctionalTimeZero_V68

INTO #FTZ

FROM #COHORT c

LEFT OUTER JOIN #C7_R65_ONLY c7 ON c7.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN #ScreenTime st ON st.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN #OSTP ssos ON ssos.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID AND ssos.SS_LINE = 1

LEFT JOIN #FirstABXTime abxt ON abxt.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN #FirstBolusTime fbt ON fbt.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

/*MODIFIED BY Developer A ON 07.16.2019 - IN CASE NONE OF THE ABOVE TIMES ARE POPULATED, WE LOOK FOR THE FIRST SCREENTIME/OSSET TIME ETC IN THE REPORTING PERIOD*/

OUTER APPLY

(	SELECT MIN(a.SCORE_TIME) AS DefaultScreenTime

	FROM #Scores a

	WHERE a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

)DefaultScreenTime

OUTER APPLY

(	SELECT MIN(a.ORDER_DTTM) AS DefaultOSetTime

	FROM #SSOrderSet a

	WHERE a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

)DefaultOSetTime

OUTER APPLY

(	SELECT MIN(a.ABX_ADMIN_TIME) AS DefaultABXTime

	FROM #TreatPlanABX a

	WHERE a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

)DefaultABXTime

OUTER APPLY

(	SELECT MIN(a.BOLUS_ADMIN_TIME) AS DefaultBolTime

	FROM #TreatPlanBolus a

	WHERE a.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

)DefaultBolTime

CREATE INDEX IDX_Ftx ON #FTZ(PAT_ENC_CSN_ID) 

-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*Time Zero Location Variable ID – V66 DEFAULT 99*/

IF OBJECT_ID(N'tempdb..#FTZLoc') IS NOT NULL DROP TABLE #FTZLoc;

SELECT c.PAT_ENC_CSN_ID

	, adt.ADT_DEPARTMENT_NAME AS FUNCTIONAL_TIME_ZERO_DEPT

	, adt.ADT_LOC_NAME AS FUNCTIONAL_TIME_ZERO_LOC

	, CASE WHEN adt.ADT_DEPARTMENT_ID IS NULL THEN 99 --NOT SPECIFIED

		WHEN adt.ADT_DEPARTMENT_ID IN (SELECT * FROM #EDDepts) THEN 1--ED

		WHEN adt.ADT_DEPARTMENT_ID IN ( SELECT d.DEPARTMENT_ID FROM #AllICUDept d ) THEN 2--ICU

		WHEN adt.ADT_DEPARTMENT_ID IN ( SELECT m.DEPARTMENT_ID FROM #MedDept m )THEN 3 --GEN FLOOR--updated on 01.21.2022

		WHEN adt.ADT_DEPARTMENT_ID IN (SELECT * FROM #HemOncBMTDepts) THEN 4--HEMONC

		ELSE 95

	END AS TimeZeroLoc_V66

INTO #FTZLoc

FROM #COHORT c

LEFT JOIN #FTZ ftz ON ftz.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN EMRDB.dbo.V_PATIENT_LOCATION_HISTORY adt ON c.PAT_ENC_CSN_ID = adt.PAT_ENC_CSN 

	AND adt.ADT_SERV_AREA_ID IS NOT NULL

	AND ftz.FTZ BETWEEN adt.IN_DTTM AND adt.OUT_DTTM

CREATE INDEX IDX_FtzLoc ON #FTZLoc (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*Time First Hypotension - If PATIENTS was hypotensive, this is the time of the first documented hypotension at time closest

to time zero (within 24 hours before to 24 hours after Time Zero). */

IF OBJECT_ID(N'tempdb..#Hypotension') IS NOT NULL DROP TABLE #Hypotension;

SELECT c.PAT_ENC_CSN_ID

	, ftz.FTZ

	, ifm.RECORDED_TIME

	, c.AGE_MONTHS

	, c.AGE_YEARS

	, CASE WHEN 

			c.AGE_MONTHS < 2 AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 65

		OR	(c.AGE_MONTHS >= 2 AND c.AGE_MONTHS < 12) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 70

		OR	(c.AGE_YEARS >= 1 AND c.AGE_YEARS < 2) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 80

		OR	(c.AGE_YEARS >= 2 AND c.AGE_YEARS < 6) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 90

		OR	(c.AGE_YEARS >= 6 AND c.AGE_YEARS < 13) AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 100

		OR	c.AGE_YEARS >= 13 AND LEFT(IFM.MEAS_VALUE, CHARINDEX('/', IFM.MEAS_VALUE)-1) < 110

		THEN ifm.RECORDED_TIME

	ELSE '1900-01-02 00:00:00'

	END AS FirstTimeHypotension_V18

	, LEFT(ifm.MEAS_VALUE, CHARINDEX('/', ifm.MEAS_VALUE)-1) AS SYSTOLIC

	, ifm.MEAS_VALUE

	, ROW_NUMBER() OVER(PARTITION BY c.PAT_ENC_CSN_ID ORDER BY ABS(DATEDIFF(SS, ftz.FTZ, ifm.RECORDED_TIME))ASC) AS ORD_RESULTS_LINE

INTO #Hypotension 

FROM #COHORT c 

LEFT JOIN #FTZ ftz ON ftz.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN EMRDB.dbo.FLOWSHEET_RECORDS ifr ON ifr.INPATIENT_DATA_ID = c.INPATIENT_DATA_ID

LEFT JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS ifm ON ifm.FSD_ID = ifr.FSD_ID AND ifm.FLO_MEAS_ID = '95'

WHERE ifm.RECORDED_TIME IS NOT NULL 

	AND ifm.MEAS_VALUE IS NOT NULL

	AND ifm.RECORDED_TIME BETWEEN DATEADD(HH, -24, ftz.FTZ) AND DATEADD(HH, 24, ftz.FTZ)

	AND (c.AGE_MONTHS < 2 AND LEFT(ifm.MEAS_VALUE, CHARINDEX('/', ifm.MEAS_VALUE)-1) < 65

		OR	(c.AGE_MONTHS >= 2 AND c.AGE_MONTHS < 12) AND LEFT(ifm.MEAS_VALUE, CHARINDEX('/', ifm.MEAS_VALUE)-1) < 70

		OR	(c.AGE_YEARS >= 1 AND c.AGE_YEARS < 2) AND LEFT(ifm.MEAS_VALUE, CHARINDEX('/', ifm.MEAS_VALUE)-1) < 80

		OR	(c.AGE_YEARS >= 2 AND c.AGE_YEARS < 6) AND LEFT(ifm.MEAS_VALUE, CHARINDEX('/',	ifm.MEAS_VALUE)-1) < 90

		OR	(c.AGE_YEARS >= 6 AND c.AGE_YEARS < 13) AND LEFT(ifm.MEAS_VALUE, CHARINDEX('/', ifm.MEAS_VALUE)-1) < 100

		OR	c.AGE_YEARS >= 13 AND LEFT(ifm.MEAS_VALUE, CHARINDEX('/', ifm.MEAS_VALUE)-1) < 110)



--CREATE INDEX IDX_hypotension ON #Hypotension (PAT_ENC_CSN_ID) 

-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* FIRST PRESSOR TIME - Indicates the time and type of vasoactive agent was first used. The target time is within 24 hours after

Time Zero.*/

IF OBJECT_ID(N'tempdb..#FirstPressorTime') IS NOT NULL DROP TABLE #FirstPressorTime;

SELECT c.PAT_ENC_CSN_ID

	, p.PRESSOR_START_TIME

	, ROW_NUMBER() OVER(PARTITION BY c.PAT_ENC_CSN_ID ORDER BY p.PRESSOR_START_TIME ASC) AS PRESSOR_ORDER_LINE

	, p.GROUPER_ID

INTO #FirstPressorTime

FROM #COHORT c

LEFT JOIN #FTZ f ON f.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

LEFT JOIN #TreatPlanPres p ON p.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID

WHERE p.PRESSOR_START_TIME BETWEEN f.FTZ AND DATEADD(HH, 24, f.FTZ)

--CREATE INDEX IDX_firstPressorTime ON #FirstPressorTime (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------	

-----------------------------------------------------------------------------------------------------------------------------------------------------	

/*CVL PLACEMENT TIME - Time of placement of central venous line in PATIENTS, if within timeframe of 72 hours before Time

Zero to 72 hours after Time Zero. Report as not applicable if the central line was placed more

than 72 hours before Time Zero or more than 72 hours after Time Zero. DEFAULT 1900-01-03T00:00:00 */

IF OBJECT_ID(N'tempdb..#ALLCVLTime') IS NOT NULL DROP TABLE #ALLCVLTime;

SELECT DISTINCT c.PAT_ENC_CSN_ID

	, iln.PLACEMENT_INSTANT	

INTO #ALLCVLTime

FROM #COHORT c

INNER JOIN EMRDB.dbo.LINE_DEVICE_AIRWAY iln ON iln.PAT_ENC_CSN_ID = c.PAT_ENC_CSN_ID 

INNER JOIN reportingDB.reports.CONFIG_VALUE_SET cvs ON cvs.CODE = iln.FLO_MEAS_ID

	AND cvs.VALUE_SET_ID = 3022 --CVL CODES

--INNER JOIN #CVLFlo cvl ON cvl.FLO_ID = iln.FLO_MEAS_ID

--CREATE INDEX IDX_allcvlTime ON #ALLCVLTime (PAT_ENC_CSN_ID) 



--CALCULATING ALL THE CVL TIME 72 HOURS BEFORE AND AFTER FTZ

IF OBJECT_ID(N'tempdb..#CVLTZIN') IS NOT NULL DROP TABLE #CVLTZIN;

SELECT DISTINCT a.PAT_ENC_CSN_ID

	, a.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY a.PAT_ENC_CSN_ID ORDER BY ABS(DATEDIFF(MI, a.PLACEMENT_INSTANT, f.FTZ)) ASC) AS LINE

INTO #CVLTZIN

FROM #ALLCVLTime a

LEFT JOIN #FTZ f ON f.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID

WHERE a.PLACEMENT_INSTANT BETWEEN DATEADD(HH, -72, f.FTZ) AND DATEADD(HH, 72, f.FTZ)

--CREATE INDEX IDX_CvlTzin ON #CVLTZIN (PAT_ENC_CSN_ID) 



--CALCULATING ALL THE CVL TIME NOT 72 HOURS BEFORE AND AFTER FTZ

IF OBJECT_ID(N'tempdb..#CVLTZOUT') IS NOT NULL DROP TABLE #CVLTZOUT;

SELECT DISTINCT a.PAT_ENC_CSN_ID

	, a.PLACEMENT_INSTANT

	, ROW_NUMBER() OVER(PARTITION BY a.PAT_ENC_CSN_ID ORDER BY ABS(DATEDIFF(MI, a.PLACEMENT_INSTANT, f.FTZ)) ASC) AS LINE

INTO #CVLTZOUT

FROM #ALLCVLTime a

LEFT JOIN #FTZ f ON f.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID

WHERE a.PLACEMENT_INSTANT NOT BETWEEN DATEADD(HH, -72, f.FTZ) AND DATEADD(HH, 72, f.FTZ)

--CREATE INDEX IDX_cvltzout ON #CVLTZOUT (PAT_ENC_CSN_ID) 



--CALCULATING CVL TIME

IF OBJECT_ID(N'tempdb..#CVLTIME') IS NOT NULL DROP TABLE #CVLTIME;

SELECT c.PAT_ENC_CSN_ID

	, CASE WHEN cvIn.PLACEMENT_INSTANT IS NULL AND cvOut.PLACEMENT_INSTANT IS NULL  THEN '1900-01-03 00:00:00'

		WHEN cvIn.PLACEMENT_INSTANT IS NOT NULL THEN cvIn.PLACEMENT_INSTANT

		WHEN cvIn.PLACEMENT_INSTANT IS NULL AND cvOut.PLACEMENT_INSTANT IS NOT NULL THEN '1900-01-02 00:00:00'

	END AS CVLTIME

INTO #CVLTIME

FROM #COHORT C

LEFT JOIN #CVLTZIN  cvIn ON cvIn.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND cvIn.LINE = 1

LEFT JOIN #CVLTZOUT cvOut ON cvOut.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND cvOut.LINE = 1

--CREATE INDEX IDX_CvlTime ON #CVLTIME (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*SVO2 - Time of obtaining mixed venous saturation for PATIENTS, if within timeframe of 72 hours before

Time Zero to 72 hours after Time Zero. Report as not applicable if mixed venous saturation was

obtained more than 72 hours before Time Zero or more than 72 hours after Time Zero.*/

--O2 SATURATION VENOUS, GEM CALC [5000001861]

--O2 SATURATION VENOUS [5000000478]



IF OBJECT_ID(N'tempdb..#ALLSVO2Time') IS NOT NULL DROP TABLE #ALLSVO2Time;

SELECT c.PAT_ENC_CSN_ID

	, ord.COMP_OBS_INST_TM AS SVO2TIME	

INTO #ALLSVO2Time

FROM #COHORT c

LEFT JOIN EMRDB.dbo.LAB_ORDER_RESULTS ord ON c.PAT_ENC_CSN_ID = ord.PAT_ENC_CSN_ID

WHERE ord.COMPONENT_ID IN (5000001861, 5000000478)

--CREATE INDEX IDX_allsvo2Time ON #AllSVO2Time (PAT_ENC_CSN_ID) 



--CALCULATING ALL THE SVO2 TIME 72 HOURS BEFORE AND AFTER FTZ

IF OBJECT_ID(N'tempdb..#SVO2IN') IS NOT NULL DROP TABLE #SVO2IN;

SELECT DISTINCT  a.PAT_ENC_CSN_ID

	, a.SVO2TIME

	, ROW_NUMBER() OVER(PARTITION BY a.PAT_ENC_CSN_ID ORDER BY ABS(DATEDIFF(MI, a.SVO2TIME, f.FTZ)) ASC) AS LINE

INTO #SVO2IN

FROM #ALLSVO2Time a

LEFT JOIN #FTZ f ON f.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID

WHERE a.SVO2TIME BETWEEN DATEADD(HH, -72, f.FTZ) AND DATEADD(HH, 72, f.FTZ)

--CREATE INDEX IDX_Svo2In ON #SVO2IN (PAT_ENC_CSN_ID) 



--CALCULATING ALL THE CVL TIME NOT 72 HOURS BEFORE AND AFTER FTZ

IF OBJECT_ID(N'tempdb..#SVO2OUT') IS NOT NULL DROP TABLE #SVO2OUT;

SELECT DISTINCT

	a.PAT_ENC_CSN_ID

	, a.SVO2TIME

	, ROW_NUMBER() OVER(PARTITION BY a.PAT_ENC_CSN_ID ORDER BY a.SVO2TIME ASC) AS LINE

INTO #SVO2OUT

FROM #ALLSVO2Time a

LEFT JOIN #FTZ f ON f.PAT_ENC_CSN_ID = a.PAT_ENC_CSN_ID

WHERE a.SVO2TIME NOT BETWEEN DATEADD(HH, -72, f.FTZ) AND DATEADD(HH, 72, f.FTZ)

--CREATE INDEX IDX_Svo2Out ON #SVO2OUT (PAT_ENC_CSN_ID) 



--CALCULATING SVO2 TIME

IF OBJECT_ID(N'tempdb..#SVO2TIME') IS NOT NULL DROP TABLE #SVO2TIME;

SELECT

	C.PAT_ENC_CSN_ID

	, CASE

		WHEN 

			#SVO2IN.SVO2TIME IS NULL AND #SVO2OUT.SVO2TIME IS NULL

		THEN

			'1900-01-02 00:00:00'

		WHEN

			#SVO2IN.SVO2TIME IS NOT NULL

		THEN

			#SVO2IN.SVO2TIME

		WHEN

			#SVO2IN.SVO2TIME IS NULL AND #SVO2OUT.SVO2TIME IS NOT NULL

		THEN

			'1900-01-02 00:00:00'

	END AS SVO2TIME

INTO

	#SVO2TIME

FROM

	#COHORT C

	LEFT JOIN #SVO2IN ON #SVO2IN.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #SVO2IN.LINE = 1

	LEFT JOIN #SVO2OUT ON #SVO2OUT.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #SVO2OUT.LINE = 1

--CREATE INDEX IDX_Svo2Time ON #SVO2TIME (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*LACTIC ACID - Time first lactic acid was obtained within timeframe of 48 hours beforeTime Zero to 48 hours

after Time Zero. This variable is not applicable if lactic acid was obtained more than 48 hours

before Time Zero or more than 48 hours after Time Zero.*/



--LACTIC ACID ISTAT [5000000446]

--LACTIC ACID, GEM RESPIRATORY [5000000447]

--LACTIC ACID LEVEL [5000000449]



IF OBJECT_ID(N'tempdb..#ALLLacticAcidTime') IS NOT NULL DROP TABLE #ALLLacticAcidTime;

SELECT

	C.PAT_ENC_CSN_ID

	, COALESCE(LAB_ORDER_RESULTS.COMP_OBS_INST_TM,'1900-01-02 00:00:00') AS LacticAcidTime

	, CASE

		WHEN LAB_ORDER_RESULTS.ORD_VALUE = '>11.0'

			THEN '11.0' 

		ELSE LAB_ORDER_RESULTS.ORD_VALUE 

	END AS LacticAcidValue	

	, LAB_ORDER_RESULTS.COMP_ANL_INST_TM

INTO 

	#ALLLacticAcidTime

FROM 

	#COHORT C

	LEFT JOIN EMRDB.dbo.LAB_ORDER_RESULTS ON LAB_ORDER_RESULTS.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

WHERE

	LAB_ORDER_RESULTS.COMPONENT_ID IN ( SELECT * FROM #LacticAcidLRR)

	--AND c.PAT_ENC_CSN_ID = '1050585796'

--CREATE INDEX IDX_AllLacticacidtime ON #ALLLacticAcidTime (PAT_ENC_CSN_ID) 



--CALCULATING ALL THE SVO2 TIME 48 HOURS BEFORE AND AFTER FTZ

IF OBJECT_ID(N'tempdb..#LAIN') IS NOT NULL DROP TABLE #LAIN;

SELECT DISTINCT

	A.PAT_ENC_CSN_ID

	, A.LacticAcidTime

	, A.LacticAcidValue

	, ROW_NUMBER() OVER(PARTITION BY A.PAT_ENC_CSN_ID ORDER BY A.LacticAcidTime, A.COMP_ANL_INST_TM ASC) AS LINE

INTO

	#LAIN

FROM

	#ALLLacticAcidTime A

	LEFT JOIN #FTZ F ON F.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID

WHERE

	A.LacticAcidTime BETWEEN DATEADD(HH, -48, F.FTZ) AND DATEADD(HH, 48, F.FTZ)

--CREATE INDEX IDX_Lain ON #LAIN (PAT_ENC_CSN_ID) 



--CALCULATING ALL THE SVO2 TIME NOT 48 HOURS BEFORE AND AFTER FTZ

IF OBJECT_ID(N'tempdb..#LAOUT') IS NOT NULL DROP TABLE #LAOUT;

SELECT DISTINCT

	A.PAT_ENC_CSN_ID

	, A.LacticAcidTime

	, A.LacticAcidValue

	, ROW_NUMBER() OVER(PARTITION BY A.PAT_ENC_CSN_ID ORDER BY ABS(DATEDIFF(MI, A.LacticAcidTime, F.FTZ)) ASC) AS LINE

INTO

	#LAOUT

FROM

	#ALLLacticAcidTime A

	LEFT JOIN #FTZ F ON F.PAT_ENC_CSN_ID = A.PAT_ENC_CSN_ID

WHERE

	A.LacticAcidTime NOT BETWEEN DATEADD(HH, -48, F.FTZ) AND DATEADD(HH, 48, F.FTZ)

--CREATE INDEX IDX_laout ON #LAOUT (PAT_ENC_CSN_ID) 



--CALCULATING LACTIC ACID TIME AND VALUE

IF OBJECT_ID(N'tempdb..#LacticAcid') IS NOT NULL DROP TABLE #LacticAcid

SELECT

	C.PAT_ENC_CSN_ID

	, CASE

		WHEN 

			#LAIN.LacticAcidTime IS NULL AND #LAOUT.LacticAcidTime IS NULL

		THEN

			'1900-01-02 00:00:00'

		WHEN

			#LAIN.LacticAcidTime IS NOT NULL

		THEN

			#LAIN.LacticAcidTime

		WHEN

			#LAIN.LacticAcidTime IS NULL AND #LAOUT.LacticAcidTime IS NOT NULL

		THEN

			'1900-01-02 00:00:00'

	END AS LacticAcidTime

	, CASE

		WHEN 

			#LAIN.LacticAcidTime IS NULL AND #LAOUT.LacticAcidTime IS NULL

		THEN

			'88'

		WHEN

			#LAIN.LacticAcidTime IS NOT NULL

		THEN

			--ROUND(CONVERT(FLOAT, #LAIN.LacticAcidValue), 1)

			ROUND(TRY_CAST(#LAIN.LacticAcidValue AS FLOAT),1)--10.12.2020--erroring out because of text in data :)

		WHEN

			#LAIN.LacticAcidTime IS NULL AND #LAOUT.LacticAcidTime IS NOT NULL

		THEN

			'88'

	END AS LacticAcidValue

INTO

	#LacticAcid

FROM

	#COHORT C

	LEFT JOIN #LAIN ON #LAIN.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #LAIN.LINE = 1

	LEFT JOIN #LAOUT ON #LAOUT.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #LAOUT.LINE = 1

--CREATE INDEX IDX_LacticAcid ON #LacticAcid (PAT_ENC_CSN_ID) 



/*END OF LACTIC ACID*/

-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* BLOOD CULTURE POSITIVE - Indicates whether or not there was a positive blood culture for the PATIENTS. The

timeframe for the positive culture can be from the 48 hours prior to arrival time at your hospital

(as reported in the ArrivalTime field) up to 72 hours after Time Zero.*/



IF OBJECT_ID(N'tempdb..#BloodCultureValue') IS NOT NULL DROP TABLE #BloodCultureValue;

SELECT

	C.PAT_ENC_CSN_ID

	, OP.ORDER_TIME AS MBOrderTime

	, RESULTS.COMP_OBS_INST_TM AS ResultTime

	, RESULTS.ORD_VALUE

	, ROW_NUMBER() OVER(PARTITION BY C.PAT_ENC_CSN_ID ORDER BY ABS(DATEDIFF(MI, OP.ORDER_TIME, #FTZ.FTZ)) ASC) AS LINE

	, CASE

		WHEN RESULTS.ORD_VALUE IS NULL THEN 99

		WHEN RESULTS.ORD_VALUE LIKE '%No growth%' THEN 0

		ELSE 1 

	END AS BCPositive_V35	

INTO 

	#BloodCultureValue 

FROM 

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.LAB_ORDER_RESULTS RESULTS ON C.PAT_ENC_CSN_ID = RESULTS.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.PROCEDURE_ORDERS OP ON RESULTS.ORDER_PROC_ID = OP.ORDER_PROC_ID 

			--AND OP.PROC_CODE in ('LAB001', 'lab6219', 'nur13204', 'lab6218')

			AND OP.PROC_ID in (SELECT * FROM #BloodCultures)

	JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

WHERE

	RESULTS.RESULT_TIME BETWEEN DATEADD(HH, -48, PEH.HOSP_ADMSN_TIME) AND DATEADD(HH, 168, #FTZ.FTZ) --MAY NEED TO CONSIDER PRLIMINARY RESULT TIME BUT AS PER STEPHANIE FINAL REULT TIME IS FINE FOR NOW

--CREATE INDEX IDX_bloodculturevalue ON #BloodCultureValue (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* Time Surgical Source Control - Time of surgical procedure to control the source of PATIENTS's infection where the source of the

infection is abscess, peritonitis, line infection, bone/joint infection, empyema, or infected

hardware, if the procedure was within 48 hours before Time Zero to 48 hours after Time Zero.*/



IF OBJECT_ID(N'tempdb..#TSSC') IS NOT NULL DROP TABLE #TSSC;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

	, VLB.IN_OR_DTTM AS PROC_DATE

	, ROW_NUMBER() OVER(PARTITION BY C.PAT_ENC_CSN_ID ORDER BY ABS(DATEDIFF(MI, VLB.IN_OR_DTTM, #FTZ.FTZ)) ASC) AS LINE

INTO

	#TSSC 

FROM

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.PAT_OR_ADM_LINK POAL ON POAL.OR_LINK_CSN = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.V_LOG_BASED VLB ON VLB.LOG_ID = POAL.LOG_ID

	INNER JOIN EMRDB.dbo.HSP_ACCT_PX_LIST HAPL ON HAPL.HSP_ACCOUNT_ID = PEH.HSP_ACCOUNT_ID

	INNER JOIN EMRDB.dbo.CL_ICD_PX CIP ON CIP.ICD_PX_ID = HAPL.FINAL_ICD_PX_ID

	INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = cip.REF_BILL_CODE AND CVS.VALUE_SET_ID = 1023 --SURGICAL SOURCE CODES

WHERE

	VLB.IN_OR_DTTM BETWEEN DATEADD(HH, -48, #FTZ.FTZ) AND DATEADD(HH, 48, #FTZ.FTZ)

--CREATE INDEX IDX_tssc ON #TSSC (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*ECMO - Indicates if PATIENTS was placed on ECMO within 30 days after Time Zero.*/



IF OBJECT_ID(N'tempdb..#ECMO') IS NOT NULL DROP TABLE #ECMO;

SELECT

	C.PAT_ENC_CSN_ID

	, IFM.MEAS_VALUE

	, ROW_NUMBER() OVER(PARTITION BY C.PAT_ENC_CSN_ID ORDER BY MEAS_VALUE DESC) AS LINE	

INTO 

	#ECMO

FROM 

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = C.INPATIENT_DATA_ID

	INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFR.FSD_ID = IFM.FSD_ID 

			AND IFM.FLO_MEAS_ID = '9000101014'

			AND IFM.RECORDED_TIME BETWEEN #FTZ.FTZ AND DATEADD(DD, 30, #FTZ.FTZ)

--CREATE INDEX IDX_ecmo ON #ECMO (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* HIGH RISK CONDITIONS - The PATIENTS's underlying high risk conditions documented in ED or on admission. May require

manual chart review to determine. Select all that apply. If no high risk conditions are identified,

use 88 for not applicable. Note: this variable is a multi-select variable. If you import data, the

import template provides a column for each high risk condition as well as a column for N/A and

you must answer TRUE or FALSE for each*/



--MALIGNANCY

IF OBJECT_ID(N'tempdb..#HRC1') IS NOT NULL DROP TABLE #HRC1;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

INTO

	#HRC1

FROM

	#COHORT C

	INNER JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES PED ON PED.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.EDG_CURRENT_ICD10 ECI ON ECI.DX_ID = PED.DX_ID

	INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = ECI.CODE AND CVS.VALUE_SET_ID = 1021 --MALIGNANCY CODES

--CREATE INDEX IDX_hrc1 ON #HRC1 (PAT_ENC_CSN_ID) 



--ASPLENIA

IF OBJECT_ID(N'tempdb..#HRC2') IS NOT NULL DROP TABLE #HRC2;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

INTO

	#HRC2

FROM

	#COHORT C

	INNER JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES PED ON PED.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.EDG_CURRENT_ICD10 ECI ON ECI.DX_ID = PED.DX_ID AND ECI.CODE IN ('Q89.01', 'Z90.81') --ASPLENIA CODES

--CREATE INDEX IDX_hrc2 ON #HRC2 (PAT_ENC_CSN_ID) 



--Bone Marrow Transp

IF OBJECT_ID(N'tempdb..#HRC3') IS NOT NULL DROP TABLE #HRC3;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

INTO

	#HRC3

FROM

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.HSP_ACCT_PX_LIST HAPL ON HAPL.HSP_ACCOUNT_ID = PEH.HSP_ACCOUNT_ID

	INNER JOIN EMRDB.dbo.CL_ICD_PX CIP ON CIP.ICD_PX_ID = HAPL.FINAL_ICD_PX_ID

	INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = cip.REF_BILL_CODE AND CVS.VALUE_SET_ID = 1018 --Bone Marrow Transp CODES

--CREATE INDEX IDX_hrc3 ON #HRC3 (PAT_ENC_CSN_ID) 



--Indwelling Line/Catheter

IF OBJECT_ID(N'tempdb..#HRC4') IS NOT NULL DROP TABLE #HRC4;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

INTO

	#HRC4

FROM

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.HSP_ACCT_PX_LIST HAPL ON HAPL.HSP_ACCOUNT_ID = PEH.HSP_ACCOUNT_ID

	INNER JOIN EMRDB.dbo.CL_ICD_PX CIP ON CIP.ICD_PX_ID = HAPL.FINAL_ICD_PX_ID

	INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = cip.REF_BILL_CODE AND CVS.VALUE_SET_ID = 1019 --Indwelling Line/Catheter CODES

--CREATE INDEX IDX_hrc4 ON #HRC4 (PAT_ENC_CSN_ID) 



--Solid Organ Transplant

IF OBJECT_ID(N'tempdb..#HRC95') IS NOT NULL DROP TABLE #HRC95;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

INTO

	#HRC95

FROM

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.HSP_ACCT_PX_LIST HAPL ON HAPL.HSP_ACCOUNT_ID = PEH.HSP_ACCOUNT_ID

	INNER JOIN EMRDB.dbo.CL_ICD_PX CIP ON CIP.ICD_PX_ID = HAPL.FINAL_ICD_PX_ID

	INNER JOIN reportingDB.reports.CONFIG_VALUE_SET CVS ON CVS.CODE = cip.REF_BILL_CODE AND CVS.VALUE_SET_ID = 1020 --Solid Organ Transplant CODES

--CREATE INDEX IDX_hrc95 ON #HRC95 (PAT_ENC_CSN_ID) 



--Severe Mental Retardation/Cerebral Palsy

IF OBJECT_ID(N'tempdb..#HRC6') IS NOT NULL DROP TABLE #HRC6;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

INTO

	#HRC6

FROM

	#COHORT C

	INNER JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES PED ON PED.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.EDG_CURRENT_ICD10 ECI ON ECI.DX_ID = PED.DX_ID

			AND ECI.CODE IN (SELECT * FROM #DXIDCebrealPalsy)

--CREATE INDEX IDX_hrc6 ON #HRC6 (PAT_ENC_CSN_ID) 



--Tech Depend (Gtube, Trach, VP Shunt)

IF OBJECT_ID(N'tempdb..#HRC98') IS NOT NULL DROP TABLE #HRC98;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

INTO

	#HRC98

FROM

	#COHORT C

	INNER JOIN EMRDB.dbo.ENCOUNTER_DIAGNOSES PED ON PED.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.EDG_CURRENT_ICD10 ECI ON ECI.DX_ID = PED.DX_ID

			AND ECI.CODE IN (SELECT * FROM #DXTrachDependent)--Tech Depend (Gtube, Trach, VP Shunt) CODES

--CREATE INDEX IDX_hrc98 ON #HRC98 (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* ICU DAYS - Number of days the PATIENTS was in ICU for any part of the day beginning at Time Zero until

discharge, death, or 30 days, whichever comes first. Do not include ICU days before Time Zero. If

the PATIENTS was not in ICU, report 0 days.*/

/* Developer D'S CODE TO COUNT ICU DAYS PRIOR TO THE CHANGE ON 08.02.2019 (BY Developer A)

IF OBJECT_ID(N'tempdb..#ICUDays1') IS NOT NULL DROP TABLE #ICUDays1;

SELECT

	C.PAT_ENC_CSN_ID

	, CASE

		WHEN ISM.ICU_STAY_START_DT < CONVERT(DATE, #FTZ.FTZ) 

			THEN CONVERT(DATE, #FTZ.FTZ)

		ELSE ISM.ICU_STAY_START_DT

	END AS START_DATE

	, CASE

		WHEN ISM.ICU_STAY_END_DT > DATEADD(DD, 29, CONVERT(DATE, #FTZ.FTZ))

			THEN DATEADD(DD, 29, CONVERT(DATE, #FTZ.FTZ))

		ELSE ISM.ICU_STAY_END_DT 

	END AS END_DATE	

INTO

	#ICUDays1

FROM

	#COHORT C

	JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.HOSPITAL_ENCOUNTERS PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.DM_ICU_STAY ISM ON ISM.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

			AND (ISM.ICU_STAY_END_DT >= CONVERT(DATE, #FTZ.FTZ) OR ISM.ICU_STAY_END_DT IS NULL)

			AND ISM.PAT_ID IS NOT NULL



IF OBJECT_ID(N'tempdb..#ICUDaySum') IS NOT NULL DROP TABLE #ICUDaySum;

SELECT

	PAT_ENC_CSN_ID

	, SUM(DATEDIFF(DD, START_DATE, END_DATE)) + 1 AS ICUDays_V58

INTO

	#ICUDaySum 

FROM

	#ICUDays

GROUP BY

	PAT_ENC_CSN_ID	

*/

IF OBJECT_ID(N'tempdb..#ICUDaySum') IS NOT NULL DROP TABLE #ICUDaySum;

SELECT

VPALH.PAT_ENC_CSN,

SUM(



CASE WHEN CONVERT(DATE,VPALH.IN_DTTM) = CONVERT(DATE,VPALH.OUT_DTTM) THEN 1

WHEN OR2ICU.SPECIALTY LIKE '%SURGERY%' THEN 99999

WHEN VPALH.IN_DTTM IS NULL THEN 0

ELSE

CEILING(DATEDIFF(MI,VPALH.IN_DTTM,VPALH.OUT_DTTM)/(60*24.0))END



)  AS ICUDays_V58

INTO #ICUDaySum

FROM

	#COHORT C

	INNER JOIN #FTZ FTZ ON FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	INNER JOIN EMRDB.dbo.V_PATIENT_LOCATION_HISTORY VPALH ON VPALH.PAT_ENC_CSN = FTZ.PAT_ENC_CSN_ID

		AND (

				VPALH.IN_DTTM > FTZ.FTZ

				OR

				(FTZ.FTZ BETWEEN VPALH.IN_DTTM AND VPALH.OUT_DTTM)--modified by Developer A on 07.30.2019				

				

			)

		AND VPALH.ADT_DEPARTMENT_ID IN (	

										SELECT d.DEPARTMENT_ID

										FROM #AllICUDept d --HS BI IP ALL ICU UNITS

										) 

	OUTER APPLY

		(

			SELECT TOP 1 DEP.SPECIALTY FROM

			EMRDB.dbo.V_PATIENT_LOCATION_HISTORY N

			INNER JOIN EMRDB.dbo.DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = N.ADT_DEPARTMENT_ID

			WHERE N.PAT_ENC_CSN = VPALH.PAT_ENC_CSN AND N.IN_DTTM < VPALH.IN_DTTM

			AND N.EVENT_TYPE_C=1--ONLY OR ADMITS

			ORDER BY N.IN_DTTM DESC

		)OR2ICU

GROUP BY VPALH.PAT_ENC_CSN

--CREATE INDEX IDX_icudaysum ON #ICUDaySum (PAT_ENC_CSN) 

-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*ABX DAYS - The number of days the PATIENTS is on IV antibiotics within the 30 days after Time Zero. Use whole

numbers only; if the PATIENTS is on IV antibiotics for part of a day, it counts as one day. If the

PATIENTS is on multiple antibiotics, each antibiotic counts as a day.*/

IF OBJECT_ID(N'tempdb..#ABXDays') IS NOT NULL DROP TABLE #ABXDays;

SELECT

	OMED.PAT_ENC_CSN_ID

	, CONVERT(DATE, (MAR.TAKEN_TIME)) AS ABX_Time

	, ROW_NUMBER() OVER(PARTITION BY OMED.PAT_ENC_CSN_ID, OMED.MEDICATION_ID ORDER BY MAR.TAKEN_TIME ASC) AS MAR_Line

	, OMED.MEDICATION_ID

	, omed.ORDER_MED_ID

INTO 

	#ABXDays 

FROM 

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.MEDICATION_ORDERS OMED ON OMED.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAR ON MAR.ORDER_MED_ID = OMED.ORDER_MED_ID 

	JOIN EMRDB.dbo.MEDICATIONS MED ON MED.MEDICATION_ID = OMED.MEDICATION_ID AND MED.THERA_CLASS_C = 11 --ANTIBIOTICS

	JOIN EMRDB.dbo.MED_DETAILS_EXT MED_TWO ON MED_TWO.MEDICATION_ID = MED.MEDICATION_ID

WHERE

	(MAR.TAKEN_TIME BETWEEN #FTZ.FTZ AND DATEADD(DD, 30, #FTZ.FTZ)) --TIME COMPARISON ONLY FOR DURING THE PATIENTS TIME IN ED. NOT WHEN THE PATIENTS IS ON THE FLOOR AS AN IP ADMIT.

	AND MAR.MAR_ACTION_C IN (SELECT * FROM #MARActions)

--VALUES BELOW ADDED TO THE CODE ON STEPHANIE'S REQUEST DURING VALIDATION.

	AND MED_TWO.ADMIN_ROUTE_C NOT IN (SELECT * FROM #RouteExclusions)

--CREATE INDEX IDX_abxdayys ON #ABXDays (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#ABXDayspermed') IS NOT NULL DROP TABLE #ABXDayspermed;

SELECT

	PAT_ENC_CSN_ID

	, COUNT(DISTINCT ABX_TIME) AS ABXDayspermed

INTO 

	#ABXDayspermed

FROM 

	#ABXDays

GROUP BY 

	PAT_ENC_CSN_ID

	, MEDICATION_ID

--CREATE INDEX IDX_abxdayspermed ON #ABXDayspermed (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#ABXDays_Count') IS NOT NULL DROP TABLE #ABXDays_Count;

SELECT

	PAT_ENC_CSN_ID

	, SUM(ABXDayspermed) AS ABXDays_V42

INTO 

	#ABXDays_Count

FROM 

	#ABXDayspermed

GROUP BY 

	PAT_ENC_CSN_ID

--CREATE INDEX IDX_abxdayscount ON #ABXDays_Count (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* PRESSOR DAYS - Number of days the PATIENTS was on pressors for any part of the day beginning at Time Zero until

discharge, death, or 30 days, whichever comes first. Do not include pressor days before Time

Zero.*/



IF OBJECT_ID(N'tempdb..#PressorAdminDays') IS NOT NULL DROP TABLE #PressorAdminDays;

SELECT DISTINCT

	B.PAT_ENC_CSN_ID

	, COUNT (DISTINCT CONVERT(DATE, MAI.TAKEN_TIME) )AS Pressor_Days_V57

INTO

	#PressorAdminDays 

FROM

	#COHORT B

	LEFT JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	LEFT JOIN EMRDB.dbo.MEDICATIONS CM ON CM.MEDICATION_ID = OM.MEDICATION_ID

	LEFT JOIN EMRDB.dbo.GROUPER_MED_RECORDS GMR ON GMR.EXP_MEDS_LIST_ID = CM.MEDICATION_ID

	LEFT JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID

	LEFT JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = B.PAT_ENC_CSN_ID	

WHERE

	GMR.GROUPER_ID IN (SELECT * FROM #MedGroupers)

	AND MAI.ROUTE_C = 11 --INTRAVENOUS

	AND (MAI.TAKEN_TIME BETWEEN #FTZ.FTZ AND COALESCE(PEH.HOSP_DISCH_TIME, DATEADD(DD, 30, #FTZ.FTZ)))

GROUP BY

	B.PAT_ENC_CSN_ID, peh.HOSP_DISCH_TIME

--CREATE INDEX IDX_pressorAdminDays ON #PressorAdminDays (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#PressorsDays') IS NOT NULL DROP TABLE #PressorsDays;

SELECT

	PAT_ENC_CSN_ID

	, CASE WHEN SUM(Pressor_Days_V57) > 30 THEN 30 ELSE SUM(Pressor_Days_V57) END AS Pressor_Days_V57--08.01.2019 Developer A UPDATED TO DEFAULT TO 30 DAYS

INTO 

	#PressorsDays 

FROM 

	#PressorAdminDays 	

GROUP BY 

	PAT_ENC_CSN_ID

--CREATE INDEX IDX_PressorsDays ON #PressorsDays (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* PRESSURE VENT DAYS - Number of days the PATIENTS was on ventilation for any part of the day beginning at Time Zero

until discharge, death, or 30 days, whichever comes first. Include days where PATIENTS had

noninvasive ventilation such as BIPAP or CPAP. Do not include ventilator days before Time Zero.*/



IF OBJECT_ID(N'tempdb..#AllPVDays') IS NOT NULL DROP TABLE #AllPVDays;

SELECT DISTINCT

	C.PAT_ENC_CSN_ID

	, CONVERT(DATE, IFM.RECORDED_TIME) AS VENT_DATE

INTO

	#AllPVDays 

FROM

	#COHORT C

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = C.INPATIENT_DATA_ID

	LEFT JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

	LEFT JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

WHERE

	IFM.FLO_MEAS_ID = '3040104328' -- VENT ON

	AND IFM.MEAS_VALUE = 'Yes'

	AND (IFM.RECORDED_TIME BETWEEN #FTZ.FTZ AND COALESCE(PEH.HOSP_DISCH_TIME, DATEADD(DD, 29, #FTZ.FTZ))) 

CREATE INDEX IDX_allpvdays ON #AllPVDays (PAT_ENC_CSN_ID) 



IF OBJECT_ID(N'tempdb..#PVDays') IS NOT NULL DROP TABLE #PVDays;

SELECT 

	PAT_ENC_CSN_ID

	, CASE WHEN COUNT(DISTINCT VENT_DATE)> 30 THEN 30 ELSE COUNT(DISTINCT VENT_DATE) END AS PRESSURE_VENT_DAYS--08.01.2019 Developer A UPDATED TO DEFAULT TO 30 DAYS

INTO

	#PVDays

FROM

	#AllPVDays

GROUP BY

	PAT_ENC_CSN_ID

--CREATE INDEX IDX_pvDays ON #PVDays (PAT_ENC_CSN_ID) 



-----------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------

/* PUTTING ALL THE DISPLAY COLUMNS TOGETHER */

IF OBJECT_ID(N'tempdb..#FinalTData') IS NOT NULL DROP TABLE #FinalTData;

SELECT DISTINCT				

	CONVERT(VARCHAR,C.INPATIENT_DATA_ID) + CONVERT(VARCHAR, YEAR(DATEADD(MM,-1,GETDATE()))) + CONVERT(VARCHAR, MONTH(DATEADD(MM,-1,GETDATE()))) AS Sepsis_Episode_ID_V01			

	, COALESCE(COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.HOSP_ADMSN_TIME),'1900‐01‐01 00:00:00') AS Arrival_Time_V10

	, COALESCE((CONVERT(VARCHAR, CONVERT(DATE, PAT.BIRTH_DATE))),'1900‐01‐01') AS Birth_Date_V02			

	, CASE WHEN CRO.PAT_ENC_CSN_ID IS NOT NULL THEN 			

		COALESCE(#ScreenTime.ScreenTime_V06,DefaultScreenTime.DefaultScreenTime, '1900‐01‐02 00:00:00')		

		ELSE COALESCE(#ScreenTime.ScreenTime_V06, '1900-01-02 00:00:00')		

		END AS ScreenTime_V06		

	, COALESCE(HuddleTime.HuddleTime, HuddleNoteTime.HuddleNoteTime,'1900-01-01 00:00:00') AS Huddle_Time_V07			

	, CASE WHEN CRO.PAT_ENC_CSN_ID IS NOT NULL THEN 			

		COALESCE(#OSTP.ORDER_DTTM, DefaulTOsetTime.DefaulTOsetTime, '1900-01-02 00:00:00') --AS OrderSet_Time_V08		

		ELSE COALESCE(#OSTP.ORDER_DTTM, '1900‐01‐02 00:00:00')		

		END AS OrderSet_Time_V08		

	, CASE WHEN CRO.PAT_ENC_CSN_ID IS NOT NULL THEN 			

		COALESCE(#FirstABXTime.FIRST_ABX_TIME,DefaultABXTime.DefaultABXTime, '1900-01-02 00:00:00')		

		ELSE COALESCE(#FirstABXTime.FIRST_ABX_TIME, '1900-01-02 00:00:00')		

		END AS FirstABXTime_V26		

	, CASE WHEN CRO.PAT_ENC_CSN_ID IS NOT NULL THEN 			

		COALESCE(#FirstBolusTime.FIRST_BOLUS_TIME,DefaultBolTime.DefaultBolTime, '1900-01-02 00:00:00')		

		ELSE COALESCE(#FirstBolusTime.FIRST_BOLUS_TIME, '1900-01-02 00:00:00')		

		END AS Bolus1Time_V20		

	, #FTZ.FunctionalTimeZero_V68			

	, #FTZLoc.TimeZeroLoc_V66			

	, 999 AS Weight_V16 -- Developer C -3/21/24 no longer tracked so setting default value 

	, COALESCE(ROUND(B1.BOLUS_VOLUME, 0), 99999) AS Bolus1Volume_V21			

	, CASE			

		WHEN B2.BOLUS_ADMIN_TIME BETWEEN DATEADD(HH, -6, #FTZ.FTZ) AND DATEADD(HH, 6, #FTZ.FTZ)		

			THEN COALESCE(B2.BOLUS_ADMIN_TIME, '1900-01-02 00:00:00')	

		ELSE '1900-01-02 00:00:00'		

	END AS Bolus2Time_V22			

	, CASE			

		WHEN B2.BOLUS_ADMIN_TIME BETWEEN DATEADD(HH, -6, #FTZ.FTZ) AND DATEADD(HH, 6, #FTZ.FTZ)		

			THEN COALESCE(ROUND(B2.BOLUS_VOLUME, 0), 99999) 	

		ELSE 99999		

	END AS Bolus2Volume_V23			

	, CASE			

		WHEN B3.BOLUS_ADMIN_TIME BETWEEN DATEADD(HH, -6, #FTZ.FTZ) AND DATEADD(HH, 6, #FTZ.FTZ)		

			THEN COALESCE(B3.BOLUS_ADMIN_TIME, '1900-01-02 00:00:00') 	

		ELSE '1900-01-02 00:00:00'		

	END AS Bolus3Time_V24			

	, CASE			

		WHEN B3.BOLUS_ADMIN_TIME BETWEEN DATEADD(HH, -6, #FTZ.FTZ) AND DATEADD(HH, 6, #FTZ.FTZ)		

			THEN COALESCE(ROUND(B3.BOLUS_VOLUME, 0), 99999) 	

		ELSE 99999		

	END AS Bolus3Volume_V25			

	, COALESCE(#Hypotension.FirstTimeHypotension_V18, '1900-01-02 00:00:00') AS FirstTimeHypotension_V18			

	, COALESCE(F.PRESSOR_START_TIME, '1900-01-02 00:00:00') AS FirstPressorTime_V29			

	, CASE			

		WHEN F.GROUPER_ID = '8000100' THEN '1'		

		WHEN F.GROUPER_ID = '8000101' THEN '2'		

		WHEN F.GROUPER_ID = '8000102' THEN '95'		

		WHEN F.GROUPER_ID = '8000103' THEN '4'		

		WHEN F.GROUPER_ID = '8000104' THEN '3'		

		ELSE '88'		

	END AS FirstPressorType_V30			

	, 99 AS OrganDysfunction_V41			

	, COALESCE(#CVLTIME.CVLTIME, '1900‐01‐01 00:00:00') AS CVLPlacementTime_V44			

	, CASE WHEN			

		#SVO2TIME.SVO2TIME < COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.HOSP_ADMSN_TIME) THEN '1900‐01‐01 00:00:00'--ARRIVAL TIME CHECK ADDED BY Developer A ON 08.08.2019		

		ELSE COALESCE(#SVO2TIME.SVO2TIME, '1900‐01‐01 00:00:00')		

	END AS SVO2Time_V45			

	, CASE WHEN			

		#LacticAcid.LacticAcidTime < COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.HOSP_ADMSN_TIME) THEN '1900‐01‐01 00:00:00'--ARRIVAL TIME CHECK ADDED BY Developer A ON 08.08.2019		

		ELSE COALESCE(#LacticAcid.LacticAcidTime, '1900‐01‐01 00:00:00')		

	END AS LacticAcidTime_V46			

	, COALESCE(#LacticAcid.LacticAcidValue, '99') AS LacticAcidValue_V47			

	, COALESCE(#BloodCultureValue.BCPositive_V35, 99) AS BCPositive_V35			

	, COALESCE(#TSSC.PROC_DATE, '1900‐01‐03 00:00:00') AS TimeSurgicalSourceControl_V39			

	, CASE --if time zero is 24 hours after arrival, Outside Hospital should be reported as zero. Developer A updated this on 08.01.2019			

		WHEN PEH.ADMIT_SOURCE_C IS NULL THEN 99		

		WHEN  #FTZ.FTZ > DATEADD(HH,24,COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.HOSP_ADMSN_TIME)) THEN 0--NEWLY ADDED, SHOULD CHECK THIS BEFORE CHECKING IF ADMIT SOURCE IS NOT NULL		

		WHEN PEH.ADMIT_SOURCE_C IN (106,23,4,95,6) THEN 1 		

		ELSE 0		

	END AS OutsideHospital_V11 			

	, '1900‐01‐02 00:00:00' AS ED2GenCareTime_V12 -- Developer C -3/21/24 no longer tracked so setting default value 

	, '1900‐01‐02 00:00:00' AS ED2HemoncTime_V63 -- Developer C -3/21/24 no longer tracked so setting default value 

	, '1900‐01‐02 00:00:00' AS ED2ICUTime_V13 -- Developer C -3/21/24 no longer tracked so setting default value 

	, '1900‐01‐02 00:00:00' AS GENCARE2ICUTime_V94 -- Developer C -3/21/24 no longer tracked so setting default value 

	, '1900‐01‐02 00:00:00' AS HEMONC2ICUTime_V64 -- Developer C -3/21/24 no longer tracked so setting default value 

	, CASE			

		WHEN PEH.HOSP_DISCH_TIME IS NULL THEN 4		

		WHEN PEH.DISCH_DISP_C IN ('1', '40', '50', '6', '81', '86') THEN 1		

		WHEN PEH.DISCH_DISP_C IN ('62', '90') THEN 2		

		WHEN PEH.DISCH_DISP_C IN ('20', '40', '41', '42') THEN 3		

		ELSE 6		

	END AS Disposition_V54			

	, #FTZ.FTZ AS FunctionalTimeZero			

	, CASE	WHEN CRO.PAT_ENC_CSN_ID IS NOT NULL THEN CONVERT(char(10), DATEADD(DD, 30, PEH.HOSP_ADMSN_TIME), 126) 		

			WHEN (PEH.HOSP_DISCH_TIME IS NOT NULL AND DATEADD(DD, 30, #FTZ.FTZ)< PEH.HOSP_DISCH_TIME) THEN DATEADD(DD, 30, #FTZ.FTZ)	

			ELSE COALESCE(CONVERT(char(10), PEH.HOSP_DISCH_TIME, 126), CONVERT(char(10), DATEADD(DD, 30, #FTZ.FTZ), 126))	

	END AS DispositionDate_V53			

	, CASE			

		WHEN CRO.PAT_ENC_CSN_ID IS NOT NULL THEN CONVERT(char(10), DATEADD(DD, 30, PEH.HOSP_ADMSN_TIME), 126)		

		WHEN PEH.HOSP_DISCH_TIME IS NULL OR (PEH.HOSP_DISCH_TIME NOT BETWEEN @StartDate AND @EndDate)		

		 THEN CONVERT(char(10), DATEADD(DD, 30, #FTZ.FTZ), 126) ELSE CONVERT(char(10), PEH.HOSP_DISCH_TIME, 126) END AS New_DispositionDate_V53		

	, PEH.HOSP_DISCH_TIME as Hospital_Discharge_Time			

	, CASE 			

		WHEN #ECMO.MEAS_VALUE = 'On' THEN 1		

		ELSE 0		

	END AS ECMO_V48			

	, 99 AS Risk_Score_V52			

	, CASE 			

		WHEN COALESCE(CEILING(DM_ICU_STAY.ICU_LENGTH_OF_STAY_DAYS), 0) = 0 THEN 99 		

		ELSE 4 		

	END AS Risk_Score_Method_V51			

	, CASE			

		WHEN #HRC1.PAT_ENC_CSN_ID IS NULL THEN 'FALSE'		

		ELSE 'TRUE'		

	END AS HighRiskConditions_1_V65			

	, CASE			

		WHEN #HRC2.PAT_ENC_CSN_ID IS NULL THEN 'FALSE'		

		ELSE 'TRUE'		

	END AS HighRiskConditions_2_V65			

	, CASE			

		WHEN #HRC3.PAT_ENC_CSN_ID IS NULL THEN 'FALSE'		

		ELSE 'TRUE'		

	END AS HighRiskConditions_3_V65			

	, CASE			

		WHEN #HRC4.PAT_ENC_CSN_ID IS NULL THEN 'FALSE'		

		ELSE 'TRUE'		

	END AS HighRiskConditions_4_V65			

	, CASE			

		WHEN #HRC95.PAT_ENC_CSN_ID IS NULL THEN 'FALSE'		

		ELSE 'TRUE'		

	END AS HighRiskConditions_95_V65			

	, CASE			

		WHEN #HRC6.PAT_ENC_CSN_ID IS NULL THEN 'FALSE'		

		ELSE 'TRUE'		

	END AS HighRiskConditions_6_V65			

	, 'FALSE' AS HighRiskConditions_7_V65			

	, CASE			

		WHEN #HRC98.PAT_ENC_CSN_ID IS NULL THEN 'FALSE'		

		ELSE 'TRUE'		

	END AS HighRiskConditions_98_V65			

	, CASE			

		WHEN 		

			#HRC1.PAT_ENC_CSN_ID IS NULL	

			AND #HRC2.PAT_ENC_CSN_ID IS NULL	

			AND #HRC3.PAT_ENC_CSN_ID IS NULL	

			AND #HRC4.PAT_ENC_CSN_ID IS NULL	

			AND #HRC95.PAT_ENC_CSN_ID IS NULL	

			AND #HRC6.PAT_ENC_CSN_ID IS NULL	

			AND #HRC98.PAT_ENC_CSN_ID IS NULL	

		THEN 'TRUE'		

		ELSE 'FALSE'		

	END AS HighRiskConditions_88_V65			

	, COALESCE(#ABXDays_Count.ABXDays_V42, 99999) AS ABXDays_V42--Developer A UPDATED THIS FROM COALESCE(#ABXDays_Count.ABXDays_V42, 99999) TO COALESCE(#ABXDays_Count.ABXDays_V42, 0), PER IPSO VARIABLE DEFINITION			

	, COALESCE(#PressorsDays.Pressor_Days_V57, 0) AS Pressor_Days_V57			

	, CASE 			

		WHEN #ICUDaySum.ICUDays_V58 IS NULL THEN 0		

		WHEN #ICUDaySum.ICUDays_V58 =99999 THEN 99999		

		WHEN COALESCE(#ICUDaySum.ICUDays_V58, 0) > 30 THEN 30 ELSE #ICUDaySum.ICUDays_V58 END AS ICUDays_V58		

	, 99 AS Pt_Chronically_Vented_V32			

	, COALESCE(#PVDays.PRESSURE_VENT_DAYS, 0) AS PressureVentDays_V56			

	, '1900‐01‐02 00:00:00' AS Clinically_Derived_Time_Zero_V09			

	, C.PAT_ENC_CSN_ID			

	, DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate)) AS DATE_STAMP			

	, 0 AS REVIEWED			

	, CASE WHEN CRO.PAT_ENC_CSN_ID IS NOT NULL THEN 1 ELSE 0 END AS R_65	

	, '3036' [NACHRI_hosp]

	, peh.HSP_ACCOUNT_ID [bill]

INTO #FinalTData	

FROM #COHORT C

	LEFT JOIN #Base_Pop PEH ON PEH.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN EMRDB.dbo.PATIENTS PAT ON PAT.PAT_ID = PEH.PAT_ID

	LEFT JOIN #ScreenTime ON #ScreenTime.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #OSTP ON #OSTP.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #OSTP.SS_LINE = 1

	LEFT JOIN #FirstABXTime ON #FirstABXTime.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #FirstBolusTime ON #FirstBolusTime.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #TreatPlanBolus B1 ON B1.PAT_ENC_CSN_ID = #FirstBolusTime.PAT_ENC_CSN_ID AND B1.BOLUS_NUM = #FirstBolusTime.BOLUS_NUM

	LEFT JOIN #FTZ ON #FTZ.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #FTZLoc ON #FTZLoc.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #TreatPlanBolus B2 ON B2.PAT_ENC_CSN_ID = #FirstBolusTime.PAT_ENC_CSN_ID AND B2.BOLUS_NUM = (#FirstBolusTime.BOLUS_NUM + 1) --select * from #TreatPlanBolus--ftz 2019-06-28 21:24:00.000

	LEFT JOIN #TreatPlanBolus B3 ON B3.PAT_ENC_CSN_ID = #FirstBolusTime.PAT_ENC_CSN_ID AND B3.BOLUS_NUM = (#FirstBolusTime.BOLUS_NUM + 2)

	LEFT JOIN #Hypotension ON #Hypotension.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #Hypotension.ORD_RESULTS_LINE = 1

	LEFT JOIN #FirstPressorTime F ON F.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND F.PRESSOR_ORDER_LINE = 1

	LEFT JOIN #CVLTIME ON #CVLTime.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID 

	LEFT JOIN #SVO2TIME ON #SVO2TIME.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #LacticAcid ON #LacticAcid.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #BloodCultureValue ON #BloodCultureValue.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #BloodCultureValue.LINE = 1

	LEFT JOIN #ECMO ON #ECMO.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #ECMO.LINE = 1

	LEFT JOIN #ICUDaySum ON #ICUDaySum.PAT_ENC_CSN = C.PAT_ENC_CSN_ID

	OUTER APPLY(SELECT TOP 1 ICU_LENGTH_OF_STAY_DAYS 

				FROM EMRDB.dbo.DM_ICU_STAY 

				WHERE DM_ICU_STAY.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID 

						AND DM_ICU_STAY.ICU_STAY_END_DTTM > #FTZ.FTZ

				)DM_ICU_STAY

	LEFT JOIN #ABXDays_Count ON #ABXDays_Count.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #PressorsDays ON #PressorsDays.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #PVDays ON #PVDays.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #HRC1 ON #HRC1.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #HRC2 ON #HRC2.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #HRC3 ON #HRC3.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #HRC4 ON #HRC4.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #HRC95 ON #HRC95.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #HRC6 ON #HRC6.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #HRC98 ON #HRC98.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	LEFT JOIN #TSSC ON #TSSC.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID AND #TSSC.LINE = 1

	LEFT OUTER JOIN #C7_R65_ONLY CRO ON CRO.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	/*MODIFIED BY Developer A OM 07.16.2019 - IN CASE NONE OF THE ABOVE TIMES ARE POPULATED, WE LOOK FOR THE FIRST SCREENTIME/OSSET TIME ETC IN THE REPORTING PERIOD*/

	OUTER APPLY

	(

		SELECT

		MIN(A.SCORE_TIME) AS DefaultScreenTime

		FROM #Scores A

		WHERE A.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	)DefaultScreenTime

	OUTER APPLY

	(

		SELECT

		MIN(A.ORDER_DTTM) AS DefaultOSetTime

		FROM #SSOrderSet A

		WHERE A.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	)DefaultOSetTime

	OUTER APPLY

	(

		SELECT

		MIN(A.ABX_ADMIN_TIME) AS DefaultABXTime

		FROM #TreatPlanABX A

		WHERE A.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	)DefaultABXTime

	OUTER APPLY

	(

		SELECT

		MIN(A.BOLUS_ADMIN_TIME) AS DefaultBolTime

		FROM #TreatPlanBolus A

		WHERE A.PAT_ENC_CSN_ID = C.PAT_ENC_CSN_ID

	)DefaultBolTime

	OUTER APPLY

	(

		SELECT MIN(IFM.RECORDED_TIME) AS HuddleTime

		FROM 

			#Base_Pop PEH

			INNER JOIN EMRDB.dbo.FLOWSHEET_RECORDS IFR ON IFR.INPATIENT_DATA_ID = PEH.INPATIENT_DATA_ID

			INNER JOIN EMRDB.dbo.FLOWSHEET_MEASUREMENTS IFM ON IFM.FSD_ID = IFR.FSD_ID

			INNER JOIN #IP_PositiveScores IPS ON IPS.PAT_ENC_CSN_ID = PEH.PAT_ENC_CSN_ID

				AND IPS.RECORDED_TIME = IFM.RECORDED_TIME--MAKE SURE THE SCORE IS AN OD SCORE AND NOT ED SCORE - BECAUSE THERE IS NO HUDDLE TIME FOR ED SCORE

		WHERE

			PEH.PAT_ENC_CSN_ID = #ScreenTime.PAT_ENC_CSN_ID

			AND IFM.FLO_MEAS_ID = '9000002733'--HUDDLE TIME

			AND IFM.RECORDED_TIME>=#ScreenTime.ScreenTime

		--ORDER BY IFM.RECORDED_TIME ASC

	)HuddleTime

	OUTER APPLY

	(--HUDDLE TIME FROM NOTES TKT-014

		SELECT MIN(HNO.CRT_INST_LOCAL_DTTM) AS HuddleNoteTime

		FROM 

			EMRDB.dbo.CLINICAL_NOTES HNO			

			INNER JOIN EMRDB.dbo.HNO_NOTE_TEXT HNT ON HNT.NOTE_ID = HNO.NOTE_ID			

		WHERE

			HNO.PAT_ENC_CSN_ID = #ScreenTime.PAT_ENC_CSN_ID

			AND HNO.IP_NOTE_TYPE_C='1000007'--	Significant Event

			AND HNT.NOTE_TEXT LIKE '%Sepsis%Huddle%Note%'

		--ORDER BY IFM.RECORDED_TIME ASC

	) HuddleNoteTime

CREATE INDEX IDX_finalTData ON #FinalTData (PAT_ENC_CSN_ID) 	



-------------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

IF OBJECT_ID(N'tempdb..#FinalData') IS NOT NULL DROP TABLE #FinalData;

SELECT

	CONVERT(numeric, F.Sepsis_Episode_ID_V01) AS Sepsis_Episode_ID_V01				

	, CONVERT(datetime2(0), F.Arrival_Time_V10) AS Arrival_Time_V10			

	, CONVERT(date, F.Birth_Date_V02) AS Birth_Date_V02			

	, CONVERT(datetime2(0), F.ScreenTime_V06) AS ScreenTime_V06			

	, CONVERT(datetime2(0), F.Huddle_Time_V07) AS Huddle_Time_V07			

	, CONVERT(datetime2(0), F.OrderSet_Time_V08) AS OrderSet_Time_V08			

	, CONVERT(datetime2(0), F.FirstABXTime_V26) AS FirstABXTime_V26			

	, CONVERT(datetime2(0), F.Bolus1Time_V20) AS Bolus1Time_V20			

	, CONVERT(numeric, F.FunctionaLTimeZero_V68) AS FunctionaLTimeZero_V68			

	, CONVERT(numeric, F.TimeZeroLoc_V66) AS TimeZeroLoc_V66			

	, CONVERT(float, F.Weight_V16) AS Weight_V16			

	, CONVERT(int, F.Bolus1Volume_V21) AS Bolus1Volume_V21			

	, CONVERT(datetime2(0), F.Bolus2Time_V22) AS Bolus2Time_V22			

	, CONVERT(int, F.Bolus2Volume_V23) AS Bolus2Volume_V23			

	, CONVERT(datetime2(0), F.Bolus3Time_V24) AS Bolus3Time_V24			

	, CONVERT(int, F.Bolus3Volume_V25) AS Bolus3Volume_V25			

	, CONVERT(datetime2(0), F.FirstTimeHypotension_V18) AS FirstTimeHypotension_V18			

	, CONVERT(datetime2(0), F.FirstPressorTime_V29) AS FirstPressorTime_V29			

	, CONVERT(numeric, F.FirstPressorType_V30) AS FirstPressorType_V30			

	, CONVERT(numeric, F.OrganDysfunction_V41) AS OrganDysfunction_V41			

	, CONVERT(datetime2(0), F.CVLPlacementTime_V44) AS CVLPlacementTime_V44			

	, CONVERT(datetime2(0), F.SVO2Time_V45) AS SVO2Time_V45			

	, CONVERT(datetime2(0), F.LacticAcidTime_V46) AS LacticAcidTime_V46			

	, CONVERT(float, F.LacticAcidValue_V47) AS LacticAcidValue_V47			

	, CONVERT(numeric, F.BCPositive_V35) AS BCPositive_V35			

	, CONVERT(datetime2(0), F.TimeSurgicalSourceControl_V39) AS TimeSurgicalSourceControl_V39			

	, CONVERT(numeric, F.OutsideHospital_V11) AS OutsideHospital_V11			

	, CONVERT(datetime2(0), F.ED2GenCareTime_V12) AS ED2GenCareTime_V12			

	, CONVERT(datetime2(0), F.ED2HemoncTime_V63) AS ED2HemoncTime_V63			

	, CONVERT(datetime2(0), F.ED2ICUTime_V13) AS ED2ICUTime_V13			

	, CONVERT(datetime2(0), F.GENCARE2ICUTime_V94) AS GENCARE2ICUTime_V94			

	, CONVERT(datetime2(0), F.HEMONC2ICUTime_V64) AS HEMONC2ICUTime_V64			

	, CONVERT(numeric, F.Disposition_V54) AS Disposition_V54 			

	--, CONVERT(date, F.FunctionalTimeZero) AS FunctionalTimeZero			

	, CONVERT(date, F.DispositionDate_V53) AS DispositionDate_V53			

	, CONVERT(numeric, F.ECMO_V48) AS ECMO_V48			

	, CONVERT(float, F.Risk_Score_V52) AS Risk_Score_V52			

	, CONVERT(numeric, F.Risk_Score_Method_V51) AS Risk_Score_Method_V51			

	, CONVERT(varchar, F.HighRiskConditions_1_V65) AS HighRiskConditions_1_V65			

	, CONVERT(varchar, F.HighRiskConditions_2_V65) AS HighRiskConditions_2_V65			

	, CONVERT(varchar, F.HighRiskConditions_3_V65) AS HighRiskConditions_3_V65			

	, CONVERT(varchar, F.HighRiskConditions_4_V65) AS HighRiskConditions_4_V65			

	, CONVERT(varchar, F.HighRiskConditions_95_V65) AS HighRiskConditions_95_V65			

	, CONVERT(varchar, F.HighRiskConditions_6_V65) AS HighRiskConditions_6_V65			

	, CONVERT(varchar, F.HighRiskConditions_7_V65) AS HighRiskConditions_7_V65			

	, CONVERT(varchar, F.HighRiskConditions_98_V65) AS HighRiskConditions_98_V65			

	, CONVERT(varchar, F.HighRiskConditions_88_V65) AS HighRiskConditions_88_V65 			

	, CONVERT(int, F.ABXDays_V42) AS ABXDays_V42			

	, CONVERT(int, F.Pressor_Days_V57) AS Pressor_Days_V57			

	, CASE			

		WHEN F.ICUDays_V58 = 0 OR F.ICUDays_V58 = 99999 THEN F.ICUDays_V58		

		WHEN DATEDIFF(DD,CONVERT(DATE,FunctionalTimeZero), DispositionDate_V53)+1 < F.ICUDays_V58 THEN DATEDIFF(DD,CONVERT(DATE,FunctionalTimeZero), DispositionDate_V53)+1		

		WHEN		

			F.ED2ICUTime_V13 ='1900-01-02 00:00:00'	

			AND 	

			F.GENCARE2ICUTime_V94 ='1900-01-02 00:00:00'	

			AND 	

			F.HEMONC2ICUTime_V64 ='1900-01-02 00:00:00'	

			AND	

			(	

				F.ICUDays_V58 = 99999 OR

				F.ICUDays_V58 = 0

			)	

			THEN 99999	

		ELSE CONVERT(int, F.ICUDays_V58)		

		END AS ICUDays_V58		

	, CONVERT(numeric, F.Pt_Chronically_Vented_V32) AS Pt_Chronically_Vented_V32			

	, CONVERT(int, F.PressureVentDays_V56) AS PressureVentDays_V56			

	, CONVERT(datetime2(0), F.Clinically_Derived_Time_Zero_V09) AS Clinically_Derived_Time_Zero_V09			

	, CONVERT(varchar, F.PAT_ENC_CSN_ID) AS PAT_ENC_CSN_ID			

	, CONVERT(varchar, F.DATE_STAMP) AS DATE_STAMP			

	, CONVERT(bit, F.REVIEWED) AS REVIEWED

	, f.[NACHRI_hosp]

	, f.[bill]

INTO

	#FinalData

FROM

	#FinalTData F

CREATE INDEX IDX_FinalData ON #FinalData (PAT_ENC_CSN_ID) 



-------------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

/* WRITING OR PRINING DATA BASED ON THE INPUT PARAMETER */

IF @TEST = 0

	BEGIN

		INSERT INTO reportingDB.[reports].[SEVERE_SEPSIS_STAGING] 

			([Sepsis_Episode_ID_V01]

			, [Arrival_Time_V10]

			, [Birth_Date_V02]

			, [ScreenTime_V06]

			, [Huddle_Time_V07]

			, [OrderSet_Time_V08]

			, [FirstABXTime_V26]

			, [Bolus1Time_V20]

			, [FunctionaLTimeZero_V68]

			, [TimeZeroLoc_V66]

			, [Weight_V16]

			, [Bolus1Volume_V21]

			, [Bolus2Time_V22]

			, [Bolus2Volume_V23]

			, [Bolus3Time_V24]

			, [Bolus3Volume_V25]

			, [FirstTimeHypotension_V18]

			, [FirstPressorTime_V29]

			, [FirstPressorType_V30]

			, [OrganDysfunction_V41]

			, [CVLPlacementTime_V44]

			, [SVO2Time_V45]

			, [LacticAcidTime_V46]

			, [LacticAcidValue_V47]

			, [BCPositive_V35]

			, [TimeSurgicalSourceControl_V39]

			, [OutsideHospital_V11]

			, [ED2GenCareTime_V12]

			, [ED2HemoncTime_V63]

			, [ED2ICUTime_V13]

			, [GENCARE2ICUTime_V94]

			, [HEMONC2ICUTime_V64]

			, [Disposition_V54]

			, [DispositionDate_V53]

			, [ECMO_V48]

			, [Risk_Score_V52]

			, [Risk_Score_Method_V51]

			, [HighRiskConditions_1_V65]

			, [HighRiskConditions_2_V65]

			, [HighRiskConditions_3_V65]

			, [HighRiskConditions_4_V65]

			, [HighRiskConditions_95_V65]

			, [HighRiskConditions_6_V65]

			, [HighRiskConditions_7_V65]

			, [HighRiskConditions_98_V65]

			, [HighRiskConditions_88_V65]

			, [ABXDays_V42]

			, [Pressor_Days_V57]

			, [ICUDays_V58]

			, [Pt_Chronically_Vented_V32]

			, [PressureVentDays_V56]

			, [Clinically_Derived_Time_Zero_V09]

			, [PAT_ENC_CSN_ID]

			, [DATE_STAMP]

			, [Reviewed]

			, [NACHRI_hosp]

			, [bill])



			SELECT [Sepsis_Episode_ID_V01] 

				, [Arrival_Time_V10] [arrivaltime]

				, [Birth_Date_V02] 

				, [ScreenTime_V06] [screentime]

				, [Huddle_Time_V07] [huddletime]

				, [OrderSet_Time_V08] [ordersettime]

				, [FirstABXTime_V26] [firstantibiotictime]

				, [Bolus1Time_V20] [bolus1time]

				, [FunctionaLTimeZero_V68] [functionaltimezero]

				, [TimeZeroLoc_V66] [timezerolocation]

				, [Weight_V16] 

				, [Bolus1Volume_V21] 

				, [Bolus2Time_V22] [bolus2time]

				, [Bolus2Volume_V23] 

				, [Bolus3Time_V24] [bolus3time]

				, [Bolus3Volume_V25] 

				, [FirstTimeHypotension_V18] [timefirsthypotension]

				, [FirstPressorTime_V29] [firstpressorstarttime]

				, [FirstPressorType_V30] 

				, [OrganDysfunction_V41] 

				, [CVLPlacementTime_V44] 

				, [SVO2Time_V45] 

				, [LacticAcidTime_V46] 

				, [LacticAcidValue_V47] [lacticacidvalue]

				, [BCPositive_V35] [bloodcxpositive]

				, [TimeSurgicalSourceControl_V39] 

				, [OutsideHospital_V11] [outsidehospital]

				, [ED2GenCareTime_V12] 

				, [ED2HemoncTime_V63] 

				, [ED2ICUTime_V13] 

				, [GENCARE2ICUTime_V94] 

				, [HEMONC2ICUTime_V64] 

				, [Disposition_V54] [disposition]

				, [DispositionDate_V53] 

				, [ECMO_V48] 

				, [Risk_Score_V52] 

				, [Risk_Score_Method_V51] 

				, [HighRiskConditions_1_V65] 

				, [HighRiskConditions_2_V65] 

				, [HighRiskConditions_3_V65] 

				, [HighRiskConditions_4_V65] 

				, [HighRiskConditions_95_V65] 

				, [HighRiskConditions_6_V65] 

				, [HighRiskConditions_7_V65] 

				, [HighRiskConditions_98_V65] 

				, [HighRiskConditions_88_V65] 

				, [ABXDays_V42] [totalivabxdays]

				, [Pressor_Days_V57] [pressordays]

				, [ICUDays_V58] [icudays]

				, [Pt_Chronically_Vented_V32] 

				, [PressureVentDays_V56] 

				, [Clinically_Derived_Time_Zero_V09] 

				, [PAT_ENC_CSN_ID] 

				, [DATE_STAMP] 

				, [REVIEWED] 

				, [NACHRI_hosp]

				, [bill]

		FROM

			#FinalData s

			

		SELECT 

			[NACHRI_hosp]

			, [bill]

			, [Arrival_Time_V10] [arrivaltime]

			, [ScreenTime_V06] [screentime]

			, [Huddle_Time_V07] [huddletime]

			, [OrderSet_Time_V08] [ordersettime]

			, [FirstABXTime_V26] [firstantibiotictime]

			, [Bolus1Time_V20] [bolus1time]

			, [FunctionaLTimeZero_V68] [functionaltimezero]

			, [TimeZeroLoc_V66] [timezerolocation]

			, [Bolus2Time_V22] [bolus2time]

			, [Bolus3Time_V24] [bolus3time]

			, [FirstTimeHypotension_V18] [timefirsthypotension]

			, [FirstPressorTime_V29] [firstpressorstarttime]

			, [LacticAcidValue_V47] [lacticacidvalue]

			, [BCPositive_V35] [bloodcxpositive]

			, [OutsideHospital_V11] [outsidehospital]

			, [Disposition_V54] [disposition]

			, [ABXDays_V42] [totalivabxdays]

			, [Pressor_Days_V57] [pressordays]

			, [ICUDays_V58] [icudays]

			, [PAT_ENC_CSN_ID]

		FROM reportingDB.[reports].[SEVERE_SEPSIS_STAGING] s

		WHERE

			DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate))

	END;

ELSE

	BEGIN

		SELECT 

			[NACHRI_hosp]

			, [bill]

			, [Arrival_Time_V10] [arrivaltime]

			, [ScreenTime_V06] [screentime]

			, [Huddle_Time_V07] [huddletime]

			, [OrderSet_Time_V08] [ordersettime]

			, [FirstABXTime_V26] [firstantibiotictime]

			, [Bolus1Time_V20] [bolus1time]

			, [FunctionaLTimeZero_V68] [functionaltimezero]

			, [TimeZeroLoc_V66] [timezerolocation]

			, [Bolus2Time_V22] [bolus2time]

			, [Bolus3Time_V24] [bolus3time]

			, [FirstTimeHypotension_V18] [timefirsthypotension]

			, [FirstPressorTime_V29] [firstpressorstarttime]

			, [LacticAcidValue_V47] [lacticacidvalue]

			, [BCPositive_V35] [bloodcxpositive]

			, [OutsideHospital_V11] [outsidehospital]

			, [Disposition_V54] [disposition]

			, [ABXDays_V42] [totalivabxdays]

			, [Pressor_Days_V57] [pressordays]

			, [ICUDays_V58] [icudays]

			, [PAT_ENC_CSN_ID]



		FROM reportingDB.[reports].[SEVERE_SEPSIS_STAGING]



		WHERE DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate))

	END;

-------------------------------------------------------------------------------------------------------------------------------------------------------

END;

END;

-------------------------------------------------------------------------------------------------------------------------------------------------------

-----------------------------------------------------------END---------------------------------------------------------------------------------------

-----------------------------------------------------------------------------------------------------------------------------------------------------
GO
