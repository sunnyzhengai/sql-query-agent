"""Fabric workspace TMDL source (the turn-key profile, no git needed).

Stubbed HTTP: what matters is the protocol — pagination, the 202
long-running getDefinition with bounded polling, TMDL part filtering,
and base64 decoding. Live verification happens on the tenant."""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import pytest

from src.extractor.tmdl_source import FabricWorkspaceTmdlSource

TMDL = "table SepsisData\n\tpartition p = m\n"


def _resp(status=200, payload=None, headers=None):
    return SimpleNamespace(
        status_code=status,
        headers=headers or {},
        json=lambda: payload or {},
        raise_for_status=lambda: None,
    )


def _part(path, content):
    return {"path": path,
            "payload": base64.b64encode(content.encode()).decode()}


class _StubHttp:
    def __init__(self, get_responses, post_responses):
        self._gets = list(get_responses)
        self._posts = list(post_responses)
        self.get_urls = []

    def get(self, url, headers=None, timeout=None):
        self.get_urls.append(url)
        return self._gets.pop(0)

    def post(self, url, headers=None, timeout=None):
        return self._posts.pop(0)


def _source(http):
    return FabricWorkspaceTmdlSource(
        "ws-1", token_provider=lambda: "tok", http=http, sleep=lambda s: None)


def test_collects_and_decodes_table_parts_only():
    http = _StubHttp(
        get_responses=[_resp(payload={"value": [
            {"id": "m1", "displayName": "Sepsis Compliance Dashboard"}]})],
        post_responses=[_resp(payload={"definition": {"parts": [
            _part("definition/tables/SepsisData.tmdl", TMDL),
            _part("definition/tables/LocalDateTable_x.tmdl", "skip me"),
            _part("definition/model.tmdl", "not a table"),
        ]}})],
    )
    files = _source(http).collect()
    assert len(files) == 1
    f = files[0]
    assert f.report_name == "Sepsis Compliance Dashboard"
    assert f.table_name == "SepsisData"
    assert f.content == TMDL
    assert f.semantic_model_path == "workspace:ws-1/m1"


def test_202_long_running_polls_until_succeeded():
    http = _StubHttp(
        get_responses=[
            _resp(payload={"value": [{"id": "m1", "displayName": "R"}]}),
            _resp(payload={"status": "Running"}),
            _resp(payload={"status": "Succeeded"}),
            _resp(payload={"definition": {"parts": [
                _part("definition/tables/T.tmdl", TMDL)]}}),
        ],
        post_responses=[_resp(status=202, headers={"Location": "https://op/1"})],
    )
    files = _source(http).collect()
    assert len(files) == 1
    assert http.get_urls[-1] == "https://op/1/result"


def test_202_that_never_finishes_raises_with_retry_message():
    src = _source(_StubHttp(
        get_responses=[_resp(payload={"status": "Running"})] * 40,
        post_responses=[_resp(status=202, headers={"Location": "https://op/1"})],
    ))
    src.MAX_POLLS = 3
    with pytest.raises(RuntimeError, match="retry later"):
        src.get_definition_parts("m1")


def test_pagination_follows_continuation():
    http = _StubHttp(
        get_responses=[
            _resp(payload={"value": [{"id": "m1", "displayName": "A"}],
                           "continuationUri": "https://next"}),
            _resp(payload={"value": [{"id": "m2", "displayName": "B"}]}),
        ],
        post_responses=[],
    )
    models = _source(http).list_semantic_models()
    assert [m["id"] for m in models] == ["m1", "m2"]


def test_rows_are_json_serializable_end_to_end():
    http = _StubHttp(
        get_responses=[_resp(payload={"value": [{"id": "m1", "displayName": "R"}]})],
        post_responses=[_resp(payload={"definition": {"parts": [
            _part("definition/tables/T.tmdl", TMDL)]}})],
    )
    files = _source(http).collect()
    json.dumps([f.__dict__ for f in files])
