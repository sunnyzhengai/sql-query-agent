"""REVIEW PROBE — does the ScriptDom tree actually expose the four
defect classes as node structure, as the DESC-SKELETON-3 order claims?

Run under the Homebrew interpreter:
  DOTNET_ROOT=~/.dotnet /opt/homebrew/bin/python3.11 <this file>

This verifies the ORDER before dev builds against it. Every claim I
made ("HAVING is just SearchCondition", "OR is BinaryExpressionType",
"NOT EXISTS carries negation", "SELECT-list CASE is out of the
deciding clauses by construction") is checked against a real parse.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/Users/sunnyzheng/sql-query-agent")

from src.parser.scriptdom_loader import parse_tsql  # noqa: E402

CASES = {
    "1_NOT_EXISTS": (
        "SELECT DISTINCT HU.PATIENT_ID INTO #NoPCP FROM #HighUtil HU "
        "WHERE NOT EXISTS (SELECT 1 FROM PATIENT_PCP_ASSIGNMENT PA "
        "WHERE PA.PATIENT_ID = HU.PATIENT_ID)"),
    "2_HAVING": (
        "SELECT PATIENT_ID INTO #HighUtil FROM ENCOUNTER "
        "WHERE CONTACT_DATE BETWEEN @dStart AND @dEnd "
        "GROUP BY PATIENT_ID HAVING COUNT(*) >= 4"),
    "3_OR": (
        "SELECT ENCOUNTER_ID INTO #Sepsis FROM ORDERS "
        "WHERE (GROUPER_ID IN ('800008','800009') OR DEPARTMENT_ID = 3022)"),
    "4_SELECT_CASE": (
        "SELECT ENCOUNTER_ID, CASE WHEN FLO_MEAS_ID IN ('900112') "
        "THEN 'ETT' ELSE 'None' END AS AIRWAY INTO #Airway "
        "FROM FLOWSHEET WHERE DEPARTMENT_ID = 3022"),
    "5_PARAM": (
        "SELECT ENCOUNTER_ID INTO #B FROM ENCOUNTER "
        "WHERE CONTACT_DATE BETWEEN @dStartDate AND @dEndDate"),
}


def first_select(fragment):
    """The first SelectStatement, however it is wrapped."""
    found = []

    def walk(node, depth=0):
        if node is None or depth > 20 or found:
            return
        if type(node).__name__ == "SelectStatement":
            found.append(node)
            return
        for attr in ("Batches", "Statements", "StatementList"):
            child = getattr(node, attr, None)
            if child is None:
                continue
            inner = getattr(child, "Statements", child)
            if hasattr(inner, "Count"):
                for i in range(inner.Count):
                    walk(inner[i], depth + 1)
            else:
                walk(inner, depth + 1)

    walk(fragment)
    return found[0] if found else None


def describe_expr(node, depth=0, label="root"):
    """Print the expression tree shallowly — node type is the point."""
    if node is None or depth > 6:
        return
    tn = type(node).__name__
    extra = ""
    for attr in ("BinaryExpressionType", "ComparisonType",
                 "NotDefined", "IsNot"):
        val = getattr(node, attr, None)
        if val is not None:
            extra += f" {attr}={val}"
    for attr in ("Value", "Name"):
        val = getattr(node, attr, None)
        if isinstance(val, str):
            extra += f" {attr}={val!r}"
    print("      " + "  " * depth + f"{label}: {tn}{extra}")
    for attr in ("FirstExpression", "SecondExpression", "Expression",
                 "Subquery", "Predicate", "SearchCondition"):
        child = getattr(node, attr, None)
        if child is not None and hasattr(child, "GetType"):
            describe_expr(child, depth + 1, attr)


def main() -> int:
    for name, sql in CASES.items():
        print(f"\n=== {name}")
        frag, errs = parse_tsql(sql)
        if errs:
            print("   PARSE ERRORS:", errs)
            continue
        stmt = first_select(frag)
        if stmt is None:
            print("   no SelectStatement found")
            continue
        spec = stmt.QueryExpression
        print(f"   QueryExpression: {type(spec).__name__}")
        where = getattr(spec, "WhereClause", None)
        having = getattr(spec, "HavingClause", None)
        group = getattr(spec, "GroupByClause", None)
        print(f"   WhereClause:  {type(where).__name__ if where else None}")
        print(f"   HavingClause: {type(having).__name__ if having else None}")
        print(f"   GroupByClause:{type(group).__name__ if group else None}")
        if where is not None:
            print("   WHERE tree:")
            describe_expr(where.SearchCondition, 0, "SearchCondition")
        if having is not None:
            print("   HAVING tree:")
            describe_expr(having.SearchCondition, 0, "SearchCondition")
        # what is in the SELECT list — the scope question
        sel = getattr(spec, "SelectElements", None)
        if sel is not None and hasattr(sel, "Count"):
            kinds = []
            for i in range(sel.Count):
                el = sel[i]
                inner = getattr(el, "Expression", None)
                kinds.append(
                    f"{type(el).__name__}"
                    f"({type(inner).__name__ if inner is not None else '-'})")
            print("   SELECT elements:", ", ".join(kinds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
