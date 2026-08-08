"""Azure Functions (v2 model) entry points — deploy-time wrapper only.

Thin by design: every decision lives in handlers.py (tested offline) and
src/marketplace (tested offline). This file only adapts HTTP <-> Azure
Functions and wires production dependencies. It is NOT imported by tests
and requires the azure-functions package only at deploy time.

Deployment notes (ADR 0028 phase T2):
- App setting MARKETPLACE_APP_ID / PUBLISHER_TENANT_ID -> HostConfig.
- verify_token: validate against Entra JWKS
  (login.microsoftonline.com/{tenant}/discovery/v2.0/keys) using PyJWT +
  cryptography — deploy-time dependencies, deliberately not in the
  library's pyproject.
- SubscriptionStore: Azure Table Storage implementation (swap the
  in-memory dev store).
- Landing page GET serves the SSO page; Entra sign-in happens before
  resolve is called (multitenant app registration, User.Read only —
  certification policy 1000.3).
"""

from __future__ import annotations

import json
import os

import azure.functions as func  # deploy-time dependency

from marketplace_host.handlers import (
    HostConfig,
    handle_landing_activate,
    handle_landing_resolve,
    handle_webhook,
)
from marketplace_host.wiring import build_dependencies

app = func.FunctionApp()

_config = HostConfig(
    fulfillment_app_id=os.environ.get("MARKETPLACE_APP_ID", ""),
    publisher_tenant_id=os.environ.get("PUBLISHER_TENANT_ID", ""),
)
_store, _client, _verify_token = build_dependencies(_config)


def _response(status: int, body: dict) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body), status_code=status, mimetype="application/json"
    )


@app.route(route="webhook", methods=["POST"])
def webhook(req: func.HttpRequest) -> func.HttpResponse:
    status, body = handle_webhook(
        dict(req.headers), req.get_json(), _config, _store, _client, _verify_token
    )
    return _response(status, body)


@app.route(route="landing/resolve", methods=["POST"])
def landing_resolve(req: func.HttpRequest) -> func.HttpResponse:
    token = (req.get_json() or {}).get("token", "")
    status, body = handle_landing_resolve(token, _client, _store)
    return _response(status, body)


@app.route(route="landing/activate", methods=["POST"])
def landing_activate(req: func.HttpRequest) -> func.HttpResponse:
    subscription_id = (req.get_json() or {}).get("subscription_id", "")
    status, body = handle_landing_activate(subscription_id, _store, _client)
    return _response(status, body)
