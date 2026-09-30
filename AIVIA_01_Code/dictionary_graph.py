# dictionary_graph.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/02_emr_data_dictionary.md (L08 + L09 — the
#           graph rules and the metadata map)
#           AIVIA_01_Design/03_chat_bot.md L04 (the split ruling)
# Contract: AIVIA_01_Design/02_emr_data_dictionary_data_contract.md
# Tests:    AIVIA_01_Test/test_02_emr_data_dictionary_data_contract.py
#           Section 7 (imports repointed here; the L06 answer/page tests
#           retire with the page)
#
# PURPOSE. The phase 02 graph ENGINE, split out of graph_chat.py so the
# phase 03 chat (and every later phase) calls a phase-02-owned module.
# This is a MOVE, not a rewrite: the functions land here byte-identical
# except imports. No new behavior, so no new red tests — the existing
# Section 7 engine tests must stay green against the new module name.
#
# WHAT MOVES IN (from graph_chat.py, unchanged):
#   load_sheets(data_dir)         — sheets + sidecar + no_match reader
#   DIMENSION_RULES               — the L08 ruled rule rows
#   build_graph(sheets)           — nodes, edges by kind, adjacency,
#                                   census with components
#   _bfs_path(graph, start, goal) — deterministic BFS
#   connect(graph, table_ids)     — union of pairwise shortest paths.
#                                   NOT called by the phase 03 chat
#                                   (03 decision 4); stays here tested,
#                                   waiting for the future phase that
#                                   writes queries.
#   score_rows(question_embedding, sheets) — the five-population scorer
#   accept(scored, floor, match, margin)   — the ruled ranking/match
#                                   split. Pure function; the acceptance
#                                   VALUES live in the 03 contract as
#                                   display defaults — this module keeps
#                                   no product constants.
#
# WHAT RETIRES (deleted with graph_chat.py, superseded by 03 L05):
#   answer(), the PAGE html, GraphChatHandler, main() — the L06 chat.
#   CANDIDATE_FLOOR / MATCH_SCORE / UNIQUE_MARGIN constants — the
#   global-band posture the 03 design replaced.
#   The three test_answer_* tests — they pin superseded L06 behavior
#   (global-pool anchoring); the 03 build brings its own answer tests
#   red-first at L05.
#
# WHAT STAYS PUT ELSEWHERE:
#   cosine_similarity, real_embedder — remain in local_chat.py (phase
#   01), imported from there as today.
#
# SUNNY'S MD: the HOW TO RUN block in her 02 md gets one line at build:
#   the L06 chat is retired; the new chat command lands with the 03
#   build. Her twelve shapes move to the 03 md by her hand (companion
#   edit, already ruled).
#
# ACCEPTANCE FOR THIS STEP: full suite green after the split (83+ tests,
# minus the three retired, imports repointed), ruff clean, and
# `python3.11 -c "import dictionary_graph"` works from AIVIA_01_Code.

import json
from collections import deque
from pathlib import Path

from local_chat import cosine_similarity

# L08: the ruled rule rows. A future rule is a new row, never a fork.
DIMENSION_RULES = [
    {"rule": "date_dimension",
     "destin_table_name": "DATE_DIMENSION",
     "destin_column_name": "CALENDAR_DT",
     "match_data_type": "DATETIME"},
]


def load_sheets(data_dir):
    data_dir = Path(data_dir)

    def _read(name, required=True):
        path = data_dir / f"02_emr_data_dictionary_extraction_{name}.json"
        if not path.exists():
            if required:
                raise FileNotFoundError(f"required sheet missing: {path}")
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    sheets = {
        "tables": _read("table"),
        "columns": _read("column"),
        "joins": _read("join"),
        "values": _read("value", required=False),
        "value_embeddings": _read("value_embeddings", required=False),
    }
    nm = data_dir / "02_no_dictionary_match.json"
    if nm.exists():
        with open(nm, encoding="utf-8") as f:
            sheets["no_match"] = json.load(f)
    else:
        sheets["no_match"] = []
    return sheets


