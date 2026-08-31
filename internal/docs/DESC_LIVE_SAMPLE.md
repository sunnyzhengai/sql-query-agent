# P0-c sample — for Sunny's hand grading

**Scale caveat (ruled 2026-08-31, corrected same day):** this corpus spans both ends of the difficulty range — the de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across 21 procs in reporting/, including the 43-step USP_ED_SEPSIS whose invented flowsheet IDs created this gate) AND clean adversarial governance shapes. Difficulty is REAL; what is limited is SCALE: a 28-proc estate, not a multi-thousand-proc enterprise. These rates are MEASURED, not extrapolated, and any place we quote them must carry this sentence.

For each: the generated description, the fragment it describes, and the PARSED FACTS the gate checked it against. Grade the DESCRIPTION, not the rates.

## USP_ED_SEPSIS.sql · ABX
*outcome: clean* · parsed tables: #allmeds, config_value_set, med_mix_components, medications, ref_generic_med · parsed grain: order, visit

**Description**

- This step selects records of medication administration, specifically focusing on encounters involving antibiotics or antibiotic mixtures, capturing the encounter ID, order medication ID, administration time, and medication name.
- Membership is determined by the condition that the administration time must occur before the patient's departure time from the emergency department, and the medication must either be classified as an antibiotic or be part of a mixture containing antibiotics.
- Additionally, only the primary agent from antibiotic mixtures is included, ensuring that the analysis focuses on the most relevant medication administered during the encounter.

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

- This step selects key laboratory culture data, including encounter identifiers, order processing details, timing metrics, and critical values, from the temporary table `#Labs_and_Cultures` and the `ORGANISMS` table.
- It specifically filters the results to include only those records where the `CULTURE_TYPE` is not null, ensuring that only relevant culture types are considered for further analysis.
- The join with the `ORGANISMS` table enriches the dataset by providing the external names of organisms associated with each culture, enhancing the contextual understanding of the laboratory results.

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

- This step selects encounter IDs along with specific airway device measurements and placement types from the base population, focusing on instances where the placement occurred within the defined arrival and departure times.
- Membership is determined by the presence of valid placement timestamps and specific measurement IDs related to endotracheal tubes (ETT) and peripheral intravenous (IV) devices, as well as a distinct value set for central venous line (CVL) placements.

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

- This step selects unique encounter identifiers and culture types from the AllCultures dataset, focusing on instances where no positive critical values are recorded.
- It aggregates the minimum order and collection times for each encounter and culture type, ensuring that only those with a maximum critical value of zero are included.
- The resulting dataset is categorized under 'Negative' in the OrganismList, highlighting encounters that did not yield any positive culture results.

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

- This step selects key identifiers and timestamps related to orders, specifically the encounter ID, order ID, order datetime, and order set ID from the base population dataset.
- It filters the data to include only those orders that occurred within the timeframe defined by the patient's arrival and departure times, ensuring relevance to the specific patient encounters.
- The inner join with the ORDER_TRACKING_METRICS table ensures that only orders associated with the relevant encounters are included in the final dataset.

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

- This step selects unique encounter identifiers and culture types from the AllCultures dataset, along with the earliest order and collection times for each combination.
- It aggregates the names of organisms associated with each encounter, providing a comprehensive list while defaulting to 'Critical Value' if no organisms are present.
- Membership is determined by the presence of at least one critical value, as indicated by the condition that the maximum value of CRITICAL_VALUE_01 must equal 1, ensuring only positive cultures are included.

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

- This step selects encounter IDs, order timestamps, and associated order set IDs from medication and procedure orders, focusing on specific order set IDs that are relevant to sepsis pathways and protocols.
- Membership is determined by the inclusion of order IDs that match predefined order set IDs, ensuring that only relevant clinical orders related to sepsis are captured for analysis.
- The query consolidates data from multiple sources, including medication and procedure orders, to provide a comprehensive view of orders associated with sepsis treatment protocols.

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

- This step selects encounter IDs and recorded times for blood pressure measurements from the #Flowsheets table, specifically focusing on entries where the measurement ID is '95' and the recorded time falls between the patient's arrival and departure times in the emergency department.

- It calculates a hypotensive systolic blood pressure value by extracting and converting the systolic component from the measurement value, applying specific age-related criteria to determine if the patient meets the hypotension condition.

