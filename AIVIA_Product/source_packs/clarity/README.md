# Clarity source pack — clarity-pack-1.1

Six scripts, one per extract file, for ANY Epic Clarity system —
the dictionary schema is Epic's, not any one hospital's, so every
customer runs these exact scripts (the turn-key ruling,
2026-09-19). Contract: `AIVIA_Design/Contract_Source_Packs.md`;
mechanically pinned by `AIVIA_Test/test_clarity_source_pack.py`
(each script parses under the engine's own ScriptDom and emits
exactly the intake headers).

| script | produces | source |
|---|---|---|
| 01_tables.sql | tables.csv | CLARITY_TBL |
| 02_columns.sql | columns.csv | CLARITY_COL + CLARITY_TBL |
| 03_pk.sql | pk.csv | CLARITY_TBL_PK + CLARITY_COL |
| 04_joins.sql | joins.csv | CLARITY_TBL_FK + CLARITY_TBL + CLARITY_COL |
| 05_values.sql | values.csv | GENERATOR: one SELECT per ZC_* table (code = first column, meaning = NAME) |
| 06_manifest.sql | manifest.json values | DB_NAME(), @@SERVERNAME |

How to run (any SQL client, read-only, dictionary metadata only —
never row-level business data):

1. Paste your batch's table list into the ONE `IN (...)` block —
   the same list in 01, 02, 03.
2. Run each script; save each grid as its CSV with headers
   included (SSMS: Tools → Options → include column headers).
3. 04 filters BOTH sides to your batch list — include the ZC_*
   and master tables your SQL touches so their joins survive.
4. 06's values go into manifest.json verbatim. db_name/server are
   OPTIONAL (MR1a): omit for the minimal form, or name the db in
   BOTH manifest and registration to arm the wrong-database
   refusal (case-sensitive when armed).
5. The six files form `<source>_snapshot/` beside your
   registration.json.

Laws carried: THE DEDUPE (every CLARITY_TBL touch filters
TBL_DESCRIPTOR_OVR IS NOT NULL — live systems carry duplicate
rows) · extras tolerated (intake reads by header name; trailing
extra columns are ignored) · the descriptor token
`<table>__<column>` is derivable and stays out.
