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
from functools import lru_cache

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
    # OP-FRONTIER-1: the legacy negated forms are exact synonyms
    # (!<  means >=, !> means <=) — same op, same voice
    "NotLessThan": "GTE",
    "NotGreaterThan": "LTE",
    "NotLike": "NOT_LIKE",
}

# OP-FRONTIER-1 (spec:G4): enum values RULED OUT of extraction, each
# with its reason on the record. tests/test_op_frontier.py holds
# _COMPARISON_OPS ⊎ DEFERRED_COMPARISONS == the ScriptDom enum, by
# reflection, both directions — Microsoft owns the denominator.
DEFERRED_COMPARISONS = {
    "LeftOuterJoin": "legacy *= join predicate — join wiring, not a "
                     "membership condition; falls to unextracted, counted",
    "RightOuterJoin": "legacy =* join predicate — same ruling",
    "IsDistinctFrom": "null-safe <> (SQL 2022) — the claim differs from "
                      "NEQ exactly on missing values; unmodeled until a "
                      "live specimen orders the phrase",
    "IsNotDistinctFrom": "null-safe = (SQL 2022) — same ruling",
}

# The CLOSED set of op codes this extractor can emit — the seam's
# extractor side, as data. test_op_frontier scans this module's own
# source so the list can drift from the code in neither direction,
# and holds EMITTED_OPS == VOICED_OPS ⊎ UNVOICED_OPS on the composer.
EMITTED_OPS = frozenset({
    "EQ", "NEQ", "GT", "LT", "GTE", "LTE",
    "IN", "NOT_IN", "BETWEEN", "NOT_BETWEEN", "LIKE", "NOT_LIKE",
    "IS", "IS_NOT", "EXISTS", "PARAMETER_DEFAULT",
})

# EXPR-IR-1 (ruled 09-03): the closed vocabulary of captured scalar-
# expression kinds — one per GRAMMAR node family, never per shape.
# The renderer holds RENDERED_KINDS ⊎ UNRENDERED_KINDS == this set
# (test_skeleton_composer's kind-frontier check, the G4 form).
EXPR_KINDS = ("column", "literal", "variable", "function",
              "arithmetic", "unary", "cast", "case", "subquery",
              "unknown")

_ARITH_SYMBOLS = {"Add": "+", "Subtract": "-", "Multiply": "*",
                  "Divide": "/", "Modulo": "%"}

# Node type names whose subtrees never hold decision contexts we want
# and are expensive to reflect over.
_SKIP_PROPERTIES = frozenset({
    "StartLine", "StartColumn", "StartOffset", "FragmentLength",
    "FirstTokenIndex", "LastTokenIndex", "ScriptTokenStream",
    "Value", "LargeValue", "IsNot", "IsPrimaryExpression",
    "Collation",
})


@dataclass
class ExprNode:
    """One captured scalar-expression node (EXPR-IR-1): the IR the
    composer and checkers interpret. kind ∈ EXPR_KINDS (closed);
    name holds the column/literal/variable/function/operator token;
    children carry the composition. Captured ONCE, in the extractor
    walk that is already standing on the ScriptDom node — never
    re-parsed, never flattened."""
    kind: str
    name: str = ""
    distinct: bool = False
    children: "list[ExprNode]" = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "name": self.name,
                "distinct": self.distinct,
                "children": [c.to_dict() for c in self.children]}


