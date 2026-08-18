# Notebook Map

**GENERATED from `src/notebook_registry.py` — do not edit.**
Regenerate: `python scripts/generate_docs.py`. The contract is
enforced by tests/test_notebook_contract.py (ADR 0042).

## The notebook contract

| Notebook | Family | Serves | Engine | Purpose |
|---|---|---|---|---|
| 00a_ingest_sql_filedrop | acquisition | A, B, C, D, F | >=1.18 | Load dropped .sql files into input_sql_sources |
| 00b_ingest_sql_folders | acquisition | A, B, C, D, F | >=1.18 | Load configured ABFS folders of .sql into input_sql_sources |
| 00c_ingest_sql_live | acquisition | A, B, C, D, F | >=1.18 | Live extraction from the customer SQL source (merge) |
| 00d_dict_clarity | acquisition | A, B | >=1.18 | Primary dictionary load (formatted CSVs or raw export) |
| 00e_dict_caboodle | acquisition | A, B | >=1.18 | Merge a second dictionary source (primary wins) |
| 01_install | verification | G | >=1.18 | Environment verification + ingestion-state report |
| 02_parse | derivation | A, B, C, F, G | >=1.18 | Parse the SQL corpus with ScriptDom into parse tables |
| 03_build_graph | derivation | A, B, C, F | >=1.18 | Build the knowledge graph (nodes/edges, all layers) |
| 04_build_metric_logic | derivation | A, E | >=1.18 | Flatten the graph into the metric card table |
| 05_export_graph_tables | derivation | B, C | >=1.18 | Export typed tables for the Fabric Graph model |
| 06_validate | verification | G | >=1.18 | Pipeline validation + deployment readiness gate |
| 07_generate_descriptions | derivation | A | >=1.18 | Bottom-up LLM descriptions over the calculation DAG |
| 07b_generate_agent_descriptions | derivation | A | >=1.18 | Data-Agent metric descriptions (owns ops_agent_descriptions) |
| 08_publish_collibra | publisher | A, E | >=1.18 | Publish descriptions onto Collibra report assets |
| 09_publish_purview | publisher | A, E | >=1.18 | Publish metric cards to the Purview Data Map |
| 10_ingest_agent_events | acquisition | G | >=1.18 | Fold agent conversation events into gov_* telemetry |
| 11_refresh_search_index | derivation | D | >=1.18 | Rebuild the semantic catalog + Eventhouse re-embed |
| 12_ingest_semantic_models | acquisition | A, B, E, G | >=1.18 | Ingest PBI semantic models (lineage, DAX, names, fallout) |
| 13_publish_pbi | publisher | A, E | >=1.18 | Publish certified descriptions onto PBI reports |

## Question-family coverage (QUESTION_MAP layer 4, generated)

| Family | Served by |
|---|---|
| A. Meaning | 00a_ingest_sql_filedrop, 00b_ingest_sql_folders, 00c_ingest_sql_live, 00d_dict_clarity, 00e_dict_caboodle, 02_parse, 03_build_graph, 04_build_metric_logic, 07_generate_descriptions, 07b_generate_agent_descriptions, 08_publish_collibra, 09_publish_purview, 12_ingest_semantic_models, 13_publish_pbi |
| B. Provenance | 00a_ingest_sql_filedrop, 00b_ingest_sql_folders, 00c_ingest_sql_live, 00d_dict_clarity, 00e_dict_caboodle, 02_parse, 03_build_graph, 05_export_graph_tables, 12_ingest_semantic_models |
| C. Impact | 00a_ingest_sql_filedrop, 00b_ingest_sql_folders, 00c_ingest_sql_live, 02_parse, 03_build_graph, 05_export_graph_tables |
| D. Discovery | 00a_ingest_sql_filedrop, 00b_ingest_sql_folders, 00c_ingest_sql_live, 11_refresh_search_index |
| E. Trust | 04_build_metric_logic, 08_publish_collibra, 09_publish_purview, 12_ingest_semantic_models, 13_publish_pbi |
| F. Consistency | 00a_ingest_sql_filedrop, 00b_ingest_sql_folders, 00c_ingest_sql_live, 02_parse, 03_build_graph |
| G. Health | 01_install, 02_parse, 06_validate, 10_ingest_agent_events, 12_ingest_semantic_models |

Every notebook must serve >=1 family — a notebook serving none
is by definition a ghost (traceability rule, QUESTION_MAP.md).
