"""THE LIVE-WIRE TOGGLE's tests (Design_Chatbot.md rider, ruled
2026-09-12). Deterministic only — the transport is SCRIPTED (the
doubles law): no live HTTP in the suite; the real wire fires only
by Sunny's hand, one counted capacity spend per query.

Proves: contract:aivia-design-to-code
"""
import json

from aivia import fabric_wire
from aivia import meaning_console as mc


def _ok_body(columns, rows, code="00000"):
    return json.dumps({
        "status": {"code": code, "description":
                   "note: successful completion"},
        "result": {"kind": "TABLE",
                   "columns": [{"name": c, "gqlType": "STRING",
                                "jsonType": "string"}
                               for c in columns],
                   "data": rows}})


def _err_body(code, description):
    return json.dumps({"status": {"code": code,
                                  "description": description}})


def _wire(script):
    """A wire whose transport replays the scripted outcomes and
    records every request it saw."""
    seen = []

    def transport(url, headers, body):
        seen.append({"url": url, "headers": headers,
                     "body": json.loads(body)})
        return script.pop(0)
    w = fabric_wire.FabricGraphWire(
        "ws-1", "gm-1", lambda: "tok-A", transport=transport)
    return w, seen


# ---- from_env: the seat-down banner law ----------------------------
def test_unconfigured_wire_is_disabled_with_the_reason():
    wire, reason = fabric_wire.from_env(env={})
    assert wire is None
    assert fabric_wire.WORKSPACE_VAR in reason
    assert fabric_wire.GRAPH_MODEL_VAR in reason


def test_configured_wire_carries_ids_into_the_documented_url():
    wire, reason = fabric_wire.from_env(env={
        fabric_wire.WORKSPACE_VAR: "ws-9",
        fabric_wire.GRAPH_MODEL_VAR: "gm-9",
        fabric_wire.TOKEN_VAR: "tok-env"})
    assert reason == ""
    assert "/workspaces/ws-9/GraphModels/gm-9/executeQuery" \
        in wire.url
    assert wire.url.endswith("?preview=true")


# ---- execute: the HTTP contract, normalized ------------------------
def test_execute_sends_the_artifact_and_normalizes_the_table():
    w, seen = _wire([(200, _ok_body(
        ["name"], [{"name": "ADT_EVENTS"}, {"name": "BED_CONFIG"}]))])
    out = w.execute("MATCH (a:table) RETURN a.name AS name")
    assert seen[0]["body"] == {
        "query": "MATCH (a:table) RETURN a.name AS name"}
    assert seen[0]["headers"]["Authorization"] == "Bearer tok-A"
    assert out["ok"] and out["row_count"] == 2
    assert out["columns"] == ["name"]
    assert out["rows"][1]["name"] == "BED_CONFIG"


def test_application_error_renders_code_and_description_verbatim():
    w, _ = _wire([(200, _err_body(
        "42001", "error: syntax error or access rule violation"))])
    out = w.execute("MATCHH (n)")
    assert not out["ok"]
    assert out["code"] == "42001"
    assert "syntax error" in out["description"]


def test_transport_error_is_honest_never_raised():
    w, _ = _wire([(503, "Service Unavailable")])
    out = w.execute("MATCH (n) RETURN n")
    assert not out["ok"] and out["code"] == "http 503"


def test_expired_token_refreshes_once_then_retries():
    calls = []
    script = [(401, ""), (200, _ok_body(["n"], [{"n": 1}]))]

    def transport(url, headers, body):
        calls.append(headers["Authorization"])
        return script.pop(0)
    tokens = iter(["tok-old", "tok-new"])
    w = fabric_wire.FabricGraphWire(
        "ws", "gm", lambda: next(tokens), transport=transport)
    out = w.execute("MATCH (n) RETURN n")
    assert out["ok"]
    assert calls == ["Bearer tok-old", "Bearer tok-new"]


# ---- run_round: the artifact fires, the comparison stays honest ----
def _round(gql, rows):
    return {"gql": gql, "rows": rows}


def test_single_query_beside_rows_earns_a_verdict():
    w, seen = _wire([(200, _ok_body(["a"], [{"a": 1}, {"a": 2}]))])
    blocks = fabric_wire.run_round(w, _round(
        ["MATCH …"], [{"a": "x"}, {"a": "y"}]))
    assert len(blocks) == 1
    assert blocks[0]["verdict"] == "MATCH"
    assert blocks[0]["local_count"] == 2


