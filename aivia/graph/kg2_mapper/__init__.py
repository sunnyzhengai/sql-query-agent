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

from aivia.graph import phi_gate
from aivia.graph.kg2_mapper.scriptdom_loader import parse_tsql
from aivia.graph.store import Store

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
    return {"fragment": ctx.text[start:start + frag.FragmentLength],
            "offset": start, "line": frag.StartLine,
            "column": frag.StartColumn}


def _node(ctx, kind_family, kind, frag, **props) -> Dict[str, Any]:
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
    if t in ("IntegerLiteral", "NumericLiteral", "MoneyLiteral",
             "RealLiteral"):
        return _node(ctx, "expression", "literal", expr, value=expr.Value)
    if t == "StringLiteral":
        return _node(ctx, "expression", "literal", expr,
                     value=f"'{expr.Value}'")
    if t == "NullLiteral":
        return _node(ctx, "expression", "literal", expr, value="NULL")
    if t == "VariableReference":
        return _node(ctx, "expression", "parameter_ref", expr, ref=expr.Name)
    if t == "FunctionCall":
        return _node(ctx, "expression", "function", expr,
                     name=expr.FunctionName.Value,
                     args=[_map_expression(ctx, p) for p in expr.Parameters])
    if t == "BinaryExpression":
        return _node(ctx, "expression", "arithmetic", expr,
                     args=[_map_expression(ctx, expr.FirstExpression),
                           _map_expression(ctx, expr.SecondExpression)])
    if t == "UnaryExpression":
        return _node(ctx, "expression", "unary", expr,
                     args=[_map_expression(ctx, expr.Expression)])
    if t in ("CastCall", "ConvertCall", "TryCastCall"):
        return _node(ctx, "expression", "cast", expr,
                     args=[_map_expression(ctx, expr.Parameter)])
    if t == "ScalarSubquery":
        return _node(ctx, "expression", "subquery_ref", expr)
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
                          selection=_node(ctx, "expression", "subquery_ref",
                                          cond.Subquery))
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
                     selection=_node(ctx, "expression", "subquery_ref",
                                     cond.Subquery))
    if t == "SubqueryComparisonPredicate":
        return _node(ctx, "predicate", "QUANTIFIED_COMPARE", cond,
                     subject=_map_expression(ctx, cond.Expression),
                     comparison_op=str(cond.ComparisonType),
                     quantifier=str(cond.SubqueryComparisonPredicateType),
                     selection=_node(ctx, "expression", "subquery_ref",
                                     cond.Subquery))
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
        refs.append({
            "table_ref": _table_name(table_ref.SchemaObject),
            "alias": table_ref.Alias.Value if table_ref.Alias else None,
            "evidence": _evidence(ctx, table_ref)})
    elif t == "QualifiedJoin":
        _collect_from(ctx, table_ref.FirstTableReference, refs, join_on)
        _collect_from(ctx, table_ref.SecondTableReference, refs, join_on)
        join_on.append(_map_predicate(ctx, table_ref.SearchCondition))
    elif t == "QueryDerivedTable":
        refs.append({
            "derived_scope": _map_query(ctx, table_ref.QueryExpression),
            "alias": table_ref.Alias.Value if table_ref.Alias else None,
            "evidence": _evidence(ctx, table_ref)})
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
    if t != "QuerySpecification":
        ctx.remainder.append({"type": t, **_evidence(ctx, query),
                              "reason": "unmapped query shape"})
        return {"node": "scope", "structures": [],
                "evidence": _evidence(ctx, query)}
    refs, join_on = [], []
    if query.FromClause:
        for tr in query.FromClause.TableReferences:
            _collect_from(ctx, tr, refs, join_on)
    where = (_map_predicate(ctx, query.WhereClause.SearchCondition)
             if query.WhereClause else None)
    select_refs = []
    for el in query.SelectElements:
        if _type_name(el) == "SelectScalarExpression":
            select_refs.append(_map_expression(ctx, el.Expression))
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
    return {"node": "scope", "structures": structures, "from_refs": refs,
            "join_on": join_on, "where": where, "select_refs": select_refs,
            "evidence": _evidence(ctx, query)}


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

    for batch in fragment.Batches:
        for stmt in executable_statements(batch.Statements):
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
            else:
                entry["statement_kind"] = t
                ctx.remainder.append({"type": t, **_evidence(ctx, stmt),
                                      "reason": "unmapped statement kind"})
            statements.append(entry)

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
    return {"node": "file", "name": file_name, "dialect": dialect,
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
        if scope and "name" in scope:
            scope_keys[scope["name"]] = scope["name_key"]
    params = {p["name"] for p in tree["parameters"]}
    census = {"resolved_refs": 0, "same_tree_refs": 0,
              "unresolved_refs": 0, "unresolved": []}

    def resolve_scope(scope):
        alias_to = {}
        for ref in scope.get("from_refs", []):
            if "derived_scope" in ref:
                resolve_scope(ref["derived_scope"])
                if ref.get("alias"):
                    alias_to[ref["alias"]] = ("derived", None)
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
                        {"ref": name, "kind": "table",
                         "schema": schema or "(unqualified)"})
                    target = ("unresolved", None)
            if ref.get("alias"):
                alias_to[ref["alias"]] = target
            elif "." in name:
                alias_to[name.rsplit(".", 1)[1]] = target

        for col in _column_refs_in([scope.get("where"),
                                    scope.get("join_on"),
                                    scope.get("select_refs")]):
            parts = col["ref"].split(".")
            if len(parts) == 2 and parts[0] in alias_to:
                kind, target = alias_to[parts[0]]
                if kind == "table":
                    col_id = folded_columns.get(
                        f"{target}|{_fold(parts[1])}")
                    if col_id:
                        col["resolves_to"] = col_id
                        census["resolved_refs"] += 1
                    else:
                        col["resolves_to"] = None
                        census["unresolved_refs"] += 1
                        census["unresolved"].append(col["ref"])
                        census.setdefault("unresolved_detail", []).append(
                            {"ref": col["ref"], "kind": "column",
                             "table": target})
                elif kind == "scope":
                    col["resolves_to"] = f"SAME-TREE scope {target}"
                    census["same_tree_column_refs"] = \
                        census.get("same_tree_column_refs", 0) + 1
                else:
                    col["resolves_to"] = None

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
    store.append_node("excluded_file", file_name, {"reason": reason},
                      as_of, f"estate@{as_of}")


def apply_file(store: Store, reg: Dict[str, Any], file_id: str,
               file_name: str, text: str, as_of: str,
               dialect: str = "tsql",
               default_schema: Optional[str] = None) -> Dict[str, Any]:
    gate = phi_gate.door1_redact(text)
    tree = resolve(map_tree(file_name, gate.text, dialect), store, reg,
                   default_schema=default_schema)
    tree["phi_redactions"] = gate.redaction_count
    current = [n for n in store.current_nodes("file")
               if n.identity == file_id]
    if current and current[0].properties.get("tree") == tree:
        return tree  # LC2-S3-style idempotence: unchanged, no new version
    store.append_node("file", file_id,
                      {"tree": tree, "dialect": dialect}, as_of, file_id)
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
