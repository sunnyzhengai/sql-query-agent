"""Relatedness — family computation over the parsed estate.

Families are connected components over shared resolved KG1 table
targets; ids are CONTENT-KEYED (deterministic hash of the sorted
member set — same estate, same ids, replayable per M5). Membership is
never stored: this lens recomputes (KG4's founding rule); minting and
drift comparison arrive with their deferred lenses.
"""
import hashlib
from typing import Any, Dict, Set


def _tables_by_file(read) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}

    def walk(node, acc):
        if isinstance(node, dict):
            rt = node.get("resolves_to")
            if isinstance(rt, str) and rt.count("|") == 2:
                acc.add(rt)
            elif isinstance(rt, str) and rt.count("|") == 3:
                acc.add(rt.rsplit("|", 1)[0])
            for v in node.values():
                walk(v, acc)
        elif isinstance(node, list):
            for v in node:
                walk(v, acc)
    for tree in read.trees().values():
        acc: Set[str] = set()
        walk(tree["statements"], acc)
        out[tree["name"]] = acc
    return out


def lens_relatedness(read, params) -> Dict[str, Any]:
    by_file = _tables_by_file(read)
    files = sorted(by_file)
    parent = {f: f for f in files}

    def find(f):
        while parent[f] != f:
            f = parent[f]
        return f
    for i, a in enumerate(files):
        for b in files[i + 1:]:
            if by_file[a] & by_file[b]:
                parent[find(b)] = find(a)
    members: Dict[str, list] = {}
    for f in files:
        members.setdefault(find(f), []).append(f)
    out = {}
    for group in members.values():
        key = hashlib.sha1("|".join(sorted(group)).encode()).hexdigest()[:12]
        out[f"fam:{key}"] = sorted(group)
    return {"yield": out, "completeness": "total over parsed estate",
            "stamp": read.stamp()}
