-- dict_extract_value.sql — the VALUE MEANINGS (code -> name),
-- SHAPE-MATCHED (table_name / code / meaning).
-- TWO PARTS make the full set:
--   1. THIS file: the vendor-standard ENTITY tables every
--      Clarity shop has (beds, departments, payors, locations,
--      rooms, service areas) — static, run as-is.
--   2. The ZC category universe: GENERATED per customer by
--      dict_extract_value_generator.sql (ZC tables do not
--      share one column shape — never guess; the generator
--      derives each table's code and meaning columns from the
--      dictionary itself).
-- Run by the customer's hand; save BOTH results together as
-- dict_extract_value.csv (this result first, the generated
-- query's result appended, one header only).
SELECT 'CLARITY_BED' AS table_name,
       CAST(BED_CSN_ID AS VARCHAR(50)) AS code,
       BED_LABEL AS meaning
FROM CLARITY.dbo.CLARITY_BED
UNION ALL
SELECT 'CLARITY_DEP' AS table_name,
       CAST(DEPARTMENT_ID AS VARCHAR(50)) AS code,
       DEPARTMENT_NAME AS meaning
FROM CLARITY.dbo.CLARITY_DEP
UNION ALL
SELECT 'CLARITY_EPM' AS table_name,
       CAST(PAYOR_ID AS VARCHAR(50)) AS code,
       PAYOR_NAME AS meaning
FROM CLARITY.dbo.CLARITY_EPM
UNION ALL
SELECT 'CLARITY_LOC' AS table_name,
       CAST(LOC_ID AS VARCHAR(50)) AS code,
       LOC_NAME AS meaning
FROM CLARITY.dbo.CLARITY_LOC
UNION ALL
SELECT 'CLARITY_ROM' AS table_name,
       CAST(ROOM_CSN_ID AS VARCHAR(50)) AS code,
       ROOM_NAME AS meaning
FROM CLARITY.dbo.CLARITY_ROM
UNION ALL
SELECT 'CLARITY_SA' AS table_name,
       CAST(SERV_AREA_ID AS VARCHAR(50)) AS code,
       SERV_AREA_NAME AS meaning
FROM CLARITY.dbo.CLARITY_SA;
