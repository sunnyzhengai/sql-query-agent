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

INTERPRETER_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

_PAGE = """<!doctype html><meta charset="utf-8">
<title>AIVIA — ask the graph</title>
<style>
 body { font: 15px/1.5 -apple-system, sans-serif; margin: 0 auto;
        max-width: 62rem; color: #222; padding: 1rem 1rem 6rem; }
 input { width: 100%; font-size: 1.1rem; padding: .5rem;
         border: 1px solid #bbb; border-radius: 4px; }
 pre { background: #f6f6f6; padding: 1rem; white-space: pre-wrap; }
 .meta { color: #777; font-size: .85rem; }
 .modes a { margin-right: .8rem; }
 .round { border-top: 1px solid #e4e4e0; padding-top: .6rem;
          margin-top: .8rem; }
 .you { color: #2b5db9; font-weight: 600; }
 #composer { position: fixed; bottom: 0; left: 0; right: 0;
             background: #fffffff2; border-top: 1px solid #ddd;
             padding: .7rem 1rem; }
 #composer form { max-width: 62rem; margin: 0 auto; }
</style>
<h2>Ask the graph <span class=meta>(__ESTATE__)</span></h2>
<p class=meta>The conversation surface: rounds append below; follow
up with 'it', 'those', 'the first one' — they mean what the last
answer showed. UNDERSTAND (caged interpreter) · GROUND (meaning
embeddings) · CONNECT (the graph's own edges) · SPEAK (floors) ·
STEER (buttons) · REMEMBER (confirmed interpretations skip the
model). Ambiguity and no-match are honest outcomes.</p>
<div id="log"></div>
<div id="composer"><form id="ask">
 <input id="q" placeholder="ask anything — the interpreter
 understands, the graph answers" autofocus autocomplete="off">
</form></div>
<script>
// One conversation per page load: the id scopes the context set
// server-side (two tabs never share; ADR 0079 Law 4 surface).
const conv = (crypto.randomUUID && crypto.randomUUID())
  || String(Math.random()).slice(2);
const log = document.getElementById('log');
const q = document.getElementById('q');
function esc(t) { const d = document.createElement('span');
  d.textContent = t; return d.innerHTML; }
function append(html) {
  const d = document.createElement('div');
  d.className = 'round'; d.innerHTML = html;
  log.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}
async function round(params) {
  params.set('c', conv);
  if (params.get('q'))
    append('<p class="you">' + esc(params.get('q')) + '</p>');
  try {
    const r = await fetch('/round?' + params.toString());
    const j = await r.json();
    append(j.html);
  } catch (err) {
    append('<p class=meta>round failed (' + esc(String(err)) +
           ') — the server may be restarting; ask again.</p>');
  }
}
document.getElementById('ask').addEventListener('submit', (e) => {
  e.preventDefault();
  const text = q.value.trim();
  if (!text) return;
  q.value = '';                       // the box clears and stays
  round(new URLSearchParams({ q: text }));
});
// links inside rounds (candidates, Referenced, display modes,
// confirm) stay IN the conversation: intercept and fetch
log.addEventListener('click', (e) => {
  const a = e.target.closest('a');
  if (!a) return;
  const u = new URL(a.href, location.origin);
  const p = u.searchParams;
  if (p.get('q') || p.get('entity')) {
    e.preventDefault();
    round(p);
  }
});
// legacy deep links (/?q=...) enter the conversation as round one
const boot = new URLSearchParams(location.search);
if (boot.get('q')) round(new URLSearchParams({ q: boot.get('q') }));
</script>
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
    contexts = {}  # Law 4 surface: CONTEXT SET per conversation id —
    # 'it', 'those', ordinals resolve against the conversation's own
    # last answer; two conversations never share

    def render_result(conv, q, result):
        parts = [f"<p class=meta>status: {result['status']}"
                 + (f" · via: {result['via']}"
                    if result.get("via") else "") + "</p>"]
        # ADR 0080 rider: the TRACE renders in every round —
        # plan-confirm-execute-display applied to search; always-on
        # (later suppression is a toggle, never a removal)
        if result.get("trace"):
            rows = []
            for t in result["trace"]:
                bit = (f"'{t['mention']}' → {t['tier']}/"
                       f"{t['outcome']}")
                if t.get("score") is not None:
                    bit += f" · {t['score']}"
                if t.get("expansions_tried"):
                    bit += (" · searched as: "
                            + " | ".join(t["expansions_tried"]))
                rows.append(html.escape(bit))
            parts.append("<p class=meta>searched: "
                         + " &nbsp;·&nbsp; ".join(rows) + "</p>")
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
            context = result.get("context_set") or []
            if context:
                refs = " · ".join(
                    f'<a href="/?q={urllib.parse.quote(i)}">'
                    f"{html.escape(i.split('::')[-1].split('|')[-1])}"
                    "</a>" for i in context[:12])
                more = (f" … ({len(context) - 12} more in context)"
                        if len(context) > 12 else "")
                parts.append(
                    f"<p class=meta>Referenced: {refs}{more}</p>")
        elif result["status"] == "confirm":
            grounded = []
            for g in result["groundings"]:
                what = (g["entity"]["name"]
                        if g.get("outcome") == "matched"
                        else f"kind:{g['kind']}"
                        if g.get("outcome") == "kind"
                        else f"set:{len(g.get('entities', []))} from "
                             "context"
                        if g.get("outcome") == "set"
                        else f"topic:'{g['mention']}'")
                grounded.append(f"{g['mention']} → {what}")
            pending[(conv, ask._fold(" ".join(q.split())))] = (
                result["interpretation"],
                list(contexts.get(conv) or []))
            href = "/?q=" + urllib.parse.quote(q) + "&accept=1"
            parts.append(
                "<p>I understood: <b>"
                + html.escape("; ".join(grounded))
                + f'</b></p><p><a href="{href}">Confirm — remember '
                "this and answer</a> (or rephrase below)</p>")
        elif result["status"] == "clarify" \
                and not result.get("candidates"):
            # Law 4: a context clarify — the anaphor had nothing (or
            # not enough) to refer back to; honest, never a guess
            parts.append(f"<p>'{html.escape(result['mention'])}' — "
                         f"{html.escape(result.get('reason', ''))}"
                         "</p>")
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

    def run_round(params):
        """One round -> the JSON the client appends (CS-2: the round
        is DATA; the transcript is the client's display memory)."""
        conv = (params.get("c") or [""])[0]
        q = (params.get("q") or [""])[0]
        entity_id = (params.get("entity") or [""])[0]
        mode = (params.get("mode") or [""])[0]
        read = ReadApi(store)
        if entity_id and mode in ask.DISPLAY_MODES:
            index = ask.build_index(read)
            entity = next((e for e in index
                           if e["identity"] == entity_id), None)
            adj = connect.build_adjacency(read)
            if entity is None:
                text = "gone"
            elif mode == "card":
                text = ask.render_card(read, entity)
            elif mode == "lineage":
                text = ask.render_lineage(read, adj, entity)
            elif mode == "filters":
                text = ask.render_filters(read, entity)
            elif mode == "readers":
                text = ask.render_readers(read, adj, entity)
            else:
                text = ask.render_census(read)
            return {"status": "answer",
                    "html": f"<pre>{html.escape(text)}</pre>",
                    "context_set": contexts.get(conv) or []}
        if not q.strip():
            return {"status": "empty", "html": "", "context_set": []}
        ctx = contexts.get(conv) or None
        if (params.get("accept") or [""])[0] == "1":
            held = pending.pop(
                (conv, ask._fold(" ".join(q.split()))), None)
            if held:
                interp, snap = held
                result = ask.confirm(
                    store, q, interp, "person:console", _now(),
                    semantic=semantic,
                    basis=f"model:{INTERPRETER_MODEL}",
                    context=snap or None)
            else:
                result = ask.ask(store, q, "person:console", _now(),
                                 interpret_fn, semantic, context=ctx)
        else:
            result = ask.ask(store, q, "person:console", _now(),
                             interpret_fn, semantic, context=ctx)
        if result["status"] == "answer":
            # the conversation's context advances ONLY on an answer
            contexts[conv] = result.get("context_set") or []
        return {"status": result["status"],
                "html": render_result(conv, q, result),
                "context_set": contexts.get(conv) or []}

    class Handler(BaseHTTPRequestHandler):
        def _send(self, data, ctype):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802 — http.server's contract
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if parsed.path == "/round":
                self._send(json.dumps(run_round(params)).encode(),
                           "application/json; charset=utf-8")
                return
            page = _PAGE.replace("__ESTATE__", html.escape(estate))
            self._send(page.encode(), "text/html; charset=utf-8")

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
    entries = ask.build_index(read)
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
