# Collibra Description Update Test
# Test updating the Description attribute on an existing Power BI Report
# in Collibra Dev. Fill in your credentials below.

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
# For local: sys.path.insert(0, ".")

from src.adapters.collibra import CollibraAdapter, CollibraConfig

# ── Fill in your credentials ──
COLLIBRA_URL = "https://YOUR_INSTANCE.collibra.com/rest/2.0"  # TODO: fill in
USERNAME = "YOUR_USERNAME"  # TODO: fill in
PASSWORD = "YOUR_PASSWORD"  # TODO: fill in

PBI_REPORT_TYPE_ID = "00000000-0000-0000-0000-100000000006"

adapter = CollibraAdapter(CollibraConfig(
    base_url=COLLIBRA_URL,
    username=USERNAME,
    password=PASSWORD,
    asset_type_id=PBI_REPORT_TYPE_ID,
))

print("Testing connection...")
if adapter.test_connection():
    print("Connected!")
else:
    print("Connection failed. Check credentials and URL.")

# %% Cell 2: Update a single report description
# Change REPORT_NAME to a report that exists in your Collibra Dev instance.
# Use the exact name as it appears in Collibra (from discovery output).

REPORT_NAME = "340B Eligible Charges for HB and PB"  # TODO: change to your report
DESCRIPTION = "This report tracks 340B-eligible charges across hospital-based and professional billing."

result = adapter.update_description(REPORT_NAME, DESCRIPTION)
print(f"Status: {result.status.value}")
print(f"Message: {result.message}")

# %% Cell 3: Verify the update
# Read back the Description attribute to confirm it was written.
from src.adapters.collibra_lineage import CollibraClient

# Reuse the same credentials — CollibraClient wants the base URL without /rest/2.0
base = COLLIBRA_URL.replace("/rest/2.0", "")
client = CollibraClient(base, USERNAME, PASSWORD)

assets = client.find_asset_by_name(REPORT_NAME, PBI_REPORT_TYPE_ID)
if assets:
    asset_id = assets[0]["id"]
    attrs = client.get_asset_attributes(asset_id)
    for attr in attrs:
        if attr["type"]["id"] == CollibraAdapter.DESCRIPTION_ATTR_TYPE_ID:
            print(f"Description on '{REPORT_NAME}':")
            print(f"  {attr['value']}")
            break
    else:
        print("No Description attribute found after update.")
else:
    print(f"Asset not found: {REPORT_NAME}")

# %% Cell 4: Bulk update (optional)
# Update descriptions on multiple reports at once.
# from src.adapters.base import MetadataRecord
#
# records = [
#     MetadataRecord(
#         asset_id="report-1",
#         asset_type="report",
#         name="Report Name Here",
#         description="Description for this report.",
#     ),
#     MetadataRecord(
#         asset_id="report-2",
#         asset_type="report",
#         name="Another Report",
#         description="Description for another report.",
#     ),
# ]
#
# bulk_result = adapter.update_descriptions_bulk(records)
# print(bulk_result)
# for r in bulk_result.results:
#     print(f"  {r.asset_id}: {r.status.value} — {r.message}")
