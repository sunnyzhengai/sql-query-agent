USE [CookClarity]
GO

/****** Object:  StoredProcedure [Reporting].[USP_CCMC_LOTE_Census_Interpreter_Services_Summary_PBI]    Script Date: 9/24/2026 7:04:10 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/**********************************************************************************************
Author:  Matthew Cvitanovich
Create date:  06/04/2025

Description: Displays a list of monthly census counts for all inpatient departments and
			 selected (Joint Commission) outpatient clinics, including caregiver languages.

Purpose:	Used by CCHCS/Accreditation/CCMC LOTE Census PBI
===============================================================================================
Revision Detail 

Date        Who                        Description 
-----------------------------------------------------------------------------------------------
2025.06.04	Matthew Cvitanovich		  Initial development
===============================================================================================*/
CREATE     PROCEDURE [Reporting].[USP_CCMC_LOTE_Census_Interpreter_Services_Summary_PBI](
	@i_vSTART_DATE VARCHAR(20) = null
	, @i_vEND_DATE VARCHAR(20) = null
)

AS

SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;


DECLARE @startDate DATETIME = [Clarity].EPIC_UTIL.EFN_DIN(COALESCE(@i_vSTART_DATE,'MB-13'));
DECLARE @endDate DATETIME = [Clarity].EPIC_UTIL.EFN_DIN(COALESCE(@i_vEND_DATE,'ME-1'));


DROP TABLE IF EXISTS #census_monthly;
DROP TABLE IF EXISTS #clinic_monthly;
DROP TABLE IF EXISTS #combined_census;

DROP TABLE IF EXISTS #caregivers;
DROP TABLE IF EXISTS #caregiver_languages;
DROP TABLE IF EXISTS #combined_census_with_language;
DROP TABLE IF EXISTS #combined_census_numerators;



/* ************************ */
/* Inpatient Monthly Census */
/* ************************ */
SELECT
	[census].PAT_ID
	, [dd].[YEAR]				AS [Year]
	, [dd].QUARTER_STR			AS [Quarter]
	, [dd].MONTH_NAME			AS [Month Name]
	, [dd].MONTH_NUMBER			AS [Month Number]
	, [loc].LOCATION_ABBR		AS [Location]
	, [dep].DEPARTMENT_NAME		AS [Department]
	, [dep].EXTERNAL_NAME		AS [Dept External Name]

	, CONVERT(DATE, MIN([census].CALENDAR_DT)) AS [Monthly Census Start Date]

	, COUNT(*) AS [Census Days]

	, CASE
		WHEN [dep].DEPARTMENT_ID IN (
			100200053	-- PCCMC 2 Main PICU
			, 100200055	-- PCCMC 4 Main
			, 100200045	-- PCCMC 5 Main
			, 100200007	-- PCCMC Main OR
			)
		THEN 'Prosper CCMC'

		--WHEN [census].DEPARTMENT_ID = xxxx		-- To be decided
		--THEN 'Prosper MOB'

		WHEN [dep].DEPARTMENT_ID = 100200033	-- PCCMC Emergency
		THEN 'Prosper ED'

		WHEN [dep].DEPARTMENT_ID = 100108022	-- CCMC Emergency
		THEN 'FW ED'

		ELSE 'FW CCMC'

	  END AS [Department Label]

INTO #census_monthly

FROM [Clarity].[dbo].F_IP_HSP_PAT_DAYS	[census]
	
	LEFT JOIN [Clarity].[dbo].CLARITY_DEP				[dep]	ON [census].DEPARTMENT_ID = [dep].DEPARTMENT_ID
	LEFT JOIN [Clarity].[dbo].CLARITY_LOC				[loc]	ON [dep].REV_LOC_ID = [loc].LOC_ID
	LEFT JOIN [Clarity].[dbo].DATE_DIMENSION			[dd]	ON [census].CALENDAR_DT = [dd].CALENDAR_DT

WHERE 1=1
	AND [census].CALENDAR_DT BETWEEN @StartDate AND @EndDate
	AND [dep].REV_LOC_ID IN (
		N'100108'		-- COOK CHILDRENS MEDICAL CENTER
		, N'100200'		-- COOK CHILDRENS MEDICAL CENTER PROSPER
	)

