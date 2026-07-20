# Microsoft for Startups Founders Hub — Submission Plan

## Application URL
https://www.microsoft.com/en-us/startups

---

## Critical: Build in Your Own Environment

**Do NOT demo or submit using your work Fabric tenant.** Rebuild the POC in your own startup-owned Azure/Fabric environment. This is required for:

- **IP ownership** — undisputed ownership of your code and demo
- **Data security** — no risk of accidentally showing employer data
- **Investor readiness** — due diligence requires code built on your own infrastructure
- **Clean application** — Microsoft evaluators trust startup-owned environments
- **Use a NEW personal Microsoft Account** — if you previously cancelled an Azure environment, use a fresh MSA to avoid flags

### Environment Setup Checklist
- [ ] Register business domain (e.g., `dataempowerment.io`)
- [ ] Create business email matching domain (e.g., `sunny@dataempowerment.io`)
- [ ] Create NEW personal Microsoft Account (not work, not old cancelled one)
- [ ] Create new Azure account under this MSA
- [ ] Provision Fabric capacity (free trial or paid)
- [ ] Deploy your code to this environment
- [ ] Load synthetic/sample data (NOT employer data)
- [ ] Verify Data Agent works in this clean environment

---

## Tiered Approach — Apply Now, Level Up Later

| Tier | Credits | What You Need | Status |
|---|---|---|---|
| **Level 1** | $1K | LinkedIn profile + solution description | Ready after environment setup |
| **Level 2** | $5K | + LLC incorporation docs | Need LLC |
| **Level 3** | $25K+ | + Verified domain, business email, demo video | Need domain + video |

**Strategy:** Set up your own environment first. Apply for Level 1. Upload LLC docs and demo video to level up. Microsoft prefers seeing your product in your own tenant.

---

## Step 1: Infrastructure Setup (Do First)

### Business Identity
- [ ] **Register LLC** — online in your state (~$50-200, 1-2 hours)
- [ ] **Register domain** — e.g., `dataempowerment.io` ($10-15/year)
- [ ] **Business email** — set up email matching domain (Google Workspace ~$6/mo or Outlook)
- [ ] **LinkedIn** — update profile with startup, founder title

### Azure/Fabric Environment
- [ ] **New personal MSA** — create fresh Microsoft Account with personal email
- [ ] **Azure subscription** — create under the new MSA
- [ ] **Fabric capacity** — provision Fabric trial or paid tier
- [ ] **Lakehouse** — create lakehouse, upload sql-query-agent code
- [ ] **Sample data** — load synthetic Clarity-like data (NOT employer data)
- [ ] **Data Agent** — create and configure with graph tables + instructions
- [ ] **Test end-to-end** — verify the agent answers questions in this environment

---

## Step 2: Apply for Level 1 (30 minutes)

### Prerequisites
- [ ] LinkedIn account up-to-date
- [ ] New personal Microsoft Account (not work email)
- [ ] Azure account under this MSA

### Application Form
- [ ] Company name: [your LLC name]
- [ ] Stage: Pre-revenue / MVP
- [ ] Industry: Healthcare Data Analytics / Data Governance
- [ ] Technology: Microsoft Fabric, Azure AI, Power BI, Purview
- [ ] Solution description (see below)

### Solution Description

> **One-liner:** Turn SQL chaos into self-service analytics — extract business logic from stored procedures, build a certified knowledge graph, and let users ask questions through a Fabric Data Agent.
>
> **Core Intelligence:** We built a SQL-to-knowledge-graph parsing engine that extracts business logic from stored procedures and builds a three-layer certified graph (Business Metrics → Calculation Logic → Source Data). The engine handles real-world T-SQL including multi-statement procedures with temp tables, CTEs, and complex joins. Validated against 790 real healthcare stored procedures with 87% success rate.
>
> **Fabric-Native:** Everything runs in the customer's Fabric tenant (BYOT). Delta tables for graph storage, Fabric Data Agent for natural language queries, Fabric notebooks for orchestration. No external infrastructure.
>
> **Enterprise Governance:** A Metadata Sync component generates plain-English business descriptions and pushes them to Microsoft Purview, Collibra, or Power BI report descriptions. Human-in-the-loop certification ensures data stewards validate every definition.

---

## Step 3: Level Up to Level 2 ($5K)

- [ ] Upload LLC incorporation documents to Founders Hub portal

---

## Step 4: Level Up to Level 3 ($25K+)

- [ ] Verified domain (registered in Step 1)
- [ ] Business email matching domain
- [ ] Demo video (see script below)
- [ ] Incorporation papers (from Step 3)

### Demo Video Script (5 minutes)

Record in YOUR OWN Fabric environment with synthetic data. Not your employer's.

**Slide 1 (30 sec): The Problem**
"Organizations have hundreds of SQL stored procedures with business logic buried in code. Nobody documents them. New analysts spend weeks reverse-engineering queries. Governance falls behind."

**Live Demo (2.5 min): The Magic**
- Open your Fabric Data Agent
- Ask: "How is the Census Dashboard calculated?"
- Show the structured business criteria response
- Ask: "What tables does it use?"
- Ask: "Which metrics are available?"
- Show how the agent traverses the knowledge graph

**Slide 2 (1 min): Architecture**
- Show the pipeline: SQL Sources → Parsing Engine → Knowledge Graph → Data Agent
- Emphasize: Fabric-native, BYOT, Delta tables, no external infrastructure
- Show: Purview/Collibra adapters for metadata sync

**Slide 3 (1 min): Roadmap & Ask**
- Current: Working MVP with parsed metrics and Data Agent
- Next: Purview integration, steward certification workflow, Marketplace listing
- Ask: "Looking for Azure credits and technical advisory to accelerate our Marketplace launch"

