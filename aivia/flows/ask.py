"""The ask pipeline (ADR 0079): UNDERSTAND -> GROUND -> CONNECT ->
SPEAK -> STEER -> REMEMBER. The keyword grammar is DELETED (the
never-regex law): no pattern ever decides what a question means. The
interpreter and embedder are INJECTED callables — tests stay
hermetic; the console wires real models. Display modes are buttons
the user presses, never intents a model classifies. Every ask lands
an H5 usage event; every confirmed interpretation lands in the
ledger and repeat questions skip the model entirely.
"""
from typing import Any, Callable, Dict, List, Optional

from aivia.flows import connect, grounding, produce
from aivia.graph import kg3_artifacts, phi_gate
from aivia.lenses import ask_index, decisions
from aivia.lenses.ask_index import _fold

DISPLAY_MODES = ("card", "lineage", "filters", "readers", "census")
MAX_MENTIONS = 5


# ---- UNDERSTAND ------------------------------------------------------
def validate_interpretation(raw: Any) -> Optional[Dict[str, Any]]:
    """The cage: the interpreter may return ONLY a mentions list —
    non-empty strings, capped. Anything else is refused (parse,
    never generate; a refusal degrades to the form, never a guess)."""
    if not isinstance(raw, dict):
        return None
    mentions = raw.get("mentions")
    if not isinstance(mentions, list) or not mentions:
        return None
    clean = [m.strip() for m in mentions
             if isinstance(m, str) and m.strip()]
    if not clean or len(clean) > MAX_MENTIONS:
        return None
    return {"mentions": clean[:MAX_MENTIONS]}


# ---- REMEMBER --------------------------------------------------------
def ledger_interpretation(read, question: str) -> Optional[Dict[str, Any]]:
    """A previously CONFIRMED interpretation for this folded question
    — the interpretation is cached, never the answer."""
    folded = _fold(" ".join(question.split()))
    hits = [u for u in read.nodes("usage")
            if u.properties.get("action") == "confirmed"
            and u.properties.get("question_folded") == folded
            and u.properties.get("interpretation")]
    return hits[-1].properties["interpretation"] if hits else None


def record_confirmation(store, question: str,
                        interpretation: Dict[str, Any], author: str,
                        occurred_at: str, basis: str) -> None:
    kg3_artifacts.append_usage(
        store, action="confirmed", author=author,
        occurred_at=occurred_at,
        payload=phi_gate.door1_redact(question).text)
    event = store.current_nodes("usage")[-1]
    event.properties["question_folded"] = _fold(
        " ".join(question.split()))
    event.properties["interpretation"] = dict(interpretation)
    event.properties["basis"] = basis


# ---- SPEAK: deterministic renderers (display modes) ------------------
def _one_line(read, identity: str, index_by_id) -> str:
    entry = index_by_id.get(identity)
    if entry is None:
        return identity
    words = (entry.get("words") or "").split(". ")[0]
    return (f"[{entry['kind']}] {entry['name']}"
            + (f" — {words}" if words else ""))


def render_card(read, entity: Dict[str, Any]) -> str:
    kind = entity["kind"]
    identity = entity["identity"]
    lines = [f"{kind.upper()}: {entity['name']}  [{identity}]", ""]
    if kind in ("table", "column"):
        node = next(n for n in read.nodes(kind)
                    if n.identity == identity)
        desc = (node.properties.get("description") or "").strip()
        lines.append(desc or "No description is recorded — a counted "
                     "documentation gap.")
    elif kind == "scope":
        lines.append(produce.compose_floor(read, identity))
    elif kind == "file":
        tree = next(t for k, t in read.trees().items()
                    if k == identity or t["name"] == identity)
        names = [s["name_key"].split("::")[-1]
                 for stmt in tree["statements"]
                 for s in ([stmt.get("scope")] if stmt.get("scope")
                           else []) if "name_key" in (s or {})]
        lines.append(f"A procedure of {len(tree['statements'])} "
                     f"steps; named selections: "
                     f"{', '.join(names[:12]) or '(none)'}.")
    elif kind == "derived column":
        scope_key = identity.rsplit(".", 1)[0]
        lines.append(f"A computed output of {scope_key} — ask the "
                     "selection for its floor.")
    elif kind == "drift":
        lines.append("READER/WRITER DRIFT: this name is read by the "
                     "estate's SQL but declared by no dictionary and "
                     "no catalog — a silently-failing report until a "
                     "human fixes the report or the dictionary. "
                     "Counted forever.")
    elif kind == "term":
        node = next(n for n in read.nodes("term")
                    if n.identity == identity)
        lines.append(node.properties.get("definition", ""))
    return "\n".join(lines)


