# semantic_graph.py — the phase 05 build (05_semantic_graph.md, contract
# 05_semantic_graph_data_contract.md, both APPROVED 2026-10-01).
#
# STAGE 1 of 5 (L03): file + statement sheets, contains edges, exclusion
# ledger. Later stages (L04-L07) extend THIS file — one code file, built
# stage by stage, top-down (design decision 8).
#
# STATUS: PSEUDO CODE ONLY — awaiting Sunny's approval before any code
# is written below the pseudo code (the standing process).
#
# ============================================================ PSEUDO CODE
#
# CONSTANTS
#   1. BUILDER_VERSION = "0.1.0" (stage 1); bumped per stage landing.
#   2. The one parse door: import parse_tsql / ensure_scriptdom from
#      scriptdom_loader (same folder). NO other parser import, ever
#      (ADR 0001; test-locked already).
#   3. Sheet file names exactly as the contract lists them.
#
# INPUTS (CLI arguments, no paths inside code — the phase 01 law)
#   4. argv[1] = the sql folder (AIVIA_01_Data/01_subject_sql_files)
#      argv[2] = the output folder (AIVIA_01_Data/05_semantic_graph)
#   5. Load 05_kind_library.json from the output folder; REFUSE to run
#      (fail loudly, name the file) unless its status starts with
#      "RATIFIED" — the ratification gate is mechanical, not advisory.
#
# PER FILE (sorted file names, so output order is deterministic)
#   6. Read the .sql text; normalize \r\n -> \n AT ENTRY (the
#      normalize-early law; same bug bit twice in the prior estate).
#   7. parse_tsql(text). If errors: append one exclusion-ledger row
#      {file_name, reasons (the parser's verbatim error strings),
#      recorded_at}, SKIP the file, continue. A failed parse is
#      counted, named, never fatal (decision 3). Expect 0 of 8.
#   8. Unwrap to the ordered executable statements: walk
#      fragment.Batches; a CreateProcedureStatement or
#      BeginEndBlockStatement contributes its children, in order
#      (the prior estate's executable_statements).
#   9. NESTING (flagged for Sunny — one BEGIN..END gap in the prior
#      estate hid 3 of 28 procs' bodies): control-flow statements
#      (IF / WHILE) nest statements. Stage 1 RECURSES into them:
#      - node_id uses a dotted position path:
#        file::<name>::stmt/3 (top level), stmt/3.1, stmt/3.1.2 ...
#      - a contains edge statement -> statement carries the child
#        position. Nothing is silently skipped at any depth.
#
# PER STATEMENT
#  10. statement row:
#      - node_id (the dotted path id above)
#      - position (the dotted path, e.g. "3.1")
#      - scriptdom_type (the parser's class name, verbatim)
#      - statement_kind: mapped from scriptdom_type by a closed map
#        mirroring the kind library (SELECT, SELECT INTO, INSERT,
#        UPDATE, DELETE, IF, WHILE, SET, DECLARE, ...)
#      - disposition (contract-refined with the pseudo approval;
#        "gap" added by decision 9, ruled same day):
#          "handled"     - a kind stages 2+ will open up
#          "operational" - in the library's ruled-silent list
#          "gap"         - logic static parsing cannot open, classed
#                          by the library's Statement_Gap_Classes
#                          (first class: dynamic_sql — string-form
#                          EXEC only); gap_class names it
#          "remainder"   - NOT in any closed list; statement_kind
#                          then repeats the raw scriptdom_type
#        Gap and remainder statements still get full rows — visible
#        to Sunny's eye, not just a count.
#      - evidence {fragment (verbatim statement text), line, column}
#  11. contains edge: parent (file or outer statement) -> this
#      statement, with position.
#
# PER FILE, CLOSING (conservation — tests, not advice)
#  12. file row: file_name, dialect "tsql", parsed_at (ISO; the ONLY
#      non-deterministic field in any sheet — tests ignore it,
#      everything else byte-identical on re-run), statement_total,
#      statements_handled, statements_operational, remainder_total,
#      parser_version (from scriptdom_loader), kind_library_version.
#  13. ASSERT handled + operational + remainder == total, else the
#      build DIES loudly naming the file. (The red-build law proper
#      — unmapped BOOLEAN types — arms at stage 4 with predicates;
#      stage 1's unknown statement kinds go to the remainder by the
#      contract.)
#
# WRITE (all files, every run — rebuild is the only edit path)
#  14. 05_file_sheet.json, 05_statement_sheet.json,
#      05_contains_edges.json, 05_exclusion_ledger.json — json,
#      indent 2, keys in the contract's listed order, rows in
#      deterministic order (file name, then position path).
#  15. Print the census to stdout: per file "name: N statements
#      (H handled / O operational / R remainder), excluded: none",
#      then totals — what Sunny eyeballs against the raw SQL.
#
# TESTS (written RED before the code below this line)
#  16. AIVIA_01_Test/test_05_semantic_graph_data_contract.py —
#      stage-1 tests: ratification gate refuses an unratified
#      library; conservation equality per file; dotted-path identity
#      law (ids deterministic across two runs); evidence present on
#      every row; exclusion path exercised with a deliberately
#      broken SQL string; remainder rows visible (a fabricated
#      unknown type maps to disposition "remainder").
#
# ======================================================== END PSEUDO CODE
# Pseudo code approved by Sunny 2026-10-01 (incl. the two contract
# refinements); stage-1 tests shown RED the same day. Code follows.

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from scriptdom_loader import parse_tsql

BUILDER_VERSION = "0.1.0"
PARSER_VERSION = "ScriptDom 18.0.78.1 / TSql160Parser"

FILE_SHEET = "05_file_sheet.json"
STATEMENT_SHEET = "05_statement_sheet.json"
SCOPE_SHEET = "05_scope_sheet.json"
STRUCTURE_SHEET = "05_structure_sheet.json"
PREDICATE_SHEET = "05_predicate_sheet.json"
EXPRESSION_SHEET = "05_expression_sheet.json"
PARAMETER_SHEET = "05_parameter_sheet.json"
RESOLVES_EDGES = "05_resolves_edges.json"
DISCOVERED_JOINS = "05_discovered_joins.json"
CONTAINS_EDGES = "05_contains_edges.json"
EXCLUSION_LEDGER = "05_exclusion_ledger.json"
KIND_LIBRARY = "05_kind_library.json"

# STAGE 2 (L04, contract stage-2 amendment APPROVED 2026-10-02):
# population statements mint scopes — named scopes key by NAME (a
# later FROM #temp / FROM cte resolves to them by name at stage 5),
# subqueries key positionally, the delivery scope emits the result.
POPULATION_KINDS = {"SELECT", "SELECT INTO", "INSERT", "UPDATE",
                    "DELETE"}

# The closed statement map: ScriptDom type -> statement_kind. These are
# the kinds stages 2+ open up (disposition "handled"). Everything not
# here and not in the library's Operational_Statement_Kinds sheet is a
# full visible remainder row.
HANDLED_KINDS = {
    "SelectStatement": "SELECT",          # "SELECT INTO" when .Into is set
    "InsertStatement": "INSERT",
    "UpdateStatement": "UPDATE",
    "DeleteStatement": "DELETE",
    "IfStatement": "IF",
    "WhileStatement": "WHILE",
    "SetVariableStatement": "SET",
    "GoToStatement": "GOTO",
}

# Wrapper statements contribute their bodies IN PLACE (a proc's body is
# the file's top level; BEGIN/END is punctuation, not a nesting level).
_UNWRAP = ("CreateProcedureStatement", "CreateOrAlterProcedureStatement",
           "AlterProcedureStatement", "BeginEndBlockStatement",
           "BeginEndAtomicBlockStatement")

# D13 (2026-10-07): the view class — a view's body is ONE
# SelectStatement, not a StatementList, so it unwraps by its own branch.
_VIEW_UNWRAP = ("CreateViewStatement", "CreateOrAlterViewStatement",
                "AlterViewStatement")


def _type_name(frag):
    return frag.GetType().Name


def _evidence(text, frag):
    start = frag.StartOffset
    return {"fragment": text[start:start + frag.FragmentLength],
            "line": frag.StartLine, "column": frag.StartColumn}


def _load_kind_library(out_dir: Path) -> dict:
    path = out_dir / KIND_LIBRARY
    if not path.exists():
        raise ValueError(f"{KIND_LIBRARY} not found in {out_dir} — the "
                         "build refuses to run without the ratified "
                         "kind library (contract Input File 1).")
    library = json.loads(path.read_text())
    if not str(library.get("status", "")).startswith("RATIFIED"):
        raise ValueError(
            f"{KIND_LIBRARY} is not ratified (status: "
            f"{library.get('status', 'MISSING')!r}). Sunny's ratification "
            "gate is mechanical: the build refuses to run.")
    return library


def _operational_types(library: dict) -> set:
    rows = library["sheets"]["Operational_Statement_Kinds"]
    return {r["ScriptDom type"] for r in rows
            if not r["ScriptDom type"].startswith("_")}


def _gap_classes(library: dict) -> set:
    rows = library["sheets"].get("Statement_Gap_Classes", [])
    return {r["Gap class"] for r in rows}


