"""ADR 0055 — run the shape corpus through the REAL pipeline and hold
it to the manifest (expected vs actual, per cell).

One implementation for both consumers: the `shapes` CI family
(tests/shapes/test_shapes_end_to_end.py) and the SHAPES_GAPCHECK.md
report generator. Parse (ScriptDom, local) → graph build → sweep —
the same code paths the tenant runs; nothing shape-specific in the
pipeline (isolation ruling: shapes touch none of the realism corpus).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from src.graph.serialization import parsed_sql_to_parse_result_row
from src.parser.identity import fold_identifier
from src.parser.sql_parser import parse_sql
from src.shapes.generator import (
    dict_rows,
    generate,
    metric_name_rows,
    steward_rows,
)
from src.steps.build_graph import BuildGraphOutput, build_graph_step


@dataclass
class CorpusRun:
    parse_rows: "list[dict]"
    build: BuildGraphOutput      # sweep folded in (ADR 0057)
    files: "dict[str, str]"
    manifest: dict
    parse_failures: "list[tuple[str, str]]" = field(default_factory=list)


@dataclass
class CellResult:
    cell_id: str
    status: str                 # instantiated | excluded
    ok: bool
    details: "list[str]" = field(default_factory=list)   # failures only
    reason: str = ""            # excluded cells carry their reason


def run_corpus(palette: dict) -> CorpusRun:
    files, manifest = generate(palette)
    parse_rows, failures = [], []
    for relpath in sorted(files):
        sql = files[relpath]
        schema, fname = relpath.split("/", 1)
        proc = fname[:-len(".sql")]
        metric_id = f"{schema}.{proc}"
        try:
            # normalize-early law: \r\n dies at the entry point,
            # exactly as the ingest notebooks normalize on load
            parsed = parse_sql(sql.replace("\r\n", "\n"))
            parse_rows.append(parsed_sql_to_parse_result_row(
                metric_id, proc, parsed,
                line_count=sql.count("\n") + 1))
        except Exception as e:              # noqa: BLE001 — classified
            # the pipeline grain: 200_parse classifies per-proc parse
            # errors into ops_parse_errors — a CLASSIFIED category is
            # a declared exception path, an unclassified one is a
            # product defect
            from src.parser.error_classifier import classify_parse_error
            cls = classify_parse_error(str(e), metric_id,
                                       sql.count("\n") + 1)
            failures.append((metric_id,
                             str(cls.get("error_category") or
                                 f"UNCLASSIFIED:{type(e).__name__}")))
    tables, columns = dict_rows(palette)
    build = build_graph_step(parse_rows, tables, columns,
                             steward_records=steward_rows(palette),
                             metric_name_records=metric_name_rows(palette),
                             sweep_run_at="shape-corpus")
    return CorpusRun(parse_rows=parse_rows, build=build,
                     files=files, manifest=manifest,
                     parse_failures=failures)


# ---------------------------------------------------------------------
# expectation checks — the GRAPH is the sole flag truth (ADR 0057),
# so every flag expectation ALSO asserts its reified cluster node
# and membership edges: this checker is the migration gate.


def _flags_by(run: CorpusRun) -> "list[dict]":
    return run.build.flags_rows


def _edges(run: CorpusRun) -> "list[dict]":
    return run.build.edges_rows


def _fold(name: str) -> str:
    return fold_identifier(str(name).replace(" ", "_"))


def _metric_keys(run: CorpusRun, metric_id: str) -> "tuple":
    import hashlib

    from src.orchestrator.tools import _content_key
    keys = []
    for n in run.build.nodes_rows:
        nid = str(n["node_id"])
        if not nid.startswith(f"transform:{metric_id}:"):
            continue
        props = n.get("properties")
        if isinstance(props, str):
            props = json.loads(props or "{}")
        frag = str((props or {}).get("sql_fragment") or "")
        if frag.strip():
            keys.append((int((props or {}).get("step_no") or 0),
                         _content_key(frag)))
    ordered = [k for _, k in sorted(keys)]
    return (hashlib.sha256("|".join(ordered).encode()).hexdigest()[:16]
            if ordered else "")


def _step_key(run: CorpusRun, metric_id: str,
              step_name: str) -> "str | None":
    from src.orchestrator.tools import _content_key
    prefix = f"transform:{metric_id}:"
    for n in run.build.nodes_rows:
        nid = str(n["node_id"])
        if nid.startswith(prefix) and _fold(
                nid[len(prefix):]) == _fold(step_name):
            props = n.get("properties")
            if isinstance(props, str):
                props = json.loads(props or "{}")
            frag = str((props or {}).get("sql_fragment") or "")
            return _content_key(frag) if frag.strip() else None
    return None


def _metric_fragments(run: CorpusRun, metric_id: str) -> str:
    prefix = f"transform:{metric_id}:"
    frags = []
    for n in run.build.nodes_rows:
        if str(n["node_id"]).startswith(prefix):
            props = n.get("properties")
            if isinstance(props, str):
                props = json.loads(props or "{}")
            frags.append(str((props or {}).get("sql_fragment") or ""))
    return "\n".join(frags)


def check_cell(cell: dict, run: CorpusRun) -> CellResult:
    if cell["status"] == "excluded":
        return CellResult(cell["cell_id"], "excluded", True,
                          reason=cell.get("reason", ""))
    exp = cell.get("expect") or {}
    fails: "list[str]" = []
    flags = _flags_by(run)
    edges = _edges(run)

    for f in exp.get("flags", []):
        found = [r for r in flags
                 if r["flag_class"] == f["flag_class"]
                 and r["grain"] == f["grain"]
                 and (f["identity"] is None
                      or _fold(r["identity"]) == _fold(f["identity"]))]
        if f["identity"] is None and exp.get("duplicate_members"):
            want = {_fold(x) for x in exp["duplicate_members"]}
            found = [r for r in found
                     if want <= {_fold(m.get("name", ""))
                                 for m in json.loads(r["members"])}]
        if not found:
            fails.append(f"expected flag missing: {f}")
            continue
        r = found[0]
        if r["severity"] != f["severity"]:
            fails.append(f"{f['identity'] or 'duplicate'}: severity "
                         f"{r['severity']} != expected {f['severity']}")
        if f.get("distinct_logics") is not None \
                and r["distinct_logics"] != f["distinct_logics"]:
            fails.append(f"{f['identity'] or 'duplicate'}: "
                         f"distinct_logics {r['distinct_logics']} != "
                         f"expected {f['distinct_logics']}")
        # ADR 0057 migration gate: the verdict must exist as a
        # reified cluster NODE with its logic_group structure and
        # membership edges — the graph is the sole flag truth
        cid = r["flag_id"]
        node_ids = {str(n["node_id"]) for n in run.build.nodes_rows}
        if cid not in node_ids:
            fails.append(f"{cid}: flag has NO cluster node — the "
                         "graph is not carrying the verdict")
        else:
            groups = [e for e in run.build.edges_rows
                      if e["edge_type"] == "member_of"
                      and e["target_id"] == cid]
            if len(groups) != r["distinct_logics"]:
                fails.append(
                    f"{cid}: {len(groups)} logic_group edge(s) != "
                    f"{r['distinct_logics']} distinct logics")
            member_edges = [
                e for e in run.build.edges_rows
                if e["edge_type"] == "member_of"
                and e["target_id"] in {g["source_id"] for g in groups}]
            if len(member_edges) != r["member_count"]:
                fails.append(
                    f"{cid}: {len(member_edges)} member edge(s) != "
                    f"{r['member_count']} members")

    for identity in exp.get("absent_flag_identities", []):
        hit = [r for r in flags
               if _fold(r["identity"]) == _fold(identity)
               and r["flag_class"] != "cousin_conflict"]
        if hit:
            fails.append(f"control violated: {identity!r} is flagged "
                         f"({hit[0]['flag_class']})")

    for e in exp.get("edges", []):
        target = "tech:" + e["column"].split("TECH:", 1)[-1]
        hit = [x for x in edges
               if x["edge_type"] == "transform_to_column"
               and x["source_id"] == e["step"]
               and x["target_id"].upper() == target.upper()]
        if not hit:
            fails.append(f"expected projection edge missing: "
                         f"{e['step']} -> {e['column']}")
        if e.get("via_step") and \
                run.build.projection_minted_via_step < 1:
            fails.append("via_step expected but the chase minted 0")

    for e in exp.get("absent_edges", []):
        hit = [x for x in edges
               if x["edge_type"] == "transform_to_column"
               and x["source_id"] == e["step"]
               and x["target_id"].upper().endswith(
                   e["column_suffix"].upper())]
        if hit:
            fails.append(f"edge must NOT exist (ambiguous ref): "
                         f"{e['step']} -> …{e['column_suffix']}")

    for bucket, minimum in (exp.get("drop_min") or {}).items():
        got = run.build.projection_dropped.get(bucket, 0)
        if got < minimum:
            fails.append(f"drop bucket {bucket!r}: {got} < {minimum}")

    for pair in exp.get("t2t_edges", []):
        hit = [x for x in edges
               if x["edge_type"] == "transform_to_transform"
               and x["source_id"] == pair[0]
               and x["target_id"] == pair[1]]
        if not hit:
            fails.append(f"expected step chain edge missing: "
                         f"{pair[0]} -> {pair[1]}")

    node_ids = {str(n["node_id"]) for n in run.build.nodes_rows}
    for sid in exp.get("steps_present", []):
        if sid not in node_ids:
            fails.append(f"expected step node missing: {sid}")
    for mid_ in exp.get("metrics_present", []):
        if f"canonical:{mid_}" not in node_ids:
            fails.append(f"expected metric node missing: {mid_}")

    if exp.get("handled_exception"):
        mid_ = exp["handled_exception"]
        pr = next((p for p in run.parse_rows
                   if p["metric_id"] == mid_), None)
        category = next((c for m, c in run.parse_failures
                         if m == mid_), None)
        if category is not None:
            # a classified parse error IS a declared path (the 200
            # error classifier + ops_parse_errors contract)
            if category.startswith("UNCLASSIFIED"):
                fails.append(f"{mid_}: parse error escaped the "
                             f"classifier ({category}) — undeclared")
        elif pr is not None and not (
                pr.get("extraction_suppressed")
                or int(pr.get("cte_count") or 0) == 0):
            fails.append(f"{mid_}: dynamic SQL neither suppressed, "
                         "step-free, nor classified — undeclared "
                         "handling")

    if exp.get("phi_redaction_step"):
        from src.phi_scan import scan_sql
        sid = exp["phi_redaction_step"]
        want_step = _fold(sid.rsplit(":", 1)[-1])
        hits = []
        for d in run.build.decision_rows:
            if _fold(str(d.get("step_name") or "")) != want_step:
                continue
            findings = scan_sql(str(d.get("metric_id") or ""),
                                str(d.get("expression_sql") or ""))
            hits.extend(f for f in findings
                        if f.disposition == "redact")
        if not hits:
            fails.append(f"PHI literal in {sid} produced no redact "
                         "finding — the read-time gate would not fire")

    if exp.get("compare"):
        c = exp["compare"]
        ka = _metric_keys(run, c["a"])
        kb = _metric_keys(run, c["b"])
        actual = "IDENTICAL" if (ka and ka == kb) else "DIFFERS"
        if actual != c["verdict"]:
            fails.append(f"compare {c['a']} vs {c['b']}: {actual} != "
                         f"expected {c['verdict']}")

    if exp.get("shared_step_core"):
        # Extension (derive): the named step's content key must match
        # across the pair — reuse INSIDE divergence
        sc = exp["shared_step_core"]
        keys = set()
        for mid_ in sc["metrics"]:
            key = _step_key(run, mid_, sc["name"])
            if key is None:
                fails.append(f"shared core: {mid_} has no step "
                             f"{sc['name']!r} with a fragment")
            else:
                keys.add(key)
        if len(keys) > 1:
            fails.append(f"shared core {sc['name']!r}: content keys "
                         "diverge — the extension lost its base")

    if exp.get("diff_pinpoints"):
        # Codeset drift (repair): the diff between the two metrics'
        # logic must contain the drifted token — in exactly one side
        dp = exp["diff_pinpoints"]
        frags = [_metric_fragments(run, m) for m in dp["metrics"]]
        holds = [dp["token"] in f for f in frags]
        if sum(holds) != 1:
            fails.append(
                f"drift token {dp['token']!r} in {sum(holds)} of "
                f"{len(frags)} members — the diff cannot pinpoint it")

    outcome = exp.get("canonical_outcome")
    if outcome:
        # the canonical tie-in: validate the outcome's structural
        # signature where the cell carries one (annotation otherwise)
        if outcome == "consolidate" and not any(
                f["flag_class"] == "duplicate"
                for f in exp.get("flags", [])):
            fails.append("consolidate outcome without a duplicate "
                         "flag expectation")
        if outcome == "link" and not any(
                f["flag_class"] == "cousin_conflict"
                for f in exp.get("flags", [])):
            fails.append("link outcome without a cousin expectation")
        if outcome == "repair" and not exp.get("diff_pinpoints"):
            fails.append("repair outcome without a pinpointing diff")
        if outcome == "derive" and not exp.get("shared_step_core"):
            fails.append("derive outcome without a shared step core")

    return CellResult(cell["cell_id"], "instantiated", not fails,
                      details=fails)


def check_all(run: CorpusRun) -> "list[CellResult]":
    return [check_cell(c, run) for c in run.manifest["cells"]]
