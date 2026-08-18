CREATE TABLE [reports].[NON_SEVERE_SEPSIS_STAGING] (
    [EncounterID]                    DECIMAL (18, 4) NULL,
    [PatientID]                      NVARCHAR (400)  NULL,
    [SepsisDate]                     DATE            NULL,
    [AntibioticAdministeredTime_V60] DATETIME2 (7)   NULL,
    [AntibioticOrderedTime_V59]      DATETIME2 (7)   NULL,
    [BloodCultureOrderedTime_V61]    DATETIME2 (7)   NULL,
    [DATE_STAMP]                     DATETIME2 (7)   NULL,
    [ENCOUNTER_ID]                   DECIMAL (18, 4) NULL,
    [Reviewed]                       NVARCHAR (400)  NULL,
    [Sepsis_Episode_ID_V01]          NVARCHAR (400)  NULL
);


GO

