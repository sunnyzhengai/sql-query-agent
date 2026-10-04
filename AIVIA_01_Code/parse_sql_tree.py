# parse_sql_tree.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/02_emr_data_dictionary.md (L03 — the FULL
#           MAPPED TREE ruling, 2026-09-27)
# Contract: AIVIA_01_Design/02_emr_data_dictionary_data_contract.md
#           (Output File 1: 02_sql_extraction.json)
# Tests:    AIVIA_01_Test/test_02_emr_data_dictionary_data_contract.py
#           (tree section, written RED first)
#
# PURPOSE. Parse each subject sql file ONCE through the parse door
# (scriptdom_loader.parse_tsql) and save the full mapped tree —
# statements, scopes, table references, join predicates, columns —
# every node carrying its evidence (verbatim fragment, offset, line,
# column). Everything downstream (tables-used list, generated queries,
# drift) derives from this file; nothing ever parses the sql again.
#
# PORT PROVENANCE. The walk's architecture is the previous build's
# proven mapper (aisql/graph/kg2_mapper/__init__.py, map_tree):
#   - \r\n -> \n normalization AT ENTRY, before any offset is taken
#     (the phase-01 normalize-at-entry ruling; every evidence offset
#     indexes into this normalized text).
#   - No visitor subclass — pythonnet cannot subclass ScriptDom's
#     visitor; dispatch is on each .NET node's type name.
#   - The universal node shape: {"node": <family>, "kind": <kind>,
#     "evidence": {fragment, offset, line, column}, ...props}.
#   - THE CONSERVATION LAW: anything the walk cannot classify goes to
#     a counted remainder ({type, reason, evidence}) — counted, never
#     dropped. handled + remainder = total.
#   - The 2026-09-06 plug-all-holes classes are handled from birth,
#     not re-discovered: subquery interiors mapped, UNION/EXCEPT/
#     INTERSECT sides mapped (never an empty scope), comma joins
#     (FROM A, B) collected, CASE mapped, INSERT...SELECT and
#     SELECT INTO are named write scopes.
#   - CTEs and temp tables are NAMED SCOPES in the same tree (a temp
#     table's leading # is part of its name); they are never EMR
#     tables and never leave the tree as leaves.
#
# DELIBERATE TRIMS from the source mapper, each with its reason:
#   - No PHI redaction pass (contract: no desensitization needed).
#   - No incremental re-parse cache (change quanta): 8 files parse in
#     about a second, locally, run by hand — the cache earns nothing.
#     If the corpus grows, it returns with a ruling.
#   - No parameter-default-IF pattern: decorates meaning phases we
#     haven't reached; such IF statements land in the counted
#     remainder like any unmapped statement kind.
#   - No dictionary binding — L03: resolution is a SEPARATE pass that
#     runs when the data sheets arrive (step 3+). This file records
#     aliases; it never guesses what a bare column belongs to.
#
# COMMENTS — RULED 2026-09-28 (the trailing/leading convention).
# Comments are trivia: the grammar gives them no seat in the AST, but
# ScriptDom keeps every one in its token stream with text/offset/line/
# column. We attach each comment INTO the tree by the industry-standard
# lexical convention (Roslyn model), adapted to our mapped grain:
#   - trailing: a comment on the SAME LINE, after a mapped node's last
#     character (and before any other node starts) -> attached to that
#     node: {"text", "offset", "line", "column", "kind":
#     "single_line"|"multi_line", "position": "trailing"}.
#   - leading: any other comment -> attached to the NEXT mapped node
#     that starts after it, "position": "leading".
#   - file level: comments before the first statement (the header
#     banner, the change log) -> the file entry's own "comments" list.
# Text is VERBATIM and untruncated. This records WHERE a comment sits —
# never what it means; meaning conventions (R8-style "describes the
# thing to its left") stay derivable later from the artifact alone.
# Conservation: every comment token in the stream lands in exactly one
# place; the census prints the per-file comment count.
#
# OUTPUT SHAPE (02_sql_extraction.json). RULED 2026-09-28: this is
# THE ONE GROWING SQL-SIDE FILE — a dict of sections owned by
# different scripts: "files" (this script), "derived" (step 3),
# "resolution" (step 5). Re-running this parse REPLACES the whole
# file with just "files" and prints which sections were dropped —
# they re-derive deterministically; stale is worse than absent.
# The "files" section is a json list, one entry per sql file, sorted
# by file_name:
#   {"node": "file", "name": <file_name>, "dialect": "tsql",
#    "tree_version": TREE_VERSION,          # bump = re-derive downstream
#    "comments": [ ... ],                    # file-level (header banner)
#    "statements": [ ... ],
#    "remainder": [ {type, reason, evidence}, ... ]}
#   Any mapped node may additionally carry "comments": [...] per the
#   trailing/leading convention above.
#
#   statement: {"statement_kind": "SELECT" | "SELECT INTO" | "INSERT"
#               | "IF" | "WHILE" | "SET" | "DECLARE" | "DROP"
#               | "EXECUTE" | "USE" (ruled 2026-09-28: the database
#               context — the resolve pass wants it) | "RETURN"
#               | <raw .NET type name for anything else,
#               + remainder entry>,
#               "position": n,               # global counter across GO
#               "ctes": [named scopes],       # when WITH ... precedes
#               "scope": {...}}               # the query scope, if any
#     DROP:    + "targets": [names]  (DROP TABLE IF EXISTS #temp — the
#              corpus has 9+ of these; temp lifecycle, never EMR reads)
#     EXECUTE: + "argument": mapped expression (see DYNAMIC SQL below)
#
#   scope: {"node": "scope", "name": <target for SELECT INTO /
#           INSERT ... SELECT; absent for a plain SELECT>,
#           "distinct": true when SELECT DISTINCT,
#           "from_refs": [...], "join_on": [...], "where": <predicate>,
#           "group_by": [...], "order_by": [...],   # RULED 2026-09-28
#           "projection": [...],
#           "set_op": {"kind": "UNION"|"EXCEPT"|"INTERSECT",
#                      "all": bool, "sides": [scope, scope]},  # when the
#                      query is a set operation — both sides mapped
#           "evidence": {...}}
#
#   from_ref (the six shapes, ported):
#     named table    -> {"table_ref": "db.schema.table" as written
#                        (1-4 dot parts, inner parts may be empty),
#                        "alias": <or None>, "evidence": ...}
#     qualified join -> both sides recursed into from_refs; the ON
#                       predicate appended to join_on with
#                       "join_type": "Inner"|"LeftOuter"|... stamped on
#     comma join     -> both sides recursed (the 61-invisible-reads
#                       lesson)
#     derived table  -> {"derived_scope": <nested scope>, "alias": ...}
#     table function -> {"function_ref": name, "args": [...], "alias"}
#                       (ruled 2026-09-28: STRING_SPLIT in FROM — a
#                       read structure, clearly not an EMR table)
#     anything else  -> counted remainder ("unmapped table reference")
#
#   expression kinds (closed set): column_ref (multi-part name kept
#     whole, e.g. "adt.EFFECTIVE_TIME"), literal, parameter_ref (@x),
#     function (name + args; a qualified call keeps its whole name —
#     "Clarity.EPIC_UTIL.fn" never loses the qualifier (ruled
#     2026-09-28); + "distinct": true for COUNT(DISTINCT x);
#     + "over": {"partition_by": [...], "order_by": [...]} for window
#     functions — ROW_NUMBER() OVER(...) is in 2 corpus files;
#     + "within_group": {"order_by": [...]} for STRING_AGG ... WITHIN
#     GROUP, ruled 2026-09-28),
#     arithmetic, unary, cast, case, subquery_ref (interior scope
#     MAPPED — the invisible-reads lesson), star (with qualifier;
#     meaning = every column of the source at read time, never
#     enumerated), remainder_ref.
#
#   predicate kinds (closed set): COMPARE_EQ/NEQ/GT/GTE/LT/LTE,
#     PATTERN_MATCH (LIKE), IN_LIST, IN_SELECTION, RANGE (BETWEEN),
#     NULL_CHECK, EXISTS_SELECTION, AND/OR (same-op chains FLATTENED),
#     NOT (structural wrap of the positive kind), remainder.
#
# DYNAMIC SQL — FOUND 2026-09-28, RECONSTRUCTION APPROVED (Sunny,
# same day).
# Two corpus files (Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_
# SSRS and _Totals_SSRS) build their entire query — FROM, the Clarity
# joins, WHERE, GROUP BY — inside a string variable and run
# EXEC (@SQL). A structural parse cannot see table reads inside string
# literals. Baseline behavior (this file, regardless of the ruling):
#   - the EXECUTE statement is mapped with its argument expression;
#   - the SET @SQL = '...' + @var + '...' statements are mapped, so
#     every string fragment is captured VERBATIM in evidence;
#   - the file entry is stamped "dynamic_sql": true — the derive step
#     (step 3) must report these files as under-extracted, counted,
#     never silently thin.
# The approved reconstruction: track SET/DECLARE assignments to the
# executed variable; assemble the value deterministically — string
# literals verbatim, other variables become AIVIA_VAR_<name>
# placeholders (recorded), non-literal expressions (CASE, CONVERT)
# become empty text (recorded as dropped) — then parse the assembled
# text through the SAME parse door and attach the inner tree to the
# EXECUTE statement as "reconstruction": {variable, text, placeholders,
# dropped, statements, remainder}. Inner evidence offsets index into
# the reconstruction's own "text", never the file. If the assembled
# text does not parse, the errors are recorded on the reconstruction —
# loud, no tree, never a guess. No LLM anywhere.
#
# THE CONSTRUCT MASTER — RULED 2026-09-28 (contract Output File 6,
# 02_tsql_construct_master.json). build_extraction also maintains it:
#   - the complete construct inventory comes from the parser DLL by
#     reflection (every concrete fragment class, ~1000 rows) — known
#     BEFORE any file arrives; ingestion only fills counts. One scan.
#   - script columns regenerated each run: construct, keyword hint
#     (camel-case split), count_in_corpus (a raw full-AST walk counts
#     every fragment the parser produced — deeper than the mapped
#     tree, so even a silently-skipped construct is counted), one
#     example fragment (first seen, capped at 120 chars — a hint, not
#     evidence), status: "mapped" (in MAPPED_TYPES, the declared
#     handler registry) / "remainder" (observed, not mapped) /
#     "unseen" (count 0).
#   - Sunny's column preserved across rebuilds: "ruling". Required
#     only where status is "remainder"; the lock test in the suite
#     goes red naming any observed-and-unruled construct.
#   - the parser NEVER reads this file; it audits the code, the code
#     never obeys it.
#
# PSEUDO CODE
#
# TREE_VERSION = "1.0.0"
#
# map_tree(file_name, text) -> dict
#   Step 1 — normalize: text = text.replace("\r\n","\n").replace("\r","\n")
#   Step 2 — fragment, errors = parse_tsql(text)
#            errors -> raise ValueError naming the file and the first
#            errors (all 8 must parse; the gate test already holds).
#   Step 3 — walk fragment.Batches; unwrap CREATE PROCEDURE and
#            BEGIN/END blocks to their executable children, in order
#            (GO batches come flat from ScriptDom; one global
#            statement position counter).
#   Step 4 — per statement: classify statement_kind; map WITH-CTEs as
#            named scopes; map the query scope (dispatch by .NET type
#            name through _map_query/_collect_from/_map_expression/
#            _map_predicate, mutually recursive, exactly the port).
#   Step 5 — every mapped node gets evidence via frag.StartOffset /
#            FragmentLength / StartLine / StartColumn against the
#            NORMALIZED text.
#   Step 6 — return the file entry; remainder rides on it.
#
# build_extraction(sql_dir, out_path) -> list of file entries
#   List the sql files (same rule as phase 01: visible, non-json).
#   map_tree each (utf-8-sig read), sort entries by name, write
#   out_path as json, indent=2, utf-8. Return the entries.
#   Paths are PARAMETERS — never written inside this file (the law).
#   Deterministic: same files in -> byte-identical json out.
#
# CLI (the command Sunny runs):
#   /opt/homebrew/bin/python3.11 AIVIA_01_Code/parse_sql_tree.py \
#       AIVIA_01_Data/01_subject_sql_files \
#       AIVIA_01_Data/02_emr_data_dictionary/02_sql_extraction.json
#   Prints: files parsed, statements mapped, remainder count per file
#   (the conservation census, visible at every run).
#
# CLAUDE'S TESTS (red first) pin:
#   - all 8 files produce a tree; entries sorted by name; top shape.
#   - THE EVIDENCE LAW: for every node with evidence, fragment ==
#     normalized_text[offset : offset+len(fragment)] — checked
#     mechanically across the whole output.
#   - ground truth from Sunny's files: usp_SF_CensusDashboard has a
#     CTE named month_cte, and a from_ref "Clarity.dbo.CLARITY_ADT"
#     with alias "adt".
#   - comments: usp_SF_CensusDashboard's header banner is file-level;
#     "--Census" rides trailing on the EVENT_TYPE_C comparison;
#     "--Canceled" rides trailing on the EVENT_SUBTYPE_C comparison.
#   - joins carry join_type; comma-join reads appear as from_refs.
#   - the two SSRS files are stamped dynamic_sql: true, and their
#     reconstructions parse to inner trees reading Clarity.dbo.CLARITY_ADT.
#   - every remainder entry carries type + reason + evidence.
#   - build_extraction is deterministic (two runs, identical bytes).
#   - the json lands where the parameter says, nowhere else.
#   - the construct master: complete inventory, statuses consistent
#     with the trees, rulings preserved across rebuilds, and the LOCK:
#     every observed-remainder construct carries a ruling (red until
#     Sunny rules).

