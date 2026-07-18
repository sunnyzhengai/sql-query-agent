"""Fabric Notebook: Test Collibra OAuth Connection

Test OAuth client_credentials flow against Collibra.
Kept as .py for version control — copy cells into a Fabric Notebook.

Prerequisites:
    - %pip install requests
    - A Collibra OAuth Integration app with client_id and client_secret
"""

# %% Cell 1: Setup
import requests

# REPLACE THESE THREE VALUES
collibra_base = "https://YOUR-COLLIBRA-DEV"
client_id = "YOUR-CLIENT-ID"
client_secret = "YOUR-CLIENT-SECRET"

# %% Cell 2: Get OAuth token (tries two endpoints)
print("Attempting OAuth token...")

# Try Collibra sessions endpoint
token_resp = requests.post(
    f"{collibra_base}/rest/2.0/auth/sessions",
    json={"grantType": "client_credentials", "clientId": client_id, "clientSecret": client_secret},
    timeout=10,
)
print(f"Sessions endpoint: {token_resp.status_code}")

if token_resp.status_code != 200:
    # Try standard OAuth endpoint
    token_resp = requests.post(
        f"{collibra_base}/rest/oauth/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=10,
    )
    print(f"OAuth endpoint: {token_resp.status_code}")

if token_resp.status_code != 200:
    # Try alternative token endpoint
    token_resp = requests.post(
        f"{collibra_base}/rest/2.0/auth/oauth/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=10,
    )
    print(f"Alt OAuth endpoint: {token_resp.status_code}")

print(f"Response: {token_resp.text[:500]}")

# %% Cell 3: Test API call with token (only run after Cell 2 succeeds)
if token_resp.status_code == 200:
    token_data = token_resp.json()
    # Token might be in different fields depending on endpoint
    token = token_data.get("token") or token_data.get("access_token") or token_data.get("csrfToken")

    if token:
        print(f"Got token: {token[:20]}...")

        # Test API call
        test_resp = requests.get(
            f"{collibra_base}/rest/2.0/users/current",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        print(f"API test status: {test_resp.status_code}")
        print(f"Response: {test_resp.text[:300]}")
    else:
        print(f"Token not found in response. Full response: {token_data}")
else:
    print("Could not get token — check client_id, client_secret, and collibra_base URL")
