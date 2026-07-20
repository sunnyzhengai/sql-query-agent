"""Fabric Notebook: Test Fabric Lineage API

Discovers the actual dependency chain between PBI reports and their
data sources using the Fabric/Power BI lineage APIs.

Run this to see what lineage data is available in your workspace.
"""

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.adapters.fabric_lineage import FabricLineageClient

# %% Cell 2: Test lineage for a PBI workspace
# UPDATE with a workspace ID that contains PBI reports
PBI_WORKSPACE_ID = "REPLACE_WITH_PBI_WORKSPACE_ID"

# Get token from Fabric (mssparkutils is a global in Fabric notebooks)
access_token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
client = FabricLineageClient(access_token=access_token)

# Get raw lineage data
print("Fetching workspace lineage...")
lineage_data = client.get_workspace_lineage(PBI_WORKSPACE_ID)

if lineage_data:
    print(f"Got lineage data. Keys: {list(lineage_data.keys())}")
    # Show raw structure for debugging
    import json
    print(json.dumps(lineage_data, indent=2, default=str)[:2000])
else:
    print("No lineage data returned. Check workspace ID and permissions.")

# %% Cell 3: Get report-level lineage
print("Building report lineage...")
report_lineages = client.get_report_lineage(PBI_WORKSPACE_ID)

print(f"\nFound {len(report_lineages)} reports with lineage:\n")
for rl in report_lineages[:10]:
    print(f"  Report: {rl.report_name}")
    print(f"    Datasets: {[d.name for d in rl.upstream_datasets]}")
    print(f"    Sources: {[s.name for s in rl.upstream_sources]}")
    print(f"    Tables: {rl.source_tables[:5]}")
    print()

if len(report_lineages) > 10:
    print(f"  ... and {len(report_lineages) - 10} more")

# %% Cell 4: Scan multiple PBI workspaces
# Add all your PBI workspace IDs here
PBI_WORKSPACE_IDS = [
    "REPLACE_WITH_WORKSPACE_ID_1",
    # "REPLACE_WITH_WORKSPACE_ID_2",
    # "REPLACE_WITH_WORKSPACE_ID_3",
]

all_lineages = []
for ws_id in PBI_WORKSPACE_IDS:
    print(f"Scanning workspace {ws_id}...")
    lineages = client.get_report_lineage(ws_id)
    all_lineages.extend(lineages)
    print(f"  Found {len(lineages)} reports")

print(f"\nTotal: {len(all_lineages)} reports across {len(PBI_WORKSPACE_IDS)} workspaces")

# Show reports with their source tables
for rl in all_lineages[:20]:
    tables_str = ", ".join(rl.source_tables[:3]) if rl.source_tables else "(no tables found)"
    print(f"  {rl.report_name} -> {tables_str}")
