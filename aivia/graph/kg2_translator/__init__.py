"""KG2b's ONE writer — the translator (the parser's twin, the second
derived-layer builder; twin-graph ruling / ADR 0077, Phase B).

parser : KG2a :: translator : KG2b. Walks a resolved parsed tree and
builds its homomorphic meaning twin: every tree node yields exactly
one meaning node — translated or a reason-coded gap, no third bucket
(the conservation equation, generalized). Composite nodes (file,
statement, selection) compose their children's meanings; they never
invent. Derived meaning cites its sources: draws_from names every
KG1 node consulted; a column with no dictionary words translates as
its readable name AND lands a counted coverage gap — never silence.

content_key is MEANING IDENTITY (ruling 2e — the law of when a
certification survives): hash over (kind, operand identities resolved
to KG1 ids or scope paths, literal values, children's content_keys,
join kind). INVARIANT to formatting/whitespace (evidence never keys),
alias names (unresolved refs key by the folded column name, resolved
refs by KG1 identity), AND/join order (commutative sets sort), and
comments (R8 annotations are evidence, never truth). SENSITIVE to any
column, operator, literal value, join kind, or structural change.

Degenerate predicates (both sides literal) are TRANSLATED with
subkind 'degenerate' and voiced never — presence in the twin is the
homomorphism law; silence is the voicing policy's explicit choice.
"""
import hashlib
import json
from typing import Any, Dict, List, Optional

from aivia.graph import metamodel
from aivia.graph.kg2_mapper import METAMODEL_VERSION

TRANSLATOR_VERSION = "1.3.0"
# 1.3.0 (ADR 0080, the center law corollary): COMPOSITION IS THE
# TRANSLATOR'S JOB — the twin stores the file's up-composed SUBJECT
# (the steward words of every source table its scopes read, in
# appearance order). The cause-1 corpse dies at the root: the file's
# searchable meaning is BUILT and STORED, never assembled by a
# reading at point of use. The subject rides beside the nodes (never
# in a content_key): steward-word edits re-derive it without
# orphaning governance anchors.
# 1.1.0 (Phase C): the T-2 operational class (ruled list from the
# registry) + Gap B cross-scope resolution (temp/CTE columns resolve
# through the defining scope's projection member).
# 1.2.0 (the gap taxonomy, Sunny's Phase-C review ruling): every
# coverage gap carries its CAUSE, and the census rolls up by class —
# ruled_silent vs open(engine) vs open(estate). Registry Gap_Classes
# is the taxonomy's law.

# T-2 RULED (Sunny, 2026-09-06): operational statement kinds carry no
# analytic meaning BY RULING — the closed list lives in the registry,
# never in code opinion.
OPERATIONAL_STATEMENTS = frozenset(
    r["ScriptDom type"]
    for r in metamodel.load("kg2_kind_library")
    .sheets["Operational_Statement_Kinds"]
    if r["ScriptDom type"] != "_ruling"
)

# roles in a predicate, keyed in THIS order (role identity, never
# source position — a BETWEEN's bounds are lower/upper wherever the
# parser met them)
# literal: schema-mirror kg2_kind_library
_PRED_ROLES = ("subject", "comparand", "lower_bound", "upper_bound",
               "pattern", "escape", "selection")
_COMMUTATIVE = {"AND", "OR"}  # arm order is syntax, not meaning


