# Handoff — extractor must become the turn-key front door

> **Status (2026-08-16, dev session): items 1–6 implemented in 1.8.0.**
> Strip killed (definitions stored as-extracted, \r\n normalized, 7-column
> rows fixing a latent MERGE schema mismatch); procs default-on;
> three connection profiles with injectable AAD token provider;
> proc-parity tests (tests/extractor/test_proc_parity.py) prove
> extracted == file-loaded bytes over the golden corpus; runbook in
> INSTALLATION_GUIDE "Automated Extraction"; dual-writer protocol
> documented in the SQL_SOURCES contract (owner 01_install, extractor
> merges by metric_id). Appendix: extractor/discovery sqlglot references
> are GONE; the parser-core demolition remains a separate release.
> LIVE-VERIFIED 2026-08-16: first extraction run on Fabric succeeded —
> 28/28 procs discovered and merged via the fabric_native profile
> (00_extract_sql against the seeded demo SQL database). Two
> customer-shaped fixes fell out en route: ODBC driver resolution
> (Fabric ships 18, config said 17 — 1.12.1) and single-database
> corpus (Fabric SQL rejects three-part names — 1.11.3). Parse
> parity confirms when 02 reproduces the known counts.

**From:** the learning/review session, 2026-08-16 (read-only by agreement).
**To:** the dev session. **Origin:** Sunny's turn-key requirement ("no manual
load for anything, procs or views") collided with the extractor's actual
state during the notebook-map exercise.

## Finding

The product's PROVEN ingestion path is the manual one (files → 01_install /
load_sql_files → ScriptDom): that is how the 790-proc, 99%-parse result was
achieved. The automated path (extract_views via gateway) is scaffolding:

1. **Never run in production** — its MERGE was 100%-broken until the
   2026-08-15 fix (noqa-inside-f-string), proving zero production use.
2. **Zero proc-specific tests** — tests/extractor/test_extractor.py covers
   hashing/change-tracking generically; "PROCEDURE" appears 0 times. The
   type map + discovery query DO support SQL_STORED_PROCEDURE (config
   `object_types`), but nothing proves the end-to-end path.
3. **Design conflict at the front door:** `discovery.strip_create_prefix`
   strips CREATE VIEW/PROC wrappers with **sqlglot** (+ the audit-flagged
   naive " AS " fallback that can corrupt bodies). This routes every
   extracted definition through the decommissioned parser — violating the
   native-parsers rule — to perform a strip that ScriptDom does not need
   (02 parses full CREATE PROCEDURE definitions natively; the 790 procs
   went in unstripped).

## Wanted

1. **Promote the extractor to first-class**: default `object_types` to
   `["VIEW", "SQL_STORED_PROCEDURE"]` (or make the install flow ask);
   Marketplace customers must not hand-export files.
2. **Kill the sqlglot strip**: store definitions as extracted and let
   ScriptDom (02) handle wrappers — or if stripping is truly needed,
   ScriptDom-based, loud failure, never the naive fallback. Verify 02's
   ScriptDom path accepts CREATE VIEW wrappers the same way it accepts
   CREATE PROCEDURE.
3. **Proc-parity tests**: run the golden corpus (anonymized fixtures)
   through the extractor path — discovery filter, hash/tracking, MERGE
   upsert, then 02 parse — proving extracted == file-loaded results.
4. **Gateway runbook**: INSTALLATION_GUIDE section for the on-prem gateway
   + extractor config (plain numbered steps), since this becomes the
   primary customer path.
5. Registry/gates: extract_views writes input_sql_sources but is not its
   owner (01_install is) — decide how the contract models two writers of
   one input table before promoting the second writer.

## 6. Turn-key for BOTH source environments (Sunny, 2026-08-16)

Customers split into: (a) on-prem SQL Server — gateway path, what
extract_views targets today; (b) Azure SQL / Managed Instance — direct
connection, no gateway; (c) Fabric-native (Warehouse, Fabric SQL DB,
mirrored DB) — T-SQL endpoint reachable straight from the notebook with an
AAD token. The discovery core is source-agnostic (sys.objects /
sys.sql_modules exist across all three), so this is a CONNECTION-PROFILE
problem, not a new extractor: extractor config gains
`source_type: onprem_gateway | azure_direct | fabric_native`, and
create_connection grows the third profile (AAD token via
notebookutils.credentials, no gateway). Sunny's own workplace is case (a);
the manual-upload route existed only because the gateway path was never
finished — with 1–5 done, no customer environment requires manual load.

## Appendix: complete sqlglot inventory (2026-08-16 sweep)

The audit-src removal list covered the parser core. The full-repo sweep
adds references it missed — ALL must move in the demolition:

- FUNCTIONAL imports: parser/sql_parser.py, parser/sql_extractor.py,
  parser/scriptdom_extractor.py, extractor/discovery.py
  (strip_create_prefix), tests/golden (TestFallbackParserSmoke),
  tests/parser/test_sql_extractor.py.
- BEHAVIORAL (easy to forget):
  - 01_install notebook line ~86: dependency-check list includes
    ("sqlglot", "sqlglot") — install would FAIL post-removal.
  - parser/error_classifier.py: taxonomy classifies sqlglot-era error
    strings; needs ScriptDom-era categories.
  - schemas.py ~979: ops_extraction_inspection column description says
    "sqlglot parse succeeded".
  - environment/requirements.txt pin + environment/README.md probe;
    pyproject dependency; CI pip-audit grep (ci.yml ~71) lists sqlglot.
- COMMENT-ONLY (update wording): steps/parse.py docstring,
  scriptdom_fabric.py docstrings, 02_parse comment.
