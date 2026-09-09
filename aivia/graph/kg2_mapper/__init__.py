"""KG layer 2's ONE writer — the mapper (one tree per SQL file).

Parser authority (CHECK-KG2-1): this package is the only home of
parser machinery — ScriptDom via the ported loader, no fallback
grammar (ADR 0001). The mapper walks the native AST into the ratified
kind library: kinds name meanings, never syntax; negated syntax
normalizes to structural NOT over the positive kind (R1); parentheses
shape the tree and dissolve; no kind -> COUNTED remainder with the
ScriptDom type named (conservation: handled u remainder = total).

Evidence: every mapped node carries its verbatim fragment + location
against the door-1-redacted text (H6: verbatim-after-redaction).
Scope identity follows the ratified Scope_Identity sheet: named scopes
key file::name (dupes file::name#i), the single result-set emitter
keys file::delivery (A11), unnamed scopes take no name_key (A4).
"""
import bisect
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aivia.graph import metamodel, phi_gate
from aivia.graph.kg2_mapper.scriptdom_loader import parse_tsql
from aivia.graph.store import Store

# Phase A (ADR 0077): trees stamp the metamodel version they were
# mapped under — the bump IS the re-parse trigger (a stamped tree
# under an old version differs from its re-map, so apply_file's
# idempotence check regenerates it; nothing improvises).
METAMODEL_VERSION = metamodel.load("kg2_kind_library").version

# literal: schema-mirror kg2_kind_library (values; keys ScriptDom)
COMPARISON_KINDS = {
    "Equals": "COMPARE_EQ",
    "NotEqualToBrackets": "COMPARE_NEQ",
    "NotEqualToExclamation": "COMPARE_NEQ",
    "GreaterThan": "COMPARE_GT",
    "GreaterThanOrEqualTo": "COMPARE_GTE",
    "NotLessThan": "COMPARE_GTE",
    "LessThan": "COMPARE_LT",
    "LessThanOrEqualTo": "COMPARE_LTE",
    "NotGreaterThan": "COMPARE_LTE",
}


class UnsupportedDialect(Exception):
    pass


@dataclass
class MapContext:
    text: str
    remainder: List[Dict[str, Any]] = field(default_factory=list)


def _evidence(ctx: MapContext, frag) -> Dict[str, Any]:
    start = frag.StartOffset
    # literal: shape
    return {"fragment": ctx.text[start:start + frag.FragmentLength],
            "offset": start, "line": frag.StartLine,
            "column": frag.StartColumn}


def _node(ctx, kind_family, kind, frag, **props) -> Dict[str, Any]:
    # literal: shape
    node = {"node": kind_family, "kind": kind,
            "evidence": _evidence(ctx, frag)}
    node.update({k: v for k, v in props.items() if v is not None})
    return node


def _type_name(frag) -> str:
    return frag.GetType().Name


# ---- expressions ----
def _map_expression(ctx, expr) -> Dict[str, Any]:
    t = _type_name(expr)
    if t == "ColumnReferenceExpression":
        parts = [i.Value for i in expr.MultiPartIdentifier.Identifiers]
        return _node(ctx, "expression", "column_ref", expr,
                     ref=".".join(parts))
    # literal: mechanical ScriptDom API names
    if t in ("IntegerLiteral", "NumericLiteral", "MoneyLiteral",
             "RealLiteral"):
        return _node(ctx, "expression", "literal", expr, value=expr.Value)
    if t == "StringLiteral":
        return _node(ctx, "expression", "literal", expr,
                     value=f"'{expr.Value}'")
    if t == "NullLiteral":
        return _node(ctx, "expression", "literal", expr, value="NULL")
    if t == "IdentifierLiteral":
        # a bare identifier used as a value token — DATEADD/DATEPART
        # dateparts (HH, DD ...); Phase C build find: these were the
        # whole 'unmapped expression construct' class in the corpus
        return _node(ctx, "expression", "literal", expr, value=expr.Value)
    if t == "VariableReference":
        return _node(ctx, "expression", "parameter_ref", expr, ref=expr.Name)
    if t == "FunctionCall":
        return _node(ctx, "expression", "function", expr,
                     name=expr.FunctionName.Value,
                     args=[_map_expression(ctx, p) for p in expr.Parameters],
                     # Phase A: an OVER clause marks a window function —
                     # a property, not a new expression kind (the
                     # Expression_Kinds set stays closed; RG-C3)
                     over=(True if expr.OverClause is not None else None))
    if t == "BinaryExpression":
        return _node(ctx, "expression", "arithmetic", expr,
                     args=[_map_expression(ctx, expr.FirstExpression),
                           _map_expression(ctx, expr.SecondExpression)])
    if t == "UnaryExpression":
        return _node(ctx, "expression", "unary", expr,
                     args=[_map_expression(ctx, expr.Expression)])
    # literal: mechanical ScriptDom API names
    if t in ("CastCall", "ConvertCall", "TryCastCall", "TryConvertCall"):
        return _node(ctx, "expression", "cast", expr,
                     args=[_map_expression(ctx, expr.Parameter)])
    if t in ("SearchedCaseExpression", "SimpleCaseExpression"):
        # the CASE kind (declared in Expression_Kinds since v1.0.0;
        # 424 corpus instances were remainder until the 2026-09-06
        # plug-all-holes sweep). Searched: WHEN <predicate> THEN
        # <expr>; Simple: CASE <input> WHEN <expr> THEN <expr>.
        whens = []
        for w in expr.WhenClauses:
            when_t = _type_name(w.WhenExpression)
            when = (_map_predicate(ctx, w.WhenExpression)
                    if when_t.startswith("Boolean")
                    or when_t.endswith("Predicate")
                    else _map_expression(ctx, w.WhenExpression))
            whens.append({"when": when,
                          "then": _map_expression(ctx, w.ThenExpression)})
        return _node(ctx, "expression", "case", expr,
                     input=(_map_expression(ctx, expr.InputExpression)
                            if t == "SimpleCaseExpression" else None),
                     whens=whens,
                     else_result=(_map_expression(ctx, expr.ElseExpression)
                                  if expr.ElseExpression else None))
    if t == "CoalesceExpression":
        return _node(ctx, "expression", "function", expr, name="COALESCE",
                     args=[_map_expression(ctx, p)
                           for p in expr.Expressions])
    if t == "NullIfExpression":
        return _node(ctx, "expression", "function", expr, name="NULLIF",
                     args=[_map_expression(ctx, expr.FirstExpression),
                           _map_expression(ctx, expr.SecondExpression)])
    if t in ("LeftFunctionCall", "RightFunctionCall"):
        return _node(ctx, "expression", "function", expr,
                     name=t[:-12].upper(),
                     args=[_map_expression(ctx, p)
                           for p in expr.Parameters])
    if t == "ParameterlessCall":
        return _node(ctx, "expression", "function", expr,
                     name=str(expr.ParameterlessCallType).upper(), args=[])
    if t == "ScalarSubquery":
        # the interior maps as a full scope (plug-all-holes sweep:
        # tables read ONLY inside subqueries were invisible to the
        # working set — a lineage-truth hole)
        return _node(ctx, "expression", "subquery_ref", expr,
                     scope=_map_query(ctx, expr.QueryExpression))
    if t == "ParenthesisExpression":
        return _map_expression(ctx, expr.Expression)
    ctx.remainder.append({"type": t, **_evidence(ctx, expr),
                          "reason": "unmapped expression construct"})
    return _node(ctx, "expression", "remainder_ref", expr)


