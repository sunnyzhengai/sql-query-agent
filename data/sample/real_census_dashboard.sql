-- Source: [Book_RPT].[usp_PTA_CensusDashboard_PBI]
-- Author: Adam Smith
-- Description: This procedure pulls Census data from ADT
-- Database: BookClarity (Epic Clarity)
-- Scrubbed: Org-specific identifiers removed

CREATE PROCEDURE [Book_RPT].[usp_PTA_CensusDashboard_PBI]
AS
SET NOCOUNT ON;

declare @StartDate DATE =
  case when dateadd(m, -24, getdate() - datepart(d, getdate()) + 1) < '03/01/2018'
  then '03/01/2018' else dateadd(m, -24, getdate() - datepart(d, getdate()) + 1) end

;with month_cte as
(select datepart(day, Max(adt.EFFECTIVE_TIME)) as 'CurrentMonth'
  from Clarity.dbo.CLARITY_ADT adt
  where adt.EVENT_TYPE_C = 6 --Census
    and EFFECTIVE_TIME >= @StartDate
    AND adt.PAT_ID IS NOT NULL
    AND adt.EVENT_SUBTYPE_C <> 2 --Canceled
)

SELECT
  adt.EFFECTIVE_TIME
, adt.PAT_ID
, pt.PAT_MRN_ID
, adt.PAT_ENC_CSN_ID
, adt.PAT_CLASS_C
, class.ABBR as 'ClassType'
, dep.DEPARTMENT_ID
, dep.DEPT_ABBREVIATION as 'Dept'
, dep.EXTERNAL_NAME as 'DeptName'
, room.ROOM_NAME as 'Room'
, bed.BED_LABEL as 'Bed'
, adt.PAT_SERVICE_C
, serv.ABBR as 'ServiceType'
, sa.SERV_AREA_NAME as 'ServiceArea'
, adt.EVENT_ID
, case
    when datepart(month, adt.EFFECTIVE_TIME) = datepart(month, getdate())
      and datepart(year, adt.EFFECTIVE_TIME) = datepart(year, getdate())
    then (Select CurrentMonth from month_cte)
    else datediff(dd, adt.EFFECTIVE_TIME, dateadd(mm, 1, adt.EFFECTIVE_TIME))
  end as 'DayinMonth'
, (select MAX(EXEC_START_TIME)
   from clarity.dbo.CR_STAT_EXECUTION
   where EXEC_SCHEDULED_YN = 'Y'
     AND EXEC_NAME = 'Daily_ETL'
  ) as 'RefreshDate'
, CONVERT(DATE, pt.BIRTH_DATE) [DOB]
, CASE
    WHEN DATEDIFF(DAY, CONVERT(DATE, pt.BIRTH_DATE), adt.EFFECTIVE_TIME) > 31
    THEN 'over 30 days' ELSE 'under 30 days'
  END [age]
, CASE
    WHEN dep.REV_LOC_ID = 100200 THEN 'PCCMC' ELSE 'CCMC'
  END [Location]
, disp.NAME as Disch_Deposition
, hsp.DISCH_DISP_C
FROM Clarity.dbo.CLARITY_ADT adt
  LEFT OUTER JOIN Clarity.dbo.CLARITY_BED bed
    ON adt.BED_CSN_ID=bed.BED_CSN_ID
  LEFT OUTER JOIN Clarity.dbo.CLARITY_ROM room
    ON adt.ROOM_CSN_ID=room.ROOM_CSN_ID
  LEFT OUTER JOIN Clarity.dbo.CLARITY_DEP dep
    ON adt.DEPARTMENT_ID=dep.DEPARTMENT_ID
  LEFT OUTER JOIN Clarity.dbo.ZC_PAT_CLASS class
    ON adt.PAT_CLASS_C=class.ADT_PAT_CLASS_C
  LEFT OUTER JOIN Clarity.dbo.ZC_PAT_SERVICE serv
    ON adt.PAT_SERVICE_C=serv.HOSP_SERV_C
  LEFT OUTER JOIN Clarity.dbo.CLARITY_SA sa
    ON dep.SERV_AREA_ID=sa.SERV_AREA_ID
  LEFT JOIN Clarity.dbo.PATIENT pt
    ON adt.PAT_ID = pt.PAT_ID
  Left Join Clarity.dbo.PAT_ENC_HSP hsp
    ON adt.PAT_ENC_CSN_ID = hsp.PAT_ENC_CSN_ID
  left join Clarity.dbo.ZC_DISCH_DISP disp
    ON hsp.DISCH_DISP_C = disp.DISCH_DISP_C
WHERE adt.EVENT_TYPE_C = 6 --Census
  and EFFECTIVE_TIME >= @StartDate
  AND adt.PAT_ID IS NOT NULL
  AND adt.EVENT_SUBTYPE_C <> 2 --Canceled
  AND dep.SERV_AREA_ID = 10
order by adt.EFFECTIVE_TIME, adt.ROOM_ID
GO
