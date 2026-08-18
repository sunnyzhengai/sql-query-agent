-- Column patch v2 (PER-PROC alias scoping): corpus-referenced
-- columns missing from the dictionary-derived stubs. Generated
-- by scripts/build_demo_stub_column_patch.py. Idempotent;
-- GO-separated; verification tail expects an EMPTY result.

IF COL_LENGTH('reporting.ip_sepsis', 'ABXYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ABXYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'AddOrdersReceivedPlacedByMDPNP') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [AddOrdersReceivedPlacedByMDPNP] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'AgeMonths') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [AgeMonths] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'AgeYears') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [AgeYears] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'AlertActivatedComment') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [AlertActivatedComment] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'AlertNotActivatedComment') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [AlertNotActivatedComment] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'AlertNotActivatedReason') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [AlertNotActivatedReason] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'AMDenom') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [AMDenom] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'BloodCultureYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [BloodCultureYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'BolusYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [BolusYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'BP') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [BP] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'CapillaryRefill') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [CapillaryRefill] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'CSFYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [CSFYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'CVLYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [CVLYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'CVVHYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [CVVHYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Denominator') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Denominator] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Disposition') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Disposition] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'DobutamineYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [DobutamineYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'DopamineYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [DopamineYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'DvtprophylaxisYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [DvtprophylaxisYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ECMOYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ECMOYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'EDLosHours') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [EDLosHours] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ENCORDER') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ENCORDER] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'EncounterDiagnoses') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [EncounterDiagnoses] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'EncounterWeight') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [EncounterWeight] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ENCOVERALLORDER') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ENCOVERALLORDER] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'EpinephrineYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [EpinephrineYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'EthnicGroup') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [EthnicGroup] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ETTYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ETTYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ExternalCreatinine') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ExternalCreatinine] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ExternalLactateResult') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ExternalLactateResult] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ExternalPlatelets') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ExternalPlatelets] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FifteenthOrEOM') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FifteenthOrEOM] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstABXGivenInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstABXGivenInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstABXName') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstABXName] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstABXTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstABXTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstABXVolume') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstABXVolume] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBloodCultureInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBloodCultureInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBloodCultureOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBloodCultureOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBloodCultureProcedureOrdered') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBloodCultureProcedureOrdered] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBloodCultureResult') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBloodCultureResult] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBolus') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBolus] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBolusGivenInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBolusGivenInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBolusTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBolusTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstBolusVolume') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstBolusVolume] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstCSFInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstCSFInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstCSFOrdered') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstCSFOrdered] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstCSFOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstCSFOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstCVLInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstCVLInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstCVLTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstCVLTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstETTInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstETTInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstHypotensionTakenInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstHypotensionTakenInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstHypotensionTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstHypotensionTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstHypotensionValue') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstHypotensionValue] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstIntubationTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstIntubationTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstLacticAcidOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstLacticAcidOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstLacticAcidResult') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstLacticAcidResult] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstLacticActidInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstLacticActidInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstOrderSetID') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstOrderSetID] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstOrderSetInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstOrderSetInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstOrderSetTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstOrderSetTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstPIVAfterScreen') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstPIVAfterScreen] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstPIVInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstPIVInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstPositiveScoreInED') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstPositiveScoreInED] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstPositiveScoreTimeInED') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstPositiveScoreTimeInED] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstProcalcitoninInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstProcalcitoninInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstProcalcitoninOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstProcalcitoninOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstProcalcitoninResult') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstProcalcitoninResult] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstSVO2InDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstSVO2InDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FirstSVO2Time') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FirstSVO2Time] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FY') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FY] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FYDate') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FYDate] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FYMonthName') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FYMonthName] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FYMonthNumber') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FYMonthNumber] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FYMonthShortName') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FYMonthShortName] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'FYYear') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [FYYear] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'HematologicDysfunction') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [HematologicDysfunction] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'HuddleDate') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [HuddleDate] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'HuddleTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [HuddleTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'InDepartmentTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [InDepartmentTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'InfectiousSymptoms') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [InfectiousSymptoms] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'InpAdmDate') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [InpAdmDate] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'InRecord') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [InRecord] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'IPSOSevereSepsisYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [IPSOSevereSepsisYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LacticAcidYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LacticAcidYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastABXGivenInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastABXGivenInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastABXName') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastABXName] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastABXTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastABXTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastABXToODScoreTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastABXToODScoreTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastABXToODScoreVolume') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastABXToODScoreVolume] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBloodCultureInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBloodCultureInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBloodCultureOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBloodCultureOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBloodCultureProcedureOrdered') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBloodCultureProcedureOrdered] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBloodCultureResult') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBloodCultureResult] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBolus') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBolus] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBolusGivenInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBolusGivenInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBolusTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBolusTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBolusToScreenTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBolusToScreenTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastBolusVolume') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastBolusVolume] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastCSFInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastCSFInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastCSFOrdered') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastCSFOrdered] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastCSFOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastCSFOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastCVLInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastCVLInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastCVLTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastCVLTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastETTInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastETTInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastHypotensionTakenInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastHypotensionTakenInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastHypotensionTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastHypotensionTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastHypotensionValue') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastHypotensionValue] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastIntubationTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastIntubationTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastLacticAcidInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastLacticAcidInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastLacticAcidOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastLacticAcidOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastLacticAcidResult') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastLacticAcidResult] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastOrderSetID') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastOrderSetID] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastOrderSetInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastOrderSetInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastOrderSetTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastOrderSetTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastPIVBeforeScreen') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastPIVBeforeScreen] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastPIVInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastPIVInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastProcalcitoninInDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastProcalcitoninInDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastProcalcitoninOrderTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastProcalcitoninOrderTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastProcalcitoninResult') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastProcalcitoninResult] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastSVO2InDeptYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastSVO2InDeptYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LastSVO2Time') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LastSVO2Time] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LBrachialPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LBrachialPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Location') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Location] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LosHours') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LosHours] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LPedalPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LPedalPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LPosteriorTibialPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LPosteriorTibialPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'LRadialPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [LRadialPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'MilrinoneYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [MilrinoneYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'NeurologicalDysfunction') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [NeurologicalDysfunction] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'NorepinephrineYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [NorepinephrineYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'NoteAuthor') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [NoteAuthor] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'NoteCreatedTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [NoteCreatedTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Notification') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Notification] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ODScoreToFirstABXTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ODScoreToFirstABXTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'OutDepartmentTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [OutDepartmentTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'OutRecord') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [OutRecord] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'OXYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [OXYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PATENCENCID') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PATENCENCID] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PatientAssessedByMDPNP') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PatientAssessedByMDPNP] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PerfusionWDL') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PerfusionWDL] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PhysicianName') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PhysicianName] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PIVYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PIVYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PMDenom') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PMDenom] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PositiveODScore') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PositiveODScore] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Predisposition') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Predisposition] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'PressorYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [PressorYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ProcalcitoninYN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ProcalcitoninYN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Pulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Pulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Race') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Race] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'RBrachialPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [RBrachialPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'RenalDysfunction') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [RenalDysfunction] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'Resp') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [Resp] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'RespiratoryDysfunction') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [RespiratoryDysfunction] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'RPedalPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [RPedalPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'RPosteriorTibialPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [RPosteriorTibialPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'RRadialPulse') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [RRadialPulse] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ScoreTime') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ScoreTime] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ScreenTimeToFirstBolus') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ScreenTimeToFirstBolus] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'SepsisPatientHuddleorAlertWithMDPNP') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [SepsisPatientHuddleorAlertWithMDPNP] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftAMPM') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftAMPM] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftCNs') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftCNs] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftColor') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftColor] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftColorDisplay') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftColorDisplay] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftCompliance') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftCompliance] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftDate') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftDate] DATETIME2 NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftEnd') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftEnd] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftRNs') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftRNs] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'ShiftStart') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [ShiftStart] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'SkinColor') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [SkinColor] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'SkinConditionTemp') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [SkinConditionTemp] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'SVO2YN') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [SVO2YN] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'UniqueRow') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [UniqueRow] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reporting.ip_sepsis', 'UnitOrder') IS NULL
ALTER TABLE [reporting].[ip_sepsis] ADD [UnitOrder] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.config_value_set', 'VALUE_SET_ABBR') IS NULL
ALTER TABLE [reports].[config_value_set] ADD [VALUE_SET_ABBR] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.config_value_set', 'VALUE_SET_DISPLAY') IS NULL
ALTER TABLE [reports].[config_value_set] ADD [VALUE_SET_DISPLAY] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.fy_date_dimension', 'HS_FY') IS NULL
ALTER TABLE [reports].[fy_date_dimension] ADD [HS_FY] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.fy_date_dimension', 'HS_FY_MONTH_NUMBER') IS NULL
ALTER TABLE [reports].[fy_date_dimension] ADD [HS_FY_MONTH_NUMBER] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.fy_date_dimension', 'YEAR') IS NULL
ALTER TABLE [reports].[fy_date_dimension] ADD [YEAR] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.non_severe_sepsis_staging', 'AntibioticAdministeredTime_V60') IS NULL
ALTER TABLE [reports].[non_severe_sepsis_staging] ADD [AntibioticAdministeredTime_V60] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.non_severe_sepsis_staging', 'AntibioticOrderedTime_V59') IS NULL
ALTER TABLE [reports].[non_severe_sepsis_staging] ADD [AntibioticOrderedTime_V59] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.non_severe_sepsis_staging', 'BloodCultureOrderedTime_V61') IS NULL
ALTER TABLE [reports].[non_severe_sepsis_staging] ADD [BloodCultureOrderedTime_V61] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.non_severe_sepsis_staging', 'DATE_STAMP') IS NULL
ALTER TABLE [reports].[non_severe_sepsis_staging] ADD [DATE_STAMP] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.non_severe_sepsis_staging', 'ENCOUNTER_ID') IS NULL
ALTER TABLE [reports].[non_severe_sepsis_staging] ADD [ENCOUNTER_ID] DECIMAL(18,4) NULL;
GO

