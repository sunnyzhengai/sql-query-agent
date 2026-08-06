# Changelog

All notable changes to AIVIA SQL Intelligence Agent are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

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
