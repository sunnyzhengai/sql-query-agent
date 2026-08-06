"""Tests for the marketplace subscription state machine + webhook contract."""

import pytest

from src.marketplace.fulfillment import (
    MARKETPLACE_RESOURCE_APP_ID,
    InvalidTransition,
    Subscription,
    SubscriptionStatus,
    WebhookAction,
    WebhookEvent,
    activate,
    apply_webhook_event,
    validate_webhook_claims,
)

APP = "11111111-1111-1111-1111-111111111111"
TENANT = "22222222-2222-2222-2222-222222222222"


def sub(status=SubscriptionStatus.PENDING_FULFILLMENT_START, **kw):
    defaults = dict(subscription_id="s-1", plan_id="pro-monthly", quantity=None)
    defaults.update(kw)
    return Subscription(status=status, **defaults)


def event(action, **kw):
    defaults = dict(subscription_id="s-1")
    defaults.update(kw)
    return WebhookEvent(action=action, **defaults)


class TestActivation:
    def test_activate_moves_pending_to_subscribed(self):
        assert activate(sub()).status == SubscriptionStatus.SUBSCRIBED

    def test_activate_twice_is_invalid(self):
        with pytest.raises(InvalidTransition):
            activate(sub(SubscriptionStatus.SUBSCRIBED))

    def test_auto_activation_subscribe_webhook(self):
        out = apply_webhook_event(sub(), event(WebhookAction.SUBSCRIBE))
        assert out.subscription.status == SubscriptionStatus.SUBSCRIBED
        assert not out.requires_operation_ack


class TestLifecycle:
    def test_full_lifecycle(self):
        s = activate(sub())
        s = apply_webhook_event(s, event(WebhookAction.RENEW)).subscription
        s = apply_webhook_event(s, event(WebhookAction.SUSPEND)).subscription
        assert s.status == SubscriptionStatus.SUSPENDED
        s = apply_webhook_event(s, event(WebhookAction.REINSTATE)).subscription
        assert s.status == SubscriptionStatus.SUBSCRIBED
        s = apply_webhook_event(s, event(WebhookAction.UNSUBSCRIBE)).subscription
        assert s.status == SubscriptionStatus.UNSUBSCRIBED

    def test_change_plan_updates_plan_and_needs_ack(self):
        out = apply_webhook_event(
            sub(SubscriptionStatus.SUBSCRIBED),
            event(WebhookAction.CHANGE_PLAN, plan_id="enterprise-annual"),
        )
        assert out.subscription.plan_id == "enterprise-annual"
        assert out.requires_operation_ack

    def test_change_quantity_updates_quantity_and_needs_ack(self):
        out = apply_webhook_event(
            sub(SubscriptionStatus.SUBSCRIBED, quantity=5),
            event(WebhookAction.CHANGE_QUANTITY, quantity=8),
        )
        assert out.subscription.quantity == 8
        assert out.requires_operation_ack

    def test_notify_only_events_need_no_ack(self):
        for action in (WebhookAction.RENEW, WebhookAction.SUSPEND, WebhookAction.UNSUBSCRIBE):
            out = apply_webhook_event(sub(SubscriptionStatus.SUBSCRIBED), event(action))
            assert not out.requires_operation_ack, action

    def test_unsubscribe_valid_from_every_live_status(self):
        for status in (
            SubscriptionStatus.PENDING_FULFILLMENT_START,
            SubscriptionStatus.SUBSCRIBED,
            SubscriptionStatus.SUSPENDED,
        ):
            out = apply_webhook_event(sub(status), event(WebhookAction.UNSUBSCRIBE))
            assert out.subscription.status == SubscriptionStatus.UNSUBSCRIBED


class TestInvalidTransitions:
    @pytest.mark.parametrize("status,action", [
        (SubscriptionStatus.PENDING_FULFILLMENT_START, WebhookAction.CHANGE_PLAN),
        (SubscriptionStatus.PENDING_FULFILLMENT_START, WebhookAction.SUSPEND),
        (SubscriptionStatus.SUSPENDED, WebhookAction.CHANGE_PLAN),
        (SubscriptionStatus.SUSPENDED, WebhookAction.CHANGE_QUANTITY),
        (SubscriptionStatus.SUSPENDED, WebhookAction.RENEW),
        (SubscriptionStatus.SUBSCRIBED, WebhookAction.REINSTATE),
        (SubscriptionStatus.UNSUBSCRIBED, WebhookAction.REINSTATE),
        (SubscriptionStatus.UNSUBSCRIBED, WebhookAction.SUBSCRIBE),
    ])
    def test_impossible_events_raise(self, status, action):
        with pytest.raises(InvalidTransition):
            apply_webhook_event(sub(status), event(action))

    def test_unsubscribed_is_terminal(self):
        for action in WebhookAction:
            with pytest.raises(InvalidTransition):
                apply_webhook_event(sub(SubscriptionStatus.UNSUBSCRIBED), event(action))


class TestPayloadParsing:
    def test_tolerant_parsing_ignores_unknown_fields(self):
        e = WebhookEvent.from_payload({
            "action": "ChangePlan",
            "subscriptionId": "s-9",
            "id": "op-1",
            "planId": "enterprise-annual",
            "futureField": {"microsoft": "extends this"},
        })
        assert e.action == WebhookAction.CHANGE_PLAN
        assert e.subscription_id == "s-9"
        assert e.operation_id == "op-1"
        assert e.quantity is None

    def test_unknown_action_raises(self):
        with pytest.raises(ValueError):
            WebhookEvent.from_payload({"action": "NotAThing", "subscriptionId": "s"})


class TestWebhookClaims:
    def good_claims(self):
        return {"aud": APP, "appid": MARKETPLACE_RESOURCE_APP_ID, "tid": TENANT}

    def test_valid_claims_pass(self):
        assert validate_webhook_claims(self.good_claims(), APP, TENANT) == []

    def test_azp_accepted_in_place_of_appid(self):
        claims = {"aud": APP, "azp": MARKETPLACE_RESOURCE_APP_ID, "tid": TENANT}
        assert validate_webhook_claims(claims, APP, TENANT) == []

    def test_each_bad_claim_is_reported(self):
        claims = {"aud": "wrong", "appid": "wrong", "tid": "wrong"}
        problems = validate_webhook_claims(claims, APP, TENANT)
        assert len(problems) == 3

    def test_missing_claims_fail(self):
        assert len(validate_webhook_claims({}, APP, TENANT)) == 3
