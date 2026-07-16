# Fabric Setup

## Prerequisites

- Microsoft Fabric workspace with a Lakehouse
- Fabric Notebook access
- Data dictionary tables (dict_tables, dict_columns) loaded into the Lakehouse

## Steps

1. **Clone repo into Fabric** — pull from GitHub into your Fabric workspace
2. **Upload org_config.yaml** — place in the notebook's working directory (not committed to git)
3. **Create Lakehouse tables** — ensure `dict_tables`, `dict_columns`, and `sql_sources` Delta tables exist
4. **Run the orchestrator notebook** — `notebooks/orchestrator.ipynb` drives the pipeline
5. **Connect Data Agent** — point the Fabric Data Agent at the `graph_nodes` and `graph_edges` Delta tables

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
