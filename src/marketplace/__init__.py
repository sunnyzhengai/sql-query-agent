"""Microsoft Marketplace SaaS fulfillment — pure logic, no hosting.

The subscription lifecycle and webhook contract for the transactable offer
(ADR 0028), kept framework-free so the eventual Azure host (Functions/App
Service) is a thin adapter around tested code — the same pattern as
notebooks around src/steps/.
"""

from src.marketplace.fulfillment import (  # noqa: F401
    MARKETPLACE_RESOURCE_APP_ID,
    EventOutcome,
    InvalidTransition,
    Subscription,
    SubscriptionStatus,
    WebhookAction,
    WebhookEvent,
    activate,
    apply_webhook_event,
    validate_webhook_claims,
)
