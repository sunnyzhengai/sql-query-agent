"""Fabric Notebook: Load Clarity Dictionary CSVs into Delta Tables

Reads CLARITY_TBL.csv and CLARITY_COL.csv with headers, resolves
TABLE_ID → TABLE_NAME, and saves as dict_tables and dict_columns.

Run this before load_caboodle_dictionary.py (which merges on top).
"""

# %% Cell 0: Setup
# Prerequisites: Attach the 'sql-logic-env' Fabric Environment. No %pip install.

import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# %% Cell 1: Configuration
# UPDATE THESE PATHS to match your CSV locations
CLARITY_TBL_PATH = "abfss://BI-POC@onelake.dfs.fabric.microsoft.com/SZ_SQL_Logic.Lakehouse/Files/data/dictionaries/CLARITY_TBL.csv"
CLARITY_COL_PATH = "abfss://BI-POC@onelake.dfs.fabric.microsoft.com/SZ_SQL_Logic.Lakehouse/Files/data/dictionaries/CLARITY_COL.csv"

DICT_TABLES_OUTPUT = "input_dict_tables"
DICT_COLUMNS_OUTPUT = "input_dict_columns"

# %% Cell 2: Load CLARITY_TBL
# CSV format: TABLE_NAME, TABLE_ID, TABLE_INTRODUCTION
raw_tbl = spark.read.option("header", "true").csv(CLARITY_TBL_PATH)

dict_tables_df = raw_tbl.selectExpr(
    "TABLE_NAME",
    "TABLE_ID",
    "TABLE_INTRODUCTION as DESCRIPTION"
)

print(f"CLARITY_TBL: {dict_tables_df.count()} rows")
dict_tables_df.show(5, truncate=80)

# %% Cell 3: Load CLARITY_COL
# CSV format: TABLE_ID, COLUMN_ID, COLUMN_NAME, DESCRIPTION
raw_col = spark.read.option("header", "true").csv(CLARITY_COL_PATH)

# Join to resolve TABLE_ID → TABLE_NAME
dict_columns_df = (
    raw_col
    .join(
        dict_tables_df.select("TABLE_ID", "TABLE_NAME"),
        on="TABLE_ID",
        how="left",
    )
    .select("TABLE_NAME", "COLUMN_NAME", "DESCRIPTION")
)

print(f"CLARITY_COL: {dict_columns_df.count()} rows")
dict_columns_df.show(5, truncate=80)

# %% Cell 4: Save as Delta tables
dict_tables_out = dict_tables_df.select("TABLE_NAME", "DESCRIPTION")
dict_tables_out.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(DICT_TABLES_OUTPUT)
print(f"Saved {dict_tables_out.count()} rows to {DICT_TABLES_OUTPUT}")

dict_columns_df.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(DICT_COLUMNS_OUTPUT)
print(f"Saved {dict_columns_df.count()} rows to {DICT_COLUMNS_OUTPUT}")

# %% Cell 5: Verify
print("=== dict_tables ===")
spark.table(DICT_TABLES_OUTPUT).show(5, truncate=80)

print("=== dict_columns ===")
spark.table(DICT_COLUMNS_OUTPUT).show(10, truncate=80)

print(f"\ndict_tables: {spark.table(DICT_TABLES_OUTPUT).count()} rows")
print(f"dict_columns: {spark.table(DICT_COLUMNS_OUTPUT).count()} rows")
print("\n→ Next: run load_caboodle_dictionary.py to merge Caboodle tables")
