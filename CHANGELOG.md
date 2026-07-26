# Changelog

All notable changes to AIVIA SQL Intelligence Agent are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

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