IF COL_LENGTH('reports.non_severe_sepsis_staging', 'Reviewed') IS NULL
ALTER TABLE [reports].[non_severe_sepsis_staging] ADD [Reviewed] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.non_severe_sepsis_staging', 'Sepsis_Episode_ID_V01') IS NULL
ALTER TABLE [reports].[non_severe_sepsis_staging] ADD [Sepsis_Episode_ID_V01] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ABXDays_V42') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ABXDays_V42] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Arrival_Time_V10') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Arrival_Time_V10] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'BCPositive_V35') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [BCPositive_V35] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'bill') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [bill] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Birth_Date_V02') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Birth_Date_V02] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Bolus1Time_V20') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Bolus1Time_V20] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Bolus1Volume_V21') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Bolus1Volume_V21] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Bolus2Time_V22') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Bolus2Time_V22] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Bolus2Volume_V23') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Bolus2Volume_V23] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Bolus3Time_V24') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Bolus3Time_V24] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Bolus3Volume_V25') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Bolus3Volume_V25] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Clinically_Derived_Time_Zero_V09') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Clinically_Derived_Time_Zero_V09] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'CVLPlacementTime_V44') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [CVLPlacementTime_V44] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'DATE_STAMP') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [DATE_STAMP] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Disposition_V54') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Disposition_V54] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'DispositionDate_V53') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [DispositionDate_V53] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ECMO_V48') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ECMO_V48] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ED2GenCareTime_V12') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ED2GenCareTime_V12] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ED2HemoncTime_V63') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ED2HemoncTime_V63] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ED2ICUTime_V13') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ED2ICUTime_V13] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ENCOUNTER_ID') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ENCOUNTER_ID] DECIMAL(18,4) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'FirstABXTime_V26') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [FirstABXTime_V26] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'FirstPressorTime_V29') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [FirstPressorTime_V29] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'FirstPressorType_V30') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [FirstPressorType_V30] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'FirstTimeHypotension_V18') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [FirstTimeHypotension_V18] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'FunctionaLTimeZero_V68') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [FunctionaLTimeZero_V68] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'GENCARE2ICUTime_V94') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [GENCARE2ICUTime_V94] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HEMONC2ICUTime_V64') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HEMONC2ICUTime_V64] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_1_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_1_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_2_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_2_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_3_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_3_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_4_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_4_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_6_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_6_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_7_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_7_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_88_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_88_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_95_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_95_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'HighRiskConditions_98_V65') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [HighRiskConditions_98_V65] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Huddle_Time_V07') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Huddle_Time_V07] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ICUDays_V58') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ICUDays_V58] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'LacticAcidTime_V46') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [LacticAcidTime_V46] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'LacticAcidValue_V47') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [LacticAcidValue_V47] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'NACHRI_hosp') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [NACHRI_hosp] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'OrderSet_Time_V08') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [OrderSet_Time_V08] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'OrganDysfunction_V41') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [OrganDysfunction_V41] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'OutsideHospital_V11') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [OutsideHospital_V11] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Pressor_Days_V57') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Pressor_Days_V57] DECIMAL(18,4) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'PressureVentDays_V56') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [PressureVentDays_V56] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Pt_Chronically_Vented_V32') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Pt_Chronically_Vented_V32] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Reviewed') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Reviewed] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Risk_Score_Method_V51') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Risk_Score_Method_V51] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Risk_Score_V52') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Risk_Score_V52] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'ScreenTime_V06') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [ScreenTime_V06] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Sepsis_Episode_ID_V01') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Sepsis_Episode_ID_V01] NVARCHAR(400) NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'SVO2Time_V45') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [SVO2Time_V45] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'TimeSurgicalSourceControl_V39') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [TimeSurgicalSourceControl_V39] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'TimeZeroLoc_V66') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [TimeZeroLoc_V66] DATETIME2 NULL;
GO

