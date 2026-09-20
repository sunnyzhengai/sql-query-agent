"""Decision lenses — readings of KG2 predicates by tree position.

The mapper captures faithfully; these lenses judge. Membership
excludes join keys (they live in join_on structures, not WHERE) and
both-sides-literal predicates (ruled 2026-09-05: degenerate literals
route to the degenerate lens ONLY, never membership). Deterministic:
same graph state, same answer (M5).
"""
from typing import Any, Dict, List

# literal: schema-mirror kg2_kind_library
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
    # literal: schema-mirror kg2_kind_library
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


def is_join_key(pred: Dict[str, Any]) -> bool:
    """col = col between two references — structure, never membership."""
    return (pred.get("kind") == "COMPARE_EQ"
            and pred.get("subject", {}).get("kind") == "column_ref"
            and pred.get("comparand", {}).get("kind") == "column_ref")


def inner_join_residues(scope) -> List[Dict[str, Any]]:
    """Grammar v1.3.0 (the #BPA corpse): non-key predicates in an
    INNER join's ON clause are MEMBERSHIP — a filter is a filter
    wherever the developer parked it. OUTER-join residues are match
    conditions, not membership: excluded here, counted by gap-census."""
    out = []
    for join_pred in scope.get("join_on", []):
        if join_pred.get("join_type", "Inner") != "Inner":
            continue
        for leaf in flatten_where(join_pred):
            if not is_join_key(leaf):
                out.append(leaf)
    return out


def membership_predicates(scope) -> List[Dict[str, Any]]:
    """The scope's full membership set: INNER-join ON residues (join
    order precedes WHERE in the source) + WHERE predicates. A
    COMBINATION scope's membership is its arms' union, arm order kept
    (the ABX corpse, 2026-09-06: a UNION CTE's filters were invisible
    because the empty top scope had no WHERE)."""
    if "combination_arms" in scope:
        out: List[Dict[str, Any]] = []
        for arm in scope["combination_arms"]:
            out.extend(membership_predicates(arm))
        return out
    return inner_join_residues(scope) + flatten_where(scope.get("where"))


def nested_membership(scope) -> List[Dict[str, Any]]:
    """The RESTRICTIVE-SPINE membership of a subselection (grammar
    2.2.0, the ABX first-leg find): this scope's membership plus every
    derived source's, recursively — EXCEPT arms of OUTER APPLY (an
    optional lookup's interior never restricts the producing rows) and
    combination arms (alternatives cannot flatten as conjunction).
    Truthful because restrictive-spine composition is conjunctive."""
    if "combination_arms" in scope:
        return []
    out = list(membership_predicates(scope))
    for ref in scope.get("from_refs", []):
        if "derived_scope" in ref and not ref.get("outer_apply"):
            out.extend(nested_membership(ref["derived_scope"]))
    return [p for p in out if not is_join_key(p)]


def nested_sources(scope) -> List[Dict[str, Any]]:
    """Every table/scope READ of a subselection, all depths, in
    appearance order — lookups included (a read is a read)."""
    out: List[Dict[str, Any]] = []
    for s in ([scope] + scope.get("combination_arms", [])):
        for ref in s.get("from_refs", []):
            if "derived_scope" in ref:
                out.extend(nested_sources(ref["derived_scope"]))
            else:
                out.append(ref)
    return out


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
                render_predicate(p) for p in membership_predicates(scope)
                if not is_degenerate(p)]
    # literal: shape
    return {"yield": out, "completeness": "total per tree",
            "stamp": read.stamp()}


def lens_degenerate(read, params) -> Dict[str, Any]:
    out = []
    for tree in read.trees().values():
        for scope in named_scopes(tree):
            for p in flatten_where(scope.get("where")):
                if is_degenerate(p):
                    out.append(f"{tree['name']} :: {render_predicate(p)}")
    # literal: shape
    return {"yield": out, "completeness": "total", "stamp": read.stamp()}
