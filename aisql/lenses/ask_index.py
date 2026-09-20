"""The ask index — the console's entity READING (ADR 0078): every
askable thing under its names — KG1 tables/columns, named scopes and
files, KG3 terms, minted concepts (via their accepted terms), and
UNRESOLVED NAMES (the search law: a drift column is findable, never
silent). Derived, versioned, writes nothing.
"""
import re
from typing import Any, Dict, List


def _fold(name: str) -> str:
    return name.strip("[]\"'").upper()


def _words(text: str) -> str:
    return re.sub(r"[_\W]+", " ", text or "").strip().lower()


def _tokens(text: str) -> set:
    """Word-grain tokens with CamelCase split first (ADR 0079's
    blessed mechanical transform; ADR 0080 word-grain law):
    SepsisDetails carries the sepsis token; BED_CONFIG never
    carries ed."""
    spread = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text or "")
    return set(_words(spread).split())


def lens_ask_index(read, params) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []

    def add(kind, identity, name, words=""):
        # literal: shape
        entries.append({"label": kind, "identity": identity,
                        "name": name, "folded": _fold(name),
                        "words": words})

    for n in read.nodes("table"):
        name = n.identity.rsplit("|", 1)[-1]
        add("table", n.identity, name,
            (n.properties.get("description") or "").lower())
    for n in read.nodes("column"):
        name = n.identity.rsplit("|", 1)[-1]
        add("column", n.identity, name,
            (n.properties.get("description") or "").lower())
    for key, tree in read.trees().items():
        add("file", key, tree["name"].rsplit("/", 1)[-1]
            .removesuffix(".sql"))
        for stmt in tree["statements"]:
            for s in (list(stmt.get("ctes", []))
                      + ([stmt["scope"]] if stmt.get("scope") else [])):
                if "name_key" in s:
                    # delivery scopes carry a key but no NAME (the
                    # unnamed emitters) — they are the estate's
                    # PRACTICED metrics and must be askable
                    add("scope", s["name_key"],
                        s.get("name") or s["name_key"].split("::")[-1])
        # the search law: unresolved names are findable — each is the
        # reader/writer drift finding wearing its own name
        for ref in tree.get("resolution_census", {}).get(
                "unresolved", []):
            add("drift", f"{tree['name']}::{ref}",
                ref.rsplit(".", 1)[-1])
    # THE (c) RE-HOME (Sunny's "fix (c)" 2026-09-16, closing his
    # AGE_IN_DAYS find): derived columns are the M4 STORE NODES —
    # one entry per node, the node's own name; the words become the
    # stored R12 description in speak() (the center law: the index
    # is a verbatim projection of stored speech). The old tree-grain
    # pseudo entries ({scope}.{NAME}) and their dead passthrough
    # filter retired here; renamed passthroughs are a COUNTED
    # exclusion (the derived-layer receipt splits them out).
    for n in read.nodes("derived_column"):
        add("derived_column", n.identity,
            n.properties.get("name", ""))
    for n in read.nodes("pbi_report"):
        add("pbi_report", n.identity, n.properties.get("name", ""))
    seen_terms = {}
    for n in read.nodes("term"):
        seen_terms[n.properties["artifact_id"]] = n
    for term in seen_terms.values():
        add("term", term.identity, term.properties.get("name", ""),
            (term.properties.get("definition") or "").lower())
    # literal: shape
    return {"yield": entries,
            "completeness": "total over KG1 objects, named scopes, "
                            "files, terms, and unresolved names",
            "stamp": read.stamp()}


def find(index: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
    """Deterministic entity resolution: exact folded name -> unique
    match or ambiguity; else word-containment; else nearest names.
    Never guesses: 0/1/many are three honest outcomes."""
    wanted = _fold(text.strip())
    # a fully-qualified identity always resolves uniquely — the way
    # out of an honest ambiguity ('pick one' offers these)
    by_identity = [e for e in index
                   if _fold(e["identity"]) == wanted]
    if len(by_identity) >= 1:
        return {"outcome": "matched", "entity": by_identity[0]}
    exact = [e for e in index if e["folded"] == wanted]
    if not exact and "." in wanted:  # schema-qualified lookups
        exact = [e for e in index
                 if e["folded"] == wanted.rsplit(".", 1)[-1]]
    if len(exact) == 1:
        return {"outcome": "matched", "entity": exact[0]}
    if len(exact) > 1:
        # one KIND with one identity is still unique (a column named
        # in several drift rows collapses); true cross-kind splits
        # stay ambiguous for the human
        identities = {(e["label"], e["identity"]) for e in exact}
        if len(identities) == 1:
            return {"outcome": "matched", "entity": exact[0]}
        kinds = {e["label"] for e in exact}
        if kinds == {"drift"}:
            # literal: shape
            return {"outcome": "matched", "entity": exact[0],
                    "sightings": exact}
        return {"outcome": "ambiguous", "candidates": exact[:12]}
    loose = [e for e in index
             if _words(text) and _words(text) in (e["words"] or "")]
    if len(loose) == 1:
        return {"outcome": "matched", "entity": loose[0]}
    if loose:
        return {"outcome": "ambiguous", "candidates": loose[:12]}
    near = [e for e in index
            if wanted[:4] and wanted[:4] in e["folded"]][:8]
    return {"outcome": "no-match", "nearest": near}
