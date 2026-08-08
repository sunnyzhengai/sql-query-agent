# Product Roadmap

> **This document is the single source of truth for project status.** No other
> document carries live checkboxes or current metrics. Rationale for decisions
> lives in [docs/decisions/](../decisions/README.md) (ADRs). Frozen snapshots
> (e.g. [MARKETPLACE_PIVOT.md](MARKETPLACE_PIVOT.md)) are historical and
> banner-marked as such.

Phased plan for taking the **Data Empowerment Suite** from internal tool to
Microsoft Marketplace product. No fixed dates — phases have exit criteria, not
deadlines. Update this as you go.

**Last reconciled:** 2026-08-06

## Canonical Numbers

Cite these from other documents by reference — do not copy values.

| Metric | Value | As of |
|---|---|---|
| Package version | 1.4.0 (`pyproject.toml`) | 2026-08-06 |
| Parse rate (latest full corpus) | 1,337 / 1,344 procs (99.5%), 0 errors | 2026-07-25 |
| Earlier validation run | 788 / 790 procs (99.7%), 24 min | 2026-07 |
| Test suite | 362 tests collected (`pytest --collect-only`) | 2026-08-06 |
| Pipeline notebooks | 01_install … 09_publish_purview (9 numbered) | 2026-08-02 |
| Pricing | $2,000/mo, $21,600/yr, 30-day free trial | 2026-07-25 |

## Product Components

| Component | Short Name | Description | Tier |
|-----------|-----------|-------------|------|
| **Metadata Agent** | "agent" | Knowledge graph + Data Agent that ANSWERS metadata questions ("how is this calculated?") with certified, owner-attributed answers — plus Purview/Collibra sync. Renamed from "Metadata Sync" 2026-08-07: we answer questions, static catalogs only store them. | Basic |
| **Analytics Agent** | "analytics" | Self-service tier: certified semantic layer compiled from the graph; Data Agent #2 executes certified metrics against real data ("what WAS it last month?"). | Pro (roadmap) |

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

**Connector roadmap (added 2026-08-07, see
[REFERENCE_ARCHITECTURE.md](../architecture/REFERENCE_ARCHITECTURE.md)):**
next up are **dbt** (manifest.json → compiled T-SQL + free DAG; cheapest
connector, ScriptDom-compatible via dbt-fabric — Sunny's org's own path)
and **Fabric semantic models** (TMDL extraction: lineage now, DAX measure
parsing as its own ADR 0001 lane). Then Databricks (SQL views + Unity
Catalog only — PySpark logic explicitly out of scope for v1) and
Snowflake (GET_DDL + sqlglot dialect).

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
- [x] LPG export: 9 typed tables (see [ADR 0014](../decisions/0014-metric-logic-grounding-mandatory-dictionary.md))

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
- [x] Purview push tested END TO END on own tenant (~2026-08-01: live test
      drove the single-entity-API and service-principal-auth fixes, both
      committed; account deprovisioned after — Purview pay-as-you-go bills
      hard, provision short-lived for demos only). Remaining: wire
      ops_sync_log audit rows during the next short-lived provision
- [ ] Test PBI description updates against dev workspace
- [ ] Test Fabric lineage API against PBI workspace (needs PBI Admin — own tenant)

### Enterprise readiness (PARTIALLY DONE)
- [x] Data contracts for all Delta tables (`src/schemas.py`): shape, semantics,
      single-writer ownership, consumers, invariants — enforced against code
      ground truth by `tests/test_table_contracts.py` (2026-08-02)
- [x] Offline-executable pipeline, slice 1 (2026-08-02): pure step functions in
      `src/steps/` (parse, build_graph, metric_logic, export, readiness) with
      logic relations asserted inside; notebooks are thin callers ending in a
      registry-driven postcondition gate; full 02→05 pipeline runs in CI with
      zero Fabric cost (`tests/steps/`)
- [x] Offline slice 2 (2026-08-02): verified DAG — read-side scanner (consumers
      code-verified both directions), relations field (cross-table flow
      contracts, gate-enforced), generated PIPELINE_MAP.md with freshness test;
      CI now runs on dev
- [x] Offline slice 3 (2026-08-02): record-replay infrastructure — anonymization
      engine lifted to src/ (crosswalk-driven, org terms parameterized),
      export_test_fixtures notebook (select→anonymize→leak-gate→export),
      run_pipeline_local.py replays 03→06 pure-python with full gates,
      recorded-pipeline tests skip until fixtures land
- [x] Run export_test_fixtures on Fabric once, download to
      tests/fixtures/recorded/, run pytest, commit — CI replays ScriptDom
      truth on every push (fixtures landed 2026-08-02)
- [x] Offline slice 4 (2026-08-06): LLM stand-in via AgentBackend protocol
      (devtools/local_llm.py + describe_local.py); full-corpus description
      fixtures generated locally, leak-gated (with `~cs` case-sensitive scan
      terms for org words that are common English), committed