import json
import re
import sys
from collections import Counter
from pathlib import Path

from scriptdom_loader import ensure_scriptdom, parse_tsql

# 1.1.0: COUNT(*)'s Wildcard maps as star, never a column_ref
TREE_VERSION = "1.1.0"

# Example fragments in the construct master are hints, capped here;
# tree evidence is never capped.
EXAMPLE_CAP = 120

COMPARISON_KINDS = {
    "Equals": "COMPARE_EQ",
    "GreaterThan": "COMPARE_GT",
    "LessThan": "COMPARE_LT",
    "GreaterThanOrEqualTo": "COMPARE_GTE",
    "LessThanOrEqualTo": "COMPARE_LTE",
    "NotEqualToBrackets": "COMPARE_NEQ",
    "NotEqualToExclamation": "COMPARE_NEQ",
    "NotLessThan": "COMPARE_GTE",
    "NotGreaterThan": "COMPARE_LTE",
}

LITERAL_TYPES = (
    "IntegerLiteral", "NumericLiteral", "RealLiteral", "MoneyLiteral",
    "StringLiteral", "NullLiteral", "IdentifierLiteral", "BinaryLiteral",
    "DefaultLiteral", "MaxLiteral",
)


def _tn(frag):
    return frag.GetType().Name


def _get(obj, name):
    return getattr(obj, name, None)


