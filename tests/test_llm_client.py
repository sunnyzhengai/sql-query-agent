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