# ---------------------------------------------------------------- STAGE 5
# (L07, contract stage-5 amendment APPROVED 2026-10-02): resolution.
# Binding is EDGES (one resolves row per reference, resolved or
# classed), names match bare + case-folded and nothing fuzzier, joins
# bind direction-free with coverage, the value bridge routes through
# PK-keyed value tables, parameters become nodes.

_TRUTHY_PK = {"Y", "YES", "TRUE", "1", True}


def _load_dictionary(dict_dir: Path) -> dict:
    def rd(name):
        return json.loads((dict_dir / name).read_text())
    cols = rd("02_emr_data_dictionary_extraction_column.json")
    joins = rd("02_emr_data_dictionary_extraction_join.json")
    vals = rd("02_emr_data_dictionary_extraction_value.json")

    tables, columns, pks = {}, {}, {}
    for c in cols:
        tu, cu = c["table_name"].upper(), c["column_name"].upper()
        tables[tu] = c["table_name"]
        columns.setdefault(tu, {})[cu] = c["column_name"]
        if c.get("is_primary_key") in _TRUTHY_PK:
            pks.setdefault(tu, set()).add(cu)

    # declared joins: direction-free pair sets, keyed by join_id,
    # kept with ordinals for coverage reporting
    by_id, pair_index = {}, {}
    for j in joins:
        pair = frozenset({(j["source_table_name"].upper(),
                           j["source_column_name"].upper()),
                          (j["destin_table_name"].upper(),
                           j["destin_column_name"].upper())})
        by_id.setdefault(j["join_id"], []).append(
            (j.get("ordinal", 1), pair))
        pair_index.setdefault(pair, []).append(j["join_id"])

    values = {}
    for v in vals:
        values.setdefault(v["table_name"].upper(), {})[
            str(v["code"])] = v["meaning"]

    return {"tables": tables, "columns": columns, "pks": pks,
            "joins": by_id, "pair_index": pair_index,
            "values": values}


def _basis(token: str, stored: str) -> str:
    return "exact" if token == stored else "fold"


def _value_route(dic: dict, table_u: str, col_u: str):
    """D5: direct when the subject column is the PK of a value-bearing
    table; else via ONE single-pair declared join whose far column is
    the far table's PK and the far table carries values."""
    if table_u in dic["values"] and col_u in dic["pks"].get(table_u,
                                                            ()):
        return table_u
    for join_id in sorted(dic["joins"]):
        rows = dic["joins"][join_id]
        if len(rows) != 1:
            continue
        pair = rows[0][1]
        if (table_u, col_u) in pair:
            (ot, oc), = [p for p in pair if p != (table_u, col_u)] \
                or [(None, None)]
            if (ot in dic["values"]
                    and oc in dic["pks"].get(ot, ())):
                return ot
    return None


def _deferred_types(library: dict) -> set:
    """Boolean ScriptDom types the denominator marks DEFERRED — met
    in real SQL they become visible counted rows, never red."""
    out = set()
    for r in library["sheets"]["TSQL_Denominator"]:
        if str(r["Disposition"]).startswith("DEFERRED"):
            out.update(re.findall(
                r"[A-Za-z]+(?:Predicate|Call|Expression)",
                r["ScriptDom type"]))
    return out


# PSEUDO-CODE — D13 the view class (10_work_wheel.md, ruled
# 2026-10-07; red tests: test_05 "the view class (D13)").
# APPROVED by Sunny 2026-10-07; the code follows:
#
#   1. _VIEW_UNWRAP = ("CreateViewStatement",
#      "CreateOrAlterViewStatement", "AlterViewStatement") — the
#      WHOLE class in one pass (the enumerate-all-cases law; the
#      proc trio is the precedent).
#   2. In _unwrapped: a view wrapper yields its stmt.SelectStatement
#      — a view's body is ONE SelectStatement, not a StatementList,
#      so it gets its own branch beside the _UNWRAP branch. A None
#      body (defensive; grammar should forbid it) falls through to
#      yield the wrapper itself — visible in the remainder, never
#      silently dropped.
#   3. NOTHING else changes: the yielded SELECT classifies
#      "handled" and maps scopes / structures / predicates exactly
#      as a proc body's SELECT does. File identity stays the
#      FILENAME (the proc precedent — the object name inside the
#      file is not consulted).
#   4. OUT OF SCOPE, flagged for Sunny: a declared column list
#      (CREATE VIEW v (a, b) AS SELECT x, y ...) renames the
#      projection in the header. This slice maps the SELECT's own
#      names and ignores the header list — zero cases in the
#      corpus so far; a follow-up ruling only if a work view
#      renames via the header.


def _unwrapped(stmts):
    """Ordered executable statements; wrappers contribute children."""
    for stmt in stmts:
        t = _type_name(stmt)
        if t in _UNWRAP:
            yield from _unwrapped(stmt.StatementList.Statements)
        elif t in _VIEW_UNWRAP and stmt.SelectStatement is not None:
            yield stmt.SelectStatement
        else:
            yield stmt


def _nested_children(stmt):
    """Statements a control-flow statement nests (the dotted-path law:
    nothing silently skipped at any depth)."""
    t = _type_name(stmt)
    kids = []
    if t == "IfStatement":
        if stmt.ThenStatement is not None:
            kids.extend(_unwrapped([stmt.ThenStatement]))
        if stmt.ElseStatement is not None:
            kids.extend(_unwrapped([stmt.ElseStatement]))
    elif t == "WhileStatement" and stmt.Statement is not None:
        kids.extend(_unwrapped([stmt.Statement]))
    return kids


def _base_name(schema_object):
    """The bare object name (last identifier): dbo.T -> T, #x -> #x.
    The dictionary's table names are bare — resolution needs bare."""
    return list(schema_object.Identifiers)[-1].Value


def _derived_tables_in_from(table_ref):
    """Yield QueryDerivedTable fragments under one FROM entry, in
    encounter order (joins recurse both sides; nothing skipped)."""
    t = _type_name(table_ref)
    if t == "QueryDerivedTable":
        yield table_ref
        yield from _derived_tables_in_query(table_ref.QueryExpression)
    elif t in ("QualifiedJoin", "UnqualifiedJoin"):
        yield from _derived_tables_in_from(table_ref.FirstTableReference)
        yield from _derived_tables_in_from(table_ref.SecondTableReference)
    # NamedTableReference and the rest: no derived tables underneath
    # that stage 2 can see (predicate-level subqueries are stage 4 —
    # contract stage-4 note b).


def _derived_tables_in_query(query):
    """Yield QueryDerivedTable fragments anywhere in a query
    expression's FROM level (UNION arms included)."""
    t = _type_name(query)
    if t == "QueryParenthesisExpression":
        yield from _derived_tables_in_query(query.QueryExpression)
    elif t == "BinaryQueryExpression":
        yield from _derived_tables_in_query(query.FirstQueryExpression)
        yield from _derived_tables_in_query(query.SecondQueryExpression)
    elif t == "QuerySpecification" and query.FromClause:
        for tr in query.FromClause.TableReferences:
            yield from _derived_tables_in_from(tr)


def _entry(name_key, scope_name, scope_kind, operation, evidence,
           query=None, where_clause=None):
    return {"name_key": name_key, "scope_name": scope_name,
            "scope_kind": scope_kind, "operation": operation,
            "evidence": evidence, "query": query,
            "where_clause": where_clause}


def _scopes_for(stmt, kind, text):
    """STAGE 2: the scopes one population statement mints, in edge
    order — CTEs in WITH order, subqueries in encounter order, the
    MAIN scope LAST (the amendment's edge-position law). name_key
    None = positional (subquery). Each entry carries its query
    expression so STAGE 3 can walk its structures."""
    t = _type_name(stmt)
    scopes = []
    queries = []  # query expressions to sweep for derived tables

    main = None
    if t == "SelectStatement":
        if stmt.WithCtesAndXmlNamespaces:
            for cte in stmt.WithCtesAndXmlNamespaces.CommonTableExpressions:
                name = cte.ExpressionName.Value
                scopes.append(_entry(name, name, "cte", "select",
                                     _evidence(text, cte),
                                     query=cte.QueryExpression))
        queries.append(stmt.QueryExpression)
        ev = _evidence(text, stmt.QueryExpression)
        if stmt.Into is not None:
            name = _base_name(stmt.Into)
            sk = "temp_table" if name.startswith("#") else "write_target"
            main = _entry(name, name, sk, "select", ev,
                          query=stmt.QueryExpression)
        else:
            main = _entry("delivery", "delivery", "delivery", "select",
                          ev, query=stmt.QueryExpression)
    elif t == "InsertStatement":
        spec = stmt.InsertSpecification
        name = _base_name(spec.Target.SchemaObject)
        src = spec.InsertSource
        select = (src.Select
                  if _type_name(src) == "SelectInsertSource" else None)
        if select is not None:
            queries.append(select)
        main = _entry(name, name, "write_target", "insert",
                      _evidence(text, stmt), query=select)
    elif t == "UpdateStatement":
        spec = stmt.UpdateSpecification
        name = (_base_name(spec.Target.SchemaObject)
                if _type_name(spec.Target) == "NamedTableReference"
                else None)
        main = _entry(name or "target", name, "write_target", "update",
                      _evidence(text, stmt),
                      where_clause=spec.WhereClause)
    elif t == "DeleteStatement":
        spec = stmt.DeleteSpecification
        name = (_base_name(spec.Target.SchemaObject)
                if _type_name(spec.Target) == "NamedTableReference"
                else None)
        main = _entry(name or "target", name, "write_target", "delete",
                      _evidence(text, stmt),
                      where_clause=spec.WhereClause)

    for query in queries:
        for derived in _derived_tables_in_query(query):
            scopes.append(_entry(None, None, "subquery", "select",
                                 _evidence(text, derived),
                                 query=derived.QueryExpression))
    if main is not None:
        scopes.append(main)  # main scope last
    return scopes


