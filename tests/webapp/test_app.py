"""Tests for the web surface: chat over the agent, fulfillment routes,
identity, and conversation state — all offline via TestClient."""

import json

from fastapi.testclient import TestClient

from marketplace_host.handlers import HostConfig
from src.orchestrator.events import JsonlEventSink
from src.webapp.app import MarketplaceDeps, create_app
from tests.orchestrator.test_agent import scripted_api
from tests.orchestrator.test_tools import REF_A, STEP_1, STEP_2, fake_kql


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


class TestPlannerSamenessClass:
    """ADR 0060 sameness class LIVE (ordered 2026-08-29, codeset
    FAIL #3 — the route was a coin flip): a sameness parse renders
    for confirmation and the click executes the SAME deterministic
    plan every run. Opt-in at create_app (planner=True in
    production wiring); every other class stays on the engine."""

    def _parse_api(self, engine_answer="The step is shown."):
        def api(messages, tools, tool_choice=None):
            forced = (tool_choice or {}).get("function", {}).get("name")
            if forced == "file_parse":
                return {"content": "", "tool_calls": [{
                    "id": "p1", "function": {
                        "name": "file_parse",
                        "arguments": json.dumps({
                            "entities": ["Scores"],
                            "primitives": ["same_or_different"]})}}]}
            if forced == "file_verdict":
                return {"content": "", "tool_calls": [{
                    "id": "v1", "function": {
                        "name": "file_verdict",
                        "arguments": json.dumps({
                            "answered": False,
                            "missing_op": ""})}}]}
            return {"content": engine_answer, "tool_calls": []}
        return api

    def _client(self, planner=True):
        import tempfile
        from pathlib import Path

        from src.orchestrator.events import JsonlEventSink
        sink = JsonlEventSink(
            Path(tempfile.mkdtemp()) / "events.jsonl")
        app = create_app(self._parse_api(), fake_kql, sink,
                         planner=planner)
        return TestClient(app)

    def test_sameness_question_renders_the_parse_not_an_answer(self):
        client = self._client()
        r = client.post("/api/ask", json={
            "message": "are the two Scores steps the same?"})
        assert r.status_code == 200
        j = r.json()
        assert "same_or_different over {Scores}" in j["parse_confirm"]
        assert "outputs" not in j            # nothing executed yet

    def test_confirm_click_runs_the_deterministic_plan(self):
        client = self._client()
        r1 = client.post("/api/ask", json={
            "message": "are the two Scores steps the same?"})
        conv = r1.json()["conversation_id"]
        r2 = client.post("/api/parse/confirm",
                         json={"conversation_id": conv})
        assert r2.status_code == 200
        j = r2.json()
        assert j["planned"] is True
        ops = [o["component"]["op"] for o in j["outputs"]]
        assert ops == ["retrieve", "compare"]
        assert j["conclusion"]["kind"] == "compare"
        assert j["answered"] is True
        assert "planner:" in j["loop_status"]

    def test_confirm_without_pending_parse_is_409(self):
        client = self._client()
        r = client.post("/api/parse/confirm",
                        json={"conversation_id": "nope"})
        assert r.status_code == 409
        assert r.json()["reason_class"] == "no_pending_parse"

    def test_planner_false_body_flag_skips_to_the_engine(self):
        client = self._client()
        r = client.post("/api/ask", json={
            "message": "are the two Scores steps the same?",
            "planner": False})
        j = r.json()
        assert "parse_confirm" not in j
        assert j["caption"] == "The step is shown."

    def test_planner_off_by_default_engine_untouched(self):
        client = self._client(planner=False)
        r = client.post("/api/ask", json={
            "message": "are the two Scores steps the same?"})
        assert "parse_confirm" not in r.json()


