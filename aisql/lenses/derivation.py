"""The spine's derived states — arithmetic over version chains and
dispositions. No stored field exists to disagree with any of these
(the ledger law, CHECK-KG3-1): every layer-3 version is its own node;
these lenses derive what other systems store.

The A6 model (ruled 2026-09-05), verbatim as code:
  current(A) := max(versions(A))                 if ownership = machine
                max({v : human_authored(v) or accepted(v)})   otherwise
ownership is one-way by construction: human iff any human-authored
version OR an accepting disposition (F5's certification-without-edit
branch). Disagreement: distinct rulers' latest rulings conflict ->
a named state, no winner.
"""
from typing import Any, Dict, List

# literal: schema-mirror kg3_artifacts.Classes
STATE_CLASSES = ("description", "term", "responsibility")


def _artifacts(read) -> Dict[str, List]:
    out: Dict[str, List] = {}
    for kind in STATE_CLASSES:
        for node in read.nodes(kind):
            key = node.properties.get("artifact_id", node.identity)
            out.setdefault(key, []).append(node)
    return out


def _dispositions_about(read, artifact_id, version_ids):
    targets = {artifact_id} | set(version_ids)
    return [d for d in read.nodes("disposition")
            if d.properties["about"] in targets]


def _is_machine(node) -> bool:
    return str(node.properties.get("author", "")).startswith("agent:")


def _ownership(read, artifact_id, versions) -> str:
    if any(not _is_machine(v) for v in versions):
        return "human"
    rulings = _dispositions_about(read, artifact_id,
                                  [v.identity for v in versions])
    if any(d.properties["ruling"] == "accept" for d in rulings):
        return "human"  # certification without edit still flips (F5)
    return "machine"


def lens_ownership(read, params) -> Dict[str, Any]:
    out = {aid: _ownership(read, aid, versions)
           for aid, versions in _artifacts(read).items()}
    # literal: shape
    return {"yield": out, "completeness": "total over artifacts",
            "stamp": read.stamp()}


def lens_authorship(read, params) -> Dict[str, Any]:
    out = {}
    for aid, versions in _artifacts(read).items():
        for v in versions:
            key = aid if len(versions) == 1 else v.identity
            out[key] = "machine" if _is_machine(v) else "human"
    # literal: shape
    return {"yield": out, "completeness": "total over versions",
            "stamp": read.stamp()}


def lens_version(read, params) -> Dict[str, Any]:
    out = {aid: len(versions) for aid, versions in _artifacts(read).items()}
    # literal: shape
    return {"yield": out, "completeness": "total over artifacts (chain "
            "depth, derived)", "stamp": read.stamp()}


def lens_standing(read, params) -> Dict[str, Any]:
    out = {}
    for aid, versions in _artifacts(read).items():
        rulings = _dispositions_about(read, aid,
                                      [v.identity for v in versions])
        if not rulings:
            out[aid] = "pending"
            continue
        latest_by_author: Dict[str, str] = {}
        for d in rulings:  # store order = ruling order
            latest_by_author[d.properties["author"]] = d.properties["ruling"]
        distinct = set(latest_by_author.values())
        if len(distinct) > 1:
            named = ", ".join(f"{a}: {r}" for a, r in
                              sorted(latest_by_author.items()))
            out[aid] = f"disagreement ({named}) — no winner; humans talk"
        else:
            ruling = rulings[-1].properties["ruling"]
            # literal: schema-mirror kg3_artifacts.Classes ruling words
            out[aid] = {"accept": "accepted", "reject": "rejected",
                        "revoke": "revoked"}.get(ruling, "pending")
    # literal: shape
    return {"yield": out, "completeness": "total over artifacts",
            "stamp": read.stamp()}


def lens_current(read, params) -> Dict[str, Any]:
    """A6, verbatim. Non-empty by construction: human ownership derives
    from such a version existing."""
    out = {}
    for aid, versions in _artifacts(read).items():
        if _ownership(read, aid, versions) == "machine":
            chosen = versions[-1]
        else:
            accepted_ids = set()
            for d in _dispositions_about(read, aid,
                                         [v.identity for v in versions]):
                if d.properties["ruling"] == "accept":
                    accepted_ids.add(d.properties.get("accepted_version"))
                    accepted_ids.add(d.properties["about"])
            candidates = [v for v in versions
                          if not _is_machine(v)
                          or v.identity in accepted_ids]
            chosen = candidates[-1]
        out[aid] = {"version_id": chosen.identity, **chosen.properties}
    # literal: shape
    return {"yield": out, "completeness": "total over artifacts",
            "stamp": read.stamp()}


def lens_current_outcome(read, params) -> Dict[str, Any]:
    out: Dict[str, str] = {}
    for p in read.nodes("proposal"):
        if p.properties.get("kind") == "observed":
            out[p.properties["about"]] = p.properties["outcome"]
    # literal: shape
    return {"yield": out, "completeness": "total over observations",
            "stamp": read.stamp()}


def lens_staleness(read, params) -> Dict[str, Any]:
    """PROD-2: the worklist IS this lens's output — every named scope
    lacking a description artifact about it."""
    described = set()
    for d in read.nodes("description"):
        described.update(d.properties.get("about", []))
    stale = [n.identity for n in read.nodes("scope")
             if n.identity not in described]
    # literal: shape
    return {"yield": sorted(stale),
            "completeness": "total over named scopes",
            "stamp": read.stamp()}
