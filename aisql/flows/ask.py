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

from aisql.flows import connect, grounding, produce
from aisql.graph import kg3_artifacts, phi_gate
from aisql.lenses import ask_index, decisions
from aisql.lenses.ask_index import _fold

# literal: schema-mirror lenses.Ask_Views
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
    out = {"mentions": clean[:MAX_MENTIONS]}
    # the proposal (nine-law dig): the Interpreter may also PROPOSE
    # expansions (search strings), KIND-MARKS (word -> node type,
    # validated against the closed metamodel list = physics),
    # REFERENCE-ROLES (the anaphor word list died — L4-D3), and a
    # DISPLAY HINT (preselects a view, visibly — L4-D4). All of it
    # proposal, none of it action; confirmation is what makes any
    # of it stick.
    raw_exp = raw.get("expansions")
    if isinstance(raw_exp, dict):
        exp = {}
        for m, alts in raw_exp.items():
            if m in out["mentions"] and isinstance(alts, list):
                good = [a.strip() for a in alts
                        if isinstance(a, str) and a.strip()][:5]
                if good:
                    exp[m] = good
        if exp:
            out["expansions"] = exp
    # a 'kinds' field is STRIPPED (THE SEARCH IS THE ANSWER: the
    # model never proposes type targets; type words hit the label
    # entries by vector like everything else)
    # relation-marks (prompt 3.1.0, ruled 2026-09-12): the
    # Interpreter flags which mentions are RELATION WORDS — a role
    # classification like reference-roles (L4-D3), never a type
    # target; only mentions qualify, anything else is refused
    raw_rel = raw.get("relations")
    if isinstance(raw_rel, list):
        rel = []
        for m in raw_rel:
            if isinstance(m, str) and m in out["mentions"] \
                    and m not in rel:
                rel.append(m)
        if rel:
            out["relations"] = rel
    raw_refs = raw.get("references")
    if isinstance(raw_refs, dict):
        refs = {}
        for m, r in raw_refs.items():
            if m in out["mentions"] and isinstance(r, str) and (
                    r in ("singular", "set")
                    or (r.startswith("ordinal:")
                        and r.split(":")[1].isdigit())):
                refs[m] = r
        if refs:
            out["references"] = refs
    hint = raw.get("hint")
    if isinstance(hint, str) and hint in DISPLAY_MODES:
        out["hint"] = hint
    return out


# ---- REMEMBER --------------------------------------------------------
def reference_set_key(groundings: List[Dict[str, Any]]) -> str:
    """The MEANING of an interpretation = what it resolved to
    (L2-D1): sorted references, phrasing-independent."""
    parts = []
    for g in groundings:
        if g["outcome"] == "label":
            parts.append(f"kind:{g['label']}")
        elif g["outcome"] == "matched":
            parts.append(f"id:{g['entity']['identity']}")
        elif g["outcome"] == "set":
            parts.append("set:context")
        else:
            parts.append(f"topic:{_fold(g['mention'])}")
    return "|".join(sorted(parts))


def ledger_interpretation(read, question: str):
    """A previously CONFIRMED interpretation for this folded question
    — the fast path of the MEANING-BOOK (L2-D1): the blessed object
    is the reference-set; the folded text key only skips the model."""
    folded = _fold(" ".join(question.split()))
    hits = [u for u in read.nodes("usage")
            if u.properties.get("action") == "confirmed"
            and u.properties.get("question_folded") == folded
            and u.properties.get("interpretation")]
    if not hits:
        return None, None
    props = hits[-1].properties
    return props["interpretation"], props.get("context_snapshot")


def confirmed_reference_sets(read) -> Dict[str, str]:
    """reference-set key -> confirmed-at date (L2-D1): a NEW
    phrasing that resolves to a confirmed set answers immediately."""
    out = {}
    for u in read.nodes("usage"):
        if u.properties.get("action") == "confirmed" \
                and u.properties.get("reference_set"):
            out[u.properties["reference_set"]] = \
                u.properties.get("occurred_at", "")
    return out


