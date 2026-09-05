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
    for path in sorted(estate_dir.iterdir()):
        if path.name == "manifest.json":
            continue
        if path.suffix != ".sql":
            report.counted_excluded.append({
                "file": path.name,
                "reason": f"unsupported-dialect ({path.suffix.lstrip('.')} "
                          "placeholder)"})
            continue
        tree = kg2_mapper.apply_file(
            store, reg, file_id=f"{location}{path.name}",
            file_name=path.name, text=path.read_text(),
            as_of=manifest["as_of"])
        report.acquired.append(path.name)
        report.trees[path.name] = tree
    return report
