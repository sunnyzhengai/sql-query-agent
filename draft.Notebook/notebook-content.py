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

import importlib.metadata
print(importlib.metadata.version("sql-query-agent"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from src.steps.semantic_catalog import build_semantic_catalog

nodes_rows = [r.asDict() for r in spark.table("graph_nodes").collect()]
out = build_semantic_catalog(nodes_rows)
print(f"{out.metric_count} metrics, {out.step_count} steps, {out.term_count} terms")

df = spark.createDataFrame(out.rows)
df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("output_semantic_catalog")
print(f"wrote {df.count()} rows to output_semantic_catalog")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
