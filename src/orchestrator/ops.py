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
import re
from dataclasses import dataclass, field

from src.graph.templates import _fold
from src.orchestrator.assemble import (
    AssemblyError,
    assemble_consumption_node,
    assemble_metric,
    assemble_step,
)
from src.orchestrator.core import resolve
from src.orchestrator.tools import (
    BATCH_FRAGMENTS_QUERY,
    CATALOG_KINDS,
    COLUMN_FILTERS_QUERY,
    COLUMN_SELECTS_QUERY,
    DECISION_COUNT_QUERY,
    DECISIONS_OF_METRIC_QUERY,
    DECISIONS_OF_STEP_QUERY,
    FIND_BY_NAME_QUERY,
    LINKS_OF_REPORT_QUERY,
    LIST_CATALOG_QUERY,
    NAME_CONTAINS_QUERY,
    NAME_CONTAINS_TOKENS_QUERY,
    PROJECTION_EDGES_COUNT_QUERY,
    REPORTS_OF_METRIC_QUERY,
    STEPS_OF_QUERY,
    TABLE_COLUMNS_QUERY,
    TABLE_USED_BY_QUERY,
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

def _containment_rows(phrase: str, run_kql) -> "list[dict]":
    """Name-containment companions for a phrase: full-phrase matches
    first; a multi-word phrase that matches nothing degrades to its
    PRODUCTIVE tokens (has_all over every token that matches anything)
    — the same degradation law as the filtered census. Suite find
    2026-08-21: the model paraphrased 'Sepsis Case' into 'Sepsis Case
    Definition' and the full-phrase containment went dark."""
    clean = phrase.strip()
    if not clean:
        return []
    rows = list(run_kql(NAME_CONTAINS_QUERY, {"p_phrase": clean}))
    if rows:
        return rows
    tokens = [t for t in re.split(r"[^A-Za-z0-9_]+", clean)
              if len(t) >= 2]
    if len(tokens) < 2:
        return []
    productive = [
        t for t in tokens
        if run_kql(NAME_CONTAINS_QUERY, {"p_phrase": t})]
    if not productive:
        return []
    return list(run_kql(NAME_CONTAINS_TOKENS_QUERY,
                        {"p_tokens": " ".join(productive)}))


def _bridge_note(phrase: str, run_kql,
                 session: "OpsSession | None" = None) -> str:
    """Bridge material for an honest-empty result whose parameter is a
    phrase — computed as DATA, stamped into the headline, present no
    matter which op the model chose or how few rounds it took.

    Two clauses (walk finds, Sunny 2026-08-21): near-NAMES from
    catalog containment (shown in the form that contains the phrase),
    and source-TABLE identity from the graph's technical nodes — 'how
    is IP_SEPSIS defined' names a table the catalog surfaces cannot
    see, and the honest zero must say so instead of 'cannot be
    provided'."""
    clean = phrase.strip()
    if not clean:
        return ""
    parts = []
    near: "list[str]" = []
    for r in _containment_rows(clean, run_kql):
        val = next((v for v in (r.get("business_name"), r["name"])
                    if v and clean.lower() in str(v).lower()),
                   r.get("business_name") or r["name"])
        if val and val not in near:
            near.append(str(val))
        # names on screen are surfaced (corpse fixture 2026-08-21:
        # the model retrieved the note's names, the read guarantee
        # refused unsurfaced ids, and the flail burned the round cap)
        if session is not None:
            rid = r["ref"] if r.get("kind") == "metric" else r["node_id"]
            if rid:
                session.surfaced.add(rid)
    if near:
        parts.append(f"Nothing is NAMED {clean!r} exactly; closest by "
                     f"name: {', '.join(near[:5])}.")
    tables: "dict[str, list[str]]" = {}
    for r in run_kql(TABLE_USED_BY_QUERY, {"p_phrase": clean}):
        disp = r.get("business_name") or r.get("ref") or ""
        tables.setdefault(str(r["table_name"]), []).append(str(disp))
        if session is not None and r.get("ref"):
            session.surfaced.add(str(r["ref"]))
    for tname in sorted(tables)[:2]:
        readers = sorted({d for d in tables[tname] if d})
        parts.append(f"{tname!r} is a SOURCE TABLE read by "
                     f"{len(readers)} certified metric(s): "
                     f"{', '.join(readers[:5])}.")
    return " ".join(parts)


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
        out = _attach_cards(out, run_kql)
        # Walk step 1 (Sunny, 2026-08-21): 'how is Sepsis Case
        # defined' ran exact, got an honest 0, and the engine stopped
        # at one round — the floored caption carried no did-you-mean
        # because the bridge stamp existed only on semantic results.
        note = (_bridge_note(clean, run_kql, session)
                if not out else "")
        return session.register(
            "search", {"phrase": phrase, "mode": "exact"},
            out,
            complete=True,
            universe="every catalog item whose name, business name, or "
                     "ref equals the phrase (case-insensitive)",
            note=note)
    result = resolve(phrase, run_kql)
    out = [
        {"id": (c.ref if c.kind == "metric" else c.node_id),
         "kind": c.kind, "name": c.name,
         "business_name": c.business_name or None,
         "of_metric": c.ref if c.kind == "step" else None,
         "closeness": round(c.closeness, 3)}
        for c in result.candidates
    ]
    # Name-containment union (live find 2026-08-21): the embedding
    # ranking buried literal near-names below the top-K; containment
    # IS relevance, so those rows always ride along, flagged.
    have = {r["id"] for r in out}
    for r in _containment_rows(phrase, run_kql):
        rid = r["ref"] if r["kind"] == "metric" else r["node_id"]
        if rid in have:
            continue
        have.add(rid)
        out.append({"id": rid, "kind": r["kind"], "name": r["name"],
                    "business_name": r.get("business_name") or None,
                    "of_metric": r["ref"] if r["kind"] == "step" else None,
                    "name_match": True})
    return session.register(
        "search", {"phrase": phrase, "mode": "semantic"},
        _attach_cards(out, run_kql),
        complete=False,
        universe=f"closest matches by meaning (top {len(out)} of "
                 f"{result.total_matches} above the similarity floor) "
                 "plus every name-containment match — NOT an "
                 "exhaustive list")


def normalize_kind(kind: str) -> "str | None":
    """'metrics' → 'metric'; unknown kinds → None (never guessed)."""
    k = str(kind).strip().lower()
    if k not in CATALOG_KINDS and k.endswith("s") and k[:-1] in CATALOG_KINDS:
        k = k[:-1]
    return k if k in CATALOG_KINDS else None


# The fields the topic-filtered census universe sentence names. The
# filter scans exactly these — never the serialized row. of_metric
# joined 1.50.7 (walk find: census step contains='USP_Severe_Sepsis'
# returned 0 because a step's parent REF lived in no scanned field —
# the model's op choice was right and the data said no).
_MENTION_FIELDS = ("name", "business_name", "description", "of_metric")


def row_mentions(row: dict, needle: str) -> bool:
    """The 'mentions T' predicate — the SPEC of topic-filtered census,
    shared by op_census and the suite oracle so execution and grading
    can never disagree on what 'mentions' means. Its behavior is pinned
    by L0 tests, not by the suite (which, sharing it, cannot catch it).

    Whole-token match over _MENTION_FIELDS only. 1.50.4 (pre-empting
    Sunny's walk question 'how many metrics contain ED logic'): the old
    substring-over-json.dumps matched 'ED' inside 'defined'/'created',
    and JSON keys counted as mentions while the stamped universe
    claimed name/business-name/description scope — a machine-stamped
    sentence the code didn't implement. Underscores are token
    boundaries: 'ED' matches 'ED_SEPSIS' and 'ED Sepsis Screening'."""
    pat = re.compile(
        r"(?<![A-Za-z0-9])" + re.escape(needle.strip())
        + r"(?![A-Za-z0-9])", re.IGNORECASE)
    return any(pat.search(str(row.get(f) or "")) for f in _MENTION_FIELDS)


def op_census(kind: str, run_kql, session: OpsSession,
              contains: "str | None" = None) -> ResultSet:
    """Complete enumeration of one catalog KIND, with the exact count.

    Field find (2026-08-20, Sunny's web-UI test): 'how many metrics are
    there' was planned as an exact name-search for the word 'metrics' —
    an honest empty that the caption then over-read as 'no metrics
    exist'. Kind words are categories, never names; enumeration
    questions get an enumeration primitive."""
    k = normalize_kind(kind)
    if k is None:
        raise OpError(f"census kind must be one of "
                      f"{', '.join(CATALOG_KINDS)}, got {kind!r}")
    rows = run_kql(LIST_CATALOG_QUERY, {"p_kind": k})
    out = [
        {"id": (r["ref"] if r["kind"] == "metric" else r["node_id"]),
         "kind": r["kind"], "name": r["name"],
         "business_name": r.get("business_name") or None,
         "of_metric": r["ref"] if r["kind"] == "step" else None}
        for r in rows
    ]
    out = _attach_cards(out, run_kql)
    params: dict = {"kind": k}
    universe = f"every {k} in the certified catalog — the count is exact"
    if contains and contains.strip():
        # Topic-filtered census (2026-08-21): "how many X mention T"
        # is a DATA operation the store answers exactly — filter the
        # complete enumeration by the shared row_mentions predicate.
        # Question-agnostic parameter, not flow.
        needle = contains.strip()
        full = out
        out = [r for r in full if row_mentions(r, needle)]
        params["contains"] = needle
        universe = (f"every {k} in the certified catalog whose name, "
                    f"business name, description, or parent metric "
                    f"mentions {needle!r} — the count is exact")
        if not out:
            # Multi-word degradation (suite find 2026-08-21: the model
            # filtered by the user's literal words 'ED logic'; the
            # filler noun matched nothing and the honest 0 read as
            # 'none' — while a per-token clause sat unread in the
            # note). A zero-match multi-word phrase degrades to its
            # PRODUCTIVE tokens (AND over every token that matches
            # anything), with the degradation stamped in the universe
            # — the count on screen is then the one the question
            # meant, exactly scoped.
            tokens = [t for t in re.split(r"[^A-Za-z0-9_]+", needle)
                      if len(t) >= 2]
            productive = [t for t in tokens
                          if any(row_mentions(r, t) for r in full)]
            if len(tokens) > 1 and productive:
                out = [r for r in full
                       if all(row_mentions(r, t) for t in productive)]
                dropped = [t for t in tokens if t not in productive]
                params["effective_contains"] = " ".join(productive)
                universe = (
                    f"every {k} in the certified catalog whose name, "
                    f"business name, description, or parent metric "
                    f"mentions "
                    + " AND ".join(repr(t) for t in productive)
                    + f" — no {k} mentions {needle!r} as a phrase"
                    + (f"; {', '.join(repr(t) for t in dropped)} "
                       f"matches nothing and was disregarded"
                       if dropped else "")
                    + " — the count is exact")
    # Same law as the empty exact search (enumerate-all-cases): a
    # zero-row FILTERED census is an honest empty holding a phrase —
    # it carries the bridge note, whichever op the model chose (walk
    # find 2026-08-21: census step contains='IP_SEPSIS' → 0 →
    # "cannot be provided", while the graph knew the table).
    note = (_bridge_note(contains, run_kql, session)
            if contains and contains.strip() and not out else "")
    return session.register("census", params, out, complete=True,
                            universe=universe, note=note)


# --- retrieve: one read primitive (facts + structure merged) ----------

def _shape_decision(d: dict) -> dict:
    """One decision-site row for the ask-path — READ-TIME PHI gate
    (ADR 0025, Sunny's rider 2026-08-21): the export-side redactor
    historically covered only transformation fragments, so decision
    expression_sql in the store predates the gate — every expression
    is scanned and redacted at the last point before it can enter an
    ask-path prompt."""
    from src.phi_scan import redact, scan_sql
    props = d.get("properties")
    if isinstance(props, str):
        props = json.loads(props or "{}")
    props = props or {}
    expr = str(props.get("expression_sql") or "")
    if expr:
        findings = [
            f for f in scan_sql(str(props.get("metric_id") or ""), expr)
            if f.disposition == "redact"]
        if findings:
            expr = redact(expr, findings)
    cols = d.get("columns")
    if isinstance(cols, str):
        cols = json.loads(cols or "[]")
    return {"id": d["node_id"],
            "step": props.get("step_name"),
            "context": props.get("context"),
            "predicate_count": props.get("predicate_count"),
            "expression_sql": expr,
            # columns work 2026-08-22 (walk C3): the site names the
            # columns its predicates decide on — resolved edges only
            "columns": sorted(str(x) for x in (cols or []) if x)}


def _decisions_of(step_id: str, run_kql) -> "list[dict]":
    """The step's decision sites (ADR 0044 → ask-surface, ADR 0052
    backfill item 1)."""
    return [_shape_decision(d)
            for d in run_kql(DECISIONS_OF_STEP_QUERY,
                             {"p_step": step_id})]


def _token_in(needle: str, text: str) -> bool:
    """Whole-token containment — the row_mentions law for plain
    values: 'ED' matches 'ED_SEPSIS' and 'ED Sepsis', never
    'AGGREGATED' (underscores are token boundaries)."""
    pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(needle.strip())
                     + r"(?![A-Za-z0-9])", re.IGNORECASE)
    return bool(pat.search(text or ""))