- [x] Recovered from dead-code purge (2026-08-02): ops_error_log (regression
      detection, appended by 02_parse) and gov_steward_assignments
      (manage_stewards utility → applied to graph by 03 → agent-visible via
      metric_logic); ops_extraction_tracking reactivated (extract_views writer)
- [ ] Reconcile remaining 2 "planned" contracts: ops_extraction_inspection,
      ops_sync_log — reinstate writers or drop
- [x] Business-friendly metric names (2026-08-07): input_metric_names
      contract (PBI lineage via extract_pbix_sources --names-csv, or
      manual CSV) → canonical nodes → metric_logic.business_name +
      graph_canonical.businessName → both agents search & display them;
      ambiguous bare names skipped, never guessed. On-tenant: author the
      dev-corpus mapping, rerun 03→05, re-Load
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
- [x] Push metadata to at least one catalog via API (Purview, live test
      ~2026-08-01 on own tenant)
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
- [x] Business verification approved (2026-08-06)
- [x] Tax profile W-9 completed (2026-08-06)
- [x] Payout profile: Chase business account connected in Partner Center
      (2026-08-06 — confirm verification status shows green)
- [x] Business bank account (Chase)
- [ ] Review employment contract for invention assignment clauses — DELEGATED
      to Sunny's lawyer 2026-08-06 (brief: domain overlap with employer's
      BI/healthcare space; personal time/equipment coverage; CoI disclosure
      obligations)

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
- [x] Data flow diagram showing security boundaries — 2026-08-06: "System
      at a Glance" mermaid in ARCHITECTURE.md (tenant boundary, single
      PHI-redacted egress to customer's Azure OpenAI); GitHub renders it,
      screenshot for Partner Center attestation
- [ ] Microsoft Publisher Attestation questionnaire in Partner Center
- [ ] Review CSA STAR registry — self-attestation needed for v1?

### Documentation for customers/reviewers
- [x] [INSTALLATION_GUIDE.md](../deployment/INSTALLATION_GUIDE.md) — canonical customer install guide
- [x] [DATA_DICTIONARY_REQUIREMENTS.md](../deployment/DATA_DICTIONARY_REQUIREMENTS.md)
- [x] [REVIEWER_GUIDE.md](../product/REVIEWER_GUIDE.md) — for Microsoft certification testers
- [x] Deployment packaging script (`scripts/build_deployment_package.py`) —
      allowlist build of the customer zip with internal-content leak guard (tested)
- [x] Prerequisite validation script (`scripts/validate_deployment.py`) —
      2026-08-06: config/llm/dictionary/sql/DLL/package checks, contract-
      driven column requirements, fix-stating failures, tested
- [ ] Document Fabric API rate limits and handling
- [ ] Add Fabric/API error codes to error_classifier (403, 404, 429 → resolution steps)

### Fabric capacity (BLOCKER)
Get capacity through one of:
- [ ] **Option A:** Founders Hub credits approved → provision F2
- [ ] **Option B:** Buy F2 directly ($262/month) → demo → cancel
- [ ] **Option C:** Fabric free trial activates

### Deploy to own tenant (needs capacity)
- [x] Workspace AIVIA-DEV-2 + lakehouse; wheel ships via git-integrated
      environment (see RESUME_CHECKLISTS.md runbook)
- [x] Demo data DECIDED 2026-08-06: the anonymized real corpus (28 sepsis
      metrics, leak-gated crosswalk output), NOT toy synthetic — real CTE
      depth demos better. Pre-video check: confirm crosswalk output is
      public-safe on screen
- [x] Full pipeline + 07 descriptions live (1.4.1, 2026-08-06); agent
      answers verified grounded (step-catalog answer traced to certified
      descriptions)
- [ ] Verify /errors, /coverage admin commands on current deployment
- [ ] Golden lakehouse snapshot after successful run; rollback steps documented

### Demo & screenshots (needs deployed tenant)
- [ ] 5-minute demo video per [DEMO_SCRIPT.md](DEMO_SCRIPT.md) — business Q,
      developer Q, admin command, architecture diagram; no org-specific data visible
- [ ] 3-5 screenshots: business answer, technical details, validation health,
      graph structure, architecture diagram

### Submission
- [x] **Decide: Contact Me vs. Transactable for launch** — DECIDED 2026-08-06
      ([ADR 0028](../decisions/0028-contact-me-first-transactable-on-first-buyer.md)):
      Contact Me as soon as verification clears; convert the same offer at
      first-buyer signal (not "after 3 customers" — private offers need
      transactable). Execution plan:
      [MARKETPLACE_TRANSACTABLE_PLAN.md](MARKETPLACE_TRANSACTABLE_PLAN.md)
