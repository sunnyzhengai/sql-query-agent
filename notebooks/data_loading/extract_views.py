"""Fabric Notebook: Extract SQL views from on-prem SQL Server.

Connects to SQL Server via On-premises Data Gateway, discovers views
matching the domain filter, tracks changes, and writes sql_sources.

In Fabric: create a new Notebook, copy each cell, attach to your Lakehouse, run all.
"""

# %% Cell 1: Setup
import sys

sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

# Prerequisites: Attach 'sql-logic-env' Fabric Environment. No %pip install.

from src.config import load_config
from src.extractor.connection import create_connection
from src.extractor.extractor import ViewExtractor

# %% Cell 2: Load config and connect to SQL Server
config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

if config.extractor is None:
    raise ValueError("No 'extractor' section in org_config.yaml. See org_config.example.yaml.")

conn = create_connection(config.extractor.sql_server, spark_session=spark)  # noqa: F821
print(f"Connected to {config.extractor.sql_server.host}/{config.extractor.sql_server.database}")
print(f"Domain filter — schemas: {config.extractor.domain.schemas}, base_tables: {config.extractor.domain.base_tables}")

# %% Cell 3: Load existing tracking data
# Existence checked explicitly — Cell 7 overwrites the tracking table, so a
# swallowed read error would reset change tracking (audit 2026-08-15).
tracking_records = []
if spark.catalog.tableExists(config.extractor.tracking_table):
    tracking_df = spark.table(config.extractor.tracking_table)
    tracking_records = [row.asDict() for row in tracking_df.collect()]
    print(f"Loaded {len(tracking_records)} existing tracking records")
else:
    print("No existing tracking table found — starting fresh")

# %% Cell 4: Run extraction
extractor = ViewExtractor(conn, config.extractor.domain)
result = extractor.extract(existing_tracking=tracking_records)

print("\n=== Extraction Summary ===")
print(result.summary)

# %% Cell 5: Review new and changed objects before committing
if result.delta.new:
    print(f"\n--- NEW ({len(result.delta.new)}) ---")
    for obj in result.delta.new:
        print(f"  {obj.schema_name}.{obj.object_name} ({obj.object_type})")

if result.delta.changed:
    print(f"\n--- CHANGED ({len(result.delta.changed)}) ---")
    for obj in result.delta.changed:
        print(f"  {obj.schema_name}.{obj.object_name} ({obj.object_type})")

if result.delta.deleted:
    print(f"\n--- DELETED ({len(result.delta.deleted)}) ---")
    for oid in result.delta.deleted:
        print(f"  {oid}")

if not result.sql_sources:
    print("\nNo new or changed objects to write.")

# STOP HERE and review before running the next cells.
# If you see unexpected objects, adjust your domain filter in org_config.yaml and re-run.

# %% Cell 6: Write extracted sql_sources to Delta table
from pyspark.sql.types import StringType, StructField, StructType  # noqa: E402

if result.sql_sources:
    sql_sources_schema = StructType([
        StructField("metric_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("sql", StringType(), False),
        StructField("steward", StringType(), True),
        StructField("developer", StringType(), True),
    ])

    new_rows = [
        (s["metric_id"], s["name"], s["sql"], s.get("steward"), s.get("developer"))
        for s in result.sql_sources
    ]
    new_df = spark.createDataFrame(new_rows, schema=sql_sources_schema)  # noqa: F821

    # Upsert by metric_id. Existence is checked EXPLICITLY: the old version
    # caught every MERGE failure as "table doesn't exist" and blind-appended,
    # duplicating every row on re-runs — and its SQL contained a stray
    # comment inside the f-string that made the MERGE fail 100% of the time
    # (audit 2026-08-15). A real MERGE failure now raises.
    new_df.createOrReplaceTempView("new_sql_sources")

    if spark.catalog.tableExists(config.lakehouse.sql_sources):
        spark.sql(f"""
            MERGE INTO {config.lakehouse.sql_sources} AS target
            USING new_sql_sources AS source
            ON target.metric_id = source.metric_id
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)
        print(f"Merged {len(result.sql_sources)} sql_sources records")
    else:
        new_df.write.format("delta").saveAsTable(config.lakehouse.sql_sources)
        print(f"Created {config.lakehouse.sql_sources} with {len(result.sql_sources)} records")
else:
    print("Nothing to write — all objects unchanged")

# %% Cell 7: Update tracking table

tracking_schema = StructType([
    StructField("object_id", StringType(), False),
    StructField("schema_name", StringType(), False),
    StructField("object_name", StringType(), False),
    StructField("object_type", StringType(), False),
    StructField("sql_hash", StringType(), False),
    StructField("extracted_at", StringType(), False),
    StructField("sql_definition", StringType(), True),
    StructField("status", StringType(), False),
])

tracking_rows = [
    (r["object_id"], r["schema_name"], r["object_name"], r["object_type"],
     r["sql_hash"], r["extracted_at"], r.get("sql_definition", ""), r["status"])
    for r in result.tracking_records
]

tracking_df = spark.createDataFrame(tracking_rows, schema=tracking_schema)  # noqa: F821
tracking_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(config.extractor.tracking_table)
print(f"Updated tracking table: {len(result.tracking_records)} records")

# %% Cell 8: Summary
current = sum(1 for r in result.tracking_records if r["status"] == "current")
deleted = sum(1 for r in result.tracking_records if r["status"] == "deleted")
print("\n=== Tracking Summary ===")
print(f"  Current: {current}")
print(f"  Deleted: {deleted}")
print("\nNext step: run the Orchestrator notebook to rebuild the graph with the new sql_sources.")
