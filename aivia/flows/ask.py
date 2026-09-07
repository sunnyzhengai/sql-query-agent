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
# the closed kind list = the metamodel's searchable kinds (physics)
# + 'metric' (the practiced/governed pair ruling)
VALID_KINDS = ("file", "table", "column", "scope", "condition",
               "derived column", "term", "drift", "parameter",
               "metric", "kind")


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
    raw_kinds = raw.get("kinds")
    if isinstance(raw_kinds, dict):
        marks = {m: k for m, k in raw_kinds.items()
                 if m in out["mentions"] and isinstance(k, str)
                 and k in VALID_KINDS}
        if marks:
            out["kinds"] = marks
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
        if g["outcome"] == "kind":
            parts.append(f"kind:{g['kind']}")
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
    event.properties["question_folded"] = _fold(
        " ".join(question.split()))
    event.properties["interpretation"] = dict(interpretation)
    event.properties["basis"] = basis
    if interpretation.get("reference_set"):
        event.properties["reference_set"] = \
            interpretation["reference_set"]
    if context:  # Law 4: the snapshot rides — replay is deterministic
        event.properties["context_snapshot"] = list(context)


def build_index(read) -> List[Dict[str, Any]]:
    """The ask index = the VERBATIM projection of speech (ADR 0080,
    the center law): every entry's words are its node's declared
    stored property or grammar render — recomputable, never
    authored here. Conditions, parameters, and kinds join the
    surface (census 3)."""
    from aivia.flows import speech
    return speech.entries(read)


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
        # R10 (grammar 2.3.0, live find #9): the report floor — the
        # census placeholder is dead; the file speaks its meaning
        lines.append(produce.compose_file_floor(read, identity))
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
    elif kind in ("condition", "parameter", "kind"):
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


# ---- THE ONE ENGINE (L4-D1) ------------------------------------------
# Every grounded mention is a SET of nodes; the engine CONNECTS the
# sets; the DISPLAY SET is chosen by the user's own words (a named
# kind is the answer shape). Nothing is ever classified — the old
# branch dispatch died here (the dig's death warrant, executed).


def _sets_from(groundings, index):
    """grounding outcomes -> typed node-sets."""
    sets = []
    for g in groundings:
        if g["outcome"] == "kind":
            kind = g["kind"]
            if kind == "metric":
                members = [e for e in index if e["kind"] == "scope"
                           and "::delivery" in e["identity"]]
            elif kind == "kind":
                members = [e for e in index if e["kind"] == "kind"]
            else:
                members = [e for e in index if e["kind"] == kind]
            sets.append({"shape": "kindset", "kind": kind,
                         "members": members, "g": g})
        elif g["outcome"] == "matched":
            sets.append({"shape": "one", "members": [g["entity"]],
                         "g": g})
        elif g["outcome"] == "set":
            sets.append({"shape": "pool", "members": g["entities"],
                         "g": g})
        else:  # topic: an ungrounded mention riding an anchor
            sets.append({"shape": "topic", "members": [],
                         "text": " ".join(
                             [g["mention"]]
                             + g.get("expansions_tried", [])),
                         "g": g})
    # terms ARE vocabulary: beside a named kind, a matched term is
    # the TOPIC (its name filters), never a graph anchor
    if any(t["shape"] == "kindset" for t in sets):
        for t in sets:
            if t["shape"] == "one" \
                    and t["members"][0].get("kind") == "term":
                t["shape"] = "topic"
                t["text"] = t["members"][0]["name"]
                t["members"] = []
    return sets


def _connected(member, anchor_ids, adj):
    """ONE connection test: a direct edge, or identity containment
    (ownership chains are identity prefixes by construction)."""
    nbrs = {n for n, _ in adj.get(member["identity"], [])}
    mid = member["identity"]
    owner = member.get("owner") or ""
    for a in anchor_ids:
        if (a in nbrs or mid.startswith(a) or a.startswith(mid)
                or owner.startswith(a) or a.startswith(owner)
                or mid.split("::")[0] in a
                or a.split("::")[0] in mid):
            return True
    return False


