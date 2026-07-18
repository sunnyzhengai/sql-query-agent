# Architecture

## Three-Layer Graph Model

This system builds a **graph of business logic** from SQL, stored in Delta tables, and uses it to ground a Fabric Data Agent so it can answer metric questions with 100% traceable accuracy.

```
┌─────────────────────────────────┐
│  CANONICAL LAYER                │
│  Business metrics (e.g. ER_LOS) │
│  Owners: steward + developer    │
│  Usage weight (query count)     │
└──────────────┬──────────────────┘
               │ canonical_to_transform
┌──────────────▼──────────────────┐
│  TRANSFORMATION LAYER           │
│  CTE pipeline steps             │
│  Stores: sql_fragments (NOT     │
│  full SQL — LLM assembles)      │
│  Edges: transform_to_transform  │
└──────────────┬──────────────────┘
               │ transform_to_technical
┌──────────────▼──────────────────┐
│  TECHNICAL LAYER                │
│  Physical tables + columns      │
│  Enriched with data dictionary  │
│  descriptions at build time     │
├─────────────────────────────────┤
│  ◄── DIMENSION NODES            │
│  Branch sideways for dynamic    │
│  parameter filtering            │
└─────────────────────────────────┘
```

## User Question Flow

When a user asks the Data Agent a question, two things happen in parallel:

```
User asks: "What is the average ER length of stay?"
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
  KNOWLEDGE GRAPH           PURVIEW
  (ground truth)         (report discovery)
        │                       │
        │ Traverse certified    │ Search for existing
        │ path, assemble        │ reports/dashboards
        │ answer from           │ that cover this
        │ sql_fragments         │ metric
        │                       │
        ▼                       ▼
  ┌─────────────┐       ┌──────────────────┐
  │ ANSWER:     │       │ "BTW, the Monthly│
  │ 4.2 hours   │       │ OR Dashboard     │
  │ (certified) │       │ already tracks   │
  │             │       │ this — here's    │
  │ Source:     │       │ the link"        │
  │ encounter + │       │                  │
  │ department  │       │ OR:              │
  │ tables      │       │ "No existing     │
  │             │       │ report found"    │
  └─────────────┘       └──────────────────┘
        │
        ▼
  Usage weight incremented
  on the metric node
```

### Two Paths for Every Question

**Path A: Known Logic (certified path exists)**
1. Agent finds metric in the knowledge graph
2. Assembles answer from sql_fragments via the transformation chain
3. Checks Purview for existing reports covering this metric
4. Returns answer + report link (if found) + lineage
5. Increments usage weight on the canonical node

**Path B: Unknown Logic (no certified path)**
1. Agent says "I don't have a certified definition for that yet"
2. Triggers notification to data steward
3. Checks Purview for existing reports (may still find something useful)
4. Steward reviews, certifies -> new node added to graph
5. Next time anyone asks, Path A handles it

### Why Knowledge Graph for Answers, Purview for Discovery

The knowledge graph and Purview serve different roles:

| | Knowledge Graph | Purview |
|---|---|---|
| **Role** | The brain — answers questions | The librarian — finds existing reports |
| **Contains** | sql_fragments, transformation chains, dimension filters | Report/dataset metadata, lineage, classifications |
| **Strength** | Composable, executable logic | Catalog of everything in the org |
| **Weakness** | Only knows certified metrics | Metadata only — can't compute answers |

Purview is a catalog, not a query engine. It stores metadata *about* data but not the calculation logic, sql_fragments, or dimensional filtering rules the agent needs to assemble a query. The knowledge graph stores all of that.

But Purview excels at discovery: "Does a report already exist that answers this?" This reduces redundant report requests and helps users find dashboards they didn't know about.

## Design Decisions

### Why Delta tables over Neo4j?
Stay in the Microsoft Fabric ecosystem. No external graph DB to manage, no additional auth/networking. Delta tables are queryable from Notebooks, Data Agent, and Power BI natively.

