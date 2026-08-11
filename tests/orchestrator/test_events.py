"""Tests for decision telemetry (Sunny, 2026-08-11): every turn records
WHO made its load-bearing decisions, so no-solution feedback patterns
attribute to the deterministic layer or the LLM."""

from src.orchestrator.events import (
    OneLakeJsonlSink,
    TurnEvent,
    decision_shape,
)


def call(tool, result=None, args=None):
    return {"tool": tool, "args": args or {}, "result": result or {"ok": 1}}


class TestDecisionShape:
    def test_verified_by_tool(self):
        d = decision_shape(
            [call("find_by_name"), call("check_same_logic")],
            "No — the logic is not the same; 2 distinct definitions.")
        assert d["verified_by_tool"] is True
        assert d["unverified_sameness_language"] is False

    def test_llm_assembled_comparison_is_flagged(self):
        # two fact reads, no verify call, sameness language in the
        # answer: the LLM decided in its head — the highest-risk shape
        d = decision_shape(
            [call("get_facts"), call("get_facts")],
            "They share the same source tables and look identical.")
        assert d["llm_assembled"] is True
        assert d["unverified_sameness_language"] is True
        assert d["verified_by_tool"] is False

    def test_small_fact_assembly_without_sameness_claims(self):
        d = decision_shape(
            [call("get_facts"), call("get_facts")],
            "Metric A is stewarded by Pat; Metric B lists no steward.")
        assert d["llm_assembled"] is True
        assert d["unverified_sameness_language"] is False

    def test_refusals_and_smalltalk(self):
        d = decision_shape([], "I cannot provide patient counts.")
        assert d["no_tools"] is True and d["search_only"] is False
        d2 = decision_shape([call("search_catalog")],
                            "Several metrics relate to sepsis: ...")
        assert d2["search_only"] is True

    def test_tool_errors_counted(self):
        d = decision_shape(
            [call("get_facts", result={"error": "not surfaced"}),
             call("search_catalog"), call("get_facts")],
            "Here are the facts.")
        assert d["tool_errors"] == 1


class FakeResponse:
    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400 and self.status_code != 404:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeDfs:
    """Programmable ADLS-gen2 transport: tracks the appended bytes."""

    def __init__(self, exists=False, length=0):
        self.exists, self.length = exists, length
        self.calls, self.appended = [], b""

    def head(self, url, **kw):
        self.calls.append(("head", url))
        if not self.exists:
            return FakeResponse(404)
        return FakeResponse(200, {"Content-Length": str(self.length)})

    def put(self, url, **kw):
        self.calls.append(("put", url))
        self.exists, self.length = True, 0
        return FakeResponse(201)

    def patch(self, url, data=b"", **kw):
        self.calls.append(("patch", url))
        if "action=append" in url:
            self.appended += data
            self.length += len(data)
        return FakeResponse(202)


def _event():
    return TurnEvent(
        event_at="t", user_id="u", question="q", tools_used=(),
        ids_read=(), basis="b", answered=True,
        conversation_id="c", turn_index=0)


class TestOneLakeSink:
    URL = "https://onelake.dfs.fabric.microsoft.com/ws/lh.Lakehouse/Files/agent_events/webapp.jsonl"

    def test_creates_then_appends_and_flushes(self):
        dfs = FakeDfs(exists=False)
        sink = OneLakeJsonlSink(self.URL, lambda: "tok", transport=dfs)
        sink.record(_event())
        ops = [c[0] for c in dfs.calls]
        assert ops == ["head", "put", "patch", "patch"]
        assert "action=append&position=0" in dfs.calls[2][1]
        assert dfs.appended.endswith(b"\n")
        assert b'"question": "q"' in dfs.appended

    def test_appends_at_existing_length(self):
        dfs = FakeDfs(exists=True, length=100)
        OneLakeJsonlSink(self.URL, lambda: "tok", transport=dfs).record(_event())
        assert "action=append&position=100" in dfs.calls[1][1]
        flush = dfs.calls[2][1]
        assert f"action=flush&position={100 + dfs.length - 100 + 100}" \
            not in flush  # flush position = 100 + len(line)
        assert f"action=flush&position={dfs.length}" in flush
