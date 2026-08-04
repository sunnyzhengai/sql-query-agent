# Notebooks

## Organization

```
notebooks/
├── pipeline/              ← Core pipeline (run in order)
│   ├── 02_parse.py        — Parse SQL files → parse_results, parse_errors
│   ├── 03_build_graph.py  — Build knowledge graph → graph_nodes, graph_edges
│   ├── 04_build_metric_logic.py — Flatten graph → metric_logic
│   └── 05_validate.py     — Validate pipeline health → pipeline_validation
│
├── data_loading/          ← Data ingestion (run before pipeline)
│   ├── load_sql_files.py  — Load .sql files → sql_sources
│   ├── load_clarity_dictionary.py — Load data dictionary → dict_tables, dict_columns
│   └── extract_views.py   — Extract views from SQL Server via gateway
│
├── utilities/             ← Operational tools (run as needed)
│   ├── ast_explorer_cell.py    — Explore ScriptDom AST for debugging
│   ├── check_stale_data.py     — Verify data freshness across tables
│   ├── collibra_discovery.py   — Discover Collibra API data model
│   └── verify_graph.py         — Verify graph integrity
│
└── delta_agent_instructions.md  ← System prompt for the Delta Agent (production)
```

## How to Use

1. **First time:** Run a data_loading notebook to populate sql_sources and dictionary tables
2. **Build the graph:** Run pipeline notebooks 02 → 03 → 04 → 05 in order
3. **Iterate:** When code changes, rerun only the affected pipeline step
4. **Each notebook is self-contained** — has its own Cell 0 with setup (deps, config, ScriptDom)

## Delta Table Flow

```
sql_sources ──→ 02_parse ──→ parse_results ──→ 03_build_graph ──→ graph_nodes
dict_tables ─┘                                                     graph_edges
dict_columns ─────────────────────────────────┘                        │
                                                                       ▼
                                                    04_build_metric_logic ──→ metric_logic
                                                                       │
                                                                       ▼
                                                              05_validate ──→ pipeline_validation
                                                                               build_summary
```
