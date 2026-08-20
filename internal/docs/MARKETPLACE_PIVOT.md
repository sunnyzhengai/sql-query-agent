# Marketplace Pivot: Decision Record & Project Plan

> **FROZEN SNAPSHOT (2026-07-25) — do not update.** This document records the
> POC-to-product pivot as it stood on that date. Checkbox state and "already
> done" claims below are historical. Current status lives in
> [ROADMAP.md](ROADMAP.md); decisions D1–D7 are extracted as ADRs
> [0008](../decisions/0008-ship-tier-1-first.md)–[0013](../decisions/0013-transactable-saas-on-marketplace.md)
> in [docs/decisions/](../decisions/README.md).

**Date:** 2026-07-25
**Context:** POC validated (99%+ parse rate, 1337/1344 procs, Data Agent working). Pivoting from POC to commercial Marketplace product.

---

## Key Decisions

### D1: Ship Tier 1 first, don't wait for all three tiers

**Decision:** List the Core Metadata & Semantic Q&A agent on Marketplace as Tier 1. Build Collibra/Purview sync (Tier 2) and Dynamic SQL Execution (Tier 3) as add-on modules after listing.

**Why:**
- Fastest path to revenue and market validation
- Tier 1 has the widest addressable market (any org with SQL sources in Fabric)
- Governance sync (Tier 2) requires per-tool integration (Collibra, Purview, Alation) — narrow market, blocks the broad product
- Dynamic SQL (Tier 3) introduces security/compliance complexity that could delay certification

**How to apply:** Marketplace listing describes Tier 1 capabilities. Product roadmap mentions Tiers 2 and 3 as upcoming modules. Demo video shows Tier 1 in action.

### D2: Decouple Collibra integration from core product

**Decision:** Collibra sync is a configurable add-on, not a requirement. Same for Purview, Alation, etc.

**Why:**
- Not every org has a data governance tool
- Not every tool is Collibra
- Bundling blocks the core product on the narrowest feature
- Each governance tool is a separate adapter with separate API credentials

**How to apply:** Core product works standalone. `org_config.yaml` has an `adapters` section where customer enables their specific tool. Each adapter is a separate module in `src/adapters/`.

### D3: Skip Founders Hub Level 3, go directly to Partner Center

**Decision:** Do not spend time polishing a demo for Founders Hub Level 3 approval. Go directly to Microsoft Partner Center and submit the Marketplace listing.

**Why:**
- Level 3 is only about $25K Azure credits — not needed if self-funded
- Level 3 does not unlock Marketplace access or Co-Sell status
- Partner Center and Marketplace operate independently from Founders Hub
- Every day spent on Founders Hub demo is a day not shipping to market

**How to apply:** Focus all effort on Partner Center submission requirements.

### D4: Static deployment guide for v1, co-pilot agent for v2

**Decision:** Ship v1 with a written DEPLOYMENT_GUIDE.md checklist. Build the AI-powered installation/troubleshooting co-pilot agent after first customer feedback.

**Why:**
- The co-pilot agent is a second product — months of work (knowledge graph, prompt engineering, testing against real customer environments)
- No real customer data to validate what actually breaks during installation
- A static guide is what every enterprise product ships with at v1
- After 3+ customers, patterns in support questions will inform the co-pilot design

**How to apply:** Write DEPLOYMENT_GUIDE.md with step-by-step checklist. Document operational decisions (HOW + WHY) in `docs/decisions/` markdown files. These become the raw material for the v2 co-pilot.

### D5: Document operational decisions for future co-pilot

**Decision:** Start capturing operational decisions now in structured markdown, even though the co-pilot isn't built yet.

**Why:**
- Decisions are freshest when made — capture them now, index them later
- Structured format (Constraint-Action-Outcome) makes future graph ingestion trivial
- Only document customer-facing decisions: installation, configuration, security, error modes
- Do NOT document internal engineering choices (ScriptDom vs sqlglot, etc.)

**Filter test:** "If a system admin encounters an error, does knowing this decision help resolve it?" If yes → document. If no → skip.

### D6: Stay in current repo, don't start fresh

**Decision:** Build the enterprise product on top of the current sql-query-agent repository.

**Why:**
- Current repo has battle-tested parsing engine (99%+ accuracy)
- Rewriting introduces regression bugs and wastes weeks
- Architecture docs should reflect reality, not theoretical ideals
- Incremental refactoring is safer than clean-slate rewrites

**How to apply:** Retrofit governance, documentation, and packaging layers around the existing codebase.

