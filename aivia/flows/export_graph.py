"""M1 — the Fabric Graph export (Manifest_Build §E5; ruled
2026-09-09: the verification surface is Fabric Graph on Sunny's
capacity — no Neo4j in a Microsoft Marketplace offering).

A READING under the center law: writes nothing to the graph.
Produces one table per node label and one per (source, edge,
target) pair — flattened camelCase columns, nodeId key, the shape
the Fabric Graph model editor maps directly (the proven NL2GQL
export shape). The export mirrors the store AS-IS: absent grains
stay absent, so Sunny's GQL sees the same truth the shape census
declares.

PARQUET, never CSV (ruled by corpse 2026-09-09: Fabric's
Load-to-Tables mis-parsed standard CSV quote-escaping — every
column whose description contained double-quotes loaded as NULL
and its nodes/edges vanished at graph refresh; Sunny's per-table
GQL diff found them. Parquet has no parsing layer.)

Usage:  python3.11 -m aivia.flows.export_graph <estate>
        (writes AIVIA_Product/estates/<estate>/graph_export/*.parquet)
"""
import pathlib
import sys
from typing import Dict, List, Optional, Tuple

from aivia.flows import connect
from aivia.graph.read_api import ReadApi

# batch M1: the technical layer; later batches append labels here
# in their own commits (the Shape_Ledger names each landing)
# literal: schema-mirror lenses.Shape_Ledger
EXPORT_LABELS = ("db", "db_schema", "table", "column")

_PAIR_NAMES = {("db", "db_schema"): "dbSchema",
               ("db_schema", "table"): "schemaTable",
               ("table", "column"): "tableColumn"}  # literal: shape


