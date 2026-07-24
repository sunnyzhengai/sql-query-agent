USE [CookClarity]
GO

/****** Object: StoredProcedure [Reporting].[USP_CCHCS_ScanningSummaryReports_PBI]    Script Date: 7/23/2026 10:53:30 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****************************************************************************************************
    TITLE:      [USP_BCMA_SUMMARY_REPORTS]
    REPORT NAME: This sp is used by 2 reports:
                    1. BCMA 100% Scanners
                    2. Scanning for Safety Report
    PURPOSE:    This stored procedure combines data from medication, blood, and specimen scanning, and generate the two summary reports
    AUTHOR:     Eric Tong
    PARAMETERS:
                    i_vRelativeStartDate    - VARCHAR(20)    - string containing relative start date
                    i_vRelativeEndDate      - VARCHAR(20)    - string containing relative end date
                    @ReportType             bit              - 0: Scanning for Safety Report, 1: BCMA 100% Scanners
    RETURNS:    None
    DESTINATION TABLE(S): None
    REVISION HISTORY:
                    2019-02-07 Eric Tong - Original version
                    2019-02-13 Eric Tong - Updated logic to pull documenting user first, then MAR user
                    2019-04-16 Eric Tong - Added calculation for overall compliance %
                    2021-11-19 KB - Added Respiratory Therapy Department Roll up
                    2023-05-04 Heidi Dammen - #1815556 - separating CCMC and PCCMC data

    USAGE:
            EXEC [CookClarity].[Reporting].[USP_CCHCS_ScanningSummaryReports_PBI] 'mb-2' ,'me-1', 0

****************************************************************************************************/

CREATE   PROCEDURE [Reporting].[USP_CCHCS_ScanningSummaryReports_PBI] (
    --DECLARE
    @i_vRelativeStartDate VARCHAR(20) = NULL
    , @i_vRelativeEndDate VARCHAR(20) = NULL
    , @ReportType bit = 0 -- 0 = Scanning for Safety Report; 1 = BCMA 100% Scanners
)

AS