GROUP BY
	[census].PAT_ID
	, [dd].[YEAR]
	, [dd].QUARTER_STR
	, [dd].MONTH_NUMBER
	, [dd].MONTH_NAME
	, [loc].LOCATION_ABBR
	, [dep].DEPARTMENT_ID
	, [dep].DEPARTMENT_NAME
	, [dep].EXTERNAL_NAME
;


/* ********************* */
/* Clinic Monthly Census */
/* ********************* */
DROP TABLE IF EXISTS #clinic_monthly;
SELECT
	[appt].PAT_ID
	, [dd].[YEAR]				AS [Year]
	, [dd].QUARTER_STR			AS [Quarter]
	, [dd].MONTH_NAME			AS [Month Name]
	, [dd].MONTH_NUMBER			AS [Month Number]
	, [loc].LOCATION_ABBR		AS [Location]
	, [dep].DEPARTMENT_NAME		AS [Department]
	, [dep].EXTERNAL_NAME		AS [Dept External Name]

	, CONVERT(DATE, MIN([appt].CONTACT_DATE)) AS [Monthly Census Start Date]

	, COUNT(*) AS [Census Days]

	, 'FW Dodson/TJC Ambulatory' AS [Department Label]

INTO #clinic_monthly

FROM [Clarity].[dbo].F_SCHED_APPT	appt
	
	LEFT JOIN [Clarity].[dbo].CLARITY_DEP			dep		ON [appt].DEPARTMENT_ID = [dep].DEPARTMENT_ID
	LEFT JOIN [Clarity].[dbo].CLARITY_LOC			loc		ON [dep].REV_LOC_ID = [loc].LOC_ID
	LEFT JOIN [Clarity].[dbo].DATE_DIMENSION		dd		ON [appt].CONTACT_DATE = [dd].CALENDAR_DT

WHERE 1=1
	AND [appt].APPT_STATUS_C = 2			-- Completed
	AND [appt].CONTACT_DATE BETWEEN @StartDate AND @EndDate
	AND [dep].DEPARTMENT_ID IN (
		10101207	--CARDIOTHORACIC SURGERY
		,10101209	--ENT
		,10101219	--PALLIATIVE CARE
		,10120165	--PEDIATRIC ENT
		,100050003	--DMSS PSYCHOLOGY
		,100063010	--HMSS PSYCHOLOGY
		,100063017	--HMSS HURST SPORT PT
		,100063019	--HMSS HURST PT
		,100063021	--HMSS HURST AUDIO
		,100073003	--SWMS PSYCHOLOGY
		,100074001	--MOB PSYCHOLOGY
		,100106001	--ARL CARDIOLOGY
		,100106002	--ARL DIAGNOSTIC CARDIO
		,100108067	--CCMC UC SOUTHLAKE DS
		,100117001	--HOGC HEM ONC
		,100119101	--RHBSO SOUTH PT
		,100119104	--RHBSO SOUTH AUDIO
		,100119105	--RHBSO SOUTH SPORT PT
		,100300005	--PROSPER PEDI SURGERY
		,100381011	--SMSS PSYCHOLOGY
		,100581001	--DOD CRANIOFACIAL
		,100581002	--DOD ENDOCRINOLOGY
		,100581003	--DOD GASTROENTEROLOGY
		,100581004	--DOD CARDIOLOGY
		,100581006	--DOD HEM ONC
		,100581007	--DOD INFECTIOUS DISEASE
		,100581008	--DOD NEPHROLOGY
		,100581009	--DOD NEUROLOGY
		,100581010	--DOD NEUROSURGERY
		,100581012	--DOD PAIN MANAGEMENT
		,100581013	--DOD PEDIATRIC SURGERY
		,100581014	--DOD PULMONOLOGY
		,100581015	--DOD MR IMAGING
		,100581016	--DOD US IMAGING
		,100581017	--DOD X-RAY IMAGING
		,100581018	--DOD RHEUMATOLOGY
		,100581020	--DOD ORTHO X-RAY
		,100581022	--DOD INFUSION
		,100581023	--DOD NEST FOLLOW UP
		,100581032	--DOD SLEEP MEDICINE
		,100581033	--DOD PULMONARY LAB
		,100581035	--DOD DIAGNOSTIC CARDIO
		,100581047	--DOD IMMUNOLOGY
		,100581050	--DOD PSYCHOLOGY
		,100581052	--DOD DEVELOPMENTAL PEDS
		,100581053	--DOD WOUND CLINIC
		,100581059	--DOD DERMATOLOGY
		,100581060	--DOD UROLOGY
		,100581063	--DOD UROLOGY RADIOLOGY
		,100581075	--DOD CARDIAC REHAB
		,100590009	--MAN URGENT CARE
		,100590010	--MMS MANS PT
		,100590015	--MMS MANS AUDIO
		,100590021	--MMS MANS SPORT PT
		,100618001	--FTW URGENT CARE
		,100618020	--FTW URGENT CARE X-RAY
		,100624020	--MAN URGENT CARE X-RAY
		,100624021	--MAN URGENT CARE
		,100632010	--ALMS PSYCHOLOGY
		,100632022	--ALMS AUDIO
		,100635001	--SLK URGENT CARE
		,100641001	--HUR URGENT CARE
		,100641002	--HUR URGENT CARE X-RAY
		,100643001	--HRC US IMAGING
		,100643002	--HRC X-RAY IMAGING
		,100643003	--HRC MR IMAGING
		,100651001	--ALL URGENT CARE
		,100657003	--VIRTUAL CARE
		,100663001	--DENTON PSYCHOLOGY
		,100674003	--WR SPORT PT
		,100675001	--WR URGENT CARE
		,100675002	--WR URGENT CARE X-RAY
		,100676006	--CSC PSYCHOLOGY
		,100682001	--PROSPER URGENT CARE
		,100683001	--COOPER NEST FOLLOW UP
		,100683002	--COOPER NEUROPSYCH
		,100685001	--DENTON PSYCHOLOGY
		,100700005	--PROSPER PEDI SURGERY
	)

