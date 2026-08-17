





/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Created From: <Document the name of the previous stored procedure if this is a re-write>

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023		Developer C		Developed TKT-006

07/24/2025		Developer C		Removed restrictionof ODScore >= 2, Stakeholder A wants them all to display TKT-008

=====================================================================================

USAGE:

exec [reporting].[USP_IP_SepsisScreeningAudit_v1]

************************************************************************************/

CREATE       PROCEDURE [reporting].[USP_IP_SepsisScreeningAudit_v1]



AS



SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT 

	[PATENCENCID] [ENC_ID],

	[ScoreDate] [Score Date],

	[ODScore] [OD Score],

	[ScoreTime] [OD Score Time],

	[SepsisPatientHuddleorAlertWithMDPNP] [Sepsis PATIENTS Huddle or CLINICAL_ALERTS With MD/PNP],

	[HuddleDate] [Huddle Date],

	[HuddleTime] [Huddle Time],

	[PatientAssessedByMDPNP] [PATIENTS Assessed by MD/PNP],

	[PhysicianName] [Physician Name],

	[AddOrdersReceivedPlacedByMDPNP] [Additional Orders Received/Placed by MD/PNP],

	[AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason],

	[AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment],

	[AlertActivatedComment] [CLINICAL_ALERTS Activated Comment],

	[Predisposition] [Predisposition?],

	[InfectiousSymptoms] [Infectious Symptoms?],

	[HematologicDysfunction] [Hematologic Dysfunction],

	[RenalDysfunction] [Renal Dysfunction],

	[NeurologicalDysfunction] [Neurological Dysfunction],

	[RespiratoryDysfunction] [Respiratory Dysfunction],

	[CirculatoryDysfunction] [Circulatory Dysfunction],

	[Pulse],

	[Resp],

	[BP],

	[BPGirlsPercentile] [BP Girls Percentile],

	[BPBoysPercentile] [BP Boys Percentile],

	[PerfusionWDL] [Perfusion (WDL)],

	[RBrachialPulse] [R Brachial Pulse],

	[LBrachialPulse] [L Brachial Pulse],

	[RRadialPulse] [R Radial Pulse],

	[LRadialPulse] [L Radial Pulse],

	[RPosteriorTibialPulse] [R Posterior Tibial Pulse],

	[LPosteriorTibialPulse] [L Posterior Tibial Pulse],

	[RPedalPulse] [R Pedal Pulse],

	[LPedalPulse] [L Pedal Pulse],

	[CapillaryRefill] [Capillary Refill],

	[SkinColor] [Skin Color],



	[SkinConditionTemp] [Skin Condition/Temp],

	[ExternalLactateResult] [External Lactate Result],

	[ExternalCreatinine] [External Creatinine],

	[ExternalPlatelets] [External Platelets],

	[Notification],

	[ODScoreIs2] [OD Score 2],

	[PosODScore] [+ OD Score],

	CASE WHEN [ODScoreIs2] = 1 THEN 'Yes' ELSE 'No' END [OD Score = 2?],

	CASE WHEN [PosODScore] = 1 THEN 'Yes' ELSE 'No' END  [+ OD Score?],

	[NoteAuthor] [Note Author],

	[NoteCreatedTime] [Note Created Time],

	[FifteenthOrEOM] [15th or EOM],

	[ShiftColorDisplay] [Shift Color Display],

	[UniqueRow] [Unique Row],

	[RefreshDate] [Refresh Date]

	, CASE WHEN [ODScore] IS NOT NULL THEN 1 ELSE 0 END [Screened]

	FROM [reporting].[IP_SepsisScreeningAudit] 

