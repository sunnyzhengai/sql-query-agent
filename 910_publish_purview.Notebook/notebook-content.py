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

"""Publish metric descriptions to Microsoft Purview.

Reads from:  output_metric_logic (Delta)
Writes to:   Microsoft Purview Data Map (Atlas API)

Pushes all metrics with descriptions as Purview catalog entities,
enabling enterprise-wide data governance and search.

Prerequisites:
  - Purview account configured in org_config.yaml
  - Azure identity with Data Curator role on the Purview collection
  - azure-identity package installed in Environment
"""

# %% Cell 0: Setup
import sys

try:
    import src
except ImportError:
    sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
    import src
print(f"v{src.__version__}")

# Version binding (ADR 0042): notebook/wheel skew dies here, loudly.
REQUIRES_ENGINE = "1.24"
from src.engine_floor import require_engine

require_engine(src.__version__, REQUIRES_ENGINE, "910_publish_purview")


from src.config import load_config

config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

if not config.adapters or not config.adapters.purview:
    print("[X] Purview not configured in org_config.yaml")
    print("    Add under adapters:")
    print("      purview:")
    print("        account_name: 'your-purview-account'")
    print("        collection_name: 'your-collection'")
    raise SystemExit("Cannot publish without Purview config.")

purview_cfg = config.adapters.purview
print(f"Purview account: {purview_cfg.account_name}")
print(f"Collection: {purview_cfg.collection_name or '(default)'}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 1: Test Purview connection
from src.steps.gates import precondition_gate

# Required inputs must exist (and be non-empty where the contract says so)
# BEFORE work starts — a missing table fails with a message naming the
# producing notebook, not a pyspark stack trace. Registry-driven; see
# src/steps/gates.py.
precondition_gate("910_publish_purview", table_exists=spark.catalog.tableExists,
                  count=lambda t: spark.table(t).count(),
                  columns_of=lambda t: spark.table(t).columns)


from src.adapters.purview import PurviewAdapter, PurviewConfig

# Auth via service principal (tenant_id + client_id + client_secret in org_config.yaml)
adapter = PurviewAdapter(PurviewConfig(
    account_name=purview_cfg.account_name,
    collection_name=purview_cfg.collection_name,
    custom_type_name=purview_cfg.custom_type_name,
    tenant_id=purview_cfg.tenant_id,
    client_id=purview_cfg.client_id,
    client_secret=purview_cfg.client_secret,
))

print("Testing connection to Purview...")
if adapter.test_connection():
    print("[+] Connected to Purview successfully!")
else:
    print("[X] Connection failed. Check:")
    print("    1. Purview account_name is correct in org_config.yaml")
    print("    2. Service principal has Data Curator role on the Purview collection")
    print("    3. tenant_id, client_id, client_secret are set in org_config.yaml")
    raise SystemExit("Cannot proceed without Purview connection.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 2: Load metrics with descriptions
ml_df = spark.table("output_metric_logic")
metrics = [r.asDict() for r in ml_df.collect()]

with_desc = [m for m in metrics if m.get("description")]
without_desc = [m for m in metrics if not m.get("description")]

print(f"Total metrics: {len(metrics)}")
print(f"With descriptions (will publish): {len(with_desc)}")
print(f"Without descriptions (skipped): {len(without_desc)}")

if not with_desc:
    print("\n[!] No metrics have descriptions. Run 600_generate_descriptions first.")
    raise SystemExit("Nothing to publish.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3: Build metadata records and publish
from src.adapters.base import MetadataRecord

records = []
for m in with_desc:
    # Build a rich description combining business description + source tables
    description = m["description"]
    if m.get("source_tables"):
        description += f"\n\nSource tables: {m['source_tables']}"
    if m.get("table_descriptions"):
        description += f"\n\nTable details: {m['table_descriptions']}"
    # Freshness trailer (Trust family): the catalog card carries the
    # same dates the agent cites — one truth, two surfaces.
    freshness_bits = []
    if m.get("logic_last_changed_at"):
        freshness_bits.append(f"logic last changed {m['logic_last_changed_at'][:10]}")
    if m.get("source_extracted_at"):
        freshness_bits.append(f"source extracted {m['source_extracted_at'][:10]}")
    if freshness_bits:
        description += f"\n\nFreshness: {'; '.join(freshness_bits)}"

    records.append(MetadataRecord(
        asset_id=m["metric_id"],
        # Display name is the schema-qualified identity (ADR 0015): bare
        # object names collide across schemas and become indistinguishable
        # in the Purview browse view. Business-friendly display names come
        # later from PBI lineage, which supplies genuinely distinct names.
        name=m["metric_id"],
        asset_type="metric",
        description=description,
        owner=m.get("steward") or "",
        properties={
            "schema": m["metric_id"].split(".")[0] if "." in m["metric_id"] else "dbo",
            "transform_count": str(m.get("transform_count", 0)),
            "has_calculation_logic": str(m.get("calculation_logic") is not None),
        },
    ))

print(f"\nPublishing {len(records)} metrics to Purview...")
result = adapter.publish_bulk(records)

succeeded = sum(1 for r in result.results if r.status.value == "success")
failed = sum(1 for r in result.results if r.status.value == "failed")

print(f"\n[+] Published: {succeeded}")
if failed:
    print(f"[!] Failed: {failed}")
    for r in result.results:
        if r.status.value == "failed":
            print(f"    {r.asset_id}: {r.message[:100]}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 3b: Durable publish log (gov_publish_log — admin telemetry)
# Every push is answerable forever: what went to Purview, and did it land.
from datetime import datetime, timezone

from src.governance.publish_log import publish_log_rows
from src.schemas import PUBLISH_LOG, to_spark_schema

_now = datetime.now(timezone.utc)
log_rows = publish_log_rows(
    result, target="purview", kind="asset",
    run_id=_now.strftime("%Y%m%dT%H%M%SZ"),
    published_at=_now.isoformat(),
)
if log_rows:
    spark.createDataFrame(log_rows, schema=to_spark_schema(PUBLISH_LOG)) \
        .write.format("delta").mode("append").saveAsTable("gov_publish_log")
print(f"[+] gov_publish_log: {len(log_rows)} rows appended")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# %% Cell 4: Summary
print(f"\n{'=' * 60}")
print("PURVIEW PUBLISH SUMMARY")
print(f"{'=' * 60}")
print(f"  Purview account:    {purview_cfg.account_name}")
print(f"  Collection:         {purview_cfg.collection_name or '(default)'}")
print(f"  Metrics published:  {succeeded}/{len(records)}")
print(f"  Failed:             {failed}")
if succeeded > 0:
    print(f"\n  Verify in Purview: https://{purview_cfg.account_name}.purview.azure.com")
    print("  Search for any metric name (e.g., 'USP_Severe_Sepsis') to see the catalog entry.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
