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
    """M2 (the bottom-up re-ruling, 2026-09-10): scope nodes with
    their STORED descriptions + scope—reads→table at TRUE grain —
    ties straight down into the verified technical layer; the
    file—reads→table rollup died with the top-down plan."""
    table_ids = {n.identity for n in read.nodes("table")}
    rows, reads_pairs = [], set()
    for n in sorted(read.nodes("scope"), key=lambda x: x.identity):
        ident = n.identity
        # literal: shape
        rows.append({
            "nodeId": ident,
            "name": ident.rsplit("::", 1)[-1],
            "description": str(n.properties.get("description") or ""),
            "structures": " ".join(n.properties.get("structures")
                                   or [])})
        for target, elbl in adj.get(ident, []):
            if elbl == "reads" and target in table_ids:
                reads_pairs.add((ident, target))
    return {"graph_scope": rows,
            "graph_reads_scopeTable": [
                {"sourceId": s_, "targetId": t_}
                for s_, t_ in sorted(reads_pairs)]}


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
