/************************************************************************************
Author: 
Create date: 6/25/2025
Description: CC ADT Monthly Inpatient Census Days
Report Name: CC ADT Monthly Inpatient Census Days
=====================================================================================
Revision Detail
Created From: 
Date       Who                        Description
-------------------------------------------------------------------------------------
06/25/2025           Fabric Migration
=====================================================================================

************************************************************************************/


CREATE   PROCEDURE  [schema2].[USP__ADT_Monthly_IP_Census_Days_SSRS]
(
@GROUP1 Varchar(400),
@GROUP2 Varchar(400),
@GROUP3 Varchar(400),
@Month varchar(10),
@Year varchar(10),
@ServiceArea  varchar(20),
@TillDate Date

)

AS

DECLARE @SQL  VARCHAR(MAX) ,
		@STillDate VARCHAR(20),
		@CurrentMonth varchar(10),
		@NextMonth varchar(10)

SET @STillDate = FORMAT(TRY_CONVERT(DATETIME,@TillDate),'yyyy-MM-dd')

SET @CurrentMonth = @Year +'-'+@Month+'-01'
SET @NextMonth = FORMAT(DATEADD(MONTH,1,CONVERT(DATETIME,@CurrentMonth)),'yyyy-MM-dd')


SET @SQL = '
SELECT  
	DAY(CLARITY_ADT.EFFECTIVE_TIME) EFFECTIVE_DAY,'
	+@GROUP1 +' AS Group1,'
	+@GROUP2+ +' AS Group2,'
	+@GROUP3 +' AS Group3 ,
	 COUNT(CLARITY_ADT.EVENT_ID) COUNT_EVENT_ID
FROM Clarity.dbo.CLARITY_ADT CLARITY_ADT 
LEFT OUTER JOIN Clarity.dbo.CLARITY_BED CLARITY_BED ON CLARITY_ADT.BED_CSN_ID = CLARITY_BED.BED_CSN_ID
LEFT OUTER JOIN Clarity.dbo.CLARITY_ROM CLARITY_ROM ON CLARITY_ADT.ROOM_CSN_ID = CLARITY_ROM.ROOM_CSN_ID
LEFT OUTER JOIN Clarity.dbo.CLARITY_DEP CLARITY_DEP ON CLARITY_ADT.DEPARTMENT_ID = CLARITY_DEP.DEPARTMENT_ID
LEFT OUTER JOIN Clarity.dbo.ZC_PAT_CLASS ZC_PAT_CLASS ON CLARITY_ADT.PAT_CLASS_C = ZC_PAT_CLASS.ADT_PAT_CLASS_C
LEFT OUTER JOIN Clarity.dbo.ZC_PAT_SERVICE ZC_PAT_SERVICE ON CLARITY_ADT.PAT_SERVICE_C = ZC_PAT_SERVICE.HOSP_SERV_C
LEFT OUTER JOIN Clarity.dbo.CLARITY_SA CLARITY_SA ON CLARITY_DEP.SERV_AREA_ID = CLARITY_SA.SERV_AREA_ID
WHERE CLARITY_ADT.EVENT_TYPE_C = 6 
 AND  (CLARITY_ADT.EFFECTIVE_TIME>= '''+@CurrentMonth+''' 
 AND CLARITY_ADT.EFFECTIVE_TIME< '''+@NextMonth+''')
 AND CLARITY_ADT.EVENT_TIME< '''+@STillDate+''' 
 AND CLARITY_ADT.PAT_ID IS  NOT  NULL 
 AND ((CLARITY_ADT.EVENT_SUBTYPE_C<>2) 
 OR (CLARITY_ADT.EVENT_SUBTYPE_C=2 
 AND CLARITY_ADT.DELETE_TIME>= '''+@STillDate+''')) 
 ' +CASE WHEN @ServiceArea <> '0' THEN 'AND CLARITY_DEP.SERV_AREA_ID= '+ CONVERT(VARCHAR(10),@ServiceArea) ELSE '' END
 +' 
 GROUP BY DAY(CLARITY_ADT.EFFECTIVE_TIME) , ' + @GROUP1 +','+@GROUP2 + ','+ @GROUP3 

EXEC (@SQL)
GO


