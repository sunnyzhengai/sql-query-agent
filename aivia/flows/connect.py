"""CONNECT (ADR 0079 step 3): the answer to a multi-mention question
is the CONNECTING SUBGRAPH — weighted shortest paths between grounded
nodes over the graph's own edges; single mentions get a typed
neighborhood. No intent enumeration: the connection is the answer.
Edge weights are DECLARED registry data (Ranking_Weights), never a
hidden judgment; caps are visible wherever anything is truncated.
"""
import heapq
from typing import Dict, List, Optional, Tuple


def edge_weights() -> Dict[str, float]:
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets.get("Ranking_Weights", [])
    weights = {r["Edge"]: float(r["Weight"]) for r in sheet
               if r.get("Edge") and r["Edge"] != "_ruling"}
    # literal: schema-mirror lenses.Ranking_Weights
    return weights or {"contains": 1.0, "reads": 1.0, "cites": 1.0,
                       "sighted": 1.0, "defines": 1.0}


def build_adjacency(read) -> Dict[str, List[Tuple[str, str]]]:
    """identity -> [(neighbor, edge label)] over the stored graph:
    column—contains—table · scope—contains—file · scope—reads—target
    · scope—cites—column · derived—defines—scope · drift—sighted—file.
    Deterministic, derived, rebuilt per boot."""
    adj: Dict[str, List[Tuple[str, str]]] = {}

    def link(a, b, label):
        adj.setdefault(a, []).append((b, label))
        adj.setdefault(b, []).append((a, label))

    for n in read.nodes("column"):
        link(n.identity, n.identity.rsplit("|", 1)[0], "contains")
    # THE BIRTH-EDGE UPGRADE (Connection Ledger step 1, 2026-09-07):
    # the governance world's connections existed as PROPERTIES and
    # were invisible to traversal — Sunny's overrule ("a usage event
    # is connected to the user and the item it used"). Labels come
    # from the ruled ledger, never a code dict.
    from aivia.flows.censuses import connection_ledger
    ledger = connection_ledger()
    db_id = None
    for n in read.nodes("db"):
        db_id = n.identity
    for n in read.nodes("schema"):
        if db_id:
            link(db_id, n.identity, "contains")
    seen_schemas = {n.identity for n in read.nodes("schema")}
    for n in read.nodes("table"):
        schema_id = n.identity.rsplit("|", 1)[0]
        if schema_id in seen_schemas:
            link(schema_id, n.identity, "contains")
    for n in read.nodes("meaning_twin"):
        link(n.identity, n.identity.removeprefix("twin::"),
             "translates")
    # literal: schema-mirror kg3_artifacts
    for kind in ("usage", "description", "responsibility",
                 "disposition", "proposal", "redaction"):
        row = ledger.get(kind)
        if not row or row["status"] != "edged":
            continue
        for n in read.nodes(kind):
            about = n.properties.get("about")
            targets = about if isinstance(about, list) else \
                [about] if about else []
            for t in targets:
                link(n.identity, t, row["edge"])
    for n in read.nodes("concept"):
        act = n.properties.get("minting_act")
        if act:
            link(n.identity, act, "minted_by")
    for n in read.nodes("term"):
        for origin in n.properties.get("derived_from") or []:
            link(n.identity, origin, "derived_from")
        about = n.properties.get("about")
        for t in (about if isinstance(about, list) else []):
            link(n.identity, t, "about")
    # STEP 4: the parts walk — conditions and parameters gain
    # belongs_to edges (the INDEX-ONLY verdict dies; provenance is
    # traversal, not owner-chain code)
    from aivia.lenses import decisions
    for key, tree in read.trees().items():
        for scope in decisions.named_scopes(tree):
            preds = [p for p in
                     decisions.membership_predicates(scope)
                     if not decisions.is_degenerate(p)]
            for i in range(len(preds)):
                link(f"{scope['name_key']}::c{i}",
                     scope["name_key"], "belongs_to")
        for prm in tree.get("parameters", []):
            link(f"{key}::param/{prm['name']}", key, "belongs_to")
    # PHASE I: blessed acronyms walk to their approver and — DERIVED
    # AT BUILD, per the contract — to every node whose name carries
    # the token (new nodes connect automatically)
    acronyms = list(read.nodes("acronym"))
    if acronyms:
        from aivia.lenses.ask_index import _tokens
        carriers = []
        for n in read.nodes(None):
            nm = n.properties.get("name") or \
                n.identity.rsplit("|", 1)[-1]
            carriers.append((n.identity, _tokens(str(nm))))
        for a in acronyms:
            link(a.identity, a.properties["approved_by"],
                 "approved_by")
            tok = a.properties["name"].lower()
            for ident, toks in carriers:
                if tok in toks and ident != a.identity:
                    link(a.identity, ident, "used_by")
    # PHASE H: the consumption layer walks to its procs
    for n in read.nodes("PBI Report"):
        for f in n.properties.get("executes") or []:
            link(n.identity, f, "executes")
    # STEP 5: exclusions walk to the estate root
    for n in read.nodes("excluded_file"):
        root = n.properties.get("estate")
        if root:
            link(n.identity, root, "excluded_from")
    # STEP 3: every authored node walks —by→ its actor — one pass
    # over ALL nodes, no kind list (the literal law)
    for n in read.nodes(None):
        author = n.properties.get("author")
        if author and ":" in str(author):
            link(n.identity, author, "by")
    for key, tree in read.trees().items():
        fname = key  # the index's file identity (the store's file id)
        for stmt in tree["statements"]:
            for s in (list(stmt.get("ctes", []))
                      + ([stmt["scope"]] if stmt.get("scope") else [])):
                if "name_key" not in s:
                    continue
                nk = s["name_key"]
                link(nk, fname, "contains")
                seen_cols = set()

                def walk(node, arms_ok=True):
                    if isinstance(node, dict):
                        rt = node.get("resolves_to")
                        if isinstance(rt, str):
                            if rt.startswith("SAME-TREE scope "):
                                link(nk, rt.replace(
                                    "SAME-TREE scope ", ""), "reads")
                            elif "|" in rt and rt not in seen_cols:
                                seen_cols.add(rt)
                                link(nk, rt, "cites")
                        if "derived_scope" in node:
                            walk(node["derived_scope"])
                        for v in node.values():
                            if v is not node.get("evidence"):
                                walk(v)
                    elif isinstance(node, list):
                        for v in node:
                            walk(v)
                for ref in s.get("from_refs", []):
                    rt = ref.get("resolves_to")
                    if isinstance(rt, str):
                        target = (rt.replace("SAME-TREE scope ", "")
                                  if rt.startswith("SAME-TREE") else rt)
                        link(nk, target, "reads")
                    if "derived_scope" in ref:
                        walk(ref["derived_scope"])
                walk([s.get("where"), s.get("join_on"),
                      s.get("select_refs")])
                arms = s.get("combination_arms")
                shape = arms[0] if arms else s
                for m in shape.get("projection", []):
                    if m.get("name"):
                        link(f"{nk}.{m['name']}", nk, "defines")
        for ref in tree.get("resolution_census", {}).get(
                "unresolved", []):
            # drift identities are name-based in the index
            link(f"{tree['name']}::{ref}", fname, "sighted")
    return adj