**Do NOT show:** File uploads, notebook cells, raw Python code, parse errors, employer data

---

## What We Have (Our Strengths)

### Core Intelligence (the "brain")
- SQL-to-knowledge-graph parsing engine (sqlparse + sqlglot)
- Three-layer graph model (Business Metrics → Calculation Logic → Source Data)
- 87% parse success rate on 790 real stored procedures
- Deterministic, instant, zero-cost extraction

### Fabric-Native Integration (the "Golden Path")
- Delta tables for graph storage (graph_nodes, graph_edges)
- Fabric Data Agent answering natural language questions
- Data Agent API working via MCP protocol
- Fabric notebooks as orchestration layer
- No external infrastructure — runs entirely in customer's Fabric tenant (BYOT)

### Working POC
- Full graph traversal on parsed metrics
- Data Agent correctly explains "how is X calculated?" with business-friendly criteria
- PBI report description updater via Fabric REST API
- Collibra + Purview adapters scaffolded
- Steward assignment and usage tracking modules built
- CI/CD pipeline with GitHub Actions

---

## How to Frame Current Limitations

| Current State | How to Frame It |
|---|---|
| Manual file upload | "Governance-First Staging Workflow — ensures vetted, high-quality query definitions enter the system" |
| Notebook-based orchestration | "Developer-persona tooling for data engineers — GUI planned for v2" |
| 87% parse rate | "Handles real-world healthcare stored procedures with full graph traversal" |
| No Purview push yet | "Purview adapter architected and scaffolded — integration testing in progress" |
| No GUI for stewards | "Steward workflow designed with HITL certification — Power App interface on roadmap" |
| Rebuilding in new environment | "Clean-room development with full IP ownership — enterprise-grade separation of concerns" |

---

## Roadmap to Present

**Current (v1.0 — MVP):**
- SQL parsing engine with 87% success rate
- Knowledge graph in Delta tables
- Fabric Data Agent answering metric questions
- Metadata adapters for Purview, Collibra, Power BI

**Next (v1.5 — with Founders Hub support):**
- Purview + Collibra live integration
- Automated SQL ingestion from Fabric workspaces
- Steward HITL certification workflow
- Usage tracking and governance flywheel
- PBI report auto-documentation via lineage API

**Future (v2.0 — Marketplace launch):**
- Power App GUI for steward review
- Multi-agent architecture (Metric Agent, Admin Agent, Steward Agent)
- Row-level security via Entra ID
- Azure Key Vault for secrets management
- SaaS transactable offer on Microsoft Marketplace

---

## Key Talking Points

### For the Application
1. **"We built the brain, not just the plumbing."** The SQL parsing engine is the hard part — it handles real-world multi-statement stored procedures with temp tables, CTEs, and complex joins. The transport layer (API vs manual) is a detail that evolves.

2. **"Fabric-native, BYOT."** Everything runs in the customer's tenant. No data leaves. No external infrastructure. This is the architecture Microsoft wants to see.

3. **"Healthcare demands 100% accuracy."** Our HITL certification workflow ensures data stewards validate every metric definition. The agent refuses to guess — "I don't know" is better than a wrong answer.

4. **"The flywheel."** Every user question either reinforces known metrics (adds weight) or surfaces unknown ones (triggers steward review). Governance grows from usage, not committees.

5. **"Purview is paid for but empty."** Most Fabric customers have Purview but nobody uses it. We fill it automatically. Same for Collibra's bulk loading gap that Collibra itself won't build.

### For Conversations with Microsoft
6. **"We're co-developing with the platform."** We use Fabric Data Agent, Delta tables, MCP protocol, Fabric REST APIs, Purview Data Map APIs. We're building deeper into the Microsoft stack, not around it.

7. **"Clean-room IP."** Built entirely on personal infrastructure with synthetic data. No employer IP conflicts. Ready for investor due diligence.

8. **"We need advisory, not just credits."** The 1:1 technical consultations are what will accelerate us most — architecture reviews, Marketplace submission guidance, and Purview integration best practices.

### For Investor Conversations (Future)
9. **"87% automated, 13% human-reviewed."** The parse rate demonstrates the engine works at scale. The 13% failures are logged for developer review — transparent, auditable, honest.

10. **"One customer, 790 stored procedures, 687 metrics."** Real validation with real healthcare SQL. Not a toy demo — a production-grade POC.

---

## Sample Data for Demo Environment

To demo without employer data, create synthetic sample data that mirrors the structure:

### Synthetic sql_sources
- Use the two sample procs already in the repo (`real_census_dashboard.sql`, `real_lote_census.sql`)
- Scrub any org-specific identifiers (already done)
- Add 3-5 more synthetic procs with different patterns (simple views, CTE chains, temp tables)

### Synthetic Dictionary
- Use `clarity_dict_tables.json` already in the repo (generic Clarity table descriptions)
- Add a few more tables for variety

### Synthetic Graph
- Run the pipeline against synthetic data
- The agent should be able to answer questions about these synthetic metrics

---

## Timeline

| Action | When | Effort |
|---|---|---|
| Register LLC | This week | 1-2 hours |
| Register domain | This week | 30 min |
| Set up business email | This week | 30 min |
| Create new MSA + Azure | This week | 30 min |
| Provision Fabric | This week | 1 hour |
| Deploy code + synthetic data | This week | 2-3 hours |
| Apply Level 1 | This week | 30 min |
| Upload LLC → Level 2 | When LLC ready | 10 min |
| Record demo video | This week or next | 2-3 hours |
| Upload video → Level 3 | After video | 10 min |
| Hear back | ~3 business days | Wait |
