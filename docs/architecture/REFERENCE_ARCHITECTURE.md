# AIVIA Reference Architecture

**Audience:** Marketplace listing, Microsoft certification reviewers, and
co-sell bill of materials. The security-focused companion view lives in
[ARCHITECTURE.md](ARCHITECTURE.md) ("System at a Glance"); this document
is the product view: both tiers, all source connectors, and the Azure
consumption footprint. This mermaid is the source of truth — regenerate
designed/PDF versions from it, never the reverse. Current designed
export: `docs/product/AIVIA Architecture Diagram V2.0.pdf`.

```mermaid
flowchart TB
    subgraph ESTATE["CUSTOMER'S CLOUD ESTATE — no data ever reaches the vendor"]
        subgraph SRC["SQL logic sources"]
            TSQL["SQL Server / Azure SQL<br/>T-SQL procs & views — SHIPPED"]
            DBT["dbt projects (dbt-fabric)<br/>manifest.json: compiled T-SQL + native DAG — NEXT"]
            SM["Fabric semantic models<br/>TMDL: tables · DAX measures · lineage — NEXT"]
            PBIR["Power BI reports (DevOps git)<br/>TMDL/DAX report lineage — SHIPPED"]
            DBX["Azure Databricks<br/>SQL views + Unity Catalog — ROADMAP"]
            SNOW["Snowflake<br/>GET_DDL views/tasks — ROADMAP"]
        end
        subgraph FABRIC["Microsoft Fabric (customer capacity)"]
            FILES["SQL files + data dictionary<br/>(Lakehouse Files)"]
            ENGINE["AIVIA Metadata Engine<br/>parse (ScriptDom) · PHI scan ·<br/>three-layer knowledge graph +<br/>business names & terms<br/>(Delta + Labeled Property Graph)"]
            SEMCAT["Semantic catalog — SHIPPED<br/>(Eventhouse: catalog + embeddings +<br/>semantic_search() KQL function)<br/>live 2026-08-10, ADR 0030/0032"]
            MAGENT["AIVIA Agent — SHIPPED (ADR 0035)<br/>LLM conversation over five deterministic<br/>tools · code-stamped Basis every answer ·<br/>web chat (App Service) · Teams next"]
            FDAOPT["Fabric Data Agent — OPTIONAL<br/>customer-configured over the same<br/>certified tables; not the product's<br/>answer path"]
            subgraph SS["AIVIA Analytics Self-Service — ROADMAP"]
                COMPILER["Certified semantic layer compiler<br/>graph → generated views & measures<br/>(dimension layer = filter vocabulary)"]
                SAGENT["Analytics agent<br/>'What WAS this metric last month?'<br/>NL2SQL over certified views only"]
            end
        end
        AOAI["Customer's own Azure OpenAI<br/>build time: descriptions + embeddings<br/>(PHI-redacted) · ask time: the agent's<br/>conversation + question embeddings under<br/>the user's identity — no stored key"]
        PURVIEW["Microsoft Purview"]
        COLLIBRA["Collibra (optional)"]
    end
    USERS["Business users — plain English<br/>endorse terms (citizen stewardship)"]

    TSQL --> FILES
    DBT --> FILES
    SM --> FILES
    PBIR --> FILES
    DBX -.-> FILES
    SNOW -.-> FILES
    FILES --> ENGINE
    ENGINE --> SEMCAT
    ENGINE --> MAGENT
    SEMCAT --> MAGENT
    ENGINE <--> AOAI
    MAGENT <--> AOAI
    ENGINE -->|"asset descriptions +<br/>glossary terms (multi-asset)"| PURVIEW
    ENGINE -.-> COLLIBRA
    ENGINE -.optional:<br/>compatible export.-> FDAOPT
    ENGINE --> COMPILER
    COMPILER --> SAGENT
    USERS --> MAGENT
    USERS -.-> FDAOPT
    USERS --> SAGENT
```

## Source connector tiers

| Source | What's extracted | Dialect / parser | Status |
|---|---|---|---|
| SQL Server / Azure SQL | Stored procs, views (live extraction or file drop) | T-SQL / ScriptDom | **Shipped** |
| Power BI reports (DevOps git) | TMDL + DAX report lineage | TMDL (structured text) | **Shipped** |
| dbt (dbt-fabric) | `manifest.json`: compiled SQL, model DAG, docs, tests | Compiled T-SQL / ScriptDom (DAG comes free from `ref()` edges) | Next — cheapest connector; manifest is JSON, no Jinja parsing |
| Fabric semantic models | TMDL: tables, partitions, relationships, DAX measures | TMDL now; DAX measure parsing is its own lane (ADR 0001) | Next — lineage first, DAX semantics later |
| Azure Databricks | SQL views + Unity Catalog DDL (**scope: SQL only** — PySpark/DLT notebook logic is a separate future problem) | Spark SQL / sqlglot dialect | Roadmap |
| Snowflake | `GET_DDL()`: views, materialized views, tasks, dynamic tables | Snowflake SQL / sqlglot dialect | Roadmap |

**2026-08-08 additions:** business names + report links flow inside the
Metadata Engine (no topology change); the **Purview arrow now carries
glossary terms** at term grain, one term per definition, multi-asset
assigned (ADR 0031); the **semantic catalog** node is settled — engine
DECIDED by live probes 2026-08-08 (SQL-DB path failed at the agent's
validation layer; **Eventhouse PASSED end to end**, ADR 0030) — still
roadmap-yellow because the product pipeline that fills it isn't built.
When it ships, the Azure OpenAI arrow gains an **ask-time** leg
(question-phrase embeddings, user impersonation, no stored key) — a
security-story change the whitepaper must state explicitly: user
question text, not SQL fragments, reaches the customer's own endpoint
at ask time. Topology is now settled — the Lucid/designed PDF should be
updated to match on its next pass (add the Eventhouse semantic-catalog
box, roadmap style).

## The two tiers, one sentence each

- **Metadata Engine (shipped):** parses the SQL estate into a certified,
  steward-owned knowledge graph and answers *"how is this calculated?"*
  with named accountability — refusing beyond the graph (ADR 0005/0021).
- **Analytics Self-Service (roadmap):** a build-time **compiler**, not a
  new runtime — it emits each certified metric's assembled SQL (ADR 0003
  fragments) as generated views/measures, parameterized by the dimension
  layer (ADR 0029); the analytics agent runs plain NL2SQL over those
  views, so the habitual query IS the certified query (the ADR 0020
  lesson applied to execution). Runtime is 100% Microsoft's engine.

## Azure consumption footprint (co-sell annotation)

Field-seller-relevant consumption this solution drives, in order:
**Fabric capacity** (pipeline + Eventhouse + graph), **Azure
OpenAI** (customer's own endpoint, build-time), **Microsoft Purview**
(catalog publish), **Azure DevOps** (git-integrated workspaces, TMDL
lineage), **Azure SQL / SQL Server** (source estates). Snowflake and
Databricks connectors pull external SQL estates *into* Fabric governance
— workload gravity toward Microsoft, not away.

## Review-critical properties (certification / attestation)

1. Everything runs in the customer's tenant on customer capacity; the
   vendor ships a library (.whl) and holds no data, no keys, no service.
2. The only AI dependency is the **customer's own Azure OpenAI**
   endpoint; fragments are PHI-redacted (deterministic rules, ADR 0025)
   before any prompt is built; interactive answers never call out.
3. Agent answers are grounded exclusively in the certified graph, with
   certification state and named owners disclosed (ADR 0021) — refusal
   over fabrication (ADR 0005).
