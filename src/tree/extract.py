"""Decision-site extraction — ADR 0044 clause 1 (conservation of
decision sites), on the NATIVE parser.

Every decision-bearing position in a fragment's AST (WHERE / JOIN ON /
HAVING / CASE WHEN, at predicate grain) maps to exactly one extracted
DecisionNode OR one counted UnextractedSite:

    handled_count + len(unextracted) == decision_sites_total

There is no third bucket. Boolean shape (AND/OR/NOT nesting) is
preserved, never flattened — flattening an OR into AND-bullets silently
changes meaning (the LDA OR-inside-AND, TRACE_USP_ED_SEPSIS.md).

Parser: ScriptDom via src/parser/scriptdom_loader — the dialect-native
parser, per the native-parser law (ADR 0001, hardened 2026-08-19:
"under no circumstances" sqlglot — Sunny). Expression text is taken
VERBATIM from the token stream (no regeneration, no CONVERT→CAST
rewriting). What the walker does not model lands in `unextracted` with
a reason code — counted, escalated (ADR 0045 §3), never silent:
dynamic SQL (`EXEC(@sql)`) permanently; IF control-flow until the
`parameter_default` modeling decision (TREE_PHASE1_ED_SEPSIS.md
reviewer question 3) is made.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.parser.scriptdom_loader import parse_tsql
from src.parser.sql_parser import normalize_sql_whitespace

FALLOUT_STAGE = "300_tree_unextracted"
CONTRACT_ID = "contract:graph_decision_sites"

# ScriptDom BooleanComparisonExpression.ComparisonType -> our op names
_COMPARISON_OPS = {
    "Equals": "EQ",
    "NotEqualToBrackets": "NEQ",
    "NotEqualToExclamation": "NEQ",
    "GreaterThan": "GT",
    "LessThan": "LT",
    "GreaterThanOrEqualTo": "GTE",
    "LessThanOrEqualTo": "LTE",
}

# Node type names whose subtrees never hold decision contexts we want
# and are expensive to reflect over.
_SKIP_PROPERTIES = frozenset({
    "StartLine", "StartColumn", "StartOffset", "FragmentLength",
    "FirstTokenIndex", "LastTokenIndex", "ScriptTokenStream",
    "Value", "LargeValue", "IsNot", "IsPrimaryExpression",
    "Collation",
})


@dataclass
class DecisionNode:
    node_id: str
    kind: str                       # "and" | "or" | "not" | "predicate"
    context: str                    # where | join_on | having | case_when
    expression_sql: str             # VERBATIM token-stream text, whitespace-normalized
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
    # dynamic_sql | parse_failed | control_flow_if |
    # unmodeled_construct:<Type> | reflection_suppressed
    reason_code: str
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
    # alias/name (UPPER) -> (schema or None, table-with-#-marker) — the
    # resolution material for decision→column edges (1b). CTE names map
    # to (None, name) like temps: both are step-side.
    table_aliases: "dict[str, tuple]" = field(default_factory=dict)

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


def _type_name(node) -> str:
    return node.GetType().Name


def _verbatim(node) -> str:
    """Original source text from the token stream — never regenerated."""
    tokens = node.ScriptTokenStream
    if tokens is None:
        return ""
    start, end = node.FirstTokenIndex, node.LastTokenIndex
    if start < 0 or end < 0:
        return ""
    return normalize_sql_whitespace(
        "".join(tokens[i].Text for i in range(start, min(end + 1, tokens.Count))))


class _Extractor:
    def __init__(self, tree: DecisionTree):
        self.tree = tree
        self._site_n = 0
        self.suppressed = 0

    # -- accounting ----------------------------------------------------
    def _next_site_id(self) -> str:
        self._site_n += 1
        return f"site{self._site_n - 1}"

    def add_unextracted(self, context: str, reason_code: str, sql_text: str) -> None:
        self.tree.decision_sites_total += 1
        self.tree.unextracted.append(UnextractedSite(
            site_id=self._next_site_id(), context=context,
            reason_code=reason_code, expression_sql=sql_text[:500]))

    def add_site(self, context: str, condition) -> None:
        site_id = self._next_site_id()
        root = self._convert(condition, context, f"{site_id}.0")
        if root is not None:
            self.tree.sites.append(DecisionSite(
                site_id=site_id, context=context, root=root))

    # -- generic reflection walk (the scriptdom_fabric idiom, with a
    # type-level property cache: thousands of AST nodes share ~50 types,
    # and each pythonnet GetProperties() call marshals — caching is the
    # difference between seconds and minutes at corpus scale) ----------
    _PROPS_BY_TYPE: "dict[str, list]" = {}

    def _props(self, node):
        tn = node.GetType().Name
        cached = self._PROPS_BY_TYPE.get(tn)
        if cached is None:
            cached = []
            try:
                for prop in node.GetType().GetProperties():
                    if prop.Name in _SKIP_PROPERTIES:
                        continue
                    try:
                        if prop.GetIndexParameters().Length > 0:
                            continue  # an indexer, not a child property
                    except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                        self.suppressed += 1
                        continue
                    cached.append(prop)
            except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                self.suppressed += 1
            self._PROPS_BY_TYPE[tn] = cached
        return cached

    def _children(self, node):
        for prop in self._props(node):
            try:
                value = prop.GetValue(node)
            except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                self.suppressed += 1
                continue
            if value is None:
                continue
            if hasattr(value, "GetType") and hasattr(value, "StartLine"):
                yield value
            elif hasattr(value, "Count") and not isinstance(value, str):
                try:
                    for k in range(value.Count):
                        item = value[k]
                        if hasattr(item, "StartLine"):
                            yield item
                except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                    self.suppressed += 1

    def _walk_scalars(self, node, type_names: "set[str]", out: list,
                      depth: int = 0) -> None:
        if node is None or depth > 40:
            return
        if _type_name(node) in type_names:
            out.append(node)
        for child in self._children(node):
            self._walk_scalars(child, type_names, out, depth + 1)

    # -- leaf helpers ---------------------------------------------------
    def _column_names(self, node) -> "list[str]":
        cols = []
        self._walk_scalars(node, {"ColumnReferenceExpression"}, cols)
        names = []
        for c in cols:
            try:
                idents = c.MultiPartIdentifier.Identifiers
                names.append(".".join(idents[i].Value
                                      for i in range(idents.Count)))
            except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                self.suppressed += 1
        return names

    def _operands(self, node) -> "list[str]":
        found = []
        literal_types = {"IntegerLiteral", "NumericLiteral", "StringLiteral",
                         "MoneyLiteral", "RealLiteral", "BinaryLiteral",
                         "NullLiteral", "VariableReference"}
        raw = []
        self._walk_scalars(node, literal_types, raw)
        for lit in raw:
            try:
                tn = _type_name(lit)
                if tn == "VariableReference":
                    found.append(lit.Name)
                elif tn == "StringLiteral":
                    found.append(f"'{lit.Value}'")
                elif tn == "NullLiteral":
                    found.append("NULL")
                else:
                    found.append(lit.Value)
            except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                self.suppressed += 1
        return found

    def _principal_column(self, side) -> "str | None":
        if side is not None and _type_name(side) == "ColumnReferenceExpression":
            names = self._column_names(side)
            return names[0] if names else None
        return None

    def _leaf(self, node, context: str, path: str, op: str,
              principal_side=None) -> DecisionNode:
        self.tree.decision_sites_total += 1
        self.tree.handled_count += 1
        return DecisionNode(
            node_id=path, kind="predicate", op=op, context=context,
            expression_sql=_verbatim(node),
            column=self._principal_column(principal_side),
            columns=self._column_names(node),
            operands=self._operands(node),
            must_voice=True)

    # NOTE on negation: when the negation is intrinsic to the predicate's
    # own text (x NOT IN (...), x IS NOT NULL, x NOT BETWEEN a AND b) the
    # polarity lives in the OP (NOT_IN / IS_NOT / NOT_BETWEEN) — a single
    # leaf, no extra NOT node. Wrapping such a leaf in NOT would DOUBLE
    # the negation (caught by the ED-sepsis acceptance render 2026-08-19:
    # "NOT(x IS NOT NULL)" claimed the opposite of the SQL). A standalone
    # NOT (BooleanNotExpression, e.g. NOT EXISTS) remains a real node.

    # -- boolean tree conversion ----------------------------------------
    def _convert(self, node, context: str, path: str) -> "DecisionNode | None":
        tn = _type_name(node)

        if tn == "BooleanParenthesisExpression":
            return self._convert(node.Expression, context, path)

        if tn == "BooleanBinaryExpression":
            kind = str(node.BinaryExpressionType).lower()   # and | or
            children = []
            for i, part in enumerate((node.FirstExpression,
                                      node.SecondExpression)):
                child = self._convert(part, context, f"{path}.{i}")
                if child is not None:
                    children.append(child)
            return DecisionNode(node_id=path, kind=kind, context=context,
                                expression_sql=_verbatim(node),
                                children=children)

        if tn == "BooleanNotExpression":
            child = self._convert(node.Expression, context, f"{path}.0")
            return DecisionNode(node_id=path, kind="not", context=context,
                                expression_sql=_verbatim(node),
                                children=[child] if child else [])

        if tn == "BooleanComparisonExpression":
            op = _COMPARISON_OPS.get(str(node.ComparisonType))
            if op is None:
                self.tree.decision_sites_total += 1
                self.tree.unextracted.append(UnextractedSite(
                    site_id=path, context=context,
                    reason_code=f"unmodeled_construct:Comparison."
                                f"{node.ComparisonType}",
                    expression_sql=_verbatim(node)[:500]))
                return None
            return self._leaf(node, context, path, op,
                              principal_side=node.FirstExpression)

        if tn == "InPredicate":
            op = "NOT_IN" if node.NotDefined else "IN"
            return self._leaf(node, context, path, op,
                              principal_side=node.Expression)

        if tn == "BooleanTernaryExpression":
            # ScriptDom's BETWEEN: TernaryExpressionType Between/NotBetween
            # (live find 2026-08-19: 22 arrival-window filters — including
            # Base_Pop's ONE true filter — landed unmodeled until this).
            kind = str(node.TernaryExpressionType)
            if kind in ("Between", "NotBetween"):
                op = "BETWEEN" if kind == "Between" else "NOT_BETWEEN"
                return self._leaf(node, context, path, op,
                                  principal_side=node.FirstExpression)
            self.tree.decision_sites_total += 1
            self.tree.unextracted.append(UnextractedSite(
                site_id=path, context=context,
                reason_code=f"unmodeled_construct:Ternary.{kind}",
                expression_sql=_verbatim(node)[:500]))
            return None

        if tn == "LikePredicate":
            op = "NOT_LIKE" if node.NotDefined else "LIKE"
            return self._leaf(node, context, path, op,
                              principal_side=node.FirstExpression)

        if tn == "BooleanIsNullExpression":
            op = "IS_NOT" if node.IsNot else "IS"
            return self._leaf(node, context, path, op,
                              principal_side=node.Expression)

        if tn == "ExistsPredicate":
            # The subquery's own WHERE becomes its own site via the
            # context walk; the EXISTS itself is one existence decision.
            self.tree.decision_sites_total += 1
            self.tree.handled_count += 1
            return DecisionNode(
                node_id=path, kind="predicate", op="EXISTS", context=context,
                expression_sql=_verbatim(node),
                columns=self._column_names(node),
                operands=self._operands(node), must_voice=True)

        # A boolean position we do not model — counted, never dropped.
        self.tree.decision_sites_total += 1
        self.tree.unextracted.append(UnextractedSite(
            site_id=path, context=context,
            reason_code=f"unmodeled_construct:{tn}",
            expression_sql=_verbatim(node)[:500]))
        return None

    # -- context collection over a statement -----------------------------
    def walk_statement(self, node, depth: int = 0) -> None:
        """Visit every AST node exactly once; a context node registers
        its site, then descent ALWAYS continues — subqueries inside a
        WHERE (EXISTS, IN (SELECT ...)) carry their own WhereClause
        nodes, which become their own sites. Only dynamic SQL stops
        descent (nothing inside a runtime string is static SQL)."""
        if node is None or depth > 60:
            return
        tn = _type_name(node)

        if tn == "ExecutableStringList":
            # dynamic SQL: EXEC(@sql) / EXEC('...') — permanent counted gap
            self.add_unextracted("statement", "dynamic_sql", _verbatim(node))
            return
        if tn == "NamedTableReference":
            try:
                so = node.SchemaObject
                table = so.BaseIdentifier.Value  # keeps the '#' marker
                schema = so.SchemaIdentifier.Value if so.SchemaIdentifier else None
                self.tree.table_aliases.setdefault(table.upper(), (schema, table))
                if node.Alias is not None:
                    self.tree.table_aliases[node.Alias.Value.upper()] = (schema, table)
            except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                self.suppressed += 1
        elif tn == "CommonTableExpression":
            try:
                name = node.ExpressionName.Value
                self.tree.table_aliases.setdefault(name.upper(), (None, name))
            except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                self.suppressed += 1
        elif tn == "QueryDerivedTable":
            try:
                if node.Alias is not None:
                    name = node.Alias.Value
                    self.tree.table_aliases.setdefault(name.upper(), (None, name))
            except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
                self.suppressed += 1
        if tn == "IfStatement":
            # RULED (Sunny 2026-08-19): parameter-defaulting IF blocks
            # (branches SET variables — the default reporting window) are
            # first-class parameter_default sites so descriptions can
            # voice them. Other control-flow IFs stay counted gaps.
            # Descent still collects the branches' statements and any
            # subqueries in the predicate.
            sets = []
            self._walk_scalars(node, {"SetVariableStatement"}, sets)
            if sets and node.Predicate is not None:
                site_id = self._next_site_id()
                self.tree.decision_sites_total += 1
                self.tree.handled_count += 1
                leaf = DecisionNode(
                    node_id=f"{site_id}.0", kind="predicate",
                    op="PARAMETER_DEFAULT", context="parameter_default",
                    expression_sql=_verbatim(node)[:1000],
                    columns=[], operands=self._operands(node),
                    must_voice=True)
                self.tree.sites.append(DecisionSite(
                    site_id=site_id, context="parameter_default", root=leaf))
            else:
                self.add_unextracted(
                    "statement", "control_flow_if",
                    _verbatim(node.Predicate) if node.Predicate else "IF")
        elif tn == "WhereClause":
            self.add_site("where", node.SearchCondition)
        elif tn == "HavingClause":
            self.add_site("having", node.SearchCondition)
        elif tn == "QualifiedJoin":
            if node.SearchCondition is not None:
                self.add_site("join_on", node.SearchCondition)
        elif tn == "SearchedWhenClause":
            self.add_site("case_when", node.WhenExpression)
        elif tn == "SimpleCaseExpression":
            # CASE <input> WHEN <value> ... — each WHEN is an equality
            # decision; synthesized as a leaf so it is never silent.
            try:
                for i in range(node.WhenClauses.Count):
                    wc = node.WhenClauses[i]
                    site_id = self._next_site_id()
                    self.tree.decision_sites_total += 1
                    self.tree.handled_count += 1
                    leaf = DecisionNode(
                        node_id=f"{site_id}.0", kind="predicate", op="EQ",
                        context="case_when",
                        expression_sql=normalize_sql_whitespace(
                            f"{_verbatim(node.InputExpression)} = "
                            f"{_verbatim(wc.WhenExpression)}"),
                        column=self._principal_column(node.InputExpression),
                        columns=self._column_names(node.InputExpression)
                        + self._column_names(wc.WhenExpression),
                        operands=self._operands(wc.WhenExpression),
                        must_voice=True)
                    self.tree.sites.append(DecisionSite(
                        site_id=site_id, context="case_when", root=leaf))
            except Exception:  # noqa: BLE001 — .NET reflection; counted, escalated
                self.add_unextracted("case_when", "reflection_suppressed",
                                     _verbatim(node))

        for child in self._children(node):
            self.walk_statement(child, depth + 1)


def build_decision_tree(fragment: str) -> DecisionTree:
    """Parse one fragment with the NATIVE parser and extract its
    decision sites under the conservation law. A fragment that cannot
    be parsed becomes a single counted unextracted site — the tree
    never lies by omission."""
    tree = DecisionTree(fragment=fragment)
    if not fragment or not fragment.strip():
        return tree

    ex = _Extractor(tree)
    ast, errors = parse_tsql(fragment)
    if errors:
        upper = fragment.upper()
        reason = ("dynamic_sql"
                  if ("EXEC" in upper or "SP_EXECUTESQL" in upper)
                  else "parse_failed")
        ex.add_unextracted("statement", reason,
                           f"{fragment[:300]} -- {errors[0]}")
        return tree

    ex.walk_statement(ast)

    if ex.suppressed:
        # Reflection suppressions could have HIDDEN a decision context —
        # surface the possibility as one counted, escalated site.
        ex.add_unextracted(
            "statement", "reflection_suppressed",
            f"{ex.suppressed} reflection accesses suppressed during walk")

    assert tree.handled_count + len(tree.unextracted) == tree.decision_sites_total, (
        "conservation violated — a decision site fell into a third bucket"
    )
    return tree


def find_nodes(root, type_names: "set[str]") -> list:
    """Collect AST nodes by ScriptDom type name (cached reflection walk)
    — shared utility for corpus tooling (e.g. the join-map deriver)."""
    ex = _Extractor(DecisionTree(fragment=""))
    out: list = []
    ex._walk_scalars(root, set(type_names), out)
    return out


def statement_texts(sql: str) -> "list[str]":
    """Verbatim top-level statement texts, split by the NATIVE parser —
    ScriptDom owns statement boundaries (no heuristics, ever)."""
    ast, errors = parse_tsql(sql)
    if errors:
        raise ValueError(f"T-SQL parse errors: {errors[0]}")
    out = []
    for b in range(ast.Batches.Count):
        batch = ast.Batches[b]
        for s in range(batch.Statements.Count):
            out.append(_verbatim(batch.Statements[s]))
    return out


# ---------------------------------------------------------------------
# Persistence (graph_decision_sites) and escalation (ops_fallout)
# ---------------------------------------------------------------------

def decision_site_rows(tree: DecisionTree, metric_id: str,
                       step_name: str = "") -> "list[dict]":
    """Rows for graph_decision_sites — extracted sites carry the
    faithful subtree as JSON; unextracted sites appear with status
    'unextracted' so conservation is queryable in the table itself."""
    import json
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
            "reachability": None,  # patched by the graph wiring (1b)
        })
    for u in tree.unextracted:
        rows.append({
            "metric_id": metric_id, "step_name": step_name,
            "site_id": u.site_id, "context": u.context,
            "status": "unextracted", "predicate_count": 1,
            "columns_used": json.dumps([]), "tree": None,
            "expression_sql": u.expression_sql,
            "reason_code": u.reason_code,
            "reachability": None,
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
