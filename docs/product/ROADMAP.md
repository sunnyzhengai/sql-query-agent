# Product Roadmap

Phased plan for taking the **Data Empowerment Suite** from internal tool to Microsoft Marketplace product.
No fixed dates — phases have exit criteria, not deadlines. Update this as you go.

## Product Components

| Component | Short Name | Description | Tier |
|-----------|-----------|-------------|------|
| **Metadata Sync** | "sync" | Generate and push metadata to Purview/Collibra. Bulk, incremental, or triggered by report changes. | Basic |
| **GraphRAG Engine** | "engine" | Knowledge graph + Data Agent grounding for certified, traceable answers. | Pro |

Both components live in a single repo (`sql-query-agent`) and ship as one `.whl` package.

## Data Source Tiers (validated by coworker feedback 2026-07-21)

| Tier | Data Source | Parser | Market |
|------|------------|--------|--------|
| **Tier 1** | Fabric-native (semantic models, lakehouses, SQL endpoints) | ScriptDom (T-SQL) | Fabric-first customers, greenfield |
| **Tier 2** | On-prem SQL Server (stored procs, views) | ScriptDom (T-SQL) | Healthcare, finance, legacy enterprise |
| **Tier 3** | On-prem Oracle (PL/SQL packages, views) | ANTLR PL/SQL grammar | Large enterprise, government |

**Tier 1 is the priority.** Coworkers asked: "Can we use this against native Fabric reports and data models?" — this is the first use case. No on-prem gateway needed, everything stays in Fabric.

**Tier 2 shares the same parser** (ScriptDom) as Tier 1 since Fabric SQL is T-SQL. The difference is the data source connection (Fabric gateway to on-prem SQL Server).

