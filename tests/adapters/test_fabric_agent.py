"""Tests for FabricAgentClient token handling.

Audit 2026-08-15: notebook 08 fetched one token and passed it by value,
so >1hr description runs died mid-loop with auth failures disguised as
content failures. The client now takes a token_provider callable (the
pattern notebook 11 uses for Kusto) and retries once with a forced
refresh on 401/403.
"""

import requests

from src.adapters.fabric_agent import FabricAgentClient


class FakeResp:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {"result": {"content": [{"text": "ok"}]}}
        self.text = text

    def json(self):
        return self._json


def make_client(**kwargs):
    return FabricAgentClient(
        workspace_id="ws", agent_id="ag", tool_name="DataAgent_Test", **kwargs
    )


def test_token_provider_called_per_request(monkeypatch):
    tokens = iter(["tok-1", "tok-2"])
    seen_auth = []

    def fake_post(url, headers=None, json=None, timeout=None):
        seen_auth.append(headers["Authorization"])
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    client = make_client(token_provider=lambda: next(tokens))
    client.query("q1")
    client.query("q2")
    assert seen_auth == ["Bearer tok-1", "Bearer tok-2"]


def test_401_forces_refresh_and_retries_once(monkeypatch):
    calls = []
    provider_calls = []

    def provider():
        provider_calls.append(1)
        return f"tok-{len(provider_calls)}"

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(headers["Authorization"])
        if len(calls) == 1:
            return FakeResp(status_code=401, text="TokenExpired")
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    client = make_client(token_provider=provider)
    resp = client.query("q")
    assert resp.status == "success"
    assert len(calls) == 2, "401 must trigger exactly one retry"
    assert calls[0] != calls[1], "retry must use a refreshed token"


def test_persistent_401_surfaces_auth_error(monkeypatch):
    monkeypatch.setattr(
        requests, "post",
        lambda url, headers=None, json=None, timeout=None: FakeResp(
            status_code=401, text="TokenExpired"),
    )
    client = make_client(token_provider=lambda: "tok")
    resp = client.query("q")
    assert resp.status == "failed"
    assert "401" in resp.error


def test_explicit_access_token_still_works(monkeypatch):
    seen = []

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.append(headers["Authorization"])
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    client = make_client(access_token="static-tok")
    client.query("q")
    assert seen == ["Bearer static-tok"]