### Why sql_fragments, not full SQL blobs?
Full SQL is brittle and hard to version. Fragments are minimal logic snippets tied to individual CTE steps. The LLM assembles complete queries from fragments + templates at query time. This makes the graph composable and auditable.

### Why two-stage HITL certification?
Healthcare requires 100% accuracy. Developer certifies technical correctness (does the SQL compute the right thing?). Steward certifies business correctness (is this the right metric definition?). Both must pass before a metric enters the certified graph.

### Why "I don't know" over guessing?
If no certified graph path exists for a question, the agent refuses. In healthcare, a wrong answer is worse than no answer. The graph is the guardrail — and "I don't know" triggers the certification process that fills the gap.

### Why Knowledge Graph grounds answers, not Purview?
Purview is a metadata catalog — it knows *about* data but can't compute answers. The knowledge graph stores composable sql_fragments, transformation chains, and dimension filters that the agent needs to actually assemble and execute queries. Purview's role is report discovery: surfacing existing dashboards that already cover a user's question.

## Module Map

```
src/
├── config.py              # Load org_config.yaml (gitignored)
├── models.py              # Pydantic models: GraphNode, GraphEdge, enums
├── dictionary.py          # Data dictionary loader
├── pipeline.py            # End-to-end graph build orchestration
├── parser/
│   └── sql_parser.py      # SQL -> ParsedSQL (CTEs, table/column refs)
├── graph/
│   ├── builder.py         # Build graph from parsed SQL + dictionary
│   └── traversal.py       # Traverse graph to answer metric questions
├── extractor/
│   ├── connection.py      # SQL Server connection (Fabric JDBC / local pyodbc)
│   ├── discovery.py       # Discover views/procs from sys catalogs
│   ├── extractor.py       # Orchestrator: discover -> diff -> produce sql_sources
│   └── tracker.py         # Change detection via SHA-256 hashing
└── adapters/
    ├── base.py            # CatalogAdapter protocol + MetadataRecord models
    ├── metadata_generator.py  # Graph nodes -> catalog-agnostic MetadataRecords
    ├── publisher.py       # Orchestrate publishing to multiple catalogs
    ├── purview.py         # Microsoft Purview Data Map adapter
    └── collibra.py        # Collibra REST API adapter
```

## Data Flow

```
SQL Sources ──► sql_parser ──► ParsedSQL
                                  │
Data Dictionary ──────────────────┤
                                  ▼
                           GraphBuilder
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼              ▼
             Delta Tables   MetadataGenerator   (future: more)
            (nodes + edges)       │
                    │        ┌────┴────┐
                    ▼        ▼         ▼
             GraphTraverser  Purview   Collibra
                    │        Adapter   Adapter
                    ▼
             Fabric Data Agent
              (user questions)
                    │
              ┌─────┴─────┐
              ▼            ▼
        Knowledge     Purview Lookup
        Graph Answer   (existing reports)
```

## Deployment Models

The product is packaged as a **Python library (.whl)** that runs inside the customer's
Microsoft Fabric environment (BYOT — Bring Your Own Tenant).

### Current: Fabric Notebook + Library

```
Customer's Fabric Tenant
├── Lakehouse (their data)
├── Notebook (imports our library)
│   └── pip install sql-query-agent.whl
├── Delta Tables (graph_nodes, graph_edges)
└── Data Agent (grounded in the graph)
```

- Simplest to build and maintain
- Fabric customers already comfortable with Notebooks
- Customer pays for Fabric compute, we charge for the library license

### Future Option: Azure Managed Application

Package as an Azure Managed Application for one-click enterprise deployment:
- Customer deploys from Marketplace into their resource group
- Governed by our deployment template (ARM/Bicep)
- More "productized" than a raw .whl — easier for enterprise procurement
- Consider when customer base grows beyond early adopters
