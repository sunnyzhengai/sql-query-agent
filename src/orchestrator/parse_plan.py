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
    # TESTPLAN_0062 starting lexicon (B10): how many/count/rows →
    # the data-policy refusal proposal + the definition offer.
    # A word-grain entry, never a question shape (P4/0062).
    "count_rows",
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

# FUZZ-FINDINGS-3 (GENERATOR CLAUSE invoked, 2026-08-29 night): the
# same phrasings flip-flopped their oracles across runs — the LLM's
# primitive choice was a stochastic router wearing a parser's badge.
# The relation lexicon is now DATA that resolves DETERMINISTICALLY
# on the raw question BEFORE the LLM gets a vote (0060's spirit:
# the parse is as deterministic as the plan). Word-grain surface
# forms, never question shapes (P4); the LLM keeps exactly one
# freedom — ENTITY extraction — and confirm-all covers it.
RELATION_LEXICON: "dict[str, tuple]" = {
    "same_or_different": (
        "defined the same", "defined uniformly", "definitions match",
        "same", "different", "differently", "difference", "match",
        "matches", "matching", "identical", "equivalent", "uniform",
        "uniformly", "uniformity", "consistent", "drift"),
    "variants": ("another way", "other than", "ways of", "variants",
                 "variant", "versions", "version"),
    "reads_or_feeds": ("comes from", "reads", "read", "uses", "use",
                       "using", "feeds", "feed", "depends", "depend"),
    "flags": ("red flags", "governance issues", "flags", "flag",
              "issues", "issue", "wrong", "conflicts", "conflict",
              "problems", "problem", "concerns", "concern", "risks",
              "risk"),
    "defines": ("how calculated", "logic of", "defines", "define",
                "defined", "definition", "definitions", "criteria",
                "calculated"),
    "owns": ("who owns", "who stewards", "owns", "steward",
             "stewards"),
    "grain": ("grain", "per-what"),
    "count_rows": ("how many", "number of rows",
                   "number of patients", "count"),
}

# longest-first so phrases win over their own words; word-bounded
_LEXICON_PATTERNS: "list[tuple]" = sorted(
    ((_form, _prim)
     for _prim, _forms in RELATION_LEXICON.items()
     for _form in _forms),
    key=lambda x: -len(x[0]))


def detect_relations(question: str) -> "list[str]":
    """The deterministic relation pass: primitives by FIRST
    OCCURRENCE in the question, deduped — a pure function of the
    string; the flip-flop class structurally cannot exist here."""
    import re as _re
    low = " ".join(question.lower().split())
    hits: "list[tuple]" = []
    claimed: "list[tuple]" = []   # (start, end) spans already won
    for form, prim in _LEXICON_PATTERNS:
        for m in _re.finditer(r"\b" + _re.escape(form) + r"\b", low):
            span = (m.start(), m.end())
            if any(s < span[1] and span[0] < e for s, e in claimed):
                continue          # a longer form already owns this
            claimed.append(span)
            hits.append((span[0], prim))
    out: "list[str]" = []
    for _pos, prim in sorted(hits):
        if prim not in out:
            out.append(prim)
    return out


def _vocabulary_lines() -> str:
    return "\n".join(
        f"{' / '.join(forms)} -> {prim}"
        for prim, forms in RELATION_LEXICON.items())


# The prompt's vocabulary section GENERATES from the lexicon — one
# source, zero drift; the LLM's role here is entity extraction (its
# primitive guess is only the fallback when the scan finds nothing).
PARSE_PROMPT = (
    "You are a PARSER, nothing else. Translate the question into "
    "entities (the user's own tokens that name catalog things) and "
    "relation primitives from the closed vocabulary. You never "
    "answer, never route, never explain. If the question maps to no "
    "primitive, return empty primitives.\n"
    "The vocabulary (surface forms -> primitive):\n"
    + _vocabulary_lines()
)