def _wrap_not(ctx, frag, inner, negated) -> Dict[str, Any]:
    if not negated:
        return inner
    return _node(ctx, "structure", "NOT", frag, children=[inner])


# ---- predicates (the kind library's closed set) ----
def _map_predicate(ctx, cond) -> Dict[str, Any]:
    t = _type_name(cond)
    if t == "BooleanParenthesisExpression":
        return _map_predicate(ctx, cond.Expression)  # dissolves
    if t == "BooleanBinaryExpression":
        kind = str(cond.BinaryExpressionType).upper()  # AND | OR
        children = []
        for side in (cond.FirstExpression, cond.SecondExpression):
            child = _map_predicate(ctx, side)
            if child["kind"] == kind and child["node"] == "structure":
                children.extend(child["children"])  # flatten same-op chain
            else:
                children.append(child)
        return _node(ctx, "structure", kind, cond, children=children)
    if t == "BooleanNotExpression":
        return _node(ctx, "structure", "NOT", cond,
                     children=[_map_predicate(ctx, cond.Expression)])
    if t == "BooleanComparisonExpression":
        kind = COMPARISON_KINDS.get(str(cond.ComparisonType))
        if kind is None:
            ctx.remainder.append({"type": f"{t}:{cond.ComparisonType}",
                                  **_evidence(ctx, cond),
                                  "reason": "deferred comparison syntax"})
            return _node(ctx, "predicate", "remainder", cond)
        return _node(ctx, "predicate", kind, cond,
                     subject=_map_expression(ctx, cond.FirstExpression),
                     comparand=_map_expression(ctx, cond.SecondExpression))
    if t == "LikePredicate":
        inner = _node(ctx, "predicate", "PATTERN_MATCH", cond,
                      subject=_map_expression(ctx, cond.FirstExpression),
                      pattern=_map_expression(ctx, cond.SecondExpression),
                      escape=(_map_expression(ctx, cond.EscapeExpression)
                              if cond.EscapeExpression else None))
        return _wrap_not(ctx, cond, inner, cond.NotDefined)
    if t == "InPredicate":
        if cond.Subquery is not None:
            inner = _node(ctx, "predicate", "IN_SELECTION", cond,
                          subject=_map_expression(ctx, cond.Expression),
                          selection=_node(
                              ctx, "expression", "subquery_ref",
                              cond.Subquery,
                              scope=_map_query(
                                  ctx, cond.Subquery.QueryExpression)))
        else:
            members = [dict(_map_expression(ctx, v), position=i + 1)
                       for i, v in enumerate(cond.Values)]
            inner = _node(ctx, "predicate", "IN_LIST", cond,
                          subject=_map_expression(ctx, cond.Expression),
                          comparand_list=members)
        return _wrap_not(ctx, cond, inner, cond.NotDefined)
    if t == "BooleanTernaryExpression":
        negated = "Not" in str(cond.TernaryExpressionType)
        inner = _node(ctx, "predicate", "RANGE", cond,
                      subject=_map_expression(ctx, cond.FirstExpression),
                      lower_bound=_map_expression(ctx, cond.SecondExpression),
                      upper_bound=_map_expression(ctx, cond.ThirdExpression))
        return _wrap_not(ctx, cond, inner, negated)
    if t == "BooleanIsNullExpression":
        inner = _node(ctx, "predicate", "NULL_CHECK", cond,
                      subject=_map_expression(ctx, cond.Expression))
        return _wrap_not(ctx, cond, inner, cond.IsNot)
    if t == "ExistsPredicate":
        return _node(ctx, "predicate", "EXISTS_SELECTION", cond,
                     selection=_node(
                         ctx, "expression", "subquery_ref", cond.Subquery,
                         scope=_map_query(ctx,
                                          cond.Subquery.QueryExpression)))
    if t == "SubqueryComparisonPredicate":
        return _node(ctx, "predicate", "QUANTIFIED_COMPARE", cond,
                     subject=_map_expression(ctx, cond.Expression),
                     comparison_op=str(cond.ComparisonType),
                     quantifier=str(cond.SubqueryComparisonPredicateType),
                     selection=_node(
                         ctx, "expression", "subquery_ref", cond.Subquery,
                         scope=_map_query(ctx,
                                          cond.Subquery.QueryExpression)))
    ctx.remainder.append({"type": t, **_evidence(ctx, cond),
                          "reason": "unmapped boolean construct — "
                          "deferred or new vendor syntax"})
    return _node(ctx, "predicate", "remainder", cond)


