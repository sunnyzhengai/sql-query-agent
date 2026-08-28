CREATE PROCEDURE reporting.USP_Diabetic_Patients_Lab
AS
BEGIN
WITH
Base_Cohort AS (
  SELECT LR.PATIENT_ID, LR.RESULT_DATE
  FROM LAB_RESULTS LR
  WHERE LR.HBA1C_VALUE >= 6.5
),
    enc_recent as (
    select mo.patient_id, mo.order_date
    from medication_orders mo
    where mo.med_name in ('metformin', 'insulin glargine')
    ),
Lab_Draws AS (
  SELECT LR.PATIENT_ID, LR.RESULT_DATE
  FROM LAB_RESULTS LR
  WHERE LR.HBA1C_VALUE >= 6.5
),
A1c_High AS (
  SELECT LR.PATIENT_ID, LR.RESULT_DATE
  FROM LAB_RESULTS LR
  WHERE 6.5 <= LR.HBA1C_VALUE
),
Rx_Current AS (
  SELECT MO.PATIENT_ID, MO.ORDER_DATE
  FROM MEDICATION_ORDERS MO
  WHERE MO.MED_NAME IN ('METFORMIN', 'INSULIN GLARGINE')
)
SELECT * FROM Base_Cohort;
END

GO

