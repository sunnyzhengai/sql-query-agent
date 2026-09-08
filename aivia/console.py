"""The ask-the-graph console (ADR 0079 + the nine-law dig).
THE SEATS (L1 rights table): the INTERPRETER proposes (below),
the RANKER embeds (make_embedder), the SCRIBE (description
drafting) does not run at ask time, the SMOOTHER is deferred.
Seats never write; flows record events; human acts create truth.

Free questions
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
from aivia.graph import kg1_intake, kg3_artifacts, phi_gate
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
 #wrap { display: flex; gap: 1.2rem; }
 #main { flex: 3; min-width: 0; }
 #table { flex: 1; border-left: 1px solid #e4e4e0;
          padding-left: .8rem; font-size: .85rem; color: #555;
          max-width: 16rem; }
 #table h4 { margin: .2rem 0; }
</style>
<h2>Ask the graph <span class=meta>(__ESTATE__ — __COVERAGE__)
</span></h2>
<p class=meta>The conversation surface: rounds append below; follow
up with 'it', 'those', 'the first one' — they mean what the last
answer showed. UNDERSTAND (caged interpreter) · GROUND (meaning
embeddings) · CONNECT (the graph's own edges) · SPEAK (floors) ·
STEER (buttons) · REMEMBER (confirmed interpretations skip the
model). Ambiguity and no-match are honest outcomes.</p>
<div id="wrap"><div id="main"><div id="log"></div></div>
<div id="table"><h4>the table</h4>
<div id="tbody"><p class=meta>nothing yet — ask something.</p></div>
<p class=meta><a href="#" id="cleartable">clear the table</a></p>
</div></div>
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
    if (j.table) renderTable(j.table);
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
  if (p.get('q') || p.get('entity') || p.get('label')) {
    e.preventDefault();
    round(p);
  }
});
// L5-D3: the visible table — top round expanded, older collapsed
function renderTable(stack) {
  const tb = document.getElementById('tbody');
  tb.innerHTML = '';
  stack.forEach((round, i) => {
    const d = document.createElement('details');
    if (i === 0) d.open = true;
    const sm = document.createElement('summary');
    sm.textContent = (i === 0 ? 'this round' : 'round -' + i)
      + ' (' + round.length + ')';
    d.appendChild(sm);
    round.slice(0, 12).forEach(id => {
      const a = document.createElement('a');
      a.href = '/?q=' + encodeURIComponent(id);
      a.textContent = id.split('::').pop().split('|').pop();
      const line = document.createElement('div');
      line.appendChild(a);
      d.appendChild(line);
    });
    tb.appendChild(d);
  });
  if (!stack.length)
    tb.innerHTML = '<p class=meta>nothing yet.</p>';
}
document.getElementById('cleartable')
  .addEventListener('click', (e) => {
    e.preventDefault();
    round(new URLSearchParams({ clear: '1' }));
    renderTable([]);
  });
// L9-D2: the census is the front door — the estate introduces itself
round(new URLSearchParams({ card: 'estate' }));
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


def interpreter_prompt():
    """The Interpreter's prompt IS registry law (Seat_Prompts,
    v1.26.0) — versioned; editing it is a registry bump. Returns
    (text, version)."""
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Seat_Prompts"]
    row = next(r for r in sheet if r["Seat"] == "interpreter")
    return row["Prompt"], row["Version"]


def make_interpreter(key: str, cache_path=None):
    """THE INTERPRETER seat: reads nothing, writes nothing — one
    question in, one typed PROPOSAL out. The proposal cache keys on
    (question, model, PROMPT VERSION): a prompt fix reaches every
    already-asked question (the change-quanta law — a prompt is a
    rule)."""
    prompt, prompt_version = interpreter_prompt()
    cache = {}
    if cache_path and cache_path.is_file():
        cache = json.loads(cache_path.read_text())

    def interpret(question: str):
        ck = (f"{' '.join(question.split()).lower()}|"
              f"{INTERPRETER_MODEL}|{prompt_version}")
        if ck in cache:
            return cache[ck]
        out = _openai("chat/completions", {
            "model": INTERPRETER_MODEL, "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": prompt},
                         {"role": "user", "content": question}],
            "max_tokens": 300}, key)
        raw = json.loads(out["choices"][0]["message"]["content"])
        cache[ck] = raw
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache))
        return raw
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


def make_handler(store, estate, interpret_fn, semantic, pending,
                 coverage: str = ""):
    seat_failures = {"count": 0}  # the visible ops counter
    contexts = {}  # L5-D1: a STACK of context sets per conversation
    # (newest first, bounded TABLE_DEPTH); two conversations never
    # share
    last_clarify = {}  # L3-D3: conv -> candidate ids of the last
    # clarify, for the miss counter (picked / re-typed)
    TABLE_DEPTH = int(ask.response_shapes()["TABLE_DEPTH"])

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
                if t.get("tier") == "table":
                    bit = (f"'{t['mention']}' — from the table: "
                           f"{t.get('hits', 0)} thing(s)")
                else:
                    bit = (f"'{t['mention']}' — searched as: "
                           f"{t.get('searched_as', t['mention'])} "
                           f"→ {t.get('hits', 0)} hit(s)")
                if t.get("seat_down"):
                    bit += " · ranker seat down"
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
        if result.get("resolved_to_confirmed"):
            parts.append(
                "<p class=meta>resolved to a meaning you confirmed "
                f"on {html.escape(str(result['resolved_to_confirmed'])[:10])}"
                "</p>")
        if result["status"] == "answer":
            if result.get("pending_confirmation"):
                # L7-D2: inline, non-blocking — the answer ships,
                # confirming blesses the boundary artifact
                pending[(conv, ask._fold(" ".join(q.split())))] = (
                    result["interpretation"],
                    list((contexts.get(conv) or [[]])[0]))
                href = "/?q=" + urllib.parse.quote(q) + "&accept=1"
                reads = []
                for m, k in (result["interpretation"].get("kinds")
                             or {}).items():
                    reads.append(f"{m} → {k}")
                parts.append(
                    '<p class=meta>✓ I read it as: '
                    + html.escape("; ".join(
                        reads or result["interpretation"]["mentions"]))
                    + f' — <a href="{href}">confirm</a> '
                    "(or rephrase)</p>")
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
                    f'<a href="/round?entity='
                    f'{urllib.parse.quote(i)}">'
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
                href = ("/round?entity="
                        + urllib.parse.quote(c["identity"]))
                score = (f" · {c['score']}" if "score" in c else "")
                places = (f" (in {c['places']} places)"
                          if c.get("places", 1) > 1 else "")
                speech = (c.get("words") or "")[:70]
                parts.append(
                    f'<li><a href="{href}">[{html.escape(c["kind"])}] '
                    f"{html.escape(c['name'])}{places}{score}</a>"
                    + (f" <span class=meta>{html.escape(speech)}"
                       "</span>" if speech else "") + "</li>")
            parts.append("</ul>")
            if result.get("more_candidates"):
                parts.append(f"<p class=meta>… and "
                             f"{result['more_candidates']} more — "
                             "narrow by kind?</p>")
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
        if (params.get("clear") or [""])[0] == "1":
            contexts.pop(conv, None)  # L5-D3: an explicit user act
            return {"status": "cleared", "html":
                    "<p class=meta>the table is cleared.</p>",
                    "context_set": []}
        if (params.get("card") or [""])[0] == "estate":
            # L9-D2: the census IS the front door
            index = ask.build_index(read)
            kinds = {}
            for e in index:
                kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
            lines = [f"This estate ({estate}):"]
            for k in sorted(kinds, key=lambda k: -kinds[k]):
                lines.append(f"- {kinds[k]} {k}(s)")
            lines.append("Ask about anything above by name or "
                         "meaning; honest zeros and clarifies are "
                         "real answers. Follow up with 'it' / "
                         "'those' / 'the first one'.")
            return {"status": "answer",
                    "html": "<pre>" + html.escape("\n".join(lines))
                            + "</pre>",
                    "context_set": []}
        label = (params.get("label") or [""])[0]
        if label:
            # STEP A: a label-group click is STEER — list the
            # members directly, no model, no search
            index = ask.build_index(read)
            members = [e for e in index if e["kind"] == label]
            lines = [f"{len(members)} {label}(s):"]
            for e in sorted(members,
                            key=lambda e: e["name"])[:60]:
                lines.append(f"- {e['name']}  ({e['identity']})")
            if len(members) > 60:
                lines.append(f"… and {len(members) - 60} more")
            ids = [e["identity"] for e in members][:100]
            stack = contexts.get(conv) or []
            stack.insert(0, ids)
            contexts[conv] = stack[:TABLE_DEPTH]
            refs = " · ".join(
                f'<a href="/round?entity={urllib.parse.quote(i)}">'
                f"{html.escape(i.split('::')[-1].split('|')[-1])}"
                "</a>" for i in ids[:12])
            return {"status": "answer",
                    "html": "<pre>" + html.escape("\n".join(lines))
                            + "</pre><p class=meta>Referenced: "
                            + refs + "</p>",
                    "context_set": ids,
                    "table": contexts.get(conv) or []}
        if entity_id and not mode:
            # STEP A: an entity click is STEER — the card directly,
            # no model; lands on the table
            index = ask.build_index(read)
            entity = next((e for e in index
                           if e["identity"] == entity_id), None)
            if entity is None:
                return {"status": "answer",
                        "html": "<pre>gone</pre>",
                        "context_set": []}
            adj = connect.build_adjacency(read)
            card = ask.render_card(read, entity)
            hood = connect.neighborhood(adj, entity["identity"])
            listed = [entity["identity"]]
            for members in hood.values():
                listed += [m for m in members if m not in listed]
            listed = listed[:100]
            stack = contexts.get(conv) or []
            stack.insert(0, listed)
            contexts[conv] = stack[:TABLE_DEPTH]
            links = " ".join(
                f'<a href="/round?entity='
                f'{urllib.parse.quote(entity_id)}&mode={m}">'
                f"{m}</a>" for m in ask.DISPLAY_MODES)
            refs = " · ".join(
                f'<a href="/round?entity={urllib.parse.quote(i)}">'
                f"{html.escape(i.split('::')[-1].split('|')[-1])}"
                "</a>" for i in listed[:12])
            return {"status": "answer",
                    "html": "<pre>" + html.escape(card)
                            + f"</pre><p class=modes>views: {links}"
                            "</p><p class=meta>Referenced: "
                            + refs + "</p>",
                    "context_set": listed,
                    "table": contexts.get(conv) or []}
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
        # L3-D3 the clarify-miss counter: what happened after the
        # last clarify — picked one of its rows, or re-typed?
        pend_clar = last_clarify.pop(conv, None)
        if pend_clar and q.strip():
            action = ("picked" if q.strip() in pend_clar
                      else "retyped")
            kg3_artifacts.append_usage(
                store, action=f"clarify-{action}",
                author="person:console", occurred_at=_now(),
                payload=phi_gate.door1_redact(q).text)
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
        if result["status"] == "answer" \
                and result.get("context_set"):
            # L5-D1: the new round lands on TOP of the stack
            stack = contexts.get(conv) or []
            stack.insert(0, result["context_set"])
            contexts[conv] = stack[:TABLE_DEPTH]
        if result["status"] == "clarify":
            last_clarify[conv] = {c["identity"] for c in
                                  result.get("candidates", [])}
        top = (contexts.get(conv) or [[]])[0]
        return {"status": result["status"],
                "html": render_result(conv, q, result),
                "context_set": top,
                "table": contexts.get(conv) or []}

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
            page = (_PAGE
                    .replace("__ESTATE__", html.escape(estate))
                    .replace("__COVERAGE__", html.escape(coverage)))
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
    interpret_fn = (make_interpreter(
        key, cache_path=base / ".cache" / "proposals.json")
        if key else None)
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
    kinds_count = {}
    for e in entries:
        kinds_count[e["kind"]] = kinds_count.get(e["kind"], 0) + 1
    coverage = (f"{kinds_count.get('file', 0)} files · "
                f"{kinds_count.get('table', 0)} tables · "
                f"{kinds_count.get('column', 0)} columns")
    server = ThreadingHTTPServer(("127.0.0.1", port),
                                 make_handler(store, estate,
                                              interpret_fn, semantic,
                                              {}, coverage))
    print(f"ask the graph: http://127.0.0.1:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
