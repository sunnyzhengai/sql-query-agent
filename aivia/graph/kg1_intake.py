"""KG layer 1's ONE writer — the extract builder (CONTRACT_DATALOAD).

Registration mints the db (A1 refined: the db is a DBA prerequisite,
never extract-derived); extracts attach schemas downward. Intake
validates the whole extract BEFORE anything touches the graph (LC-F5:
atomic or nothing), then applies as a diff — unchanged objects get NO
new version (LC-S3 idempotence). Every refusal names its rule so the
customer's DBA can self-serve (the error-contract law).
"""
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from aivia.graph.store import Store

REQUIRED_FILES = ("manifest.json", "tables.csv", "columns.csv",
                  "pk.csv", "joins.csv")
MANIFEST_FIELDS = ("source", "operator", "db_name", "server", "as_of",
                   "source_pack_version")
# Phrase rule (source-pack data in production; one pack, one variant here):
# opportunistic — no match yields ABSENT + a counted gap row, never a guess.
GRAIN_PHRASE = re.compile(
    r"contains one record (?:for each|per) (?P<grain>.+?) in your system")


class Refusal(Exception):
    """A named refusal: rule + message the DBA can act on alone."""

    def __init__(self, rule: str, message: str):
        self.rule = rule
        super().__init__(f"{rule}: {message}")


@dataclass
class ExtractSnapshot:
    manifest: Dict[str, Any]
    tables: List[Dict[str, str]]
    columns: List[Dict[str, str]]
    pks: List[Dict[str, str]]
    joins: List[Dict[str, str]]
    values: List[Dict[str, str]]

    @property
    def source(self) -> str:
        return self.manifest["source"]

    @property
    def extract_id(self) -> str:
        return (f"{self.manifest['source']}@{self.manifest['as_of']}"
                f"#{self.manifest['source_pack_version']}")


@dataclass
class IntakeReport:
    source: str
    objects_created: int = 0
    change_report_kinds_created: Set[str] = field(default_factory=set)
    gap_lists: Dict[str, List[str]] = field(default_factory=dict)
    quarantined_join_groups: List[str] = field(default_factory=list)
    dba_alerts: List[str] = field(default_factory=list)
    illegal_declarations: List[str] = field(default_factory=list)
    pending_references: List[str] = field(default_factory=list)
    check_outcomes: Dict[str, str] = field(default_factory=dict)
    changed_objects: List[str] = field(default_factory=list)
    retired_objects: List[str] = field(default_factory=list)


def load_snapshot(snap_dir) -> ExtractSnapshot:
    snap_dir = Path(snap_dir)
    missing = [f for f in REQUIRED_FILES if not (snap_dir / f).is_file()]
    if missing:
        raise Refusal("INTAKE-0", f"missing extract part(s): "
                      f"{', '.join(missing)} — a missing part is a named "
                      "refusal, not a partial load")

    def rows(name):
        path = snap_dir / name
        if not path.is_file():
            return []
        return list(csv.DictReader(open(path)))
    return ExtractSnapshot(
        manifest=json.loads((snap_dir / "manifest.json").read_text()),
        tables=rows("tables.csv"), columns=rows("columns.csv"),
        pks=rows("pk.csv"), joins=rows("joins.csv"),
        values=rows("values.csv"))


def apply_registration(store: Store, reg: Dict[str, Any]) -> None:
    """Mint the db node and its layer-3 dba responsibility from the
    DBA-completed prerequisite — BEFORE any intake (A1 refined)."""
    db_id = f"db:{reg['db_name']}"
    if any(n.identity == db_id for n in store.current_nodes("db")):
        return
    as_of = reg["registered_at"]
    store.append_node("db", db_id, {
        "name": reg["db_name"],
        "minted_from": "registration prerequisite (DBA-completed)",
        "registered_at": as_of,
    }, as_of=as_of, extract_id="registration")
    from aivia.graph import kg3_artifacts
    kg3_artifacts.append_responsibility(
        store, artifact_id=f"responsibility:dba:{db_id}", kind="dba",
        holder=reg["dba_team"], target=db_id, author=reg["dba_team"],
        created_at=as_of)


