# P0-c sample — for Sunny's hand grading

**Scale caveat (ruled 2026-08-31, corrected same day):** this corpus spans both ends of the difficulty range — the de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across 21 procs in reporting/, including the 43-step USP_ED_SEPSIS whose invented flowsheet IDs created this gate) AND clean adversarial governance shapes. Difficulty is REAL; what is limited is SCALE: a 28-proc estate, not a multi-thousand-proc enterprise. These rates are MEASURED, not extrapolated, and any place we quote them must carry this sentence.

For each: the generated description, the fragment it describes, and the PARSED FACTS the gate checked it against. Grade the DESCRIPTION, not the rates.

## USP_ED_SEPSIS.sql · ABX
*outcome: clean* · parsed tables: #allmeds, config_value_set, med_mix_components, medications, ref_generic_med · parsed grain: order, visit

**Description**

- Encounters are included when the medication administered is an antibiotic or a mixture containing antibiotics, and the administration time occurs before the patient's departure from the emergency department (ED).
- Encounters are also included if the medication falls under the therapeutic class of antibiotics, ensuring that all relevant antibiotic administrations are captured.

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
*outcome: clean* · parsed tables: #labs_and_cultures, organisms · parsed grain: order, visit

**Description**

- Encounters are included when the CULTURE_TYPE is specified, ensuring that only relevant cases are considered for analysis.
- Encounters are included when they have associated ORDER_PROC_ID and ENCOUNTER_ID, providing a clear link to the procedures performed.
- Encounters are included when they contain critical values, allowing for the identification of significant results in the laboratory processes.

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

## USP_ED_SEPSIS.sql · All_LDAs
*outcome: clean* · parsed tables: #base_pop, config_value_set, line_device_airway · parsed grain: (unknown)

**Description**

- Records are included when the PLACEMENT_INSTANT is not null and falls between the ADT_ARRIVAL_TIME and ED_DEPARTURE_TIME.
- Records are included when the FLO_MEAS_ID is either '900112' for ETT or '900111' for IV, or when the VALUE_SET_ID is 3022 for SEPSIS_CVL_PLACEMENT. 
- Records are included when the LDA_PLACEMENT_TYPE is determined based on the specified FLO_MEAS_ID or VALUE_SET_ID criteria.

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

- Encounters are included when they have a CULTURE_TYPE associated with a negative result, ensuring that only those with no positive CRITICAL_VALUE_01 are considered.
- Encounters are included when the earliest MBOrderTime and CollectionTime are recorded, providing a clear timeline for negative cultures.
- Encounters are included in the analysis to identify patterns and trends related to negative cultures, contributing to overall quality improvement efforts.

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
*outcome: clean* · parsed tables: #base_pop, order_tracking_metrics · parsed grain: order, visit

**Description**

- Encounters are included when the ORDER_DTTM falls within the timeframe defined by ADT_ARRIVAL_TIME and ED_DEPARTURE_TIME.
- Encounters are tracked by their unique ENCOUNTER_ID, ensuring accurate association with corresponding orders.
- Encounters are linked to specific orders through the ORDER_ID, providing a clear timeline of order activity.

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

## USP_ED_SEPSIS.sql · PositiveCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

- Encounters are included when there is at least one positive culture result, indicated by a maximum critical value of 1.
- Each encounter captures the earliest order and collection times, ensuring timely tracking of culture results.
- The list of organisms associated with each encounter is aggregated, providing a comprehensive view of the identified organisms.

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

## USP_ED_SEPSIS.sql · SSOrderSetOSQ_PRL
*outcome: clean* · parsed tables: medication_orders_ext, procedure_orders_ext · parsed grain: order, visit

**Description**

- Encounters are included when they are associated with specific medication or procedure orders identified by the PRL_ORDERSET_IDs of 400002, 400007, 400003, 400004, 400006, 400005, and 4001326025.
- Encounters are also included when they fall under the Sepsis Pathway or HS ED ONCOLOGY SEPSIS RN PROTOCOL, as indicated by the PRL_ORDERSET_IDs of 400001 and 4001326023.

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

- Encounters are included when the recorded blood pressure measurement indicates hypotensive systolic blood pressure based on age-specific thresholds.
- Encounters for patients under 2 months are included if the systolic blood pressure is below 56, while those under 6 months are included if it is below 65.
- For patients aged 13 years and older, encounters are included when the systolic blood pressure is below 100.

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

- Encounters are included when they are categorized by ENCOUNTER_ID and LDA_PLACEMENT_TYPE, ensuring each encounter is uniquely identified in the timeline.
- Encounters are included when they are ordered by PLACEMENT_INSTANT, allowing for a chronological representation of events.
- Encounters are included when they are assigned a TIME_LINE number, facilitating the tracking of their sequence within the specified categories.

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

- Encounters are included when there is a valid LAB_TEST_TYPE associated with them, ensuring that only relevant lab tests are considered for analysis.  
- Encounters are included when they are uniquely identified by ENCOUNTER_ID and LAB_TEST_TYPE, allowing for precise tracking of lab test timelines.  
- Encounters are included when they are ordered by MBOrderTime, providing a chronological perspective on lab test administration.

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

- Records are included when the FLO_MEAS_ID is one of the specified values: '9000613042', '9000613043', '9000613044', '9000613045', '9000613047', '9000613048', or '9000613050'.
- Records are included when the RECORDED_TIME is not null, ensuring that only valid entries are considered.

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

