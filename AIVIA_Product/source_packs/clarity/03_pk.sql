-- clarity-pack-1.2 · Script 3 -> pk.csv (schema,table,column,ordinal)
--
-- CLARITY_TBL_PK (Sunny's find, 2026-09-19, F-CP4): LINE is the
-- key ordinal; PK_COLUMN_ID joins CLARITY_COL.COLUMN_ID for the
-- column name; COLUMN_DESCRIPTOR is the derivable token (unused).
-- The dedupe law applies to the CLARITY_TBL join (see Script 1).
SELECT
    'dbo'           AS [schema],
    TBL.TABLE_NAME  AS [table],
    COL.COLUMN_NAME AS [column],
    PK.LINE         AS [ordinal]
FROM CLARITY_TBL_PK PK
INNER JOIN CLARITY_TBL TBL
        ON TBL.TABLE_ID = PK.TABLE_ID
INNER JOIN CLARITY_COL COL
        ON COL.COLUMN_ID = PK.PK_COLUMN_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
    'PASTE_YOUR_BATCH_TABLES_HERE'
)
ORDER BY TBL.TABLE_NAME, PK.LINE;
