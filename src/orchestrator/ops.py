"""The primitive algebra (ADR 0036): search, retrieve, compare kernels,
and the session result-set registry.

"Make the operations the product. The answer is a caption." Every
operation returns a RESULT SET — a first-class, displayable,
session-registered object (R1, R2, ...) that later actions reference.
Every result self-declares its completeness (mode/universe), so scope
is a visible property of data, never a claim in prose.

Kernels are deterministic and minimal; orchestration (what to search,
what to compare, in what sequence) belongs to the LLM and the human —
the LLM is the orchestrator, never the calculator.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from src.graph.templates import _fold
from src.orchestrator.assemble import (
    AssemblyError,
    assemble_metric,
    assemble_step,
)
from src.orchestrator.core import resolve
from src.orchestrator.tools import (
    BATCH_FRAGMENTS_QUERY,
    FIND_BY_NAME_QUERY,
    STEPS_OF_QUERY,
    _cap,
    _content_key,
    _diff,
)


@dataclass
class ResultSet:
    """One operation's output: displayable rows + self-declared scope."""

    ref: str                     # "R1", "R2", ... assigned by the session
    op: str                      # search | retrieve | compare
    params: dict                 # the CONFIRMED parameters that produced it
    rows: "list[dict]"
    complete: bool               # exact enumeration / full computation?
    universe: str                # what the rows are drawn from, plainly
    note: str = ""               # honesty notes (caps, not-comparable, ...)

    def display(self) -> dict:
        return {"ref": self.ref, "op": self.op, "params": self.params,
                "rows": self.rows, "complete": self.complete,
                "universe": self.universe, "note": self.note,
                "count": len(self.rows)}


@dataclass
class OpsSession:
    """Registry of everything surfaced this session — the visible
    provenance (ADR 0036: the session IS the basis) and the read
    guarantee (only surfaced/user-named ids may be retrieved)."""

    results: "dict[str, ResultSet]" = field(default_factory=dict)
    surfaced: "set[str]" = field(default_factory=set)
    user_text: str = ""
    _counter: int = 0

    def register(self, op, params, rows, complete, universe, note="") -> ResultSet:
        self._counter += 1
        rs = ResultSet(ref=f"R{self._counter}", op=op, params=params,
                       rows=rows, complete=complete, universe=universe,
                       note=note)
        self.results[rs.ref] = rs
        for row in rows:
            rid = row.get("id")
            if rid:
                self.surfaced.add(rid)
        return rs

    def note_user(self, text: str) -> None:
        self.user_text += "\n" + _fold(text)

    def permitted(self, an_id: str) -> bool:
        return an_id in self.surfaced or _fold(an_id) in self.user_text

    def rows_of(self, refs: "list[str]") -> "list[dict]":
        out = []
        for ref in refs:
            if ref in self.results:
                out.extend(self.results[ref].rows)
        return out


class OpError(Exception):
    """Visible, recoverable — rendered to the user, never a 500."""


# --- search: one primitive, two modes ---------------------------------

def _node_cards(ids: "set[str]", run_kql) -> "dict[str, dict]":
    """id -> {name, description, props} from graph_nodes, one batch."""
    cards: "dict[str, dict]" = {}
    for r in run_kql(BATCH_FRAGMENTS_QUERY, {"p_ids": json.dumps(sorted(ids))}):
        props = r.get("properties") or "{}"
        if isinstance(props, str):
            props = json.loads(props)
        cards[r["node_id"]] = {"name": r.get("name"),
                               "description": r.get("description"),
                               "props": props}
    return cards


def _attach_cards(rows: "list[dict]", run_kql) -> "list[dict]":
    """Search rows answer "what does this MEAN", not just what it is
    called (live ask 2026-08-13: the basic tier is customer-facing).
    Each row gains its catalog description; step rows also gain their
    parent metric's business identity and the step's position."""
    want: "set[str]" = set()
    for r in rows:
        if r["kind"] == "metric":
            want.add("canonical:" + r["id"])
        elif r["kind"] == "step":
            want.add(r["id"])
            if r.get("of_metric"):
                want.add("canonical:" + r["of_metric"])
    if not want:
        return rows
    cards = _node_cards(want, run_kql)
    for r in rows:
        if r["kind"] == "metric":
            card = cards.get("canonical:" + r["id"]) or {}
            r["description"] = card.get("description") or None
        elif r["kind"] == "step":
            card = cards.get(r["id"]) or {}
            r["description"] = card.get("description") or None
            r["step_no"] = (card.get("props") or {}).get("step_no")
            parent = cards.get("canonical:" + (r.get("of_metric") or "")) or {}
            r["business_name"] = (
                (parent.get("props") or {}).get("business_name")
                or r.get("business_name") or None)
    return rows

