"""The spine's derived states — small arithmetic over chains and
dispositions. No stored field exists to disagree with any of these
(the ledger law): ownership, authorship, version, standing and
current-outcome DERIVE; staleness derives the produce worklist.

Until slice 4 lands the artifact layer these run total over an empty
class set — a lens is total over its domain, and an empty domain is a
domain (B3: the completeness declaration says so out loud).
"""
from typing import Any, Dict

ARTIFACT_CLASSES = ("description", "term", "responsibility")
EVENT_CLASSES = ("disposition", "usage", "proposal")


def _artifact_versions(read, kind):
    return [n for n in read.nodes(kind)]


def lens_ownership(read, params) -> Dict[str, Any]:
    out = {}
    for kind in ARTIFACT_CLASSES:
        for node in _artifact_versions(read, kind):
            author = node.properties.get("author", "")
            out[node.identity] = ("human" if not str(author).startswith(
                "agent") else "machine")
    return {"yield": out,
            "completeness": "total over artifact classes",
            "stamp": read.stamp()}


def lens_authorship(read, params) -> Dict[str, Any]:
    out = {}
    for kind in ARTIFACT_CLASSES + EVENT_CLASSES:
        for node in _artifact_versions(read, kind):
            author = str(node.properties.get("author", ""))
            out[node.identity] = ("machine" if author.startswith("agent")
                                 else "human")
    return {"yield": out, "completeness": "total over versions",
            "stamp": read.stamp()}


def lens_version(read, params) -> Dict[str, Any]:
    out = {}
    for kind in ARTIFACT_CLASSES:
        for node in read.nodes(kind):
            versions, _ = read.read(node.identity, mode="all")
            out[node.identity] = len(versions)  # chain depth, derived
    return {"yield": out, "completeness": "total over versions",
            "stamp": read.stamp()}


def lens_standing(read, params) -> Dict[str, Any]:
    dispositions = read.nodes("disposition")
    by_target: Dict[str, str] = {}
    for d in dispositions:
        by_target[d.properties["about"]] = d.properties["ruling"]
    out = {}
    for kind in ARTIFACT_CLASSES:
        for node in read.nodes(kind):
            ruling = by_target.get(node.identity)
            out[node.identity] = {"accept": "accepted",
                                  "reject": "rejected",
                                  "revoke": "revoked"}.get(ruling, "pending")
    return {"yield": out, "completeness": "total over artifacts",
            "stamp": read.stamp()}


def lens_current_outcome(read, params) -> Dict[str, Any]:
    out: Dict[str, str] = {}
    for p in read.nodes("proposal"):
        if p.properties.get("kind") == "observed":
            out[p.properties["about"]] = p.properties["outcome"]
    return {"yield": out, "completeness": "total over observations",
            "stamp": read.stamp()}


def lens_staleness(read, params) -> Dict[str, Any]:
    """PROD-2: the worklist IS this lens's output — every named scope
    lacking a CURRENT description artifact about it."""
    described = set()
    for d in read.nodes("description"):
        described.add(d.properties.get("about"))
    stale = [n.identity for n in read.nodes("scope")
             if n.identity not in described]
    return {"yield": sorted(stale),
            "completeness": "total over named scopes",
            "stamp": read.stamp()}
