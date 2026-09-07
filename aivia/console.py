"""The ask-the-graph console, Tier A (ADR 0079) — free questions
through the caged interpreter, grounding through the semantic index,
answers from the connecting graph, display modes as buttons. The
keyword grammar is gone (the never-regex law). Real model seats wire
HERE and only here: gpt-4o-mini interprets (mentions out, validated),
text-embedding-3-small grounds — keys from .env, demo-boundary only;
production swaps to the customer's Azure OpenAI by config.

Usage: python3.11 -m aivia.console [estate] [port]
"""
import datetime
import html
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aivia.flows import ask, connect, grounding, inbound
from aivia.graph import kg1_intake
from aivia.graph.read_api import ReadApi
from aivia.lenses import ask_index

INTERPRETER_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

_PAGE = """<!doctype html><meta charset="utf-8">
<title>AIVIA — ask the graph</title>
<style>
 body {{ font: 15px/1.5 -apple-system, sans-serif; margin: 2rem auto;
        max-width: 62rem; color: #222; }}
 input {{ width: 100%; font-size: 1.1rem; padding: .5rem; }}
 pre {{ background: #f6f6f6; padding: 1rem; white-space: pre-wrap; }}
 .meta {{ color: #777; font-size: .85rem; }}
 .modes a {{ margin-right: .8rem; }}
</style>
<h2>Ask the graph <span class=meta>({estate})</span></h2>
<form method=get action=/>
 <input name=q value="{q}" placeholder="ask anything — the
 interpreter understands, the graph answers" autofocus>
</form>
{body}
<p class=meta>UNDERSTAND (caged interpreter) · GROUND (meaning
embeddings) · CONNECT (the graph's own edges) · SPEAK (floors) ·
STEER (buttons) · REMEMBER (confirmed interpretations skip the
model). Ambiguity and no-match are honest outcomes.</p>
"""


def _env_key() -> str:
    env = pathlib.Path(__file__).resolve().parents[1] / ".env"
    if env.is_file():
        for line in env.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("OPENAI_API_KEY", "").strip()


SEAT_BUDGET_SECONDS = 20  # the declared time budget (seat-failure law)


def _openai(path: str, payload: dict, key: str) -> dict:
    """One bounded retry inside the budget; a second failure raises —
    and the callers turn that into a seat_down OUTCOME, never a dead
    page (ADR 0079 Law 3)."""
    req = urllib.request.Request(
        f"https://api.openai.com/v1/{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    last = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(
                    req, timeout=SEAT_BUDGET_SECONDS) as r:
                return json.load(r)
        except Exception as err:  # noqa: BLE001 — bounded retry, then
            last = err            # the containment layer takes over
    raise last


def make_interpreter(key: str):
    prompt = (
        "You translate a question about a SQL estate into MENTIONS — "
        "the entity-ish or topic phrases the question is about. "
        "Return ONLY JSON: {\"mentions\": [\"...\"]}. Rules: 1-5 "
        "mentions; keep column/table/procedure names verbatim; a "
        "kind word (tables, columns, reports, procedures, "
        "selections, metrics, terms, drift) is itself a mention; a "
        "topic (like a disease or subject) is a mention. Never "
        "answer the question; never invent names.")

    def interpret(question: str):
        out = _openai("chat/completions", {
            "model": INTERPRETER_MODEL, "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": prompt},
                         {"role": "user", "content": question}],
            "max_tokens": 200}, key)
        return json.loads(out["choices"][0]["message"]["content"])
    return interpret