def _topic_filter(members, topic_text, kind, index, index_by_id,
                  semantic):
    """Connect a member-set to a TOPIC: word-grain name/speech
    containment (whole tokens, CamelCase split) + semantic adds +
    facet rollup with card provenance. Returns (by_name, by_meaning,
    by_facet, facet_via, note)."""
    want_tokens = ask_index._tokens(topic_text)

    def tokens_of(e):
        return ask_index._tokens(
            f"{e['name']} {e.get('words') or ''}")
    by_name = [e for e in members
               if want_tokens and want_tokens <= tokens_of(e)]
    named_ids = {e["identity"] for e in by_name}
    by_meaning, facet_via, note = [], {}, ""
    member_ids = {e["identity"] for e in members}
    if semantic is not None:
        floor = grounding.thresholds()["CANDIDATE_FLOOR"]
        try:
            for h in semantic.search(topic_text, top_k=40,
                                     kind=None):
                if h["identity"] in member_ids \
                        and h["score"] >= grounding.MATCH_SCORE \
                        and h["identity"] not in named_ids:
                    by_meaning.append(h)
            # facet rollup: a hit on a PART surfaces its owner in
            # the member set, the card named (census 3)
            for h in semantic.search(topic_text, top_k=60):
                if h["score"] < floor or not h.get("owner"):
                    continue
                owner_id, hops = h["owner"], 0
                while owner_id and hops < 4:
                    owner = index_by_id.get(owner_id)
                    if owner is None:
                        break
                    if owner["identity"] in member_ids:
                        facet_via.setdefault(
                            owner["identity"],
                            f"{h['kind']}: "
                            f"{(h.get('words') or h['name'])[:70]}"
                            f" · {h['score']}")
                        break
                    owner_id = owner.get("owner")
                    hops += 1
        except Exception:  # noqa: BLE001 — seat-failure law
            note = " [meaning tier unavailable — name matches only]"
    seen = named_ids | {e["identity"] for e in by_meaning}
    by_facet = [index_by_id[i] for i in facet_via
                if i in index_by_id and i not in seen]
    return by_name, by_meaning, by_facet, facet_via, note