# RW-BATCH-6 item 3: KIND words are SYSTEM vocabulary — an "entity"
# made entirely of them is a KIND FILTER on the plan, never an
# unmatched entity polluting the SHOW ("certified metrics" grounded
# nothing on B6 and read as a miss). Words, never question shapes.
KIND_WORDS = frozenset({
    "metric", "metrics", "report", "reports", "table", "tables",
    "step", "steps", "term", "terms", "measure", "measures",
    "dashboard", "dashboards", "certified", "governance"})


def split_kind_words(entities: "list[str]") -> "tuple[list, list]":
    """(real_entities, kinds) — an entity whose every token is a kind
    word becomes a filter; anything with one real token stays."""
    import re as _re
    real, kinds = [], []
    for e in entities:
        toks = [t for t in _re.split(r"[^A-Za-z0-9_]+", e) if t]
        if toks and all(t.lower() in KIND_WORDS for t in toks):
            kinds.append(e)
        else:
            real.append(e)
    return real, kinds


@dataclass
class Parse:
    entities: "list[str]"
    primitives: "list[str]"
    modifiers: "list[str]" = field(default_factory=list)
    kinds: "list[str]" = field(default_factory=list)

    def render(self) -> str:
        """The confirm-on-glass line (0060 §2d): the parse IS the
        plan, displayed before anything executes. No relation word
        recognized → the DEFAULT MAP reading (0062, ratified
        emergent-shape debate): show what is connected."""
        if not self.entities and self.kinds:
            # RW-21: kind-only asks are a census, never a dead end
            return ("reading your question as: the catalog census "
                    f"of {', '.join(self.kinds)}")
        ents = ", ".join(self.entities) or "(no entities)"
        if not self.primitives:
            return ("reading your question as: the map around "
                    f"{{{ents}}} — what these are and what connects "
                    "to them")
        prim = ", ".join(self.primitives)
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
    entities, kinds = split_kind_words(
        [str(e) for e in raw.get("entities") or []])
    # FUZZ-FINDINGS-3: the deterministic scan OWNS the primitives;
    # the LLM's schema-closed guess is only the fallback when the
    # lexicon finds nothing in the question
    detected = detect_relations(question)
    return Parse(
        entities=entities,
        primitives=detected or [
            str(p) for p in raw.get("primitives") or []
            if p in PRIMITIVES],
        modifiers=[str(m) for m in raw.get("modifiers") or []],
        kinds=kinds)