def record_confirmation(store, question: str,
                        interpretation: Dict[str, Any], author: str,
                        occurred_at: str, basis: str,
                        context: Optional[List[str]] = None) -> None:
    kg3_artifacts.append_usage(
        store, action="confirmed", author=author,
        occurred_at=occurred_at,
        payload=phi_gate.door1_redact(question).text)
    event = store.current_nodes("usage")[-1]
    props = dict(event.properties)
    props["question_folded"] = _fold(" ".join(question.split()))
    props["interpretation"] = dict(interpretation)
    props["basis"] = basis
    if interpretation.get("reference_set"):
        props["reference_set"] = interpretation["reference_set"]
    if context:  # Law 4: the snapshot rides — replay is deterministic
        props["context_snapshot"] = list(context)
    # supersede with the FULL properties — mutating after append
    # would leave the governance journal holding the bare event
    # (the E1 rebirth bug); one write, one journal line, whole
    return store.append_node("usage", event.identity, props,
                             occurred_at, f"kg3@{occurred_at}")


def build_index(read) -> List[Dict[str, Any]]:
    """The ask index = the VERBATIM projection of speech (ADR 0080,
    the center law): every entry's words are its node's declared
    stored property or grammar render — recomputable, never
    authored here. Conditions, parameters, and kinds join the
    surface (census 3)."""
    from aisql.flows import speech
    return speech.entries(read)


# ---- SPEAK: deterministic renderers (display modes) ------------------
def _one_line(read, identity: str, index_by_id) -> str:
    entry = index_by_id.get(identity)
    if entry is None:
        return identity
    words = (entry.get("words") or "").split(". ")[0]
    return (f"[{entry['label']}] {entry['name']}"
            + (f" — {words}" if words else ""))


def render_card(read, entity: Dict[str, Any]) -> str:
    kind = entity["label"]
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
        # R10 (grammar 2.3.0, live find #9): the report floor — the
        # census placeholder is dead; the file speaks its meaning
        lines.append(produce.compose_file_floor(read, identity))
    elif kind == "derived_column":
        # M4 store grain: the card speaks the stored R12 description
        node = next((n for n in read.nodes("derived_column")
                     if n.identity == identity), None)
        desc = ((node.properties.get("description") or "").strip()
                if node else "")
        lines.append(desc or "No description is recorded — a "
                     "counted documentation gap.")
    elif kind == "drift":
        # the literal law (E3): the drift card claim is REGISTRY
        # text (Speech_Sources drift row Card_Text)
        from aisql.graph import metamodel
        lines.append(next(
            r for r in metamodel.load("lenses").sheets["Speech_Sources"]
            if r["Label"] == "drift name")["Card_Text"])
    elif kind == "term":
        node = next(n for n in read.nodes("term")
                    if n.identity == identity)
        lines.append(node.properties.get("definition", ""))
    # literal: shape
    elif kind in ("condition", "param", "label"):
        # speech IS the card for the part-kinds (census 2): the
        # stored/rendered phrase, plus the owner chain
        lines.append(entity.get("words") or "")
        if entity.get("owner"):
            lines.append(f"Belongs to: {entity['owner']}")
    return "\n".join(lines)


def render_lineage(read, adj, entity) -> str:
    hood = connect.neighborhood(adj, entity["identity"])
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
    from aisql.lenses import census
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
        terms = [e for e in index if e["label"] == "term"]
        deliveries = sorted({e["identity"] for e in index
                             if e["label"] == "scope"
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
                      if e["label"] == kind})
    if topic_entries is not None:
        allowed = {e["identity"] for e in topic_entries}
        entries = [(n, i) for n, i in entries if i in allowed]
    if kind == "column" and len(entries) > 60 and topic_entries is None:
        return (f"{len(entries)} columns — too many to list flatly. "
                "Ground a table to see its shape.")
    lines = [f"{len(entries)} {kind}(s):"]
    # literal: shape
    lines += [f"- {n}  ({i})" if kind in ("scope", "drift",
                                          "derived_column")
              else f"- {n}" for n, i in entries[:60]]
    if len(entries) > 60:
        lines.append(f"… and {len(entries) - 60} more "
                     "(showing 60)")
    if not entries:
        lines.append("- (none)")
    return "\n".join(lines)


