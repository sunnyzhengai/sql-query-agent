"""ADR 0060 — the parse is the plan (PROTOTYPE; the experiment's
vehicle, never wired into the shipping engine until the corpus
measurement rules).

The LLM is demoted two ranks: never the router, never the author —
only the PARSER. It translates the user's sentence into a small
closed vocabulary; everything after the parse is deterministic:

    NL → PARSE (LLM, schema-closed) → CONFIRM (glass) →
    COMPOSE (code → the existing ops algebra) → DISPLAY (stamped)

Closure is STRUCTURAL: the primitives are an enum in the parse
tool's schema, so an out-of-vocabulary parse cannot exist; an
unmappable question fails closed with the vocabulary offer (0060
§6 metric 5). Entities ground by exact-then-contains against the
catalog — the user's own tokens, no embeddings, no LLM judgment.
The composed plan is a sequence of EXISTING algebra calls — the
prototype is a planner in front of the engine, not an engine.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from src.orchestrator.ops import (
    OpsSession,
    op_census,
    op_compare,
    op_lineage,
    op_retrieve,
    op_search,
)

# The RATIFIED relation lexicon (0060 §2b, ACCEPTED 2026-08-28) —
# primitive -> the deterministic computation it binds to.
PRIMITIVES = (
    "same_or_different",   # compare(logic) — hash partition + diff
    "variants",            # cluster node + logic-group partition
    "reads_or_feeds",      # lineage edges (reads-grain, stamped)
    "flags",               # flag nodes (0054 sweep layer)
    "defines",             # record + decision sites + steps
    "owns",                # ownership fields on the record
    "grain",               # compare + grain_shift flags
)

PARSE_TOOL = {
    "type": "function",
    "function": {
        "name": "file_parse",
        "description": (
            "Translate the user's question into catalog entities and "
            "relation primitives. Entities are the user's OWN tokens "
            "naming things (metrics, steps, tables, people's "
            "phrases); primitives are the closed relation vocabulary."
            " If no primitive fits, return an empty primitives list —"
            " never force a fit."),
        "parameters": {
            "type": "object",
            "properties": {
                "entities": {"type": "array",
                             "items": {"type": "string"}},
                "primitives": {"type": "array",
                               "items": {"type": "string",
                                         "enum": list(PRIMITIVES)}},
                "modifiers": {"type": "array",
                              "items": {"type": "string"}},
            },
            "required": ["entities", "primitives"],
        },
    },
}

PARSE_PROMPT = (
    "You are a PARSER, nothing else. Translate the question into "
    "entities (the user's own tokens that name catalog things) and "
    "relation primitives from the closed vocabulary. You never "
    "answer, never route, never explain. If the question maps to no "
    "primitive, return empty primitives.\n"
    "The vocabulary (surface forms -> primitive):\n"
    "same / different / match / drift / consistent -> "
    "same_or_different\n"
    "ways of / variants / versions -> variants\n"
    "reads / uses / comes from / feeds -> reads_or_feeds\n"
    "flags / issues / wrong / conflicts / problems -> flags\n"
    "defines / criteria / logic of / how calculated -> defines\n"
    "who owns / who stewards -> owns\n"
    "grain / per-what / level -> grain"
)


@dataclass
class Parse:
    entities: "list[str]"
    primitives: "list[str]"
    modifiers: "list[str]" = field(default_factory=list)

    def render(self) -> str:
        """The confirm-on-glass line (0060 §2d): the parse IS the
        plan, displayed before anything executes."""
        prim = ", ".join(self.primitives) or "(no primitive — fails "\
            "closed)"
        ents = ", ".join(self.entities) or "(no entities)"
        return f"reading your question as: {prim} over {{{ents}}}"


class ParseRefusal(Exception):
    """Fail-closed with the vocabulary offer — never a guessed route."""


VOCABULARY_OFFER = (
    "I could not map that question to the relation vocabulary. I can "
    "answer: same/different, variants/ways-of, reads/uses/feeds, "
    "flags/conflicts, how-defined/criteria, who-owns, and grain "
    "questions about named catalog items.")


def parse_question(question: str, chat_api) -> Parse:
    msg = chat_api(
        [{"role": "system", "content": PARSE_PROMPT},
         {"role": "user", "content": question}],
        [PARSE_TOOL],
        {"type": "function", "function": {"name": "file_parse"}})
    calls = msg.get("tool_calls") or []
    raw = {}
    if calls:
        try:
            raw = json.loads(calls[0]["function"]["arguments"] or "{}")
        except json.JSONDecodeError:
            raw = {}
    return Parse(
        entities=[str(e) for e in raw.get("entities") or []],
        primitives=[str(p) for p in raw.get("primitives") or []
                    if p in PRIMITIVES],
        modifiers=[str(m) for m in raw.get("modifiers") or []])


def ground_entities(entities: "list[str]", run_kql,
                    session: OpsSession) -> "list[dict]":
    """Exact-then-contains against the catalog — deterministic string
    matching over the user's own tokens (0060 §2a). Ungrounded
    entities are RETURNED, never guessed around."""
    anchors: "list[dict]" = []
    for e in entities:
        rs = op_search(e, "exact", run_kql, session)
        rows = rs.rows
        if not rows:
            rs = op_search(e, "semantic", run_kql, session)
            rows = [r for r in rs.rows
                    if str(r.get("business_name") or r.get("name")
                           or "").lower() == e.lower()]
        if not rows:
            # containment fallback: the closest semantic row whose
            # display name contains the entity (or the reverse) —
            # deterministic string logic over the search result
            rows = [r for r in rs.rows
                    if e.lower() in str(r.get("business_name")
                                        or r.get("name") or "").lower()
                    or str(r.get("business_name") or r.get("name")
                           or "").lower() in e.lower()][:4]
        if rows:
            # NAME COLLISIONS ANCHOR WHOLLY (the corpus's founding
            # shape): every same-kind row of the exact/containment
            # match is an anchor — one shared name over two metrics
            # is two anchors, and sameness then compares them
            kind0 = rows[0].get("kind")
            same_kind = [r for r in rows
                         if r.get("kind") == kind0][:4]
            for r in same_kind:
                anchors.append({"entity": e, "id": r["id"],
                                "kind": r.get("kind"),
                                "rows": [r]})
        else:
            anchors.append({"entity": e, "id": None, "kind": None,
                            "rows": []})
    return anchors


def compose_plan(parse: Parse,
                 anchors: "list[dict]") -> "list[dict]":
    """Primitives + anchors → a deterministic op sequence over the
    existing algebra. NO fallbacks, NO guessed routes: a shape the
    lexicon cannot compose raises ParseRefusal (metric 5)."""
    grounded = [a for a in anchors if a["id"]]
    ids = [a["id"] for a in grounded]
    if not parse.primitives:
        raise ParseRefusal(VOCABULARY_OFFER)
    plan: "list[dict]" = []
    for prim in parse.primitives:
        if prim in ("same_or_different", "grain"):
            if len(ids) >= 2:
                plan.append({"op": "retrieve", "ids": ids[:4]})
                plan.append({"op": "compare", "refs": ["@prev"],
                             "aspect": "logic"})
            elif len(ids) == 1:
                # one name, sameness asked: the identity's recorded
                # flags carry the machine verdicts (cluster layer)
                plan.append({"op": "retrieve", "ids": ids})
                plan.append({"op": "census", "kind": "flag",
                             "contains": grounded[0]["entity"]})
            else:
                raise ParseRefusal(
                    "a sameness/grain question needs at least one "
                    "named catalog item. " + VOCABULARY_OFFER)
        elif prim == "variants":
            if not grounded:
                raise ParseRefusal(
                    "a variants question needs a named item. "
                    + VOCABULARY_OFFER)
            plan.append({"op": "census", "kind": "flag",
                         "contains": grounded[0]["entity"]})
        elif prim == "reads_or_feeds":
            if not grounded:
                raise ParseRefusal(
                    "a reads/feeds question needs a named table, "
                    "metric, or step. " + VOCABULARY_OFFER)
            a = grounded[0]
            if str(a["id"]).startswith("transform:"):
                plan.append({"op": "retrieve", "ids": [a["id"]]})
            else:
                plan.append({"op": "lineage",
                             "table": a["entity"]})
        elif prim == "flags":
            plan.append({"op": "census", "kind": "flag",
                         "contains": (grounded[0]["entity"]
                                      if grounded else None)})
        elif prim in ("defines", "owns"):
            if not ids:
                raise ParseRefusal(
                    "a definition/ownership question needs a named "
                    "item. " + VOCABULARY_OFFER)
            plan.append({"op": "retrieve", "ids": ids[:4]})
    if not plan:
        raise ParseRefusal(VOCABULARY_OFFER)
    return plan


def execute_plan(plan: "list[dict]", run_kql,
                 session: OpsSession) -> "list":
    """Run the composed sequence through the EXISTING algebra —
    stamped results are the answer; nothing is narrated."""
    results = []
    for step in plan:
        if step["op"] == "retrieve":
            results.append(op_retrieve(step["ids"], run_kql, session))
        elif step["op"] == "compare":
            refs = step["refs"]
            if refs == ["@prev"]:
                refs = [results[-1].ref]
            results.append(op_compare(refs, step.get("aspect"),
                                      run_kql, session))
        elif step["op"] == "census":
            results.append(op_census(
                step["kind"], run_kql, session,
                contains=step.get("contains")))
        elif step["op"] == "lineage":
            results.append(op_lineage(step.get("table", ""),
                                      run_kql, session,
                                      column=step.get("column")))
    return results


def run_parse_traverse(question: str, chat_api, run_kql,
                       session: "OpsSession | None" = None) -> dict:
    """The full prototype path. Returns the parse (the plan on
    glass), the composed steps, and the stamped results — or the
    fail-closed refusal. Confirm-all (ruled §7.1): the harness
    records the rendered parse as the confirmation artifact."""
    session = session or OpsSession()
    session.note_user(question)
    parse = parse_question(question, chat_api)
    try:
        anchors = ground_entities(parse.entities, run_kql, session)
        plan = compose_plan(parse, anchors)
        results = execute_plan(plan, run_kql, session)
    except ParseRefusal as e:
        return {"parse": parse, "confirm": parse.render(),
                "refused": str(e), "plan": [], "results": []}
    return {"parse": parse, "confirm": parse.render(),
            "refused": None, "plan": plan,
            "results": [r.display() for r in results]}
