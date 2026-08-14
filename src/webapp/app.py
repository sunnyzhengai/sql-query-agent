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
        return WORKBENCH_PAGE

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


WORKBENCH_PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIVIA — certified metrics workbench</title>
<style>
  :root { --ink:#1a1f2e; --paper:#f7f7f5; --accent:#2b5db9;
          --line:#e2e2de; --ok:#1a7f4b; --warn:#b76e00; --bad:#b3261e; }
  * { box-sizing:border-box; }
  body { margin:0; font:15px/1.5 -apple-system,"Segoe UI",sans-serif;
         color:var(--ink); background:var(--paper);
         display:flex; flex-direction:column; height:100vh; }
  header { padding:12px 22px; border-bottom:1px solid var(--line);
           background:#fff; font-weight:600; }
  header span { color:var(--accent); font-weight:400; }
  #log { flex:1; overflow-y:auto; padding:18px; max-width:980px;
         width:100%; margin:0 auto; }
  .you { font-weight:600; margin:14px 0 8px; }
  .card { background:#fff; border:1px solid var(--line);
          border-radius:10px; padding:14px 16px; margin:0 0 14px; }
  .card h3 { margin:0 0 8px; font-size:13px; text-transform:uppercase;
             letter-spacing:.06em; color:#6b7080; }
  .comp { display:flex; gap:10px; align-items:flex-start;
          padding:8px 0; border-top:1px dashed var(--line); }
  .comp:first-of-type { border-top:0; }
  .comp .num { font:600 13px ui-monospace,monospace; color:var(--accent);
               padding-top:7px; min-width:22px; }
  .comp .fields { flex:1; display:flex; flex-wrap:wrap; gap:8px;
                  align-items:center; }
  .comp input[type=text], .comp textarea, .comp select {
      font:13px ui-monospace,monospace; padding:6px 8px;
      border:1px solid var(--line); border-radius:6px; background:#fff; }
  .comp input[type=text] { min-width:220px; }
  .comp textarea { min-width:320px; min-height:34px; }
  .comp .note { font-size:12.5px; color:#6b7080; width:100%; }
  .comp.invalid { background:#fdf1f0; border-radius:8px; padding:8px; }
  .comp .reason { color:var(--bad); font-size:12.5px; width:100%; }
  .oplabel { font:600 12px ui-monospace,monospace; background:#eef2fa;
             color:var(--accent); border-radius:6px; padding:4px 8px; }
  .actions { margin-top:10px; display:flex; gap:8px; }
  button { padding:8px 16px; border:0; border-radius:8px; font:inherit;
           cursor:pointer; background:#e9e9e5; }
  button.primary { background:var(--accent); color:#fff; }
  button:disabled { opacity:.45; cursor:default; }
  .clarify { background:#fff8e8; border:1px solid #f0dfae;
             border-radius:10px; padding:12px 14px; margin-bottom:14px; }
  .rs { margin:0 0 14px; }
  .rs .head { display:flex; gap:8px; align-items:center; flex-wrap:wrap;
              margin-bottom:6px; }
  .ref { font:600 13px ui-monospace,monospace; color:#fff;
         background:var(--accent); border-radius:6px; padding:2px 8px; }
  .badge { font-size:11.5px; border-radius:6px; padding:2px 8px;
           font-weight:600; }
  .badge.complete { background:#e6f4ec; color:var(--ok); }
  .badge.partial { background:#fdf3e2; color:var(--warn); }
  .badge.error { background:#fdf1f0; color:var(--bad); }
  .universe { font-size:12px; color:#6b7080; }
  .tblwrap { overflow-x:auto; border:1px solid var(--line);
             border-radius:8px; background:#fff; }
  table { border-collapse:collapse; width:100%; font-size:12.5px; }
  th { text-align:left; padding:6px 10px; background:#f2f2ee;
       position:sticky; top:0; white-space:nowrap; }
  td { padding:6px 10px; border-top:1px solid var(--line);
       vertical-align:top; max-width:420px; }
  td pre { margin:0; white-space:pre-wrap; font-size:11.5px;
           max-height:180px; overflow-y:auto; }
  details summary { cursor:pointer; color:var(--accent);
                    font-size:12px; }
  .caption { background:#f0f4fb; border-radius:10px; padding:12px 16px;
             margin:0 0 8px; white-space:pre-wrap; }
  .caption .inputs { display:block; margin-top:6px; font:11.5px
             ui-monospace,monospace; color:#6b7080; }
  .chips { display:flex; gap:8px; flex-wrap:wrap; margin:0 0 14px; }
  .chip { border:1px solid var(--accent); color:var(--accent);
          background:#fff; border-radius:999px; padding:6px 14px;
          font-size:13px; cursor:pointer; }
  .fb { margin:-6px 0 14px; }
  .fb button { background:none; border:1px solid var(--line);
               color:#6b7080; padding:2px 10px; border-radius:6px;
               margin-right:6px; font-size:13px; }
  .fb button.done { border-color:var(--accent); color:var(--accent); }
  form#ask { display:flex; gap:10px; padding:14px 22px 20px;
             max-width:980px; width:100%; margin:0 auto; }
  #q { flex:1; padding:12px 14px; border:1px solid var(--line);
       border-radius:8px; font:inherit; background:#fff; }
  .err { color:var(--bad); margin:0 0 14px; }
  .muted { color:#6b7080; font-style:italic; }
</style></head>
<body>
<header>AIVIA workbench <span>· ask about your certified metrics — every
operation shown, confirmed by you, results are the answer</span></header>
<div id="log"></div>
<form id="ask"><input id="q" autocomplete="off"
  placeholder="e.g. are all definitions of Base_Pop_Severe_ED_Scores the same?">
  <button class="primary" id="askbtn">Plan</button></form>
<script>
let conversationId = null;
const log = document.getElementById('log');
const q = document.getElementById('q');
const askbtn = document.getElementById('askbtn');

function el(html) { const d = document.createElement('div');
  d.innerHTML = html; return d.firstElementChild; }
function esc(s) { const t = document.createElement('span');
  t.textContent = String(s ?? ''); return t.innerHTML; }
function add(node) { log.appendChild(node);
  log.scrollTop = log.scrollHeight; return node; }

// ---- plan card: per-op editors, skip, run --------------------------
function fieldFor(c) {
  const p = c.params || {};
  if (c.op === 'search') return `
    <input type="text" data-f="phrase" value="${esc(p.phrase||'')}">
    <select data-f="mode">
      <option value="semantic" ${p.mode==='semantic'?'selected':''}>semantic — closest by meaning (top-K, not exhaustive)</option>
      <option value="exact" ${p.mode==='exact'?'selected':''}>exact — complete enumeration by name</option>
    </select>`;
  if (c.op === 'retrieve') return `
    <textarea data-f="ids">${esc((p.ids||[]).join('\n'))}</textarea>
    <span class="note">one id per line</span>`;
  if (c.op === 'compare') return `
    <input type="text" data-f="refs" value="${esc((p.refs||[]).join(', '))}">
    <input type="text" data-f="aspect" placeholder="aspect (blank = logic)"
           value="${esc(p.aspect||'')}">
    <span class="note">refs: R1… for earlier results, $n for this plan's step n</span>`;
  return '';
}

function planCard(plan, question) {
  const card = el('<div class="card"><h3>Proposed plan — review, edit, then run</h3></div>');
  if (plan.clarification) {
    add(el(`<div class="clarify">${esc(plan.clarification)}</div>`));
    if (!plan.components.length) return null;
  }
  (plan.components || []).forEach(c => {
    const comp = el(`<div class="comp ${c.valid?'':'invalid'}" data-op="${esc(c.op)}">
      <span class="num">${c.index}</span>
      <div class="fields">
        <span class="oplabel">${esc(c.op)}</span>
        ${c.valid ? fieldFor(c) : ''}
        <label style="margin-left:auto;font-size:12px">
          <input type="checkbox" data-f="skip"> skip</label>
        ${c.note ? `<span class="note">${esc(c.note)}</span>` : ''}
        ${c.valid ? '' : `<span class="reason">cannot run: ${esc(c.invalid_reason)}</span>`}
      </div></div>`);
    if (!c.valid) comp.querySelector('[data-f=skip]').checked = true;
    card.appendChild(comp);
  });
  const actions = el(`<div class="actions">
    <button class="primary" data-a="run">Run plan</button>
    <button data-a="cancel">Cancel</button></div>`);
  card.appendChild(actions);
  actions.querySelector('[data-a=run]').onclick = () => runPlan(card, question);
  actions.querySelector('[data-a=cancel]').onclick = () => {
    card.querySelector('h3').textContent = 'Plan cancelled';
    actions.remove(); };
  add(card);
  return card;
}

function collectPlan(card) {
  const components = [];
  card.querySelectorAll('.comp').forEach(comp => {
    if (comp.querySelector('[data-f=skip]').checked) return;
    const op = comp.dataset.op;
    const get = f => { const n = comp.querySelector(`[data-f=${f}]`);
                       return n ? n.value : ''; };
    let params = {};
    if (op === 'search') params = { phrase: get('phrase'), mode: get('mode') };
    if (op === 'retrieve') params = { ids: get('ids').split('\n')
        .map(s => s.trim()).filter(Boolean) };
    if (op === 'compare') { params = { refs: get('refs').split(',')
        .map(s => s.trim()).filter(Boolean) };
      if (get('aspect').trim()) params.aspect = get('aspect').trim(); }
    components.push({ op, params });
  });
  return { components };
}

// ---- execute + display ---------------------------------------------
async function runPlan(card, question) {
  const plan = collectPlan(card);
  if (!plan.components.length) { add(el('<p class="err">Nothing to run — every component is skipped.</p>')); return; }
  card.querySelectorAll('button,input,select,textarea').forEach(n => n.disabled = true);
  card.querySelector('h3').textContent = 'Plan confirmed — running…';
  try {
    const r = await fetch('/api/execute', { method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ conversation_id: conversationId, question,
                             plan })});
    const j = await r.json();
    if (!r.ok) { add(el(`<p class="err">${esc(j.error||('error '+r.status))}</p>`)); return; }
    card.querySelector('h3').textContent = 'Plan (as run)';
    (j.outputs || []).forEach(renderOutput);
    if (j.caption) {
      add(el(`<div class="caption">${esc(j.caption)}
        <span class="inputs">caption based on: ${esc((j.caption_inputs||[]).join(', ')||'—')}</span></div>`));
      renderFeedback(j.turn_index);
    }
    renderSuggestions(j.suggestions || []);
  } catch (e) { add(el(`<p class="err">network error: ${esc(e)}</p>`)); }
}

function renderOutput(o) {
  if (o.error) {
    add(el(`<div class="rs"><div class="head">
      <span class="oplabel">${esc(o.component.op)}</span>
      <span class="badge error">error</span>
      <span class="universe">${esc(o.error)}</span></div></div>`));
    return;
  }
  const r = o.result;
  const badge = r.complete
    ? '<span class="badge complete">complete</span>'
    : '<span class="badge partial">not exhaustive</span>';
  const rs = el(`<div class="rs"><div class="head">
    <span class="ref">${esc(r.ref)}</span>
    <span class="oplabel">${esc(r.op)}</span>
    <span class="universe">${esc(JSON.stringify(r.params))}</span>
    ${badge}
    <span class="universe">${esc(r.universe)}${r.note ? ' · ' + esc(r.note) : ''}</span>
    </div></div>`);
  rs.appendChild(renderTable(r.rows));
  add(rs);
}

function renderTable(rows) {
  if (!rows || !rows.length)
    return el('<p class="muted">no rows — an honest empty result</p>');
  const cols = [...new Set(rows.flatMap(r => Object.keys(r)))];
  const wrap = el('<div class="tblwrap"></div>');
  const cell = v => {
    if (v === null || v === undefined) return '';
    if (typeof v === 'object') v = JSON.stringify(v, null, 1);
    v = String(v);
    if (v.length > 160 || v.includes('\n'))
      return `<details><summary>${esc(v.slice(0, 60))}…</summary><pre>${esc(v)}</pre></details>`;
    return esc(v);
  };
  wrap.innerHTML = `<table><thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
    <tbody>${rows.map(r => `<tr>${cols.map(c => `<td>${cell(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  return wrap;
}

function renderSuggestions(suggestions) {
  if (!suggestions.length) return;
  const chips = el('<div class="chips"></div>');
  suggestions.forEach(s => {
    const chip = el(`<button class="chip">${esc(s.op)}: ${esc(JSON.stringify(s.params))}${s.note ? ' — ' + esc(s.note) : ''}</button>`);
    chip.onclick = () => planCard({ components: [ { ...s, index: 1, valid: true } ] },
                                  '(suggested action)');
    chips.appendChild(chip);
  });
  add(chips);
}

function renderFeedback(turnIndex) {
  const fb = el(`<div class="fb">
    <button data-v="helpful">&#128077; helpful</button>
    <button data-v="not_helpful">&#128078; not what I needed</button></div>`);
  fb.querySelectorAll('button').forEach(b => b.onclick = async () => {
    await fetch('/api/feedback', { method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ conversation_id: conversationId,
        turn_index: turnIndex, verdict: b.dataset.v })});
    fb.querySelectorAll('button').forEach(x => x.classList.remove('done'));
    b.classList.add('done');
  });
  add(fb);
}

// ---- ask -----------------------------------------------------------
document.getElementById('ask').addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = q.value.trim();
  if (!message) return;
  q.value = ''; askbtn.disabled = true;
  add(el(`<p class="you">you&gt; ${esc(message)}</p>`));
  const thinking = add(el('<p class="muted">planning…</p>'));
  try {
    const r = await fetch('/api/plan', { method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ message, conversation_id: conversationId })});
    const j = await r.json();
    thinking.remove();
    if (!r.ok) { add(el(`<p class="err">${esc(j.error||('error '+r.status))}</p>`)); }
    else { conversationId = j.conversation_id; planCard(j.plan, message); }
  } catch (e2) { thinking.remove();
    add(el(`<p class="err">network error: ${esc(e2)}</p>`)); }
  askbtn.disabled = false; q.focus();
});
q.focus();
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