- Patients are included when they have an encounter recorded with a valid in-shift date and out-shift date, ensuring their time in the department is accurately captured.
- Patients are included when their shifts span across multiple days, allowing for a comprehensive view of their care across different shifts.
- Patients are included when they meet specific criteria related to their admission and discharge times, ensuring that only relevant encounters are considered for analysis.

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
*outcome: clean* · parsed tables: #mainadmdetails, adt_events, departments, hospital_encounters · parsed grain: visit

**Description**

- Encounters are included when they are associated with admission or transfer in events, ensuring that only relevant patient interactions are captured.
- Encounters are included when they have a valid department ID, allowing for accurate departmental reporting and analysis.
- Encounters are included when they occur within specified time frames, such as previous PM, AM, and current PM periods, facilitating time-based evaluations of patient flow.

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

## USP_IP_SepsisPatientDates.sql · dateCTE
*outcome: clean* · parsed tables: #base_poptemp, datecte · parsed grain: patient, visit

**Description**

- Patients are included when they have an encounter that falls within the specified department rollup, excluding 'ER' and 'P-ER'.
- Patients are included when their expansion date is within the range defined by the expansion end date.
- Patients are included when their in-department and out-department times are recorded accurately during their stay.

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

- Patients are included when they have an encounter recorded with a valid in-shift date and out-shift date, ensuring accurate tracking of their time in the department.
- Patients are included when their shifts span across multiple days, allowing for comprehensive monitoring of their care across different shifts.
- Patients are included when they meet specific criteria for AM and PM shifts, ensuring that all relevant timeframes are accounted for in the analysis.

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

- Encounters are included when the InDepartmentTime and OutDepartmentTime are recorded, ensuring accurate tracking of patient movement within departments.
- Encounters are included when they fall within specified time frames, such as the previous PM, AM, and current PM periods, allowing for effective analysis of patient flow.
- Encounters are included when they have a unique identifier, ensuring each encounter is distinctly recognized for reporting and analysis purposes.

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

first pass violated: technical vocabulary in a business description: 'Row' — say what is included, not how the SQL assembles it

## USP_RPTS_ED_Sepsis.sql · ABX
*outcome: clean* · parsed tables: #base_pop, config_value_set, med_admin_records, med_mix_components, medication_orders, medications, or, previous, ref_generic_med · parsed grain: order, visit

**Description**

- Encounters are included when patients have a positive score and have received antibiotics administered in the emergency department before their departure time.
- Encounters are included when the antibiotics are given intravenously and the administration records indicate that the medication was either given, restarted, or applied during downtime.
- Encounters are included when the administered antibiotics are classified under specific therapeutic classes, ensuring compliance with treatment protocols.

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

- Encounters are included when the procedure orders fall within specific lab categories, ensuring relevance to critical lab results.
- Encounters are included when the order time occurs between the patient's arrival and departure times, capturing the full scope of care during their visit.
- Encounters are included when the results indicate abnormal or critical values, highlighting significant health concerns for timely intervention.

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

- Encounters are included when the procedure orders are related to specific lab tests, such as LAB006, LAB007, or LAB003, and the specimen source is a lumbar puncture.
- Encounters are included when the order time falls between the patient's arrival and departure times.
- Encounters are included when critical values are identified in the lab results, indicating abnormal or critical conditions.

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

- Encounters are included when the maximum value of CRITICAL_VALUE_01 is zero, indicating no critical results were recorded.
- Each encounter reflects the earliest order time and collection time for blood culture results, categorized under 'Negative' organisms.
- This metric helps identify encounters that did not yield any critical findings, supporting quality assurance in patient care.

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

- Encounters are included when the maximum critical value recorded is zero, indicating no significant growth or contamination.
- Each encounter reflects the earliest order time and collection time associated with negative culture results.
- Encounters are categorized under 'Negative' to signify instances of no growth or contamination with normal flora.

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

- Encounters are included when the maximum value of CRITICAL_VALUE_01 is 0, indicating no critical results were observed.
- Each encounter reflects the earliest recorded order time and collection time for the associated results.
- Encounters are categorized under 'Negative' to signify the absence of critical findings.

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
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

- Encounters are included when they have a recorded critical value indicating a significant finding in the blood culture results.
- Each encounter reflects the earliest order time and collection time associated with the positive culture results.
- The organism list for each encounter is compiled, highlighting the relevant external names of organisms identified during the testing process.

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

## USP_RPTS_ED_Sepsis.sql · PositiveCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

- Encounters are included when they have a recorded CRITICAL_VALUE_01 indicating a critical condition.
- Each encounter captures the earliest ORDER_TIME and the corresponding CollectionTime for accurate tracking.
- The list of organisms associated with each encounter is compiled, ensuring critical values are highlighted for review.

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

## USP_RPTS_ED_Sepsis.sql · PositiveCultures
*outcome: clean* · parsed tables: — · parsed grain: visit

**Description**

- Encounters are included when they have a recorded critical value indicating a significant finding, ensuring that only relevant cases are considered for analysis.
- Each encounter captures the earliest order time and collection time, providing a clear timeline for the events associated with the culture results.
- The organism list for each encounter is compiled, highlighting the relevant organisms identified during the culture process, which aids in understanding the clinical context.

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
*outcome: clean* · parsed tables: #base_pop, lab_order_results, organisms, procedure_orders · parsed grain: order, visit

**Description**

- Encounters are included when the order time of the procedure falls between the patient's arrival and departure times.
- Encounters are included when the results indicate a critical value, signifying an abnormal or critical condition.
- Encounters are included when they are associated with specific laboratory procedures related to urine culture testing.

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