def execute(read, index, adj, groundings: List[Dict[str, Any]],
            semantic: Optional[grounding.SemanticIndex]):
    """-> (text, listed_ids). ONE algorithm: sets -> connect ->
    present; the display set is the user's own named shape."""
    index_by_id = {e["identity"]: e for e in index}
    sets = _sets_from(groundings, index)
    kindsets = [t for t in sets if t["shape"] == "kindset"]
    ones = [t for t in sets if t["shape"] == "one"]
    pools = [t for t in sets if t["shape"] == "pool"]
    topics = [t for t in sets if t["shape"] == "topic"]

    # THE DISPLAY SET: the user's named kind wins; else a pool
    # (anaphor); else the subject/path of the singletons
    display = (kindsets[0] if kindsets
               else pools[0] if pools
               else None)

    if display is not None:
        members = display["members"]
        seen = set()
        members = [m for m in members
                   if not (m["identity"] in seen
                           or seen.add(m["identity"]))]
        kind_word = display.get("kind") or "item"
        # ENTITY ANCHORS contribute BOTH connection candidates AND
        # their names as topic text (the find-#5 truth and the
        # ownership truth, one rule): buckets are disjoint in
        # precedence order connected -> by name -> by meaning ->
        # via parts; "connected" prints only when nonzero.
        anchors = [t["members"][0] for t in ones]
        pool = display["members"] if display["shape"] == "kindset" \
            else members
        connected = []
        if anchors and (topics or display["shape"] == "kindset"):
            anchor_ids = [a["identity"] for a in anchors]
            connected = [m for m in members
                         if _connected(m, anchor_ids, adj)]
        elif anchors:
            anchor_ids = [a["identity"] for a in anchors]
            members = [m for m in members
                       if _connected(m, anchor_ids, adj)]
        topic_texts = [t["text"] for t in topics] \
            + [a["name"] for a in anchors
               if display["shape"] == "kindset"]
        facet_via, note = {}, ""
        provenance = None
        if topic_texts:
            want_all = " ".join(topic_texts)
            by_name, by_meaning, by_facet, fv, note = _topic_filter(
                members, want_all, kind_word, index, index_by_id,
                semantic)
            facet_via.update(fv)
            # bucket precedence for "about" evidence: NAME first
            # (the find-#5 truth), structural connection as the
            # remainder, then meaning, then parts
            name_ids = {m["identity"] for m in by_name}
            connected = [m for m in connected
                         if m["identity"] not in name_ids]
            members = by_name + connected + by_meaning + by_facet
            provenance = (
                f"({len(by_name)} by name, "
                + (f"{len(connected)} more connected, "
                   if connected else "")
                + f"{len(by_meaning)} more by meaning, "
                f"{len(by_facet)} via their parts)")
        # PRESENT the display set
        if display["shape"] == "pool":
            names = ", ".join(a["name"] for a in anchors) \
                or "the context"
            lines = [f"{len(members)} of them"
                     + (f" connect to {names}:" if anchors else ":")]
            for m in members[:40]:
                lines.append(
                    f"- {_one_line(read, m['identity'], index_by_id)}"
                    f"  ({m['identity']})")
            if len(members) > 40:
                lines.append(f"… and {len(members) - 40} more")
            if not members:
                lines.append("- (none)")
            return ("\n".join(lines),
                    [m["identity"] for m in members][:100])
        if not topics and not anchors:
            # the bare kind census — render_kind_list keeps its
            # ruled forms (incl. the practiced/governed metric pair)
            return (render_kind_list(read, index, display["kind"],
                                     None),
                    [e["identity"] for e in members][:100])
        want = " · ".join(topic_texts) \
            or " ".join(a["name"] for a in anchors)
        header = (f"{len(members)} {kind_word}(s) about '{want}' "
                  + (provenance or "(connected)") + f"{note}:")
        lines = [header]
        for m in members[:40]:
            line = f"- {_one_line(read, m['identity'], index_by_id)}"
            if m["identity"] in facet_via:
                line += f"  — via {facet_via[m['identity']]}"
            lines.append(line)
        if len(members) > 40:
            lines.append(f"… and {len(members) - 40} more")
        if not members:
            lines.append("- (none — an honest zero, counted)")
        return ("\n".join(lines),
                [m["identity"] for m in members][:100])

    # no display set: singletons connect as a PATH, or one speaks
    entities = [t["members"][0] for t in ones]
    if len(entities) >= 2:
        weights = connect.edge_weights()
        lines = []
        listed = [e["identity"] for e in entities]
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
                if node not in listed:
                    listed.append(node)
        return "\n".join(lines), listed[:100]
    if len(entities) == 1:
        entity = entities[0]
        card = render_card(read, entity)
        hood = connect.neighborhood(adj, entity["identity"])
        extra = []
        listed = [entity["identity"]]
        for label in sorted(hood):
            members = hood[label]
            extra.append(f"- {label}: " + ", ".join(members[:8])
                         + (f" … ({len(members) - 8} more)"
                            if len(members) > 8 else ""))
            listed += [m for m in members if m not in listed]
        return (card + ("\n\nConnected:\n" + "\n".join(extra)
                        if extra else ""), listed[:100])
    return ("Nothing grounded — the graph carries none of these "
            "names or meanings."), []


_SHAPES: Dict[str, float] = {}


def response_shapes() -> Dict[str, float]:
    """L3-D1/L5-D1 margins as registry data."""
    if not _SHAPES:
        from aivia.graph import metamodel
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
        return {"tier": g.get("tier"), "outcome": "matched",
                "entity": cands[0], "mention": g["mention"],
                "score": cands[0]["score"], "provisional": True,
                "runners_up": cands[1:4],
                "expansions_tried": g.get("expansions_tried", [])}
    return g


