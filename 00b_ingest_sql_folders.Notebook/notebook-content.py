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

"""Fabric Notebook: Ingestion Route B — multi-folder load

ROUTE: one of the peer acquisition routes (00a filedrop | 00b folders |
00c live). All routes write input_sql_sources under the same contract;
run whichever matches where your SQL lives — see the INSTALLATION_GUIDE
route table. NOTE: this route keys identity on FILENAME; 02's identity
derivation still governs (content wins where present).

Reads from: configured ABFS folders of .sql files
Writes to:  input_sql_sources (overwrite; partial loads REFUSE)
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


# %% Cell 1: Configure source folders, load, and save
# UPDATE SQL_FOLDERS for your environment: each entry is a folder of
# .sql files with its source_type and schema label.
from functools import reduce

from pyspark.sql import DataFrame
from pyspark.sql.functions import input_file_name, lit, regexp_extract

ABFS_BASE = "abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/sql"
SQL_FOLDERS = [
    {"path": f"{ABFS_BASE}/procs_reporting", "source_type": "procedure", "schema": "reporting"},
    {"path": f"{ABFS_BASE}/views_reporting", "source_type": "view", "schema": "reporting"},
]

SQL_SOURCES_OUTPUT = "input_sql_sources"

all_dfs = []
failed_folders = []
for folder in SQL_FOLDERS:
    path, source_type, schema = folder["path"], folder["source_type"], folder["schema"]
    try:
        sql_files = spark.read.text(path + "/*.sql", wholetext=True)
        folder_df = (
            sql_files
            .withColumn("file_path", input_file_name())
            .withColumn("file_name", regexp_extract("file_path", r"([^/]+)\.sql$", 1))
            .withColumn("source_type", lit(source_type))
            .withColumn("source_schema", lit(schema))
            .selectExpr(
                "file_name as metric_id", "file_name as name", "value as sql",
                "null as steward", "null as developer", "source_type", "source_schema",
            )
        )
        count = folder_df.count()
        all_dfs.append(folder_df)
        print(f"  {path.split('/')[-1]}: {count} SQL files ({source_type}, {schema})")
    except Exception as e:  # noqa: BLE001 — collected below; partial loads must not overwrite
        failed_folders.append((path, str(e)))
        print(f"  {path.split('/')[-1]}: ERROR — {e}")

# A partial load must NOT overwrite input_sql_sources — losing folders
# silently shrinks the corpus and every downstream count still "passes"
# (audit 2026-08-15). Fix the failing folder or remove it from SQL_FOLDERS.
if failed_folders:
    raise RuntimeError(
        f"{len(failed_folders)} folder(s) failed to load: "
        + "; ".join(f"{p} ({e})" for p, e in failed_folders)
    )

if all_dfs:
    combined_df = reduce(DataFrame.unionAll, all_dfs)
    total = combined_df.count()
    combined_df.write.format("delta").mode("overwrite") \
        .option("overwriteSchema", "true").saveAsTable(SQL_SOURCES_OUTPUT)
    print(f"\nSaved {total} records to {SQL_SOURCES_OUTPUT}")
else:
    raise SystemExit("No SQL files found in any folder")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 2: Verify
verify_df = spark.table("input_sql_sources")
verify_df.groupBy("source_type", "source_schema").count().orderBy("source_type", "source_schema").show()
print(f"Total: {verify_df.count()} SQL sources")
print("\nNext: run 01_install to verify state, then 02_parse onward.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
