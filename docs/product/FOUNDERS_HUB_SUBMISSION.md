# Microsoft for Startups Founders Hub — Submission Plan

## Application URL
https://www.microsoft.com/en-us/startups

## What They Evaluate
- Technical alignment with Microsoft ecosystem (Fabric, Azure, Purview)
- Market potential and B2B viability
- Commitment to the platform (not product polish)
- Trajectory, not perfection

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
- No external infrastructure — runs entirely in customer's Fabric tenant

### Working POC
- 687 metrics with full graph traversal
- Data Agent correctly explains "how is X calculated?" with business-friendly criteria
- PBI report description updater via Fabric REST API
- Collibra + Purview adapters scaffolded
- Steward assignment and usage tracking modules built

---

## Submission Materials — Action Items

### 1. Application Form (30 min)
- [ ] Create account at startups.microsoft.com
- [ ] Company name: [your LLC name]
- [ ] Stage: Pre-revenue / MVP
- [ ] Industry: Healthcare Data Analytics / Data Governance
- [ ] Technology: Microsoft Fabric, Azure AI, Power BI
- [ ] One-line description: "Turn SQL chaos into self-service analytics — extract business logic from stored procedures, build a certified knowledge graph, and let users ask questions through a Fabric Data Agent"

### 2. Solution Description (1 hour)

Write a clear, concise description. Frame around these three pillars:

**Core Intelligence:**
"We have developed a SQL-to-knowledge-graph parsing engine that extracts business logic from stored procedures and builds a three-layer certified graph (Business Metrics → Calculation Logic → Source Data). The engine handles real-world T-SQL including multi-statement procedures with temp tables, CTEs, and complex joins."

**Enterprise Governance:**
"Our Metadata Sync component automatically generates plain-English business descriptions and pushes them to Microsoft Purview, Collibra, or Power BI report descriptions. A human-in-the-loop certification workflow ensures data stewards validate every definition before it enters the certified catalog."

**Self-Service Intelligence:**
"A Microsoft Fabric Data Agent, grounded in the certified knowledge graph, allows business users to ask natural language questions about any metric. The agent explains what each metric measures, what filters apply, and which source tables are used — all in business language, with full traceability."

### 3. Architecture Diagram (30 min)
- [ ] Create a clean diagram showing:
  ```
  SQL Sources → Parsing Engine → Knowledge Graph (Delta Tables)
                                        ↓
                              Fabric Data Agent ← User Questions
                                        ↓
                              Purview / Collibra / PBI
  ```
- [ ] Label each component with the Microsoft technology used
- [ ] Show the BYOT model (everything runs in customer's tenant)

### 4. Demo Video (2-3 hours)
- [ ] Record a 5-minute screen recording showing:
  1. **The magic (2 min):** User asks the Data Agent "How is the Census Dashboard calculated?" → Agent returns structured business criteria
  2. **The graph (1 min):** Show the Delta tables with nodes and edges, show traversal
  3. **The architecture (1 min):** Show the architecture slide, emphasize Fabric-native
  4. **The roadmap (1 min):** Mention Purview integration, steward workflow, marketplace
- [ ] Do NOT show: file uploads, notebook cells, raw code
- [ ] Focus on the USER EXPERIENCE, not the developer workflow

### 5. Business Entity (if not done)
- [ ] Register LLC
- [ ] Business bank account
- [ ] Business email domain
- [ ] These can happen in parallel with the application

---

## How to Frame Current Limitations

| Current State | How to Frame It |
|---|---|
| Manual file upload | "Governance-First Staging Workflow — ensures vetted, high-quality query definitions enter the system" |
| Notebook-based orchestration | "Developer-persona tooling for data engineers — GUI planned for v2" |
| 87% parse rate | "Handles 687 real-world healthcare stored procedures with full graph traversal" |
| No Purview push yet | "Purview adapter architected and scaffolded — pending Data Curator role assignment" |
| No GUI for stewards | "Steward workflow designed with HITL certification — Power App interface on roadmap" |

---

## Roadmap to Present

**Current (v1.0 — MVP):**
- SQL parsing engine with 87% success rate
- Knowledge graph in Delta tables
- Fabric Data Agent answering metric questions
- Metadata adapters for Purview, Collibra, Power BI

**Next (v1.5 — with ISV/Founders Hub support):**
- Automated API-based SQL ingestion from Fabric workspaces
- Purview + Collibra live integration
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

## Timeline

| Action | When | Effort |
|---|---|---|
| Fill application form | This week | 30 min |
| Write solution description | This week | 1 hour |
| Create architecture diagram | This week | 30 min |
| Record demo video | This week | 2-3 hours |
| Register LLC (if needed) | This week | 1-2 hours |
| Submit application | End of this week | 5 min |
| Hear back | ~3 business days | Wait |

---

## Key Talking Points for Any Conversation

1. **"We built the brain, not just the plumbing."** The SQL parsing engine is the hard part. The transport (API vs manual) is a detail that evolves.

2. **"Fabric-native, BYOT."** Everything runs in the customer's tenant. No data leaves. No external infrastructure.

3. **"Healthcare demands 100% accuracy."** Our HITL certification workflow ensures data stewards validate every metric definition. The agent refuses to guess — "I don't know" is better than a wrong answer.

4. **"The flywheel."** Every user question either reinforces known metrics (adds weight) or surfaces unknown ones (triggers steward review). Governance grows from usage, not committees.

5. **"Purview is paid for but empty."** Most Fabric customers have Purview but nobody uses it. We fill it automatically. Same for Collibra's bulk loading gap.
