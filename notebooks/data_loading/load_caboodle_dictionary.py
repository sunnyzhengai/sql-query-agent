"""Fabric Notebook: Load Caboodle Dictionary and Merge with Clarity

Reads Caboodle table and column CSVs, resolves TABLE_ID → TABLE_NAME,
merges with existing Clarity dictionary in dict_tables/dict_columns.

Run this after load_clarity_dictionary.py (or standalone if Clarity
dictionary isn't loaded yet).
"""

# %% Cell 0: Setup
# Prerequisites: Attach the 'sql-logic-env' Fabric Environment. No %pip install.

import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# %% Cell 1: Load Caboodle CSVs
# Update this path to match your Lakehouse Files location
CABOODLE_BASE = "abfss://BI-POC@onelake.dfs.fabric.microsoft.com/SZ_SQL_Logic.Lakehouse/Files/data/dictionaries"

cab_tbl = spark.read.option("header", "true").csv(f"{CABOODLE_BASE}/CABOODLE_TBL.csv")
cab_col = spark.read.option("header", "true").csv(f"{CABOODLE_BASE}/CABOODLE_COL.csv")

print(f"Caboodle tables: {cab_tbl.count()}")
print(f"Caboodle columns: {cab_col.count()}")

# %% Cell 2: Resolve TABLE_ID → TABLE_NAME and normalize schema
# Caboodle columns CSV has TABLE_ID, not TABLE_NAME — join to resolve
cab_col_resolved = (
    cab_col
    .join(cab_tbl.select("TABLE_ID", "TABLE_NAME"), on="TABLE_ID", how="left")
    .selectExpr(
        "TABLE_NAME",
        "COLUMN_NAME",
        "cast(null as string) as DESCRIPTION"
    )
)

# Normalize Caboodle tables to match dict_tables schema
cab_tbl_normalized = cab_tbl.selectExpr(
    "TABLE_NAME",
    "INTRODUCTION as DESCRIPTION"
)

print(f"Resolved columns: {cab_col_resolved.count()}")
print(f"Normalized tables: {cab_tbl_normalized.count()}")

# %% Cell 3: Merge with existing dictionary and save
# Load existing dictionary (Clarity or previous run). Existence checked
# explicitly: this cell OVERWRITES both tables, so a swallowed read error
# would wipe the Clarity dictionary and leave Caboodle-only (audit 2026-08-15).
if spark.catalog.tableExists("input_dict_tables") and spark.catalog.tableExists("input_dict_columns"):
    existing_tbl = spark.table("input_dict_tables")
    existing_col = spark.table("input_dict_columns")
    print(f"Existing dict_tables: {existing_tbl.count()}")
    print(f"Existing dict_columns: {existing_col.count()}")
    merged_tbl = existing_tbl.unionByName(cab_tbl_normalized).dropDuplicates(["TABLE_NAME"])
    merged_col = existing_col.unionByName(cab_col_resolved).dropDuplicates(["TABLE_NAME", "COLUMN_NAME"])
else:
    print("No existing dictionary tables — using Caboodle only")
    merged_tbl = cab_tbl_normalized
    merged_col = cab_col_resolved

# Write merged dictionary
merged_tbl.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("input_dict_tables")
merged_col.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("input_dict_columns")

print(f"\nSaved dict_tables: {merged_tbl.count()} tables")
print(f"Saved dict_columns: {merged_col.count()} columns")
print("→ Run 03_build_graph.py to rebuild graph with Caboodle tables included")