class TestIterationCard:
    """ADR 0062 conversion (hold-lift order 08-29, first task): the
    parse card becomes the ITERATION card — SHOW grounded matches
    before the ask, prune as a decision item, developer door on
    every round (a standing option, never a last resort)."""

    def _client(self, contact=""):
        import tempfile
        from pathlib import Path

        from src.orchestrator.events import JsonlEventSink
        path = Path(tempfile.mkdtemp()) / "events.jsonl"
        sink = JsonlEventSink(path)
        maker = TestPlannerSamenessClass()
        app = create_app(maker._parse_api(), fake_kql, sink,
                         planner=True, escalation_contact=contact)
        return TestClient(app), path

    def test_card_shows_grounded_matches_before_the_ask(self):
        client, _ = self._client()
        r = client.post("/api/ask", json={
            "message": "are the two Scores steps the same?"})
        j = r.json()
        [entry] = j["show"]
        assert entry["entity"] == "Scores"
        ids = {m["id"] for m in entry["matches"]}
        assert ids == {STEP_1, STEP_2}   # collisions anchor wholly
        assert "outputs" not in j        # still nothing executed

    def test_pruning_a_match_excludes_it_from_the_plan(self):
        client, _ = self._client()
        r1 = client.post("/api/ask", json={
            "message": "are the two Scores steps the same?"})
        conv = r1.json()["conversation_id"]
        # prune BOTH matches → the sameness plan cannot compose →
        # typed refusal, never a guessed route
        r2 = client.post("/api/parse/confirm", json={
            "conversation_id": conv,
            "exclude_ids": [STEP_1, STEP_2]})
        assert r2.status_code == 422
        assert r2.json()["reason_class"] == "parse_refusal"

    def test_developer_door_captures_the_demand(self):
        client, events = self._client(contact="dev@example.org")
        r1 = client.post("/api/ask", json={
            "message": "are the two Scores steps the same?"})
        conv = r1.json()["conversation_id"]
        r2 = client.post("/api/escalate",
                         json={"conversation_id": conv,
                               "note": "I meant the sepsis scores"})
        assert r2.status_code == 200
        j = r2.json()
        assert j["captured"] is True
        assert "none of the shown understanding" in j["summary"]
        assert "I meant the sepsis scores" in j["summary"]
        assert j["mailto"].startswith("mailto:dev@example.org?")
        row = json.loads(events.read_text().splitlines()[-1])
        assert row["question"].startswith("[ESCALATE]")
        assert row["answered"] is False
        assert row["decision"]["made_by"] == "user_escalation"
        # the pending attempt ends at the door
        r3 = client.post("/api/parse/confirm",
                         json={"conversation_id": conv})
        assert r3.status_code == 409

    def test_door_without_contact_still_captures(self):
        client, _ = self._client(contact="")
        r = client.post("/api/escalate",
                        json={"conversation_id": "c1",
                              "question": "anything at all"})
        j = r.json()
        assert j["captured"] is True and j["mailto"] == ""


