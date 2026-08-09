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

"""Fabric Notebook (utility): Golden lakehouse snapshot.

Run AFTER a verified-good pipeline run (06_validate green, agent sanity
Q&A passed). The pipeline is deterministic — inputs + wheel version
rebuild everything — so the snapshot only clones what is expensive or
impossible to rebuild:

    input_sql_sources, input_dict_tables, input_dict_columns   (the inputs)
    ops_description_cache                                      (~460 LLM calls)
    ops_phi_findings                                           (steward dispositions)
    ops_error_log                                              (append-only history)

Each is copied via CTAS (Fabric Spark is OSS Delta — no DEEP
CLONE; that is Databricks-only) to golden_<table>; a manifest (row counts, wheel
version, timestamp) goes to Files/golden/manifest.json.

RESTORE: for each golden_<table>:
    CREATE OR REPLACE TABLE <table> AS SELECT * FROM golden_<table>
then rerun 02 -> 07 (05, 06) — with cache and findings restored, the
rebuild costs minutes and pennies, not a description regeneration.
"""

# %% Cell 0: Snapshot
import json
import os
from datetime import datetime, timezone

try:
    import src
except ImportError:
    import sys
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src

GOLDEN_TABLES = [
    "input_sql_sources",
    "input_dict_tables",
    "input_dict_columns",
    "ops_description_cache",
    "ops_phi_findings",
    "ops_error_log",
]

manifest = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "wheel_version": src.__version__,
    "tables": {},
}

for table in GOLDEN_TABLES:
    if not spark.catalog.tableExists(table):
        print(f"[!] {table} missing — skipped (run the pipeline first)")
        continue
    spark.sql(f"CREATE OR REPLACE TABLE golden_{table} AS SELECT * FROM {table}")
    count = spark.table(f"golden_{table}").count()
    manifest["tables"][table] = count
    print(f"[+] golden_{table}: {count} rows")

# Health numbers from the last validation run, if present
if spark.catalog.tableExists("ops_pipeline_validation"):
    latest = spark.table("ops_pipeline_validation").collect()
    manifest["validation_rows"] = len(latest)

manifest_path = "/lakehouse/default/Files/golden/manifest.json"
os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)
print("\nManifest -> Files/golden/manifest.json")
print(json.dumps(manifest, indent=2))
print("\nRestore: CREATE OR REPLACE TABLE <t> AS SELECT * FROM golden_<t> per table, "
      "then rerun 02->07.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