def _column_usage(column: str, run_kql, session: OpsSession) -> ResultSet:
    """The column blast radius (columns work 2026-08-22, walk probes
    C2/D5; projection grain ordered by Sunny, ADR 0053): which metrics
    FILTER on a column (decision_to_column) and which SELECT it
    (transform_to_column) — the governance answer is the pair
    ('selected by 9, filtered by none')."""
    clean = column.strip()
    frows = list(run_kql(COLUMN_FILTERS_QUERY, {"p_col": clean}))
    srows = list(run_kql(COLUMN_SELECTS_QUERY, {"p_col": clean}))
    exact_names = {str(r.get("column_name") or "")
                   for r in frows + srows
                   if str(r.get("column_name") or "").lower()
                   == clean.lower()}
    def scoped(rows):
        if exact_names:
            return [r for r in rows
                    if str(r.get("column_name") or "") in exact_names]
        # token fallback, never raw substring (the 1.56.1 'ED' corpse)
        return [r for r in rows
                if _token_in(clean, str(r.get("column_name") or ""))]
    out, have = [], set()
    for relation, rows in (("filters", scoped(frows)),
                           ("selects", scoped(srows))):
        for r in rows:
            rid = str(r.get("ref") or "")
            if not rid:
                continue
            key = (relation, str(r.get("column_name")), rid)
            if key in have:
                continue
            have.add(key)
            out.append({"id": rid, "kind": "metric",
                        "name": rid.rsplit(".", 1)[-1],
                        "business_name": r.get("business_name") or None,
                        "of_metric": None,
                        "relation": relation,
                        "column": r.get("column_name"),
                        "at_step": r.get("step_name")})
    scope_word = ("the column" if exact_names
                  else "a column whose name contains")
    # Machine-stamped relation summary with NAMES (1.56.1: the floor
    # must carry the answer for small complete results).
    parts = []
    for relation, label in (("filters", "Filters on"),
                            ("selects", "Selects")):
        names = sorted({str(r.get("business_name") or r["id"])
                        for r in out if r["relation"] == relation})
        if names and len(names) <= 10:
            parts.append(f"{label} {clean!r}: {', '.join(names)}.")
        elif names:
            parts.append(f"{label} {clean!r}: "
                         f"{len(names)} metric(s).")
    note = " ".join(parts)
    if not any(r["relation"] == "selects" for r in out):
        present = run_kql(PROJECTION_EDGES_COUNT_QUERY, {})
        n_proj = present[0].get("Count", 0) if present else 0
        if not n_proj:
            note = (note + " " if note else "") + (
                "Projection (selects) coverage is absent from "
                "this graph export — it predates the ADR 0053 "
                "edges; rerun the pipeline to mint them. Filter "
                "coverage above is current.")
        elif not out:
            note = (f"No decision site filters on and no step selects "
                    f"a column matching {clean!r}.")
    return session.register(
        "lineage", {"column": clean},
        _attach_cards(out, run_kql),
        complete=True,
        universe=(f"every certified metric that FILTERS on "
                  f"(decision_to_column) or SELECTS "
                  f"(transform_to_column) {scope_word} {clean!r} — "
                  "parsed lineage edges, never name mentions; counts "
                  "are exact over recorded edges"),
        note=note)


