"""Fabric Notebook: Load SQL files from another workspace into sql_sources Delta table.

Reads .sql files from an ABFS path, extracts file names as metric IDs,
and saves the full SQL text as sql_sources for the orchestrator.

To use in Fabric:
1. Create a new Notebook or add as a cell in your orchestrator
2. Update the SQL_FILES_PATH to your ABFS path
3. Attach to the Lakehouse where you want sql_sources
4. Run all cells
"""

# %% Cell 1: Configuration
# UPDATE THIS PATH to point to your SQL files
SQL_FILES_PATH = "abfss://BI-POC@onelake.dfs.fabric.microsoft.com/SZ_SQL_Logic.Lakehouse/Files/data/procs_cookrpt"

# Output table name
SQL_SOURCES_OUTPUT = "sql_sources"

# %% Cell 2: Read SQL files and build sql_sources
from pyspark.sql.functions import input_file_name, regexp_extract

# Read all .sql files as whole text (one row per file)
sql_files = spark.read.text(SQL_FILES_PATH + "/*.sql", wholetext=True)

# Extract file name as metric_id and name
sql_sources_df = (
    sql_files
    .withColumn("file_path", input_file_name())
    .withColumn("file_name", regexp_extract("file_path", r"([^/]+)\.sql$", 1))
    .selectExpr(
        "file_name as metric_id",
        "file_name as name",
        "value as sql",
        "null as steward",
        "null as developer",
    )
)

print(f"Found {sql_sources_df.count()} SQL files")
sql_sources_df.select("metric_id").show(50, truncate=False)

# %% Cell 3: Save as Delta table
sql_sources_df.write.format("delta").mode("overwrite").saveAsTable(SQL_SOURCES_OUTPUT)
print(f"Saved {sql_sources_df.count()} records to {SQL_SOURCES_OUTPUT}")

# %% Cell 4: Verify
print(f"=== {SQL_SOURCES_OUTPUT} ===")
spark.table(SQL_SOURCES_OUTPUT).select("metric_id", "name").show(50, truncate=False)
print(f"Total: {spark.table(SQL_SOURCES_OUTPUT).count()} SQL sources")