class TestCardEverywhere:
    """RW-BATCH-5 item 2 (0062 proper): EVERY question grounding at
    least one entity gets the understanding card; no relation word →
    the DEFAULT MAP reading; silent engine fallback survives only
    for zero-grounded questions. Plus RW-18: parallel grounding,
    streamed skeleton, measured latency."""

    def _api(self, entities, primitives):
        def api(messages, tools, tool_choice=None):
            forced = (tool_choice or {}).get("function", {}).get("name")
            if forced == "file_parse":
                return {"content": "", "tool_calls": [{
                    "id": "p1", "function": {
                        "name": "file_parse",
                        "arguments": json.dumps({
                            "entities": entities,
                            "primitives": primitives})}}]}
            if forced == "file_verdict":
                return {"content": "", "tool_calls": [{
                    "id": "v1", "function": {
                        "name": "file_verdict",
                        "arguments": json.dumps({
                            "answered": False, "missing_op": ""})}}]}
            return {"content": "Engine answered.", "tool_calls": []}
        return api

    def _client(self, entities, primitives):
        import tempfile
        from pathlib import Path

        from src.orchestrator.events import JsonlEventSink
        sink = JsonlEventSink(Path(tempfile.mkdtemp()) / "e.jsonl")
        app = create_app(self._api(entities, primitives), fake_kql,
                         sink, planner=True)
        return TestClient(app)

    def test_no_relation_word_gets_the_default_map_card(self):
        client = self._client(["ED Sepsis Screening"], [])
        r = client.post("/api/ask", json={
            "message": "tell me about ED Sepsis Screening"})
        j = r.json()
        assert "the map around" in j["parse_confirm"]
        assert j["show"][0]["matches"]
        assert "outputs" not in j
        # the confirm executes the default map: retrieve, no compare
        r2 = client.post("/api/parse/confirm",
                         json={"conversation_id": j["conversation_id"]})
        jj = r2.json()
        assert [o["component"]["op"] for o in jj["outputs"]] == [
            "retrieve"]
        assert jj["conclusion"]["kind"] == "definition"

    def test_zero_grounded_entities_get_the_no_match_card(self):
        # B9 + the remove-the-type ruling: NO silent engine route —
        # the no-match card carries rephrase + doors instead
        client = self._client(["Zzz Nothing Ever"], [])
        r = client.post("/api/ask", json={
            "message": "what about zzz nothing ever?"})
        j = r.json()
        assert j["no_match"] is True
        assert "no catalog match" in j["parse_confirm"]
        assert "contact a developer" in j["parse_confirm"]
        assert "caption" not in j          # the engine never ran

    def test_zero_entity_question_gets_the_no_match_card(self):
        # B9 exact: "what is the weather today"
        client = self._client([], [])
        r = client.post("/api/ask", json={
            "message": "what is the weather today"})
        j = r.json()
        assert j["no_match"] is True
        assert "rephrase" in j["parse_confirm"]

    def test_engine_reachable_only_via_the_explicit_button(self):
        # C5: planner:false (the card button's wire shape) is the
        # ONLY road to the engine
        client = self._client(["Zzz Nothing Ever"], [])
        r = client.post("/api/ask", json={
            "message": "what about zzz?", "planner": False})
        assert r.json()["caption"] == "Engine answered."

    def test_count_words_propose_the_policy_refusal(self):
        # B10: row-data asks ground fine but PROPOSE the refusal +
        # the definition offer; confirm retrieves the record
        client = self._client(["ED Sepsis Screening"], ["count_rows"])
        r = client.post("/api/ask", json={
            "message": "how many patients are in the cohort?"})
        j = r.json()
        assert "patient rows never reach the model" in j["parse_confirm"]
        assert "definition" in j["parse_confirm"]
        r2 = client.post("/api/parse/confirm",
                         json={"conversation_id": j["conversation_id"]})
        assert [o["component"]["op"] for o in r2.json()["outputs"]] == [
            "retrieve"]

    def test_latency_split_is_measured_on_card_and_confirm(self):
        client = self._client(["ED Sepsis Screening"], [])
        r = client.post("/api/ask", json={"message": "about sepsis"})
        j = r.json()
        assert set(j["latency_ms"]) == {"parse", "ground"}
        r2 = client.post("/api/parse/confirm",
                         json={"conversation_id": j["conversation_id"]})
        assert "execute" in r2.json()["latency_ms"]
        assert "ms — the parse was the plan" in r2.json()["loop_status"]

    def test_stream_surface_emits_skeleton_then_matches_then_done(self):
        client = self._client(["ED Sepsis Screening"], [])
        r = client.post("/api/ask/stream",
                        json={"message": "about sepsis"})
        text = r.text
        assert text.index("event: stage") < text.index("event: card")
        assert '"parse_line"' in text and '"grounded"' in text
        assert text.rstrip().split("event: ")[-1].startswith("done")

    def test_confirm_stream_emits_op_chips_then_done(self):
        client = self._client(["ED Sepsis Screening"], [])
        r1 = client.post("/api/ask", json={"message": "about sepsis"})
        conv = r1.json()["conversation_id"]
        r2 = client.post("/api/parse/confirm/stream",
                         json={"conversation_id": conv})
        text = r2.text
        assert '"pending": true' in text
        assert text.index("event: output") < text.index("event: done")


class TestBatch7:
    """RW-BATCH-7 (Sunny's three fresh questions): the no-match card
    wires (RW-19, DOM leg in test_page_dom), grounding is generous
    (RW-20 — match maximally, human prunes), and kind-only asks are
    a census, never a dead end (RW-21)."""

    def _client(self, entities, primitives):
        maker = TestCardEverywhere()
        return maker._client(entities, primitives)

    def test_rw21_kind_only_composes_the_census(self):
        client = self._client([], [])   # parse: all kind words
        # simulate the parser splitting "metrics" into kinds: the
        # split happens in parse_question, so feed the raw entity
        maker = TestCardEverywhere()
        client = maker._client(["metrics"], [])
        r = client.post("/api/ask", json={
            "message": "what metrics are there"})
        j = r.json()
        assert j.get("no_match") is not True
        assert "catalog census of metrics" in j["parse_confirm"]
        r2 = client.post("/api/parse/confirm",
                         json={"conversation_id": j["conversation_id"]})
        assert [o["component"]["op"] for o in r2.json()["outputs"]] == [
            "census"]

    def test_rw20_stem_tokens_reach_near_names(self):
        # "diabetes" reaches "Diabetic" via the stem tier — using
        # the sepsis fixture: "sepsi screening" style near-miss
        from src.orchestrator.ops import OpsSession
        from src.orchestrator.parse_plan import _ground_one
        got = _ground_one("sepsis screenings", fake_kql, OpsSession())
        assert any(a["id"] for a in got), (
            "stem tier found nothing for a near-miss phrase")

    def test_rw20_stem_is_deterministic_morphology(self):
        from src.orchestrator.parse_plan import _stem
        assert _stem("diabetes") == "diabet"
        assert _stem("diabetic") == "diabet"
        assert _stem("codesets") == "codeset"
        assert _stem("definition") == "definition"


