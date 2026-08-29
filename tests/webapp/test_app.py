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

    def test_turn_event_carries_decision_shape_and_trace(self, tmp_path):
        client, events = chat_client(tmp_path, [
            [("search_catalog", {"phrase": "ed sepsis"}),
             ("get_facts", {"id": REF_A})],
            "It is calculated from encounters.",
        ])
        client.post("/api/chat", json={"message": "how is it calculated?"})
        row = json.loads(events.read_text().splitlines()[0])
        assert row["conversation_id"] and row["turn_index"] == 0
        assert row["decision"]["verified_by_tool"] is False
        assert row["decision"]["no_tools"] is False
        assert [t["tool"] for t in row["trace"]] == ["search_catalog",
                                                     "get_facts"]

    def test_feedback_joins_to_the_turn(self, tmp_path):
        client, events = chat_client(tmp_path, [
            [("search_catalog", {"phrase": "x"})], "A.",
        ])
        r = client.post("/api/chat", json={"message": "q"}).json()
        fb = client.post("/api/feedback", json={
            "conversation_id": r["conversation_id"],
            "turn_index": r["turn_index"],
            "verdict": "not_helpful", "comment": "wrong metric"})
        assert fb.status_code == 200
        rows = [json.loads(x) for x in events.read_text().splitlines()]
        assert rows[1]["verdict"] == "not_helpful"
        assert rows[1]["conversation_id"] == rows[0]["conversation_id"]
        assert rows[1]["turn_index"] == rows[0]["turn_index"]

    def test_feedback_verdict_validated(self, tmp_path):
        client, _ = chat_client(tmp_path, [])
        assert client.post("/api/feedback", json={
            "verdict": "meh"}).status_code == 400


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


class TestOneMindAskEndpoint:
    """ADR 0051: reads run immediately on /api/ask via the merged
    engine; the plan-protocol endpoints were deleted with their minds."""

    def test_ask_runs_the_engine_and_stamps_everything(self, tmp_path):
        from tests.orchestrator.test_turn_engine import scripted_engine
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        app = TestClient(create_app(scripted_engine([
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"text": "Two candidates are shown in R1."},
            {"verdict": {"answered": True,
                         "evidence_quote": "measures ED Sepsis "
                                           "Screening"}},
        ]), fake_kql, sink))
        r = app.post("/api/ask", json={"message": "what exists?"}).json()
        assert r["outputs"][0]["result"]["headline"].startswith("R1:")
        assert r["caption"].startswith("Two candidates")
        assert r["answered"] is True
        assert "one mind: 1 tool round(s)" in r["loop_status"]
        events = (tmp_path / "e.jsonl").read_text().splitlines()
        assert any('"answered": true' in e for e in events)

    def test_plan_endpoints_are_gone(self, tmp_path):
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        app = TestClient(create_app(lambda *a, **k: {}, fake_kql, sink))
        assert app.post("/api/plan", json={"message": "x"}).status_code == 404
        assert app.post("/api/execute", json={}).status_code == 404

    def test_ask_stream_emits_pending_output_and_done(self, tmp_path):
        """Walk W2: the SSE surface streams the ACTUAL trail — a
        pending pre-event at dispatch, the display dict at completion,
        stage events at the boundary, and a `done` payload identical
        in shape to /api/ask."""
        import json as _j

        from tests.orchestrator.test_turn_engine import scripted_engine
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        app = TestClient(create_app(scripted_engine([
            {"calls": [("search", {"phrase": "ed sepsis",
                                   "mode": "semantic"})]},
            {"text": "Two candidates are shown in R1."},
            {"verdict": {"answered": True,
                         "evidence_quote": "measures ED Sepsis "
                                           "Screening"}},
        ]), fake_kql, sink))
        with app.stream("POST", "/api/ask/stream",
                        json={"message": "what exists?"}) as r:
            assert r.status_code == 200
            body = "".join(chunk for chunk in r.iter_text())
        events = []
        for block in body.split("\n\n"):
            name, data = None, ""
            for line in block.split("\n"):
                if line.startswith("event: "):
                    name = line[7:].strip()
                elif line.startswith("data: "):
                    data += line[6:]
            if name:
                events.append((name, _j.loads(data)))
        names = [n for n, _ in events]
        assert "output" in names and "done" in names
        # pending pre-event precedes its completed display
        outputs = [d for n, d in events if n == "output"]
        assert outputs[0].get("pending") is True
        assert outputs[0]["component"]["op"] == "search"
        completed = [o for o in outputs if not o.get("pending")]
        assert completed and completed[0]["result"]["headline"].startswith(
            "R1:")
        # stage events cover the boundary
        assert {"stage": "gate"} in [d for n, d in events if n == "stage"]
        # done payload matches the /api/ask shape
        done = [d for n, d in events if n == "done"][0]
        assert done["caption"].startswith("Two candidates")
        assert done["answered"] is True
        # the turn event reached the sink exactly once
        lines = (tmp_path / "e.jsonl").read_text().splitlines()
        assert len(lines) == 1


