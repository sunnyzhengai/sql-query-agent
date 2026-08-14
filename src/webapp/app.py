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

import json as _json

from src.orchestrator.agent import Turn, run_turn
from src.orchestrator.events import FeedbackEvent, TurnEvent, decision_shape
from src.orchestrator.protocol import (
    ProtocolSession,
    caption_turn,
    execute_confirmed,
    propose_turn,
)
from src.orchestrator.tools import Session

MAX_CONVERSATIONS = 500          # in-memory cap; oldest evicted
MAX_TURNS_PER_CONVERSATION = 60


@dataclass
class Conversation:
    history: "list[dict]" = field(default_factory=list)
    session: Session = field(default_factory=Session)
    protocol: ProtocolSession = field(default_factory=ProtocolSession)
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

    @app.get("/favicon.ico")
    def favicon():
        from fastapi.responses import Response
        return Response(status_code=204)

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
        try:
            turn: Turn = run_turn(conv.history, message, chat_api, run_kql,
                                  conv.session)
        except Exception as e:                 # noqa: BLE001 — surface layer
            return JSONResponse(
                {"error": ("The assistant is temporarily unavailable "
                           f"({type(e).__name__}). Check that the data "
                           "platform and AI endpoint are running, then "
                           "try again."),
                 "conversation_id": conv_id}, status_code=502)
        turn_index = conv.turns
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
            conversation_id=conv_id, turn_index=turn_index,
            decision=decision_shape(turn.trace, turn.answer),
            trace=tuple(
                {"tool": t["tool"], "args": t["args"],
                 "result": _json.dumps(t["result"])[:1500]}
                for t in turn.trace),
        ))
        return JSONResponse({"conversation_id": conv_id,
                             "turn_index": turn_index,
                             "answer": turn.answer, "basis": turn.basis})

    @app.post("/api/feedback")
    async def feedback(request: Request) -> JSONResponse:
        body = await request.json()
        verdict = str(body.get("verdict", ""))
        if verdict not in ("helpful", "not_helpful"):
            return JSONResponse({"error": "verdict must be helpful or "
                                 "not_helpful"}, status_code=400)
        sink.record(FeedbackEvent(
            event_at=datetime.now(timezone.utc).isoformat(),
            user_id=_user_from(request),
            conversation_id=str(body.get("conversation_id", "")),
            turn_index=int(body.get("turn_index", 0)),
            verdict=verdict,
            comment=str(body.get("comment", ""))[:2000],
        ))
        return JSONResponse({"recorded": True})

    # ---- the plan protocol (ADR 0036) -------------------------------

    @app.post("/api/plan")
    async def plan(request: Request) -> JSONResponse:
        """Interpret only — returns the plan for CONFIRMATION. Nothing
        executes here; that separation is structural (the protocol has
        no execution path from this call)."""
        body = await request.json()
        message = str(body.get("message", "")).strip()
        if not message:
            return JSONResponse({"error": "empty message"}, status_code=400)
        user = _user_from(request)
        conv_id = str(body.get("conversation_id") or uuid.uuid4())
        conv = _conversation(user, conv_id)
        try:
            proposed = propose_turn(conv.protocol, message, chat_api)
        except Exception as e:                 # noqa: BLE001
            return JSONResponse(
                {"error": f"planner unavailable ({type(e).__name__})",
                 "conversation_id": conv_id}, status_code=502)
        return JSONResponse({"conversation_id": conv_id,
                             "plan": proposed})

    @app.post("/api/execute")
    async def execute(request: Request) -> JSONResponse:
        """Execute a HUMAN-CONFIRMED (possibly edited) plan, display
        results, caption them. The plan arrives as data from the
        confirming surface — the only path to execution."""
        body = await request.json()
        user = _user_from(request)
        conv_id = str(body.get("conversation_id") or "")
        confirmed = body.get("plan") or {}
        if not conv_id or not confirmed.get("components"):
            return JSONResponse({"error": "conversation_id and a plan "
                                 "with components are required"},
                                status_code=400)
        conv = _conversation(user, conv_id)
        turn_index = conv.turns
        outputs = execute_confirmed(conv.protocol, confirmed, run_kql)
        try:
            cap = caption_turn(conv.protocol, outputs, chat_api)
        except Exception as e:                 # noqa: BLE001
            cap = {"caption": f"(caption unavailable: {type(e).__name__} "
                              "— the results above are complete)",
                   "caption_inputs": [], "suggestions": []}
        trace = [{"tool": o["component"]["op"],
                  "args": o["component"]["params"],
                  "result": (o.get("result") or {"error": o.get("error")})}
                 for o in outputs]
        sink.record(TurnEvent(
            event_at=datetime.now(timezone.utc).isoformat(),
            user_id=user,
            question=str(body.get("question", ""))[:500],
            tools_used=tuple(t["tool"] for t in trace),
            ids_read=tuple(sorted({
                str(i) for t in trace if t["tool"] == "retrieve"
                for i in t["args"].get("ids", [])})),
            basis="; ".join(
                f"{t['tool']}({_json.dumps(t['args'])[:80]})"
                for t in trace),
            answered=any("result" in o for o in outputs),
            conversation_id=conv_id, turn_index=turn_index,
            decision=decision_shape(trace, cap.get("caption", "")),
            trace=tuple(
                {"tool": t["tool"], "args": t["args"],
                 "result": _json.dumps(t["result"])[:1500]}
                for t in trace),
        ))
        conv.turns += 1
        return JSONResponse({"conversation_id": conv_id,
                             "turn_index": turn_index,
                             "outputs": outputs, **cap})

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
  .fb { margin-top:6px; }
  .fb button { background:none; border:1px solid var(--line);
               color:#6b7080; padding:2px 10px; border-radius:6px;
               margin-right:6px; cursor:pointer; font-size:13px; }
  .fb button.done { border-color:var(--accent); color:var(--accent); }
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
        '<div class="basis">Basis: ' + esc(j.basis) + '</div>' +
        '<div class="fb">' +
        '<button onclick="fb(this,' + j.turn_index + ',\\'helpful\\')">' +
        '&#128077; helpful</button>' +
        '<button onclick="fb(this,' + j.turn_index +
        ',\\'not_helpful\\')">&#128078; not what I needed</button></div>';
    }
  } catch (err) { w.textContent = 'network error: ' + err; }
  button.disabled = false; input.focus();
});
async function fb(btn, turnIndex, verdict) {
  await fetch('/api/feedback', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({conversation_id: conversationId,
                          turn_index: turnIndex, verdict})});
  btn.parentElement.querySelectorAll('button')
     .forEach(b => b.classList.remove('done'));
  btn.classList.add('done');
}
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
