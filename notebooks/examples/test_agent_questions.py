"""Fabric Notebook: Test different question formats with Data Agent API

Tests which question styles work through the MCP API.
"""

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.adapters.fabric_agent import FabricAgentClient

WORKSPACE_ID = "REPLACE_WITH_YOUR_WORKSPACE_ID"
AGENT_ID = "REPLACE_WITH_YOUR_AGENT_ID"

access_token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
client = FabricAgentClient(workspace_id=WORKSPACE_ID, agent_id=AGENT_ID, access_token=access_token)

tool_name = client.discover_tool_name()
print(f"Tool: {tool_name}")

# %% Cell 2: Test different question formats
questions = [
    # SQL-style (known working)
    "SELECT name FROM graph_nodes WHERE layer = 'canonical' LIMIT 3",

    # Specific metric name
    "How is USP_PTA_CensusDashboard_PBI calculated?",

    # Specific metric with describe
    "Describe what USP_PTA_CensusDashboard_PBI measures and its criteria",

    # Generic natural language
    "List 3 business metrics available in the system",

    # Direct table reference
    "What data is in the graph_nodes table?",

    # Criteria question
    "What filters does USP_PTA_CensusDashboard_PBI apply?",
]

for q in questions:
    print(f"\nQ: {q[:80]}...")
    resp = client.query(q)
    print(f"Status: {resp.status}")
    if resp.status == "success":
        # Show first 200 chars of answer
        print(f"A: {resp.answer[:200]}...")
    else:
        print(f"Error: {resp.error[:100]}")
    print("-" * 60)
