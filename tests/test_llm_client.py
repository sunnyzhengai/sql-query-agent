"""Tests for the Azure-aware LLM doorway — request shape, no live calls."""

import pytest

from src.llm_client import (
    DEFAULT_AZURE_API_VERSION,
    build_chat_request,
    chat_completion,
    is_azure_endpoint,
)

KEY = "sk-test"
AZURE = "https://myres.openai.azure.com/openai/deployments/gpt4o-mini"
OPENAI = "https://api.openai.com/v1"


class TestEndpointDetection:
    def test_azure_detected_case_insensitive(self):
        assert is_azure_endpoint(AZURE)
        assert is_azure_endpoint(AZURE.upper())
        assert not is_azure_endpoint(OPENAI)


class TestOpenAIShape:
    def test_bearer_header_only(self):
        url, headers = build_chat_request(OPENAI, KEY)
        assert headers == {"Authorization": f"Bearer {KEY}"}
        assert url == "https://api.openai.com/v1/chat/completions"

    def test_trailing_slash_tolerated(self):
        url, _ = build_chat_request(OPENAI + "/", KEY)
        assert url == "https://api.openai.com/v1/chat/completions"


class TestAzureShape:
    def test_api_key_header_only_no_bearer(self):
        _, headers = build_chat_request(AZURE, KEY)
        assert headers == {"api-key": KEY}
        assert "Authorization" not in headers

    def test_default_api_version_appended(self):
        url, _ = build_chat_request(AZURE, KEY)
        assert url == (f"{AZURE}/chat/completions"
                       f"?api-version={DEFAULT_AZURE_API_VERSION}")

    def test_configured_api_version_survives_path_join(self):
        # the classic bug: naive f"{endpoint}/chat/completions" would
        # produce ...?api-version=X/chat/completions
        url, _ = build_chat_request(AZURE + "?api-version=2024-10-21", KEY)
        assert url == f"{AZURE}/chat/completions?api-version=2024-10-21"
        assert "api-version=2024-10-21/chat" not in url

    def test_env_override_of_default_version(self, monkeypatch):
        monkeypatch.setenv("SQA_AZURE_API_VERSION", "2025-01-01")
        url, _ = build_chat_request(AZURE, KEY)
        assert "api-version=2025-01-01" in url


class TestChatCompletion:
    def test_posts_resolved_shape_and_parses_reply(self, monkeypatch):
        seen = {}

        class FakeResponse:
            status_code = 200
            headers: dict = {}

            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "  the answer  "}}]}

        def fake_post(url, headers=None, json=None, timeout=None):
            seen.update(url=url, headers=headers, body=json, timeout=timeout)
            return FakeResponse()

        monkeypatch.setattr("src.llm_client.requests.post", fake_post)
        out = chat_completion("sys", "usr", endpoint=AZURE, api_key=KEY, model="ignored")
        assert out == "the answer"
        assert seen["headers"] == {"api-key": KEY}
        assert "api-version=" in seen["url"]
        assert seen["body"]["temperature"] == 0
        assert seen["body"]["messages"][0] == {"role": "system", "content": "sys"}

    def test_missing_key_or_endpoint_raises(self):
        with pytest.raises(ValueError):
            chat_completion("s", "u", endpoint=OPENAI, api_key="")
        with pytest.raises(ValueError):
            chat_completion("s", "u", endpoint="", api_key=KEY)


class _Resp:
    def __init__(self, status, content="ok", headers=None):
        self.status_code = status
        self.headers = headers or {}
        self._content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


class TestTransientRetry:
    """Field find (tenant 600 run, 2026-08-20): a ~460-call run lost two
    adjacent steps to one transient burst — a single POST with no retry
    turns a momentary 429 into a permanently missing description."""

    def _patch(self, monkeypatch, responses):
        import src.llm_client as lc
        calls = {"posts": 0, "sleeps": []}

        def fake_post(url, **kwargs):
            calls["posts"] += 1
            r = responses[calls["posts"] - 1]
            if isinstance(r, Exception):
                raise r
            return r

        monkeypatch.setattr(lc.requests, "post", fake_post)
        monkeypatch.setattr(lc, "_sleep", calls["sleeps"].append)
        return calls

    def test_429_retried_then_succeeds(self, monkeypatch):
        calls = self._patch(monkeypatch, [_Resp(429), _Resp(200, "fine")])
        out = chat_completion("s", "u", endpoint=OPENAI, api_key=KEY)
        assert out == "fine" and calls["posts"] == 2

    def test_retry_after_header_honored(self, monkeypatch):
        calls = self._patch(
            monkeypatch, [_Resp(429, headers={"Retry-After": "7"}), _Resp(200)])
        chat_completion("s", "u", endpoint=OPENAI, api_key=KEY)
        assert calls["sleeps"] == [7.0]

    def test_timeout_retried_then_succeeds(self, monkeypatch):
        import requests as rq
        calls = self._patch(
            monkeypatch, [rq.Timeout("slow"), _Resp(200, "fine")])
        assert chat_completion("s", "u", endpoint=OPENAI, api_key=KEY) == "fine"
        assert calls["posts"] == 2

    def test_persistent_transient_error_still_raises(self, monkeypatch):
        calls = self._patch(monkeypatch, [_Resp(503)] * 3)
        with pytest.raises(RuntimeError, match="HTTP 503"):
            chat_completion("s", "u", endpoint=OPENAI, api_key=KEY)
        assert calls["posts"] == 3  # bounded — never an infinite loop

    def test_hard_client_error_never_retried(self, monkeypatch):
        calls = self._patch(monkeypatch, [_Resp(401)])
        with pytest.raises(RuntimeError, match="HTTP 401"):
            chat_completion("s", "u", endpoint=OPENAI, api_key=KEY)
        assert calls["posts"] == 1
