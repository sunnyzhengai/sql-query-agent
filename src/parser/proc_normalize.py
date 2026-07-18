"""Normalize a CTE-shaped stored procedure into a single view-shaped SELECT.

Converts multi-statement stored procedures that stage temp tables into
equivalent single-SELECT queries with CTEs:

    -- proc form (input)
    SELECT a, b INTO #stage FROM base WHERE x > 0;
    SELECT a, SUM(b) FROM #stage GROUP BY a;

    -- normalized form (output)
    WITH stage AS (SELECT a, b FROM base WHERE x > 0)
    SELECT a, SUM(b) FROM stage GROUP BY a;

The rewrite is only valid when:
- Every temp table is defined exactly once via SELECT INTO
- No temp is mutated after creation (no INSERT/UPDATE/MERGE/DELETE)
- There is exactly one terminal SELECT

When constraints are violated, ProcNotViewShaped is raised.

Ported from sql-business-logic-extractor with minimal changes.
"""

from __future__ import annotations

import logging
import re

import sqlglot
from sqlglot import exp
from sqlglot.tokens import TokenType

logger = logging.getLogger(__name__)

_DEFAULT_DIALECT = "tsql"


class ProcNotViewShaped(Exception):
    """Raised when a proc cannot be safely rewritten to one view-shaped SELECT.

    `reason` is a short machine-readable code; `detail` carries the
    offending fragment for human-readable logging.
    """

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        msg = reason if not detail else f"{reason}: {detail}"
        super().__init__(msg)


# ---- wrapper / guard stripping (regex, pre-parse) ------------------------

_PROC_HEADER_RE = re.compile(
    r"\bCREATE\s+(?:OR\s+ALTER\s+)?PROC(?:EDURE)?\s+"
    r"(?P<name>(?:\[[^\]]+\]|\w+)(?:\.(?:\[[^\]]+\]|\w+))?)"
    r".*?\bAS\b",
    re.IGNORECASE | re.DOTALL,
)

_TEMP_GUARD_RE = re.compile(
    r"IF\s+OBJECT_ID\s*\([^)]*\)\s+IS\s+NOT\s+NULL\s+"
    r"(?:BEGIN\s+)?DROP\s+TABLE\s+#\w+\s*;?(?:\s+END)?\s*;?",
    re.IGNORECASE,
)

_BARE_DROP_RE = re.compile(
    r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?#\w+\s*;?",
    re.IGNORECASE,
)


def _strip_bare_header(sql: str) -> str:
    """Strip bare-text headers above the CREATE PROCEDURE line."""
    lines = sql.split("\n")
    _SQL_START_RE = re.compile(
        r"^\s*("
        r"CREATE\b|ALTER\b|SELECT\b|WITH\b|DECLARE\b|SET\b|INSERT\b|"
        r"UPDATE\b|DELETE\b|MERGE\b|EXEC\b|USE\b|IF\b|BEGIN\b|"
        r"--|/\*"
        r")",
        re.IGNORECASE,
    )
    for i, line in enumerate(lines):
        if _SQL_START_RE.match(line):
            if i == 0:
                return sql
            return "\n".join(lines[i:])
    return sql


def _strip_proc_wrapper(sql: str) -> tuple[str | None, str]:
    """Peel the CREATE PROCEDURE ... AS [BEGIN] ... [END] wrapper.

    Returns (proc_name, body).
    """
    m = _PROC_HEADER_RE.search(sql)
    if not m:
        return None, sql
    proc_name = m.group("name")
    body = sql[m.end():]

    body = body.strip()
    begin_match = re.match(r"BEGIN\b", body, re.IGNORECASE)
    if begin_match:
        body = body[begin_match.end():]
        body = re.sub(r"\bEND\s*;?\s*(?:GO\s*)?$", "", body.strip(),
                       flags=re.IGNORECASE)
    return proc_name, body


def _strip_temp_guards(body: str) -> str:
    """Remove IF OBJECT_ID(...) DROP TABLE #x guards and bare DROP TABLEs.

    Replaces with `;` to preserve statement boundaries.
    """
    body = _TEMP_GUARD_RE.sub(";\n", body)
    body = _BARE_DROP_RE.sub(";\n", body)
    return body


# ---- statement boundary detection ----------------------------------------

_HARD_STARTERS = {
    TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE, TokenType.MERGE,
    TokenType.DROP, TokenType.CREATE, TokenType.WITH,
}
# Add version-dependent token types (not all exist in older sqlglot)
for _name in ("TRUNCATE", "DECLARE"):
    if hasattr(TokenType, _name):
        _HARD_STARTERS.add(getattr(TokenType, _name))
_SET_OPS = {TokenType.UNION, TokenType.EXCEPT, TokenType.INTERSECT}


