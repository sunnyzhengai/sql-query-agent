# P0-c sample — for Sunny's hand grading

**Scale caveat (ruled 2026-08-31, corrected same day):** this corpus spans both ends of the difficulty range — the de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across 21 procs in reporting/, including the 43-step USP_ED_SEPSIS whose invented flowsheet IDs created this gate) AND clean adversarial governance shapes. Difficulty is REAL; what is limited is SCALE: a 28-proc estate, not a multi-thousand-proc enterprise. These rates are MEASURED, not extrapolated, and any place we quote them must carry this sentence.

For each: the generated description, the fragment it describes, and the PARSED FACTS the gate checked it against. Grade the DESCRIPTION, not the rates.

## USP_ED_SEPSIS.sql · #Pressors
*outcome: clean* · parsed tables: grouper_med_records · parsed grain: visit

**Description**

This SQL selects encounters related to specific medications administered during a defined time frame.

- Encounter IDs are included where the TAKEN_TIME falls between ADT_ARRIVAL_TIME and ED_DEPARTURE_TIME.
- Only medications with GROUPER_IDs of '8000100', '8000101', '8000102', '8000103', and '8000104' are considered.
- The TAKEN_TIME is ordered to create a timeline for each encounter, with distinct entries based on ENCOUNTER_ID.

**Fragment**

```sql
SELECT DISTINCT	-- reduce cardinality

	ENCOUNTER_ID

	, TAKEN_TIME

	, MEDICATION_NAME

	, ROW_NUMBER() OVER(PARTITION BY ENCOUNTER_ID ORDER BY TAKEN_TIME) AS TIME_LINE

INTO #Pressors 

FROM #AllMeds

	INNER JOIN [dbo].GROUPER_MED_RECORDS VCG ON [#AllMeds].MEDICATION_ID = [VCG].EXP_MEDS_LIST_ID

WHERE 1=1

	AND TAKEN_TIME BETWEEN ADT_ARRIVAL_TIME AND ED_DEPARTURE_TIME

	AND [VCG].GROUPER_ID IN ('8000100'		-- HS RX EPINEPHRINE SEPSIS

							, '8000101'		-- HS RX DOPAMINE SEPSIS

							, '8000102'		-- HS RX DOBUTAMINE SEPSIS

							, '8000103'		-- HS RX MILRINONE SEPSIS

							, '8000104'		-- HS RX NOREPINEPHRINE SEPSIS

						)

;
```

## USP_IP_SEPSIS.sql · #MedGroupers
*outcome: recovered* · parsed tables: grouper_groups · parsed grain: (unknown)

**Description**

This SQL selects records of medical groupers.

- Inclusion is determined by the grouper id being exactly '800011'.

**Fragment**

```sql
SELECT vcg.GROUPER_LIST VCG_ID

	INTO #MedGroupers

	FROM [dbo].[GROUPER_GROUPS] vcg

	WHERE vcg.GROUPER_ID IN ('800011')
```

first pass violated: column name in a business description: 'GROUPER_ID' — write from its dictionary description, or say 'grouper id'

## USP_IP_SEPSIS.sql · #RouteExclusions
*outcome: recovered* · parsed tables: config_grouper_categories · parsed grain: (unknown)

**Description**

This SQL selects records of route exclusions.

- Grouper ID must be '800008'.
- Includes the code '11'.
- The selection is based on the presence of these specific values.

**Fragment**

```sql
SELECT vcg.LIST_CAT_VALUE_CODE CAT_ID

	INTO #RouteExclusions

	FROM [dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800008')

	UNION 

	SELECT '11'
```

first pass violated: column name in a business description: 'GROUPER_ID' — write from its dictionary description, or say 'grouper id'

## USP_IP_SepsisDetails.sql · #BolusMeds
*outcome: clean* · parsed tables: grouper_compiled_list · parsed grain: (unknown)

**Description**

This SQL selects bolus medication records.

- Compiled context must be 'MEDS'.
- Base grouper ID must be '800009'.

**Fragment**

```sql
SELECT vcg.GROUPER_RECORDS_NUMERIC_ID MED_ID

	INTO #BolusMeds

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'MEDS'

	AND vcg.BASE_GROUPER_ID IN ('800009')
```

## USP_IP_SepsisDetails.sql · #RouteExclusions
*outcome: recovered* · parsed tables: config_grouper_categories · parsed grain: (unknown)

**Description**

Records of route exclusions.

- Grouper ID must be '800008'.
- Includes the code '11'.

**Fragment**

```sql
SELECT vcg.LIST_CAT_VALUE_CODE CAT_ID

	INTO #RouteExclusions

	FROM [dbo].[CONFIG_GROUPER_CATEGORIES] vcg

	WHERE vcg.GROUPER_ID IN ('800008')

	UNION 

	SELECT '11'
```

first pass violated: column name in a business description: 'GROUPER_ID' — write from its dictionary description, or say 'grouper id'

## USP_IP_SepsisEncounters.sql · #Base_Pop_ENC_Reason
*outcome: salvaged* · parsed tables: diagnoses, encounter_diagnoses · parsed grain: visit

**Description**

This SQL selects encounters with associated diagnosis names.

- Encounter IDs must be present.
- Diagnosis names are aggregated, with a range of values from the lowest to the highest actual diagnosis names, with a total count of distinct diagnosis names included.

**Fragment**