class _Ctx:
    def __init__(self, text):
        self.text = text
        self.remainder = []
        self.assignments = []  # (variable name, value expression frag)


def _evidence(ctx, frag):
    start = frag.StartOffset
    return {
        "fragment": ctx.text[start:start + frag.FragmentLength],
        "offset": start,
        "line": frag.StartLine,
        "column": frag.StartColumn,
    }


def _node(ctx, family, kind, frag, **props):
    out = {"node": family, "kind": kind, "evidence": _evidence(ctx, frag)}
    out.update({k: v for k, v in props.items() if v is not None})
    return out


def _remaindered(ctx, frag, reason):
    ctx.remainder.append({
        "type": _tn(frag), "reason": reason, "evidence": _evidence(ctx, frag),
    })


def _multi_part(mpi):
    return ".".join(i.Value for i in mpi.Identifiers)


def _schema_object_name(son):
    parts = []
    for attr in ("ServerIdentifier", "DatabaseIdentifier",
                 "SchemaIdentifier", "BaseIdentifier"):
        ident = _get(son, attr)
        parts.append(ident.Value if ident is not None else None)
    while parts and parts[0] is None:
        parts.pop(0)
    return ".".join(p if p is not None else "" for p in parts)


# --------------------------------------------------------------------------
# Expressions
# --------------------------------------------------------------------------