def render_lineage(read, adj, entity) -> str:
    hood = connect.neighborhood(adj, entity["identity"])
    readers = hood.get("reads", []) + hood.get("cites", [])
    lines = [f"Lineage of {entity['name']}:"]
    for label in sorted(hood):
        members = hood[label]
        shown = members[:12]
        lines.append(f"- {label}: " + ", ".join(shown)
                     + (f" … ({len(members) - 12} more)"
                        if len(members) > 12 else ""))
    if not hood:
        lines.append("- no edges recorded")
    return "\n".join(lines)


def render_filters(read, entity) -> str:
    wanted = {entity["identity"]}
    found = []
    for key, tree in sorted(read.trees().items()):
        for scope in decisions.named_scopes(tree):
            for pred in decisions.membership_predicates(scope):
                cited = False

                def walk(n):
                    nonlocal cited
                    if isinstance(n, dict):
                        if n.get("resolves_to") in wanted:
                            cited = True
                        for v in n.values():
                            walk(v)
                    elif isinstance(n, list):
                        for v in n:
                            walk(v)
                walk(pred)
                if cited and not decisions.is_degenerate(pred):
                    voice = produce._Voice(read, tree)
                    phrase = produce._voice_predicate(pred, voice)
                    if phrase:
                        note = pred.get("annotation")
                        if note:
                            phrase = (phrase.rstrip(".") +
                                      f" (annotated '{note}' in the "
                                      "source).")
                        found.append(f"- {scope['name_key']}: {phrase}")
    header = f"{len(found)} filter(s) cite {entity['name']}:"
    return "\n".join([header] + (found[:40] or ["- (none)"])
                     + ([f"… and {len(found) - 40} more"]
                        if len(found) > 40 else []))


def render_readers(read, adj, entity) -> str:
    hood = connect.neighborhood(adj, entity["identity"])
    scopes = sorted(set(hood.get("cites", []) + hood.get("reads", [])))
    scopes = [s for s in scopes if "::" in s]
    files = sorted({s.split("::")[0] for s in scopes})
    usage = [u for u in read.nodes("usage")
             if u.properties.get("about") == entity["identity"]]
    return "\n".join(
        [f"Read by {len(scopes)} selection(s) across "
         f"{len(files)} file(s):"]
        + [f"- {s}" for s in scopes[:30]]
        + ([f"… and {len(scopes) - 30} more"]
           if len(scopes) > 30 else [])
        + [f"Recorded usage events: {len(usage)}"])


def render_census(read) -> str:
    from aivia.lenses import census
    gc = census.lens_gap_census(read, None)
    drift = sum(t["resolution_census"].get("unresolved_refs", 0)
                for t in read.trees().values())
    lines = ["THE GAP TAXONOMY (ruled-silent = ok forever; open = "
             "needs resolution):"]
    lines += [f"- {k}: {v}" for k, v in sorted(gc.items())
              if isinstance(v, int)]
    lines.append(f"- drift refs (estate findings): {drift}")
    return "\n".join(lines)


def render_kind_list(read, index, kind: str,
                     topic_entries: Optional[List[Dict[str, Any]]]
                     = None) -> str:
    if kind == "metric":
        terms = [e for e in index if e["kind"] == "term"]
        deliveries = sorted({e["identity"] for e in index
                             if e["kind"] == "scope"
                             and "::delivery" in e["identity"]})
        lines = ["GOVERNED metrics (minted concepts): 0 — a concept "
                 "is born only when a HUMAN blesses a family (the "
                 "lens computes; a human touch mints). Accepted "
                 f"terms so far: {len(terms)}.", "",
                 f"PRACTICED metrics ({len(deliveries)} delivery "
                 "selections — what the report procedures actually "
                 "emit):"]
        lines += [f"- {d}" for d in deliveries[:40]]
        if len(deliveries) > 40:
            lines.append(f"… and {len(deliveries) - 40} more")
        return "\n".join(lines)
    entries = sorted({(e["name"], e["identity"]) for e in index
                      if e["kind"] == kind})
    if topic_entries is not None:
        allowed = {e["identity"] for e in topic_entries}
        entries = [(n, i) for n, i in entries if i in allowed]
    if kind == "column" and len(entries) > 60 and topic_entries is None:
        return (f"{len(entries)} columns — too many to list flatly. "
                "Ground a table to see its shape.")
    lines = [f"{len(entries)} {kind}(s):"]
    lines += [f"- {n}  ({i})" if kind in ("scope", "drift",
                                          "derived column")
              else f"- {n}" for n, i in entries[:60]]
    if len(entries) > 60:
        lines.append(f"… and {len(entries) - 60} more "
                     "(showing 60)")
    if not entries:
        lines.append("- (none)")
    return "\n".join(lines)