def build_graph(sheets):
    tables = {r["table_id"]: r for r in sheets["tables"]}
    tables_by_name = {r["table_name"]: r["table_id"]
                      for r in sheets["tables"]}
    columns = {r["column_id"]: r for r in sheets["columns"]}
    table_columns = {}
    for r in sheets["columns"]:
        table_columns.setdefault(r["table_id"], []).append(r["column_id"])

    edges = {}
    # joins_by_fk: in-scope rows GROUPED by join_id — one edge per join,
    # ordered column pairs as properties (composite joins reassemble by
    # construction).
    for row in sheets["joins"]:
        if not row["destin_in_scope"]:
            continue
        e = edges.get(row["join_id"])
        if e is None:
            e = edges[row["join_id"]] = {
                "kind": "joins_by_fk", "edge_key": row["join_id"],
                "source_table_id": row["source_table_id"],
                "source_table_name": row["source_table_name"],
                "destin_table_id": row["destin_table_id"],
                "destin_table_name": row["destin_table_name"],
                "column_pairs": [],
                "conditional_c": row["conditional_c"],
                "may_be_stale_c": row["may_be_stale_c"],
                "is_current_data_model_yn": row["is_current_data_model_yn"],
                "is_supplemental_yn": row["is_supplemental_yn"],
            }
        e["column_pairs"].append({
            "ordinal": row["ordinal"],
            "source_column_id": row["source_column_id"],
            "source_column_name": row["source_column_name"],
            "destin_column_id": row["destin_column_id"],
            "destin_column_name": row["destin_column_name"],
        })
    for e in edges.values():
        e["column_pairs"].sort(key=lambda p: p["ordinal"])

    # joins_by_rule: derived at EVERY build from the rule rows + data
    # types — parallel edges are distinct joins, keyed by column.
    for rule in DIMENSION_RULES:
        dt_id = tables_by_name.get(rule["destin_table_name"])
        if dt_id is None:
            continue
        dcol = next((columns[cid] for cid in table_columns.get(dt_id, [])
                     if columns[cid]["column_name"]
                     == rule["destin_column_name"]), None)
        if dcol is None:
            continue
        for r in sheets["columns"]:
            if (r["data_type"] != rule["match_data_type"]
                    or r["table_id"] == dt_id):
                continue
            key = f"rule:{rule['rule']}:{r['column_id']}"
            edges[key] = {
                "kind": "joins_by_rule", "edge_key": key,
                "rule": rule["rule"],
                "source_table_id": r["table_id"],
                "source_table_name": r["table_name"],
                "destin_table_id": dt_id,
                "destin_table_name": rule["destin_table_name"],
                "column_pairs": [{
                    "ordinal": 1,
                    "source_column_id": r["column_id"],
                    "source_column_name": r["column_name"],
                    "destin_column_id": dcol["column_id"],
                    "destin_column_name": dcol["column_name"],
                }],
            }

    # adjacency: walkable both directions; the STORED direction stays
    # on the edge and is reported, never flipped.
    adjacency = {tid: [] for tid in tables}
    for e in edges.values():
        adjacency[e["source_table_id"]].append(
            (e["edge_key"], e["destin_table_id"]))
        adjacency[e["destin_table_id"]].append(
            (e["edge_key"], e["source_table_id"]))

    def _order(item):
        key, nb = item
        e = edges[key]
        return (0 if e["kind"] == "joins_by_fk" else 1,
                tables[nb]["table_name"], key)
    for tid in adjacency:
        adjacency[tid].sort(key=_order)

    seen, components = set(), []
    for tid in sorted(tables, key=lambda t: tables[t]["table_name"]):
        if tid in seen:
            continue
        comp, q = [], deque([tid])
        seen.add(tid)
        while q:
            n = q.popleft()
            comp.append(tables[n]["table_name"])
            for _, nb in adjacency[n]:
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        components.append(sorted(comp))
    components.sort(key=len, reverse=True)

    census = {
        "tables": len(tables), "columns": len(columns),
        "joins_by_fk": sum(1 for e in edges.values()
                           if e["kind"] == "joins_by_fk"),
        "joins_by_rule": sum(1 for e in edges.values()
                             if e["kind"] == "joins_by_rule"),
        "values": len(sheets["values"] or []),
        "value_search": sheets["value_embeddings"] is not None,
        "components": components,
    }
    return {"tables": tables, "tables_by_name": tables_by_name,
            "columns": columns, "table_columns": table_columns,
            "edges": edges, "adjacency": adjacency, "census": census}


