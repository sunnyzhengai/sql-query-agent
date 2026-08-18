CREATE TABLE [dbo].[ENCOUNTER_VISIT_REASONS] (
    [BODY_LOC_ID]           DECIMAL (18, 4) NULL,
    [CM_CT_OWNER_ID]        NVARCHAR (400)  NULL,
    [COMMENTS]              NVARCHAR (400)  NULL,
    [CONTACT_DATE]          DATETIME2 (7)   NULL,
    [ENCOUNTER_ID]          DECIMAL (18, 4) NULL,
    [ENC_REASON_ID]         DECIMAL (18, 4) NULL,
    [ENC_REASON_NAME]       NVARCHAR (400)  NULL,
    [ENC_REASON_OTHER]      NVARCHAR (400)  NULL,
    [LINE]                  INT             NULL,
    [PATIENT_ENC_DATE_REAL] FLOAT (53)      NULL,
    [PATIENT_ID]            NVARCHAR (400)  NULL,
    [RFV_ONSET_DT]          DATETIME2 (7)   NULL,
    [_SURROGATEKEY]         BIGINT          NULL
);


GO

