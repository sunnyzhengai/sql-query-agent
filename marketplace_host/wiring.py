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


class JsonFileSubscriptionStore:
    """Durable single-file store — right-sized for one App Service
    instance at listing-launch volume (a handful of subscriptions).
    Azure Table Storage swaps in behind the same two methods when
    volume ever justifies it."""

    def __init__(self, path) -> None:
        import pathlib
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        import json
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text() or "{}")

    def get(self, subscription_id: str) -> "dict | None":
        return self._load().get(subscription_id)

    def save(self, record: dict) -> None:
        import json
        rows = self._load()
        rows[record["subscription_id"]] = dict(record)
        self.path.write_text(json.dumps(rows, indent=1))


def entra_token_provider(tenant_id: str, client_id: str,
                         client_secret: str):
    """Client-credentials token for the Fulfillment API scope, cached
    until 5 minutes before expiry (T2 implementation, 2026-08-11)."""
    import time

    cache = {"token": "", "expires": 0.0}

    def provider() -> str:
        if time.time() < cache["expires"] - 300:
            return cache["token"]
        r = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": f"{MARKETPLACE_RESOURCE}/.default",
            },
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()
        cache["token"] = body["access_token"]
        cache["expires"] = time.time() + int(body.get("expires_in", 3600))
        return cache["token"]

    return provider


def entra_webhook_verifier(tenant_id: str):
    """Webhook JWT verification against Entra's JWKS (T2, 2026-08-11):
    signature + expiry here; claim checks (aud/tid) stay in
    validate_webhook_claims so tests cover them without crypto.
    Returns decoded claims, or None on any verification failure."""
    import jwt
    from jwt import PyJWKClient

    jwks = PyJWKClient(
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys")

    def verify(token: str) -> "dict | None":
        try:
            key = jwks.get_signing_key_from_jwt(token)
            return jwt.decode(
                token, key.key, algorithms=["RS256"],
                options={"verify_aud": False},  # aud checked by claims layer
            )
        except Exception:                        # noqa: BLE001
            return None

    return verify


def build_dependencies(config: HostConfig):
    """Deploy-time wiring (dev flavor): in-memory store + loud-failing
    token provider. Production wiring lives in src.webapp.main, which
    supplies entra_token_provider / entra_webhook_verifier /
    JsonFileSubscriptionStore from env config."""

    def token_provider() -> str:
        raise NotImplementedError(
            "supply entra_token_provider(tenant, client_id, secret)")

    return InMemoryStore(), HttpMarketplaceClient(token_provider), \
        entra_webhook_verifier(config.publisher_tenant_id)