def _insert_statement_separators(body: str, dialect: str) -> str:
    """Insert `;` at real top-level statement boundaries via tokenizer.

    Handles: set operations (UNION), INSERT..SELECT, WITH..SELECT,
    MERGE WHEN clauses, subqueries (paren depth > 0).
    """
    try:
        toks = sqlglot.tokenize(body, dialect=dialect)
    except Exception:
        return body

    depth = 0
    opener = None
    saw_select = False
    after_setop = False
    cuts: list[int] = []

    for t in toks:
        tt = t.token_type
        if tt == TokenType.L_PAREN:
            depth += 1
            after_setop = False
            continue
        if tt == TokenType.R_PAREN:
            depth = max(0, depth - 1)
            continue
        if depth != 0:
            continue

        if tt == TokenType.SEMICOLON:
            opener, saw_select, after_setop = None, False, False
            continue
        if tt in _SET_OPS:
            after_setop = True
            continue
        if tt in (TokenType.ALL, TokenType.DISTINCT):
            continue

        new = False
        if tt in _HARD_STARTERS:
            after_setop = False
            if opener == TokenType.MERGE and tt in (
                    TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE):
                pass
            elif opener == TokenType.WITH:
                opener = tt
            elif opener is None:
                opener = tt
            else:
                new = True
        elif tt == TokenType.SELECT:
            if after_setop:
                after_setop = False
            elif opener in (TokenType.INSERT, TokenType.WITH) and not saw_select:
                saw_select = True
            elif opener is None:
                opener, saw_select = tt, True
            else:
                new = True
        else:
            after_setop = False

        if new:
            cuts.append(t.start)
            opener = tt
            saw_select = (tt == TokenType.SELECT)

    if not cuts:
        return body
    out: list[str] = []
    last = 0
    for pos in cuts:
        out.append(body[last:pos])
        out.append(";\n")
        last = pos
    out.append(body[last:])
    return "".join(out)


# ---- control flow detection ------

_SPECIAL_BLOCK = {"TRY", "CATCH", "TRANSACTION", "TRAN", "DISTRIBUTED"}


def _has_control_flow(body: str, dialect: str) -> bool:
    """True if the body has IF/WHILE or BEGIN TRY/CATCH/TRANSACTION."""
    try:
        toks = sqlglot.tokenize(body, dialect=dialect)
    except Exception:
        return False
    n = len(toks)
    for i, t in enumerate(toks):
        if t.token_type == TokenType.VAR and (t.text or "").upper() in ("IF", "WHILE"):
            return True
        if t.token_type == TokenType.BEGIN and i + 1 < n \
                and (toks[i + 1].text or "").upper() in _SPECIAL_BLOCK:
            return True
    return False


def _strip_block_begin_end(body: str, dialect: str) -> str:
    """Remove plain BEGIN ... END block delimiters.

    Preserves CASE ... END. Bails on real control flow (IF/WHILE/TRY-CATCH).
    """
    if _has_control_flow(body, dialect):
        return body
    try:
        toks = sqlglot.tokenize(body, dialect=dialect)
    except Exception:
        return body

    stack: list[str] = []
    remove: list[tuple[int, int]] = []
    for t in toks:
        tt = t.token_type
        if tt == TokenType.CASE:
            stack.append("case")
        elif tt == TokenType.BEGIN:
            stack.append("begin")
            remove.append((t.start, t.end))
        elif tt == TokenType.END:
            kind = stack.pop() if stack else None
            if kind == "begin":
                remove.append((t.start, t.end))

    if not remove:
        return body
    out: list[str] = []
    last = 0
    for s, e in sorted(remove):
        out.append(body[last:s])
        out.append(" ")
        last = e + 1
    out.append(body[last:])
    return "".join(out)


# ---- AST helpers ---------------------------------------------------------

def _is_temp_table(node: exp.Expression | None) -> bool:
    """True if node is a reference to a #temp table."""
    if isinstance(node, exp.Into):
        node = node.this
    if not isinstance(node, exp.Table):
        return False
    ident = node.this
    return bool(getattr(ident, "args", {}).get("temporary"))


def _cte_name(temp_name: str) -> str:
    """CTE alias for a temp table (#stage -> stage)."""
    return temp_name


def _rewrite_temp_refs(select: exp.Select, defined: dict[str, str]) -> None:
    """Rewrite every #temp reference to its CTE alias. Mutates in place."""
    for tbl in select.find_all(exp.Table):
        if not _is_temp_table(tbl):
            continue
        name = tbl.name
        if name not in defined:
            raise ProcNotViewShaped("undefined_temp_reference", f"#{name}")
        ident = tbl.this
        ident.set("temporary", False)
        ident.set("this", defined[name])


# ---- public entry point --------------------------------------------------

