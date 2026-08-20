"""The one LLM doorway: OpenAI-compatible chat completions, Azure-aware.

Azure OpenAI and api.openai.com disagree on two things this module owns:

  auth header   Azure wants `api-key: <key>`; OpenAI wants
                `Authorization: Bearer <key>`. Sending the wrong one (or
                both) is undefined behavior we don't gamble on — the
                endpoint shape picks exactly one.
  url shape     Azure requires `?api-version=...` on the request; the
                deployment is in the path and any query string in the
                configured endpoint must survive the path join.

Consumers: 600_generate_descriptions (customer's Azure OpenAI in
production), devtools (dev key against api.openai.com). Keys arrive as
arguments — this module never reads key material from disk.
"""

from __future__ import annotations

import time

import requests

# Bump deliberately; override per-deployment via SQA_AZURE_API_VERSION
# or by putting api-version=... in the configured endpoint.
DEFAULT_AZURE_API_VERSION = "2024-06-01"


def is_azure_endpoint(endpoint: str) -> bool:
    return ".openai.azure.com" in endpoint.lower()


def build_chat_request(endpoint: str, api_key: str) -> "tuple[str, dict]":
    """Resolve (url, auth headers) for a chat-completions call.

    Any query string on the configured endpoint is preserved; Azure
    endpoints get a default api-version appended when none is given.
    """
    base, _, query = endpoint.partition("?")
    url = base.rstrip("/") + "/chat/completions"
    if is_azure_endpoint(endpoint):
        headers = {"api-key": api_key}
        if "api-version" not in query:
            from src.branding import legacy_env
            version = legacy_env("AZURE_API_VERSION", DEFAULT_AZURE_API_VERSION)
            query = (query + "&" if query else "") + f"api-version={version}"
    else:
        headers = {"Authorization": f"Bearer {api_key}"}
    if query:
        url += "?" + query
    return url, headers


# Field find (tenant 600 run, 2026-08-20): a ~460-call sequential run
# lost 2 adjacent steps to one transient burst — a single POST with no
# retry turns a momentary 429 into a permanently missing description.
TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_ATTEMPTS = 3
_sleep = time.sleep  # injection point for tests


def chat_completion(
    system: str,
    user: str,
    *,
    endpoint: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    timeout: int = 60,
) -> str:
    """One chat call, temperature 0. On Azure the deployment in the URL
    decides the model; the body's model field is accepted and ignored.
    Transient failures (429/5xx/timeout) are retried up to MAX_ATTEMPTS
    with backoff, honoring Retry-After; persistent failures still raise."""
    if not api_key:
        raise ValueError("api_key is required")
    if not endpoint:
        raise ValueError("endpoint is required")
    url, headers = build_chat_request(endpoint, api_key)
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
    }
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(url, headers=headers, json=body, timeout=timeout)
        except (requests.Timeout, requests.ConnectionError):
            if attempt == MAX_ATTEMPTS:
                raise
            _sleep(2 * attempt)
            continue
        if response.status_code in TRANSIENT_STATUS and attempt < MAX_ATTEMPTS:
            try:
                delay = float(response.headers.get("Retry-After", ""))
            except ValueError:
                delay = 2 * attempt
            _sleep(min(delay, 60))
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    raise RuntimeError("unreachable")  # loop always returns or raises