# ---- THE SEARCH IS THE ANSWER (ruled 2026-09-07) ---------------------
# The engine's set dispatch died with the tier ladder: mentions +
# expansions become vector queries against EVERYTHING (labels,
# names, descriptions — the facet cards); the answer is the RANKED
# SCORED HIT LIST, grouped by label. Relational filtering happens
# on demand (a set-pool beside strong hits filters by connection).


def _estate_vocabulary(index, blessed_names) -> set:
    """The estate's own words: the ask index's NAME tokens + LABEL
    tokens + blessed acronym names — NEVER speech/description text
    (stored English contains 'it'). Ruled 2026-09-20
    (Brief_Anaphor_Clarify, "agree with all four"): a
    reference-marked mention with an empty context table searches
    as text only if one of its tokens is in this set."""
    words = set(blessed_names)
    for e in index:
        words.update(ask_index._tokens(e.get("name") or ""))
        words.update(ask_index._tokens(e.get("label") or ""))
    return words


def _anchor_band(hits) -> list:
    """The ruled band (SET FORMATION 2026-09-11, landed on the
    Law-4 connection filter 2026-09-20 as a FIX): anchors are the
    non-table hits with a card >= MATCH_SCORE AND within
    UNIQUE_MARGIN of the best such card — the best over NON-TABLE
    hits only (a table entry's 1.0 card is context, never the
    anchor bar; all-cards->0.5 made 409 anchors of one mention and
    the filter could not filter)."""
    t = grounding.thresholds()
    cand = [h for h in hits if h.get("via_card") != "table"
            and h.get("best_card_score", 0) >= t["MATCH_SCORE"]]
    if not cand:
        return []
    best = max(h["best_card_score"] for h in cand)
    return [h["identity"] for h in cand
            if h["best_card_score"] >= best - t["UNIQUE_MARGIN"]]


def _connected(member_id: str, anchor_ids, adj) -> bool:
    nbrs = {n for n, _ in adj.get(member_id, [])}
    for a in anchor_ids:
        if (a in nbrs or member_id.startswith(a)
                or a.startswith(member_id)
                or member_id.split("::")[0] in a
                or a.split("::")[0] in member_id):
            return True
    return False


def present_hits(read, index_by_id, hits) -> str:
    """The ranked list, grouped by label — scores and cards visible
    (frame words; every fact line is a node)."""
    if not hits:
        return ""
    lines = []
    by_label: Dict[str, list] = {}
    for h in hits:
        by_label.setdefault(h["label"], []).append(h)
    for label in sorted(by_label,
                        key=lambda lb: -by_label[lb][0]["score"]):
        rows = by_label[label]
        # labels display as WORDS (the 2026-09-09 reserved-word
        # renames made slugs like pbi_report; users see "pbi report")
        from aisql.lenses.ask_index import _words as _lw
        lines.append(f"{_lw(label)} ({len(rows)}):")
        for h in rows[:12]:
            via = f" · via {h['via_card']}" if h.get("via_card") \
                else ""
            lines.append(f"- {h['name']} — {h['score']:.2f}{via}"
                         f"  ({h['identity']})")
        if len(rows) > 12:
            lines.append(f"  … and {len(rows) - 12} more")
    return "\n".join(lines)


_SHAPES: Dict[str, float] = {}


