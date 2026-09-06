





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

 -- Description:          SSS NON SEVERE SEPSIS. THIS CODE MUST BE RAN FOR FULL MONTH.

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

		SET @StartDate = [dbo].[fn_parse_date]('MB-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @StartDate = [dbo].[fn_parse_date](@i_vRelativeStartDate)



	IF @i_vRelativeEndDate IS NULL OR @i_vRelativeEndDate = ''

		SET @EndDate = [dbo].[fn_parse_date]('ME-1')--DEFAULTING TO PREVIOUS MONTH

	ELSE

		SET @EndDate = [dbo].[fn_parse_date](@i_vRelativeEndDate)	



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

	DELETE FROM [reports].[NON_SEVERE_SEPSIS_STAGING]



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

				[reports].[NON_SEVERE_SEPSIS_STAGING]



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

	HE.ENCOUNTER_ID

	, HE.INPATIENT_DATA_ID

	, DATEDIFF(MM,PAT.BIRTH_DATE,COALESCE(HE.ADT_ARRIVAL_TIME,HE.HOSP_ADMSN_TIME)) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,HE.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS



INTO 

	#Base_Pop_1



FROM 

	dbo.V_HOSPITAL_TRANSACTIONS HTR

	JOIN dbo.HOSPITAL_ENCOUNTERS HE 

		ON HTR.ENCOUNTER_ID = HE.ENCOUNTER_ID

	JOIN dbo.PATIENTS PAT 

		ON PAT.PATIENT_ID = HE.PATIENT_ID



WHERE

	HTR.SERVICE_DATE BETWEEN @StartDate AND @EndDate 

	--and HE.ENCOUNTER_ID=1018379064

	AND (HE.INP_ADM_DATE IS NOT NULL --PATIENTS UST BE ADMITTED

		OR HE.ED_DISPOSITION_CODE = 3 --ADMITTED

		or HE.ADT_PATIENT_CLASS_CODE IN (101, 104)) 



/* LIST OF ENCOUNTER ADMITTED DIRECTLY TO NICU BEGIN */

IF OBJECT_ID(N'tempdb..#NICUAdmissions') IS NOT NULL 

DROP TABLE #NICUAdmissions;



SELECT DISTINCT 

	ADT.ENCOUNTER_ID 



INTO 

	#NICUAdmissions



FROM

	#Base_Pop_1 B

	JOIN dbo.ADT_EVENTS ADT

		ON ADT.ENCOUNTER_ID = B.ENCOUNTER_ID



WHERE 

	ADT.EVENT_TYPE_CODE = 1 --ADMISSION

	AND ADT.EVENT_SUBTYPE_CODE <> 2 --CANCELLED

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

		ON NA.ENCOUNTER_ID = FP.ENCOUNTER_ID



WHERE 

	NA.ENCOUNTER_ID IS NULL



--Getting List of Encounters where a ABX was ordered. 

IF OBJECT_ID(N'tempdb..#ABXORDER_TIMES') IS NOT NULL DROP TABLE #ABXORDER_TIMES;

SELECT

	B.ENCOUNTER_ID

	, MO.ORDER_INST AS ABX_ORDER_TIME

	, MIN(MA.TAKEN_TIME) AS FIRST_ABX_ADMIN_TIME

	--, ROW_NUMBER() OVER(PARTITION BY B.ENCOUNTER_ID ORDER BY MO.ORDER_INST ASC) LINE

INTO

	#ABXORDER_TIMES	

FROM

		#Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN dbo.MEDICATION_ORDERS MO ON MO.ENCOUNTER_ID = B.ENCOUNTER_ID

		INNER JOIN dbo.MEDICATIONS MEDS ON MEDS.MEDICATION_ID = MO.MEDICATION_ID --AND MEDS.THERA_CLASS_CODE = 11 --Antibiotics

		INNER JOIN dbo.MED_ADMIN_RECORDS MA ON MA.ORDER_MED_ID = MO.ORDER_MED_ID

	WHERE

		MA.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND MA.TAKEN_TIME < @EndDate

		AND MO.MED_ROUTE_CODE=11--IV ONLY

		AND MA.MAR_ACTION_CODE IN ('1'			--GIVEN

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

		AND MO.MEDICATION_ID IN 

			(



				select 

						medlist.MEDICATION_ID

					from

						(

							SELECT 

								RXM.MEDICATION_ID,

								RXM.NAME,

								cntl.VALUE_SET_DISPLAY as AGENT,

								case when CHARINDEX('^',cntl.VALUE_SET_ABBR)>0 then SUBSTRING(cntl.VALUE_SET_ABBR,0,CHARINDEX('^',cntl.VALUE_SET_ABBR)) else cntl.VALUE_SET_ABBR end as AGENT_GROUP,

								case when cntl.VALUE_SET_ABBR like '%^Y' then 1 else 0 end as DOT_MONITORING,

								gen.TITLE,

								ROW_NUMBER() over(partition by RXM.MEDICATION_ID order by cntl.VALUE_SET_ABBR,cntl.VALUE_SET_DISPLAY asc) as AGENT_ORDER



							FROM

								dbo.MEDICATIONS RXM

								OUTER APPLY(

									--Get the main medication's simple generic if its a mixture

									SELECT TOP 1 

										mix.DRUG_ID,

										comp.SIMPLE_GENERIC_CODE 

									FROM

										dbo.MED_MIX_COMPONENTS mix

										INNER JOIN dbo.MEDICATIONS comp on mix.DRUG_ID=comp.MEDICATION_ID

									WHERE

										mix.TYPE_CODE=3		--3 - Medications 

										AND mix.MEDICATION_ID=RXM.MEDICATION_ID

									ORDER BY

										mix.LINE

								) mixture

								INNER JOIN dbo.REF_GENERIC_MED gen on gen.SIMPLE_GENERIC_CODE=coalesce(RXM.SIMPLE_GENERIC_CODE,mixture.SIMPLE_GENERIC_CODE)

								INNER JOIN reports.CONFIG_VALUE_SET cntl on cntl.VALUE_SET_ID=3016 and cntl.CODE=gen.SIMPLE_GENERIC_CODE -- and cntl.VALUE_SET_ABBR='Antibacterial'

						) medlist

					where

						medlist.AGENT_ORDER=1						

			)

GROUP BY

	B.ENCOUNTER_ID

	, MO.ORDER_INST		

	UNION

	SELECT

		DISTINCT

		B.ENCOUNTER_ID

		, MO.ORDER_INST AS ABX_ORDER_TIME

		, MIN(MA.TAKEN_TIME) AS FIRST_ABX_ADMIN_TIME

		--, MEDS.NAME

	FROM

		#Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN dbo.MEDICATION_ORDERS MO ON MO.ENCOUNTER_ID = B.ENCOUNTER_ID

		INNER JOIN dbo.MEDICATIONS MEDS ON MEDS.MEDICATION_ID = MO.MEDICATION_ID AND MEDS.THERA_CLASS_CODE = 11 --Antibiotics

		INNER JOIN dbo.MED_ADMIN_RECORDS MA ON MA.ORDER_MED_ID = MO.ORDER_MED_ID

	WHERE

		MA.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND MO.MED_ROUTE_CODE=11--IV ONLY

		AND MA.MAR_ACTION_CODE IN ('1'			--GIVEN

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

	B.ENCOUNTER_ID

	, MO.ORDER_INST



IF OBJECT_ID(N'tempdb..#ABXORDER') IS NOT NULL DROP TABLE #ABXORDER;				

SELECT *

, ROW_NUMBER() OVER(PARTITION BY A.ENCOUNTER_ID ORDER BY A.ABX_ORDER_TIME ASC) LINE

INTO #ABXORDER

FROM #ABXORDER_TIMES A



--Getting List of Encounters where a Blood Culture was ordered. this is the 2nd pat of treatment plan

IF OBJECT_ID(N'tempdb..#TP2') IS NOT NULL DROP TABLE #TP2;



SELECT

	B.ENCOUNTER_ID

	, PO.ORDER_INST AS BLOOD_CULTURE_ORDER_TIME

	, ROW_NUMBER() OVER(PARTITION BY B.ENCOUNTER_ID ORDER BY PO.ORDER_INST ASC) LINE



INTO

	#TP2



FROM

	#Base_Pop B

	JOIN dbo.PROCEDURE_ORDERS PO

		ON PO.ENCOUNTER_ID = B.ENCOUNTER_ID

			AND PO.PROC_ID IN (600003,600004,600011,600012)  --BLOOD CULTURE

			AND ORDER_STATUS_CODE <> 4  --CANCELED

	WHERE PO.ORDER_INST < @EndDate



--GETTING LIST OF ALL ENCOUNTERS WHERE AN ABX AND BLOOD CULTURE WERE ORDERED WITHIN 24 HOURS OF EACH OTHER

IF OBJECT_ID(N'tempdb..#Base_Popmed') IS NOT NULL 

DROP TABLE #Base_Popmed;



SELECT DISTINCT

	B.ENCOUNTER_ID

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

		ON A.ENCOUNTER_ID = B.ENCOUNTER_ID

	JOIN #TP2

		ON #TP2.ENCOUNTER_ID = B.ENCOUNTER_ID



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

	B.ENCOUNTER_ID NOT IN (SELECT DISTINCT ENCOUNTER_ID FROM reports.[NON_SEVERE_SEPSIS_STAGING] )--08.12.2019 make sure we are not includiung already submitted encounters

	AND  B.ENCOUNTER_ID NOT IN  (SELECT DISTINCT ENCOUNTER_ID FROM reports.[SEVERE_SEPSIS_STAGING] )--08.12.2019 make sure we are not includiung already submitted encounters



IF OBJECT_ID(N'tempdb..#FINAL') IS NOT NULL 

DROP TABLE #FINAL;



SELECT

	CONVERT(VARCHAR, C.INPATIENT_DATA_ID) + CONVERT(VARCHAR, YEAR(DATEADD(MM,-1,GETDATE()))) + CONVERT(VARCHAR, MONTH(DATEADD(MM, -1, GETDATE()))) AS Sepsis_Episode_ID_V01

	, C.ABX_ORDER_TIME AS AntibioticOrderedTime_V59

	, C.FIRST_ABX_ADMIN_TIME AS AntibioticAdministeredTime_V60

	, C.BLOOD_CULTURE_ORDER_TIME AS BloodCultureOrderedTime_V61

	, C.ENCOUNTER_ID 

	, DATENAME(month, DATEADD(MM,-1,getdate()))+DATENAME(YEAR, DATEADD(MM,-1,getdate())) AS DATE_STAMP

	, 0 AS REVIEWED



INTO

	#FINAL



FROM

	#COHORT C



WHERE

	C.ABX_LINE = (SELECT MIN(C2.ABX_LINE)

				FROM #COHORT C2

				WHERE C2.ENCOUNTER_ID = C.ENCOUNTER_ID)

	AND BC_LINE = (SELECT MIN(C2.BC_LINE)

				FROM #COHORT C2

				WHERE C2.ENCOUNTER_ID = C.ENCOUNTER_ID)



ORDER BY ENCOUNTER_ID



--FINDING PATIENTS WHO WENT TO CARDIAC UNITS



IF OBJECT_ID(N'tempdb..#CARDIAC') IS NOT NULL 

DROP TABLE #CARDIAC;



SELECT 

	C.ENCOUNTER_ID

	, V.IN_DTTM

	, V.OUT_DTTM



INTO

	#CARDIAC



FROM

	#COHORT C

	JOIN .V_PATIENT_LOCATION_HISTORY V

		ON V.ENCOUNTER_NUM = C.ENCOUNTER_ID



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

	, CONVERT(varchar, C.ENCOUNTER_ID) AS ENCOUNTER_ID

	, CONVERT(varchar, C.DATE_STAMP) AS DATE_STAMP

	, CONVERT(bit, C.REVIEWED) AS REVIEWED



INTO

	#FinalData 



FROM

	#FINAL C

	LEFT JOIN #CARDIAC A

		ON A.ENCOUNTER_ID = C.ENCOUNTER_ID



WHERE

	A.ENCOUNTER_ID IS NULL



-------------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

IF @TEST = 0

	BEGIN

		INSERT INTO [reports].[NON_SEVERE_SEPSIS_STAGING]

			([Sepsis_Episode_ID_V01]

			, [AntibioticOrderedTime_V59]

			, [AntibioticAdministeredTime_V60]

			, [BloodCultureOrderedTime_V61]

			, [ENCOUNTER_ID]

			, [DATE_STAMP]

			, [Reviewed])



		SELECT 

			* 

		FROM

			#FinalData



		SELECT 

			*



		FROM

			[reports].[NON_SEVERE_SEPSIS_STAGING]



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

			, [ENCOUNTER_ID]



		FROM

			[reports].[NON_SEVERE_SEPSIS_STAGING]



		WHERE

			DATE_STAMP = DATENAME(month, CONVERT(DATE, @EndDate)) + DATENAME(YEAR, CONVERT(DATE, @EndDate))

	END;

-------------------------------------------------------------------------------------------------------------------------------------------------------

END;

END;

-------------------------------------------------------------------------------------------------------------------------------------------------------

-------------------------------------------------------------END---------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------------------------------------------------------------------------

