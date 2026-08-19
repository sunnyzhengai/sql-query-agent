# Notebook Map

**GENERATED from `src/notebook_registry.py` — do not edit.**
Regenerate: `python scripts/generate_docs.py`. The contract is
enforced by tests/test_notebook_contract.py (ADR 0042).

## The notebook contract

| Notebook | Family | Serves | Engine | Purpose |
|---|---|---|---|---|
| 010_ingest_sql_filedrop | acquisition | A, B, C, D, F | >=1.24 | Load dropped .sql files into input_sql_sources |
| 020_ingest_sql_folders | acquisition | A, B, C, D, F | >=1.24 | Load configured ABFS folders of .sql into input_sql_sources |
| 030_ingest_sql_live | acquisition | A, B, C, D, F | >=1.24 | Live extraction from the customer SQL source (merge) |
| 040_dict_clarity | acquisition | A, B | >=1.24 | Primary dictionary load (formatted CSVs or raw export) |
| 050_dict_caboodle | acquisition | A, B | >=1.24 | Merge a second dictionary source (primary wins) |
| 060_ingest_semantic_models | acquisition | A, B, E, G | >=1.24 | Ingest PBI semantic models (lineage, DAX, names, fallout) |
| 100_install | verification | G | >=1.24 | Environment verification + ingestion-state report |
| 200_parse | derivation | A, B, C, F, G | >=1.24 | Parse the SQL corpus with ScriptDom into parse tables |
| 300_build_graph | derivation | A, B, C, F | >=1.26 | Build the knowledge graph (nodes/edges, all layers, decision trees) |
| 400_build_metric_logic | derivation | A, E | >=1.24 | Flatten the graph into the metric card table |
| 500_validate | verification | G | >=1.24 | Pipeline validation + deployment readiness gate |
| 600_generate_descriptions | derivation | A | >=1.24 | Bottom-up LLM descriptions over the calculation DAG |
| 610_generate_agent_descriptions | derivation | A | >=1.24 | Data-Agent metric descriptions (owns ops_agent_descriptions) |
| 700_refresh_search_index | derivation | D | >=1.24 | Rebuild the semantic catalog + Eventhouse re-embed |
| 800_export_graph_tables | derivation | B, C | >=1.24 | Export typed tables for the Fabric Graph model |
| 900_publish_collibra | publisher | A, E | >=1.24 | Publish descriptions onto Collibra report assets |
| 910_publish_purview | publisher | A, E | >=1.24 | Publish metric cards to the Purview Data Map |
| 920_publish_pbi | publisher | A, E | >=1.24 | Publish certified descriptions onto PBI reports |
| 950_ingest_agent_events | acquisition | G | >=1.24 | Fold agent conversation events into gov_* telemetry |

## Question-family coverage (QUESTION_MAP layer 4, generated)

| Family | Served by |
|---|---|
| A. Meaning | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 040_dict_clarity, 050_dict_caboodle, 060_ingest_semantic_models, 200_parse, 300_build_graph, 400_build_metric_logic, 600_generate_descriptions, 610_generate_agent_descriptions, 900_publish_collibra, 910_publish_purview, 920_publish_pbi |
| B. Provenance | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 040_dict_clarity, 050_dict_caboodle, 060_ingest_semantic_models, 200_parse, 300_build_graph, 800_export_graph_tables |
| C. Impact | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 200_parse, 300_build_graph, 800_export_graph_tables |
| D. Discovery | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 700_refresh_search_index |
| E. Trust | 060_ingest_semantic_models, 400_build_metric_logic, 900_publish_collibra, 910_publish_purview, 920_publish_pbi |
| F. Consistency | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 200_parse, 300_build_graph |
| G. Health | 060_ingest_semantic_models, 100_install, 200_parse, 500_validate, 950_ingest_agent_events |

Every notebook must serve >=1 family — a notebook serving none
is by definition a ghost (traceability rule, QUESTION_MAP.md).
