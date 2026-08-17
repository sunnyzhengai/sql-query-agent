





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

2019.07.19		V_DEV001				MAR_ACTION_CODE changed data type from INT to VARCHAR.

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

	PEH.ENCOUNTER_ID

	, PEH.PATIENT_ID

	, PAT.PATIENT_MRN

	, PAT.PATIENT_NAME

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

	, PEH.ED_DISPOSITION_CODE

	, ZED.NAME AS [Disposition]

	, LOC.LOCATION_ABBR [Location]

	, FLOOR(DATEDIFF(day,PAT.BIRTH_DATE,PEH.ADT_ARRIVAL_TIME)) AS AGE_IN_DAYS ---ADDED V_DEV003 6/15/2023 TKT-007 

	, FLOOR(DATEDIFF(MM,PAT.BIRTH_DATE,COALESCE(PEH.ADT_ARRIVAL_TIME,PEH.ADT_ARRIVAL_TIME)) ) AS AGE_MONTHS  ---ADDED V_DEV003 6/15/2023 TKT-007  (AGE IN MONTHS IS SHOWING AS 1 WHEN ITS ONLY 2 WEEKS, ETC.)

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,PEH.ADT_ARRIVAL_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,PEH.ADT_ARRIVAL_TIME)) + DATENAME(YEAR, CONVERT(DATE, PEH.ADT_ARRIVAL_TIME)) AS DATE_STAMP



INTO #Base_Pop



FROM [EMRDB].[dbo].ED_ENCOUNTERS_FACT FEE



	INNER JOIN [EMRDB].[dbo].HOSPITAL_ENCOUNTERS PEH ON FEE.ENCOUNTER_ID = PEH.ENCOUNTER_ID

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.ENCOUNTER_ID = FEE.ENCOUNTER_ID

	INNER JOIN [EMRDB].[dbo].PATIENTS PAT ON PAT.PATIENT_ID = PEH.PATIENT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ED_DISPOSITION ZED ON ZED.ED_DISPOSITION_CODE = PEH.ED_DISPOSITION_CODE

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ETHNIC_GROUP ZEG ON ZEG.ETHNIC_GROUP_CODE = PAT.ETHNIC_GROUP_CODE

	LEFT OUTER JOIN [EMRDB].[dbo].PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PATIENT_ID = PAT.PATIENT_ID AND RACE.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].REF_PATIENT_RACE ZPR ON ZPR.PATIENT_RACE_CODE = RACE.PATIENT_RACE_CODE

	LEFT OUTER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = PEH.DEPARTMENT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].LOCATIONS LOC ON LOC.LOC_ID = DEP.REV_LOC_ID



WHERE FEE.ADT_ARRIVAL_DATE BETWEEN @dStartDate AND @dEndDate

;



CREATE NONCLUSTERED INDEX INX_BASE_POP_ENC ON #Base_Pop ([ENCOUNTER_ID]);









/* ****************************************************************************************************************



													MEDICATIONS



******************************************************************************************************************/



-- All (intravenous) medications given prior to ED departure (used for Abx, Bolus, Pressors tables)

SELECT

	OM.ENCOUNTER_ID

	, OM.ORDER_MED_ID

	, MAI.TAKEN_TIME

	, [ERX].[NAME] AS MEDICATION_NAME

	, [ERX].THERA_CLASS_CODE

	, OM.MED_ROUTE_CODE

	, MAI.MAR_ACTION_CODE

	, OM.MEDICATION_ID

	, OM.HV_DISCR_FREQ_ID

	, MAI.SIG

	, B.ADT_ARRIVAL_TIME

	, B.ED_DEPARTURE_TIME



INTO #AllMeds



FROM #Base_Pop B

	INNER JOIN EMRDB.dbo.MEDICATION_ORDERS OM ON OM.ENCOUNTER_ID = B.ENCOUNTER_ID

	INNER JOIN EMRDB.dbo.MEDICATIONS ERX ON [ERX].MEDICATION_ID = OM.MEDICATION_ID

	INNER JOIN EMRDB.dbo.MED_ADMIN_RECORDS MAI ON MAI.ORDER_MED_ID = OM.ORDER_MED_ID



WHERE 1=1

	AND MAI.TAKEN_TIME IS NOT NULL

	AND MAI.TAKEN_TIME < B.ED_DEPARTURE_TIME	-- while in ED

	AND MED_ROUTE_CODE = 11 -- intravenous

	AND MAR_ACTION_CODE IN ('1'		--GIVEN

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

		ENCOUNTER_ID

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

										comp.SIMPLE_GENERIC_CODE 

									FROM [EMRDB].[dbo].MED_MIX_COMPONENTS mix

										INNER JOIN [EMRDB].[dbo].MEDICATIONS comp ON mix.DRUG_ID = comp.MEDICATION_ID

									WHERE 1=1

										AND mix.TYPE_CODE = 3 -- Medications 

										AND mix.MEDICATION_ID = erx.MEDICATION_ID

									ORDER BY

										mix.LINE

								) mixture



								INNER JOIN [EMRDB].[dbo].REF_GENERIC_MED		gen ON gen.SIMPLE_GENERIC_CODE = COALESCE(erx.SIMPLE_GENERIC_CODE, mixture.SIMPLE_GENERIC_CODE)

								INNER JOIN [reportingDB].[reports].CONFIG_VALUE_SET cntl ON cntl.VALUE_SET_ID=3016 AND cntl.CODE = gen.SIMPLE_GENERIC_CODE

						) medlist

					WHERE

						medlist.AGENT_ORDER=1						

			)



	UNION



	SELECT DISTINCT

		ENCOUNTER_ID

		, ORDER_MED_ID

		, TAKEN_TIME AS ABX_ADMIN_TIME

		, MEDICATION_NAME



	FROM #AllMeds



	WHERE 1=1

		AND THERA_CLASS_CODE = 11 --Antibiotics

		AND TAKEN_TIME < ED_DEPARTURE_TIME	-- including prior to "Arrival"

)