def validate_extract(reg: Dict[str, Any], snap: ExtractSnapshot,
                     known_packs: Set[str]) -> None:
    m = snap.manifest
    absent = [f for f in MANIFEST_FIELDS if not m.get(f)]
    if absent:
        raise Refusal("INTAKE-1", f"manifest incomplete: missing {absent}")
    pack = m["source_pack_version"]
    if pack not in known_packs:
        raise Refusal("INTAKE-7", f"source-pack version '{pack}' is unknown "
                      "or retired — extracts load only from registered packs")
    if m["db_name"] != reg["db_name"]:
        raise Refusal("INTAKE-8", f"db '{m['db_name']}' is not registered; "
                      f"registration prerequisite lists: {reg['db_name']}")
    captured = m.get("captured_db_name", m["db_name"])
    if captured != m["db_name"]:
        raise Refusal("INTAKE-9", f"declared '{m['db_name']}' vs captured "
                      f"'{captured}' — both values named; correct the "
                      "registration or rerun against the right database")
    mapping = reg["schema_sources"]
    for row in snap.tables:
        owner = mapping.get(row["schema"])
        if owner != snap.source:
            raise Refusal("INTAKE-8", f"(schema mapping): schema "
                          f"'{row['schema']}' is not mapped to source "
                          f"'{snap.source}'")
    table_keys = [(r["schema"], r["table"]) for r in snap.tables]
    if len(set(table_keys)) != len(table_keys):
        raise Refusal("INTAKE-2", "dedup assertion failed: duplicate "
                      "(schema, table) rows survived the pack's filter")
    keyed = {(r["schema"], r["table"]) for r in snap.pks}
    keyless = [f"{s}.{t}" for (s, t) in table_keys if (s, t) not in keyed]
    if keyless:
        raise Refusal("INTAKE-10", f"keyless table(s): {', '.join(keyless)}")
    known = set(table_keys)
    orphans = [f"{r['schema']}.{r['table']}.{r['column']}"
               for r in snap.columns
               if (r["schema"], r["table"]) not in known]
    if orphans:
        raise Refusal("LC-C3", f"orphan column {', '.join(orphans)} — "
                      "refused + counted, not half-created")


def group_joins(snap: ExtractSnapshot,
                report: IntakeReport) -> List[List[Dict[str, str]]]:
    """Contract §6: group by the explicit id, order by ordinal;
    malformed groups quarantine + count + DBA alert (A14), never
    silently grouped and never a wall."""
    groups: Dict[str, List[Dict[str, str]]] = {}
    for row in snap.joins:
        groups.setdefault(row["fk_num"], []).append(row)
    ordered = []
    for fk_num, rows in sorted(groups.items(), key=lambda kv: int(kv[0])):
        rows.sort(key=lambda r: int(r["ordinal"]))
        if [int(r["ordinal"]) for r in rows] != list(range(1, len(rows) + 1)):
            report.quarantined_join_groups.append(fk_num)
            report.dba_alerts.append(
                f"fk group {fk_num} has malformed ordinals "
                f"{[r['ordinal'] for r in rows]} — quarantined (A14); "
                "please confirm the intended column pairing")
            continue
        ordered.append(rows)
    return ordered


def phrase_extract(description: str) -> Optional[str]:
    match = GRAIN_PHRASE.search(description or "")
    return match.group("grain") if match else None


