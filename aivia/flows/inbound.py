"""The two inbound doors — extracts to kg1_intake, estate to the mapper.

Thin by design: validation and lifecycle live in the layers' single
writers; these flows sequence the doors and return reports. Estate
conservation (E5): acquired u counted-excluded = every file in scope —
an unsupported dialect lands as a counted exclusion, never parsed,
never silent.
"""
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from aivia.graph import kg1_intake, kg2_mapper, kg2_translator


def receive_extract(store, reg: Dict[str, Any],
                    snap: "kg1_intake.ExtractSnapshot",
                    known_packs: Set[str]) -> "kg1_intake.IntakeReport":
    kg1_intake.validate_extract(reg, snap, known_packs)
    return kg1_intake.apply_extract(store, reg, snap)


def render_intake_report(reg: Dict[str, Any], extract_reports,
                         estate_report, read) -> str:
    """The DBA-facing rendering of the intake result data (SOP: what
    loaded, what was counted as missing, anything quarantined; a
    refusal would have named its rule before this ever rendered).
    DATA FIRST — every number here is recomputed from the graph and
    the reports, never hand-written."""
    lines = ["AIVIA INTAKE REPORT",
             f"Registered db: {reg['db_name']} (server {reg['server']}); "
             f"sources: {', '.join(reg['registered_sources'])}; "
             f"DBA: {reg['dba_team']}", ""]
    tables = read.nodes("table")
    columns = read.nodes("column")
    for rep in extract_reports:
        src = rep.source
        n_tables = sum(1 for t in tables if t.identity.startswith(f"{src}|"))
        n_cols = sum(1 for c in columns if c.identity.startswith(f"{src}|"))
        lines.append(f"[extract: {src}] loaded {n_tables} tables, "
                     f"{n_cols} columns; checks: "
                     f"{rep.check_outcomes.get('INTAKE-0..10', '?')}")
        grain_gap = rep.gap_lists.get("grain_not_declared", [])
        lines.append(f"  counted missing: {len(grain_gap)} table(s) with "
                     "no declared grain"
                     + (f" ({', '.join(grain_gap)})" if grain_gap else ""))
        for alert in rep.dba_alerts:
            lines.append(f"  QUARANTINED (needs your confirmation): {alert}")
        for decl in rep.illegal_declarations:
            lines.append(f"  refused declaration: {decl}")
        for pend in rep.pending_references:
            lines.append(f"  pending reference: {pend}")
    lines.append("")
    lines.append(f"[estate] acquired {len(estate_report.acquired)} file(s): "
                 f"{', '.join(sorted(estate_report.acquired))}")
    for exc in estate_report.counted_excluded:
        lines.append(f"  excluded (counted): {exc['file']} — {exc['reason']}")
    unresolved = [(t['name'], r)
                  for t in estate_report.trees.values()
                  for r in t['resolution_census']['unresolved']]
    for fname, ref in unresolved:
        lines.append(f"  unresolved reference: {ref} in {fname} — not in "
                     "the dictionary (counted, never guessed)")
    return "\n".join(lines)


