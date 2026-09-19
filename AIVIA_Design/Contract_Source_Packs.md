# Contract_Source_Packs — vendor extract scripts as contracted rows

**Status: LIVING (born 2026-09-19, Brief_Clarity_Source_Pack;
Sunny's ruling: "we need contracts for these tables. because every
hospital customer who uses epic would use the exact same scripts")**

One table per vendor pack. Each row binds a vendor dictionary
source to the extract file it feeds and the intake header it must
produce — enforcement is `AIVIA_Test/test_clarity_source_pack.py`:
every script parses under the engine's ScriptDom and its aliases
equal the headers byte-exact, on every commit, no vendor access
needed. Joined to the KG1 intake contract
(`L1_KG1_CONTRACT_DATALOAD.md`, `kg1_intake.REQUIRED_FILES`) by the
extract-file key.

## PACK: clarity (clarity-pack-1.1)

| script | feeds | vendor source | headers (exact) | status |
|---|---|---|---|---|
| 01_tables.sql | tables.csv | CLARITY_TBL (TABLE_NAME, TABLE_INTRODUCTION) | schema,table,description | SOLID |
| 02_columns.sql | columns.csv | CLARITY_COL ⋈ CLARITY_TBL (COLUMN_NAME, DESCRIPTION, DATA_TYPE) | schema,table,column,description,data_type | SOLID |
| 03_pk.sql | pk.csv | CLARITY_TBL_PK ⋈ CLARITY_TBL ⋈ CLARITY_COL (LINE = ordinal; PK_COLUMN_ID → COLUMN_ID) | schema,table,column,ordinal | SOLID |
| 04_joins.sql | joins.csv | CLARITY_TBL_FK ⋈ CLARITY_TBL ×2 ⋈ CLARITY_COL ×2 (LINE enumerates; SOURCE_COLUMN_ID / DESTNATN_TABLE_ID / DESTNATN_COLUMN_ID — Epic's spelling) | fk_num,ordinal,src_schema,src_table,src_column,dest_schema,dest_table,dest_column | SOLID (pack 1.1) |
| 05_values.sql | values.csv | GENERATOR over every ZC_* table: code = the table's first column, meaning = NAME (his law: "the 'NAME' column is always the value column"); only NAME-carrying tables qualify | table,code,meaning | SOLID (generator, pack 1.1) |
| 06_manifest.sql | manifest.json | DB_NAME(), @@SERVERNAME, SYSUTCDATETIME() | db_name,server,as_of | SOLID |

## LAWS (Sunny's rulings, 2026-09-19, quoted in Brief_Clarity_Source_Pack)

| law | content |
|---|---|
| THE DEDUPE | "there are duplicates … otherwise you'll get two rows for each table" — every CLARITY_TBL touch carries `TBL_DESCRIPTOR_OVR IS NOT NULL`; pinned mechanically |
| ONE BATCH LIST | the customer's table list is pasted ONCE per script, the same list in 01/02/03 — never maintained twice |
| THE WALL'S SCOPE | "only metadata is fine. no real data." — dictionary metadata may cross for engine work; row-level business data never |
| EXTRAS TOLERATED | intake reads by header name; a customer adding trailing columns breaks nothing; the shipped scripts emit the exact shape |
| THE DERIVED-LIST LAW | (Brief_Extract_Autogen, "i don't want to keep manually writing and maintaining these lists and files") the batch list is DERIVED: `aivia.fabric_run.extract_scripts(estate)` parses estate_snapshot/*.sql through the one parse door and writes the pack scripts list-filled to `<estate>/extract_scripts/`; the SQL batch is the list's source of truth; hand-pasting stays the no-notebook fallback |

## FINDINGS

| id | finding | status |
|---|---|---|
| F-CP1 | Epic's dictionary carries JOIN metadata (his word: "the pk, joins are both in clarity tables too"); his findings row landed the SAME sitting: CLARITY_TBL_FK — TABLE_ID = the src table, LINE enumerates, SOURCE_COLUMN_ID / DESTNATN_TABLE_ID / DESTNATN_COLUMN_ID resolve through CLARITY_COL/CLARITY_TBL → 04 re-based, pack 1.1, the tripwire flipped in the same act | CLOSED (2026-09-19) |
| F-CP6 | 04 groups rows into ONE join per (src, dest) table pair ordered by LINE — correct for compound keys IF Epic lists their column-pairs as adjacent lines to the same destination; two DISTINCT relationships between the same table pair would over-merge | OPEN — verify by eye on the first real joins.csv (a compound join should read as one fk_num with ordinals 1..n) |
| F-CP2 | the descriptor field is the token `<table>__<column>` — "i don't think it's useful"; derivable from schema+table+column | RULED OUT (derivable is never stored) |
| F-CP3 | CLARITY_TBL duplicates per table in live systems | CLOSED → THE DEDUPE law |
| F-CP4 | the pk dictionary = CLARITY_TBL_PK: LINE = ordinal, PK_COLUMN_ID → CLARITY_COL.COLUMN_ID, COLUMN_DESCRIPTOR = the derivable token | CLOSED → 03_pk.sql |
| F-CP5 | the SOP's "source pack provided separately" predates packs living IN the product | CLOSED → SOP re-pointed to AIVIA_Product/source_packs/ |
