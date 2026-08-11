"""The AIVIA web app: chat surface + marketplace fulfillment, one host.

Everything is injected (chat_api, run_kql, sink, marketplace deps), so
the whole app is offline-testable with FastAPI's TestClient; the
production factory (main.py) wires live pieces.

Identity: App Service Easy Auth forwards the signed-in user as
X-MS-CLIENT-PRINCIPAL-NAME — per-user identity for the flywheel with
zero auth code here (the platform owns sign-in). Local dev: "local-dev".

Conversation state lives in memory per (user, conversation_id) — v1 of
a single-instance App Service; a store-backed session is the scale-out
follow-up, not a v1 concern.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from src.orchestrator.agent import Turn, run_turn
from src.orchestrator.events import TurnEvent
from src.orchestrator.tools import Session

MAX_CONVERSATIONS = 500          # in-memory cap; oldest evicted
MAX_TURNS_PER_CONVERSATION = 60


@dataclass
class Conversation:
    history: "list[dict]" = field(default_factory=list)
    session: Session = field(default_factory=Session)
    turns: int = 0


@dataclass
class MarketplaceDeps:
    """Wired only in deployments that serve the marketplace endpoints."""
    config: object                 # marketplace_host.handlers.HostConfig
    store: object                  # SubscriptionStore
    client: object                 # MarketplaceClient
    verify_token: Callable


def _user_from(request: Request) -> str:
    return request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", "local-dev")


def create_app(
    chat_api,
    run_kql,
    sink,
    marketplace: "MarketplaceDeps | None" = None,
) -> FastAPI:
    app = FastAPI(title="AIVIA", docs_url=None, redoc_url=None)
    conversations: "dict[str, Conversation]" = {}

    def _conversation(user: str, conv_id: str) -> Conversation:
        key = f"{user}:{conv_id}"
        if key not in conversations:
            if len(conversations) >= MAX_CONVERSATIONS:
                conversations.pop(next(iter(conversations)))
            conversations[key] = Conversation()
        return conversations[key]

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return CHAT_PAGE

    @app.post("/api/chat")
    async def chat(request: Request) -> JSONResponse:
        body = await request.json()
        message = str(body.get("message", "")).strip()
        if not message:
            return JSONResponse({"error": "empty message"}, status_code=400)
        user = _user_from(request)
        conv_id = str(body.get("conversation_id") or uuid.uuid4())
        conv = _conversation(user, conv_id)
        if conv.turns >= MAX_TURNS_PER_CONVERSATION:
            return JSONResponse(
                {"error": "conversation limit reached — start a new one",
                 "conversation_id": conv_id}, status_code=409)
        turn: Turn = run_turn(conv.history, message, chat_api, run_kql,
                              conv.session)
        conv.turns += 1
        sink.record(TurnEvent(
            event_at=datetime.now(timezone.utc).isoformat(),
            user_id=user, question=message,
            tools_used=tuple(t["tool"] for t in turn.trace),
            ids_read=tuple(sorted({
                t["args"].get("id") or t["args"].get("ref")
                for t in turn.trace
                if t["tool"] in ("get_facts", "list_steps")
                and (t["args"].get("id") or t["args"].get("ref"))})),
            basis=turn.basis, answered=bool(turn.answer),
        ))
        return JSONResponse({"conversation_id": conv_id,
                             "answer": turn.answer, "basis": turn.basis})

    # ---- marketplace fulfillment (SaaS Fulfillment API v2) ----------

    def _not_configured() -> JSONResponse:
        return JSONResponse(
            {"error": "marketplace endpoints not configured"},
            status_code=503)

    @app.get("/landing", response_class=HTMLResponse)
    def landing(token: str = "") -> HTMLResponse:
        if marketplace is None:
            return HTMLResponse("marketplace not configured", status_code=503)
        from marketplace_host.handlers import handle_landing_resolve
        status, body = handle_landing_resolve(
            token, marketplace.client, marketplace.store)
        if status != 200:
            return HTMLResponse(
                f"<h1>AIVIA</h1><p>Could not resolve this purchase: "
                f"{body.get('error')}</p>", status_code=status)
        sub = body["subscription"]
        return HTMLResponse(LANDING_PAGE.format(
            plan=sub.get("plan_id") or "",
            subscription_id=sub.get("subscription_id") or "",
            purchaser=sub.get("purchaser") or ""))

    @app.post("/api/marketplace/activate")
    async def activate(request: Request) -> JSONResponse:
        if marketplace is None:
            return _not_configured()
        from marketplace_host.handlers import handle_landing_activate
        body = await request.json()
        status, out = handle_landing_activate(
            str(body.get("subscription_id", "")),
            marketplace.store, marketplace.client)
        return JSONResponse(out, status_code=status)

    @app.post("/api/marketplace/webhook")
    async def webhook(request: Request) -> JSONResponse:
        if marketplace is None:
            return _not_configured()
        from marketplace_host.handlers import handle_webhook
        payload = await request.json()
        status, out = handle_webhook(
            dict(request.headers), payload, marketplace.config,
            marketplace.store, marketplace.client,
            marketplace.verify_token)
        return JSONResponse(out, status_code=status)

    return app


CHAT_PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIVIA — certified metrics</title>
<style>
  :root { --ink:#1a1f2e; --paper:#f7f7f5; --accent:#2b5db9; --line:#e2e2de; }
  * { box-sizing:border-box; }
  body { margin:0; font:16px/1.5 -apple-system, "Segoe UI", sans-serif;
         color:var(--ink); background:var(--paper);
         display:flex; flex-direction:column; height:100vh; }
  header { padding:14px 22px; border-bottom:1px solid var(--line);
           background:#fff; font-weight:600; }
  header span { color:var(--accent); }
  #log { flex:1; overflow-y:auto; padding:22px; max-width:860px;
         width:100%; margin:0 auto; }
  .msg { margin:0 0 16px; white-space:pre-wrap; }
  .you { font-weight:600; }
  .basis { font:12px/1.4 ui-monospace, monospace; color:#6b7080;
           border-left:3px solid var(--line); padding-left:10px;
           margin-top:6px; word-break:break-all; }
  form { display:flex; gap:10px; padding:16px 22px 22px;
         max-width:860px; width:100%; margin:0 auto; }
  input { flex:1; padding:12px 14px; border:1px solid var(--line);
          border-radius:8px; font:inherit; background:#fff; }
  button { padding:12px 20px; border:0; border-radius:8px;
           background:var(--accent); color:#fff; font:inherit;
           cursor:pointer; }
  button:disabled { opacity:.5; }
  .thinking { color:#6b7080; font-style:italic; }
</style></head>
<body>
<header>AIVIA <span>·</span> ask about your certified metrics</header>
<div id="log"></div>
<form id="f"><input id="q" autocomplete="off"
  placeholder="e.g. are all definitions of Base_Pop_Severe_ED_Scores the same?">
  <button id="b">Ask</button></form>
<script>
let conversationId = null;
const log = document.getElementById('log');
const form = document.getElementById('f');
const input = document.getElementById('q');
const button = document.getElementById('b');
function add(html, cls) {
  const d = document.createElement('div');
  d.className = 'msg ' + (cls || '');
  d.innerHTML = html;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
  return d;
}
function esc(s) { const t = document.createElement('span');
  t.textContent = s; return t.innerHTML; }
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = ''; button.disabled = true;
  add('you&gt; ' + esc(message), 'you');
  const w = add('thinking…', 'thinking');
  try {
    const r = await fetch('/api/chat', { method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message, conversation_id: conversationId})});
    const j = await r.json();
    if (!r.ok) { w.textContent = j.error || ('error ' + r.status); }
    else {
      conversationId = j.conversation_id;
      w.className = 'msg';
      w.innerHTML = esc(j.answer) +
        '<div class="basis">Basis: ' + esc(j.basis) + '</div>';
    }
  } catch (err) { w.textContent = 'network error: ' + err; }
  button.disabled = false; input.focus();
});
input.focus();
</script>
</body></html>
"""

LANDING_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>AIVIA — activate</title>
<style>body{{font:16px/1.6 -apple-system,"Segoe UI",sans-serif;
max-width:640px;margin:60px auto;color:#1a1f2e;padding:0 20px}}
button{{padding:12px 24px;border:0;border-radius:8px;background:#2b5db9;
color:#fff;font:inherit;cursor:pointer}}</style></head>
<body>
<h1>AIVIA</h1>
<p>Thanks for your purchase. {purchaser}</p>
<p>Plan: <b>{plan}</b><br>Subscription: <code>{subscription_id}</code></p>
<p>Activating starts your subscription billing. Our onboarding team
will contact you to schedule installation into your Fabric tenant.</p>
<button onclick="activate()">Activate subscription</button>
<p id="out"></p>
<script>
async function activate() {{
  const r = await fetch('/api/marketplace/activate', {{method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{subscription_id:'{subscription_id}'}})}});
  const j = await r.json();
  document.getElementById('out').textContent =
    r.ok ? 'Activated — status: ' + j.status : (j.error || 'error');
}}
</script>
</body></html>
"""
