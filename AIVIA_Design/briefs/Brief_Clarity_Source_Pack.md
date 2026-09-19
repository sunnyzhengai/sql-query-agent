# Brief_Clarity_Source_Pack — the Epic extract as a contracted product artifact

**Status: BUILT** (2026-09-19 the same sitting — the pack went 1.0
→ 1.1 BEFORE first push: F-CP1 CLOSED live (his CLARITY_TBL_FK
findings row landed within the hour; the tripwire flipped in the
same act, proving itself on its first day) · Script 5 became THE
GENERATOR at his NAME-column law · pins 8/8 GREEN (every script
parses under the engine's own ScriptDom; aliases == intake headers;
the dedupe law mechanical) · FULL SUITE 751/0 (11:10) · ruff zero
new offenses · closing check BALANCED 14==14 · CLOSED at the push +
his first real extract through the pack. APPROVED mid-extract: "please
solidify these queries in the contract" — with four live rulings
the same message: (1) the CLARITY_TBL dedupe — "there are
duplicates that's why i included the is not null. otherwise you'll
get two rows for each table" → THE DEDUPE LAW, applied at every
CLARITY_TBL touch; (2) the single-table literal was "an example to
show you what the metadata looks like … remove this example" → the
one batch list; (3) "you can re-write to fit the shape"; (4) the
descriptor field is `<table>__<column>` — "i don't think it's
useful" → RULED OUT as derivable (F-CP2). PLUS the wall's scope
refined: "only metadata is fine. no real data." PLUS the pk
dictionary FOUND (F-CP4): CLARITY_TBL_PK — LINE is the ordinal,
PK_COLUMN_ID joins CLARITY_COL, COLUMN_DESCRIPTOR is the derivable
token. CS1–CS4 proceed as proposed, standing unopposed under his
"solidify" word.)

| field | content |
|---|---|
| class | planned addition — fills the source-pack slot the sepsis pack established (`source_pack_version` is already a manifest law; `sepsis-pack-1.2` is the precedent; the SOP runbook already tells every customer "run the source pack's Script 1") |
| claims | Sunny's words (2026-09-19, mid-extract): "no, Clarity has tables about Clarity's metadata. i've given you the sql files to get all metadata" (found: scripts/extract_clarity_dictionary.sql — CLARITY_TBL + CLARITY_COL, era-1, sepsis-scoped) · "the pk, joins are both in clarity tables too" · **"we need contracts for these tables. because every hospital customer who uses epic would use the exact same scripts"** |
| impacts (computed) | NEW `AIVIA_Product/source_packs/clarity/` (the pack: one SQL script per extract file + README + the pack version string) · contract rows binding each Epic dictionary source table to the extract file it feeds (home per CS1) · tests FIRST: every pack script parses under ScriptDom and its SELECT aliases equal the intake contract's headers EXACTLY (the parser we ship proves the pack we ship — no Epic access needed in CI) · scripts/extract_clarity_dictionary.sql retires INTO the pack (one home; the era-1 file was sepsis-scoped) · the SOP runbook's "provided separately" line re-points to the pack path |
| ambiguities | CS1–CS4 below |
| debt declared | THE PK/JOIN DICTIONARY NAMES: Sunny has confirmed Clarity's dictionary carries primary-key and join metadata; the exact table/column names return from his work session as FINDINGS ROWS (Epic-generic names, not work data — they may land in the repo). THE PLACEHOLDER LAW: until they land, the pack's pk/joins scripts ship as named placeholders WITH a tripwire test that fails when the real names arrive un-integrated |
| retirement (P4) | supersedes scripts/extract_clarity_dictionary.sql (era-1, sepsis-pinned table list) — retires into the pack in this act |
| does this promote? (P5) | with the next promotion after CLOSED |
| Sunny's approval | (pending — rule CS1–CS4) |
| closing check | (filled at CLOSED) |

## The design: one pack, six scripts, one contract

