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

"""Fabric Notebook: Ingestion Route A — file drop

ROUTE: one of the peer acquisition routes (00a filedrop | 00b folders |
00c live). All routes write input_sql_sources under the same contract;
run whichever matches where your SQL lives — see the INSTALLATION_GUIDE
route table. Acquisition is event-driven: run when files change.

Reads from: Files/sql-query-agent/sql_input/*.sql
Writes to:  input_sql_sources (overwrite)
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

require_engine(src.__version__, REQUIRES_ENGINE, "010_ingest_sql_filedrop")


from src.config import load_config  # noqa: F401

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# %% Cell 1: Load .sql files from sql_input/ into input_sql_sources
from src.parser.identity import (
    extract_object_identity,
    find_duplicate_identities,
    normalize_sql_text,
)
from src.schemas import SQL_SOURCES, to_spark_schema

SQL_DIR = "/lakehouse/default/Files/sql-query-agent/sql_input/"
if not os.path.isdir(SQL_DIR):
    raise SystemExit(
        "sql_input/ folder not found — this route loads dropped .sql files. "
        "Create Files/sql-query-agent/sql_input/ and upload, or use route "
        "00b (folders) / 00c (live extraction) instead."
    )

sql_rows = []
identity_files = []
skipped = []
for root, dirs, files in os.walk(SQL_DIR):
    for fname in sorted(files):
        if not fname.endswith(".sql"):
            continue
        filepath = os.path.join(root, fname)
        try:
            with open(filepath, encoding="utf-8-sig") as f:
                sql_content = normalize_sql_text(f.read())
            schema, obj_name, source_type = extract_object_identity(sql_content)
            if schema and obj_name:
                metric_id = f"{schema}.{obj_name}"
                display_name = obj_name
                source_schema = schema
            else:
                metric_id = fname.replace(".sql", "")
                display_name = metric_id
                source_schema = None
                print(f"  [!] No CREATE PROCEDURE/VIEW found in {fname} — using filename as metric_id")
            sql_rows.append((metric_id, display_name, sql_content, None, None, source_type, source_schema))
            identity_files.append((metric_id, os.path.relpath(filepath, SQL_DIR)))
        except Exception as e:  # noqa: BLE001 — recorded in `skipped`, reported below
            skipped.append((fname, str(e)))

if not sql_rows:
    raise SystemExit("No .sql files found in sql_input/ — upload your SQL files first.")

# Contract gate: unique(metric_id). Two definitions of the same
# [schema].[object] is a governance decision, not something to guess at.
collisions = find_duplicate_identities(identity_files)
if collisions:
    print(f"[X] FATAL: {len(collisions)} duplicate metric identities detected:")
    for metric_id, files in sorted(collisions.items()):
        print(f"    {metric_id} is defined by {len(files)} files:")
        for f in files:
            print(f"      - {f}")
    print("    Each [schema].[object] may be defined by exactly one file.")
    raise SystemExit("Resolve duplicate identities first.")

sql_df = spark.createDataFrame(sql_rows, schema=to_spark_schema(SQL_SOURCES))
sql_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("input_sql_sources")

print(f"\n[+] Loaded {len(sql_rows)} SQL files into input_sql_sources")
schemas_found = set(r[6] for r in sql_rows if r[6])
print(f"    Schemas found: {', '.join(sorted(schemas_found)) if schemas_found else 'none'}")
if skipped:
    print(f"[!] Skipped {len(skipped)} files: {', '.join(f[0] for f in skipped)}")
print("\nNext: run 100_install to verify state, then 200_parse onward.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************