def op_lineage(table: str, run_kql, session: OpsSession,
               column: "str | None" = None) -> ResultSet:
    """Which certified metrics READ a table — the uses relation from
    parsed transform_to_technical edges, never name mentions. Walk
    find 4 (Sunny, 2026-08-21): 'is there any other metrics using
    IP_SEPSIS?' routed to a mention-census; lineage questions get a
    lineage primitive. Promoted from the reachability roadmap's
    rank-3 item with a walk corpse attached.

    column= (columns work 2026-08-22): the filter blast radius
    instead — exactly one of table/column."""
    if column and column.strip():
        if table.strip():
            raise OpError("lineage takes table OR column, not both")
        return _column_usage(column, run_kql, session)
    clean = table.strip()
    if not clean:
        raise OpError("lineage needs a table or column name")
    rows = list(run_kql(TABLE_USED_BY_QUERY, {"p_phrase": clean}))
    # Exact-table scoping first (1.54.1 corpse: 'IP_SEPSIS' pulled 23
    # table-reader PAIRS across every table containing the phrase —
    # the caption then computed the true per-table count itself and
    # was floored for it, flailing into a dishonest turn). When a
    # table matches exactly, the result is ITS readers — the count on
    # screen is the answer. The fallback is TOKEN matching, never raw
    # substring (1.56.1 corpse: lineage(table='ED') matched every
    # table CONTAINING 'ed' — 80 pairs read as '80 metrics', a
    # dishonest turn; the census learned this lesson in 1.50.4 and
    # the newest op relearned it).
    exact = [r for r in rows
             if str(r.get("table_name") or "").lower() == clean.lower()]
    scoped = exact or [r for r in rows
                       if _token_in(clean,
                                    str(r.get("table_name") or ""))]
    out, have = [], set()
    for r in scoped:
        rid = str(r.get("ref") or "")
        key = (str(r.get("table_name")), rid)
        if not rid or key in have:
            continue
        have.add(key)
        out.append({"id": rid, "kind": "metric",
                    "name": rid.rsplit(".", 1)[-1],
                    "business_name": r.get("business_name") or None,
                    "of_metric": None,
                    "reads_table": r.get("table_name")})
    scope_word = ("the table" if exact
                  else "a table whose name has the token")
    # The reader NAMES are machine truth worth stamping (1.56.1: the
    # gate correctly floored a caption for an invented sub-count, and
    # the floor then lost the reader names — headlines must carry the
    # answer for small complete results).
    distinct = sorted({str(r.get("business_name") or r["id"])
                       for r in out})
    n_tables = len({str(r.get("reads_table")) for r in out})
    note = ""
    if distinct and len(distinct) <= 10:
        note = (f"{len(distinct)} distinct metric(s)"
                + (f" across {n_tables} table(s)" if n_tables > 1
                   else "")
                + f": {', '.join(distinct)}.")
    elif distinct:
        note = (f"{len(distinct)} distinct metric(s) across "
                f"{n_tables} table(s).")
    return session.register(
        "lineage", {"table": clean},
        _attach_cards(out, run_kql),
        complete=True,
        universe=(f"every certified metric whose calculation reads "
                  f"{scope_word} {clean!r} — from parsed SQL lineage "
                  "edges, never name mentions; the count is exact"),
        note=note)