# ---- scopes ----
def _table_name(schema_object) -> str:
    return ".".join(i.Value for i in schema_object.Identifiers)


def _collect_from(ctx, table_ref, refs, join_on):
    t = _type_name(table_ref)
    if t == "NamedTableReference":
        # literal: shape
        refs.append({
            "table_ref": _table_name(table_ref.SchemaObject),
            "alias": table_ref.Alias.Value if table_ref.Alias else None,
            "evidence": _evidence(ctx, table_ref)})
    elif t == "QualifiedJoin":
        _collect_from(ctx, table_ref.FirstTableReference, refs, join_on)
        _collect_from(ctx, table_ref.SecondTableReference, refs, join_on)
        on_pred = _map_predicate(ctx, table_ref.SearchCondition)
        on_pred["join_type"] = str(table_ref.QualifiedJoinType)
        join_on.append(on_pred)
    elif t == "UnqualifiedJoin":
        # the comma join (FROM A, B) — Clarity-era style; 61 corpus
        # reads were invisible to from_refs until the ABX sweep found
        # the class (2026-09-06). No ON clause: the link lives in the
        # WHERE as col=col keys, already structure by the v1.3.0 law.
        # OUTER APPLY's right side is an OPTIONAL lookup — rows
        # survive without a match — so its refs carry the marker the
        # v1.3.0 inner/outer law needs downstream.
        _collect_from(ctx, table_ref.FirstTableReference, refs, join_on)
        before = len(refs)
        _collect_from(ctx, table_ref.SecondTableReference, refs, join_on)
        if str(table_ref.UnqualifiedJoinType) == "OuterApply":
            for ref in refs[before:]:
                ref["outer_apply"] = True
    elif t == "QueryDerivedTable":
        # literal: shape
        refs.append({
            "derived_scope": _map_query(ctx, table_ref.QueryExpression),
            "alias": table_ref.Alias.Value if table_ref.Alias else None,
            "evidence": _evidence(ctx, table_ref)})
    elif t == "PivotedTableReference":
        # ledger-close (2026-09-06): the pivot TRANSFORM maps — the
        # aggregate, the pivot column, and the in-values (which become
        # the output columns) are captured; reads recurse as before
        before = len(refs)
        _collect_from(ctx, table_ref.TableReference, refs, join_on)
        # literal: shape
        pivot = {
            "aggregate": (table_ref.AggregateFunctionIdentifier
                          .Identifiers[0].Value
                          if table_ref.AggregateFunctionIdentifier
                          else None),
            "pivot_column": (_map_expression(ctx, table_ref.PivotColumn)
                             if table_ref.PivotColumn is not None
                             else None),
            "in_values": [i.Value for i in table_ref.InColumns],
            "alias": (table_ref.Alias.Value if table_ref.Alias
                      else None)}
        for ref in refs[before:]:
            ref["pivot"] = pivot
    else:
        ctx.remainder.append({"type": t, **_evidence(ctx, table_ref),
                              "reason": "unmapped table reference"})


def _column_refs_in(node) -> List[Dict[str, Any]]:
    out = []
    if isinstance(node, dict):
        if node.get("kind") == "column_ref":
            out.append(node)
        for v in node.values():
            out.extend(_column_refs_in(v))
    elif isinstance(node, list):
        for v in node:
            out.extend(_column_refs_in(v))
    return out


