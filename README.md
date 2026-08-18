# SQL Query Agent — Data Empowerment Suite

A Python library that extracts business logic from SQL stored procedures, builds a certified knowledge graph, and generates metadata for governance catalogs — all running natively in Microsoft Fabric.

## What It Does

1. **Parses SQL at scale** — handles real-world T-SQL stored procedures including multi-statement procs with temp tables, CTEs, and procedural scaffolding
2. **Builds a knowledge graph** — three-layer model (Business Metrics → Calculation Logic → Source Data) stored in Delta tables
3. **Generates business descriptions** — LLM-powered summaries of what each metric measures, in plain English
4. **Pushes metadata to catalogs** — Purview, Collibra, or Power BI report descriptions
5. **Grounds a Data Agent** — Fabric Data Agent answers questions by traversing the certified graph

## Components

| Component | Description | Tier |
|-----------|-------------|------|
| **Metadata Sync** | Generate and push metadata to Purview/Collibra | Basic |
| **GraphRAG Engine** | Knowledge graph + Data Agent grounding | Pro |

## Quick Start

### Local Development

```bash
git clone https://github.com/sunnyzhengai/sql-query-agent.git
cd sql-query-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp org_config.example.yaml org_config.yaml  # edit with your values
pytest  # run tests
python scripts/run_local.py  # test with sample data
```

### Microsoft Fabric

Follow the step-by-step [Installation Guide](docs/deployment/INSTALLATION_GUIDE.md). In short:

1. Create a Fabric Environment (`sql-logic-env`) with the pinned packages and the product wheel
2. Create a Lakehouse; upload the ScriptDom DLL, your `.sql` files, data dictionary CSVs, and `org_config.yaml`
3. Run the numbered pipeline notebooks in order:
   - `100_install` — create Delta tables, load SQL files and dictionary
   - `200_parse` — parse SQL with ScriptDom
   - `300_build_graph` — build the three-layer knowledge graph
   - `400_build_metric_logic` — flatten the graph for the Data Agent
   - `800_export_graph_tables` — export typed LPG tables (automatic)
   - `500_validate` — pipeline health gate (DEPLOYMENT READY / BLOCKED)
   - `600_generate_descriptions` — LLM business descriptions (optional)
   - `900_publish_collibra` / `910_publish_purview` — catalog sync (optional add-ons)
4. Create a Fabric Data Agent and add `output_metric_logic` plus the graph tables as data sources
5. Paste `notebooks/delta_agent_instructions.md` into the agent's instructions

## Configuration

All settings in `org_config.yaml` (gitignored — never commit credentials):

```yaml
org:
  name: "Your Organization"

lakehouse:
  dict_tables: "input_dict_tables"
  dict_columns: "input_dict_columns"
  sql_sources: "input_sql_sources"
  graph_nodes: "graph_nodes"
  graph_edges: "graph_edges"

dictionary:
  table_name_col: "TABLE_NAME"
  column_name_col: "COLUMN_NAME"
  description_col: "DESCRIPTION"
```

See `org_config.example.yaml` for all options including catalog adapters.

## Architecture

See [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for the full design.

```
SQL Sources → Parser → Graph Builder → Delta Tables → Data Agent
                                          ↓
                                    Metadata Generator
                                          ↓
                                    Purview / Collibra
```

## Documentation

- [Documentation Index](docs/README.md) — all documentation, organized by audience
- [Architecture](docs/architecture/ARCHITECTURE.md) — three-layer graph model, data flow
- [Decision Records](docs/decisions/README.md) — one ADR per architectural/product decision
- [User Flow](docs/architecture/USER_FLOW.md) — how questions move through the system
- [Installation Guide](docs/deployment/INSTALLATION_GUIDE.md) — deploying to Microsoft Fabric
- [Setup](docs/development/SETUP.md) — local development
- [Testing](docs/development/TESTING.md) — test strategy

## License

MIT License — see [LICENSE](LICENSE) for details.
