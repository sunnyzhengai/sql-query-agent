# Handoff — ingestion routes: verification-only 01 + peer route notebooks

> **Status (2026-08-17, dev session): items 1–5 implemented in 1.14.0.**
> 01_install is verification-only (env checks; error-seed kept; final
> cell reports ingestion STATE from the tables with route pointers; no
> folder FATALs — sql_input/dictionary are informational). Routes:
> 00a_ingest_sql_filedrop (from 01's load cell, dup-identity gate
> intact), 00b_ingest_sql_folders (promoted loader, loud partial-load
> refusal), 00c_ingest_sql_live (renamed from 00_extract_sql, same
> logicalId so the Fabric item renames in place), 00d_dict_clarity
> (formatted-CSV cell + raw-export cell, dup gates intact),
> 00e_dict_caboodle (merge, wipe-guard intact). Old loader scripts
> retired. Registry owners/writers rewired (writers ground truth
> enforced; contracts scanner glob widened to see lettered notebooks).
> INSTALLATION_GUIDE Step 5a is the route decision table + the
> source-pairing rule. 00a-e lettering kept — no renumbering (item 5).

**From:** review session, 2026-08-17. **To:** dev session.
**Evidence:** during the work-copy setup, Sunny was pulled back to
01_install THREE times despite explicit skip-it guidance — its cell-0
sql_input FATAL blocked its salvageable cells, and nothing tells a user
which ingestion route is in effect or already satisfied. The installer
currently ASSUMES the file-drop route; loader-based and extractor-based
installs must skip it and cherry-pick its cells by hand (env checks ✓,
dictionary load, error-seed cell). Absorbs the parked "01 couples
env-checks with file-drop ingestion" item.

## Wanted

1. **01_install becomes verification-only**: environment, packages,
   ScriptDom/DLL, config, folder layout. Its FINAL cell reports ingestion
   STATE from the tables/registry instead of assuming a route:
   "input_sql_sources: present (1344 rows) / ABSENT — run one of 00a/b/c".
   Same mechanism as the gates: state-driven, never memory-driven. No
   FATAL for a missing sql_input folder — that folder belongs to route
   00a only.
2. **Route notebooks as labeled peers**, each with a route banner in cell 0
   and title: `00a_ingest_sql_filedrop` (current 01 cell 1),
   `00b_ingest_sql_folders` (promote notebooks/data_loading/load_sql_files
   to first-class: config block for folders, loud partial-load failure —
   already hardened), `00c_ingest_sql_live` (extract_views, 3 connection
   profiles). Dictionary routes likewise (`00d_dict_clarity` filedrop/ABFS,
   `00e_dict_caboodle`). All routes write the same contract tables under
   the dual-writer protocol (1.8.0 precedent); registry owner/enrichers
   updated to match (writers-ground-truth test will enforce).
3. **Error-seed and any other route-independent 01 cells** move to the
   verification notebook (they must not be hostage to a route assumption).
4. **INSTALLATION_GUIDE route decision table**: files in one folder → 00a;
   files across folders/workspaces → 00b; live server → 00c. One look, no
   guessing.
5. Numbering note: 00a-e naming keeps 02-13 stable; if renumbering is
   preferred instead, it cascades into docs/tests/PIPELINE_MAP — dev
   session's call, but don't renumber casually.

## Naming principle (Sunny + review session, 2026-08-17)

**Number the derivation, letter the acquisition.** Numbered notebooks
(02+) = derivation: org-agnostic, rerunnable, order-meaningful. The 00
letter family = acquisition: org-specific, route-alternative,
event-driven (run when source material changes). Order is enforced by
the precondition gates on STATE, not by numbering — numbers are cadence
documentation, and acquisition has no fixed cadence.

## Source-pairing rule (same evening's finding, belongs in the guide)

A source system enters as a PAIR — its SQL and its dictionary together —
or the 06 dictionary_coverage gate blocks (by design). The route table
should say this where users pick routes.

## Field evidence (2026-08-17, work deployment, added post-1.14.0)

00b's filename-keyed identity produced 25 REAL metric_id collisions at
Sunny's work deployment (same proc names exported in both procs_schema_a
and procs_schema_b folders) — caught by 02's ops_parse_results
unique(metric_id) postcondition. Stopgap applied in the field: regex on
each file's CREATE header (schema-qualified id, folder-schema fallback) +
dropDuplicates. Wanted properly: parse-based identity in 00b (ScriptDom /
src/parser/identity.py, NOT regex — native-parsers rule), plus a
duplicate-identity gate inside every ingestion route so collisions fail
AT THE ROUTE with a message, not downstream at 02's postcondition.
