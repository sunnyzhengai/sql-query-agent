CREATE TABLE [dbo].[BED_CONFIG] (
    [ACCOMMODATION_CODE]         NVARCHAR (400)  NULL,
    [ADDL_FLAG_CODE]             INT             NULL,
    [BED_CONT_DATE_REAL]         FLOAT (53)      NULL,
    [BED_ID]                     NVARCHAR (400)  NULL,
    [BED_LABEL]                  NVARCHAR (400)  NULL,
    [BED_STATUS_CODE]            NVARCHAR (400)  NULL,
    [BED_STAY_ID]                DECIMAL (18, 4) NULL,
    [CENSUS_INCLUSN_FLAG]        NVARCHAR (400)  NULL,
    [CM_LOG_OWNER_ID]            NVARCHAR (400)  NULL,
    [CM_PHY_OWNER_ID]            NVARCHAR (400)  NULL,
    [CONTACT_DATE]               DATETIME2 (7)   NULL,
    [DFLT_SVC_PRI_CODE]          INT             NULL,
    [ED_HOLD_ARR_MODE_CODE]      NVARCHAR (400)  NULL,
    [ED_HOLD_CREATE_DTTM]        DATETIME2 (7)   NULL,
    [ED_HOLD_EX_DTTM]            DATETIME2 (7)   NULL,
    [ED_HOLD_FLAG]               NVARCHAR (400)  NULL,
    [END_CONT_DATE_REAL]         FLOAT (53)      NULL,
    [EVS_OPT_OUT_FLAG]           NVARCHAR (400)  NULL,
    [GO_LIVE_DATE]               DATETIME2 (7)   NULL,
    [HAAG_INCLUDE_CODE]          INT             NULL,
    [IS_BUNK_CODE]               INT             NULL,
    [IVR_NAME]                   NVARCHAR (400)  NULL,
    [LEVEL_OF_CARE_GROUPER_CODE] INT             NULL,
    [PERIOPERATIVE_FLAG]         NVARCHAR (400)  NULL,
    [PERMANENTLY_CLOSED_DATE]    DATETIME2 (7)   NULL,
    [POOL_BED_FLAG]              NVARCHAR (400)  NULL,
    [RECORD_STATE]               NVARCHAR (400)  NULL,
    [ROOM_ID]                    NVARCHAR (400)  NULL,
    [SERVICE_GROUPER_CODE]       INT             NULL,
    [SVC_PRIORITY_CODE]          INT             NULL,
    [TELEPHONE_NUMBER]           NVARCHAR (400)  NULL
);


GO