```sql
SELECT DISTINCT cat.ENCOUNTER_ID

	, STRING_AGG(DIAG.DX_NAME,  ' % ') AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM #MainAdmDetails cat

INNER JOIN [dbo].[ENCOUNTER_DIAGNOSES] EDX ON EDX.ENCOUNTER_ID = cat.ENCOUNTER_ID AND EDX.LINE >= 1

INNER JOIN [dbo].[DIAGNOSES] DIAG ON DIAG.DX_ID = EDX.DX_ID

GROUP BY cat.ENCOUNTER_ID
```

first pass violated: column name in a business description: 'DX_ID' — write from its dictionary description, or say 'dx id'

## USP_IP_SepsisEncounters.sql · #MainAdmDetails
*outcome: salvaged* · parsed tables: calendar_dates, departments, hospital_encounters, hospital_transactions, locations, patient_demographics_race, patients, ref_discharge_disposition, ref_ethnic_group, ref_patient_race · parsed grain: patient, visit

**Description**

This SQL selects distinct inpatient admissions.

- The service date of a charge falls between @dStartDate and @dEndDate.
- The location's pos type is null.

**Fragment**

```sql
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

AND loc.POS_TYPE IS NULL
```

first pass violated: ungrounded filter claim: '- Inclusion requires that HE.INP_ADM_DATE is not null.'; column name in a business description: 'INP_ADM_DATE' — write from its dictionary description, or say 'inp adm date'; column name in a business description: 'POS_TYPE' — write from its dictionary description, or say '

## USP_IP_SepsisPatientDates.sql · #Base_PopTemp
*outcome: recovered* · parsed tables: config_value_set, ip_sepsisencounterswlocations · parsed grain: patient, visit

**Description**

This SQL selects a set of patient encounters related to inpatient data.

- Inclusion is determined by the ADTDepartmentID being part of the value set with ID 3031.
- The InDepartmentTime and OutDepartmentTime must be recorded.
- The BirthDate must be present for each patient.

**Fragment**

```sql
SELECT DISTINCT

	main.[PATENCENCID] ENCOUNTER_ID

	, main.[PatientID] PATIENT_ID

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

	, main.ENCORDER [ENC_ID Order]

	, main.UniqueRow

INTO #Base_PopTemp

FROM [reporting].[IP_SepsisEncountersWLocations] main

INNER JOIN [reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = main.[ADTDepartmentID]

			AND cvs.VALUE_SET_ID = 3031
```

first pass violated: column name in a business description: 'VALUE_SET_ID' — write from its dictionary description, or say 'value set id'

## USP_IP_SepsisPatientDates.sql · #MainAdmDetails
*outcome: recovered* · parsed tables: ip_sepsisencounters · parsed grain: patient, visit

**Description**

This SQL selects patient encounter details.

- Inclusion is determined by distinct values of [PATENCENCID], [PatientID], and [InpatientDataID].
- The [EthnicGroup] can include values such as [Ethnic Group] and [Race].
- A placement time is recorded for [ADTArrivalTime], [HospAdmsnTime], and [HospDischTime].

**Fragment**

```sql
SELECT DISTINCT

	[PATENCENCID] ENCOUNTER_ID

	, [PatientID] PATIENT_ID

	, [PATIENTMRN] PATIENT_MRN

	, [PatientName] PATIENT_NAME

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

FROM [reporting].[IP_SepsisEncounters]
```

first pass violated: ungrounded value: '2000' not in the SQL; ungrounded value: '1001' not in the SQL; ungrounded value: 'Hispanic' not in the SQL; ungrounded value: 'Admitted' not in the SQL; ungrounded value: 'Non-Hispanic' not in the SQL; ungrounded value: 'Unknown' not in the SQL; ungrounded value: 'Discharged' not 

## USP_IP_SepsisScreeningAudit.sql · #FlwshtLst
*outcome: salvaged* · parsed tables: flowsheet_measurements, flowsheet_records · parsed grain: visit

**Description**

This SQL selects encounters with associated measurements.

- Recorded time must fall between in dept date and out dept date.
- Encounter id must be present, and documented department id must be recorded.

**Fragment**

```sql
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
```

first pass violated: column name in a business description: 'ENCOUNTER_ID' — write from its dictionary description, or say 'encounter id'; column name in a business description: 'FLO_MEAS_ID' — write from its dictionary description, or say 'flo meas id'; column name in a business description: 'RECORDED_TIME' — write fro

## USP_IP_SepsisScreeningAudit.sql · #FlwshtLstHuddleODScore
*outcome: recovered* · parsed tables: flowsheet_measurements, flowsheet_records · parsed grain: visit

**Description**

This SQL selects encounters with specific measurements.

- Only includes measurements where flo meas id is in ('9000002705', '9000002732', '9000002733', '9000002706', '9000002734', '9000002707').
- Only includes measurements where recorded time is between the in dept date and out dept date.
- Only includes measurements where recorded time is less than or equal to the recorded time of the corresponding encounter.

**Fragment**

```sql
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
```

first pass violated: selected-not-filtered: '- Only includes measurements where MEAS_VALUE is not NULL.' — the concept appears only in the SELECT list, never in a condition; column name in a business description: 'FLO_MEAS_ID' — write from its dictionary description, or say 'flo meas id'; column name in a business descr

## USP_IP_SepsisScreeningAudit.sql · #ODScores
*outcome: clean* · parsed tables: grouper_compiled_list · parsed grain: (unknown)

**Description**

This SQL selects records identified by FLO_ID.

- The compiled context must be 'FLO'.
- The base grouper ID must be '800006'.

**Fragment**

```sql
SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO #ODScores

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800006')
```

