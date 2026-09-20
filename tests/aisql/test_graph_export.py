"""M1 — THE FABRIC GRAPH EXPORT READING (the materialization plan,
Manifest_Build §E5; ruled 2026-09-09: no Neo4j — the verification
surface is Fabric Graph on Sunny's capacity).

A READING: writes nothing to the graph; produces one table per
node label and one per (source, edge, target) pair — flattened
camelCase columns, nodeId key (the proven NL2GQL shape). M1 scope
is the TECHNICAL LAYER only: db · schema · table · column +
contains. The export mirrors the store EXACTLY — the same Q1/Q3
equalities Sunny will run in GQL are pinned here first.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql.flows import connect, export_graph
from aisql.graph.read_api import ReadApi

M1_LABELS = ("db", "db_schema", "table", "column")


@pytest.fixture(scope="module")
def world():
    from aisql.console import build_store
    store, _ = build_store("sepsis")
    read = ReadApi(store)
    return read, export_graph.export_tables(read, labels=M1_LABELS)


def test_one_node_table_per_label_with_store_counts(world):
    read, tables = world
    for label in M1_LABELS:
        rows = tables[f"graph_{label}"]
        assert len(rows) == len(read.nodes(label))


def test_governance_stays_home_until_m8(world):
    """THE M7 RE-SCOPE (Sunny 2026-09-18, Brief_M7 amendment:
    "make M7 only the consumption layer … make governance M8.
    plus we need to really design M8 before implementing"): no
    governance node table and no describes edge table rides the
    export until the M8 design sitting rules the physical form
    per item. SERVED_LABELS (lenses.Closed_Sets, registry 1.49.0)
    is the mirror. Consumption stays: pbi_report + executes."""
    _read, tables = world
    for label in ("description", "agent", "role", "responsibility",
                  "blessed_name", "person", "term", "usage"):
        assert f"graph_{label}" not in tables, label
    assert "graph_describes" not in tables
    assert "graph_pbi_report" in tables
    assert "graph_executes_reportFile" in tables


def test_camel_case_columns_and_node_id_key(world):
    _read, tables = world
    for name, rows in tables.items():
        assert rows, f"{name} is empty"
        for col in rows[0]:
            assert "_" not in col, f"{name}.{col} is not camelCase"
        if not (name.startswith("graph_has_part")
                    or name.startswith("graph_reads")
                    or name.startswith("graph_joins_to")
                    or name.startswith("graph_left_side")
                    or name.startswith("graph_right_side")
                    or name.startswith("graph_resolves_to")
                    or name.startswith("graph_uses_param")
                    or name.startswith("graph_cites")
                    or name.startswith("graph_executes")
                    or name.startswith("graph_describes")):
            assert "nodeId" in rows[0]
            ids = [r["nodeId"] for r in rows]
            assert len(ids) == len(set(ids)), f"{name}: dup nodeIds"


def test_descriptions_ride_verbatim(world):
    read, tables = world
    by_id = {r["nodeId"]: r for r in tables["graph_table"]}
    for n in read.nodes("table"):
        assert by_id[n.identity]["description"] == \
            (n.properties.get("description") or "")


def test_contains_edges_split_per_pair_and_mirror_the_store(world):
    read, tables = world
    adj = connect.build_adjacency(read)
    label_of = {n.identity: lbl for lbl in M1_LABELS
                for n in read.nodes(lbl)}
    ruled = {("db", "db_schema"), ("db_schema", "table"),
             ("table", "column")}  # containment points parent->child
    store_contains = {(s, t) for s, es in adj.items()
                      for t, lbl in es if lbl == "has_part"
                      and (label_of.get(s), label_of.get(t)) in ruled}
    exported = set()
    for pair in ("dbSchema", "schemaTable", "tableColumn"):
        for r in tables[f"graph_has_part_{pair}"]:
            exported.add((r["sourceId"], r["targetId"]))
    assert exported == store_contains


def test_parquet_write_is_deterministic_and_lossless(tmp_path, world):
    """Parquet by corpse (2026-09-09): CSV quote-escaping broke
    Fabric's loader — quote-bearing descriptions loaded NULL and
    their nodes/edges vanished. Parquet round-trips VERBATIM."""
    import pyarrow.parquet as pq
    _read, tables = world
    a, b = tmp_path / "a", tmp_path / "b"
    export_graph.write_parquet(tables, a)
    export_graph.write_parquet(tables, b)
    for f in sorted(a.iterdir()):
        assert f.read_bytes() == (b / f.name).read_bytes()
    # the corpse row survives byte-perfect, quotes and all
    cols = pq.read_table(a / "graph_column.parquet").to_pylist()
    victim = next(r for r in cols
                  if r["name"] == "WRONG_MED_ALT_CNT")
    assert '"NDC Not Part of Order"' in victim["description"]


# ---- M2: the scope layer (bottom-up re-ruling, 2026-09-10) ----------
def test_scope_rows_carry_stored_descriptions(world):
    read, tables = world
    rows = tables["graph_scope"]
    assert len(rows) == len(read.nodes("scope"))
    for r in rows:
        assert r["description"], f"{r['nodeId']}: empty description"
    names = {r["name"] for r in rows}
    assert "#Base_Pop" in names


def test_direct_read_nodes_ride_the_export_reads_retired(world):
    """ERA 3 (ratified 2026-09-14, superseding the M2 remainder
    rule): the no-join FROM ships as a direct_read node + one
    left_side edge — same sided shape as joins; the
    graph_reads_scopeTable parquet is RETIRED. The M2 deciding
    example (#Base_Pop × ED_ENCOUNTERS_FACT through a join side)
    still stands."""
    read, tables = world
    assert "graph_reads_scopeTable" not in tables
    nodes = tables["graph_direct_read"]
    assert nodes
    scopes = {r["nodeId"] for r in tables["graph_scope"]}
    table_ids = {n.identity for n in read.nodes("table")}
    owners = {r["targetId"]: r["sourceId"]
              for r in tables["graph_has_part_scopeDirectRead"]}
    sides = tables["graph_left_side_directReadTable"]
    by_dr = {r["sourceId"]: r["targetId"] for r in sides}
    assert len(sides) == len(nodes) == len(owners)
    for n in nodes:
        assert "::read#" in n["nodeId"]
        assert n["description"].startswith("Reads ")
        assert owners[n["nodeId"]] in scopes
        assert by_dr[n["nodeId"]] in table_ids
    # one mechanism now: a direct_read target is never ALSO a join
    # side of the same scope (the old DISJOINT, kept as a sanity)
    side_tabs = {}
    for lbl in ("left_side", "right_side"):
        for ed in read._store.current_edges(lbl):
            if ed.to_id in table_ids and "::join#" in ed.from_id:
                side_tabs.setdefault(
                    ed.from_id.rsplit("::join#", 1)[0],
                    set()).add(ed.to_id)
    for dr, t_ in by_dr.items():
        assert t_ not in side_tabs.get(
            dr.rsplit("::read#", 1)[0], set()), (dr, t_)
    # the M2 deciding example still travels through a join
    assert "emr|dbo|ED_ENCOUNTERS_FACT" in side_tabs.get(
        "reporting/USP_ED_SEPSIS.sql::#Base_Pop", set())


def test_declared_dictionary_joins_ride_the_export(world):
    read, tables = world
    rows = tables["graph_joins_to_tableTable"]
    assert len(rows) == len(list(
        read._store.current_edges("joins_to")))
    table_ids = {n.identity for n in read.nodes("table")}
    for r in rows:
        assert r["sourceId"] in table_ids
        assert r["targetId"] in table_ids
        assert r["onColumns"]
    # the deciding example: ADT_EVENTS joins DEPARTMENTS by id
    assert any(r["sourceId"].endswith("ADT_EVENTS")
               and r["targetId"].endswith("|DEPARTMENTS")
               and "DEPARTMENT_ID" in r["onColumns"]
               for r in rows)


# ---- THE RESERVED-WORD GATE (Sunny 2026-09-09: 'let's replace
# these key words' — checked against the vendored OFFICIAL list,
# never discovered live in the query editor again) ----------------
def test_no_name_collides_with_gql_reserved_words(world):
    import json
    import pathlib

    from aisql.graph.metamodel import REGISTRY_DIR
    reserved = set(json.loads(
        (pathlib.Path(REGISTRY_DIR).parent
         / "Registry_GQL_Reserved_Words.json")
        .read_text())["reserved"])
    _read, tables = world
    offenders = []
    ledger = metamodel_ledger()
    for name, row in ledger:
        if name.upper() in reserved:
            offenders.append(f"ledger {row['Kind']} '{name}'")
    for tname, rows in tables.items():
        if tname.upper() in reserved:
            offenders.append(f"table '{tname}'")
        for col in (rows[0] if rows else {}):
            if col.upper() in reserved:
                offenders.append(f"{tname}.{col}")
    assert not offenders, (
        "GQL-reserved names in the export/ledger — rename by "
        f"ruling before shipping: {offenders}")


def metamodel_ledger():
    from aisql.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Shape_Ledger"]
    return [(r["Name"], r) for r in sheet if r["Name"] != "-"]


# ---- M5 rides: the F2+F4 export fix (Brief_M5_Statement_Layer) ----
# Ruled 2026-09-17 (F2 "yes" + F4 "yes" on all three parts): list
# and dict node properties export as "; "-joined text — lists as
# "A; B", dict pairs as "code = meaning" — instead of the silent
# line-51 drop that ate pk_columns and values.

def test_pk_columns_ride_as_joined_text(world):
    read, tables = world
    rows = {r["nodeId"]: r for r in tables["graph_table"]}
    witnessed = 0
    for n in read.nodes("table"):
        pk = n.properties.get("pk_columns")
        if pk:
            witnessed += 1
            assert rows[n.identity]["pkColumns"] == "; ".join(pk)
    assert witnessed, "the fixture carries pk_columns tables"


def test_dict_values_ride_as_code_meaning_pairs():
    """No estate fixture carries a values dict today (measured:
    sepsis 0, ed_sepsis_dev 0) — the witness is a synthetic node,
    so the pin can never be silently vacuous (the placeholder
    law's no-naked-pin clause)."""
    from aisql.graph.store import Store
    store = Store()
    store.append_node(
        "column", "simemr|dbo|T|CODE",
        {"description": "a coded field",
         "values": {"1": "Emergency", "2": "Urgent"},
         "data_type": "varchar"},
        "2026-09-17T00:00:00Z", "kg1@test")
    tables = export_graph.export_tables(ReadApi(store),
                                        labels=("column",))
    row = tables["graph_column"][0]
    assert row["values"] == "1 = Emergency; 2 = Urgent"
    assert row["dataType"] == "varchar"


# ---- M6 rides: the file's blob-free row (Brief_M6_File_Layer) ----

def test_file_rows_are_blob_free(world):
    """M6-4 (Sunny "yes" #2): nodeId · name · description ·
    technicalDefinition · contentHash · loadedAt ONLY — the tree
    and twin blobs NEVER ride the export."""
    read, tables = world
    rows = tables["graph_file"]
    assert rows, "the file ships at M6"
    for r in rows:
        assert set(r) == {"nodeId", "name", "description",
                          "technicalDefinition", "contentHash",
                          "loadedAt"}
        assert "tree" not in r and "twin" not in r
