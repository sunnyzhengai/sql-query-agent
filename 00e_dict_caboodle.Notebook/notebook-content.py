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

"""Fabric Notebook: Dictionary Route E — merge a second source

ROUTE: dictionary acquisition (00d primary | 00e merge). Run AFTER 00d;
merges by table/column name, primary rows win on duplicates.

Reads from: second-source dictionary export CSVs
Writes to:  input_dict_tables, input_dict_columns (merged overwrite)
"""

# %% Cell 0: Setup
import os  # noqa: F401
import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from src.config import load_config  # noqa: F401

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load second-source export and resolve TABLE_ID -> TABLE_NAME
# UPDATE the path for your environment.
SECOND_SOURCE_BASE = "abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/dictionaries"

cab_tbl = spark.read.option("header", "true").csv(f"{SECOND_SOURCE_BASE}/CABOODLE_TBL.csv")
cab_col = spark.read.option("header", "true").csv(f"{SECOND_SOURCE_BASE}/CABOODLE_COL.csv")
print(f"Second-source tables: {cab_tbl.count()}")
print(f"Second-source columns: {cab_col.count()}")

cab_col_resolved = (
    cab_col
    .join(cab_tbl.select("TABLE_ID", "TABLE_NAME"), on="TABLE_ID", how="left")
    .selectExpr("TABLE_NAME", "COLUMN_NAME", "cast(null as string) as DESCRIPTION")
)
cab_tbl_normalized = cab_tbl.selectExpr("TABLE_NAME", "INTRODUCTION as DESCRIPTION")
print(f"Resolved columns: {cab_col_resolved.count()}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Merge with the existing dictionary and save
# Existence checked explicitly: this cell OVERWRITES both tables, so a
# swallowed read error would wipe the primary dictionary and leave the
# second source only (audit 2026-08-15).
if spark.catalog.tableExists("input_dict_tables") and spark.catalog.tableExists("input_dict_columns"):
    existing_tbl = spark.table("input_dict_tables")
    existing_col = spark.table("input_dict_columns")
    print(f"Existing dict_tables: {existing_tbl.count()}")
    print(f"Existing dict_columns: {existing_col.count()}")
    merged_tbl = existing_tbl.unionByName(cab_tbl_normalized).dropDuplicates(["TABLE_NAME"])
    merged_col = existing_col.unionByName(cab_col_resolved).dropDuplicates(["TABLE_NAME", "COLUMN_NAME"])
else:
    print("No existing dictionary tables — using this source only")
    merged_tbl = cab_tbl_normalized
    merged_col = cab_col_resolved

merged_tbl.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("input_dict_tables")
merged_col.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("input_dict_columns")
print(f"\nSaved dict_tables: {merged_tbl.count()} tables")
print(f"Saved dict_columns: {merged_col.count()} columns")
print("Next: run 01_install to verify state, then 03_build_graph onward.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
