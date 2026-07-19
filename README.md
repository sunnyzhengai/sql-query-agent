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

1. Download this repo and upload to your Lakehouse `Files/sql-query-agent/`
2. Copy `org_config.example.yaml` to `org_config.yaml` and fill in your values
3. Run notebooks in order:
   - `load_clarity_dictionary.py` — load data dictionary (one-time)
   - `load_sql_files.py` — load SQL source files
   - `orchestrator.py` — parse SQL → build graph → write Delta tables
   - `generate_summaries.py` — LLM-generate business descriptions
4. Point a Fabric Data Agent at `graph_nodes` and `graph_edges` tables
5. Paste `notebooks/data_agent_instructions.md` into the agent's instructions

## Configuration

All settings in `org_config.yaml` (gitignored — never commit credentials):

```yaml
org:
  name: "Your Organization"

lakehouse:
  dict_tables: "dict_tables"
  dict_columns: "dict_columns"
  sql_sources: "sql_sources"
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

- [Architecture](docs/architecture/ARCHITECTURE.md) — three-layer graph model, design decisions
- [User Flow](docs/architecture/USER_FLOW.md) — how questions move through the system
- [Setup](docs/development/SETUP.md) — local development
- [Fabric Setup](docs/development/FABRIC_SETUP.md) — deploying to Microsoft Fabric
- [Testing](docs/development/TESTING.md) — test strategy
- [Roadmap](docs/product/ROADMAP.md) — product phases
- [Marketplace Checklist](docs/product/MARKETPLACE_CHECKLIST.md) — Microsoft Marketplace readiness

## License

MIT License — see [LICENSE](LICENSE) for details.