def _map_expression(ctx, e):
    t = _tn(e)
    if t == "ColumnReferenceExpression":
        if str(e.ColumnType) == "Wildcard":
            # COUNT(*)'s star arrives as a ColumnReferenceExpression of
            # type Wildcard — it is a star, never a column named that.
            return _node(ctx, "expression", "star", e)
        mpi = _get(e, "MultiPartIdentifier")
        name = _multi_part(mpi) if mpi is not None else str(e.ColumnType)
        return _node(ctx, "expression", "column_ref", e, name=name)
    if t in LITERAL_TYPES:
        return _node(ctx, "expression", "literal", e,
                     value=_get(e, "Value"), literal_type=t)
    if t == "VariableReference":
        return _node(ctx, "expression", "parameter_ref", e, name=e.Name)
    if t == "FunctionCall":
        args = [_map_expression(ctx, p) for p in e.Parameters]
        distinct = str(_get(e, "UniqueRowFilter")) == "Distinct" or None
        over = _map_over(ctx, _get(e, "OverClause"))
        name = e.FunctionName.Value
        ct = _get(e, "CallTarget")
        if ct is not None:
            # RULED 2026-09-28: a qualified call keeps its whole name.
            if _tn(ct) == "MultiPartIdentifierCallTarget":
                name = _multi_part(ct.MultiPartIdentifier) + "." + name
            else:
                _remaindered(ctx, ct, "unmapped call target")
        within_group = None
        wgc = _get(e, "WithinGroupClause")
        if wgc is not None:
            # RULED 2026-09-28: STRING_AGG ... WITHIN GROUP ordering.
            within_group = {"order_by": [
                _map_order_element(ctx, el)
                for el in wgc.OrderByClause.OrderByElements]}
        return _node(ctx, "expression", "function", e,
                     name=name, args=args,
                     distinct=distinct, over=over,
                     within_group=within_group)
    if t in ("LeftFunctionCall", "RightFunctionCall"):
        args = [_map_expression(ctx, p) for p in e.Parameters]
        return _node(ctx, "expression", "function", e,
                     name="LEFT" if t.startswith("Left") else "RIGHT",
                     args=args)
    if t == "CoalesceExpression":
        args = [_map_expression(ctx, p) for p in e.Expressions]
        return _node(ctx, "expression", "function", e, name="COALESCE",
                     args=args)
    if t == "NullIfExpression":
        args = [_map_expression(ctx, e.FirstExpression),
                _map_expression(ctx, e.SecondExpression)]
        return _node(ctx, "expression", "function", e, name="NULLIF",
                     args=args)
    if t == "IIfCall":
        return _node(ctx, "expression", "function", e, name="IIF",
                     args=[_map_predicate(ctx, e.Predicate),
                           _map_expression(ctx, e.ThenExpression),
                           _map_expression(ctx, e.ElseExpression)])
    if t in ("CastCall", "TryCastCall"):
        return _node(ctx, "expression", "cast", e,
                     expression=_map_expression(ctx, e.Parameter),
                     data_type=_data_type_name(e.DataType))
    if t in ("ConvertCall", "TryConvertCall"):
        style = _get(e, "Style")
        return _node(ctx, "expression", "cast", e,
                     expression=_map_expression(ctx, e.Parameter),
                     data_type=_data_type_name(e.DataType),
                     style=_map_expression(ctx, style) if style is not None
                     else None)
    if t == "BinaryExpression":
        return _node(ctx, "expression", "arithmetic", e,
                     op=str(e.BinaryExpressionType),
                     first=_map_expression(ctx, e.FirstExpression),
                     second=_map_expression(ctx, e.SecondExpression))
    if t == "UnaryExpression":
        return _node(ctx, "expression", "unary", e,
                     op=str(e.UnaryExpressionType),
                     expression=_map_expression(ctx, e.Expression))
    if t == "ParenthesisExpression":
        return _map_expression(ctx, e.Expression)  # parentheses dissolve
    if t == "SearchedCaseExpression":
        whens = [{"when": _map_predicate(ctx, w.WhenExpression),
                  "then": _map_expression(ctx, w.ThenExpression)}
                 for w in e.WhenClauses]
        else_e = _get(e, "ElseExpression")
        return _node(ctx, "expression", "case", e, whens=whens,
                     else_result=_map_expression(ctx, else_e)
                     if else_e is not None else None)
    if t == "SimpleCaseExpression":
        whens = [{"when": _map_expression(ctx, w.WhenExpression),
                  "then": _map_expression(ctx, w.ThenExpression)}
                 for w in e.WhenClauses]
        else_e = _get(e, "ElseExpression")
        return _node(ctx, "expression", "case", e,
                     input=_map_expression(ctx, e.InputExpression),
                     whens=whens,
                     else_result=_map_expression(ctx, else_e)
                     if else_e is not None else None)
    if t == "ScalarSubquery":
        return _node(ctx, "expression", "subquery_ref", e,
                     scope=_map_query(ctx, e.QueryExpression))
    if t == "SelectStarExpression":
        q = _get(e, "Qualifier")
        return _node(ctx, "expression", "star", e,
                     qualifier=_multi_part(q) if q is not None else None)
    _remaindered(ctx, e, "unmapped expression construct")
    return _node(ctx, "expression", "remainder_ref", e)


def _map_over(ctx, over):
    if over is None:
        return None
    partition = [_map_expression(ctx, p) for p in over.Partitions]
    order_by = []
    obc = _get(over, "OrderByClause")
    if obc is not None:
        order_by = [_map_order_element(ctx, el) for el in obc.OrderByElements]
    return {"partition_by": partition, "order_by": order_by}


def _map_order_element(ctx, el):
    out = {"expression": _map_expression(ctx, el.Expression)}
    sort = str(el.SortOrder)
    if sort != "NotSpecified":
        out["sort"] = sort
    return out


def _data_type_name(dt):
    if dt is None:
        return None
    name = _get(dt, "Name")
    if name is not None:
        return _schema_object_name(name)
    return _tn(dt)


# --------------------------------------------------------------------------
# Predicates
# --------------------------------------------------------------------------


def _wrap_not(ctx, frag, inner):
    return _node(ctx, "predicate", "NOT", frag, member=inner)


def _map_predicate(ctx, p):
    t = _tn(p)
    if t == "BooleanComparisonExpression":
        kind = COMPARISON_KINDS.get(str(p.ComparisonType))
        if kind is None:
            _remaindered(ctx, p, "deferred comparison syntax")
            return _node(ctx, "predicate", "remainder", p)
        return _node(ctx, "predicate", kind, p,
                     subject=_map_expression(ctx, p.FirstExpression),
                     comparand=_map_expression(ctx, p.SecondExpression))
    if t == "BooleanBinaryExpression":
        op = str(p.BinaryExpressionType).upper()
        members = []
        for side in (p.FirstExpression, p.SecondExpression):
            mapped = _map_predicate(ctx, side)
            if mapped.get("kind") == op:  # flatten same-op chains
                members.extend(mapped["members"])
            else:
                members.append(mapped)
        return _node(ctx, "predicate", op, p, members=members)
    if t == "BooleanParenthesisExpression":
        return _map_predicate(ctx, p.Expression)  # parentheses dissolve
    if t == "BooleanNotExpression":
        return _wrap_not(ctx, p, _map_predicate(ctx, p.Expression))
    if t == "BooleanIsNullExpression":
        inner = _node(ctx, "predicate", "NULL_CHECK", p,
                      subject=_map_expression(ctx, p.Expression))
        return _wrap_not(ctx, p, inner) if p.IsNot else inner
    if t == "LikePredicate":
        inner = _node(ctx, "predicate", "PATTERN_MATCH", p,
                      subject=_map_expression(ctx, p.FirstExpression),
                      pattern=_map_expression(ctx, p.SecondExpression))
        return _wrap_not(ctx, p, inner) if p.NotDefined else inner
    if t == "InPredicate":
        subject = _map_expression(ctx, p.Expression)
        sub = _get(p, "Subquery")
        if sub is not None:
            inner = _node(ctx, "predicate", "IN_SELECTION", p,
                          subject=subject,
                          scope=_map_query(ctx, sub.QueryExpression))
        else:
            inner = _node(ctx, "predicate", "IN_LIST", p, subject=subject,
                          members=[_map_expression(ctx, v)
                                   for v in p.Values])
        return _wrap_not(ctx, p, inner) if p.NotDefined else inner
    if t == "BooleanTernaryExpression":
        kind = str(p.TernaryExpressionType)
        inner = _node(ctx, "predicate", "RANGE", p,
                      subject=_map_expression(ctx, p.FirstExpression),
                      low=_map_expression(ctx, p.SecondExpression),
                      high=_map_expression(ctx, p.ThirdExpression))
        return _wrap_not(ctx, p, inner) if kind == "NotBetween" else inner
    if t == "ExistsPredicate":
        return _node(ctx, "predicate", "EXISTS_SELECTION", p,
                     scope=_map_query(ctx, p.Subquery.QueryExpression))
    _remaindered(ctx, p, "unmapped boolean construct")
    return _node(ctx, "predicate", "remainder", p)


