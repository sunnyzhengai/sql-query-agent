"""Fabric Notebook: Test Data Agent via MCP protocol

The Data Agent uses JSON-RPC (MCP) format, not chat completions.
"""

# %% Cell 1: Configure
WORKSPACE_ID = "REPLACE_WITH_YOUR_WORKSPACE_ID"
AGENT_ID = "REPLACE_WITH_YOUR_AGENT_ID"

# %% Cell 2: Test MCP query
import requests
import json

token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

endpoint = f"https://api.fabric.microsoft.com/v1/mcp/workspaces/{WORKSPACE_ID}/dataagents/{AGENT_ID}/agent"

# MCP JSON-RPC format
payload = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": "1"
}

print("Listing available tools...")
resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")

# %% Cell 3: Call the agent with a question
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "query",
        "arguments": {"question": "What metrics are available? List the first 3."}
    },
    "id": "2"
}

print("Asking agent a question...")
resp = requests.post(endpoint, headers=headers, json=payload, timeout=120)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)[:1000]}")

# %% Cell 4: If Cell 3 fails, try alternative tool names
# The tool name might not be "query" — Cell 2 should show available tools
# Try with different method/param combinations

alternatives = [
    {"method": "tools/call", "params": {"name": "ask", "arguments": {"question": "Say hello"}}},
    {"method": "tools/call", "params": {"name": "chat", "arguments": {"message": "Say hello"}}},
    {"method": "completion", "params": {"messages": [{"role": "user", "content": "Say hello"}]}},
    {"method": "query", "params": {"question": "Say hello"}},
]

for i, alt in enumerate(alternatives):
    payload = {"jsonrpc": "2.0", **alt, "id": str(i + 10)}
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        print(f"\nAttempt {i+1}: method={alt['method']}")
        print(f"  Status: {resp.status_code}")
        result = resp.json()
        if "error" not in result:
            print(f"  SUCCESS: {json.dumps(result, indent=2)[:500]}")
            break
        else:
            print(f"  Error: {result.get('error', {}).get('message', 'unknown')}")
    except Exception as e:
        print(f"  Failed: {e}")
