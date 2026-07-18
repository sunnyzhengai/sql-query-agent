# Product Positioning & Talking Points

Key framing, messaging, and strategic options for the Data Empowerment Suite.
Use these when writing Marketplace copy, investor conversations, or customer pitches.

---

## What We Are

### The Framing

**We are a "Fabric Accelerator" — not a SaaS, not a chatbot.**

The product is a **Knowledge Graph Generator for Fabric Data Agents**. It's a Python library that customers install into their own Fabric environment. It parses their existing SQL, builds a certified knowledge graph, and makes their Data Agent dramatically more accurate.

**Why this framing matters:**
- "Accelerator" signals native Fabric integration — customers trust Fabric-native tools
- "Generator" signals automation — it does the work for you
- "Knowledge Graph" signals intelligence — this isn't just a metadata scraper
- Avoids "chatbot" stigma — this is infrastructure, not a toy

### The One-Liner

> "Turn your existing SQL into a certified knowledge graph that makes your Fabric Data Agent 100% accurate and traceable."

### The Problem Statement

> "Your organization has 1,000+ SQL queries with business logic buried in code. Your Data Agent hallucinates because it has no governed context. Your governance team creates definitions nobody uses. We fix all three problems with one tool."

---

## The Value Proposition (For Different Audiences)

### For Data Governance Leaders
- "Stop maintaining spreadsheets of business definitions. Let usage build your catalog automatically."
- "Bulk-load report metadata into Collibra and Purview — the feature Collibra told you they won't build."
- Key pain: manual term creation is slow (50/year), this does 250+ and accelerating

### For BI / Analytics Leaders
- "Eliminate the 6-week report backlog. Let users ask the Data Agent and get certified answers in seconds."
- "Know exactly which metrics your organization cares about — usage-weighted demand signals."
- Key pain: users waiting for IT, conflicting metric definitions

### For IT / Architecture Leaders
- "Fabric-native, BYOT, zero infrastructure. Your code runs in your tenant. Your data never leaves."
- "Extends what you already own — Fabric, Purview, Power BI. No new systems to manage."
- Key pain: vendor sprawl, data sovereignty concerns, integration complexity

### For Clinical / Medical Directors (Healthcare)
- "Surgeons can ask 'What's my FCOTS rate?' and see only their own data. No IT ticket. No privacy concerns."
- "Same certified metric, personalized access. One source of truth for 1:1 coaching."
- Key pain: sensitive performance data, can't share dashboards, bottleneck on IT

---

## Strategic Options to Keep in Mind

### Open-Source Core + Paid Managed Experience

**Option (not decided — preserve for future):**
Open-source the core parsing engine (SQL -> knowledge graph), charge for:
- The managed SaaS experience (auto-updating graph, usage analytics dashboard)
- Enterprise security wrappers (Entra ID integration, RBAC, audit trails)
- Catalog adapters (Purview, Collibra connectors)
- Premium support (implementation consulting)

**Why consider it:**
- Open-source builds community and trust
- Enterprises pay for reliability and support, not code
- Creates a moat through adoption — if you're the standard, you win

**Why defer it:**
- Solo founder — can't support a community yet
- BYOT model already gives enterprise trust
- Open-sourcing prematurely gives competitors a head start

### Azure Managed Applications (Deployment Path)

**Option (alternative to pure library/.whl distribution):**
Package as an Azure Managed Application:
- Customer deploys from Marketplace into their resource group
- Governed by your deployment template
- They pay for Fabric compute, you charge for the application license
- "Managed" because you control the template, but they own the infrastructure

**Why consider it:**
- More "productized" than a raw .whl file
- Microsoft has tooling for this (ARM templates, Bicep)
- Easier for enterprise procurement (one-click deploy)

**Why the .whl/Notebook approach may be better initially:**
- Simpler to build and maintain as a solo founder
- Fabric customers are already comfortable with Notebooks
- Less infrastructure to manage on your side

### AI-Powered Customer Support

**Planned feature:**
Build an AI support tool that handles 80%+ of common user questions about the product itself.

**Why:**
- Solo founder cannot provide 24/7 support
- Eating your own dogfood — use the same knowledge graph approach for your own product docs
- Reduces support burden to: documentation (automated) + premium consulting (paid)

**Implementation:**
- Knowledge graph of product documentation and FAQs
- Data Agent grounded in your own docs
- "I don't know" triggers escalation to you (same flywheel pattern)

---

## Competitive Positioning

### What We're NOT
- Not a replacement for Purview or Collibra (we complement them)
- Not a BI tool (we make existing BI tools smarter)
- Not a generic AI chatbot (we're grounded in certified logic — no hallucination)
- Not a data catalog (we're the engine that makes catalogs useful)

### What Makes This Different
1. **Starts from existing SQL** — most governance tools require manual input. We extract logic that already exists.
2. **Usage-driven governance** — governance grows from demand, not committees. The flywheel.
3. **Certified accuracy** — two-stage HITL (developer + steward). "I don't know" over guessing.
4. **Fabric-native** — not a bolt-on. Runs inside the customer's tenant using their existing infrastructure.
5. **The Collibra gap** — Collibra customers have been asking for bulk report metadata loading. Collibra said no. We said yes.

---

## Pricing Anchors

Don't sell hours of engineering time. Sell outcomes.

| What they'd pay without you | What you charge |
|---|---|
| 1 FTE governance analyst ($80K+/yr) maintaining definitions manually | $500-1,000/month |
| 6-week backlog per report request (opportunity cost) | Instant answers |
| 3 conflicting definitions per metric (audit risk) | One certified source |
| Collibra professional services for bulk loading ($$$) | Included in Basic plan |

**Anchor the conversation in value, not cost.** If your tool saves a governance team 20 hours/month, even $1,000/month is a 90%+ discount versus hiring another analyst.
