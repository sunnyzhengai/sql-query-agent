CREATE TABLE [dbo].[V_PATIENT_LOCATION_HISTORY] (
    [ADT_BED_ENC]             DECIMAL (18, 4) NULL,
    [ADT_BED_ID]              NVARCHAR (400)  NULL,
    [ADT_BED_LABEL_WID]       NVARCHAR (400)  NULL,
    [ADT_DEPARTMENT_ID]       DECIMAL (18, 4) NULL,
    [ADT_DEPARTMENT_NAME]     NVARCHAR (400)  NULL,
    [ADT_DEPARTMENT_NM_WID]   NVARCHAR (400)  NULL,
    [ADT_LOC_ID]              DECIMAL (18, 4) NULL,
    [ADT_LOC_NAME]            NVARCHAR (400)  NULL,
    [ADT_LOC_NM_WID]          NVARCHAR (400)  NULL,
    [ADT_ROOM_ENC]            DECIMAL (18, 4) NULL,
    [ADT_ROOM_ID]             NVARCHAR (400)  NULL,
    [ADT_ROOM_NM_WID]         NVARCHAR (400)  NULL,
    [ADT_SERVICE_AREA_ID]     DECIMAL (18, 4) NULL,
    [ADT_SERVICE_AREA_NAME]   NVARCHAR (400)  NULL,
    [ADT_SERVICE_AREA_NM_WID] NVARCHAR (400)  NULL,
    [ENCOUNTER_NUM]           DECIMAL (18, 4) NULL,
    [EVENT_ID]                DECIMAL (18, 4) NULL,
    [EVENT_TYPE_CODE]         INT             NULL,
    [IN_DTTM]                 DATETIME2 (7)   NULL,
    [OUT_DTTM]                DATETIME2 (7)   NULL,
    [PATIENT_OUT_DTTM]        DATETIME2 (7)   NULL
);


GO

