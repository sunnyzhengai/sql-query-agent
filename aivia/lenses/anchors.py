"""The anchor census — the S1/S2 corollaries as a READING (twin-graph
ruling 2f, Phase D): after any rebuild, every anchored description is
INTACT (same content_key — survives silently, zero steward touches),
a DRIFT ORPHAN (the scope's meaning changed — flagged for re-review,
never silently carried onto changed logic), or a DELETED ORPHAN (the
scope is gone — surfaced with similarity candidates found by MEANING:
a renamed scope with the same content_key is the top candidate).
Re-attachment stays a human act. Derived, writes nothing.
"""
from typing import Any, Dict


def selection_keys(read) -> Dict[str, str]:
    """name_key -> the selection/combination node's content_key, from
    the stored twins (first occurrence wins on dupes — the #i retire
    branch keeps dupes rare and counted)."""
    keys: Dict[str, str] = {}
    for n in read.nodes("meaning_twin"):
        twin = n.properties["twin"]
        for node in twin["nodes"]:
            nk = node.get("content", {}).get("name_key")
            if nk and nk not in keys:
                keys[nk] = node["content_key"]
    return keys


def lens_anchor_census(read, params) -> Dict[str, Any]:
    current = selection_keys(read)
    by_key: Dict[str, list] = {}
    for nk, key in current.items():
        by_key.setdefault(key, []).append(nk)
    latest: Dict[str, Any] = {}
    for v in read.nodes("description"):
        latest[v.properties["artifact_id"]] = v
    intact, drift, deleted, unanchored = [], [], [], []
    for artifact_id, v in sorted(latest.items()):
        anchor = v.properties.get("anchor")
        if not anchor:
            unanchored.append(artifact_id)
            continue
        scope, key = anchor["scope"], anchor["content_key"]
        if scope in current:
            (intact if current[scope] == key else drift).append(scope)
        else:
            deleted.append(
                {"scope": scope,
                 "candidates": by_key.get(key, [])})  # same MEANING,
            # new name — the rename case resolves itself for the human
    # literal: shape
    # literal: shape
    return {"yield": {"intact": intact, "drift_orphans": drift,
                      "deleted_orphans": deleted,
                      "unanchored": unanchored},
            "completeness": "total over current descriptions",
            "stamp": read.stamp()}