# ---- CONNECT + SPEAK: execute a grounded interpretation --------------
def execute(read, index, adj, groundings: List[Dict[str, Any]],
            semantic: Optional[grounding.SemanticIndex]) -> str:
    index_by_id = {e["identity"]: e for e in index}
    kinds = [g for g in groundings if g["outcome"] == "kind"]
    entities = [g["entity"] for g in groundings
                if g["outcome"] == "matched"]
    topics = [g["mention"] for g in groundings
              if g["outcome"] not in ("kind", "matched")]

    # kind (+ optional topic): the filtered enumeration — the class
    # of Sunny's live finds #2 and #4. Live find #5 (the missing 7
    # sepsis reports): NAME CONTAINMENT is deterministic and runs
    # over the ENTIRE kind first; the semantic tier ADDS meaning
    # matches on top of it — never a truncated pool deciding the set,
    # and the answer states which tier found what.
    if kinds:
        kind = kinds[0]["kind"]
        topic_texts = topics + [e["name"] for e in entities]
        if topic_texts and kind != "metric":
            want = " ".join(topic_texts)
            want_words = ask_index._words(want)
            kind_entries = [e for e in index if e["kind"] == kind]
            by_name = [e for e in kind_entries
                       if want_words and
                       (want_words in ask_index._words(e["name"])
                        or want_words in (e.get("words") or ""))]
            named_ids = {e["identity"] for e in by_name}
            by_meaning = []
            meaning_note = ""
            if semantic is not None:
                try:
                    for h in semantic.search(want, top_k=40,
                                             kind=kind):
                        if h["score"] >= grounding.MATCH_SCORE \
                                and h["identity"] not in named_ids:
                            by_meaning.append(h)
                except Exception:  # noqa: BLE001 — seat-failure law:
                    meaning_note = (" [meaning tier unavailable — "
                                    "name matches only]")
            matched = by_name + by_meaning
            header = (f"{len(matched)} {kind}(s) about '{want}' "
                      f"({len(by_name)} by name, {len(by_meaning)} "
                      f"more by meaning){meaning_note}:")
            body = render_kind_list(read, index, kind, matched)
            return header + "\n" + body.split("\n", 1)[1] \
                if "\n" in body else header
        return render_kind_list(read, index, kind, None)

    if len(entities) >= 2:
        weights = connect.edge_weights()
        lines = []
        a = entities[0]
        for b in entities[1:]:
            path = connect.shortest_path(adj, weights,
                                         a["identity"], b["identity"])
            if path is None:
                lines.append(f"No recorded path connects "
                             f"{a['name']} and {b['name']}.")
                continue
            lines.append(f"How {a['name']} connects to {b['name']} "
                         f"({len(path) - 1} hop(s)):")
            for node, label in path:
                arrow = f"  —{label}→ " if label else "• "
                lines.append(arrow +
                             _one_line(read, node, index_by_id))
        return "\n".join(lines)

    if len(entities) == 1:
        entity = entities[0]
        card = render_card(read, entity)
        hood = connect.neighborhood(adj, entity["identity"])
        extra = []
        for label in sorted(hood):
            members = hood[label]
            extra.append(f"- {label}: " + ", ".join(members[:8])
                         + (f" … ({len(members) - 8} more)"
                            if len(members) > 8 else ""))
        return card + ("\n\nConnected:\n" + "\n".join(extra)
                       if extra else "")

    return ("Nothing grounded — the graph carries none of these "
            "names or meanings.")