def response_shapes() -> Dict[str, float]:
    """L3-D1/L5-D1 margins as registry data."""
    if not _SHAPES:
        from aisql.graph import metamodel
        for r in metamodel.load("lenses").sheets["Response_Shapes"]:
            if r["Name"] != "_ruling":
                _SHAPES[r["Name"]] = float(r["Value"])
    return _SHAPES


def _provisional(g: Dict[str, Any]) -> Dict[str, Any]:
    """L3-D1: a candidates outcome with a CLEAR winner becomes a
    PROVISIONAL match — the assumption disclosed, runners-up kept.
    A disclosed, reversible assumption is not a guess."""
    if g.get("outcome") != "candidates":
        return g
    cands = g.get("candidates") or []
    if len(cands) < 1 or "score" not in cands[0]:
        return g
    margin = response_shapes()["PROVISIONAL_MARGIN"]
    if len(cands) == 1 or (cands[0]["score"]
                           - cands[1]["score"]) >= margin:
        # literal: shape
        return {"tier": g.get("tier"), "outcome": "matched",
                "entity": cands[0], "mention": g["mention"],
                "score": cands[0]["score"], "provisional": True,
                "runners_up": cands[1:4],
                "expansions_tried": g.get("expansions_tried", [])}
    return g


def _trace(groundings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The search trace (ADR 0080 rider): what was searched and how —
    rendered in every round, and the audit record either way."""
    out = []
    for g in groundings:
        # literal: shape
        row = {"mention": g.get("mention"), "tier": g.get("tier"),
               "outcome": g.get("outcome")}
        if "score" in g:
            row["score"] = g["score"]
        if g.get("expansions_tried"):
            row["expansions_tried"] = g["expansions_tried"]
        if g.get("via_expansion"):
            row["via_expansion"] = g["via_expansion"]
        out.append(row)
    return out


# ---- the pipeline ----------------------------------------------------
def ask(store, question: str, author: str, occurred_at: str,
        interpret_fn: Optional[Callable[[str], Any]] = None,
        semantic: Optional[grounding.SemanticIndex] = None,
        confirmed: Optional[Dict[str, Any]] = None,
        context: Optional[List[str]] = None) -> Dict[str, Any]:
    """THE SEARCH IS THE ANSWER: question -> the Interpreter
    (intention, mentions, expansions) -> vector search against
    everything -> ranked scored hits. Statuses: answer | clarify
    (an anaphor with nothing on the table) | form (no interpreter).
    Memory (ledger/meaning-book/proposal cache) runs before the
    model; anaphors resolve deterministically against the table."""
    from aisql.graph.read_api import ReadApi
    read = ReadApi(store)
    index = build_index(read)
    adj = connect.build_adjacency(read)
    q = " ".join(question.split())
    index_by_id = {e["identity"]: e for e in index}

    def _entities(ids):
        return [index_by_id[i] for i in (ids or [])
                if i in index_by_id]

    if context and isinstance(context[0], list):
        stack = [c for c in context if c]
    elif context:
        stack = [context]
    else:
        stack = []
    stack_entities = [_entities(c) for c in stack]

    def _usage(outcome, about=None):
        kg3_artifacts.append_usage(
            store, action="asked", author=author,
            occurred_at=occurred_at,
            payload=phi_gate.door1_redact(question).text,
            outcome=outcome, about=about)

    # MEMORY before the model: the confirmed-question ledger
    stored_context = None
    interpretation = confirmed
    if interpretation is None:
        interpretation, stored_context = ledger_interpretation(read, q)
    via = ("confirmed" if confirmed
           else "ledger" if interpretation else None)
    if via == "ledger" and context is None and stored_context:
        stack_entities = [_entities(stored_context)]
    if interpretation is None:
        if interpret_fn is None:
            _usage("no-match")
            # literal: shape
            return {"status": "form",
                    "answer": "No interpreter is available — ask "
                              "by clicking, or bring the seat back.",
                    "hits": [], "trace": []}
        try:
            raw = interpret_fn(q)
        except Exception:  # noqa: BLE001 — the seat-failure law
            _usage("no-match")
            # literal: shape
            return {"status": "form", "seat_down": True,
                    "answer": "The interpreter seat is UNAVAILABLE "
                              "— clicks, the table, and confirmed "
                              "questions still work. This failure "
                              "is counted.",
                    "hits": [], "trace": []}
        interpretation = validate_interpretation(raw)
        if interpretation is None:
            _usage("no-match")
            # literal: shape
            return {"status": "form",
                    "answer": "The interpreter's output failed "
                              "validation.",
                    "hits": [], "trace": []}
        via = "model"

    # THE SEARCH: every mention (+ its expansions) against
    # everything; anaphors resolve from the table
    merged: Dict[str, Dict[str, Any]] = {}
    trace: List[Dict[str, Any]] = []
    pools: List[List[Dict[str, Any]]] = []
    empty_table_marks = False
    floor = grounding.thresholds()["CANDIDATE_FLOOR"]
    expansions = interpretation.get("expansions") or {}
    references = interpretation.get("references") or {}
    # THE ONE-VOCABULARY LAW: blessed acronyms expand mentions
    # DETERMINISTICALLY — the same stored words the cards carry
    blessed = {n.properties["name"].lower():
               n.properties["expansions"]
               for n in read.nodes("acronym")}
    estate_words = None
    for m in interpretation["mentions"]:
        role = references.get(m)
        if role is not None:
            pool = stack_entities[0] if stack_entities else []
            if not pool:
                # a role-mark is a PROPOSAL, never a veto (the live
                # 22:27 corpse: an over-marked 'ED' killed 24 found
                # hits). Empty table -> the mention is SEARCHED AS
                # TEXT; the hard clarify happens below only if
                # nothing anywhere answers.
                role = None
                references = dict(references)
                references.pop(m, None)
                empty_table_marks = True
                # THE ESTATE-VOCABULARY GATE (ruled 2026-09-20,
                # Brief_Anaphor_Clarify): text search is for words
                # that could NAME something here — name/label
                # tokens + blessed acronyms, never speech ('it' vs
                # the name card 'ett' scored 0.6322; a pronoun and
                # a short name separate by no threshold)
                if estate_words is None:
                    estate_words = _estate_vocabulary(index, blessed)
                if not any(t in estate_words
                           for t in ask_index._tokens(m)):
                    # literal: shape
                    trace.append({"mention": m, "tier": "gate",
                                  "outcome": "no-estate-word",
                                  "searched_as": m, "hits": 0,
                                  "note": "reference-marked, the "
                                          "table is empty, and no "
                                          "token names anything in "
                                          "this estate — not "
                                          "searched"})
                    continue
        if role is not None:
            pool = stack_entities[0]
            if role.startswith("ordinal:"):
                n = int(role.split(":")[1])
                if not (1 <= n <= len(pool)):
                    _usage("ambiguous")
                    # literal: shape
                    return {"status": "clarify", "mention": m,
                            "candidates": [], "hits": [],
                            "reason": f"the table holds {len(pool)}"
                                      f" item(s); '{m}' points past"
                                      " it",
                            "answer": f"the table holds {len(pool)}"
                                      f" item(s); '{m}' points past"
                                      " it",
                            "trace": trace}
                chosen = [pool[n - 1]]
            elif role == "set":
                chosen = list(pool)
                pools.append(chosen)
            else:  # singular: the head of the table
                chosen = [pool[0]]
            for e in chosen:
                # literal: shape
                merged.setdefault(e["identity"], {
                    "identity": e["identity"], "label": e["label"],
                    "name": e["name"], "score": 0.0,
                    "best_card_score": 1.0, "via_card": "table"})
                merged[e["identity"]]["score"] += 1.0
            # literal: shape
            trace.append({"mention": m, "tier": "table",
                          "outcome": "resolved",
                          "searched_as": m, "hits": len(chosen)})
            continue
        vocab_exp = []
        for tok in ask_index._tokens(m):
            vocab_exp += [x for x in blessed.get(tok, [])
                          if x.lower() not in m.lower()]
        searched_as = " ".join([m] + vocab_exp
                               + [x for x in expansions.get(m, [])
                                  if x not in vocab_exp])
        # literal: shape
        row = {"mention": m, "tier": "search",
               "searched_as": searched_as, "hits": 0}
        if empty_table_marks and m not in references \
                and (interpretation.get("references") or {}).get(m):
            row["note"] = ("reference-marked but the table is "
                           "empty — searched as text")
        if expansions.get(m):
            row["expansions_tried"] = expansions[m]
        if semantic is not None:
            try:
                # the FULL index per mention — a pre-merge top-k cut
                # silently broke the total-score law (measured
                # 2026-09-09: the dashboard's label credit for
                # 'reports' fell outside a 100-cut and its
                # cross-mention sum lost it); the band applies
                # AFTER the merge, never before
                found = semantic.search(searched_as,
                                        top_k=len(index) or 1)
            except Exception:  # noqa: BLE001 — seat-failure law
                found = []
                row["seat_down"] = True
            kept = [h for h in found if h["score"] >= floor]
            row["hits"] = len(kept)
            row["strong"] = sum(
                1 for h in kept if h.get("best_card_score", 0)
                >= grounding.thresholds()["MATCH_SCORE"])
            # ONE contribution per identity per mention (the index
            # may carry duplicate entries; a mention never
            # double-counts) — cross-mention sums remain the boost
            best_of: Dict[str, Dict[str, Any]] = {}
            for h in kept:
                b = best_of.get(h["identity"])
                if b is None or h["score"] > b["score"]:
                    best_of[h["identity"]] = h
            for h in best_of.values():
                # literal: shape
                cur = merged.setdefault(h["identity"], {
                    "identity": h["identity"], "label": h["label"],
                    "name": h["name"], "score": 0.0,
                    "best_card_score": 0.0,
                    "via_card": h.get("via_card")})
                cur["score"] += h["score"]
                cur["best_card_score"] = max(
                    cur.get("best_card_score", 0.0),
                    h.get("best_card_score", 0.0))
        trace.append(row)

    # on-demand connection: a set-pool beside strong searched hits
    # filters by connection (Law 4's follow-up filtering, preserved)
    if pools:
        anchors = _anchor_band(list(merged.values()))
        if anchors:
            pool_ids = {e["identity"] for p in pools for e in p}
            for pid in list(merged):
                h = merged[pid]
                if h["via_card"] == "table" \
                        and pid in pool_ids \
                        and not _connected(pid, anchors, adj):
                    del merged[pid]

    hits = sorted(merged.values(),
                  key=lambda h: (-h["score"], h["identity"]))
    band = int(response_shapes().get("CLARIFY_CAP", 6)) * 8
    hits = hits[:band]
    for h in hits:
        h["score"] = round(h["score"], 4)

    # MATCH is judged at CARD grain (2026-09-09, the real-physics
    # finding): the SUM ranks, but "is anything a real match?" asks
    # for one card at MATCH_SCORE — under real embeddings 'it'
    # sums floor-dribbles past 0.5 on half the estate, and the
    # honest pure-anaphor clarify died until this split
    strong = any(h.get("best_card_score", 0)
                 >= grounding.thresholds()["MATCH_SCORE"]
                 for h in hits)
    if empty_table_marks and not strong:
        # every road ended: reference-marked mentions, no table,
        # and the text search found nothing strong — THIS is the
        # honest "nothing to refer back to"
        _usage("ambiguous")
        # literal: shape
        return {"status": "clarify", "mention": q,
                "candidates": [], "hits": [],
                "reason": "nothing to refer back to — ask a "
                          "direct question first",
                "answer": "nothing to refer back to — ask a "
                          "direct question first",
                "trace": trace}
    if not hits:
        answer = (f"Nothing found for '{q}' — searched all "
                  f"{len(index)} named and described things in "
                  "this estate (labels, names, descriptions). "
                  "Rephrase, or click a group in the estate card.")
    else:
        answer = present_hits(read, index_by_id, hits)
    new_set = [h["identity"] for h in hits][:100]
    if via == "ledger" and stored_context:
        old, new = set(stored_context), set(new_set)
        added, gone = len(new - old), len(old - new)
        if added or gone:
            answer = (f"[changed since you confirmed this: "
                      f"+{added} new, -{gone} gone]\n" + answer)
    about = hits[0]["identity"] if len(hits) == 1 else None
    _usage("matched" if hits else "no-match", about)
    # literal: shape
    result = {"status": "answer", "answer": answer, "hits": hits,
              "via": via, "context_set": new_set, "trace": trace,
              "groundings": []}
    if via == "model":
        ref_key = reference_set_key_from_hits(interpretation, hits)
        known = confirmed_reference_sets(read)
        if ref_key in known:
            result["via"] = "meaning-book"
            result["resolved_to_confirmed"] = known[ref_key]
        else:
            interpretation = dict(interpretation)
            interpretation["reference_set"] = ref_key
            result["pending_confirmation"] = True
            result["interpretation"] = interpretation
    return result


def reference_set_key_from_hits(interpretation, hits) -> str:
    """The meaning of a search = its mentions + expansions (the
    resolved hits vary as the graph moves; the QUESTION's meaning
    is what the human blesses)."""
    parts = [f"m:{_fold(m)}" for m in interpretation["mentions"]]
    for m, alts in (interpretation.get("expansions") or {}).items():
        parts += [f"x:{_fold(a)}" for a in alts]
    return "|".join(sorted(parts))


def confirm(store, question: str, interpretation: Dict[str, Any],
            author: str, occurred_at: str,
            semantic: Optional[grounding.SemanticIndex] = None,
            basis: str = "model:unspecified",
            context: Optional[List[str]] = None) -> Dict[str, Any]:
    """The human blessed a fresh interpretation: record it (with its
    context snapshot, Law 4), then execute it as a ledger
    interpretation."""
    event = record_confirmation(store, question, interpretation,
                                author, occurred_at, basis,
                                context=context)
    result = ask(store, question, author, occurred_at,
                 interpret_fn=None, semantic=semantic,
                 confirmed=interpretation, context=context)
    # ADR 0080 + step 2 (the birth-edge law): confirming BLESSES the
    # expansions into KG3 terms, each citing the confirming event —
    # the click becomes a walkable edge
    grounded = [g["entity"]["identity"]
                for g in result.get("groundings", [])
                if g.get("outcome") == "matched"]
    for m, alts in (interpretation.get("expansions") or {}).items():
        for alt in alts:
            kg3_artifacts.append_term(
                store, f"term::vocab/{_fold(m)}", m,
                f"{m} — confirmed ask vocabulary for: {alt}",
                author, occurred_at,
                basis={"label": "ask-expansion", "basis": basis},
                derived_from=[event.identity],
                about=grounded[:8] or None)
    return result


def _earned_vocabulary(read) -> Dict[str, str]:
    """Word -> kind, EARNED (v1.20.0 — the mapping table died):
    confirmed kind-mappings live as KG3 terms with parent
    'kind::<K>'. The LLM proposed, the human confirmed, the ledger
    remembers — deterministic forever after."""
    out: Dict[str, str] = {}
    for n in read.nodes("term"):
        parent = n.properties.get("parent") or ""
        if parent.startswith("kind::"):
            out[_fold(n.properties.get("name", ""))] = \
                parent.removeprefix("kind::")
    return out
