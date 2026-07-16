# Architecture

## Three-Layer Graph Model

This system builds a **graph of business logic** from SQL, stored in Delta tables, and uses it to ground a Fabric Data Agent so it can answer metric questions with 100% traceable accuracy.

```
┌─────────────────────────────────┐
│  CANONICAL LAYER                │
│  Business metrics (e.g. ER_LOS) │
│  Owners: steward + developer    │
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

## Design Decisions

### Why Delta tables over Neo4j?
Stay in the Microsoft Fabric ecosystem. No external graph DB to manage, no additional auth/networking. Delta tables are queryable from Notebooks, Data Agent, and Power BI natively.

### Why sql_fragments, not full SQL blobs?
Full SQL is brittle and hard to version. Fragments are minimal logic snippets tied to individual CTE steps. The LLM assembles complete queries from fragments + templates at query time. This makes the graph composable and auditable.

### Why two-stage HITL certification?
Healthcare requires 100% accuracy. Developer certifies technical correctness (does the SQL compute the right thing?). Steward certifies business correctness (is this the right metric definition?). Both must pass before a metric enters the certified graph.

### Why "I don't know" over guessing?
If no certified graph path exists for a question, the agent refuses. In healthcare, a wrong answer is worse than no answer. The graph is the guardrail.

## Module Map

```
src/
├── config.py          # Load org_config.yaml (gitignored)
├── models.py          # Pydantic models: GraphNode, GraphEdge, enums
├── dictionary.py      # Data dictionary loader
├── parser/
│   └── sql_parser.py  # SQL -> ParsedSQL (CTEs, table/column refs)
└── graph/
    ├── builder.py     # Build graph from parsed SQL + dictionary
    └── traversal.py   # Traverse graph to answer metric questions
```

## Data Flow

```
SQL Sources ──► sql_parser ──► ParsedSQL
                                  │
Data Dictionary ──────────────────┤
                                  ▼
                           GraphBuilder
                                  │
                                  ▼
                        Delta Tables (nodes + edges)
                                  │
                                  ▼
                        GraphTraverser ──► Fabric Data Agent
```
