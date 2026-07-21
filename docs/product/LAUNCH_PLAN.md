# Launch Plan: Metadata Sync to Microsoft Marketplace

**Living document — update as we progress. Check boxes as items complete.**

**End Goal:** Metadata Sync published on Microsoft Commercial Marketplace, generating revenue.

---

## Current Status

| Milestone | Status |
|---|---|
| Core product (parser, graph, agent) | **87% done** |
| Website (aiviaapp.com) | **Live** |
| LLC | **Registered (AIVIA LLC)** |
| Founders Hub application | **Submitted 2026-07-20, awaiting review** |
| Own Azure/Fabric tenant | **Azure ready, Fabric capacity pending** |
| Partner Center publisher account | Not started |
| Marketplace listing | Not started |
| Certification | Not started |

---

## Phase 1: Foundation & Trust Signals (THIS WEEK)

*Build credibility and prepare everything that doesn't require Fabric capacity.*

### Business Identity (DONE)
- [x] Register LLC
- [x] Register domain (aiviaapp.com)
- [x] Business email (founder@aiviaapp.com)
- [x] M365 Business account
- [x] Azure subscription
- [x] Website live (www.aiviaapp.com)
- [x] Founders Hub application submitted

### Legal & Compliance (DO NOW — no Fabric needed)
- [ ] **Privacy Policy** — publish on aiviaapp.com/privacy
  - What data the tool accesses
  - BYOT model: customer data stays in their tenant
  - No data collection by AIVIA
  - GDPR/HIPAA statement
- [ ] **Terms of Service / EULA** — publish on aiviaapp.com/terms
  - License grant
  - Customer responsibilities (their data, their tenant)
  - Liability limitations
  - Support terms
- [ ] **Security Whitepaper** (1-2 pages)
  - Data handling: BYOT, no data leaves customer tenant
  - Authentication: Microsoft Entra ID / SSO
  - Encryption: at rest (Delta tables) and in transit (HTTPS)
  - RBAC: respects existing Fabric workspace permissions
  - No model training on customer data
  - HITL certification workflow for data accuracy

### Partner Center Setup (DO NOW — has its own verification timeline)
- [ ] Join **Microsoft AI Cloud Partner Program**
- [ ] Create **publisher account** in Partner Center
- [ ] Accept **Microsoft Publisher Agreement**
- [ ] Complete **identity verification** (company legal registration, 3-5 business days)
- [ ] Set up **legal/tax information** (EIN for LLC, banking payout details)

### Marketing Assets (DO NOW — no Fabric needed)
- [ ] **Logo** — professional, multiple sizes (48x48, 90x90, 216x216, 255x115)
- [ ] **Offer name** — "AIVIA Metadata Sync" or "AIVIA Data Empowerment Suite"
- [ ] **Short description** (100 chars)
- [ ] **Long description** (3000 chars) — problem, solution, features, benefits
- [ ] **Search keywords** — data governance, metadata, Fabric, AI agent, SQL parsing
- [ ] **Categories** — Data & Analytics, AI, Developer Tools

### Product Improvements (DO NOW — local development)
- [ ] Improve sqlparse extractor (87% → 95%+ parse rate)
- [ ] Add more synthetic sample data (5-10 diverse SQL patterns)
- [ ] Prepare **reviewer's guide** (step-by-step for Microsoft testers)

### Work Environment (DO NOW — send admin email)
- [ ] Send admin access request email (4 items: PBI lineage, audit logs, Purview, Collibra)
- [ ] Test Collibra push when service account arrives
- [ ] Test PBI lineage API when admin access arrives
- [ ] Validate product against work data (POC only, not for product demo)

---

## Phase 2: Product Integration & Infrastructure (WHEN FABRIC AVAILABLE)

*Deploy to own Fabric tenant, build integrations, record demo.*

### Fabric Deployment

**How Fabric capacity arrives (one of these):**
- [ ] Plan A: Fabric free trial activates (check daily)
- [ ] Plan B: Founders Hub credits → provision F2 ($262/mo covered by credits)
- [ ] Plan C: Buy F2 out of pocket → deploy → record → cancel

