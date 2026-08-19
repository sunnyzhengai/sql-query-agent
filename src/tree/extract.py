"""Decision-site extraction — ADR 0044 clause 1 (conservation of
decision sites).

Every decision-bearing position in a fragment's AST (WHERE / JOIN ON /
HAVING / CASE WHEN conditions, at predicate grain) maps to exactly one
extracted DecisionNode OR one counted UnextractedSite:

    handled_count + len(unextracted) == decision_sites_total

There is no third bucket. Boolean shape (AND/OR/NOT nesting) is
preserved, never flattened — flattening an OR into AND-bullets silently
changes meaning (the LDA OR-inside-AND, TRACE_USP_ED_SEPSIS.md).

Parser note (ADR 0001 unchanged): ScriptDom remains production parse
truth for statement splitting and reference extraction. This module
re-parses SINGLE-STATEMENT fragments (ScriptDom's own output) with
sqlglot to get a walkable expression AST everywhere the wheel runs —
Fabric, dev machines, CI. Anything sqlglot cannot model lands in
`unextracted` with a reason code; dynamic SQL (`EXEC(@sql)`) is a
permanent, counted, escalated gap — never described by guesswork.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

# sqlglot's known failure modes: SqlglotError for grammar it rejects,
# plus bare AssertionError/ValueError/TypeError from dialect internals
# (live find 2026-08-19: tsql FORMAT() with one argument raises a bare
# AssertionError in _format_time). Any of these turns the statement
# into a COUNTED unextracted site — never a crash, never a silent drop.
_PARSER_FAILURES = (SqlglotError, AssertionError, ValueError, TypeError)

_DIALECT = "tsql"

FALLOUT_STAGE = "300_tree_unextracted"
CONTRACT_ID = "contract:graph_decision_sites"

# Predicate classes the extractor models. An expression at a boolean
# position that is not one of these (and not a connective) is counted
# unextracted — the conservation equation makes the gap loud.
_LEAF_OPS: "dict[type, str]" = {
    exp.EQ: "EQ", exp.NEQ: "NEQ",
    exp.GT: "GT", exp.GTE: "GTE", exp.LT: "LT", exp.LTE: "LTE",
    exp.In: "IN", exp.Between: "BETWEEN",
    exp.Like: "LIKE", exp.ILike: "LIKE",
    exp.Is: "IS", exp.Exists: "EXISTS",
}


@dataclass
class DecisionNode:
    node_id: str
    kind: str                       # "and" | "or" | "not" | "predicate"
    context: str                    # where | join_on | having | case_when
    expression_sql: str             # canonical tsql rendering (deterministic)
    op: "str | None" = None         # EQ / IN / BETWEEN / EXISTS / ... (leaves)
    column: "str | None" = None     # principal (left-side) column, if simple
    columns: "list[str]" = field(default_factory=list)
    operands: "list[str]" = field(default_factory=list)  # literals + @params
    children: "list[DecisionNode]" = field(default_factory=list)
    must_voice: bool = False        # predicate leaves must be voiced (clause 5)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id, "kind": self.kind, "op": self.op,
            "context": self.context, "column": self.column,
            "columns": self.columns, "operands": self.operands,
            "expression_sql": self.expression_sql,
            "must_voice": self.must_voice,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class UnextractedSite:
    site_id: str
    context: str
    reason_code: str        # dynamic_sql | parse_failed | unmodeled_construct:<Type>
    expression_sql: str


@dataclass
class DecisionSite:
    site_id: str
    context: str
    root: DecisionNode


@dataclass
class DecisionTree:
    fragment: str
    sites: "list[DecisionSite]" = field(default_factory=list)
    unextracted: "list[UnextractedSite]" = field(default_factory=list)
    decision_sites_total: int = 0
    handled_count: int = 0

    @property
    def nodes(self) -> "list[DecisionNode]":
        flat: "list[DecisionNode]" = []

        def walk(n: DecisionNode) -> None:
            flat.append(n)
            for c in n.children:
                walk(c)

        for s in self.sites:
            walk(s.root)
        return flat

    def has_or_node(self, within: "list[str]") -> bool:
        """True when some OR node's subtree carries every given token —
        the boolean-shape guard: the OR must survive as an OR."""
        return any(
            n.kind == "or" and all(t in n.expression_sql for t in within)
            for n in self.nodes
        )


def _sql(e: exp.Expression) -> str:
    return e.sql(dialect=_DIALECT)


def _repr_safe(e: exp.Expression) -> str:
    try:
        return _sql(e)[:400]
    except _PARSER_FAILURES:
        return str(e)[:400]  # regeneration can fail where parsing did not


def _looks_dynamic(text: str) -> bool:
    upper = text.upper()
    return "EXEC" in upper or "SP_EXECUTESQL" in upper


def _statement_is_dynamic_exec(stmt: exp.Expression) -> bool:
    if isinstance(stmt, (exp.Command, exp.Anonymous)):
        head = _sql(stmt).lstrip().upper()
        return head.startswith(("EXEC", "SP_EXECUTESQL"))
    return False


class _Extractor:
    def __init__(self, tree: DecisionTree):
        self.tree = tree
        self._site_n = 0

    def _next_site_id(self) -> str:
        self._site_n += 1
        return f"site{self._site_n - 1}"

    def add_unextracted(self, context: str, reason_code: str, sql_text: str) -> None:
        self.tree.decision_sites_total += 1
        self.tree.unextracted.append(UnextractedSite(
            site_id=self._next_site_id(), context=context,
            reason_code=reason_code, expression_sql=sql_text[:500]))

    def add_site(self, context: str, condition: exp.Expression) -> None:
        site_id = self._next_site_id()
        root = self._convert(condition, context, f"{site_id}.0")
        if root is not None:
            self.tree.sites.append(DecisionSite(
                site_id=site_id, context=context, root=root))

    def _convert(self, e: exp.Expression, context: str,
                 path: str) -> "DecisionNode | None":
        """One boolean expression → one faithful subtree. Every leaf
        position increments the conservation counters exactly once."""
        if isinstance(e, exp.Paren):
            return self._convert(e.this, context, path)

        if isinstance(e, (exp.And, exp.Or)):
            kind = "and" if isinstance(e, exp.And) else "or"
            children = []
            for i, part in enumerate((e.this, e.expression)):
                child = self._convert(part, context, f"{path}.{i}")
                if child is not None:
                    children.append(child)
            return DecisionNode(node_id=path, kind=kind, context=context,
                                expression_sql=_sql(e), children=children)

        if isinstance(e, exp.Not):
            child = self._convert(e.this, context, f"{path}.0")
            return DecisionNode(node_id=path, kind="not", context=context,
                                expression_sql=_sql(e),
                                children=[child] if child else [])

        op = next((name for cls, name in _LEAF_OPS.items()
                   if isinstance(e, cls)), None)
        self.tree.decision_sites_total += 1
        if op is None:
            # A boolean position we do not model — counted, never dropped.
            self.tree.unextracted.append(UnextractedSite(
                site_id=path, context=context,
                reason_code=f"unmodeled_construct:{type(e).__name__}",
                expression_sql=_sql(e)[:500]))
            return None

        self.tree.handled_count += 1
        columns = [_sql(c) for c in e.find_all(exp.Column)]
        left = e.this if isinstance(e.this, exp.Column) else None
        operands = [_sql(lit) for lit in e.find_all(exp.Literal)]
        operands += [_sql(p) for p in e.find_all(exp.Parameter)]
        return DecisionNode(
            node_id=path, kind="predicate", op=op, context=context,
            expression_sql=_sql(e),
            column=_sql(left) if left is not None else None,
            columns=columns, operands=operands, must_voice=True)

    def walk_statement(self, stmt: exp.Expression) -> None:
        if _statement_is_dynamic_exec(stmt):
            self.add_unextracted("statement", "dynamic_sql", _sql(stmt))
            return
        if isinstance(stmt, (exp.Command, exp.Anonymous)):
            return  # DECLARE / SET — carries no decision itself

        for select in stmt.find_all(exp.Select):
            where = select.args.get("where")
            if where is not None:
                self.add_site("where", where.this)
            having = select.args.get("having")
            if having is not None:
                self.add_site("having", having.this)
            for join in select.args.get("joins") or []:
                on = join.args.get("on")
                if on is not None:
                    self.add_site("join_on", on)

        for case in stmt.find_all(exp.Case):
            for if_ in case.args.get("ifs") or []:
                self.add_site("case_when", if_.this)


def build_decision_tree(fragment: str) -> DecisionTree:
    """Parse one fragment and extract its decision sites under the
    conservation law. A fragment that cannot be parsed at all becomes a
    single counted unextracted site — the tree never lies by omission."""
    tree = DecisionTree(fragment=fragment)
    if not fragment or not fragment.strip():
        return tree

    ex = _Extractor(tree)
    try:
        statements = sqlglot.parse(fragment, read=_DIALECT)
    except _PARSER_FAILURES as err:
        reason = "dynamic_sql" if _looks_dynamic(fragment) else "parse_failed"
        ex.add_unextracted("statement", reason, f"{fragment[:400]} -- {err}")
        return tree

    for stmt in statements:
        if stmt is None:
            continue
        try:
            ex.walk_statement(stmt)
        except _PARSER_FAILURES as err:
            ex.add_unextracted(
                "statement", "parse_failed",
                f"{_repr_safe(stmt)} -- walk failed: {err}")

    assert tree.handled_count + len(tree.unextracted) == tree.decision_sites_total, (
        "conservation violated — a decision site fell into a third bucket"
    )
    return tree


# ---------------------------------------------------------------------
# Persistence (graph_decision_sites) and escalation (ops_fallout)
# ---------------------------------------------------------------------

def decision_site_rows(tree: DecisionTree, metric_id: str,
                       step_name: str = "") -> "list[dict]":
    """Rows for graph_decision_sites — extracted sites carry the
    faithful subtree as JSON; unextracted sites appear with status
    'unextracted' so conservation is queryable in the table itself."""
    rows = []
    for s in tree.sites:
        leaf_count = sum(1 for n in tree.nodes
                         if n.kind == "predicate"
                         and n.node_id.startswith(f"{s.site_id}."))
        cols = sorted({c for n in _flatten(s.root) for c in n.columns})
        rows.append({
            "metric_id": metric_id, "step_name": step_name,
            "site_id": s.site_id, "context": s.context,
            "status": "extracted", "predicate_count": leaf_count,
            "columns_used": json.dumps(cols),
            "tree": json.dumps(s.root.to_dict()),
            "expression_sql": s.root.expression_sql,
            "reason_code": None,
        })
    for u in tree.unextracted:
        rows.append({
            "metric_id": metric_id, "step_name": step_name,
            "site_id": u.site_id, "context": u.context,
            "status": "unextracted", "predicate_count": 1,
            "columns_used": json.dumps([]), "tree": None,
            "expression_sql": u.expression_sql,
            "reason_code": u.reason_code,
        })
    return rows


def _flatten(node: DecisionNode) -> "list[DecisionNode]":
    out = [node]
    for c in node.children:
        out.extend(_flatten(c))
    return out


def unextracted_fallout_rows(tree: DecisionTree, metric_id: str,
                             step_name: str = "",
                             run_at: str = "") -> "list[dict]":
    """Every unextracted site ALSO lands in ops_fallout and escalates
    to the human checklist (ADR 0044 clause 1, ADR 0045 clause 3) —
    visible on the admin dashboard, never only an internal counter."""
    entity_base = f"{metric_id}:{step_name}" if step_name else metric_id
    return [{
        "run_at": run_at,
        "stage": FALLOUT_STAGE,
        "entity_id": f"{entity_base}:{u.site_id}",
        "reason_code": u.reason_code,
        "reason_text": (f"decision site not extracted ({u.reason_code}): "
                        f"{u.expression_sql[:200]}"),
        "contract_id": CONTRACT_ID,
        "resolution": "escalated",
    } for u in tree.unextracted]
