"""The ask flow (ADR 0078): free question -> typed path -> rendered
answer. The op set is CLOSED (registry Ask_Console); the parser is a
deterministic keyword grammar (an LLM parse hook may map text ->
(op, entity) but is validated against the closed set — parse, never
generate); answers render from MEANINGS: the node answers for
itself, no answer shapes (ADR 0077). Every ask lands an H5 usage
event: outcome matched|ambiguous|no-match, about only on match,
payload post phi-gate. Replay-deterministic (Group E).
"""
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from aivia.flows import produce
from aivia.graph import kg3_artifacts, phi_gate
from aivia.lenses import ask_index, decisions

OPS = ("lookup", "lineage", "filters_on", "who_reads", "define",
       "gaps", "list")

_OP_GRAMMAR: List[Tuple[str, str]] = [
    # browse/enumerate (op ruled 2026-09-06 from Sunny's live ask
    # 'what metrics are there' — a browse question is not a lookup)
    (r"^(?:list|show(?:\s+me)?(?:\s+the)?|browse)\s+(?:all\s+)?(.+?)"
     r"\s*$", "list"),
    (r"^what\s+(.+?)\s+(?:are\s+there|exist|do\s+we\s+have)\s*\??$",
     "list"),
    (r"^(?:what\s+is|whats|describe|define)\s+(.+)$", "lookup"),
    (r"^lineage\s+(?:of\s+)?(.+)$", "lineage"),
    (r"^(?:filters?\s+on|what\s+filters\s+(?:on\s+)?)(.+)$",
     "filters_on"),
    (r"^who\s+(?:reads|uses)\s+(.+)$", "who_reads"),
    (r"^gaps?\s*(.*)$", "gaps"),
]


def parse(question: str) -> Tuple[str, str]:
    """Deterministic keyword grammar; a bare entity name defaults to
    lookup — the least-claiming op."""
    q = " ".join(question.strip().split())
    for pattern, op in _OP_GRAMMAR:
        m = re.match(pattern, q, re.IGNORECASE)
        if m:
            return op, m.group(1).strip(" ?")
    return "lookup", q.strip(" ?")


def _kind_vocabulary() -> Dict[str, str]:
    """Word -> kind, FROM THE REGISTRY (v1.10.0, Sunny's audit: the
    word table was a patch wearing a dict — vocabulary is meaning and
    lands as ruled data, never code). Org words extend via KG3 terms,
    steward-blessed; a new product word is a registry row."""
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Kind_Vocabulary"]
    return {row["Word"].upper(): row["Kind"] for row in sheet
            if row["Word"] != "_ruling"}


def _render_list(read, index, kind_text: str) -> Optional[str]:
    from aivia.lenses.ask_index import _fold
    kind = _kind_vocabulary().get(_fold(kind_text))
    if kind is None:
        return None
    if kind == "metric":
        # the practiced-vs-governed pair (registry ruling): governed
        # metrics are minted concepts; practiced metrics are what the
        # report procs actually EMIT — their delivery selections
        terms = [e for e in index if e["kind"] == "term"]
        deliveries = sorted({e["identity"] for e in index
                             if e["kind"] == "scope"
                             and "::delivery" in e["identity"]})
        lines = [
            "GOVERNED metrics (minted concepts): 0 — a concept is "
            "born only when a HUMAN blesses a family (the lens "
            "computes; a human touch mints). Accepted terms so far: "
            f"{len(terms)}.",
            "",
            f"PRACTICED metrics ({len(deliveries)} delivery "
            "selections — what the report procedures actually emit):"]
        lines += [f"- {d}" for d in deliveries[:40]]
        if len(deliveries) > 40:
            lines.append(f"… and {len(deliveries) - 40} more")
        lines += ["", "Ask any of them by identity for its floor — "
                  "the population, sources, and conditions it ships."]
        return "\n".join(lines)
    entries = sorted({(e["name"], e["identity"]) for e in index
                      if e["kind"] == kind})
    lines = [f"{len(entries)} {kind_text.strip().lower()}:"]
    if kind == "column" and len(entries) > 60:
        return (f"{len(entries)} columns — too many to list flatly. "
                "Ask a table by name to see its shape, or ask "
                "'filters on <column>' / 'lineage of <column>'.")
    shown = [f"- {name}" + (f"  ({ident})" if kind in
                            ("scope", "drift", "derived column")
                            else "")
             for name, ident in entries[:60]]
    lines += shown
    if len(entries) > 60:
        lines.append(f"… and {len(entries) - 60} more")
    return "\n".join(lines)


def _twins(read) -> Dict[str, Dict[str, Any]]:
    return {n.properties["twin"]["file"]: n.properties["twin"]
            for n in read.nodes("meaning_twin")}