# ---- the pipeline ----------------------------------------------------
def ask(store, question: str, author: str, occurred_at: str,
        interpret_fn: Optional[Callable[[str], Any]] = None,
        semantic: Optional[grounding.SemanticIndex] = None,
        confirmed: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """One ask. Statuses: answer | confirm (fresh model interpretation
    awaiting the human) | clarify (a mention needs a pick) | form
    (no interpreter available and nothing grounded)."""
    from aivia.graph.read_api import ReadApi
    read = ReadApi(store)
    index = ask_index.lens_ask_index(read, None)["yield"]
    kind_words = _kind_vocabulary()
    adj = connect.build_adjacency(read)
    q = " ".join(question.split())

    def _usage(outcome, about=None):
        kg3_artifacts.append_usage(
            store, action="asked", author=author,
            occurred_at=occurred_at,
            payload=phi_gate.door1_redact(question).text,
            outcome=outcome, about=about)

    # deterministic pre-tier: the WHOLE question as one mention —
    # bare-name asks never touch a model (GR-1)
    whole = grounding.ground(q, index, kind_words, None)
    if whole["outcome"] in ("matched", "kind"):
        answer = execute(read, index, adj, [whole], semantic)
        about = (whole["entity"]["identity"]
                 if whole["outcome"] == "matched" else None)
        _usage("matched", about)
        return {"status": "answer", "answer": answer,
                "groundings": [whole], "via": "deterministic"}
    if whole["outcome"] == "candidates":
        _usage("ambiguous")
        return {"status": "clarify", "mention": q,
                "candidates": whole["candidates"]}

    interpretation = confirmed or ledger_interpretation(read, q)
    via = ("confirmed" if confirmed
           else "ledger" if interpretation else None)
    if interpretation is None:
        if interpret_fn is None:
            _usage("no-match")
            return {"status": "form",
                    "answer": "No interpreter is available and the "
                              "question grounds to nothing directly — "
                              "use the structured form."}
        try:
            raw = interpret_fn(q)
        except Exception:  # noqa: BLE001 — THE SEAT-FAILURE LAW (ADR
            # 0079 Law 3, live find #6): a seat failure is an OUTCOME,
            # never an exception — deterministic tiers stay alive, the
            # degradation is bannered, the failure is countable
            _usage("no-match")
            return {"status": "form", "seat_down": True,
                    "answer": "The interpreter seat is UNAVAILABLE "
                              "right now — exact names, identities, "
                              "and kind words still answer, and the "
                              "structured form works. This failure "
                              "is counted."}
        interpretation = validate_interpretation(raw)
        if interpretation is None:
            _usage("no-match")
            return {"status": "form",
                    "answer": "The interpreter's output failed "
                              "validation — use the structured form."}
        via = "model"

    groundings = [grounding.ground(m, index, kind_words, semantic)
                  for m in interpretation["mentions"]]
    for g in groundings:
        if g["outcome"] == "candidates":
            _usage("ambiguous")
            return {"status": "clarify", "mention": g["mention"],
                    "candidates": g["candidates"],
                    "interpretation": interpretation}
        if g["outcome"] == "unknown":
            _usage("no-match")
            return {"status": "answer",
                    "answer": f"NO MATCH for '{g['mention']}' — "
                              "nothing in the graph carries that name "
                              "or meaning."
                              + ("\nNearest: " + ", ".join(
                                  e["name"] for e in g["nearest"])
                                 if g.get("nearest") else ""),
                    "groundings": groundings, "via": via}

    if via == "model":
        # fresh model interpretation: the human confirms before it
        # enters the ledger (plan -> confirm -> execute -> display)
        _usage("ambiguous")
        return {"status": "confirm", "interpretation": interpretation,
                "groundings": groundings}

    answer = execute(read, index, adj, groundings, semantic)
    about = None
    matched = [g for g in groundings if g["outcome"] == "matched"]
    if len(matched) == 1:
        about = matched[0]["entity"]["identity"]
    _usage("matched", about)
    return {"status": "answer", "answer": answer,
            "groundings": groundings, "via": via}


def confirm(store, question: str, interpretation: Dict[str, Any],
            author: str, occurred_at: str,
            semantic: Optional[grounding.SemanticIndex] = None,
            basis: str = "model:unspecified") -> Dict[str, Any]:
    """The human blessed a fresh interpretation: record it, then
    execute it as a ledger interpretation."""
    record_confirmation(store, question, interpretation, author,
                        occurred_at, basis)
    return ask(store, question, author, occurred_at,
               interpret_fn=None, semantic=semantic,
               confirmed=interpretation)


def _kind_vocabulary() -> Dict[str, str]:
    """Word -> kind, FROM THE REGISTRY (v1.10.0): vocabulary is
    meaning and lands as ruled data, never code."""
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Kind_Vocabulary"]
    return {row["Word"].upper(): row["Kind"] for row in sheet
            if row["Word"] != "_ruling"}
