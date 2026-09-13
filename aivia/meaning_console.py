"""THE MEANING-TEST CONSOLE (Design_Chatbot.md, ruled by Sunny
2026-09-11): gates verify STRUCTURE, this console tests MEANING —
per ACCEPTED ladder batch, over the store-as-built. First target:
THE TECHNICAL LAYER (M1–M3 accepted 2026-09-11).

The loop (THE MATCHED GRAPH, ruled same day — the crown rule is
dead): (1) an NL question — (2) the LLM interprets and TOKENIZES,
its only seat — (3) SET FORMATION: each token's match is a SET
(exact hits all equal citizens; semantic hits the band =
MATCH_SCORE + UNIQUE_MARGIN), the label constraint shapes it
before banding (proposal, never a veto), a kind claims its token
by subsumption, a PIN (the human act) replaces the set — (4) THE
SHAPE LADDER, deterministic: connected sets ENUMERATE their
existing edges · disconnected sets pathfind (the minimal
connecting subgraph is the FALLBACK for missing structure) · one
member = neighborhood · one set many members = the list · nothing
= the honest zero; the GQL is a displayed ARTIFACT (paste-able
into Fabric), executed LOCALLY until M12 lands vectors on node
rows — (5) DELIVERY BY RESULT SHAPE: rows render as a table
(visible cap, counted remainder, the conservation line), plus THE
TURN DEFAULT: every round OFFERS the runners-up; a click pins and
re-runs.

Three match classes: INSTANCE → set member · KIND (the _self
speech rows) → label constraint / population by subsumption ·
EDGE-KIND (Shape_Ledger edge rows) → traversal constraint. Kinds
ground by meaning, never word lists.

Usage: python3.11 -m aivia.meaning_console [estate] [port]
"""
import html
import json
import pathlib
import shutil
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Set, Tuple

from aivia import fabric_wire
from aivia.flows import ask, connect, glossary, grounding
from aivia.graph.read_api import ReadApi
from aivia.lenses.ask_index import _fold

# the accepted scope of the console's targets — instances that
# SPEAK (db/db_schema carry no speech source and are counted
# exclusions, never silent ones). SECOND TARGET (the join layer,
# ruled 2026-09-11): scopes join, their floors are the speech;
# joins are connective structure, never indexed
# literal: frame — the console's target-scope contract (the pull
# from the full index; store-grain admissions ride separately —
# THIRD TARGET: conditions + params come from the STORE, the
# census twin retires counted)
# literal: frame — the console's target-scope contract
TECHNICAL_SPEAKING = ("table", "column", "scope")
# literal: frame — the console's target-scope contract
TECHNICAL_KINDS = ("table", "column", "scope", "condition",
                   "parameter")
# literal: frame — registry kind names -> store labels
KIND_ALIAS = {"parameter": "param"}
TECHNICAL_EDGE_KINDS = ("has_part", "joins_to")
# THE NEAR-FIRST DEFAULT (ruled 2026-09-12, "all 3, go"): when an
# OWNER grain anchors a question about its OWNED logic, the answer
# is its own subtree; wider connections are counted, one click away
# literal: frame — the ownership vocabulary
OWNER_LABELS = ("scope", "file", "statement")
# literal: frame — the owned-logic populations
OWNED_POPS = ("condition", "join", "param", "derived_column")
# literal: frame — the ownership edges (downward reach)
NEAR_EDGES = ("has_part", "uses_param", "cites")
# STRUCTURE NEVER ROWS (same ruling): composite condition kinds
# frame the delivered list — they never row
# literal: frame
FRAME_KINDS = ("AND", "OR")


def _kind_label(kind_name: str) -> str:
    return KIND_ALIAS.get(kind_name, kind_name)


# ---- the index (step 3's search surface) -----------------------------
def technical_scope(read) -> Tuple[List[Dict[str, Any]],
                                   Dict[str, int]]:
    """The console's card index: technical instance entries + kind
    self-descriptions + edge-kind meanings. Returns (entries,
    exclusions) — every out-of-scope grain COUNTED."""
    full = ask.build_index(read)
    entries = [e for e in full if e["label"] in TECHNICAL_SPEAKING]
    exclusions: Dict[str, int] = {}
    for e in full:
        if e["label"] not in TECHNICAL_SPEAKING:
            # THE THIRD TARGET: the census-twin condition rows
            # retire, counted — the accepted store grains supersede
            key = ("condition_census" if e["label"] == "condition"
                   else e["label"])
            exclusions[key] = exclusions.get(key, 0) + 1
    for lbl in ("db", "db_schema"):  # present, speechless — counted
        exclusions[lbl] = sum(1 for _ in read.nodes(lbl))
    # THE THIRD TARGET (ruled 2026-09-11): the store's SCOPE-ROOTED
    # non-degenerate condition grains join — voiced phrases as the
    # speech; JOIN-ROOTED (ON) conditions stay connective structure
    # (vacuous voicings measured); degenerate counted; params join
    store = getattr(read, "_store", None)
    joins = {n.identity for n in read.nodes("join")}
    conds = {n.identity for n in read.nodes("condition")}
    join_rooted: Set[str] = set()
    if store is not None:
        kids: Dict[str, List[str]] = {}
        stack = []
        for e in store.current_edges("has_part"):
            if e.to_id in conds:
                if e.from_id in joins:
                    stack.append(e.to_id)
                elif e.from_id in conds:
                    kids.setdefault(e.from_id, []).append(e.to_id)
        while stack:
            cur = stack.pop()
            if cur in join_rooted:
                continue
            join_rooted.add(cur)
            stack.extend(kids.get(cur, []))
    for n in read.nodes("condition"):
        if n.identity in join_rooted:
            exclusions["condition_on"] = \
                exclusions.get("condition_on", 0) + 1
            continue
        if str(n.properties.get("degenerate")).lower() == "true":
            exclusions["condition_degenerate"] = \
                exclusions.get("condition_degenerate", 0) + 1
            continue
        nm = str(n.properties.get("name")
                 or n.identity.rsplit("::", 1)[-1])
        # literal: shape
        entries.append({"label": "condition",
                        "identity": n.identity, "name": nm,
                        "folded": _fold(nm),
                        "owner": n.identity.rsplit("::", 1)[0],
                        "words": str(n.properties.get("description")
                                     or "").lower()})
    for n in read.nodes("param"):
        nm = str(n.properties.get("name")
                 or n.identity.rsplit("/", 1)[-1])
        # literal: shape
        entries.append({"label": "param", "identity": n.identity,
                        "name": nm, "folded": _fold(nm),
                        "owner": None,
                        "words": str(n.properties.get("description")
                                     or "").lower()})
    # joins carry meaning but stay unindexed BY RULING — counted
    exclusions["join_structure"] = len(joins)
    from aivia.graph import metamodel
    lens = metamodel.load("lenses")
    for r in lens.sheets["Speech_Sources"]:
        name = str(r["Label"])
        if name.startswith("_self "):
            kind = name.removeprefix("_self ")
            if kind in TECHNICAL_KINDS:
                # literal: shape
                entries.append({"label": "label",
                                "identity": f"kind::{kind}",
                                "name": kind, "folded": _fold(kind),
                                "owner": None,
                                "words": str(r["Speech"])})
    # edge kinds speak their OWN speech (THE RELATION-WORD SEAT,
    # 2026-09-12): Speech_Sources _edge rows — the Shape_Ledger's
    # engineering Notes stop serving as speech
    edge_speech = {
        str(r["Label"]).removeprefix("_edge "): str(r["Speech"])
        for r in lens.sheets["Speech_Sources"]
        if str(r["Label"]).startswith("_edge ")}
    for r in lens.sheets["Shape_Ledger"]:
        if r.get("Kind") == "edge" and r.get("Name") in \
                TECHNICAL_EDGE_KINDS:
            # literal: shape
            entries.append({"label": "edge_kind",
                            "identity": f"edgekind::{r['Name']}",
                            "name": str(r["Name"]).replace("_", " "),
                            "folded": _fold(str(r["Name"])
                                            .replace("_", " ")),
                            "owner": None,
                            "words": edge_speech.get(
                                str(r["Name"]),
                                str(r.get("Notes") or ""))})
    return entries, exclusions


