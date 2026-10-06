-- dict_extract_column.sql — THE FULL-DICTIONARY extraction
-- (ruled 2026-10-06: unscoped) — SHAPE-MATCHED (her ruling,
-- same day: the SQL produces the engine's shape; no smart
-- converter). This one query folds in what the home build
-- merged from three extracts:
--   is_primary_key / key_ordinal  <- CLARITY_TBL_PK
--   column_ini / column_item      <- CLARITY_COL_INIITM LINE 1
--     (the standing iniitm ruling: line 1 only becomes the
--      properties; multi-line columns keep line 1 here)
-- Run by the customer's hand; save as dict_extract_column.csv.
-- SELECT aliases ARE the engine's json keys — do not rename.
SELECT
    CAST(COL.COLUMN_ID AS VARCHAR(80)) AS column_id,
    CAST(TBL.TABLE_ID AS VARCHAR(80))  AS table_id,
    TBL.TABLE_NAME                     AS table_name,
    COL.COLUMN_NAME                    AS column_name,
    COL.DATA_TYPE                      AS data_type,
    COL.DESCRIPTION                    AS column_description,
    COL.DEPRECATED_YN                  AS deprecated_yn,
    'CLARITY'                          AS database_name,
    'dbo'                              AS schema_name,
    CASE WHEN PK.PK_COLUMN_ID IS NOT NULL
         THEN 'Y' ELSE 'N' END         AS is_primary_key,
    PK.LINE                            AS key_ordinal,
    INI.COLUMN_INI                     AS column_ini,
    INI.COLUMN_ITEM                    AS column_item
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_COL COL
        ON TBL.TABLE_ID = COL.TABLE_ID
    LEFT JOIN CLARITY.dbo.CLARITY_TBL_PK PK
        ON PK.TABLE_ID = TBL.TABLE_ID
       AND PK.PK_COLUMN_ID = COL.COLUMN_ID
    LEFT JOIN CLARITY.dbo.CLARITY_COL_INIITM INI
        ON INI.COLUMN_ID = COL.COLUMN_ID
       AND INI.LINE = 1
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
ORDER BY TBL.TABLE_NAME, COL.COLUMN_NAME;