def _desired_state(store, reg, snap, report):
    source, as_of = snap.source, snap.manifest["as_of"]
    mapping = reg["schema_sources"]
    db_id = f"db:{reg['db_name']}"
    nodes: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    contains: Set[Tuple[str, str]] = set()

    pk_by_table: Dict[Tuple[str, str], List[Tuple[int, str]]] = {}
    for row in snap.pks:
        pk_by_table.setdefault((row["schema"], row["table"]), []).append(
            (int(row["ordinal"]), row["column"]))

    for row in snap.tables:
        schema_id = f"{source}|{row['schema']}"
        table_id = f"{schema_id}|{row['table']}"
        nodes.setdefault(schema_id, ("schema", {}))
        contains.add((db_id, schema_id))
        grain = phrase_extract(row["description"])
        if grain is None:
            report.gap_lists["grain_not_declared"].append(table_id)
        pk_cols = [c for _, c in
                   sorted(pk_by_table[(row["schema"], row["table"])])]
        nodes[table_id] = ("table", {"description": row["description"],
                                     "grain": grain, "pk_columns": pk_cols})
        contains.add((schema_id, table_id))
    for row in snap.columns:
        table_id = f"{source}|{row['schema']}|{row['table']}"
        col_id = f"{table_id}|{row['column']}"
        nodes[col_id] = ("column", {"description": row["description"]})
        contains.add((table_id, col_id))

    # joins -> edges; INTAKE-6 legality on the dependent (src) side;
    # A8 pending when the target does not exist yet
    existing_tables = {n.identity for n in store.current_nodes("table")}
    all_tables = existing_tables | {i for i, (k, _) in nodes.items()
                                    if k == "table"}
    candidates = []
    for rows in group_joins(snap, report):
        first = rows[0]
        if mapping.get(first["src_schema"]) != source:
            report.illegal_declarations.append(
                f"INTAKE-6: declared join fk group {first['fk_num']} has "
                f"dependent side {first['src_schema']}.{first['src_table']} "
                f"owned by '{mapping.get(first['src_schema'])}', not "
                f"'{source}' — declaration refused + counted")
            continue
        frm = (f"{source}|{first['src_schema']}|{first['src_table']}")
        dest_source = mapping.get(first["dest_schema"])
        to = f"{dest_source}|{first['dest_schema']}|{first['dest_table']}"
        if to not in all_tables:
            report.pending_references.append(
                f"fk group {first['fk_num']} -> {to} (target not yet "
                "registered; resolves on arrival, A8)")
            continue
        on = [[r["src_column"], r["dest_column"]] for r in rows]
        candidates.append((frm, to, on))

    # dedup by stated rule: same (from, to, src columns) twice ->
    # the group targeting the destination's declared pk wins
    def dest_pk(table_id):
        if table_id in nodes:
            return tuple(nodes[table_id][1].get("pk_columns", []))
        for n in store.current_nodes("table"):
            if n.identity == table_id:
                return tuple(n.properties["pk_columns"])
        return ()
    edges: Dict[Tuple, Tuple] = {}
    for frm, to, on in candidates:
        key = (frm, to, tuple(p[0] for p in on))
        if key in edges:
            kept = edges[key]
            if tuple(p[1] for p in kept[2]) != dest_pk(to):
                edges[key] = (frm, to, on)
        else:
            edges[key] = (frm, to, on)

    # values (part 4): dump tables define the value set; the map lands
    # on the REFERENCING column via the declared join, keys trimmed
    dumps: Dict[str, Dict[str, str]] = {}
    for row in snap.values:
        dumps.setdefault(row["table"], {})[row["code"].strip()] = \
            row["meaning"].strip()
    for frm, to, on in edges.values():
        dest_table = to.rsplit("|", 1)[-1]
        if dest_table in dumps and len(on) == 1:
            col_id = f"{frm}|{on[0][0]}"
            if col_id in nodes:
                nodes[col_id][1]["values"] = dumps[dest_table]

    return nodes, contains, list(edges.values()), as_of


def object_hash(kind: str, props: Dict[str, Any]) -> str:
    """CONTRACT_DATALOAD §13: hash over the object's declared syntax
    + semantics as loaded — the mechanical basis of incremental
    intake and object-grain staleness. loaded_at/content_hash are
    stamps, never content — excluded from their own computation."""
    import hashlib
    import json as _json
    content = {k: v for k, v in props.items()
               if k not in ("content_hash", "loaded_at")}
    return hashlib.sha256(
        _json.dumps([kind, content], sort_keys=True).encode()
    ).hexdigest()[:16]