def _stem(t: str) -> str:
    """Deterministic morphology (RW-20: 'diabetes' must reach
    'Diabetic') — a suffix strip, never a lexicon of user phrases."""
    t = t.lower()
    for suf in ("ical", "ies", "es", "ic", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 4:
            return t[: len(t) - len(suf)]
    return t


def _ground_one(e: str, run_kql, session: OpsSession) -> "list[dict]":
    """Ground ONE entity: exact tier, then semantic-exact, then
    containment, then STEM-token candidates — deterministic string
    matching over the user's own tokens (0060 §2a; RW-20 'match
    maximally, human prunes' — generosity is safe because every
    match is a prunable checkbox on the card). An entity nothing
    reaches is RETURNED, never guessed around."""
    import re as _re

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
    if not rows:
        # RW-20 (Sunny live: "diabetes codeset" grounded NOTHING —
        # conjunctive brittleness violates ratified 0062): ranked
        # stem-token candidates via the ONE labeled scan; every
        # candidate rides the card as a prunable match
        from src.orchestrator.tools import NAME_CONTAINS_ANY_TOKEN_QUERY
        toks = [t for t in _re.split(r"[^A-Za-z0-9_]+", e)
                if len(t) >= 2]
        stems = []
        for t in toks:
            s = _stem(t)
            if len(s) >= 4 and s not in stems:
                stems.append(s)
        if stems:
            labeled = list(run_kql(NAME_CONTAINS_ANY_TOKEN_QUERY,
                                   {"p_tokens": " ".join(stems)}))
            rows = []
            for r in labeled[:6]:
                rid = (str(r.get("ref"))
                       if r.get("kind") == "metric"
                       else str(r.get("node_id") or ""))
                if not rid:
                    continue
                session.surfaced.add(rid)
                rows.append({"id": rid, "kind": r.get("kind"),
                             "name": r.get("name"),
                             "business_name":
                                 r.get("business_name") or None})
    # TIER2-1 (0060 §2a tier 2, Sunny-authorized 2026-08-29):
    # semantic candidates from the description embeddings NOMINATE —
    # ranked (the search's own closeness order), LABELED, PRUNABLE.
    # Confirm-all makes generosity safe; a pruned nomination is a
    # captured decision. Only when the exact tier missed (rs then
    # holds the semantic result — zero extra queries).
    nominations: "list[dict]" = []
    if rs.params.get("mode") == "semantic":
        # relevance bar (deterministic, no threshold-tuning): a
        # nomination must share a stem token with the candidate's
        # name or DESCRIPTION — tier-2's own data — so junk
        # phrases still report honest misses (B9 survives)
        ent_stems = {_stem(t) for t in _re.split(r"[^A-Za-z0-9_]+", e)
                     if len(_stem(t)) >= 4}
        have = {r.get("id") for r in rows}
        for r in rs.rows:
            if r.get("id") in have or len(nominations) >= 3:
                continue
            blob = " ".join(
                str(r.get(k) or "") for k in
                ("name", "business_name", "description")).lower()
            if not any(s in blob for s in ent_stems):
                continue
            have.add(r.get("id"))
            nominations.append({"entity": e, "id": r["id"],
                                "kind": r.get("kind"),
                                "semantic": True, "rows": [r]})
    if not rows and not nominations:
        return [{"entity": e, "id": None, "kind": None, "rows": []}]
    # NAME COLLISIONS ANCHOR WHOLLY (the corpus's founding
    # shape): every same-kind row of the exact/containment
    # match is an anchor — one shared name over two metrics
    # is two anchors, and sameness then compares them
    kind0 = rows[0].get("kind") if rows else None
    return [{"entity": e, "id": r["id"], "kind": r.get("kind"),
             "rows": [r]}
            for r in rows if r.get("kind") == kind0][:4] + nominations


def ground_entities(entities: "list[str]", run_kql,
                    session: OpsSession,
                    on_grounded=None) -> "list[dict]":
    """Ground every entity — queries run in PARALLEL (RW-18: the
    blank-screen echo; per-entity grounding was serial and each
    tier is a store round-trip). Anchor order follows the input
    entity order regardless of completion order. `on_grounded`
    (optional) fires per entity AS ITS RESULT LANDS — the streamed
    card's fill signal. Registration is lock-safe (OpsSession)."""
    if not entities:
        return []
    if len(entities) == 1:
        got = _ground_one(entities[0], run_kql, session)
        if on_grounded is not None:
            on_grounded(entities[0], got)
        return got
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(4, len(entities))) as ex:
        futures = [ex.submit(_ground_one, e, run_kql, session)
                   for e in entities]
        results: "list[list[dict]]" = [[] for _ in entities]
        for i, f in enumerate(futures):
            try:
                results[i] = f.result()
            except Exception:   # noqa: BLE001 — one miss ≠ all miss
                results[i] = [{"entity": entities[i], "id": None,
                               "kind": None, "rows": []}]
            if on_grounded is not None:
                on_grounded(entities[i], results[i])
    return [a for group in results for a in group]


def _anchor_name(a: dict) -> str:
    """The grounded record's own display name (canonical), falling
    back to the user's phrase only when no row rode along."""
    row = (a.get("rows") or [{}])[0]
    return str(row.get("business_name") or row.get("name")
               or a.get("entity") or "")


