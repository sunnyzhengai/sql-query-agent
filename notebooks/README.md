# notebooks/

Helper notebooks and agent assets. **The production pipeline does NOT live
here** — it is the numbered `*.Notebook` folders at the repo root
(`01_install` … `11_refresh_search_index`), which Fabric syncs as workspace
items. Everything in this directory is pasted into a Fabric notebook or run
ad hoc.

## Organization

```
notebooks/
├── data_loading/          ← "Step 00": load org inputs (run once per org, before 01–11)
│   ├── load_clarity_dictionary.py  — Clarity dictionary CSVs → input_dict_tables/_columns
│   ├── load_caboodle_dictionary.py — Caboodle variant of the same
│   ├── load_sql_files.py           — .sql files → input_sql_sources
│
├── utilities/             ← Operational tools (run as needed)
│   ├── ast_explorer_cell.py         — Explore a proc's ScriptDom AST (paste into 02_parse)
│   ├── check_stale_data.py          — Spot-check descriptions/logic freshness
│   ├── collibra_discovery.py        — Discover Collibra API data model
│   ├── collibra_lineage_match.py    — Match PBI reports to Collibra assets
│   ├── collibra_update_description.py — Push one description to a Collibra asset
│   ├── devops_lineage.py            — TMDL lineage from an Azure DevOps repo
│   ├── manage_stewards.py           — Assign stewards (writes gov_steward_assignments)
│   └── verify_graph.py              — Verify graph integrity
│
├── delta_agent_instructions.md   ← System prompt for the Delta Agent (production)
├── delta_agent_fewshots.json     ← Few-shot examples for the Delta Agent
└── graph_agent_instructions.md   ← System prompt for the Graph Agent (Fabric Graph)
```

## How to use

1. **First time per org:** run a `data_loading/` loader to populate
   `input_sql_sources`, `input_dict_tables`, `input_dict_columns`.
2. **Pipeline:** run the ROOT notebooks in order (02 → 03 → … → 11 as needed).
   Prerequisite for all of them: attach the `sql-logic-env` Fabric
   Environment — no `%pip install` anywhere.
3. **Iterate:** when code changes, rerun only the affected root notebook.

## Delta table flow (current names)

```
input_sql_sources ──→ 02_parse ──→ ops_parse_results ──→ 03_build_graph ──→ graph_nodes
input_dict_tables ─────────────────(+ errors/successes/────────┘             graph_edges
input_dict_columns ─────────────────phi_findings)──────────────┘                 │
                                                                                 ▼
                                                    04_build_metric_logic ──→ output_metric_logic
                                                                                 │
                                                                                 ▼
                                                              06_validate ──→ ops_pipeline_validation
                                                                              ops_build_summary
```

Table names and contracts: `src/schemas.py` is the single source of truth.