def _map_query(ctx, query) -> Dict[str, Any]:
    """One QuerySpecification -> one scope dict (unnamed here; naming
    is the statement walk's duty per the Scope_Identity sheet)."""
    t = _type_name(query)
    if t == "QueryParenthesisExpression":
        return _map_query(ctx, query.QueryExpression)
    if t == "BinaryQueryExpression":
        # UNION/EXCEPT/INTERSECT — the COMBINATION structure (Sunny's
        # ABX corpse, 2026-09-06: the old walk counted the shape but
        # returned an EMPTY scope, and the floor read 'no sources' as
        # 'no source records are read' — a counted gap laundered into
        # a false claim). Arms map as full scopes; nested combinations
        # flatten in order.
        arms = []
        for side in (query.FirstQueryExpression,
                     query.SecondQueryExpression):
            arm = _map_query(ctx, side)
            if arm.get("combination") == str(query.BinaryQueryExpressionType) \
                    and arm.get("combination_all") == bool(query.All):
                arms.extend(arm["combination_arms"])
            else:
                arms.append(arm)
        # literal: shape
        return {"node": "scope", "structures": ["COMBINATION"],
                "combination": str(query.BinaryQueryExpressionType),
                "combination_all": bool(query.All),
                "combination_arms": arms,
                "evidence": _evidence(ctx, query)}
    if t != "QuerySpecification":
        ctx.remainder.append({"type": t, **_evidence(ctx, query),
                              "reason": "unmapped query shape"})
        # literal: shape
        return {"node": "scope", "structures": [], "unmapped_shape": t,
                "evidence": _evidence(ctx, query)}
    refs, join_on = [], []
    if query.FromClause:
        for tr in query.FromClause.TableReferences:
            _collect_from(ctx, tr, refs, join_on)
    where = (_map_predicate(ctx, query.WhereClause.SearchCondition)
             if query.WhereClause else None)
    # Phase A (ADR 0077, A12 un-deferral): the SELECT list is a
    # PROJECTION structure — one member per output column (name +
    # expression subtree, position-ordered). Non-scalar elements were
    # previously SKIPPED SILENTLY; conservation now counts them: a
    # star is a counted remainder until star expansion is ruled.
    projection = []
    for i, el in enumerate(query.SelectElements):
        et = _type_name(el)
        if et == "SelectScalarExpression":
            expr = _map_expression(ctx, el.Expression)
            if el.ColumnName is not None:
                name = el.ColumnName.Value
            elif expr["kind"] == "column_ref":
                name = expr["ref"].rsplit(".", 1)[-1]
            else:
                name = None  # anonymous output column — legal T-SQL
            # literal: shape
            projection.append({"node": "projection_member",
                               "position": i + 1, "name": name,
                               "expression": expr,
                               "evidence": _evidence(ctx, el)})
        elif et == "SelectStarExpression":
            # RESOLVED 2026-09-06 (plug-all-holes sweep): a star's
            # MEANING is 'every column of the source at read time' —
            # meaning without enumeration, drift-safe by construction
            # (an enumerated expansion would freeze a column list the
            # source can outgrow). No longer a counted gap.
            qualifier = (".".join(i.Value for i in
                                  el.Qualifier.Identifiers)
                         if el.Qualifier else None)
            # literal: shape
            projection.append({"node": "projection_member",
                               "position": i + 1, "name": None,
                               "star": True, "qualifier": qualifier,
                               # literal: shape
                               "expression": {"node": "expression",
                                              "kind": "star",
                                              "evidence":
                                              _evidence(ctx, el)},
                               "evidence": _evidence(ctx, el)})
        else:
            ctx.remainder.append({"type": et, **_evidence(ctx, el),
                                  "reason": "unmapped select element"})
    # select_refs alias the member expressions (same dicts) so the
    # resolver annotates projection subtrees like everything else
    select_refs = [m["expression"] for m in projection]
    structures = []
    if refs:
        structures.append("FROM")
    if join_on:
        structures.append("JOIN")
    if where is not None:
        structures.append("WHERE")
    if query.GroupByClause:
        structures.append("GROUP BY")
    if query.OrderByClause:
        structures.append("ORDER BY")
    if projection:
        structures.append("PROJECTION")
    # literal: shape
    return {"node": "scope", "structures": structures, "from_refs": refs,
            "join_on": join_on, "where": where, "select_refs": select_refs,
            "projection": projection, "evidence": _evidence(ctx, query)}


# ---- statements & the file tree ----
def _param_default(ctx, stmt) -> Optional[Dict[str, Any]]:
    """The parameter-default pattern, STRUCTURAL: IF <param IS NULL>
    SET <same param> = <literal> (never a pseudo-op)."""
    pred = _map_predicate(ctx, stmt.Predicate)
    then = stmt.ThenStatement
    if pred["kind"] != "NULL_CHECK" or _type_name(then) != "SetVariableStatement":
        return None
    subject = pred.get("subject", {})
    if subject.get("kind") != "parameter_ref" \
            or subject.get("ref") != then.Variable.Name:
        return None
    default = _map_expression(ctx, then.Expression)
    return {"name": then.Variable.Name.lstrip("@"),
            "default_logic": default["evidence"]["fragment"]}