def test_count_mismatch_is_a_reported_divergence():
    w, _ = _wire([(200, _ok_body(["a"], [{"a": 1}]))])
    blocks = fabric_wire.run_round(w, _round(
        ["MATCH …"], [{"a": "x"}, {"a": "y"}]))
    assert blocks[0]["verdict"] == "DIVERGE"


def test_multiple_queries_report_counts_without_a_verdict():
    w, _ = _wire([(200, _ok_body(["a"], [{"a": 1}])),
                  (200, _ok_body(["a"], []))])
    blocks = fabric_wire.run_round(w, _round(
        ["MATCH 1", "MATCH 2"], [{"a": "x"}]))
    assert len(blocks) == 2
    assert all("verdict" not in b for b in blocks)
    assert [b["row_count"] for b in blocks] == [1, 0]


# ---- the rendered round: served rows beside local, spend counted --
def _result(**over):
    base = {"question": "q", "seat": "floor", "tokens": ["q"],
            "match_sets": [], "anchors": [], "mode": "list",
            "rows": [], "counts": {}, "capped": None,
            "kind_constraints": [], "label_constraint": [],
            "label_relaxed": [], "pinned": [], "pin_misses": [],
            "edge_constraints": [], "gql": [], "evidence": [],
            "edge_lines": [], "gaps": [], "relaxed": [],
            "unmatched": []}
    base.update(over)
    return base


def test_render_shows_served_rows_verdict_and_the_spend_line():
    r = _result(gql=["MATCH …"], wire_spent=3, wire=[{
        "gql": "MATCH …", "ok": True, "code": "00000",
        "description": "", "columns": ["name"],
        "rows": [{"name": "ADT_EVENTS"}], "row_count": 1,
        "local_count": 1, "verdict": "MATCH"}])
    out = mc.render_round(r)
    assert "the SERVED graph answers" in out
    assert "ADT_EVENTS" in out
    assert "local 1 row(s) · served 1 row(s) — MATCH" in out
    assert "capacity spends this session: 3 queries" in out


def test_render_shows_wire_errors_verbatim():
    r = _result(wire_spent=1, wire=[{
        "gql": "g", "ok": False, "code": "42001",
        "description": "error: syntax error", "columns": [],
        "rows": [], "row_count": 0}])
    out = mc.render_round(r)
    assert "wire error [42001]" in out
    assert "syntax error" in out


def test_a_round_without_the_wire_renders_no_wire_block():
    out = mc.render_round(_result(gql=["MATCH …"]))
    assert "SERVED graph" not in out
    assert "capacity spends" not in out


# ---- the handler: OFF at boot, Sunny's hand flips, spends count ----
def test_the_toggle_is_off_at_boot_and_the_flip_counts_spends():
    import urllib.request
    from http.server import ThreadingHTTPServer

    w, seen = _wire([(200, _ok_body(["a"], [{"a": 1}]))])
    handler = mc.make_handler(
        "test", "coverage", lambda q, pins=None, reach="near": _result(
            gql=["MATCH …"],
            rows=[{"a": "T1", "edge": "has_part", "b": "C1"}]),
        wire=w, wire_reason="")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    import threading
    threading.Thread(target=server.serve_forever,
                     daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    def get(path):
        with urllib.request.urlopen(base + path, timeout=10) as r:
            return json.loads(r.read())
    try:
        # OFF at every boot — the capacity law; a round fires nothing
        assert get("/wire")["on"] is False
        get("/round?q=hello")
        assert seen == [] and get("/wire")["spent"] == 0
        # Sunny's hand flips it; the round fires and the spend counts
        assert get("/wire?on=1")["on"] is True
        out = get("/round?q=hello")
        assert "SERVED graph" in out["html"]
        assert len(seen) == 1
        assert get("/wire")["spent"] == 1
    finally:
        server.shutdown()


def test_an_unconfigured_wire_reports_disabled_over_the_endpoint():
    import urllib.request
    from http.server import ThreadingHTTPServer
    handler = mc.make_handler(
        "test", "coverage", lambda q, pins=None, reach="near": _result(),
        wire=None, wire_reason="live wire disabled: set X")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    import threading
    threading.Thread(target=server.serve_forever,
                     daemon=True).start()
    try:
        url = (f"http://127.0.0.1:{server.server_address[1]}"
               "/wire?on=1")
        with urllib.request.urlopen(url, timeout=10) as r:
            out = json.loads(r.read())
        assert out["on"] is False
        assert "disabled" in out["reason"]
    finally:
        server.shutdown()
