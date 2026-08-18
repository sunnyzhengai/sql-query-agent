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

"""Fabric Notebook: Dictionary Route D — primary dictionary load

ROUTE: dictionary acquisition (00d primary | 00e merge a second
source). A source system enters as a PAIR — its SQL and its dictionary
together — or 06's dictionary_coverage gate blocks (by design).

Reads from: Files/dictionary CSVs (Cell 1) OR raw export (Cell 2)
Writes to:  input_dict_tables, input_dict_columns (overwrite)
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

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.18"
from src.engine_floor import require_engine
require_engine(src.__version__, REQUIRES_ENGINE, "00d_dict_clarity")


from src.config import load_config  # noqa: F401

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: ROUTE D-1 — formatted CSVs from Files/dictionary/ (the standard path)
# Run THIS cell if you have dict_tables.csv + dict_columns.csv in the
# documented format (DATA_DICTIONARY_REQUIREMENTS.md). Skip to Cell 2
# for raw Clarity exports instead. Run ONE of the two.
from src.parser.identity import find_duplicate_identities

DICT_DIR = "/lakehouse/default/Files/sql-query-agent/dictionary/"

tables_path = os.path.join(DICT_DIR, "dict_tables.csv")
columns_path = os.path.join(DICT_DIR, "dict_columns.csv")
if not (os.path.exists(tables_path) and os.path.exists(columns_path)):
    raise SystemExit(
        "dictionary/dict_tables.csv + dict_columns.csv not found — this "
        "cell loads formatted CSVs. Use Cell 2 for raw Clarity exports, "
        "or upload the CSVs (see DATA_DICTIONARY_REQUIREMENTS.md)."
    )

from pyspark.sql.functions import lit

dict_tables_df = spark.read.option("header", "true").csv("file://" + tables_path)
cols = [c.upper() for c in dict_tables_df.columns]
if "TABLE_NAME" not in cols:
    raise SystemExit(f"dict_tables.csv missing TABLE_NAME column (found: {dict_tables_df.columns})")
if "DESCRIPTION" not in cols:
    print("[!] WARNING: dict_tables.csv missing DESCRIPTION column — adding empty descriptions")
    dict_tables_df = dict_tables_df.withColumn("DESCRIPTION", lit(""))
dict_tables_df = dict_tables_df.select("TABLE_NAME", "DESCRIPTION")

# Contract gate: unique(TABLE_NAME), case-insensitive (ADR 0016)
_names = [r["TABLE_NAME"] for r in dict_tables_df.collect()]
_dupes = find_duplicate_identities([(n, n) for n in _names])
if _dupes:
    print("[X] FATAL: dict_tables.csv has duplicate table names (matching is case-insensitive):")
    for folded, originals in sorted(_dupes.items()):
        print(f"    {folded}: {originals}")
    raise SystemExit("Fix dict_tables.csv (one row per table) and re-run.")

dict_tables_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("input_dict_tables")
print(f"[+] Loaded {dict_tables_df.count()} table descriptions into input_dict_tables")

dict_columns_df = spark.read.option("header", "true").csv("file://" + columns_path)
cols = [c.upper() for c in dict_columns_df.columns]
if "TABLE_NAME" not in cols or "COLUMN_NAME" not in cols:
    raise SystemExit(f"dict_columns.csv missing TABLE_NAME or COLUMN_NAME (found: {dict_columns_df.columns})")
if "DESCRIPTION" not in cols:
    print("[!] WARNING: dict_columns.csv missing DESCRIPTION column — adding empty descriptions")
    dict_columns_df = dict_columns_df.withColumn("DESCRIPTION", lit(""))
dict_columns_df = dict_columns_df.select("TABLE_NAME", "COLUMN_NAME", "DESCRIPTION")

# Contract gate: unique(TABLE_NAME, COLUMN_NAME), case-insensitive (ADR 0016)
_pairs = [f'{r["TABLE_NAME"]}.{r["COLUMN_NAME"]}' for r in dict_columns_df.collect()]
_dupes = find_duplicate_identities([(p, p) for p in _pairs])
if _dupes:
    print("[X] FATAL: dict_columns.csv has duplicate columns (matching is case-insensitive):")
    for folded, originals in sorted(_dupes.items()):
        print(f"    {folded}: {originals}")
    raise SystemExit("Fix dict_columns.csv (one row per table+column) and re-run.")

dict_columns_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("input_dict_columns")
print(f"[+] Loaded {dict_columns_df.count()} column descriptions into input_dict_columns")
print("\nNext: run 01_install to verify state.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: ROUTE D-2 — raw Clarity export (TABLE_ID-keyed CSVs)
# Run this INSTEAD of Cell 1 when you have the raw two-file export.
# UPDATE the paths for your environment.
CLARITY_TBL_PATH = "abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/dictionaries/CLARITY_TBL.csv"
CLARITY_COL_PATH = "abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/dictionaries/CLARITY_COL.csv"

raw_tbl = spark.read.option("header", "true").csv(CLARITY_TBL_PATH)
dict_tables_df = raw_tbl.selectExpr("TABLE_NAME", "TABLE_ID", "TABLE_INTRODUCTION as DESCRIPTION")
print(f"Tables export: {dict_tables_df.count()} rows")

raw_col = spark.read.option("header", "true").csv(CLARITY_COL_PATH)
dict_columns_df = (
    raw_col
    .join(dict_tables_df.select("TABLE_ID", "TABLE_NAME"), on="TABLE_ID", how="left")
    .select("TABLE_NAME", "COLUMN_NAME", "DESCRIPTION")
)
print(f"Columns export: {dict_columns_df.count()} rows")

dict_tables_df.select("TABLE_NAME", "DESCRIPTION").write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable("input_dict_tables")
dict_columns_df.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable("input_dict_columns")
print(f"Saved {spark.table('input_dict_tables').count()} tables, "
      f"{spark.table('input_dict_columns').count()} columns")
print("\nNext: 00e (merge a second source) or 01_install to verify state.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
