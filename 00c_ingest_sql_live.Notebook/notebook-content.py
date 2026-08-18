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

"""Fabric Notebook: Ingestion Route C — live extraction from a SQL source

ROUTE: one of the peer acquisition routes (00a filedrop | 00b folders |
00c live). All routes write input_sql_sources under the same contract;
run whichever matches where your SQL lives — see the INSTALLATION_GUIDE
route table.

The turn-key front door (1.8.0): connects via the configured profile
(onprem_gateway | azure_direct | fabric_native), discovers procedures
and views, tracks changes by content hash, and MERGES new/changed
objects into input_sql_sources. Manual file upload (01_install) remains
the fallback path; both writers share the metric_id upsert protocol.

Reads from: the customer SQL source (sys.objects / sys.sql_modules)
Writes to:  input_sql_sources (merge), ops_extraction_tracking

Acquisition is event-driven: run when source SQL changes — only new
and changed objects are re-loaded. 01_install verifies state after.
"""

# %% Cell 0: Setup
import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

from src.config import load_config
from src.extractor.connection import create_connection
from src.extractor.extractor import ViewExtractor

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

if config.extractor is None:
    raise ValueError(
        "No 'extractor' section in org_config.yaml — add one (see "
        "org_config.example.yaml and INSTALLATION_GUIDE 'Automated "
        "Extraction'), or load SQL files manually via 01_install."
    )

conn = create_connection(config.extractor.sql_server, spark_session=spark)  # noqa: F821
print(f"Source: {config.extractor.sql_server.host}/{config.extractor.sql_server.database} "
      f"({config.extractor.sql_server.source_type})")
print(f"Domain filter — schemas: {config.extractor.domain.schemas}, "
      f"base_tables: {config.extractor.domain.base_tables}, "
      f"object_types: {config.extractor.domain.object_types}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Load existing tracking data
# Existence checked explicitly — Cell 4 overwrites the tracking table, so a
# swallowed read error would reset change tracking (audit 2026-08-15).
tracking_records = []
if spark.catalog.tableExists(config.extractor.tracking_table):
    tracking_df = spark.table(config.extractor.tracking_table)
    tracking_records = [row.asDict() for row in tracking_df.collect()]
    print(f"Loaded {len(tracking_records)} existing tracking records")
else:
    print("No existing tracking table found — starting fresh")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Run extraction and REVIEW the delta before committing
extractor = ViewExtractor(conn, config.extractor.domain)
result = extractor.extract(existing_tracking=tracking_records)

print("\n=== Extraction Summary ===")
print(result.summary)

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

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3: Write extracted sql_sources to Delta (merge by metric_id)
from pyspark.sql.types import StringType, StructField, StructType  # noqa: E402

if result.sql_sources:
    # Column set MUST match the input_sql_sources contract (7 columns) —
    # MERGE ... UPDATE SET * fails or nulls columns when source and target
    # schemas differ. The extractor emits all seven.
    sql_sources_schema = StructType([
        StructField("metric_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("sql", StringType(), False),
        StructField("steward", StringType(), True),
        StructField("developer", StringType(), True),
        StructField("source_type", StringType(), True),
        StructField("source_schema", StringType(), True),
    ])

    new_rows = [
        (s["metric_id"], s["name"], s["sql"], s.get("steward"), s.get("developer"),
         s.get("source_type"), s.get("source_schema"))
        for s in result.sql_sources
    ]
    new_df = spark.createDataFrame(new_rows, schema=sql_sources_schema)  # noqa: F821

    # Upsert by metric_id. Existence is checked EXPLICITLY: the old version
    # caught every MERGE failure as "table doesn't exist" and blind-appended,
    # duplicating every row on re-runs (audit 2026-08-15). A real MERGE
    # failure now raises.
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

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 4: Update tracking table and summarize

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

current = sum(1 for r in result.tracking_records if r["status"] == "current")
deleted = sum(1 for r in result.tracking_records if r["status"] == "deleted")
print("\n=== Tracking Summary ===")
print(f"  Current: {current}")
print(f"  Deleted: {deleted}")
print("\nNext: run 01_install (first install) or 02_parse onward (refresh).")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
