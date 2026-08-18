CREATE TABLE [dbo].[LINE_DEVICE_AIRWAY] (
    [ADDED_TO_BACKGROUND_AVATAR_CODE] INT             NULL,
    [AVATAR_CALCULATED_RECORD_ID]     DECIMAL (18, 4) NULL,
    [AVATAR_ORIENT_CODE]              INT             NULL,
    [AVATAR_PROPERTY_OVERRIDE_FLAG]   NVARCHAR (400)  NULL,
    [AVATAR_RECORD_ID]                DECIMAL (18, 4) NULL,
    [AVATAR_X_COORDINATE]             DECIMAL (18, 4) NULL,
    [AVATAR_Y_COORDINATE]             DECIMAL (18, 4) NULL,
    [CM_LOG_OWNER_ID]                 NVARCHAR (400)  NULL,
    [CM_PHY_OWNER_ID]                 NVARCHAR (400)  NULL,
    [DESCRIPTION]                     NVARCHAR (400)  NULL,
    [ENCOUNTER_ID]                    DECIMAL (18, 4) NULL,
    [FLO_MEAS_ID]                     NVARCHAR (400)  NULL,
    [FSD_ID]                          NVARCHAR (400)  NULL,
    [IP_LDA_ID]                       NVARCHAR (400)  NULL,
    [LDA_GROUP_CDR]                   FLOAT (53)      NULL,
    [LINKED_SUPPLY_ID]                NVARCHAR (400)  NULL,
    [PATIENT_ID]                      NVARCHAR (400)  NULL,
    [PLACEMENT_INSTANT]               DATETIME2 (7)   NULL,
    [PROPERTIES_DISPLAY]              NVARCHAR (400)  NULL,
    [RECORDED_DTTM]                   DATETIME2 (7)   NULL,
    [REC_ARCHIVED_FLAG]               NVARCHAR (400)  NULL,
    [REMOVAL_DTTM]                    DATETIME2 (7)   NULL,
    [REMOVAL_INSTANT]                 DATETIME2 (7)   NULL,
    [SITE]                            NVARCHAR (400)  NULL,
    [TRIP_BEGIN_DATE]                 DATETIME2 (7)   NULL,
    [TRIP_DATE_APPROX_CODE]           INT             NULL,
    [TRIP_END_DATE]                   DATETIME2 (7)   NULL,
    [TRIP_PAT_ENTERED_FLAG]           NVARCHAR (400)  NULL,
    [TRIP_REGION_ID]                  DECIMAL (18, 4) NULL,
    [_SURROGATEKEY]                   BIGINT          NULL
);


GO