# --------------------------------------------------------------------------
# FROM clause
# --------------------------------------------------------------------------


def _collect_from(ctx, tref, refs, join_on):
    t = _tn(tref)
    if t == "NamedTableReference":
        alias = _get(tref, "Alias")
        refs.append({
            "table_ref": _schema_object_name(tref.SchemaObject),
            "alias": alias.Value if alias is not None else None,
            "evidence": _evidence(ctx, tref),
        })
        return
    if t == "QualifiedJoin":
        _collect_from(ctx, tref.FirstTableReference, refs, join_on)
        _collect_from(ctx, tref.SecondTableReference, refs, join_on)
        pred = _map_predicate(ctx, tref.SearchCondition)
        pred["join_type"] = str(tref.QualifiedJoinType)
        join_on.append(pred)
        return
    if t == "UnqualifiedJoin":
        _collect_from(ctx, tref.FirstTableReference, refs, join_on)
        before = len(refs)
        _collect_from(ctx, tref.SecondTableReference, refs, join_on)
        jt = str(tref.UnqualifiedJoinType)
        if jt in ("OuterApply", "CrossApply"):
            for r in refs[before:]:
                r["apply"] = jt
        return
    if t == "QueryDerivedTable":
        alias = _get(tref, "Alias")
        refs.append({
            "derived_scope": _map_query(ctx, tref.QueryExpression),
            "alias": alias.Value if alias is not None else None,
            "evidence": _evidence(ctx, tref),
        })
        return
    if t == "VariableTableReference":
        refs.append({
            "table_ref": tref.Variable.Name,
            "variable": True,
            "evidence": _evidence(ctx, tref),
        })
        return
    if t == "GlobalFunctionTableReference":
        # RULED 2026-09-28: a table-valued function read (STRING_SPLIT
        # in FROM) — a read structure, clearly not an EMR table.
        alias = _get(tref, "Alias")
        refs.append({
            "function_ref": tref.Name.Value,
            "args": [_map_expression(ctx, p) for p in tref.Parameters],
            "alias": alias.Value if alias is not None else None,
            "evidence": _evidence(ctx, tref),
        })
        return
    _remaindered(ctx, tref, "unmapped table reference")


# --------------------------------------------------------------------------
# Queries / scopes
# --------------------------------------------------------------------------


def _map_query(ctx, qe):
    t = _tn(qe)
    if t == "QueryParenthesisExpression":
        return _map_query(ctx, qe.QueryExpression)
    if t == "BinaryQueryExpression":
        scope = {"node": "scope", "evidence": _evidence(ctx, qe)}
        scope["set_op"] = {
            "kind": str(qe.BinaryQueryExpressionType),
            "all": bool(qe.All),
            "sides": [_map_query(ctx, qe.FirstQueryExpression),
                      _map_query(ctx, qe.SecondQueryExpression)],
        }
        return scope
    if t != "QuerySpecification":
        _remaindered(ctx, qe, "unmapped query shape")
        return {"node": "scope", "evidence": _evidence(ctx, qe)}

    scope = {"node": "scope"}
    if str(_get(qe, "UniqueRowFilter")) == "Distinct":
        scope["distinct"] = True
    top = _get(qe, "TopRowFilter")
    if top is not None:
        _remaindered(ctx, top, "unmapped top filter")
    refs, join_on = [], []
    fc = _get(qe, "FromClause")
    if fc is not None:
        for tref in fc.TableReferences:
            _collect_from(ctx, tref, refs, join_on)
    scope["from_refs"] = refs
    scope["join_on"] = join_on
    wc = _get(qe, "WhereClause")
    if wc is not None:
        scope["where"] = _map_predicate(ctx, wc.SearchCondition)
    hc = _get(qe, "HavingClause")
    if hc is not None:
        _remaindered(ctx, hc, "unmapped having clause")
    gbc = _get(qe, "GroupByClause")
    if gbc is not None:
        group_by = []
        for gs in gbc.GroupingSpecifications:
            if _tn(gs) == "ExpressionGroupingSpecification":
                group_by.append(_map_expression(ctx, gs.Expression))
            else:
                _remaindered(ctx, gs, "unmapped grouping specification")
        scope["group_by"] = group_by
    obc = _get(qe, "OrderByClause")
    if obc is not None:
        scope["order_by"] = [_map_order_element(ctx, el)
                             for el in obc.OrderByElements]
    projection = []
    for i, el in enumerate(qe.SelectElements):
        et = _tn(el)
        if et == "SelectScalarExpression":
            cn = _get(el, "ColumnName")
            projection.append({
                "node": "projection_member", "position": i + 1,
                "name": cn.Value if cn is not None else None,
                "expression": _map_expression(ctx, el.Expression),
                "evidence": _evidence(ctx, el),
            })
        elif et == "SelectStarExpression":
            q = _get(el, "Qualifier")
            projection.append({
                "node": "projection_member", "position": i + 1,
                "name": None, "star": True,
                "qualifier": _multi_part(q) if q is not None else None,
                "evidence": _evidence(ctx, el),
            })
        elif et == "SelectSetVariable":
            projection.append({
                "node": "projection_member", "position": i + 1,
                "name": None, "set_variable": el.Variable.Name,
                "expression": _map_expression(ctx, el.Expression),
                "evidence": _evidence(ctx, el),
            })
        else:
            _remaindered(ctx, el, "unmapped select element")
    scope["projection"] = projection
    scope["evidence"] = _evidence(ctx, qe)
    return scope


# --------------------------------------------------------------------------
# Statements
# --------------------------------------------------------------------------


def _executable_statements(stmts):
    for stmt in stmts:
        t = _tn(stmt)
        if t == "CreateProcedureStatement":
            yield from _executable_statements(stmt.StatementList.Statements)
        elif t in ("BeginEndBlockStatement", "BeginEndBlock"):
            yield from _executable_statements(stmt.StatementList.Statements)
        else:
            yield stmt


