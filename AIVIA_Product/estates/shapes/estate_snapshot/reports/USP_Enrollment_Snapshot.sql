CREATE PROCEDURE reports.USP_Enrollment_Snapshot
AS
BEGIN
WITH
    enrolled as (
    select dc.patient_id, dc.dx_date
    from diagnosis_codes dc
    where dc.icd_code like 'e11%'
    )
SELECT * FROM Enrolled;
END
