# Product Roadmap

> **This document is the single source of truth for project status.** No other
> document carries live checkboxes or current metrics. Rationale for decisions
> lives in [docs/decisions/](../decisions/README.md) (ADRs). Frozen snapshots
> (e.g. [MARKETPLACE_PIVOT.md](MARKETPLACE_PIVOT.md)) are historical and
> banner-marked as such.

Phased plan for taking the **Data Empowerment Suite** from internal tool to
Microsoft Marketplace product. No fixed dates — phases have exit criteria, not
deadlines. Update this as you go.

**Last reconciled:** 2026-08-02

## Canonical Numbers

Cite these from other documents by reference — do not copy values.

| Metric | Value | As of |
|---|---|---|
| Package version | 1.1.0 (`pyproject.toml`) | 2026-08-02 |
| Parse rate (latest full corpus) | 1,337 / 1,344 procs (99.5%), 0 errors | 2026-07-25 |
| Earlier validation run | 788 / 790 procs (99.7%), 24 min | 2026-07 |
| Test suite | 186 tests collected (`pytest --collect-only`) | 2026-08-02 |
| Pipeline notebooks | 01_install … 09_publish_purview (9 numbered) | 2026-08-02 |
| Pricing | $2,000/mo, $21,600/yr, 30-day free trial | 2026-07-25 |

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

**Tier 1 is the priority** (see [ADR 0008](../decisions/0008-ship-tier-1-first.md)).
Tier 2 shares the ScriptDom parser; Tier 3 requires a separate grammar
([ADR 0001](../decisions/0001-native-parsers-per-dialect.md)).

---

## Phase 0: Foundation
**Status: DONE**

Core library, graph model, and adapter scaffolding.

- [x] Three-layer graph model (canonical, transformation, technical, dimension)
- [x] SQL parser, graph builder, traverser, dictionary loader, end-to-end pipeline
- [x] Config-driven portability (`org_config.yaml`)
- [x] View extractor with SQL Server discovery + change tracking
- [x] Catalog adapter scaffolding (CatalogAdapter protocol, Purview + Collibra)
- [x] Metadata generator + publisher orchestrator
- [x] Pydantic models, tests, sample data, Fabric orchestrator notebook
- [x] Architecture and product docs written

### Exit criteria: MET
Core pipeline works end-to-end; adapter pattern scaffolded with tests;
architecture and strategy documented.

---

## Phase 1: Metadata Sync MVP (Wedge)
**Status: IN PROGRESS**

Get Metadata Sync working end-to-end with real data against Purview/Collibra.

### Code quality (DONE)
- [x] Python `logging` throughout the library (no print statements in `src/`)
- [x] Pinned dependency versions; `pip-audit` clean

### Parser (DONE — ScriptDom, production-grade)
- [x] ScriptDom via pythonnet: 99%+ parse rate, 0 errors (see Canonical Numbers)
- [x] DLL loaded from Lakehouse Files/libs/ via pythonnet CoreCLR
- [x] AST walk extracts SELECT/INSERT verbatim; sqlglot structural analysis
- [x] sqlparse-based fallback if ScriptDom unavailable
- [x] Regression test suite preventing yoyo between approaches
- [x] Persistent error log with regression detection across runs

### Graph & traversal (DONE)
- [x] Three-layer graph with full dependency chain traversal
- [x] Multi-statement proc support (temp tables → CTE entries with dependencies)
- [x] `__final_select__` synthetic node; 400K+ nodes, 12K+ edges from real data
- [x] LPG export: 8 typed tables (see [ADR 0014](../decisions/0014-metric-logic-grounding-mandatory-dictionary.md))

### Data Agent (DONE)
- [x] Fabric Data Agent grounded in `metric_logic` + graph tables
- [x] Persona-based responses; self-contained instruction knowledge base
- [x] Data Agent API via MCP protocol (JSON-RPC); programmatic description generation

### Description generation (DONE)
- [x] LLM summary generators (combined per-metric call; Data Agent API variant)
- [x] Descriptions stored on graph nodes

### Adapters & integrations (BUILT, WAITING ON ACCESS)
- [x] Collibra adapter (REST API, bulk publish)
- [x] Purview adapter (Data Map REST API; service-principal auth, single entity API)
- [x] PBI report description updater; Fabric lineage API client
- [x] Metadata Sync notebook; Fabric Agent client (MCP)

### Blocked on access
- [ ] Collibra service account → test Collibra push (work admin)
- [ ] Purview Data Curator role → test Purview push (own tenant when Fabric available)
- [ ] Test PBI description updates against dev workspace
- [ ] Test Fabric lineage API against PBI workspace (needs PBI Admin — own tenant)