class TestRW25IdleWake:
    """RW-25 (Sunny's walk, the 57-min idle): store-no-answer
    auto-retries once (the wake is a ~10-15s transient — one retry
    makes the error card never exist); a second miss renders the
    typed card WITH a retry button flag; the engine's infra text
    names the wake cure."""

    def _flaky_kql(self, failures):
        state = {"n": 0}

        def kql(query, params):
            if state["n"] < failures:
                state["n"] += 1
                raise ConnectionError("store idle — no answer")
            return fake_kql(query, params)
        return kql

    def _client(self, kql):
        import tempfile
        from pathlib import Path

        from src.orchestrator.events import JsonlEventSink
        sink = JsonlEventSink(Path(tempfile.mkdtemp()) / "e.jsonl")
        maker = TestCardEverywhere()
        return TestClient(create_app(
            maker._api(["ED Sepsis Screening"], []), kql, sink,
            planner=True))

    def test_one_store_failure_retries_and_the_card_lands(self):
        client = self._client(self._flaky_kql(failures=1))
        r = client.post("/api/ask", json={"message": "about sepsis"})
        j = r.json()
        assert j.get("no_match") is not True
        assert j["show"][0]["matches"]      # the retry grounded

    def test_persistent_failure_renders_the_retry_card(self):
        client = self._client(self._flaky_kql(failures=99))
        r = client.post("/api/ask", json={"message": "about sepsis"})
        j = r.json()
        assert j["no_match"] is True and j["retry"] is True
        assert "waking from idle" in j["parse_confirm"]

    def test_engine_infra_text_names_the_wake_cure(self):
        from src.orchestrator.turn_engine import _infra_error
        msg = _infra_error(ConnectionError("timed out"))
        assert "waking from idle" in msg and "retry" in msg


class TestFuzzer1:
    """FUZZER-1 (test automation, dev's half): the paraphrase
    fuzzer asserts every phrasing yields a CARD, grounding hits the
    expected names, planted oracles hold, and every miss is logged
    verbatim as lexicon food. Offline: stubbed paraphraser +
    TestClient post adapter over the fixture estate."""

    def _post(self, client):
        def post(path, payload):
            r = client.post(path, json=payload)
            return r.json(), r.status_code
        return post

    def _chat(self, phrases):
        def chat(messages, tools, tool_choice=None):
            return {"content": json.dumps(phrases), "tool_calls": []}
        return chat

    def test_green_run_has_no_findings(self):
        from devtools.walk_fuzzer import fuzz
        maker = TestCardEverywhere()
        client = maker._client(["ED Sepsis Screening"], [])
        result = fuzz(
            self._post(client), self._chat(["about the sepsis one"]),
            n=1, intents=[{
                "name": "definition",
                "seed": "tell me about ED Sepsis Screening",
                "expect_ground": ["ED Sepsis Screening"],
                "oracle": {"kind": "definition"}}])
        assert result["findings"] == []
        assert result["phrasings"] == 1

    def test_grounding_miss_is_logged_as_lexicon_food(self):
        from devtools.walk_fuzzer import fuzz
        maker = TestCardEverywhere()
        client = maker._client(["Zzz Nothing"], [])
        result = fuzz(
            self._post(client), self._chat(["some odd phrasing"]),
            n=1, intents=[{
                "name": "definition",
                "seed": "x",
                "expect_ground": ["ED Sepsis Screening"],
                "oracle": {}}])
        assert any("lexicon food" in f for f in result["findings"])

    def test_dead_paraphraser_is_a_finding_not_a_crash(self):
        from devtools.walk_fuzzer import fuzz
        maker = TestCardEverywhere()
        client = maker._client(["ED Sepsis Screening"], [])
        result = fuzz(self._post(client), self._chat([]), n=1,
                      intents=[{"name": "d", "seed": "x",
                                "oracle": {}}])
        assert any("unfuzzed" in f for f in result["findings"])

    def test_oracle_miss_is_a_finding(self):
        from devtools.walk_fuzzer import fuzz
        maker = TestCardEverywhere()
        client = maker._client(["ED Sepsis Screening"], [])
        result = fuzz(
            self._post(client), self._chat(["about sepsis"]), n=1,
            intents=[{"name": "d", "seed": "x",
                      "oracle": {"kind": "flags"}}])
        assert any("card kind" in f for f in result["findings"])


