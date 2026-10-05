# Brief_Packaging — the allowlist manifest and the deterministic work wheel

Status: DRAFT for Sunny's stamp — scope RULED 2026-10-04 (Sunny,
in chat): DETERMINISTIC-ONLY. Drafted by Claude the same day.
Fulfils the queued gate from the 2026-09-18 wall ruling
("engine-outbound only, work data never comes back" — the
'never mix' law's mechanical form is THIS manifest).

## The law this brief implements

The engine may travel TO work; nothing of the estate travels
with it, and work data never comes back. A work-bound wheel is
legal ONLY when its contents equal a ruled ALLOWLIST exactly —
checked mechanically at build, refused loud on any drift.

## The two wheels (recommendation: separate names, never confused)

1. `aivia01` — the FABRIC wheel (exists, 0.3.0): the full
   AIVIA_01 modules for Sunny's own tenant. Not in this brief's
   scope beyond the naming split.
2. `aivia01-sqldesc` — the WORK wheel (new): the deterministic
   description engine only. Parse T-SQL, build the structural
   sheets, render the 06 technical descriptions. ZERO API keys,
   ZERO LLM calls, zero AIVIA prompts — the 07 business layer
   (card laws, walk, blessing machinery) stays home.

## THE ALLOWLIST (the work wheel's exact contents)

TRAVELS — engine code only:
- scriptdom_loader.py        (the one parse door, ADR 0001)
- parse_sql_tree.py          (the walker to the 05 sheets)
- derive_tables_columns.py   (structural derivation)
- technical_descriptions.py  (the deterministic 06 renderer)
- the ScriptDom DLL, wheel-internal (the loader's four-route
  law already knows this route; the old estate shipped it)
- a NEW thin CLI wrapper (build item): one command, folder of
  .sql in, one technical-description .txt per file out
- this manifest itself, as data — the wheel can state its law

NEVER TRAVELS (refused at build, test-locked):
- business_descriptions.py, business_walk.py (prompt laws, the
  walk, the checker — AIVIA's 07 IP)
- chat_bot.py, local_chat.py, azure_models.py, fabric_assets.py
  and every loader/notebook module (keys, endpoints, tenant)
- AIVIA_01_Data/** in any form — dictionaries, graphs, sheets,
  registries, blessings, descriptions (customer/estate data)
- .env, any key, any endpoint string
- AIVIA_01_Design/**, AIVIA_01_Test/** (laws and locks stay home)

## The mechanical gate (test-locked, red first at build)

1. MANIFEST EQUALITY: the built wheel's file list == the
   allowlist exactly; one extra or missing file = refused build.
2. THE SECRETS GREP: packaged modules contain no key-shaped
   strings (OPENAI, AZURE, api_key, endpoints) and import no
   network client — deterministic engine imports pythonnet only
   (the old wheel's one-dependency precedent).
3. THE DATA GREP: no packaged file originates under
   AIVIA_01_Data/ or carries estate values (the eight-department
   census strings as the canary test).
4. The work_* gitignore guard stands (built 2026-09-18): work
   SQL parsed BY the wheel at work never enters this repo.

## Prereqs at work (the turn-key checklist, 5-rule gate)

- Python 3.11+ and `pip install aivia01_sqldesc-<v>.whl`
- .NET 8 runtime present (the loader asserts DOTNET_ROOT only
  if its folder exists; macOS/Windows both known routes)
- No network, no keys, no config — a folder of .sql files is
  the entire input; .txt descriptions are the entire output.

## For Sunny's stamp

[x] Scope: deterministic-only (RULED 2026-10-04, in chat)
[ ] The wheel name: aivia01-sqldesc (or her name)
[ ] The CLI shape: `aivia-describe <folder>` one-command form
[ ] DLL wheel-internal (vs carried alongside)
[ ] The allowlist above, line by line

Build order after her stamp, per the standing process: the
manifest-equality + secrets-grep + canary locks land RED, the
CLI wrapper's pseudo code for her eye, then the build, then the
wheel artifact for her hand.
