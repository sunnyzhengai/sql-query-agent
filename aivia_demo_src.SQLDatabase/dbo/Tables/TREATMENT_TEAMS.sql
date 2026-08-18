CREATE TABLE [dbo].[TREATMENT_TEAMS] (
    [CM_CT_OWNER_ID]        NVARCHAR (400)  NULL,
    [ENCOUNTER_ID]          DECIMAL (18, 4) NULL,
    [LINE]                  INT             NULL,
    [PATIENT_ENC_DATE_REAL] FLOAT (53)      NULL,
    [PATIENT_ID]            NVARCHAR (400)  NULL,
    [PROV_ID]               NVARCHAR (400)  NULL,
    [TEAM_ADD_FLAG]         NVARCHAR (400)  NULL,
    [TRTMNT_TEAM_REL_CODE]  NVARCHAR (400)  NULL,
    [TRTMNT_TM_BEGIN_DT]    DATETIME2 (7)   NULL,
    [TRTMNT_TM_ED_FLAG]     NVARCHAR (400)  NULL,
    [TRTMNT_TM_END_DT]      DATETIME2 (7)   NULL,
    [_SURROGATEKEY]         BIGINT          NULL
);


GO