**Once Fabric is available:**
- [ ] Provision Fabric F2 capacity
- [ ] Create workspace (AIVIA-Dev)
- [ ] Create lakehouse
- [ ] Upload sql-query-agent code to Files/
- [ ] Upload synthetic sample data
- [ ] Create org_config.yaml (sample config, no real credentials)
- [ ] Run orchestrator notebook → verify graph builds
- [ ] Create Data Agent → configure with graph tables + instructions
- [ ] Verify Data Agent answers questions correctly

### Integration Testing (own tenant = you're admin)
- [ ] **Purview:** Assign yourself Data Curator → test metadata push
- [ ] **PBI Lineage:** You're PBI Admin → test lineage API
- [ ] **Audit Logs:** You're Fabric Admin → test audit log API
- [ ] **PBI Descriptions:** Test report description update
- [ ] End-to-end: SQL → parse → graph → agent → description → Purview push

### Authentication & Security
- [ ] Configure Microsoft Entra ID for the product
- [ ] Set up Service Principal for automated API calls
- [ ] Move secrets to Azure Key Vault (replace notebook-embedded keys)
- [ ] Test RBAC: different user roles see different things

### Demo Recording
- [ ] Record 5-minute demo video in own Fabric tenant
  - Show the "magic": agent answering questions
  - Show architecture diagram
  - Show Purview integration
  - Show roadmap
  - Use ONLY synthetic data
- [ ] Take 3-5 screenshots for Marketplace listing
- [ ] Upload demo video → Founders Hub Level 3 ($25K credits)

---

## Phase 3: Marketplace Packaging & Submission

*Configure the SaaS offer, build the subscription infrastructure, submit for certification.*

### SaaS Offer Configuration
- [ ] Choose offer type: **Transactable SaaS**
- [ ] Configure pricing plans:
  - **Basic (Metadata Sync):** flat-rate monthly
  - **Pro (GraphRAG Engine):** flat-rate monthly, higher price
- [ ] Set up plan features:
  - Basic: SQL parsing, graph building, Purview/Collibra push, PBI descriptions
  - Pro: Basic + Data Agent grounding, usage tracking, steward workflow
- [ ] Configure up to 100 plans (start with 2)
- [ ] Set up private offers capability (for enterprise custom pricing)

### Subscription Infrastructure
- [ ] Build **landing page** for subscription activation
  - Customer clicks "Get It Now" in Marketplace → redirected here
  - Handles: activation, plan selection, account setup
- [ ] Integrate with **Marketplace Fulfillment API**
  - Handle subscription lifecycle: activate, suspend, cancel, change plan
  - Webhook endpoints for Microsoft notifications