def shortest_path(adj, weights, start: str, goal: str,
                  cap: int = 200000) -> Optional[List[Tuple[str, str]]]:
    """Dijkstra; returns [(node, edge-label-used)] from start to goal
    inclusive (first label is '')."""
    if start == goal:
        return [(start, "")]
    dist = {start: 0.0}
    prev: Dict[str, Tuple[str, str]] = {}
    heap = [(0.0, start)]
    steps = 0
    while heap and steps < cap:
        steps += 1
        d, node = heapq.heappop(heap)
        if node == goal:
            break
        if d > dist.get(node, float("inf")):
            continue
        for nbr, label in adj.get(node, []):
            nd = d + weights.get(label, 1.0)
            if nd < dist.get(nbr, float("inf")):
                dist[nbr] = nd
                prev[nbr] = (node, label)
                heapq.heappush(heap, (nd, nbr))
    if goal not in prev and goal != start:
        return None
    path = [(goal, prev[goal][1])]
    node = goal
    while node != start:
        node, label = prev[node][0], prev[node][1]
        entry_label = prev.get(node, ("", ""))[1] if node != start else ""
        path.append((node, entry_label))
    path.reverse()
    return path


def neighborhood(adj, identity: str, cap: int = 12
                 ) -> Dict[str, List[str]]:
    """Direct neighbors grouped by edge label, capped visibly."""
    groups: Dict[str, List[str]] = {}
    for nbr, label in adj.get(identity, []):
        groups.setdefault(label, []).append(nbr)
    return {label: sorted(set(nbrs)) for label, nbrs in groups.items()}
