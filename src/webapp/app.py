"""The chat web app: certified-metrics surface + marketplace fulfillment, one host.

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

import json as _json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from src.branding import product_name
from src.orchestrator.agent import Turn, run_turn
from src.orchestrator.events import FeedbackEvent, TurnEvent, decision_shape
from src.orchestrator.tools import Session
from src.orchestrator.turn_engine import EngineSession
from src.orchestrator.turn_engine import run_turn as engine_run_turn

MAX_CONVERSATIONS = 500          # in-memory cap; oldest evicted
MAX_TURNS_PER_CONVERSATION = 60


@dataclass
class Conversation:
    history: "list[dict]" = field(default_factory=list)
    session: Session = field(default_factory=Session)
    engine: EngineSession = field(default_factory=EngineSession)
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
    app = FastAPI(title=product_name(), docs_url=None, redoc_url=None)
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
        return WORKBENCH_PAGE.replace("__PRODUCT__", product_name())

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

    # ---- the one-mind turn (ADR 0051) -------------------------------

    @app.post("/api/ask")
    async def ask(request: Request) -> JSONResponse:
        """One user turn on the merged engine: the mind loops over
        read-only tools with full evidence in ONE conversation; the
        boundary stamps, gates, and verifies. Reads run immediately —
        the plan-confirm card remains only for writes (ADR 0050)."""
        body = await request.json()
        question = str(body.get("message", "")).strip()
        if not question:
            return JSONResponse({"error": "empty message"},
                                status_code=400)
        user = _user_from(request)
        conv_id = str(body.get("conversation_id") or uuid.uuid4())
        conv = _conversation(user, conv_id)
        turn_index = conv.turns
        try:
            turn = engine_run_turn(conv.engine, question, chat_api,
                                   run_kql)
        except Exception as e:                 # noqa: BLE001
            return JSONResponse(
                {"error": f"engine unavailable ({type(e).__name__})",
                 "conversation_id": conv_id}, status_code=502)
        trace = [{"tool": o["component"]["op"],
                  "args": o["component"]["params"],
                  "result": (o.get("result") or {"error": o.get("error")})}
                 for o in turn["outputs"]]
        sink.record(TurnEvent(
            event_at=datetime.now(timezone.utc).isoformat(),
            user_id=user,
            question=question[:500],
            tools_used=tuple(t["tool"] for t in trace),
            ids_read=tuple(sorted({
                str(i) for t in trace if t["tool"] == "retrieve"
                for i in t["args"].get("ids", [])})),
            basis="; ".join(
                f"{t['tool']}({_json.dumps(t['args'])[:80]})"
                for t in trace),
            answered=bool(turn["answered"]),
            conversation_id=conv_id, turn_index=turn_index,
            decision=decision_shape(trace, turn["answer"]),
            trace=tuple(
                {"tool": t["tool"], "args": t["args"],
                 "result": _json.dumps(t["result"])[:1500]}
                for t in trace),
        ))
        conv.turns += 1
        return JSONResponse({
            "conversation_id": conv_id,
            "turn_index": turn_index,
            "outputs": turn["outputs"],
            "caption": turn["answer"],
            "caption_inputs": sorted({
                (o.get("result") or {}).get("ref")
                for o in turn["outputs"] if o.get("result")} - {None}),
            "caption_corrected": turn["caption_corrected"],
            "caption_violations": turn["caption_violations"],
            "answered": turn["answered"],
            "missing_op": turn["missing_op"],
            "loop_status": (f"one mind: {turn['rounds']} tool round(s)"
                            + (" — budget exhausted"
                               if turn["exhausted"] else "")),
            "loop_note": turn["missing_op"] if not turn["answered"] else "",
            "suggestions": [],
        })

    # ADR 0051: the plan-protocol endpoints were DELETED with their
    # minds. Writes, when they exist, get a fresh plan-confirm
    # surface built against ADR 0050's floors.

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
                f"<h1>{product_name()}</h1><p>Could not resolve this purchase: "
                f"{body.get('error')}</p>", status_code=status)
        sub = body["subscription"]
        return HTMLResponse(LANDING_PAGE.replace("__PRODUCT__", product_name()).format(
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
<title>__PRODUCT__ — certified metrics workbench</title>
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
  .badge.auto { background:#fff7e6; color:#8a5a00;
                border:1px solid #e0b96a; }
  .loopline { font:11.5px ui-monospace,monospace; color:#8a5a00;
              margin:0 0 6px; }
  .headline { font:13px/1.5 ui-monospace,monospace; font-weight:600;
              background:#eef7ee; border-left:3px solid #2e7d32;
              padding:8px 12px; margin:0 0 6px; }
  .caption { background:#f0f4fb; border-radius:10px; padding:12px 16px;
             margin:0 0 8px; white-space:pre-wrap; font-size:13px;
             color:#4a4f5a; }
  .caption::before { content:"commentary (model-written; headlines "
             "above are machine-stamped)"; display:block; font:10.5px
             ui-monospace,monospace; color:#8a8fa0; margin-bottom:4px; }
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
  .foldmore { display:block; width:100%; padding:7px; border:0;
              border-top:1px solid var(--line); background:#f7f7f4;
              color:var(--accent); cursor:pointer; font-size:12px; }
</style></head>
<body>
<header>__PRODUCT__ workbench <span>· ask about your certified metrics — every
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

// ADR 0051: the plan-card JS was deleted with the plan protocol.
// Reads run immediately; a fresh confirm surface returns with writes.

function renderOutput(o) {
  const auto = (o.component && o.component.auto_round)
    ? `<span class="badge auto">auto round ${o.component.auto_round} · read-only</span>`
    : '';
  if (o.error) {
    add(el(`<div class="rs"><div class="head">
      <span class="oplabel">${esc(o.component.op)}</span>${auto}
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
    <span class="oplabel">${esc(r.op)}</span>${auto}
    <span class="universe">${esc(JSON.stringify(r.params))}</span>
    ${badge}
    <span class="universe">${esc(r.universe)}${r.note ? ' · ' + esc(r.note) : ''}</span>
    </div></div>`);
  if (r.headline) rs.appendChild(
    el(`<div class="headline">${esc(r.headline)}</div>`));
  let rows2 = r.rows, prefer = null;
  if (r.op === 'search' || r.op === 'census') {
    // Customer-facing view: an exec asking what logic is in a report
    // reads business identities, not CTE names or refs.
    rows2 = [...rows2].sort((a, b) => (b.closeness || 0) - (a.closeness || 0));
    rows2 = rows2.map(x => {
      let label;
      if (x.kind === 'step') {
        label = (x.business_name || x.of_metric || x.id) + ' → step' +
          (x.step_no ? ' ' + x.step_no
                     : (x.description ? '' : ' · ' + (x.name || '')));
      } else {
        label = x.business_name || x.name || x.id;
      }
      const row = { item: label, description: x.description || '' };
      if (x.closeness !== undefined) row.closeness = x.closeness;
      return row;
    });
    prefer = ['item', 'description', 'closeness'];
  }
  rs.appendChild(renderTable(rows2, prefer));
  add(rs);
}

function renderTable(rows, prefer) {
  if (!rows || !rows.length)
    return el('<p class="muted">no rows — an honest empty result</p>');
  let cols = [...new Set(rows.flatMap(r => Object.keys(r)))];
  if (prefer) cols = prefer.filter(c => cols.includes(c));
  const wrap = el('<div class="tblwrap"></div>');
  const cell = v => {
    if (v === null || v === undefined) return '';
    if (typeof v === 'object') v = JSON.stringify(v, null, 1);
    v = String(v);
    if (v.length > 160 || v.includes('\\n'))
      return `<details><summary>${esc(v.slice(0, 60))}…</summary><pre>${esc(v)}</pre></details>`;
    return esc(v);
  };
  // Walk feedback (Sunny, 2026-08-21): a 413-row census answered one
  // count and buried it. Presentation-only fold — the stamped headline
  // above still carries the exact total, so nothing honest is hidden.
  const FOLD = 30;
  const head = `<thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>`;
  const tr = r => `<tr>${cols.map(c => `<td>${cell(r[c])}</td>`).join('')}</tr>`;
  if (rows.length <= FOLD) {
    wrap.innerHTML = `<table>${head}<tbody>${rows.map(tr).join('')}</tbody></table>`;
    return wrap;
  }
  wrap.innerHTML = `<table>${head}<tbody>${rows.slice(0, FOLD).map(tr).join('')}</tbody></table>`;
  const more = el(`<button class="foldmore">show all ${rows.length} rows (${FOLD} shown)</button>`);
  more.onclick = () => {
    wrap.querySelector('tbody').innerHTML = rows.map(tr).join('');
    more.remove();
  };
  wrap.appendChild(more);
  return wrap;
}

function renderSuggestions(suggestions) {
  if (!suggestions.length) return;
  const chips = el('<div class="chips"></div>');
  suggestions.forEach(s => {
    const label = `${esc(s.op)}: ${esc(JSON.stringify(s.params))}${s.note ? ' — ' + esc(s.note) : ''}`;
    const chip = el(`<span class="chip">${label}</span>`);
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
  const thinking = add(el('<p class="muted">working — operations will appear as run…</p>'));
  try {
    // One-mind turn (ADR 0051): reads run immediately; every
    // operation the mind ran is displayed, stamped. The plan-confirm
    // card returns only when write operations exist.
    const r = await fetch('/api/ask', { method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ message, conversation_id: conversationId })});
    const j = await r.json();
    thinking.remove();
    if (!r.ok) { add(el(`<p class="err">${esc(j.error||('error '+r.status))}</p>`)); }
    else {
      conversationId = j.conversation_id;
      (j.outputs || []).forEach(renderOutput);
      if (j.loop_status) {
        add(el(`<div class="loopline">${esc(j.loop_status)}${
          j.loop_note ? ' — ' + esc(j.loop_note) : ''}</div>`));
      }
      if (j.caption) {
        const gate = j.caption_corrected
          ? `<span class="inputs">honesty gate: original answer over-claimed
              — showing the verified floor
              (${esc((j.caption_violations||[]).join('; '))})</span>`
          : '';
        add(el(`<div class="caption">${esc(j.caption)}
          <span class="inputs">based on: ${esc((j.caption_inputs||[]).join(', ')||'—')}${
          j.answered ? ' · verdict: answered (evidence verified)' : ''}</span>${gate}</div>`));
        renderFeedback(j.turn_index);
      }
    }
  } catch (e2) { thinking.remove();
    add(el(`<p class="err">network error: ${esc(e2)}</p>`)); }
  askbtn.disabled = false; q.focus();
});
q.focus();
</script>
</body></html>
"""

LANDING_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>__PRODUCT__ — activate</title>
<style>body{{font:16px/1.6 -apple-system,"Segoe UI",sans-serif;
max-width:640px;margin:60px auto;color:#1a1f2e;padding:0 20px}}
button{{padding:12px 24px;border:0;border-radius:8px;background:#2b5db9;
color:#fff;font:inherit;cursor:pointer}}</style></head>
<body>
<h1>__PRODUCT__</h1>
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