SELECT

	ENCOUNTER_ID

	,ORDER_MED_ID

	,MEDICATION_NAME

	,ABX_ADMIN_TIME

	,ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY ABX_ADMIN_TIME) TIME_LINE



INTO #BasePopABX

FROM ABX						

;





/* ******************* */

/* Bolus               */

/* ******************* */

DROP TABLE IF EXISTS #BasePopBolus;



SELECT

	ENCOUNTER_ID

	, TAKEN_TIME AS BOLUS_ADMIN_TIME

	, CASE	WHEN MEDICATION_ID IN (700001, 700002) THEN 'SODIUM CHLORIDE 0.99%'

			ELSE MEDICATION_NAME

	  END AS Medication

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY TAKEN_TIME ASC) AS TIME_LINE

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

	ENCOUNTER_ID

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

	ENCOUNTER_ID

	, TAKEN_TIME

	, MEDICATION_NAME

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY TAKEN_TIME) AS TIME_LINE

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

	A.ENCOUNTER_ID

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

			WHERE	ORD_CNTCT_TYPE_CODE = 4 --VERIFY

		) VERIFY ON ord.ORDER_MED_ID = VERIFY.ORDER_MED_ID AND VERIFY.MYLINE = 1



	INNER JOIN

		(

			SELECT	ORDER_MED_ID, ACTION_INSTANT, VERIFY_CONTDATREAL, CONTACT_DATE_REAL, CONTACT_DATE, ROW_NUMBER() OVER(PARTITION BY ORDER_MED_ID ORDER BY ACTION_INSTANT ASC) AS MYLINE

			FROM	[EMRDB].[dbo].ORDER_DISPENSE_INFO

			WHERE	ORD_CNTCT_TYPE_CODE = 95 --DISPENSE

		) DISPENSE ON ord.ORDER_MED_ID = DISPENSE.ORDER_MED_ID AND DISPENSE.MYLINE = 1

					AND VERIFY.CONTACT_DATE_REAL = DISPENSE.VERIFY_CONTDATREAL

					AND DISPENSE.ACTION_INSTANT<A.ABX_ADMIN_TIME --MAKE SURE WE ARE LOOKING AT THE RIGHT MEDICATION ADMIN TIME. A MEDICATION ORDER COULD HAVE MULTIPLE DISPENSES

	

	/* Dispense */

	LEFT OUTER JOIN [EMRDB].[dbo].V_PHARMACY_DISPENSE disp on DISPENSE.ORDER_MED_ID = disp.ORDER_MED_ID and DISPENSE.CONTACT_DATE_REAL = disp.CONTACT_DATE_REAL



	LEFT OUTER JOIN 

		(

			SELECT	ACTION_ID, ACTION_DTTM, ROW_NUMBER() OVER(PARTITION BY ACTION_ID ORDER BY ACTION_DTTM ASC) AS MYLINE 

			FROM	[EMRDB].[dbo].V_PHARMACY_DISPENSE_ACTION

			WHERE	ACTION_TYPE_CODE=270

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

	, [#Base_Pop].ENCOUNTER_ID

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

	ENCOUNTER_ID

	, CAST(ROUND(CONVERT(FLOAT, MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

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

		ENCOUNTER_ID

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

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO #Hypotension 

FROM Systolic

WHERE HYPOTENSION_Y = 'Y'

;



/* ************** */

/* Blood Pressure */

/* ************** */

SELECT 

	ENCOUNTER_ID

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



CREATE NONCLUSTERED INDEX INX_BLD_MMHG_ENC ON #Base_Pop ([ENCOUNTER_ID]);





/* ********************** */

/* Sepsis CLINICAL_ALERTS Cancelled */

/* ********************** */

DROP TABLE IF EXISTS #SepsisAlertCancelled;



SELECT 

	ENCOUNTER_ID

	, RECORDED_TIME	AS SEPSIS_ALERT_CANC_TIME

	, 'Y'			AS SEPSIS_ALERT_CANC_FLAG

	, MEAS_COMMENT	AS SEPSIS_ALERT_CANC_BY		-- Free text

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

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

	ENCOUNTER_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

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

	ENCOUNTER_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO #ED_PositiveScores

FROM #Base_Pop_Severe_ED_Scores

WHERE MEAS_VALUE > 4

;



/* ******************* */

/* Negative Sepsis     */

/* ******************* */

DROP TABLE IF EXISTS #ED_NegativeScores;



SELECT

	ENCOUNTER_ID

	, MEAS_VALUE

	, RECORDED_TIME

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS FIRST_TIME_LINE

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY RECORDED_TIME DESC) AS LAST_TIME_LINE

INTO #ED_NegativeScores

FROM #Base_Pop_Severe_ED_Scores

WHERE 1=1

	AND MEAS_VALUE <= 4

	AND NOT EXISTS (SELECT 1 FROM #ED_PositiveScores WHERE #ED_PositiveScores.ENCOUNTER_ID = #Base_Pop_Severe_ED_Scores.ENCOUNTER_ID)

;



/* ************************ */

/* Severe + Positive Sepsis */

/* ************************ */

DROP TABLE IF EXISTS #Base_Pop_SepsisScores_ConCat;



SELECT DISTINCT 

	[CAT].ENCOUNTER_ID

    , STUFF((

				SELECT ',' + CONVERT(VARCHAR,SUB.MEAS_VALUE)

				FROM #Base_Pop_Severe_ED_Scores SUB

				WHERE SUB.ENCOUNTER_ID = [CAT].ENCOUNTER_ID

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

		[#Base_Pop].ENCOUNTER_ID

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

		INNER JOIN [EMRDB].[dbo].LINE_DEVICE_AIRWAY ILN ON ILN.ENCOUNTER_ID = [#Base_Pop].ENCOUNTER_ID

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

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, LDA_PLACEMENT_TYPE ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

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

--	ENCOUNTER_ID,

--	IP_LDA_ID,

--	PLACEMENT_INSTANT,

--	ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

--INTO #ETT

--FROM #LDAs

--WHERE FLO_MEAS_ID = '900112' -- LDA HS IP ETT

--;





--/* ******************* */

--/* IV Placement        */

--/* ******************* */

--DROP TABLE IF EXISTS #IV;



--SELECT

--	ENCOUNTER_ID,

--	IP_LDA_ID,

--	PLACEMENT_INSTANT,

--	ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

--INTO #IV

--FROM #LDAs

--WHERE FLO_MEAS_ID = '900111' --LDA HS IP PERIPHERAL IV

--;





--/* ******************* */

--/* CVL Time            */

--/* ******************* */

--DROP TABLE IF EXISTS #ALLCVLTime;



--SELECT DISTINCT

--	ENCOUNTER_ID

--	, PLACEMENT_INSTANT

--	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

--INTO #ALLCVLTime

--FROM #LDAs

--WHERE VALUE_SET_ID = 3022	-- SEPSIS_CVL_PLACEMENT

--;







/* ****************************************************************************************************************



													Labs



******************************************************************************************************************/



SELECT

	[#Base_Pop].ENCOUNTER_ID

	, OP.PROC_ID

	, OP.ORDER_TIME AS MBOrderTime

	, OP.SPECIMEN_SOURCE_CODE

	, LAB_ORDER_RESULTS.RESULT_TIME

	, LAB_ORDER_RESULTS.COMP_OBS_INST_TM AS CollectionTime

	, LAB_ORDER_RESULTS.ORD_VALUE

	--, ROW_NUMBER() OVER(PARTITION BY [#Base_Pop].ENCOUNTER_ID ORDER BY OP.ORDER_TIME ASC) AS TIME_LINE

	, LAB_ORDER_RESULTS.ORDER_PROC_ID

	, LAB_ORDER_RESULTS.COMPONENT_ID

	, LAB_ORDER_RESULTS.RESULT_FLAG_CODE

	, CASE WHEN LAB_ORDER_RESULTS.RESULT_FLAG_CODE IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01 -- Abnormal or Critical

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

	INNER JOIN [EMRDB].[dbo].LAB_ORDER_RESULTS ON [#Base_Pop].ENCOUNTER_ID = LAB_ORDER_RESULTS.ENCOUNTER_ID

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

				OP.SPECIMEN_SOURCE_CODE = 304	-- Lumber puncture

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

		, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, LAB_TEST_TYPE ORDER BY MBOrderTime ASC) AS TIME_LINE

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

		ENCOUNTER_ID

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

		ENCOUNTER_ID

		, CULTURE_TYPE



		, MIN(MBOrderTime)		AS [MBOrderTime]

		, MIN(CollectionTime)	AS [CollectionTime]



		, COALESCE(STRING_AGG(OrganismName, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM AllCultures

	GROUP BY ENCOUNTER_ID, CULTURE_TYPE

	HAVING MAX(CRITICAL_VALUE_01) = 1	-- any positives

)



, NegativeCultures AS

(

	SELECT

		ENCOUNTER_ID

		, CULTURE_TYPE



		, MIN(MBOrderTime)		AS [MBOrderTime]

		, MIN(CollectionTime)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]



	FROM AllCultures

	GROUP BY ENCOUNTER_ID, CULTURE_TYPE

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

	[#Base_Pop].ENCOUNTER_ID

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

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS ADT01 ON [ADT01].ENCOUNTER_ID =  [#Base_Pop].ENCOUNTER_ID

	INNER JOIN [EMRDB].[dbo].ADT_EVENTS ADT02 ON [ADT01].XFER_IN_EVENT_ID = [ADT02].EVENT_ID

	INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON [DEP].DEPARTMENT_ID = [ADT02].DEPARTMENT_ID



WHERE 1=1

	-- Transferred out of Emergency

	AND [ADT01].EVENT_TYPE_CODE = 4		--TRANSFER OUT

	AND [ADT01].EVENT_SUBTYPE_CODE <> 2	--CANCELED

	AND [ADT01].DEPARTMENT_ID IN (200108022) -- Emergency 



	-- Transferred into XXX

	AND [ADT02].EVENT_TYPE_CODE = 3		--TRANSFER IN

	AND [ADT02].EVENT_SUBTYPE_CODE <> 2	--CANCELED

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

	ENCOUNTER_ID

	, DEPARTMENT_NAME

	, EFFECTIVE_TIME AS ED2HemoncTime

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY EFFECTIVE_TIME ASC) AS TIME_LINE

INTO #ED2HEMONC

FROM #ADT

WHERE DEPT_GROUP = 'HemOnc'

;



/* ******************* */

/* ICU                 */

/* ******************* */

DROP TABLE IF EXISTS #ED2ICU;



SELECT

	ENCOUNTER_ID

	, DEPARTMENT_NAME

	, EFFECTIVE_TIME AS ED2ICUTime

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY EFFECTIVE_TIME ASC) AS TIME_LINE

INTO #ED2ICU

FROM #ADT

WHERE DEPT_GROUP = 'ICU'

;





/* ******************* */

/* Gen Care            */

/* ******************* */

DROP TABLE IF EXISTS #ED2GEN;



SELECT

	ENCOUNTER_ID

	, [#ADT].DEPARTMENT_NAME

	, [#ADT].EFFECTIVE_TIME AS ED2GENTime

	, [GEN2ICU].EFFECTIVE_TIME AS [Gen Back To ICU Time]

	, [GEN2ICU].DEPARTMENT_NAME AS [Gen Back To ICU Department]



	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY [#ADT].EFFECTIVE_TIME ASC) AS TIME_LINE



INTO #ED2GEN

FROM #ADT



	OUTER APPLY	--09.09.2020 V_DEV001 added this to check for PATIENTS who went from ED --> Gen Care and then back to ICU within 24 hours

	(

		SELECT TOP 1 ICU.EFFECTIVE_TIME, DEP.DEPARTMENT_NAME

		FROM #ADT ICU

			INNER JOIN [EMRDB].[dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = ICU.DEPARTMENT_ID

		WHERE 1=1

			AND [#ADT].ENCOUNTER_ID = [ICU].ENCOUNTER_ID

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

	B.ENCOUNTER_ID,

	ALT.ALT_ID,

	AH.ALT_ACTION_INST,

	ZAS.[NAME] AS ALERT_STATUS,

	ZSP.[NAME] AS ALERT_SHOWN_PLACE,

	ZAAT.[NAME] AS ACTION_TAKE,

	ROW_NUMBER() OVER(PARTITION BY B.ENCOUNTER_ID ORDER BY AH.ALT_ACTION_INST) AS TIME_LINE,

	ZASOR.[NAME] AS OVERRIDDEN,

	ah.SPEC_OVR_CMNT,

	EMP.[NAME]

INTO #BPA

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].CLINICAL_ALERTS ALT ON ALT.VISIT_ID = B.ENCOUNTER_ID AND ALT.BPA_LOCATOR_ID = '900130001'

	INNER JOIN [EMRDB].[dbo].ALERT_HISTORY AH ON AH.ALT_ID = ALT.ALT_ID

	LEFT OUTER JOIN [EMRDB].[dbo].ALERT_ACTIONS ACA ON ACA.ALT_ENCOUNTER_ID = AH.ALT_ENCOUNTER_ID AND ACA.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_ACTIONS ZAAT ON ZAAT.ALT_ACTION_TAKEN_CODE = ACA.ACTION_TAKEN_CODE

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_OVERRIDE_REASONS ZASOR ON ZASOR.ALRT_SP_OVR_RSN_CODE = AH.SPEC_OVR_RSN_CODE

	LEFT OUTER JOIN [EMRDB].[dbo].REF_ALERT_STATUS ZAS ON ZAS.ALT_STATUS_CODE = AH.ALT_STATUS_CODE

	LEFT OUTER JOIN [EMRDB].[dbo].REF_SHOWN_PLACE ZSP ON ZSP.SHOWN_PLACE_CODE = AH.SHOWN_PLACE_CODE

	LEFT OUTER JOIN [EMRDB].[dbo].EMPLOYEES EMP ON EMP.[USER_ID] = AH.[USER_ID]

WHERE AH.ALT_ACTION_INST BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME

;



/* ********** */

/* Bed Events */

/* ********** */

DROP TABLE IF EXISTS #BedEvents;



SELECT

	B.ENCOUNTER_ID, C.RECORD_NAME AS [EVENT], EIEI.EVENT_TYPE AS [EVENT ID],EIEI.EVENT_TIME,

	ROW_NUMBER() OVER(PARTITION BY B.ENCOUNTER_ID ORDER BY EIEI.EVENT_TIME ) AS TIME_LINE,

	ROW_NUMBER() OVER(PARTITION BY B.ENCOUNTER_ID, EIEI.EVENT_TYPe ORDER BY EIEI.EVENT_TIME ) AS REQ_LINE --JUST IN CASE IF THERE IS MORE THAN ONE EVENT OF THE SAME EVENT_TYPE.

INTO #BedEvents

FROM #Base_Pop B

	INNER JOIN [EMRDB].[dbo].ED_PATIENT_INFO EIPI ON EIPI.ENCOUNTER_ID = B.ENCOUNTER_ID

	INNER JOIN [EMRDB].[dbo].ED_EVENT_INFO EIEI ON EIEI.EVENT_ID = EIPI.EVENT_ID AND EIEI.EVENT_TYPE IN ('2600000347','2600000346')

	INNER JOIN [EMRDB].[dbo].ED_EVENT_TEMPLATES C ON EIEI.EVENT_TYPE = C.RECORD_ID

;



/* ************ */

/* Readmissions */

/* ************ */

DROP TABLE IF EXISTS #Base_Pop_ED_Readmit_All;



SELECT DISTINCT [#Base_Pop].ENCOUNTER_ID

INTO #Base_Pop_ED_Readmit_All

FROM #Base_Pop

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PATIENT_ID = [#Base_Pop].PATIENT_ID 

											AND DEE.ARRIVAL_DTTM BETWEEN ED_DEPARTURE_TIME AND DATEADD(HH, 24, ED_DEPARTURE_TIME)

;



/* *********************************** */

/* Readmissions (positive sepsis only) */

/* *********************************** */

DROP TABLE IF EXISTS #Base_Pop_ED_Readmit;



SELECT DISTINCT [#Base_Pop].ENCOUNTER_ID

INTO #Base_Pop_ED_Readmit

FROM #ED_PositiveScores

	INNER JOIN #Base_Pop ON [#ED_PositiveScores].ENCOUNTER_ID = [#Base_Pop].ENCOUNTER_ID

	INNER JOIN [EMRDB].[dbo].ED_ENCOUNTERS_DM DEE ON DEE.PATIENT_ID = [#Base_Pop].PATIENT_ID 

											AND DEE.ARRIVAL_DTTM BETWEEN [#Base_Pop].ED_DEPARTURE_TIME AND DATEADD(HH, 24, [#Base_Pop].ED_DEPARTURE_TIME)

WHERE [#ED_PositiveScores].FIRST_TIME_LINE= 1 

;



/* **************** */

/* PATIENTS Location */

/* **************** */

SELECT 

	ENCOUNTER_NUM

	, IN_DTTM

	, ADT_DEPARTMENT_NAME

INTO #PatientLocation

FROM [EMRDB].[dbo].V_PATIENT_LOCATION_HISTORY

WHERE 1=1

	AND [V_PATIENT_LOCATION_HISTORY].ADT_DEPARTMENT_ID IS NOT NULL

	AND EXISTS (SELECT 1 FROM #Base_Pop WHERE [#Base_Pop].ENCOUNTER_ID = [V_PATIENT_LOCATION_HISTORY].ENCOUNTER_NUM)

;



CREATE NONCLUSTERED INDEX INX_ADT_LOC ON #PatientLocation (ENCOUNTER_NUM);



/* ******************************************* */

/* Time from First Positive Score -> First Abx */

/* ******************************************* */

DROP TABLE IF EXISTS #FirstPositiveOD_To_ABXAdminTime;



SELECT

	[subQ].ENCOUNTER_ID

	,[subQ].MEDICATION

	,[subQ].ABX_ADMIN_TIME

	,[subQ].RECORDED_TIME,

	DATEDIFF(MI, [subQ].RECORDED_TIME, [subQ].ABX_ADMIN_TIME) AS POSOD2ABX



INTO #FirstPositiveOD_To_ABXAdminTime



FROM 

	(

		SELECT 

			[#BasePopABX].ENCOUNTER_ID

			, [#BasePopABX].MEDICATION_NAME AS MEDICATION

			, [#BasePopABX].ABX_ADMIN_TIME

			, [#ED_PositiveScores].MEAS_VALUE

			, [#ED_PositiveScores].RECORDED_TIME

			, ROW_NUMBER() OVER(PARTITION BY [#BasePopABX].ENCOUNTER_ID ORDER BY [#BasePopABX].ABX_ADMIN_TIME ASC) AS MYLINE

		FROM #BasePopABX

			INNER JOIN #ED_PositiveScores ON [#BasePopABX].ENCOUNTER_ID = [#ED_PositiveScores].ENCOUNTER_ID

										AND [#ED_PositiveScores].RECORDED_TIME < [#BasePopABX].ABX_ADMIN_TIME

										AND [#ED_PositiveScores].FIRST_TIME_LINE=1

	) subQ

WHERE [subQ].MYLINE=1

;



/* ********************** */

/* Chief Complaints (all) */

/* ********************** */

DROP TABLE IF EXISTS #Base_Pop_ENC_Reason;



SELECT DISTINCT   CAT.ENCOUNTER_ID,

        STUFF((	SELECT ';' + CONVERT(VARCHAR,CRFV.REASON_VISIT_NAME)-- AS [text()]

                FROM #Base_Pop SUB

					INNER JOIN [EMRDB].[dbo].ENCOUNTER_VISIT_REASONS RSN ON RSN.ENCOUNTER_ID = SUB.ENCOUNTER_ID AND RSN.LINE>1

					INNER JOIN [EMRDB].[dbo].VISIT_REASONS CRFV ON CRFV.REASON_VISIT_ID = RSN.ENC_REASON_ID

				WHERE

                    SUB.ENCOUNTER_ID = CAT.ENCOUNTER_ID

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



SELECT DISTINCT ENCOUNTER_ID

INTO #ED_BORDER

FROM [EMRDB].[dbo].ED_PATIENT_INFO

	INNER JOIN [EMRDB].[dbo].ED_EVENT_INFO	 ON [ED_EVENT_INFO].EVENT_ID = [ED_PATIENT_INFO].EVENT_ID

WHERE 1=1

	AND EXISTS (SELECT 1 FROM #Base_Pop WHERE [#Base_Pop].ENCOUNTER_ID = [ED_PATIENT_INFO].ENCOUNTER_ID)

	AND [ED_EVENT_INFO].EVENT_TYPE IN ('2600000007')--ED BOARDER PATIENTS

;



/* ******************* */

/* Order Set           */

/* ******************* */

DROP TABLE IF EXISTS #SSOrderSet;



WITH OrderMetricIDs AS

(

	SELECT

		[#Base_Pop].ENCOUNTER_ID

		, ORDER_ID

		, ORDER_DTTM

		, PRL_ORDERSET_ID

	FROM #Base_Pop

		INNER JOIN [EMRDB].[dbo].ORDER_TRACKING_METRICS ON [ORDER_TRACKING_METRICS].ENCOUNTER_ID = [#Base_Pop].ENCOUNTER_ID

	WHERE [ORDER_TRACKING_METRICS].ORDER_DTTM BETWEEN [#Base_Pop].ADT_ARRIVAL_TIME AND [#Base_Pop].ED_DEPARTURE_TIME

)



, SSOrderSetOSQ_PRL AS

(

	-- OSQ

	SELECT

		[OrderMetricIDs].ENCOUNTER_ID

		, [OrderMetricIDs].ORDER_DTTM

		, [MEDICATION_ORDERS_EXT].ORD_OSQ_ID AS PRL_ORDERSET_ID

	FROM OrderMetricIDs

		INNER JOIN [EMRDB].[dbo].MEDICATION_ORDERS_EXT ON [OrderMetricIDs].ORDER_ID = [MEDICATION_ORDERS_EXT].ORDER_ID AND [MEDICATION_ORDERS_EXT].ORD_OSQ_ID IN (400002,400007,400003,400004,400006,400005,4001326025)



	UNION



		SELECT

			[OrderMetricIDs].ENCOUNTER_ID

			, [OrderMetricIDs].ORDER_DTTM

			, [PROCEDURE_ORDERS_EXT].ORD_OSQ_ID AS PRL_ORDERSET_ID

		FROM OrderMetricIDs

			INNER JOIN [EMRDB].[dbo].PROCEDURE_ORDERS_EXT ON [OrderMetricIDs].ORDER_ID =  [PROCEDURE_ORDERS_EXT].ORDER_ID AND [PROCEDURE_ORDERS_EXT].ORD_OSQ_ID IN (400002,400007,400003,400004,400006,400005,4001326025)



	UNION



		SELECT

			[OrderMetricIDs].ENCOUNTER_ID

			, [OrderMetricIDs].ORDER_DTTM

			, [OrderMetricIDs].PRL_ORDERSET_ID

		FROM OrderMetricIDs

		-- see VCG 800018 -- HS BI SEPSIS PRL ORDERSETS (the entire Grouper is used by IPSO Severe Sepsis; ED Sepsis only uses ED-specific PRLs)

		WHERE [OrderMetricIDs].PRL_ORDERSET_ID IN (400001, 4001326023) -- Sepsis Pathway [400001]; HS ED ONCOLOGY SEPSIS RN PROTOCOL OPA [4001326023]

)



SELECT

	ENCOUNTER_ID

	, ORDER_DTTM

	, PRL_ORDERSET_ID

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY ORDER_DTTM ASC) AS TIME_LINE

INTO #SSOrderSet 

FROM SSOrderSetOSQ_PRL

;



-- @99:48 mins





/* ****************************************************************************************************************



												FINAL QUERY



******************************************************************************************************************/

SELECT

	[BasePop].PATIENT_MRN		AS MRN

	,[BasePop].PATIENT_NAME			AS PATIENTS

	,[BasePop].[Ethnic Group]

	,[BasePop].[Race]

	,[BasePop].ENCOUNTER_ID	AS ENC_ID

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



	--,CASE WHEN SepsisScreened.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END AS [Sepsis Screened 01]	-- Why is this needed?

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

	, CASE WHEN [#BPA].ALT_ACTION_INST IS NOT NULL THEN ISNULL([#SepsisAlertCancelled].SEPSIS_ALERT_CANC_FLAG, 'N') END AS [SEPSIS_ALERT_CANC_FLAG]



	/* Blood pressure */

	, CASE WHEN EXISTS (SELECT 1 FROM #BloodPressure WHERE [#BloodPressure].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID AND [#BloodPressure].FLO_MEAS_ID = '95') THEN 'Y' ELSE 'N' END AS [Any BP During ED Stay?]



	, BE1.EVENT_TIME AS [ED IP Bed Requested Time]

	, BE2.EVENT_TIME AS [ED IP Bed Assigned Time]

	, DATEDIFF(MI,BE1.EVENT_TIME,BE2.EVENT_TIME) AS [Bed Request to Bed Assigned Time]

	, DATEDIFF(MI,BE1.EVENT_TIME, ICU.ED2ICUTime) AS [IP Bed Request to PICU Transfer Time]



	, CASE WHEN EXISTS (SELECT 1 FROM #ED_BORDER WHERE [#ED_BORDER].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID) THEN 'Y' ELSE 'N' END	AS [ED Border PATIENTS]

	, CASE WHEN READMIT.ENCOUNTER_ID IS NOT NULL THEN 'Y' ELSE 'N' END	AS [Sepsis Pos ED Readmit in 24Hrs]

	, CASE WHEN READMITALL.ENCOUNTER_ID IS NOT NULL THEN 'Y' ELSE 'N' END AS [ED Readmit in 24Hrs]

	, CASE WHEN SEVERE.ENCOUNTER_ID IS NOT NULL THEN 'Y' ELSE 'N' END		AS [IPSO Severe Sepsis Criteria Met]

	, CASE WHEN NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 'Y' ELSE 'N' END	AS [IPSO Non Severe Sepsis Criteria Met]

 

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

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END					AS [IPSO SEVERE and Positive Sepsis and Blood Culture NOT Ordered]



	/* IPSO non-severe (+) and Sepsis (+) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO NON SEVERE and Positive Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Positive Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Positive Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NOT NULL AND [BLD].MBOrderTime IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO NON SEVERE and Positive Sepsis and Blood Culture NOT Ordered]



	/* IPSO severe (+) and Sepsis (neg) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO SEVERE and Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO SEVERE and Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO SEVERE and Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NULL AND SEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO SEVERE and Negative Sepsis and Blood Culture NOT Ordered]



	/* IPSO non-severe (+) and Sepsis (neg) */

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END	AS [IPSO NON SEVERE and Negative Sepsis and OrderSet Placed]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [#SSOrderSet].ORDER_DTTM IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and OrderSet NOT Placed]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and Abx Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND ABX1.ABX_ADMIN_TIME IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Abx NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END		AS [IPSO NON SEVERE and Negative Sepsis and Bolus Administered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND BPB1.BOLUS_ADMIN_TIME IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Bolus NOT Administered]



	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NOT NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END			AS [IPSO NON SEVERE and Negative Sepsis and Blood Culture Ordered]

	,CASE WHEN [#ED_PositiveScores].MEAS_VALUE IS NULL AND ALLSCORES.AllSepsis_Scores IS NOT NULL AND [BLD].MBOrderTime IS NULL AND NONSEVERE.ENCOUNTER_ID IS NOT NULL THEN 1 ELSE 0 END				AS [IPSO NON SEVERE and Negative Sepsis and Blood Culture NOT Ordered]



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



	LEFT OUTER JOIN [EMRDB].[dbo].ENCOUNTER_VISIT_REASONS	CHIEF_CMPLNT	ON CHIEF_CMPLNT.ENCOUNTER_ID = [BasePop].ENCOUNTER_ID AND CHIEF_CMPLNT.LINE=1

	LEFT OUTER JOIN [EMRDB].[dbo].VISIT_REASONS	CRFV			ON CRFV.REASON_VISIT_ID = CHIEF_CMPLNT.ENC_REASON_ID



	LEFT OUTER JOIN [reportingDB].[reports].[SEVERE_SEPSIS_STAGING]		SEVERE		ON SEVERE.DATE_STAMP = [BasePop].DATE_STAMP AND SEVERE.ENCOUNTER_ID = [BasePop].ENCOUNTER_ID

	LEFT OUTER JOIN [reportingDB].[reports].[NON_SEVERE_SEPSIS_STAGING]	NONSEVERE	ON NONSEVERE.DATE_STAMP = [BasePop].DATE_STAMP AND NONSEVERE.ENCOUNTER_ID = [BasePop].ENCOUNTER_ID



	LEFT OUTER JOIN #Base_Pop_SepsisScores_ConCat	ALLSCORES		ON ALLSCORES.ENCOUNTER_ID = [BasePop].ENCOUNTER_ID

	LEFT OUTER JOIN #Base_Pop_Severe_ED_Scores		SepsisScreened	ON SepsisScreened.ENCOUNTER_ID = [BasePop].ENCOUNTER_ID and SepsisScreened.TIME_LINE=1



	LEFT OUTER JOIN #ED_PositiveScores							ON [#ED_PositiveScores].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID AND [#ED_PositiveScores].FIRST_TIME_LINE=1

	LEFT OUTER JOIN #ED_NegativeScores							ON [#ED_NegativeScores].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID AND [#ED_NegativeScores].FIRST_TIME_LINE=1



	-- Medications

	LEFT OUTER JOIN #BasePopABX						abx1		ON [BasePop].ENCOUNTER_ID = ABX1.ENCOUNTER_ID AND ABX1.TIME_LINE=1

	LEFT OUTER JOIN #BasePopABX						abx2		ON [BasePop].ENCOUNTER_ID = ABX2.ENCOUNTER_ID AND ABX2.TIME_LINE=2

	LEFT OUTER JOIN #BasePopBolus					BPB1		ON [BasePop].ENCOUNTER_ID = BPB1.ENCOUNTER_ID AND BPB1.TIME_LINE=1

	LEFT OUTER JOIN #BasePopBolus					BPB2		ON [BasePop].ENCOUNTER_ID = BPB2.ENCOUNTER_ID AND BPB2.TIME_LINE=2

	LEFT OUTER JOIN #BasePopBolus					BPB3		ON [BasePop].ENCOUNTER_ID = BPB3.ENCOUNTER_ID AND BPB3.TIME_LINE=3

	LEFT OUTER JOIN #Pressors									ON [BasePop].ENCOUNTER_ID = [#Pressors].ENCOUNTER_ID AND [#Pressors].TIME_LINE=1

	LEFT OUTER JOIN #FirstABXAdminTimeDetails		ABXTimes	ON ABXTimes.ENCOUNTER_ID = [BasePop].ENCOUNTER_ID



	-- Flowsheets

	LEFT OUTER JOIN #EncounterWeights				EW			ON [BasePop].ENCOUNTER_ID = EW.ENCOUNTER_ID AND EW.TIME_LINE=1

	LEFT OUTER JOIN #Hypotension								ON [BasePop].ENCOUNTER_ID = [#Hypotension].ENCOUNTER_ID AND [#Hypotension].TIME_LINE=1



	-- LDAs

	LEFT OUTER JOIN #LDA							ETT			ON [BasePop].ENCOUNTER_ID = [ETT].ENCOUNTER_ID AND [ETT].LDA_PLACEMENT_TYPE = 'ETT'

	LEFT OUTER JOIN #LDA							IV			ON [BasePop].ENCOUNTER_ID = [IV].ENCOUNTER_ID AND [IV].LDA_PLACEMENT_TYPE = 'IV'

	LEFT OUTER JOIN #LDA							CVL			ON [BasePop].ENCOUNTER_ID = [CVL].ENCOUNTER_ID AND [CVL].LDA_PLACEMENT_TYPE = 'CVL'



	-- Labs and Cultures

	LEFT OUTER JOIN #Labs							SPO2		ON [BasePop].ENCOUNTER_ID = [SPO2].ENCOUNTER_ID AND [SPO2].LAB_TEST_TYPE = 'O2 Saturation'

	LEFT OUTER JOIN #Labs							LAC			ON [BasePop].ENCOUNTER_ID = [LAC].ENCOUNTER_ID AND [LAC].LAB_TEST_TYPE = 'Lactic Acid'

	LEFT OUTER JOIN #Labs							PCT			ON [BasePop].ENCOUNTER_ID = [PCT].ENCOUNTER_ID AND [PCT].LAB_TEST_TYPE = 'Procalcitonin'

	LEFT OUTER JOIN #Cultures						BLD			ON [BasePop].ENCOUNTER_ID = [BLD].ENCOUNTER_ID AND [BLD].CULTURE_TYPE = 'Blood' 

	LEFT OUTER JOIN #Cultures						URN			ON [BasePop].ENCOUNTER_ID = [URN].ENCOUNTER_ID AND [URN].CULTURE_TYPE = 'Urine' 

	LEFT OUTER JOIN #Cultures						CSF			ON [BasePop].ENCOUNTER_ID = [CSF].ENCOUNTER_ID AND [CSF].CULTURE_TYPE = 'CSF' 



	-- Transfers

	LEFT OUTER JOIN #ED2HEMONC									ON [BasePop].ENCOUNTER_ID = [#ED2HEMONC].ENCOUNTER_ID AND [#ED2HEMONC].TIME_LINE=1

	LEFT OUTER JOIN #ED2ICU							ICU			ON [BasePop].ENCOUNTER_ID = [ICU].ENCOUNTER_ID AND [ICU].TIME_LINE=1

	LEFT OUTER JOIN #ED2GEN							GEN			ON [BasePop].ENCOUNTER_ID = [GEN].ENCOUNTER_ID AND [GEN].TIME_LINE=1



	-- Miscellaneous

	LEFT OUTER JOIN #BPA										ON [BasePop].ENCOUNTER_ID = [#BPA].ENCOUNTER_ID AND [#BPA].TIME_LINE=1

	LEFT OUTER JOIN #Base_Pop_ED_Readmit_All		READMITALL	ON [READMITALL].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID

	LEFT OUTER JOIN #Base_Pop_ED_Readmit			READMIT		ON [READMIT].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID

	LEFT OUTER JOIN #Base_Pop_ENC_Reason			RSN			ON [RSN].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID

	LEFT OUTER JOIN #FirstPositiveOD_To_ABXAdminTime OD2ABX		ON OD2ABX.ENCOUNTER_ID = [BasePop].ENCOUNTER_ID

	LEFT OUTER JOIN #SSOrderSet									ON [BasePop].ENCOUNTER_ID = [#SSOrderSet].ENCOUNTER_ID AND [#SSOrderSet].TIME_LINE=1

	LEFT OUTER JOIN #SepsisAlertCancelled						ON [BasePop].ENCOUNTER_ID = [#SepsisAlertCancelled].ENCOUNTER_ID AND [#SepsisAlertCancelled].TIME_LINE=1

	LEFT OUTER JOIN #BedEvents						BE1			ON [BE1].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID AND [BE1].REQ_LINE=1 AND [BE1].TIME_LINE=1--BED REQUESTED

	LEFT OUTER JOIN #BedEvents						BE2			ON [BE2].ENCOUNTER_ID = [BasePop].ENCOUNTER_ID AND [BE2].REQ_LINE=1 AND [BE2].TIME_LINE=2--BED ASSIGNED







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

			--AND [#Base_Pop_Severe_ED_Scores].ENCOUNTER_ID = [#ED_PositiveScores].ENCOUNTER_ID

			--AND [#ED_PositiveScores].FIRST_TIME_LINE = 1

			AND [#Base_Pop_Severe_ED_Scores].ENCOUNTER_ID = [#Final].ENC_ID

			AND (RECORDED_TIME > [First Positive Score Time] AND RECORDED_TIME <= DATEADD(MI, 90, [First Positive Score Time]))

		ORDER BY [First Positive Score Time] DESC

	) RESCREEN



	OUTER APPLY

	(

		SELECT TOP 1 RECORDED_TIME

		FROM #Base_Pop_Severe_ED_Scores

		WHERE 1=1

			AND [#Base_Pop_Severe_ED_Scores].ENCOUNTER_ID = [#Final].ENC_ID

			AND (RECORDED_TIME >  DATEADD(MI, -60, [ED Departure Time]) AND RECORDED_TIME < [ED Departure Time])

		ORDER BY RECORDED_TIME DESC

	) REPEATSCREEN



	OUTER APPLY

	(

		SELECT TOP 1 ADT_DEPARTMENT_NAME

		FROM #PatientLocation

		WHERE 1=1

			AND [#PatientLocation].ENCOUNTER_NUM = [#Final].ENC_ID 

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

			AND [#BloodPressure].ENCOUNTER_ID = [#Final].ENC_ID

			AND (

					RECORDED_TIME BETWEEN DATEADD(MI, -30, [First Positive Score Time]) AND [First Positive Score Time]

					OR

					-- first negative screen ONLY if encounter was never positive (so each ENC_ID has either Pos or Neg, but not both)

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

			AND [#BloodPressure].ENCOUNTER_ID = [#Final].ENC_ID

			AND (

					RECORDED_TIME BETWEEN DATEADD(MI, -30, [First Positive Score Time]) AND [First Positive Score Time]

					OR

					-- first negative screen ONLY if encounter was never positive (so each ENC_ID has either Pos or Neg, but not both)

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

			AND [#BloodPressure].ENCOUNTER_ID = [#Final].ENC_ID

			AND (

					RECORDED_TIME BETWEEN [First Positive Score Time] AND DATEADD(MI, 30, [First Positive Score Time])

					OR

					-- first negative screen ONLY if encounter was never positive (so each ENC_ID has either Pos or Neg, but not both)

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

			AND [#BloodPressure].ENCOUNTER_ID = [#Final].ENC_ID

			AND (

					RECORDED_TIME BETWEEN [First Positive Score Time] AND DATEADD(MI, 30, [First Positive Score Time])

					OR

					-- first negative screen ONLY if encounter was never positive (so each ENC_ID has either Pos or Neg, but not both)

					RECORDED_TIME BETWEEN [First Negative Score Time] AND DATEADD(MI, 30, [First Negative Score Time])

				)

		ORDER BY RECORDED_TIME DESC			

	) FIRST_BP_PERCENTILE



;