# ---------------------------------------------------------------- STAGE 3
# (L05, contract stage-3 amendment APPROVED 2026-10-02): each scope's
# clause skeleton as structure nodes from the closed clause set
# (library sheet Clause_Structure_Kinds). Combination arms are FULL
# scopes (union_arm) — never an empty combination.

def _unparen(query):
    while _type_name(query) == "QueryParenthesisExpression":
        query = query.QueryExpression
    return query


def _flatten_arms(query):
    """Immediate arms of a combination; same-(type, all) chains
    flatten in order, different combinations stay nested (the nested
    arm becomes a union_arm scope carrying its own COMBINATION)."""
    key = (str(query.BinaryQueryExpressionType), bool(query.All))

    def rec(side):
        side = _unparen(side)
        if (_type_name(side) == "BinaryQueryExpression"
                and (str(side.BinaryQueryExpressionType),
                     bool(side.All)) == key):
            return rec(side.FirstQueryExpression) \
                + rec(side.SecondQueryExpression)
        return [side]

    return rec(query.FirstQueryExpression) \
        + rec(query.SecondQueryExpression)


def _join_type(table_ref, text):
    t = _type_name(table_ref)
    if t == "QualifiedJoin":
        return str(table_ref.QualifiedJoinType)
    jt = str(table_ref.UnqualifiedJoinType)
    if jt in ("CrossApply", "OuterApply"):
        return jt
    # ScriptDom parses both `CROSS JOIN` and the comma join as
    # CrossJoin — the evidence text tells them apart (the comma-join
    # class was invisible in the prior estate until found by sweep).
    frag = _evidence(text, table_ref)["fragment"].upper()
    return "Cross" if "CROSS" in frag.split() else "comma"


# ---------------------------------------------------------------- STAGE 4
# (L06, contract stage-4 amendment APPROVED 2026-10-02): predicates +
# expressions. The operator is the predicate's KIND (closed 13); roles
# ride the contains edges; boolean AND/OR/NOT append to the structure
# sheet; parentheses dissolve; logic is never rewritten (no De Morgan).

# schema-mirror kg2_kind_library: Predicate_Kinds + TSQL_Denominator
COMPARISON_KINDS = {
    "Equals": "COMPARE_EQ",
    "NotEqualToBrackets": "COMPARE_NEQ",
    "NotEqualToExclamation": "COMPARE_NEQ",
    "GreaterThan": "COMPARE_GT",
    "GreaterThanOrEqualTo": "COMPARE_GTE",
    "LessThan": "COMPARE_LT",
    "LessThanOrEqualTo": "COMPARE_LTE",
}
PREDICATE_TYPE_MIRROR = {
    "BooleanComparisonExpression", "LikePredicate", "InPredicate",
    "BooleanTernaryExpression", "BooleanIsNullExpression",
    "ExistsPredicate", "SubqueryComparisonPredicate",
}
BOOLEAN_SHAPE_TYPES = {
    "BooleanBinaryExpression", "BooleanNotExpression",
    "BooleanParenthesisExpression",
}
_LITERAL_TYPES = {
    "IntegerLiteral", "NumericLiteral", "MoneyLiteral", "RealLiteral",
    "StringLiteral", "NullLiteral", "IdentifierLiteral",
    "BinaryLiteral", "MaxLiteral", "DefaultLiteral", "OdbcLiteral",
}
_CAST_TYPES = {"CastCall", "ConvertCall", "TryCastCall",
               "TryConvertCall"}


def _next_child(ctx, parent_id, family):
    key = (parent_id, family)
    n = ctx["child_counts"][key] = ctx["child_counts"].get(key, 0) + 1
    return n


def _unparen_bool(cond):
    while _type_name(cond) == "BooleanParenthesisExpression":
        cond = cond.Expression  # parentheses dissolve (ratified)
    return cond


def _emit_expr(ctx, parent_id, expr, role=None, output_name=None,
               descending=None):
    """One expression row (+ its nested children). Role rides the
    contains edge AND is mirrored on the row. Returns the node_id."""
    while _type_name(expr) == "ParenthesisExpression":
        expr = expr.Expression
    text = ctx["text"]
    t = _type_name(expr)
    n = _next_child(ctx, parent_id, "expr")
    node_id = f"{parent_id}::expr/{n}"
    ev = _evidence(text, expr)
    row = {"node_id": node_id, "expression_kind": None,
           "raw_text": ev["fragment"], "role": role, "position": n,
           "evidence": ev}
    if output_name is not None:
        row["output_name"] = output_name
    if descending:
        row["descending"] = True
    ctx["expression_rows"].append(row)
    ctx["expr_by_id"][node_id] = row
    ctx["edges"].append({"from_id": parent_id, "to_id": node_id,
                         "position": str(n), "role": role})

    if t == "ColumnReferenceExpression":
        row["expression_kind"] = "column_ref"
        # COUNT(*)'s argument is a column reference with a wildcard
        # and NO identifier — ref "*" (classed wildcard at stage 5).
        row["ref"] = ("*" if expr.MultiPartIdentifier is None
                      else ".".join(
                          i.Value for i in
                          expr.MultiPartIdentifier.Identifiers))
        ctx["pending_refs"].append(
            {"expr_id": node_id, "kind": "column",
             "ref": row["ref"], "scope": ctx["current_scope"]})
    elif t in _LITERAL_TYPES:
        row["expression_kind"] = "literal"
        row["value"] = (expr.Value if hasattr(expr, "Value")
                        else ev["fragment"])
    elif t == "VariableReference":
        row["expression_kind"] = "parameter_ref"
        row["ref"] = expr.Name
        ctx["pending_refs"].append(
            {"expr_id": node_id, "kind": "parameter",
             "ref": expr.Name, "scope": ctx["current_scope"]})
    elif t == "FunctionCall":
        row["expression_kind"] = "function"
        row["name"] = expr.FunctionName.Value
        if expr.OverClause is not None:
            # OVER contents stay verbatim here; their structural
            # capture is the grain family's need and lands with
            # phase 06 (declared deferral, not a silent cap).
            row["over_text"] = _evidence(text,
                                         expr.OverClause)["fragment"]
        for p in expr.Parameters:
            _emit_expr(ctx, node_id, p)
    elif t == "CoalesceExpression":
        row["expression_kind"] = "function"
        row["name"] = "COALESCE"
        for p in expr.Expressions:
            _emit_expr(ctx, node_id, p)
    elif t == "NullIfExpression":
        row["expression_kind"] = "function"
        row["name"] = "NULLIF"
        _emit_expr(ctx, node_id, expr.FirstExpression)
        _emit_expr(ctx, node_id, expr.SecondExpression)
    elif t in ("LeftFunctionCall", "RightFunctionCall"):
        row["expression_kind"] = "function"
        row["name"] = t[:-12].upper()
        for p in expr.Parameters:
            _emit_expr(ctx, node_id, p)
    elif t == "ParameterlessCall":
        row["expression_kind"] = "function"
        row["name"] = str(expr.ParameterlessCallType).upper()
    elif t == "BinaryExpression":
        row["expression_kind"] = "arithmetic"
        row["op"] = str(expr.BinaryExpressionType)
        _emit_expr(ctx, node_id, expr.FirstExpression)
        _emit_expr(ctx, node_id, expr.SecondExpression)
    elif t == "UnaryExpression":
        row["expression_kind"] = "unary"
        row["op"] = str(expr.UnaryExpressionType)
        _emit_expr(ctx, node_id, expr.Expression)
    elif t in _CAST_TYPES:
        row["expression_kind"] = "cast"
        _emit_expr(ctx, node_id, expr.Parameter)
    elif t in ("SearchedCaseExpression", "SimpleCaseExpression"):
        row["expression_kind"] = "case"
        if t == "SimpleCaseExpression":
            _emit_expr(ctx, node_id, expr.InputExpression,
                       role="subject")
        for w in expr.WhenClauses:
            if t == "SearchedCaseExpression":
                _emit_pred_tree(ctx, node_id, w.WhenExpression,
                                edge_role="condition")
            else:
                _emit_expr(ctx, node_id, w.WhenExpression,
                           role="comparand")
            _emit_expr(ctx, node_id, w.ThenExpression)
        if expr.ElseExpression is not None:
            _emit_expr(ctx, node_id, expr.ElseExpression)
    elif t == "IIfCall":
        # IIF(cond, a, b) is value branching — a two-branch CASE in
        # sugar form; the ratified `case` kind covers it (closed set
        # stays closed, the L06 corpus build's red-build find).
        row["expression_kind"] = "case"
        _emit_pred_tree(ctx, node_id, expr.Predicate,
                        edge_role="condition")
        _emit_expr(ctx, node_id, expr.ThenExpression)
        _emit_expr(ctx, node_id, expr.ElseExpression)
    elif t == "ScalarSubquery":
        row["expression_kind"] = "subquery_ref"
        row["scope_id"] = _mint_subquery(ctx, expr.QueryExpression,
                                         _evidence(text, expr))
    else:
        raise RuntimeError(
            f"RED BUILD: unmapped expression construct {t} at "
            f"L{ev['line']} ({ev['fragment'][:60]!r}) — rule it into "
            "the closed set or the library before building on.")
    return node_id