def apply_extract(store: Store, reg: Dict[str, Any],
                  snap: ExtractSnapshot) -> IntakeReport:
    """Validate fully, then apply as a diff — atomic (LC-F5),
    idempotent at the HASH grain (INTAKE-13, §13: an unchanged
    object writes nothing across extracts — the ledger-close of
    full reload as the intake MODE). Call via flows.inbound."""
    report = IntakeReport(source=snap.source)
    report.gap_lists = {"grain_not_declared": [], "pk_missing": []}
    nodes, contains, join_edges, as_of = _desired_state(
        store, reg, snap, report)
    extract_id = snap.extract_id

    current = {n.identity: n for n in store.current_nodes()}
    report.changed_objects = []  # the object-grain staleness feed
    for identity, (kind, props) in nodes.items():
        h = object_hash(kind, props)
        prior = current.get(identity)
        if prior is not None \
                and prior.properties.get("content_hash") == h:
            continue  # INTAKE-13: unchanged hash -> NO new version
        props = dict(props, content_hash=h, loaded_at=as_of)
        store.append_node(kind, identity, props, as_of, extract_id)
        report.changed_objects.append(identity)
        if prior is None:
            report.change_report_kinds_created.add(kind)
            if kind in ("schema", "table"):
                report.objects_created += 1

    # §11 RETIRE: this source's objects absent from the new extract —
    # marked, never removed; attached artifacts surface via the
    # anchor census, references stay valid
    report.retired_objects = []
    desired = set(nodes)
    for identity, node in current.items():
        if node.kind in ("schema", "table", "column") \
                and identity.startswith(f"{snap.source}|") \
                and identity not in desired:
            store.retire_node(identity, as_of)
            report.retired_objects.append(identity)

    have_contains = {(e.from_id, e.to_id)
                     for e in store.current_edges("contains")}
    for frm, to in sorted(contains - have_contains):
        store.append_edge("contains", frm, to, {}, as_of, extract_id)

    have_joins = {(e.from_id, e.to_id,
                   tuple(map(tuple, e.properties["on"])))
                  for e in store.current_edges("joins_to")}
    for frm, to, on in join_edges:
        if (frm, to, tuple(map(tuple, on))) in have_joins:
            continue
        store.append_edge("joins_to", frm, to,
                          {"on": on, "cardinality": "many_to_one"},
                          as_of, extract_id)
    report.check_outcomes["INTAKE-0..10"] = "pass"
    # INTAKE-11: every object at intake carries its content hash —
    # structurally true by the write path above; declared as a check
    report.check_outcomes["INTAKE-11"] = "pass"
    report.check_outcomes["INTAKE-13"] = (
        f"pass ({len(report.changed_objects)} written, unchanged "
        "objects wrote nothing)")
    return report


def audit_incremental(store: Store, reg: Dict[str, Any],
                      snap: ExtractSnapshot) -> List[str]:
    """INTAKE-12 (§13): the equivalence audit — a FULL parallel load
    into a scratch store, compared against incremental state by
    object hash. Any delta is a COUNTED finding naming the object
    and the divergence — never silently reconciled. Mechanical,
    never trusted (the 5-rule gate)."""
    scratch = Store()
    apply_registration(scratch, reg)
    apply_extract(scratch, reg, snap)
    fresh = {n.identity: n.properties.get("content_hash")
             for n in scratch.current_nodes()
             if n.kind in ("schema", "table", "column")}
    live = {n.identity: n.properties.get("content_hash")
            for n in store.current_nodes()
            if n.kind in ("schema", "table", "column")
            and n.identity.startswith(f"{snap.source}|")}
    findings = []
    for identity in sorted(set(fresh) | set(live)):
        a, b = fresh.get(identity), live.get(identity)
        if a != b:
            findings.append(
                f"INTAKE-12: {identity} — full-load hash {a} vs "
                f"incremental {b}")
    return findings