BEGIN

    DECLARE @dStartDate         DATETIME,
            @dEndDate           DATETIME,
            @dLastMonthDate     DATETIME,
            @bLastMonth         Bit

    SET @dStartDate = clarity.[EPIC_UTIL].[EFN_DIN](coalesce(@i_vRelativeStartDate,'mb-1'));
    SET @dEndDate = clarity.[EPIC_UTIL].[EFN_DIN](coalesce(@i_vRelativeEndDate,'me-1'));
    SET @dLastMonthDate = clarity.[EPIC_UTIL].[EFN_DIN]('me-1');

    if object_id('tempdb..#lab') is not null
        drop table #lab

    if object_id('tempdb..#lab_compliant_by_dept') is not null
        drop table #lab_compliant_by_dept

    if object_id('tempdb..#lab_compliant_by_user') is not null
        drop table #lab_compliant_by_user

    if object_id('tempdb..#blood_and_meds') is not null
        drop table #blood_and_meds

    if object_id('tempdb..#blood_meds_compliant') is not null
        drop table #blood_meds_compliant

    if object_id('tempdb..#blood_meds_compliant_by_dept') is not null
        drop table #blood_meds_compliant_by_dept

    if object_id('tempdb..#blood_meds_compliant_by_user') is not null
        drop table #blood_meds_compliant_by_user

    if object_id('tempdb..#dep_summary') is not null
        drop table #dep_summary

    if object_id('tempdb..#user_summary') is not null
        drop table #user_summary

    /****************************************************************************************************
    Lab/Specimen Scanning Details
    ****************************************************************************************************/
    SELECT ORDER_PROC_3.ORDER_ID
        ,case when ALT_ORDINFO.ALT_ID is null or ALERT.GENERAL_ALT_TYPE_C not in (34562,51000)
                then ORDER_PROC_2.SPECIMEN_TAKEN_TIME
                else ALT_HISTORY.ALT_ACTION_INST
        end as [ACTION_DATE_TIME]
        ,case when ALT_ORDINFO.ALT_ID is null or ALERT.GENERAL_ALT_TYPE_C not in (34562,51000)
                then CLARITY_EMP.USER_ID
                else CLARITY_EMP_alert.USER_ID
        end as [USER_ID]
        ,case when ALT_ORDINFO.ALT_ID is null or ALERT.GENERAL_ALT_TYPE_C not in (34562,51000)
                then CLARITY_EMP.NAME
                else CLARITY_EMP_alert.NAME
        end as [USER_NAME]
        ,case when ALT_ORDINFO.ALT_ID is null or ALERT.GENERAL_ALT_TYPE_C not in (34562,51000)
                then CLARITY_DEP.DEPARTMENT_ID
                else CLARITY_DEP_alert.DEPARTMENT_ID
        end as [DEPARTMENT_ID]
        ,case when ALT_ORDINFO.ALT_ID is null or ALERT.GENERAL_ALT_TYPE_C not in (34562,51000)
                then CLARITY_DEP.DEPARTMENT_NAME
                else CLARITY_DEP_alert.DEPARTMENT_NAME
        end as DEPARTMENT_NAME
        ,case when ORDER_PROC_3.COLLECT_PPID_REQ_C in (23,24) then 'Nurse'
                else 'Lab'
        end as COMPLIANT_TYPE
        ,case when ALT_ORDINFO.ALT_ID is null or ALERT.GENERAL_ALT_TYPE_C not in (34562,51000)
                then 1
                else 0
        end as SCANNED_ORDER
        ,case when ALT_ORDINFO.ALT_ID is null or ALERT.GENERAL_ALT_TYPE_C not in (34562,51000)
                then coalesce(ZC_DEP_RPT_GRP_12.NAME,CLARITY_DEP.DEPARTMENT_NAME, '*Unspecified Department')
                else coalesce(ZC_DEP_grp12_alert.NAME,CLARITY_DEP_alert.DEPARTMENT_NAME, '*Unspecified Department')
        end as DEPARTMENT_GROUP
        , CASE WHEN CLARITY_DEP.DEPARTMENT_ID = 'SURGERY_AREA' then 'Surgery'
            when REVIEW_AREA_collect.GROUPER_RECORDS_NUMERIC_ID is not null then 'Review'
            when RADIOLOGY_AREA_collect.GROUPER_RECORDS_NUMERIC_ID is not null then 'Radiology'
            else coalesce(ZC_DEP_grp13.NAME,'Review')
        end as AREA
        , CASE WHEN CLARITY_DEP.REV_LOC_ID in ('108200', '108299') THEN 'PCCMC' ELSE 'CCMC' END [Location]
        , fy.COOK_FY [FY Year]
        , fy.COOK_FY_MONTH_NUMBER [FY Month #]
        , fy.MONTH_NAME [FY Month]
        , CASE WHEN fy.MONTH_END_DT = @dLastMonthDate THEN 1 ELSE 0 END [Last Month]

    into #lab
    FROM Clarity.dbo.ORDER_PROC_3
    LEFT OUTER JOIN Clarity.dbo.ALT_ORDINFO ON ORDER_PROC_3.ORDER_ID = ALT_ORDINFO.ORDER_ID
    LEFT OUTER JOIN Clarity.dbo.ORDER_PROC ON ORDER_PROC_3.ORDER_ID = ORDER_PROC.ORDER_PROC_ID
    LEFT OUTER JOIN Clarity.dbo.ORDER_PROC_2 ON ORDER_PROC_3.ORDER_ID = ORDER_PROC_2.ORDER_PROC_ID
    LEFT OUTER JOIN Clarity.dbo.CLARITY_EAP ON ORDER_PROC_3.ORDER_ID = CLARITY_EAP.PROC_ID
    LEFT JOIN Clarity.dbo.ALT_HISTORY ON ALT_ORDINFO.ALT_ID = ALT_HISTORY.ALT_ID
    LEFT JOIN Clarity.dbo.ALERT ON ALT_ORDINFO.ALT_ID = ALERT.ALT_ID
    LEFT JOIN CLARITY..ZC_ALT_SP_OVR_RSN crsnd ON msdn.SPEC_RSK_C = crsnd.ALT_SP_OVR_RSN_C
    LEFT JOIN CLARITY..ZC_ALT_SP_OVR_RSN crpat ON msdn.SPEC_RSK_C = crpat.ALT_SP_OVR_RSN_C
    LEFT JOIN Clarity.dbo.CLARITY_EMP ON ORDER_PROC_2.SPECIMEN_TAKEN_TIME IS NOT NULL AND CLARITY_EMP.USER_ID = ORDER_PROC_2.SPECIMEN_COLLECT_ID
    LEFT JOIN Clarity.dbo.CLARITY_EMP CLARITY_EMP_alert ON ALT_HISTORY.USER_ID = CLARITY_EMP_alert.USER_ID
    LEFT JOIN Clarity.dbo.CLARITY_DEP ON CLARITY_EMP.DEPARTMENT_ID = dep.DEPARTMENT_ID
    LEFT JOIN Clarity.dbo.CLARITY_DEP CLARITY_DEP_alert ON CLARITY_EMP_alert.DEPARTMENT_ID = CLARITY_DEP_alert.DEPARTMENT_ID
    LEFT OUTER JOIN Clarity.dbo.ZC_DEP_RPT_GRP 10 depgrp12 on dep.RPT_GRP_TWELVE_C = depgrp12.RPT_GRP_TWELVE_C -- collect department group
    LEFT OUTER JOIN Clarity.dbo.ZC_DEP_RPT_GRP 13 depgrp13 on dep.RPT_GRP_THIRTEEN_C = depgrp13.RPT_GRP_THIRTEEN_C -- area
    LEFT OUTER JOIN Clarity.dbo.GROUPER_COMPILED_REC_LIST SURGERY_AREA
        on dep.DEPARTMENT_ID = SURGERY_AREA.GROUPER_RECORDS_NUMERIC_ID and SURGERY_AREA_collect.BASE_GROUPER_ID = '115279'
    LEFT OUTER JOIN Clarity.dbo.GROUPER_COMPILED_REC_LIST REVIEW_AREA
        on dep.DEPARTMENT_ID = REVIEW_AREA.GROUPER_RECORDS_NUMERIC_ID and REVIEW_AREA_collect.BASE_GROUPER_ID = '115277'
    LEFT OUTER JOIN Clarity.dbo.GROUPER_COMPILED_REC_LIST RADIOLOGY_AREA
        on CLARITY_DEP.alert.DEPARTMENT_ID = RADIOLOGY_AREA.GROUPER_RECORDS_NUMERIC_ID and RADIOLOGY_AREA_collect.BASE_GROUPER_ID = '115335'
    LEFT JOIN Clarity.dbo.CLARITY_EMP emp on ORDER_PROC_2.COLLECTOR_ID = CLARITY_EMP.USER_ID
    LEFT JOIN Clarity.dbo.CLARITY_LOC loc on dep.REV_LOC_ID = loc.LOC_ID
    LEFT JOIN CookClarity.dbo.COOK_FY_CALENDAR fy on fy.CALENDAR_DT = CONVERT(DATE, ORDER_PROC_2.SPECIMEN_TAKEN_TIME)
    WHERE ORDER_PROC_2.SPECIMEN_TAKEN_TIME >= @dStartDate AND ORDER_PROC_2.SPECIMEN_TAKEN_TIME <= @dEndDate
        and (medAdmin.MED_REQUIRED_SCAN_BOOL=1 or medAdmin.PAT_REQUIRED_SCAN_BOOL=1)
        and (medAdmin.MAR_BLOOD_INFO_LN is not null or (rx.SPECIAL_MED_TYPE_C is null or rx.SPECIAL_MED_TYPE_C <> 5))

    /****************************************************************************************************
    Specimen scanning compliant by department
    ****************************************************************************************************/
    select ORDER_ID [Order ID]
        ,AREA [Area]
        ,DEPARTMENT_NAME
        ,coalesce(DEPARTMENT_NAME, '*Unspecified Department') as DEPARTMENT_NAME
        ,DEPARTMENT_GROUP [Department Group]
        ,COMPLIANT_TYPE [Compliant Type]
        ,min(SCANNED_ORDER) as [Compliant]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]

    into #lab_compliant_by_dept
    from #lab
    group by ORDER_ID
        ,AREA
        ,DEPARTMENT_GROUP
        ,COMPLIANT_TYPE
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]

    /****************************************************************************************************
    Specimen scanning compliant by user
    ****************************************************************************************************/
    select ORDER_ID [Order ID]
        ,[USER_ID] [User ID]
        ,[USER_NAME] [User Name]
        ,min(SCANNED_ORDER) as [Compliant]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]

    into #lab_compliant_by_user
    from #lab
    group by ORDER_ID
        ,[USER_ID]
        ,[USER_NAME]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]

    /****************************************************************************************************
    Blood and Medication Scanning details
    ****************************************************************************************************/
    SELECT medAdmin.ORDER_MED_ID
        ,medAdmin.TAKEN_DATETIME
        ,medAdmin.SAVED_DATETIME
        ,medAdmin.TAKEN_DATE
        ,medAdmin.HOSP_ADMSN_DATE
        ,medAdmin.HOSP_DISCH_DATE
        ,medAdmin.ADMIN_PAT_DEPT_ID
        ,dep.DEPARTMENT_NAME ADMIN_PAT_DEP_NAME
        ,dep.REV_LOC_ID ADMIN_PAT_LOC_ID
        ,loc.LOC_NAME ADMIN_PAT_LOC_NAME
        ,medAdmin.ADMIN_USER_ID
        ,emp.NAME AS ADMIN_USER_NAME
        ,medAdmin.PAT_ENC_CSN_ID
        ,medAdmin.PAT_ID
        ,pat.PAT_MRN_ID
        ,pat.PAT_NAME
        ,medAdmin.PAT_OVRIDE_ALERT_ID
        ,medAdmin.MED_OVRIDE_ALERT_ID
        ,medAdmin.MEDICATION_ID
        ,medAdmin.MED_REQUIRED_SCAN_BOOL
        ,medAdmin.MED_SCANNED_BOOL
        ,medAdmin.PAT_REQUIRED_SCAN_BOOL
        ,medAdmin.PAT_SCANNED_BOOL
        ,medAdmin.ENC_TYPE_C
        ,medAdmin.PROC_ID
        ,medAdmin.MAR_BLOOD_INFO_LN          --is not null then blood
        ,medAdmin.DISPLAY_NAME
        ,medAdmin.PROC_CODE
        ,medAdmin.CLIENT_SRC_C

        , rx.SPECIAL_MED_TYPE_C               --if equal 5 then Feedings
        , medah.SPEC_OVR_RSN_C    AS MED_SPEC_OVR_RSN_C
        , zcmed.NAME MED_REASON
        , patah.SPEC_OVR_RSN_C    AS PAT_SPEC_OVR_RSN_C
        , zcpat.NAME PAT_REASON

        , CASE
            WHEN medAdmin.MAR_BLOOD_INFO_LN is not null THEN 'Blood'
            --WHEN rx.SPECIAL_MED_TYPE_C = 5 THEN 'Feedings'
            WHEN medAdmin.MAR_BLOOD_INFO_LN is null and (rx.SPECIAL_MED_TYPE_C is null or rx.SPECIAL_MED_TYPE_C <> 5) THEN 'Medications'
            ELSE 'Unknown'
        END AS COMPLIANT_TYPE
        ,CASE WHEN ser.CREDENTIALS = 'RRT' THEN 'RESPIRATORY THERAPY'
            ELSE coalesce(depgrp12.NAME,dep.DEPARTMENT_NAME,'*Unspecified Department')
        END as DEPARTMENT_GROUP
        --,coalesce(depgrp12.NAME,dep.DEPARTMENT_NAME,'*Unspecified Department') as DEPARTMENT_GROUP--KB updated to the line above
        ,case when SURGERY_AREA.GROUPER_RECORDS_NUMERIC_ID is not null then 'Surgery'
                when REVIEW_AREA.GROUPER_RECORDS_NUMERIC_ID is not null then 'Review'
                when RADIOLOGY_AREA.GROUPER_RECORDS_NUMERIC_ID is not null then 'Radiology'
            else coalesce(depgrp13.NAME,'Review')
        end as AREA
        , CASE WHEN dep.REV_LOC_ID in ('108200' , '108299') THEN 'PCCMC' ELSE 'CCMC' END [Location]
        , fy.COOK_FY [FY Year]
        , fy.COOK_FY_MONTH_NUMBER [FY Month #]
        , fy.MONTH_NAME [FY Month]
        , CASE WHEN fy.MONTH_END_DT = @dLastMonthDate THEN 1 ELSE 0 END [Last Month]

    into #blood_and_meds
    FROM CLARITY_F.IP.HEP_SUM_MED_ADMIN medAdmin
    INNER JOIN CLARITY..MAR_ADMIN_INFO marAdmin on medAdmin.ORDER_MED_ID = marAdmin.ORDER_MED_ID and medAdmin.LINE = marAdmin.LINE
    INNER JOIN CLARITY..DATE_DIMENSION dd ON dd.CALENDAR_DT = medAdmin.TAKEN_DATE
    LEFT JOIN CLARITY..PATIENT pat ON medAdmin.PAT_ID = pat.PAT_ID
    LEFT JOIN CLARITY..CLARITY_DEP dep ON medAdmin.ADMIN_PAT_DEPT_ID = dep.DEPARTMENT_ID
    LEFT OUTER JOIN Clarity.dbo.ZC_DEP_RPT_GRP 12 depgrp12 on dep.RPT_GRP_TWELVE_C = depgrp12.RPT_GRP_TWELVE_C -- department group
    LEFT OUTER JOIN Clarity.dbo.ZC_DEP_RPT_GRP 13 depgrp13 on dep.RPT_GRP_THIRTEEN_C = depgrp13.RPT_GRP_THIRTEEN_C -- area
    LEFT OUTER JOIN Clarity.dbo.GROUPER_COMPILED_REC_LIST SURGERY_AREA
        on dep.DEPARTMENT_ID = SURGERY_AREA.GROUPER_RECORDS_NUMERIC_ID and SURGERY_AREA.BASE_GROUPER_ID = '115279'
    LEFT OUTER JOIN Clarity.dbo.GROUPER_COMPILED_REC_LIST REVIEW_AREA
        on dep.DEPARTMENT_ID = REVIEW_AREA.GROUPER_RECORDS_NUMERIC_ID and REVIEW_AREA.BASE_GROUPER_ID = '115277'
    LEFT OUTER JOIN Clarity.dbo.GROUPER_COMPILED_REC_LIST RADIOLOGY_AREA
        on CLARITY_DEP.alert.DEPARTMENT_ID = RADIOLOGY_AREA.GROUPER_RECORDS_NUMERIC_ID and RADIOLOGY_AREA.BASE_GROUPER_ID = '115335'
    LEFT JOIN Clarity.dbo.CLARITY_EMP emp on medAdmin.ADMIN_USER_ID = CLARITY_EMP.USER_ID
    LEFT JOIN CLARITY..CLARITY_SER ser on medAdmin.ADMIN_USER_ID = ser.PROV_ID
    LEFT JOIN CLARITY..CLARITY_LOC loc on dep.REV_LOC_ID = loc.LOC_ID
    LEFT JOIN CookClarity.dbo.COOK_FY_CALENDAR fy on fy.CALENDAR_DT = CONVERT(DATE, medAdmin.TAKEN_DATE)
    LEFT JOIN CLARITY..CLARITY_MEDICATION rx on medAdmin.MEDICATION_ID = rx.MEDICATION_ID
    LEFT JOIN CLARITY..ALT_HISTORY medah ON medAdmin.MED_OVRIDE_ALERT_ID = medah.ALT_ID
    LEFT JOIN CLARITY..ALT_HISTORY patah on medAdmin.PAT_OVRIDE_ALERT_ID = patah.ALT_ID
    LEFT JOIN CLARITY..ZC_ALT_SP_OVR_RSN zcmed on medah.SPEC_RSK_C = zcmed.ALT_SP_OVR_RSN_C
    LEFT JOIN CLARITY..ZC_ALT_SP_OVR_RSN zcpat on patah.SPEC_RSK_C = zcpat.ALT_SP_OVR_RSN_C
    LEFT JOIN Clarity.dbo.BLOOD_ADMIN_INFO blood ON (medAdmin.ORDER_MED_ID = blood.ORDER_ID AND medAdmin.MAR_BLOOD_INFO_LN=blood.LINE)
    LEFT JOIN CLARITY..ZC_NO_YES_MA rczn_exp ON medAdmin.CLIENT_SRC_C = rczn.CLIENT_SRC_C
    LEFT JOIN CLARITY..ZC_NO_YES_MA rczn_exp ON blood.BLOOD_SCHCMP_PC_C = rczn_exp.NO_YES_MA_C
    LEFT JOIN CLARITY..ZC_NO_YES_MA rczn_rep ON blood.BLOOD_SCHCMP_PC_C = rczn_rep.NO_YES_MA_C
    LEFT JOIN CLARITY..ZC_NO_YES_MA rczn_type ON blood.BLOOD_SCHCMP_TYPE_C = rczn_type.NO_YES_MA_C
    LEFT JOIN CLARITY..ZC_MAR_MULT_ACTION_C rcact on medAdmin.MAR_ACTION_C=rcact.action_RESULT_C
    LEFT JOIN CookClarity.COOK_FY_COST_DATE_DIMENSION fy on fy.CALENDAR_DT = CONVERT(DATE, medAdmin.TAKEN_DATE)
    WHERE
        medAdmin.TAKEN_DATE BETWEEN @dStartDate AND @dEndDate
        and (medAdmin.MED_REQUIRED_SCAN_BOOL=1 or medAdmin.PAT_REQUIRED_SCAN_BOOL=1)
        and (medAdmin.MAR_BLOOD_INFO_LN is not null or (rx.SPECIAL_MED_TYPE_C is null or rx.SPECIAL_MED_TYPE_C <> 5)) -- Blood and Medication

    /****************************************************************************************************
    Blood and Medication Scanning: Get the compliant status for each order
    ****************************************************************************************************/
    select ORDER_MED_ID as [Order ID]
        ,AREA [Area]
        ,DEPARTMENT_GROUP [Department Group]
        ,COMPLIANT_TYPE [Compliant Type]
        /*
        ,CASE WHEN (MED_SCANNED_BOOL=1 OR MED_REQUIRED_SCAN_BOOL=0 OR MED_SPEC_OVR_RSN_C is not null)
                    AND (PAT_SCANNED_BOOL=1 OR PAT_REQUIRED_SCAN_BOOL=0 OR PAT_SPEC_OVR_RSN_C is not null)
            THEN 1
            ELSE 0
        END as COMPLIANT
        */
        ,case when MED_SCANNED_BOOL=1 and PAT_SCANNED_BOOL=1 then 1 else 0 end as [Compliant]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]
    into #blood_meds_compliant
    from #blood_and_meds

    /****************************************************************************************************
    Blood and Medication compliant by department
    ****************************************************************************************************/
    select [Order ID]
        , [Area]
        --,DEPARTMENT_ID
        --,DEPARTMENT_NAME
        , [Department Group]
        , [Compliant Type]
        , [Compliant]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]
    into #blood_meds_compliant_by_dept
    from #blood_meds_compliant

    /****************************************************************************************************
    Blood and Medication compliant by user
    ****************************************************************************************************/
    select [Order ID]
        , [User ID]
        , [User Name]
        , [Compliant]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]
    into #blood_meds_compliant_by_user
    from #blood_meds_compliant

    /****************************************************************************************************
    Summary by Department: combine lab + blood + med into one summary
    ****************************************************************************************************/
    select AREA [Area]
        --,DEPARTMENT_ID
        --,DEPARTMENT_NAME
        , [Department Group]
        ,sum(case when [Compliant Type] = 'Nurse' then 1 else 0 end) as [Nurse Count]
        ,sum(case when [Compliant Type] = 'Nurse'
                then case when COMPLIANT = 1 then 1
                    else 0
                end
        end) as [Nurse Compliant]
        ,sum(case when [Compliant Type] = 'Lab' then 1 else 0 end) as [Lab Count]
        ,sum(case when [Compliant Type] = 'Lab'
                then case when COMPLIANT = 1 then 1
                    else 0
                end
        end) as [Lab Compliant]
        ,sum(case when [Compliant Type] = 'Blood' then 1 else 0 end) as [Blood Count]
        ,sum(case when [Compliant Type] = 'Blood'
                then case when COMPLIANT = 1 then 1
                    else 0
                end
        end) as [Blood Compliant]
        ,sum(case when [Compliant Type] = 'Medications' then 1 else 0 end) as [Med Count]
        ,sum(case when [Compliant Type] = 'Medications'
                then case when COMPLIANT = 1 then 1
                    else 0
                end
        end) as [Med Compliant]
        ,sum(case when [Compliant Type] in ('Nurse','Lab','Blood','Medications') then 1 else 0 end) as [Overall Count]
        ,sum(case when [Compliant Type] in ('Nurse','Lab','Blood','Medications')
                then case when COMPLIANT = 1 then 1
                    else 0
                end
        end) as [Overall Compliant]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]
    into #dep_summary
    from (select * from #lab_compliant_by_dept
            union all
            select * from #blood_meds_compliant_by_dept
        ) a
    Where [Department Group] <> 'Hurst Periop'
    group by AREA, [Department Group], [Location], [FY Year], [FY Month #], [FY Month], [Last Month]

    /****************************************************************************************************
    Summary by User: combine lab + blood + med into one summary
    Select users with 100% scan rate and have > 24 chances to scan
    ****************************************************************************************************/
    select [User ID]
        , [User Name]
        , COUNT([Order ID]) as [Count]
        , SUM([Compliant]) as [Compliant]
        , [Location]
        , [FY Year]
        , [FY Month #]
        , [FY Month]
        , [Last Month]
    into #user_summary
    from (select * from #lab_compliant_by_user
            union all
            select * from #blood_meds_compliant_by_user
        ) a
    group by [User ID], [User Name], [Location], [FY Year], [FY Month #], [FY Month], [Last Month]
    having COUNT([Order ID]) > 24
    and COUNT([Order ID]) = sum([Compliant])

    /****************************************************************************************************
    -- display dept or user summary base on parameter
    ****************************************************************************************************/
    IF @ReportType = 0
    begin
        select * From #dep_summary
    end
    else
    begin
        select *,RAND(CHECKSUM(NEWID())) as RAND_NUM from #user_summary order by RAND(CHECKSUM(NEWID()))
    end

    ;
END
GO