def write_intake_result_tables(out_dir, reg, extract_reports,
                               estate_report, read) -> List[str]:
    """Contract §8: the intake report is DATA FIRST — result tables
    beside the graph, from which renderings derive. One row per
    distinct finding (a DBA troubleshoots a list, not prose): CSVs
    always; an .xlsx workbook of the same sheets when openpyxl is
    present. Returns the files written."""
    import csv as _csv
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dict_tables = {}
    for t in read.nodes("table"):
        source, schema, table = t.identity.split("|")
        dict_tables.setdefault(table.upper(), []).append(schema)

    sheets: Dict[str, List[List[str]]] = {}
    sheets["summary"] = [["item", "value"]]
    for rep in extract_reports:
        sheets["summary"] += [
            [f"{rep.source}: checks", rep.check_outcomes.get(
                "INTAKE-0..10", "?")],
            [f"{rep.source}: quarantined join groups",
             str(len(rep.quarantined_join_groups))],
            [f"{rep.source}: refused declarations",
             str(len(rep.illegal_declarations))],
            [f"{rep.source}: pending references",
             str(len(rep.pending_references))]]
    sheets["summary"] += [
        ["estate: files acquired", str(len(estate_report.acquired))],
        ["estate: files excluded (counted)",
         str(len(estate_report.counted_excluded))]]

    # The COVERAGE CHECK — every customer needs this: their SQL scanned
    # against their delivered dictionary; what falls through names the
    # next metadata to load, or a drift they are not aware of.
    unresolved: Dict[str, Dict[str, Any]] = {}
    for fname, tree in estate_report.trees.items():
        for detail in tree["resolution_census"].get(
                "unresolved_detail", []):
            row = unresolved.setdefault(
                detail["ref"], {"n": 0, "files": set(), **detail})
            row["n"] += 1
            row["files"].add(fname)
    sources_to_load: Dict[str, Dict[str, Any]] = {}
    sheets["unresolved_references"] = [
        # literal: frame
        ["reference", "kind", "occurrences", "diagnosis", "files"]]
    for ref in sorted(unresolved, key=lambda r: -unresolved[r]["n"]):
        row = unresolved[ref]
        bare = ref.split(".")[-1].upper()
        if row["kind"] == "table" and bare in dict_tables:
            diagnosis = ("SCHEMA MISMATCH — table exists in the "
                         "dictionary under schema "
                         f"'{'/'.join(dict_tables[bare])}'; the SQL "
                         "qualifies it differently")
        elif row["kind"] == "table":
            schema = row.get("schema", "(unqualified)")
            diagnosis = (f"TABLE NOT IN DELIVERED METADATA — schema "
                         f"'{schema}' has no registered extract "
                         "covering it; see sources_to_load")
            agg = sources_to_load.setdefault(
                schema, {"tables": set(), "refs": 0})
            agg["tables"].add(bare)
            agg["refs"] += row["n"]
        else:
            table = row.get("table", "?")
            diagnosis = (f"COLUMN NOT IN DELIVERED METADATA — table "
                         f"'{table}' is delivered but carries no such "
                         "column: dictionary metadata incomplete, OR "
                         "the SQL drifted from the source (a report "
                         "that may be failing silently)")
        sheets["unresolved_references"].append(
            [ref, row["kind"], str(row["n"]), diagnosis,
             "; ".join(sorted(row["files"]))])
    sheets["sources_to_load"] = [
        # literal: frame
        ["schema / source", "missing tables", "references",
         "recommendation"]]
    for schema in sorted(sources_to_load,
                         key=lambda s: -sources_to_load[s]["refs"]):
        agg = sources_to_load[schema]
        sheets["sources_to_load"].append(
            [schema, ", ".join(sorted(agg["tables"])), str(agg["refs"]),
             "register this schema's source and load its dictionary/"
             "catalog metadata (contract §3c: org schemas come from the "
             "database catalog when no vendor dictionary covers them)"])

    sheets["grain_gaps"] = [["table", "note"]]
    for rep in extract_reports:
        for table in rep.gap_lists.get("grain_not_declared", []):
            sheets["grain_gaps"].append(
                [table, "description carries no grain declaration"])
    sheets["quarantines_and_alerts"] = [["source", "detail"]]
    for rep in extract_reports:
        for alert in rep.dba_alerts:
            sheets["quarantines_and_alerts"].append([rep.source, alert])
        for decl in rep.illegal_declarations:
            sheets["quarantines_and_alerts"].append([rep.source, decl])
    sheets["excluded_files"] = [["file", "reason"]]
    for exc in estate_report.counted_excluded:
        sheets["excluded_files"].append([exc["file"], exc["reason"]])

    written = []
    for name, rows in sheets.items():
        path = out_dir / f"{name}.csv"
        with open(path, "w", newline="") as f:
            _csv.writer(f).writerows(rows)
        written.append(str(path))
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for name, rows in sheets.items():
            ws = wb.create_sheet(name[:31])
            for row in rows:
                ws.append(row)
            for cell in ws[1]:
                cell.font = openpyxl.styles.Font(bold=True)
        xlsx = out_dir / "intake_report.xlsx"
        wb.save(xlsx)
        written.append(str(xlsx))
    except ImportError:
        pass  # CSVs are the data of record; the workbook is a rendering
    (out_dir / "intake_report.txt").write_text(
        render_intake_report(reg, extract_reports, estate_report, read))
    written.append(str(out_dir / "intake_report.txt"))
    return written


@dataclass
class EstateReport:
    acquired: List[str] = field(default_factory=list)
    counted_excluded: List[Dict[str, str]] = field(default_factory=list)
    trees: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    twins: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    reused: List[str] = field(default_factory=list)