@dataclass
class DecisionNode:
    node_id: str
    kind: str                       # "and" | "or" | "not" | "predicate"
    context: str                    # where | join_on | having | case_when
    expression_sql: str             # VERBATIM token-stream text, whitespace-normalized
    op: "str | None" = None         # EQ / IN / BETWEEN / EXISTS / ... (leaves)
    column: "str | None" = None     # principal (left-side) column, if simple
    func: "str | None" = None       # principal-side function name (DESC-LEAF-1:
    func_distinct: bool = False     # COUNT(DISTINCT x) vs COUNT(x) — a claim)
    exprs: "list[ExprNode]" = field(default_factory=list)  # EXPR-IR-1:
    # role-ordered captured sides (subject first, then comparands /
    # bounds) — the walk keeps the tree it is standing on instead of
    # flattening it (the depth-1 cliff, ruled dead 09-03)
    columns: "list[str]" = field(default_factory=list)
    operands: "list[str]" = field(default_factory=list)  # literals + @params
    children: "list[DecisionNode]" = field(default_factory=list)
    must_voice: bool = False        # predicate leaves must be voiced (clause 5)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id, "kind": self.kind, "op": self.op,
            "context": self.context, "column": self.column,
            "func": self.func, "func_distinct": self.func_distinct,
            "exprs": [x.to_dict() for x in self.exprs],
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
    # "outer" = the statement's own scope; "sub" = inside a derived
    # table / subquery — ITS decision, not the outer step's claim
    # (DESC-SKELETON-3a, the 8a8f13d leak). In-memory only: the
    # persisted graph_decision_sites rows are unchanged this cut.
    scope: str = "outer"


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
        self.sub_depth = 0          # >0 = inside a derived/subquery scope

    def _scope(self) -> str:
        return "outer" if self.sub_depth == 0 else "sub"

    # -- accounting ----------------------------------------------------
    def _next_site_id(self) -> str:
        self._site_n += 1
        return f"site{self._site_n - 1}"

    def add_unextracted(self, context: str, reason_code: str, sql_text: str) -> None:
        self.tree.decision_sites_total += 1
        self.tree.unextracted.append(UnextractedSite(
            site_id=self._next_site_id(), context=context,
            reason_code=reason_code, expression_sql=sql_text[:4000]))

    def add_site(self, context: str, condition) -> None:
        site_id = self._next_site_id()
        root = self._convert(condition, context, f"{site_id}.0")
        if root is not None:
            self.tree.sites.append(DecisionSite(
                site_id=site_id, context=context, root=root,
                scope=self._scope()))

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

    _CAPTURE_LIMIT = 24   # recursion guard; past this, honesty > detail

    def _capture_expr(self, node, depth: int = 0) -> ExprNode:
        """EXPR-IR-1: structural capture of a scalar expression — one
        branch per GRAMMAR family; recursion handles depth, so no
        shape is ever enumerated. An unknown family becomes
        kind='unknown' (the renderer's counted outcome), never
        dropped — the conservation law at expression grain."""
        if node is None:
            return ExprNode("unknown", "")
        if depth > self._CAPTURE_LIMIT:
            return ExprNode("unknown", _verbatim(node)[:160])
        tn = _type_name(node)
        try:
            if tn == "ColumnReferenceExpression":
                names = self._column_names(node)
                return ExprNode(
                    "column", names[0] if names else _verbatim(node)[:80])
            if tn == "StringLiteral":
                return ExprNode("literal", f"'{node.Value}'")
            if tn == "NullLiteral":
                return ExprNode("literal", "NULL")
            if tn.endswith("Literal"):
                return ExprNode("literal", str(node.Value))
            if tn == "VariableReference":
                return ExprNode("variable", str(node.Name))
            if tn == "FunctionCall":
                name = str(node.FunctionName.Value).upper()
                distinct = str(getattr(node, "UniqueRowFilter",
                                       "")) == "Distinct"
                kids = [self._capture_expr(p, depth + 1)
                        for p in list(node.Parameters or [])]
                return ExprNode("function", name, distinct, kids)
            if tn in ("LeftFunctionCall", "RightFunctionCall"):
                kids = [self._capture_expr(p, depth + 1)
                        for p in list(node.Parameters or [])]
                return ExprNode("function",
                                tn[:-len("FunctionCall")].upper(),
                                False, kids)
            if tn == "CoalesceExpression":
                kids = [self._capture_expr(p, depth + 1)
                        for p in list(node.Expressions or [])]
                return ExprNode("function", "COALESCE", False, kids)
            if tn == "NullIfExpression":
                return ExprNode("function", "NULLIF", False, [
                    self._capture_expr(node.FirstExpression, depth + 1),
                    self._capture_expr(node.SecondExpression, depth + 1)])
            if tn == "BinaryExpression":
                sym = _ARITH_SYMBOLS.get(
                    str(node.BinaryExpressionType), "?")
                return ExprNode("arithmetic", sym, False, [
                    self._capture_expr(node.FirstExpression, depth + 1),
                    self._capture_expr(node.SecondExpression, depth + 1)])
            if tn == "UnaryExpression":
                sym = {"Negative": "-", "Positive": "+"}.get(
                    str(node.UnaryExpressionType), "?")
                return ExprNode("unary", sym, False, [
                    self._capture_expr(node.Expression, depth + 1)])
            if tn == "ParenthesisExpression":
                return self._capture_expr(node.Expression, depth)
            if tn in ("CastCall", "TryCastCall", "ConvertCall",
                      "TryConvertCall"):
                inner = getattr(node, "Parameter", None)
                return ExprNode("cast", "", False,
                                [self._capture_expr(inner, depth + 1)])
            if tn.endswith("CaseExpression"):
                return ExprNode("case", _verbatim(node)[:160])
            if tn == "ScalarSubquery":
                return ExprNode("subquery", "")
        except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
            self.suppressed += 1
            return ExprNode("unknown", "")
        return ExprNode("unknown", _verbatim(node)[:160])

    def _principal_func(self, side) -> "tuple[str | None, bool]":
        """Function name (+ DISTINCT flag) when the principal side is a
        function call — the structured fact leaf voicing needs
        (DESC-LEAF-1: COUNT(x) >= 4 must voice the counted entity, and
        the name must come from the parse, never from text)."""
        if side is None or _type_name(side) != "FunctionCall":
            return None, False
        try:
            name = str(side.FunctionName.Value).upper()
        except Exception:  # noqa: BLE001 — .NET reflection; counted via suppressed
            self.suppressed += 1
            return None, False
        distinct = False
        try:
            distinct = str(side.UniqueRowFilter) == "Distinct"
        except Exception:  # noqa: BLE001 — property absent on some node versions
            self.suppressed += 1
        return name, distinct

    def _leaf(self, node, context: str, path: str, op: str,
              principal_side=None, sides=None) -> DecisionNode:
        self.tree.decision_sites_total += 1
        self.tree.handled_count += 1
        columns = self._column_names(node)
        operands = self._operands(node)
        # Trivial tautologies (WHERE 1=1 scaffolding) are extracted and
        # counted but carry no decision content — not voice-worthy, not
        # part of the round-trip meaning (live find 2026-08-20).
        trivial = (op == "EQ" and not columns and len(set(operands)) <= 1)
        func, distinct = self._principal_func(principal_side)
        # EXPR-IR-1: capture the sides we are already standing on —
        # role-ordered (subject first), full depth, one walk.
        capture = sides if sides is not None else (
            [principal_side] if principal_side is not None else [])
        exprs = [self._capture_expr(s) for s in capture if s is not None]
        return DecisionNode(
            node_id=path, kind="predicate", op=op, context=context,
            expression_sql=_verbatim(node),
            column=self._principal_column(principal_side),
            func=func, func_distinct=distinct,
            exprs=exprs,
            columns=columns,
            operands=operands,
            must_voice=not trivial)

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
                    expression_sql=_verbatim(node)[:4000]))
                return None
            return self._leaf(node, context, path, op,
                              principal_side=node.FirstExpression,
                              sides=[node.FirstExpression,
                                     node.SecondExpression])

        if tn == "InPredicate":
            op = "NOT_IN" if node.NotDefined else "IN"
            return self._leaf(node, context, path, op,
                              principal_side=node.Expression,
                              sides=[node.Expression])

        if tn == "BooleanTernaryExpression":
            # ScriptDom's BETWEEN: TernaryExpressionType Between/NotBetween
            # (live find 2026-08-19: 22 arrival-window filters — including
            # Base_Pop's ONE true filter — landed unmodeled until this).
            kind = str(node.TernaryExpressionType)
            if kind in ("Between", "NotBetween"):
                op = "BETWEEN" if kind == "Between" else "NOT_BETWEEN"
                return self._leaf(node, context, path, op,
                                  principal_side=node.FirstExpression,
                                  sides=[node.FirstExpression,
                                         node.SecondExpression,
                                         node.ThirdExpression])
            self.tree.decision_sites_total += 1
            self.tree.unextracted.append(UnextractedSite(
                site_id=path, context=context,
                reason_code=f"unmodeled_construct:Ternary.{kind}",
                expression_sql=_verbatim(node)[:4000]))
            return None

        if tn == "LikePredicate":
            op = "NOT_LIKE" if node.NotDefined else "LIKE"
            return self._leaf(node, context, path, op,
                              principal_side=node.FirstExpression,
                              sides=[node.FirstExpression])

        if tn == "BooleanIsNullExpression":
            op = "IS_NOT" if node.IsNot else "IS"
            return self._leaf(node, context, path, op,
                              principal_side=node.Expression,
                              sides=[node.Expression])

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
            expression_sql=_verbatim(node)[:4000]))
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
                    site_id=site_id, context="parameter_default", root=leaf,
                    scope=self._scope()))
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
                        site_id=site_id, context="case_when", root=leaf,
                        scope=self._scope()))
            except Exception:  # noqa: BLE001 — .NET reflection; counted, escalated
                self.add_unextracted("case_when", "reflection_suppressed",
                                     _verbatim(node))

        nested = tn in ("QueryDerivedTable", "ScalarSubquery")
        if nested:
            self.sub_depth += 1
        try:
            for child in self._children(node):
                self.walk_statement(child, depth + 1)
        finally:
            if nested:
                self.sub_depth -= 1


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


