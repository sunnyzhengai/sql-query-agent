"""The ask-the-graph console (ADR 0078) — a thin localhost web
surface over an estate's store: one box, free questions, rendered
answers. Deterministic end to end; every ask lands its H5 usage
event. This is the sanctioned validation surface (web UI, never the
Fabric agent) and the ask surface of the graph — NOT the deferred
inward flow: no data-question matching, no generation, no open chat.

Usage: python3.11 -m aivia.console [estate] [port]
       (estate defaults to sepsis; port to 8377)
"""
import datetime
import html
import json
import pathlib
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from aivia.flows import ask, inbound
from aivia.graph import kg1_intake

_PAGE = """<!doctype html><meta charset="utf-8">
<title>AIVIA — ask the graph</title>
<style>
 body {{ font: 15px/1.5 -apple-system, sans-serif; margin: 2rem auto;
        max-width: 60rem; color: #222; }}
 input {{ width: 100%; font-size: 1.1rem; padding: .5rem; }}
 pre {{ background: #f6f6f6; padding: 1rem; white-space: pre-wrap; }}
 .meta {{ color: #777; font-size: .85rem; }}
</style>
<h2>Ask the graph <span class=meta>({estate})</span></h2>
<form method=get action=/>
 <input name=q value="{q}" placeholder="what is THERA_CLASS_CODE ·
 lineage of ED_ENCOUNTERS_DM · filters on MEDICATION_ID · gaps"
 autofocus>
</form>
{answer}
<p class=meta>Typed ops: lookup · lineage · filters_on · who_reads ·
define · gaps — free text in, deterministic traversal, meanings out;
every ask is a usage event. Ambiguity and no-match are honest
outcomes.</p>
"""


def build_store(estate: str):
    base = (pathlib.Path(__file__).resolve().parents[1]
            / "AIVIA_Product" / "estates" / estate)
    store = kg1_intake.new_store()
    reg = json.loads((base / "registration.json").read_text())
    kg1_intake.apply_registration(store, reg)
    for snap in sorted(base.glob("*_snapshot")):
        if snap.name == "estate_snapshot":
            continue
        pack = json.loads((snap / "manifest.json").read_text()) \
            .get("source_pack_version", "")
        inbound.receive_extract(store, reg,
                                kg1_intake.load_snapshot(snap),
                                known_packs={pack})
    inbound.receive_estate(store, reg, base / "estate_snapshot")
    return store


def make_handler(store, estate: str):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 — http.server's contract
            params = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            q = (params.get("q") or [""])[0]
            answer = ""
            if q.strip():
                result = ask.ask(
                    store, q, author="person:console",
                    occurred_at=datetime.datetime.now(
                        datetime.timezone.utc).isoformat())
                answer = (f"<p class=meta>op: {result['op']} · "
                          f"outcome: {result['outcome']}</p>"
                          f"<pre>{html.escape(result['answer'])}</pre>")
            body = _PAGE.format(estate=html.escape(estate),
                                q=html.escape(q), answer=answer)
            data = body.encode()
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):  # quiet
            pass
    return Handler


def main() -> None:
    estate = sys.argv[1] if len(sys.argv) > 1 else "sepsis"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8377
    print(f"building the {estate} graph …")
    store = build_store(estate)
    server = HTTPServer(("127.0.0.1", port),
                        make_handler(store, estate))
    print(f"ask the graph: http://127.0.0.1:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