def map_tree(file_name: str, text: str, dialect: str = "tsql"
             ) -> Dict[str, Any]:
    if dialect != "tsql":
        raise UnsupportedDialect(dialect)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    fragment, errors = parse_tsql(text)
    if errors:
        raise ValueError(f"T-SQL parse errors ({len(errors)}): "
                         + " | ".join(errors[:3]))
    ctx = MapContext(text=text)
    statements: List[Dict[str, Any]] = []
    parameters: Dict[str, Dict[str, Any]] = {}
    position = 0

    def executable_statements(stmts):
        """Wrapper statements NEST their bodies (registry: control-flow
        blocks nest statements): CREATE PROCEDURE and BEGIN/END unwrap
        to their executable children, in order."""
        for stmt in stmts:
            t = _type_name(stmt)
            if t == "CreateProcedureStatement":
                yield from executable_statements(
                    stmt.StatementList.Statements)
            elif t in ("BeginEndBlockStatement", "BeginEndBlock"):
                yield from executable_statements(
                    stmt.StatementList.Statements)
            else:
                yield stmt

    def process(stmt):
        nonlocal position
        position += 1
        t = _type_name(stmt)
        entry: Dict[str, Any] = {"position": position,
                                 "evidence": _evidence(ctx, stmt)}
        if t == "IfStatement":
            entry["statement_kind"] = "IF"
            entry["predicate"] = _map_predicate(ctx, stmt.Predicate)
            param = _param_default(ctx, stmt)
            if param:
                parameters[param["name"]] = param
        elif t == "SelectStatement":
            scope = _map_query(ctx, stmt.QueryExpression)
            # CTEs: each mints a NAMED scope in the same tree
            ctes = []
            if stmt.WithCtesAndXmlNamespaces:
                for cte in stmt.WithCtesAndXmlNamespaces.CommonTableExpressions:
                    inner = _map_query(ctx, cte.QueryExpression)
                    inner["name"] = cte.ExpressionName.Value
                    ctes.append(inner)
            if stmt.Into is not None:
                scope["name"] = _table_name(stmt.Into)
                entry["statement_kind"] = "SELECT INTO"
            else:
                entry["statement_kind"] = "SELECT"
                entry["emits"] = True
            entry["scope"] = scope
            if ctes:
                entry["ctes"] = ctes
        elif t == "InsertStatement":
            # plug-all-holes sweep (2026-09-06): INSERT is a
            # population WRITE — its source selection maps as a scope
            # NAMED for the write target (the SELECT INTO pattern), so
            # downstream reads of the target resolve through it
            spec = stmt.InsertSpecification
            src = spec.InsertSource
            if _type_name(src) == "SelectInsertSource":
                scope = _map_query(ctx, src.Select)
                scope["name"] = _table_name(spec.Target.SchemaObject)
                names = [list(c.MultiPartIdentifier.Identifiers)[-1].Value
                         for c in spec.Columns]
                if names and len(names) == len(scope.get("projection",
                                                         [])):
                    # explicit column list names the TARGET columns —
                    # they override the source expressions' names
                    for member, name in zip(scope["projection"], names):
                        member["name"] = name
                entry["statement_kind"] = "INSERT"
                entry["scope"] = scope
            else:
                entry["statement_kind"] = "INSERT"
                ctx.remainder.append(
                    {"type": f"InsertStatement:{_type_name(src)}",
                     **_evidence(ctx, stmt),
                     "reason": "unmapped insert source"})
        elif t == "WhileStatement":
            # control flow nests statements: the WHILE entry carries
            # its predicate; the body's statements process in order
            entry["statement_kind"] = "WHILE"
            entry["predicate"] = _map_predicate(ctx, stmt.Predicate)
            statements.append(entry)
            for inner in executable_statements([stmt.Statement]):
                process(inner)
            return
        elif t == "DeleteStatement":
            # ledger-close (2026-09-06): DELETE shapes a population by
            # REMOVAL — target read + conditions map as a scope with
            # the operation marked; the grammar voices removal, never
            # 'a selection'
            spec = stmt.DeleteSpecification
            if _type_name(spec.Target) == "NamedTableReference":
                target_name = _table_name(spec.Target.SchemaObject)
                # literal: shape
                scope = {"node": "scope", "operation": "delete",
                         "name": target_name,
                         "structures": ["FROM"]
                         + (["WHERE"] if spec.WhereClause else []),
                         # literal: shape
                         "from_refs": [{
                             "table_ref": target_name,
                             "alias": None,
                             "evidence": _evidence(ctx, spec.Target)}],
                         "join_on": [],
                         "where": (_map_predicate(
                             ctx, spec.WhereClause.SearchCondition)
                             if spec.WhereClause else None),
                         "projection": [],
                         "select_refs": [],
                         "evidence": _evidence(ctx, stmt)}
                entry["statement_kind"] = "DELETE"
                entry["scope"] = scope
            else:
                entry["statement_kind"] = "DELETE"
                ctx.remainder.append(
                    {"type": f"DeleteStatement:{_type_name(spec.Target)}",
                     **_evidence(ctx, stmt),
                     "reason": "unmapped delete target"})
        elif t == "GoToStatement":
            # control flow: 'repeat from the label' — the loop meaning
            # is the jump itself, captured with its target
            entry["statement_kind"] = "GOTO"
            entry["label"] = stmt.LabelName.Value.rstrip(":")
        elif t == "LabelStatement":
            entry["statement_kind"] = "LABEL"
            entry["label"] = stmt.Value.rstrip(":")
        elif t == "SetVariableStatement":
            # value FLOW is meaning: @var carries logic into later
            # filters; the assignment is captured, never dropped
            entry["statement_kind"] = "SET"
            entry["parameter"] = stmt.Variable.Name.lstrip("@")
            entry["expression"] = _map_expression(ctx, stmt.Expression)
        else:
            entry["statement_kind"] = t
            ctx.remainder.append({"type": t, **_evidence(ctx, stmt),
                                  "reason": "unmapped statement kind"})
        statements.append(entry)

    for batch in fragment.Batches:
        for stmt in executable_statements(batch.Statements):
            process(stmt)

    # R8 annotations (grammar v1.2.0): a TRAILING SAME-LINE comment is
    # the predicate's (or IN-member's) annotation — verbatim estate
    # text, evidence-grade; the floor voices it WITH ATTRIBUTION only.
    lines = text.split("\n")
    line_starts = [0]
    for ln in lines[:-1]:
        line_starts.append(line_starts[-1] + len(ln) + 1)

    def trailing_comment(node):
        ev = node.get("evidence")
        if not ev:
            return None
        end = ev["offset"] + len(ev["fragment"])
        idx = bisect.bisect_right(line_starts, end - 1) - 1
        line = lines[idx]
        col = end - line_starts[idx]
        pos = line.find("--", col)
        if pos < 0:
            return None
        note = " ".join(line[pos + 2:].split()).strip()
        return note[:60] if note else None

    def annotate(node, pred_end_line=None):
        if isinstance(node, dict):
            if node.get("node") == "predicate":
                note = trailing_comment(node)
                if note:
                    node["annotation"] = note
                ev = node.get("evidence")
                end_line = None
                if ev:
                    end_line = bisect.bisect_right(
                        line_starts,
                        ev["offset"] + len(ev["fragment"]) - 1) - 1
                for member in node.get("comparand_list", []):
                    mev = member.get("evidence")
                    if not mev:
                        continue
                    m_line = bisect.bisect_right(
                        line_starts, mev["offset"] - 1) - 1
                    if m_line == end_line:
                        continue  # the predicate owns that line's note
                    note = trailing_comment(member)
                    if note:
                        member["annotation"] = note
            for v in node.values():
                annotate(v)
        elif isinstance(node, list):
            for v in node:
                annotate(v)
    annotate(statements)

    # Scope_Identity: name_key per A3 (#i on dupes) + A11 (::delivery)
    seen: Dict[str, int] = {}

    def name_key(name):
        seen[name] = seen.get(name, 0) + 1
        return (f"{file_name}::{name}" if seen[name] == 1
                else f"{file_name}::{name}#{seen[name]}")
    emitters = [s for s in statements if s.get("emits")]
    for stmt in statements:
        for cte in stmt.get("ctes", []):
            cte["name_key"] = name_key(cte["name"])
        scope = stmt.get("scope")
        if scope is None:
            continue
        if "name" in scope:
            scope["name_key"] = name_key(scope["name"])
        elif stmt.get("emits"):
            if len(emitters) == 1:
                scope["name_key"] = f"{file_name}::delivery"
            else:
                n = emitters.index(stmt) + 1
                scope["name_key"] = f"{file_name}::delivery_{n}"
    # literal: shape
    return {"node": "file", "name": file_name, "dialect": dialect,
            "metamodel_version": METAMODEL_VERSION,
            "statements": statements,
            "parameters": sorted(parameters.values(),
                                 key=lambda p: p["name"]),
            "remainder": ctx.remainder,
            "plural_emitters": len(emitters) > 1}


