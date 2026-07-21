"""Fabric Notebook: Load SQL files from multiple folders into sql_sources Delta table.

Reads .sql files from multiple ABFS paths (procs and views from different schemas),
extracts file names as metric IDs, tags each with its source folder,
and saves the full SQL text as sql_sources for the orchestrator.

To use in Fabric:
1. Create a new Notebook or add as a cell in your orchestrator
2. Update the SQL_FOLDERS list with your ABFS paths
3. Attach to the Lakehouse where you want sql_sources
4. Run all cells
"""

# %% Cell 1: Configuration
# UPDATE THESE PATHS to point to your SQL file folders
ABFS_BASE = "abfss://BI-POC@onelake.dfs.fabric.microsoft.com/SZ_SQL_Logic.Lakehouse/Files/data"

SQL_FOLDERS = [
    {"path": f"{ABFS_BASE}/procs_cookrpt",    "source_type": "stored_procedure", "schema": "cookrpt"},
    {"path": f"{ABFS_BASE}/procs_reporting",   "source_type": "stored_procedure", "schema": "reporting"},
    {"path": f"{ABFS_BASE}/views_cookrpt",     "source_type": "view",             "schema": "cookrpt"},
    {"path": f"{ABFS_BASE}/views_reporting",   "source_type": "view",             "schema": "reporting"},
]

# Output table name
SQL_SOURCES_OUTPUT = "sql_sources"

# %% Cell 2: Read SQL files from all folders
from pyspark.sql.functions import input_file_name, regexp_extract, lit
from functools import reduce
from pyspark.sql import DataFrame

all_dfs = []

for folder in SQL_FOLDERS:
    path = folder["path"]
    source_type = folder["source_type"]
    schema = folder["schema"]

    try:
        sql_files = spark.read.text(path + "/*.sql", wholetext=True)

        folder_df = (
            sql_files
            .withColumn("file_path", input_file_name())
            .withColumn("file_name", regexp_extract("file_path", r"([^/]+)\.sql$", 1))
            .withColumn("source_type", lit(source_type))
            .withColumn("source_schema", lit(schema))
            .selectExpr(
                "file_name as metric_id",
                "file_name as name",
                "value as sql",
                "null as steward",
                "null as developer",
                "source_type",
                "source_schema",
            )
        )

        count = folder_df.count()
        all_dfs.append(folder_df)
        print(f"  {path.split('/')[-1]}: {count} SQL files ({source_type}, {schema})")

    except Exception as e:
        print(f"  {path.split('/')[-1]}: ERROR — {e}")

# Combine all folders
if all_dfs:
    sql_sources_df = reduce(DataFrame.unionAll, all_dfs)
    total = sql_sources_df.count()
    print(f"\nTotal: {total} SQL files from {len(all_dfs)} folders")
else:
    print("ERROR: No SQL files found in any folder")

# %% Cell 3: Summary by source type and schema
print("\n=== Summary ===")
sql_sources_df.groupBy("source_type", "source_schema").count().orderBy("source_type", "source_schema").show()

# %% Cell 4: Save as Delta table
sql_sources_df.write.format("delta").mode("overwrite").saveAsTable(SQL_SOURCES_OUTPUT)
print(f"Saved {sql_sources_df.count()} records to {SQL_SOURCES_OUTPUT}")

# %% Cell 5: Verify
print(f"=== {SQL_SOURCES_OUTPUT} ===")
spark.table(SQL_SOURCES_OUTPUT).groupBy("source_type", "source_schema").count().show()
print(f"Total: {spark.table(SQL_SOURCES_OUTPUT).count()} SQL sources")