def select_into_to_cte(
    sql: str,
    *,
    dialect: str = _DEFAULT_DIALECT,
    emit_create_view: bool = False,
) -> str:
    """Rewrite a CTE-shaped proc into one view-shaped SELECT.

    Args:
        sql: Full stored-proc text or bare proc body.
        dialect: sqlglot dialect; T-SQL by default.
        emit_create_view: When True and proc name was recovered, wrap
            result as CREATE VIEW. Default False for this repo.

    Returns:
        The normalized SQL string (WITH ... SELECT ...).

    Raises:
        ProcNotViewShaped: when the proc can't be safely rewritten.
    """
    sql = _strip_bare_header(sql)
    proc_name, body = _strip_proc_wrapper(sql)
    body = _strip_temp_guards(body)

    # Apply the parsing-rule registry for sqlglot-gap fixes
    from src.parser.parsing_rules import apply_all
    body, fired = apply_all(body)
    if fired:
        logger.info("Parsing rules fired: %s", fired)

    # Strip plain BEGIN..END block delimiters
    body = _strip_block_begin_end(body, dialect)

    # Insert missing statement separators (tokenizer-based)
    body = _insert_statement_separators(body, dialect)

    # Parse into top-level statements
    try:
        statements = [s for s in sqlglot.parse(body, dialect=dialect) if s is not None]
    except Exception:
        if _has_control_flow(body, dialect):
            raise ProcNotViewShaped("procedural")
        raise
    if not statements:
        raise ProcNotViewShaped("empty_body")

    logger.info("Parsed %d statements from proc body", len(statements))

    # First pass: classify each statement
    cte_defs: list[tuple[str, exp.Select]] = []
    terminals: list[exp.Select] = []
    defined: dict[str, str] = {}

    # exp.Declare may not exist in older sqlglot versions
    _declare_type = getattr(exp, "Declare", None)

    for st in statements:
        if isinstance(st, exp.Set):
            continue
        if _declare_type is not None and isinstance(st, _declare_type):
            continue
        if isinstance(st, exp.Select) and st.expressions and all(
                isinstance(e, exp.EQ) and isinstance(e.this, exp.Parameter)
                for e in st.expressions):
            continue
        if isinstance(st, (exp.Union, exp.Except, exp.Intersect)):
            # Check if the left side has SELECT INTO #temp (UNION with staging)
            left = st.this
            if isinstance(left, exp.Select):
                into = left.args.get("into")
                if into is not None and _is_temp_table(into):
                    temp_name = into.this.name
                    if temp_name in defined:
                        raise ProcNotViewShaped("temp_redefined", f"#{temp_name}")
                    cte = _cte_name(temp_name)
                    left.set("into", None)
                    defined[temp_name] = cte
                    cte_defs.append((cte, st))
                    continue
            terminals.append(st)
            continue
        if isinstance(st, exp.Command):
            cmd_text = (st.this or "").strip().upper() if isinstance(st.this, str) else ""
            if not cmd_text:
                cmd_text = st.sql(dialect=dialect).strip().upper()
            _SAFE_CMD_PREFIXES = (
                "DECLARE", "SET @", "SET NOCOUNT", "SET ANSI",
                "SET XACT", "SET TRANSACTION", "SET QUOTED",
                "SET ARITHABORT", "SET CONCAT_NULL",
                "SET DATEFIRST", "SET DATEFORMAT", "SET DEADLOCK",
                "SET FMTONLY", "SET IDENTITY", "SET LANGUAGE",
                "SET LOCK_TIMEOUT", "SET NUMERIC",
                "SET ROWCOUNT", "SET TEXTSIZE",
                "EXEC", "EXECUTE",
                "PRINT", "RETURN", "USE",
                "RAISERROR", "THROW",
            )
            if any(cmd_text.startswith(p) for p in _SAFE_CMD_PREFIXES):
                continue
            raise ProcNotViewShaped("unsupported_statement",
                                     f"Command: {cmd_text[:60]}")
        if isinstance(st, exp.Column):
            # Stray identifiers (e.g. GO parsed as a column reference) — skip
            continue
        if not isinstance(st, exp.Select):
            raise ProcNotViewShaped("unsupported_statement", type(st).__name__)

        into = st.args.get("into")
        if into is None:
            terminals.append(st)
            continue

        target = into.this
        if not _is_temp_table(into):
            tgt = target.sql(dialect=dialect) if target is not None else "?"
            raise ProcNotViewShaped("select_into_persistent", tgt)
        temp_name = target.name
        if temp_name in defined:
            raise ProcNotViewShaped("temp_redefined", f"#{temp_name}")
        cte = _cte_name(temp_name)
        st.set("into", None)
        defined[temp_name] = cte
        cte_defs.append((cte, st))

    if not terminals:
        raise ProcNotViewShaped("no_terminal_select")
    if len(terminals) > 1:
        raise ProcNotViewShaped("multiple_terminal_selects", str(len(terminals)))
    main = terminals[0]

    logger.info("Found %d CTE definitions, 1 terminal SELECT", len(cte_defs))

    # Second pass: rewrite #temp references -> CTE names
    for _name, cte_select in cte_defs:
        _rewrite_temp_refs(cte_select, defined)
    _rewrite_temp_refs(main, defined)

    # Assemble: prepend CTEs to the terminal SELECT in source order
    result = main
    for cte_name, cte_select in cte_defs:
        result = result.with_(cte_name, as_=cte_select, dialect=dialect)

    select_sql = result.sql(dialect=dialect, pretty=True)
    if emit_create_view and proc_name:
        return f"CREATE VIEW {proc_name} AS\n{select_sql}"
    return select_sql