def _map_ctes(ctx, stmt, entry):
    wcx = _get(stmt, "WithCtesAndXmlNamespaces")
    if wcx is None:
        return
    ctes = []
    for cte in wcx.CommonTableExpressions:
        scope = _map_query(ctx, cte.QueryExpression)
        scope["name"] = cte.ExpressionName.Value
        cols = _get(cte, "Columns")
        if cols is not None and cols.Count:
            scope["declared_columns"] = [c.Value for c in cols]
        ctes.append(scope)
    if ctes:
        entry["ctes"] = ctes


def _map_statement(ctx, stmt, position):
    t = _tn(stmt)
    entry = {"statement_kind": t, "position": position,
             "evidence": _evidence(ctx, stmt)}
    if t == "SelectStatement":
        entry["statement_kind"] = "SELECT"
        _map_ctes(ctx, stmt, entry)
        scope = _map_query(ctx, stmt.QueryExpression)
        into = _get(stmt, "Into")
        if into is not None:
            entry["statement_kind"] = "SELECT INTO"
            scope["name"] = _schema_object_name(into)
        entry["scope"] = scope
        return entry
    if t == "InsertStatement":
        entry["statement_kind"] = "INSERT"
        _map_ctes(ctx, stmt, entry)
        spec = stmt.InsertSpecification
        target = spec.Target
        target_name = (_schema_object_name(target.SchemaObject)
                       if _tn(target) == "NamedTableReference" else _tn(target))
        columns = [_multi_part(c.MultiPartIdentifier) for c in spec.Columns]
        src = spec.InsertSource
        st = _tn(src)
        if st == "SelectInsertSource":
            scope = _map_query(ctx, src.Select)
            scope["name"] = target_name
            if columns:
                scope["insert_columns"] = columns
            entry["scope"] = scope
        else:
            _remaindered(ctx, src, "unmapped insert source")
            entry["target"] = target_name
        return entry
    if t == "IfStatement":
        entry["statement_kind"] = "IF"
        entry["predicate"] = _map_predicate(ctx, stmt.Predicate)
        entry["then"] = [_map_statement(ctx, s, position)
                         for s in _executable_statements([stmt.ThenStatement])]
        els = _get(stmt, "ElseStatement")
        if els is not None:
            entry["else"] = [_map_statement(ctx, s, position)
                             for s in _executable_statements([els])]
        return entry
    if t == "WhileStatement":
        entry["statement_kind"] = "WHILE"
        entry["predicate"] = _map_predicate(ctx, stmt.Predicate)
        entry["body"] = [_map_statement(ctx, s, position)
                         for s in _executable_statements([stmt.Statement])]
        return entry
    if t == "SetVariableStatement":
        entry["statement_kind"] = "SET"
        entry["variable"] = stmt.Variable.Name
        entry["expression"] = _map_expression(ctx, stmt.Expression)
        ctx.assignments.append((stmt.Variable.Name, stmt.Expression))
        return entry
    if t == "PredicateSetStatement":
        entry["statement_kind"] = "SET"
        entry["options"] = str(stmt.Options)
        entry["on"] = bool(stmt.IsOn)
        return entry
    if t == "DeclareVariableStatement":
        entry["statement_kind"] = "DECLARE"
        decls = []
        for d in stmt.Declarations:
            decl = {"name": d.VariableName.Value,
                    "data_type": _data_type_name(d.DataType)}
            val = _get(d, "Value")
            if val is not None:
                decl["value"] = _map_expression(ctx, val)
                ctx.assignments.append((d.VariableName.Value, val))
            decls.append(decl)
        entry["declarations"] = decls
        return entry
    if t == "DropTableStatement":
        entry["statement_kind"] = "DROP"
        entry["targets"] = [_schema_object_name(o) for o in stmt.Objects]
        entry["if_exists"] = bool(stmt.IsIfExists)
        return entry
    if t == "ExecuteStatement":
        entry["statement_kind"] = "EXECUTE"
        entity = stmt.ExecuteSpecification.ExecutableEntity
        et = _tn(entity)
        if et == "ExecutableStringList":
            parts = [_map_expression(ctx, s) for s in entity.Strings]
            entry["argument"] = parts
            entry["reconstruction"] = _reconstruct(ctx, entity.Strings)
        elif et == "ExecutableProcedureReference":
            entry["procedure"] = _schema_object_name(
                entity.ProcedureReference.ProcedureReference.Name)
        else:
            _remaindered(ctx, entity, "unmapped executable entity")
        return entry
    if t == "UseStatement":
        # RULED 2026-09-28: the database context — the resolve pass
        # reads it to qualify bare table names.
        entry["statement_kind"] = "USE"
        entry["database"] = stmt.DatabaseName.Value
        return entry
    if t == "ReturnStatement":
        entry["statement_kind"] = "RETURN"
        return entry
    _remaindered(ctx, stmt, "unmapped statement kind")
    return entry


# --------------------------------------------------------------------------
# Dynamic SQL reconstruction (RULED 2026-09-28)
# --------------------------------------------------------------------------


def _assemble(ctx, expr, target, current, placeholders, dropped):
    t = _tn(expr)
    if t == "StringLiteral":
        return expr.Value
    if t == "VariableReference":
        if expr.Name.lower() == target.lower():
            return current or ""
        name = "AIVIA_VAR_" + expr.Name.lstrip("@")
        if name not in placeholders:
            placeholders.append(name)
        return name
    if t == "BinaryExpression" and str(expr.BinaryExpressionType) == "Add":
        return (_assemble(ctx, expr.FirstExpression, target, current,
                          placeholders, dropped)
                + _assemble(ctx, expr.SecondExpression, target, current,
                            placeholders, dropped))
    if t == "ParenthesisExpression":
        return _assemble(ctx, expr.Expression, target, current,
                         placeholders, dropped)
    dropped.append(t)
    return ""


def _reconstruct(ctx, strings):
    placeholders, dropped = [], []
    texts = []
    for s in strings:
        if _tn(s) == "VariableReference":
            target = s.Name
            current = None
            for name, expr in ctx.assignments:
                if name.lower() == target.lower():
                    current = _assemble(ctx, expr, target, current,
                                        placeholders, dropped)
            texts.append(current or "")
            variable = target
        else:
            texts.append(_assemble(ctx, s, "", None, placeholders, dropped))
            variable = None
    text = "".join(texts)
    out = {"variable": variable, "text": text,
           "placeholders": placeholders, "dropped": dropped}
    if not text.strip():
        out["errors"] = ["assembled text is empty"]
        return out
    fragment, messages = parse_tsql(text)
    if messages:
        out["errors"] = messages
        return out
    inner = _Ctx(text)
    statements = []
    position = 0
    for batch in fragment.Batches:
        for stmt in _executable_statements(batch.Statements):
            position += 1
            statements.append(_map_statement(inner, stmt, position))
    out["reconstructed"] = True
    out["statements"] = statements
    out["remainder"] = inner.remainder
    return out


