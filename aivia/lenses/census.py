"""Estate-shape accounting — the honesty counters.

working_set: the two-denominator coverage metric's numerator.
gap_census: one lens, every counted absence.
referenced_keys: D12 ruling — derived from inbound joins_to groups,
never stored; yields DISTINCT column-sets, not one row per FK.
"""
from typing import Any, Dict, Set


def _touched_tables(read) -> Set[str]:
    touched = set()

    def walk(node):
        if isinstance(node, dict):
            rt = node.get("resolves_to")
            if isinstance(rt, str) and not rt.startswith("SAME-TREE") \
                    and not rt.startswith("file parameter"):
                if rt.count("|") == 2:
                    touched.add(rt)
                elif rt.count("|") == 3:
                    touched.add(rt.rsplit("|", 1)[0])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    for tree in read.trees().values():
        walk(tree["statements"])
    return touched


def lens_working_set(read, params) -> Dict[str, Any]:
    touched = _touched_tables(read)
    all_tables = {n.identity for n in read.nodes("table")}
    return {"yield": sorted(touched),
            "not_touched": sorted(all_tables - touched),
            "completeness": "total over resolved refs",
            "stamp": read.stamp()}


def lens_gap_census(read, params) -> Dict[str, Any]:
    unresolved = []
    unmapped = 0
    for tree in read.trees().values():
        for ref in tree["resolution_census"]["unresolved"]:
            unresolved.append({"file": tree["name"], "ref": ref})
        unmapped += len(tree["remainder"])
    grain_gap = sum(1 for n in read.nodes("table")
                    if n.properties.get("grain") is None)
    keyless = sum(1 for n in read.nodes("table")
                  if not n.properties.get("pk_columns"))
    excluded = sorted(n.identity for n in read.nodes("excluded_file"))
    return {"unresolved_refs": unresolved,
            "grain_not_declared": grain_gap,
            "keyless_tables": keyless,
            "unmapped_remainder": unmapped,
            "unsupported_dialect_files": excluded,
            "completeness": "total", "stamp": read.stamp()}


def lens_referenced_keys(read, params) -> Dict[str, Any]:
    keys: Dict[str, Set[tuple]] = {}
    for e in read.edges("joins_to"):
        dest_cols = tuple(pair[1] for pair in e.properties["on"])
        keys.setdefault(e.to_id, set()).add(dest_cols)
    return {"yield": {t: sorted(v) for t, v in sorted(keys.items())},
            "completeness": "total over referenced tables",
            "stamp": read.stamp()}
