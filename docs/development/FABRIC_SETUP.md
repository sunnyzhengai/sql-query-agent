# Fabric Setup

## Prerequisites

- Microsoft Fabric workspace with a Lakehouse
- Fabric Notebook access
- Data dictionary tables (dict_tables, dict_columns) loaded into the Lakehouse

## Architecture: Library + Notebook

This project follows the **orchestration-by-notebook** pattern:

- **Library (`src/`)** — all business logic. Testable, versionable, reusable.
- **Notebook (`notebooks/`)** — thin orchestrator. Imports the library, loads config, calls functions.

```
Your Fabric Workspace
├── Lakehouse
│   ├── Tables/dict_tables          (input)
│   ├── Tables/dict_columns         (input)
│   ├── Tables/sql_sources          (input)
│   ├── Tables/graph_nodes          (output)
│   └── Tables/graph_edges          (output)
├── Environment
│   └── sql_query_agent-0.1.0.whl   (your library)
└── Notebooks
    ├── orchestrator.ipynb           (calls the library)
    ├── extract_views.ipynb          (optional: SQL Server extraction)
    └── (future notebooks reuse the same library)
```

**Why this split:**
- Notebooks are hard to version control, unit test, and refactor
- Libraries are easy to test with pytest, manage with git, and distribute
- The same .whl can be imported across multiple notebooks, pipelines, and Spark jobs
- Customers can extend with their own notebooks without touching your code

## Deployment Steps

### 1. Build the library

On your development machine:
```bash
pip install build
python -m build --wheel
# Output: dist/sql_query_agent-0.1.0-py3-none-any.whl
```

### 2. Create a Fabric Environment

In your Fabric workspace:
1. Go to **Workspace Settings** → **Environments**
2. Create a new Environment (e.g., "sql-query-agent-env")
3. Upload `sql_query_agent-0.1.0.whl` to the custom libraries section
4. Publish the Environment

> **Important:** Use Fabric Environments for production — not `%pip install` in notebook cells.
> Inline pip installs are fine for quick testing but unreliable for production.
> Environments ensure all notebooks use the same library version.

### 3. Attach Environment to Notebooks

1. Open each notebook (orchestrator, extract_views, etc.)
2. In the notebook toolbar, select your Environment
3. The library is now importable: `from src.pipeline import build_graph`

### 4. Upload org_config.yaml

Place `org_config.yaml` in the Lakehouse Files section (not Tables):
- Lakehouse → Files → upload `org_config.yaml`
- The notebook reads it from: `/lakehouse/default/Files/org_config.yaml`
- This file is never committed to git — each customer creates their own

### 5. Create Lakehouse tables

Ensure these Delta tables exist in the Lakehouse:

**Input tables** (customer provides):
- `dict_tables` — table-level data dictionary
- `dict_columns` — column-level data dictionary
- `sql_sources` — SQL queries to parse

**Output tables** (created by the pipeline):
- `graph_nodes` — the knowledge graph nodes
- `graph_edges` — the knowledge graph edges

### 6. Run the orchestrator notebook

Open `orchestrator.ipynb` and run all cells. It will:
1. Load org_config.yaml
2. Read dictionary and SQL source tables
3. Build the three-layer graph
4. Write nodes and edges to Delta tables
5. Print a summary

### 7. Connect Data Agent

Point the Fabric Data Agent at `graph_nodes` and `graph_edges`:
1. Create a new Data Agent in your workspace
2. Add the two Delta tables as data sources
3. Paste the grounding instructions from `notebooks/data_agent_instructions.md`
4. Test with: "What is ER Length of Stay?"

## Delta Table Schemas

### graph_nodes
| Column | Type | Description |
|--------|------|-------------|
| node_id | string | Unique node identifier |
| layer | string | canonical / transformation / technical / dimension |
| name | string | Display name |
| description | string | Human-readable description |
| properties | string | JSON blob of layer-specific properties |

### graph_edges
| Column | Type | Description |
|--------|------|-------------|
| source_id | string | Source node ID |
| target_id | string | Target node ID |
| edge_type | string | Edge type enum value |
| properties | string | JSON blob of edge properties |

## Environment Promotion (Dev → Test → Prod)

When ready for multiple environments:

1. **Dev workspace** — your working environment, latest code
2. **Test workspace** — stable version for validation
3. **Prod workspace** — customer-facing, locked down

Use Fabric Deployment Pipelines to promote:
- Environment (.whl version) + Notebooks + Lakehouse config
- Each workspace has its own `org_config.yaml` with environment-specific settings

This is not needed initially — start with a single workspace and add promotion when you have customers.
