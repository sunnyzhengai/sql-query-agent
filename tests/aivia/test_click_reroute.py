"""STEP A of the search rebuild — CLICKS ARE STEER (gap 12). Suite
first (step discipline; Sunny's blanket 'execute one by one').

Ruled: a click on a rendered node is never a question — it opens
the entity round directly (no Interpreter, no search) and lands on
the table. This must hold BEFORE the pre-tier dies, or every click
would hit the model.

Pins:
1. /round?entity=<id> answers with the entity's card, updates the
   conversation's table, and never calls the Interpreter.
2. Identity links minted in rendered rounds point at entity=, not
   q= (Referenced, clarify candidates).
3. A label-group round exists for group clicks (/round?label=table
   lists the members) — the destination the search rebuild's group
   hits will need.

Proves: contract:aivia-design-to-code
"""
import json
import threading
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from aivia.graph.read_api import ReadApi

from .test_ask_console import fake_embed

T0 = "2026-09-07T12:00:00Z"


@pytest.fixture(scope="module")
def surface():
    from aivia import console
    from aivia.flows import ask, grounding
    store, _ = console.build_store("sepsis")
    read = ReadApi(store)
    index = ask.build_index(read)
    semantic = grounding.SemanticIndex(index, fake_embed,
                                       "fake-64", cache_path=None)
    calls = []

    def recording_interpreter(question):
        calls.append(question)
        return {"mentions": [question]}

    handler = console.make_handler(store, "sepsis",
                                   recording_interpreter, semantic,
                                   {})
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", calls
    srv.shutdown()


def _round(base, **params):
    url = base + "/round?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def test_entity_click_is_direct_and_lands_on_the_table(surface):
    base, calls = surface
    before = list(calls)
    out = _round(base, entity="emr|dbo|ED_ENCOUNTERS_DM", c="ca")
    assert out["status"] == "answer"
    assert "ED_ENCOUNTERS_DM" in out["html"]
    assert "emr|dbo|ED_ENCOUNTERS_DM" in out["context_set"]
    assert calls == before  # the Interpreter was never consulted


def test_minted_identity_links_are_entity_links(surface):
    base, _calls = surface
    out = _round(base, entity="emr|dbo|ADT_EVENTS|ENCOUNTER_ID",
                 c="cb")
    # the round's Referenced links carry entity=, never q=
    assert "entity=" in out["html"]
    assert "/?q=emr%7C" not in out["html"]


def test_label_group_round_lists_the_members(surface):
    base, calls = surface
    before = list(calls)
    out = _round(base, label="table", c="cc")
    assert out["status"] == "answer"
    assert "90" in out["html"]
    assert "ADT_EVENTS" in out["html"]
    assert calls == before  # groups are steer too
