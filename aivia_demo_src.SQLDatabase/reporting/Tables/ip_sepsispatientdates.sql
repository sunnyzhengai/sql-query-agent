CREATE TABLE [reporting].[ip_sepsispatientdates] (
    [ADTDepartmentID]   NVARCHAR (400) NULL,
    [ADTDepartmentName] NVARCHAR (400) NULL,
    [AgeOnDateMonths]   DATETIME2 (7)  NULL,
    [AgeOnDateYears]    DATETIME2 (7)  NULL,
    [DepartmentRollup]  NVARCHAR (400) NULL,
    [ENCORDER]          NVARCHAR (400) NULL,
    [ENCOVERALLORDER]   NVARCHAR (400) NULL,
    [InDepartmentTime]  DATETIME2 (7)  NULL,
    [InpatientDataID]   NVARCHAR (400) NULL,
    [OutDepartmentTime] DATETIME2 (7)  NULL,
    [PATENCENCID]       NVARCHAR (400) NULL,
    [PatientID]         NVARCHAR (400) NULL,
    [RefreshDate]       DATETIME2 (7)  NULL,
    [SepsisPatientDate] DATETIME2 (7)  NULL,
    [UniqueRow]         NVARCHAR (400) NULL,
    [UnitOrder]         NVARCHAR (400) NULL
);


GO