class TestFlywheel1Surface:
    """FLYWHEEL-1 web half: /api/mine serves the shelf; cards carry
    provenance lines from the captured decisions."""

    def _client(self, tmp_path):
        from src.orchestrator.events import JsonlEventSink
        path = tmp_path / "events.jsonl"
        sink = JsonlEventSink(path)
        maker = TestCardEverywhere()
        app = create_app(maker._api(["ED Sepsis Screening"], []),
                         fake_kql, sink, planner=True,
                         events_path=path)
        return TestClient(app)

    def test_mine_serves_the_shelf_after_a_confirm(self, tmp_path):
        client = self._client(tmp_path)
        r1 = client.post("/api/ask", json={"message": "about sepsis"})
        conv = r1.json()["conversation_id"]
        client.post("/api/parse/confirm",
                    json={"conversation_id": conv})
        shelf = client.get("/api/mine").json()
        assert shelf["definitions"], "no definitions on the shelf"
        assert "about sepsis" in shelf["questions"]

    def test_definition_card_carries_provenance(self, tmp_path):
        client = self._client(tmp_path)
        for _ in range(2):
            r1 = client.post("/api/ask",
                             json={"message": "about sepsis"})
            client.post("/api/parse/confirm", json={
                "conversation_id": r1.json()["conversation_id"]})
        r = client.post("/api/ask", json={"message": "about sepsis"})
        fin = client.post("/api/parse/confirm", json={
            "conversation_id": r.json()["conversation_id"]}).json()
        concl = fin["conclusion"]
        blob = json.dumps(concl)
        assert "no official designated" in blob
        assert "confirmed" in blob

    def test_mine_unconfigured_refuses_typed(self, tmp_path):
        from src.orchestrator.events import JsonlEventSink
        sink = JsonlEventSink(tmp_path / "e.jsonl")
        maker = TestCardEverywhere()
        app = create_app(maker._api([], []), fake_kql, sink)
        r = TestClient(app).get("/api/mine")
        assert r.status_code == 503
        assert r.json()["reason_class"] == "unconfigured"


class TestFuzzer2AllIntents:
    """FUZZER-2 (overnight queue 2): the fuzzer covers ALL intent
    classes with per-intent oracles; kind_any admits the legitimate
    data-driven card classes."""

    def test_all_named_intent_classes_present(self):
        from devtools.walk_fuzzer import INTENTS
        names = {i["name"] for i in INTENTS}
        for wanted in ("codeset_sameness", "tables_of_metric",
                       "kind_census", "flags_family",
                       "count_refusal", "definition", "feeds",
                       "variants"):
            assert wanted in names, wanted
        assert all(i.get("oracle") for i in INTENTS)

    def test_kind_any_oracle_judges(self):
        from devtools.walk_fuzzer import _check
        card = {"parse_confirm": "reading", "show": []}
        fin = {"conclusion": {"kind": "map"}}
        ok = _check(card, fin, {"oracle": {"kind_any": ["map"]}}, "p")
        assert ok == []
        bad = _check(card, fin,
                     {"oracle": {"kind_any": ["flags"]}}, "p")
        assert any("not in" in f for f in bad)