### Enterprise readiness (PARTIALLY DONE)
- [ ] Business-friendly metric names from PBI lineage (replace proc names)
- [x] Steward assignment module; usage tracking module
- [x] Admin commands in agent (/admindash, /stewards, /errors, /coverage, /health)
- [x] CI/CD pipeline (GitHub Actions: lint + test + build + security audit)
- [ ] Automated refresh via Fabric Pipeline (document in admin guide)
- [ ] Secrets management via Azure Key Vault (replace notebook API keys)

### Scale testing
- [x] Full-corpus validation runs (see Canonical Numbers)
- [x] Inspection table (extraction_inspection) for manual validation
- [ ] Golden file tests for 3-5 critical real-world queries
- [ ] Test bulk catalog push with 50+ records

### Exit criteria
- [x] Parse real SQL at 99%+ with 0 errors
- [x] Full pipeline end-to-end (parse → graph → traverse → metadata → descriptions)
- [x] Data Agent answers metric questions correctly
- [ ] Push metadata to at least one catalog (Purview or Collibra) via API
- [ ] PBI report descriptions updated programmatically
- [x] All tests pass; no print statements in library code

---

## Phase 2: Business Setup
**Status: MOSTLY DONE — verification pending**

Legal entity and Microsoft partner registration. Runs in parallel with Phase 1.

- [x] Establish business entity — **AIVIA LLC registered**
- [x] Website live (www.aiviaapp.com); email aliases (privacy@, support@, legal@)
- [x] Privacy policy and terms of service published
- [x] Apply to Microsoft for Startups Founders Hub (submitted 2026-07-20;
      Level 3 deliberately skipped — [ADR 0010](../decisions/0010-skip-founders-hub-level-3.md))
- [x] Register as ISV on Partner Center; enroll in Commercial Marketplace program
- [ ] Business verification approved (resubmitted — waiting 3-5 days)
- [ ] Tax profile W-9 completed (form loading issue — follow up with apmdg@microsoft.com)
- [ ] Payout profile verified
- [ ] Business bank account
- [ ] Review employment contract for invention assignment clauses; HR disclosure

### Exit criteria
- [x] Legal entity exists
- [ ] Partner Center publisher account fully verified (identity + tax + payout)
- [x] Founders Hub application submitted
- [ ] Conflict of interest documented and mitigated

---

## Phase 3: Production Hardening
**Status: IN PROGRESS**

Make the codebase enterprise-ready for Marketplace certification.

### Done
- [x] CI/CD (GitHub Actions): lint + test + build + security audit on every push
- [x] `LICENSE` file (MIT); `README.md`; `org_config.example.yaml`
- [x] Pinned dependency versions; `pip-audit` clean
- [x] Dead code removed (38 files; 0 unreachable modules)
- [x] Schema contracts; error classification with user explanations

### Remaining
- [ ] Build `.whl` artifact and verify with `twine check`
- [ ] Test `.whl` install in a clean Fabric Environment
- [ ] Type hints throughout (`mypy` clean)
- [ ] Input validation/sanitization audit on SQL parsing
- [ ] Verify no hardcoded secrets, paths, or org-specific details
- [ ] Ensure no Fabric-specific imports in core library
- [ ] Structured error handling audit (no bare exceptions)
- [ ] Docstrings on all public functions/classes

### Exit criteria
- [ ] `.whl` installs cleanly in a fresh Fabric Environment
- [ ] `mypy` and `ruff` pass with zero errors
- [x] CI green on every push; `pip-audit` clean

---

## Phase 4: Marketplace Submission
**Status: IN PROGRESS** — blocked on Fabric capacity for the demo tenant.

### Listing assets (DONE)
- [x] Offer name: "AIVIA — SQL Intelligence Agent for Fabric"
- [x] Offer description drafted ([MARKETPLACE_LISTING.md](../product/MARKETPLACE_LISTING.md))
- [x] Logo in 4 sizes (48x48, 90x90, 216x216, 255x115)
- [x] Pricing defined (see Canonical Numbers)
- [x] Search keywords: business logic extraction, report metadata summary, data governance agent
- [x] Privacy/terms/support URLs live on aiviaapp.com

### Security & compliance docs
- [x] Security whitepaper ([SECURITY_WHITEPAPER.md](../product/SECURITY_WHITEPAPER.md))
- [ ] Data flow diagram showing security boundaries
- [ ] Microsoft Publisher Attestation questionnaire in Partner Center
- [ ] Review CSA STAR registry — self-attestation needed for v1?

