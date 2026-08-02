# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "f7c297eb-4659-4600-ab89-0e860638fb6c",
# META       "default_lakehouse_name": "sql_query_lh",
# META       "default_lakehouse_workspace_id": "1f55e1c1-b660-4715-9b56-4140edce3940",
# META       "known_lakehouses": [
# META         {
# META           "id": "f7c297eb-4659-4600-ab89-0e860638fb6c"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "0776fc8d-1451-838d-47e6-f5c7a0bd174b",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# CELL ********************

"""Fabric Notebook: Export Typed Tables for Fabric Graph Model

Reads from: graph_nodes, graph_edges (Delta tables)
Writes to:  graph_canonical, graph_transformation, graph_technical, graph_dimension,
            graph_edge_c2t, graph_edge_t2t, graph_edge_t2tech, graph_edge_tech2dim (Delta tables)

Run 03_build_graph.py at least once before this.

After running, create a Graph Model in the Fabric UI:
1. Select + New item > Graph model in your workspace
2. Connect to the same lakehouse
3. Map each table to a node/edge type:
   - graph_canonical     -> Canonical (key: node_id)
   - graph_transformation -> Transformation (key: node_id)
   - graph_technical     -> Technical (key: node_id)
   - graph_dimension     -> Dimension (key: node_id)
   - graph_edge_c2t      -> CANONICAL_TO_TRANSFORM (source_id -> Canonical, target_id -> Transformation)
   - graph_edge_t2t      -> TRANSFORM_TO_TRANSFORM (source_id -> Transformation, target_id -> Transformation)
   - graph_edge_t2tech   -> TRANSFORM_TO_TECHNICAL (source_id -> Transformation, target_id -> Technical)
   - graph_edge_tab2col  -> TABLE_TO_COLUMN (source_id -> Technical table, target_id -> Technical column)
   - graph_edge_tech2dim -> TECHNICAL_TO_DIMENSION (source_id -> Technical, target_id -> Dimension)
4. Save the model to ingest data and build the queryable graph
"""

# %% Cell 0: Setup
import json
import sys
# If the wheel is installed via Fabric Environment, src is already importable.
# Fallback to sys.path for dev mode or non-wheel deployments.
try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from src.config import load_config
from src.schemas import (
    GRAPH_CANONICAL, GRAPH_DIMENSION, GRAPH_EDGE_C2T, GRAPH_EDGE_T2T,
    GRAPH_EDGE_T2TECH, GRAPH_EDGE_TECH2DIM, GRAPH_TECHNICAL, GRAPH_TRANSFORMATION,
    to_spark_schema,
)

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load graph nodes and edges from Delta
nodes_rows = [r.asDict() for r in spark.table(config.lakehouse.graph_nodes).collect()]
edges_rows = [r.asDict() for r in spark.table(config.lakehouse.graph_edges).collect()]
print(f"Loaded {len(nodes_rows)} nodes, {len(edges_rows)} edges from Delta")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Export typed tables (logic in src/steps/export.py)
from src.steps.export import export_step

export_tables = export_step(nodes_rows, edges_rows)

for name, rows in export_tables.items():
    print(f"  {name}: {len(rows)} rows")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 3: Write typed tables to Delta and run the postcondition gate
from src.schemas import TABLE_REGISTRY
from src.steps.gates import postcondition_gate

for table_name, rows in export_tables.items():
    if not rows:
        print(f"  {table_name}: 0 rows (skipped)")
        continue

    schema = to_spark_schema(TABLE_REGISTRY[table_name])
    df = spark.createDataFrame(rows, schema=schema)
    df.write.format("delta").mode("overwrite").saveAsTable(table_name)
    print(f"  {table_name}: {df.count()} rows written")

checked = postcondition_gate(
    "05_export_graph_tables",
    fetch=lambda t, cols: [r.asDict() for r in spark.table(t).select(*cols).collect()],
    table_exists=spark.catalog.tableExists,
)
print(f"[+] Postcondition gate passed for: {', '.join(checked)}")

print("\n=== Export complete ===")
print("Next: Create a Graph Model in the Fabric UI and map these tables.")
print("Then: run 06_validate.py")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