# ---- resolution (binds to KG1 identity, never version) ----
def _fold(name: str) -> str:
    """A2's match function: fold_upper(strip_brackets_quotes(x)) —
    SQL identifiers compare case-insensitively; identities keep their
    declared casing."""
    return name.strip("[]\"'").upper()


def resolve(tree: Dict[str, Any], store: Store, reg: Dict[str, Any],
            default_schema: Optional[str] = None) -> Dict[str, Any]:
    tables = {_fold(n.identity.rsplit("|", 1)[-1]) + "|" +
              "|".join(n.identity.split("|")[:2]): n.identity
              for n in store.current_nodes("table")}

    def table_identity(schema: str, table: str) -> Optional[str]:
        source = reg["schema_sources"].get(schema)
        return tables.get(f"{_fold(table)}|{source}|{schema}")
    columns = {n.identity for n in store.current_nodes("column")}
    folded_columns = {"|".join(c.split("|")[:3]) + "|" + _fold(
        c.rsplit("|", 1)[-1]): c for c in columns}
    scope_keys = {}
    for stmt in tree["statements"]:
        for cte in stmt.get("ctes", []):
            scope_keys[cte["name"]] = cte["name_key"]
        scope = stmt.get("scope")
        if scope and "name" in scope \
                and scope.get("operation") != "delete":
            # a DELETE scope is named for its TARGET but produces no
            # readable shape — registering it would hijack later
            # reads of the real table (ledger-close find)
            scope_keys[scope["name"]] = scope["name_key"]
    params = {p["name"] for p in tree["parameters"]}
    # literal: shape
    census = {"resolved_refs": 0, "same_tree_refs": 0,
              "unresolved_refs": 0, "unresolved": []}

    # named scopes' output shape (folded members + star sources), for
    # disambiguation, scope-member binding, and STAR-THROUGH
    # resolution (the star ruling: 'every column of the source at
    # read time' — resolution IS read time, so looking through a star
    # to the underlying table is lawful and drift-safe: recomputed
    # each run, never frozen). Combination scopes expose arm 1.
    scope_projections: Dict[str, Dict[str, Any]] = {}
    for stmt in tree["statements"]:
        for s in (list(stmt.get("ctes", []))
                  + ([stmt["scope"]] if stmt.get("scope") else [])):
            if "name_key" not in s:
                continue
            arms = s.get("combination_arms")
            shape = arms[0] if arms else s
            proj = shape.get("projection", [])
            scope_projections[s["name_key"]] = {
                "members": {_fold(m["name"]) for m in proj
                            if m.get("name")},
                "star_refs": ([r for r in shape.get("from_refs", [])]
                              if any(m.get("star") for m in proj)
                              else [])}

    def scope_declares(name_key: str, colname: str,
                       depth: int = 0) -> Optional[str]:
        """Does the named scope output this column? Returns the
        UNDERLYING KG1 column identity when a star lets us look
        through to a resolved table, 'member' for an explicit member,
        None otherwise. Depth-guarded; never guesses."""
        info = scope_projections.get(name_key)
        if info is None or depth > 4:
            return None
        if _fold(colname) in info["members"]:
            return "member"
        for ref in info["star_refs"]:
            rt = ref.get("resolves_to")
            if rt and not str(rt).startswith("SAME-TREE"):
                col_id = folded_columns.get(f"{rt}|{_fold(colname)}")
                if col_id:
                    return col_id
            elif rt:
                inner = scope_declares(
                    str(rt).replace("SAME-TREE scope ", ""),
                    colname, depth + 1)
                if inner:
                    return inner
        return None

    def _count_unresolved(ref, detail):
        census["unresolved_refs"] += 1
        census["unresolved"].append(ref)
        census.setdefault("unresolved_detail", []).append(detail)

    def _bind_column(col, kind, target, colname) -> None:
        if kind == "table":
            col_id = folded_columns.get(f"{target}|{_fold(colname)}")
            if col_id:
                col["resolves_to"] = col_id
                census["resolved_refs"] += 1
            else:
                col["resolves_to"] = None
                _count_unresolved(col["ref"],
                                  # literal: shape
                                  {"ref": col["ref"], "kind": "column",
                                   "table": target})
        elif kind == "scope":
            col["resolves_to"] = f"SAME-TREE scope {target}"
            census["same_tree_column_refs"] = \
                census.get("same_tree_column_refs", 0) + 1
        else:
            col["resolves_to"] = None
            census["ambiguous_unqualified"] = \
                census.get("ambiguous_unqualified", 0) + 1

    def _subquery_scopes_in(node):
        if isinstance(node, dict):
            if node.get("kind") == "subquery_ref" and "scope" in node:
                yield node["scope"]
            else:
                for v in node.values():
                    yield from _subquery_scopes_in(v)
        elif isinstance(node, list):
            for v in node:
                yield from _subquery_scopes_in(v)

    def resolve_scope(scope, outer=()):
        for arm in scope.get("combination_arms", []):
            resolve_scope(arm, outer)
        alias_to = {}
        for ref in scope.get("from_refs", []):
            if "derived_scope" in ref:
                resolve_scope(ref["derived_scope"],
                              (alias_to,) + tuple(outer))
                if ref.get("alias"):
                    # carry the scope OBJECT: its projection answers
                    # membership questions (ledger-close)
                    alias_to[_fold(ref["alias"])] = \
                        ("derived", ref["derived_scope"])
                continue
            name = ref["table_ref"]
            folded_scopes = {_fold(k): v for k, v in scope_keys.items()}
            if _fold(name) in folded_scopes:
                key = folded_scopes[_fold(name)]
                ref["resolves_to"] = f"SAME-TREE scope {key}"
                census["same_tree_refs"] += 1
                target = ("scope", key)
            else:
                if "." in name:
                    schema, table = name.rsplit(".", 1)
                elif default_schema:
                    # the estate's declared default schema (real estates
                    # reference unqualified names constantly)
                    schema, table = default_schema, name
                else:
                    schema, table = None, name
                identity = table_identity(schema, table) if schema else None
                if identity:
                    ref["resolves_to"] = identity
                    census["resolved_refs"] += 1
                    target = ("table", identity)
                else:
                    ref["resolves_to"] = None
                    census["unresolved_refs"] += 1
                    census["unresolved"].append(name)
                    census.setdefault("unresolved_detail", []).append(
                        # literal: shape
                        {"ref": name, "kind": "table",
                         "schema": schema or "(unqualified)"})
                    target = ("unresolved", None)
            if ref.get("alias"):
                alias_to[_fold(ref["alias"])] = target
            else:
                # no alias: the table's own name qualifies its columns
                # (ledger-close find: 287 '[#Temp].COL' refs unbound
                # because bare temp names were never registered)
                alias_to[_fold(name.rsplit(".", 1)[-1])] = target

        # subquery interiors resolve with THIS scope's aliases in
        # reach (correlated refs — plug-all-holes sweep 2026-09-06)
        for sub in _subquery_scopes_in([scope.get("where"),
                                        scope.get("join_on"),
                                        scope.get("select_refs")]):
            resolve_scope(sub, (alias_to,) + tuple(outer))

        def lookup_alias(alias):
            folded = _fold(alias)  # SQL aliases compare folded (A2)
            for frame in (alias_to,) + tuple(outer):
                if folded in frame:
                    return frame[folded]
            return None

        def derived_declares(scope_obj, colname) -> bool:
            arms = scope_obj.get("combination_arms")
            shape = arms[0] if arms else scope_obj
            proj = shape.get("projection", [])
            if any(_fold(m["name"]) == _fold(colname)
                   for m in proj if m.get("name")):
                return True
            if any(m.get("star") for m in proj):
                return True  # could carry it — wildcard, never certain
            return False

        # single-part refs: bind by SOLE source, else disambiguate by
        # COLUMN MEMBERSHIP — if exactly one source declares the
        # column, the binding is safe; 0 or 2+ stay counted
        # dedup by identity where hashable; derived targets (scope
        # dicts) dedup by object id
        targets, seen_t = [], set()
        for kt in alias_to.values():
            marker = (kt[0], id(kt[1]) if isinstance(kt[1], dict)
                      else kt[1])
            if marker not in seen_t:
                seen_t.add(marker)
                targets.append(kt)
        for col in _column_refs_in([scope.get("where"),
                                    scope.get("join_on"),
                                    scope.get("select_refs")]):
            if col.get("resolves_to") is not None:
                continue  # bound while resolving a subquery pass
            parts = col["ref"].split(".")
            if len(parts) == 1:
                colname = parts[0]
                candidates, wildcards = [], 0
                for kind, target in targets:
                    if kind == "table":
                        if folded_columns.get(
                                f"{target}|{_fold(colname)}"):
                            candidates.append(("table", target))
                    elif kind == "scope":
                        found = scope_declares(target, colname)
                        if found == "member":
                            candidates.append(("scope", target))
                        elif found:  # star-through KG1 identity
                            candidates.append(("column", found))
                        elif (scope_projections.get(target) or
                              {}).get("star_refs"):
                            wildcards += 1
                    elif kind == "derived":
                        if target is not None \
                                and derived_declares(target, colname):
                            candidates.append(("derived", target))
                        else:
                            wildcards += 1
                    else:  # unresolved table: members unknowable
                        wildcards += 1
                if len(candidates) == 1:
                    # unique holder — sound even beside wildcards: a
                    # second holder would make the estate's own SQL
                    # error ('ambiguous column name'), and the estate
                    # RUNS (the same assumption resolution stands on)
                    kind, target = candidates[0]
                    if kind == "column":
                        col["resolves_to"] = target
                        census["resolved_refs"] += 1
                    elif kind == "derived":
                        col["resolves_to"] = "DERIVED scope member"
                        census["resolved_derived"] = \
                            census.get("resolved_derived", 0) + 1
                    else:
                        _bind_column(col, kind, target, colname)
                elif not candidates and not wildcards and targets:
                    # every source known, NONE declares it — drift
                    col["resolves_to"] = None
                    _count_unresolved(col["ref"],
                                      # literal: shape
                                      {"ref": col["ref"],
                                       "kind": "column",
                                       "table": "(no source declares "
                                       "it)"})
                else:
                    col["resolves_to"] = None
                    census["ambiguous_unqualified"] = \
                        census.get("ambiguous_unqualified", 0) + 1
                continue
            if len(parts) == 2:
                bound = lookup_alias(parts[0])
                if bound is not None:
                    kind, target = bound
                    if kind == "scope":
                        found = scope_declares(target, parts[1])
                        if found and found != "member":
                            col["resolves_to"] = found  # star-through
                            census["resolved_refs"] += 1
                            continue
                    if kind == "derived":
                        col["resolves_to"] = "DERIVED scope member"
                        census["resolved_derived"] = \
                            census.get("resolved_derived", 0) + 1
                        continue
                    _bind_column(col, kind, target, parts[1])
                else:
                    # a qualifier naming no known source: counted,
                    # never silently skipped (the old walk's hole)
                    col["resolves_to"] = None
                    census["unbound_qualified"] = \
                        census.get("unbound_qualified", 0) + 1

    def walk_params(node):
        if isinstance(node, dict):
            if node.get("kind") == "parameter_ref":
                name = node.get("ref", "").lstrip("@")
                if name in params:
                    node["resolves_to"] = f"file parameter {name}"
                    census["resolved_refs"] += 1
            for v in node.values():
                walk_params(v)
        elif isinstance(node, list):
            for v in node:
                walk_params(v)

    for stmt in tree["statements"]:
        for cte in stmt.get("ctes", []):
            resolve_scope(cte)
        if stmt.get("scope"):
            resolve_scope(stmt["scope"])
    walk_params(tree["statements"])
    tree["resolution_census"] = census
    return tree