def op_search(phrase: str, mode: str, run_kql,
              session: OpsSession) -> ResultSet:
    if mode not in ("semantic", "exact"):
        raise OpError(f"search mode must be semantic or exact, got {mode!r}")
    if not phrase.strip():
        raise OpError("search needs a phrase")
    if mode == "exact":
        clean = phrase.strip().lstrip("#").strip("[]")
        rows = run_kql(FIND_BY_NAME_QUERY, {"p_name": clean})
        out = [
            {"id": (r["ref"] if r["kind"] == "metric" else r["node_id"]),
             "kind": r["kind"], "name": r["name"],
             "business_name": r.get("business_name") or None,
             "of_metric": r["ref"] if r["kind"] == "step" else None}
            for r in rows
        ]
        return session.register(
            "search", {"phrase": phrase, "mode": "exact"},
            _attach_cards(out, run_kql),
            complete=True,
            universe="every catalog item whose name, business name, or "
                     "ref equals the phrase (case-insensitive)")
    result = resolve(phrase, run_kql)
    out = [
        {"id": (c.ref if c.kind == "metric" else c.node_id),
         "kind": c.kind, "name": c.name,
         "business_name": c.business_name or None,
         "of_metric": c.ref if c.kind == "step" else None,
         "closeness": round(c.closeness, 3)}
        for c in result.candidates
    ]
    return session.register(
        "search", {"phrase": phrase, "mode": "semantic"},
        _attach_cards(out, run_kql),
        complete=False,
        universe=f"closest matches by meaning (top {len(out)} of "
                 f"{result.total_matches} above the similarity floor) — "
                 "NOT an exhaustive list")


# --- retrieve: one read primitive (facts + structure merged) ----------

def op_retrieve(ids: "list[str]", run_kql, session: OpsSession) -> ResultSet:
    if not ids:
        raise OpError("retrieve needs at least one id")
    for an_id in ids:
        if not session.permitted(an_id):
            raise OpError(
                f"id {an_id!r} has not been surfaced in this session and "
                "was not named by the user — search first")
    rows, notes = [], []
    for an_id in ids:
        try:
            if an_id.startswith("transform:"):
                fs = assemble_step(an_id, an_id.split(":", 2)[1], run_kql)
                rows.append({"id": an_id, "kind": "step", **fs.facts})
            else:
                fs = assemble_metric(an_id, run_kql)
                steps = run_kql(STEPS_OF_QUERY, {"p_ref": an_id})
                step_rows = [{"id": s["node_id"], "name": s["name"]}
                             for s in steps]
                for s in step_rows:
                    session.surfaced.add(s["id"])
                rows.append({"id": an_id, "kind": "metric", **fs.facts,
                             "steps": step_rows})
        except AssemblyError as e:
            notes.append(str(e))
    return session.register(
        "retrieve", {"ids": ids}, rows, complete=True,
        universe="full certified records for the requested ids",
        note="; ".join(notes))


# --- compare: three deterministic kernels over any selection ----------

def _texts_for(items: "list[dict]", run_kql) -> "dict[str, str]":
    """id -> comparable SQL text (step fragment or metric whole logic)."""
    texts: "dict[str, str]" = {}
    step_ids = [i["id"] for i in items if i["id"].startswith("transform:")]
    if step_ids:
        rows = run_kql(BATCH_FRAGMENTS_QUERY,
                       {"p_ids": json.dumps(sorted(step_ids))})
        for r in rows:
            props = r.get("properties") or "{}"
            if isinstance(props, str):
                props = json.loads(props)
            texts[r["node_id"]] = props.get("sql_fragment") or ""
    for i in items:
        an_id = i["id"]
        if an_id.startswith("transform:"):
            texts.setdefault(an_id, i.get("sql_fragment") or "")
        else:
            logic = i.get("calculation_logic")
            if logic is None:
                logic = assemble_metric(an_id, run_kql).facts.get(
                    "calculation_logic")
            texts[an_id] = logic or ""
    return texts


def kernel_partition(items: "list[dict]", run_kql) -> "tuple[list, str, bool]":
    """Content-equality partition: N items -> hash groups + diff of the
    two largest. Pairwise, ten-way, one-vs-many are all this kernel."""
    texts = _texts_for(items, run_kql)
    unrecorded = sorted(i for i, t in texts.items() if not t.strip())
    grouped: "dict[str, list]" = {}
    for an_id in sorted(t for t in texts if t not in unrecorded):
        grouped.setdefault(_content_key(texts[an_id]), []).append(an_id)
    groups = sorted(grouped.values(), key=lambda g: (-len(g), g[0]))
    rows = [{"group": gi + 1, "members": g,
             "logic_identical_within_group": True}
            for gi, g in enumerate(groups)]
    if len(groups) >= 2:
        rows.append({"diff_between_two_largest_groups": _diff(
            _cap(texts[groups[0][0]]), _cap(texts[groups[1][0]]))})
    note = ""
    if unrecorded:
        note = (f"SQL not recorded for {unrecorded} — absence is not "
                "sameness; these are excluded from every group")
    return rows, note, not unrecorded


