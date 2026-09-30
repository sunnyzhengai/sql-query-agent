-- 02_emr_data_dictionary_discovery.sql (contract Output File 3, first
-- move). Run ONCE in the EMR's Clarity database by Sunny's hand.
-- Save the full result as 02_emr_data_dictionary_discovery.csv in
-- AIVIA_01_Data/02_emr_data_dictionary/.
-- Also answer (from knowledge or the inventory rows below): which
-- dictionary table holds the JOIN relationships between tables?
--
-- ONE result set, two kinds of rows:
--   COLUMN_NAME filled -> the columns of CLARITY_TBL / CLARITY_COL
--   COLUMN_NAME blank  -> inventory: every table named CLARITY_...
--     (to spot where joins, keys, and category values live)
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME,
       DATA_TYPE, ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('CLARITY_TBL', 'CLARITY_COL')
UNION ALL
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, '', '', 0
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE 'CLARITY\_%' ESCAPE '\'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
