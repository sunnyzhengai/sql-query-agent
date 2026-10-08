-- dict_extract_value_generator.sql — THE ZC UNIVERSE, derived
-- never guessed (the standing law: id columns come from the
-- dictionary itself). ZC category tables do not share one
-- shape, so this query EMITS the extraction SQL instead of
-- running it:
--   code    = the table's first primary-key column
--   meaning = the first of NAME / TITLE / ABBR the table has
-- HOW TO USE (two steps, the customer's hand):
--   1. Run THIS query. It returns one row per ZC table: a
--      ready SELECT ... UNION ALL fragment. Copy the whole
--      result column into a new query window; delete the
--      trailing UNION ALL on the last line; EYEBALL it.
--   2. Run the assembled query; append its result to
--      dict_extract_value.csv (keep one header row).
-- Tables whose code or meaning column cannot be derived are
-- SKIPPED by this generator — counted by eye, never guessed.
-- FIELD FIX (2026-10-07, first customer tenant):
-- CLARITY_TBL_PK.COLUMN_DESCRIPTOR is NOT the bare column
-- name — it is TABLENAME__COLUMNNAME. CODECOL strips the
-- table-name prefix AND proves the result exists in
-- CLARITY_COL; tables that fail the proof are skipped
-- (same skip rule as MEANING).
SELECT
    'SELECT ''' + TBL.TABLE_NAME + ''' AS table_name, ' +
    'CAST(' + CODECOL.COLUMN_NAME + ' AS VARCHAR(50)) AS code, ' +
    MEANING.COLUMN_NAME + ' AS meaning ' +
    'FROM CLARITY.dbo.' + TBL.TABLE_NAME + ' UNION ALL'
    AS generated_sql
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_TBL_PK PK
        ON PK.TABLE_ID = TBL.TABLE_ID AND PK.LINE = 1
    CROSS APPLY (
        SELECT COL.COLUMN_NAME
        FROM CLARITY.dbo.CLARITY_COL COL
        WHERE COL.TABLE_ID = TBL.TABLE_ID
          AND COL.COLUMN_NAME =
              CASE WHEN PK.COLUMN_DESCRIPTOR LIKE
                        TBL.TABLE_NAME + '[_][_]%'
                   THEN SUBSTRING(PK.COLUMN_DESCRIPTOR,
                        LEN(TBL.TABLE_NAME) + 3, 4000)
                   ELSE PK.COLUMN_DESCRIPTOR END
    ) CODECOL
    CROSS APPLY (
        SELECT TOP 1 COL.COLUMN_NAME
        FROM CLARITY.dbo.CLARITY_COL COL
        WHERE COL.TABLE_ID = TBL.TABLE_ID
          AND COL.COLUMN_NAME IN ('NAME', 'TITLE', 'ABBR')
        ORDER BY CASE COL.COLUMN_NAME
                     WHEN 'NAME' THEN 1
                     WHEN 'TITLE' THEN 2
                     ELSE 3 END
    ) MEANING
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME LIKE 'ZC[_]%'
ORDER BY TBL.TABLE_NAME;