- Membership in the hypotension category is determined based on age and systolic blood pressure thresholds, with distinct criteria for infants, young children, and adolescents, ensuring accurate assessment tailored to the patient's age group.

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

- This step selects all records from the `All_LDAs` table, enriching the dataset with a sequential identifier for each record based on the `ENCOUNTER_ID` and `LDA_PLACEMENT_TYPE`.
- The `ROW_NUMBER()` function is utilized to create a unique timeline for each encounter and placement type, ordered by the `PLACEMENT_INSTANT`, ensuring that the sequence of placements is accurately represented.
- Membership in this dataset is determined by the combination of `ENCOUNTER_ID` and `LDA_PLACEMENT_TYPE`, allowing for a detailed analysis of placement occurrences over time within each encounter.

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

- This step selects all records from the `#Labs_and_Cultures` table, focusing specifically on entries where the `LAB_TEST_TYPE` is not null, ensuring that only relevant lab test data is included for analysis.
- It utilizes the `ROW_NUMBER()` function to assign a sequential number to each lab test within the same `ENCOUNTER_ID` and `LAB_TEST_TYPE`, ordered by the `MBOrderTime`, thereby creating a timeline of lab tests for each encounter.
- The result is a structured dataset that allows for the identification of the order in which lab tests were conducted, facilitating better insights into patient care timelines and lab test management.

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

- This step selects the unique identifiers (FSD_ID) and recorded timestamps (Recorded_Time) of specific measurements from the flowsheet records associated with inpatient data.
- Membership is determined by the inclusion of specific flow measurement IDs (FLO_MEAS_ID) and the requirement that the recorded time is not null, ensuring only valid and relevant data entries are considered.

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

- This step selects encounter records along with their associated shift dates, department information, and patient details, focusing on encounters that are not in the emergency department (ER or P-ER) and have a specific departmental ranking (inDeptRN = 1).
- It calculates the number of shifts per day based on the shift type (AM or PM) and the relationship between the in and out shift dates, ensuring that only relevant records are included based on defined conditions for both AM and PM shifts.
- The selection criteria also include the expansion of dates for encounters that span multiple days, allowing for a comprehensive view of patient encounters across shifts while maintaining the integrity of the data by filtering out non-relevant departments.

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

- This step selects patient encounter details, including encounter IDs, effective timestamps for admissions and transfers, and associated department information, ensuring a comprehensive view of patient movements within the hospital.
- It filters the data to include only relevant "in" events, specifically admissions and transfers, while excluding any deleted or canceled events to maintain data integrity.
- The query also handles potential missing department information by providing default labels for unspecified or unknown departments, ensuring clarity in reporting.

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

- This step selects patient encounter data, including key identifiers such as ENCOUNTER_ID, PATIENT_ID, and departmental information, while focusing on inpatient stays that are not categorized under 'ER' or 'P-ER'.
- It generates a date range for each encounter by expanding the initial admission date (Expansion Date) to include all days up to the discharge date (Expansion End Date), ensuring that only valid inpatient stays are considered.
- The selection criteria ensure that only encounters with a defined duration between the Expansion Date and Expansion End Date are included, facilitating a comprehensive analysis of inpatient department utilization.

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

- This step selects patient encounter records, including key details such as encounter ID, department information, and shift timings, from a temporary dataset while excluding emergency department cases.
- It determines the number of shifts per day based on the shift start and end dates, categorizing them into AM and PM shifts, and includes conditions to identify whether the records are for the start or end of a shift.
- The selection criteria ensure that only relevant records with a valid department rollup and specific shift conditions are included, facilitating accurate tracking of patient encounters across shifts.

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
*outcome: clean* · parsed tables: ip_sepsisencounterswlocations · parsed grain: visit

**Description**

- This step selects key encounter details, including encounter ID, in and out department times, department identifiers, and calculated time intervals for both previous and current day shifts (AM and PM) from the `IP_SepsisEncountersWLocations` table.
- Membership is determined by the presence of valid encounter records, with specific time calculations applied to both the in and out department times, ensuring that the data reflects accurate timeframes for patient encounters within the specified departments.
- The use of `COALESCE` ensures that if an out department time is not available, the current date and time are used, allowing for a comprehensive view of encounters even when certain data points are missing.

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