def _table_record(name: str, run_kql, session: OpsSession
                  ) -> "list[dict]":
    """The TABLE record (columns work 2026-08-22, walk probe D4): a
    warehouse table's identity — its columns from the dictionary-
    derived table_to_column edges, and its certified readers from
    parsed lineage. Resolved by name, exact first."""
    rows = list(run_kql(TABLE_COLUMNS_QUERY, {"p_table": name.strip()}))
    exact = [r for r in rows
             if str(r.get("table_name") or "").lower()
             == name.strip().lower()]
    scoped = exact or rows
    tables: "dict[str, dict]" = {}
    for r in scoped:
        t = str(r.get("table_name") or "")
        rec = tables.setdefault(t, {"id": str(r.get("table_id") or ""),
                                    "kind": "table", "name": t,
                                    "columns": []})
        col = r.get("column_name")
        if col and col not in rec["columns"]:
            rec["columns"].append(str(col))
    out = []
    for t, rec in sorted(tables.items()):
        readers = sorted({
            str(u.get("business_name") or u.get("ref") or "")
            for u in run_kql(TABLE_USED_BY_QUERY, {"p_phrase": t})
            if str(u.get("table_name") or "").lower() == t.lower()})
        rec["columns"] = sorted(rec["columns"])
        rec["read_by"] = [x for x in readers if x]
        session.surfaced.add(rec["id"])
        out.append(rec)
    return out


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
                rows.append({"id": an_id, "kind": "step", **fs.facts,
                             "decisions": _decisions_of(an_id, run_kql)})
            elif an_id.startswith(("report:", "measure:")):
                # ADR 0052 backfill item 2 (Sunny's order, 2026-08-21):
                # reports/measures were searchable but hollow — the
                # consumption record plus, for reports, its parsed
                # TMDL links (deterministic lineage, never names).
                fs = assemble_consumption_node(an_id, run_kql)
                row = {"id": an_id, "kind": fs.kind, **fs.facts}
                if an_id.startswith("report:"):
                    bucket = {"report_to_canonical": "executes_metrics",
                              "report_to_technical": "reads_tables",
                              "report_to_measure": "measures"}
                    links: "dict[str, list]" = {
                        v: [] for v in bucket.values()}
                    for r in run_kql(LINKS_OF_REPORT_QUERY,
                                     {"p_id": an_id}):
                        entry = {"id": r["node_id"], "name": r["name"]}
                        if r["edge_type"] == "report_to_canonical":
                            entry["id"] = r["node_id"].removeprefix(
                                "canonical:")
                        session.surfaced.add(entry["id"])
                        links[bucket[r["edge_type"]]].append(entry)
                    row.update(links)
                rows.append(row)
            else:
                try:
                    fs = assemble_metric(an_id, run_kql)
                except AssemblyError:
                    # Not a metric ref — resolve as a TABLE by name
                    # (columns work 2026-08-22, walk D4: 'what columns
                    # does IP_SEPSIS have'); if that also misses, the
                    # original honest note stands.
                    trecs = _table_record(an_id, run_kql, session)
                    if not trecs:
                        raise
                    rows.extend(trecs)
                    continue
                steps = run_kql(STEPS_OF_QUERY, {"p_ref": an_id})
                step_rows = [{"id": s["node_id"], "name": s["name"]}
                             for s in steps]
                for s in step_rows:
                    session.surfaced.add(s["id"])
                reports = [
                    {"id": r["node_id"], "name": r["name"]}
                    for r in run_kql(REPORTS_OF_METRIC_QUERY,
                                     {"p_id": f"canonical:{an_id}"})]
                for r in reports:
                    session.surfaced.add(r["id"])
                dc = run_kql(DECISION_COUNT_QUERY, {"p_ref": an_id})
                # M2 design pass (2026-08-21): the metric record
                # carries its decision evidence INLINE — the top sites
                # by predicate weight, PHI-gated, with the exact total
                # beside them — so drill-down needs ZERO further hops.
                # The closure is the ADR 0044 id scheme itself; the
                # cap is disclosed in the stamped headline (B3).
                sites = [_shape_decision(d)
                         for d in run_kql(DECISIONS_OF_METRIC_QUERY,
                                          {"p_ref": an_id})]
                rows.append({"id": an_id, "kind": "metric", **fs.facts,
                             "steps": step_rows, "reports": reports,
                             "decision_count":
                                 (dc[0].get("Count", 0) if dc else 0),
                             "decision_sites": sites})
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
                                  + ", ".join(available[:16])})
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
