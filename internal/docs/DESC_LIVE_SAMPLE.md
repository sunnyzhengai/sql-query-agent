# P0-c sample — for Sunny's hand grading

**Scale caveat (ruled 2026-08-31, corrected same day):** this corpus spans both ends of the difficulty range — the de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across 21 procs in reporting/, including the 43-step USP_ED_SEPSIS whose invented flowsheet IDs created this gate) AND clean adversarial governance shapes. Difficulty is REAL; what is limited is SCALE: a 28-proc estate, not a multi-thousand-proc enterprise. These rates are MEASURED, not extrapolated, and any place we quote them must carry this sentence.

For each: the generated description, the fragment it describes, and the PARSED FACTS the gate checked it against. Grade the DESCRIPTION, not the rates.

## USP_ED_SEPSIS.sql · ABX
*outcome: clean* · parsed tables: #allmeds, config_value_set, med_mix_components, medications, ref_generic_med · parsed grain: order, visit

**Description**

This SQL selects encounters with antibiotic administration times.

- TAKEN_TIME must be less than ED_DEPARTURE_TIME.
- MEDICATION_ID must be in a list derived from medications with mixtures that include antibiotics, where AGENT_ORDER equals 1.
- THERA_CLASS_CODE must equal 11.

**Fragment**

```sql
ABX AS 

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

								RXM.MEDICATION_ID

								--,RXM.NAME

								--,cntl.VALUE_SET_DISPLAY as AGENT

								--,case when CHARINDEX('^',cntl.VALUE_SET_ABBR)>0 then SUBSTRING(cntl.VALUE_SET_ABBR,0,CHARINDEX('^',cntl.VALUE_SET_ABBR)) else cntl.VALUE_SET_ABBR end as AGENT_GROUP

								--,case when cntl.VALUE_SET_ABBR like '%^Y' then 1 else 0 end as DOT_MONITORING

								--,gen.TITLE

								,ROW_NUMBER() OVER(PARTITION BY RXM.MEDICATION_ID ORDER BY [cntl].VALUE_SET_ABBR, [cntl].VALUE_SET_DISPLAY ASC) AS AGENT_ORDER



							FROM [dbo].MEDICATIONS RXM

								OUTER APPLY (

									--Get the main medication's simple generic if its a mixture

									SELECT TOP 1 

										mix.DRUG_ID,

										comp.SIMPLE_GENERIC_CODE 

									FROM [dbo].MED_MIX_COMPONENTS mix

										INNER JOIN [dbo].MEDICATIONS comp ON mix.DRUG_ID = comp.MEDICATION_ID

									WHERE 1=1

										AND mix.TYPE_CODE = 3 -- Medications 

										AND mix.MEDICATION_ID = RXM.MEDICATION_ID

									ORDER BY

										mix.LINE

								) mixture



								INNER JOIN [dbo].REF_GENERIC_MED		gen ON gen.SIMPLE_GENERIC_CODE = COALESCE(RXM.SIMPLE_GENERIC_CODE, mixture.SIMPLE_GENERIC_CODE)

								INNER JOIN [reports].CONFIG_VALUE_SET cntl ON cntl.VALUE_SET_ID=3016 AND cntl.CODE = gen.SIMPLE_GENERIC_CODE

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
```

