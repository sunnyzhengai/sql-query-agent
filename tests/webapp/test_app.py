"""Tests for the web surface: chat over the agent, fulfillment routes,
identity, and conversation state — all offline via TestClient."""

import json

from fastapi.testclient import TestClient

from marketplace_host.handlers import HostConfig
from src.orchestrator.events import JsonlEventSink
from src.webapp.app import MarketplaceDeps, create_app
from tests.orchestrator.test_agent import scripted_api
from tests.orchestrator.test_tools import REF_A, STEP_1, fake_kql


def chat_client(tmp_path, script):
    sink = JsonlEventSink(tmp_path / "events.jsonl")
    app = create_app(scripted_api(script), fake_kql, sink)
    return TestClient(app), tmp_path / "events.jsonl"


class TestChat:
    def test_page_and_health(self, tmp_path):
        client, _ = chat_client(tmp_path, [])
        assert client.get("/healthz").json() == {"ok": True}
        page = client.get("/")
        assert page.status_code == 200
        assert "certified metrics" in page.text

    def test_chat_turn_returns_answer_and_stamped_basis(self, tmp_path):
        client, events = chat_client(tmp_path, [
            [("search_catalog", {"phrase": "ed sepsis"})],
            "ED Sepsis Screening tracks sepsis in the ED.",
        ])
        r = client.post("/api/chat",
                        json={"message": "how is ed sepsis calculated?"})
        assert r.status_code == 200
        body = r.json()
        assert body["answer"].startswith("ED Sepsis Screening")
        assert "search('ed sepsis') -> 2 candidates shown" in body["basis"]
        assert body["conversation_id"]
        row = json.loads(events.read_text().splitlines()[0])
        assert row["user_id"] == "local-dev"          # no Easy Auth header
        assert row["tools_used"] == ["search_catalog"]

    def test_conversation_state_carries_across_requests(self, tmp_path):
        client, _ = chat_client(tmp_path, [
            [("search_catalog", {"phrase": "ed sepsis"})], "Answer one.",
            [("get_facts", {"id": STEP_1})], "Here is the SQL.",
        ])
        r1 = client.post("/api/chat", json={"message": "q1"}).json()
        r2 = client.post("/api/chat", json={
            "message": "show me its sql",
            "conversation_id": r1["conversation_id"]}).json()
        # STEP_1 was surfaced in turn 1 — permitted in turn 2 because
        # the Session persisted under the conversation id
        assert f"facts[{STEP_1}]" in r2["basis"]

    def test_easy_auth_identity_reaches_the_flywheel(self, tmp_path):
        client, events = chat_client(tmp_path, [
            [("search_catalog", {"phrase": "x"})], "A.",
        ])
        client.post("/api/chat", json={"message": "q"},
                    headers={"X-MS-CLIENT-PRINCIPAL-NAME": "sunny@aivia"})
        row = json.loads(events.read_text().splitlines()[0])
        assert row["user_id"] == "sunny@aivia"

    def test_users_do_not_share_conversations(self, tmp_path):
        client, _ = chat_client(tmp_path, [
            [("search_catalog", {"phrase": "x"})], "A.",
            [("get_facts", {"id": REF_A})], "B.",
        ])
        r1 = client.post("/api/chat", json={"message": "q"},
                         headers={"X-MS-CLIENT-PRINCIPAL-NAME": "alice"}).json()
        # same conversation id, DIFFERENT user: fresh session — the id
        # surfaced for alice must not be permitted for bob
        r2 = client.post("/api/chat", json={
            "message": "read it", "conversation_id": r1["conversation_id"]},
            headers={"X-MS-CLIENT-PRINCIPAL-NAME": "bob"}).json()
        assert "error" in r2["basis"]     # get_facts refused: not surfaced

    def test_empty_message_rejected(self, tmp_path):
        client, _ = chat_client(tmp_path, [])
        assert client.post("/api/chat", json={"message": " "}).status_code == 400


class FakeStore:
    def __init__(self):
        self.rows = {}

    def get(self, sid):
        return self.rows.get(sid)

    def save(self, record):
        self.rows[record["subscription_id"]] = dict(record)


class FakeMktClient:
    def resolve(self, token):
        assert token == "tok123"
        return {"id": "sub-1", "planId": "annual",
                "subscription": {"purchaser": {"emailId": "buyer@x.com"}}}

    def activate(self, sid, plan):
        self.activated = (sid, plan)

    def get_operation(self, sid, oid):
        return {"action": "Unsubscribe"}

    def ack_operation(self, sid, oid, status):
        self.acked = (sid, oid, status)


def mkt_app(tmp_path, verify=lambda t: None):
    deps = MarketplaceDeps(
        config=HostConfig(fulfillment_app_id="app-1",
                          publisher_tenant_id="tenant-1"),
        store=FakeStore(), client=FakeMktClient(), verify_token=verify)
    sink = JsonlEventSink(tmp_path / "e.jsonl")
    return TestClient(create_app(scripted_api([]), fake_kql, sink, deps)), deps


class TestMarketplace:
    def test_not_configured_is_503(self, tmp_path):
        client, _ = chat_client(tmp_path, [])
        assert client.get("/landing?token=t").status_code == 503
        assert client.post("/api/marketplace/webhook", json={}).status_code == 503

    def test_landing_resolves_and_renders(self, tmp_path):
        client, deps = mkt_app(tmp_path)
        r = client.get("/landing?token=tok123")
        assert r.status_code == 200
        assert "annual" in r.text and "sub-1" in r.text
        assert deps.store.rows["sub-1"]["status"] == "PendingFulfillmentStart"

    def test_activate_flow(self, tmp_path):
        client, deps = mkt_app(tmp_path)
        client.get("/landing?token=tok123")
        r = client.post("/api/marketplace/activate",
                        json={"subscription_id": "sub-1"})
        assert r.status_code == 200
        assert r.json()["status"] == "Subscribed"
        assert deps.client.activated == ("sub-1", "annual")

    def test_webhook_rejects_bad_auth(self, tmp_path):
        client, _ = mkt_app(tmp_path, verify=lambda t: None)
        r = client.post("/api/marketplace/webhook", json={},
                        headers={"Authorization": "Bearer bad"})
        assert r.status_code == 401

    def test_webhook_unsubscribe_end_to_end(self, tmp_path):
        from src.marketplace.fulfillment import MARKETPLACE_RESOURCE_APP_ID
        claims = {"aud": "app-1", "tid": "tenant-1",
                  "appid": MARKETPLACE_RESOURCE_APP_ID}
        client, deps = mkt_app(tmp_path, verify=lambda t: claims)
        client.get("/landing?token=tok123")
        client.post("/api/marketplace/activate",
                    json={"subscription_id": "sub-1"})
        r = client.post("/api/marketplace/webhook", json={
            "id": "op-9", "subscriptionId": "sub-1",
            "action": "Unsubscribe", "planId": "annual",
        }, headers={"Authorization": "Bearer good"})
        assert r.status_code == 200
        assert r.json()["handled"] is True
        assert deps.store.rows["sub-1"]["status"] == "Unsubscribed"


class TestJsonFileStore:
    def test_round_trip_and_durability(self, tmp_path):
        from marketplace_host.wiring import JsonFileSubscriptionStore
        store = JsonFileSubscriptionStore(tmp_path / "subs.json")
        store.save({"subscription_id": "s1", "plan_id": "monthly",
                    "quantity": None, "status": "Subscribed"})
        again = JsonFileSubscriptionStore(tmp_path / "subs.json")
        assert again.get("s1")["status"] == "Subscribed"
        assert again.get("ghost") is None