def _camel(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _node_row(n) -> Dict[str, str]:
    # literal: shape
    row = {"nodeId": n.identity,
           "name": str(n.properties.get("name")
                       or n.identity.rsplit("|", 1)[-1]),
           "description": str(n.properties.get("description") or "")}
    for k, v in sorted(n.properties.items()):
        if k in ("name", "description") or isinstance(v, (dict, list)):
            continue
        row[_camel(k)] = "" if v is None else str(v)
    return row


def _scope_tables(read: ReadApi,
                  adj) -> Dict[str, List[Dict[str, str]]]:
    """M2 THE JOIN LAYER (the redesign ruling, 2026-09-10): scope
    nodes with STORED descriptions · join nodes (the observed
    pairs) · scope—has_part→join · join—left_side/right_side→
    table-or-scope · scope—reads→table as the REMAINDER ONLY —
    every row a STORE row (one home of meaning), never an
    adjacency recomputation."""
    store = read._store
    table_ids = {n.identity for n in read.nodes("table")}
    scope_rows = []
    for n in sorted(read.nodes("scope"), key=lambda x: x.identity):
        # literal: shape
        scope_rows.append({
            "nodeId": n.identity,
            "name": n.identity.rsplit("::", 1)[-1],
            "description": str(n.properties.get("description") or ""),
            "structures": " ".join(n.properties.get("structures")
                                   or [])})
    join_rows = []
    for n in sorted(read.nodes("join"), key=lambda x: x.identity):
        # literal: shape
        join_rows.append({
            "nodeId": n.identity,
            "name": str(n.properties.get("name") or ""),
            "description": str(n.properties.get("description") or ""),
            "onPredicate": str(n.properties.get("on") or ""),
            "joinType": str(n.properties.get("joinType") or "")})
    # era 3 (ratified 2026-09-14): the single-table FROM's sided
    # node — no ON, no type, BY KIND
    dr_rows = []
    for n in sorted(read.nodes("direct_read"),
                    key=lambda x: x.identity):
        # literal: shape
        dr_rows.append({
            "nodeId": n.identity,
            "name": str(n.properties.get("name") or ""),
            "description": str(n.properties.get("description")
                               or "")})
    cond_rows = []
    for n in sorted(read.nodes("condition"), key=lambda x: x.identity):
        # literal: shape
        cond_rows.append({
            "nodeId": n.identity,
            "name": str(n.properties.get("name") or ""),
            "description": str(n.properties.get("description") or ""),
            "kind": str(n.properties.get("kind") or ""),
            "degenerate": str(n.properties.get("degenerate") or ""),
            "fragment": str(n.properties.get("fragment") or "")})
    param_rows = []
    for n in sorted(read.nodes("param"), key=lambda x: x.identity):
        # literal: shape
        param_rows.append({
            "nodeId": n.identity,
            "name": str(n.properties.get("name") or ""),
            "description": str(n.properties.get("description") or "")})
    # M4 (2026-09-16): one node per computed output — STAY FLAT
    dcol_rows = []
    for n in sorted(read.nodes("derived_column"),
                    key=lambda x: x.identity):
        # literal: shape
        dcol_rows.append({
            "nodeId": n.identity,
            "name": str(n.properties.get("name") or ""),
            "description": str(n.properties.get("description") or ""),
            "derivation": str(n.properties.get("derivation") or ""),
            "operation": str(n.properties.get("operation") or ""),
            "position": str(n.properties.get("position") or ""),
            "fragment": str(n.properties.get("fragment") or "")})
    # literal: shape
    tables: Dict[str, List[Dict[str, str]]] = {
        "graph_scope": scope_rows, "graph_join": join_rows,
        "graph_direct_read": dr_rows,
        "graph_condition": cond_rows, "graph_param": param_rows,
        "graph_derived_column": dcol_rows}
    tables["graph_has_part_scopeJoin"] = sorted(
        ({"sourceId": e.from_id, "targetId": e.to_id}
         for e in store.current_edges("has_part")
         if "::join#" in e.to_id),
        key=lambda r: (r["sourceId"], r["targetId"]))
    tables["graph_has_part_scopeDirectRead"] = sorted(
        ({"sourceId": e.from_id, "targetId": e.to_id}
         for e in store.current_edges("has_part")
         if "::read#" in e.to_id),
        key=lambda r: (r["sourceId"], r["targetId"]))
    tables["graph_has_part_scopeDerivedColumn"] = sorted(
        ({"sourceId": e.from_id, "targetId": e.to_id}
         for e in store.current_edges("has_part")
         if "::dcol#" in e.to_id),
        key=lambda r: (r["sourceId"], r["targetId"]))
    tables["graph_cites_scopeColumn"] = sorted(
        ({"sourceId": e.from_id, "targetId": e.to_id}
         for e in store.current_edges("cites")),
        key=lambda r: (r["sourceId"], r["targetId"]))
    hp_jc, hp_sc, hp_cc = [], [], []
    for e in store.current_edges("has_part"):
        if "::cond#" not in e.to_id:
            continue
        # literal: shape
        row = {"sourceId": e.from_id, "targetId": e.to_id}
        if "::join#" in e.from_id:
            hp_jc.append(row)
        elif "::cond#" in e.from_id:
            hp_cc.append(row)
        else:
            hp_sc.append(row)
    for name, rows_ in (("joinCondition", hp_jc),
                        ("scopeCondition", hp_sc),
                        ("conditionCondition", hp_cc)):
        tables[f"graph_has_part_{name}"] = sorted(
            rows_, key=lambda r: (r["sourceId"], r["targetId"]))
    rt_col, rt_par = [], []
    for e in store.current_edges("resolves_to"):
        # literal: shape
        row = {"sourceId": e.from_id, "targetId": e.to_id,
               "role": str(e.properties.get("role") or "")}
        (rt_par if "::param/" in e.to_id else rt_col).append(row)
    tables["graph_resolves_to_conditionColumn"] = sorted(
        rt_col, key=lambda r: (r["sourceId"], r["targetId"], r["role"]))
    tables["graph_resolves_to_conditionParam"] = sorted(
        rt_par, key=lambda r: (r["sourceId"], r["targetId"], r["role"]))
    tables["graph_uses_param_scopeParam"] = sorted(
        ({"sourceId": e.from_id, "targetId": e.to_id}
         for e in store.current_edges("uses_param")),
        key=lambda r: (r["sourceId"], r["targetId"]))
    for side in ("left_side", "right_side"):
        by_target: Dict[str, List[Dict[str, str]]] = {
            "Table": [], "Scope": []}
        dr_side: List[Dict[str, str]] = []
        for e in store.current_edges(side):
            row = {"sourceId": e.from_id, "targetId": e.to_id}
            if "::read#" in e.from_id:
                dr_side.append(row)   # era 3: direct_read's side
                continue
            kind = "Table" if e.to_id in table_ids else "Scope"
            by_target[kind].append(row)
        for kind, rows_ in by_target.items():
            tables[f"graph_{side}_join{kind}"] = sorted(
                rows_, key=lambda r: (r["sourceId"], r["targetId"]))
        if side == "left_side":
            tables["graph_left_side_directReadTable"] = sorted(
                dr_side,
                key=lambda r: (r["sourceId"], r["targetId"]))
    # era 3: graph_reads_scopeTable RETIRED — the reads edge is
    # gone from the store; every read travels a side
    return tables


def export_tables(read: ReadApi,
                  labels: Optional[Tuple[str, ...]] = None
                  ) -> Dict[str, List[Dict[str, str]]]:
    labels = labels or EXPORT_LABELS
    tables: Dict[str, List[Dict[str, str]]] = {}
    label_of = {}
    for label in labels:
        rows = []
        for n in sorted(read.nodes(label), key=lambda x: x.identity):
            rows.append(_node_row(n))
            label_of[n.identity] = label
        tables[f"graph_{label}"] = rows
    adj = connect.build_adjacency(read)
    pairs: Dict[str, List[Dict[str, str]]] = {}
    for src, edges in sorted(adj.items()):
        for tgt, elabel in sorted(edges):
            if elabel != "has_part":
                continue
            sl, tl = label_of.get(src), label_of.get(tgt)
            pair = _PAIR_NAMES.get((sl, tl))
            if pair:
                pairs.setdefault(f"graph_has_part_{pair}", []).append(
                    {"sourceId": src, "targetId": tgt})
    tables.update(pairs)
    tables.update(_scope_tables(read, adj))
    joins = []
    for e in read._store.current_edges("joins_to"):
        on = e.properties.get("on") or []
        # literal: shape
        joins.append({"sourceId": e.from_id, "targetId": e.to_id,
                      "onColumns": "; ".join(
                          f"{a} = {b}" for a, b in on)})
    tables["graph_joins_to_tableTable"] = sorted(
        joins, key=lambda r: (r["sourceId"], r["targetId"]))
    return tables


def write_parquet(tables: Dict[str, List[Dict[str, str]]],
                  outdir) -> List[pathlib.Path]:
    import pyarrow as pa
    import pyarrow.parquet as pq
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, rows in sorted(tables.items()):
        cols = sorted({c for r in rows for c in r},
                      # literal: shape
                      key=lambda c: (c not in ("nodeId", "sourceId",
                                               "targetId", "name",
                                               "description"), c))
        table = pa.table({c: [r.get(c, "") for r in rows]
                          for c in cols})
        p = outdir / f"{name}.parquet"
        pq.write_table(table, p)
        written.append(p)
    return written


def main(estate: str) -> None:
    from aivia.console import build_store
    store, base = build_store(estate)
    tables = export_tables(ReadApi(store))
    files = write_parquet(tables, base / "graph_export")
    import pyarrow.parquet as pq
    for p in files:
        print(f"  {p.name:<36} {pq.read_metadata(p).num_rows:>6} rows")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sepsis")