- [ ] Consider using [SaaS Accelerator](https://github.com/Azure/Commercial-Marketplace-SaaS-Accelerator) to speed this up
- [ ] Set up **usage reporting** (if usage-based pricing in future)

### Certification Preparation
- [ ] **Reviewer sandbox:** dedicated Fabric workspace with sample data + test credentials
- [ ] **Tester's guide:** step-by-step instructions for Microsoft reviewers
- [ ] **Data flow diagrams:** visual of SQL → parse → graph → agent → catalog
- [ ] **Security documentation:** whitepaper + data handling docs (from Phase 1)
- [ ] Verify all Marketplace listing fields are complete
- [ ] Verify privacy policy + terms of use URLs are accessible

### Submit for Certification
- [ ] Submit offer in Partner Center
- [ ] Microsoft runs automated validation
- [ ] Microsoft runs manual compliance review
- [ ] Respond to any certification feedback
- [ ] Iterate until approved
- [ ] **Estimated review time: 2-4 weeks**

---

## Phase 4: Go Live & Growth

*Publish, sell, and grow the business.*

### Launch
- [ ] Offer goes live on Microsoft Commercial Marketplace
- [ ] Verify customers can find, subscribe, and deploy
- [ ] Monitor first subscriptions and disbursements

### Post-Launch
- [ ] Activate **Marketplace Rewards** (marketing support)
- [ ] Track revenue toward **Azure IP co-sell status**
- [ ] First customer onboarding
- [ ] Collect testimonials / case studies
- [ ] Iterate on product based on customer feedback

### Growth Milestones
- [ ] 3 paying customers → validates product-market fit
- [ ] Azure IP co-sell status → Microsoft sales force helps sell
- [ ] Pro tier launch (GraphRAG Engine) → higher revenue per customer
- [ ] Expand beyond healthcare → finance, government, insurance

---

## Founders Hub: How It Helps at Each Phase

| Phase | Founders Hub Benefit |
|---|---|
| **Phase 1 (Foundation)** | Credibility signal, Azure credits for initial setup |
| **Phase 2 (Integration)** | **$1K-$25K Azure credits** pay for Fabric F2 capacity, Azure OpenAI, Key Vault |
| **Phase 2 (Integration)** | **1:1 technical advisory** for architecture review, Purview integration guidance |
| **Phase 2 (Integration)** | **GitHub Enterprise** for CI/CD and code management |
| **Phase 3 (Marketplace)** | **Technical advisory** for Marketplace submission, certification guidance |
| **Phase 3 (Marketplace)** | **ISV Success transition** — structured path from Founders Hub to Marketplace |
| **Phase 4 (Growth)** | **Co-sell readiness** — Microsoft sales force collaboration |
| **Phase 4 (Growth)** | **MACC eligibility** — customers buy with pre-committed Azure budgets |

---

## Key Talking Points (for any conversation)

1. **"We built the brain, not just the plumbing."** The SQL parsing engine handles real-world multi-statement stored procedures — the hard technical problem.

2. **"Fabric-native, BYOT."** Everything runs in the customer's tenant. No data leaves. No external infrastructure.

3. **"Healthcare demands 100% accuracy."** HITL certification ensures stewards validate every definition. The agent refuses to guess.

4. **"The flywheel."** Every user question reinforces known metrics or surfaces unknown ones. Governance grows from usage.

5. **"Purview is paid for but empty."** Most Fabric customers have Purview but nobody uses it. We fill it automatically.

6. **"Co-developing with Microsoft."** We use Fabric Data Agent, Delta tables, MCP protocol, Purview APIs — building deeper into the stack.

7. **"Clean-room IP."** Built on personal infrastructure with synthetic data. Ready for investor due diligence.

8. **"87% automated, 13% human-reviewed."** Transparent, auditable. Parse failures are logged for developer review.

---

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-18 | BYOT model over hosted SaaS | Solo founder, no infrastructure burden |
| 2026-07-18 | Bundled suite over separate products | One listing, one billing, one security audit |
| 2026-07-18 | Collibra + Purview as one wedge | Same persona, same problem, different API |
| 2026-07-19 | Knowledge graph for answers, Purview for discovery | Purview is catalog not query engine |
| 2026-07-19 | sqlparse extractor over LLM extraction | Deterministic, instant, free, 87% success |
| 2026-07-20 | Own Azure tenant for product | IP ownership, admin access, clean demo |
| 2026-07-20 | Founders Hub before Marketplace | Credits, advisory, ISV Success path |
| 2026-07-20 | Plan B: develop locally, deploy when ready | Don't wait for Fabric trial, keep building |
| 2026-07-21 | ScriptDom via pythonnet in Fabric | 100% accurate T-SQL parsing, no microservice, no data leaves tenant |
| 2026-07-21 | Tier 1: Fabric-native first | Coworker validation: "can we use this against Fabric reports?" |
| 2026-07-21 | Tier 2: on-prem SQL Server, Tier 3: Oracle | Same ScriptDom for T-SQL; ANTLR PL/SQL grammar for Oracle |

---

## Quick Reference: What Can Be Done Without Fabric

| Task | Fabric needed? |
|---|---|
| Improve parser / extractor | No — runs locally |
| Write security whitepaper | No |
| Write privacy policy / terms | No |
| Join Partner Center | No |
| Create logo / marketing copy | No |
| Build SaaS landing page scaffold | No |
| Add synthetic sample data | No |
| Write reviewer's guide | No |
| Send admin email (work access) | No |
| Test at work (POC) | Uses work Fabric |
| Record demo video | **Yes — needs own Fabric** |
| Take screenshots | **Yes — needs own Fabric** |
| Test Purview/lineage/audit as admin | **Yes — needs own Fabric** |
| Submit to Marketplace | **Yes — needs reviewer sandbox** |
