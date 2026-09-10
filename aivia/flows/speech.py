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
from aivia.lenses.ask_index import _fold, _tokens, _words


def drift_sentence() -> str:
    """The literal law (E3): the drift speech is REGISTRY text
    (Speech_Sources drift row) — claim words never live in code."""
    from aivia.graph import metamodel
    row = next(r for r in metamodel.load("lenses")
               .sheets["Speech_Sources"]
               if r["Label"] == "drift name")
    return row["Text"]

# entry kind -> Speech_Sources sheet kind (the closed assignment)
# literal: shape
SHEET_KINDS = {
    "table": "table", "column": "column",
    "scope": "scope (selection)", "file": "file",
    "condition": "condition (predicate)", "param": "parameter",
    "derived_column": "derived_column", "term": "term (KG3)",
    "drift": "drift name", "label": "kind (node type)",
    "pbi_report": "pbi_report",
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


def _file_voicing(read, identity: str) -> str:
    """Delivery lead (grammar render) + the twin's STORED subject —
    the node's structural ANATOMY. Since the speech contract
    (2026-09-09) this is EVIDENCE for the Scribe and display text,
    NEVER the search speech: a 4,600-char recitation of upstream
    catalog text embeds as being about nothing (the ED-file
    corpse)."""
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


def _aboutness(read, identity: str) -> str:
    """The node's own description artifact (kg3), when one exists —
    THE speech under the contract."""
    for n in read.nodes("description"):
        if identity in (n.properties.get("about") or []):
            return (n.properties.get("description") or "").strip().lower()
    return ""


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
        # THE SPEECH CONTRACT: a file speaks its OWN aboutness (the
        # Scribe-drafted description) or NOTHING — a counted gap,
        # never the structural wall (that stays as _file_voicing
        # for display/evidence)
        return _aboutness(read, identity)
    if kind == "condition":
        scope_key, tag = identity.rsplit("::c", 1)
        tree, scope = _tree_and_scope(read, scope_key)
        if scope is None:
            return ""
        return _condition_phrase(read, tree, scope, int(tag))
    if kind == "param":
        return f"parameter {_words(entry['name'])} of " \
               f"{_words(entry['owner'].rsplit('/', 1)[-1])}"
    if kind == "derived_column":
        # the entry's own name never rides in speech (one evidence,
        # one card — the name card owns it; total-score law)
        scope_key = identity.rsplit(".", 1)[0]
        return (f"a computed output of the "
                f"{_words(scope_key.split('::')[-1])} selection")
    if kind == "pbi_report":
        node = next(n for n in read.nodes("pbi_report")
                    if n.identity == identity)
        # THE DERIVATION RULING (Sunny, 2026-09-09: "the report
        # users SHOULD see the logic"): a report's aboutness IS its
        # executed procs' descriptions, through the executes edge —
        # 1:1 = the same words; the (single) multi-proc report
        # composes both. Shell description only when no proc
        # speaks; displays are the node's own parts and stay
        parts = []
        for ex in (node.properties.get("executes") or []):
            about = _aboutness(read, ex)
            if about and about not in parts:
                parts.append(about)
        desc = " ".join(parts) \
            or (node.properties.get("description") or "").lower()
        disp = node.properties.get("displays") or []
        return (desc + (" displays: " + ", ".join(
            _words(d) for d in disp) if disp else "")).strip()
    if kind == "term":
        node = next(n for n in read.nodes("term")
                    if n.identity == identity)
        return (node.properties.get("definition") or "").lower()
    if kind == "drift":
        return drift_sentence()
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
    acr = {n.properties["name"].lower():
           " ".join(n.properties["expansions"])
           for n in read.nodes("acronym")}
    for e in out:
        if acr:
            toks = _tokens(e["name"])
            exps = [acr[t] for t in sorted(toks) if t in acr]
            if exps:
                e["expansions_text"] = " ".join(exps)
        if e["label"] == "scope":
            e["owner"] = scope_owner.get(e["identity"])
        elif e["label"] == "derived_column":
            e["owner"] = e["identity"].rsplit(".", 1)[0]
        elif e["label"] == "drift":
            e["owner"] = e["identity"].split("::")[0]
        e["words"] = speak(read, e)

    def add(kind, identity, name, owner):
        # literal: shape
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
            add("param", f"{key}::param/{p['name']}",
                p["name"], key)
    # THE TOTAL-SCORE LAW (2026-09-08): label:: group entries died —
    # the label is a CARD on every member (grounding.cards)
    return [e for e in out if e["words"] or e["label"] not in
            ("condition",)]  # empty conditions never index
