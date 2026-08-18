CREATE TABLE [dbo].[ORGANISMS] (
    [ABBREVIATION]           NVARCHAR (400)  NULL,
    [BIOTYPE_CODE]           INT             NULL,
    [CM_LOG_OWNER_ID]        NVARCHAR (400)  NULL,
    [CM_PHY_OWNER_ID]        NVARCHAR (400)  NULL,
    [EXTERNAL_NAME]          NVARCHAR (400)  NULL,
    [GENUS_CODE]             INT             NULL,
    [MDRO_ANY_ORGANISM_FLAG] NVARCHAR (400)  NULL,
    [MDRO_THRESHOLD]         INT             NULL,
    [MDRO_UPPER_THRESHOLD]   INT             NULL,
    [NAME]                   NVARCHAR (400)  NULL,
    [ORGANISM_GROUP_CODE]    INT             NULL,
    [ORGANISM_ID]            DECIMAL (18, 4) NULL,
    [ORGANISM_TYPE_CODE]     INT             NULL,
    [PHAGE_TYPE_CODE]        INT             NULL,
    [RECORD_STATE_CODE]      INT             NULL,
    [RECORD_STATUS_CODE]     INT             NULL,
    [RECORD_TYPE_CODE]       INT             NULL,
    [REC_STATE]              NVARCHAR (400)  NULL,
    [RESULT_CHECKING_ID]     DECIMAL (18, 4) NULL,
    [SEROTYPE_CODE]          INT             NULL,
    [SPECIES_CODE]           INT             NULL,
    [_SURROGATEKEY]          BIGINT          NULL
);


GO

