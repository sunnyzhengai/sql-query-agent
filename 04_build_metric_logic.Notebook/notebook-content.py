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

"""Fabric Notebook: Build Metric Logic Table

Reads from: graph_nodes, graph_edges (Delta)
Writes to:  output_metric_logic (Delta)

Run 03_build_graph.py at least once before this.
Flattens the graph into a single table the Data Agent can query.
"""

# %% Cell 0: Setup
# Prerequisites: Attach 'sql-logic-env' Fabric Environment. No %pip install.
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
from src.schemas import METRIC_LOGIC, to_spark_schema

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load graph and build metric_logic (all logic in src/)
from src.graph.serialization import rows_to_nodes, rows_to_edges
from src.graph.metric_logic import build_metric_logic_rows

nodes = rows_to_nodes([r.asDict() for r in spark.table(config.lakehouse.graph_nodes).collect()])
edges = rows_to_edges([r.asDict() for r in spark.table(config.lakehouse.graph_edges).collect()])
print(f"Loaded {len(nodes)} nodes, {len(edges)} edges")

metric_logic_rows = build_metric_logic_rows(nodes, edges)
print(f"Built {len(metric_logic_rows)} metric logic rows")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Save to Delta
ml_df = spark.createDataFrame(metric_logic_rows, schema=to_spark_schema(METRIC_LOGIC))
ml_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("output_metric_logic")

with_logic = sum(1 for r in metric_logic_rows if r[6] is not None)
with_tables = sum(1 for r in metric_logic_rows if r[7] is not None)
print(f"Saved {len(metric_logic_rows)} rows. Logic: {with_logic}, Tables: {with_tables}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
