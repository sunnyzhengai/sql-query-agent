-- clarity-pack-1.2 · Script 2 -> columns.csv
-- (schema,table,column,description,data_type)
--
-- DESCRIPTION must be the PROSE field (English sentences). Some
-- Clarity versions name it COLUMN_DESCRIPTION — verify one known
-- column reads as a sentence before saving. The token-style
-- COL_DESCRIPTOR (`<table>__<column>`) is DERIVABLE and ruled out
-- of the extract (F-CP2, Sunny 2026-09-19: "i don't think it's
-- useful").
--
-- The dedupe law applies to the CLARITY_TBL join (see Script 1).
SELECT
    'dbo'            AS [schema],
    TBL.TABLE_NAME   AS [table],
    COL.COLUMN_NAME  AS [column],
    COL.DESCRIPTION  AS [description],
    COL.DATA_TYPE    AS [data_type]
FROM CLARITY_COL COL
INNER JOIN CLARITY_TBL TBL
        ON TBL.TABLE_ID = COL.TABLE_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
    'PASTE_YOUR_BATCH_TABLES_HERE'
)
ORDER BY TBL.TABLE_NAME, COL.COLUMN_NAME;