# ---- lifecycle ----
def record_exclusion(store: Store, file_name: str, reason: str,
                     as_of: str) -> None:
    """E5 conservation citizen: an unsupported-dialect file lands as a
    COUNTED exclusion in the graph — never parsed, never silent."""
    current = [n for n in store.current_nodes("excluded_file")
               if n.identity == file_name]
    if current and current[0].properties.get("reason") == reason:
        return
    # STEP 5 (the birth-edge law): an exclusion is deduced from the
    # estate's intake — it chains to the root like everything
    # intake-born
    dbs = store.current_nodes("db")
    props = {"reason": reason}
    if dbs:
        props["estate"] = dbs[0].identity
    store.append_node("excluded_file", file_name, props,
                      as_of, f"estate@{as_of}")


def apply_file(store: Store, reg: Dict[str, Any], file_id: str,
               file_name: str, text: str, as_of: str,
               dialect: str = "tsql",
               default_schema: Optional[str] = None,
               kg1_changed: Optional[set] = None) -> Dict[str, Any]:
    import hashlib
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    current = [n for n in store.current_nodes("file")
               if n.identity == file_id]
    # THE CHANGE QUANTA (flows registry; ruled 2026-09-06): KG2's
    # data quantum is the FILE — an unchanged file under an unchanged
    # metamodel never re-parses. A KG1 ripple re-RESOLVES the stored
    # tree (name binding reads current KG1) without re-parsing; only
    # a text or metamodel change pays the parser.
    if current \
            and current[0].properties.get("text_hash") == text_hash \
            and current[0].properties.get("tree", {}).get(
                "metamodel_version") == METAMODEL_VERSION:
        import copy
        # deep-copy at the boundary: the in-memory store shares dict
        # references, and resolve() mutates in place — re-resolving
        # the stored object would compare it to itself
        stored = copy.deepcopy(current[0].properties["tree"])
        if not kg1_changed:
            stored["_reused"] = True
            return stored

        def strip(node):  # name binding restarts clean — a partial
            if isinstance(node, dict):   # re-resolve would skew census
                node.pop("resolves_to", None)
                for v in node.values():
                    strip(v)
            elif isinstance(node, list):
                for v in node:
                    strip(v)
        strip(stored.get("statements"))
        stored.pop("resolution_census", None)
        tree = resolve(stored, store, reg,
                       default_schema=default_schema)
        if current[0].properties.get("tree") == tree:
            tree["_reused"] = True
            return tree
    else:
        gate = phi_gate.door1_redact(text)
        tree = resolve(map_tree(file_name, gate.text, dialect), store,
                       reg, default_schema=default_schema)
        tree["phi_redactions"] = gate.redaction_count
        if current and current[0].properties.get("tree") == tree:
            return tree  # LC2-S3 idempotence: unchanged, no new version
    tree.pop("_reused", None)
    store.append_node("file", file_id,
                      # literal: shape
                      {"tree": tree, "dialect": dialect,
                       "text_hash": text_hash}, as_of, file_id)
    have = {n.identity for n in store.current_nodes("scope")}
    for stmt in tree["statements"]:
        scopes = list(stmt.get("ctes", []))
        if stmt.get("scope"):
            scopes.append(stmt["scope"])
        for scope in scopes:
            key = scope.get("name_key")
            if key and key not in have:
                store.append_node("scope", key,
                                  {"structures": scope["structures"]},
                                  as_of, file_id)
                store.append_edge("contains", file_id, key, {}, as_of,
                                  file_id)
    for param in tree["parameters"]:
        pid = f"{file_id}::@{param['name']}"
        if pid not in {n.identity for n in store.current_nodes("parameter")}:
            store.append_node("parameter", pid, dict(param), as_of, file_id)
            store.append_edge("contains", file_id, pid, {}, as_of, file_id)
    return tree
