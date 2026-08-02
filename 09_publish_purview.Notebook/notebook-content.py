# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
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
    print("\n[!] No metrics have descriptions. Run 07_generate_descriptions first.")
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

    records.append(MetadataRecord(
        asset_id=m["metric_id"],
        name=m["metric_name"],
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

# %% Cell 4: Summary
print(f"\n{'=' * 60}")
print(f"PURVIEW PUBLISH SUMMARY")
print(f"{'=' * 60}")
print(f"  Purview account:    {purview_cfg.account_name}")
print(f"  Collection:         {purview_cfg.collection_name or '(default)'}")
print(f"  Metrics published:  {succeeded}/{len(records)}")
print(f"  Failed:             {failed}")
if succeeded > 0:
    print(f"\n  Verify in Purview: https://{purview_cfg.account_name}.purview.azure.com")
    print(f"  Search for any metric name (e.g., 'USP_Severe_Sepsis') to see the catalog entry.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
