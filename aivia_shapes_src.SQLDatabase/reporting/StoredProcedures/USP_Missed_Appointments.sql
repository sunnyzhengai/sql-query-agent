CREATE PROCEDURE reporting.USP_Missed_Appointments
AS
BEGIN
WITH
Sched_Misses AS (
  SELECT A.PATIENT_ID, A.APPT_ID
  FROM APPOINTMENTS A
  WHERE A.APPT_STATUS IN ('cancelled', 'no-show')
)
SELECT * FROM Sched_Misses;
END

GO