class TestRW26NominateMeansOffer:
    """RW-26 (live trace: nominations entered the compare and a
    5-way partition diluted the twins' E11.80 diff): semantic
    nominations are DEFAULT-EXCLUDED at confirm — the straight-
    through click compares only the exact-tier matches; include_ids
    opts a nomination in."""

    def _client(self):
        maker = TestCardEverywhere()
        return maker._client(["screening for sepsis cases"], [
            "same_or_different"])

    def test_straight_through_confirm_excludes_nominations(self):
        client = self._client()
        r1 = client.post("/api/ask", json={
            "message": "are the sepsis screenings the same?"})
        j = r1.json()
        sems = [m for s in j["show"] for m in s["matches"]
                if m["semantic"]]
        assert sems, "fixture produced no nominations"
        r2 = client.post("/api/parse/confirm", json={
            "conversation_id": j["conversation_id"]})
        jj = r2.json()
        if r2.status_code != 200:
            # nominations excluded leaves <2 anchors: typed refusal
            # is the honest shape for this fixture phrase
            assert jj["reason_class"] in ("parse_refusal", "op_error")
            return
        ran = {i for o in jj["outputs"]
               for i in (o["component"]["params"].get("ids")
                         or o["component"]["params"].get("refs")
                         or [])}
        assert not ({m["id"] for m in sems} & ran)

    def test_include_ids_opts_a_nomination_in(self):
        client = self._client()
        r1 = client.post("/api/ask", json={
            "message": "are the sepsis screenings the same?"})
        j = r1.json()
        sems = [m["id"] for s in j["show"] for m in s["matches"]
                if m["semantic"]]
        r2 = client.post("/api/parse/confirm", json={
            "conversation_id": j["conversation_id"],
            "include_ids": sems})
        assert r2.status_code == 200
        ran = {i for o in r2.json()["outputs"]
               for i in (o["component"]["params"].get("ids")
                         or o["component"]["params"].get("refs")
                         or [])}
        assert set(sems) & ran


class TestRung2AndProcRun:
    """RUNG2-1 + PROC-RUN-1 on the wire: a value change runs at
    rung 2 with the sites stamped; a logic edit refuses as the
    fork; a single-SELECT proc fragment runs via its body."""

    def _client(self, frag):
        from src.orchestrator.assemble import NODE_FACTS_QUERY

        def kql(query, params):
            if query == NODE_FACTS_QUERY:
                return [{"node_id": params["p_node_id"], "name": "S",
                         "properties": json.dumps(
                             {"sql_fragment": frag})}]
            return []
        events = []
        class Sink:
            def record(self, e): events.append(e)
        app = create_app(lambda *a, **k: {"content": "",
                                          "tool_calls": []},
                         kql, Sink(),
                         run_executor=lambda sql: [{"ID": 1}],
                         run_cap=5, run_source="fx")
        return TestClient(app)

    CERT = ("SELECT PATIENT_ID FROM DM_REGISTRY "
            "WHERE HBA1C >= 6.5")

    def test_value_change_runs_at_rung_2(self):
        client = self._client(self.CERT)
        r = client.post("/api/run", json={
            "step_id": "transform:m:S",
            "sql": self.CERT.replace("6.5", "8.0")})
        assert r.status_code == 200
        j = r.json()
        assert j["rung"] == 2
        assert j["param_sites"][0]["submitted"] == "8.0"
        assert "types only" in j["sampling_label"]
        assert j["stamps"]["rung"] == 2

    def test_logic_edit_refuses_as_the_fork(self):
        client = self._client(self.CERT)
        r = client.post("/api/run", json={
            "step_id": "transform:m:S",
            "sql": self.CERT.replace(">=", "<")})
        assert r.status_code == 422
        j = r.json()
        assert j["reason_class"] == "variant_fork"
        assert "your variant" in j["message"]

    def test_plain_run_stays_rung_1(self):
        client = self._client(self.CERT)
        r = client.post("/api/run", json={"step_id": "transform:m:S"})
        j = r.json()
        assert j["rung"] == 1 and j["param_sites"] == []
        assert "byte-identical" in j["sampling_label"]

    def test_single_select_proc_runs_via_its_body(self):
        proc = ("CREATE PROCEDURE reporting.USP_Reg AS\n"
                + self.CERT)
        client = self._client(proc)
        r = client.post("/api/run", json={"step_id": "metric:m"})
        assert r.status_code == 200
        assert r.json()["rung"] == 1

    def test_multi_statement_proc_stays_refused(self):
        proc = ("CREATE PROCEDURE p AS\nBEGIN\n"
                "UPDATE T SET X=1;\nSELECT 1;\nEND")
        client = self._client(proc)
        r = client.post("/api/run", json={"step_id": "metric:m"})
        assert r.status_code == 422
        assert r.json()["reason_class"] in ("multi_statement",
                                            "not_select")