## USP_IP_SepsisShiftCompliance.sql · #Base_PopTemp
*outcome: recovered* · parsed tables: config_value_set, ip_sepsisencounterswlocations · parsed grain: patient, visit

**Description**

This SQL selects encounters for patients in specific departments.

- Inclusion is determined by the adt department id being present and not null.
- The in dttm must fall within the defined time ranges: between the previous PM start and end, or between the AM start and end.
- The out dttm must also fall within the defined time ranges: between the previous PM start and end, or between the AM start and end.
- The value set id must equal 3031.

**Fragment**

```sql
WITH vaplh AS

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



SELECT DISTINCT

	main.ENCOUNTER_ID

	, main.PATIENT_ID

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

	, ROW_NUMBER() OVER (PARTITION BY main.ENCOUNTER_ID, vaplh.IN_DTTM ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM) [inDeptRN]

	, ROW_NUMBER() OVER (PARTITION BY main.ENCOUNTER_ID ORDER BY vaplh.IN_DTTM, vaplh.OUT_DTTM ) [ENC_ID Order]

	, vaplh.[Unique Row]

INTO #Base_PopTemp

FROM #MainAdmDetails main

INNER JOIN  vaplh ON vaplh.ENCOUNTER_ID = main.ENCOUNTER_ID AND vaplh.ADT_DEPARTMENT_ID IS NOT NULL /*[dbo].V_PATIENT_LOCATION_HISTORY*/

INNER JOIN [reports].[CONFIG_VALUE_SET] cvs ON cvs.CODE = vaplh.ADT_DEPARTMENT_ID

			AND cvs.VALUE_SET_ID = 3031
```

first pass violated: column name in a business description: 'ADT_DEPARTMENT_ID' — write from its dictionary description, or say 'adt department id'; column name in a business description: 'IN_DTTM' — write from its dictionary description, or say 'in dttm'; column name in a business description: 'OUT_DTTM' — write from i

## USP_IP_SepsisShiftCompliance.sql · #FlwshtLst
*outcome: recovered* · parsed tables: flowsheet_measurements, flowsheet_records · parsed grain: visit

**Description**

This SQL selects encounters with specific measurements.

- Included measurements have a flo meas id that is in a defined list.
- The recorded time falls between the shift start and shift end.
- The recorded time is between the in dttm and out dttm for the documented department id.

**Fragment**

```sql
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
```

first pass violated: column name in a business description: 'FLO_MEAS_ID' — write from its dictionary description, or say 'flo meas id'; column name in a business description: 'IN_DTTM' — write from its dictionary description, or say 'in dttm'; column name in a business description: 'OUT_DTTM' — write from its dictionar

## USP_RPTS_ED_Sepsis.sql · #BasePopABX
*outcome: clean* · parsed tables: config_value_set, med_admin_records, med_mix_components, medication_orders, medications, or, previous, ref_generic_med · parsed grain: order, visit

**Description**

This SQL selects encounters with administered antibiotics.

- Inclusion requires that the medication administration time is recorded and falls before the patient's ED departure time.
- Only IV medications are included, as indicated by a medication route code of 11.
- The MAR action codes must be one of the following: '1', '7', '102', '105', '113', '114', '115', '122', '124', '132', '143', '1604', '1605', '1607', '6', or '99'.

**Fragment**

```sql
WITH ABX AS

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



SELECT

	ABX.ENCOUNTER_ID

	,ABX.ORDER_MED_ID

	,ABX.NAME

	,ABX.ABX_ADMIN_TIME

	,ROW_NUMBER() OVER(PARTITION BY ABX.ENCOUNTER_ID ORDER BY ABX.ABX_ADMIN_TIME) TIME_LINE



INTO #BasePopABX

FROM ABX						

;
```

## USP_RPTS_ED_Sepsis.sql · #Base_Pop
*outcome: recovered* · parsed tables: departments, ed_encounters_dm, ed_encounters_fact, hospital_encounters, locations, patient_demographics_race, patients, ref_ed_disposition, ref_ethnic_group, ref_patient_race · parsed grain: patient, visit

**Description**

This SQL selects patient encounters.

- Inclusion requires that the adt arrival date falls between the specified start and end dates.
- The ed disposition code must match a recorded code in the reference for emergency department dispositions.
- The ethnic group code must match a recorded code in the reference for ethnic groups. 

Additional values include patient IDs, encounter IDs, and a range of ages at arrival in months and years.

**Fragment**