def receive_estate(store, reg: Dict[str, Any], estate_dir,
                   kg1_changed=None) -> EstateReport:
    estate_dir = pathlib.Path(estate_dir)
    manifest = json.loads((estate_dir / "manifest.json").read_text())
    location = manifest["location"]
    report = EstateReport()
    for path in sorted(estate_dir.rglob("*")):
        if path.is_dir() or path.name == "manifest.json":
            continue
        name = path.relative_to(estate_dir).as_posix()
        if path.suffix != ".sql":
            reason = (f"unsupported-dialect ({path.suffix.lstrip('.')} "
                      "placeholder)")
            kg2_mapper.record_exclusion(store, name, reason,
                                        manifest["as_of"])
            report.counted_excluded.append({"file": name,
                                            "reason": reason})
            continue
        try:
            tree = kg2_mapper.apply_file(
                store, reg, file_id=f"{location}{name}",
                file_name=name, text=path.read_text(),
                as_of=manifest["as_of"],
                default_schema=manifest.get("default_schema"),
                kg1_changed=kg1_changed)
        except ValueError as err:
            # conservation: a parse failure is a COUNTED exclusion with
            # the parser's own message — never fatal, never silent
            reason = f"parse-error: {err}"
            kg2_mapper.record_exclusion(store, name, reason,
                                        manifest["as_of"])
            report.counted_excluded.append({"file": name,
                                            "reason": reason})
            continue
        report.acquired.append(name)
        report.trees[name] = tree
        if tree.pop("_reused", False):
            # unchanged file, no KG1 ripple: tree AND twin stand —
            # the file quantum skips the whole chain (change quanta)
            report.reused.append(name)
            twin_node = next(
                (n for n in store.current_nodes("meaning_twin")
                 if n.identity == f"twin::{location}{name}"), None)
            if twin_node is not None:
                report.twins[name] = twin_node.properties["twin"]
                continue
        # Phase B (ADR 0077): parse and translate in the SAME RUN,
        # atomic — the twin regenerates with its tree at the file
        # quantum; the homomorphism law is asserted inside translate()
        report.twins[name] = kg2_translator.apply_twin(
            store, f"{location}{name}", tree, manifest["as_of"])
    _store_scope_descriptions(store, manifest["as_of"])
    return report


def _store_scope_descriptions(store, as_of) -> None:
    """THE SHAPE CONTRACT, M2 (Sunny's bottom-up ruling,
    2026-09-10): every scope node carries its description STORED —
    the lead render, composed from KG1 words. The verbatim law is a
    standing test: stored == recomputed (test_scope_layer)."""
    from aivia.flows import produce
    from aivia.graph.read_api import ReadApi
    from aivia.lenses import decisions
    read = ReadApi(store)
    by_id = {n.identity: n for n in read.nodes("scope")}
    for key, tree in sorted(read.trees().items()):
        for scope in decisions.named_scopes(tree):
            node = by_id.get(scope["name_key"])
            if node is None:
                continue
            lead = produce._scope_lead(read, tree, scope)
            if node.properties.get("description") == lead:
                continue
            store.append_node(
                "scope", node.identity,
                {**node.properties, "description": lead},
                as_of, node.extract_id)


def receive_pbi(store, pbi_dir) -> int:
    """THE CONSUMPTION LAYER (Sunny's ruling 2026-09-08: every proc
    feeds a PBI report; the mapping is real even where the shell is
    synthetic). Loads pbi_snapshot/reports.json as PBI Report nodes
    — label chosen to BE the words users say — with executes
    mappings; DISPLAYS are composed from the executed procs' twins
    (delivery projection members: what the report actually shows,
    derived, never invented)."""
    import json as _json
    import pathlib as _pl

    from aivia.graph.read_api import ReadApi
    pbi_dir = _pl.Path(pbi_dir)
    if not (pbi_dir / "reports.json").is_file():
        return 0
    manifest = _json.loads((pbi_dir / "manifest.json").read_text())
    rows = _json.loads((pbi_dir / "reports.json").read_text())
    read = ReadApi(store)
    trees = read.trees()
    rel_to_key = {}
    for key, tree in trees.items():
        rel_to_key[tree.get("name", key)] = key

    def displays_of(rel):
        tree = trees.get(rel_to_key.get(rel, rel))
        if not tree:
            return []
        out = []
        for stmt in tree.get("statements", []):
            if not stmt.get("emits") or not stmt.get("scope"):
                continue
            arms = stmt["scope"].get("combination_arms")
            shape = arms[0] if arms else stmt["scope"]
            for m in shape.get("projection", []):
                if m.get("name"):
                    out.append(m["name"])
        return out[:8]

    n = 0
    for row in rows:
        slug = row["name"].lower().replace(" ", "-")
        displays = []
        executes = []
        for rel in row["executes"]:
            executes.append(rel_to_key.get(rel, rel))
            displays += displays_of(rel)
        store.append_node(
            "pbi_report", f"pbi://sepsis/{slug}",
            # literal: shape
            {"name": row["name"],
             "description": row["description"],
             "displays": displays, "executes": executes,
             "source": row["source"]},
            manifest["as_of"], f"pbi@{manifest['as_of']}")
        n += 1
    return n


def receive_descriptions(store, path) -> int:
    """E1 estate-data loading: the Scribe's committed drafts
    (descriptions.json) land as kg3 description artifacts at boot —
    machine-authored, 'drafted', basis-stamped. Estate data, not a
    journal act: every boot (test or prod) speaks the same
    aboutness; blessing is a later human act in the journal."""
    import json as _json
    import pathlib as _pl

    from aivia.flows import describe as _describe
    path = _pl.Path(path)
    if not path.is_file():
        return 0
    data = _json.loads(path.read_text())
    return _describe.land(store, data["descriptions"],
                          basis=data["basis"],
                          created_at=data["created_at"])
