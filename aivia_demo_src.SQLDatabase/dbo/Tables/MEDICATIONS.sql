CREATE TABLE [dbo].[MEDICATIONS] (
    [CM_LOG_OWNER_ID]        NVARCHAR (400)  NULL,
    [CM_PHY_OWNER_ID]        NVARCHAR (400)  NULL,
    [CONTROLLED_MED_FLAG]    NVARCHAR (400)  NULL,
    [COST]                   NVARCHAR (400)  NULL,
    [DAY_SUP_ENABLE_FLAG]    NVARCHAR (400)  NULL,
    [DEA_CLASS_CODE_CODE]    INT             NULL,
    [EQUIP_STATUS_FLAG]      NVARCHAR (400)  NULL,
    [FORM]                   NVARCHAR (400)  NULL,
    [GENERIC_NAME]           NVARCHAR (400)  NULL,
    [GPI]                    NVARCHAR (400)  NULL,
    [INVESTIGATL_MED_FLAG]   NVARCHAR (400)  NULL,
    [MEDICATION_ID]          DECIMAL (18, 4) NULL,
    [MED_IS_CONFIGURED_CODE] INT             NULL,
    [NAME]                   NVARCHAR (400)  NULL,
    [PHARM_CLASS_CODE]       INT             NULL,
    [PHARM_SUBCLASS_CODE]    INT             NULL,
    [RECORD_STATE]           NVARCHAR (400)  NULL,
    [ROUTE]                  NVARCHAR (400)  NULL,
    [SIMPLE_GENERIC_CODE]    NVARCHAR (400)  NULL,
    [STRENGTH]               NVARCHAR (400)  NULL,
    [THERA_CLASS_CODE]       INT             NULL,
    [_SURROGATEKEY]          BIGINT          NULL
);


GO

