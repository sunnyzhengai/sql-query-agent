# Brief_Extract_Autogen — the batch list derives itself from the SQL

**Status: BUILT** (2026-09-19 same sitting: derivation pins
RED→GREEN 4/4 (list derives from the SQL through map_tree · 04
carries it both sides · unparseable counted-named · empty-estate
refusal); the wheel pins re-based (2.1.0 carries the pack as
package data); FULL SUITE 761/0 (11:11) after ONE reconcile —
the zero-SQL zip pin met the pack's ship-in-zip ruling and
narrowed to "no SQL outside the source packs", both his quotes in
the pin's docstring; ruff zero new offenses; the 2.1.0 wheel in
dist/ (sha256 bd870f93…), 2.0.0 retired. CLOSED at his cell run.
APPROVED: "approved, build it" — EA1/EA2 as
proposed; his download question answered: YES, wheel 2.1.0 carries
it. PRESENTED the same sitting at: "this
is too manual. can you automate: read the sql files in the
estate_snapshot/ folder, extract the clarity tables and columns,
and populate these queries? i don't want to keep manually writing
and maintaining these lists and files")

| field | content |
|---|---|
| class | planned addition — extends the pack (Brief_Clarity_Source_Pack) and the thin-shell driver (Brief_Fabric_Resident FR5) with the derivation the engine already owns: ScriptDom parses the estate's SQL; the table list falls out of the parse |
| claims | his words above — THE DERIVED-LIST LAW: a customer never hand-maintains a table list; the SQL batch IS the list's source of truth |
| impacts (computed) | `aivia/fabric_run.py` gains `extract_scripts(estate_path)`: parse every `estate_snapshot/*.sql` via the existing `map_tree` (the ONE parse door — no second extractor), collect distinct table references (bare names → default_schema `dbo`; unparseable files COUNTED and named, never fatal), substitute the list into the pack scripts' `PASTE_YOUR_BATCH_TABLES_HERE` slot, write the populated scripts to `<estate>/extract_scripts/` and print them · the pack templates ride INSIDE the wheel (build_wheel copies `source_packs/clarity/` → `aivia/_source_packs/`, same one-home pattern as the registries) · pyproject → 2.1.0; the wheel-boot pin gains the pack-carriage clause · dist swaps 2.0.0 → 2.1.0 |
| ambiguities | EA1 bare names default to `dbo` (the manifest's default_schema) — proposed yes · EA2 a file that fails to parse is a counted, named line in the cell's output; generation continues — proposed yes |
| debt declared | none; supersedes tonight's "option 1" by his choice — running the new cell at work requires the 2.1.0 wheel re-upload (one publish), which also carries the minimal-registration change for free |
| retirement (P4) | nothing retires; the manual paste-the-list route stays documented as the no-notebook fallback |
| does this promote? (P5) | with the next promotion |
| Sunny's approval | "approved, build it" (2026-09-19; .gitignore added for the build-time _source_packs transient, the registries pattern) |
| closing check | (filled at CLOSED) |

## The customer's whole flow after this

    cell: f.extract_scripts("/lakehouse/default/Files/sql_pilot")
      -> "parsed 31 files · 24 tables referenced · 0 unparseable"
      -> extract_scripts/01..05.sql appear in the lakehouse, lists filled
    copy each into the SQL client -> run -> save CSVs -> upload
    cell: f.dry_run(...)

No hand-written list, ever; adding a SQL file to the estate and
re-running the cell regenerates the scripts.

## Files declared

    AIVIA_Design/briefs/Brief_Extract_Autogen.md
    AIVIA_Design/INDEX.md
    AIVIA_Design/Contract_Source_Packs.md
    aivia/fabric_run.py
    devtools/build_wheel.py
    pyproject.toml
    tests/aivia/test_extract_autogen.py
    tests/aivia/test_wheel_boot.py
    AIVIA_Product/source_packs/clarity/README.md
    pilots/work_dryrun/README_Runbook.md
    docs/architecture/TEST_MAP.md
    dist/sql_query_agent-2.1.0-py3-none-any.whl
    .gitignore
    tests/aivia/test_ship_surface.py

(test_ship_surface.py added at build: the zero-SQL zip pin
(Brief_Packaging: "i don't need to download any sql files") met
the pack's ship-in-zip ruling (Brief_Clarity_Source_Pack) — the
intents reconcile as "no SQL ships OUTSIDE the source packs";
data SQL stays banned, tool SQL ships.)

(+ the 2.0.0 wheel retires from dist/ per FR2's one-current-wheel
law — git history keeps it.)

## Build order (after APPROVED)

1. Tests first, RED: the synthetic-estate derivation pin (two toy
   SQL files → the list lands in 01–04, `dbo` defaulting, the
   unparseable counter) + the wheel pins re-based (2.1.0, pack
   carried).
2. fabric_run.extract_scripts + the template resolver (repo path
   in the repo, package data in the wheel — the registry pattern).
3. build_wheel copies the pack; pyproject 2.1.0; wheel built,
   dist swapped.
4. Docs; full suite + ruff; push at his word; his re-upload.
