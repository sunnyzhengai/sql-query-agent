"""Fabric Notebook: Load Clarity Dictionary CSVs into Delta Tables

One-time loader that reads headerless CLARITY_TBL.csv and CLARITY_COL.csv,
extracts only the columns we need, and saves as managed Delta tables.

To use in Fabric:
1. Create a new Notebook in your workspace
2. Copy each cell below into the notebook (cells are delimited by # %%)
3. Attach to your Lakehouse (the one where you want dict_tables and dict_columns)
4. Update the ABFS paths in Cell 2 to match your CSV locations
5. Run all cells
"""

# %% Cell 1: Configuration
# UPDATE THESE PATHS to match your CSV locations
CLARITY_TBL_PATH = "abfss://BI-POC@onelake.dfs.fabric.microsoft.com/SZ_SQL_Logic.Lakehouse/Files/data/dictionaries/CLARITY_TBL.csv"
CLARITY_COL_PATH = "abfss://BI-POC@onelake.dfs.fabric.microsoft.com/SZ_SQL_Logic.Lakehouse/Files/data/dictionaries/CLARITY_COL.csv"

# Output table names (will be created in the attached Lakehouse)
DICT_TABLES_OUTPUT = "dict_tables"
DICT_COLUMNS_OUTPUT = "dict_columns"

# %% Cell 2: Load CLARITY_TBL (headerless CSV)
# Columns by position (1-based): 1=TABLE_ID, 2=TABLE_NAME, 25=TABLE_INTRODUCTION
raw_tbl = spark.read.option("header", "false").csv(CLARITY_TBL_PATH)

dict_tables_df = raw_tbl.select(
    raw_tbl["_c0"].alias("TABLE_ID"),
    raw_tbl["_c1"].alias("TABLE_NAME"),
    raw_tbl["_c24"].alias("DESCRIPTION"),    # TABLE_INTRODUCTION -> DESCRIPTION
)

print(f"CLARITY_TBL: {dict_tables_df.count()} rows")
dict_tables_df.show(5, truncate=80)

# %% Cell 3: Load CLARITY_COL (headerless CSV)
# Columns by position (1-based): 1=COLUMN_ID, 2=COLUMN_NAME, 3=TABLE_ID, 15=DESCRIPTION
raw_col = spark.read.option("header", "false").csv(CLARITY_COL_PATH)

dict_columns_raw = raw_col.select(
    raw_col["_c0"].alias("COLUMN_ID"),
    raw_col["_c1"].alias("COLUMN_NAME"),
    raw_col["_c2"].alias("TABLE_ID"),
    raw_col["_c14"].alias("DESCRIPTION"),
)

# Join to get TABLE_NAME from dict_tables (CLARITY_COL only has TABLE_ID)
dict_columns_df = (
    dict_columns_raw
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
# dict_tables: TABLE_NAME, DESCRIPTION
dict_tables_out = dict_tables_df.select("TABLE_NAME", "DESCRIPTION")
dict_tables_out.write.format("delta").mode("overwrite").saveAsTable(DICT_TABLES_OUTPUT)
print(f"Saved {dict_tables_out.count()} rows to {DICT_TABLES_OUTPUT}")

# dict_columns: TABLE_NAME, COLUMN_NAME, DESCRIPTION
dict_columns_df.write.format("delta").mode("overwrite").saveAsTable(DICT_COLUMNS_OUTPUT)
print(f"Saved {dict_columns_df.count()} rows to {DICT_COLUMNS_OUTPUT}")

# %% Cell 5: Verify
print("=== dict_tables ===")
spark.table(DICT_TABLES_OUTPUT).show(5, truncate=80)

print("=== dict_columns ===")
spark.table(DICT_COLUMNS_OUTPUT).show(10, truncate=80)

print(f"\ndict_tables: {spark.table(DICT_TABLES_OUTPUT).count()} rows")
print(f"dict_columns: {spark.table(DICT_COLUMNS_OUTPUT).count()} rows")
print("\nDone! These tables are now ready for the orchestrator.")
