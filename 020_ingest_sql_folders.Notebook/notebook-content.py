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
route table. Identity: schema-qualified metric_id derived from each
file's own CREATE header (folder schema label as fallback), deduped —
filename-keyed identity produced 25 real cookrpt/reporting collisions at
a live deployment (2026-08-17). Parse-based identity (ScriptDom) remains
the wanted upgrade per HANDOFF_INGESTION_ROUTES.

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

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.22"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "020_ingest_sql_folders")


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
from pyspark.sql.functions import (
    coalesce,
    col,
    concat_ws,
    input_file_name,
    lit,
    nullif,
    regexp_extract,
)

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
                # cast REQUIRED: bare "null as x" writes a VOID-typed column that Delta
                # persists and full-table reads then crash on (live find 2026-08-18)
                "cast(null as string) as steward", "cast(null as string) as developer",
                "source_type", "source_schema",
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

    # Identity (2026-08-17): schema-qualify metric_id from each file's own
    # CREATE header — the content is the authority on which schema an
    # object belongs to; the folder label is only a fallback. Then dedupe:
    # the same object exported into two folders collapses to one row,
    # while genuine same-name twins across schemas stay distinct.
    # (Header pattern ONLY — parse-based identity is the wanted upgrade;
    # see HANDOFF_INGESTION_ROUTES. The pattern has ONE spelling, in
    # src.parser.identity, per the notebook contract.)
    from src.parser.identity import CREATE_HEADER_SPARK_PATTERN

    header_schema = regexp_extract("sql", CREATE_HEADER_SPARK_PATTERN, 1)
    header_object = regexp_extract("sql", CREATE_HEADER_SPARK_PATTERN, 2)
    combined_df = (combined_df
        .withColumn("_schema", coalesce(nullif(header_schema, lit("")), col("source_schema")))
        .withColumn("_object", coalesce(nullif(header_object, lit("")), col("metric_id")))
        .withColumn("metric_id", concat_ws(".", "_schema", "_object"))
        .withColumn("name", col("metric_id"))
        .withColumn("source_schema", col("_schema"))
        .drop("_schema", "_object")
        .dropDuplicates(["metric_id"]))

    total = combined_df.count()
    distinct_ids = combined_df.select("metric_id").distinct().count()
    assert total == distinct_ids, f"identity fix left {total - distinct_ids} collisions"
    combined_df.write.format("delta").mode("overwrite") \
        .option("overwriteSchema", "true").saveAsTable(SQL_SOURCES_OUTPUT)
    print(f"\nSaved {total} records ({distinct_ids} distinct ids) to {SQL_SOURCES_OUTPUT}")
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
print("\nNext: run 100_install to verify state, then 200_parse onward.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