| pack script | feeds | source (Epic's dictionary) | status |
|---|---|---|---|
| `01_tables.sql` | tables.csv | `CLARITY_TBL` (TABLE_NAME, TABLE_INTRODUCTION) | known — the found script, generalized |
| `02_columns.sql` | columns.csv | `CLARITY_COL` join `CLARITY_TBL` (COLUMN_NAME, COLUMN_DESCRIPTION, DATA_TYPE) | known — same |
| `03_pk.sql` | pk.csv | the dictionary's key metadata (Sunny: it exists) — INFORMATION_SCHEMA fallback documented beside it | PLACEHOLDER until his findings row |
| `04_joins.sql` | joins.csv | the dictionary's relationship metadata (Sunny: it exists) | PLACEHOLDER until his findings row |
| `05_values.sql` | values.csv | the `ZC_*` category tables (code + meaning) | authored with the pack (the SOP's "values dump") |
| `06_manifest.sql` | manifest.json values | `DB_NAME()`, `@@SERVERNAME`, the pack version constant | known |

Scoping law: every script takes ONE table list (the customer's SQL
batch's tables) in ONE place — the same `IN (...)` block, generated
or pasted once, never maintained twice.

The contract: each row above IS a contract row — source table →
extract file → the intake header it must produce, byte-exact. The
enforcement is mechanical and Epic-free: CI parses each script with
ScriptDom (the parser we already ship) and asserts the SELECT
aliases equal the intake headers (`schema,table,description` …).
A pack edit that drifts from the intake contract goes red before
any customer sees it.

## The ambiguities — Sunny rules each

| id | question | proposal (Sunny may overrule) |
|---|---|---|
| CS1 | where the contract rows live: Contract_Technical_Layer (the intake side already lives near it) vs a new `Contract_Source_Packs.md` (packs are per-vendor and will multiply: Caboodle, Cerner…) | a new `Contract_Source_Packs.md` — one doc, one table per vendor pack, joined to the KG1 intake contract by the extract-file key |
| CS2 | the pk/joins scripts before his findings rows land: ship the INFORMATION_SCHEMA forms as the interim body (real, working, PK-complete; joins empty on Epic) with the dictionary forms as the tripwired placeholder — or hold the pack until the names arrive | ship interim + tripwire — his dry run proceeds today either way |
| CS3 | pack version string | `clarity-pack-1.0`; the manifest law already carries it |
| CS4 | the values script scope | `ZC_*` tables in the batch list only, `table,code,meaning` — small, useful, bounded |

## Files declared

    AIVIA_Design/briefs/Brief_Clarity_Source_Pack.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Contract_Source_Packs.md
    AIVIA_Product/source_packs/clarity/README.md
    AIVIA_Product/source_packs/clarity/01_tables.sql
    AIVIA_Product/source_packs/clarity/02_columns.sql
    AIVIA_Product/source_packs/clarity/03_pk.sql
    AIVIA_Product/source_packs/clarity/04_joins.sql
    AIVIA_Product/source_packs/clarity/05_values.sql
    AIVIA_Product/source_packs/clarity/06_manifest.sql
    AIVIA_Test/test_clarity_source_pack.py
    AIVIA_Product/SOP_Extract_Runbook.md
    scripts/extract_clarity_dictionary.sql
    docs/architecture/TEST_MAP.md

(The pack ships in the zip automatically — AIVIA_Product/
source_packs/ is already on the ship-surface allowlist; every Epic
customer downloads the same six scripts. CS1's new contract doc is
AIVIA_Design — Sunny-only, never ships.)

## Build order (after APPROVED)

1. Test FIRST: the parse-and-alias pin, RED (no pack exists).
2. The six scripts (03/04 per CS2) + README; the era-1 script
   retires into 01/02.
3. Contract_Source_Packs.md rows; SOP re-point; INDEX same breath.
4. Full suite + ruff; the tripwire proven RED-able.
5. His findings rows land the real pk/join dictionary names →
   03/04 re-based, tripwire green, pack 1.1.