def _emit_pred_leaf(ctx, parent_id, cond, edge_role, extra_negate):
    text = ctx["text"]
    t = _type_name(cond)
    n = _next_child(ctx, parent_id, "pred")
    node_id = f"{parent_id}::pred/{n}"
    row = {"node_id": node_id, "predicate_kind": None,
           "negated": extra_negate, "position": n,
           "on_class": None,  # stamped at stage 5 under JOINs (D4)
           "evidence": _evidence(text, cond)}
    ctx["predicate_rows"].append(row)
    ctx["edges"].append({"from_id": parent_id, "to_id": node_id,
                         "position": str(n), "role": edge_role})

    if t == "BooleanComparisonExpression":
        kind = COMPARISON_KINDS.get(str(cond.ComparisonType))
        if kind is None:  # the denominator's deferred comparison row
            row["predicate_kind"] = (
                f"DEFERRED:BooleanComparisonExpression:"
                f"{cond.ComparisonType}")
            return
        row["predicate_kind"] = kind
        subj = _emit_expr(ctx, node_id, cond.FirstExpression,
                          role="subject")
        comp = _emit_expr(ctx, node_id, cond.SecondExpression,
                          role="comparand")
        ctx["pending_values"].append(
            {"subject": subj, "comparands": [comp],
             "scope": ctx["current_scope"]})
    elif t == "LikePredicate":
        row["predicate_kind"] = "PATTERN_MATCH"
        row["negated"] = bool(cond.NotDefined) ^ extra_negate
        _emit_expr(ctx, node_id, cond.FirstExpression, role="subject")
        _emit_expr(ctx, node_id, cond.SecondExpression, role="pattern")
        if cond.EscapeExpression is not None:
            _emit_expr(ctx, node_id, cond.EscapeExpression,
                       role="escape")
    elif t == "InPredicate":
        row["negated"] = bool(cond.NotDefined) ^ extra_negate
        subj = _emit_expr(ctx, node_id, cond.Expression,
                          role="subject")
        if cond.Subquery is not None:
            row["predicate_kind"] = "IN_SELECTION"
            _emit_expr(ctx, node_id, cond.Subquery, role="selection")
        else:
            row["predicate_kind"] = "IN_LIST"
            members = [_emit_expr(ctx, node_id, v, role="comparand")
                       for v in cond.Values]
            ctx["pending_values"].append(
                {"subject": subj, "comparands": members,
                 "scope": ctx["current_scope"]})
    elif t == "BooleanTernaryExpression":
        row["predicate_kind"] = "RANGE"
        row["negated"] = ("Not" in str(cond.TernaryExpressionType)) \
            ^ extra_negate
        _emit_expr(ctx, node_id, cond.FirstExpression, role="subject")
        _emit_expr(ctx, node_id, cond.SecondExpression,
                   role="lower_bound")
        _emit_expr(ctx, node_id, cond.ThirdExpression,
                   role="upper_bound")
    elif t == "BooleanIsNullExpression":
        row["predicate_kind"] = "NULL_CHECK"
        row["negated"] = bool(cond.IsNot) ^ extra_negate
        _emit_expr(ctx, node_id, cond.Expression, role="subject")
    elif t == "ExistsPredicate":
        row["predicate_kind"] = "EXISTS_SELECTION"
        _emit_expr(ctx, node_id, cond.Subquery, role="selection")
    elif t == "SubqueryComparisonPredicate":
        row["predicate_kind"] = "QUANTIFIED_COMPARE"
        row["comparison_op"] = str(cond.ComparisonType)
        row["quantifier"] = str(cond.SubqueryComparisonPredicateType)
        _emit_expr(ctx, node_id, cond.Expression, role="subject")
        _emit_expr(ctx, node_id, cond.Subquery, role="selection")
    elif t in ctx["deferred_types"]:
        row["predicate_kind"] = f"DEFERRED:{t}"  # visible, counted
    else:
        ev = row["evidence"]
        raise RuntimeError(
            f"RED BUILD: boolean type {t} is beyond the "
            f"TSQL_Denominator (L{ev['line']}: {ev['fragment'][:60]!r})"
            " — add a denominator row (mapped or DEFERRED) before "
            "building on.")


def _emit_pred_tree(ctx, parent_id, cond, edge_role=None):
    """One condition tree under parent_id: AND/OR/NOT shape to the
    structure sheet, leaves to the predicate sheet. Single-predicate
    negation folds to the flag; NOT over a group stays a NOT node."""
    cond = _unparen_bool(cond)
    t = _type_name(cond)
    if t == "BooleanBinaryExpression":
        kind = str(cond.BinaryExpressionType).upper()  # AND | OR

        def arms(side):
            side = _unparen_bool(side)
            if (_type_name(side) == "BooleanBinaryExpression"
                    and str(side.BinaryExpressionType).upper() == kind):
                return arms(side.FirstExpression) \
                    + arms(side.SecondExpression)
            return [side]

        node_id = _emit_bool_structure(ctx, parent_id, kind, cond,
                                       edge_role)
        for child in arms(cond.FirstExpression) \
                + arms(cond.SecondExpression):
            _emit_pred_tree(ctx, node_id, child)
    elif t == "BooleanNotExpression":
        inner = _unparen_bool(cond.Expression)
        if _type_name(inner) in ("BooleanBinaryExpression",
                                 "BooleanNotExpression"):
            node_id = _emit_bool_structure(ctx, parent_id, "NOT", cond,
                                           edge_role)
            _emit_pred_tree(ctx, node_id, inner)
        else:  # NOT over one predicate folds to the flag
            _emit_pred_leaf(ctx, parent_id, inner, edge_role,
                            extra_negate=True)
    else:
        _emit_pred_leaf(ctx, parent_id, cond, edge_role,
                        extra_negate=False)


def _emit_bool_structure(ctx, parent_id, kind, cond, edge_role):
    n = _next_child(ctx, parent_id, f"structure/{kind}")
    node_id = f"{parent_id}::structure/{kind}/{n}"
    ctx["structure_rows"].append({
        "node_id": node_id, "structure_kind": kind, "position": n,
        "owning_scope": ctx["current_scope"],
        "evidence": _evidence(ctx["text"], cond)})
    ctx["edges"].append({"from_id": parent_id, "to_id": node_id,
                         "position": str(n), "role": edge_role})
    return node_id


def _mint_subquery(ctx, query, evidence):
    """A predicate-level subquery scope: numbering CONTINUES the
    statement's subN counter; the scope is FULL — structures and
    predicates recurse (never an empty scope)."""
    stmt_id = ctx["current_statement"]
    n = ctx["sub_counts"][stmt_id] = ctx["sub_counts"].get(stmt_id,
                                                           0) + 1
    scope_id = f"{stmt_id}::scope/sub{n}"
    ctx["scope_rows"].append({
        "node_id": scope_id, "scope_name": None,
        "scope_kind": "subquery", "operation": "select",
        "owning_statement": stmt_id, "evidence": evidence})
    ctx["edges"].append({"from_id": stmt_id, "to_id": scope_id,
                         "position": f"sub{n}", "role": None})
    _emit_structures(ctx, scope_id, stmt_id, query)
    return scope_id