- [x] Fulfillment scaffold (2026-08-06): subscription state machine +
      webhook contract + JWT claim validation as pure library code with
      tests (`src/marketplace/`, `tests/marketplace/`)
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

## Open Questions (steward backlog, raised 2026-08-02)

Raised during the contract review; each gets a ground-truth answer and, where
needed, a design pass. Do not resolve casually — these are product decisions.

- [x] **PHI/hardcoded-value scanning at ingestion** — DESIGNED + library
      IMPLEMENTED 2026-08-06 (listing prerequisite per Sunny):
      [ADR 0025](../decisions/0025-phi-scanning-at-ingestion.md);
      `src/phi_scan.py` (5 rules, every-member IN-list flagging, steward
      dispositions survive re-scans) + redaction live at describe_local's
      prompt boundary. Fixture audit: 278 findings, 102/432 steps carry
      redact-level literals, committed descriptions verified leak-free.
      Remaining: notebook wiring (02 writes ops_phi_findings → flip
      contract active; 07 applies redaction on-tenant — regenerates ~102
      steps' cache on first redacted run) + 08/09 publish gates.
- [x] **Usage-weight flywheel + answer feedback** — DESIGNED 2026-08-06:
      [ADR 0023](../decisions/0023-usage-weighted-governance-flywheel.md)
      (append-only events, derived weights, demand-sorted steward queue) +
      `gov_usage_events` contract draft. Implementation pending.
- [x] **Error-to-data lineage** — DESIGNED 2026-08-06:
      [ADR 0026](../decisions/0026-error-to-data-lineage.md) (mandatory
      reference invariants on error tables; runtime events with
      affected_objects) + `ops_runtime_error_events` contract draft.
      Implementation pending.
- [x] **Steward creation + certification workflow** — DESIGNED 2026-08-06:
      [ADR 0021](../decisions/0021-certification-discloses-never-gates.md)
      (constitution: certification discloses, never gates) +
      [ADR 0022](../decisions/0022-definition-versioning-certification-pins-a-version.md)
      (content-hash versions, certification pins a version) +
      [ADR 0024](../decisions/0024-layered-truth-personal-and-enterprise.md)
      (personal + enterprise truth layers) + `gov_certification_events` /
      `gov_personal_definitions` contract drafts. Implementation pending.
- [x] **Dimension-layer activation (design pass)** — DESIGNED 2026-08-06:
      [ADR 0029](../decisions/0029-dimension-layer-activation.md)
      (filter-usage qualifies; scope-local alias resolution at parse time;
      unresolvable refs dropped and counted). Implementation pending.
- [x] **Ownership attribution** — DESIGNED 2026-08-06:
      [ADR 0027](../decisions/0027-ownership-attribution-layered-sources.md)
      (manual floor, Entra enrichment adapter, provenance columns) +
      [Entra feasibility findings](../development/OWNERSHIP_ATTRIBUTION.md).
      Implementation pending.
- [ ] **Fallback splitter environment divergence** — identical bytes, Python
      version, sqlparse and sqlglot versions produce different statement
      boundaries on GitHub runners vs macOS (SELECT INTO absorbs a following
      CREATE INDEX; 0/56 queries then parse). Discovered on first dev CI run
      2026-08-03. Fallback goldens are local-only until diagnosed; production
      parsing (ScriptDom) is unaffected and CI-covered via recorded fixtures.
- [ ] **Count-oracle agent evals** — extend devtools/grounding_evals.py with
      count-assertion cases generated from certified fixtures (readers-of-table,
      tables-of-metric, columns-of-table counts) and run against the published
      agents via FabricAgentBackend. Counts are cheap oracles: they catch
      silent-undercount defects (e.g. the 2026-08-04 shallow-traversal bug,
      5/13 readers) that prose-level evals cannot see.
- [ ] **Delta vs Graph rematch** — Round 2 PARTIAL (2026-08-05): 3/9
      questions green on the post-1.3.1 graph (Q1 32/32, Q4 13/13, Q3
      ambiguity surfaced); halted on F2 throttling. Writeup drafted:
      [REMATCH_WRITEUP.md](REMATCH_WRITEUP.md); completion plan:
      [RESUME_CHECKLISTS.md](RESUME_CHECKLISTS.md). Full rerun once the
      dimension layer is live remains open. Original framing: rerun once
      contracts are enforced in production and the dimension layer is live;
      the original experiment compared curated Delta (metric_logic) against
      a structurally impoverished graph (case-split nodes, empty dimension
      layer, floating column nodes). Hypothesis to test (Sunny, 2026-08-02):
      SQL is set theory and LLMs get "creative" transforming NL into it,
      while graph traversal is semantically closer to NL — given a quality
      graph structure and good grounding rules, NL-to-traversal should be
      easier and more accurate. Measure: answer accuracy + refusal
      correctness on the same question set via GraphBackend protocol.

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