def technical_adjacency(read) -> Tuple[
        Dict[str, List[Tuple[str, str]]], Set[Tuple[str, str, str]]]:
    """The walk surface, both undirected (for the planner) and as
    the DIRECTED store truth (for the GQL writer): the spine
    (db—has_part→db_schema—has_part→table—has_part→column +
    table—joins_to→table) plus THE JOIN LAYER (second target):
    scope—has_part→join + join—left_side/right_side→
    table-or-scope + the reads remainder — plus THE CONDITION
    LAYER (third target, 2026-09-11, superseding the §D hold for
    the console): scope/join—has_part→condition,
    condition—has_part→condition, condition—resolves_to→
    column-or-param, uses_param."""
    adj: Dict[str, List[Tuple[str, str]]] = {}
    directed: Set[Tuple[str, str, str]] = set()

    def link(a: str, b: str, label: str) -> None:
        adj.setdefault(a, []).append((b, label))
        adj.setdefault(b, []).append((a, label))
        directed.add((a, b, label))

    db_id = next((n.identity for n in read.nodes("db")), None)
    schemas = {n.identity for n in read.nodes("db_schema")}
    for s in sorted(schemas):
        if db_id:
            link(db_id, s, "has_part")
    for n in read.nodes("table"):
        parent = n.identity.rsplit("|", 1)[0]
        if parent in schemas:
            link(parent, n.identity, "has_part")
    for n in read.nodes("column"):
        link(n.identity.rsplit("|", 1)[0], n.identity, "has_part")
    store = getattr(read, "_store", None)
    if store is not None:
        joins = {n.identity for n in read.nodes("join")}
        conds = {n.identity for n in read.nodes("condition")}
        for e in store.current_edges("joins_to"):
            link(e.from_id, e.to_id, "joins_to")
        for e in store.current_edges("has_part"):
            # scope—has_part→join · scope/join—has_part→condition
            # · condition—has_part→condition
            if e.to_id in joins or e.to_id in conds:
                link(e.from_id, e.to_id, "has_part")
        # literal: mechanical — the join + condition layers' walk
        for lbl in ("left_side", "right_side", "reads",
                    "resolves_to", "uses_param"):
            for e in store.current_edges(lbl):
                link(e.from_id, e.to_id, lbl)
    return adj, directed


# ---- step 2: the tokenizer seat (with the deterministic floor) -------
def fallback_tokens(question: str) -> List[str]:
    """The seat-failure floor: mechanical tokens — the whole
    question plus each whitespace word. No vocabulary, no meaning
    extracted (the never-regex law holds)."""
    q = " ".join(question.split())
    seen, out = set(), []
    for tok in [q] + q.split():
        f = _fold(tok)
        if f and f not in seen:
            seen.add(f)
            out.append(tok)
    return out


def tokens_from(question: str, interpret_fn
                ) -> Tuple[List[str], str, Set[str]]:
    """(tokens, seat, relations) — the interpreter's mentions ARE
    the tokens (multi-word phrases stay whole); relation-marked
    mentions ride along (prompt 3.1.0, THE RELATION-WORD SEAT: a
    role classification, validated to be mentions); any seat
    failure drops to the mechanical floor, visibly."""
    if interpret_fn is None:
        return fallback_tokens(question), "floor", set()
    try:
        proposal = interpret_fn(question)
        mentions = [m for m in (proposal.get("mentions") or [])
                    if str(m).strip()]
        if mentions:
            toks = [str(m) for m in mentions]
            rels = {str(m) for m in (proposal.get("relations")
                                     or []) if str(m) in set(toks)}
            return toks, "interpreter", rels
    except Exception:  # noqa: BLE001 — the seat-failure law: a
        # tokenizer failure is never a dead round; the mechanical
        # floor answers and the seat name says so
        return fallback_tokens(question), "floor", set()
    return fallback_tokens(question), "floor", set()


# ---- step 3: match sets (deterministic tiers, then vectors) ----------
def classify(entry: Dict[str, Any]) -> str:
    if entry["label"] == "label":
        return "kind"
    if entry["label"] == "edge_kind":
        return "edge-kind"
    return "instance"


def match_token(token: str, entries: List[Dict[str, Any]],
                semantic: Optional[grounding.SemanticIndex]
                ) -> Dict[str, Any]:
    """One token → its match set. Exact identity/name matches are
    free and certain; otherwise the vector tier reports every hit
    above the floor with its score (never a cliff)."""
    wanted = _fold(token.strip())
    exact = [e for e in entries
             if e["folded"] == wanted or _fold(e["identity"]) == wanted]
    if exact:
        # literal: shape
        return {"token": token, "tier": "exact",
                "matches": [{"score": 1.0, "class": classify(e), **e}
                            for e in exact[:grounding.TOP_K]]}
    if semantic is not None:
        t = grounding.thresholds()
        try:
            # the whole index per token — a top-k window here is a
            # CLIFF (the 2026-09-09 pre-merge-cut corpse echoed
            # 2026-09-11: 20 bulk blessings pushed the true crown
            # out of an 8-hit window); the floor decides, never k
            hits = semantic.search(token, top_k=len(entries))
        except Exception:  # noqa: BLE001 — seat down ≠ dead round
            # literal: shape
            return {"token": token, "tier": "seat-down", "matches": []}
        kept = [{"class": classify(h), **h} for h in hits
                if h["score"] >= t["CANDIDATE_FLOOR"]]
        # literal: shape
        return {"token": token, "tier": "semantic", "matches": kept}
    # literal: shape
    return {"token": token, "tier": "none", "matches": []}


