CREATE TABLE [reporting].[ip_sepsisencounters] (
    [ADTArrivalTime]    DATETIME2 (7)   NULL,
    [ADTDepartmentID]   NVARCHAR (400)  NULL,
    [ADTDepartmentName] NVARCHAR (400)  NULL,
    [AgeMonths]         NVARCHAR (400)  NULL,
    [AgeYears]          NVARCHAR (400)  NULL,
    [AllEncDx]          NVARCHAR (400)  NULL,
    [AllEncReasons]     NVARCHAR (400)  NULL,
    [BirthDate]         DATETIME2 (7)   NULL,
    [Disposition]       NVARCHAR (400)  NULL,
    [EDDepartureTime]   DATETIME2 (7)   NULL,
    [ENCOUNTER_ID]      DECIMAL (18, 4) NULL,
    [EthnicGroup]       NVARCHAR (400)  NULL,
    [HospAdmsnTime]     DATETIME2 (7)   NULL,
    [HospDischTime]     DATETIME2 (7)   NULL,
    [INPATIENT_DATA_ID] DECIMAL (18, 4) NULL,
    [InDepartmentTime]  DATETIME2 (7)   NULL,
    [InpAdmDate]        DATETIME2 (7)   NULL,
    [InpatientDataID]   NVARCHAR (400)  NULL,
    [Location]          NVARCHAR (400)  NULL,
    [LosHours]          NVARCHAR (400)  NULL,
    [OutDepartmentTime] DATETIME2 (7)   NULL,
    [PATENCENCID]       NVARCHAR (400)  NULL,
    [PATIENTMRN]        NVARCHAR (400)  NULL,
    [PatientID]         NVARCHAR (400)  NULL,
    [PatientName]       NVARCHAR (400)  NULL,
    [Race]              NVARCHAR (400)  NULL,
    [RefreshDate]       DATETIME2 (7)   NULL,
    [UniqueRow]         NVARCHAR (400)  NULL
);


GO