def _emit_structures(ctx, scope_id, owning_statement, query):
    """Walk one scope's query expression into structure rows (stage
    3) and their predicates/expressions (stage 4); a combination
    mints arm scopes and recurses into them."""
    text = ctx["text"]
    prior_scope = ctx["current_scope"]
    ctx["current_scope"] = scope_id
    ctx["scope_parent"][scope_id] = prior_scope
    pos = 0
    kind_counts = {}

    def add(kind, evidence, **props):
        nonlocal pos
        pos += 1
        k = kind_counts[kind] = kind_counts.get(kind, 0) + 1
        row = {"node_id": f"{scope_id}::structure/{kind}/{k}",
               "structure_kind": kind, "position": pos,
               "owning_scope": scope_id, "evidence": evidence}
        row.update(props)
        ctx["structure_rows"].append(row)
        ctx["edges"].append({"from_id": scope_id,
                             "to_id": row["node_id"],
                             "position": str(pos), "role": None})
        return row

    try:
        query = _unparen(query)
        t = _type_name(query)

        if t == "BinaryQueryExpression":
            combo = add("COMBINATION", _evidence(text, query),
                        combination_type=str(
                            query.BinaryQueryExpressionType),
                        all=bool(query.All))
            for i, arm_q in enumerate(_flatten_arms(query), start=1):
                arm_id = f"{scope_id}::arm{i}"
                ctx["scope_rows"].append({
                    "node_id": arm_id, "scope_name": None,
                    "scope_kind": "union_arm", "operation": "select",
                    "owning_statement": owning_statement,
                    "evidence": _evidence(text, arm_q),
                })
                ctx["edges"].append({"from_id": combo["node_id"],
                                     "to_id": arm_id,
                                     "position": str(i), "role": None})
                _emit_structures(ctx, arm_id, owning_statement, arm_q)
            return

        if t != "QuerySpecification":
            return  # unmapped query shape — nothing invented

        els = list(query.SelectElements)
        start = els[0].StartOffset
        end = els[-1].StartOffset + els[-1].FragmentLength
        proj = add("PROJECTION",
                   {"fragment": text[start:end],
                    "line": els[0].StartLine,
                    "column": els[0].StartColumn},
                   distinct=str(query.UniqueRowFilter) == "Distinct",
                   member_total=len(els), star_total=0,
                   star_qualifiers=[])
        memb = ctx["scope_members"].setdefault(
            scope_id, {"members": {}, "star": False})
        for el in els:
            et = _type_name(el)
            if et == "SelectScalarExpression":
                inner = el.Expression
                while _type_name(inner) == "ParenthesisExpression":
                    inner = inner.Expression
                if el.ColumnName is not None:
                    name = el.ColumnName.Value
                elif (_type_name(inner) == "ColumnReferenceExpression"
                        and inner.MultiPartIdentifier is not None):
                    name = list(inner.MultiPartIdentifier
                                .Identifiers)[-1].Value
                else:
                    name = None  # anonymous output column, legal
                member_id = _emit_expr(ctx, proj["node_id"],
                                       el.Expression, output_name=name)
                if name is not None:
                    memb["members"].setdefault(name.upper(), member_id)
            elif et == "SelectStarExpression":
                # the ratified star meaning: every column of the
                # source at read time — counted, never a row
                proj["star_total"] += 1
                proj["star_qualifiers"].append(
                    ".".join(i.Value
                             for i in el.Qualifier.Identifiers)
                    if el.Qualifier else None)
                memb["star"] = True
            else:
                raise RuntimeError(
                    f"RED BUILD: unmapped select element {et}")
        if query.TopRowFilter is not None:
            top = query.TopRowFilter
            trow = add("TOP", _evidence(text, top),
                       top_text=_evidence(text,
                                          top.Expression)["fragment"])
            _emit_expr(ctx, trow["node_id"], top.Expression)
        if query.FromClause is not None:
            from_row = add("FROM", _evidence(text, query.FromClause))
            sources = ctx["scope_sources"].setdefault(scope_id, [])

            def source(table_ref):
                """STAGE 5 catch-up: table_ref expression rows for
                named tables + the scope's source entries (alias
                map, scope reads, table functions)."""
                tt = _type_name(table_ref)
                alias = (table_ref.Alias.Value
                         if getattr(table_ref, "Alias", None) is not None
                         else None)
                if tt == "NamedTableReference":
                    ids = [i.Value for i in
                           table_ref.SchemaObject.Identifiers]
                    n = _next_child(ctx, from_row["node_id"], "expr")
                    eid = f"{from_row['node_id']}::expr/{n}"
                    ev = _evidence(text, table_ref)
                    erow = {"node_id": eid,
                            "expression_kind": "table_ref",
                            "raw_text": ev["fragment"],
                            "role": None, "position": n,
                            "evidence": ev, "ref": ".".join(ids),
                            "alias": alias}
                    ctx["expression_rows"].append(erow)
                    ctx["expr_by_id"][eid] = erow
                    ctx["edges"].append(
                        {"from_id": from_row["node_id"], "to_id": eid,
                         "position": str(n), "role": None})
                    sources.append({"alias": alias, "bare": ids[-1],
                                    "kind": "named", "expr_id": eid})
                elif tt == "QueryDerivedTable":
                    key = (table_ref.StartLine, table_ref.StartColumn)
                    sources.append(
                        {"alias": alias, "bare": None,
                         "kind": "scope",
                         "target": ctx["subscope_by_pos"].get(key)})
                elif tt in ("QualifiedJoin", "UnqualifiedJoin"):
                    source(table_ref.FirstTableReference)
                    source(table_ref.SecondTableReference)
                elif tt.endswith("FunctionTableReference"):
                    ev = _evidence(text, table_ref)
                    n = _next_child(ctx, from_row["node_id"], "expr")
                    eid = f"{from_row['node_id']}::expr/{n}"
                    erow = {"node_id": eid,
                            "expression_kind": "table_ref",
                            "raw_text": ev["fragment"],
                            "role": None, "position": n,
                            "evidence": ev, "ref": ev["fragment"],
                            "alias": alias}
                    ctx["expression_rows"].append(erow)
                    ctx["expr_by_id"][eid] = erow
                    ctx["edges"].append(
                        {"from_id": from_row["node_id"], "to_id": eid,
                         "position": str(n), "role": None})
                    sources.append({"alias": alias, "bare": None,
                                    "kind": "tfunc", "expr_id": eid})
                else:
                    ev = _evidence(text, table_ref)
                    sources.append({"alias": alias, "bare": None,
                                    "kind": "unmapped",
                                    "frag": ev["fragment"]})

            def joins(table_ref):
                tt = _type_name(table_ref)
                if tt in ("QualifiedJoin", "UnqualifiedJoin"):
                    joins(table_ref.FirstTableReference)
                    joins(table_ref.SecondTableReference)
                    ev = (_evidence(text, table_ref.SearchCondition)
                          if tt == "QualifiedJoin"
                          else _evidence(text, table_ref))
                    jrow = add("JOIN", ev,
                               join_type=_join_type(table_ref, text))
                    if tt == "QualifiedJoin":
                        _emit_pred_tree(ctx, jrow["node_id"],
                                        table_ref.SearchCondition)

            refs = list(query.FromClause.TableReferences)
            for tr in refs:
                source(tr)
                joins(tr)
            # The comma join: `FROM T1, T2` arrives as MULTIPLE
            # entries in TableReferences, not as a join node — n
            # sources at the clause level are n-1 comma joins (the
            # prior estate's invisible-reads class, named here).
            for tr in refs[1:]:
                add("JOIN", _evidence(text, tr), join_type="comma")
        if query.WhereClause is not None:
            wrow = add("WHERE", _evidence(text, query.WhereClause))
            _emit_pred_tree(ctx, wrow["node_id"],
                            query.WhereClause.SearchCondition)
        if query.GroupByClause is not None:
            grow = add("GROUP BY",
                       _evidence(text, query.GroupByClause))
            for spec in query.GroupByClause.GroupingSpecifications:
                if _type_name(spec) != "ExpressionGroupingSpecification":
                    raise RuntimeError(
                        "RED BUILD: unmapped grouping specification "
                        f"{_type_name(spec)}")
                _emit_expr(ctx, grow["node_id"], spec.Expression)
        if query.HavingClause is not None:
            hrow = add("HAVING", _evidence(text, query.HavingClause))
            _emit_pred_tree(ctx, hrow["node_id"],
                            query.HavingClause.SearchCondition)
        if query.OrderByClause is not None:
            orow = add("ORDER BY",
                       _evidence(text, query.OrderByClause))
            for el in query.OrderByClause.OrderByElements:
                _emit_expr(ctx, orow["node_id"], el.Expression,
                           descending=str(el.SortOrder) == "Descending")
    finally:
        ctx["current_scope"] = prior_scope


_PROC_TYPES = ("CreateProcedureStatement",
               "CreateOrAlterProcedureStatement",
               "AlterProcedureStatement")


def _add_param(ctx, name, kind, dtype_frag, default_frag, ev):
    key = name.upper()
    if key in ctx["param_registry"]:
        return
    node_id = f"{ctx['file_id']}::param/{name}"
    ctx["param_registry"][key] = node_id
    pos = len(ctx["param_registry"])
    ctx["param_rows"].append({
        "node_id": node_id, "name": name, "kind": kind,
        "data_type": dtype_frag, "default_text": default_frag,
        "evidence": ev})
    ctx["edges"].append({"from_id": ctx["file_id"], "to_id": node_id,
                         "position": str(pos), "role": None})


def _collect_proc_params(ctx, stmt, text):
    """D6: the CREATE PROCEDURE header's parameters — Phase IV's
    future knobs."""
    if _type_name(stmt) not in _PROC_TYPES:
        return
    for p in stmt.Parameters:
        _add_param(
            ctx, p.VariableName.Value, "procedure_parameter",
            _evidence(text, p.DataType)["fragment"]
            if p.DataType is not None else None,
            _evidence(text, p.Value)["fragment"]
            if p.Value is not None else None,
            _evidence(text, p))


