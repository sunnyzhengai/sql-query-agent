# Handoff — ingestion routes: verification-only 01 + peer route notebooks

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
