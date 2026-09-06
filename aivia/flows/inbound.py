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

from aivia.graph import kg1_intake, kg2_mapper


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

    unresolved: Dict[str, Dict[str, Any]] = {}
    for fname, tree in estate_report.trees.items():
        for ref in tree["resolution_census"]["unresolved"]:
            row = unresolved.setdefault(ref, {"n": 0, "files": set()})
            row["n"] += 1
            row["files"].add(fname)
    sheets["unresolved_references"] = [
        ["reference", "occurrences", "diagnosis", "files"]]
    for ref in sorted(unresolved, key=lambda r: -unresolved[r]["n"]):
        bare = ref.split(".")[-1].upper()
        if bare in dict_tables:
            diagnosis = ("SCHEMA MISMATCH — table exists in the "
                         "dictionary under schema "
                         f"'{'/'.join(dict_tables[bare])}'; the SQL "
                         "qualifies it differently")
        else:
            diagnosis = ("NOT IN DICTIONARY — not delivered by any "
                         "registered extract; likely an org-created or "
                         "out-of-scope object")
        sheets["unresolved_references"].append(
            [ref, str(unresolved[ref]["n"]), diagnosis,
             "; ".join(sorted(unresolved[ref]["files"]))])

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


def receive_estate(store, reg: Dict[str, Any], estate_dir) -> EstateReport:
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
                default_schema=manifest.get("default_schema"))
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
    return report