def make_embedder(key: str):
    def embed(texts):
        vectors = []
        for i in range(0, len(texts), 512):
            out = _openai("embeddings",
                          {"model": EMBEDDING_MODEL,
                           "input": texts[i:i + 512]}, key)
            vectors += [d["embedding"] for d in out["data"]]
        return vectors
    return embed


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
    return store, base


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def make_handler(store, estate, interpret_fn, semantic, pending):
    seat_failures = {"count": 0}  # the visible ops counter

    def render_result(q, result):
        parts = [f"<p class=meta>status: {result['status']}"
                 + (f" · via: {result['via']}"
                    if result.get("via") else "") + "</p>"]
        if result.get("seat_down"):
            seat_failures["count"] += 1
            parts.append(
                '<p style="background:#fff3cd;padding:.5rem">'
                "⚠ interpreter seat unavailable "
                f"(failure #{seat_failures['count']} this session) — "
                "exact names, identities and kind words still "
                "answer.</p>")
        if result["status"] == "answer":
            parts.append(f"<pre>{html.escape(result['answer'])}</pre>")
            matched = [g["entity"] for g in
                       result.get("groundings", [])
                       if g.get("outcome") == "matched"]
            if len(matched) == 1:
                identity = matched[0]["identity"]
                links = " ".join(
                    f'<a href="/?entity='
                    f'{urllib.parse.quote(identity)}&mode={m}">'
                    f"{m}</a>" for m in ask.DISPLAY_MODES)
                parts.append(f'<p class=modes>Display: {links}</p>')
        elif result["status"] == "confirm":
            mentions = result["interpretation"]["mentions"]
            grounded = []
            for g in result["groundings"]:
                what = (g["entity"]["name"]
                        if g.get("outcome") == "matched"
                        else f"kind:{g['kind']}"
                        if g.get("outcome") == "kind"
                        else f"topic:'{g['mention']}'")
                grounded.append(f"{g['mention']} → {what}")
            pending[ask._fold(" ".join(q.split()))] = \
                result["interpretation"]
            href = "/?q=" + urllib.parse.quote(q) + "&accept=1"
            parts.append(
                "<p>I understood: <b>"
                + html.escape("; ".join(grounded))
                + f'</b></p><p><a href="{href}">Confirm — remember '
                "this and answer</a> (or rephrase above)</p>")
        elif result["status"] == "clarify":
            parts.append(f"<p>'{html.escape(result['mention'])}' is "
                         "ambiguous — pick one:</p><ul>")
            for c in result["candidates"]:
                href = "/?q=" + urllib.parse.quote(c["identity"])
                score = (f" · {c['score']}" if "score" in c else "")
                parts.append(
                    f'<li><a href="{href}">[{html.escape(c["kind"])}] '
                    f"{html.escape(c['name'])} — "
                    f"{html.escape(c['identity'])}{score}</a></li>")
            parts.append("</ul>")
        else:
            parts.append(f"<pre>{html.escape(result['answer'])}</pre>")
        return "".join(parts)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 — http.server's contract
            params = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            q = (params.get("q") or [""])[0]
            entity_id = (params.get("entity") or [""])[0]
            mode = (params.get("mode") or [""])[0]
            body = ""
            read = ReadApi(store)
            if entity_id and mode in ask.DISPLAY_MODES:
                index = ask_index.lens_ask_index(read, None)["yield"]
                entity = next((e for e in index
                               if e["identity"] == entity_id), None)
                adj = connect.build_adjacency(read)
                if entity is None:
                    body = "<pre>gone</pre>"
                elif mode == "card":
                    body = f"<pre>{html.escape(ask.render_card(read, entity))}</pre>"
                elif mode == "lineage":
                    body = f"<pre>{html.escape(ask.render_lineage(read, adj, entity))}</pre>"
                elif mode == "filters":
                    body = f"<pre>{html.escape(ask.render_filters(read, entity))}</pre>"
                elif mode == "readers":
                    body = f"<pre>{html.escape(ask.render_readers(read, adj, entity))}</pre>"
                elif mode == "census":
                    body = f"<pre>{html.escape(ask.render_census(read))}</pre>"
            elif q.strip():
                if (params.get("accept") or [""])[0] == "1":
                    interp = pending.get(
                        ask._fold(" ".join(q.split())))
                    if interp:
                        result = ask.confirm(
                            store, q, interp, "person:console",
                            _now(), semantic=semantic,
                            basis=f"model:{INTERPRETER_MODEL}")
                    else:
                        result = ask.ask(store, q, "person:console",
                                         _now(), interpret_fn,
                                         semantic)
                else:
                    result = ask.ask(store, q, "person:console",
                                     _now(), interpret_fn, semantic)
                body = render_result(q, result)
            page = _PAGE.format(estate=html.escape(estate),
                                q=html.escape(q), body=body)
            data = page.encode()
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass
    return Handler


def main() -> None:
    estate = sys.argv[1] if len(sys.argv) > 1 else "sepsis"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8377
    key = _env_key()
    print(f"building the {estate} graph …")
    store, base = build_store(estate)
    read = ReadApi(store)
    entries = ask_index.lens_ask_index(read, None)["yield"]
    interpret_fn = make_interpreter(key) if key else None
    semantic = None
    if key:
        print(f"grounding index: embedding {len(entries)} meanings "
              "(cached by content — only changed meanings re-embed) …")
        try:
            semantic = grounding.SemanticIndex(
                entries, make_embedder(key), EMBEDDING_MODEL,
                cache_path=base / ".cache" / "embeddings.json")
            print(f"  embedded now: {semantic.embedded_now}; "
                  f"cached: {len(entries) - semantic.embedded_now}")
        except Exception as err:  # noqa: BLE001 — seat-failure law:
            print(f"  EMBED SEAT DOWN at boot ({err}) — continuing "
                  "with deterministic tiers only")
            semantic = None
    else:
        print("no OPENAI_API_KEY — deterministic tiers only")
    # concurrent serving (seat-failure law): a slow seat call never
    # blocks deterministic asks
    server = ThreadingHTTPServer(("127.0.0.1", port),
                                 make_handler(store, estate,
                                              interpret_fn, semantic,
                                              {}))
    print(f"ask the graph: http://127.0.0.1:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
