-- ==================================================================================
-- Author:		
-- Create date: March 28, 2019
-- Description:	This procedure pulls Census data from ADT
-- ==================================================================================
-- version	Date          Who						Description
-- -------	----------    -----------------			---------------------------------
-- 1.0.0	03/28/2019   				Developed - Zendesk 860655
-- ==================================================================================


CREATE PROCEDURE [COOK_RPT].[usp_SF_CensusDashboard]
                            
AS

SET NOCOUNT ON;



declare @StartDate DATE =  case when dateadd(m, -24, getdate() - datepart(d, getdate()) + 1) < '03/01/2018' then '03/01/2018' else dateadd(m, -24, getdate() - datepart(d, getdate()) + 1) end



;with month_cte as
(select datepart(day, Max(adt.EFFECTIVE_TIME)) as 'CurrentMonth' 
	from Clarity.dbo.CLARITY_ADT adt
	where adt.EVENT_TYPE_C = 6 --Census
		and EFFECTIVE_TIME >= @StartDate
		AND adt.PAT_ID IS NOT NULL  
		AND adt.EVENT_SUBTYPE_C <> 2 --Canceled
		)

SELECT --adt.EVENT_TYPE_C
		--, adt.EVENT_SUBTYPE_C
		 adt.EFFECTIVE_TIME
		, adt.PAT_ID
		, pt.PAT_MRN_ID
		, adt.PAT_ENC_CSN_ID
		, adt.PAT_CLASS_C
		, class.ABBR as 'ClassType'
		, dep.DEPT_ABBREVIATION as 'Dept'
		, dep.EXTERNAL_NAME as 'DeptName'
		, room.ROOM_NAME as 'Room'
		, bed.BED_LABEL as 'Bed'
		, adt.PAT_SERVICE_C
		, serv.ABBR  as 'ServiceType'
		, sa.SERV_AREA_NAME as 'ServiceArea'
		, adt.EVENT_ID
		, case when datepart(month, adt.EFFECTIVE_TIME) =  datepart(month, getdate()) 
					and datepart(year, adt.EFFECTIVE_TIME) = datepart(year, getdate())
				then (Select CurrentMonth from month_cte) 
				else datediff(dd,adt.EFFECTIVE_TIME,dateadd(mm,1,adt.EFFECTIVE_TIME)) end as 'DayinMonth'
		, /* Get last start time for daily etl job */
		(select MAX(EXEC_START_TIME)
			from clarity.dbo.CR_STAT_EXECUTION
			where EXEC_SCHEDULED_YN = 'Y'
				AND EXEC_NAME = 'Daily_ETL'	) as  'RefreshDate'
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
WHERE  adt.EVENT_TYPE_C = 6 --Census
	and EFFECTIVE_TIME >=  @StartDate
	AND adt.PAT_ID IS NOT NULL  
	AND adt.EVENT_SUBTYPE_C <> 2 --Canceled
	AND dep.SERV_AREA_ID = 10


order by adt.EFFECTIVE_TIME, adt.ROOM_ID
GO