# --------------------------------------------------------------------------
# Comments (RULED 2026-09-28: trailing/leading attachment)
# --------------------------------------------------------------------------


def _comment_tokens(ctx, fragment):
    comments = []
    for tok in fragment.ScriptTokenStream:
        tt = str(tok.TokenType)
        if tt not in ("SingleLineComment", "MultilineComment"):
            continue
        comments.append({
            "text": tok.Text,
            "offset": tok.Offset,
            "line": tok.Line,
            "column": tok.Column,
            "kind": "single_line" if tt == "SingleLineComment"
            else "multi_line",
        })
    return comments


def _anchors(obj, depth=0, out=None):
    """Every mapped node with evidence, with its nesting depth.
    Reconstruction subtrees are skipped — their offsets index another
    text."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        ev = obj.get("evidence")
        if isinstance(ev, dict) and "offset" in ev:
            out.append((obj, depth))
        for key, v in obj.items():
            if key in ("evidence", "reconstruction", "comments"):
                continue
            _anchors(v, depth + 1, out)
    elif isinstance(obj, list):
        for item in obj:
            _anchors(item, depth, out)
    return out


def _attach_comments(entry, comments):
    anchors = []
    for stmt in entry["statements"]:
        anchors.extend(_anchors(stmt))
    for item in entry["remainder"]:
        anchors.append((item, 0))
    first_start = min((a["evidence"]["offset"] for a, _ in anchors),
                      default=0)
    file_comments = []
    for c in comments:
        if c["offset"] < first_start or not anchors:
            file_comments.append(dict(c))
            continue
        trailing = []
        for node, depth in anchors:
            ev = node["evidence"]
            end_off = ev["offset"] + len(ev["fragment"])
            end_line = ev["line"] + ev["fragment"].count("\n")
            if end_off <= c["offset"] and end_line == c["line"]:
                trailing.append((end_off, ev, depth, node))
        if trailing:
            # Nearest end wins. Among nodes sharing that end, the owner
            # is the LARGEST node that also STARTS on the comment's
            # line ("adt.EVENT_TYPE_C = 6 --Census" belongs to the
            # comparison, not the bare literal 6, not the multi-line
            # AND chain); if none starts on the line, the deepest.
            max_end = max(t[0] for t in trailing)
            at_end = [t for t in trailing if t[0] == max_end]
            same_line = [t for t in at_end if t[1]["line"] == c["line"]]
            if same_line:
                node = max(same_line, key=lambda t: len(t[1]["fragment"]))[3]
            else:
                node = max(at_end, key=lambda t: t[2])[3]
            node.setdefault("comments", []).append(
                dict(c, position="trailing"))
            continue
        leading = []
        for node, depth in anchors:
            ev = node["evidence"]
            if ev["offset"] >= c["offset"] + len(c["text"]):
                leading.append((ev["offset"], -depth, node))
        if leading:
            leading.sort(key=lambda x: (x[0], x[1]))
            node = leading[0][2]
            node.setdefault("comments", []).append(
                dict(c, position="leading"))
        else:
            file_comments.append(dict(c))
    if file_comments:
        entry["comments"] = file_comments


# --------------------------------------------------------------------------
# The file entry
# --------------------------------------------------------------------------


def map_tree(file_name, text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    fragment, messages = parse_tsql(text)
    if messages:
        raise ValueError(
            f"T-SQL parse errors in {file_name} "
            f"({len(messages)}): " + " | ".join(messages[:3]))
    ctx = _Ctx(text)
    statements = []
    position = 0
    for batch in fragment.Batches:
        for stmt in _executable_statements(batch.Statements):
            position += 1
            statements.append(_map_statement(ctx, stmt, position))
    entry = {"node": "file", "name": file_name, "dialect": "tsql",
             "tree_version": TREE_VERSION, "statements": statements,
             "remainder": ctx.remainder}
    if any(s.get("statement_kind") == "EXECUTE" and "reconstruction" in s
           for s in statements):
        entry["dynamic_sql"] = True
    _attach_comments(entry, _comment_tokens(ctx, fragment))
    return entry, fragment, text


# --------------------------------------------------------------------------
# The construct master (contract Output File 6)
# --------------------------------------------------------------------------

# The handler registry: every fragment type the walk CONSUMES into
# structure (including helper types absorbed into node fields). The
# census audits this set against reality.
MAPPED_TYPES = frozenset({
    # containers and helpers
    "TSqlScript", "TSqlBatch", "StatementList", "Identifier",
    "MultiPartIdentifier", "SchemaObjectName", "IdentifierOrValueExpression",
    "FromClause", "WhereClause", "GroupByClause", "OrderByClause",
    "ExpressionGroupingSpecification", "ExpressionWithSortOrder",
    "SelectScalarExpression", "SelectStarExpression", "SelectSetVariable",
    "CommonTableExpression", "WithCtesAndXmlNamespaces",
    "CreateProcedureStatement", "ProcedureReference", "ProcedureParameter",
    "BeginEndBlockStatement", "OverClause",
    "SearchedWhenClause", "SimpleWhenClause",
    "SqlDataTypeReference", "UserDataTypeReference",
    "ExecuteSpecification", "ExecutableStringList",
    "ExecutableProcedureReference", "DeclareVariableElement",
    # statements
    "SelectStatement", "InsertStatement", "InsertSpecification",
    "SelectInsertSource", "IfStatement", "WhileStatement",
    "SetVariableStatement", "PredicateSetStatement",
    "DeclareVariableStatement", "DropTableStatement", "ExecuteStatement",
    "ReturnStatement", "UseStatement",
    # ruled 2026-09-28 (the first construct-lock round)
    "GlobalFunctionTableReference", "MultiPartIdentifierCallTarget",
    "WithinGroupClause",
    # queries and table references
    "QuerySpecification", "BinaryQueryExpression",
    "QueryParenthesisExpression", "NamedTableReference", "QualifiedJoin",
    "UnqualifiedJoin", "QueryDerivedTable", "VariableTableReference",
    # expressions
    "ColumnReferenceExpression", "VariableReference", "FunctionCall",
    "LeftFunctionCall", "RightFunctionCall", "CoalesceExpression",
    "NullIfExpression", "IIfCall", "CastCall", "TryCastCall",
    "ConvertCall", "TryConvertCall", "BinaryExpression", "UnaryExpression",
    "ParenthesisExpression", "SearchedCaseExpression",
    "SimpleCaseExpression", "ScalarSubquery",
    *LITERAL_TYPES,
    # predicates
    "BooleanComparisonExpression", "BooleanBinaryExpression",
    "BooleanParenthesisExpression", "BooleanNotExpression",
    "BooleanIsNullExpression", "LikePredicate", "InPredicate",
    "BooleanTernaryExpression", "ExistsPredicate",
})


def _all_fragment_type_names():
    ensure_scriptdom()
    import clr
    from Microsoft.SqlServer.TransactSql.ScriptDom import TSqlFragment
    frag_t = clr.GetClrType(TSqlFragment)
    names = []
    for t in frag_t.Assembly.GetTypes():
        if t.IsSubclassOf(frag_t) and not t.IsAbstract:
            names.append(t.Name)
    return sorted(set(names))


def _raw_walk(frag, text, counts, examples, _seen_props={}):
    """Count EVERY fragment the parser produced — deeper than the
    mapped tree, so silently-skipped constructs still get counted."""
    ensure_scriptdom()
    from Microsoft.SqlServer.TransactSql.ScriptDom import TSqlFragment
    stack = [frag]
    while stack:
        f = stack.pop()
        name = _tn(f)
        counts[name] += 1
        if name not in examples and f.StartOffset >= 0:
            examples[name] = text[f.StartOffset:
                                  f.StartOffset + min(f.FragmentLength,
                                                      EXAMPLE_CAP)]
        t = f.GetType()
        props = _seen_props.get(t.FullName)
        if props is None:
            props = [p.Name for p in t.GetProperties()
                     if p.Name != "ScriptTokenStream"
                     and not p.GetIndexParameters().Length]
            _seen_props[t.FullName] = props
        for pname in props:
            try:
                v = getattr(f, pname)
            except Exception:  # noqa: BLE001, S112 — .NET reflection edge; the census only loses one property read
                continue
            if v is None or isinstance(v, (str, int, float, bool)):
                continue
            if isinstance(v, TSqlFragment):
                stack.append(v)
                continue
            try:
                items = list(v)
            except TypeError:
                continue
            stack.extend(i for i in items if isinstance(i, TSqlFragment))


_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _keyword_hint(name):
    return _CAMEL.sub(" ", name).upper()


def update_master(master_path, counts, examples):
    master_path = Path(master_path)
    rulings = {}
    if master_path.exists():
        with open(master_path, encoding="utf-8") as f:
            for row in json.load(f):
                if row.get("ruling"):
                    rulings[row["construct"]] = row["ruling"]
    rows = []
    for name in _all_fragment_type_names():
        count = counts.get(name, 0)
        if name in MAPPED_TYPES:
            status = "mapped"
        elif count:
            status = "remainder"
        else:
            status = "unseen"
        rows.append({
            "construct": name,
            "keywords": _keyword_hint(name),
            "count_in_corpus": count,
            "example": examples.get(name, ""),
            "status": status,
            "ruling": rulings.get(name, ""),
        })
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    return rows


# --------------------------------------------------------------------------
# The build
# --------------------------------------------------------------------------


def build_extraction(sql_dir, out_path, master_path=None):
    sql_dir = Path(sql_dir)
    out_path = Path(out_path)
    files = sorted(
        p for p in sql_dir.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.suffix != ".json"
    )
    entries = []
    counts, examples = Counter(), {}
    for path in files:
        entry, fragment, text = map_tree(
            path.stem,  # extensionless names (the
            # 2026-10-03 .sql rename; the stored law)
            path.read_text(encoding="utf-8-sig"))
        _raw_walk(fragment, text, counts, examples)
        entries.append(entry)
    entries.sort(key=lambda e: e["name"])
    # THE ONE-FILE LAW (ruled 2026-09-28): the parse owns "files" and
    # drops every other section loudly — they re-derive by script.
    if out_path.exists():
        try:
            with open(out_path, encoding="utf-8") as f:
                old = json.load(f)
            dropped = [k for k in old if k != "files"] \
                if isinstance(old, dict) else []
            if dropped:
                print(f"re-parse dropped sections: {', '.join(dropped)} "
                      f"— re-derive them (steps 3+)")
        except ValueError:
            pass
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"files": entries}, f, indent=2)
    if master_path is not None:
        update_master(master_path, counts, examples)
    return entries


def main(argv):
    if len(argv) < 3:
        print("usage: python3.11 AIVIA_01_Code/parse_sql_tree.py "
              "<sql dir> <extraction json out> [construct master json]",
              file=sys.stderr)
        return 2
    master = argv[3] if len(argv) > 3 else None
    entries = build_extraction(argv[1], argv[2], master)
    print(f"files parsed: {len(entries)}")
    for e in entries:
        n_stmt = len(e["statements"])
        n_rem = len(e["remainder"])
        dyn = "  DYNAMIC SQL" if e.get("dynamic_sql") else ""
        print(f"  {e['name']}: {n_stmt} statements, "
              f"{n_rem} remainder{dyn}")
        for item in e["remainder"]:
            print(f"    remainder {item['type']}: {item['reason']}")
    if master:
        with open(master, encoding="utf-8") as f:
            rows = json.load(f)
        observed = [r for r in rows if r["status"] == "remainder"]
        unruled = [r for r in observed if not r["ruling"]]
        n_mapped = sum(1 for r in rows if r["status"] == "mapped")
        print(f"construct master: {len(rows)} constructs, "
              f"{n_mapped} mapped, {len(observed)} observed-remainder "
              f"({len(unruled)} AWAITING RULING), "
              f"{sum(1 for r in rows if r['status'] == 'unseen')} unseen")
        for r in unruled:
            print(f"    AWAITING RULING: {r['construct']} "
                  f"(count {r['count_in_corpus']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
