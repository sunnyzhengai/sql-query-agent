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