```sql
SELECT DISTINCT

	HE.ENCOUNTER_ID

	, HE.PATIENT_ID

	, PAT.PATIENT_MRN

	, PAT.PATIENT_NAME

	, REG.NAME AS [Ethnic Group]

	, RPR.NAME AS [Race]

	, EEF.AGE_AT_ARRIVAL_MONTHS

	, EEF.AGE_AT_ARRIVAL_YEARS

	, HE.INPATIENT_DATA_ID

	, HE.ADT_ARRIVAL_TIME

	, EED.TRIAGE_START_DTTM

	, EED.TRIAGE_END_DTTM

	, HE.HOSP_ADMSN_TIME

	, HE.HOSP_DISCH_TIME

	, HE.INP_ADM_DATE

	, HE.ED_DEPARTURE_TIME

	, HE.ED_DISPOSITION_CODE

	, REDI.NAME AS [Disposition]

	, LOC.LOCATION_ABBR [Location]

	, FLOOR(DATEDIFF(day,PAT.BIRTH_DATE,HE.ADT_ARRIVAL_TIME)) AS AGE_IN_DAYS ---ADDED V_DEV003 6/15/2023 TKT-007 

	, FLOOR(DATEDIFF(MM,PAT.BIRTH_DATE,COALESCE(HE.ADT_ARRIVAL_TIME,HE.ADT_ARRIVAL_TIME)) ) AS AGE_MONTHS  ---ADDED V_DEV003 6/15/2023 TKT-007  (AGE IN MONTHS IS SHOWING AS 1 WHEN ITS ONLY 2 WEEKS, ETC.)

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,HE.ADT_ARRIVAL_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,HE.ADT_ARRIVAL_TIME)) + DATENAME(YEAR, CONVERT(DATE, HE.ADT_ARRIVAL_TIME)) AS DATE_STAMP



INTO #Base_Pop



FROM [dbo].ED_ENCOUNTERS_FACT EEF



	INNER JOIN [dbo].HOSPITAL_ENCOUNTERS HE ON EEF.ENCOUNTER_ID = HE.ENCOUNTER_ID

	INNER JOIN [dbo].ED_ENCOUNTERS_DM EED ON EED.ENCOUNTER_ID = EEF.ENCOUNTER_ID

	INNER JOIN [dbo].PATIENTS PAT ON PAT.PATIENT_ID = HE.PATIENT_ID

	LEFT OUTER JOIN [dbo].REF_ED_DISPOSITION REDI ON REDI.ED_DISPOSITION_CODE = HE.ED_DISPOSITION_CODE

	LEFT OUTER JOIN [dbo].REF_ETHNIC_GROUP REG ON REG.ETHNIC_GROUP_CODE = PAT.ETHNIC_GROUP_CODE

	LEFT OUTER JOIN [dbo].PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PATIENT_ID = PAT.PATIENT_ID AND RACE.LINE=1

	LEFT OUTER JOIN [dbo].REF_PATIENT_RACE RPR ON RPR.PATIENT_RACE_CODE = RACE.PATIENT_RACE_CODE

	LEFT OUTER JOIN [dbo].DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = HE.DEPARTMENT_ID

	LEFT OUTER JOIN [dbo].LOCATIONS LOC ON LOC.LOC_ID = DEP.REV_LOC_ID



WHERE 1=1

	AND EEF.ADT_ARRIVAL_DATE BETWEEN @dStartDate AND @dEndDate

;
```

first pass violated: column name in a business description: 'ADT_ARRIVAL_DATE' — write from its dictionary description, or say 'adt arrival date'; column name in a business description: 'ED_DISPOSITION_CODE' — write from its dictionary description, or say 'ed disposition code'; column name in a business description: 'ET

## USP_RPTS_ED_Sepsis.sql · #Base_Pop_ENC_Reason
*outcome: emptied* · parsed tables: encounter_visit_reasons, visit_reasons · parsed grain: visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
SELECT DISTINCT   CAT.ENCOUNTER_ID,

        STUFF((	SELECT ';' + CONVERT(VARCHAR,VR.REASON_VISIT_NAME)-- AS [text()]

                FROM #Base_Pop SUB

					INNER JOIN [dbo].ENCOUNTER_VISIT_REASONS RSN ON RSN.ENCOUNTER_ID = SUB.ENCOUNTER_ID AND RSN.LINE>1

					INNER JOIN [dbo].VISIT_REASONS VR ON VR.REASON_VISIT_ID = RSN.ENC_REASON_ID

				WHERE

                    SUB.ENCOUNTER_ID = CAT.ENCOUNTER_ID

				ORDER BY LINE

                    FOR XML PATH('')

               ), 1, 1, '' )

            AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM  #Base_Pop CAT

;
```

first pass violated: column name in a business description: 'ENCOUNTER_ID' — write from its dictionary description, or say 'encounter id'; column name in a business description: 'REASON_VISIT_ID' — write from its dictionary description, or say 'reason visit id'; technical vocabulary in a business description: 'dataset' 

## USP_RPTS_IP_SEPSIS.sql · #Base_Pop
*outcome: emptied* · parsed tables: config_value_set, patients · parsed grain: patient, visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
SELECT 

	#Main.ENCOUNTER_ID

	, #Main.PATIENT_ID

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

INNER JOIN dbo.PATIENTS PAT ON PAT.PATIENT_ID = #Main.PATIENT_ID

cross apply (

			SELECT

				ADTIN.ENCOUNTER_ID,

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

				.HOSPITAL_ENCOUNTERS HENC

				INNER JOIN .ADT_EVENTS ADTIN ON ADTIN.ENCOUNTER_ID = HENC.ENCOUNTER_ID

				LEFT OUTER JOIN .ADT_EVENTS ADTOUT ON ADTIN.NEXT_OUT_EVENT_ID = ADTOUT.EVENT_ID

				LEFT OUTER JOIN .DEPARTMENTS DEP ON ADTIN.DEPARTMENT_ID = DEP.DEPARTMENT_ID

				left outer join .BED_CONFIG bed on bed.BED_STAY_ID = adtin.BED_STAY_ID

			WHERE

				HENC.ENCOUNTER_ID = #Main.ENCOUNTER_ID

				and ADTIN.EVENT_TYPE_CODE IN (1, 3) --Only look at "in" events (Admission and Transfer In, LOA Return)

				AND ADTIN.EVENT_SUBTYPE_CODE <> 2 --Exclude deleted/canceled events

)ADT

INNER JOIN reports.CONFIG_VALUE_SET CVS ON CVS.CODE = ADT.adt_DEPARTMENT_ID

			AND CVS.VALUE_SET_ID = 3031
```

