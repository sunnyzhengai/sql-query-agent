"""Fabric Notebook: Debug Data Agent API v2

The MCP endpoint works but returns "no metrics found".
Published chat UI works fine. This tests alternative endpoints
and query formats to find the right API pattern.
"""

# %% Cell 1: Setup (reuse from previous debug)
import requests
import json

WORKSPACE_ID = "REPLACE_WITH_YOUR_WORKSPACE_ID"
AGENT_ID = "REPLACE_WITH_YOUR_AGENT_ID"

token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
mcp_endpoint = f"https://api.fabric.microsoft.com/v1/mcp/workspaces/{WORKSPACE_ID}/dataagents/{AGENT_ID}/agent"

# %% Cell 2: Try alternative non-MCP endpoints
payload = {
    "messages": [
        {"role": "user", "content": "What metrics are available? List the first 3."}
    ]
}

endpoints_to_try = [
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items/{AGENT_ID}/jobs/instances?jobType=DataAgentChat",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/dataagents/{AGENT_ID}/conversations",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/dataagents/{AGENT_ID}/query",
]

for ep in endpoints_to_try:
    try:
        resp = requests.post(ep, headers=headers, json=payload, timeout=30)
        short = ep.split(AGENT_ID + "/")[1] if AGENT_ID in ep else ep[-30:]
        print(f"{resp.status_code}: .../{short}")
        if resp.status_code != 404:
            print(f"  {resp.text[:300]}")
            print()
    except Exception as e:
        print(f"ERROR: {e}")

# %% Cell 3: Try SQL query directly through MCP
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "DataAgent_SQL_Query_Agent",
        "arguments": {"userQuestion": "SELECT name FROM graph_nodes WHERE layer = 'canonical' LIMIT 3"}
    },
    "id": "3"
}

print("Trying direct SQL through MCP...")
resp = requests.post(mcp_endpoint, headers=headers, json=payload, timeout=120)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2)[:1000])

# %% Cell 4: Try different question phrasings through MCP
questions = [
    "List all canonical nodes from graph_nodes table",
    "Query graph_nodes and show me 3 rows where layer equals canonical",
    "How is USP_PTA_CensusDashboard_PBI calculated?",
    "Show me data from the graph_nodes table",
]

for q in questions:
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "DataAgent_SQL_Query_Agent",
            "arguments": {"userQuestion": q}
        },
        "id": "4"
    }

    print(f"\nQ: {q}")
    resp = requests.post(mcp_endpoint, headers=headers, json=payload, timeout=120)
    result = resp.json()
    if "result" in result:
        content = result["result"].get("content", [{}])
        if isinstance(content, list) and content:
            text = content[0].get("text", "")[:200]
        else:
            text = str(content)[:200]
        print(f"A: {text}")
    elif "error" in result:
        print(f"Error: {result['error'].get('message', '')[:200]}")

# %% Cell 5: Check if MCP needs initialization first
# Some MCP servers need an initialize handshake before tools/call
payload_init = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "sql-query-agent", "version": "0.1.0"}
    },
    "id": "init-1"
}

print("\nSending MCP initialize...")
resp = requests.post(mcp_endpoint, headers=headers, json=payload_init, timeout=30)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2)[:500])

# Now try query again after initialize
print("\nRetrying query after initialize...")
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "DataAgent_SQL_Query_Agent",
        "arguments": {"userQuestion": "What metrics are available? List the first 3."}
    },
    "id": "5"
}
resp = requests.post(mcp_endpoint, headers=headers, json=payload, timeout=120)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2)[:1000])
