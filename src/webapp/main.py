"""Production wiring for the chat web app.

Env (chat; legacy pre-rename names still read for one release):
  SQA_PRODUCT_NAME    display name shown in the UI (deployment brands itself)
  SQA_KUSTO_URI       Eventhouse query URI
  SQA_KUSTO_DB        database name
  OPENAI_BASE_URL / OPENAI_API_KEY / SQA_LLM_MODEL   (Azure OpenAI)
  SQA_EVENTS_PATH     TurnEvent JSONL path (default data/events/...)

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

from src.branding import legacy_env


def resolve_store() -> "tuple[str, str, str]":
    """(uri, db, source) — the workbench's store, ONE obvious lever
    (board item 2026-08-28: the env-var-only switch cost Sunny 20
    minutes; the org_config line she reached for now works here
    too). Precedence: env override > org_config search block >
    default. The startup banner prints the winner, so the store in
    use is always visible."""
    from src.branding import legacy_env
    uri = legacy_env(
        "KUSTO_URI",
        "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com")
    env_db = legacy_env("KUSTO_DB", "")
    if env_db:
        return uri, env_db, "env KUSTO_DB"
    cfg = Path("org_config.yaml")
    if cfg.exists():
        try:
            import yaml
            search = (yaml.safe_load(cfg.read_text())
                      or {}).get("search") or {}
            cfg_uri = str(search.get("kusto_uri") or "").strip()
            cfg_db = str(search.get("kusto_db") or "").strip()
            if cfg_db:
                return cfg_uri or uri, cfg_db, "org_config.yaml search:"
        except Exception as e:              # noqa: BLE001 — visible
            print(f"[!] org_config.yaml unreadable ({e}) — "
                  "falling through to the default store")
    return uri, "semantic_catalog", "built-in default"


def _kusto_run():
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider
    uri, db, source = resolve_store()
    print(f"[workbench] store: {db} @ {uri} (from {source}) — "
          "override with KUSTO_DB or org_config.yaml search.kusto_db")
    return KustoClient(uri, db, az_cli_token_provider(uri)).run


def _run_executor():
    """ADR 0061 slice 1: the run layer's source binding from
    org_config.yaml `run:` — returns (executor, cap, source_label,
    unbound_reason). Unbound/undriverable states refuse typed AND
    name their cure (RW-16, field find 2026-08-29: pyodbc + unixodbc
    + msodbcsql18 all absent and the bind failed silently — every
    state distinguishes itself per the error-contract law)."""
    unbound = ("the run layer is unbound: add a run: block (server, "
               "database) to org_config.yaml — the runbook line is in "
               "internal/docs/HANDOFF_0055_BUILD.md")
    cfg = Path("org_config.yaml")
    if not cfg.exists():
        return None, 200, "", unbound
    try:
        import yaml
        block = (yaml.safe_load(cfg.read_text()) or {}).get("run") or {}
    except Exception as e:                  # noqa: BLE001 — visible
        print(f"[run layer] org_config unreadable ({e}) — unbound")
        return None, 200, "", (
            f"org_config.yaml is unreadable ({type(e).__name__}) — "
            "fix the YAML, then add the run: block")
    server = str(block.get("server") or "").strip()
    database = str(block.get("database") or "").strip()
    cap = int(block.get("row_cap") or 200)
    if not (server and database):
        return None, cap, "", unbound
    try:
        from src.config import SqlServerConfig
        from src.extractor.connection import AzureDirectConnection
        from src.orchestrator.kusto import az_cli_token_provider
        conn = AzureDirectConnection(
            SqlServerConfig(host=server, database=database,
                            source_type="azure_direct"),
            lambda: az_cli_token_provider(
                "https://database.windows.net/")())
        print(f"[run layer] bound read-only to {database} "
              "(confirm-each-run; TOP cap enforced)")
        return conn.execute_query, cap, database.split("-")[0], ""
    except Exception as e:                  # noqa: BLE001 — typed
        from src.run_layer import classify_run_error
        reason_class, message = classify_run_error(e)
        print(f"[run layer] binding failed ({reason_class}) — runs "
              f"will refuse typed: {message}")
        return None, cap, "", message


def _marketplace():
    keys = ("MKT_FULFILLMENT_APP_ID", "MKT_PUBLISHER_TENANT_ID",
            "MKT_CLIENT_ID", "MKT_CLIENT_SECRET")
    if not all(os.environ.get(k) for k in keys):
        return None
    from marketplace_host.handlers import HostConfig
    from marketplace_host.wiring import (
        HttpMarketplaceClient,
        JsonFileSubscriptionStore,
        entra_token_provider,
        entra_webhook_verifier,
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
    onelake_url = legacy_env("EVENTS_ONELAKE_URL", "")
    if onelake_url:
        from src.orchestrator.events import OneLakeJsonlSink
        from src.orchestrator.kusto import az_cli_token_provider
        return OneLakeJsonlSink(
            onelake_url, az_cli_token_provider("https://storage.azure.com"))
    from src.orchestrator.events import JsonlEventSink
    return JsonlEventSink(Path(os.environ.get(
        "SQA_EVENTS_PATH", "data/events/turn_events.jsonl")))


def build() -> "object":
    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.orchestrator.agent import azure_chat_api
    from src.webapp.app import create_app
    executor, cap, source, unbound = _run_executor()
    # planner=True: ADR 0060 sameness class rides the parse→plan
    # path in production (ordered 2026-08-29 after codeset FAIL #3);
    # every other class stays on the engine
    return create_app(azure_chat_api(), _kusto_run(), _sink(),
                      _marketplace(), run_executor=executor,
                      run_cap=cap, run_source=source,
                      run_unbound=unbound, planner=True)


app = build() if legacy_env("WEBAPP_EAGER", "1") != "0" else None