first pass violated: ungrounded table claim: 'ADT_EVENT_TYPE_CODE' — the fragment reads #main, config_value_set, patients; ungrounded table claim: 'ADT_EVENT_SUBTYPE_CODE' — the fragment reads #main, config_value_set, patients

## USP_RPTS_IP_SEPSIS.sql · #Base_Pop_ENC_Reason
*outcome: emptied* · parsed tables: diagnoses, encounter_diagnoses · parsed grain: visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
SELECT

	sub.ENCOUNTER_ID,

	string_agg(DIAG.DX_NAME,'% ') AS [AllEncReasons]

INTO #Base_Pop_ENC_Reason

FROM  #Main sub

	INNER JOIN dbo.ENCOUNTER_DIAGNOSES EDX ON EDX.ENCOUNTER_ID = SUB.ENCOUNTER_ID AND EDX.LINE>1

	INNER JOIN dbo.DIAGNOSES DIAG ON DIAG.DX_ID = EDX.DX_ID

group by sub.ENCOUNTER_ID
```

first pass violated: column name in a business description: 'DX_NAME' — write from its dictionary description, or say 'dx name'; column name in a business description: 'ENCOUNTER_DIAGNOSES' — write from its dictionary description, or say 'encounter diagnoses'; technical object in a business description: '#Main' — the so

## USP_RPTS_IP_SEPSIS.sql · #Base_Pop_Severe_ED_Scores
*outcome: recovered* · parsed tables: flowsheet_measurements, flowsheet_records, hospital_encounters · parsed grain: visit

**Description**

This SQL selects encounters with specific measurements related to sepsis scores.

- Inclusion is determined by the following measurement IDs: '9000161709', '9000002613'.
- The recorded time of measurements must be on or before the ED departure time.
- The hours in the ED are calculated as a ceiling value of the difference between ADT arrival time and ED departure time, expressed in hours.

**Fragment**

```sql
SELECT

	BP.ENCOUNTER_ID

	, CEILING(CONVERT(FLOAT,DATEDIFF(MI, BP.ADT_ARRIVAL_TIME,BP.ED_DEPARTURE_TIME))/60) HoursInED--CHECK WITH STEPHANIE ON 

	, BP.ADT_ARRIVAL_TIME

	, FM.MEAS_VALUE

	, FM.RECORDED_TIME

	, BP.ED_DEPARTURE_TIME

	, ROW_NUMBER() OVER(PARTITION BY BP.ENCOUNTER_ID ORDER BY RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#Base_Pop_Severe_ED_Scores 

FROM #Main BP 

	INNER JOIN dbo.HOSPITAL_ENCOUNTERS HE ON HE.ENCOUNTER_ID = BP.ENCOUNTER_ID --and bp.ENCOUNTER_ID=1016405505 

	INNER JOIN dbo.FLOWSHEET_RECORDS FR ON FR.INPATIENT_DATA_ID = HE.INPATIENT_DATA_ID

	INNER JOIN dbo.FLOWSHEET_MEASUREMENTS FM ON FM.FSD_ID = FR.FSD_ID and

		FM.FLO_MEAS_ID IN ('9000161709','9000002613')--SEPSIS SCORE--ADDED NEW ED SEPSIS SCORE 9000002613 ON 10.01.2019

		and (FM.RECORDED_TIME <=  BP.ED_DEPARTURE_TIME)
```

first pass violated: technical vocabulary in a business description: 'dataset' — say what is included, not how the SQL assembles it

## USP_RPTS_IP_SEPSIS.sql · #Main
*outcome: emptied* · parsed tables: hospital_encounters, patient_demographics_race, patients, ref_discharge_disposition, ref_ed_disposition, ref_ethnic_group, ref_patient_race, v_hospital_transactions · parsed grain: patient, visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
SELECT DISTINCT

	HE.ENCOUNTER_ID

	, HE.PATIENT_ID

	, PAT.PATIENT_MRN

	, PAT.PATIENT_NAME

	, REG.NAME AS [Ethnic Group]

	, RPR.NAME AS [Race]

	, HE.INPATIENT_DATA_ID

	, HE.ADT_ARRIVAL_TIME

	, HE.HOSP_ADMSN_TIME

	, HE.HOSP_DISCH_TIME

	, HE.INP_ADM_DATE

	, HE.ED_DEPARTURE_TIME

	, RDD.NAME AS [Disposition]

	, DATEDIFF(MM,PAT.BIRTH_DATE,HE.HOSP_ADMSN_TIME) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,HE.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,HE.HOSP_ADMSN_TIME)) + DATENAME(YEAR, CONVERT(DATE, HE.HOSP_ADMSN_TIME)) AS DATE_STAMP

	, DATEDIFF(HH, HE.HOSP_ADMSN_TIME, HE.HOSP_DISCH_TIME) AS LOS_HRS

INTO 

	#Main

FROM dbo.V_HOSPITAL_TRANSACTIONS HTR

	INNER JOIN dbo.HOSPITAL_ENCOUNTERS HE ON HTR.ENCOUNTER_ID = HE.ENCOUNTER_ID

	INNER JOIN dbo.PATIENTS PAT ON PAT.PATIENT_ID = HE.PATIENT_ID

	LEFT OUTER JOIN dbo.REF_DISCHARGE_DISPOSITION RDD ON RDD.DISCH_DISP_CODE = HE.DISCH_DISP_CODE

	LEFT OUTER JOIN dbo.REF_ETHNIC_GROUP REG ON REG.ETHNIC_GROUP_CODE = PAT.ETHNIC_GROUP_CODE

	LEFT OUTER JOIN dbo.PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PATIENT_ID = PAT.PATIENT_ID AND RACE.LINE=1

	LEFT OUTER JOIN dbo.REF_PATIENT_RACE RPR ON RPR.PATIENT_RACE_CODE = RACE.PATIENT_RACE_CODE

	LEFT OUTER JOIN dbo.REF_ED_DISPOSITION REDI ON REDI.ED_DISPOSITION_CODE = HE.ED_DISPOSITION_CODE

WHERE

	HE.INP_ADM_DATE IS NOT NULL

	AND CONVERT(DATE,HTR.SERVICE_DATE) BETWEEN @dStartDate AND @dEndDate
```

first pass violated: ungrounded value: '9999' not in the SQL; ungrounded value: '1001' not in the SQL; ungrounded filter claim: '- Inclusion requires that HE.INP_ADM_DATE is not null.'; column name in a business description: 'ENCOUNTER_ID' — write from its dictionary description, or say 'encounter id'; column name in a 

## USP_RPTS_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES.sql · #Base_Pop_OD_Scores
*outcome: emptied* · parsed tables: config_value_set, flowsheet_measurements, flowsheet_records, fy_date_dimension, providers, treatment_teams · parsed grain: visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
SELECT

	PD.[PATIENTS]

	, PD.[MRN]

	, PD.ENCOUNTER_ID

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

	, ROW_NUMBER() OVER(PARTITION BY PD.ENCOUNTER_ID, PD.IN_DTTM,PD.OUT_DTTM ORDER BY SEPSIS_1sC0RE.RECORDED_TIME ASC) AS DEPT_TIME_LINE

INTO 

	#Base_Pop_OD_Scores 

FROM #Main PD

	INNER JOIN reports.FY_DATE_DIMENSION FYDD ON FYDD.CALENDAR_DT = PD.CALENDAR_DT

	OUTER APPLY

	(

		SELECT

			TOP 1 FM.RECORDED_TIME, FM.MEAS_VALUE

		FROM dbo.FLOWSHEET_RECORDS FR

			INNER JOIN dbo.FLOWSHEET_MEASUREMENTS FM ON FM.FSD_ID = FR.FSD_ID

		WHERE FM.FLO_MEAS_ID IN ('9000161711','9000002644') --ORGAN DYSFUNCTION SCORE

			AND FR.INPATIENT_DATA_ID= PD.INPATIENT_DATA_ID

			AND (FM.RECORDED_TIME BETWEEN DATEADD(MI,420,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1139,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

			AND CONVERT(DATE,FM.RECORDED_TIME) = PD.CALENDAR_DT

	)SEPSIS_1sC0RE

	OUTER APPLY

	(

		SELECT

			TOP 1 FM.RECORDED_TIME, FM.MEAS_VALUE

		FROM dbo.FLOWSHEET_RECORDS FR

			INNER JOIN dbo.FLOWSHEET_MEASUREMENTS FM ON FM.FSD_ID = FR.FSD_ID

		WHERE FM.FLO_MEAS_ID IN ('9000161711','9000002644') --ORGAN DYSFUNCTION SCORE

			AND FR.INPATIENT_DATA_ID= PD.INPATIENT_DATA_ID

			AND (FM.RECORDED_TIME BETWEEN DATEADD(MI,1140,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,419,DATEADD(DD, 1, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

			AND CONVERT(DATE,FM.RECORDED_TIME) = PD.CALENDAR_DT

	)SEPSIS_2sC0RE

	

	LEFT OUTER JOIN reports.CONFIG_VALUE_SET CVS ON CVS.CODE = PD.ADT_DEPARTMENT_ID

				AND CVS.VALUE_SET_ID = 3031 --DEPARTMENT ROLL UP

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +PRV.PROV_NAME-- AS [text()]

                        FROM dbo.TREATMENT_TEAMS SUB

						INNER JOIN dbo.PROVIDERS PRV ON PRV.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.ENCOUNTER_ID = CAT.ENCOUNTER_ID

						AND (SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

						AND SUB.TRTMNT_TEAM_REL_CODE=2

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift1_RNs]	

	FROM  dbo.TREATMENT_TEAMS CAT where CAT.ENCOUNTER_ID = PD.ENCOUNTER_ID

	AND CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = PD.CALENDAR_DT

	AND (CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

	AND cat.TRTMNT_TEAM_REL_CODE=2--Registered Nurse

	group by cat.ENCOUNTER_ID

	)Shift1_RNs

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +PRV.PROV_NAME-- AS [text()]

                        FROM dbo.TREATMENT_TEAMS SUB

						INNER JOIN dbo.PROVIDERS PRV ON PRV.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.ENCOUNTER_ID = CAT.ENCOUNTER_ID

						AND (

								(CONVERT(DATE, SUB.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

								and

								(SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

							)

						AND SUB.TRTMNT_TEAM_REL_CODE=2

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift2_RNs]	

	FROM  dbo.TREATMENT_TEAMS CAT where CAT.ENCOUNTER_ID = PD.ENCOUNTER_ID

	AND (

			(CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

			and

			(CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

		)	

	AND cat.TRTMNT_TEAM_REL_CODE=2--Registered Nurse

	group by cat.ENCOUNTER_ID

	)Shift2_RNs

	--CHARGE NURSE

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +PRV.PROV_NAME-- AS [text()]

                        FROM dbo.TREATMENT_TEAMS SUB

						INNER JOIN dbo.PROVIDERS PRV ON PRV.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.ENCOUNTER_ID = CAT.ENCOUNTER_ID

						AND (SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

						AND SUB.TRTMNT_TEAM_REL_CODE=99--Charge Nurse

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift1_CNs]	

	FROM  dbo.TREATMENT_TEAMS CAT where CAT.ENCOUNTER_ID = PD.ENCOUNTER_ID

	AND CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = PD.CALENDAR_DT

	AND (CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,360,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1020,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))---BEGIN BETWEEN 6AM AND 7 PM

	AND cat.TRTMNT_TEAM_REL_CODE=99--Charge Nurse

	group by cat.ENCOUNTER_ID

	)Shift1_CNs

	OUTER APPLY

	(

		SELECT  top 1

            STUFF((    SELECT '; ' +PRV.PROV_NAME-- AS [text()]

                        FROM dbo.TREATMENT_TEAMS SUB

						INNER JOIN dbo.PROVIDERS PRV ON PRV.PROV_ID = SUB.PROV_ID

						WHERE

						SUB.ENCOUNTER_ID = CAT.ENCOUNTER_ID

						AND (

								(CONVERT(DATE, SUB.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

								and

								(SUB.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

							)

						AND SUB.TRTMNT_TEAM_REL_CODE=99--Charge Nurse

                        FOR XML PATH('')

                        ), 1, 1, '' )

            AS [Shift2_CNs]	

	FROM  dbo.TREATMENT_TEAMS CAT where CAT.ENCOUNTER_ID = PD.ENCOUNTER_ID

	AND (

			(CONVERT(DATE, CAT.TRTMNT_TM_BEGIN_DT) = CONVERT(DATE,PD.CALENDAR_DT))

			and

			(CAT.TRTMNT_TM_BEGIN_DT BETWEEN DATEADD(MI,1080,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))) AND DATEADD(MI,1439,DATEADD(DD, 0, DATEDIFF(DD, 0, PD.CALENDAR_DT))))

		)	

	AND cat.TRTMNT_TEAM_REL_CODE=99--Charge Nurse

	group by cat.ENCOUNTER_ID

	)Shift2_CNs
```

first pass violated: column name in a business description: 'TRTMNT_TEAM_REL_CODE' — write from its dictionary description, or say 'trtmnt team rel code'

## USP_RPTS_IP_SEPSIS_REPORT.sql · #EncounterWeights
*outcome: emptied* · parsed tables: flowsheet_measurements, flowsheet_records · parsed grain: visit

**Description**

_(emptied — nothing grounded survived)_

**Fragment**

```sql
SELECT

	A.ENCOUNTER_ID

	, CAST(ROUND(CONVERT(FLOAT, MEAS_VALUE) * 0.0283495, 2) AS DECIMAL(4, 1)) AS EncWeight

	, ROW_NUMBER() OVER(PARTITION BY A.ENCOUNTER_ID ORDER BY C.RECORDED_TIME ASC) AS TIME_LINE

INTO 

	#EncounterWeights

FROM 

	#Main A

INNER JOIN dbo.FLOWSHEET_RECORDS B ON A.INPATIENT_DATA_ID = B.INPATIENT_DATA_ID

INNER JOIN dbo.FLOWSHEET_MEASUREMENTS C ON B.FSD_ID = C.FSD_ID AND  C.FLO_MEAS_ID='94'
```

first pass violated: column name in a business description: 'FLO_MEAS_ID' — write from its dictionary description, or say 'flo meas id'; technical object in a business description: '#Main' — the source object is carried by the relationship, not the sentence; technical vocabulary in a business description: 'table' — say 

## USP_RPTS_IP_SEPSIS_REPORT.sql · #Main
*outcome: salvaged* · parsed tables: departments, hospital_encounters, locations, patient_demographics_race, patients, ref_discharge_disposition, ref_ethnic_group, ref_patient_race, v_hospital_transactions · parsed grain: patient, visit

**Description**

This SQL selects encounters for patients.

- The service date falls between @dStartDate and @dEndDate.
- The disposition is recorded in the ref discharge disposition, and the ethnic group is recorded in the ref ethnic group.

**Fragment**

```sql
SELECT DISTINCT

	HE.ENCOUNTER_ID

	, HE.PATIENT_ID

	, PAT.PATIENT_MRN

	, PAT.PATIENT_NAME

	, REG.NAME AS [Ethnic Group]

	, RPR.NAME AS [Race]

	--, EEF.AGE_AT_ARRIVAL_MONTHS

	--, EEF.AGE_AT_ARRIVAL_YEARS

	, HE.INPATIENT_DATA_ID

	, HE.ADT_ARRIVAL_TIME

	, HE.HOSP_ADMSN_TIME

	, HE.HOSP_DISCH_TIME

	, HE.INP_ADM_DATE

	, HE.ED_DEPARTURE_TIME

	, RDD.NAME AS [Disposition]

	, LOC.LOC_NAME [Location]

	, DATEDIFF(MM,PAT.BIRTH_DATE,HE.HOSP_ADMSN_TIME) AS AGE_MONTHS

	, FLOOR(DATEDIFF(DD,PAT.BIRTH_DATE,HE.HOSP_ADMSN_TIME)/365.25) AS AGE_YEARS

	, DATENAME(month, CONVERT(DATE,HE.HOSP_ADMSN_TIME)) + DATENAME(YEAR, CONVERT(DATE, HE.HOSP_ADMSN_TIME)) AS DATE_STAMP

	, DATEDIFF(HH, HE.HOSP_ADMSN_TIME, HE.HOSP_DISCH_TIME) AS LOS_HRS

INTO 

	#Main

FROM 

dbo.V_HOSPITAL_TRANSACTIONS HTR

INNER JOIN dbo.HOSPITAL_ENCOUNTERS HE ON HTR.ENCOUNTER_ID = HE.ENCOUNTER_ID

INNER JOIN dbo.PATIENTS PAT ON PAT.PATIENT_ID = HE.PATIENT_ID

LEFT OUTER JOIN dbo.REF_DISCHARGE_DISPOSITION RDD ON RDD.DISCH_DISP_CODE = HE.DISCH_DISP_CODE

LEFT OUTER JOIN dbo.REF_ETHNIC_GROUP REG ON REG.ETHNIC_GROUP_CODE = PAT.ETHNIC_GROUP_CODE

LEFT OUTER JOIN dbo.PATIENT_DEMOGRAPHICS_RACE RACE ON RACE.PATIENT_ID = PAT.PATIENT_ID AND RACE.LINE=1

LEFT OUTER JOIN dbo.REF_PATIENT_RACE RPR ON RPR.PATIENT_RACE_CODE = RACE.PATIENT_RACE_CODE

LEFT OUTER JOIN dbo.DEPARTMENTS DEP ON DEP.DEPARTMENT_ID = HE.DEPARTMENT_ID

LEFT OUTER JOIN dbo.LOCATIONS LOC ON LOC.LOC_ID = DEP.REV_LOC_ID

WHERE

HE.INP_ADM_DATE IS NOT NULL

AND CONVERT(DATE,HTR.SERVICE_DATE) BETWEEN @dStartDate AND @dEndDate
```

first pass violated: ungrounded filter claim: '- Inclusion requires that HE.INP_ADM_DATE is not null.'; column name in a business description: 'INP_ADM_DATE' — write from its dictionary description, or say 'inp adm date'; column name in a business description: 'REF_DISCHARGE_DISPOSITION' — write from its dictionary desc

## USP_RPTS_NonSevere_Sepsis.sql · #Base_Pop
*outcome: recovered* · parsed tables: — · parsed grain: (unknown)

**Description**

This SQL selects records from a population of encounters.

- Inclusion is determined by the absence of an encounter id in the NICU admissions.
- Encounter ids must not be present in the NICU admissions list.

**Fragment**

```sql
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
```

first pass violated: column name in a business description: 'ENCOUNTER_ID' — write from its dictionary description, or say 'encounter id'; technical object in a business description: '#Base_Pop_1' — the source object is carried by the relationship, not the sentence; technical object in a business description: '#NICUAdmi

## USP_RPTS_NonSevere_Sepsis.sql · #NICUAdmissions
*outcome: recovered* · parsed tables: adt_events · parsed grain: visit

**Description**

This SQL selects NICU admissions.

- Admission event type code: 1
- Excludes cancelled event subtype code: 2
- Department IDs: 200108002, 200108003, 200108004, 200108005, 200108006

**Fragment**

```sql
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

	AND ADT.DEPARTMENT_ID IN (200108002, 200108003, 200108004, 200108005, 200108006)
```

first pass violated: column name in a business description: 'DEPARTMENT_ID' — write from its dictionary description, or say 'department id'; column name in a business description: 'EVENT_SUBTYPE_CODE' — write from its dictionary description, or say 'event subtype code'; column name in a business description: 'EVENT_TYPE

## USP_RPTS_Severe_Sepsis.sql · #AllICUDept
*outcome: clean* · parsed tables: grouper_compiled_list · parsed grain: (unknown)

**Description**

This SQL selects department records.

- Inclusion is determined by the compiled context being 'DEP'.
- Only records with a base grouper ID of '800016' are included.

**Fragment**

```sql
SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEPARTMENT_ID

	INTO #AllICUDept

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800016')
```

## USP_RPTS_Severe_Sepsis.sql · #MedDept
*outcome: clean* · parsed tables: grouper_compiled_list · parsed grain: (unknown)

**Description**

This SQL selects department records.

- Compiled context must be 'DEP'.
- Base grouper ID must be '800004'.

**Fragment**

```sql
SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEPARTMENT_ID

	INTO #MedDept

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800004')
```

## USP_RPTS_Severe_Sepsis.sql · #NICUCICUDept
*outcome: clean* · parsed tables: grouper_compiled_list · parsed grain: (unknown)

**Description**

This SQL selects department records.

- Inclusion is determined by the compiled context being 'DEP'.
- The base grouper IDs must be one of the following: '800001', '800002', '800003'.

**Fragment**

```sql
SELECT vcg.GROUPER_RECORDS_NUMERIC_ID DEPARTMENT_ID

	INTO #NICUCICUDept

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'DEP'

	AND vcg.BASE_GROUPER_ID IN ('800001', '800002', '800003')
```

## USP_RPTS_Severe_Sepsis.sql · #ODScores
*outcome: clean* · parsed tables: grouper_compiled_list · parsed grain: (unknown)

**Description**

This SQL selects records identified by FLO_ID.

- The compiled context must be 'FLO'.
- The base grouper ID must be '800006'.

**Fragment**

```sql
SELECT vcg.GROUPER_RECORDS_NUMERIC_ID FLO_ID

	INTO #ODScores

	FROM [dbo].[GROUPER_COMPILED_LIST] vcg

	WHERE vcg.COMPILED_CONTEXT = 'FLO'

	AND vcg.BASE_GROUPER_ID IN ('800006')
```
