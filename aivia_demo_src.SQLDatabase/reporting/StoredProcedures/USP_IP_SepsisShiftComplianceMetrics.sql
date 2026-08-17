
-- ==== reporting/USP_IP_SepsisShiftComplianceMetrics.sql ====
/************************************************************************************

Author: Developer C 

Create date: 04/24/2023 

Description: Display Detailed information for patients with Severe Sepsis

Report Name: IP Sepsis Screening Compliance

=====================================================================================

Revision Detail

Date			Who					Description

-------------------------------------------------------------------------------------

04/24/2023	Developer C		Developed TKT-006

=====================================================================================

USAGE:

exec [reporting].[USP_IP_SepsisShifComplianceMetrics_PBI]

************************************************************************************/

CREATE PROCEDURE [reporting].[USP_IP_SepsisShiftComplianceMetrics]

AS

BEGIN

SET NOCOUNT ON;

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; 



SELECT [PATENCENCID] [ENC_ID]

	, [ShiftDate] [Shift Date]

	, [ShiftAMPM] [Shift AM/PM]

	, [ODScore] [OD Score]

	, [ScoreTime] [OD Score Time]

	, [AlertNotActivatedReason] [CLINICAL_ALERTS Not Activated Reason]

	, [AlertNotActivatedComment] [CLINICAL_ALERTS Not Activated Comment]

	, [AlertActivatedComment] [CLINICAL_ALERTS Activated Comment]

	, [FY] [FY]

	, [FYMonthNumber] [FY Month #]

	, [FYMonthName] [FY Month]

	, [FYYear] [FY Year]

	, [FYMonthShortName] [FY Month Abrv]

	, [FYDate] [FY Date]

	, [NoteAuthor] [Note Author]

	, [NoteCreatedTime] [Note Created Time]

	, [Denominator]

	, [ShiftCompliance] [Numerator]

	, [FifteenthOrEOM] [15th or EOM]

	, [ShiftComplianceFlag] [Shift Compliance Y/N]

	, [ShiftCompliance] [Shift Compliance]

	, [ShiftColor] [Shift Color]

	, [ShiftColorDisplay] [Shift Color Display]

	, [ShiftCompliance] [Shift Non-Compliance]

	, [PositiveODScore] [Positive OD Score]

	, [UniqueRow] [Unique Row]

	,[RefreshDate]

FROM reporting.[IP_SepsisShiftCompliance]

ORDER BY ENC_ID, ENCOVERALLORDER

END

GO