### D7: Package as SaaS application on Microsoft Commercial Marketplace

**Decision:** List as a Transactable SaaS offer through Microsoft Partner Center.

**Why:**
- SaaS model aligns with BYOT architecture (customer deploys in their own Fabric tenant)
- Transactable offers are eligible for MACC (Microsoft Azure Consumption Commitment) — enterprise customers can use pre-committed Azure budgets
- Co-Sell Ready status becomes available once listed
- Microsoft's sales force is incentivized to pitch Co-Sell Ready products

**How to apply:** Set up Partner Center publisher account, configure SaaS offer, build landing page for subscription activation, integrate with Marketplace Fulfillment API.

---

## Product Tiers

| Tier | Name | What it does | Target buyer | Status |
|---|---|---|---|---|
| 1 | **Core Agent** | Metadata Q&A from knowledge graph in Fabric | Any org with SQL + Fabric | **Ship first** |
| 2 | **Governance Sync** | Push descriptions to Collibra, Purview, etc. | Orgs with data governance tools | Build as add-on |
| 3 | **Active Data Agent** | Dynamic SQL execution against Fabric data | Advanced analytics teams | Future roadmap |

---

## Project Plan: Marketplace Listing

### Phase 1: Partner Center Setup (Week 1)

- [ ] Verify ISV registration status on Partner Center
- [ ] Complete business identity verification (3-5 business days)
- [ ] Set up legal/tax information (EIN, banking payout)
- [ ] Accept Microsoft Publisher Agreement

### Phase 2: Legal & Marketing (Week 1-2, parallel with Phase 1)

- [ ] Publish privacy policy at aiviaapp.com/privacy
- [ ] Publish terms of service at aiviaapp.com/terms
- [ ] Create professional logo (48x48, 90x90, 216x216, 255x115)
- [ ] Write offer description (short: 100 chars, long: 3000 chars)
- [ ] Define search keywords and categories
- [ ] Define pricing plan(s)

### Phase 3: Product Packaging (Week 2-3)

- [ ] Build .whl distribution package
- [ ] Write DEPLOYMENT_GUIDE.md (step-by-step admin checklist)
- [ ] Create org_config.example.yaml with all configurable options documented
- [ ] Remove all print() statements → replace with logging module
- [ ] Ensure no hardcoded paths, URLs, or credentials
- [ ] Pin exact dependency versions
- [ ] Write reviewer's guide (for Microsoft certification testers)

### Phase 4: Demo Environment (Week 2-3, needs Fabric)

- [ ] Provision Fabric capacity (own tenant)
- [ ] Deploy product with synthetic sample data
- [ ] Configure Data Agent with updated instructions
- [ ] Verify agent answers questions correctly for multiple metrics
- [ ] Record 5-minute demo video
- [ ] Take 3-5 screenshots for listing

### Phase 5: Marketplace Submission (Week 3-4)

- [ ] Create SaaS offer in Partner Center
- [ ] Configure pricing plans
- [ ] Upload all listing assets (logo, screenshots, video, descriptions)
- [ ] Provide test environment credentials for Microsoft reviewers
- [ ] Upload reviewer's guide
- [ ] Submit for certification
- [ ] Respond to any certification feedback

### Phase 6: Concurrent Development (Weeks 2-4, parallel)

- [ ] Build Collibra discovery + lineage retrieval (started)
- [ ] Build Collibra description push
- [ ] Write operational decision documents in docs/decisions/
- [ ] Clean up dead code (5 unreachable modules identified)

---

## What's Already Done

| Item | Status |
|---|---|
| Core parsing engine (99%+ accuracy) | Done |
| Three-layer knowledge graph | Done |
| Data Agent with updated instructions | Done |
| metric_logic flattened table | Done |
| Error classification with user explanations | Done |
| Pipeline split into independent notebooks | Done |
| Dead code detector | Done |
| Schema contracts | Done |
| Website (aiviaapp.com) | Done |
| LLC registered (AIVIA LLC) | Done |
| Founders Hub submitted | Done |
| ISV registration | Done |
| CI/CD with tests (87 tests passing) | Done |

---

## What's NOT Needed for v1 Marketplace Listing

- Collibra/Purview integration (Tier 2 — add-on module)
- Dynamic SQL execution (Tier 3 — future roadmap)
- AI installation co-pilot agent (v2 feature)
- Decision graph database (v2 — markdown files are sufficient for now)
- Founders Hub Level 3 approval (credits only, not needed)
