CREATE TABLE [dbo].[ENCOUNTER_DIAGNOSES] (
    [ANNOTATION]            NVARCHAR (400)  NULL,
    [CM_CT_OWNER_ID]        NVARCHAR (400)  NULL,
    [COMMENTS]              NVARCHAR (400)  NULL,
    [CONTACT_DATE]          DATETIME2 (7)   NULL,
    [DX_CHRONIC_FLAG]       NVARCHAR (400)  NULL,
    [DX_ED_FLAG]            NVARCHAR (400)  NULL,
    [DX_ID]                 DECIMAL (18, 4) NULL,
    [DX_LINK_PROB_ID]       DECIMAL (18, 4) NULL,
    [DX_QUALIFIER_CODE]     NVARCHAR (400)  NULL,
    [DX_STAGE_ID]           DECIMAL (18, 4) NULL,
    [DX_UNIQUE]             NVARCHAR (400)  NULL,
    [ENCOUNTER_ID]          DECIMAL (18, 4) NULL,
    [ENC_ICD_CODE]          NVARCHAR (400)  NULL,
    [ICD9_CODE]             NVARCHAR (400)  NULL,
    [LINE]                  INT             NULL,
    [PATIENT_ENC_DATE_REAL] FLOAT (53)      NULL,
    [PATIENT_ID]            NVARCHAR (400)  NULL,
    [PRIMARY_DX_FLAG]       NVARCHAR (400)  NULL,
    [UPDATE_DATE]           DATETIME2 (7)   NULL
);


GO

