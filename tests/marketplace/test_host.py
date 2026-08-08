"""Tests for the fulfillment host handlers (transport layer, no Azure)."""

from marketplace_host.handlers import (
    HostConfig,
    handle_landing_activate,
    handle_landing_resolve,
    handle_webhook,
)
from marketplace_host.wiring import InMemoryStore
from src.marketplace import MARKETPLACE_RESOURCE_APP_ID

APP = "app-1111"
TENANT = "tenant-2222"
CONFIG = HostConfig(fulfillment_app_id=APP, publisher_tenant_id=TENANT)

GOOD_CLAIMS = {"aud": APP, "appid": MARKETPLACE_RESOURCE_APP_ID, "tid": TENANT}


def verifier(expected_token="tok", claims=GOOD_CLAIMS):
    return lambda tok: dict(claims) if tok == expected_token else None


class FakeClient:
    def __init__(self, operations=None, resolved=None):
        self.operations = operations or {}
        self.resolved = resolved or {}
        self.activated = []
        self.acks = []

    def resolve(self, purchase_token):
        return self.resolved

    def activate(self, subscription_id, plan_id):
        self.activated.append((subscription_id, plan_id))

    def get_operation(self, subscription_id, operation_id):
        return self.operations.get(operation_id, {})

    def ack_operation(self, subscription_id, operation_id, status):
        self.acks.append((operation_id, status))


def seeded_store(status="Subscribed", plan="pro-monthly"):
    store = InMemoryStore()
    store.save({"subscription_id": "s-1", "plan_id": plan,
                "quantity": None, "status": status})
    return store


def webhook(payload, store, client, headers=None, verify=None):
    return handle_webhook(
        headers if headers is not None else {"Authorization": "Bearer tok"},
        payload, CONFIG, store, client, verify or verifier(),
    )


class TestWebhookAuth:
    def test_missing_token_is_401(self):
        status, body = webhook({}, seeded_store(), FakeClient(), headers={})
        assert status == 401

    def test_bad_signature_is_401(self):
        status, _ = webhook({}, seeded_store(), FakeClient(),
                            headers={"Authorization": "Bearer wrong"})
        assert status == 401

    def test_wrong_claims_are_401_with_problems(self):
        bad = verifier(claims={"aud": "other", "appid": "x", "tid": "y"})
        status, body = webhook({"action": "Renew", "subscriptionId": "s-1"},
                               seeded_store(), FakeClient(), verify=bad)
        assert status == 401 and len(body["problems"]) == 3


class TestWebhookEvents:
    def test_change_plan_applies_and_acks(self):
        store = seeded_store()
        client = FakeClient(operations={"op-1": {"action": "ChangePlan"}})
        status, body = webhook(
            {"action": "ChangePlan", "subscriptionId": "s-1",
             "id": "op-1", "planId": "enterprise-annual"},
            store, client,
        )
        assert (status, body["handled"], body["acked"]) == (200, True, True)
        assert store.get("s-1")["plan_id"] == "enterprise-annual"
        assert client.acks == [("op-1", "Success")]

    def test_suspend_applies_without_ack(self):
        store = seeded_store()
        status, body = webhook(
            {"action": "Suspend", "subscriptionId": "s-1"}, store, FakeClient()
        )
        assert (status, body["acked"]) == (200, False)
        assert store.get("s-1")["status"] == "Suspended"

    def test_operation_mismatch_acked_but_not_applied(self):
        store = seeded_store()
        client = FakeClient(operations={"op-1": {"action": "Unsubscribe"}})
        status, body = webhook(
            {"action": "ChangePlan", "subscriptionId": "s-1",
             "id": "op-1", "planId": "x"},
            store, client,
        )
        assert (status, body["handled"]) == (200, False)
        assert store.get("s-1")["plan_id"] == "pro-monthly"  # unchanged

    def test_impossible_transition_acked_flagged_not_applied(self):
        store = seeded_store(status="Unsubscribed")
        status, body = webhook(
            {"action": "Renew", "subscriptionId": "s-1"}, store, FakeClient()
        )
        assert status == 200 and body["handled"] is False
        assert "reconcile" in body["reason"]

    def test_unknown_subscription_acked_flagged(self):
        status, body = webhook(
            {"action": "Renew", "subscriptionId": "ghost"},
            InMemoryStore(), FakeClient(),
        )
        assert status == 200 and body["handled"] is False

    def test_future_schema_action_acked_not_500(self):
        status, body = webhook(
            {"action": "SomeFutureThing", "subscriptionId": "s-1"},
            seeded_store(), FakeClient(),
        )
        assert status == 200 and body["handled"] is False


class TestLanding:
    def test_resolve_persists_pending_subscription(self):
        store = InMemoryStore()
        client = FakeClient(resolved={
            "id": "s-9", "planId": "pro-monthly", "quantity": None,
            "offerId": "aivia-sql-agent",
            "subscription": {"purchaser": {"emailId": "buyer@customer.org"}},
        })
        status, body = handle_landing_resolve("purchase-tok", client, store)
        assert status == 200
        rec = store.get("s-9")
        assert rec["status"] == "PendingFulfillmentStart"
        assert rec["purchaser"] == "buyer@customer.org"

    def test_resolve_without_token_is_400(self):
        status, _ = handle_landing_resolve("", FakeClient(), InMemoryStore())
        assert status == 400

    def test_activate_calls_api_and_flips_status(self):
        store = seeded_store(status="PendingFulfillmentStart")
        client = FakeClient()
        status, body = handle_landing_activate("s-1", store, client)
        assert status == 200 and body["status"] == "Subscribed"
        assert client.activated == [("s-1", "pro-monthly")]

    def test_activate_unknown_subscription_404(self):
        status, _ = handle_landing_activate("ghost", InMemoryStore(), FakeClient())
        assert status == 404
