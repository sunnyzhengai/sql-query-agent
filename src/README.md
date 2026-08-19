# src/ — Core Library

## Pipeline Flow

```
SQL files → parser/ → graph/ → adapters/
                                    ↓
                              External tools
                         (Collibra, Purview, PBI)
```

| Order | Module | What it does | Input | Output |
|---|---|---|---|---|
| 1 | `parser/` | Parse SQL files, extract CTEs, tables, dependencies | Raw SQL text | `ParsedSQL` objects |
| 2 | `graph/` | Build three-layer knowledge graph from parsed results | `ParsedSQL` + data dictionary | Nodes + edges |
| 3 | `adapters/` | Push metadata to external tools | Graph data | API calls to Collibra, Purview, PBI |

## Supporting Modules (not pipeline steps — used by all)

| Module | What it does | Used by |
|---|---|---|
| `config.py` | Load org_config.yaml | All notebooks |
| `models.py` | Data classes: GraphNode, GraphEdge, NodeLayer, EdgeType | graph/, adapters/ |
| `schemas.py` | Delta table schema definitions | All notebooks that write to Delta |
| `dictionary.py` | In-memory data dictionary (table/column descriptions) | graph/ |
| `pipeline.py` | End-to-end pipeline runner (local dev) | scripts/run_local.py |
| `extractor/` | Discover SQL objects from SQL Server via JDBC/pyodbc | notebooks/data_loading/extract_views.py |
| `governance/` | Steward assignment + error tracking across runs | Future: admin workflows |

## Module Details

### parser/ — SQL Parsing (Step 1)

| File | Purpose | Tested by |
|---|---|---|
| `sql_parser.py` | Parse single/multi-statement SQL, extract CTEs + table refs | tests/parser/test_sql_parser.py |
| `scriptdom_fabric.py` | ScriptDom AST extraction via pythonnet (primary, Fabric only) | Tested in Fabric notebooks |
| `error_classifier.py` | Classify parse errors into user-facing categories | tests/parser/test_error_classifier.py |

### graph/ — Knowledge Graph (Step 2)

| File | Purpose | Tested by |
|---|---|---|
| `builder.py` | Build three-layer graph: canonical → transformation → technical | tests/graph/test_builder.py |
| `traversal.py` | BFS/DFS traversal from canonical node to technical tables | tests/graph/test_traversal.py |

### adapters/ — External Integrations (Step 3)

| File | Purpose | Tested by |
|---|---|---|
| `base.py` | CatalogAdapter protocol + MetadataRecord data class | tests/adapters/test_adapters.py |
| `publisher.py` | Multi-adapter dispatcher | tests/adapters/test_adapters.py |
| `metadata_generator.py` | Convert graph nodes → MetadataRecords | tests/adapters/test_adapters.py |
| `collibra.py` | Collibra REST API adapter | tests/adapters/test_adapters.py |
| `collibra_lineage.py` | Collibra lineage discovery client | — (new, manual testing) |
| `purview.py` | Microsoft Purview adapter | tests/adapters/test_adapters.py |
| `fabric_agent.py` | Fabric Data Agent MCP/JSON-RPC client | — (Fabric only) |
| `fabric_pbi.py` | Power BI report description updater | — (Fabric only) |

### extractor/ — SQL Server Discovery

| File | Purpose | Tested by |
|---|---|---|
| `extractor.py` | Orchestrate: discover → compute delta → produce sql_sources | tests/extractor/test_extractor.py |
| `discovery.py` | Query sys.catalog for views/procs | tests/extractor/test_extractor.py |
| `connection.py` | JDBC (Fabric) and pyodbc (local) connection abstraction | tests/extractor/test_extractor.py |
| `tracker.py` | SHA-256 change detection across runs | tests/extractor/test_extractor.py |

### governance/ — Data Governance

| File | Purpose | Tested by |
|---|---|---|
| `steward.py` | Steward assignment: individual, bulk, by pattern | tests/test_pipeline.py |
| `error_log.py` | Error tracking with regression detection across runs | tests/test_pipeline.py |
