"""Fabric Notebook: Debug Data Agent API endpoints

Tests which API endpoint pattern works for your Data Agent.
"""

# %% Cell 1: Configure
WORKSPACE_ID = "REPLACE_WITH_YOUR_WORKSPACE_ID"
AGENT_ID = "REPLACE_WITH_YOUR_AGENT_ID"

# %% Cell 2: Test all endpoint patterns
import requests

token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")

endpoints = [
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items/{AGENT_ID}/chat/completions",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/dataagents/{AGENT_ID}/chat/completions",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/aiskills/{AGENT_ID}/chat/completions",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items/{AGENT_ID}/getCompletion",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/aiskills/{AGENT_ID}/getCompletion",
    f"https://api.fabric.microsoft.com/v1/mcp/workspaces/{WORKSPACE_ID}/dataagents/{AGENT_ID}/agent",
]

payload = {"messages": [{"role": "user", "content": "Say hello"}]}
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

for ep in endpoints:
    try:
        resp = requests.post(ep, headers=headers, json=payload, timeout=30)
        short = ep.replace(f"https://api.fabric.microsoft.com/v1/", "").replace(WORKSPACE_ID, "WS").replace(AGENT_ID, "AG")
        print(f"{resp.status_code}: {short}")
        if resp.status_code != 404:
            print(f"  Response: {resp.text[:300]}")
            print()
    except Exception as e:
        print(f"ERROR: {e}")

# %% Cell 3: Test with GET to check if agent exists
print("Checking if agent exists...\n")

get_endpoints = [
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items/{AGENT_ID}",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/dataagents/{AGENT_ID}",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/aiskills/{AGENT_ID}",
]

for ep in get_endpoints:
    try:
        resp = requests.get(ep, headers=headers, timeout=15)
        short = ep.replace(f"https://api.fabric.microsoft.com/v1/", "").replace(WORKSPACE_ID, "WS").replace(AGENT_ID, "AG")
        print(f"{resp.status_code}: {short}")
        if resp.status_code == 200:
            print(f"  FOUND: {resp.text[:300]}")
            print()
    except Exception as e:
        print(f"ERROR: {e}")