def compose_plan(parse: Parse,
                 anchors: "list[dict]") -> "list[dict]":
    """Primitives + anchors → a deterministic op sequence over the
    existing algebra. NO fallbacks, NO guessed routes: a shape the
    lexicon cannot compose raises ParseRefusal (metric 5)."""
    grounded = [a for a in anchors if a["id"]]
    ids = [a["id"] for a in grounded]
    if not parse.entities and parse.kinds:
        # RW-21 (kind-only regression, Sunny live: "what metrics are
        # there" hit the no-entity card — the engine answered this
        # for weeks): a kind filter with zero entities is a VALID
        # census plan; the first kind word that normalizes wins
        import re as _re

        from src.orchestrator.ops import normalize_kind
        for phrase in parse.kinds:
            for tok in _re.split(r"[^A-Za-z0-9_]+", phrase):
                k = normalize_kind(tok)
                if k:
                    return [{"op": "census", "kind": k}]
    if not parse.primitives:
        # 0062 (card-everywhere, ratified emergent-shape debate): no
        # relation word recognized is NOT a refusal when something
        # grounded — the DEFAULT MAP reading retrieves the records
        # and their connections; the answer's shape emerges from the
        # subgraph. Zero grounded entities still fails closed.
        if ids:
            return [{"op": "retrieve", "ids": ids[:4]}]
        raise ParseRefusal(VOCABULARY_OFFER)
    plan: "list[dict]" = []
    for prim in parse.primitives:
        if prim in ("same_or_different", "grain"):
            if len(ids) >= 2:
                plan.append({"op": "retrieve", "ids": ids[:4]})
                # FUZZ-FINDINGS-3 rider: compare over EXPLICIT ids
                # (op_compare resolves catalog ids, W12a) — @prev
                # broke under multi-primitive plans where dedup
                # left the wrong retrieve as the last result
                plan.append({"op": "compare", "refs": ids[:4],
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
            if grounded:
                a = grounded[0]
                if str(a["id"]).startswith("transform:"):
                    plan.append({"op": "retrieve", "ids": [a["id"]]})
                elif a.get("kind") in ("metric", "report"):
                    # B6-class: metric/report anchors carry their
                    # own link edges — the record IS the lineage
                    plan.append({"op": "retrieve", "ids": ids[:4]})
                else:
                    plan.append({"op": "lineage",
                                 "table": a["entity"]})
            elif parse.entities:
                # a table WORD needs no catalog anchor — lineage
                # probes the name; its result stamps its own honesty
                # (W13b non-evidence machinery owns the miss)
                plan.append({"op": "lineage",
                             "table": parse.entities[0]})
            else:
                raise ParseRefusal(
                    "a reads/feeds question needs a named table, "
                    "metric, or step. " + VOCABULARY_OFFER)
        elif prim == "flags":
            # FUZZ-FINDINGS-2: the census filter uses the grounded
            # CANONICAL name, never the user's raw phrase —
            # "diabetic individuals" grounded Diabetic Patients but
            # then filtered the flags by the raw words and got zero
            plan.append({"op": "census", "kind": "flag",
                         "contains": (_anchor_name(grounded[0])
                                      if grounded else None)})
        elif prim in ("defines", "owns", "count_rows"):
            # count_rows (B10): the PROPOSAL carries the data-policy
            # refusal wording (the card layer owns it); the plan is
            # the definition OFFER — the record, never row data
            if not ids:
                raise ParseRefusal(
                    "a definition/ownership question needs a named "
                    "item. " + VOCABULARY_OFFER)
            plan.append({"op": "retrieve", "ids": ids[:4]})
    if not plan:
        raise ParseRefusal(VOCABULARY_OFFER)
    # FUZZ-FINDINGS-1 item 3: a multi-relation parse composes each
    # primitive; identical steps dedup (order-preserving) so
    # "defined in the same way" (same_or_different + defines) runs
    # ONE retrieve then the compare, never a duplicate-op refusal
    seen: "set[str]" = set()
    deduped: "list[dict]" = []
    for step in plan:
        key = json.dumps(step, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(step)
    return deduped


def execute_plan(plan: "list[dict]", run_kql,
                 session: OpsSession, on_event=None) -> "list":
    """Run the composed sequence through the EXISTING algebra —
    stamped results are the answer; nothing is narrated. `on_event`
    (RW-18c: progressive op status, the engine's stream pattern)
    receives a pending pre-event at each op's dispatch and never
    breaks the run."""
    def _emit(evt: dict) -> None:
        if on_event is not None:
            try:
                on_event(evt)
            except Exception:   # noqa: BLE001, S110 — listener only
                pass

    results = []
    for step in plan:
        _emit({"component": {"op": step["op"],
                             "params": {k: v for k, v in step.items()
                                        if k != "op"}},
               "pending": True})
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