class TestStoreResolution:
    """Board item 2026-08-28: the workbench store switch gets ONE
    obvious lever + a visible banner (env-var-only cost 20 min)."""

    def test_env_wins(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SQA_KUSTO_DB", "some_db")
        monkeypatch.chdir(tmp_path)
        from src.webapp.main import resolve_store
        _, db, source = resolve_store()
        assert db == "some_db" and "env" in source

    def test_org_config_search_block_is_read(self, monkeypatch,
                                             tmp_path):
        monkeypatch.delenv("SQA_KUSTO_DB", raising=False)
        monkeypatch.delenv("KUSTO_DB", raising=False)
        (tmp_path / "org_config.yaml").write_text(
            "search:\n  kusto_db: \"semantic_catalog_shapes\"\n")
        monkeypatch.chdir(tmp_path)
        from src.webapp.main import resolve_store
        _, db, source = resolve_store()
        assert db == "semantic_catalog_shapes"
        assert "org_config" in source

    def test_default_when_nothing_configured(self, monkeypatch,
                                             tmp_path):
        monkeypatch.delenv("SQA_KUSTO_DB", raising=False)
        monkeypatch.delenv("KUSTO_DB", raising=False)
        monkeypatch.chdir(tmp_path)
        from src.webapp.main import resolve_store
        _, db, source = resolve_store()
        assert db == "semantic_catalog" and "default" in source


class TestRunEndpoint:
    """ADR 0061 slice 1: /api/run — typed refusals, the read
    guarantee extended to runs, P5 stamps-only capture."""

    def _app(self, executor=None):
        from src.webapp.app import create_app
        events = []
        class Sink:
            def record(self, e): events.append(e)
        app = create_app(lambda *a, **k: {"content": "", "tool_calls": []},
                         _run_kql_step, Sink(),
                         run_executor=executor, run_cap=5,
                         run_source="fixture")
        from fastapi.testclient import TestClient
        return TestClient(app), events

    def test_unconfigured_refuses_typed(self):
        client, _ = self._app(None)
        r = client.post("/api/run", json={"step_id": "transform:x:y"})
        assert r.status_code == 503
        assert r.json()["reason_class"] == "unconfigured"

    def test_run_returns_rows_to_display_and_stamps_to_the_event(self):
        client, events = self._app(
            lambda sql: [{"PATIENT_ID": i} for i in range(9)])
        r = client.post("/api/run",
                        json={"step_id": "transform:r.X:Scores"})
        assert r.status_code == 200
        j = r.json()
        assert j["stamps"]["capped"] is True and len(j["rows"]) == 5
        assert "read-only" in j["sampling_label"]
        # P5: the captured event carries STAMPS — count/schema/
        # elapsed — and structurally no rows key at all
        ev = events[-1]
        blob = str(ev.trace) + str(ev.decision)
        assert "'rows'" not in blob and '"rows"' not in blob
        assert ev.decision["stamps"]["row_count"] == 5
        assert "[RUN]" in ev.question

    def test_non_select_fragment_refused_typed(self):
        client, _ = self._app(lambda sql: [])
        r = client.post("/api/run",
                        json={"step_id": "transform:r.X:Bad"})
        assert r.status_code == 422
        assert r.json()["reason_class"] == "not_select"

    def test_unbound_reason_carries_the_specific_cure(self):
        # RW-16: the wiring's distinguished reason rides the 503
        from fastapi.testclient import TestClient

        from src.webapp.app import create_app
        app = create_app(lambda *a, **k: {"content": "",
                                          "tool_calls": []},
                         _run_kql_step, type("S", (), {
                             "record": lambda self, e: None})(),
                         run_unbound="pyodbc is not installed — "
                                     "cure: pip install pyodbc")
        r = TestClient(app).post("/api/run",
                                 json={"step_id": "transform:x:y"})
        assert r.status_code == 503
        assert "pip install pyodbc" in r.json()["message"]

    def test_executor_failure_returns_typed_cure_not_500(self):
        # RW-16: a driver-stack blowup at execute time names the
        # brew/apt cure as a typed refusal, never a bare 500
        def broken(sql):
            raise Exception(
                "[unixODBC][Driver Manager]Can't open lib "
                "'ODBC Driver 18 for SQL Server'")
        client, _ = self._app(broken)
        r = client.post("/api/run",
                        json={"step_id": "transform:r.X:Scores"})
        assert r.status_code == 502
        j = r.json()
        assert j["reason_class"] == "driver_stack"
        assert "msodbcsql18" in j["message"]


def _run_kql_step(query, params):
    import json as _j

    from src.orchestrator.assemble import NODE_FACTS_QUERY
    if query == NODE_FACTS_QUERY:
        nid = params["p_node_id"]
        frag = ("UPDATE T SET X=1" if "Bad" in nid
                else "SELECT PATIENT_ID FROM DM_REGISTRY")
        return [{"node_id": nid, "name": nid.split(":")[-1],
                 "properties": _j.dumps({"sql_fragment": frag})}]
    return []