def score_rows(question_embedding, sheets):
    scored = []
    for r in sheets["tables"]:
        scored.append({
            "kind": "table", "name": r["table_name"],
            "table_name": r["table_name"],
            "scores": {
                "name": cosine_similarity(
                    question_embedding, r["table_name_embedding"]),
                "description": cosine_similarity(
                    question_embedding, r["table_description_embedding"]),
            }})
    for r in sheets["columns"]:
        scored.append({
            "kind": "column",
            "name": f"{r['table_name']}.{r['column_name']}",
            "table_name": r["table_name"],
            "column_name": r["column_name"],
            "scores": {
                "name": cosine_similarity(
                    question_embedding, r["column_name_embedding"]),
                "description": cosine_similarity(
                    question_embedding, r["column_description_embedding"]),
            }})
    if sheets["value_embeddings"] is not None:
        for r in sheets["value_embeddings"]:
            scored.append({
                "kind": "value",
                "name": f"{r['table_name']}:{r['code']}",
                "table_name": r["table_name"],
                "code": r["code"], "meaning": r["meaning"],
                "scores": {"meaning": cosine_similarity(
                    question_embedding, r["meaning_embedding"])}})
    return scored


def accept(scored, floor, match, margin):
    """The contract's ruled split: RANKING by the sum of scores that
    clear the floor; IS-IT-A-MATCH by the best single score. Below-match
    hits stay visible as candidates — thresholds are never cliffs."""
    for e in scored:
        e["best"] = max(e["scores"].values())
        e["rank"] = sum(s for s in e["scores"].values() if s >= floor)
    top = max((e["best"] for e in scored if e["best"] >= match), default=0.0)
    anchors, candidates = [], []
    for e in sorted(scored, key=lambda e: (-e["rank"], -e["best"],
                                           e["name"])):
        if e["best"] >= match and e["best"] >= top - margin:
            anchors.append(e)
        elif e["best"] >= match:
            e["margin_trimmed"] = True
            candidates.append(e)
        elif e["best"] >= floor:
            candidates.append(e)
    return anchors, candidates


def _bfs_path(graph, start, goal):
    """Deterministic BFS over the adjacency (fk edges explored before
    rule edges, then by neighbor name). Returns [(from, edge_key, to)]
    or None."""
    if start == goal:
        return []
    prev = {start: None}
    q = deque([start])
    while q:
        n = q.popleft()
        for key, nb in graph["adjacency"][n]:
            if nb in prev:
                continue
            prev[nb] = (n, key)
            if nb == goal:
                path = []
                cur = nb
                while prev[cur] is not None:
                    frm, k = prev[cur]
                    path.append((frm, k, cur))
                    cur = frm
                return list(reversed(path))
            q.append(nb)
    return None


def connect(graph, table_ids):
    """The minimal connecting subgraph: union of pairwise shortest
    paths; shared edges appear once; a pair with no path is a GAP,
    reported, never hidden. NOT called by the phase 03 chat — waits
    for the future phase that writes queries."""
    ids = sorted(set(table_ids),
                 key=lambda t: graph["tables"][t]["table_name"])
    hops, tables_in, gaps = {}, set(ids), []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            path = _bfs_path(graph, a, b)
            if path is None:
                gaps.append({
                    "from": graph["tables"][a]["table_name"],
                    "to": graph["tables"][b]["table_name"]})
                continue
            for frm, key, to in path:
                tables_in.add(frm)
                tables_in.add(to)
                if key not in hops:
                    e = graph["edges"][key]
                    hop = {
                        "from_table": graph["tables"][frm]["table_name"],
                        "to_table": graph["tables"][to]["table_name"],
                        "edge_key": key, "edge_kind": e["kind"],
                        "owner_table": e["source_table_name"],
                        "column_pairs": e["column_pairs"],
                    }
                    if e["kind"] == "joins_by_rule":
                        hop["rule"] = e["rule"]
                    hops[key] = hop
    return {"tables": sorted(graph["tables"][t]["table_name"]
                             for t in tables_in),
            "hops": list(hops.values()), "gaps": gaps}