def _scopes_reading(read, wanted_ids) -> List[str]:
    """Scopes whose twins draw from (or whose trees resolve to) any
    of the wanted identities — the lineage traversal."""
    hits = []
    for key, tree in sorted(read.trees().items()):
        for stmt in tree["statements"]:
            for s in (list(stmt.get("ctes", []))
                      + ([stmt["scope"]] if stmt.get("scope") else [])):
                if "name_key" not in s:
                    continue
                found = False

                def walk(n):
                    nonlocal found
                    if found or not isinstance(n, (dict, list)):
                        return
                    if isinstance(n, dict):
                        if n.get("resolves_to") in wanted_ids or \
                                n.get("table_ref") in wanted_ids:
                            found = True
                            return
                        for v in n.values():
                            walk(v)
                    else:
                        for v in n:
                            walk(v)
                walk(s)
                if found:
                    hits.append(s["name_key"])
    return hits


def _floor_or_words(read, entity) -> str:
    kind = entity["kind"]
    if kind in ("table", "column"):
        node = next(n for n in read.nodes(kind)
                    if n.identity == entity["identity"])
        desc = (node.properties.get("description") or "").strip()
        return desc or (f"No description is recorded — a counted "
                        f"documentation gap ({entity['name']}).")
    if kind == "scope":
        return produce.compose_floor(read, entity["identity"])
    if kind == "file":
        tree = read.trees()[entity["identity"]]
        names = [s["name_key"].split("::")[-1]
                 for stmt in tree["statements"]
                 for s in ([stmt.get("scope")] if stmt.get("scope")
                           else []) if s and "name_key" in s]
        return (f"A procedure of {len(tree['statements'])} steps; "
                f"named selections: {', '.join(names[:12]) or '(none)'}.")
    if kind == "term":
        node = next(n for n in read.nodes("term")
                    if n.identity == entity["identity"])
        return node.properties.get("definition", "")
    if kind == "derived column":
        scope_key, colname = entity["identity"].rsplit(".", 1)
        for tree in read.trees().values():
            for stmt in tree["statements"]:
                for s in (list(stmt.get("ctes", []))
                          + ([stmt["scope"]] if stmt.get("scope")
                             else [])):
                    if s.get("name_key") != scope_key:
                        continue
                    arms = s.get("combination_arms")
                    shape = arms[0] if arms else s
                    for m in shape.get("projection", []):
                        if m.get("name") == colname:
                            frag = " ".join(
                                m["evidence"]["fragment"].split())
                            return (f"A computed output of "
                                    f"{scope_key}, defined as: "
                                    f"{frag}")
        return f"A computed output of {scope_key}."
    if kind == "drift":
        return ("READER/WRITER DRIFT: this name is read by the "
                "estate's SQL but declared by no dictionary and no "
                "catalog — a silently-failing report until a human "
                "fixes the report or the dictionary. Counted forever.")
    return entity["name"]


def _render(read, op: str, resolution: Dict[str, Any]) -> str:
    entity = resolution.get("entity")
    if op == "gaps" and entity is None:
        from aivia.lenses import census
        gc = census.lens_gap_census(read, None)
        drift = sum(t["resolution_census"].get("unresolved_refs", 0)
                    for t in read.trees().values())
        lines = ["THE GAP TAXONOMY (ruled-silent = ok forever; open "
                 "= needs resolution):"]
        lines += [f"- {k}: {v}" for k, v in sorted(gc.items())
                  if isinstance(v, int)]
        lines.append(f"- drift refs (estate findings): {drift}")
        return "\n".join(lines)
    lines = [f"{entity['kind'].upper()}: {entity['name']}"
             f"  [{entity['identity']}]", ""]
    if op == "lookup":
        lines.append(_floor_or_words(read, entity))
        if entity["kind"] == "drift" and resolution.get("sightings"):
            lines.append("Sighted at: " + ", ".join(
                s["identity"].split("::")[0]
                for s in resolution["sightings"][:8]))
        if entity["kind"] in ("table", "column", "scope"):
            readers = _scopes_reading(
                read, {entity["identity"],
                       "SAME-TREE scope " + entity["identity"]})
            if readers:
                lines += ["", f"Read by {len(readers)} selection(s): "
                          + ", ".join(readers[:8])
                          + (" …" if len(readers) > 8 else "")]
    elif op == "lineage":
        readers = _scopes_reading(
            read, {entity["identity"],
                   "SAME-TREE scope " + entity["identity"]})
        lines.append(f"Read by {len(readers)} selection(s):")
        lines += [f"- {r}" for r in readers[:40]]
        if entity["kind"] == "scope":
            floor = produce.compose_floor(read, entity["identity"])
            drawn = [ln for ln in floor.splitlines()
                     if ln.startswith("Drawn from")]
            lines += [""] + drawn
    elif op == "filters_on":
        wanted = {entity["identity"]}
        found = []
        for key, tree in sorted(read.trees().items()):
            for scope in decisions.named_scopes(tree):
                for pred in decisions.membership_predicates(scope):
                    cited = False

                    def walk(n):
                        nonlocal cited
                        if isinstance(n, dict):
                            if n.get("resolves_to") in wanted:
                                cited = True
                            for v in n.values():
                                walk(v)
                        elif isinstance(n, list):
                            for v in n:
                                walk(v)
                    walk(pred)
                    if cited and not decisions.is_degenerate(pred):
                        voice = produce._Voice(read, tree)
                        phrase = produce._voice_predicate(pred, voice)
                        if phrase:
                            note = pred.get("annotation")
                            if note:
                                phrase = (phrase.rstrip(".")
                                          + f" (annotated '{note}' in "
                                          "the source).")
                            found.append(
                                f"- {scope['name_key']}: {phrase}")
        lines.append(f"{len(found)} filter(s) cite it:")
        lines += found[:40] or ["- (none)"]
    elif op == "who_reads":
        readers = _scopes_reading(
            read, {entity["identity"],
                   "SAME-TREE scope " + entity["identity"]})
        files = sorted({r.split("::")[0] for r in readers})
        lines.append(f"Files: {', '.join(files) or '(none)'}")
        usage = [u for u in read.nodes("usage")
                 if u.properties.get("about") == entity["identity"]]
        lines.append(f"Recorded usage events: {len(usage)}"
                     + ("" if usage else " (none yet — the ledger "
                        "starts when people ask)"))
    elif op == "define":
        lines.append(_floor_or_words(read, entity))
    elif op == "gaps":
        lines.append(_floor_or_words(read, entity))
    return "\n".join(lines)


