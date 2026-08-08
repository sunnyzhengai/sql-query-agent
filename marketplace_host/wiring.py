"""Production dependency wiring for the Functions host.

Kept separate from function_app so the pieces are importable and the
HTTP client is testable without azure-functions installed.
"""

from __future__ import annotations

import requests

from marketplace_host.handlers import HostConfig

MARKETPLACE_API = "https://marketplaceapi.microsoft.com/api/saas"
API_VERSION = "2018-08-31"  # v2's wire version — unchanged since GA
MARKETPLACE_RESOURCE = "20e940b3-4c77-4b0b-9a53-9e16a1b010a7"


class HttpMarketplaceClient:
    """SaaS Fulfillment v2 over HTTP. token_provider returns a bearer
    token for scope f"{MARKETPLACE_RESOURCE}/.default" (client
    credentials against the publisher tenant; 1h lifetime — provider
    owns caching/refresh)."""

    def __init__(self, token_provider, timeout: int = 30) -> None:
        self._token = token_provider
        self.timeout = timeout

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json"}

    def resolve(self, purchase_token: str) -> dict:
        r = requests.post(
            f"{MARKETPLACE_API}/subscriptions/resolve",
            params={"api-version": API_VERSION},
            headers=self._headers() | {"x-ms-marketplace-token": purchase_token},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def activate(self, subscription_id: str, plan_id: str) -> None:
        r = requests.post(
            f"{MARKETPLACE_API}/subscriptions/{subscription_id}/activate",
            params={"api-version": API_VERSION},
            headers=self._headers(),
            json={"planId": plan_id},
            timeout=self.timeout,
        )
        r.raise_for_status()

    def get_operation(self, subscription_id: str, operation_id: str) -> dict:
        r = requests.get(
            f"{MARKETPLACE_API}/subscriptions/{subscription_id}/operations/{operation_id}",
            params={"api-version": API_VERSION},
            headers=self._headers(),
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def ack_operation(self, subscription_id: str, operation_id: str,
                      status: str) -> None:
        r = requests.patch(
            f"{MARKETPLACE_API}/subscriptions/{subscription_id}/operations/{operation_id}",
            params={"api-version": API_VERSION},
            headers=self._headers(),
            json={"status": status},
            timeout=self.timeout,
        )
        r.raise_for_status()


class InMemoryStore:
    """Dev/test store. Production: Azure Table Storage with the same
    two methods."""

    def __init__(self) -> None:
        self._rows: dict = {}

    def get(self, subscription_id: str) -> "dict | None":
        return self._rows.get(subscription_id)

    def save(self, record: dict) -> None:
        self._rows[record["subscription_id"]] = dict(record)


def build_dependencies(config: HostConfig):
    """Deploy-time wiring. Token provider + JWKS verifier are stubs that
    fail loudly until phase T2 fills them in — never silently insecure."""

    def token_provider() -> str:
        raise NotImplementedError(
            "Phase T2: client-credentials token for scope "
            f"{MARKETPLACE_RESOURCE}/.default (MSAL confidential client)"
        )

    def verify_token(token: str) -> "dict | None":
        raise NotImplementedError(
            "Phase T2: validate signature against Entra JWKS "
            f"(tenant {config.publisher_tenant_id}) before decoding claims"
        )

    return InMemoryStore(), HttpMarketplaceClient(token_provider), verify_token