def tree_content_hash(tree: "DecisionTree",
                      dict_lines: "list[str] | None" = None) -> str:
    """Cache identity for anything generated FROM a tree (spec's
    version-binding meta-clause): TREE_CONTRACT_VERSION is read at call
    time so tightening the contract regenerates everything it governs."""
    import hashlib

    import src.tree as _tree_pkg
    payload = (
        _tree_pkg.TREE_CONTRACT_VERSION + "\n"
        + "\n".join(sorted(n.expression_sql for n in tree.nodes
                           if n.kind == "predicate"))
        + "\n--unextracted--\n"
        + "\n".join(sorted(u.reason_code for u in tree.unextracted))
        + "\n--dict--\n" + "\n".join(dict_lines or [])
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


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

# --- query shape (GATE-RECUT, 2026-09-02) ---------------------------
# The gate's SQL-side evidence, parser-native — the composer's cut
# (DESC-SKELETON-3) applied to the checker. Outcome vocabulary is
# CLOSED (spec:G4 discipline): parse_ok False ⇒ every field empty ⇒
# callers' standing law applies (absence of evidence refuses no
# claim) and the failure is visible on the shape — no silent third
# state, no regex fallback.



@dataclass(frozen=True)
class QueryShape:
    parse_ok: bool
    base_tables: "frozenset[str]"      # named refs (any scope, '#'
                                       # kept) minus self-defined CTEs
    own_ctes: "frozenset[str]"
    select_cols: "tuple[str, ...]"     # OUTER select list columns
    key_cols: "tuple[str, ...]"        # OUTER DISTINCT/GROUP BY cols
    deciding_exprs: "tuple[str, ...]"  # OUTER-scope site expressions
    deciding_cols: "frozenset[str]"    # columns those sites touch


_EMPTY_SHAPE = QueryShape(False, frozenset(), frozenset(), (), (), (),
                          frozenset())

_SUBSCOPE_TYPES = ("QueryDerivedTable", "ScalarSubquery")


def _last_identifier(node) -> "str | None":
    try:
        ids = node.MultiPartIdentifier.Identifiers
        return ids[ids.Count - 1].Value
    except Exception:  # noqa: BLE001 — .NET reflection
        return None


@lru_cache(maxsize=512)
def query_shape(fragment: str) -> QueryShape:
    try:
        tree = build_decision_tree(fragment or "")
        parsed, errors = parse_tsql(
            normalize_sql_whitespace(fragment or ""))
        if errors:
            return _EMPTY_SHAPE
    except Exception:  # noqa: BLE001 — closed outcome: parse_ok False
        return _EMPTY_SHAPE

    tables: "set[str]" = set()
    ctes: "set[str]" = set()
    select_cols: "list[str]" = []
    key_cols: "list[str]" = []

    def walk(node, sub: int, depth: int = 0) -> None:
        if node is None or depth > 60:
            return
        tn = _type_name(node)
        if tn == "NamedTableReference":
            try:
                tables.add(node.SchemaObject.BaseIdentifier.Value)
            except Exception:  # noqa: BLE001, S110 — reflection
                pass           # miss = no evidence, by design
        elif tn == "CommonTableExpression":
            try:
                ctes.add(node.ExpressionName.Value)
            except Exception:  # noqa: BLE001, S110 — reflection
                pass           # miss = no evidence, by design
        elif tn == "QuerySpecification" and sub == 0:
            try:
                if (node.UniqueRowFilter is not None
                        and "Distinct" in str(node.UniqueRowFilter)):
                    for i in range(node.SelectElements.Count):
                        col = _select_col(node.SelectElements[i])
                        if col:
                            key_cols.append(col)
            except Exception:  # noqa: BLE001, S110 — reflection
                pass           # miss = no evidence, by design
        elif tn == "SelectScalarExpression" and sub == 0:
            expr = getattr(node, "Expression", None)
            col = (_last_identifier(expr)
                   if _type_name(expr) == "ColumnReferenceExpression"
                   else None)
            if col:
                select_cols.append(col)
        elif tn == "ExpressionGroupingSpecification" and sub == 0:
            expr = getattr(node, "Expression", None)
            if _type_name(expr) == "ColumnReferenceExpression":
                col = _last_identifier(expr)
                if col:
                    key_cols.append(col)
        bump = 1 if tn in _SUBSCOPE_TYPES else 0
        for child in _shape_children(node):
            walk(child, sub + bump, depth + 1)

    def _select_col(el):
        expr = getattr(el, "Expression", None)
        if _type_name(expr) == "ColumnReferenceExpression":
            return _last_identifier(expr)
        return None

    for b in range(parsed.Batches.Count):
        for s in range(parsed.Batches[b].Statements.Count):
            walk(parsed.Batches[b].Statements[s], 0)

    outer_sites = [s for s in tree.sites if s.scope == "outer"]
    deciding_cols = frozenset(
        c.split(".")[-1].upper()
        for site in outer_sites
        for n in _flatten(site.root) for c in n.columns if c)
    return QueryShape(
        parse_ok=True,
        base_tables=frozenset(t for t in tables
                              if t.upper() not in
                              {c.upper() for c in ctes}),
        own_ctes=frozenset(ctes),
        select_cols=tuple(select_cols),
        key_cols=tuple(key_cols),
        deciding_exprs=tuple(s.root.expression_sql for s in outer_sites),
        deciding_cols=deciding_cols,
    )


_shape_children = None  # bound below to the extractor's reflection walk


def _bind_shape_children():
    global _shape_children
    ex = _Extractor(DecisionTree(fragment=""))
    _shape_children = ex._children


_bind_shape_children()