IF COL_LENGTH('reports.severe_sepsis_staging', 'Weight_V16') IS NULL
ALTER TABLE [reports].[severe_sepsis_staging] ADD [Weight_V16] NVARCHAR(400) NULL;
GO

-- VERIFICATION: expect an EMPTY result.
SELECT v.tbl AS table_name, v.col AS missing_column FROM (VALUES
    ('reporting.ip_sepsis', 'ABXYN'),
    ('reporting.ip_sepsis', 'AddOrdersReceivedPlacedByMDPNP'),
    ('reporting.ip_sepsis', 'AgeMonths'),
    ('reporting.ip_sepsis', 'AgeYears'),
    ('reporting.ip_sepsis', 'AlertActivatedComment'),
    ('reporting.ip_sepsis', 'AlertNotActivatedComment'),
    ('reporting.ip_sepsis', 'AlertNotActivatedReason'),
    ('reporting.ip_sepsis', 'AMDenom'),
    ('reporting.ip_sepsis', 'BloodCultureYN'),
    ('reporting.ip_sepsis', 'BolusYN'),
    ('reporting.ip_sepsis', 'BP'),
    ('reporting.ip_sepsis', 'CapillaryRefill'),
    ('reporting.ip_sepsis', 'CSFYN'),
    ('reporting.ip_sepsis', 'CVLYN'),
    ('reporting.ip_sepsis', 'CVVHYN'),
    ('reporting.ip_sepsis', 'Denominator'),
    ('reporting.ip_sepsis', 'Disposition'),
    ('reporting.ip_sepsis', 'DobutamineYN'),
    ('reporting.ip_sepsis', 'DopamineYN'),
    ('reporting.ip_sepsis', 'DvtprophylaxisYN'),
    ('reporting.ip_sepsis', 'ECMOYN'),
    ('reporting.ip_sepsis', 'EDLosHours'),
    ('reporting.ip_sepsis', 'ENCORDER'),
    ('reporting.ip_sepsis', 'EncounterDiagnoses'),
    ('reporting.ip_sepsis', 'EncounterWeight'),
    ('reporting.ip_sepsis', 'ENCOVERALLORDER'),
    ('reporting.ip_sepsis', 'EpinephrineYN'),
    ('reporting.ip_sepsis', 'EthnicGroup'),
    ('reporting.ip_sepsis', 'ETTYN'),
    ('reporting.ip_sepsis', 'ExternalCreatinine'),
    ('reporting.ip_sepsis', 'ExternalLactateResult'),
    ('reporting.ip_sepsis', 'ExternalPlatelets'),
    ('reporting.ip_sepsis', 'FifteenthOrEOM'),
    ('reporting.ip_sepsis', 'FirstABXGivenInDeptYN'),
    ('reporting.ip_sepsis', 'FirstABXName'),
    ('reporting.ip_sepsis', 'FirstABXTime'),
    ('reporting.ip_sepsis', 'FirstABXVolume'),
    ('reporting.ip_sepsis', 'FirstBloodCultureInDeptYN'),
    ('reporting.ip_sepsis', 'FirstBloodCultureOrderTime'),
    ('reporting.ip_sepsis', 'FirstBloodCultureProcedureOrdered'),
    ('reporting.ip_sepsis', 'FirstBloodCultureResult'),
    ('reporting.ip_sepsis', 'FirstBolus'),
    ('reporting.ip_sepsis', 'FirstBolusGivenInDeptYN'),
    ('reporting.ip_sepsis', 'FirstBolusTime'),
    ('reporting.ip_sepsis', 'FirstBolusVolume'),
    ('reporting.ip_sepsis', 'FirstCSFInDeptYN'),
    ('reporting.ip_sepsis', 'FirstCSFOrdered'),
    ('reporting.ip_sepsis', 'FirstCSFOrderTime'),
    ('reporting.ip_sepsis', 'FirstCVLInDeptYN'),
    ('reporting.ip_sepsis', 'FirstCVLTime'),
    ('reporting.ip_sepsis', 'FirstETTInDeptYN'),
    ('reporting.ip_sepsis', 'FirstHypotensionTakenInDeptYN'),
    ('reporting.ip_sepsis', 'FirstHypotensionTime'),
    ('reporting.ip_sepsis', 'FirstHypotensionValue'),
    ('reporting.ip_sepsis', 'FirstIntubationTime'),
    ('reporting.ip_sepsis', 'FirstLacticAcidOrderTime'),
    ('reporting.ip_sepsis', 'FirstLacticAcidResult'),
    ('reporting.ip_sepsis', 'FirstLacticActidInDeptYN'),
    ('reporting.ip_sepsis', 'FirstOrderSetID'),
    ('reporting.ip_sepsis', 'FirstOrderSetInDeptYN'),
    ('reporting.ip_sepsis', 'FirstOrderSetTime'),
    ('reporting.ip_sepsis', 'FirstPIVAfterScreen'),
    ('reporting.ip_sepsis', 'FirstPIVInDeptYN'),
    ('reporting.ip_sepsis', 'FirstPositiveScoreInED'),
    ('reporting.ip_sepsis', 'FirstPositiveScoreTimeInED'),
    ('reporting.ip_sepsis', 'FirstProcalcitoninInDeptYN'),
    ('reporting.ip_sepsis', 'FirstProcalcitoninOrderTime'),
    ('reporting.ip_sepsis', 'FirstProcalcitoninResult'),
    ('reporting.ip_sepsis', 'FirstSVO2InDeptYN'),
    ('reporting.ip_sepsis', 'FirstSVO2Time'),
    ('reporting.ip_sepsis', 'FY'),
    ('reporting.ip_sepsis', 'FYDate'),
    ('reporting.ip_sepsis', 'FYMonthName'),
    ('reporting.ip_sepsis', 'FYMonthNumber'),
    ('reporting.ip_sepsis', 'FYMonthShortName'),
    ('reporting.ip_sepsis', 'FYYear'),
    ('reporting.ip_sepsis', 'HematologicDysfunction'),
    ('reporting.ip_sepsis', 'HuddleDate'),
    ('reporting.ip_sepsis', 'HuddleTime'),
    ('reporting.ip_sepsis', 'InDepartmentTime'),
    ('reporting.ip_sepsis', 'InfectiousSymptoms'),
    ('reporting.ip_sepsis', 'InpAdmDate'),
    ('reporting.ip_sepsis', 'InRecord'),
    ('reporting.ip_sepsis', 'IPSOSevereSepsisYN'),
    ('reporting.ip_sepsis', 'LacticAcidYN'),
    ('reporting.ip_sepsis', 'LastABXGivenInDeptYN'),
    ('reporting.ip_sepsis', 'LastABXName'),
    ('reporting.ip_sepsis', 'LastABXTime'),
    ('reporting.ip_sepsis', 'LastABXToODScoreTime'),
    ('reporting.ip_sepsis', 'LastABXToODScoreVolume'),
    ('reporting.ip_sepsis', 'LastBloodCultureInDeptYN'),
    ('reporting.ip_sepsis', 'LastBloodCultureOrderTime'),
    ('reporting.ip_sepsis', 'LastBloodCultureProcedureOrdered'),
    ('reporting.ip_sepsis', 'LastBloodCultureResult'),
    ('reporting.ip_sepsis', 'LastBolus'),
    ('reporting.ip_sepsis', 'LastBolusGivenInDeptYN'),
    ('reporting.ip_sepsis', 'LastBolusTime'),
    ('reporting.ip_sepsis', 'LastBolusToScreenTime'),
    ('reporting.ip_sepsis', 'LastBolusVolume'),
    ('reporting.ip_sepsis', 'LastCSFInDeptYN'),
    ('reporting.ip_sepsis', 'LastCSFOrdered'),
    ('reporting.ip_sepsis', 'LastCSFOrderTime'),
    ('reporting.ip_sepsis', 'LastCVLInDeptYN'),
    ('reporting.ip_sepsis', 'LastCVLTime'),
    ('reporting.ip_sepsis', 'LastETTInDeptYN'),
    ('reporting.ip_sepsis', 'LastHypotensionTakenInDeptYN'),
    ('reporting.ip_sepsis', 'LastHypotensionTime'),
    ('reporting.ip_sepsis', 'LastHypotensionValue'),
    ('reporting.ip_sepsis', 'LastIntubationTime'),
    ('reporting.ip_sepsis', 'LastLacticAcidInDeptYN'),
    ('reporting.ip_sepsis', 'LastLacticAcidOrderTime'),
    ('reporting.ip_sepsis', 'LastLacticAcidResult'),
    ('reporting.ip_sepsis', 'LastOrderSetID'),
    ('reporting.ip_sepsis', 'LastOrderSetInDeptYN'),
    ('reporting.ip_sepsis', 'LastOrderSetTime'),
    ('reporting.ip_sepsis', 'LastPIVBeforeScreen'),
    ('reporting.ip_sepsis', 'LastPIVInDeptYN'),
    ('reporting.ip_sepsis', 'LastProcalcitoninInDeptYN'),
    ('reporting.ip_sepsis', 'LastProcalcitoninOrderTime'),
    ('reporting.ip_sepsis', 'LastProcalcitoninResult'),
    ('reporting.ip_sepsis', 'LastSVO2InDeptYN'),
    ('reporting.ip_sepsis', 'LastSVO2Time'),
    ('reporting.ip_sepsis', 'LBrachialPulse'),
    ('reporting.ip_sepsis', 'Location'),
    ('reporting.ip_sepsis', 'LosHours'),
    ('reporting.ip_sepsis', 'LPedalPulse'),
    ('reporting.ip_sepsis', 'LPosteriorTibialPulse'),
    ('reporting.ip_sepsis', 'LRadialPulse'),
    ('reporting.ip_sepsis', 'MilrinoneYN'),
    ('reporting.ip_sepsis', 'NeurologicalDysfunction'),
    ('reporting.ip_sepsis', 'NorepinephrineYN'),
    ('reporting.ip_sepsis', 'NoteAuthor'),
    ('reporting.ip_sepsis', 'NoteCreatedTime'),
    ('reporting.ip_sepsis', 'Notification'),
    ('reporting.ip_sepsis', 'ODScoreToFirstABXTime'),
    ('reporting.ip_sepsis', 'OutDepartmentTime'),
    ('reporting.ip_sepsis', 'OutRecord'),
    ('reporting.ip_sepsis', 'OXYN'),
    ('reporting.ip_sepsis', 'PATENCENCID'),
    ('reporting.ip_sepsis', 'PatientAssessedByMDPNP'),
    ('reporting.ip_sepsis', 'PerfusionWDL'),
    ('reporting.ip_sepsis', 'PhysicianName'),
    ('reporting.ip_sepsis', 'PIVYN'),
    ('reporting.ip_sepsis', 'PMDenom'),
    ('reporting.ip_sepsis', 'PositiveODScore'),
    ('reporting.ip_sepsis', 'Predisposition'),
    ('reporting.ip_sepsis', 'PressorYN'),
    ('reporting.ip_sepsis', 'ProcalcitoninYN'),
    ('reporting.ip_sepsis', 'Pulse'),
    ('reporting.ip_sepsis', 'Race'),
    ('reporting.ip_sepsis', 'RBrachialPulse'),
    ('reporting.ip_sepsis', 'RenalDysfunction'),
    ('reporting.ip_sepsis', 'Resp'),
    ('reporting.ip_sepsis', 'RespiratoryDysfunction'),
    ('reporting.ip_sepsis', 'RPedalPulse'),
    ('reporting.ip_sepsis', 'RPosteriorTibialPulse'),
    ('reporting.ip_sepsis', 'RRadialPulse'),
    ('reporting.ip_sepsis', 'ScoreTime'),
    ('reporting.ip_sepsis', 'ScreenTimeToFirstBolus'),
    ('reporting.ip_sepsis', 'SepsisPatientHuddleorAlertWithMDPNP'),
    ('reporting.ip_sepsis', 'ShiftAMPM'),
    ('reporting.ip_sepsis', 'ShiftCNs'),
    ('reporting.ip_sepsis', 'ShiftColor'),
    ('reporting.ip_sepsis', 'ShiftColorDisplay'),
    ('reporting.ip_sepsis', 'ShiftCompliance'),
    ('reporting.ip_sepsis', 'ShiftDate'),
    ('reporting.ip_sepsis', 'ShiftEnd'),
    ('reporting.ip_sepsis', 'ShiftRNs'),
    ('reporting.ip_sepsis', 'ShiftStart'),
    ('reporting.ip_sepsis', 'SkinColor'),
    ('reporting.ip_sepsis', 'SkinConditionTemp'),
    ('reporting.ip_sepsis', 'SVO2YN'),
    ('reporting.ip_sepsis', 'UniqueRow'),
    ('reporting.ip_sepsis', 'UnitOrder'),
    ('reports.config_value_set', 'VALUE_SET_ABBR'),
    ('reports.config_value_set', 'VALUE_SET_DISPLAY'),
    ('reports.fy_date_dimension', 'HS_FY'),
    ('reports.fy_date_dimension', 'HS_FY_MONTH_NUMBER'),
    ('reports.fy_date_dimension', 'YEAR'),
    ('reports.non_severe_sepsis_staging', 'AntibioticAdministeredTime_V60'),
    ('reports.non_severe_sepsis_staging', 'AntibioticOrderedTime_V59'),
    ('reports.non_severe_sepsis_staging', 'BloodCultureOrderedTime_V61'),
    ('reports.non_severe_sepsis_staging', 'DATE_STAMP'),
    ('reports.non_severe_sepsis_staging', 'ENCOUNTER_ID'),
    ('reports.non_severe_sepsis_staging', 'Reviewed'),
    ('reports.non_severe_sepsis_staging', 'Sepsis_Episode_ID_V01'),
    ('reports.severe_sepsis_staging', 'ABXDays_V42'),
    ('reports.severe_sepsis_staging', 'Arrival_Time_V10'),
    ('reports.severe_sepsis_staging', 'BCPositive_V35'),
    ('reports.severe_sepsis_staging', 'bill'),
    ('reports.severe_sepsis_staging', 'Birth_Date_V02'),
    ('reports.severe_sepsis_staging', 'Bolus1Time_V20'),
    ('reports.severe_sepsis_staging', 'Bolus1Volume_V21'),
    ('reports.severe_sepsis_staging', 'Bolus2Time_V22'),
    ('reports.severe_sepsis_staging', 'Bolus2Volume_V23'),
    ('reports.severe_sepsis_staging', 'Bolus3Time_V24'),
    ('reports.severe_sepsis_staging', 'Bolus3Volume_V25'),
    ('reports.severe_sepsis_staging', 'Clinically_Derived_Time_Zero_V09'),
    ('reports.severe_sepsis_staging', 'CVLPlacementTime_V44'),
    ('reports.severe_sepsis_staging', 'DATE_STAMP'),
    ('reports.severe_sepsis_staging', 'Disposition_V54'),
    ('reports.severe_sepsis_staging', 'DispositionDate_V53'),
    ('reports.severe_sepsis_staging', 'ECMO_V48'),
    ('reports.severe_sepsis_staging', 'ED2GenCareTime_V12'),
    ('reports.severe_sepsis_staging', 'ED2HemoncTime_V63'),
    ('reports.severe_sepsis_staging', 'ED2ICUTime_V13'),
    ('reports.severe_sepsis_staging', 'ENCOUNTER_ID'),
    ('reports.severe_sepsis_staging', 'FirstABXTime_V26'),
    ('reports.severe_sepsis_staging', 'FirstPressorTime_V29'),
    ('reports.severe_sepsis_staging', 'FirstPressorType_V30'),
    ('reports.severe_sepsis_staging', 'FirstTimeHypotension_V18'),
    ('reports.severe_sepsis_staging', 'FunctionaLTimeZero_V68'),
    ('reports.severe_sepsis_staging', 'GENCARE2ICUTime_V94'),
    ('reports.severe_sepsis_staging', 'HEMONC2ICUTime_V64'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_1_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_2_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_3_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_4_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_6_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_7_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_88_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_95_V65'),
    ('reports.severe_sepsis_staging', 'HighRiskConditions_98_V65'),
    ('reports.severe_sepsis_staging', 'Huddle_Time_V07'),
    ('reports.severe_sepsis_staging', 'ICUDays_V58'),
    ('reports.severe_sepsis_staging', 'LacticAcidTime_V46'),
    ('reports.severe_sepsis_staging', 'LacticAcidValue_V47'),
    ('reports.severe_sepsis_staging', 'NACHRI_hosp'),
    ('reports.severe_sepsis_staging', 'OrderSet_Time_V08'),
    ('reports.severe_sepsis_staging', 'OrganDysfunction_V41'),
    ('reports.severe_sepsis_staging', 'OutsideHospital_V11'),
    ('reports.severe_sepsis_staging', 'Pressor_Days_V57'),
    ('reports.severe_sepsis_staging', 'PressureVentDays_V56'),
    ('reports.severe_sepsis_staging', 'Pt_Chronically_Vented_V32'),
    ('reports.severe_sepsis_staging', 'Reviewed'),
    ('reports.severe_sepsis_staging', 'Risk_Score_Method_V51'),
    ('reports.severe_sepsis_staging', 'Risk_Score_V52'),
    ('reports.severe_sepsis_staging', 'ScreenTime_V06'),
    ('reports.severe_sepsis_staging', 'Sepsis_Episode_ID_V01'),
    ('reports.severe_sepsis_staging', 'SVO2Time_V45'),
    ('reports.severe_sepsis_staging', 'TimeSurgicalSourceControl_V39'),
    ('reports.severe_sepsis_staging', 'TimeZeroLoc_V66'),
    ('reports.severe_sepsis_staging', 'Weight_V16')
) v(tbl, col) WHERE COL_LENGTH(v.tbl, v.col) IS NULL;
GO
