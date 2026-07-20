# Microsoft for Startups Founders Hub — Submission Plan

## Application URL
https://www.microsoft.com/en-us/startups

---

## Tiered Approach — Start Today, Level Up Later

You don't need everything ready to apply. Microsoft scales requirements by benefit tier:

| Tier | Credits | What You Need | Status |
|---|---|---|---|
| **Level 1** | $1K | LinkedIn profile + solution description | **Ready now** |
| **Level 2** | $5K | + Business entity (LLC incorporation docs) | Need LLC |
| **Level 3** | $25K+ | + Verified domain, business email, demo video, incorporation | Need LLC + video |

**Strategy:** Apply today for Level 1 with LinkedIn only. Upload LLC and demo video later to unlock higher tiers. You get platform access immediately.

---

## Step 1: Apply Today (Level 1 — 30 minutes)

### Prerequisites
- [ ] **LinkedIn account** — up-to-date profile with career history (Microsoft verifies identity through this)
- [ ] **Personal Microsoft account** — use personal email (@outlook.com or @gmail.com), NOT work/school email
- [ ] **Azure account** — create new if needed (free)

### Application Form
- [ ] Company name: [your LLC name, or personal name if LLC not yet formed]
- [ ] Stage: Pre-revenue / MVP
- [ ] Industry: Healthcare Data Analytics / Data Governance
- [ ] Technology: Microsoft Fabric, Azure AI, Power BI, Purview
- [ ] Solution description (see below)

### Solution Description (for Level 1)

> **One-liner:** Turn SQL chaos into self-service analytics — extract business logic from stored procedures, build a certified knowledge graph, and let users ask questions through a Fabric Data Agent.
>
> **Core Intelligence:** We built a SQL-to-knowledge-graph parsing engine that extracts business logic from stored procedures and builds a three-layer certified graph (Business Metrics → Calculation Logic → Source Data). The engine handles real-world T-SQL including multi-statement procedures with temp tables, CTEs, and complex joins. Validated against 790 real healthcare stored procedures with 87% success rate.
>
> **Fabric-Native:** Everything runs in the customer's Fabric tenant (BYOT). Delta tables for graph storage, Fabric Data Agent for natural language queries, Fabric notebooks for orchestration. No external infrastructure.
>
> **Enterprise Governance:** A Metadata Sync component generates plain-English business descriptions and pushes them to Microsoft Purview, Collibra, or Power BI report descriptions. Human-in-the-loop certification ensures data stewards validate every definition.

---

## Step 2: Level Up to Level 2 ($5K credits)

### What You Need
- [ ] **Register LLC** — can do online in your state (~$50-200, 1-2 hours)
- [ ] **Upload incorporation documents** to Founders Hub portal
- [ ] That's it — the solution description from Level 1 carries over

---

## Step 3: Level Up to Level 3 ($25K+ credits)

### What You Need
- [ ] **Business domain** — register a domain (e.g., dataempowerment.io)
- [ ] **Business email** — email matching your domain (e.g., sunny@dataempowerment.io)
- [ ] **Demo video** (5-10 minutes) — see script below
- [ ] **Incorporation papers** — from Step 2

### Demo Video Script (5 minutes)

**Slide 1 (30 sec): The Problem**
"Organizations have hundreds of SQL stored procedures with business logic buried in code. Nobody documents them. New analysts spend weeks reverse-engineering queries. Governance falls behind."

**Live Demo (2.5 min): The Magic**
- Open Fabric Data Agent
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
- Current: Working MVP with 687 parsed metrics
- Next: Purview integration, steward certification workflow, marketplace listing
- Ask: "Looking for Azure credits and technical advisory to accelerate our Marketplace launch"

**Do NOT show:** File uploads, notebook cells, raw Python code, parse errors

---

## What We Have (Our Strengths)

### Core Intelligence (the "brain")
- SQL-to-knowledge-graph parsing engine (sqlparse + sqlglot)
- Three-layer graph model (Business Metrics → Calculation Logic → Source Data)
- 87% parse success rate on 790 real Epic Clarity stored procedures
- Deterministic, instant, zero-cost extraction

### Fabric-Native Integration (the "Golden Path")
- Delta tables for graph storage (graph_nodes, graph_edges)
- Fabric Data Agent answering natural language questions
- Data Agent API working via MCP protocol
- Fabric notebooks as orchestration layer
- No external infrastructure — runs entirely in customer's Fabric tenant (BYOT)

### Working POC
- 687 metrics with full graph traversal
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
| 87% parse rate | "Handles 687 real-world healthcare stored procedures with full graph traversal" |
| No Purview push yet | "Purview adapter architected and scaffolded — pending access role assignment" |
| No GUI for stewards | "Steward workflow designed with HITL certification — Power App interface on roadmap" |

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

1. **"We built the brain, not just the plumbing."** The SQL parsing engine is the hard part. The transport (API vs manual) is a detail that evolves.

2. **"Fabric-native, BYOT."** Everything runs in the customer's tenant. No data leaves. No external infrastructure.

3. **"Healthcare demands 100% accuracy."** Our HITL certification workflow ensures data stewards validate every metric definition. The agent refuses to guess — "I don't know" is better than a wrong answer.

4. **"The flywheel."** Every user question either reinforces known metrics (adds weight) or surfaces unknown ones (triggers steward review). Governance grows from usage, not committees.

5. **"Purview is paid for but empty."** Most Fabric customers have Purview but nobody uses it. We fill it automatically. Same for Collibra's bulk loading gap.

---

## Timeline

| Action | When | Effort |
|---|---|---|
| Apply Level 1 (LinkedIn + description) | **Today** | 30 min |
| Register LLC | This week | 1-2 hours |
| Upload LLC docs → Level 2 | This week | 10 min |
| Create architecture diagram | This week | 30 min |
| Record demo video | This week | 2-3 hours |
| Upload video → Level 3 | This week | 10 min |
| Hear back | ~3 business days | Wait |
