CREATE TABLE [dbo].[ALERT_ACTIONS] (
    [ACTION_TAKEN_CODE] INT             NULL,
    [ALERT_ID]          DECIMAL (18, 4) NULL,
    [ALT_ENCOUNTER_ID]  DECIMAL (18, 4) NULL,
    [CM_CT_OWNER_ID]    NVARCHAR (400)  NULL,
    [CONTACT_DATE]      DATETIME2 (7)   NULL,
    [CONTACT_DATE_REAL] FLOAT (53)      NULL,
    [LINE]              INT             NULL
);


GO