### Documentation for customers/reviewers
- [x] [INSTALLATION_GUIDE.md](../deployment/INSTALLATION_GUIDE.md) — canonical customer install guide
- [x] [DATA_DICTIONARY_REQUIREMENTS.md](../deployment/DATA_DICTIONARY_REQUIREMENTS.md)
- [x] [REVIEWER_GUIDE.md](../product/REVIEWER_GUIDE.md) — for Microsoft certification testers
- [ ] Prerequisite validation script (`scripts/validate_deployment.py`)
- [ ] Document Fabric API rate limits and handling
- [ ] Add Fabric/API error codes to error_classifier (403, 404, 429 → resolution steps)

### Fabric capacity (BLOCKER)
Get capacity through one of:
- [ ] **Option A:** Founders Hub credits approved → provision F2
- [ ] **Option B:** Buy F2 directly ($262/month) → demo → cancel
- [ ] **Option C:** Fabric free trial activates

### Deploy to own tenant (needs capacity)
- [ ] Workspace "AIVIA-Demo" + lakehouse; upload code and ScriptDom DLL
- [ ] Synthetic SQL files (5-10 diverse patterns, no real data) + synthetic dictionary
- [ ] Run pipeline: 02_parse → 03_build_graph → 04_build_metric_logic →
      05_export_graph_tables → 06_validate (expect 100% health)
- [ ] Configure Data Agent; verify answers, /errors, /coverage
- [ ] Golden lakehouse snapshot after successful run; rollback steps documented

### Demo & screenshots (needs deployed tenant)
- [ ] 5-minute demo video per [DEMO_SCRIPT.md](DEMO_SCRIPT.md) — business Q,
      developer Q, admin command, architecture diagram; no org-specific data visible
- [ ] 3-5 screenshots: business answer, technical details, validation health,
      graph structure, architecture diagram

### Submission
- [ ] **Decide: Contact Me vs. Transactable for launch** — recommendation:
      Contact Me first (days not weeks, no fulfillment infrastructure), convert
      to transactable after 3 customers ([ADR 0013](../decisions/0013-transactable-saas-on-marketplace.md))
- [ ] Reviewer sandbox: dedicated workspace, synthetic data, test credentials, REVIEWER_GUIDE
- [ ] Create offer in Partner Center; upload assets; submit for certification
- [ ] Respond to certification feedback (review takes 2-4 weeks)

### Support & operations readiness
- [ ] Define support hours and response-time SLA
- [ ] Escalation path: support@ email → founder review → resolution
- [ ] Lead intake questionnaire + deployment package for qualified leads
- [ ] Scheduling link (Calendly/Bookings) for onboarding calls

### Exit criteria
- [ ] Offer approved and listed on Microsoft Commercial Marketplace
- [ ] At least one plan is live (Contact Me acceptable for v1)

---

## Phase 5: Post-Launch & Pro Tier
**Status: NOT STARTED**

### Second adapter
- [ ] Wire up the adapter not completed in Phase 1 (Collibra or Purview)
- [ ] Test with at least one customer or POC environment

### Pro tier: Chat Data Agent
- [ ] Package Data Agent grounding as a configurable feature
- [ ] Steward notification workflow for Path B (unknown questions)
- [ ] Purview report discovery (existing reports matching user questions)
- [ ] Row-level security for personalized access (surgeon-sees-own-data pattern)
- [ ] Add Pro plan to Marketplace listing

### Entra ID security & access control
- [ ] Identify the asking user via Entra ID; `security_groups` on canonical nodes
- [ ] Access-denied → request workflow → steward approval expands access list
- [ ] Row-level security: same metric, different data by identity
- [ ] Audit trail: who asked, what was denied/approved, when

### AI support bot
- [ ] Knowledge graph of product documentation (seeded by `docs/decisions/` —
      [ADR 0011](../decisions/0011-static-guide-v1-copilot-v2.md))
- [ ] Self-service support agent; target 80%+ of common questions

### Growth
- [ ] Marketplace Rewards; track revenue toward Azure IP co-sell
- [ ] Customer testimonials / case studies
- [ ] Evaluate open-source core + paid managed experience
- [ ] Evaluate Azure Managed Application deployment (vs .whl — [ADR 0007](../decisions/0007-byot-library-deployment.md))

### Exit criteria
- [ ] Both adapters working in production
- [ ] Pro tier listed with Agent features
- [ ] At least 3 paying customers

---

## How to Use This Roadmap

1. **This file owns status.** Update checkboxes here and nowhere else.
2. Phases 1–4 can overlap where independent; don't skip exit criteria.
3. Move items between phases if priorities shift — this is a living document.
4. Record the *why* behind new decisions as ADRs in `docs/decisions/`.