**Tier 3 requires a separate grammar** (ANTLR PL/SQL or Oracle's own parser). This is a future expansion, not Phase 1.

---

## Phase 0: Foundation
**Status: DONE**

Core library, graph model, and adapter scaffolding.

### What was built
- [x] Three-layer graph model (canonical, transformation, technical, dimension)
- [x] SQL parser using sqlglot (T-SQL dialect)
- [x] Graph builder with incremental node/edge construction
- [x] Graph traverser for metric subgraph extraction
- [x] Data dictionary loader
- [x] End-to-end pipeline (`build_graph()`)
- [x] Config-driven portability (`org_config.yaml`)
- [x] View extractor with SQL Server discovery + change tracking
- [x] Catalog adapter scaffolding (CatalogAdapter Protocol, Purview + Collibra adapters)
- [x] Metadata generator (graph nodes -> catalog-agnostic MetadataRecords)
- [x] Publisher orchestrator (config-driven, multi-adapter)
- [x] Pydantic models for all data structures
- [x] 45 passing tests (parser, builder, traversal, pipeline, adapters)
- [x] Sample data and local run script
- [x] Fabric orchestrator notebook
- [x] Data Agent grounding instructions

### Docs created
- [x] `docs/architecture/ARCHITECTURE.md`
- [x] `docs/architecture/USER_FLOW.md`
- [x] `docs/development/SETUP.md`
- [x] `docs/development/FABRIC_SETUP.md`
- [x] `docs/development/TESTING.md`
- [x] `docs/product/MARKETPLACE_CHECKLIST.md`
- [x] `docs/product/PRODUCT_POSITIONING.md`
- [x] `docs/product/ROADMAP.md` (this file)
- [x] `notebooks/data_agent_instructions.md`

### Exit criteria: MET
- Core pipeline works end-to-end (SQL in -> graph out -> traversal works)
- Adapter pattern scaffolded with tests
- Architecture and product strategy documented

---

## Phase 1: Metadata Sync MVP (Wedge)
**Status: IN PROGRESS**

Get Metadata Sync working end-to-end with real data against Purview/Collibra.

### Code quality (DONE)
- [x] Add Python `logging` module throughout library (12 modules)
- [x] Pin all dependency versions in pyproject.toml (`~=` compatible release)
- [x] Run `pip-audit` — no vulnerabilities in direct dependencies
- [x] Audit for print statements — zero in `src/`, all in scripts/notebooks where they belong

### Parser (DONE — ScriptDom, production-grade)
- [x] **ScriptDom via pythonnet: 99% parse rate (788-790/790), 0 errors**
- [x] Microsoft's native T-SQL parser running directly in Fabric notebooks
- [x] DLL loaded from Lakehouse Files/libs/ via pythonnet CoreCLR
- [x] Manual AST walk extracts SelectStatement / InsertStatement nodes verbatim
- [x] sqlglot parses each extracted query for structural analysis
- [x] sqlparse-based fallback if ScriptDom unavailable
- [x] Core design principle: native parsers for each dialect (ScriptDom, ANTLR)
- [x] 67 regression tests preventing yoyo between approaches
- [x] Persistent error log with regression detection across runs
- [x] Validated against 790 real Epic Clarity stored procedures in 24 minutes

### Graph & traversal (DONE)
- [x] Three-layer graph model with full dependency chain traversal
- [x] Multi-statement proc support (temp tables → CTE entries with dependencies)
- [x] `__final_select__` synthetic node for tables only in final SELECT
- [x] 400K+ nodes, 12K+ edges from real data
- [x] Full pipeline tested end-to-end (parse → graph → traverse → metadata)

### Data Agent (DONE)
- [x] Fabric Data Agent working with graph tables
- [x] Persona-based responses (business, developer, admin)
- [x] Agent instructions: self-contained knowledge base (metrics, admin, setup, troubleshooting)
- [x] Data Agent API working via MCP protocol (JSON-RPC)
- [x] Programmatic description generation via agent API
- [x] SQL-to-business translation table in instructions

### Description generation (DONE)
- [x] OpenAI-based summary generator (transform + canonical summaries)
- [x] Combined summary generator (one LLM call per metric, 3x faster)
- [x] Data Agent API-based description generator (best quality)
- [x] Descriptions stored in graph_nodes description field + properties.summary

### Adapters & integrations (BUILT, WAITING ON ACCESS)
- [x] Collibra adapter scaffolded (REST API, bulk publish)
- [x] Purview adapter scaffolded (Data Map REST API, Atlas entities)
- [x] PBI report description updater (Fabric REST API PATCH)
- [x] Fabric lineage API client (trace report → dataset → source tables)
- [x] Metadata Sync notebook (reads graph, generates records, pushes to catalogs)
- [x] Fabric Agent client (MCP protocol, auto-discovers tool name)

### Blocked on access
- [ ] Get Collibra service account → test Collibra push (work admin)
- [ ] Get Purview Data Curator role → test Purview push (own tenant when Fabric available)
- [ ] Test PBI description updates against dev workspace
- [ ] Test Fabric lineage API against PBI workspace (needs PBI Admin — own tenant)

### Enterprise readiness (PARTIALLY DONE)
- [ ] Business-friendly metric names from PBI lineage (replace proc names)
- [x] Steward assignment module (Delta table + pattern matching + agent commands)
- [x] Usage tracking module (user nodes, queried_by edges, usage weight)
- [x] Admin commands in agent (/admindash, /stewards, /errors, /coverage, /health)
- [x] Persistent error log with regression detection
- [x] CI/CD pipeline (GitHub Actions: lint + test + build + security audit)
- [ ] Automated refresh via Fabric Pipeline (document in admin guide)
- [ ] Secrets management via Azure Key Vault (replace notebook API keys)

### Product readiness (DONE)
- [x] README.md, LICENSE (MIT), pyproject.toml complete
- [x] Security whitepaper written
- [x] Website live (www.aiviaapp.com)
- [x] Founders Hub submitted (2026-07-20)
- [x] Partner Center account created (verification pending)
- [x] Architecture document with native parser design principle
- [x] Launch plan with tiered submission approach

### Scale testing (DONE)
- [x] **ScriptDom: 99% parse rate on 790 procs (0 errors, 24 min)**
- [x] 67 regression tests (extraction, parsing, real procs, edge cases)
- [x] Inspection table (extraction_inspection) for manual validation
- [ ] Golden file tests for 3-5 critical real-world queries
- [ ] Test bulk catalog push with 50+ records

### Exit criteria
- [x] **Can parse 790 real SQL queries with 99% success and 0 errors**
- [x] Full pipeline works end-to-end (parse → graph → traverse → metadata → descriptions)
- [x] Data Agent answers metric questions correctly
- [ ] Can push metadata to at least one catalog (Purview or Collibra) via API
- [ ] PBI report descriptions can be updated programmatically
- [x] All tests pass (67/67), no print statements in library code

### Checklist items satisfied
- MARKETPLACE_CHECKLIST §2: Code Standards — DONE
- MARKETPLACE_CHECKLIST §2: Testing — DONE (67 regression tests)
- MARKETPLACE_CHECKLIST §3: Security — DONE (whitepaper written)

---

## Phase 2: Business Setup
**Status: NOT STARTED**

Legal entity and Microsoft partner registration. Can run in parallel with Phase 1.

### Do
- [ ] Establish business entity (LLC)
- [ ] Business bank account
- [ ] Business email domain
- [ ] Join Microsoft AI Cloud Partner Program
- [ ] Create publisher account in Partner Center
- [ ] Complete identity verification (3-5 business days)
- [ ] Apply to Microsoft for Startups Founders Hub (free, self-paced)
- [ ] Review employment contract for invention assignment clauses
- [ ] Consider HR disclosure for written release/waiver

### Exit criteria
- [ ] Legal entity exists with bank account
- [ ] Partner Center publisher account verified
- [ ] Founders Hub application submitted
- [ ] Conflict of interest documented and mitigated

### Checklist items satisfied
- MARKETPLACE_CHECKLIST §1: Business Setup (all items)

---

## Phase 3: Production Hardening
**Status: NOT STARTED**

Make the codebase enterprise-ready for Marketplace certification.

### Build
- [ ] CI/CD pipeline (GitHub Actions): lint + test on every push
- [ ] Build `.whl` artifact in CI
- [ ] Type hints throughout (`mypy` clean)
- [ ] Input validation/sanitization audit on SQL parsing
- [ ] Verify no hardcoded secrets, paths, or org-specific details
- [ ] Ensure no Fabric-specific imports in core library
- [ ] Add structured error handling (not bare exceptions)

### Package
- [ ] Validate `pyproject.toml` metadata (author, license, version, description)
- [ ] Build and verify `.whl` and `.tar.gz` with `twine check`
- [ ] Add `LICENSE` file (MIT or Apache 2.0)
- [ ] Test `.whl` install in clean Fabric Environment

### Docs
- [ ] Write `README.md` (installation, quick-start, configuration)
- [ ] Ensure all public functions/classes have docstrings
- [ ] Review and update all docs under `docs/`

### Exit criteria
- [ ] CI/CD green on every push (lint + test + build)
- [ ] `.whl` installs cleanly in a fresh Fabric Environment
- [ ] `mypy` and `ruff` pass with zero errors
- [ ] `pip-audit` clean
- [ ] README exists with clear getting-started instructions

### Checklist items satisfied
- MARKETPLACE_CHECKLIST §2: Code Quality (all items)
- MARKETPLACE_CHECKLIST §8: Development Guardrails (all items)

---

## Phase 4: Marketplace Submission
**Status: NOT STARTED**

Prepare everything Microsoft needs to evaluate and list the product.

### Security docs
- [ ] Write Security Whitepaper (1-2 pages)
- [ ] Create Data Flow Diagrams
- [ ] Publish Privacy Policy on business website
- [ ] Publish Terms of Use / EULA on business website

### Listing assets
- [ ] Product name, summary, detailed description
- [ ] Logo (48x48, 90x90, 216x216, 255x115)
- [ ] 3-5 screenshots of the tool in action
- [ ] 5-minute demo video (optional but recommended)
- [ ] Pricing plans defined (Basic + Pro tiers, flat-rate)
- [ ] Categories and search keywords

### Technical integration
- [ ] Set up personal Fabric/Azure tenant (separate from work)
- [ ] Create reviewer sandbox with sample data pre-loaded
- [ ] Create test account credentials for Microsoft reviewers
- [ ] Write Tester's Guide (step-by-step for reviewers)
- [ ] Integrate with Marketplace Fulfillment API (subscription lifecycle)
- [ ] Build landing page for subscription activation
- [ ] Configure Entra ID (SSO) support

### Submit
- [ ] Submit offer in Partner Center
- [ ] Respond to any certification feedback
- [ ] Iterate until approved

### Exit criteria
- [ ] Offer approved and listed on Microsoft Commercial Marketplace
- [ ] At least one plan (Basic) is transactable

### Checklist items satisfied
- MARKETPLACE_CHECKLIST §3: Security & Compliance (all items)
- MARKETPLACE_CHECKLIST §4: Listing Assets (all items)
- MARKETPLACE_CHECKLIST §5: Technical Integration (all items)
- MARKETPLACE_CHECKLIST §6: Reviewer's Experience (all items)

---

## Phase 5: Post-Launch & Pro Tier
**Status: NOT STARTED**

Expand the product after the Basic tier is live and generating feedback.

### Second adapter
- [ ] Wire up the adapter not done in Phase 1 (Collibra or Purview)
- [ ] Test with at least one customer or POC environment

### Pro tier: Chat Data Agent
- [ ] Package the Data Agent grounding as a configurable feature
- [ ] Add usage weight tracking (query counts on canonical nodes)
- [ ] Add steward notification workflow for Path B (unknown questions)
- [ ] Add Purview report discovery (search for existing reports matching user questions)
- [ ] Row-level security for personalized access (surgeon-sees-own-data pattern)
- [ ] Add Pro plan to Marketplace listing

### Entra ID Security & Access Control
- [ ] Integrate with Microsoft Entra ID to identify the user asking questions
- [ ] Add `security_groups` property to canonical nodes (which AD groups can access)
- [ ] Agent checks user's AD group membership before answering
- [ ] Access denied response: "You don't have access to this data. Request sent to [owner] for approval."
- [ ] Access request workflow: denied requests logged, sent to metric owner (steward) for approval
- [ ] Approved requests expand the access list automatically
- [ ] Row-level security (RLS): same metric, different data based on user identity
  - Example: surgeon sees only their own FCOTS; Medical Director sees department-wide
- [ ] Access request patterns feed the flywheel: demand signals for cross-department data sharing
- [ ] Audit trail: who asked, what was denied/approved, when

### AI support bot
- [ ] Build knowledge graph of product documentation
- [ ] Deploy self-service support agent (eat your own dogfood)
- [ ] Target: handle 80%+ of common questions automatically

### Growth
- [ ] Activate Marketplace Rewards
- [ ] Track revenue toward Azure IP co-sell status
- [ ] Collect customer testimonials / case studies
- [ ] Evaluate open-source core + paid managed experience option
- [ ] Evaluate Azure Managed Application deployment (alternative to .whl)

### Exit criteria
- [ ] Both adapters (Purview + Collibra) working in production
- [ ] Pro tier listed with Agent features
- [ ] At least 3 paying customers

### Checklist items satisfied
- MARKETPLACE_CHECKLIST §7: Post-Launch Maintenance (all items)

---

## How to Use This Roadmap

1. **Work on one phase at a time** (Phases 1 & 2 can overlap since they're independent)
2. **Update checkboxes** as items are completed
3. **Move items between phases** if priorities shift — this is a living document
4. **Don't skip exit criteria** — each phase builds on the last
5. **Reference MARKETPLACE_CHECKLIST.md** for detailed requirements behind each item
