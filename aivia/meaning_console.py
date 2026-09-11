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

from aivia.flows import ask, connect, glossary, grounding
from aivia.graph.read_api import ReadApi
from aivia.lenses.ask_index import _fold

# the accepted scope of this console's first target — instances
# that SPEAK (db/db_schema carry no speech source and are counted
# exclusions, never silent ones)
TECHNICAL_SPEAKING = ("table", "column")
TECHNICAL_KINDS = ("table", "column")
TECHNICAL_EDGE_KINDS = ("has_part", "joins_to")


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
            exclusions[e["label"]] = exclusions.get(e["label"], 0) + 1
    for lbl in ("db", "db_schema"):  # present, speechless — counted
        exclusions[lbl] = sum(1 for _ in read.nodes(lbl))
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
                            "words": str(r.get("Notes") or "")})
    return entries, exclusions


def technical_adjacency(read) -> Tuple[
        Dict[str, List[Tuple[str, str]]], Set[Tuple[str, str, str]]]:
    """The technical layer's own edges, both as an undirected walk
    surface (for the planner) and the DIRECTED store truth (for the
    GQL writer): db—has_part→db_schema—has_part→table—has_part→
    column + table—joins_to→table."""
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
        for e in store.current_edges("joins_to"):
            link(e.from_id, e.to_id, "joins_to")
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


def tokens_from(question: str, interpret_fn) -> Tuple[List[str], str]:
    """(tokens, seat) — the interpreter's mentions ARE the tokens
    (multi-word phrases stay whole); any seat failure drops to the
    mechanical floor, visibly."""
    if interpret_fn is None:
        return fallback_tokens(question), "floor"
    try:
        proposal = interpret_fn(question)
        mentions = [m for m in (proposal.get("mentions") or [])
                    if str(m).strip()]
        if mentions:
            return [str(m) for m in mentions], "interpreter"
    except Exception:  # noqa: BLE001 — the seat-failure law: a
        # tokenizer failure is never a dead round; the mechanical
        # floor answers and the seat name says so
        return fallback_tokens(question), "floor"
    return fallback_tokens(question), "floor"


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


# ---- step 5: the answer --------------------------------------------
def answer_question(question: str, interpret_fn,
                    entries: List[Dict[str, Any]],
                    semantic: Optional[grounding.SemanticIndex],
                    read, adj, directed,
                    pins: Optional[Dict[str, str]] = None
                    ) -> Dict[str, Any]:
    """The whole ruled loop for one question — deterministic after
    tokenization; every outcome (no-match, gap, relaxation) is a
    returned fact, never an invention."""
    pins = pins or {}
    tokens, seat = tokens_from(question, interpret_fn)
    msets = [match_token(t, entries, semantic) for t in tokens]
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
    for mset in msets:
        if mset["token"] in pin_sets:
            continue
        top = _strong(mset)
        if top is None:
            continue
        kind_claim = None
        if top["class"] == "kind":
            kind_claim = top
        elif top["class"] == "instance":
            bar = grounding.thresholds()["MATCH_SCORE"]
            kind_claim = next(
                (m for m in mset["matches"]
                 if m["class"] == "kind" and m["score"] >= bar
                 and m["name"] == top["label"]), None)
        if kind_claim is not None:
            kind_hits.append(kind_claim)
            allowed_labels.add(kind_claim["name"])
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
    enum_kinds = [k["name"] for k in kind_hits
                  if k["name"] not in inst_labels]
    # THE SHAPE LADDER: enumeration -> connection -> neighborhood
    # -> list -> honest zero; the matched graph decides, the
    # planner only fills MISSING structure
    rows: List[Dict[str, str]] = []
    counts: Dict[str, Any] = {}
    capped: Optional[Tuple[int, int]] = None
    described = {e["identity"]: e for e in entries}

    def _speech(ident: str) -> str:
        e = described.get(ident)
        return ((e.get("words") or "").split(". ")[0]
                if e else "")

    # literal: shape
    plan = {"paths": [], "nodes": [], "edges": [], "gaps": [],
            "relaxed": []}
    gql: List[str] = []
    if enum_kinds and anchors:
        mode = "enumeration"
        kind_label = enum_kinds[0]
        pop = {n.identity for n in read.nodes(kind_label)}
        hit_pop = set()
        for m in anchors:
            for nbr, elbl in adj.get(m["identity"], []):
                if edge_kinds and elbl not in edge_kinds:
                    continue
                if nbr in pop:
                    hit_pop.add(nbr)
                    # literal: shape
                    rows.append({"a": nbr.rsplit("|", 1)[-1],
                                 "edge": elbl, "b": m["name"],
                                 "words": _speech(nbr),
                                 "a_id": nbr,
                                 "b_id": m["identity"]})
        rows.sort(key=lambda r: (r["a"], r["b"]))
        # literal: shape
        counts = {"connected": len(hit_pop),
                  "population": len(pop), "label": kind_label}
        names = sorted({m["name"] for m in anchors})
        flt = " OR ".join(f"b.name = '{n}'" for n in names[:8])
        edge = sorted(edge_kinds)[0] if edge_kinds else "has_part"
        gql = [f"MATCH (a:{kind_label})-[:{edge}]->"
               f"(b:{anchors[0]['label']}) FILTER {flt} "
               "RETURN a.name, b.name"]
    elif enum_kinds:
        mode = "list"
        kind_label = enum_kinds[0]
        members = sorted(n.identity for n in read.nodes(kind_label))
        # literal: shape
        rows = [{"a": i.rsplit("|", 1)[-1], "edge": "", "b": "",
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
    # literal: mechanical — the technical spine's label walk
    for lbl in ("db", "db_schema", "table", "column"):
        for n in read.nodes(lbl):
            if n.identity in plan["nodes"]:
                label_of[n.identity] = lbl
    if mode == "connection":
        gql = [write_gql(p, directed, label_of)
               for p in plan["paths"]]
    evidence = []
    for ident in plan["nodes"]:
        e = described.get(ident)
        if e:
            words = (e.get("words") or "").split(". ")[0]
            evidence.append(f"[{e['label']}] {e['name']}"
                            + (f" — {words}" if words else ""))
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
function esc(t) { const d = document.createElement('span');
  d.textContent = t; return d.innerHTML; }
function append(html) {
  const d = document.createElement('div');
  d.className = 'round'; d.innerHTML = html;
  log.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}
log.addEventListener('click', async (e) => {
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
    for g in result["gql"]:
        parts.append(f"<pre class=gql>{html.escape(g)}</pre>")
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


def make_handler(estate: str, coverage: str, ask_fn):
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
            if parsed.path == "/round":
                q = (params.get("q") or [""])[0]
                pins = {}
                for p in params.get("pin", []):
                    token, _, ident = p.partition(":::")
                    if token and ident:
                        pins[token] = ident
                out = {"html": render_round(ask_fn(q, pins))} \
                    if q.strip() else {"html": ""}
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

    def ask_fn(q: str, pins=None) -> Dict[str, Any]:
        return answer_question(q, interpret_fn, entries, semantic,
                               read, adj, directed, pins=pins)

    coverage = coverage_line(entries, exclusions)
    server = ThreadingHTTPServer(
        ("127.0.0.1", port), make_handler(estate, coverage, ask_fn))
    print(f"the meaning-test console: http://127.0.0.1:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
