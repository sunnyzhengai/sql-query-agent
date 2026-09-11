"""Generate the M1 graph visual FROM THE STORE — reads the
ed_sepsis_dev export parquets (the exact rows Fabric Graph
serves), computes a deterministic layout, and emits a
self-contained HTML page. Nothing hand-authored: every node,
edge, and description is a parquet row."""
import json
import math
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXP = ROOT / "AIVIA_Product/estates/ed_sepsis_dev/graph_export"
OUT = pathlib.Path(__file__).parent / "aivia_graph_m1.html"

t = pd.read_parquet(EXP / "graph_table.parquet")
c = pd.read_parquet(EXP / "graph_column.parquet")
s = pd.read_parquet(EXP / "graph_db_schema.parquet")
db = pd.read_parquet(EXP / "graph_db.parquet")
hp_sc_t = pd.read_parquet(EXP / "graph_has_part_schemaTable.parquet")
hp_t_c = pd.read_parquet(EXP / "graph_has_part_tableColumn.parquet")
hp_db_s = pd.read_parquet(EXP / "graph_has_part_dbSchema.parquet")
joins = pd.read_parquet(EXP / "graph_joins_to_tableTable.parquet")
pkcsv = pd.read_csv(ROOT / "AIVIA_Product/estates/ed_sepsis_dev/"
                    "sepsis_snapshot/pk.csv")
pk_of = {}
for r in pkcsv.sort_values(["schema", "table", "ordinal"]).itertuples():
    pk_of.setdefault((r.schema, r.table), []).append(r.column)

def trunc(x, n=170):
    x = (x or "").strip()
    return x[: n - 1] + "…" if len(x) > n else x

# ---- indices -------------------------------------------------
tables = list(t.sort_values("nodeId").itertuples(index=False))
tid = {row.nodeId: i for i, row in enumerate(tables)}
schema_of_table = {r.targetId: r.sourceId
                   for r in hp_sc_t.itertuples(index=False)}
schemas = list(s.sort_values("nodeId").itertuples(index=False))
sid = {row.nodeId: i for i, row in enumerate(schemas)}
cols_by_table = {}
for r in hp_t_c.itertuples(index=False):
    cols_by_table.setdefault(r.sourceId, []).append(r.targetId)
cmeta = {row.nodeId: row for row in c.itertuples(index=False)}

jpairs = [(tid[r.sourceId], tid[r.targetId], r.onColumns)
          for r in joins.itertuples(index=False)]

# ---- layout: force sim over the 90 tables --------------------
N = len(tables)
ncols = [len(cols_by_table.get(row.nodeId, [])) for row in tables]
rad = [95 + 6.5 * math.sqrt(max(n, 1)) for n in ncols]  # column disc radius
pos = []
for i, row in enumerate(tables):
    k = sid.get(schema_of_table.get(row.nodeId), 0)
    base = k * 2.1 + (i * 2.399963)  # schema-clustered ring start
    r0 = 900 + 420 * (i % 5)
    pos.append([r0 * math.cos(base), r0 * math.sin(base)])

for it in range(900):
    fx = [0.0] * N
    fy = [0.0] * N
    for i in range(N):
        for j in range(i + 1, N):
            dx = pos[i][0] - pos[j][0]
            dy = pos[i][1] - pos[j][1]
            d2 = dx * dx + dy * dy + 0.01
            d = math.sqrt(d2)
            mind = rad[i] + rad[j] + 700
            rep = 300000 / d2 + (max(0, mind - d) * 0.9)
            fx[i] += dx / d * rep
            fy[i] += dy / d * rep
            fx[j] -= dx / d * rep
            fy[j] -= dy / d * rep
    for a, b, _ in jpairs:
        dx = pos[b][0] - pos[a][0]
        dy = pos[b][1] - pos[a][1]
        d = math.sqrt(dx * dx + dy * dy) + 0.01
        rest = rad[a] + rad[b] + 700
        f = 0.012 * (d - rest)
        fx[a] += dx / d * f
        fy[a] += dy / d * f
        fx[b] -= dx / d * f
        fy[b] -= dy / d * f
    for i, row in enumerate(tables):
        k = sid.get(schema_of_table.get(row.nodeId), 0)
        ax = 3800 * math.cos(k * 2.1 + 1.0)
        ay = 3800 * math.sin(k * 2.1 + 1.0)
        fx[i] += (ax - pos[i][0]) * 0.0003
        fy[i] += (ay - pos[i][1]) * 0.0003
        step = min(28.0, 0.9 * (1 - it / 900) + 0.08) * 18
        mag = math.sqrt(fx[i] ** 2 + fy[i] ** 2) + 1e-9
        lim = min(mag, step)
        pos[i][0] += fx[i] / mag * lim
        pos[i][1] += fy[i] / mag * lim

