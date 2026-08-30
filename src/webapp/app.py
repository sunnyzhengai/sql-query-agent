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
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from src.branding import product_name
from src.orchestrator.agent import Turn, run_turn
from src.orchestrator.caption_gate import stamped_headline
from src.orchestrator.conclusion import compose_conclusion
from src.orchestrator.events import FeedbackEvent, TurnEvent, decision_shape
from src.orchestrator.ops import OpError
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
    # ADR 0060 (sameness class live, ordered 2026-08-29): the parse
    # awaiting Sunny's call-1 confirmation — nothing executes until
    # the click; a new question replaces it (stale parses die)
    pending_parse: "dict | None" = None


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
    run_executor=None,
    run_cap: int = 200,
    run_source: str = "",
    run_unbound: str = "",
    planner: bool = False,
    escalation_contact: str = "",
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

    @app.post("/api/run")
    async def run_confirmed_step(request: Request) -> JSONResponse:
        """ADR 0061 slice 1: execute ONE certified step SELECT —
        byte-for-byte what the user confirmed on glass. P5 ABSOLUTE:
        rows go to THIS response (the display); the model context
        never sees them (the run is not an engine tool); the
        decision event records STAMPS only."""
        body = await request.json()
        step_id = str(body.get("step_id", "")).strip()
        conv_id = str(body.get("conversation_id") or "")
        user = _user_from(request)
        if not step_id:
            return JSONResponse({"error": "step_id required"},
                                status_code=400)
        conv = _conversation(user, conv_id) if conv_id else None
        if conv is not None and not conv.engine.ops.permitted(step_id):
            return JSONResponse(
                {"error": "refusal", "reason_class": "unsurfaced",
                 "message": "that step has not been surfaced in this "
                            "conversation — retrieve it first (the "
                            "read guarantee applies to runs too)"},
                status_code=403)
        if run_executor is None:
            # RW-16: the unbound state DISTINGUISHES its cause — the
            # wiring passes the specific reason + cure when it knows
            return JSONResponse(
                {"error": "refusal", "reason_class": "unconfigured",
                 "message": run_unbound or (
                     "the run layer has no source binding — add the "
                     "run: section to org_config.yaml (server, "
                     "database) with a READ-ONLY credential")},
                status_code=503)
        from src.orchestrator.assemble import NODE_FACTS_QUERY
        rows = run_kql(NODE_FACTS_QUERY, {"p_node_id": step_id})
        if not rows:
            return JSONResponse({"error": "refusal",
                                 "reason_class": "unknown_step",
                                 "message": f"no step {step_id!r}"},
                                status_code=404)
        props = rows[0].get("properties") or "{}"
        if isinstance(props, str):
            props = _json.loads(props)
        fragment = str(props.get("sql_fragment") or "")
        from src.run_layer import RunRefusal, run_step
        try:
            res = run_step(fragment, run_executor, cap=run_cap,
                           source=run_source)
        except RunRefusal as e:
            return JSONResponse(
                {"error": "refusal", "reason_class": e.reason_class,
                 "message": str(e)}, status_code=422)
        except Exception as e:  # noqa: BLE001 — RW-16: name the cure
            from src.run_layer import classify_run_error
            reason_class, message = classify_run_error(e)
            return JSONResponse(
                {"error": "refusal", "reason_class": reason_class,
                 "message": message}, status_code=502)
        # 0056-shape capture: the run + confirm as a decision event —
        # STAMPS only (P5), never rows
        sink.record(TurnEvent(
            event_at=datetime.now(timezone.utc).isoformat(),
            user_id=user,
            question=f"[RUN] {step_id}",
            tools_used=("run",),
            ids_read=(step_id,),
            basis=f"run_step({step_id}) — confirmed on glass",
            answered=True,
            conversation_id=conv_id, turn_index=-1,
            decision={"made_by": "deterministic_run",
                      "stamps": res.model_stamps()},
            trace=({"tool": "run", "args": {"step_id": step_id},
                    "result": _json.dumps(res.model_stamps())},),
        ))
        return JSONResponse({
            "step_id": step_id,
            "columns": res.columns,
            "rows": res.rows,
            "sampling_label": res.sampling_label(run_cap, run_source),
            "stamps": res.model_stamps()})

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

    def _ask_finish(user: str, conv_id: str, conv: Conversation,
                    question: str, turn: dict) -> dict:
        """Record the turn event and build the response payload —
        shared by /api/ask and /api/ask/stream so the two surfaces
        can never drift."""
        turn_index = conv.turns
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
        return {
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
            "conclusion": compose_conclusion(
                turn["outputs"], turn["answer"], turn["answered"]),
            "folded_refs": turn.get("folded_refs", []),
            "missing_op": turn["missing_op"],
            "loop_status": (f"one mind: {turn['rounds']} tool round(s)"
                            + (" — budget exhausted"
                               if turn["exhausted"] else "")),
            "loop_note": turn["missing_op"] if not turn["answered"] else "",
            "suggestions": [],
        }

    def _planner_intercept(conv: Conversation, question: str,
                           on_progress=None) -> "dict | None":
        """ADR 0060, sameness class LIVE (ordered 2026-08-29 after
        codeset FAIL #3 — three runs, three routes, three failures:
        the route was a coin flip). The parse is the plan: a
        sameness parse RENDERS for confirmation (Sunny's call 1 —
        confirm every parse) and executes deterministically on the
        click — same parse, same plan, same DIFFERS line, every
        run. Any parser trouble falls through to the engine, which
        remains the default surface for every other class."""
        import time as _time

        from src.orchestrator.parse_plan import (
            ground_entities,
            parse_question,
        )
        # RULED 2026-08-29 (remove-the-type-first): NO SILENT
        # fallback anywhere. Every state is a CARD — the engine is
        # reachable ONLY via the card's explicit button. A question
        # nothing grounds gets the NO-MATCH card (rephrase + the
        # developer door + the engine button), never a silent route.
        def _no_match(line: str) -> dict:
            return {"parse_confirm": line, "no_match": True,
                    "show": [], "parse": {"question": question,
                                          "entities": [],
                                          "primitives": [],
                                          "modifiers": []}}
        t0 = _time.monotonic()
        try:
            parse = parse_question(question, chat_api)
        except Exception:   # noqa: BLE001 — parser down is a CARD too
            return _no_match(
                "the parser is unavailable right now — you can "
                "answer without the planner, or contact a developer")
        t_parse = int((_time.monotonic() - t0) * 1000)
        if not parse.entities and not parse.kinds:
            conv.pending_parse = {"question": question,
                                  "entities": [], "primitives": [],
                                  "modifiers": [], "kinds": [],
                                  "show": []}
            return _no_match(
                "no catalog entities found in the question — "
                "rephrase with a metric, step, table, or report "
                "name, answer without the planner, or contact a "
                "developer")
        if on_progress is not None:
            try:
                on_progress({"parse_line": parse.render(),
                             "entities": parse.entities})
            except Exception:   # noqa: BLE001, S110 — listener only
                pass
        # SHOW grounds BEFORE the ask (a read; reads run immediately,
        # ADR 0050) — in PARALLEL, streamed per entity (RW-18a/b).
        show: "list[dict]" = []

        def _grounded(entity, group):
            matches = [
                {"id": a["id"], "kind": a.get("kind"),
                 "name": ((a.get("rows") or [{}])[0].get("business_name")
                          or (a.get("rows") or [{}])[0].get("name")
                          or a["id"])}
                for a in group if a["id"]]
            show.append({"entity": entity, "matches": matches})
            if on_progress is not None:
                try:
                    on_progress({"grounded": {"entity": entity,
                                              "matches": matches}})
                except Exception:   # noqa: BLE001, S110 — listener only
                    pass

        t1 = _time.monotonic()
        # RW-25 (Sunny's walk, the 57-min idle): store-no-answer
        # auto-retries ONCE — the idle-wake is a known ~10-15s
        # transient, and one retry makes the error card never
        # exist; the skeleton says "store waking…" meanwhile
        for attempt in (1, 2):
            try:
                del show[:]
                ground_entities(parse.entities, run_kql,
                                conv.engine.ops, on_grounded=_grounded)
                break
            except Exception:   # noqa: BLE001 — second miss is a card
                if attempt == 2:
                    payload = _no_match(
                        "the catalog store did not answer the "
                        "grounding queries — likely waking from "
                        "idle. Retry, answer without the planner, "
                        "or contact a developer")
                    payload["retry"] = True   # the named remedy IS
                    return payload            # a button (RW-25)
                if on_progress is not None:
                    try:
                        on_progress({"store_waking": True})
                    except Exception:   # noqa: BLE001, S110
                        pass
        t_ground = int((_time.monotonic() - t1) * 1000)
        conv.pending_parse = {"question": question,
                              "entities": parse.entities,
                              "primitives": parse.primitives,
                              "modifiers": parse.modifiers,
                              "kinds": parse.kinds,
                              "show": show}
        proposal = parse.render()
        if "count_rows" in parse.primitives:
            # B10: row-data asks propose the POLICY REFUSAL + the
            # definition offer — grounding proceeds, wandering never
            from src.orchestrator.conclusion import POLICY_REFUSAL
            proposal = (POLICY_REFUSAL + " I can show the certified "
                        "definition instead — confirm to see it.")
        payload = {"parse_confirm": proposal,
                   "parse": {k: conv.pending_parse[k] for k in
                             ("question", "entities", "primitives",
                              "modifiers", "kinds")},
                   "show": show,
                   # RW-18d: the latency split is MEASURED, on glass
                   # and in RESULTS — never guessed
                   "latency_ms": {"parse": t_parse,
                                  "ground": t_ground}}
        # RW-BATCH-6 (B4): no-match is COMPOSE-DRIVEN, not
        # grounding-driven — a bare table WORD composes a lineage
        # probe even though the catalog grounds nothing; only a
        # question the lexicon truly cannot compose gets the
        # no-match card (the doors remain)
        from src.orchestrator.parse_plan import (
            ParseRefusal,
            compose_plan,
        )
        anchors_now = [
            {"entity": s["entity"], "id": m["id"],
             "kind": m.get("kind"), "rows": [m]}
            for s in show for m in s["matches"]] or [
            {"entity": e, "id": None, "kind": None, "rows": []}
            for e in parse.entities]
        try:
            compose_plan(parse, anchors_now)
        except ParseRefusal:
            payload["no_match"] = True
            payload["parse_confirm"] = (
                "no catalog match for "
                + ", ".join(repr(e) for e in parse.entities[:4])
                + " — rephrase with a catalog name, answer without "
                "the planner, or contact a developer")
        return payload

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
        if planner and body.get("planner") is not False:
            p = _planner_intercept(conv, question)
            if p:
                return JSONResponse({"conversation_id": conv_id, **p})
        try:
            turn = engine_run_turn(conv.engine, question, chat_api,
                                   run_kql)
        except Exception as e:                 # noqa: BLE001
            return JSONResponse(
                {"error": f"engine unavailable ({type(e).__name__})",
                 "conversation_id": conv_id}, status_code=502)
        return JSONResponse(_ask_finish(user, conv_id, conv, question,
                                        turn))

    def _confirm_execute(user: str, conv_id: str, conv, body: dict,
                         on_event=None) -> "tuple[dict, int]":
        """The click that runs the plan (0060 confirm-all): grounds
        the entities, composes the op sequence, executes through the
        EXISTING algebra in this conversation's session — stamped
        results and the machine conclusion are the answer; nothing
        is narrated by a model. Shared by the JSON and stream
        surfaces (the _ask_finish pattern) so they can never drift."""
        import time as _time

        from src.orchestrator.parse_plan import (
            Parse,
            ParseRefusal,
            compose_plan,
            execute_plan,
            ground_entities,
        )
        if conv is None or not conv.pending_parse:
            return ({"error": "refusal",
                     "reason_class": "no_pending_parse",
                     "message": "no parse awaits confirmation in this "
                                "conversation — ask the question "
                                "first"}, 409)
        pp, conv.pending_parse = conv.pending_parse, None
        parse = Parse(entities=list(pp["entities"]),
                      primitives=list(pp["primitives"]),
                      modifiers=list(pp.get("modifiers") or []),
                      kinds=list(pp.get("kinds") or []))
        # 0062 ASK items: pruning a shown match is a decision — the
        # excluded ids never enter the plan (no-nag: this ONE confirm
        # ratifies the pruned reading; its ops then run freely)
        exclude = {str(x) for x in (body.get("exclude_ids") or [])}
        ops = conv.engine.ops
        ops.begin_turn()
        ops.note_user(pp["question"])
        t0 = _time.monotonic()
        try:
            anchors = ground_entities(parse.entities, run_kql, ops)
            if exclude:
                anchors = [a for a in anchors
                           if str(a.get("id")) not in exclude]
            plan = compose_plan(parse, anchors)
            results = execute_plan(plan, run_kql, ops,
                                   on_event=on_event)
        except ParseRefusal as e:
            return ({"error": "refusal", "reason_class": "parse_refusal",
                     "message": str(e),
                     "conversation_id": conv_id}, 422)
        except OpError as e:
            return ({"error": "refusal", "reason_class": "op_error",
                     "message": str(e),
                     "conversation_id": conv_id}, 422)
        t_exec = int((_time.monotonic() - t0) * 1000)
        outputs = []
        for r in results:
            shown = r.display()
            shown["headline"] = stamped_headline(shown)
            display = {"component": {"op": shown["op"],
                                     "params": shown["params"],
                                     "planner": True},
                       "result": shown}
            outputs.append(display)
            if on_event is not None:
                try:
                    on_event(display)   # RW-18c: results stream too
                except Exception:   # noqa: BLE001, S110 — listener
                    pass
        conv.engine.displays.extend(outputs)
        turn = {"answer": "", "outputs": outputs,
                "rounds": len(results), "answered": True,
                "missing_op": "", "evidence_quote": "",
                "caption_corrected": False, "caption_violations": [],
                "exhausted": False, "folded_refs": []}
        payload = _ask_finish(user, conv_id, conv,
                              f"[PLANNER] {pp['question']}", turn)
        payload["planned"] = True
        payload["parse_confirm"] = parse.render()
        payload["latency_ms"] = {"execute": t_exec}
        payload["loop_status"] = (
            f"planner: {len(results)} deterministic op(s) in "
            f"{t_exec} ms — the parse was the plan")
        return (payload, 200)

    @app.post("/api/parse/confirm")
    async def parse_confirm(request: Request) -> JSONResponse:
        body = await request.json()
        conv_id = str(body.get("conversation_id") or "")
        user = _user_from(request)
        conv = _conversation(user, conv_id) if conv_id else None
        payload, status = _confirm_execute(user, conv_id, conv, body)
        return JSONResponse(payload, status_code=status)

    @app.post("/api/parse/confirm/stream")
    async def parse_confirm_stream(request: Request):
        """RW-18c: the post-confirm blank dies — each op's chip
        renders at DISPATCH and its stamped result at completion
        (the ask/stream pattern, verbatim)."""
        import asyncio
        import queue as _q
        import threading

        body = await request.json()
        conv_id = str(body.get("conversation_id") or "")
        user = _user_from(request)
        conv = _conversation(user, conv_id) if conv_id else None
        events: "_q.Queue[tuple]" = _q.Queue()

        def work() -> None:
            payload, status = _confirm_execute(
                user, conv_id, conv, body,
                on_event=lambda e: events.put(("evt", e)))
            events.put(("done", (payload, status)))

        threading.Thread(target=work, daemon=True).start()

        def _sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {_json.dumps(data)}\n\n"

        async def gen():
            loop = asyncio.get_event_loop()
            while True:
                kind, payload = await loop.run_in_executor(None,
                                                           events.get)
                if kind == "evt":
                    yield _sse("output", payload)
                else:
                    result, status = payload
                    yield _sse("done" if status == 200 else "refusal",
                               result)
                    return

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/api/escalate")
    async def escalate(request: Request) -> JSONResponse:
        """THE DEVELOPER DOOR (0062, RULED: offered at EVERY round —
        a standing door, never a last resort). "None of these is
        right" is not a dead end: the whole exchange — shown
        matches, proposed reading, the human's rejection — becomes a
        CAPTURED DEMAND (0056 deny shape) and the developer arrives
        already knowing what the user wants and what the graph
        lacks. Returns the summary + a prefilled mailto (Teams users
        paste the same summary)."""
        body = await request.json()
        conv_id = str(body.get("conversation_id") or "")
        note = str(body.get("note") or "").strip()[:500]
        user = _user_from(request)
        conv = _conversation(user, conv_id) if conv_id else None
        pp = (conv.pending_parse if conv else None) or {}
        if conv is not None:
            conv.pending_parse = None      # the attempt ends here
        question = str(pp.get("question")
                       or body.get("question") or "")[:500]
        shown = pp.get("show") or []
        lines = [f"Captured demand from {user}",
                 f"Question: {question}"]
        for s in shown:
            names = ", ".join(m["name"] for m in s["matches"]) or "—"
            lines.append(f"  matched {s['entity']!r}: {names}")
        lines.append("User verdict: none of the shown understanding "
                     "or options is right"
                     + (f" — note: {note}" if note else ""))
        summary = "\n".join(lines)
        sink.record(TurnEvent(
            event_at=datetime.now(timezone.utc).isoformat(),
            user_id=user,
            question=f"[ESCALATE] {question}",
            tools_used=("escalate",),
            ids_read=tuple(sorted({m["id"] for s in shown
                                   for m in s["matches"]})),
            basis="developer door (0062): captured demand",
            answered=False,
            conversation_id=conv_id, turn_index=-1,
            decision={"made_by": "user_escalation",
                      "rejected_reading": True,
                      "shown": shown, "note": note},
            trace=({"tool": "escalate",
                    "args": {"question": question},
                    "result": summary[:1500]},),
        ))
        import urllib.parse as _url
        mailto = ""
        if escalation_contact:
            mailto = ("mailto:" + escalation_contact
                      + "?subject=" + _url.quote(
                          f"[{product_name()}] captured demand")
                      + "&body=" + _url.quote(summary))
        return JSONResponse({"captured": True, "summary": summary,
                             "mailto": mailto,
                             "contact": escalation_contact})

    @app.post("/api/ask/stream")
    async def ask_stream(request: Request):
        """The same turn, streamed (walk W2, 2026-08-23): each op's
        chip renders at DISPATCH time and its stamped headline at
        completion — the status shown is the actual operation running,
        never a fake spinner. Events: `output` (pending pre-events and
        completed display dicts, verbatim), `stage` (gate/verdict),
        `done` (the exact /api/ask payload), `error`."""
        import asyncio
        import queue as _q
        import threading

        body = await request.json()
        question = str(body.get("message", "")).strip()
        if not question:
            return JSONResponse({"error": "empty message"},
                                status_code=400)
        user = _user_from(request)
        conv_id = str(body.get("conversation_id") or uuid.uuid4())
        conv = _conversation(user, conv_id)

        events: "_q.Queue[tuple]" = _q.Queue()

        def work() -> None:
            # RW-18a: the interception runs IN the worker so the
            # skeleton and per-entity matches stream while grounding
            # is still in flight — the blank before the card dies
            if planner and body.get("planner") is not False:
                events.put(("evt", {"stage": "parse"}))
                p = _planner_intercept(
                    conv, question,
                    on_progress=lambda e: events.put(("card", e)))
                if p:
                    events.put(("card_done",
                                {"conversation_id": conv_id, **p}))
                    return
            try:
                turn = engine_run_turn(conv.engine, question, chat_api,
                                       run_kql,
                                       on_event=lambda e: events.put(
                                           ("evt", e)))
                events.put(("done", turn))
            except Exception as e:             # noqa: BLE001
                events.put(("err",
                            f"engine unavailable ({type(e).__name__})"))

        threading.Thread(target=work, daemon=True).start()

        def _sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {_json.dumps(data)}\n\n"

        async def gen():
            loop = asyncio.get_event_loop()
            while True:
                kind, payload = await loop.run_in_executor(None,
                                                           events.get)
                if kind == "evt":
                    name = "stage" if "stage" in payload else "output"
                    yield _sse(name, payload)
                elif kind == "card":
                    yield _sse("card", payload)
                elif kind == "card_done":
                    yield _sse("done", payload)
                    return
                elif kind == "err":
                    yield _sse("error", {"error": payload,
                                         "conversation_id": conv_id})
                    return
                else:
                    yield _sse("done", _ask_finish(
                        user, conv_id, conv, question, payload))
                    return

        return StreamingResponse(gen(), media_type="text/event-stream")

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
  .caption::before { content:"commentary (model-written; stamped "
             "headlines carry the machine truth)"; display:block; font:10.5px
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
  .caption a { color:var(--accent); }
  .caption ul { margin:6px 0; padding-left:22px; }
  .caption code { background:#e9edf5; border-radius:4px;
                  padding:1px 5px; font:12px ui-monospace,monospace; }
  .sqlfold { margin:6px 0; }
  .sqlfold summary { cursor:pointer; color:var(--accent);
                     font:12px ui-monospace,monospace; }
  .sqlfold pre { background:#f4f4f1; border:1px solid var(--line);
                 border-radius:8px; padding:10px;
                 font:12px ui-monospace,monospace; overflow-x:auto; }
  .cite { font:11.5px ui-monospace,monospace; background:#eef2fa;
          color:var(--accent); border-radius:6px; padding:1px 6px; }
  .runbtn { margin:8px 0 2px; padding:6px 14px; border-radius:8px;
    border:1px solid var(--accent); background:#fff;
    color:var(--accent); cursor:pointer; font-size:13px; }
  .runlabel { font:12.5px ui-monospace,monospace; color:#3a4160;
    margin:8px 0 2px; }
  .runlabel.refused { color:#b3423e; }
  .parsecard { border-left:4px solid #8a63c9; }
  .parsebtns { display:flex; gap:10px; margin:8px 0 2px;
    flex-wrap:wrap; }
  .parsebtns .skipparse, .parsebtns .doorbtn { padding:6px 14px;
    border-radius:8px; border:1px solid #9aa3b8; background:#fff;
    color:#3a4160; cursor:pointer; font-size:13px; }
  .parsebtns .doorbtn { border-color:#c9a04a; color:#8a6a1d; }
  .showbox { margin:8px 0 2px; }
  .showline { font-size:13.5px; margin:3px 0; }
  .matchrow { margin-right:12px; font-size:13px; }
  .concl { border-left:4px solid var(--accent); }
  .cc-machine { font:12.5px ui-monospace,monospace; color:#3a4160;
    margin:6px 0; }
  .cc-item { margin:6px 0; font-size:13.5px; }
  .cc-prose { margin-top:8px; }
  .fc-gloss { font-size:12.5px; font-style:italic; color:#6b7080;
    margin-top:2px; }
  .diffline { font:12.5px ui-monospace,monospace; padding:1px 8px;
    border-radius:4px; margin:2px 0; }
  .diffline.plus { background:#e7f6ec; }
  .diffline.minus { background:#fdecec; }
  .badge.verdict { background:var(--accent); color:#fff; }
  .roundfold { margin:4px 0; }
  .roundfold > .rf-sum { cursor:pointer; list-style:none;
    font:12.5px ui-monospace,monospace; color:#6b7080;
    padding:4px 8px; background:#f4f6fb; border-radius:8px; }
  .roundfold > .rf-sum::-webkit-details-marker { display:none; }
  .flagcards { display:flex; flex-direction:column; gap:8px;
    margin:8px 0; }
  .flagcard { border:1px solid #e2e6f0; border-radius:10px;
    padding:10px 14px; background:#fff; }
  .flagcard.sev-CONFLICT { border-left:4px solid #d9534f; }
  .flagcard.sev-INFO { border-left:4px solid #f0ad4e; }
  .fc-head { display:flex; gap:8px; align-items:center; }
  .fc-members { font-size:12.5px; margin-top:4px; }
  .fc-counts { font:12px ui-monospace,monospace; color:#6b7080;
    margin-top:4px; }
  .fc-why { margin-top:6px; font-size:13.5px; }
  .auxfold { margin:4px 0 2px; }
  .auxfold summary { cursor:pointer; font-size:12px; color:#6b7080;
                     list-style:none; }
  .auxfold summary::-webkit-details-marker { display:none; }
  .errfold { margin:0 0 10px; }
  .errfold summary { cursor:pointer; display:flex; gap:8px;
                     align-items:center; list-style:none;
                     font-size:12.5px; color:#6b7080; }
  .errfold summary::-webkit-details-marker { display:none; }
  .errfold .errdetail { margin:6px 0 0 6px; padding:8px 12px;
                        background:#fdf7f6; border-left:3px solid
                        var(--bad); font-size:12.5px; color:#6b7080; }
  .runline { font:12px ui-monospace,monospace; color:#6b7080;
             margin:0 0 8px; display:flex; gap:8px; align-items:center; }
  .runline .dot { width:8px; height:8px; border-radius:50%;
                  background:var(--warn);
                  animation:pulse 1s infinite alternate; }
  @keyframes pulse { from { opacity:.35; } to { opacity:1; } }
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

// Stamped headlines rendered this turn — the caption renderer
// collapses verbatim re-quotes of these into compact citations
// (walk W1/W3c, display-only; the caption TEXT the suite grades is
// unchanged on the wire).
let turnHeadlines = [];
// RW-5: the panels rendered THIS turn — the finale folds them to
// one-line headlines and seats the conclusion card on top
let turnPanels = [];

function renderOutput(o) {
  const auto = (o.component && o.component.auto_round)
    ? `<span class="badge auto">auto round ${o.component.auto_round} · read-only</span>`
    : '';
  if (o.error) {
    // F1 (demo feedback from friends, 2026-08-24): error/anti-flail
    // chips read as breakage to outsiders — fold to a calm one-line
    // badge, expandable. Machinery stays inspectable; default calm.
    const node = el(`<details class="errfold"><summary>
      <span class="badge error">1 skipped call</span>
      <span class="oplabel">${esc(o.component.op)}</span>
      <span class="universe">guard engaged — expand for detail</span>
      </summary><div class="errdetail">${esc(o.error)}</div></details>`);
    add(node);
    return node;
  }
  const r = o.result;
  const badge = r.complete
    ? '<span class="badge complete">complete</span>'
    : '<span class="badge partial">not exhaustive</span>';
  const rs = el(`<div class="rs" id="ref-${esc(r.ref)}"><div class="head">
    <span class="ref">${esc(r.ref)}</span>
    <span class="oplabel">${esc(r.op)}</span>${auto}
    <span class="universe">${esc(JSON.stringify(r.params))}</span>
    ${badge}
    <span class="universe">${esc(r.universe)}${r.note ? ' · ' + esc(r.note) : ''}</span>
    </div></div>`);
  if (r.headline) {
    rs.appendChild(el(`<div class="headline">${esc(r.headline)}</div>`));
    turnHeadlines.push({ ref: r.ref, text: String(r.headline) });
  }
  // RW-7/RW-1 (capture gate): flag rows render as CARDS — class,
  // severity, counts, disposition, the sweep-authored why-sentence —
  // never machine-grade node labels
  if (r.rows && r.rows.length && r.rows[0].flag_class) {
    const wrap = el(`<div class="flagcards"></div>`);
    for (const f of r.rows) {
      const sev = String(f.severity || '');
      wrap.appendChild(el(`<div class="flagcard sev-${esc(sev)}">
        <div class="fc-head"><b>${esc(f.identity || f.flag_id)}</b>
          <span class="badge">${esc(f.flag_class)}</span>
          <span class="badge sev">${esc(sev)}</span></div>
        <div class="fc-counts">${esc(f.member_count)} members ·
          ${esc(f.distinct_logics)} distinct logics ·
          disposition: ${esc(f.disposition || 'open')}</div>
        <div class="fc-why">${esc(f.description || '')}</div>
      </div>`));
    }
    rs.appendChild(wrap);
    add(rs);
    turnPanels.push(rs);
    return rs;
  }
  let rows2 = r.rows, prefer = null;
  if (r.op === 'search' || r.op === 'census') {
    // Customer-facing view: an exec asking what logic is in a report
    // reads business identities, not CTE names or refs.
    rows2 = [...rows2].sort((a, b) => (b.closeness || 0) - (a.closeness || 0));
    let labeled = rows2.map(x => {
      let label;
      if (x.kind === 'step') {
        label = (x.business_name || x.of_metric || x.id) + ' → step' +
          (x.step_no ? ' ' + x.step_no
                     : (x.description ? '' : ' · ' + (x.name || '')));
      } else {
        label = x.business_name || x.name || x.id;
      }
      return { x, label };
    });
    // Schema-qualify on display-name collision (walk W3a: reporting.
    // vs reports. both showed as bare USP_ED_Sepsis — two identical-
    // looking list entries). Display-only.
    const counts = {};
    labeled.forEach(({ label }) => { counts[label] = (counts[label] || 0) + 1; });
    rows2 = labeled.map(({ x, label }) => {
      if (counts[label] > 1 && x.id && String(x.id) !== label)
        label = label + ' (' + x.id + ')';
      const row = { item: label, description: x.description || '' };
      if (x.closeness !== undefined) row.closeness = x.closeness;
      return row;
    });
    prefer = ['item', 'description', 'closeness'];
  }
  rs.appendChild(renderTable(rows2, prefer));
  // ADR 0061 slice 1: a retrieved STEP is runnable — confirm-each-
  // run IS the click on the displayed, certified SQL (nothing
  // generated). Results render to the DISPLAY; the model sees
  // stamps only (P5).
  if (r.op === 'retrieve') {
    for (const row of (r.rows || [])) {
      if (row.kind === 'step' && row.sql_fragment) {
        const btn = el(`<button class="runbtn">&#9654; run this step (read-only, TOP 200)</button>`);
        const sid = row.id;
        btn.addEventListener('click', async () => {
          btn.disabled = true; btn.textContent = 'running…';
          const resp = await fetch('/api/run', { method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ step_id: sid,
              conversation_id: conversationId }) });
          const rj = await resp.json();
          btn.remove();
          if (rj.error) {
            rs.appendChild(el(`<div class="runlabel refused">run refused — ${esc(rj.message || rj.error)}</div>`));
            return;
          }
          rs.appendChild(el(`<div class="runlabel">${esc(rj.sampling_label)}</div>`));
          rs.appendChild(renderTable(rj.rows, rj.columns));
        });
        rs.appendChild(btn);
      }
    }
  }
  add(rs);
  turnPanels.push(rs);
  return rs;
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

// ---- caption rendering (walk W4/W3b/W5/W1, display-only) -----------
// The caption TEXT on the wire is what the suite grades — untouched.
// This layer renders it: sanitized markdown (escape first, then a
// small safe subset), SQL fences ALWAYS collapsed behind an expander
// (register defense-in-depth — rule 5 is stochastic, the collapse is
// not), verbatim headline re-quotes folded to compact citations, and
// R-number tokens linked to the result panel they cite (a wrong label
// is then checkable in one click — the Q8 nit made visible).

function mdInline(s) {
  // input is HTML-escaped text; output adds only whitelisted tags
  s = s.replace(/\\b(R\\d{1,3})\\b/g,
    '<a class="cite" href="#ref-$1">$1</a>');
  s = s.replace(/\\[([^\\]]{1,160})\\]\\((https?:\\/\\/[^)\\s]+)\\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  s = s.replace(/\\*\\*([^*]{1,200})\\*\\*/g, '<b>$1</b>');
  s = s.replace(/`([^`]{1,160})`/g, '<code>$1</code>');
  return s;
}

function renderMarkdown(raw) {
  const parts = String(raw).split(/```[a-zA-Z]*\\n?([\\s\\S]*?)```/g);
  let html = '';
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 1) {
      html += `<details class="sqlfold"><summary>show SQL</summary><pre>${esc(parts[i].trim())}</pre></details>`;
      continue;
    }
    const lines = esc(parts[i]).split('\\n');
    const out = []; let list = null;
    for (const line of lines) {
      const m = line.match(/^\\s*[-*]\\s+(.*)$/);
      if (m) { (list = list || []).push('<li>' + mdInline(m[1]) + '</li>'); }
      else {
        if (list) { out.push('<ul>' + list.join('') + '</ul>'); list = null; }
        out.push(mdInline(line));
      }
    }
    if (list) out.push('<ul>' + list.join('') + '</ul>');
    html += out.join('\\n');
  }
  return html;
}

function foldHeadlineQuotes(raw) {
  // verbatim re-quote of a stamped headline → a ref citation
  let text = String(raw);
  for (const h of turnHeadlines) {
    if (h.text.length >= 40 && text.includes(h.text))
      text = text.split(h.text).join(`(${h.ref} headline)`);
  }
  return text;
}

function flagCardHtml(f) {
  return `<div class="flagcard sev-${esc(f.severity)}">
    <div class="fc-head"><b>${esc(f.identity)}</b>
      <span class="badge">${esc(f.flag_class)}</span>
      <span class="badge sev">${esc(f.severity)}</span></div>
    <div class="fc-gloss">${esc(f.gloss || '')}</div>
    ${(f.member_names && f.member_names.length) ?
      `<div class="fc-members">${esc(f.member_names.join(', '))}</div>` : ''}
    <div class="fc-counts">${esc(f.member_count)} members ·
      ${esc(f.distinct_logics)} distinct logics ·
      disposition: ${esc(f.disposition)}</div>
    <div class="fc-why">${esc(f.why || '')}</div></div>`;
}

function renderConclusion(j) {
  const c = j.conclusion;
  const based = `<span class="inputs">based on: ${esc((j.caption_inputs||[]).join(', ')||'—')}${
    j.answered ? ' · verdict: answered (evidence verified)' : ''}</span>`;
  const prose = (c && c.prose) ? c.prose : j.caption;
  const proseHtml = prose ?
    `<div class="cc-prose">${renderMarkdown(foldHeadlineQuotes(prose))}</div>` : '';
  if (!c) {
    if (!j.caption) return null;
    return el(`<div class="caption concl">${proseHtml}${based}</div>`);
  }
  if (c.kind === 'flags') {
    return el(`<div class="caption concl">
      ${c.cards.map(flagCardHtml).join('')}
      <div class="cc-machine">${esc(c.closing)}</div>${based}</div>`);
  }
  if (c.kind === 'compare') {
    const diff = (c.diff_lines || []).map(l =>
      `<div class="diffline ${l.startsWith('+') ? 'plus' : 'minus'}">${esc(l)}</div>`).join('');
    const items = (c.items || []).map(i =>
      `<div class="cc-item"><b>${esc(i.name)}</b> — ${esc(i.description)}</div>`).join('');
    return el(`<div class="caption concl">
      <span class="badge verdict">${esc(c.verdict || 'COMPARED')}</span>
      <span class="cc-machine">${esc(c.verdict_note || '')}</span>
      ${diff}${items}${proseHtml}${based}</div>`);
  }
  if (c.kind === 'definition') {
    return el(`<div class="caption concl">
      <div class="cc-item"><b>${esc(c.name)}</b> — ${esc(c.description)}</div>
      ${c.criteria ? `<div class="cc-machine">criteria: <code>${esc(c.criteria)}</code></div>` : ''}
      ${proseHtml}${based}</div>`);
  }
  if (c.kind === 'policy_refusal') {
    const d = c.definition;
    return el(`<div class="caption concl">
      <div class="cc-machine"><b>${esc(c.refusal)}</b></div>
      ${d ? `<div class="cc-item"><b>${esc(d.name)}</b> — ${esc(d.description)}</div>` : ''}
      ${proseHtml}${based}</div>`);
  }
  if (c.kind === 'lineage') {
    return el(`<div class="caption concl">
      <div class="cc-machine">${esc(c.grain_line)}</div>
      ${c.note ? `<div class="cc-machine">${esc(c.note)}</div>` : ''}
      ${proseHtml}${based}</div>`);
  }
  // RW-BATCH-6: the FEEDS card — a report record renders its chain
  if (c.kind === 'feeds') {
    const seg = (label, arr) => (arr && arr.length)
      ? `<div class="cc-item"><b>${esc(label)}:</b> ${esc(arr.join(', '))}</div>`
      : '';
    return el(`<div class="caption concl">
      <div class="cc-item"><b>${esc(c.name)}</b></div>
      ${seg('executes metrics', c.executes_metrics)}
      ${seg('reads tables', c.reads_tables)}
      ${seg('measures', c.measures)}
      ${c.link_state ? `<div class="cc-machine">${esc(c.link_state)}</div>` : ''}
      ${proseHtml}${based}</div>`);
  }
  // RW-22: the CENSUS card — the count line + the rows
  if (c.kind === 'census') {
    const items = (c.items || []).map(i =>
      `<div class="cc-item"><b>${esc(i.name)}</b>${
        i.description ? ' — ' + esc(i.description) : ''}</div>`).join('');
    // RW-24: NEVER positional ("above" broke under the folded
    // answer-first layout) — link the round ref instead
    const more = c.total > (c.items || []).length
      ? `<div class="cc-machine">… and ${esc(String(
          c.total - c.items.length))} more — expand <a class="cite"
          href="#ref-${esc(c.ref)}">${esc(c.ref)}</a> for the full
          table</div>` : '';
    return el(`<div class="caption concl">
      <div class="cc-machine">${esc(c.count_line)}</div>
      ${items}${more}${proseHtml}${based}</div>`);
  }
  // RW-BATCH-6: the MAP card — every retrieved record with its
  // connections (default-map and multi-record shapes)
  if (c.kind === 'map') {
    const items = (c.items || []).map(i => {
      const bits = [];
      if (i.of_metric) bits.push('of ' + i.of_metric);
      if (i.steps && i.steps.length)
        bits.push('steps: ' + i.steps.join(', '));
      if (i.source_tables && i.source_tables.length)
        bits.push('reads: ' + i.source_tables.join(', '));
      return `<div class="cc-item"><b>${esc(i.name)}</b>
        <span class="cite">${esc(i.record_kind || '')}</span>
        ${i.description ? ' — ' + esc(i.description) : ''}
        ${bits.length ? `<div class="cc-machine">${esc(bits.join(' · '))}</div>` : ''}
        </div>`;
    }).join('');
    return el(`<div class="caption concl">${items}${proseHtml}${based}</div>`);
  }
  return el(`<div class="caption concl">${proseHtml}${based}</div>`);
}

function renderFinale(j) {
  // RW-3 (mandatory, echoed): tables from auxiliary rounds fold once
  // the verdict lands — the map on demand; headlines stay visible.
  for (const ref of (j.folded_refs || [])) {
    const panel = document.getElementById('ref-' + ref);
    if (!panel) continue;
    const tbl = panel.querySelector('table');
    if (!tbl) continue;
    const d = el(`<details class="auxfold"><summary>` +
      'auxiliary table folded — the verdict rests on another ' +
      'result (expand for the map)' + `</summary></details>`);
    tbl.replaceWith(d); d.appendChild(tbl);
  }
  // RW-5 (capture gate): answer-first folded-rounds layout — every
  // panel of this turn folds to its one-line stamped headline
  // (fold, never hide: every receipt stays one click away), and the
  // conclusion card seats ABOVE them.
  let anchor = null;
  for (const panel of turnPanels) {
    const head = panel.querySelector('.headline');
    const line = head ? head.textContent :
      (panel.querySelector('.ref') || {}).textContent || 'result';
    const fold = el(`<details class="roundfold"></details>`);
    const sum = el(`<summary class="rf-sum"></summary>`);
    sum.textContent = line;
    fold.appendChild(sum);
    panel.parentNode.insertBefore(fold, panel);
    fold.appendChild(panel);
    if (!anchor) anchor = fold;
  }
  // RW-10 (the answer format contract): the conclusion card is
  // MACHINE-COMPOSED from stamped fields; prose is additive color.
  // It renders ONCE, on top (RW-9: the duplicate path is deleted).
  const card = renderConclusion(j);
  if (card) {
    if (anchor) anchor.parentNode.insertBefore(card, anchor);
    else add(card);
  }
  if (j.loop_status) {
    add(el(`<div class="loopline">${esc(j.loop_status)}${
      j.loop_note ? ' — ' + esc(j.loop_note) : ''}</div>`));
  }
    renderFeedback(j.turn_index);
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

// ---- ask (walk W2: live trail via SSE; JSON /api/ask is the
// fallback so the workbench still answers if streaming breaks) ------

const pendingNodes = new Map();
let stageNode = null;
let skeletonNode = null;   // RW-18a: the streamed card skeleton

function keyOf(c) {
  return (c.op || '') + '|' + JSON.stringify(c.params || {}) + '|' +
    (c.auto_round || 0);
}

function clearStage() {
  if (stageNode) { stageNode.remove(); stageNode = null; }
  if (skeletonNode) { skeletonNode.remove(); skeletonNode = null; }
  pendingNodes.forEach(n => n.remove());
  pendingNodes.clear();
}

function handleStreamEvent(name, data) {
  if (name === 'output') {
    if (data.pending) {
      // the ACTUAL op dispatching — named status, never a fake spinner
      const node = add(el(`<div class="runline"><span class="dot"></span>
        <span class="oplabel">${esc(data.component.op)}</span>
        <span>${esc(JSON.stringify(data.component.params))}</span>
        <span>running…</span></div>`));
      pendingNodes.set(keyOf(data.component), node);
      return;
    }
    const p = pendingNodes.get(keyOf(data.component || {}));
    if (p) { p.remove(); pendingNodes.delete(keyOf(data.component || {})); }
    renderOutput(data);
    return;
  }
  if (name === 'stage') {
    const label = data.stage === 'verdict'
      ? 'filing the typed verdict (machine-verified)…'
      : data.stage === 'parse'
      ? 'reading your question…'
      : 'honesty gate checking the answer…';
    if (stageNode) stageNode.remove();
    stageNode = add(el(`<div class="runline"><span class="dot"></span>
      <span>${esc(label)}</span></div>`));
    return;
  }
  // RW-18a: the iteration-card SKELETON — renders the instant the
  // parse lands; per-entity matches fill in as grounding queries
  // complete (parallel server-side). The blank before the card dies.
  if (name === 'card') {
    if (data.parse_line) {
      if (stageNode) { stageNode.remove(); stageNode = null; }
      skeletonNode = add(el(`<div class="rs parsecard"><div class="head">
        <span class="badge complete">understanding</span>
        <span class="universe">${esc(data.parse_line)}</span></div>
        <div class="showbox skelbox">matching
        ${esc(String(data.entities.length))} entit${
        data.entities.length === 1 ? 'y' : 'ies'}…</div></div>`));
      return;
    }
    if (data.store_waking && skeletonNode) {
      // RW-25: the idle-wake retry is VISIBLE, never a blank
      skeletonNode.querySelector('.skelbox').appendChild(
        el(`<div class="showline">store waking from idle —
          retrying…</div>`));
      return;
    }
    if (data.grounded && skeletonNode) {
      const g = data.grounded;
      const names = g.matches.map(m => m.name).join(', ')
        || 'no catalog match';
      skeletonNode.querySelector('.skelbox').appendChild(
        el(`<div class="showline">matched <b>${esc(g.entity)}</b>:
          ${esc(names)}</div>`));
    }
  }
}

async function askViaStream(message, noPlanner) {
  const resp = await fetch('/api/ask/stream', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ message, conversation_id: conversationId,
      planner: noPlanner ? false : undefined })});
  if (!resp.ok || !resp.body) throw new Error('stream unavailable');
  const reader = resp.body.getReader();
  const dec = new TextDecoder();
  let buf = '', final = null, errmsg = null;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf('\\n\\n')) >= 0) {
      const block = buf.slice(0, i); buf = buf.slice(i + 2);
      let ev = null, data = '';
      for (const line of block.split('\\n')) {
        if (line.startsWith('event: ')) ev = line.slice(7).trim();
        else if (line.startsWith('data: ')) data += line.slice(6);
      }
      if (!ev || !data) continue;
      const payload = JSON.parse(data);
      if (ev === 'done') final = payload;
      else if (ev === 'error') errmsg = payload.error || 'engine error';
      else handleStreamEvent(ev, payload);
    }
  }
  clearStage();
  if (errmsg) throw new Error(errmsg);
  if (!final) throw new Error('stream ended without a result');
  return final;
}

// RW-18c: the confirm click streams — op chips at dispatch, results
// at completion (the askViaStream reader, on the confirm endpoint)
async function confirmViaStream(excluded) {
  const resp = await fetch('/api/parse/confirm/stream', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ conversation_id: conversationId,
                           exclude_ids: excluded })});
  if (!resp.ok || !resp.body) throw new Error('stream unavailable');
  const reader = resp.body.getReader();
  const dec = new TextDecoder();
  let buf = '', final = null, refused = null;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf('\\n\\n')) >= 0) {
      const block = buf.slice(0, i); buf = buf.slice(i + 2);
      let ev = null, data = '';
      for (const line of block.split('\\n')) {
        if (line.startsWith('event: ')) ev = line.slice(7).trim();
        else if (line.startsWith('data: ')) data += line.slice(6);
      }
      if (!ev || !data) continue;
      const payload = JSON.parse(data);
      if (ev === 'done') final = payload;
      else if (ev === 'refusal') refused = payload;
      else handleStreamEvent(ev, payload);
    }
  }
  clearStage();
  if (refused) return { refused_message: refused.message ||
    refused.error || 'the plan was refused' };
  if (!final) throw new Error('stream ended without a result');
  return final;
}

async function askViaJson(message, noPlanner) {
  const r = await fetch('/api/ask', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ message, conversation_id: conversationId,
      planner: noPlanner ? false : undefined })});
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || ('error ' + r.status));
  (j.outputs || []).forEach(renderOutput);
  return j;
}

// ADR 0062: the ITERATION CARD — show what the graph matched,
// propose the reading, ask; nothing executes before the click.
// The developer door is on EVERY round (ruled 08-29): a standing
// option, never a last resort.
function renderParseCard(j, message) {
  if (skeletonNode) { skeletonNode.remove(); skeletonNode = null; }
  const showRows = (j.show || []).map(s => {
    const ms = s.matches.length
      ? s.matches.map(m =>
          `<label class="matchrow"><input type="checkbox" checked
            data-id="${esc(m.id)}"> ${esc(m.name)}
            <span class="cite">${esc(m.kind || '')}</span></label>`
        ).join('')
      : '<span class="universe">no catalog match</span>';
    return `<div class="showline">matched
      <b>${esc(s.entity)}</b>: ${ms}</div>`;
  }).join('');
  // no_match (RULED: no silent fallback): nothing composes, so no
  // run button — the rephrase text, the engine button, and the
  // developer door remain (no dead ends)
  const runBtn = j.no_match ? ''
    : '<button class="primary confirmparse">run this plan</button>';
  // RW-25: a named remedy IS a button — the store-error card
  // carries "retry now", never retry-in-prose alone
  const retryBtn = j.retry
    ? '<button class="primary retrybtn">retry now</button>' : '';
  const badge = j.no_match ? 'no match' : 'understanding';
  const card = add(el(`<div class="rs parsecard"><div class="head">
    <span class="badge complete">${badge}</span>
    <span class="universe">${esc(j.parse_confirm)}</span></div>
    <div class="showbox">${showRows}</div>
    <div class="parsebtns">
    ${runBtn}${retryBtn}
    <button class="skipparse">answer without the planner</button>
    <button class="doorbtn">none of these is right —
      contact a developer</button>
    </div></div>`));
  const retryEl = card.querySelector('.retrybtn');
  if (retryEl) retryEl.addEventListener('click', async () => {
    card.querySelectorAll('button').forEach(b => b.disabled = true);
    try {
      let jj;
      try { jj = await askViaStream(message); }
      catch (e1) { clearStage(); jj = await askViaJson(message); }
      conversationId = jj.conversation_id;
      if (jj.parse_confirm && !jj.planned) renderParseCard(jj, message);
      else renderFinale(jj);
    } catch (e2) {
      add(el(`<div class="loopline">${esc(e2.message)}</div>`));
    }
    askbtn.disabled = false;
  });
  // RW-19: the door wires on EVERY card (it is the point of the
  // no-match card); only the run button is variant-conditional —
  // its listener attaches below, guarded on the element existing
  card.querySelector('.doorbtn').addEventListener('click',
    async () => {
      card.querySelectorAll('button').forEach(b => b.disabled = true);
      const r = await fetch('/api/escalate', { method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ conversation_id: conversationId,
                               question: message })});
      const jj = await r.json();
      const link = jj.mailto
        ? ` <a href="${esc(jj.mailto)}">open email</a>` : '';
      add(el(`<div class="rs"><div class="head">
        <span class="badge complete">captured demand</span>
        <span class="universe">sent to the developer queue — a
        developer will arrive already knowing what you asked and
        what the graph lacked${link}</span></div>
        <pre class="errdetail">${esc(jj.summary)}</pre></div>`));
      askbtn.disabled = false;
    });
  const runEl = card.querySelector('.confirmparse');
  if (runEl) runEl.addEventListener('click',
    async () => {
      // unchecked matches are PRUNED — the one confirm ratifies
      // the pruned reading (no-nag: its ops then run freely)
      const excluded = Array.from(
        card.querySelectorAll('input[type=checkbox]'))
        .filter(c => !c.checked).map(c => c.dataset.id);
      card.querySelectorAll('button').forEach(b => b.disabled = true);
      // RW-18c: each op chip renders at dispatch, the stamped
      // result at completion — the post-confirm blank dies; JSON
      // is the fallback if streaming breaks
      let jj = null, refusal = null;
      try {
        jj = await confirmViaStream(excluded);
      } catch (e1) {
        clearStage();
        const r = await fetch('/api/parse/confirm', { method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ conversation_id: conversationId,
                                 exclude_ids: excluded })});
        jj = await r.json();
        if (!r.ok) refusal = jj;
        else (jj.outputs || []).forEach(renderOutput);
      }
      if (jj && jj.refused_message) refusal = jj;
      if (refusal) {
        add(el(`<div class="loopline">${esc(refusal.message ||
          refusal.refused_message || refusal.error ||
          'the plan was refused')}</div>`));
        askbtn.disabled = false;
        return;
      }
      renderFinale(jj);
      askbtn.disabled = false;
    });
  card.querySelector('.skipparse').addEventListener('click',
    async () => {
      card.querySelectorAll('button').forEach(b => b.disabled = true);
      try {
        let jj;
        try { jj = await askViaStream(message, true); }
        catch (e1) { clearStage(); jj = await askViaJson(message, true); }
        conversationId = jj.conversation_id;
        renderFinale(jj);
      } catch (e2) {
        add(el(`<div class="loopline">${esc(e2.message)}</div>`));
      }
      askbtn.disabled = false;
    });
  return card;   // RW-19: the DOM smoke inspects the wired card
}

document.getElementById('ask').addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = q.value.trim();
  if (!message) return;
  q.value = ''; askbtn.disabled = true;
  turnHeadlines = [];
  turnPanels = [];
  add(el(`<p class="you">you&gt; ${esc(message)}</p>`));
  try {
    let j;
    try {
      j = await askViaStream(message);        // outputs rendered live
    } catch (e1) {
      clearStage();
      j = await askViaJson(message);          // fallback renders them
    }
    conversationId = j.conversation_id;
    if (j.parse_confirm && !j.planned) {
      renderParseCard(j, message);   // the click owns what runs next
      q.focus();
      return;
    }
    renderFinale(j);
  } catch (e2) {
    clearStage();
    add(el(`<p class="err">${esc(e2.message || e2)}</p>`));
  }
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
