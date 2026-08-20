"""Pure HTTP handlers for the fulfillment webhook and landing page.

Everything injectable, nothing imported from Azure: the host
(function_app.py) supplies a token verifier, a subscription store, and
a marketplace API client. Handlers return (status_code, body_dict) so
tests assert on plain values.

Webhook contract obligations implemented here (see
internal/docs/MARKETPLACE_TRANSACTABLE_PLAN.md):
- always ACK 200 once authenticated (Microsoft retries 500x/8h on 5xx);
- verify the Authorization JWT (signature by the injected verifier,
  claims by src.marketplace.validate_webhook_claims);
- validate payloads via the operations API before acting;
- impossible transitions are ACKed and flagged for reconciliation,
  never applied blind.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from src.marketplace import (
    InvalidTransition,
    Subscription,
    SubscriptionStatus,
    WebhookEvent,
    activate,
    apply_webhook_event,
    validate_webhook_claims,
)


@dataclass
class HostConfig:
    fulfillment_app_id: str      # Entra app registered in the offer's tech config
    publisher_tenant_id: str


class SubscriptionStore(Protocol):
    def get(self, subscription_id: str) -> "dict | None": ...
    def save(self, record: dict) -> None: ...


class MarketplaceClient(Protocol):
    """Thin wrapper over the SaaS Fulfillment v2 REST API."""

    def resolve(self, purchase_token: str) -> dict: ...
    def activate(self, subscription_id: str, plan_id: str) -> None: ...
    def get_operation(self, subscription_id: str, operation_id: str) -> dict: ...
    def ack_operation(self, subscription_id: str, operation_id: str,
                      status: str) -> None: ...


TokenVerifier = Callable[[str], "dict | None"]
"""Bearer token -> decoded claims, or None if the signature/expiry is
invalid. Production: Entra JWKS validation (host concern); tests: fakes."""


def _subscription_from(record: dict) -> Subscription:
    return Subscription(
        subscription_id=record["subscription_id"],
        plan_id=record["plan_id"],
        quantity=record.get("quantity"),
        status=SubscriptionStatus(record["status"]),
    )


def _record_from(sub: Subscription) -> dict:
    return {
        "subscription_id": sub.subscription_id,
        "plan_id": sub.plan_id,
        "quantity": sub.quantity,
        "status": sub.status.value,
    }


def handle_webhook(
    headers: "dict[str, str]",
    payload: "dict[str, Any]",
    config: HostConfig,
    store: SubscriptionStore,
    client: MarketplaceClient,
    verify_token: TokenVerifier,
) -> "tuple[int, dict]":
    """The connection webhook. Auth failures are the ONLY non-200s."""
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    token = auth.removeprefix("Bearer ").strip()
    claims = verify_token(token) if token else None
    if claims is None:
        return 401, {"error": "invalid or missing bearer token"}
    problems = validate_webhook_claims(
        claims, config.fulfillment_app_id, config.publisher_tenant_id
    )
    if problems:
        return 401, {"error": "claim validation failed", "problems": problems}

    try:
        event = WebhookEvent.from_payload(payload)
    except (KeyError, ValueError) as e:
        # Unknown/extended action: ACK and log — Microsoft may extend the
        # schema; a 500 here would trigger 8 hours of retries.
        return 200, {"handled": False, "reason": f"unparseable event: {e}"}

    # Validate against the operations API before acting (docs requirement)
    if event.operation_id:
        op = client.get_operation(event.subscription_id, event.operation_id)
        if (op.get("action") or "").lower() != event.action.value.lower():
            return 200, {"handled": False,
                         "reason": "operation mismatch — reconcile"}

    record = store.get(event.subscription_id)
    if record is None:
        return 200, {"handled": False,
                     "reason": "unknown subscription — reconcile"}

    try:
        outcome = apply_webhook_event(_subscription_from(record), event)
    except InvalidTransition as e:
        return 200, {"handled": False, "reason": f"impossible transition: {e} — reconcile"}

    store.save(_record_from(outcome.subscription))
    if outcome.requires_operation_ack and event.operation_id:
        client.ack_operation(event.subscription_id, event.operation_id, "Success")
    return 200, {"handled": True,
                 "status": outcome.subscription.status.value,
                 "acked": outcome.requires_operation_ack}


def handle_landing_resolve(
    purchase_token: str,
    client: MarketplaceClient,
    store: SubscriptionStore,
) -> "tuple[int, dict]":
    """Landing page step 1: purchase token -> subscription details.

    The token arrives URL-decoded from the ?token= query parameter; the
    caller has already authenticated the BUYER via Entra SSO (host
    concern). Persists the subscription as PendingFulfillmentStart.
    """
    if not purchase_token:
        return 400, {"error": "missing purchase token"}
    resolved = client.resolve(purchase_token)
    sub = resolved.get("subscription") or {}
    record = {
        "subscription_id": resolved.get("id") or sub.get("id"),
        "plan_id": resolved.get("planId") or sub.get("planId"),
        "quantity": resolved.get("quantity") or sub.get("quantity"),
        "status": SubscriptionStatus.PENDING_FULFILLMENT_START.value,
        "offer_id": resolved.get("offerId"),
        "purchaser": (sub.get("purchaser") or {}).get("emailId", ""),
    }
    if not record["subscription_id"]:
        return 502, {"error": "resolve returned no subscription id"}
    store.save(record)
    return 200, {"subscription": record}


def handle_landing_activate(
    subscription_id: str,
    store: SubscriptionStore,
    client: MarketplaceClient,
) -> "tuple[int, dict]":
    """Landing page step 2: operator/buyer confirms -> activate.

    Billing starts when this succeeds — deliberately a separate explicit
    call (auto-activation stays OFF per ADR 0028 while onboarding is
    high-touch).
    """
    record = store.get(subscription_id)
    if record is None:
        return 404, {"error": "unknown subscription"}
    sub = activate(_subscription_from(record))  # raises on double-activate
    client.activate(sub.subscription_id, sub.plan_id)
    store.save(_record_from(sub) | {
        k: v for k, v in record.items()
        if k not in ("subscription_id", "plan_id", "quantity", "status")
    })
    return 200, {"subscription_id": sub.subscription_id,
                 "status": sub.status.value}
