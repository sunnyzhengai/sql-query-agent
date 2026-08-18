CREATE TABLE [dbo].[V_PHARMACY_DISPENSE_ACTION] (
    [ACTION_DATE]            DATETIME2 (7)   NULL,
    [ACTION_DATE_REAL]       FLOAT (53)      NULL,
    [ACTION_DTTM]            DATETIME2 (7)   NULL,
    [ACTION_HOUR]            INT             NULL,
    [ACTION_ID]              DECIMAL (18, 4) NULL,
    [ACTION_NUM]             DECIMAL (18, 4) NULL,
    [ACTION_TYPE_CODE]       INT             NULL,
    [DISPENSE_ACTION]        NVARCHAR (400)  NULL,
    [DISP_CONTAINER_NAME]    NVARCHAR (400)  NULL,
    [DISP_SENT_METHOD]       NVARCHAR (400)  NULL,
    [DISP_SENT_METHOD_CODE]  INT             NULL,
    [RECEIVED_DEPARTMENT_ID] DECIMAL (18, 4) NULL,
    [RECEIVED_DEPT_NAME]     NVARCHAR (400)  NULL,
    [USER_ID]                NVARCHAR (400)  NULL
);


GO

