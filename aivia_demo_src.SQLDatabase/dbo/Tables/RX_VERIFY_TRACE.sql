CREATE TABLE [dbo].[RX_VERIFY_TRACE] (
    [CM_LOG_OWNER_ID]        NVARCHAR (400)  NULL,
    [CM_PHY_OWNER_ID]        NVARCHAR (400)  NULL,
    [DEFER_PROVIDER_CODE]    NVARCHAR (400)  NULL,
    [DEFER_SPECIALTY_CODE]   NVARCHAR (400)  NULL,
    [LINE]                   INT             NULL,
    [ORDER_MED_ID]           DECIMAL (18, 4) NULL,
    [RXQ_INSTANT]            DATETIME2 (7)   NULL,
    [RXQ_REASON_CODE]        INT             NULL,
    [RX_AUDIT_TRL_GRP_LN]    INT             NULL,
    [RX_UNQUEUE_REASON_CODE] INT             NULL,
    [RX_VERIFY_INSTANT]      DATETIME2 (7)   NULL,
    [RX_VER_IS_CANCEL_FLAG]  NVARCHAR (400)  NULL,
    [RX_VER_USER_DEP_ID]     DECIMAL (18, 4) NULL,
    [RX_VER_USER_ID]         NVARCHAR (400)  NULL
);


GO

