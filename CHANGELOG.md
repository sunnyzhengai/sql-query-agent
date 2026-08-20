# Changelog

All notable changes to AIVIA SQL Intelligence Agent are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [1.31.0] - 2026-08-20

### Changed — ADR 0044 phase 2: the translator (clauses 2+5 GREEN)
- The step description LLM NEVER sees SQL: src/tree/translate.py
  renders typed tree facts (numbered, or-groups marked, negation in
  the op) and enforces the LEDGER — every must-voice fact returns as a
  numbered line or is counted unvoiced and rendered by the
  deterministic template floor (src/tree/render.py). Clause 2+5
  strict-xfail exit gates flipped.
- descriptions.py: STEP_PROMPT (the SQL-reading prompt) DELETED — no
  dual path; PROMPT_VERSION = 5.t1 (TREE_CONTRACT_VERSION rides in
  every cache key); grounding gate retained on the assembled text;
  DescriptionResult gains unvoiced counts.
- Live spot-check (real model, real fragments): Base_Pop 11/11,
  All_LDAs 11/11 (real codes with the devs' comment meanings),
  ED_PositiveScores 1/1 — zero unvoiced, zero grounding violations.
- Honest limitation: projection-only steps (~10%) get a deterministic
  one-liner until computed-output facts land (filed).

---

## [1.30.0] - 2026-08-20

### Added — tree phase 1b complete (overnight run; ADR 0044)
- Decision nodes IN THE GRAPH: decision layer + step_to_decision /
  decision_to_column / decision_to_step edges, alias-resolved;
  reachability verdict per site (connected or counted — Sunny's law);
  decision layer deliberately excluded from the LPG export until the
  0046 read model (counted exclusion, exact conservation asserts).
- parameter_default sites (Sunny's ruling): the IF default-window
  logic is first-class; ED sepsis now 488/488 decisions, gaps 0.
- Parser-walker fixes ported to production (1b item 8): indexer noise
  excluded (13,156 suppressions -> 0, ZERO structural change — pure
  noise, measured) and the REAL silent bucket fixed: depth cap 15->60
  and counted. Recovered reads corpus-wide: the trace's 3 named misses
  (MED_MIX_COMPONENTS, both SEPSIS_STAGING) + FY_DATE_DIMENSION,
  DM_ICU_STAY — all gains, zero losses.
- Recorded fixtures RE-RECORDED locally via the native parser: 417
  full fragments (0 truncated), anonymization scan clean — the
  stale-fixtures debt is dead. Answer keys re-certified with delta doc
  docs/internal/RECERT_ANSWER_KEY_1_30.md (PENDING Sunny's sign-off);
  grounding evals made summarization-robust (>=2 of the metric's own
  certified tables; refusals stay strict) and cassette re-recorded.
- Dictionary: DM_ICU_STAY authored (newly-seen read); join map steady
  at 68 pairs; C4 verdict 28/28 against the improved parse.
- Toolchain contract (owed from 2026-08-19): CI tools pinned EXACTLY
  (pytest/pytest-cov/ruff/build) + tests/test_toolchain_contract.py
  bans floors on CI tools.

---

## [1.29.0] - 2026-08-19

### Added — the shadow specification adopted (Φ_AIVIA, ADR 0047)
- docs/architecture/SPEC.md v0.3: adversarially audited (A1's cited
  test didn't exist — added; E6's prompt-only gap stated; Term
  projection corrected to PENDING — Term nodes/implements edges do not
  exist yet) and every UNBOUND axiom bound or gated.
- EXTRACTION_REGISTRY (spec:C1): functor XOR exclusion per source kind;
  the missing-joins incident pinned as the acceptance test;
  Snowflake/Databricks/usage-layer/business-terms exclusions explicit.
- T_org vehicle (spec:C4/E5): ORIGIN column (vendor|org) on
  input_dict_tables; 040/050 write it; NULL = vendor.
- Leaf grounding (spec:C4) as a computed verdict in 500:
  completely_parsed per file + fraction + escalated fallout
  (stage 500_leaf_grounding). First recorded-corpus verdict: 27/28 —
  USP_Severe_Sepsis reads 6 undictionaried tables.
- CAPABILITY_REGISTRY (spec:G1–G3): one owner per capability;
  Uses ∖ S = ∅ over src/ for pythonnet/clr/requests/httpx; banned
  parsers ownerless forever.
- Spec gates: E1/E5 strict-xfail exit gates (land with the 0046
  engine). 500's engine floor -> 1.29.

---

## [1.28.0] - 2026-08-19

### Changed — the native-parser law is TOTAL: sqlglot and sqlparse are gone
- Sunny's ruling ("under no circumstances"): sqlglot/sqlparse deleted
  from the entire codebase and BANNED by CI
  (tests/test_native_parser_law.py: imports fail, dependency
  declarations fail, parser instantiation outside the loader fails).
  ADR 0001 amended: the dialect-native parser is the ONLY parser, in
  every environment.
- ScriptDom now runs EVERYWHERE via src/parser/scriptdom_loader:
  Fabric (unchanged), dev machines (pythonnet + ~/.dotnet; Apple's
  hardened system Python is subprocess-probed and fails with
  remediation — local standard is Homebrew python3.11), and CI
  (setup-dotnet step added). pythonnet promoted to a wheel dependency.
- Tree extractor (ADR 0044 clause 1) ported to ScriptDom: verbatim
  token-stream expression text (no CONVERT→CAST rewriting), FOR XML
  PATH / CTE+SELECT INTO / one-arg FORMAT all extract natively; IF
  control flow is a counted gap (control_flow_if) pending the
  parameter_default modeling decision; type-level reflection caching
  (the 13,156-suppression counter is reproduced locally and diagnosed
  as .NET indexer noise — production fix filed as 1b item 8).
- Fallback parser ABOLISHED: sql_parser.py is now the parse model +
  native parse_sql only; sql_extractor.py and scriptdom_extractor.py
  (dead sqlparse/microservice paths) deleted; golden tests reborn as
  exact native structural pins that run on EVERY platform (no CI
  skip — local native parse reproduces the Fabric recording: 417
  steps exactly); parser tests rewritten for whole-script semantics.
- Join map regenerated natively: 62 pairs, 374 evidence occurrences,
  BLIND SPOT 0 (was 192 unevidenced JOINs); two sqlglot-era corrupt
  rows eliminated (a /* comment */ inside a column name, a mangled
  write-target pair); derived-table aliases classified step-side.

---

## [1.27.0] - 2026-08-19

### Added — the join map, deduced from our own corpus (ADR 0046 bootstrap)
- `data/synthetic/dict_relationships.csv`: 63 table-to-table join pairs
  with joining columns and per-pair evidence counts, DEDUCED from the
  de-dialected corpus's own join predicates (users'-reality layer) —
  explicitly never extracted from any vendor dictionary (wall + IP
  decision, Sunny 2026-08-19). Generator:
  `scripts/derive_dict_relationships.py` (bootstrap; retires when
  phase 1b regenerates relationships from graph_decision_sites).
- `input_dict_relationships` registered (planned) with EVIDENCE
  provenance column (corpus | declared) and CARDINALITY (declared or
  blank — Clarity publishes none, so ours is ours).
- Tests pin the CSV to a fresh derivation (drift fails CI) and pin two
  live finds: sqlglot renders [bracketed] identifiers as "quoted"
  (phantom aliases), and t.name drops the '#' temp marker (a temp
  named like a base table could fabricate evidence; names now taken
  from the rendered form).

---

## [1.26.0] - 2026-08-19

### Added — ADR 0044 phase 1: the faithful decision tree (clause 1 green)
- `src/tree/extract.py`: sqlglot-AST decision-site extractor under the
  conservation law — every WHERE / JOIN ON / HAVING / CASE WHEN
  predicate maps to exactly one tree node OR one counted unextracted
  row (`handled + unextracted == total`, no third bucket); boolean
  shape (AND/OR/NOT) preserved, never flattened; dynamic SQL and
  unmodeled constructs are counted, escalated gaps. Proven corpus-wide:
  the equation holds for all 417 recorded fragments.
- `graph_decision_sites` (owner 300, overwrite): one row per decision
  site with the faithful subtree as JSON; conservation queryable in
  the table itself. Unextracted sites also append to `ops_fallout`
  (stage `300_tree_unextracted`) — admin dashboard + future checklist
  inherit them (ADR 0045 §3). 300's engine floor is now 1.26.
- All four clause-1 exit gates flipped (strict-xfail markers removed;
  the lock test now tracks shipped clauses). 16 new extractor tests
  including real corpus shapes (OR-inside-AND, computed systolic
  expression, NOT EXISTS, STUFF/FOR XML PATH as an honest counted gap).
- Found while proving conservation: the recorded fixtures still carry
  pre-1.25.0 TRUNCATED fragments (~190 amputated mid-token) — parse
  truth in CI is unaffected (fixtures replay recorded structure), but
  fixtures must be re-recorded after the full tenant rerun on 1.25+.

### Added — contracts locked in red before the tree redesign (same day, pre-release commit)
- ADR 0044 (tree contract): faithful decision trees + blind round-trip
  verified descriptions; six clauses, each bound to a mechanical check
  in `tests/test_tree_contract.py` as STRICT xfail — CI fails the
  moment a clause passes with its marker present; removing the marker
  is the phase's exit gate. Fixtures are real corpus constructs from
  the traced proc.
- ADR 0045 (escalation contract): no silent residue — every fallout
  row declares `resolution ∈ {auto_resolved, escalated}`; escalated +
  open rows ARE the human checklist (`ops_human_checklist`, future
  admin-dashboard page); novelty (unknown M shapes, unmodeled SQL
  constructs, dynamic SQL, flagged round trips) always escalates.
  Gated in `tests/test_escalation_contract.py`, same red pattern.
- ADR audit: 0003/0006/0019/0032 amended with dated notes (fragments
  become provenance-only, reports are in-graph since 0040, tree facts
  replace raw-fragment prompting, description edge narrowed);
  0034/0035 file statuses synced with the index (superseded in part);
  index rows added for 0041–0045.

---

## [1.25.0] - 2026-08-19

### Fixed — description fabrication eliminated (deep-trace follow-through)
- ROOT CAUSE: fragments were truncated to 500 chars at parse time —
  the description LLM saw amputated SQL (column lists, no WHERE) and
  invented the missing filters; same-logic hashes were blind past
  char 500. Caps removed; regression test pins full fragments.
- Grounding gate: deterministic post-generation checks (ungrounded
  values, ungrounded filter claims, selected-not-filtered) + one
  corrective retry + surgical line removal — absence over fabrication.
  Wired into steps, measures, and metric composition; failures land in
  ops_fallout (stage 600_grounding). Acceptance fixtures are the real
  captured fabrications; live verification 4/4 grounded on the same
  model 600 uses.
- STEP_PROMPT hardened; PROMPT_VERSION=4 — next 600 run regenerates
  every description from full fragments under the gate.
- Orchestrator card facts now expose logic_last_changed_at /
  source_extracted_at (dropped at the assemble layer until now).

---

## [1.24.0] - 2026-08-19

### Added — trust instrumentation (Sunny's three asks)
- Deep trace of reporting.USP_ED_Sepsis (docs/internal/
  TRACE_USP_ED_SEPSIS.md): 43/43 steps exact, 45/48 reads (known
  suppression class), card correct; description audit found fabricated
  filters and invented literal codes at the STEP level — mechanism
  identified, fix designed (HANDOFF_DESCRIPTION_GROUNDING_GATE).
- src/replan.py: registry-derived minimal re-run advisor — consumers
  propagation + owner-invalidates-enrichers; the 2026-08-18
  description-wipe incident is the acceptance test.
- Journey tables are per-run HISTORY (append; unique per run_at +
  entity): every proc's lifecycle by each notebook run, per the
  admin-journey handoff; dashboard runbook gains the run-over-run
  lifecycle matrix and quick-create path.

### Changed
- Engine floor raised to 1.24 (journey contract change rides with it).

---

## [1.23.0] - 2026-08-18

### Added — admin journey dashboard tables (family G's UI half)
- ops_metric_journey: one row per metric, stage columns left-to-right
  ARE the pipeline (loaded/parsed+error_type/in_graph/card/
  described_status/report ties/published flags). Metric-grain always —
  junctions never multiply the driving grain.
- ops_report_journey: report-grain twin — workspace NAME, proc count +
  list, tie_kind with corpus membership.
- Workspace display names: the collector fetches them (one call per
  workspace per run); input_report_sources carries workspace_name; all
  chart axes use names, never ids.
- Unified error vocabulary: journey shares the funnel's codes
  (rejected_by_agent; parse error_category pass-through).
- Reconciliation tests pin loaded = parsed + errored and both grains;
  RUNBOOK_JOURNEY_DASHBOARD.md gives the four-visual build steps.

---

## [1.22.0] - 2026-08-18

### Changed — century-phase renumbering (Sunny's full scheme)
- All 19 notebooks renamed: 0xx acquire (010 filedrop, 020 folders,
  030 live, 040/050 dictionaries, 060 semantic models — the 12
  misfile corrected), 100 verify, 200 parse, 300 graph, 400 cards,
  500 validate, 600/610 describe, 700 index, 800 export, 900/910/920
  publish, 950 ops. Lexicographic sort = run order; 100-gaps leave
  insertion room.
- THE ordering fix: 800_export runs AFTER descriptions — the
  documented "re-run 05 after 07" double-run is deleted everywhere.
- Engine floor raised to 1.22 in every notebook: gates key on step
  names, so notebook/wheel skew across the rename dies loudly.
- Fallout stage codes renamed with their notebooks (060_*, 500_*,
  900_match); historical rows keep old codes (append tables).

---

## [1.21.0] - 2026-08-18

### Added — the funnel view (Question Map gap 3, family G — complete)
- ops_funnel (06-owned, registry-declared): per run per stage —
  in_count, out_count, fell_off, aggregated reason codes. Fallout rows
  that don't cover a drop surface as 'unexplained', loudly. 02 errors
  and 07b rejections fold into the same view.
- 08 matcher retrofit: unmatched Collibra reports write
  no_collibra_match fallout rows (queryable, not scrollback).
- Agent instructions: health questions answer funnel-first, counts
  always WITH reasons. (Re-paste delta_agent_instructions.md.)

---

## [1.20.0] - 2026-08-18

### Added — the diff kernel (Question Map gap 1, family F; ADR 0043)
- src/graph/decomposition_diff.py: deterministic step-aligned diff of
  metric decompositions — WHERE definitions diverge (aligned pairs,
  fragment diffs, per-step table divergence, missing-step findings).
  Alignment: name -> identical content -> table-set similarity;
  unmatched steps are findings, never noise. LLM captions, never
  judges (ADR 0032).
- op_compare gains aspect 'steps' (fourth kernel) — METHODOLOGY
  AMENDMENT made loudly per the amendment rule (ADR 0043; approved
  via HANDOFF_COMPARISON_SHAPE + go-ahead 2026-08-18).
- output_metric_twins: cached divergence verdicts for same-bare-name
  metric groups, recomputed every 04 run (doctrine level 3 —
  verifiable cache of the kernel).
- Agent instructions: sameness questions go twin-cache-first, report
  the kernel verdict verbatim, and never claim sameness from names.
  (Re-paste delta_agent_instructions.md into the Data Agent.)

---

## [1.19.0] - 2026-08-18

### Added — freshness reaches the answer (Question Map gap 2, Trust)
- output_metric_logic carries logic_last_changed_at (logic-hash change
  across runs) and source_extracted_at (extraction tracker; null on
  file-drop routes — unknown is stated, never invented).
- Agent instructions: trust-questions section — the agent cites both
  dates and volunteers them when currency is questioned. (Re-paste
  delta_agent_instructions.md into the Data Agent.)
- 09 Purview descriptions carry a Freshness trailer.
- freshness.stale_after_days (default 30): 06 warns and appends
  stale_source rows to ops_fallout — health signal, never a gate.

---

## [1.18.0] - 2026-08-18

### Added — the notebook contract (ADR 0042)
- NOTEBOOK_REGISTRY: truth-as-data for the driver layer — family,
  serves (Layer-0 question families; >=1 or the notebook is a ghost),
  permitted src.steps entry points, wrapper whitelist, required gates,
  REQUIRES_ENGINE floor. NOTEBOOK_MAP.md (with the QUESTION_MAP
  layer-4 coverage table) is a generated projection.
- Six planks enforced by AST against notebook sources: registry 1:1,
  regex ban, thinness (no classes; only whitelisted wrappers; import
  allowlist; entry-point restriction), gates-by-family, version
  binding (require_engine in every cell 0 — version skew dies loudly),
  field-patch law (marker illegal in repo; patches die on sync).

### Changed
- 01's dictionary-coverage preview moved to src.dictionary
  (preview_table_references, tested); 00b's CREATE-header identity
  pattern now has ONE spelling (src.parser.identity
  CREATE_HEADER_SPARK_PATTERN); 02's unused read_source deleted.
- 10 and 11 gained the standard setup cell (src import + version
  binding) they had been missing.

---

## [1.17.0] - 2026-08-18

### Added — the estate-scale recovery release (four handoffs + ADR 0041)
- M mini-parser + shape census (src/mquery/): tokenizer + recursive
  descent over the needed M subset; shape signatures carry argument
  KINDS; anonymization is whitelist-based (CI leak test — customer
  identifiers cannot appear in a signature). SHAPE_REGISTRY is the
  declarative authority; every supported shape must have a fixture that
  classifies AND extracts. Census runs as 12's pre-step and prints the
  coverage statement up front.
- ops_fallout contract table: every stage that drops an entity writes a
  reason row (stage, entity_id, reason_code, contract_id). 12 fully
  retrofitted (partition drops, naming refusals, collector skips) with
  a per-run funnel print. The 174-silent-models class is impossible.
- TMDL pattern-breakers fixed for Sql.Database AND Odbc.Query:
  parameter/quoted-identifier servers, 3-part bracketed EXEC targets,
  string-concatenated Query values (first-literal-chunk extraction),
  Query field at any record position, Schema/Item navigation. ~430
  files recoverable at the reference estate.

### Changed
- Business-name derivation INVERTED to proc-keyed: a proc consumed by
  one report (or same-titled workspace copies) inherits the title;
  differently-titled consumers refuse with a fallout row — supersedes
  the 1.16.0 first-workspace naming verdict. Identity case-folded;
  corpus membership replaces the TMDL Kind filter (views-as-Table now
  name; DirectLake/InlineSQL self-exclude).
- Test fixtures and docstring examples de-identified (work identifiers
  swept from parser/matcher fixtures and notebook examples).

---

## [1.16.1] - 2026-08-18

### Fixed — the small-fixes sweep (five handoffs, all field-driven)
- Workspace TMDL collector is per-model record-and-continue: one
  non-exportable model no longer kills a whole harvest; skips
  classified (not-exportable / permission / timeout) in 12's report.
- Matcher keys on bare object names (schema-qualified ids produced
  junk keys); the 1.00-junk-score bug fixed (short tokens must match
  exactly, no more 1-char substring wins).
- 07b hardening from live confirmation: "I don't have information
  about" joins REJECT_PHRASES; a CANARY probe runs before every batch
  (stale agent data sources caught before the spend).
- Environment drift: requirements.txt == environment item's yml, now
  test-pinned; environment/README de-versioned and covered by the
  no-hardcoded-version test.
- Collibra description attribute type configurable
  (description_attr_type_id; enterprise layouts display custom fields).

### Removed
- Purview glossary surface (ensure_glossary/publish_glossary_term):
  ghost rule — zero callers ever. Term mining stays. ADR 0031 amended
  with resurrection requirements.

---

## [1.16.0] - 2026-08-18

### Added
- **Multi-workspace TMDL collection** (field find: reports span 4–5 PBI
  workspaces): `semantic_models.workspace_ids` collects every workspace
  in one pass and one write (sequential runs would clobber under
  overwrite semantics); per-workspace counts in the run report.
  Cross-workspace duplicate verdict promoted to contract: workspace_ids
  ORDER names a shared metric; all other reports stay listed for
  steward review — never silently deduped.

---

## [1.15.0] - 2026-08-18

### Changed
- **Generation split from publishing** (HANDOFF_SPLIT_GENERATION_FROM_
  PUBLISH; audit finding #37): new step 07b_generate_agent_descriptions
  owns ops_agent_descriptions (status column added — rejected agent
  non-answers persist for queryable retry/inspection; batch vs final
  tallies distinct; resume-by-rerun preserved). 08 (Collibra) and 13
  (PBI) are pure publishers; a PBI-only customer never touches a
  Collibra notebook. Logic in src/steps/agent_descriptions.py, tested.
- Notebook reorganization audit: devops_lineage.py retired (superseded
  by 12's devops profile), empty notebooks/data_loading/ removed,
  root-utility constraint documented, guide-coverage tests widened to
  lettered notebooks.

---

## [1.14.0] - 2026-08-17

### Changed
- **Ingestion decoupled from installation** (HANDOFF_INGESTION_ROUTES —
  evidence: three pullbacks into 01's route-assuming FATAL during a
  loader-based setup). 01_install is now VERIFICATION-ONLY: environment
  checks, error-seed, and a state-driven ingestion report (which routes
  are satisfied, from the tables — never from memory). Acquisition is
  the 00 letter family of peer routes: 00a filedrop, 00b folders
  (promoted), 00c live (renamed from 00_extract_sql, item renames in
  place), 00d dictionary (formatted or raw), 00e second-source merge.
  Naming principle recorded: number the derivation, letter the
  acquisition. Guide Step 5a is now a route decision table with the
  source-pairing rule (SQL + dictionary enter together).

---

## [1.13.0] - 2026-08-17

### Added
- Brand-neutral core (HANDOFF_BRAND_NEUTRAL_CORE): the commercial name no
  longer appears anywhere in src/ or the numbered notebooks — enforced by
  a CI grep test (tests/test_brand_neutral_core.py, allowlist empty).
  New src/branding.py seam: SQA_PRODUCT_NAME env var brands a deployment
  (neutral default "SQL Intelligence Agent"); Purview glossary + term
  trailer, web UI titles, CLI banner, and the agent system prompt all
  read it. docs/deployment/BRAND_NEUTRAL_SNAPSHOT.md documents what a
  neutral snapshot includes.
- Notebook 11 endpoints moved to org_config `search:` block (kusto_uri,
  kusto_db, embed_endpoint) — tenant URIs no longer hardcoded in the
  notebook; loud config error names the missing keys.

### Changed
- Env var rename with one-release deprecation window (old prefix still
  read, warning logged): SQA_AZURE_API_VERSION, SQA_KUSTO_URI,
  SQA_KUSTO_DB, SQA_LLM_MODEL, SQA_EVENTS_PATH, SQA_EVENTS_ONELAKE_URL,
  SQA_WEBAPP_EAGER. Integration registry endpoint token is now "core".

### Upgrade notes
- App Service (marketplace host): set SQA_PRODUCT_NAME=AIVIA to keep the
  branded UI, and migrate AIVIA_* app settings to SQA_* before the
  fallback is removed next release.
- org_config.yaml: add the `search:` block before running notebook 11
  (see org_config.example.yaml).

---

## [1.12.1] - 2026-08-16

### Fixed
- fabric_native/azure_direct connections failed on Fabric with "Can't
  open lib 'ODBC Driver 17'" — the config default named a driver the
  Fabric Spark runtime doesn't ship (it has Driver 18). The connection
  now RESOLVES the driver: configured name if installed, else newest
  Microsoft driver present, else any SQL Server driver, else a loud
  error listing what IS installed. First live customer-shaped contact
  for the token profile; hardcoded environment assumptions lose again.

---

## [1.12.0] - 2026-08-16

### Changed
- **extract_views promoted to pipeline notebook `00_extract_sql`**
  (Sunny's call): the turn-key front door now git-syncs like every
  numbered notebook — no more copy-paste import. Runs before 01;
  handles procs AND views (old name undersold it). The
  notebooks/data_loading script is retired (ghost rule); registry
  writer names updated (input_sql_sources, ops_extraction_tracking).
- ops_extraction_tracking contract drift fixed: registry columns now
  match the tracker's real record shape (object_id/extracted_at/
  sql_definition were undeclared; last_seen never existed).

---

## [1.11.3] - 2026-08-16

### Fixed
- Seed script failed on Fabric SQL database (Msg 40515): three-part
  cross-database names are unsupported there. Database qualifiers
  (EMRDB., reportingDB.) stripped from the CORPUS, not the seed — one
  corpus everywhere keeps file-load and extraction byte-identical (no
  flip-flop between writers). Also caught by the now-SQL-policing scan:
  aliases HAR->HACC, ERX->RXM, EMRDB_-prefixed aliases, and the Epic
  grouper context literal 'ERX'->'MEDS'. Zero warnings; fixtures,
  cassette, and seed regenerated in lockstep.

---

## [1.11.2] - 2026-08-16

### Changed
- Alias de-fingerprinting (Sunny's find): 33 table aliases derived from
  ORIGINAL vendor table initials (PEH, HSP, SER, EAP, EDG, HNO, the
  ZC_* family) renamed corpus-wide via a new crosswalk `aliases`
  category; generic aliases (DX, DD, ADT, RSN, MAR) kept.
- Master-file vocabulary scrubbed from dictionary prose in every
  observed form — "(I SER .1)", "(EDG 2002)", "HNO-34150", bare-word
  INIs, "(.1 ITEM)" notation, LDA — enumerated from source; scan terms
  gained a word-boundary mode (~wcs) because short codes are substrings
  of ordinary words (SER in USER, EPT in DEPT).
- All previously stubbed descriptions resolved (paraphrase retries +
  12 hand-rewritten short rows); zero stubs remain.

---

## [1.11.1] - 2026-08-16

### Changed — corpus fully de-dialected (Sunny's verdict: no Epic
anything, ever, anywhere customer-facing)

- **Column-level anonymization completed** (reversing the 2026-07
  "columns are fine" call): 1,264 rule-generated, per-table
  collision-checked renames in the crosswalk — the CSN family,
  PAT_/HSP_ prefixes (mid-token included), _C→_CODE, _YN→_FLAG,
  SERV_AREA — applied to the 28-proc corpus, both dictionary CSVs, all
  recorded fixtures, and the agent cassette. Scan terms extended (CSN,
  PAT_*, HSP_ACCOUNT, Chronicles, Hyperspace) so the fixture and
  cassette scans mechanically enforce the standard.
- Dictionary prose: vendor master-file refs "(EPT/18838)"-style
  stripped; "Chronicles" and "contact serial number" vocabulary
  replaced; ALL ~4,200 descriptions LLM-paraphrased in place
  (scripts/paraphrase_dictionary.py — cached, scan-verified, loud on
  failure) so no vendor documentation prose survives verbatim.
- Output filenames pinned in the crosswalk (`output_file`) — filenames
  are a corpus contract; regeneration can no longer mint strays
  (found: 7 stale reports/ files + name drift from July).
- **Raw pre-anonymization sources relocated OUT of the repo tree** to
  ~/aivia-private/ (never git-tracked — verified); anonymize scripts
  read AIVIA_RAW_SQL_DIR. Regeneration order: anonymize_sql →
  anonymize_dictionary → paraphrase_dictionary.
- Demo seed script regenerated from the clean corpus.

---

## [1.11.0] - 2026-08-16

### Added
- **`workspace` semantic-model source profile** (demo gap analysis:
  part of the offering, so built): TMDL pulled straight from the
  Fabric workspace REST API (getDefinition, TMDL format, bounded LRO
  polling) — works with or without git integration, no credentials to
  manage. Now the recommended default in config, guide, and registry.
- DEMO_SCRIPT.md rewritten as the V1 narrative with every claim
  verified: three shipped source profiles named (Snowflake removed —
  watchlist), notebook review cell as the ingestion surface, refusal
  beat restored, tenant-prep runbook + live QA gate embedded.

---

## [1.10.0] - 2026-08-16

### Added
- **The agent learns the consumption layer** (demo gap 1, ADR 0040
  consequence closed): semantic catalog gains report + measure kinds;
  new `list_report_links` tool (metric → reports built on it; report →
  executed metrics, DirectLake tables, DAX measures — deterministic
  edges, never name-matched); `get_facts` reads report/measure nodes;
  system prompt teaches the report-links exception to the lineage
  refusal. GraphView gains reports_of_metric / metrics_of_report /
  measures_of_report. Requires a `graph_edges` OneLake shortcut in the
  Eventhouse (RESUME_CHECKLISTS updated).
- **07 describes DAX** (demo gap 2): measure nodes get dictionary-
  grounded business descriptions (MEASURE_PROMPT, v3 discipline: keep
  values, ban raw identifiers), cached by content hash like steps.
- **PHI gate covers DAX**: measure expressions are scanned and redacted
  inline in 07 before any prompt (fail-safe toward redaction), and the
  literal rules gained double-quoted variants — DAX quotes strings with
  double quotes, which the SQL-shaped rules silently missed.

### Fixed
- Extractor emitted source_type "stored_procedure" but the
  input_sql_sources contract allows "procedure"/"view" (01 derives the
  same via extract_object_identity) — the direct-MERGE path would have
  failed the allowed-values invariant on first Fabric run.

---

## [1.9.2] - 2026-08-16

### Fixed
- 1.9.0 latent bug found while retiring the pbix script: two reports
  executing the same proc emitted duplicate metric_id rows into
  input_metric_names, which would fail the unique invariant in 12's
  postcondition gate. Now one row per metric — first report names it
  (friendly-cased), the rest listed in report_name for steward review.

### Changed
- collibra_lineage_match identity corrected (PBI handoff follow-up 2):
  it is publishing-side ASSET matching, not lineage. Upgrade: exact
  TMDL-derived report names from input_metric_names match
  deterministically (score 1.0; a known-but-absent asset is a miss,
  never a fuzzy guess); the _PBI-suffix heuristic is now the fallback.

### Removed
- scripts/extract_pbix_sources.py (follow-up 1): pbix-cracking is
  superseded everywhere by TMDL (git-synced or getDefinition API).
  friendly_name_from_report survives in src/governance/display_names.

---

## [1.9.1] - 2026-08-16

### Added
- Integration registry (HANDOFF_INTEGRATION_REGISTRY): the connector
  landscape as data in `src/integration_registry.py` — one record per
  tool edge (SQL Server profiles, PBI/TMDL, Collibra, Purview, dbt,
  Databricks, Snowflake) with status/tier/direction/mechanism.
  Supersedes the ROADMAP connector table and REFERENCE_ARCHITECTURE
  tier table as source of truth. Projections: generated
  `docs/architecture/INTEGRATION_MAP.md` (mermaid + table) with a
  freshness test, plus a projection test that every SHIPPED ingest
  connector is covered by the INSTALLATION_GUIDE.

---

## [1.9.0] - 2026-08-16

### Added
- **The consumption layer** (ADR 0040, HANDOFF_PBI_SEMANTIC_LAYER):
  report and measure node types with three deterministic edge types —
  report→canonical (TMDL partition lineage), report→technical
  (DirectLake pattern 5 — the Fabric-native default reads warehouse
  tables directly), report→measure (ownership), and measure→column
  (table-qualified DAX refs; unresolved refs skipped, never guessed).
  DAX is business logic and now has a home. PBI layer confirmed v1
  scope (Sunny, 2026-08-16).
- Notebook `12_ingest_semantic_models`: parses TMDL via the native
  parser into `input_report_sources`, `input_dax_expressions`, and
  `input_metric_names` (planned→ACTIVE — first writer). Two source
  profiles: `folder` (git-synced workspace / Files, no credentials) and
  `devops_git` (PAT fetched from Key Vault at run time, never stored).
- Notebook `13_publish_pbi`: `fabric_pbi.py` verdict = WIRED — metric
  descriptions published onto PBI reports via lineage-EXACT matching
  (the name-similarity guesser is deleted); pushes append to
  `gov_publish_log` (target `fabric_pbi`).
- LPG exports: `graph_report`, `graph_measure`, three new edge tables.
- End-to-end tests: TMDL fixtures → step → graph → export.

### Removed
- The ghost DIMENSION layer (zero producers since inception):
  `NodeLayer.DIMENSION`, `add_dimension_node`, `graph_dimension`,
  `graph_edge_tech2dim`, and the `dimensions` key of metric subgraphs.
  Existing deployments: drop the two empty Delta tables (upgrade note in
  05's docstring).

---

## [1.8.0] - 2026-08-16

### Changed
- **Extractor promoted to the turn-key front door** (HANDOFF_TO_DEV_EXTRACTOR
  items 1–6): `object_types` defaults to views + stored procedures;
  Marketplace customers no longer hand-export files.
- Definitions are stored **as extracted** — the sqlglot
  `strip_create_prefix` (and its naive " AS " fallback that could corrupt
  bodies) is deleted; 02's ScriptDom parses CREATE VIEW/PROCEDURE
  wrappers natively, exactly as the 790-proc corpus proved. Line endings
  normalized \r\n→\n at the extraction entry point.
- Connection profiles: `source_type: onprem_gateway | azure_direct |
  fabric_native`. Token profiles use pyodbc + AAD access token (fresh
  token per connection — the getToken() session cache breaks >1h holds);
  provider injectable for tests.

### Fixed
- extract_views wrote 5-column rows against the 7-column
  input_sql_sources contract — MERGE `UPDATE SET *` would fail; the
  extractor now emits `source_type`/`source_schema` in the file-loader's
  vocabulary, and row shape is pinned to TABLE_REGISTRY by test.

### Added
- Proc-parity tests: the 28-file golden corpus through discovery filter,
  hash/change tracking, and sql_sources production — extracted output is
  byte-identical to the file-loaded path's input to 02.
- INSTALLATION_GUIDE "Automated Extraction": prereq checklist + numbered
  runbook for all three profiles.
- SQL_SOURCES contract documents the dual-writer protocol: install path
  overwrites, extractor merges by metric_id; owner stays 01_install.

---

## [1.7.1] - 2026-08-15

### Fixed
- CI red since 1.6.0: `src/webapp` and its tests import fastapi, which was
  never declared, so CI's `pip install -e ".[dev]"` produced a collection
  error that also masked every other test. fastapi/httpx now declared in
  `dev`; new `webapp` (fastapi, uvicorn) and `marketplace` (pyjwt[crypto],
  requests) extras.
- `marketplace_host/wiring.py` imports jwt (Entra token validation) with
  PyJWT undeclared anywhere — caught before the App Service deploy
  (LISTING_CHECKLIST item) could ship without it.

### Added
- Dependency-declaration contract test
  (`tests/test_dependency_declarations.py`): every third-party import in
  src/, tests/, and marketplace_host/ must be declared in pyproject.toml;
  Fabric-runtime modules (pyspark, mssparkutils, notebookutils, pyodbc,
  clr) are exempt with named providers. Table contracts police
  declared-vs-written; this polices imported-vs-declared.

---

## [1.7.0] - 2026-08-15

### Added
- Setup-completeness contract (ADR 0039 amendment, handoff item 3): the
  third failure category — legitimate-but-degraded. Optional inputs carry
  a `remediation` field; each 03 run records their presence in the new
  `ops_setup_completeness` table (queryable by /health and admins, never
  only stdout). INSTALLATION_GUIDE gains an Optional Enrichments section,
  pinned to the registry by a docs-consistency test.

---

## [1.6.1] - 2026-08-15

### Fixed
- PHI scan: the same literal repeated within one proc (code lists copied
  across CTEs) produced duplicate finding_ids — one finding per
  (metric, rule, value) now, first occurrence's context kept. Found by
  02's postcondition gate (unique(finding_id), 219 duplicates) on the
  first full-corpus run after the .limit(50) dev cap was removed — the
  gate catching a real defect the limiter had been masking.

---

## [1.6.0] - 2026-08-15

### Added
- Precondition gates (ADR 0039): every numbered notebook checks its required
  input tables exist (and are non-empty where the contract demands) BEFORE
  reading — failures are admin-actionable messages naming the producing
  notebook and the violated contract id, never a pyspark stack trace.
  Registry-driven via new `consumers`-derived `required_inputs`; new
  registry vocabulary `must_be_nonempty` / `optional_input`.
- Gate-integrity contract in the readiness gate: required checks
  (`REQUIRED_CHECKS` incl. dictionary_coverage) may FAIL but can never
  silently disappear; local replay now enforces all four checks.
- `ParsedSQL.extraction_suppressed`: the nine ScriptDom AST-walk swallows
  now count what they suppress; the total is persisted per proc in
  ops_parse_results and reported by notebook 02 — "parse success" can no
  longer hide lost table/column refs.
- FabricAgentClient `token_provider` callable + one forced-refresh retry on
  401/403; notebook 08 uses it, so >1hr description runs survive token
  expiry instead of failing as fake content errors.
- Silence contract in CI: ruff BLE001/S110/S112 across src, tests,
  notebooks, scripts, devtools and all root *.Notebook folders — every
  surviving broad `except` carries an explicit policy annotation.

### Fixed
- Collibra adapter: publish() now writes the Description attribute (was
  name-only — descriptions silently dropped while reporting SUCCESS);
  `_find_asset` failures no longer read as "absent" (was creating duplicate
  assets on transient errors); publish_bulk routes per-record so
  descriptions land; Publisher.publish_all failure yields per-record
  FAILED results instead of an empty result indistinguishable from
  "nothing to publish".
- 06_validate: dictionary_coverage can no longer vanish from the deployment
  gate; ops_build_summary append no longer silently degrades to
  history-destroying overwrite; parse outcome reads are loud.
- 02_parse always writes all outcome tables (even empty) — absence now
  unambiguously means "02 never ran"; removed dead sqlglot fallback branch
  and a leftover `.limit(50)` dev cap on production parsing.
- 07 hard-stops without steward-reviewed PHI findings (inline rescan that
  dropped dispositions removed); 08 stops on Collibra connection failure;
  extract_views MERGE fixed (comment-in-f-string made it fail 100% and
  blind-append duplicates); 10_ingest distinguishes listing failure from
  empty directory; steward/dictionary loaders check table existence
  instead of swallowing read errors before overwrites.
- builder: ambiguous bare-name table refs resolve deterministically
  (sorted) with a warning, instead of set-iteration-order lineage.

### Removed
- Ghosts: draft.Notebook (reintroduced the fixed 2026-08-09 column-shift
  bug against a production table), dead `load_scriptdom()` + stale parser
  copy, scripts/validate_dictionary.py always-green stub,
  scripts/run_full_pipeline.py (superseded), duplicate
  export_test_fixtures copy, dead `metrics.catalog_path` config.

---

## [1.5.1] - 2026-08-13

### Fixed
- Validation step 6 is a real traversal: the shallow 2-hop check
  false-negatived metrics whose entry transform assembles from temp
  tables (ADR 0018's disease in a second location — caught by the
  admin dashboard's first render). Validator gains its first test
  suite, with the live regression as fixture.

---

## [1.5.0] - 2026-08-12

### Added
- ADR 0035 agent stack in src/orchestrator: tools (find/read/list/
  verify), function-calling agent loop with code-stamped Basis,
  decision-shape telemetry (TurnEvent/FeedbackEvent, OneLakeJsonlSink)
- src/webapp: chat surface + SaaS fulfillment endpoints (one App
  Service); src/marketplace Phase T2 wiring (token provider, JWKS
  verifier, durable store)
- Admin telemetry contracts: gov_publish_log, gov_turn_events,
  gov_feedback_events; src/governance/publish_log.py;
  src/steps/agent_events.py (notebook 10 ingest)
- Stratified plurality retrieval (ADR 0032 amendment); metric facts
  carry business_name/report fields end to end

### Removed
- Typed-intent dialogue machinery (ADR 0034 superseded by 0035)

---

## [1.4.3] - 2026-08-09

### Added
- src/steps/semantic_catalog.py + output_semantic_catalog contract
  (ADR 0030 L3): search-document build step for the Eventhouse
  resolution catalog

---

## [1.4.2] - 2026-08-08

### Added
- Business-friendly metric names: input_metric_names (qualified or
  unambiguous bare metric_id -> business_name, with provenance) applied
  to canonical nodes by 03, flowing to output_metric_logic.business_name
  and graph_canonical.businessName; both agents' instructions search and
  display them; local resolution and retrieval match them;
  extract_pbix_sources --names-csv emits mappings from report lineage.
  Ambiguous bare names are skipped and reported, never guessed
- src/llm_client.py — Azure-aware LLM doorway: Azure endpoints get
  `api-key` auth + api-version handling (query strings survive the path
  join); OpenAI endpoints get Bearer. 07 and devtools both route
  through it; 07's describe now sends the same system prompt as the
  local fixtures generation
- PHI wiring end to end (ADR 0025): parse_step scans every source
  (parse outcome irrelevant) and carries steward dispositions +
  first_seen across runs; 02 writes ops_phi_findings (contract now
  active, single-writer enforced); 07 redacts fragments from the
  findings table before any prompt — with an inline-scan fallback so
  the gate never silently disappears
- make_golden_snapshot notebook: copies (CTAS) the rebuild-expensive
  state (inputs, description cache, PHI dispositions, error history)
  to golden_ tables + manifest; restore = clone back + rerun 02->07
- PHI / hardcoded-literal scanner (ADR 0025, src/phi_scan.py): five
  deterministic rules, span-claiming to prevent double-flags, IN-lists
  flag every member, steward dispositions survive re-scans via stable
  finding ids; redaction wired into describe_local's prompt boundary.
  Fixture blast radius: 278 findings, 102/432 steps affected; committed
  descriptions verified clean (zero long numerics leaked)
- Deployment pre-flight validator (scripts/validate_deployment.py):
  config, llm block (incl. Azure api-version check), mandatory
  dictionary shape from the table contracts, sql_input, ScriptDom DLL,
  package import — every failure states the fix

---

## [1.4.1] - 2026-08-06

### Added
- Full-corpus description fixtures (ADR 0019 first pass): 432 step + 28
  metric descriptions generated locally over the recorded fixtures,
  leak-gated, committed for offline replay
- Marketplace fulfillment scaffold (ADR 0028): subscription state machine,
  webhook event contract, and JWT claim validation as pure library code
  (src/marketplace/) with tests
- Governance lifecycle design (ADRs 0021-0024) with contract drafts:
  gov_certification_events, gov_usage_events, gov_personal_definitions
- PHI-scanning and error-lineage designs (ADRs 0025-0026) with contract
  drafts: ops_phi_findings, ops_runtime_error_events
- Ownership attribution design (ADR 0027) + Entra ID feasibility findings;
  Marketplace timing decision (ADR 0028); dimension-layer activation
  design (ADR 0029)

### Changed
- Metric description prompt grounds the purpose sentence strictly in step
  descriptions and bans benefit-filler ("supports decision-making") —
  smoke-run QA showed invented purposes on a date-dimension proc
- Leak-gate scan terms support `~cs` (case-sensitive) annotation for org
  terms that are common English words ('Clarity' vs "ensuring clarity");
  describe_local quarantines gate-failed output instead of discarding the
  paid LLM calls

---

## [1.4.0] - 2026-08-05

### Added
- **Bottom-up description generation (ADR 0019):** src/descriptions.py walks
  the calculation DAG in topological order — every CTE step described from
  its own sql fragment plus its dependencies' descriptions, then each
  metric composed from its root steps (summaries of summaries). Content-hash
  cache (ops_description_cache) makes re-runs incremental. 07 rewritten
  around it: direct OpenAI-compatible endpoint (customer's Azure OpenAI),
  no more Data-Agent circularity; enriches graph_nodes + output_metric_logic
- Transformation LPG export carries the step description; the local agent's
  resolution payload gains the calculation-step catalog
- devtools/describe_local.py: leak-gated local generation over recorded
  fixtures; ask_graph.py auto-loads the results

---

## [1.3.1] - 2026-08-05

### Changed
- **Generator-compatibility export (ADR 0020):** the Fabric NL2GQL generator
  proved non-deterministic against instructions (filtered bare `name` with a
  qualified reference; always single-hop CALCULATED_BY chains), so the LPG
  export now targets its habits: `Metric.name` is schema-qualified (==
  metricId, bare name moved to `bareName`), and `graph_edge_c2t` carries the
  full metric→step closure (raw roots stay in graph_edges). The generator's
  habitual query is now the correct query.

---

## [1.3.0] - 2026-08-04

### Added
- **graph_edge_uses_table** — derived metric→table closure edges (ADR 0018):
  the full DEPENDS_ON transitive closure precomputed at export, so
  table↔metric questions are single-hop and complete by construction.
  Count-oracle tests pin the certified answer-key numbers (13 readers of
  HOSPITAL_ENCOUNTERS, 32 tables under reports.USP_Severe_Sepsis, …)
- ADRs 0017–0019: resolve-then-traverse agent retrieval, materialized
  closure edges, CTE descriptions bottom-up
- Error KB: delta_schema_mismatch_on_upgrade (contract evolution vs.
  existing Delta schema; overwriteSchema on snapshot writes)

### Changed
- Graph agent instructions rewritten resolution-first (ADR 0017): catalog
  fetch + semantic matching by the LLM, traversal only with certified keys,
  USES_TABLE preferred for lineage questions, honest Basis footer
- All snapshot-table overwrites carry overwriteSchema (05 was the straggler;
  02/06/utilities aligned)
- src.__version__ now derives from package metadata — pyproject is the
  single version home (was hand-maintained and stale at 1.1.0)

---

## [1.2.2] - 2026-08-04

### Added
- graph_canonical LPG export carries schema-qualified metricId (ADR 0015) —
  bare metric names collide across schemas and were silently collapsing in
  Graph Model metric listings
- Error KB: CapacityLimitExceeded (Fabric smoothing/throttling triage)
- Agent instructions (both): case-insensitive keyword matching rules;
  graph agent gains completeness rule (no partial lists presented as complete)

---

## [1.2.1] - 2026-08-03

### Added
- Error KB: stale_wheel_version signature (src imports but newer submodule
  missing — verify wheel version/attachment, restart the session)
- devtools: local agent stand-in (ask.py), grounding evals with recorded
  cassette (12/12), .env support — none shipped in the wheel
- Recorded ScriptDom fixtures (28 metrics) replayed in CI

### Fixed
- Dead unreachable code in sql_extractor (leftover after refactor)
- Unused variable in devops_tmdl TMDL parsing
- Lint clean across src/ and tests/ (ruff)

---

## [1.2.0] - 2026-08-02

### Added
- Data contracts for all Delta tables (`src/schemas.py` TABLE_REGISTRY): shape,
  semantics, single-writer ownership, consumers, invariants, cross-table
  relations — enforced against code ground truth by contract tests
- Generic invariant/relation checker (`src/invariants.py`); wired into the
  06_validate deployment gate and per-notebook postcondition gates
- Pure pipeline step functions (`src/steps/`): parse, build_graph,
  metric_logic, export, readiness — full 02→05 pipeline runs offline with
  no Spark/Fabric; notebooks reduced to thin callers
- SQL object identity module (`src/parser/identity.py`): CREATE PROCEDURE and
  CREATE VIEW identity, case folding (ADR 0016), duplicate detection
- Recovered governance modules: cross-run error log with regression detection
  (ops_error_log, appended by 02_parse) and steward assignments
  (gov_steward_assignments via manage_stewards utility, applied by 03)
- Crosswalk anonymization engine (`src/anonymization.py`) + export_test_fixtures
  utility notebook with proprietary-term leak gate (record-replay fixtures)
- AgentBackend protocol (`src/agent_backend.py`): Fabric agent + replay
  cassette backends, one-home description prompt and refusal vocabulary
- New TABLE_TO_COLUMN edges (columns reachable by traversal) exported to
  graph_edge_tab2col (9th LPG table)
- Local pipeline runner (`scripts/run_pipeline_local.py`) and grounding-eval
  harness (devtools/, never shipped)

### Changed
- Technical node IDs and all identifier matching case-folded to uppercase
  (ADR 0016) — Caboodle PascalCase dictionaries now match; graph rebuilds on
  next pipeline run
- Purview display names use schema-qualified metric_id (ADR 0015)
- 01_install: duplicate metric identities and case-variant dictionary
  duplicates now BLOCK with per-file listings (was silent last-wins)
- 06_validate: readiness decision extracted to a pure function; gains data
  contract invariants and dictionary schema-ambiguity gates
- 02→03 payload contract unified in src/graph/serialization.py (round-trip
  tested); column_refs now survive the boundary

### Fixed
- org_config.example.yaml: graph_edges was "Tables/graph_edges" (broken
  write for any customer copying the example); stale tracking_table name
- Dead-code detector now scans root *.Notebook folders — the blind spot that
  wrongly purged working governance modules in July

---

## [1.1.0] - 2026-07-26

### Added
- `TableRef` data class: `database`, `schema`, `table` with `qualified_name` and `full_name` properties
- Default schema population: `dbo` when schema omitted (e.g., `Clarity..PATIENT` → `Clarity.dbo.PATIENT`)
- `_find_tech_node_id()` in graph builder: exact match then fuzzy match by table name
- `_table_name_index` for fast table lookup regardless of schema
- `_extract_table_ref()` in ScriptDom: reads all 4 parts from SchemaObject
- PHI protection rule in Data Agent instructions
- Broad search across all columns for topic-based agent queries
- CHANGELOG.md with full release history

### Changed
- Technical node IDs use `schema.table` format (e.g., `tech:dbo.PATIENT` instead of `tech:PATIENT`)
- `CTEInfo.table_refs` and `ParsedSQL.final_select_tables` are now `list[TableRef]` instead of `list[str]`
- `TableRef.__eq__` supports string comparison for backward compatibility
- Graph builder `add_technical_node()` accepts `schema` and `database` parameters
- HIPAA section in security whitepaper expanded with 4 protection layers

### Breaking Changes
- Graph node IDs changed: `tech:PATIENT` → `tech:dbo.PATIENT`. Existing graph data must be rebuilt.
- `add_technical_node()` signature changed: new `schema` and `database` parameters (with defaults)

---

## [1.0.0] - 2026-07-25

First production release. Core SQL Intelligence Agent for Microsoft Fabric.

### Core Engine
- **99%+ parse accuracy** on 1,337 enterprise T-SQL files (stored procedures and views)
- **Option B architecture:** ScriptDom extracts structure directly from AST — no sqlglot in the parsing path, zero T-SQL compatibility issues
- ScriptDom loaded via pythonnet CoreCLR runtime in Fabric notebooks
- Three-layer knowledge graph: Canonical (metrics) → Transformation (SQL logic) → Technical (source tables)
- `metric_logic` flattened table for single-query Data Agent access
- Multi-statement SQL support: CTE chains, temp table dependencies, UNION ALL
- Full Unicode whitespace normalization at entry point (handles `\r\n`, `\r\r\n`, `\xa0`, BOM, zero-width spaces)

### Pipeline
- Split into 5 independent notebooks (02_parse → 03_build_graph → 04_build_metric_logic → 05_validate)
- Each notebook is self-contained with its own setup cell
- Delta table checkpoints between stages — only rerun what changed
- Pipeline validation checks 6 steps per metric with health reporting

### Data Agent
- Agent instructions grounded in `metric_logic` table (no hardcoded answers)
- PHI protection rule: never output personal names, MRNs, addresses
- Broad search across metric_name, calculation_logic, and source_tables
- Business user and developer response personas
- Admin commands: /errors, /coverage, /admindash

### Error Handling
- Error classifier with user-facing categories: `no_query`, `complex_sql`, `parse_failure`, etc.
- Each error includes `user_explanation` and `suggested_action` columns
- `parse_errors` Delta table with full context for developer review

### Code Quality
- 87 automated tests (pytest) organized to mirror src/ structure
- Dead code detector in CI — 0 unreachable modules
- Centralized schema contracts for all 13 Delta tables
- All dependencies pinned to exact versions
- Wheel builds clean: `aivia_sql_intelligence-1.0.0-py3-none-any.whl`

### Documentation
- Customer-facing deployment guide (DEPLOYMENT_GUIDE.md)
- Security whitepaper with HIPAA, GDPR, SOC 2 sections
- Privacy policy and terms of service (live at aiviaapp.com)
- Fabric readiness checklist for Marketplace submission
- src/README.md with pipeline flow and module-to-test mapping

### Business
- Registered as ISV on Microsoft Partner Center
- Commercial Marketplace program enrolled
- Pricing: $2,000/month, $21,600/year (10% discount), 30-day free trial
- Logo created (4 sizes for Marketplace listing)
- Legal: privacy policy, terms of service, email aliases configured

---

## [0.9.0] - 2026-07-23

Pre-release. ScriptDom integration and pipeline validation.

### Added
- ScriptDom via pythonnet in Fabric — 99% parse rate (788/790 procs, 0 errors)
- `parse_with_scriptdom()` — Option B: extract structure directly from AST
- `normalize_sql_whitespace()` — single entry point for whitespace cleanup
- `parse_extracted_queries()` — shared multi-statement merging logic
- Pipeline validation notebook (validate_pipeline.py)
- Debug notebooks for root cause analysis

### Fixed
- Agent "no documented calculation logic" — root cause: `\r\n\t` in stored SQL fragments
- Temp table dependency tracking — `__temp_X__` naming mismatch between cleanup and comparison
- Tokenizer errors — `\r\r\n` broke comment stripping regex
- Leading semicolons — ScriptDom preserved `; WITH` that sqlglot rejected
- `TRY_PARSE()` and ODBC `{escape}` syntax — rewrites for sqlglot compatibility
- Non-breaking spaces (`\xa0`) from SSMS copy-paste

---

## [0.8.0] - 2026-07-21

ScriptDom breakthrough. Parse rate jumped from 87% to 99%.

### Added
- ScriptDom DLL loading via pythonnet in Fabric notebooks
- AST walker using .NET reflection (can't subclass `TSqlFragmentVisitor` in pythonnet)
- `extract_with_scriptdom()` — extracts SELECT/INSERT...SELECT from stored procedures
- `_get_fragment_text()` — reconstructs SQL from token stream

### Changed
- Parser strategy: ScriptDom for extraction, sqlglot for structural analysis
- Moved from text-based extraction to native parser

---

## [0.7.0] - 2026-07-20

Product strategy and infrastructure.

### Added
- AIVIA LLC registered
- Website live at www.aiviaapp.com
- Founders Hub application submitted
- Product positioning docs, security whitepaper draft
- GPS analogy: "Microsoft built the highway and car. AIVIA builds the map."

---

## [0.6.0] - 2026-07-19

Data Agent integration and governance features.

### Added
- Fabric Data Agent client (MCP JSON-RPC protocol)
- Steward assignment manager (individual, bulk, by pattern)
- Error log with regression detection across runs
- Usage tracking (query events, user nodes, weight tracking)
- Power BI report description updater
- Fabric lineage API client

---

## [0.5.0] - 2026-07-18

Adapters and catalog integration.

### Added
- Collibra adapter (create/update assets, bulk operations)
- Purview adapter (Data Map REST API)
- Publisher dispatcher (multi-adapter orchestration)
- Metadata generator (graph → MetadataRecord conversion)
- Product strategy: BYOT model, bundled tiers, Bulk Loader wedge

---

## [0.4.0] - 2026-07-17

SQL extraction improvements.

### Added
- LLM-based SQL extractor (multi-backend: OpenAI, Azure, Fabric AI)
- Proc normalizer (temp table → CTE rewriting)
- Parsing rules engine (regex + AST rules)
- sqlparse-based query extraction with inclusion model

### Changed
- Parse rate: 64% → 87% through successive extraction improvements

---

## [0.3.0] - 2026-07-15

View extractor and data dictionary.

### Added
- SQL Server view extractor via JDBC/pyodbc
- Change tracking with SHA-256 hashing
- Clarity data dictionary loader
- Orchestrator v2 with dictionary support

---

## [0.2.0] - 2026-07-13

Graph builder and traversal.

### Added
- Three-layer graph builder (canonical, transformation, technical)
- BFS/DFS graph traversal
- Edge wiring: canonical → transform → technical
- POC setup notebook with seed data

---

## [0.1.0] - 2026-07-11

Initial scaffold.

### Added
- Project structure: src/, tests/, notebooks/, docs/
- Config loader (YAML)
- Data models (GraphNode, GraphEdge, NodeLayer, EdgeType)
- Basic SQL parser with sqlglot
- CI/CD with GitHub Actions (lint, test, security audit)
