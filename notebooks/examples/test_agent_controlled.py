"""Fabric Notebook: Controlled test — 3 known-good metrics via API

Tests the Data Agent API with 3 metrics confirmed to work in the chat UI.
"""

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.adapters.fabric_agent import FabricAgentClient

WORKSPACE_ID = "REPLACE_WITH_YOUR_WORKSPACE_ID"
AGENT_ID = "REPLACE_WITH_YOUR_AGENT_ID"

access_token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
client = FabricAgentClient(workspace_id=WORKSPACE_ID, agent_id=AGENT_ID, access_token=access_token)
client.discover_tool_name()

# %% Cell 2: Test 3 known-good metrics
test_metrics = [
    "usp_PTA_CensusDashboard_PBI",
    "usp_SF_CensusDashboard",
    "USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS",
]

for name in test_metrics:
    print(f"\n{'='*60}")
    print(f"Metric: {name}")
    resp = client.query(f"How is {name} calculated?")
    print(f"Status: {resp.status}")
    print(f"Answer:\n{resp.answer[:500]}")
    print()

# %% Cell 3: Check edges for these metrics
print("=== Edge check ===")
edges_df = spark.table("graph_edges")

for name in test_metrics:
    canonical_edges = edges_df.filter(f"source_id = 'canonical:{name}'").count()
    transform_edges = edges_df.filter(f"source_id LIKE 'transform:{name}%'").count()
    print(f"{name}: {canonical_edges} canonical edges, {transform_edges} transform edges")

# %% Cell 4: Compare API response with the generate_metric_description format
print("\n=== Testing generate_metric_description format ===")
for name in test_metrics:
    print(f"\n{'='*60}")
    print(f"Metric: {name}")
    resp = client.generate_metric_description(name)
    print(f"Status: {resp.status}")
    print(f"Answer:\n{resp.answer[:500]}")