# ---- D3 STAR EXPANSION (contract D3 as REOPENED 2026-10-02) --------
# PSEUDO CODE — APPROVED 2026-10-02 (Sunny: "go"), both sub-rulings
# as proposed: the mixed case keeps the behind_star remainder; the
# union name-vs-position bound stands as recorded below.
#
# _expand_star(ctx, scope_id, col_u, seen=None) -> (origins, blind)
#   PURPOSE: a column read lands on a scope whose outputs carry a
#   star. Walk the graph's OWN stored outputs to find the column's
#   true origin(s) — never the dictionary, never the run-time
#   catalog. Only stored graph truth binds.
#   RETURNS:
#     origins — ordered list of projection-member expression ids,
#       one per star-carrying unit whose source holds col_u
#       explicitly (unit order: the scope itself, then its union
#       arms in arm order — deterministic, same input same rows).
#     blind — True when any star path dead-ends where the graph
#       cannot see: a base-table source, a table function, an
#       unknown source — or a source scope that lacks the name
#       (in a union, that arm still feeds the position; we cannot
#       NAME what it feeds, so it is blind, never guessed).
#   WALK: for each star-carrying unit of scope_id (the scope's own
#     members entry if star=True, plus every scope_id::arm* entry
#     with star=True):
#       for each source of that unit (ctx scope_sources):
#         source resolves to a SCOPE ->
#           members, star2 = _members_of(target)
#           col_u in members -> origins += [members[col_u]]
#           elif star2       -> recurse into target (seen set
#                               guards cycles; depth-first)
#           else             -> blind = True   (arm lacks the name)
#         source resolves to a TABLE / tfunc / unknown ->
#           blind = True     (the genuinely blind class)
#   EMISSION at BOTH bind sites (bind_in_source's scope branch;
#   the unqualified single-star-source branch):
#     origins, not blind -> one resolves row PER ORIGIN:
#         to_kind=member, to_id=origin, match_basis=star_member
#     origins AND blind  -> the star_member rows PLUS exactly one
#         behind_star row recording the blind remainder
#         [SUNNY'S CALL at approval: zero corpus cases today;
#          alternative = collapse the whole read to behind_star]
#     no origins, blind  -> one behind_star row (exactly today's)
#     no origins, clean  -> unresolved scope_column_missing
#         (today this case lands behind_star whenever the star
#          flag is up — the amendment makes a name NO arm holds
#          an honest miss instead)
#   UNION NAME-vs-POSITION (recorded honesty bound): union output
#     names come from the FIRST arm; later arms feed by POSITION.
#     Name-matching later arms equals the positional truth exactly
#     when the arm's source shares the name (our corpus: always —
#     parallel-built temps). Where a later arm's source lacks the
#     name, that arm is BLIND (above), never name-guessed.
#     Positional ordinal mapping (star offsets) is deliberately
#     NOT built — zero corpus need; if a mismatch estate ever
#     arrives it is a new ruling, per the placeholder law.
#   CONSERVATION AMENDMENT: the one-row-per-reference law becomes
#     one BINDING per reference; a star_member binding may span N
#     rows (same from_id, one per origin) plus at most one
#     behind_star remainder. The contract test encodes this shape.
#   EXPECTED CORPUS CENSUS (prediction, to be confirmed red->green):
#     behind_star 67 -> 0; star_member rows = 59*2 (#combined_census
#     reads, both arms) + 8 (#coverage -> matching_coverages) = 126.
# --------------------------------------------------------------------


def _expand_star(ctx, sources_at, scope_id, col_u, seen=None):
    """-> (origins, blind, miss). origins: member expr ids, unit
    order (scope, then arms), deduped; blind: some star path is
    structurally unseeable (base table / tfunc / unknown source);
    miss: some explicit source scope lacks the name."""
    seen = set() if seen is None else seen
    if scope_id in seen:
        return [], False, False
    seen.add(scope_id)
    units = [u for u in
             [scope_id] + sorted(k for k in ctx["scope_members"]
                                 if k.startswith(f"{scope_id}::arm"))
             if ctx["scope_members"].get(u, {}).get("star")]
    origins, blind, miss = [], False, False
    for unit in units:
        for src in sources_at(unit):
            if src.get("rkind") == "scope" and src.get("target"):
                members, star2 = _members_of(ctx, src["target"])
                if col_u in members:
                    origins.append(members[col_u])
                elif star2:
                    o2, b2, m2 = _expand_star(ctx, sources_at,
                                              src["target"], col_u,
                                              seen)
                    origins.extend(o2)
                    blind, miss = blind or b2, miss or m2
                else:
                    miss = True
            else:
                blind = True
    return list(dict.fromkeys(origins)), blind, miss


def _members_of(ctx, scope_id):
    """A scope's output columns; a combination scope merges its
    arms' (the #combined_census case)."""
    base = ctx["scope_members"].get(scope_id,
                                    {"members": {}, "star": False})
    members, star = dict(base["members"]), base["star"]
    for key, m in ctx["scope_members"].items():
        if key.startswith(f"{scope_id}::arm"):
            for k, v in m["members"].items():
                members.setdefault(k, v)
            star = star or m["star"]
    return members, star


def _classify(stmt, operational: set, gap_classes: set):
    """-> (statement_kind, disposition, gap_class)."""
    t = _type_name(stmt)
    if t in HANDLED_KINDS:
        kind = HANDLED_KINDS[t]
        if t == "SelectStatement" and stmt.Into is not None:
            kind = "SELECT INTO"
        return kind, "handled", None
    if t in operational:
        return t, "operational", None
    # Decision 9 (schema-mirror: library Statement_Gap_Classes): EXEC
    # of a STRING is the dynamic_sql gap; a procedure-call EXEC is NOT
    # this class and stays visibly in the remainder until ruled.
    if t == "ExecuteStatement" and "dynamic_sql" in gap_classes:
        entity = stmt.ExecuteSpecification.ExecutableEntity
        if _type_name(entity) == "ExecutableStringList":
            return "EXEC", "gap", "dynamic_sql"
    return t, "remainder", None  # the kind repeats the ScriptDom type


