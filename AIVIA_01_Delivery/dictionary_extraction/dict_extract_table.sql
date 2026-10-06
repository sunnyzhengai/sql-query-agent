-- dict_extract_table.sql — THE FULL-DICTIONARY extraction
-- (ruled 2026-10-06: unscoped; the per-corpus table list is
-- retired for delivery). Run by the customer's hand against
-- their Clarity. Save the FULL result as
-- dict_extract_table.csv, then run tools/csv_to_json.py.
-- The TBL_DESCRIPTOR_OVR filter is the standing de-dup ruling
-- (2 rows per table without it).
-- SELECT aliases ARE the engine's json keys — do not rename.
-- One edit point: the database name below if theirs differs.
SELECT
    CAST(TBL.TABLE_ID AS VARCHAR(80)) AS table_id,
    TBL.TABLE_NAME                    AS table_name,
    TBL.TABLE_INTRODUCTION            AS table_description,
    TBL.DEPRECATED_YN                 AS deprecated_yn,
    'CLARITY'                         AS database_name,
    'dbo'                             AS schema_name
FROM CLARITY.dbo.CLARITY_TBL TBL
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
ORDER BY TBL.TABLE_NAME;
