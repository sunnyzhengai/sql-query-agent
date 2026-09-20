"""Generate the M1 graph visual FROM THE STORE — reads the
ed_sepsis_dev export parquets (the exact rows Fabric Graph
serves), computes a deterministic layout, and emits a
self-contained HTML page. Nothing hand-authored: every node,
edge, and description is a parquet row."""
import hashlib
import json
import math
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXP = ROOT / "AIVIA_Product/estates/ed_sepsis_dev/graph_export"
OUT = pathlib.Path(__file__).parent / "aivia_graph_m1.html"



def trunc(x, n=170):
    x = (x or "").strip()
    return x[: n - 1] + "…" if len(x) > n else x


def _rows(path):
    import pyarrow.parquet as pq  # pandas-free: the FS1 test env
    return pq.read_table(path).num_rows


# literal: schema-mirror lenses.Shape_Ledger (the PRESENT labels)
NODE_LABELS = ("db", "db_schema", "table", "column", "scope",
               "join", "direct_read", "condition", "param",
               "derived_column", "statement", "file")
EDGE_FAMILIES = ("has_part", "joins_to", "left_side", "right_side",
                 "resolves_to", "uses_param", "cites")


def build_payload():
    """FS1 (Sunny "a", 2026-09-17, Contract_Surfaces): the
    generator's COUNTING STEP, label-keyed exactly as the answer
    key's census speaks — tests/aisql/test_visual_counts.py holds
    this to expected_m_gates.json before every republish. Counts
    the export parquets ON DISK: the same articles the page draws
    and Fabric serves."""
    nodes = {lb: _rows(EXP / f"graph_{lb}.parquet")
             for lb in NODE_LABELS}
    edges: dict = {}
    for p in sorted(EXP.glob("graph_*.parquet")):
        name = p.stem[len("graph_"):]
        if name in NODE_LABELS:
            continue
        fam = next((f for f in EDGE_FAMILIES
                    if name.startswith(f)), None)
        if fam:
            edges[fam] = edges.get(fam, 0) + _rows(p)
    return {"counts": {"nodes": nodes, "edges": edges}}


