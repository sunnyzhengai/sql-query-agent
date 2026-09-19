-- clarity-pack-1.1 · Script 1 -> tables.csv (schema,table,description)
-- Contract: AIVIA_Design/Contract_Source_Packs.md · pinned by
-- AIVIA_Test/test_clarity_source_pack.py (parses under ScriptDom;
-- aliases == the intake headers, byte-exact).
--
-- THE DEDUPE LAW (Sunny's field ruling, 2026-09-19): CLARITY_TBL
-- carries duplicate rows per table in live systems; the
-- descriptor-override IS NOT NULL filter is the dedupe — required
-- at EVERY CLARITY_TBL touch, in every script of this pack.
--
-- THE BATCH LIST: paste the tables your SQL batch references —
-- the SAME list in scripts 01, 02 and 03, maintained once.
SELECT
    'dbo'                  AS [schema],
    TBL.TABLE_NAME         AS [table],
    TBL.TABLE_INTRODUCTION AS [description]
FROM CLARITY_TBL TBL
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
    'PASTE_YOUR_BATCH_TABLES_HERE'
)
ORDER BY TBL.TABLE_NAME;