def ask(store, question: str, author: str,
        occurred_at: str,
        llm_parse: Optional[Callable[[str], Tuple[str, str]]] = None
        ) -> Dict[str, Any]:
    """One ask: parse -> resolve -> render -> usage event. The LLM
    hook, when supplied, proposes (op, entity-text) and is VALIDATED
    against the closed op set; a bad proposal falls back to the
    deterministic parse — parse, never generate."""
    from aivia.graph.read_api import ReadApi
    read = ReadApi(store)
    op, entity_text = parse(question)
    if llm_parse is not None:
        try:
            candidate = llm_parse(question)
            if (isinstance(candidate, tuple) and len(candidate) == 2
                    and candidate[0] in OPS):
                op, entity_text = candidate
        except Exception:  # noqa: BLE001 — a model failure NEVER
            pass           # breaks the ask; the deterministic parse stands
    index = ask_index.lens_ask_index(read, None)["yield"]
    if op == "list":
        listed = _render_list(read, index, entity_text)
        if listed is not None:
            kg3_artifacts.append_usage(
                store, action="asked", author=author,
                occurred_at=occurred_at,
                payload=phi_gate.door1_redact(question).text,
                outcome="matched", about=None)
            return {"op": "list", "outcome": "matched",
                    "answer": listed,
                    "resolution": {"outcome": "matched",
                                   "entity": None}}
        op = "lookup"  # an unlistable word falls through to lookup
    if op == "gaps" and not entity_text:
        resolution: Dict[str, Any] = {"outcome": "matched",
                                      "entity": None}
        answer = _render(read, op, resolution)
        outcome = "matched"
        about = None
    else:
        resolution = ask_index.find(index, entity_text)
        outcome = resolution["outcome"]
        about = (resolution["entity"]["identity"]
                 if outcome == "matched" and resolution.get("entity")
                 else None)
        # NAME-LEVEL read-ops (Sunny's first live ask, 2026-09-06):
        # 'filters on MEDICATION_ID' across six same-named columns IS
        # the question — a read-op aggregates over the whole name,
        # each section labeled by identity. Lookup/define keep
        # ambiguity: there, WHICH one matters.
        if outcome == "ambiguous" \
                and op in ("filters_on", "lineage", "who_reads"):
            cands = resolution["candidates"]
            if len({c["folded"] for c in cands}) == 1 \
                    and {c["kind"] for c in cands} \
                    <= {"column", "derived column"}:
                sections = [
                    f"{len(cands)} columns carry the name "
                    f"{cands[0]['name']} — answering across all of "
                    "them:", ""]
                for c in cands:
                    sections.append(_render(
                        read, op, {"outcome": "matched", "entity": c}))
                    sections.append("")
                outcome = "matched"
                resolution = {"outcome": "matched", "entity": None,
                              "aggregated": cands}
                about = None  # H5: about names ONE node; a name-level
                # answer spans many, so the event carries none
                answer = "\n".join(sections).rstrip()
        if outcome == "matched" and resolution.get("aggregated"):
            pass
        elif outcome == "matched":
            answer = _render(read, op, resolution)
        elif outcome == "ambiguous":
            answer = "AMBIGUOUS — pick one:\n" + "\n".join(
                f"- [{c['kind']}] {c['name']}  ({c['identity']})"
                for c in resolution["candidates"])
        else:
            near = resolution.get("nearest", [])
            answer = ("NO MATCH — nothing in the graph carries that "
                      "name." + ("\nNearest names: " + ", ".join(
                          f"{c['name']} [{c['kind']}]" for c in near)
                          if near else ""))
    kg3_artifacts.append_usage(
        store, action="asked", author=author, occurred_at=occurred_at,
        payload=phi_gate.door1_redact(question).text,
        outcome={"matched": "matched", "ambiguous": "ambiguous",
                 "no-match": "no-match"}[outcome],
        about=about)
    return {"op": op, "outcome": outcome, "answer": answer,
            "resolution": resolution}
