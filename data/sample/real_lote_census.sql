-- Source: [Reporting].[USP_BookMedical_LOTE_Census_Interpreter_Services_Detail_PBI]
-- Author: Snow White
-- Create date: 06/04/2025
-- Description: Displays a list of patients without an English-speaking caregiver who may have
--              benefited from Translation Services during an admission within a specified
--              reporting period.
-- Purpose: Used by BookHealth/Accreditation/BookMedical LOTE Census PBI
-- Database: BookClarity (Epic Clarity)

USE [BookClarity]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [Reporting].[USP_BookMedical_LOTE_Census_Interpreter_Services_Detail_PBI](
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
DROP TABLE IF EXISTS #coverage;

/* ************************ */
/* Inpatient Monthly Census */
/* ************************ */
SELECT
    [census].PAT_ID
  , [dd].[YEAR]                    AS [Year]
  , [dd].QUARTER_STR               AS [Quarter]
  , [dd].MONTH_NAME                AS [Month Name]
  , [dd].MONTH_NUMBER              AS [Month Number]
  , [loc].LOCATION_ABBR            AS [Location]
  , [dep].DEPARTMENT_NAME          AS [Department]
  , [rom].ROOM_NAME                AS [Room]
  , [bed].BED_LABEL                AS [Bed]
  , CONVERT(DATE, MIN([census].CALENDAR_DT)) AS [Monthly Census Start Date]
  , CONVERT(DATE, MAX([census].CALENDAR_DT)) AS [Monthly Census End Date]
  , COUNT(*) AS [Census Days]
  , CONCAT(CONVERT(DATE, MIN([census].CALENDAR_DT)), ' - ',
           CONVERT(DATE, MAX([census].CALENDAR_DT))) AS [Census Period]
  , CASE WHEN [dep].DEPARTMENT_ID IN (
        100200053  -- PBookMedical 2 Main PICU
      , 100200055  -- PBookMedical 4 Main
      , 100200045  -- PBookMedical 5 Main
      , 100200007  -- PBookMedical Main OR
    )
    THEN 'BROSPER BookMedical'
    WHEN [dep].DEPARTMENT_ID = 100200033  -- PBookMedical Emergency
    THEN 'BROSPER ED'
    WHEN [dep].DEPARTMENT_ID = 100108022  -- BookMedical Emergency
    THEN 'FW ED'
    ELSE 'FW BookMedical'
    END AS [Department Label]
INTO #census_monthly
FROM [Clarity].[dbo].F_IP_HSP_PAT_DAYS  [census]
  LEFT JOIN [Clarity].[dbo].CLARITY_DEP           [dep]
    ON [census].DEPARTMENT_ID = [dep].DEPARTMENT_ID
  LEFT JOIN [Clarity].[dbo].CLARITY_LOC           [loc]
    ON [dep].REV_LOC_ID = [loc].LOC_ID
  LEFT JOIN [Clarity].[dbo].V_PAT_ADT_LOCATION_HX [adt]
    ON [census].ADT_EVENT_ID = [adt].EVENT_ID
  LEFT JOIN [Clarity].[dbo].CLARITY_BED           [bed]
    ON [adt].ADT_BED_ID = [bed].BED_ID
    AND [adt].ADT_BED_CSN = [bed].BED_CSN_ID
  LEFT JOIN [Clarity].[dbo].CLARITY_ROM           [rom]
    ON [adt].ADT_ROOM_ID = [rom].ROOM_ID
    AND [adt].ADT_ROOM_CSN = [rom].ROOM_CSN_ID
  LEFT JOIN [Clarity].[dbo].DATE_DIMENSION        [dd]
    ON [census].CALENDAR_DT = [dd].CALENDAR_DT
WHERE 1=1
  AND [census].CALENDAR_DT BETWEEN @StartDate AND @EndDate
  AND [adt].ADT_SERV_AREA_ID IS NOT NULL  -- EXCLUDE 'PRE-ADMISSION' EVENT
  AND [dep].REV_LOC_ID IN (
      '100108'    -- Book CHILDRENS MEDICAL CENTER
    , '100200'    -- Book CHILDRENS MEDICAL CENTER BROSPER
  )
GROUP BY
    [census].PAT_ID
  , [dd].[YEAR]
  , [dd].QUARTER_STR
  , [dd].MONTH_NUMBER
  , [dd].MONTH_NAME
  , [loc].LOCATION_ABBR
  , [dep].DEPARTMENT_NAME
  , [dep].DEPARTMENT_ID
  , [rom].ROOM_NAME
  , [bed].BED_LABEL
;

/* ************************ */
/* Clinic Monthly Census    */
/* ************************ */
SELECT
    [enc].PAT_ID
  , [dd].[YEAR]                    AS [Year]
  , [dd].QUARTER_STR               AS [Quarter]
  , [dd].MONTH_NAME                AS [Month Name]
  , [dd].MONTH_NUMBER              AS [Month Number]
  , [loc].LOCATION_ABBR            AS [Location]
  , [dep].DEPARTMENT_NAME          AS [Department]
  , CONVERT(VARCHAR, NULL)         AS [Room]
  , CONVERT(VARCHAR, NULL)         AS [Bed]
  , CONVERT(DATE, MIN([enc].CONTACT_DATE)) AS [Monthly Census Start Date]
  , CONVERT(DATE, MAX([enc].CONTACT_DATE)) AS [Monthly Census End Date]
  , COUNT(*) AS [Census Days]
  , CONCAT(CONVERT(DATE, MIN([enc].CONTACT_DATE)), ' - ',
           CONVERT(DATE, MAX([enc].CONTACT_DATE))) AS [Census Period]
  , 'FW Dodson/TJC Ambulatory' AS [Department Label]
INTO #clinic_monthly
FROM [Clarity].[dbo].PAT_ENC         [enc]
  LEFT JOIN [Clarity].[dbo].CLARITY_DEP  [dep]
    ON [enc].DEPARTMENT_ID = [dep].DEPARTMENT_ID
  LEFT JOIN [Clarity].[dbo].CLARITY_LOC  [loc]
    ON [dep].REV_LOC_ID = [loc].LOC_ID
  LEFT JOIN [Clarity].[dbo].DATE_DIMENSION  [dd]
    ON [enc].CONTACT_DATE = [dd].CALENDAR_DT
WHERE 1=1
  AND [enc].CONTACT_DATE BETWEEN @StartDate AND @EndDate
  AND [dep].DEPARTMENT_ID IN (
      10101207   --CARDIOTHORACIC SURGERY
    , 10101209   --ENT
    , 10101219   --PALLIATIVE CARE
    , 10120165   --PEDIATRIC ENT
    , 100050003  --DMSS PSYCHOLOGY
    , 100063010  --HMSS PSYCHOLOGY
    , 100063017  --HMSS BURST SPORT PT
    , 100063019  --HMSS BURST PT
    , 100063021  --HMSS BURST AUDIO
    , 100073003  --SWMS PSYCHOLOGY
    , 100074001  --MOB PSYCHOLOGY
    , 100106001  --ARL CARDIOLOGY
    , 100106002  --ARL DIAGNOSTIC CARDIO
    , 100108067  --BookMedical UC SOUTHLAKE DS
    , 100119104  --RHBSO SOUTH AUDIO
    , 100119105  --RHBSO SOUTH SPORT PT
    , 100300005  --BROSPER PEDI SURGERY
    , 100381011  --SMSS PSYCHOLOGY
    , 100581001  --DOD CRANIOFACIAL
    , 100581002  --DOD ENDOCRINOLOGY
    , 100581003  --DOD GASTROENTEROLOGY
    , 100581004  --DOD CARDIOLOGY
    , 100581006  --DOD HEM ONC
    , 100581007  --DOD INFECTIOUS DISEASE
    , 100581008  --DOD NEPHROLOGY
    , 100581009  --DOD NEUROLOGY
    , 100581010  --DOD NEUROSURGERY
    , 100581012  --DOD PAIN MANAGEMENT
    , 100581013  --DOD PEDIATRIC SURGERY
    , 100581014  --DOD PULMONOLOGY
    , 100581015  --DOD MR IMAGING
    , 100581016  --DOD US IMAGING
    , 100581017  --DOD X-RAY IMAGING
    , 100581018  --DOD RHEUMATOLOGY
    , 100581020  --DOD ORTHO X-RAY
    , 100581033  --DOD PULMONARY LAB
    , 100581035  --DOD DIAGNOSTIC CARDIO
    , 100581047  --DOD IMMUNOLOGY
    , 100581050  --DOD PSYCHOLOGY
    , 100581052  --DOD DEVELOPMENTAL PEDS
    , 100581053  --DOD WOUND CLINIC
    , 100581059  --DOD DERMATOLOGY
    , 100581060  --DOD UROLOGY
    , 100581063  --DOD UROLOGY RADIOLOGY
    , 100581075  --DOD CARDIAC REHAB
    , 100590009  --MAN URGENT CARE
    , 100590010  --MMS MANS PT
    , 100590015  --MMS MANS AUDIO
    , 100590021  --MMS MANS SPORT PT
    , 100618001  --FTW URGENT CARE
    , 100618020  --FTW URGENT CARE X-RAY
    , 100624020  --MAN URGENT CARE X-RAY
    , 100624021  --MAN URGENT CARE
    , 100632010  --ALMS PSYCHOLOGY
    , 100632022  --ALMS AUDIO
    , 100635001  --SLK URGENT CARE
    , 100641001  --HUR URGENT CARE
    , 100641002  --HUR URGENT CARE X-RAY
    , 100643001  --HRC US IMAGING
    , 100643002  --HRC X-RAY IMAGING
    , 100643003  --HRC MR IMAGING
    , 100651001  --ALL URGENT CARE
    , 100657003  --VIRTUAL CARE
    , 100663001  --DENTON PSYCHOLOGY
    , 100674003  --WR SPORT PT
    , 100675001  --WR URGENT CARE
    , 100675002  --WR URGENT CARE X-RAY
    , 100676006  --CSC PSYCHOLOGY
    , 100682001  --BROSPER URGENT CARE
    , 100683001  --COOPER NEST FOLLOW UP
    , 100683002  --COOPER NEUROPSYCH
    , 100685001  --DENTON PSYCHOLOGY
    , 100700005  --BROSPER PEDI SURGERY
  )
GROUP BY
    [enc].PAT_ID
  , [dd].[YEAR]
  , [dd].QUARTER_STR
  , [dd].MONTH_NUMBER
  , [dd].MONTH_NAME
  , [loc].LOCATION_ABBR
  , [dep].DEPARTMENT_NAME
;

/* *************** */
/* Combined Census */
/* *************** */
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
WHERE EXISTS (
    SELECT 1 FROM #combined_census
    WHERE [PAT_RELATIONSHIP_LIST].PAT_ID = [#combined_census].PAT_ID
)
;

/* ********************** */
/* Caregiver Languages    */
/* ********************** */
-- Assume relationship was active over the entire reporting period
SELECT
    [#caregivers].PAT_ID
  , STRING_AGG( CONCAT( IIF( [relation].NAME IS NULL, '?',
        [relation].NAME ), ';', [zc_lang].NAME ), CHAR(10)+CHAR(13))
        WITHIN GROUP(ORDER BY [lang].PAT_RELATIONSHIP_ID
    ) AS [Caregiver Languages]
INTO #caregiver_languages
FROM [Clarity].[dbo].PAT_REL_LANGUAGES    [lang]
  INNER JOIN #caregivers
    ON [lang].PAT_RELATIONSHIP_ID = [#caregivers].PAT_RELATIONSHIP_ID
  INNER JOIN [Clarity].[dbo].ZC_LANGUAGE              [zc_lang]
    ON [lang].LANGUAGE_C = [zc_lang].LANGUAGE_C
  LEFT JOIN [Clarity].[dbo].PAT_RELATIONSHIP_LIST_HX  [hx]
    ON [lang].PAT_RELATIONSHIP_ID = [hx].RELATIONSHIP_ID
  LEFT JOIN [Clarity].[dbo].ZC_EMERG_PAT_REL          [relation]
    ON [hx].RELATION_TO_PAT_C = [relation].EMERG_PAT_REL_C
WHERE 1=1
  AND [lang].LANGUAGE_TYPE_C = 1  -- SPOKEN LANGUAGE
  AND ( -- Relationship ended after report start but was active during report
        ( [hx].RELATIONSHIP_START_DATE <= @EndDate
          AND [hx].RELATIONSHIP_END_DATE >= @StartDate )
    OR  -- Relationship has no end date
        ( [hx].RELATIONSHIP_START_DATE <= @EndDate
          AND [hx].RELATIONSHIP_END_DATE IS NULL )
    OR  -- No dates entered for relationship
        ( [hx].RELATIONSHIP_START_DATE IS NULL
          AND [hx].RELATIONSHIP_END_DATE IS NULL )
  )
GROUP BY [#caregivers].PAT_ID
;

/* ********** */
/* Coverage   */
/* ********** */
;WITH matching_coverages AS
(
  SELECT
      [#combined_census].PAT_ID
    , [#combined_census].[Monthly Census Start Date]
    , [coverage].PAYOR_NAME
    , [coverage].BENEFIT_PLAN_ID
    , [coverage].BENEFIT_PLAN_NAME
    , [coverage].FIN_CLASS_NAME
    , ROW_NUMBER() OVER(
        PARTITION BY [#combined_census].PAT_ID,
            [#combined_census].[Monthly Census Start Date]
        ORDER BY [filing].FILING_ORDER ASC
      ) AS CVG_FILING_ORDER
  -- Since one coverage record can have multiple members,
  -- each row in the table corresponds to one member
  -- and is noted by the coverage ID and the line number
  FROM Clarity.dbo.COVERAGE_MEMBER_LIST   [member]
    INNER JOIN #combined_census
      ON [member].PAT_ID = [#combined_census].PAT_ID
    INNER JOIN Clarity.dbo.V_COVERAGE_PAYOR_PLAN  [coverage]
      ON [member].COVERAGE_ID = [coverage].COVERAGE_ID
    INNER JOIN Clarity.dbo.CLARITY_EPM            [payor]
      ON [coverage].PAYOR_ID = [payor].PAYOR_ID
    INNER JOIN Clarity.dbo.PAT_CVG_FILE_ORDER     [filing]
      ON [member].COVERAGE_ID = [filing].COVERAGE_ID
  WHERE 1=1
    AND [payor].PAYOR_NAME NOT LIKE 'RX%'
    -- Y - Verified and in effect
    -- 3 - Pending (not verified, but in effect)
    -- 4 - In Question (was verified, but recent carrier information or)
    AND [member].MEM_COVERED_YN IN ( 'Y', '3', '4' )
    /* Date on which the coverage (subscription) goes into effect for the member */
    AND [member].MEM_EFF_FROM_DATE <= [#combined_census].[Monthly Census Start Date]
    AND ( [member].MEM_EFF_TO_DATE > [#combined_census].[Monthly Census Start Date]
          OR [member].MEM_EFF_TO_DATE IS NULL )
    /* Date on which payor was determined
    (Managed Care contexts may change based on employer group association) */
    AND [coverage].EFF_DATE <= [#combined_census].[Monthly Census Start Date]
    AND [coverage].TERM_DATE > [#combined_census].[Monthly Census Start Date]
)
SELECT *
INTO #coverage
FROM matching_coverages
WHERE CVG_FILING_ORDER = 1
;

/* *********** */
/* Final Query */
/* *********** */
SELECT
    [#combined_census].[Year]
  , [#combined_census].[Quarter]
  , [#combined_census].[Month Name]
  , [#combined_census].[Month Number]
  , [#combined_census].[Monthly Census Start Date]
  , [#combined_census].[Monthly Census End Date]
  , [#combined_census].[Location]
  , [#combined_census].[Department]
  , [#combined_census].[Department Label]
  , [#combined_census].[Dept Type]
  , [#combined_census].[Room]
  , [#combined_census].[Bed]
  , [#combined_census].[Census Period]
  , [#combined_census].[Census Days]
  , [#caregiver_languages].[Caregiver Languages]
  , CASE
      WHEN [#caregiver_languages].[Caregiver Languages] LIKE '%SPANISH%'
      THEN 'At least one Spanish-speaking caregiver'
      WHEN [#caregiver_languages].[Caregiver Languages] NOT LIKE '%ENGLISH%'
      THEN 'Language other than English and Spanish'
      WHEN [#caregiver_languages].[Caregiver Languages] LIKE '%ENGLISH%'
      THEN 'Only English speaking caregivers'
      ELSE 'No language(s) listed'
    END AS [Caregiver Language Category]
  , ISNULL([#coverage].FIN_CLASS_NAME, 'Self-Pay') AS [Financial Class]
  , ISNULL([#coverage].PAYOR_NAME, 'SELF-PAY')    AS [Payor]
  , ISNULL([#coverage].BENEFIT_PLAN_NAME, 'SELF-PAY') AS [Benefit Plan]
  , IIF([#coverage].BENEFIT_PLAN_ID = '312302', 'Yes', 'No') AS [Foster Coverage?]
  , CASE
      WHEN [#coverage].FIN_CLASS_NAME IS NULL
        OR [#coverage].FIN_CLASS_NAME = 'Self-pay' THEN 'Self-pay'
      ELSE 'Has Coverage'
    END AS [Insurance Coverage?]
  , [pat].PAT_MRN_ID                              AS [MRN]
  , [pat].PAT_NAME                                 AS [Patient Name]
  , ISNULL([sex_zc].[NAME], 'Unknown')             AS [Legal Sex]
  , [myc_zc].[NAME]                                AS [MyChart Status]
  , [lang_zc].NAME                                 AS [Patient Language]
  , CASE WHEN [pat4].GENDER_IDENTITY_C = 6
      OR [pat4].GENDER_IDENTITY_C IS NULL THEN 'Unknown'
      ELSE [gender_zc].[NAME]
    END AS [Gender Identity]
  , CASE WHEN [pat].ETHNIC_GROUP_C IN (3, 4)
      OR [pat].ETHNIC_GROUP_C IS NULL THEN 'Unknown'
      WHEN [pat].ETHNIC_GROUP_C IN (2, 8) THEN 'Hispanic or Latino'
      ELSE [ethnicity].[NAME]
    END AS [Ethnicity]
  , CASE WHEN [race_list].PATIENT_RACE_C IN (7, 8)
      OR [race_list].PATIENT_RACE_C IS NULL
      THEN 'Unknown'
      ELSE [race].[NAME]
    END AS [Race]
  , CASE WHEN [pat4].SEX_ASGN_AT_BIRTH_C IN (3, 4, 5, 6)
      OR [pat4].SEX_ASGN_AT_BIRTH_C IS NULL
      THEN 'Unknown'
      ELSE [sex_birth_zc].[NAME]
    END AS [Birth Sex]
  , IIF([pat].INTRPTR_NEEDED_YN = 'Y', 'Yes', 'No') AS [Interpreter Needed?]
  , ISNULL([country_tmp_zc].[NAME], [country_zc].[NAME]) AS [Country]
  , ISNULL([state_tmp_zc].[NAME], [state_zc].[NAME])     AS [State]
  , ISNULL([pat].TMP_CITY, [pat].CITY)                    AS [City]
  , ISNULL([pat].TMP_ZIP, [pat].ZIP)                      AS [ZIP Code]
  , DATEDIFF(DAY, [pat].BIRTH_DATE, [#combined_census].[Monthly Census Start Date])/365 AS [Age Yrs]
  , CASE
      WHEN DATEDIFF(DAY, [pat].BIRTH_DATE, [#combined_census].[Monthly Census Start Date]) < 365*1
      THEN '<1'
      WHEN DATEDIFF(DAY, [pat].BIRTH_DATE, [#combined_census].[Monthly Census Start Date]) < 365*6
      THEN '1-5'
      WHEN DATEDIFF(DAY, [pat].BIRTH_DATE, [#combined_census].[Monthly Census Start Date]) < 365*12
      THEN '6-11'
      WHEN DATEDIFF(DAY, [pat].BIRTH_DATE, [#combined_census].[Monthly Census Start Date]) < 365*18
      THEN '12-17'
      WHEN DATEDIFF(DAY, [pat].BIRTH_DATE, [#combined_census].[Monthly Census Start Date]) >= 365*18
      THEN '>=18'
    END AS [Age Group]
  , CASE
      WHEN [pat].ETHNIC_GROUP_C IN (3, 4) THEN 'Unknown'
      WHEN [pat].ETHNIC_GROUP_C > 1 OR [race_list].PATIENT_RACE_C = 1001 THEN 'Hispanic'
      WHEN [race_list].PATIENT_RACE_C = 1       THEN 'NH White'
      WHEN [race_list].PATIENT_RACE_C = 2       THEN 'NH Black'
      WHEN [race_list].PATIENT_RACE_C IN (4, 1000) THEN 'NH Asian'
      WHEN [race_list].PATIENT_RACE_C IN (7, 8) THEN 'NH Unknown'
      ELSE 'NH Other'
    END AS [Race/Ethnicity]
FROM #combined_census
  LEFT JOIN #caregiver_languages
    ON [#combined_census].PAT_ID = [#caregiver_languages].PAT_ID
  LEFT JOIN #coverage
    ON [#combined_census].PAT_ID = [#coverage].PAT_ID
    AND [#combined_census].[Monthly Census Start Date] = [#coverage].[Monthly Census Start Date]
  /* Demographics */
  LEFT JOIN [Clarity].[dbo].PATIENT          [pat]
    ON [#combined_census].PAT_ID = [pat].PAT_ID
  LEFT JOIN [Clarity].[dbo].PATIENT_4        [pat4]
    ON [#combined_census].PAT_ID = [pat4].PAT_ID
  LEFT JOIN Clarity.dbo.PATIENT_MYC          [myc]
    ON [#combined_census].PAT_ID = [myc].PAT_ID
  LEFT JOIN [Clarity].[dbo].PATIENT_RACE     [race_list]
    ON [pat].PAT_ID = [race_list].PAT_ID
    AND [race_list].LINE = 1  -- first race listed
  /* Categories and Look-ups */
  LEFT JOIN [Clarity].[dbo].ZC_LANGUAGE      [lang_zc]
    ON [pat].LANGUAGE_C = [lang_zc].LANGUAGE_C
  LEFT JOIN [Clarity].[dbo].ZC_MYCHART_STATUS [myc_zc]
    ON [myc].MYCHART_STATUS_C = [myc_zc].MYCHART_STATUS_C
  LEFT JOIN [Clarity].[dbo].ZC_SEX           [sex_zc]
    ON [pat4].SEX_C = [sex_zc].RCPT_MEM_SEX_C
  LEFT JOIN [Clarity].[dbo].ZC_SEX_ASGN_AT_BIRTH [sex_birth_zc]
    ON [pat4].SEX_ASGN_AT_BIRTH_C = [sex_birth_zc].SEX_ASGN_AT_BIRTH_C
  LEFT JOIN [Clarity].[dbo].ZC_COUNTRY       [country_zc]
    ON [pat].COUNTRY_C = [country_zc].COUNTRY_C
  LEFT JOIN [Clarity].[dbo].ZC_COUNTRY       [country_tmp_zc]
    ON [pat].TMP_COUNTY_C = [country_tmp_zc].COUNTY_C
  LEFT JOIN [Clarity].[dbo].ZC_STATE         [state_zc]
    ON [pat].STATE_C = [state_zc].STATE_C
  LEFT JOIN [Clarity].[dbo].ZC_STATE         [state_tmp_zc]
    ON [pat].TMP_STATE_C = [state_tmp_zc].STATE_C
  LEFT JOIN [Clarity].[dbo].ZC_GENDER_IDENTITY [gender_zc]
    ON [pat4].GENDER_IDENTITY_C = [gender_zc].GENDER_IDENTITY_C
  LEFT JOIN [Clarity].[dbo].ZC_PATIENT_RACE  [race]
    ON [race_list].PATIENT_RACE_C = [race].PATIENT_RACE_C
  LEFT JOIN [Clarity].[dbo].ZC_ETHNIC_GROUP  [ethnicity]
    ON [pat].ETHNIC_GROUP_C = [ethnicity].ETHNIC_GROUP_C
  LEFT JOIN [Clarity].[dbo].ZC_COUNTY        [county_zc]
    ON [pat].COUNTY_C = [county_zc].COUNTY_C
  LEFT JOIN [Clarity].[dbo].ZC_COUNTY        [county_tmp_zc]
    ON [pat].TMP_COUNTY_C = [county_tmp_zc].COUNTY_C
-- exclude patients with an english-speaking caregiver
WHERE [#caregiver_languages].[Caregiver Languages] NOT LIKE '%ENGLISH%'
  OR ([#caregiver_languages].[Caregiver Languages] IS NULL
      AND (
          [pat].LANGUAGE_C IS NULL
          OR
          -- exclude if no Caregiver languages but patient language is 'English'
          [pat].LANGUAGE_C <> 22
      )
  )
;

GO