# ---- hard collision resolution: NO two column discs intersect
# (the force sim relaxes; this GUARANTEES — pushed pairs apart
# until every gap >= 40 world units, verified before emit)
for _ in range(400):
    moved = False
    for i in range(N):
        for j in range(i + 1, N):
            dx = pos[j][0] - pos[i][0]
            dy = pos[j][1] - pos[i][1]
            d = math.sqrt(dx * dx + dy * dy) + 1e-9
            need = rad[i] + rad[j] + 700
            if d < need:
                push = (need - d) / 2 + 0.5
                pos[i][0] -= dx / d * push
                pos[i][1] -= dy / d * push
                pos[j][0] += dx / d * push
                pos[j][1] += dy / d * push
                moved = True
    if not moved:
        break
worst = min(
    math.dist(pos[i], pos[j]) - rad[i] - rad[j]
    for i in range(N) for j in range(i + 1, N))
assert worst >= 699, f"disc overlap remains: {worst:.1f}"
print(f"collision pass: min inter-disc gap {worst:.1f} world units")

# ---- emit nodes ----------------------------------------------
GA = 2.39996322972865332  # golden angle
tnodes, cnodes = [], []
for i, row in enumerate(tables):
    d = dict(zip(t.columns, row))
    tnodes.append({
        "n": row.nodeId.rsplit("|", 1)[-1], "x": round(pos[i][0], 1),
        "y": round(pos[i][1], 1), "d": trunc(row.description, 220),
        "s": sid.get(schema_of_table.get(row.nodeId), 0),
        "pk": ", ".join(pk_of.get(
            tuple(row.nodeId.split("|")[1:3]), [])),
        "nc": ncols[i]})
    for ci, colid in enumerate(sorted(cols_by_table.get(row.nodeId, []))):
        rr = 95 + 6.5 * math.sqrt(ci + 1)
        th = ci * GA
        m = cmeta[colid]
        cnodes.append({
            "n": colid.rsplit("|", 1)[-1], "t": i,
            "x": round(pos[i][0] + rr * math.cos(th), 1),
            "y": round(pos[i][1] + rr * math.sin(th), 1),
            "d": trunc(m.description, 170)})

snodes = []
for k, row in enumerate(schemas):
    mine = [i for i, tr in enumerate(tables)
            if sid.get(schema_of_table.get(tr.nodeId)) == k]
    sx = sum(pos[i][0] for i in mine) / max(len(mine), 1)
    sy = sum(pos[i][1] for i in mine) / max(len(mine), 1)
    snodes.append({"n": row.nodeId.rsplit("|", 1)[-1] if "|" in row.nodeId
                   else row.name, "x": round(sx, 1), "y": round(sy, 1),
                   "d": trunc(row.description, 170), "tt": mine})
dbrow = next(db.itertuples(index=False))
dnode = {"n": dbrow.name, "x": 0, "y": 0, "d": trunc(dbrow.description, 170)}

jedges = [{"a": a, "b": b, "on": on} for a, b, on in jpairs]

counts = {
    "nodes": 1 + len(snodes) + len(tnodes) + len(cnodes),
    "edges": len(hp_db_s) + len(hp_sc_t) + len(hp_t_c) + len(jedges),
    "hasPart": len(hp_db_s) + len(hp_sc_t) + len(hp_t_c),
    "joins": len(jedges),
    "described": sum(1 for n in tnodes if n["d"])
    + sum(1 for n in cnodes if n["d"]),
}

data = {"db": dnode, "schemas": snodes, "tables": tnodes,
        "cols": cnodes, "joins": jedges, "counts": counts}
payload = json.dumps(data, separators=(",", ":"))
print("payload bytes:", len(payload), "| counts:", counts)

html = open(pathlib.Path(__file__).parent / "m1_template.html").read()
html = html.replace("/*__DATA__*/{}", payload)
import hashlib
build = hashlib.sha256(html.encode()).hexdigest()[:8]
html = html.replace("__BUILD__", build)
OUT.write_text(html)
print("wrote", OUT, "· build", build)
