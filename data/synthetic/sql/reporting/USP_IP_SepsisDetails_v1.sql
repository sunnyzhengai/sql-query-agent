



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

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reportingDB].[reporting].[USP_IP_SepsisDetails_v1]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisDetails_v1]

AS 

BEGIN

	

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT

	sd.[PatEncCSNID] [CSN]

	, sd.[SepsisDate] [Sepsis Date]

	, sd.[HypotensionTime] [Hyptension Time]

	, sd.[HypotensionValue] [Hypotension Value]

	, sd.[BPPercentile] [BP Percentile]

	, sd.[EncounterWeight] [Weight]

	, sd.[FirstPositiveScoreInED] [First Positive Score in ED]

	, sd.[FirstPositiveScoreTimeInED] [First Positive Score Time in ED]

	, sd.[EDLosHours] [ED LOS Hours]

	, sd.[PositiveODScore] [Positive OD Score in Department]

	, sd.[ABXVolume] [ABX Volume]

 	, sd.[ABXTime] [ABX Time]

	, sd.[ABXName] [ABX Name]

	, sd.[Bolus] [Bolus]

	, sd.[BolusVolume] [Bolus Volume]

	, sd.[BolusTime] [Bolus Time]

	, sd.[LacticAcidOrderTime] [Lactic Acid Order Time]

	, sd.[LacticAcidResult] [Lactic Acid Result]

	, sd.[OrderSetTime] [Order Set Time]

	, sd.[OrderSetID] [Order Set ID]

	, sd.[ProcalcitoninOrderTime] [Procalcitonin Order Time]

	, sd.[ProcalcitoninResult] [Procalcitonin Result]

	, sd.[BloodCultureOrderTime] [Blood Culture Order Time]

	, sd.[BloodCultureProcedureOrdered] [Blood Culture Procedure Ordered]

	, sd.[BloodCultureResult] [Blood Culture Result]

	, sd.[CSFOrderTime] [CSF Order Time]

	, sd.[CSFOrdered] [CSF Ordered]

	, sd.[CSFValue] [CSF Value]

	, sd.[PIVPlacementTime] [PIV Placement Time]

	, sd.[IntubationTime] [Intubation Time]

	, sd.[DobutamineYN] [Dobutamine Y/N]

	, sd.[DopamineYN] [Dopamine Y/N]

	, sd.[EpinephrineYN] [Epinephrine Y/N]

	, sd.[MilrinoneYN] [Milrinone Y/N]

	, sd.[NorepinephrineYN] [Norepinephrine Y/N]

	, sd.[PressorYN] [Pressor Y/N]

	, sd.[CVVHYN] [CVVH Y/N]

	, sd.[OXYN] [OX Y/N]

	, sd.[ECMOYN] [ECMO Y/N]

	, sd.[IPSOSevereSepsisYN] [IPSO Severe Sepsis Y/N]

	, sd.[CSNOverallOrder] [CSN Overall Order]

	, sd.[RefreshDate] [Refresh Date]

	FROM [reportingDB].[reporting].[IP_SepsisDetails] sd

	ORDER BY sd.PatEncCSNID, sd.CSNOverallOrder

END 

