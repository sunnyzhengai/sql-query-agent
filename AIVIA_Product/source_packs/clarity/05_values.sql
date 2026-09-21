-- clarity-pack-1.2 · Script 5 -> values.csv (table,code,meaning)
--
-- THE GENERATOR (Sunny's ruling, 2026-09-19: "for any table that
-- starts with ZC_, pull SELECT *. the 'NAME' column is always the
-- value column"): this query WRITES one SELECT per ZC_* table —
-- the code column is the table's FIRST column, the meaning is
-- always NAME (only tables carrying a NAME column qualify).
--
-- How to run:
--   1. Run this script; the result is one generated line per
--      ZC_* table, each ending in UNION ALL.
--   2. Copy the whole result column into a new query window.
--   3. Delete the trailing "UNION ALL" on the LAST line; run.
--   4. Save that grid as values.csv (headers included).
-- To scope to your batch only, add:
--   AND T.TABLE_NAME IN ( ...your ZC tables... )
SELECT
    'SELECT ''' + T.TABLE_NAME + ''' AS [table], '
    + 'CAST(' + QUOTENAME(C1.COLUMN_NAME) + ' AS varchar(50)) AS [code], '
    + 'CAST(NAME AS varchar(500)) AS [meaning] '
    + 'FROM ' + QUOTENAME(T.TABLE_SCHEMA) + '.' + QUOTENAME(T.TABLE_NAME)
    + ' UNION ALL'
    AS generated_select
FROM INFORMATION_SCHEMA.TABLES T
JOIN INFORMATION_SCHEMA.COLUMNS C1
  ON C1.TABLE_SCHEMA = T.TABLE_SCHEMA
 AND C1.TABLE_NAME = T.TABLE_NAME
 AND C1.ORDINAL_POSITION = 1
JOIN INFORMATION_SCHEMA.COLUMNS CN
  ON CN.TABLE_SCHEMA = T.TABLE_SCHEMA
 AND CN.TABLE_NAME = T.TABLE_NAME
 AND CN.COLUMN_NAME = 'NAME'
WHERE T.TABLE_TYPE = 'BASE TABLE'
  AND T.TABLE_NAME LIKE 'ZC[_]%'
ORDER BY T.TABLE_NAME;
