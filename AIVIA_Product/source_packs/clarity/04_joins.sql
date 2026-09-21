-- clarity-pack-1.2 · Script 4 -> joins.csv
-- (fk_num,ordinal,src_schema,src_table,src_column,
--  dest_schema,dest_table,dest_column)
--
-- THE REAL FORM (F-CP1 CLOSED, Sunny's findings row 2026-09-19):
-- CLARITY_TBL_FK — TABLE_ID = the referencing (src) table; LINE
-- enumerates its FK entries; SOURCE_COLUMN_ID / DESTNATN_TABLE_ID /
-- DESTNATN_COLUMN_ID (Epic's spelling) resolve through CLARITY_COL
-- and CLARITY_TBL. Rows group into ONE join per (src, dest) table
-- pair, ordered by LINE (F-CP6 records this grouping assumption —
-- eyeball a compound join on first run).
--
-- The dedupe law applies to BOTH CLARITY_TBL joins (see Script 1).
-- Both sides filter to the batch list: a join whose destination is
-- outside your list is dropped — include the ZC_* and master
-- tables your SQL touches so those joins survive.
SELECT
    DENSE_RANK() OVER (ORDER BY STBL.TABLE_NAME, DTBL.TABLE_NAME)
                     AS [fk_num],
    ROW_NUMBER() OVER (PARTITION BY STBL.TABLE_NAME, DTBL.TABLE_NAME
                       ORDER BY FK.LINE)
                     AS [ordinal],
    'dbo'            AS [src_schema],
    STBL.TABLE_NAME  AS [src_table],
    SCOL.COLUMN_NAME AS [src_column],
    'dbo'            AS [dest_schema],
    DTBL.TABLE_NAME  AS [dest_table],
    DCOL.COLUMN_NAME AS [dest_column]
FROM CLARITY_TBL_FK FK
INNER JOIN CLARITY_TBL STBL ON STBL.TABLE_ID = FK.TABLE_ID
INNER JOIN CLARITY_COL SCOL ON SCOL.COLUMN_ID = FK.SOURCE_COLUMN_ID
INNER JOIN CLARITY_TBL DTBL ON DTBL.TABLE_ID = FK.DESTNATN_TABLE_ID
INNER JOIN CLARITY_COL DCOL ON DCOL.COLUMN_ID = FK.DESTNATN_COLUMN_ID
WHERE STBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND DTBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND STBL.TABLE_NAME IN (
    'PASTE_YOUR_BATCH_TABLES_HERE'
)
  AND DTBL.TABLE_NAME IN (
    'PASTE_YOUR_BATCH_TABLES_HERE'
)
ORDER BY 1, 2;
