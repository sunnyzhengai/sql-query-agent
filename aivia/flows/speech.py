"""SPEECH (ADR 0080, census 2) — every node speaks its DECLARED
stored property; the ask index is a VERBATIM projection of speech.

This module is a READING under the center law: it renders stored
facts through the ratified grammar and composes NOTHING of its own —
`speak()` recomputes any entry's words from the store, and the
verbatim census (`entries()[i]["words"] == speak(entries()[i])`) is
what makes an authoring reading a CI failure instead of a live find.
The Speech_Sources registry sheet is the closed assignment: a kind
without a row fails the census at birth.
"""
from typing import Any, Dict, List

from aivia.flows import produce
from aivia.graph import metamodel
from aivia.lenses import ask_index, decisions
from aivia.lenses.ask_index import _fold, _words

DRIFT_SENTENCE = ("read by the estate's sql but declared by no "
                  "dictionary and no catalog — reader/writer drift, "
                  "counted forever")

# entry kind -> Speech_Sources sheet kind (the closed assignment)
SHEET_KINDS = {
    "table": "table", "column": "column",
    "scope": "scope (selection)", "file": "file",
    "condition": "condition (predicate)", "parameter": "parameter",
    "derived column": "derived column", "term": "term (KG3)",
    "drift": "drift name", "label": "kind (node type)",
    "PBI Report": "PBI Report",
}


def sources() -> Dict[str, str]:
    """Kind -> declared speech source, from the registry."""
    sheet = metamodel.load("lenses").sheets["Speech_Sources"]
    return {r["Label"]: r["Speech"] for r in sheet
            if r["Label"] != "_ruling"}


def _tree_and_scope(read, scope_key: str):
    for tree in read.trees().values():
        for scope in decisions.named_scopes(tree):
            if scope["name_key"] == scope_key:
                return tree, scope
    return None, None


def _condition_phrase(read, tree, scope, i: int) -> str:
    preds = [p for p in decisions.membership_predicates(scope)
             if not decisions.is_degenerate(p)]
    if i >= len(preds):
        return ""
    voice = produce._Voice(read, tree)
    return (produce._voice_predicate(preds[i], voice) or "").lower()


def _file_speech(read, identity: str) -> str:
    """Delivery lead (grammar render) + the twin's STORED subject —
    the composed meaning the translator built (center-law corollary;
    the cause-1 corpse dies here)."""
    lead = produce.file_words(read, identity)
    subject = ""
    for n in read.nodes("meaning_twin"):
        twin = n.properties.get("twin", {})
        key = n.identity.removeprefix("twin::")
        if key == identity or twin.get("file") == identity \
                or identity.endswith(twin.get("file") or "\x00"):
            subject = twin.get("subject", "")
            break
    return f"{lead} {subject}".strip().lower()


def speak(read, entry: Dict[str, Any]) -> str:
    """Recompute an entry's speech from the store — the verbatim
    census contract. Total over SHEET_KINDS."""
    kind, identity = entry["label"], entry["identity"]
    if kind in ("table", "column"):
        node = next(n for n in read.nodes(kind)
                    if n.identity == identity)
        return (node.properties.get("description") or "").lower()
    if kind == "scope":
        tree, scope = _tree_and_scope(read, identity)
        if scope is None:
            return ""
        return produce._scope_lead(read, tree, scope).lower()
    if kind == "file":
        return _file_speech(read, identity)
    if kind == "condition":
        scope_key, tag = identity.rsplit("::c", 1)
        tree, scope = _tree_and_scope(read, scope_key)
        if scope is None:
            return ""
        return _condition_phrase(read, tree, scope, int(tag))
    if kind == "parameter":
        return f"parameter {_words(entry['name'])} of " \
               f"{_words(entry['owner'].rsplit('/', 1)[-1])}"
    if kind == "derived column":
        # the entry's own name never rides in speech (one evidence,
        # one card — the name card owns it; total-score law)
        scope_key = identity.rsplit(".", 1)[0]
        return (f"a computed output of the "
                f"{_words(scope_key.split('::')[-1])} selection")
    if kind == "PBI Report":
        node = next(n for n in read.nodes("PBI Report")
                    if n.identity == identity)
        desc = (node.properties.get("description") or "").lower()
        disp = node.properties.get("displays") or []
        return (desc + (" displays: " + ", ".join(
            _words(d) for d in disp) if disp else "")).strip()
    if kind == "term":
        node = next(n for n in read.nodes("term")
                    if n.identity == identity)
        return (node.properties.get("definition") or "").lower()
    if kind == "drift":
        return DRIFT_SENTENCE
    return ""


def entries(read) -> List[Dict[str, Any]]:
    """The full ask index — census 3's searchable surface: the name
    lens's entries with their words REPLACED by declared speech,
    plus the node kinds the lens never carried (conditions,
    parameters, kinds themselves), each with its OWNER chain."""
    out = ask_index.lens_ask_index(read, None)["yield"]
    scope_owner: Dict[str, str] = {}
    for key, tree in sorted(read.trees().items()):
        for scope in decisions.named_scopes(tree):
            scope_owner[scope["name_key"]] = key
    for e in out:
        if e["label"] == "scope":
            e["owner"] = scope_owner.get(e["identity"])
        elif e["label"] == "derived column":
            e["owner"] = e["identity"].rsplit(".", 1)[0]
        elif e["label"] == "drift":
            e["owner"] = e["identity"].split("::")[0]
        e["words"] = speak(read, e)

    def add(kind, identity, name, owner):
        entry = {"label": kind, "identity": identity, "name": name,
                 "folded": _fold(name), "owner": owner, "words": ""}
        entry["words"] = speak(read, entry)
        out.append(entry)

    for key, tree in sorted(read.trees().items()):
        for scope in decisions.named_scopes(tree):
            preds = [p for p in
                     decisions.membership_predicates(scope)
                     if not decisions.is_degenerate(p)]
            for i in range(len(preds)):
                add("condition", f"{scope['name_key']}::c{i}",
                    f"condition {i + 1} of "
                    f"{scope['name_key'].split('::')[-1]}",
                    scope["name_key"])
        for p in tree.get("parameters", []):
            add("parameter", f"{key}::param/{p['name']}",
                p["name"], key)
    # THE TOTAL-SCORE LAW (2026-09-08): label:: group entries died —
    # the label is a CARD on every member (grounding.cards)
    return [e for e in out if e["words"] or e["label"] not in
            ("condition",)]  # empty conditions never index