def _strong(mset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The token's crown, if it clears MATCH_SCORE (exact = 1.0)."""
    ms = mset["matches"]
    if not ms:
        return None
    top = ms[0]
    if mset["tier"] == "exact":
        return top
    if top["score"] >= grounding.thresholds()["MATCH_SCORE"]:
        return top
    return None


def _token_set(mset: Dict[str, Any],
               allowed: Set[str]
               ) -> Tuple[List[Dict[str, Any]], bool]:
    """SET FORMATION (THE MATCHED-GRAPH RULING, 2026-09-11 — the
    crown rule is dead): a token's match is a SET — exact hits are
    ALL equal citizens; semantic hits form THE BAND (>= MATCH_SCORE
    and within UNIQUE_MARGIN of the best; registry thresholds).
    The label constraint applies BEFORE banding (the user's words
    pick the grain) and is a proposal, never a veto: an empty
    constrained set falls back to the unconstrained band, flagged
    True for the caller's report."""
    inst = [m for m in mset["matches"] if m["class"] == "instance"]

    def band(cands):
        if not cands:
            return []
        if mset["tier"] == "exact":
            return list(cands)
        t = grounding.thresholds()
        strong = [m for m in cands
                  if m["score"] >= t["MATCH_SCORE"]]
        if not strong:
            return []
        best = strong[0]["score"]
        return [m for m in strong
                if m["score"] >= best - t["UNIQUE_MARGIN"]]

    if allowed:
        kept = band([m for m in inst if m["label"] in allowed])
        if kept:
            return kept, False
        fallback = band(inst)
        return fallback, bool(fallback)
    return band(inst), False


# ---- step 4: the deterministic planner -------------------------------
def plan_connection(anchors: List[Dict[str, Any]],
                    adj: Dict[str, List[Tuple[str, str]]],
                    allowed: Optional[Set[str]] = None
                    ) -> Dict[str, Any]:
    """THE MINIMAL CONNECTING SUBGRAPH (the ruled starting
    algorithm): union of pairwise shortest paths between anchors.
    `allowed` is the edge-kind traversal constraint; if it
    disconnects a pair the planner retries unrestricted and REPORTS
    the relaxation — honesty over silence."""
    walk = adj
    if allowed:
        walk = {n: [(b, lbl) for b, lbl in nbrs if lbl in allowed]
                for n, nbrs in adj.items()}
    ids = [a["identity"] for a in anchors]
    paths, gaps, relaxed = [], [], []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            p = connect.shortest_path(walk, {}, ids[i], ids[j])
            if p is None and allowed:
                p = connect.shortest_path(adj, {}, ids[i], ids[j])
                if p is not None:
                    relaxed.append((ids[i], ids[j]))
            if p is None:
                gaps.append((ids[i], ids[j]))
            else:
                paths.append(p)
    nodes: List[str] = []
    edges: Set[Tuple[str, str, str]] = set()
    for p in paths:
        prev = None
        for node, label in p:
            if node not in nodes:
                nodes.append(node)
            if prev is not None:
                edges.add((prev, node, label))
            prev = node
    # literal: shape
    return {"paths": paths, "nodes": nodes, "edges": sorted(edges),
            "gaps": gaps, "relaxed": relaxed}


def write_gql(path: List[Tuple[str, str]],
              directed: Set[Tuple[str, str, str]],
              label_of: Dict[str, str]) -> str:
    """The query ARTIFACT: one Fabric-legal MATCH per pair-path,
    every hop explicit with its store direction — paste-able as-is
    (one statement per Fabric run). Never openCypher's type(r)."""
    if not path:
        return ""
    parts, filters, returns = [], [], []
    for i, (node, label) in enumerate(path):
        var = f"n{i}"
        parts.append(f"({var}:{label_of.get(node, 'table')})")
        returns.append(f"{var}.name")
        name = node.rsplit("|", 1)[-1]
        if i == 0 or i == len(path) - 1:
            filters.append(f"{var}.name = '{name}'")
        if i > 0:
            prev = path[i - 1][0]
            arrow = (f"-[:{label}]->" if (prev, node, label)
                     in directed else f"<-[:{label}]-")
            parts.insert(-1, arrow)
    return ("MATCH " + "".join(parts)
            + " FILTER " + " AND ".join(filters)
            + " RETURN " + ", ".join(returns))


def _enum_gql(anchor_label: str,
              sig: Tuple[Tuple[str, str, str], ...],
              anchors: List[Dict[str, Any]],
              pop_filter: str = "") -> str:
    """One WALKED SHAPE → one Fabric-legal MATCH (the artifact law:
    the displayed query describes the walk that produced the rows).
    The population var `a` opens the pattern, hops lead back to the
    filtered anchor `b`, and every arrow is the STORE's direction —
    the old single render pointed every hop a→b regardless of the
    store and skipped pass-through walks entirely (Sunny's
    condition-layer screenshots, 2026-09-12)."""
    names = sorted({m["name"] for m in anchors
                    if m["label"] == anchor_label})
    flt = " OR ".join(f"b.name = '{n}'" for n in names[:8])
    parts = [f"(a:{sig[-1][2]})"]
    for back, (elbl, d, _lbl) in enumerate(reversed(sig)):
        nxt = len(sig) - back - 2       # node index, walking back
        var = "b" if nxt < 0 else f"c{nxt + 1}"
        label = anchor_label if nxt < 0 else sig[nxt][2]
        arrow = f"<-[:{elbl}]-" if d == "f" else f"-[:{elbl}]->"
        parts.append(arrow + f"({var}:{label})")
    return ("MATCH " + "".join(parts)
            + f" FILTER ({flt}){pop_filter}"
            + " RETURN a.name, b.name")


def owner_qualify(rows: List[Dict[str, str]]) -> None:
    """Same-named rows disambiguate by their owner — the
    BED_STAY_ID law reaching enumeration rows (the Echo Law build,
    2026-09-12: cond#1 rendered twelve times bare; four EVENT_ID
    columns were visually identical repeat rows). A display name
    colliding across DIFFERENT identities gains owner segments
    until the collision dies; unique names stay bare."""
    def segs(ident: str) -> Tuple[List[str], str]:
        if "::" in ident:
            return ident.split("::"), "::"
        return ident.split("|"), "."
    depth: Dict[int, int] = {}
    for _ in range(4):      # deepest useful: file::scope::join::cond
        owners: Dict[str, Set[str]] = {}
        for r in rows:
            owners.setdefault(r["a"], set()).add(r["a_id"])
        clashing = {n for n, ids in owners.items() if len(ids) > 1}
        if not clashing:
            return
        moved = False
        for i, r in enumerate(rows):
            if r["a"] not in clashing:
                continue
            s, sep = segs(r["a_id"])
            d = depth.get(i, 1) + 1
            if d <= len(s):
                depth[i] = d
                r["a"] = sep.join(s[-d:])
                moved = True
        if not moved:
            return


# ---- step 5: the answer --------------------------------------------
def answer_question(question: str, interpret_fn,
                    entries: List[Dict[str, Any]],
                    semantic: Optional[grounding.SemanticIndex],
                    read, adj, directed,
                    pins: Optional[Dict[str, str]] = None,
                    reach: str = "near") -> Dict[str, Any]:
    """The whole ruled loop for one question — deterministic after
    tokenization; every outcome (no-match, gap, relaxation) is a
    returned fact, never an invention."""
    pins = pins or {}
    tokens, seat, relation_words = tokens_from(question,
                                               interpret_fn)
    # a relation-marked token grounds ONLY against structure
    # entries — its exact tier searches the structure pool, never
    # instances (the 'In'-column collision: an estate grain named
    # like a relation word must not capture it)
    struct_pool = [e for e in entries
                   if e["label"] in ("label", "edge_kind")]
    msets = [match_token(t,
                         struct_pool if t in relation_words
                         else entries, semantic)
             for t in tokens]
    # THE CHOICE STEP (ruled 2026-09-11): a pin is the HUMAN ACT —
    # it replaces the token's whole SET and outranks scores and
    # constraints. A vanished pick is an honest miss.
    pinned, pin_misses, pin_sets = [], [], {}
    for mset in msets:
        want = pins.get(mset["token"])
        if not want:
            continue
        hit = next((m for m in mset["matches"]
                    if m["identity"] == want), None)
        if hit is not None:
            pin_sets[mset["token"]] = [hit]
            pinned.append((mset["token"], hit["name"]))
        else:
            pin_misses.append((mset["token"], want))
    # kinds and edge-kinds ground from each token's crown — plus
    # THE KIND-SUBSUMPTION RULE (ruled 2026-09-11, from measured
    # scores: 'tables' -> kind 1.576 vs top table-instance 1.760,
    # the gap entirely label-card credit): same-labeled instances
    # outscoring their own kind is CIRCULAR credit — the kind
    # speaks through its members. A kind >= MATCH_SCORE whose name
    # equals the top instance's label CLAIMS the token.
    allowed_labels: Set[str] = set()
    kind_hits, edge_kinds = [], set()
    claimed: Set[str] = set()
    relation_unclaimed: List[str] = []
    bar = grounding.thresholds()["MATCH_SCORE"]
    for mset in msets:
        if mset["token"] in pin_sets:
            continue
        top = _strong(mset)
        # THE RELATION-WORD SEAT (2026-09-12): a relation-marked
        # token grounds ONLY against structure entries — it never
        # instance-anchors; clearing nothing = a COUNTED no-claim
        if mset["token"] in relation_words:
            top = next((m for m in mset["matches"]
                        if m["class"] in ("kind", "edge-kind")
                        and m["score"] >= bar), None)
            if top is None:
                relation_unclaimed.append(mset["token"])
                claimed.add(mset["token"])
                continue
        if top is None:
            continue
        # THE STRUCTURE-WORD CLAIM (2026-09-12, superseding the
        # label-agreement clause): the token's TOP-SCORING kind or
        # edge-kind entry >= MATCH_SCORE claims it BY ITS OWN
        # score — the old clause picked the kind by the noise
        # instance's label ('filters' -> kind column via
        # REF_RANGE_TYPE). Exact names still win; the pin still
        # overrides everything (THE TURN DEFAULT is the guard).
        if top["class"] == "instance" and mset["tier"] != "exact":
            claim = next((m for m in mset["matches"]
                          if m["class"] in ("kind", "edge-kind")
                          and m["score"] >= bar), None)
            if claim is not None:
                top = claim
        if top["class"] == "kind":
            kind_hits.append(top)
            allowed_labels.add(_kind_label(top["name"]))
            claimed.add(mset["token"])
        elif top["class"] == "edge-kind":
            edge_kinds.add(top["identity"].removeprefix("edgekind::"))
            claimed.add(mset["token"])
    # SET FORMATION (THE MATCHED-GRAPH RULING — the crown rule is
    # dead): every token contributes its full set; the label
    # constraint shapes it, proposal-never-veto
    inst_sets, label_relaxed, unmatched = [], [], []
    for mset in msets:
        if mset["token"] in pin_sets:
            inst_sets.append((mset["token"], pin_sets[mset["token"]]))
            continue
        if mset["token"] in claimed:
            continue
        members, relaxed = _token_set(mset, allowed_labels)
        if relaxed:
            label_relaxed.append((mset["token"],
                                  sorted(allowed_labels)))
        if members:
            inst_sets.append((mset["token"], members))
        elif not mset["matches"]:
            unmatched.append(mset["token"])
    anchors, _seen = [], set()
    for _tok, members in inst_sets:
        for m in members:
            if m["identity"] not in _seen:
                _seen.add(m["identity"])
                anchors.append(m)
    # THE KIND'S TWO FACES: its own label = a constraint (job
    # done); another label = a CONNECTION — the population joins
    inst_labels = {m["label"] for _t, ms in inst_sets for m in ms}
    enum_kinds = [_kind_label(k["name"]) for k in kind_hits
                  if _kind_label(k["name"]) not in inst_labels]
    # THE SHAPE LADDER: enumeration -> connection -> neighborhood
    # -> list -> honest zero; the matched graph decides, the
    # planner only fills MISSING structure
    rows: List[Dict[str, str]] = []
    counts: Dict[str, Any] = {}
    capped: Optional[Tuple[int, int]] = None
    described = {e["identity"]: e for e in entries}
    # THE PASS-THROUGH RULE (generalized, third target): the
    # connective labels are {join, condition} — a CHAIN of
    # connective nodes is ONE connection, cited by the phrase of
    # the connective NEAREST THE ANCHOR (the most specific truth)
    joinsmap = {n.identity: n.properties
                for n in read.nodes("join")}
    condsmap = {n.identity: n.properties
                for n in read.nodes("condition")}

    def _cite(ident: str) -> str:
        owned = "::".join(ident.split("::")[-2:])
        if ident in joinsmap:
            j = joinsmap[ident]
            return (f"via {owned}: {j.get('on', '')}").strip(": ")
        c = condsmap.get(ident, {})
        return (f"via: {str(c.get('description') or owned)[:110]}")

    def _speech(ident: str) -> str:
        e = described.get(ident)
        return ((e.get("words") or "").split(". ")[0]
                if e else "")

    # literal: shape
    plan = {"paths": [], "nodes": [], "edges": [], "gaps": [],
            "relaxed": []}
    gql: List[str] = []
    constrained_out = 0
    far_out = 0
    counted_out: Dict[str, int] = {}
    frames: List[str] = []
    if enum_kinds and anchors:
        mode = "enumeration"
        kind_label = enum_kinds[0]
        pop = {n.identity for n in read.nodes(kind_label)}
        hit_pop = set()
        seen_rows: Set[Tuple[str, str, str]] = set()
        # THE ARTIFACT LAW (2026-09-12, Sunny's condition-layer
        # screenshots): every WALKED SHAPE the delivery used is
        # recorded — (anchor label, hops as (edge, store-direction,
        # node label)) — and becomes one MATCH below
        shapes: Set[Tuple[str,
                          Tuple[Tuple[str, str, str], ...]]] = set()

        def _node_label(nid: str) -> str:
            if nid in joinsmap:
                return "join"
            if nid in condsmap:
                return "condition"
            return kind_label

        def _shape(m: Dict[str, Any],
                   hops: List[Tuple[str, str]]) -> None:
            prev, sig = m["identity"], []
            for elbl, node in hops:
                d = "f" if (prev, node, elbl) in directed else "r"
                sig.append((elbl, d, _node_label(node)))
                prev = node
            shapes.add((m["label"], tuple(sig)))

        # STRUCTURE NEVER ROWS (Sunny's ruling 2026-09-12): for a
        # condition population, composites FRAME the list,
        # degenerates and NOT-operands fold away, join-rooted ONs
        # are join structure — every exclusion counted, never lost
        not_operands: Set[str] = set()
        if kind_label == "condition":
            for a, b, lbl in directed:
                if lbl == "has_part" and b in condsmap \
                        and condsmap.get(a, {}).get("kind") == "NOT":
                    not_operands.add(b)

        def _row_class(nid: str,
                       hops: List[Tuple[str, str]]) -> str:
            if kind_label != "condition":
                return "row"
            # anything reached THROUGH a join is the join's own
            # structure — composite or not (class order matters:
            # an AND under a join is join structure, never frame)
            if any(h in joinsmap for _e, h in hops):
                return "join structure"
            p = condsmap.get(nid, {})
            if p.get("kind") in FRAME_KINDS:
                return "frame"
            if str(p.get("degenerate")).lower() == "true":
                return "degenerate"
            if nid in not_operands:
                return "folded into NOT"
            return "row"

        out_sets: Dict[str, Set[str]] = {}
        framed: Set[str] = set()

        def _row(pop_id: str, via: str, m: Dict[str, Any],
                 hops: List[Tuple[str, str]]) -> None:
            cls = _row_class(pop_id, hops)
            if cls != "row":
                out_sets.setdefault(cls, set()).add(pop_id)
                # the conjunction semantics become the FRAME of
                # the delivered list, never a row among its parts
                if cls == "frame" and pop_id not in framed \
                        and len(hops) == 1:
                    framed.add(pop_id)
                    kindw = condsmap[pop_id].get("kind")
                    owned = "::".join(pop_id.split("::")[-2:])
                    frames.append(
                        ("all of the delivered parts must hold "
                         "together" if kindw == "AND" else
                         "any one of the delivered parts suffices")
                        + f" ({owned} joins them with {kindw})")
                return
            _shape(m, hops)     # the artifact covers ROWED walks
            key = (pop_id, via, m["identity"])   # the row dedups
            if key in seen_rows:
                return
            seen_rows.add(key)
            hit_pop.add(pop_id)
            # literal: shape
            rows.append({"a": pop_id.rsplit("|", 1)[-1].split("::")[-1],
                         "edge": via, "b": m["name"],
                         "words": _speech(pop_id),
                         "a_id": pop_id, "b_id": m["identity"]})

        # THE NEAR-FIRST DEFAULT (ruled 2026-09-12): an owner
        # anchor asking about its owned logic answers from its OWN
        # subtree; the wider reach is counted, one click away —
        # an explicit relation word (edge_kinds) overrides
        near_default = (not edge_kinds and reach != "wide"
                        and kind_label in OWNED_POPS
                        and all(m["label"] in OWNER_LABELS
                                for m in anchors))
        allowed: Optional[Set[str]] = (
            set(edge_kinds) if edge_kinds
            else set(NEAR_EDGES) if near_default else None)

        def _walk_from(m: Dict[str, Any],
                       allowed_edges: Optional[Set[str]],
                       sink) -> None:
            for nbr, elbl in adj.get(m["identity"], []):
                if allowed_edges is not None \
                        and elbl not in allowed_edges:
                    continue
                start = None
                if nbr in pop:
                    sink(nbr, elbl, m, [(elbl, nbr)])
                    # THE CONDITION TREE DELIVERS WHOLE
                    # (2026-09-12): a delivered composite is ALSO
                    # connective — its parts are the meaning (the
                    # #AllMeds lesson: the AND root without its
                    # four predicates answered nothing)
                    if nbr in condsmap:
                        start = nbr
                elif nbr in joinsmap or nbr in condsmap:
                    start = nbr
                if start is None:
                    continue
                # pass-through: walk the connective CHAIN; the
                # citation is the connective nearest the anchor —
                # EXCEPT a frame (AND/OR): the frame LINE speaks
                # for the list, and a vacuous arity sentence is
                # not a citation (Sunny's live round, 2026-09-12
                # evening: "via: All 5 of its parts hold." rode
                # every filter row)
                if start in condsmap and condsmap[start].get(
                        "kind") in FRAME_KINDS:
                    via = ""
                else:
                    via = _cite(start)
                walked = {start}
                frontier = [(start, [(elbl, start)])]
                while frontier:
                    cur, hops = frontier.pop()
                    for nbr2, lbl2 in adj.get(cur, []):
                        if nbr2 == m["identity"] \
                                or nbr2 in walked:
                            continue
                        if nbr2 in pop:
                            sink(nbr2, via, m,
                                 hops + [(lbl2, nbr2)])
                            if nbr2 in condsmap:
                                walked.add(nbr2)
                                frontier.append(
                                    (nbr2,
                                     hops + [(lbl2, nbr2)]))
                        elif nbr2 in joinsmap \
                                or nbr2 in condsmap:
                            walked.add(nbr2)
                            frontier.append(
                                (nbr2, hops + [(lbl2, nbr2)]))

        for m in anchors:
            _walk_from(m, allowed, _row)
        # THE COUNTED REMAINDER (2026-09-12): a narrowed walk
        # narrows VISIBLY or not at all — the free walk counts the
        # rows the narrowing excluded (same class filter, so the
        # count means answers, never structure)
        if allowed is not None:
            free: Set[str] = set()

            def _free(p, v, m2, h):
                if _row_class(p, h) == "row":
                    free.add(p)
            for m in anchors:
                _walk_from(m, None, _free)
            outside = len(free - hit_pop)
            if edge_kinds:
                constrained_out = outside
            else:
                far_out = outside
        rows.sort(key=lambda r: (r["a"], r["b"]))
        owner_qualify(rows)
        counted_out = {k: len(v) for k, v in out_sets.items()}
        # literal: shape
        counts = {"connected": len(hit_pop),
                  "population": len(pop), "label": kind_label}
        # STRUCTURE NEVER ROWS reaches the ARTIFACT (Sunny's live
        # DIVERGE, 2026-09-12 evening: served 5 rows included the
        # 1=1 degenerate the delivery rightly excluded — the
        # displayed query must describe the delivered answer).
        # Folded NOT-operands sit deeper than any rowed shape's
        # hop count, so kind + degenerate filters restore parity.
        pop_filter = (" AND a.kind <> 'AND' AND a.kind <> 'OR'"
                      " AND a.degenerate <> 'true'"
                      if kind_label == "condition" else "")
        gql = [_enum_gql(alabel, sig, anchors, pop_filter)
               for alabel, sig in sorted(
                   shapes, key=lambda s: (len(s[1]), s))]
    elif enum_kinds:
        mode = "list"
        kind_label = enum_kinds[0]
        members = sorted(n.identity for n in read.nodes(kind_label))
        # literal: shape
        rows = [{"a": i.rsplit("|", 1)[-1].split("::")[-1],
                 "edge": "", "b": "",
                 "words": _speech(i), "a_id": i, "b_id": ""}
                for i in members]
        # literal: shape
        counts = {"connected": len(members),
                  "population": len(members), "label": kind_label}
        gql = [f"MATCH (a:{kind_label}) RETURN a.name"]
    elif len(inst_sets) >= 2:
        mode = "connection"
        plan = plan_connection(anchors, adj,
                               allowed=edge_kinds or None)
    elif len(anchors) == 1:
        mode = "neighborhood"
        a = anchors[0]["identity"]
        nbrs = adj.get(a, [])
        if len(nbrs) > 20:      # the visible cap is COUNTED,
            capped = (20, len(nbrs))  # never silent
        plan["nodes"] = [a] + [b for b, _ in nbrs][:20]
        plan["edges"] = sorted({(a, b, lbl) if (a, b, lbl) in directed
                                else (b, a, lbl)
                                for b, lbl in nbrs[:20]})
        gql = [f"MATCH (a:{anchors[0]['label']})-[e]-(b) FILTER "
               f"a.name = '{anchors[0]['name']}' "
               "RETURN a.name, b.name"]
    elif len(anchors) > 1:
        # one token, many equal citizens: the set IS the answer
        mode = "list"
        # literal: shape
        rows = [{"a": m["name"], "edge": "",
                 "b": (m["identity"].rsplit("|", 2)[-2]
                       if m["identity"].count("|") >= 2 else
                       m["label"]),
                 "words": (m.get("words") or "").split(". ")[0],
                 "a_id": m["identity"], "b_id": ""}
                for m in anchors]
        names = sorted({m["name"] for m in anchors})
        flt = " OR ".join(f"a.name = '{n}'" for n in names[:8])
        gql = [f"MATCH (a:{anchors[0]['label']}) FILTER {flt} "
               "RETURN a.name"]
    else:
        mode = "zero"
    label_of = {}
    # literal: mechanical — the walk-surface label lookup
    for lbl in ("db", "db_schema", "table", "column", "scope",
                "join", "condition", "param"):
        for n in read.nodes(lbl):
            if n.identity in plan["nodes"]:
                label_of[n.identity] = lbl
    if mode == "connection":
        gql = [write_gql(p, directed, label_of)
               for p in plan["paths"]]
    evidence = []
    anchor_ids = {m["identity"] for m in anchors}
    for ident in plan["nodes"]:
        e = described.get(ident)
        if e:
            # the ANCHOR speaks IN FULL — its speech IS the answer
            # (the #Base_Pop lesson, 2026-09-11: the first-sentence
            # cut amputated the logic the user asked for);
            # neighbors stay one-line
            words = (e.get("words") or "").strip()
            if ident not in anchor_ids:
                words = words.split(". ")[0]
            evidence.append(f"[{e['label']}] {e['name']}"
                            + (f" — {words}" if words else ""))
        elif ident in joinsmap:
            j = joinsmap[ident]
            # owner-qualified: three scopes may each have a join#1
            owned = "::".join(ident.split("::")[-2:])
            evidence.append(
                f"[join] {owned} "
                f"({j.get('joinType', '?')}) — "
                f"{j.get('description') or j.get('on', '')}")
        elif ident in condsmap:
            c = condsmap[ident]
            owned = "::".join(ident.split("::")[-2:])
            evidence.append(
                f"[condition] {owned} — "
                f"{c.get('description') or c.get('fragment', '')}")
        else:
            evidence.append(f"[{label_of.get(ident, '?')}] "
                            f"{ident.rsplit('|', 1)[-1]}")
    edge_lines = [f"{a.rsplit('|', 1)[-1]} —{lbl}→ "
                  f"{b.rsplit('|', 1)[-1]}"
                  for a, b, lbl in plan["edges"]]
    kind_lines = [f"kind '{k['name']}': {k['words']}"
                  for k in kind_hits]
    # literal: shape
    return {"question": question, "seat": seat, "tokens": tokens,
            "match_sets": msets, "anchors": anchors,
            "mode": mode, "rows": rows, "counts": counts,
            "capped": capped,
            "kind_constraints": kind_lines,
            "label_constraint": sorted(allowed_labels),
            "label_relaxed": label_relaxed,
            "pinned": pinned, "pin_misses": pin_misses,
            "edge_constraints": sorted(edge_kinds),
            "relation_unclaimed": relation_unclaimed,
            "constrained_out": constrained_out,
            "far_out": far_out, "counted_out": counted_out,
            "frames": frames, "reach": reach,
            "gql": [g for g in gql if g],
            "evidence": evidence, "edge_lines": edge_lines,
            "gaps": [(a.rsplit('|', 1)[-1], b.rsplit('|', 1)[-1])
                     for a, b in plan["gaps"]],
            "relaxed": [(a.rsplit('|', 1)[-1], b.rsplit('|', 1)[-1])
                        for a, b in plan["relaxed"]],
            "unmatched": unmatched}


# ---- the embedding cache (file-now, node-rows-at-M12) ---------------
def seed_cache(src: pathlib.Path, dst: pathlib.Path) -> bool:
    """Vectors are content-keyed (identity|card|texthash|model) —
    identical technical identities make another estate's cache a
    lawful seed. Copies only when dst is absent; returns whether it
    seeded."""
    if dst.is_file() or not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True


# ---- the surface -----------------------------------------------------
_PAGE = """<!doctype html><meta charset="utf-8">
<title>AIVIA — the meaning-test console</title>
<style>
 body { font: 15px/1.5 -apple-system, sans-serif; margin: 0 auto;
        max-width: 60rem; color: #222; padding: 1rem 1rem 6rem; }
 input { width: 100%; font-size: 1.1rem; padding: .5rem;
         border: 1px solid #bbb; border-radius: 4px; }
 pre { background: #f6f6f6; padding: .8rem; white-space: pre-wrap; }
 pre.gql { background: #eef3fb; }
 .wire { border-left: 3px solid #2b7a4b; padding: .1rem .6rem;
         margin: .3rem 0; background: #f4faf6; }
 .wire table.rows th { border: 1px solid #ddd;
         padding: .25rem .6rem; font-family: monospace;
         font-size: .9rem; background: #e8f3ec; }
 .meta { color: #777; font-size: .85rem; }
 .round { border-top: 1px solid #e4e4e0; padding-top: .6rem;
          margin-top: .8rem; }
 .you { color: #2b5db9; font-weight: 600; }
 a.pick { color: #2b5db9; text-decoration: underline dotted;
          margin-right: .5rem; }
 table.rows { border-collapse: collapse; margin: .4rem 0; }
 table.rows td { border: 1px solid #ddd; padding: .25rem .6rem;
                 font-family: monospace; font-size: .9rem; }
 #composer { position: fixed; bottom: 0; left: 0; right: 0;
             background: #fffffff2; border-top: 1px solid #ddd;
             padding: .7rem 1rem; }
 #composer form { max-width: 60rem; margin: 0 auto; }
</style>
<h2>The meaning-test console
<span class=meta>(__ESTATE__ · technical layer)</span></h2>
<p class=meta>__COVERAGE__</p>
<p class=meta id=wirebox></p>
<p class=meta>Gates verified structure; this tests MEANING. The
interpreter tokenizes (its only seat) · vectors match · a
deterministic planner writes the GRAPH query (shown below every
answer, paste-able into Fabric) · the connecting subgraph is the
answer. No-match and disconnection are honest results.</p>
<div id="log"></div>
<div id="composer"><form id="ask">
 <input id="q" autofocus autocomplete="off"
  placeholder="ask about the tables and columns — by name or meaning">
</form></div>
<script>
const log = document.getElementById('log');
const q = document.getElementById('q');
const wirebox = document.getElementById('wirebox');
function renderWire(w) {
  if (w.reason) {
    wirebox.textContent = 'live wire DISABLED — ' + w.reason;
    return;
  }
  wirebox.innerHTML = 'live wire (the SERVED Fabric graph): '
    + (w.on ? 'ON' : 'OFF')
    + ' · <a href="#" id=wireflip>turn ' + (w.on ? 'off' : 'on')
    + '</a> · ' + w.spent + ' capacity spend(s) this session'
    + (w.on ? ' — every question now also queries Fabric' : '');
  document.getElementById('wireflip').onclick = async (e) => {
    e.preventDefault();
    const r = await fetch('/wire?on=' + (w.on ? '0' : '1'));
    renderWire(await r.json());
  };
}
function refreshWire() {
  fetch('/wire').then(r => r.json()).then(renderWire)
    .catch(() => { wirebox.textContent = ''; });
}
refreshWire();
function esc(t) { const d = document.createElement('span');
  d.textContent = t; return d.innerHTML; }
function append(html) {
  const d = document.createElement('div');
  d.className = 'round'; d.innerHTML = html;
  log.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}
log.addEventListener('click', async (e) => {
  const w = e.target.closest('a.wide');
  if (w) {
    e.preventDefault();
    append('<p class="you">' + esc('show the wider reach') +
           '</p>');
    try {
      const r = await fetch('/round?q=' +
        encodeURIComponent(w.dataset.q) + '&reach=wide');
      append((await r.json()).html);
      refreshWire();
    } catch (err) {
      append('<p class=meta>round failed (' + esc(String(err)) +
             ')</p>');
    }
    return;
  }
  const a = e.target.closest('a.pick');
  if (!a) return;
  e.preventDefault();
  const d = a.dataset;
  append('<p class="you">' + esc('pick: ' + d.token + ' → '
         + d.ident) + '</p>');
  try {
    const r = await fetch('/round?q=' + encodeURIComponent(d.q)
      + '&pin=' + encodeURIComponent(d.token + ':::' + d.ident));
    append((await r.json()).html);
    refreshWire();
  } catch (err) {
    append('<p class=meta>round failed (' + esc(String(err)) +
           ')</p>');
  }
});
document.getElementById('ask').addEventListener('submit',
  async (e) => {
    e.preventDefault();
    const text = q.value.trim();
    if (!text) return;
    q.value = '';
    append('<p class="you">' + esc(text) + '</p>');
    try {
      const r = await fetch('/round?q=' +
        encodeURIComponent(text));
      append((await r.json()).html);
      refreshWire();
    } catch (err) {
      append('<p class=meta>round failed (' + esc(String(err)) +
             ')</p>');
    }
  });
</script>
"""


def render_round(result: Dict[str, Any]) -> str:
    parts = [f"<p class=meta>tokenized by: {result['seat']} → "
             + html.escape(" · ".join(f"'{t}'"
                                      for t in result["tokens"]))
             + "</p>"]
    trace = []
    for mset in result["match_sets"]:
        top = mset["matches"][0] if mset["matches"] else None
        bit = (f"'{mset['token']}' [{mset['tier']}] → "
               + (f"{top['class']}: {top['name']} "
                  f"({top['score']})" if top else "no match"))
        trace.append(html.escape(bit))
    parts.append("<p class=meta>matched: "
                 + " &nbsp;·&nbsp; ".join(trace) + "</p>")
    # THE CHOICE STEP (ruled 2026-09-11): every token's runners-up
    # are OFFERED — a click pins that candidate and re-runs the
    # round; the pin is the human act and outranks the scores
    q_attr = html.escape(result["question"], quote=True)
    for mset in result["match_sets"]:
        cands = [m for m in mset["matches"]
                 if m["class"] == "instance"][:6]
        if len(cands) < 2:
            continue
        links = []
        for m in cands:
            # same-named candidates disambiguate by their owner
            # (the BED_STAY_ID lesson, 2026-09-11)
            shown = m["name"]
            if m["label"] == "column" and m["identity"].count("|") >= 2:
                shown = (m["identity"].rsplit("|", 2)[-2]
                         + "." + m["name"])
            links.append(
                f"<a href='#' class=pick data-q=\"{q_attr}\" "
                f"data-token=\"{html.escape(mset['token'], quote=True)}\" "
                f"data-ident=\"{html.escape(m['identity'], quote=True)}\">"
                + html.escape(f"{shown} ({m['label']}, "
                              f"{round(m['score'], 3)})") + "</a>")
        n_all = sum(1 for m in mset["matches"]
                    if m["class"] == "instance")
        more = f" · showing {len(cands)} of {n_all}" \
            if n_all > len(cands) else ""
        parts.append("<p class=meta>choose for '"
                     + html.escape(mset["token"]) + "': "
                     + " ".join(links) + html.escape(more) + "</p>")
    for tok, name in result.get("pinned", []):
        parts.append("<p class=meta>pinned by you: '"
                     + html.escape(tok) + "' → "
                     + html.escape(name) + "</p>")
    for tok, ident in result.get("pin_misses", []):
        parts.append("<p class=meta>note: your pick '"
                     + html.escape(ident) + "' is no longer in "
                     "the match set for '" + html.escape(tok)
                     + "' — the round ran unpinned.</p>")
    for line in result["kind_constraints"]:
        parts.append(f"<p class=meta>{html.escape(line)}</p>")
    if result.get("label_constraint"):
        parts.append("<p class=meta>anchoring constrained to "
                     "label: " + html.escape(
                         ", ".join(result["label_constraint"]))
                     + " (your word)</p>")
    for tok, labels in result.get("label_relaxed", []):
        parts.append("<p class=meta>note: nothing labeled "
                     + html.escape("/".join(labels)) + " matched '"
                     + html.escape(tok) + "' — the label "
                     "constraint was relaxed.</p>")
    if result["edge_constraints"]:
        parts.append("<p class=meta>traversal constrained to: "
                     + html.escape(", ".join(
                         result["edge_constraints"])) + "</p>")
    for t in result.get("relation_unclaimed", []):
        parts.append("<p class=meta>relation word '"
                     + html.escape(t) + "' matched no structure "
                     "vocabulary — counted, steering nothing.</p>")
    if result.get("constrained_out"):
        lbl = (result.get("counts") or {}).get("label", "node")
        parts.append(f"<p class=meta>{result['constrained_out']} "
                     f"{html.escape(str(lbl))}(s) connect only "
                     "outside the constrained edge kind(s) — "
                     "counted, not lost.</p>")
    # THE NEAR-FIRST DEFAULT: the wider reach is one click away
    if result.get("far_out"):
        lbl = (result.get("counts") or {}).get("label", "node")
        parts.append(f"<p class=meta>{result['far_out']} more "
                     f"{html.escape(str(lbl))}(s) connect beyond "
                     "the anchor's own structure — counted; "
                     f"<a href='#' class=wide data-q=\"{q_attr}\">"
                     "show the wider reach</a>.</p>")
    # STRUCTURE NEVER ROWS: the conjunction semantics FRAME the
    # list; the exclusions are counted classes
    for f in result.get("frames", []):
        parts.append("<p class=meta>frame: " + html.escape(f)
                     + "</p>")
    co = result.get("counted_out") or {}
    if co:
        bits = " · ".join(f"{v} {k}" for k, v in sorted(co.items()))
        parts.append("<p class=meta>not rows, counted: "
                     + html.escape(bits) + ".</p>")
    for g in result["gql"]:
        parts.append(f"<pre class=gql>{html.escape(g)}</pre>")
    # THE LIVE-WIRE TOGGLE (ruled 2026-09-12): the served graph's
    # answer renders beside the local one — evidence, never the
    # answer path; errors verbatim (the error-contract)
    for w in result.get("wire") or []:
        inner = []
        if not w["ok"]:
            inner.append("<p class=meta>wire error ["
                         + html.escape(w["code"]) + "]: "
                         + html.escape(w["description"]) + "</p>")
        else:
            cap = w["rows"][:20]
            cols = w["columns"]
            head = "".join("<th>" + html.escape(c) + "</th>"
                           for c in cols)
            cells = "".join(
                "<tr>" + "".join(
                    "<td>" + html.escape(str(r.get(c, "")))
                    + "</td>" for c in cols) + "</tr>"
                for r in cap)
            inner.append("<table class=rows><tr>" + head + "</tr>"
                         + cells + "</table>")
            if w["row_count"] > len(cap):
                inner.append(f"<p class=meta>showing {len(cap)} of "
                             f"{w['row_count']} served rows</p>")
            if "verdict" in w:
                inner.append(f"<p class=meta>local "
                             f"{w['local_count']} row(s) · served "
                             f"{w['row_count']} row(s) — "
                             f"{w['verdict']}</p>")
            else:
                inner.append(f"<p class=meta>served "
                             f"{w['row_count']} row(s)</p>")
        parts.append("<div class=wire><p class=meta>the SERVED "
                     "graph answers (Fabric Graph):</p>"
                     + "".join(inner) + "</div>")
    if result.get("wire_note"):
        # the paused-capacity find: ON + no artifact renders its
        # own absence, never a page indistinguishable from success
        parts.append("<div class=wire><p class=meta>"
                     + html.escape(result["wire_note"])
                     + "</p></div>")
    if result.get("wire_spent") is not None:
        # the spends line renders whenever the wire is ON — a 0 is
        # evidence too
        parts.append(f"<p class=meta>capacity spends this session: "
                     f"{result['wire_spent']} quer"
                     f"{'y' if result['wire_spent'] == 1 else 'ies'}"
                     "</p>")
    # DELIVERY BY RESULT SHAPE (the matched-graph ruling): rows
    # render as a TABLE with a visible cap and counted remainder;
    # the conservation line rides along
    if result.get("rows"):
        cap = result["rows"][:20]
        with_words = any(r.get("words") for r in cap)
        cells = "".join(
            "<tr><td>" + html.escape(r["a"]) + "</td><td>"
            + html.escape(r["edge"]) + "</td><td>"
            + html.escape(r["b"]) + "</td>"
            + (("<td>" + html.escape(r.get("words") or "")
                + "</td>") if with_words else "")
            + "</tr>" for r in cap)
        parts.append("<table class=rows>" + cells + "</table>")
        if len(result["rows"]) > len(cap):
            parts.append(f"<p class=meta>showing {len(cap)} of "
                         f"{len(result['rows'])} rows</p>")
    if result.get("capped"):
        shown, total = result["capped"]
        parts.append(f"<p class=meta>neighborhood showing {shown} "
                     f"of {total} connections — the rest are "
                     "counted, not lost.</p>")
    c = result.get("counts") or {}
    if c and c.get("connected") != c.get("population"):
        parts.append(f"<p class=meta>{c['connected']} of "
                     f"{c['population']} {c['label']}(s) connect; "
                     f"{c['population'] - c['connected']} do "
                     "not.</p>")
    body = result["evidence"] + [""] + result["edge_lines"] \
        if result["edge_lines"] else result["evidence"]
    if body and not result.get("rows"):
        parts.append("<pre>" + html.escape("\n".join(body)) + "</pre>")
    for a, b in result["relaxed"]:
        parts.append(f"<p class=meta>note: {html.escape(a)} and "
                     f"{html.escape(b)} do not connect under the "
                     "named edge kinds — the shown path relaxes the "
                     "constraint.</p>")
    for a, b in result["gaps"]:
        parts.append(f"<p>{html.escape(a)} and {html.escape(b)} do "
                     "not connect in the technical layer — an "
                     "honest gap, not an error.</p>")
    for t in result["unmatched"]:
        parts.append(f"<p>'{html.escape(t)}' matched nothing in "
                     "this layer — an honest zero.</p>")
    return "".join(parts)


def make_handler(estate: str, coverage: str, ask_fn,
                 wire=None, wire_reason: str = ""):
    # THE LIVE-WIRE TOGGLE (ruled 2026-09-12): OFF at every boot —
    # flipping it is Sunny's hand (the capacity law); every fired
    # query is one counted spend
    wire_state = {"on": False, "spent": 0}

    class Handler(BaseHTTPRequestHandler):
        def _send(self, data: bytes, ctype: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802 — http.server's contract
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if parsed.path == "/wire":
                if wire is None:
                    # literal: shape
                    out = {"on": False, "spent": 0,
                           "reason": wire_reason}
                else:
                    flip = (params.get("on") or [""])[0]
                    if flip in ("0", "1"):
                        wire_state["on"] = flip == "1"
                    # literal: shape
                    out = {"on": wire_state["on"],
                           "spent": wire_state["spent"],
                           "reason": ""}
                self._send(json.dumps(out).encode(),
                           "application/json; charset=utf-8")
                return
            if parsed.path == "/round":
                q = (params.get("q") or [""])[0]
                pins = {}
                for p in params.get("pin", []):
                    token, _, ident = p.partition(":::")
                    if token and ident:
                        pins[token] = ident
                reach = (params.get("reach") or ["near"])[0]
                if q.strip():
                    res = ask_fn(q, pins, reach)
                    if wire is not None and wire_state["on"]:
                        blocks = fabric_wire.run_round(wire, res)
                        wire_state["spent"] += len(blocks)
                        res["wire"] = blocks
                        res["wire_spent"] = wire_state["spent"]
                        if not blocks:
                            # SUNNY'S PAUSED-CAPACITY FIND
                            # (2026-09-13): silence names itself —
                            # ON + no artifact must never look
                            # like a served success
                            res["wire_note"] = (
                                "live wire ON — this round "
                                "carried no GQL artifact; "
                                "nothing fired")
                    out = {"html": render_round(res)}
                else:
                    out = {"html": ""}
                self._send(json.dumps(out).encode(),
                           "application/json; charset=utf-8")
                return
            page = (_PAGE.replace("__ESTATE__", html.escape(estate))
                    .replace("__COVERAGE__", html.escape(coverage)))
            self._send(page.encode(), "text/html; charset=utf-8")

        def log_message(self, *args):
            pass
    return Handler


def coverage_line(entries: List[Dict[str, Any]],
                  exclusions: Dict[str, int]) -> str:
    counts: Dict[str, int] = {}
    for e in entries:
        counts[e["label"]] = counts.get(e["label"], 0) + 1
    inside = " · ".join(f"{counts[k]} {k}(s)" for k in sorted(counts))
    outside = ", ".join(f"{k} {exclusions[k]}"
                        for k in sorted(exclusions))
    return (f"in scope: {inside} | excluded (counted, later "
            f"batches): {outside}")


def main() -> None:
    from aivia.console import EMBEDDING_MODEL, _env_key, build_store, make_embedder, make_interpreter
    estate = sys.argv[1] if len(sys.argv) > 1 else "ed_sepsis_dev"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8378
    key = _env_key()
    print(f"building the {estate} graph …")
    root = pathlib.Path(__file__).resolve().parents[1]
    store, base = build_store(
        estate, journal_path=(root / "AIVIA_Product" / "estates"
                              / estate / "governance"
                              / "journal.jsonl"))
    read = ReadApi(store)
    # THE GLOSSARY PROCESS (Ruling_Glossary_Process.md): refresh
    # the token ledger (machine facts only — ruled fields are
    # untouchable), then birth the journal from its blessed slice
    census = glossary.ledger_refresh(read, base / "glossary")
    print("  glossary ledger: " + " · ".join(
        f"{v} {k}" for k, v in sorted(census.items())))
    blessed = glossary.seed_journal(store, read, base / "glossary")
    if blessed:
        print(f"  {blessed} ruled blessing(s) born into the "
              "governance journal (the ledger's blessed slice)")
    # R5.b THE BLESSED NAME (Grammar_Floor v2.8.0): registry rows
    # become blessed_name nodes; counts never silent
    names = glossary.seed_blessed_names(store, read,
                                        base / "glossary")
    if any(names.values()):
        print("  blessed names: " + " · ".join(
            f"{v} {k}" for k, v in sorted(names.items()) if v))
    entries, exclusions = technical_scope(read)
    adj, directed = technical_adjacency(read)
    seeded = seed_cache(
        base.parent / "sepsis" / ".cache" / "embeddings.json",
        base / ".cache" / "embeddings.json")
    if seeded:
        print("  seeded the vector cache from the sepsis estate "
              "(content-keyed — identical identities re-use)")
    interpret_fn = (make_interpreter(
        key, cache_path=base / ".cache" / "proposals.json")
        if key else None)
    semantic = None
    if key:
        print(f"embedding {len(entries)} cards (cached by content) …")
        try:
            semantic = grounding.SemanticIndex(
                entries, make_embedder(key), EMBEDDING_MODEL,
                cache_path=base / ".cache" / "embeddings.json")
            print(f"  embedded now: {semantic.embedded_now}")
        except Exception as err:  # noqa: BLE001 — seat-failure law
            print(f"  EMBED SEAT DOWN at boot ({err}) — exact "
                  "tiers only")
    else:
        print("no OPENAI_API_KEY — exact tiers only")

    def ask_fn(q: str, pins=None,
               reach: str = "near") -> Dict[str, Any]:
        return answer_question(q, interpret_fn, entries, semantic,
                               read, adj, directed, pins=pins,
                               reach=reach)

    coverage = coverage_line(entries, exclusions)
    wire, wire_reason = fabric_wire.from_env()
    print("live wire: configured (OFF until you flip it — every "
          "fired query is one capacity spend)" if wire
          else f"live wire: {wire_reason}")
    server = ThreadingHTTPServer(
        ("127.0.0.1", port),
        make_handler(estate, coverage, ask_fn,
                     wire=wire, wire_reason=wire_reason))
    print(f"the meaning-test console: http://127.0.0.1:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
