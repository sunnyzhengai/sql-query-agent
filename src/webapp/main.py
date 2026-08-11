"""Production wiring for the AIVIA web app.

Env (chat):
  AIVIA_KUSTO_URI       Eventhouse query URI
  AIVIA_KUSTO_DB        database name
  OPENAI_BASE_URL / OPENAI_API_KEY / AIVIA_LLM_MODEL   (Azure OpenAI)
  AIVIA_EVENTS_PATH     TurnEvent JSONL path (default data/events/...)

Env (marketplace — all four present enables the fulfillment endpoints):
  MKT_FULFILLMENT_APP_ID   Entra app id from the offer's technical config
  MKT_PUBLISHER_TENANT_ID
  MKT_CLIENT_ID / MKT_CLIENT_SECRET   client credentials for the
                                      Fulfillment API + JWKS validation

Run locally:  uvicorn src.webapp.main:app --reload
App Service:  gunicorn -k uvicorn.workers.UvicornWorker src.webapp.main:app
              (Easy Auth ON — the platform owns sign-in; the app reads
              X-MS-CLIENT-PRINCIPAL-NAME)
"""

from __future__ import annotations

import os
from pathlib import Path


def _kusto_run():
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider
    uri = os.environ.get(
        "AIVIA_KUSTO_URI",
        "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com")
    db = os.environ.get("AIVIA_KUSTO_DB", "probe-eh")
    return KustoClient(uri, db, az_cli_token_provider(uri)).run


def _marketplace():
    keys = ("MKT_FULFILLMENT_APP_ID", "MKT_PUBLISHER_TENANT_ID",
            "MKT_CLIENT_ID", "MKT_CLIENT_SECRET")
    if not all(os.environ.get(k) for k in keys):
        return None
    from marketplace_host.handlers import HostConfig
    from marketplace_host.wiring import (
        HttpMarketplaceClient,
        entra_token_provider,
        entra_webhook_verifier,
        JsonFileSubscriptionStore,
    )
    from src.webapp.app import MarketplaceDeps
    tenant = os.environ["MKT_PUBLISHER_TENANT_ID"]
    return MarketplaceDeps(
        config=HostConfig(
            fulfillment_app_id=os.environ["MKT_FULFILLMENT_APP_ID"],
            publisher_tenant_id=tenant),
        store=JsonFileSubscriptionStore(
            Path(os.environ.get("MKT_STORE_PATH",
                                "data/marketplace/subscriptions.json"))),
        client=HttpMarketplaceClient(entra_token_provider(
            tenant, os.environ["MKT_CLIENT_ID"],
            os.environ["MKT_CLIENT_SECRET"])),
        verify_token=entra_webhook_verifier(tenant),
    )


def _sink():
    """OneLake sink when configured (events land in the tenant for the
    ingest step); local JSONL otherwise."""
    onelake_url = os.environ.get("AIVIA_EVENTS_ONELAKE_URL", "")
    if onelake_url:
        from src.orchestrator.events import OneLakeJsonlSink
        from src.orchestrator.kusto import az_cli_token_provider
        return OneLakeJsonlSink(
            onelake_url, az_cli_token_provider("https://storage.azure.com"))
    from src.orchestrator.events import JsonlEventSink
    return JsonlEventSink(Path(os.environ.get(
        "AIVIA_EVENTS_PATH", "data/events/turn_events.jsonl")))


def build() -> "object":
    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.orchestrator.agent import azure_chat_api
    from src.webapp.app import create_app
    return create_app(azure_chat_api(), _kusto_run(), _sink(),
                      _marketplace())


app = build() if os.environ.get("AIVIA_WEBAPP_EAGER", "1") != "0" else None