def kernel_set_algebra(items: "list[dict]", key: str) -> "list[dict]":
    """Shared / only-in per item for a list-valued field (e.g. tables)."""
    sets = {}
    for i in items:
        raw = i.get(key) or ""
        vals = ({v.strip() for v in raw.split(",") if v.strip()}
                if isinstance(raw, str) else set(raw))
        sets[i["id"]] = vals
    if not sets:
        return []
    shared = set.intersection(*sets.values()) if sets else set()
    rows = [{"shared": sorted(shared)}]
    for an_id, vals in sets.items():
        rows.append({"id": an_id, "only_here": sorted(vals - shared)})
    return rows


def kernel_field_diff(items: "list[dict]", fields: "list[str]") -> "list[dict]":
    """Scalar fields side by side — agreement computed, never judged.
    A field NO item possesses is an honest miss, not an empty
    comparison (live find 2026-08-13: junk all-None rows)."""
    rows = []
    for f in fields:
        vals = {i["id"]: (i.get(f) or None) for i in items}
        present = {v for v in vals.values() if v}
        if not present:
            available = sorted({k for i in items for k in i
                                if not isinstance(i.get(k), (list, dict))})
            rows.append({"field": f,
                         "error": f"no item has a field {f!r} — "
                                  "available fields: "
                                  + ", ".join(available[:12])})
            continue
        rows.append({"field": f, "values": vals,
                     "all_equal": len(present) == 1 and
                     all(v for v in vals.values())})
    return rows


def kernel_step_alignment(items: "list[dict]", run_kql) -> "tuple[list, str, bool]":
    """Step-aligned decomposition diff (ADR 0043, family F): WHERE two
    metrics diverge — aligned step pairs, missing steps, fragment
    diffs. The partition kernel says THAT they differ; this says where.
    Deterministic; the LLM captions, never judges (ADR 0032)."""
    from src.graph.decomposition_diff import (
        Decomposition,
        DecompStep,
        diff_many,
    )

    # metric refs are bare metric_ids; every non-metric node id carries
    # a layer prefix (transform:/report:/measure:/tech:) — one rule,
    # no prefix lexicon
    metric_refs = [i["id"] for i in items if ":" not in i["id"]]
    if len(metric_refs) < 2:
        raise OpError("aspect 'steps' aligns metric decompositions — "
                      "select at least two metrics (not steps/reports)")
    decomps = []
    for ref in metric_refs:
        step_rows = run_kql(STEPS_OF_QUERY, {"p_ref": ref})
        ids = sorted(r["node_id"] for r in step_rows)
        frags: "dict[str, str]" = {}
        if ids:
            for r in run_kql(BATCH_FRAGMENTS_QUERY,
                             {"p_ids": json.dumps(ids)}):
                props = r.get("properties") or "{}"
                if isinstance(props, str):
                    props = json.loads(props)
                frags[r["node_id"]] = props.get("sql_fragment") or ""
        decomps.append(Decomposition(entity_id=ref, steps=[
            DecompStep(name=r["name"], fragment=frags.get(r["node_id"], ""))
            for r in step_rows
        ]))
    rows: "list[dict]" = []
    for res in diff_many(decomps):
        rows.extend(res.rows())
    skipped = len(items) - len(metric_refs)
    note = (f"{skipped} non-metric item(s) ignored — the steps aspect "
            "ranges over metric decompositions" if skipped else "")
    return rows, note, not skipped


LIST_FIELDS = {"tables": "source_tables", "source_tables": "source_tables"}


def op_compare(refs: "list[str]", aspect: "str | None", run_kql,
               session: OpsSession) -> ResultSet:
    """Compare a selection: aspect None/'logic' -> partition kernel;
    'steps' -> step-aligned decomposition diff; a list field -> set
    algebra; scalar fields -> field diff."""
    items = session.rows_of(refs)
    items = [i for i in items if i.get("id")]
    if len(items) < 2:
        raise OpError("compare needs a selection of at least two items "
                      f"(got {len(items)} from {refs})")
    if aspect == "steps":
        rows, note, complete = kernel_step_alignment(items, run_kql)
        return session.register(
            "compare", {"refs": refs, "aspect": "steps"}, rows,
            complete=complete,
            universe="step-aligned decomposition diff of the selected "
                     "metrics (name -> content -> table alignment; "
                     "whitespace/case forgiven)",
            note=note)
    if aspect in (None, "", "logic", "definition", "sql", "content"):
        rows, note, complete = kernel_partition(items, run_kql)
        return session.register(
            "compare", {"refs": refs, "aspect": "logic"}, rows,
            complete=complete,
            universe=f"content-hash partition of the {len(items)} "
                     "selected items (whitespace/case forgiven)",
            note=note)
    if aspect in LIST_FIELDS:
        rows = kernel_set_algebra(items, LIST_FIELDS[aspect])
        return session.register(
            "compare", {"refs": refs, "aspect": aspect}, rows,
            complete=True,
            universe=f"set algebra over {aspect} of the {len(items)} "
                     "selected items")
    rows = kernel_field_diff(items, [aspect])
    return session.register(
        "compare", {"refs": refs, "aspect": aspect}, rows, complete=True,
        universe=f"field comparison over the {len(items)} selected items")
