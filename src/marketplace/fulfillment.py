"""Marketplace SaaS subscription state machine + webhook contract.

Encodes the SaaS Fulfillment v2 lifecycle (api-version 2018-08-31):

    PendingFulfillmentStart -> Subscribed <-> Suspended -> Unsubscribed

and the connection-webhook semantics: which events change state, which
require an operation-level accept/reject within 10 seconds, and which are
notify-only. Everything here is pure — the HTTP host resolves tokens,
verifies JWTs cryptographically, and persists subscriptions; this module
decides what is *correct*.

References (verified 2026-08-06, docs/internal/MARKETPLACE_TRANSACTABLE_PLAN.md):
partner-center/marketplace-offers/pc-saas-fulfillment-subscription-api,
pc-saas-fulfillment-webhook.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

# Marketplace SaaS API resource id — the fixed first-party GUID used as the
# token scope (`{id}/.default`) and expected in webhook token claims.
MARKETPLACE_RESOURCE_APP_ID = "20e940b3-4c77-4b0b-9a53-9e16a1b010a7"


class SubscriptionStatus(str, Enum):
    PENDING_FULFILLMENT_START = "PendingFulfillmentStart"
    SUBSCRIBED = "Subscribed"
    SUSPENDED = "Suspended"
    UNSUBSCRIBED = "Unsubscribed"


class WebhookAction(str, Enum):
    SUBSCRIBE = "Subscribe"          # auto-activated plans only
    CHANGE_PLAN = "ChangePlan"
    CHANGE_QUANTITY = "ChangeQuantity"
    RENEW = "Renew"
    SUSPEND = "Suspend"
    REINSTATE = "Reinstate"
    UNSUBSCRIBE = "Unsubscribe"


# Actions the publisher must accept/reject by PATCHing the operation within
# 10 seconds of the ACK (silence auto-accepts). Everything else is
# notify-only: ACK with HTTP 200 and update local state.
ACTIONS_REQUIRING_OPERATION_ACK = frozenset(
    {WebhookAction.CHANGE_PLAN, WebhookAction.CHANGE_QUANTITY}
)

# (current status, action) -> next status. Anything absent is invalid and
# means our mirror is out of sync with Microsoft's — surface, never guess.
_TRANSITIONS: "dict[tuple[SubscriptionStatus, WebhookAction], SubscriptionStatus]" = {
    (SubscriptionStatus.PENDING_FULFILLMENT_START, WebhookAction.SUBSCRIBE):
        SubscriptionStatus.SUBSCRIBED,
    (SubscriptionStatus.SUBSCRIBED, WebhookAction.CHANGE_PLAN):
        SubscriptionStatus.SUBSCRIBED,
    (SubscriptionStatus.SUBSCRIBED, WebhookAction.CHANGE_QUANTITY):
        SubscriptionStatus.SUBSCRIBED,
    (SubscriptionStatus.SUBSCRIBED, WebhookAction.RENEW):
        SubscriptionStatus.SUBSCRIBED,
    (SubscriptionStatus.SUBSCRIBED, WebhookAction.SUSPEND):
        SubscriptionStatus.SUSPENDED,
    (SubscriptionStatus.SUSPENDED, WebhookAction.REINSTATE):
        SubscriptionStatus.SUBSCRIBED,
    (SubscriptionStatus.SUBSCRIBED, WebhookAction.UNSUBSCRIBE):
        SubscriptionStatus.UNSUBSCRIBED,
    (SubscriptionStatus.SUSPENDED, WebhookAction.UNSUBSCRIBE):
        SubscriptionStatus.UNSUBSCRIBED,
    (SubscriptionStatus.PENDING_FULFILLMENT_START, WebhookAction.UNSUBSCRIBE):
        SubscriptionStatus.UNSUBSCRIBED,
}


class InvalidTransition(Exception):
    def __init__(self, status: SubscriptionStatus, action: WebhookAction) -> None:
        super().__init__(f"{action.value} is not valid while {status.value}")
        self.status = status
        self.action = action


@dataclass(frozen=True)
class Subscription:
    """Our mirror of a marketplace subscription (persisted by the host)."""

    subscription_id: str
    plan_id: str
    quantity: "int | None" = None  # None for flat-rate (non-per-seat) plans
    status: SubscriptionStatus = SubscriptionStatus.PENDING_FULFILLMENT_START


@dataclass(frozen=True)
class WebhookEvent:
    """One connection-webhook POST, tolerantly parsed.

    Microsoft reserves the right to extend the payload; unknown fields are
    ignored and optional ones default — strict deserialization is a
    documented anti-pattern.
    """

    action: WebhookAction
    subscription_id: str
    operation_id: str = ""
    plan_id: str = ""
    quantity: "int | None" = None

    @classmethod
    def from_payload(cls, payload: "dict") -> "WebhookEvent":
        return cls(
            action=WebhookAction(payload["action"]),
            subscription_id=payload.get("subscriptionId", ""),
            operation_id=payload.get("id", ""),
            plan_id=payload.get("planId", ""),
            quantity=payload.get("quantity"),
        )


@dataclass(frozen=True)
class EventOutcome:
    """What the host must do about one webhook event."""

    subscription: Subscription           # updated mirror to persist
    requires_operation_ack: bool         # PATCH the operation within 10 s
    verify_via_operations_api: bool = True  # always confirm before acting


def activate(subscription: Subscription) -> Subscription:
    """Publisher-side activation after the landing-page resolve handshake.

    Billing starts when the Activate call succeeds — only valid from
    PendingFulfillmentStart.
    """
    if subscription.status != SubscriptionStatus.PENDING_FULFILLMENT_START:
        raise InvalidTransition(subscription.status, WebhookAction.SUBSCRIBE)
    return replace(subscription, status=SubscriptionStatus.SUBSCRIBED)


def apply_webhook_event(subscription: Subscription, event: WebhookEvent) -> EventOutcome:
    """Apply one webhook event to our mirror of the subscription.

    Raises InvalidTransition when the event is impossible from the current
    status — the host should still ACK 200 (Microsoft retries 500 times
    over 8 hours) but must reconcile via Get Subscription, not apply it.
    """
    key = (subscription.status, event.action)
    if key not in _TRANSITIONS:
        raise InvalidTransition(subscription.status, event.action)
    updated = replace(subscription, status=_TRANSITIONS[key])
    if event.action == WebhookAction.CHANGE_PLAN and event.plan_id:
        updated = replace(updated, plan_id=event.plan_id)
    if event.action == WebhookAction.CHANGE_QUANTITY and event.quantity is not None:
        updated = replace(updated, quantity=event.quantity)
    return EventOutcome(
        subscription=updated,
        requires_operation_ack=event.action in ACTIONS_REQUIRING_OPERATION_ACK,
    )


def validate_webhook_claims(
    claims: "dict",
    expected_app_id: str,
    expected_tenant_id: str,
) -> "list[str]":
    """Check the decoded webhook JWT claims. Returns problems; [] is valid.

    The host verifies the signature cryptographically; this validates the
    contract: aud is OUR fulfillment app, the caller is the marketplace
    first-party app, and the tenant matches. Microsoft has announced
    enforcement of Authorization-header validation for ISV webhooks.
    """
    problems = []
    if claims.get("aud") != expected_app_id:
        problems.append(f"aud {claims.get('aud')!r} != fulfillment app {expected_app_id!r}")
    caller = claims.get("appid") or claims.get("azp")
    if caller != MARKETPLACE_RESOURCE_APP_ID:
        problems.append(f"appid/azp {caller!r} is not the marketplace app")
    if claims.get("tid") != expected_tenant_id:
        problems.append(f"tid {claims.get('tid')!r} != publisher tenant {expected_tenant_id!r}")
    return problems