def _resolve_file(ctx, dic, stem):
    """STAGE 5's post-pass: after the whole file is walked (so every
    scope's sources, members and parameters exist), run every binding
    attempt and write one resolves row per reference."""
    rows = ctx["resolves_rows"]
    resolved_cols = {}     # expr_id -> (TABLE_U, COL_U)
    scope_bound = set()    # expr_ids bound to scopes/members

    def out(from_id, ref_text, **kw):
        rows.append({"from_id": from_id, "ref_text": ref_text, **kw})

    def chain(scope_id):
        while scope_id is not None:
            yield scope_id
            scope_id = ctx["scope_parent"].get(scope_id)

    def classify_source(src):
        if "rkind" in src:
            return src
        if src["kind"] == "named":
            bu = src["bare"].upper()
            if bu in ctx["named_scopes"]:
                src.update(rkind="scope",
                           target=ctx["named_scopes"][bu])
            elif bu in dic["tables"]:
                src.update(rkind="table", target=dic["tables"][bu],
                           basis=_basis(src["bare"],
                                        dic["tables"][bu]))
            else:
                src.update(rkind="unknown")
        elif src["kind"] == "scope":
            src.update(rkind="scope")
        elif src["kind"] == "tfunc":
            src.update(rkind="tfunc")
        else:
            src.update(rkind="unknown")
        return src

    def sources_at(scope_id):
        return [classify_source(s)
                for s in ctx["scope_sources"].get(scope_id, [])]

    # ---- table_ref rows (the FROM sources themselves)
    for scope_id in ctx["scope_sources"]:
        for src in sources_at(scope_id):
            eid = src.get("expr_id")
            if eid is None:
                continue
            ref = ctx["expr_by_id"][eid]["ref"]
            if src["rkind"] == "table":
                out(eid, ref, to_kind="table", to_id=src["target"],
                    match_basis=src["basis"])
            elif src["rkind"] == "scope" and src.get("target"):
                out(eid, ref, to_kind="scope", to_id=src["target"],
                    match_basis="fold")
                scope_bound.add(eid)
            elif src["rkind"] == "tfunc":
                out(eid, ref, to_kind="unresolved", to_id=None,
                    **{"class": "table_function"})
            else:
                out(eid, ref, to_kind="unresolved", to_id=None,
                    **{"class": "unknown_table"})

    # ---- column references
    def bind_through_star(eid, ref, scope_target, col_u):
        """D3 as reopened: emit the star-expansion outcome rows."""
        origins, blind, miss = _expand_star(ctx, sources_at,
                                            scope_target, col_u)
        if origins:
            for origin in origins:
                out(eid, ref, to_kind="member", to_id=origin,
                    match_basis="star_member")
            if blind or miss:  # the blind-remainder sub-ruling
                out(eid, ref, to_kind="scope", to_id=scope_target,
                    match_basis="behind_star")
        elif blind:
            out(eid, ref, to_kind="scope", to_id=scope_target,
                match_basis="behind_star")
        else:  # a name NO arm holds: an honest miss, never blind
            out(eid, ref, to_kind="unresolved", to_id=None,
                **{"class": "scope_column_missing"})
        scope_bound.add(eid)

    def bind_in_source(eid, ref, src, col, col_u):
        if src["rkind"] == "table":
            tu = src["target"].upper()
            hit = dic["columns"].get(tu, {}).get(col_u)
            if hit:
                out(eid, ref, to_kind="column",
                    to_id=f"{src['target']}.{hit}",
                    match_basis=_basis(col, hit))
                resolved_cols[eid] = (tu, col_u)
            else:
                out(eid, ref, to_kind="unresolved", to_id=None,
                    **{"class": "unknown_column"})
            return True
        if src["rkind"] == "scope" and src.get("target"):
            members, star = _members_of(ctx, src["target"])
            if col_u in members:
                out(eid, ref, to_kind="member",
                    to_id=members[col_u], match_basis="member")
                scope_bound.add(eid)
            elif star:
                bind_through_star(eid, ref, src["target"], col_u)
            else:
                out(eid, ref, to_kind="unresolved", to_id=None,
                    **{"class": "scope_column_missing"})
                scope_bound.add(eid)
            return True
        if src["rkind"] == "unknown":
            out(eid, ref, to_kind="unresolved", to_id=None,
                **{"class": "blocked_by_unknown_table"})
            return True
        return False  # tfunc/unmapped: no column home here

    for job in ctx["pending_refs"]:
        eid, ref = job["expr_id"], job["ref"]
        if job["kind"] == "parameter":
            hit = ctx["param_registry"].get(ref.upper())
            if hit:
                out(eid, ref, to_kind="parameter", to_id=hit,
                    match_basis="exact")
            else:
                out(eid, ref, to_kind="unresolved", to_id=None,
                    **{"class": "unknown_parameter"})
            continue
        if ref == "*":
            out(eid, ref, to_kind="unresolved", to_id=None,
                **{"class": "wildcard"})
            continue
        parts = ref.split(".")
        col, qual = parts[-1], (parts[-2] if len(parts) > 1 else None)
        col_u = col.upper()

        if qual is not None:
            qu = qual.upper()
            done = False
            for s in chain(job["scope"]):
                for src in sources_at(s):
                    names = {(src.get("alias") or "").upper(),
                             (src.get("bare") or "").upper()}
                    if qu in names and qu:
                        done = bind_in_source(eid, ref, src, col,
                                              col_u)
                        if done:
                            break
                if done:
                    break
            if not done and qu in ctx["named_scopes"]:
                done = bind_in_source(
                    eid, ref, {"rkind": "scope",
                               "target": ctx["named_scopes"][qu]},
                    col, col_u)
            if not done and qu in dic["tables"]:
                done = bind_in_source(
                    eid, ref, {"rkind": "table",
                               "target": dic["tables"][qu]},
                    col, col_u)
            if not done:
                out(eid, ref, to_kind="unresolved", to_id=None,
                    **{"class": "unknown_column"})
            continue

        # unqualified: first chain level with any hit decides
        placed = False
        saw_unknown = False
        scope_miss = False
        for s in chain(job["scope"]):
            table_hits, member_hits, star_srcs = [], [], []
            for src in sources_at(s):
                if src["rkind"] == "table":
                    tu = src["target"].upper()
                    if col_u in dic["columns"].get(tu, {}):
                        table_hits.append(src)
                elif src["rkind"] == "scope" and src.get("target"):
                    members, star = _members_of(ctx, src["target"])
                    if col_u in members:
                        member_hits.append((src, members[col_u]))
                    elif star:
                        star_srcs.append(src)
                    else:
                        scope_miss = True
                elif src["rkind"] == "unknown":
                    saw_unknown = True
            hits = len(table_hits) + len(member_hits)
            if hits == 1:
                if table_hits:
                    bind_in_source(eid, ref, table_hits[0], col,
                                   col_u)
                else:
                    src, member_id = member_hits[0]
                    out(eid, ref, to_kind="member", to_id=member_id,
                        match_basis="member")
                    scope_bound.add(eid)
                placed = True
            elif hits > 1:
                cands = sorted(
                    [f"{s['target']}.{col_u}" for s in table_hits]
                    + [s["target"] for s, _ in member_hits])
                out(eid, ref, to_kind="unresolved", to_id=None,
                    candidates=cands,
                    **{"class": "ambiguous_column"})
                placed = True
            elif len(star_srcs) == 1:
                bind_through_star(eid, ref, star_srcs[0]["target"],
                                  col_u)
                placed = True
            elif len(star_srcs) > 1:
                out(eid, ref, to_kind="unresolved", to_id=None,
                    candidates=sorted(s["target"]
                                      for s in star_srcs),
                    **{"class": "ambiguous_column"})
                placed = True
            if placed:
                break
        if not placed:
            cls = ("blocked_by_unknown_table" if saw_unknown
                   else "scope_column_missing" if scope_miss
                   else "unknown_column")
            out(eid, ref, to_kind="unresolved", to_id=None,
                **{"class": cls})

    # ---- the value bridge (D5)
    for job in ctx["pending_values"]:
        subj = resolved_cols.get(job["subject"])
        if subj is None:
            continue
        route = _value_route(dic, *subj)
        if route is None:
            continue  # no route -> no attempt, no noise
        codes = dic["values"][route]
        tname = dic["tables"].get(route, route)
        for cid in job["comparands"]:
            crow = ctx["expr_by_id"][cid]
            if crow["expression_kind"] != "literal":
                continue
            code = str(crow.get("value", "")).strip()
            if code in codes:
                out(cid, crow["raw_text"], to_kind="value",
                    to_id=f"{tname}::{code}", match_basis="exact")
            else:
                tu, cu = subj
                out(cid, f"{dic['tables'][tu]}.{cu} = {code}",
                    to_kind="unresolved", to_id=None,
                    **{"class": "value_code_unknown"})

    # ---- join binding (D4) + on_class stamping
    file_prefix = f"{ctx['file_id']}::"
    file_preds = [p for p in ctx["predicate_rows"]
                  if p["node_id"].startswith(file_prefix)]
    expr_children = {}
    for eid2 in ctx["expr_by_id"]:
        parent = eid2.rsplit("::expr/", 1)[0]
        expr_children.setdefault(parent, []).append(eid2)

    for jrow in ctx["structure_rows"]:
        if (not jrow["node_id"].startswith(file_prefix)
                or jrow["structure_kind"] != "JOIN"
                or jrow["join_type"] not in
                ("Inner", "LeftOuter", "RightOuter", "FullOuter")):
            continue
        jid = jrow["node_id"]
        pairs, involves_scope, pair_texts = set(), False, []
        for p in file_preds:
            if not p["node_id"].startswith(jid + "::"):
                continue
            cls = None
            if p["predicate_kind"] == "COMPARE_EQ" \
                    and not p["negated"]:
                ops = {ctx["expr_by_id"][c]["role"]: c
                       for c in expr_children.get(p["node_id"], [])}
                s_id, c_id = ops.get("subject"), ops.get("comparand")
                if s_id in resolved_cols and c_id in resolved_cols:
                    a, b = resolved_cols[s_id], resolved_cols[c_id]
                    if a[0] != b[0]:
                        pairs.add(frozenset({a, b}))
                        pair_texts.append(" = ".join(sorted(
                            f"{t}.{c}" for t, c in (a, b))))
                        cls = "join_pair"
                if cls is None and (s_id in scope_bound
                                    or c_id in scope_bound):
                    involves_scope = True
            if cls is None:
                cls = ("population_filter"
                       if jrow["join_type"] == "Inner"
                       else "lookup_shaping")
            p["on_class"] = cls

        bound = False
        if pairs:
            partials = []
            for join_id in sorted(dic["joins"]):
                declared = dic["joins"][join_id]
                dset = {pr for _, pr in declared}
                if pairs == dset:
                    out(jid, jrow["evidence"]["fragment"],
                        to_kind="declared_join", to_id=join_id,
                        coverage="full", missing_ordinals=[])
                    bound = True
                    break
                if pairs < dset:
                    missing = sorted(o for o, pr in declared
                                     if pr not in pairs)
                    partials.append((len(pairs & dset), join_id,
                                     missing))
            if not bound and partials:
                partials.sort(key=lambda x: (-x[0], x[1]))
                _, join_id, missing = partials[0]
                out(jid, jrow["evidence"]["fragment"],
                    to_kind="declared_join", to_id=join_id,
                    coverage="partial", missing_ordinals=missing)
                bound = True
        if not bound:
            related = None
            for pr in sorted(pairs, key=str):
                if pr in dic["pair_index"]:
                    related = sorted(dic["pair_index"][pr])[0]
                    break
            ctx["discovered_rows"].append({
                "file_name": stem, "join_type": jrow["join_type"],
                "pairs": sorted(pair_texts),
                "involves_scope": involves_scope,
                "related_join_id": related,
                "evidence": jrow["evidence"]})