def _h(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _fold(name: str) -> str:
    return name.strip("[]\"'").upper()


def _readable(name: str) -> str:
    import re
    return re.sub(r"[_\W]+", " ", name).strip().lower()


def _summarize_expr(expr: Dict[str, Any]) -> Dict[str, Any]:
    """A light static summary of a defining expression (Gap B) —
    NEVER creates twin nodes (the member's own nodes live in its
    defining scope; double-counting would break the homomorphism)."""
    kind = expr.get("kind")
    if kind == "column_ref":
        return {"copies": expr.get("ref")}
    if kind == "literal":
        return {"constant": expr.get("value")}
    if kind == "function":
        return {"operation": expr.get("name"),
                "window": bool(expr.get("over"))}
    return {"operation": kind}


def _collect_scope_members(tree: Dict[str, Any]
                           ) -> Dict[str, Dict[str, Any]]:
    """Gap B material: folded scope name -> folded member name ->
    projection member, over every NAMED scope (temps + CTEs)."""
    members: Dict[str, Dict[str, Any]] = {}
    def scopes(stmt):
        yield from stmt.get("ctes", [])
        if stmt.get("scope"):
            yield stmt["scope"]
    for stmt in tree.get("statements", []):
        for scope in scopes(stmt):
            name = scope.get("name")
            if not name:
                continue
            table = members.setdefault(_fold(name), {})
            # a COMBINATION's output columns are its first arm's
            # projection (UNION arms share the output shape)
            arms = scope.get("combination_arms")
            projection = (arms[0].get("projection", []) if arms
                          else scope.get("projection", []))
            for m in projection:
                if m.get("name"):
                    table.setdefault(_fold(m["name"]), m)
    return members


class _Walk:
    """One pass over a parsed tree; accumulates the twin's nodes and
    the census. Total by construction: every branch of the tree shape
    either translates or gaps — an unrecognized shape is a gap with
    its own reason, never a skip."""

    def __init__(self, columns: Dict[str, Dict[str, Any]],
                 scope_members: Optional[Dict[str, Dict[str, Any]]] = None):
        self.columns = columns          # KG1 column identity -> props
        self.scope_members = scope_members or {}  # Gap B material:
        # folded scope name -> folded member name -> member dict
        self.nodes: List[Dict[str, Any]] = []
        self.coverage_gaps: List[str] = []

    def add(self, kind: str, path: str, content: Any,
            key_parts: List[str], draws_from: Optional[List[str]] = None,
            child_keys: Optional[List[str]] = None,
            **extra) -> Dict[str, Any]:
        key = _h(kind, *key_parts, *(child_keys or []))
        # literal: shape
        node = {"kind": kind, "points_at": path, "content": content,
                "content_key": key,
                "draws_from": sorted(draws_from or [])}
        node.update(extra)
        self.nodes.append(node)
        return node

    def gap(self, path: str, reason: str) -> Dict[str, Any]:
        return self.add("gap", path, {"reason": reason}, [reason])

    # ---- expressions (meaning kind: reference) ----
    def expression(self, expr, path) -> Dict[str, Any]:
        kind = expr.get("kind")
        if kind == "column_ref":
            resolved = expr.get("resolves_to")
            identity = (resolved if resolved
                        else _fold(expr["ref"].rsplit(".", 1)[-1]))
            if resolved and not str(resolved).startswith(
                    ("SAME-TREE", "DERIVED")):
                props = self.columns.get(resolved, {})
                words = (props.get("description") or "").split(". ")[0]
                if words:
                    content = {"words": words.rstrip("."),
                               "words_source": "dictionary"}
                    draws = [resolved]
                else:
                    content = {"words": _readable(expr["ref"]
                                                  .rsplit(".", 1)[-1]),
                               "words_source": "readable_name"}
                    draws = [resolved]
                    self.coverage_gaps.append(
                        {"ref": resolved,
                         "cause": "no_dictionary_words"})
            elif resolved and str(resolved).startswith("DERIVED"):
                # bound into an anonymous derived table — known-local,
                # never a coverage gap (the meaning lives one level in)
                content = {"words": _readable(expr["ref"]
                                              .rsplit(".", 1)[-1]),
                           "words_source": "derived_member"}
                draws = []
            elif resolved and str(resolved).startswith("SAME-TREE"):
                # Gap B (Phase C): a temp/CTE column's meaning lives in
                # the defining scope's PROJECTION member — resolve
                # through it instead of falling back to the raw name
                colname = _fold(expr["ref"].rsplit(".", 1)[-1])
                scope_key = str(resolved).replace("SAME-TREE scope ", "")
                scope_name = scope_key.split("::")[-1]
                # strip only a TRAILING dupe suffix (#2, #3 ...) — a
                # temp table's LEADING # is its name (build find: the
                # first cut stripped '#Base_Pop' to nothing)
                head, _, tail = scope_name.rpartition("#")
                if head and tail.isdigit():
                    scope_name = head
                member = self.scope_members.get(
                    _fold(scope_name), {}).get(colname)
                identity = f"{scope_key}.{colname}"
                if member is not None:
                    # literal: shape
                    content = {
                        "words": _readable(expr["ref"].rsplit(".", 1)[-1]),
                        "words_source": "defining_projection",
                        "derivation": _summarize_expr(
                            member.get("expression", {}))}
                    draws = [identity]
                else:
                    # star-projected or built by an unmapped statement:
                    # the member is unknowable — counted, never guessed
                    content = {"words": _readable(expr["ref"]
                                                  .rsplit(".", 1)[-1]),
                               "words_source": "readable_name"}
                    draws = []
                    self.coverage_gaps.append(
                        {"ref": expr["ref"],
                         "cause": "built_by_unmapped_statement"})
            else:
                content = {"words": _readable(expr["ref"]
                                              .rsplit(".", 1)[-1]),
                           "words_source": "readable_name"}
                draws = []
                self.coverage_gaps.append(
                    {"ref": expr["ref"],
                     "cause": "unresolved_reference"})
            return self.add("reference", path, content,
                            ["column_ref", str(identity)], draws)
        if kind == "literal":
            return self.add("reference", path,
                            {"value": expr.get("value")},
                            ["literal", str(expr.get("value"))])
        if kind == "parameter_ref":
            return self.add("reference", path,
                            {"parameter": expr.get("ref")},
                            ["parameter", expr.get("ref", "")])
        # literal: schema-mirror kg2_kind_library
        if kind in ("function", "arithmetic", "unary", "cast"):
            child_keys = []
            for i, a in enumerate(expr.get("args", [])):
                child_keys.append(
                    self.expression(a, f"{path}/args/{i}")["content_key"])
            salient = expr.get("name", kind)
            over = "over" if expr.get("over") else ""
            return self.add("reference", path,
                            {"operation": salient,
                             "window": bool(expr.get("over"))},
                            [kind, salient, over], child_keys=child_keys)
        if kind == "case":
            child_keys = []
            if expr.get("input") is not None:
                child_keys.append(self.expression(
                    expr["input"], f"{path}/input")["content_key"])
            for i, w in enumerate(expr.get("whens", [])):
                when = w["when"]
                translator = (self.condition
                              if when.get("node") in ("predicate",
                                                      "structure")
                              else self.expression)
                child_keys.append(translator(
                    when, f"{path}/whens/{i}/when")["content_key"])
                child_keys.append(self.expression(
                    w["then"], f"{path}/whens/{i}/then")["content_key"])
            if expr.get("else_result") is not None:
                child_keys.append(self.expression(
                    expr["else_result"], f"{path}/else")["content_key"])
            return self.add("reference", path,
                            {"operation": "case",
                             "branches": len(expr.get("whens", []))},
                            ["case"], child_keys=child_keys)
        if kind == "star":
            # RESOLVED 2026-09-06: the star's meaning is total-by-
            # reference — never an enumerated column list (drift-safe)
            return self.add("reference", path,
                            {"words": "every column of the source at "
                             "read time"},
                            ["star"])
        if kind == "subquery_ref":
            child_keys = []
            if "scope" in expr:
                child_keys.append(self.scope(
                    expr["scope"], f"{path}/scope")["content_key"])
            return self.add("reference", path,
                            {"selection": "separately defined"},
                            ["subquery_ref"], child_keys=child_keys)
        if kind == "remainder_ref":
            return self.gap(path, "unmapped_expression")
        return self.gap(path, f"unrecognized_expression:{kind}")

    # ---- predicates and boolean structure (meaning kind: condition) --
    def condition(self, pred, path, join_type: Optional[str] = None
                  ) -> Dict[str, Any]:
        node_family = pred.get("node")
        kind = pred.get("kind")
        if node_family == "structure":         # AND | OR | NOT
            child_keys = []
            for i, c in enumerate(pred.get("children", [])):
                child_keys.append(
                    self.condition(c, f"{path}/children/{i}")
                    ["content_key"])
            if kind in _COMMUTATIVE:
                child_keys = sorted(child_keys)
            parts = [kind] + ([f"join:{join_type}"] if join_type else [])
            return self.add("condition", path, {"shape": kind},
                            parts, child_keys=child_keys)
        if kind == "remainder":
            return self.gap(path, "unmapped_predicate")
        # a predicate leaf
        role_keys, draws = [], []
        subject = pred.get("subject") or {}
        for role in _PRED_ROLES:
            child = pred.get(role)
            if child is None:
                continue
            meaning = self.expression(child, f"{path}/{role}")
            role_keys.append(f"{role}={meaning['content_key']}")
            draws.extend(meaning["draws_from"])
        member_keys = []
        for i, member in enumerate(pred.get("comparand_list", [])):
            meaning = self.expression(member,
                                      f"{path}/comparand_list/{i}")
            member_keys.append(meaning["content_key"])
            draws.extend(meaning["draws_from"])
        # a literal against a values-mapped subject cites the map
        content: Dict[str, Any] = {"predicate": kind}
        for value_role in ("comparand",):
            comparand = pred.get(value_role)
            if (comparand is not None
                    and comparand.get("kind") == "literal"
                    and subject.get("resolves_to")):
                col = subject["resolves_to"]
                values = (self.columns.get(col, {}).get("values")
                          or {})
                raw = str(comparand.get("value", "")).strip("'")
                if raw in values:
                    content["value_meaning"] = values[raw]
                    draws.append(f"{col}|values:{raw}")
        both_literal = (subject.get("kind") == "literal"
                        and (pred.get("comparand") or {}).get("kind")
                        == "literal")
        parts = ([kind] + role_keys + member_keys
                 + [str(pred.get("comparison_op", "")),
                    str(pred.get("quantifier", ""))]
                 + ([f"join:{join_type}"] if join_type else []))
        extra: Dict[str, Any] = {}
        if both_literal:
            extra = {"subkind": "degenerate", "voiced": "never"}
        if join_type:
            extra["join_type"] = join_type
        return self.add("condition", path, content, parts,
                        draws_from=draws, **extra)

    # ---- sources, projection, scope (selection) ----
    def source(self, ref, path) -> Dict[str, Any]:
        if "derived_scope" in ref:
            inner = self.scope(ref["derived_scope"],
                               f"{path}/derived_scope")
            content: Dict[str, Any] = {"reads": "an inline selection"}
            parts = ["derived"]
            pivot = ref.get("pivot")
            if pivot:
                content["pivot"] = {
                    "aggregate": pivot.get("aggregate"),
                    "into_columns": pivot.get("in_values")}
                parts += ["pivot", str(pivot.get("aggregate")),
                          *sorted(pivot.get("in_values", []))]
            return self.add("source", path, content, parts,
                            child_keys=[inner["content_key"]])
        target = ref.get("resolves_to") or _fold(ref.get("table_ref", ""))
        draws = ([ref["resolves_to"]]
                 if ref.get("resolves_to")
                 and not str(ref["resolves_to"]).startswith("SAME-TREE")
                 else [])
        content: Dict[str, Any] = {"reads": ref.get("table_ref"),
                                   "resolved": ref.get("resolves_to")}
        parts = ["source", str(target)]
        pivot = ref.get("pivot")
        if pivot:  # the transform is meaning: what pivots into what
            content["pivot"] = {"aggregate": pivot.get("aggregate"),
                                "into_columns": pivot.get("in_values")}
            parts += ["pivot", str(pivot.get("aggregate")),
                      *sorted(pivot.get("in_values", []))]
        return self.add("source", path, content, parts, draws)

    def projection_member(self, member, path) -> Dict[str, Any]:
        expr = self.expression(member["expression"], f"{path}/expression")
        return self.add("projection", path,
                        {"output": member.get("name"),
                         "derivation": expr["content"]},
                        [str(member.get("name")),
                         str(member.get("position"))],
                        child_keys=[expr["content_key"]])

    def scope(self, scope, path) -> Dict[str, Any]:
        if "combination_arms" in scope:
            # the COMBINATION meaning kind (the ABX corpse build):
            # arm ORDER is meaning (UNION arms differ in filters) —
            # keys stay ordered, never sorted
            arm_keys = [
                self.scope(arm, f"{path}/combination_arms/{i}")
                ["content_key"]
                for i, arm in enumerate(scope["combination_arms"])]
            # literal: shape
            content = {"selection": scope.get("name")
                       or scope.get("name_key") or "(anonymous)",
                       "name_key": scope.get("name_key"),
                       "combines": len(arm_keys),
                       "combination": scope.get("combination"),
                       "duplicates_kept": bool(
                           scope.get("combination_all"))}
            return self.add("combination", path, content,
                            ["combination",
                             str(scope.get("combination")),
                             str(bool(scope.get("combination_all")))],
                            child_keys=arm_keys)
        if scope.get("unmapped_shape"):
            return self.gap(path,
                            f"unmapped_query_shape:"
                            f"{scope['unmapped_shape']}")
        source_keys = []
        for i, ref in enumerate(scope.get("from_refs", [])):
            source_keys.append(
                self.source(ref, f"{path}/from_refs/{i}")["content_key"])
        join_keys = []
        for i, on in enumerate(scope.get("join_on", [])):
            join_keys.append(
                self.condition(on, f"{path}/join_on/{i}",
                               join_type=on.get("join_type"))
                ["content_key"])
        where_key = []
        if scope.get("where") is not None:
            where_key = [self.condition(scope["where"], f"{path}/where")
                         ["content_key"]]
        member_keys = []
        for i, m in enumerate(scope.get("projection", [])):
            member_keys.append(
                self.projection_member(m, f"{path}/projection/{i}")
                ["content_key"])
        # joins/sources sort (join ORDER is syntax); projection stays
        # ordered (output column order is meaning)
        child_keys = (sorted(source_keys) + sorted(join_keys)
                      + where_key + member_keys)
        # literal: shape
        content = {"selection": scope.get("name") or scope.get("name_key")
                   or "(anonymous)",
                   "name_key": scope.get("name_key"),
                   "reads": len(source_keys),
                   "conditions": len(join_keys) + len(where_key),
                   "outputs": len(member_keys)}
        return self.add("selection", path, content,
                        ["selection"], child_keys=child_keys)

    def statement(self, stmt, path) -> Dict[str, Any]:
        child_keys = []
        for i, cte in enumerate(stmt.get("ctes", [])):
            child_keys.append(
                self.scope(cte, f"{path}/ctes/{i}")["content_key"])
        if stmt.get("scope"):
            child_keys.append(
                self.scope(stmt["scope"], f"{path}/scope")["content_key"])
        if stmt.get("predicate") is not None:
            child_keys.append(
                self.condition(stmt["predicate"], f"{path}/predicate")
                ["content_key"])
        if stmt.get("expression") is not None:  # SET @var = <expr>
            child_keys.append(
                self.expression(stmt["expression"], f"{path}/expression")
                ["content_key"])
        kind_label = stmt.get("statement_kind", "?")
        if kind_label == "LABEL":
            # a jump marker — plumbing (the operational pattern;
            # registry row LabelStatement, ledger-close 2026-09-06)
            return self.add("statement", path,
                            {"does": "LABEL",
                             "label": stmt.get("label")},
                            ["LABEL", stmt.get("label", "")],
                            subkind="operational", voiced="never")
        if kind_label == "GOTO":
            # control flow IS meaning: 'repeat from {label}' — the
            # corpus uses GOTO+label as loops
            return self.add("statement", path,
                            {"does": "GOTO", "label": stmt.get("label")},
                            ["GOTO", stmt.get("label", "")])
        # literal: schema-mirror kg2_kind_library Operational_Statement_Kinds
        if kind_label in ("INSERT", "WHILE", "SET", "DELETE") \
                and child_keys:
            return self.add("statement", path,
                            {"does": kind_label,
                             **({"parameter": stmt["parameter"]}
                                if stmt.get("parameter") else {})},
                            [kind_label, stmt.get("parameter", "")],
                            child_keys=child_keys)
        if kind_label in OPERATIONAL_STATEMENTS:
            # T-2 RULED: no analytic meaning BY RULING — translated
            # (the homomorphism holds), silenced by policy, never debt
            return self.add("statement", path,
                            {"does": kind_label, "class": "operational"},
                            [kind_label], subkind="operational",
                            voiced="never")
        # literal: schema-mirror kg2_kind_library Operational_Statement_Kinds
        if not child_keys and kind_label not in ("SELECT", "SELECT INTO",
                                                 "IF"):
            # a statement the mapper counted as unmapped — its twin is
            # the gap, same reason class, homomorphism intact
            return self.gap(path, f"unmapped_statement:{kind_label}")
        return self.add("statement", path,
                        {"does": kind_label},
                        [kind_label], child_keys=child_keys)

    def file(self, tree) -> Dict[str, Any]:
        child_keys = []
        for i, stmt in enumerate(tree.get("statements", [])):
            child_keys.append(
                self.statement(stmt, f"/statements/{i}")["content_key"])
        for i, p in enumerate(tree.get("parameters", [])):
            meaning = self.add(
                "reference", f"/parameters/{i}",
                {"parameter": p["name"],
                 "default": p.get("default_logic")},
                ["file_parameter", p["name"],
                 str(p.get("default_logic"))])
            child_keys.append(meaning["content_key"])
        return self.add("file", "/",
                        {"file": tree.get("name"),
                         "statements": len(tree.get("statements", []))},
                        [tree.get("name", "")], child_keys=child_keys)


def parsed_census(tree: Dict[str, Any]) -> int:
    """The parsed side of the conservation equation, computed
    INDEPENDENTLY of the twin walk: counts every node the twin must
    mirror (file, statements, scopes incl. CTEs + derived, sources,
    join-ON subtrees, WHERE subtrees, IF predicates, projection
    members + their expression subtrees, parameters)."""
    count = 0

    def expr(e):
        nonlocal count
        count += 1
        for a in e.get("args", []):
            expr(a)
        if e.get("input") is not None:
            expr(e["input"])
        for w in e.get("whens", []):
            (cond if w["when"].get("node") in ("predicate", "structure")
             else expr)(w["when"])
            expr(w["then"])
        if e.get("else_result") is not None:
            expr(e["else_result"])
        if e.get("kind") == "subquery_ref" and "scope" in e:
            scope(e["scope"])

    def cond(p):
        nonlocal count
        count += 1
        for c in p.get("children", []):
            cond(c)
        for role in _PRED_ROLES:
            if p.get(role) is not None:
                expr(p[role])
        for m in p.get("comparand_list", []):
            expr(m)

    def scope(s):
        nonlocal count
        count += 1
        for arm in s.get("combination_arms", []):
            scope(arm)
        for ref in s.get("from_refs", []):
            count += 1
            if "derived_scope" in ref:
                scope(ref["derived_scope"])
        for on in s.get("join_on", []):
            cond(on)
        if s.get("where") is not None:
            cond(s["where"])
        for m in s.get("projection", []):
            count += 1
            expr(m["expression"])

    count += 1  # the file root
    for stmt in tree.get("statements", []):
        count += 1
        for cte in stmt.get("ctes", []):
            scope(cte)
        if stmt.get("scope"):
            scope(stmt["scope"])
        if stmt.get("predicate") is not None:
            cond(stmt["predicate"])
        if stmt.get("expression") is not None:
            expr(stmt["expression"])
    count += len(tree.get("parameters", []))
    return count


def translate(tree: Dict[str, Any],
              columns: Optional[Dict[str, Dict[str, Any]]] = None
              ) -> Dict[str, Any]:
    """Parsed tree -> its meaning twin. `columns` is KG1 material
    (identity -> properties with description/values); omit it and
    every reference translates by readable name with a counted
    coverage gap — grounded, never silent, never invented."""
    walk = _Walk(columns or {}, _collect_scope_members(tree))
    walk.file(tree)
    gaps = [n for n in walk.nodes if n["kind"] == "gap"]
    # literal: shape
    twin = {
        "file": tree.get("name"),
        "translator_version": TRANSLATOR_VERSION,
        "metamodel_version": METAMODEL_VERSION,
        "nodes": walk.nodes,
        # literal: shape
        "census": {
            "twin_nodes": len(walk.nodes),
            "translated": len(walk.nodes) - len(gaps),
            "gaps": len(gaps),
            "gap_reasons": sorted({n["content"]["reason"] for n in gaps}),
            "parsed_nodes": parsed_census(tree),
            "degenerate": sum(1 for n in walk.nodes
                              if n.get("subkind") == "degenerate"),
            "operational": sum(1 for n in walk.nodes
                               if n.get("subkind") == "operational"),
            "cross_scope_resolved": sum(
                1 for n in walk.nodes
                if n["content"].get("words_source")
                == "defining_projection"),
            "coverage_gaps": len(walk.coverage_gaps),
            "coverage_by_cause": {
                cause: sum(1 for g in walk.coverage_gaps
                           if g["cause"] == cause)
                for cause in sorted({g["cause"]
                                     for g in walk.coverage_gaps})},
        },
    }
    # THE GAP TAXONOMY (registry Gap_Classes; Sunny's Phase-C ruling):
    # RULED-SILENT (ok forever) vs OPEN (needs resolution), owner
    # engine|estate. At TWIN grain: estate findings are doc-word
    # gaps only; every unbound reference class (ambiguous, correlated,
    # unattempted) is ENGINE debt. The estate's drift refs (columns
    # nowhere declared) are counted at RESOLUTION grain and reported
    # there — the two grains sum in the gap-check report.
    census = twin["census"]
    cov = census["coverage_by_cause"]
    # literal: shape
    census["by_class"] = {
        "ruled_silent": census["degenerate"] + census["operational"],
        "open_engine": census["gaps"]
        + cov.get("built_by_unmapped_statement", 0)
        + cov.get("unresolved_reference", 0),
        "open_estate": cov.get("no_dictionary_words", 0),
    }
    # THE HOMOMORPHISM LAW, checked at build time, every run: the twin
    # mirrors the parse exactly — translated + gap == every parsed
    # node, no third bucket. A mismatch is a build failure, never a
    # warning (the conservation lineage, ADR 0044 -> ADR 0077).
    twin["subject"] = _compose_subject(tree, walk.columns)
    census = twin["census"]
    if census["twin_nodes"] != census["parsed_nodes"]:
        raise AssertionError(
            f"homomorphism broken for {tree.get('name')}: "
            f"{census['twin_nodes']} twin nodes vs "
            f"{census['parsed_nodes']} parsed nodes")
    return twin


def column_material(store) -> Dict[str, Dict[str, Any]]:
    """KG1 material for translation: column AND table identity ->
    properties (tables joined in 1.3.0 — the composed subject reads
    their steward words). A read the builder performs against its
    own layer's inputs — same posture as the mapper's resolve()."""
    material = {n.identity: n.properties
                for n in store.current_nodes("column")}
    material.update({n.identity: n.properties
                     for n in store.current_nodes("table")})
    return material


def _compose_subject(tree: Dict[str, Any],
                     material: Dict[str, Dict[str, Any]]) -> str:
    """The file's up-composed subject (1.3.0): the first steward
    sentence of every KG1 table its scopes read, appearance order,
    deduped — the meaning the report is ABOUT, stored in the twin."""
    sentences: List[str] = []
    seen = set()

    def scopes_of(container):
        for stmt in container.get("statements", []):
            for cte in stmt.get("ctes", []):
                yield cte
            if stmt.get("scope"):
                yield stmt["scope"]

    def walk_scope(scope):
        for s in [scope] + scope.get("combination_arms", []):
            for ref in s.get("from_refs", []):
                if "derived_scope" in ref:
                    walk_scope(ref["derived_scope"])
                    continue
                rt = str(ref.get("resolves_to") or "")
                props = material.get(rt)
                if props is None or rt in seen:
                    continue
                seen.add(rt)
                desc = (props.get("description") or "").strip()
                if desc:
                    sentences.append(desc.split(". ")[0].rstrip(".")
                                     + ".")

    for scope in scopes_of(tree):
        walk_scope(scope)
    return " ".join(sentences)


def apply_twin(store, file_id: str, tree: Dict[str, Any],
               as_of: str) -> Dict[str, Any]:
    """Store the meaning twin — KG2b's lifecycle write. File-quantum
    rebuild: the twin for a changed file is replaced WHOLE (supersede,
    never patched); an unchanged twin writes nothing (idempotent at
    the content grain, the LC-S3 discipline)."""
    twin = translate(tree, column_material(store))
    identity = f"twin::{file_id}"
    current = [n for n in store.current_nodes("meaning_twin")
               if n.identity == identity]
    if current and current[0].properties.get("twin") == twin:
        return twin
    store.append_node("meaning_twin", identity, {"twin": twin},
                      as_of, file_id)
    return twin


def content_keys(twin: Dict[str, Any]) -> Dict[str, str]:
    """points_at path -> content_key, for anchor checks and tests."""
    return {n["points_at"]: n["content_key"] for n in twin["nodes"]}


def stable_json(twin: Dict[str, Any]) -> str:
    return json.dumps(twin, sort_keys=True)
