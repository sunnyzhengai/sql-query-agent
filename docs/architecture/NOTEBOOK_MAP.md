# Notebook Map

**GENERATED from `src/notebook_registry.py` — do not edit.**
Regenerate: `python scripts/generate_docs.py`. The contract is
enforced by tests/test_notebook_contract.py (ADR 0042); the
family records by tests/test_question_families.py (ADR 0070).

## The question families (layer 0 — approved 2026-08-18)

A STORAGE-COVERAGE audit, never a runtime routing table:
ADR 0062 abolished question types (`spec:R2`) — the answer's
shape EMERGES from the matched subgraph. What stands from the
July doctrine: shape classes shape the STORAGE, and
precomputation is only verifiable cache (`spec:D1`).

| Family | Archetype question | Asked by | Answer shape | Storage | Grounds | Status |
|---|---|---|---|---|---|---|
| **A. Meaning** | What does this report/metric measure, exactly? | analyst, clinician | card (prose + quoted criteria) | `output_metric_logic` | ADR 0014/0019 | shipped |
| **B. Provenance** | Where does this number come from? | analyst, auditor | path (report -> proc -> steps -> tables) | `graph_nodes`, `graph_edges` | ADR 0040/0053 | shipped |
| **C. Impact** | If I change this table/column/proc, what breaks? | developer, admin | closure (reachable set) | `graph_edges` | ADR 0018/0037 (materialized closures as cache) | shipped |
| **D. Discovery** | Does a report for X already exist? What exists about Y? | everyone | ranked list (semantic) | — | ADR 0030 — Eventhouse semantic catalog (a projection, not a Delta table) | shipped |
| **E. Trust** | Who owns this? Certified? When did it last change? Stale? | steward, leadership | card + timeline | `gov_publish_log` | ADR 0021/0022 — freshness via the content-hash lifecycle (the 2026-08-18 gap, closed) | shipped |
| **F. Consistency** | Are these definitions the same? Why do A and B disagree? (the founding demo question) | the founding demo question | aligned diff of decompositions | `graph_nodes` | ADR 0043 (the diff kernel) + 0054 (the sweep) — the 2026-08-18 gap, closed; now the product's wedge | shipped |
| **G. Health** | What failed, what fell off, what's the coverage? | admin | funnel (counts -> reasons) | `ops_fallout`, `ops_funnel` | ADR 0039 (error-to-contract lineage) | shipped |

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
| 300_build_graph | derivation | A, B, C, F | >=1.58.4 | Build the knowledge graph (nodes/edges, all layers, decision trees) |
| 400_build_metric_logic | derivation | A, E | >=1.24 | Flatten the graph into the metric card table |
| 500_validate | verification | G | >=1.29 | Pipeline validation + deployment readiness gate + leaf grounding (spec:C4) |
| 600_generate_descriptions | derivation | A | >=1.24 | Bottom-up LLM descriptions over the calculation DAG |
| 610_generate_agent_descriptions | derivation | A | >=1.24 | Data-Agent metric descriptions (owns ops_agent_descriptions) |
| 700_refresh_search_index | derivation | D | >=1.24 | Rebuild the semantic catalog + Eventhouse re-embed |
| 800_export_graph_tables | derivation | B, C | >=1.24 | Export typed tables for the Fabric Graph model |
| 900_publish_collibra | publisher | A, E | >=1.24 | Publish descriptions onto Collibra report assets |
| 910_publish_purview | publisher | A, E | >=1.24 | Publish metric cards to the Purview Data Map |
| 920_publish_pbi | publisher | A, E | >=1.24 | Publish certified descriptions onto PBI reports |
| 950_ingest_agent_events | acquisition | G | >=1.24 | Fold agent conversation events into gov_* telemetry |

## Question-family coverage (generated)

| Family | Served by |
|---|---|
| A. Meaning | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 040_dict_clarity, 050_dict_caboodle, 060_ingest_semantic_models, 200_parse, 300_build_graph, 400_build_metric_logic, 600_generate_descriptions, 610_generate_agent_descriptions, 900_publish_collibra, 910_publish_purview, 920_publish_pbi |
| B. Provenance | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 040_dict_clarity, 050_dict_caboodle, 060_ingest_semantic_models, 200_parse, 300_build_graph, 800_export_graph_tables |
| C. Impact | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 200_parse, 300_build_graph, 800_export_graph_tables |
| D. Discovery | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 700_refresh_search_index |
| E. Trust | 060_ingest_semantic_models, 400_build_metric_logic, 900_publish_collibra, 910_publish_purview, 920_publish_pbi |
| F. Consistency | 010_ingest_sql_filedrop, 020_ingest_sql_folders, 030_ingest_sql_live, 200_parse, 300_build_graph |
| G. Health | 060_ingest_semantic_models, 100_install, 200_parse, 500_validate, 950_ingest_agent_events |

Every notebook must serve >=1 family, and every family must be
served — a notebook serving none is a ghost (the traceability
rule, mechanized by ADRs 0042 + 0070).