def build(sql_dir, out_dir, dict_dir):
    """STAGES 1-5: statements, scopes, structures, predicates,
    expressions, parameters and resolution against the phase 02
    dictionary. Returns the census dict it also prints."""
    sql_dir, out_dir = Path(sql_dir), Path(out_dir)
    library = _load_kind_library(out_dir)
    operational = _operational_types(library)
    gap_classes = _gap_classes(library)
    dic = _load_dictionary(Path(dict_dir))
    library_version = hashlib.sha256(
        (out_dir / KIND_LIBRARY).read_bytes()).hexdigest()[:12]

    file_rows, statement_rows, edges, exclusions = [], [], [], []
    scope_rows, structure_rows = [], []
    predicate_rows, expression_rows = [], []
    param_rows, resolves_rows, discovered_rows = [], [], []
    deferred = _deferred_types(library)
    census = {}

    # The phase 01 corpus files carry no extension; the folder's only
    # non-SQL resident is the data sheet json. Selection law: every
    # regular, non-hidden, non-.json file.
    sql_paths = sorted(p for p in sql_dir.iterdir() if p.is_file()
                       and not p.name.startswith(".")
                       and p.suffix != ".json")
    for sql_path in sql_paths:
        text = sql_path.read_text()
        text = text.replace("\r\n", "\n").replace("\r", "\n")  # at entry
        fragment, messages = parse_tsql(text)
        if messages:
            exclusions.append({
                "file_name": sql_path.name,
                "reasons": messages,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })
            continue

        stem = sql_path.stem
        file_id = f"file::{stem}"
        counts = {"handled": 0, "operational": 0, "gap": 0,
                  "remainder": 0}
        scope_count = 0
        name_counts = {}  # the duplicate law: #x, #x#2, ... per file
        ctx = {"text": text, "file_id": file_id,
               "scope_rows": scope_rows,
               "structure_rows": structure_rows,
               "predicate_rows": predicate_rows,
               "expression_rows": expression_rows,
               "param_rows": param_rows,
               "resolves_rows": resolves_rows,
               "discovered_rows": discovered_rows,
               "edges": edges, "child_counts": {}, "sub_counts": {},
               "deferred_types": deferred,
               "current_scope": None, "current_statement": None,
               "expr_by_id": {}, "pending_refs": [],
               "pending_values": [], "scope_sources": {},
               "scope_members": {}, "scope_parent": {},
               "named_scopes": {}, "subscope_by_pos": {},
               "param_registry": {}}

        def emit(stmt, parent_id, path):
            nonlocal scope_count
            kind, disposition, gap_class = _classify(
                stmt, operational, gap_classes)
            counts[disposition] += 1
            node_id = f"{file_id}::stmt/{path}"
            statement_rows.append({
                "node_id": node_id,
                "position": path,
                "scriptdom_type": _type_name(stmt),
                "statement_kind": kind,
                "disposition": disposition,
                "gap_class": gap_class,
                "evidence": _evidence(text, stmt),
            })
            edges.append({"from_id": parent_id, "to_id": node_id,
                          "position": path, "role": None})

            ctx["current_statement"] = node_id

            # STAGE 5 (D6): DECLAREd locals become parameter nodes;
            # the statement row itself stays operational.
            if _type_name(stmt) == "DeclareVariableStatement":
                for el in stmt.Declarations:
                    _add_param(
                        ctx, el.VariableName.Value, "local_variable",
                        _evidence(text, el.DataType)["fragment"]
                        if el.DataType is not None else None,
                        _evidence(text, el.Value)["fragment"]
                        if el.Value is not None else None,
                        _evidence(text, el))

            # STAGE 4: a control-flow statement owns its condition
            # tree directly (the ladder bends — note a).
            if disposition == "handled" and kind in ("IF", "WHILE"):
                _emit_pred_tree(ctx, node_id, stmt.Predicate,
                                edge_role="condition")

            # STAGE 2: population statements mint their scopes.
            # STAGE 3+4: clause skeleton, predicates, expressions.
            if disposition == "handled" and kind in POPULATION_KINDS:
                for edge_pos, entry in enumerate(
                        _scopes_for(stmt, kind, text), start=1):
                    if entry["name_key"] is None:  # the subquery
                        n_sub = ctx["sub_counts"][node_id] = (
                            ctx["sub_counts"].get(node_id, 0) + 1)
                        scope_id = f"{node_id}::scope/sub{n_sub}"
                    else:
                        key = entry["name_key"]
                        n = name_counts[key] = (
                            name_counts.get(key, 0) + 1)
                        scope_id = (f"{file_id}::scope/{key}"
                                    + ("" if n == 1 else f"#{n}"))
                    scope_rows.append({
                        "node_id": scope_id,
                        "scope_name": entry["scope_name"],
                        "scope_kind": entry["scope_kind"],
                        "operation": entry["operation"],
                        "owning_statement": node_id,
                        "evidence": entry["evidence"],
                    })
                    # STAGE 5 registries: named scopes (FROM #t /
                    # FROM cte resolve by name), subquery positions,
                    # the write target's implicit source.
                    if entry["scope_kind"] in ("cte", "temp_table"):
                        ctx["named_scopes"][
                            entry["scope_name"].upper()] = scope_id
                    if entry["name_key"] is None:
                        ctx["subscope_by_pos"][
                            (entry["evidence"]["line"],
                             entry["evidence"]["column"])] = scope_id
                    if (entry["scope_kind"] == "write_target"
                            and entry["scope_name"]):
                        ctx["scope_sources"][scope_id] = [{
                            "alias": None,
                            "bare": entry["scope_name"],
                            "kind": "named"}]
                    edges.append({"from_id": node_id, "to_id": scope_id,
                                  "position": str(edge_pos),
                                  "role": None})
                    scope_count += 1
                    if entry["query"] is not None:
                        _emit_structures(ctx, scope_id, node_id,
                                         entry["query"])
                    elif entry["where_clause"] is not None:
                        # UPDATE/DELETE: the population filter clause
                        wc = entry["where_clause"]
                        sid = f"{scope_id}::structure/WHERE/1"
                        structure_rows.append({
                            "node_id": sid, "structure_kind": "WHERE",
                            "position": 1, "owning_scope": scope_id,
                            "evidence": _evidence(text, wc)})
                        edges.append({"from_id": scope_id, "to_id": sid,
                                      "position": "1", "role": None})
                        prior = ctx["current_scope"]
                        ctx["current_scope"] = scope_id
                        _emit_pred_tree(ctx, sid, wc.SearchCondition)
                        ctx["current_scope"] = prior

            for i, child in enumerate(_nested_children(stmt), start=1):
                emit(child, node_id, f"{path}.{i}")

        # D6: the proc header's parameters, before the body unwraps
        for batch in fragment.Batches:
            for s in batch.Statements:
                _collect_proc_params(ctx, s, text)
        top = [s for batch in fragment.Batches
               for s in _unwrapped(batch.Statements)]
        for i, stmt in enumerate(top, start=1):
            emit(stmt, file_id, str(i))

        # STAGE 5: the resolution post-pass — every binding attempt,
        # one row each, after the whole file's registries exist.
        _resolve_file(ctx, dic, stem)

        total = sum(counts.values())
        file_rows.append({
            "file_name": stem,
            "dialect": "tsql",
            "parsed_at": datetime.now(timezone.utc).isoformat(),
            "statement_total": total,
            "statements_handled": counts["handled"],
            "statements_operational": counts["operational"],
            "statements_gap": counts["gap"],
            "remainder_total": counts["remainder"],
            "parser_version": PARSER_VERSION,
            "kind_library_version": library_version,
        })
        if counts["handled"] + counts["operational"] + counts["gap"] \
                + counts["remainder"] != total:
            raise RuntimeError(f"conservation broken for {stem}: "
                               f"{counts} != {total}")
        census[stem] = counts | {"total": total, "scopes": scope_count}

    for name, rows in ((FILE_SHEET, file_rows),
                       (STATEMENT_SHEET, statement_rows),
                       (SCOPE_SHEET, scope_rows),
                       (STRUCTURE_SHEET, structure_rows),
                       (PREDICATE_SHEET, predicate_rows),
                       (EXPRESSION_SHEET, expression_rows),
                       (PARAMETER_SHEET, param_rows),
                       (RESOLVES_EDGES, resolves_rows),
                       (DISCOVERED_JOINS, discovered_rows),
                       (CONTAINS_EDGES, edges),
                       (EXCLUSION_LEDGER, exclusions)):
        (out_dir / name).write_text(json.dumps(rows, indent=2,
                                               ensure_ascii=False) + "\n")

    for stem, c in census.items():
        print(f"{stem}: {c['total']} statements ({c['handled']} handled "
              f"/ {c['operational']} operational / {c['gap']} gap / "
              f"{c['remainder']} remainder); {c['scopes']} scopes")
    print(f"files: {len(file_rows)} built, {len(exclusions)} excluded; "
          f"statements: {len(statement_rows)}; scopes: "
          f"{len(scope_rows)}; structures: {len(structure_rows)}; "
          f"predicates: {len(predicate_rows)}; expressions: "
          f"{len(expression_rows)}; parameters: {len(param_rows)}; "
          f"edges: {len(edges)}")
    resolved_n = sum(1 for r in resolves_rows
                     if r["to_kind"] != "unresolved")
    by_class = {}
    for r in resolves_rows:
        if r["to_kind"] == "unresolved":
            by_class[r["class"]] = by_class.get(r["class"], 0) + 1
    print(f"resolution: {resolved_n} bound / "
          f"{len(resolves_rows) - resolved_n} unresolved "
          f"{by_class}; discovered joins: {len(discovered_rows)}")
    queue = sorted({r["ref_text"] for r in resolves_rows
                    if r["to_kind"] == "unresolved"
                    and r["class"] == "unknown_table"})
    if queue:
        print("UNKNOWN TABLES — THE HUMAN QUEUE (the gap-first gate: "
              "phase 06 stays closed until each is resolved into a "
              "dictionary or accepted by Sunny's named ruling):")
        for q in queue:
            print(f"  {q}")
    return census


def main(argv):
    if len(argv) != 4:
        print("usage: semantic_graph.py <sql_dir> <out_dir> "
              "<dict_dir>")
        return 2
    build(argv[1], argv[2], argv[3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
