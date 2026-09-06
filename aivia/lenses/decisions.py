"""Decision lenses — readings of KG2 predicates by tree position.

The mapper captures faithfully; these lenses judge. Membership
excludes join keys (they live in join_on structures, not WHERE) and
both-sides-literal predicates (ruled 2026-09-05: degenerate literals
route to the degenerate lens ONLY, never membership). Deterministic:
same graph state, same answer (M5).
"""
from typing import Any, Dict, List

OP_SYMBOL = {"COMPARE_EQ": "=", "COMPARE_NEQ": "<>", "COMPARE_GT": ">",
             "COMPARE_GTE": ">=", "COMPARE_LT": "<", "COMPARE_LTE": "<="}


def render_expr(expr: Dict[str, Any]) -> str:
    kind = expr.get("kind")
    if kind == "column_ref":
        return expr["ref"].split(".")[-1]  # the column speaks, not the alias
    if kind == "parameter_ref":
        return expr["ref"]
    if kind == "literal":
        return str(expr["value"])
    return expr.get("evidence", {}).get("fragment", "?")


def render_predicate(pred: Dict[str, Any]) -> str:
    kind = pred["kind"]
    if kind in OP_SYMBOL:
        return (f"{render_expr(pred['subject'])} {OP_SYMBOL[kind]} "
                f"{render_expr(pred['comparand'])}")
    if kind == "PATTERN_MATCH":
        return (f"{render_expr(pred['subject'])} LIKE "
                f"{render_expr(pred['pattern'])}")
    if kind == "IN_LIST":
        members = ", ".join(render_expr(m) for m in pred["comparand_list"])
        return f"{render_expr(pred['subject'])} IN ({members})"
    if kind == "NULL_CHECK":
        return f"{render_expr(pred['subject'])} IS NULL"
    if kind == "NOT":
        return f"NOT ({render_predicate(pred['children'][0])})"
    if kind in ("AND", "OR"):
        return f" {kind} ".join(render_predicate(c)
                                for c in pred["children"])
    return pred.get("evidence", {}).get("fragment", kind)


def is_degenerate(pred: Dict[str, Any]) -> bool:
    """Both-sides-literal: every expression role is a literal."""
    exprs = [pred.get(r) for r in ("subject", "comparand", "pattern",
                                   "lower_bound", "upper_bound")]
    exprs = [e for e in exprs if e is not None]
    exprs += pred.get("comparand_list", [])
    return bool(exprs) and all(e.get("kind") == "literal" for e in exprs)


def flatten_where(where) -> List[Dict[str, Any]]:
    if where is None:
        return []
    if where.get("kind") == "AND":
        return list(where["children"])
    return [where]


def named_scopes(tree):
    for stmt in tree["statements"]:
        for cte in stmt.get("ctes", []):
            if "name_key" in cte:
                yield cte
        scope = stmt.get("scope")
        if scope and "name_key" in scope:
            yield scope


def lens_decisions(read, params) -> Dict[str, Any]:
    assert (params or {}).get("class") == "membership", \
        "v1 implements the membership class; others arrive with their slices"
    out: Dict[str, List[str]] = {}
    for tree in read.trees().values():
        for scope in named_scopes(tree):
            out[scope["name_key"]] = [
                render_predicate(p) for p in flatten_where(scope.get("where"))
                if not is_degenerate(p)]
    return {"yield": out, "completeness": "total per tree",
            "stamp": read.stamp()}


def lens_degenerate(read, params) -> Dict[str, Any]:
    out = []
    for tree in read.trees().values():
        for scope in named_scopes(tree):
            for p in flatten_where(scope.get("where")):
                if is_degenerate(p):
                    out.append(f"{tree['name']} :: {render_predicate(p)}")
    return {"yield": out, "completeness": "total", "stamp": read.stamp()}