def main():
    import pandas as pd
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
    tnodes, cnodes, cids = [], [], []
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
            cids.append(colid)
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

    # ---- M2 THE JOIN LAYER (store rows: scope · join · sides · the
    # reads remainder) ---------------------------------------------
    sc = pd.read_parquet(EXP / "graph_scope.parquet")
    jn = pd.read_parquet(EXP / "graph_join.parquet")
    hp_sj = pd.read_parquet(EXP / "graph_has_part_scopeJoin.parquet")
    # era 3 (2026-09-14): the reads parquet retired — the no-join
    # read is a direct_read node (scope—has_part→·—left_side→table)
    # and renders like a join node with one side and no ON
    dr_df = pd.read_parquet(EXP / "graph_direct_read.parquet")
    dr_owner = {r.targetId: r.sourceId for r in pd.read_parquet(
        EXP / "graph_has_part_scopeDirectRead.parquet"
        ).itertuples(index=False)}
    dr_side = {r.sourceId: r.targetId for r in pd.read_parquet(
        EXP / "graph_left_side_directReadTable.parquet"
        ).itertuples(index=False)}
    sides = {}
    for side in ("left_side", "right_side"):
        for kind in ("Table", "Scope"):
            f = EXP / f"graph_{side}_join{kind}.parquet"
            for r in pd.read_parquet(f).itertuples(index=False):
                sides.setdefault(r.sourceId, {})[side] = r.targetId

    scopes_rows = list(sc.sort_values("nodeId").itertuples(index=False))
    scid = {r.nodeId: i for i, r in enumerate(scopes_rows)}
    rng = random.Random(7)
    scnodes = []
    for i, r in enumerate(scopes_rows):
        th = i * GA + 0.7
        rr = 2400 + 900 * rng.random()
        scnodes.append({
            "n": r.nodeId.rsplit("::", 1)[-1], "x": round(rr * math.cos(th), 1),
            "y": round(rr * math.sin(th), 1), "d": trunc(r.description, 200)})

    def ref(target):
        if target in tid:
            return {"t": "T", "i": tid[target]}
        if target in scid:
            return {"t": "S", "i": scid[target]}
        return None

    owner_of = {r.targetId: r.sourceId
                for r in hp_sj.itertuples(index=False)}
    jnodes = []
    for r in jn.sort_values("nodeId").itertuples(index=False):
        owner = scid.get(owner_of.get(r.nodeId, ""), 0)
        sd = sides.get(r.nodeId, {})
        o = scnodes[owner]
        jnodes.append({
            "n": r.name, "s": owner, "on": trunc(r.onPredicate, 120),
            "d": trunc(r.description, 200),
            "ls": ref(sd.get("left_side")), "rs": ref(sd.get("right_side")),
            "x": round(o["x"] + 60 * math.cos(len(jnodes) * GA), 1),
            "y": round(o["y"] + 60 * math.sin(len(jnodes) * GA), 1)})
    # era 3: direct_read joins the same node family — one ls, no rs
    for r in dr_df.sort_values("nodeId").itertuples(index=False):
        owner = scid.get(dr_owner.get(r.nodeId, ""), 0)
        o = scnodes[owner]
        jnodes.append({
            "n": r.name, "s": owner, "on": "",
            "d": trunc(r.description, 200),
            "ls": ref(dr_side.get(r.nodeId)), "rs": None,
            "x": round(o["x"] + 60 * math.cos(len(jnodes) * GA), 1),
            "y": round(o["y"] + 60 * math.sin(len(jnodes) * GA), 1)})
    # era 3: no scope→table reads lines — the direct_read node above
    # carries the connection; its count reports as "reads" still
    redges = []

    # ---- M3 THE CONDITION LAYER (store rows: condition · param ·
    # resolves_to role-tagged · uses_param) ------------------------
    cnd_df = pd.read_parquet(EXP / "graph_condition.parquet")
    par_df = pd.read_parquet(EXP / "graph_param.parquet")
    rt_cc = pd.read_parquet(EXP / "graph_resolves_to_conditionColumn.parquet")
    rt_cp = pd.read_parquet(EXP / "graph_resolves_to_conditionParam.parquet")
    up = pd.read_parquet(EXP / "graph_uses_param_scopeParam.parquet")

    cindex = {cid: i for i, cid in enumerate(cids)}
    cnd_rows = list(cnd_df.sort_values("nodeId").itertuples(index=False))
    cnid = {r.nodeId: i for i, r in enumerate(cnd_rows)}
    per_scope: dict = {}
    cndnodes = []
    for r in cnd_rows:
        owner = scid.get(r.nodeId.rsplit("::", 1)[0], 0)
        k = per_scope.get(owner, 0)
        per_scope[owner] = k + 1
        o = scnodes[owner]
        rr = 130 + 9 * math.sqrt(k + 1)
        th = k * GA + 1.3
        cndnodes.append({
            "n": r.nodeId.rsplit("::", 1)[-1], "s": owner,
            "x": round(o["x"] + rr * math.cos(th), 1),
            "y": round(o["y"] + rr * math.sin(th), 1),
            "d": trunc(r.description, 170)})

    par_rows = list(par_df.sort_values("nodeId").itertuples(index=False))
    pid = {r.nodeId: i for i, r in enumerate(par_rows)}
    uedges = [{"s": scid[r.sourceId], "p": pid[r.targetId]}
              for r in up.itertuples(index=False)]
    owner_scope_of_param = {e["p"]: e["s"] for e in uedges}
    pnodes = []
    for i, r in enumerate(par_rows):
        o = scnodes[owner_scope_of_param.get(i, 0)]
        pnodes.append({
            "n": r.name, "s": owner_scope_of_param.get(i, 0),
            "x": round(o["x"] + 320 * math.cos(i * 2.6 + .5), 1),
            "y": round(o["y"] + 320 * math.sin(i * 2.6 + .5), 1),
            "d": trunc(r.description, 170)})

    rc_edges = [{"c": cnid[r.sourceId], "t": cindex[r.targetId],
                 "role": getattr(r, "role", "")}
                for r in rt_cc.itertuples(index=False)
                if r.sourceId in cnid and r.targetId in cindex]
    rp_edges = [{"c": cnid[r.sourceId], "p": pid[r.targetId],
                 "role": getattr(r, "role", "")}
                for r in rt_cp.itertuples(index=False)
                if r.sourceId in cnid and r.targetId in pid]

    # ---- M4 THE DERIVED-COLUMN LAYER (store rows: derived_column ·
    # scope—has_part→derived_column · scope—cites→column) ----------
    dc_df = pd.read_parquet(EXP / "graph_derived_column.parquet")
    hp_sd = pd.read_parquet(
        EXP / "graph_has_part_scopeDerivedColumn.parquet")
    ct = pd.read_parquet(EXP / "graph_cites_scopeColumn.parquet")
    owner_of_dc = {r.targetId: r.sourceId
                   for r in hp_sd.itertuples(index=False)}
    per_scope_dc: dict = {}
    dcnodes = []
    for r in sorted(dc_df.itertuples(index=False),
                    key=lambda x: x.nodeId):
        owner = scid.get(owner_of_dc.get(r.nodeId, ""), 0)
        k = per_scope_dc.get(owner, 0)
        per_scope_dc[owner] = k + 1
        o = scnodes[owner]
        rr = 210 + 9 * math.sqrt(k + 1)
        th = k * GA + 2.6
        dcnodes.append({
            "n": r.name, "s": owner,
            "x": round(o["x"] + rr * math.cos(th), 1),
            "y": round(o["y"] + rr * math.sin(th), 1),
            "d": trunc(r.description, 170)})
    cite_edges = [{"s": scid[r.sourceId], "t": cindex[r.targetId]}
                  for r in ct.itertuples(index=False)
                  if r.sourceId in scid and r.targetId in cindex]

    side_edges = sum(1 for j in jnodes for k in ("ls", "rs") if j[k])
    counts = {
        "nodes": 1 + len(snodes) + len(tnodes) + len(cnodes)
        + len(scnodes) + len(jnodes) + len(cndnodes) + len(pnodes)
        + len(dcnodes),
        "edges": len(hp_db_s) + len(hp_sc_t) + len(hp_t_c) + len(jedges)
        + len(jnodes) + side_edges + len(redges)
        + len(cndnodes) + len(rc_edges) + len(rp_edges) + len(uedges)
        + len(dcnodes) + len(cite_edges),
        "hasPart": len(hp_db_s) + len(hp_sc_t) + len(hp_t_c) + len(jnodes)
        + len(cndnodes) + len(dcnodes),
        "joins": len(jedges),
        "scopes": len(scnodes), "joinNodes": len(jnodes),
        "sideEdges": side_edges, "reads": len(dr_df),
        "conds": len(cndnodes), "params": len(pnodes),
        "resolves": len(rc_edges) + len(rp_edges),
        "usesParam": len(uedges),
        "dcols": len(dcnodes), "cites": len(cite_edges),
        "described": sum(1 for n in tnodes if n["d"])
        + sum(1 for n in cnodes if n["d"])
        + sum(1 for n in scnodes if n["d"])
        + sum(1 for n in jnodes if n["d"])
        + sum(1 for n in cndnodes if n["d"])
        + sum(1 for n in pnodes if n["d"])
        + sum(1 for n in dcnodes if n["d"]),
    }

    data = {"db": dnode, "schemas": snodes, "tables": tnodes,
            "cols": cnodes, "joins": jedges, "scopes": scnodes,
            "joinNodes": jnodes, "reads": redges,
            "conds": cndnodes, "params": pnodes,
            "resolvesCol": rc_edges, "resolvesPar": rp_edges,
            "usesParam": uedges,
            "dcols": dcnodes, "cites": cite_edges, "counts": counts}
    payload = json.dumps(data, separators=(",", ":"))
    print("payload bytes:", len(payload), "| counts:", counts)

    html = open(pathlib.Path(__file__).parent / "m1_template.html").read()
    html = html.replace("/*__DATA__*/{}", payload)
    build = hashlib.sha256(html.encode()).hexdigest()[:8]
    html = html.replace("__BUILD__", build)
    OUT.write_text(html)
    print("wrote", OUT, "· build", build)


if __name__ == "__main__":
    main()