def _shape_clarify(candidates: List[Dict[str, Any]]
                   ) -> Dict[str, Any]:
    """L3-D2 clarify obligations: dedup at NAME grain (one row,
    'in N places'), group by kind, cap visibly. Choosing between
    meanings, never identifiers."""
    by_name: Dict[tuple, Dict[str, Any]] = {}
    for c in candidates:
        key = (c["kind"], c["folded"])
        if key in by_name:
            by_name[key]["places"] += 1
            continue
        row = dict(c)
        row["places"] = 1
        by_name[key] = row
    kind_rank = {k: i for i, k in enumerate(VALID_KINDS)}
    rows = sorted(by_name.values(),
                  key=lambda r: (kind_rank.get(r["kind"], 99),
                                 -(r.get("score") or 0)))
    cap = int(response_shapes()["CLARIFY_CAP"])
    if len(rows) == 1 and rows[0]["places"] > 1:
        # one NAME in many places (live find #1's class): the choice
        # IS the place — expand back to the identities
        rows = candidates
    return {"rows": rows[:cap],
            "more": max(0, len(rows) - cap)}


def _trace(groundings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The search trace (ADR 0080 rider): what was searched and how —
    rendered in every round, and the audit record either way."""
    out = []
    for g in groundings:
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
    """One ask. Statuses: answer | confirm (fresh model interpretation
    awaiting the human) | clarify (a mention needs a pick) | form
    (no interpreter available and nothing grounded). `context` is the
    previous answer's CONTEXT SET (Law 4): identity strings, subject
    first — anaphors resolve against it and every answer returns the
    next one as result["context_set"]."""
    from aivia.graph.read_api import ReadApi
    read = ReadApi(store)
    index = build_index(read)
    kind_words = _earned_vocabulary(read)
    adj = connect.build_adjacency(read)
    q = " ".join(question.split())
    index_by_id = {e["identity"]: e for e in index}

    def _entities(ids):
        return [index_by_id[i] for i in (ids or []) if i in index_by_id]

    def _context_set(groundings, listed):
        out = [g["entity"]["identity"] for g in groundings
               if g["outcome"] == "matched"]
        out += [i for i in listed if i not in out]
        return out[:100]

    # L5-D1 THE STACKED TABLE: context may be a flat id-list (one
    # round) or a stack of rounds (newest first). Bare anaphors
    # resolve against the TOP; kind-qualified ones walk DOWN to the
    # nearest matching pool.
    if context and isinstance(context[0], list):
        stack = [c for c in context if c]
    elif context:
        stack = [context]
    else:
        stack = []
    stack_entities = [_entities(c) for c in stack]
    context_entities = stack_entities[0] if stack_entities else None

    def _usage(outcome, about=None):
        kg3_artifacts.append_usage(
            store, action="asked", author=author,
            occurred_at=occurred_at,
            payload=phi_gate.door1_redact(question).text,
            outcome=outcome, about=about)

    # deterministic pre-tier: the WHOLE question as one mention —
    # bare-name and pure-anaphor asks never touch a model (GR-1, FU)
    whole = _provisional(
        grounding.ground(q, index, kind_words, None,
                         context=context_entities))
    if whole["outcome"] in ("matched", "kind", "set"):
        answer, listed = execute(read, index, adj, [whole], semantic)
        about = (whole["entity"]["identity"]
                 if whole["outcome"] == "matched" else None)
        _usage("matched", about)
        return {"status": "answer", "answer": answer,
                "groundings": [whole], "via": "deterministic",
                "context_set": _context_set([whole], listed),
                "trace": _trace([whole])}
    if whole["outcome"] == "clarify-context":
        _usage("ambiguous")
        return {"status": "clarify", "mention": q, "candidates": [],
                "answer": whole["reason"], "reason": whole["reason"]}
    if whole["outcome"] == "candidates":
        _usage("ambiguous")
        shaped = _shape_clarify(whole["candidates"])
        return {"status": "clarify", "mention": q,
                "candidates": shaped["rows"],
                "more_candidates": shaped["more"],
                "trace": _trace([whole])}

    stored_context = None
    interpretation = confirmed
    if interpretation is None:
        interpretation, stored_context = ledger_interpretation(read, q)
    via = ("confirmed" if confirmed
           else "ledger" if interpretation else None)
    if via == "ledger" and context is None and stored_context:
        # FU-4: the confirmed snapshot rides — replay is deterministic
        context_entities = _entities(stored_context)
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

    def _ground_with_vocab(m):
        # the proposal's kind-mark grounds the mention as a KIND
        # (validated against the closed list; the mapping table
        # died — the LLM proposes, the graph's physics validates)
        mark = (interpretation.get("kinds") or {}).get(m)
        if mark:
            return {"tier": "proposed-kind", "outcome": "kind",
                    "kind": mark, "mention": m}
        role = (interpretation.get("references") or {}).get(m)
        if role is not None and len(stack_entities) > 1:
            # walk the stack: top first; a kind-qualified anaphor
            # that finds nothing on top reaches down (L5-D1)
            g = None
            for pool in stack_entities:
                g = grounding.ground(m, index, kind_words, semantic,
                                     context=pool, role=role)
                if g["outcome"] == "matched" or (
                        g["outcome"] == "set" and g["entities"]):
                    break
        else:
            g = grounding.ground(m, index, kind_words, semantic,
                                 context=context_entities, role=role)
        tried = []
        rank = {"matched": 3, "kind": 3, "set": 3, "candidates": 2}
        if g["outcome"] in ("unknown", "candidates"):
            # the ledger's vocabulary is DATA: a KG3 term whose name
            # folds to the mention lends its definition as an
            # expansion — deterministic, no model (ADR 0080 rider)
            term = next((e for e in index if e["kind"] == "term"
                         and e["folded"] == _fold(m)
                         and e["words"]), None)
            if term:
                tried.append(term["words"])
        for exp in (interpretation.get("expansions") or {}).get(m, []):
            if exp not in tried:
                tried.append(exp)
        for exp in tried:
            if g["outcome"] in ("matched", "kind", "set"):
                break
            g2 = grounding.ground(exp, index, kind_words, semantic)
            if rank.get(g2["outcome"], 1) > rank.get(g["outcome"], 1):
                g2["mention"] = m
                g2["via_expansion"] = exp
                g = g2
        if tried:
            g["expansions_tried"] = tried
        return g

    groundings = [_provisional(_ground_with_vocab(m))
                  for m in interpretation["mentions"]]
    anchored = any(g["outcome"] in ("kind", "matched", "set")
                   for g in groundings)
    for g in groundings:
        if g["outcome"] == "clarify-context":
            _usage("ambiguous")
            return {"status": "clarify", "mention": g["mention"],
                    "candidates": [], "answer": g["reason"],
                    "reason": g["reason"],
                    "interpretation": interpretation,
                    "trace": _trace(groundings)}
        if anchored:
            # ADR 0080 / CE-4: while an anchor stands, an ungrounded
            # mention is a TOPIC, never a dead end — emptiness will
            # answer as an honest counted zero downstream
            continue
        if g["outcome"] == "candidates":
            _usage("ambiguous")
            shaped = _shape_clarify(g["candidates"])
            return {"status": "clarify", "mention": g["mention"],
                    "candidates": shaped["rows"],
                    "more_candidates": shaped["more"],
                    "interpretation": interpretation,
                    "trace": _trace(groundings)}
        if g["outcome"] == "unknown":
            _usage("no-match")
            # L9-D4: an absence answer is a DOOR — the searched
            # universe, the nearest true things, and the next act
            door = (f"NO MATCH for '{g['mention']}' — nothing in "
                    f"the graph carries that name or meaning "
                    f"(searched all {len(index)} named things in "
                    "this estate)."
                    + ("\nNearest: " + ", ".join(
                        e["name"] for e in g["nearest"])
                       if g.get("nearest") else "")
                    + "\nNext: rephrase, confirm a vocabulary "
                    "expansion, or flag this to the steward — "
                    "repeated asks for the same missing thing are "
                    "demand signal.")
            return {"status": "answer", "answer": door,
                    "groundings": groundings, "via": via,
                    "trace": _trace(groundings)}

    if via == "model":
        # L2-D1 MEANING-BOOK: a new phrasing resolving to an
        # already-confirmed reference-set answers as CONFIRMED —
        # what was blessed was the meaning, not the words
        ref_key = reference_set_key(groundings)
        known = confirmed_reference_sets(read)
        if ref_key in known:
            answer, listed = execute(read, index, adj, groundings,
                                     semantic)
            about = None
            matched = [g for g in groundings
                       if g["outcome"] == "matched"]
            if len(matched) == 1:
                about = matched[0]["entity"]["identity"]
            _usage("matched", about)
            return {"status": "answer", "answer": answer,
                    "groundings": groundings,
                    "via": "meaning-book",
                    "resolved_to_confirmed": known[ref_key],
                    "context_set": _context_set(groundings, listed),
                    "trace": _trace(groundings)}
        interpretation = dict(interpretation)
        interpretation["reference_set"] = ref_key
        # L7-D2 INLINE CONFIRMATION: every mention grounded -> the
        # provisional answer SHIPS with the confirm attached
        # (non-blocking); the interpretation enters the ledger only
        # when the human clicks. Blocking confirms died with the
        # dispatch — the engine is never "stuck" once all mentions
        # ground.
        answer, listed = execute(read, index, adj, groundings,
                                 semantic)
        about = None
        matched = [g for g in groundings
                   if g["outcome"] == "matched"]
        if len(matched) == 1:
            about = matched[0]["entity"]["identity"]
        _usage("matched", about)
        return {"status": "answer", "answer": answer,
                "groundings": groundings, "via": via,
                "pending_confirmation": True,
                "interpretation": interpretation,
                "context_set": _context_set(groundings, listed),
                "trace": _trace(groundings)}

    answer, listed = execute(read, index, adj, groundings, semantic)
    about = None
    matched = [g for g in groundings if g["outcome"] == "matched"]
    if len(matched) == 1:
        about = matched[0]["entity"]["identity"]
    _usage("matched", about)
    new_set = _context_set(groundings, listed)
    if via == "ledger" and stored_context:
        # L8-D4 THE CHANGE CAPTION: same confirmed question, moved
        # truth — say so; the diff recomputes, never stores
        old, new = set(stored_context), set(new_set)
        added, gone = len(new - old), len(old - new)
        if added or gone:
            answer = (f"[changed since you confirmed this: "
                      f"+{added} new, -{gone} gone]\n" + answer)
    return {"status": "answer", "answer": answer,
            "groundings": groundings, "via": via,
            "context_set": new_set,
            "trace": _trace(groundings)}


def confirm(store, question: str, interpretation: Dict[str, Any],
            author: str, occurred_at: str,
            semantic: Optional[grounding.SemanticIndex] = None,
            basis: str = "model:unspecified",
            context: Optional[List[str]] = None) -> Dict[str, Any]:
    """The human blessed a fresh interpretation: record it (with its
    context snapshot, Law 4), then execute it as a ledger
    interpretation."""
    record_confirmation(store, question, interpretation, author,
                        occurred_at, basis, context=context)
    result = ask(store, question, author, occurred_at,
                 interpret_fn=None, semantic=semantic,
                 confirmed=interpretation, context=context)
    # ADR 0080: confirming an interpretation BLESSES its expansions —
    # they land as KG3 terms (vocabulary is data; the LLM proposed,
    # the human confirmed, the ledger remembers)
    for m, alts in (interpretation.get("expansions") or {}).items():
        for alt in alts:
            kg3_artifacts.append_term(
                store, f"term::vocab/{_fold(m)}", m,
                f"{m} — confirmed ask vocabulary for: {alt}",
                author, occurred_at,
                basis={"kind": "ask-expansion", "basis": basis})
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