GROUP BY
	[appt].PAT_ID
	, [dd].[YEAR]
	, [dd].QUARTER_STR
	, [dd].MONTH_NUMBER
	, [dd].MONTH_NAME
	, [loc].LOCATION_ABBR
	, [dep].DEPARTMENT_ID
	, [dep].DEPARTMENT_NAME
	, [dep].EXTERNAL_NAME
;


SELECT *, 'Inpatient' as [Dept Type]
INTO #combined_census
FROM #census_monthly
UNION
SELECT *, 'Outpatient' as [Dept Type]
FROM #clinic_monthly
;



/* ********** */
/* Caregivers */
/* ********** */
SELECT PAT_ID, PAT_RELATIONSHIP_ID
INTO #caregivers
FROM [Clarity].[dbo].PAT_RELATIONSHIP_LIST
WHERE EXISTS (SELECT 1 FROM #combined_census WHERE [PAT_RELATIONSHIP_LIST].PAT_ID = [#combined_census].PAT_ID)
;



/* ******************* */
/* Caregiver Languages */
/* ******************* */
-- Assume relationship was active over the entire reporting period 
-- (otherwise must consider F_IP_HSP_PAT_DAYS.CALENDAR_DATE which will greatly slow query)
SELECT 
	[#caregivers].PAT_ID
	, STRING_AGG( CONCAT( IIF( [relation].NAME IS NULL, '?', [relation].NAME ), ';', [zc_lang].NAME ), CHAR(10)+CHAR(13)) 
		WITHIN GROUP(ORDER BY [lang].PAT_RELATIONSHIP_ID) AS [Caregiver Languages]
	
INTO #caregiver_languages

FROM [Clarity].[dbo].PAT_REL_LANGUAGES	[lang]		

	INNER JOIN #caregivers													ON [lang].PAT_RELATIONSHIP_ID = [#caregivers].PAT_RELATIONSHIP_ID
	LEFT JOIN [Clarity].[dbo].ZC_LANGUAGE					[zc_lang]		ON [lang].LANGUAGE_C = [zc_lang].LANGUAGE_C
	LEFT JOIN [Clarity].[dbo].PAT_RELATIONSHIP_LIST_HX		[hx]			ON [lang].PAT_RELATIONSHIP_ID = [hx].RELATIONSHIP_ID
	LEFT JOIN [Clarity].[dbo].ZC_EMERG_PAT_REL				[relation]		ON [hx].RELATION_TO_PAT_C = [relation].EMERG_PAT_REL_C

WHERE 1=1
	AND [lang].LANGUAGE_TYPE_C = 1	-- SPOKEN LANGUAGE
	AND (
		( [hx].RELATIONSHIP_START_DATE <= @EndDate AND [hx].RELATIONSHIP_END_DATE >= @StartDate )	-- Relationship ended after report start but was active during report period
		OR		
		( [hx].RELATIONSHIP_START_DATE <= @EndDate AND [hx].RELATIONSHIP_END_DATE IS NULL )			-- Relationship has no end date
		OR
		( [hx].RELATIONSHIP_START_DATE IS NULL AND [hx].RELATIONSHIP_END_DATE IS NULL )				-- No dates entered for relationship
		)

GROUP BY [#caregivers].PAT_ID
;



/* **************************** */
/* Census + Caregiver Languages */
/* **************************** */
SELECT
	[#combined_census].PAT_ID
	, [#combined_census].[Year]
	, [#combined_census].[Quarter]
	, [#combined_census].[Month Name]
	, [#combined_census].[Month Number]
	, [#combined_census].[Location]
	, [#combined_census].[Department]
	, [#combined_census].[Dept External Name]
	, [#combined_census].[Department Label]
	, [#combined_census].[Dept Type]
	--, [#combined_census].[Room]
	, [#combined_census].[Census Days]
	
	, CASE
		WHEN [#caregiver_languages].[Caregiver Languages] LIKE N'%SPANISH%'
		THEN 'At least one Spanish-speaking caregiver'

		WHEN [#caregiver_languages].[Caregiver Languages] NOT LIKE N'%ENGLISH%'
		THEN 'Language other than English and Spanish'
		
		WHEN [#caregiver_languages].[Caregiver Languages] LIKE N'%ENGLISH%'
		THEN 'Only English speaking caregivers'

		ELSE 'No language(s) listed'

	  END AS [Caregiver Language Category]

INTO #combined_census_with_language

FROM #combined_census

	LEFT JOIN #caregiver_languages		ON [#combined_census].PAT_ID = [#caregiver_languages].PAT_ID
;



/* ********** */
/* Numerators */
/* ********** */
SELECT 
	[Year]
	, [Quarter]
	, [Month Name]
	, [Month Number]
	, [Location]
	, [Department]
	, [Dept External Name]
	, [Department Label]
	, [Dept Type]
	, [Caregiver Language Category]

	, SUM([Census Days])		AS [Census Days]
	, COUNT(DISTINCT PAT_ID)	AS [Patient Count]

INTO #combined_census_numerators

FROM #combined_census_with_language

GROUP BY
	[Year]
	, [Quarter]
	, [Month Name]
	, [Month Number]
	, [Location]
	, [Department]
	, [Dept External Name]
	, [Department Label]
	, [Dept Type]
	, [Caregiver Language Category]
;



/* ****************** */
/* Final Census Query */
/* ****************** */
SELECT
	[num].[Year]
	, [num].[Quarter]
	, [num].[Month Name]
	, [num].[Month Number]
	, [num].[Location]
	, [num].[Department]
	, [num].[Dept External Name]
	, [num].[Department Label]
	, [num].[Dept Type]
	, [num].[Caregiver Language Category]
	, [num].[Census Days]
	, [num].[Patient Count]

	, [denom].[Census Denominator]
	, [denom].[Patient Denominator]

FROM #combined_census_numerators [num]

	/* Denominators */
	INNER JOIN (
		SELECT 
			[Year]
			, [Quarter]
			, [Month Name]
			, [Location]
			, [Dept External Name]
			, [Department Label]
			, [Dept Type]
			, SUM([Census Days])		AS [Census Denominator]
			, COUNT(DISTINCT PAT_ID)	AS [Patient Denominator]
		
		FROM #combined_census

		GROUP BY 
			[Year]
			, [Quarter]
			, [Month Name]
			, [Location]
			, [Dept External Name]
			, [Department Label]
			, [Dept Type]

	) AS denom

		ON [num].[Year] = [denom].[Year]
		AND [num].[Quarter] = [denom].[Quarter]
		AND [num].[Month Name] = [denom].[Month Name]
		AND [num].[Location] = [denom].[Location]
		AND [num].[Dept External Name] = [denom].[Dept External Name]
		AND [num].[Department Label] = [denom].[Department Label]
		AND [num].[Dept Type] = [denom].[Dept Type]
;
GO