## USP_RPTS_ED_Sepsis.sql · ABX
*outcome: clean* · parsed tables: #base_pop, config_value_set, med_admin_records, med_mix_components, medication_orders, medications, or, previous, ref_generic_med · parsed grain: order, visit

**Description**

- This step selects records of administered antibiotics (ABX) for patients with a positive score, capturing details such as encounter ID, medication order ID, administration time, and medication name.
- Membership is determined by ensuring that the antibiotics were administered within the emergency department before patient departure, specifically via intravenous route, and only includes records with valid administration actions (e.g., given, restarted, or applied).
- The selection is further refined to include only those medications classified as antibiotics, based on predefined therapeutic class codes and a specific list of medications.

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

- This step selects key data related to blood culture results, including encounter IDs, order details, result times, and critical value indicators, to assess patient conditions effectively.
- Membership is determined by filtering results based on specific procedure orders related to laboratory tests and ensuring that the order time falls within the patient's admission and departure times.
- Additionally, it identifies abnormal or critical results by flagging them based on predefined criteria, enhancing the focus on significant clinical findings.

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

- This step selects critical laboratory results associated with patient encounters, including details such as encounter ID, order procedure ID, order time, result time, and the value of the results.
- Membership is determined by filtering for specific procedure orders related to lumbar punctures and ensuring that the order time falls within the patient's arrival and departure times.
- Additionally, it identifies results flagged as abnormal or critical based on predefined criteria, enhancing the focus on significant clinical findings.

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

- This step selects the earliest order time and collection time for each unique encounter in the BloodCultureResults dataset, identifying instances where no critical values were recorded.
- It groups the results by encounter ID and filters the data to include only those encounters that have a maximum critical value of zero, indicating a lack of significant findings.
- The output categorizes these encounters under a 'Negative' organism list, providing insights into cases that did not yield positive results.

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

- This step selects the earliest order time and collection time for each unique encounter in the UrineCultureResults dataset, identifying instances where no growth or contamination with normal flora is present.
- Membership is determined by grouping the results by ENCOUNTER_ID and applying a condition that ensures the maximum critical value is zero, indicating a negative culture result.
- The output categorizes these encounters under the label 'Negative', providing insights into cases that do not show significant microbial growth.

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

- This step selects the unique `ENCOUNTER_ID` from the `CsfCultureResults` table, along with the earliest `ORDER_TIME` and `COMP_OBS_INST_TM` for each encounter.
- Membership is determined by the condition that the maximum value of `CRITICAL_VALUE_01` for each encounter must equal zero, indicating no critical results were observed.
- The results are categorized under the label 'Negative' in the `OrganismList`, signifying that these encounters did not yield any positive culture results.

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

- This step selects the earliest order time and collection time for each unique encounter in the BloodCultureResults dataset, ensuring a comprehensive view of the timing associated with each encounter.
- It aggregates the external names of organisms detected during the blood culture process, providing a consolidated list of organisms for each encounter, which is crucial for clinical decision-making.
- Membership in this dataset is determined by encounters that have at least one critical value flagged, as indicated by the condition that the maximum value of CRITICAL_VALUE_01 must equal 1.

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

- This step selects unique encounter identifiers (ENCOUNTER_ID) from the UrineCultureResults table, along with the earliest order time (MBOrderTime) and collection time (CollectionTime) for each encounter.
- It aggregates the external names of organisms associated with each encounter into a single list (OrganismList), ensuring that only encounters with a maximum critical value of 1 are included in the results.
- The use of the COALESCE function ensures that if no organisms are found, a default label of 'Critical Value' is assigned, maintaining clarity in the reporting of results.

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

- This step selects the earliest order time and collection time for each unique encounter, along with a consolidated list of organisms associated with that encounter.
- Membership is determined by encounters that have at least one critical value flagged as positive, ensuring that only significant results are included in the analysis.
- The output provides a focused view of critical culture results, facilitating targeted decision-making in clinical settings.

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

- This step selects urine culture results associated with patient encounters, including key identifiers such as encounter ID, order procedure ID, and result timestamps, along with critical value indicators for abnormal or critical results.
- Membership is determined by filtering results based on specific procedure IDs related to laboratory orders and ensuring that the order time falls within the patient's admission and departure times.
- Additionally, it includes organism information by joining with the organisms table, allowing for a comprehensive view of the results linked to each encounter.

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