## USP_ED_SEPSIS.sql · AllCultures
*outcome: emptied* · parsed tables: #labs_and_cultures, organisms · parsed grain: order, visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
AllCultures AS

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

		LEFT JOIN [dbo].ORGANISMS ON [#Labs_and_Cultures].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE CULTURE_TYPE IS NOT NULL

)
```

first pass violated: technical vocabulary in a business description: 'table' — say what is included, not how the SQL assembles it

## USP_ED_SEPSIS.sql · All_LDAs
*outcome: clean* · parsed tables: #base_pop, config_value_set, line_device_airway · parsed grain: (unknown)

**Description**

Records of LDA placements.

- Inclusion is determined by FLO_MEAS_ID values: '900112', '900111', or a VALUE_SET_ID of 3022.
- A placement time is recorded.
- The placement time falls between ADT_ARRIVAL_TIME and ED_DEPARTURE_TIME.

**Fragment**

```sql
All_LDAs AS

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

		INNER JOIN [dbo].LINE_DEVICE_AIRWAY LNA ON LNA.ENCOUNTER_ID = [#Base_Pop].ENCOUNTER_ID

		LEFT JOIN (

			SELECT DISTINCT VALUE_SET_ID, CODE

			FROM [reports].CONFIG_VALUE_SET

			WHERE VALUE_SET_ID = 3022	-- SEPSIS_CVL_PLACEMENT [3022]

		) CVS ON LNA.FLO_MEAS_ID = [CVS].CODE



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
```

## USP_ED_SEPSIS.sql · NegativeCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

NegativeCultures selects encounters with specific culture types that have no positive critical values.

- Inclusion requires MAX(CRITICAL_VALUE_01) = 0.
- Encounter_ID and CULTURE_TYPE must be grouped together.
- The minimum MBOrderTime and CollectionTime are recorded.

**Fragment**

```sql
NegativeCultures AS

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
```

## USP_ED_SEPSIS.sql · OrderMetricIDs
*outcome: recovered* · parsed tables: #base_pop, order_tracking_metrics · parsed grain: order, visit

**Description**

OrderMetricIDs selects encounters with associated order metrics.

- ORDER_DTTM falls between ADT_ARRIVAL_TIME and ED_DEPARTURE_TIME.
- Encounter_ID must match between ORDER_TRACKING_METRICS and the source.
- ORDER_ID and PRL_ORDERSET_ID are included without specific values listed.

**Fragment**

```sql
OrderMetricIDs AS

(

	SELECT

		[#Base_Pop].ENCOUNTER_ID

		, ORDER_ID

		, ORDER_DTTM

		, PRL_ORDERSET_ID

	FROM #Base_Pop

		INNER JOIN [dbo].ORDER_TRACKING_METRICS ON [ORDER_TRACKING_METRICS].ENCOUNTER_ID = [#Base_Pop].ENCOUNTER_ID

	WHERE [ORDER_TRACKING_METRICS].ORDER_DTTM BETWEEN [#Base_Pop].ADT_ARRIVAL_TIME AND [#Base_Pop].ED_DEPARTURE_TIME

)
```

first pass violated: technical vocabulary in a business description: 'table' — say what is included, not how the SQL assembles it; technical vocabulary in a business description: 'table' — say what is included, not how the SQL assembles it

## USP_ED_SEPSIS.sql · PositiveCultures
*outcome: recovered* · parsed tables: — · parsed grain: visit

**Description**

PositiveCultures selects encounters with positive culture results.

- Inclusion requires MAX(CRITICAL_VALUE_01) = 1, indicating any positives.
- The selection includes ENCOUNTER_ID and CULTURE_TYPE.
- OrganismList contains organism names aggregated with a semicolon, with a minimum of one organism listed, and the lowest value is 'Critical Value'.

**Fragment**

```sql
PositiveCultures AS

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
```

first pass violated: ungrounded value: '100' not in the SQL

## USP_ED_SEPSIS.sql · SSOrderSetOSQ_PRL
*outcome: clean* · parsed tables: medication_orders_ext, procedure_orders_ext · parsed grain: order, visit

**Description**

This is a selection of encounters related to specific order sets.

- Includes encounters with an ORDER_DTTM and an ORD_OSQ_ID of 400002, 400007, 400003, 400004, 400006, 400005, or 4001326025.
- Includes encounters where the PRL_ORDERSET_ID is 400001 or 4001326023.
- The selection is based on the presence of an ORDER_ID in the MEDICATION_ORDERS_EXT or PROCEDURE_ORDERS_EXT tables.

**Fragment**

```sql
SSOrderSetOSQ_PRL AS

(

	-- OSQ

	SELECT

		[OrderMetricIDs].ENCOUNTER_ID

		, [OrderMetricIDs].ORDER_DTTM

		, [MEDICATION_ORDERS_EXT].ORD_OSQ_ID AS PRL_ORDERSET_ID

	FROM OrderMetricIDs

		INNER JOIN [dbo].MEDICATION_ORDERS_EXT ON [OrderMetricIDs].ORDER_ID = [MEDICATION_ORDERS_EXT].ORDER_ID AND [MEDICATION_ORDERS_EXT].ORD_OSQ_ID IN (400002,400007,400003,400004,400006,400005,4001326025)



	UNION



		SELECT

			[OrderMetricIDs].ENCOUNTER_ID

			, [OrderMetricIDs].ORDER_DTTM

			, [PROCEDURE_ORDERS_EXT].ORD_OSQ_ID AS PRL_ORDERSET_ID

		FROM OrderMetricIDs

			INNER JOIN [dbo].PROCEDURE_ORDERS_EXT ON [OrderMetricIDs].ORDER_ID =  [PROCEDURE_ORDERS_EXT].ORDER_ID AND [PROCEDURE_ORDERS_EXT].ORD_OSQ_ID IN (400002,400007,400003,400004,400006,400005,4001326025)



	UNION



		SELECT

			[OrderMetricIDs].ENCOUNTER_ID

			, [OrderMetricIDs].ORDER_DTTM

			, [OrderMetricIDs].PRL_ORDERSET_ID

		FROM OrderMetricIDs

		-- see VCG 800018 -- HS BI SEPSIS PRL ORDERSETS (the entire Grouper is used by SSS Severe Sepsis; ED Sepsis only uses ED-specific PRLs)

		WHERE [OrderMetricIDs].PRL_ORDERSET_ID IN (400001, 4001326023) -- Sepsis Pathway [400001]; HS ED ONCOLOGY SEPSIS RN PROTOCOL OPA [4001326023]

)
```

## USP_ED_SEPSIS.sql · Systolic
*outcome: clean* · parsed tables: #flowsheets · parsed grain: visit

**Description**

This SQL selects encounters with recorded blood pressure measurements.

- Inclusion requires a FLO_MEAS_ID of '95'.
- Recorded time must fall between ADT_ARRIVAL_TIME and ED_DEPARTURE_TIME.
- Hypotension status is determined by systolic blood pressure values: less than 56 for ages under 2 months, less than 65 for ages under 6 months, less than 70 for ages under 12 months, less than 70 for ages up to 13 years, and less than 100 for ages over 13 years.

**Fragment**

```sql
Systolic AS

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
```

## USP_ED_SEPSIS.sql · TimeOrdered_LDAs
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

This SQL selects TimeOrdered_LDAs.

- Includes encounters with specific ENCOUNTER_IDs and LDA_PLACEMENT_TYPE values.
- The TIME_LINE is determined by the PLACEMENT_INSTANT, ordered chronologically.
- The SQL captures all records where a placement time is recorded.

**Fragment**

```sql
TimeOrdered_LDAs AS

(



SELECT *

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, LDA_PLACEMENT_TYPE ORDER BY PLACEMENT_INSTANT) AS TIME_LINE

FROM All_LDAs

)
```

## USP_ED_SEPSIS.sql · TimeOrdered_Labs
*outcome: clean* · parsed tables: #labs_and_cultures · parsed grain: visit

**Description**

This SQL selects encounters with lab tests.

- Includes encounters where LAB_TEST_TYPE is not null.
- Assigns a TIME_LINE based on the order of MBOrderTime, partitioned by ENCOUNTER_ID and LAB_TEST_TYPE.
- The TIME_LINE values range from 1 to the maximum number of lab tests per encounter, with the lowest value being 1.

**Fragment**

```sql
TimeOrdered_Labs AS

(

	SELECT *

		, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID, LAB_TEST_TYPE ORDER BY MBOrderTime ASC) AS TIME_LINE

	FROM #Labs_and_Cultures

	WHERE LAB_TEST_TYPE IS NOT NULL

)
```

## USP_IP_SEPSIS.sql · FlwshtProp
*outcome: clean* · parsed tables: #base_pop, #prophylaxisflo, flowsheet_measurements, flowsheet_records · parsed grain: (unknown)

**Description**

This SQL selects records of measurements.

- Inclusion is determined by FLO_MEAS_ID values: '9000613042', '9000613043', '9000613044', '9000613045', '9000613047', '9000613048', '9000613050'.
- RECORDED_TIME must be present and not null.

**Fragment**

```sql
FlwshtProp AS

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
```

## USP_IP_SEPSIS.sql · dateCTE
*outcome: clean* · parsed tables: #base_poptemp, datecte · parsed grain: patient, visit

**Description**

This SQL selects patient encounter records.

- Inclusion is determined by the condition that `inDeptRN = 1`.
- The `DEPARTMENT_ROLLUP` must not be in ('ER', 'P-ER').
- The `In Shift` must be either 'AM' or 'PM', and the `Out Shift Date` must be greater than or equal to the `In Shift Date`.

**Fragment**

```sql
dateCTE AS

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
```

## USP_IP_SEPSIS.sql · vaplh
*outcome: recovered* · parsed tables: #mainadmdetails, adt_events, departments, hospital_encounters · parsed grain: visit

**Description**

This SQL selects encounters with specific admission and transfer events.

- Includes encounters where the EVENT_TYPE_CODE is 1, 3, or 99.
- Excludes encounters with an EVENT_SUBTYPE_CODE of 2.
- Requires a valid DEPARTMENT_ID; if absent, it notes '*Department not specified', '*Unknown department', or '*Unnamed department'.

**Fragment**

```sql
vaplh AS

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
```

first pass violated: purpose speculation: 'ensuring' in '- Includes encounters with a DEPARTMENT_ID that is not NULL,' — say WHAT is included and on WHAT VALUES; why is the steward's to write

## USP_IP_SepsisPatientDates.sql · dateCTE
*outcome: clean* · parsed tables: #base_poptemp, datecte · parsed grain: patient, visit

**Description**

This SQL selects patient encounters.

- Inclusion is determined by the DEPARTMENT_ROLLUP not being in ('ER', 'P-ER').
- The EXPANSION DATE must be less than or equal to the EXPANSION END DATE.
- A placement time is recorded for each encounter.

**Fragment**

```sql
dateCTE AS

(

	SELECT ENCOUNTER_ID

		, InDeptDate [Expansion Date]

		, OutDeptDate [Expansion End Date]

		, IN_DTTM [InDepartmentTime]

		, OUT_DTTM [OutDepartmentTime]

		, ADT_DEPARTMENT_ID

		, ADT_DEPARTMENT_NAME

		, PATIENT_ID

		, DEPARTMENT_ROLLUP

		, INPATIENT_DATA_ID

		, BIRTH_DATE

		, [ENC_ID Order]

	FROM #Base_PopTemp

	WHERE DEPARTMENT_ROLLUP NOT IN ('ER', 'P-ER')

	UNION ALL 

	SELECT ENCOUNTER_ID

		, DATEADD(d, 1, d.[Expansion Date]) [Expansion Date]

		, d.[Expansion End Date]

		, d.[InDepartmentTime]

		, d.[OutDepartmentTime]

		, d.ADT_DEPARTMENT_ID

		, d.ADT_DEPARTMENT_NAME

		, d.PATIENT_ID

		, d.DEPARTMENT_ROLLUP

		, d.INPATIENT_DATA_ID

		, BIRTH_DATE

		, [ENC_ID Order]

	FROM dateCTE d 

	WHERE DATEADD(d, 1, d.[Expansion Date]) <= d.[Expansion End Date]

)
```

## USP_IP_SepsisShiftCompliance.sql · dateCTE
*outcome: clean* · parsed tables: #base_poptemp, datecte · parsed grain: patient, visit

**Description**

This SQL selects patient encounter records.

- Inclusion requires that `inDeptRN` equals 1.
- The `DEPARTMENT_ROLLUP` must not be in ('ER', 'P-ER').
- The `In Shift` must be either 'AM' or 'PM', and the `Out Shift Date` must be greater than or equal to the `In Shift Date`.

**Fragment**

```sql
dateCTE AS

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

		, [Unique Row]

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

		, [Unique Row]

	FROM dateCTE d 

	WHERE DATEADD(d, 1, d.[Expansion Date]) <= d.[Expansion End Date]

)
```

## USP_IP_SepsisShiftCompliance.sql · vaplh
*outcome: recovered* · parsed tables: ip_sepsisencounterswlocations · parsed grain: visit

**Description**

This SQL selects encounters.

- Encounter IDs are included as recorded in the [PATENCENCID] field.
- In-department times must be present, as indicated by the [InDepartmentTime] field.
- Out-department times must be present or default to the current date and time, as indicated by the [OutDepartmentTime] field.

**Fragment**

```sql
vaplh AS

(

	SELECT 

		enc.[PATENCENCID] ENCOUNTER_ID

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
```

first pass violated: ungrounded value: '1000' not in the SQL

## USP_RPTS_ED_Sepsis.sql · ABX
*outcome: clean* · parsed tables: #base_pop, config_value_set, med_admin_records, med_mix_components, medication_orders, medications, or, previous, ref_generic_med · parsed grain: order, visit

**Description**

This SQL selects administered antibiotics for encounters.

- Administered antibiotics must have a taken time that is not null and occurs before the ED departure time.
- The medication route code must be 11 (IV only).
- The MAR action code must be one of the following: '1', '7', '102', '105', '113', '114', '115', '122', '124', '132', '143', '1604', '1605', '1607', '6', '99'.

**Fragment**

```sql
ABX AS

(

SELECT

		MO.ENCOUNTER_ID

		, MO.ORDER_MED_ID

		, MA.TAKEN_TIME AS ABX_ADMIN_TIME

		, MEDS.[NAME]



	FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE

		INNER JOIN dbo.MEDICATION_ORDERS MO ON MO.ENCOUNTER_ID = B.ENCOUNTER_ID

		INNER JOIN dbo.MEDICATIONS MEDS ON MEDS.MEDICATION_ID = MO.MEDICATION_ID --AND MEDS.THERA_CLASS_CODE = 11 --Antibiotics

		INNER JOIN dbo.MED_ADMIN_RECORDS MA ON MA.ORDER_MED_ID = MO.ORDER_MED_ID



	WHERE 1=1

		AND MA.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND MA.TAKEN_TIME < B.ED_DEPARTURE_TIME--09.23.2020; MAKE SURE THE Antibiotics WERE GIVEN IN ED

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

									FROM dbo.MED_MIX_COMPONENTS mix

										INNER JOIN dbo.MEDICATIONS comp on mix.DRUG_ID=comp.MEDICATION_ID

									WHERE 1=1

										AND mix.TYPE_CODE=3		--3 - Medications 

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



	UNION



	SELECT DISTINCT

		MO.ENCOUNTER_ID

		, MO.ORDER_MED_ID

		, MA.TAKEN_TIME AS ABX_ADMIN_TIME

		, MEDS.NAME



	FROM #Base_Pop B -- ONLY THOSE PATIENTS WITH A POSITIVE SCORE



		INNER JOIN dbo.MEDICATION_ORDERS MO ON MO.ENCOUNTER_ID = B.ENCOUNTER_ID

		INNER JOIN dbo.MEDICATIONS MEDS ON MEDS.MEDICATION_ID = MO.MEDICATION_ID AND MEDS.THERA_CLASS_CODE = 11 --Antibiotics

		INNER JOIN dbo.MED_ADMIN_RECORDS MA ON MA.ORDER_MED_ID = MO.ORDER_MED_ID



	WHERE 1=1

		AND MA.TAKEN_TIME IS NOT NULL	--ADMINISTERED ABX ONLY

		AND MA.TAKEN_TIME < B.ED_DEPARTURE_TIME--09.23.2020; MAKE SURE THE Antibiotics WERE GIVEN IN ED

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

)
```

## USP_RPTS_ED_Sepsis.sql · BloodCultureResults
*outcome: clean* · parsed tables: #base_pop, lab_order_results, organisms, procedure_orders · parsed grain: order, visit

**Description**

Blood culture results for encounters.

- Order procedure IDs must be in (600003, 600004, 600011, 600012).
- Order time must be between ADT arrival time and ED departure time.
- Critical value flag must be in (2, 218).

**Fragment**

```sql
BloodCultureResults AS

(

	SELECT

		B.ENCOUNTER_ID

		, PO.ORDER_PROC_ID

		, PO.ORDER_TIME

		, RESULTS.RESULT_TIME

		, RESULTS.COMP_OBS_INST_TM

		, RESULTS.ORD_VALUE

		, CASE WHEN RESULTS.RESULT_FLAG_CODE IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01		-- Abnormal or Critical

		, RESULTS.LRR_BASED_ORGAN_ID

		, [ORGANISMS].EXTERNAL_NAME



	FROM #Base_Pop B



		INNER JOIN [dbo].LAB_ORDER_RESULTS RESULTS ON B.ENCOUNTER_ID = RESULTS.ENCOUNTER_ID

		INNER JOIN [dbo].PROCEDURE_ORDERS	 PO		 ON RESULTS.ORDER_PROC_ID = PO.ORDER_PROC_ID 

														AND PO.PROC_ID IN (600003,600004,600011,600012)	-- 'LAB001', 'NUR001', 'LAB012', 'LAB011'



		LEFT JOIN [dbo].ORGANISMS ON [RESULTS].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE (PO.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

)
```

## USP_RPTS_ED_Sepsis.sql · CsfCultureResults
*outcome: clean* · parsed tables: #base_pop, lab_order_results, organisms, procedure_orders · parsed grain: order, visit

**Description**

CsfCultureResults — a selection of lab order results related to encounters.

- Includes ORDER_PROC_ID values of 600005, 600006, and 600002.
- Includes SPECIMEN_SOURCE_CODE of 304.
- Includes RESULT_FLAG_CODE values of 2 and 218, indicating abnormal or critical results.
- The ORDER_TIME must fall between ADT_ARRIVAL_TIME and ED_DEPARTURE_TIME.

**Fragment**

```sql
CsfCultureResults AS 

(

	SELECT

		B.ENCOUNTER_ID

		, PO.ORDER_PROC_ID

		, PO.ORDER_TIME

		, RESULTS.RESULT_TIME

		, RESULTS.COMP_OBS_INST_TM

		, RESULTS.ORD_VALUE

		, RESULTS.RESULT_FLAG_CODE

		, CASE WHEN RESULTS.RESULT_FLAG_CODE IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01		-- Abnormal or Critical

		, RESULTS.LRR_BASED_ORGAN_ID

		, [ORGANISMS].EXTERNAL_NAME



	FROM #Base_Pop B

		INNER JOIN [dbo].LAB_ORDER_RESULTS RESULTS ON B.ENCOUNTER_ID = RESULTS.ENCOUNTER_ID

		INNER JOIN [dbo].PROCEDURE_ORDERS	 PO		 ON RESULTS.ORDER_PROC_ID = PO.ORDER_PROC_ID

														AND PO.PROC_ID IN (600005,600006, 600002)		-- 'LAB006', 'LAB007', 'LAB003'

														AND PO.SPECIMEN_SOURCE_CODE=304				-- Lumber puncture



		LEFT JOIN [dbo].ORGANISMS ON [RESULTS].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE (PO.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)

)
```

## USP_RPTS_ED_Sepsis.sql · NegativeCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

NegativeCultures selects encounters with specific criteria.

- Encounter_ID is included.
- The minimum ORDER_TIME is recorded.
- The minimum COMP_OBS_INST_TM is recorded.
- The maximum CRITICAL_VALUE_01 equals 0.

**Fragment**

```sql
NegativeCultures AS

(

	SELECT

		ENCOUNTER_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]



	FROM BloodCultureResults

	GROUP BY ENCOUNTER_ID

	HAVING MAX(CRITICAL_VALUE_01) = 0

)
```

## USP_RPTS_ED_Sepsis.sql · NegativeCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

NegativeCultures selects encounters with no growth or contamination.

- Encounter_ID is included.
- The minimum ORDER_TIME is recorded.
- The minimum COMP_OBS_INST_TM is recorded.
- MAX(CRITICAL_VALUE_01) must equal 0.

**Fragment**

```sql
NegativeCultures AS

(

	SELECT

		ENCOUNTER_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]		-- 'No Growth' or contamination with normal flora



	FROM UrineCultureResults

	GROUP BY ENCOUNTER_ID

	HAVING MAX(CRITICAL_VALUE_01) = 0

)
```

## USP_RPTS_ED_Sepsis.sql · NegativeCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

NegativeCultures selects encounters with specific criteria.

- Encounter_ID is included.
- The minimum ORDER_TIME is recorded.
- The minimum COMP_OBS_INST_TM is recorded.
- The maximum CRITICAL_VALUE_01 equals 0.

**Fragment**

```sql
NegativeCultures AS

(

	SELECT

		ENCOUNTER_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, 'Negative' AS [OrganismList]



	FROM CsfCultureResults

	GROUP BY ENCOUNTER_ID

	HAVING MAX(CRITICAL_VALUE_01) = 0

)
```

## USP_RPTS_ED_Sepsis.sql · PositiveCultures
*outcome: emptied* · parsed tables: — · parsed grain: visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
PositiveCultures AS

(

	SELECT

		ENCOUNTER_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, COALESCE(STRING_AGG(EXTERNAL_NAME, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM BloodCultureResults

	GROUP BY ENCOUNTER_ID

	HAVING MAX(CRITICAL_VALUE_01) = 1

)
```

first pass violated: ungrounded value: 'Organism C' not in the SQL; ungrounded value: 'Organism A' not in the SQL; ungrounded value: 'Organism B' not in the SQL

## USP_RPTS_ED_Sepsis.sql · PositiveCultures
*outcome: emptied* · parsed tables: — · parsed grain: visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
PositiveCultures AS

(

	SELECT

		ENCOUNTER_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, COALESCE(STRING_AGG(EXTERNAL_NAME, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM UrineCultureResults

	GROUP BY ENCOUNTER_ID

	HAVING MAX(CRITICAL_VALUE_01) = 1

)
```

first pass violated: ungrounded value: 'P. mirabilis' not in the SQL; ungrounded value: 'E. coli' not in the SQL; ungrounded value: 'K. pneumoniae' not in the SQL

## USP_RPTS_ED_Sepsis.sql · PositiveCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

This SQL selects encounters with positive cultures.

- Inclusion requires that MAX(CRITICAL_VALUE_01) equals 1.
- The minimum ORDER_TIME is recorded as [MBOrderTime].
- The minimum COMP_OBS_INST_TM is recorded as [CollectionTime].
- The organism list includes EXTERNAL_NAME values aggregated, with a minimum of 'Critical Value' if none are present.

**Fragment**

```sql
PositiveCultures AS

(

	SELECT

		ENCOUNTER_ID



		, MIN(ORDER_TIME)		AS [MBOrderTime]

		, MIN(COMP_OBS_INST_TM)	AS [CollectionTime]



		, COALESCE(STRING_AGG(EXTERNAL_NAME, '; ') WITHIN GROUP(ORDER BY LRR_BASED_ORGAN_ID), 'Critical Value') AS [OrganismList]



	FROM CsfCultureResults

	GROUP BY ENCOUNTER_ID

	HAVING MAX(CRITICAL_VALUE_01) = 1

)
```

## USP_RPTS_ED_Sepsis.sql · UrineCultureResults
*outcome: recovered* · parsed tables: #base_pop, lab_order_results, organisms, procedure_orders · parsed grain: order, visit

**Description**

Urine culture results for encounters.

- Encounter IDs from the LAB_ORDER_RESULTS.
- Procedure order IDs must be in (600001, 600007, 600008, 600009, 600010).
- Order time must fall between ADT arrival time and ED departure time. 
- Critical value flag codes must be in (2, 218). 
- Organism IDs are linked to the results. 
- Result times and observation times are recorded.

**Fragment**

```sql
UrineCultureResults AS 

(

	SELECT

		B.ENCOUNTER_ID

		, PO.ORDER_PROC_ID

		, PO.ORDER_TIME

		, RESULTS.RESULT_TIME

		, RESULTS.COMP_OBS_INST_TM

		, RESULTS.ORD_VALUE

		, RESULTS.RESULT_FLAG_CODE

		, CASE WHEN RESULTS.RESULT_FLAG_CODE IN (2, 218) THEN 1 ELSE 0 END AS CRITICAL_VALUE_01		-- Abnormal or Critical

		, RESULTS.LRR_BASED_ORGAN_ID

		, [ORGANISMS].EXTERNAL_NAME



	FROM #Base_Pop B



		INNER JOIN [dbo].LAB_ORDER_RESULTS RESULTS ON B.ENCOUNTER_ID = RESULTS.ENCOUNTER_ID

		INNER JOIN [dbo].PROCEDURE_ORDERS	 PO		 ON RESULTS.ORDER_PROC_ID = PO.ORDER_PROC_ID 

														AND PO.PROC_ID IN (600001, 600007, 600008, 600009, 600010)	-- 'LAB002', 'LAB008', 'LAB009', 'LAB010', 'POC001'



		LEFT JOIN [dbo].ORGANISMS ON [RESULTS].LRR_BASED_ORGAN_ID = [ORGANISMS].ORGANISM_ID



	WHERE (PO.ORDER_TIME BETWEEN B.ADT_ARRIVAL_TIME AND B.ED_DEPARTURE_TIME)



)
```

first pass violated: technical object in a business description: '#Base_Pop' — the source object is carried by the relationship, not the sentence; technical vocabulary in a business description: 'table' — say what is included, not how the SQL assembles it
