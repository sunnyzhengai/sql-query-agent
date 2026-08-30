"""ADR 0061 slice 1 — the run layer: Pro runs the confirmed
definition. Nothing is generated: the SQL that runs is the
certified, parsed, displayed step — byte-for-byte what the user
confirmed on glass.

Execution contract (slice 1, conservative defaults per the order —
Sunny's open calls can only relax them):
- ScriptDom statement-type gate: exactly ONE SelectStatement, no
  INTO — the parser decides, never regex (native-parser law).
  DML/DDL/EXEC → typed refusal naming the statement type.
- Row cap TOP/LIMIT 200; timeout 30s (driver-enforced where the
  driver supports it); read-only credential is the binding's duty.
- P5 ABSOLUTE: result rows go to the DISPLAY; the model sees
  count/schema/elapsed stamps only. The run is NOT a model tool —
  rows structurally cannot enter model context (the cage test in
  tests/test_run_layer.py is the slice's acceptance).
- Every run is captured as a decision event (0056 shape) — the
  flywheel counts runs from day one.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


class RunRefusal(Exception):
    """Typed refusal — rendered to the user with its reason class."""

    def __init__(self, reason_class: str, message: str) -> None:
        self.reason_class = reason_class
        super().__init__(message)


def check_single_select(sql: str) -> None:
    """The ScriptDom statement-type gate: exactly one SelectStatement,
    no INTO. Raises RunRefusal with the offending type named."""
    from src.parser.scriptdom_loader import parse_tsql
    fragment, errors = parse_tsql(sql)
    if errors:
        raise RunRefusal(
            "parse", "the step's SQL did not parse standalone: "
            + " | ".join(str(e) for e in errors[:2]))
    statements = []
    for b in range(fragment.Batches.Count):
        batch = fragment.Batches[b]
        for s in range(batch.Statements.Count):
            statements.append(batch.Statements[s])
    if len(statements) != 1:
        raise RunRefusal(
            "multi_statement",
            f"{len(statements)} statements — the run layer executes "
            "exactly one SELECT (whole procedures are a later slice)")
    stmt = statements[0]
    tname = stmt.GetType().Name
    if tname != "SelectStatement":
        raise RunRefusal(
            "not_select",
            f"statement type {tname} — only a single SELECT may run "
            "(read-only by construction)")
    into = getattr(stmt, "Into", None)
    if into is not None:
        raise RunRefusal(
            "select_into",
            "SELECT ... INTO writes a table — refused (read-only by "
            "construction)")


@dataclass
class RunResult:
    columns: "list[str]"
    rows: "list[dict]"              # DISPLAY-ONLY — never model context
    row_count: int
    capped: bool
    elapsed_ms: int
    stamps: "dict" = field(default_factory=dict)

    def sampling_label(self, cap: int, source: str) -> str:
        return (f"{self.row_count} row(s)"
                + (f" · TOP {cap} (capped)" if self.capped else "")
                + f" · elapsed {self.elapsed_ms} ms · source {source}"
                " · read-only")

    def model_stamps(self) -> dict:
        """P5: the ONLY shape of this result the model may ever see —
        count, schema, elapsed, and the assurance RUNG (C1, RUNG2-1:
        rung metadata is provenance, never row data). No rows, no
        cell values."""
        out = {"row_count": self.row_count,
               "columns": list(self.columns),
               "capped": self.capped,
               "elapsed_ms": self.elapsed_ms}
        if "rung" in self.stamps:
            out["rung"] = self.stamps["rung"]
        return out


def cap_wrap_tsql(sql: str, n: int) -> str:
    return f"SELECT TOP ({n + 1}) * FROM (\n{sql}\n) AS certified_step"

def cap_wrap_sqlite(sql: str, n: int) -> str:
    return f"SELECT * FROM (\n{sql}\n) AS certified_step LIMIT {n + 1}"


# RUNG2-1 (0058 C2 as RATIFIED — types only; overnight queue 3):
# the literal type classes a parameter site may swap within. Any
# other token difference is a LOGIC deviation → the fork.
_NUMERIC_TOKENS = frozenset({"Integer", "Numeric", "Real", "Money"})
_STRING_TOKENS = frozenset({"AsciiStringLiteral",
                            "UnicodeStringLiteral"})
_SKIP_TOKENS = frozenset({"WhiteSpace", "SingleLineComment",
                          "MultilineComment", "EndOfFile"})


def _significant_tokens(sql: str) -> "list[tuple[str, str]]":
    from src.parser.scriptdom_loader import parse_tsql
    fragment, errors = parse_tsql(sql)
    if errors:
        raise RunRefusal(
            "parse", "the SQL did not parse: "
            + " | ".join(str(e) for e in errors[:2]))
    out: "list[tuple[str, str]]" = []
    for i in range(fragment.ScriptTokenStream.Count):
        tok = fragment.ScriptTokenStream[i]
        ttype = tok.TokenType.ToString()
        if ttype in _SKIP_TOKENS:
            continue
        out.append((ttype, str(tok.Text or "")))
    return out


def _type_class(ttype: str) -> "str | None":
    if ttype in _NUMERIC_TOKENS:
        return "numeric"
    if ttype in _STRING_TOKENS:
        return "string"
    return None


def check_certified_variant(certified_sql: str,
                            submitted_sql: str) -> "list[dict]":
    """RUNG2-1: validity = token-stream equality EXCEPT at literal
    sites, where the swap must stay within its TYPE class (C2 as
    ratified: types only — range checks addable later without
    breakage). Returns the changed sites (the rung stamp's data);
    ANY logic deviation refuses as the fork — this becomes YOUR
    variant, and the 0038 path is where variants become certified
    definitions of their own."""
    cert = _significant_tokens(certified_sql)
    subm = _significant_tokens(submitted_sql)
    fork = RunRefusal(
        "variant_fork",
        "this is no longer the certified definition — a LOGIC "
        "change makes it your variant. Values at literal sites may "
        "change (types only); structure may not. To keep your "
        "version, fork it into your own definition (the 0038 "
        "path); the certified original stays untouched.")
    if len(cert) != len(subm):
        raise fork
    sites: "list[dict]" = []
    for i, ((ct, cv), (st, sv)) in enumerate(zip(cert, subm)):
        if ct == st and cv.lower() == sv.lower():
            continue
        c_cls, s_cls = _type_class(ct), _type_class(st)
        if c_cls is None or s_cls is None or c_cls != s_cls:
            raise fork
        sites.append({"site": i, "type": c_cls,
                      "certified": cv[:40], "submitted": sv[:40]})
    return sites


def extract_single_select_proc(sql: str) -> "str | None":
    """PROC-RUN-1 (0061 deferred slice): a CREATE PROCEDURE whose
    body is exactly ONE SelectStatement runs — the body SELECT is
    extracted verbatim (offset-sliced, never regenerated).
    Multi-statement bodies return None (the caller refuses typed)."""
    from src.parser.scriptdom_loader import parse_tsql
    fragment, errors = parse_tsql(sql)
    if errors:
        return None
    statements = []
    for b in range(fragment.Batches.Count):
        batch = fragment.Batches[b]
        for s in range(batch.Statements.Count):
            statements.append(batch.Statements[s])
    if len(statements) != 1:
        return None
    proc = statements[0]
    if proc.GetType().Name not in ("CreateProcedureStatement",
                                   "CreateOrAlterProcedureStatement"):
        return None
    body = getattr(proc, "StatementList", None)
    if body is None or body.Statements.Count != 1:
        return None
    inner = body.Statements[0]
    if inner.GetType().Name != "SelectStatement":
        return None
    return sql[inner.StartOffset:
               inner.StartOffset + inner.FragmentLength]


_DRIVER_CURE = (
    "the Microsoft ODBC driver stack is missing — macOS: brew tap "
    "microsoft/mssql-release https://github.com/Microsoft/"
    "homebrew-mssql-release && brew trust microsoft/mssql-release && "
    "HOMEBREW_ACCEPT_EULA=Y brew install unixodbc msodbcsql18 · "
    "Debian/Ubuntu: apt-get install -y unixodbc msodbcsql18")


def classify_run_error(exc: BaseException) -> "tuple[str, str]":
    """RW-16 (field find 2026-08-29, Sunny's laptop: pyodbc +
    unixodbc + msodbcsql18 all absent and the bind failed with no
    remediation surfaced): every failed run DISTINGUISHES its state
    and NAMES its cure — the error-contract law. Returns
    (reason_class, message-with-cure)."""
    text = f"{type(exc).__name__}: {exc}"
    low = text.lower()
    if isinstance(exc, ImportError) and "pyodbc" in low:
        return ("driver_stack",
                "pyodbc is not installed in this environment — cure: "
                "pip install pyodbc (if the NEXT error names the ODBC "
                f"driver, its cure follows). ({text[:200]})")
    if ("can't open lib" in low or "odbc driver" in low
            or "driver manager" in low or "libodbc" in low
            or "im002" in low):
        return ("driver_stack", f"{_DRIVER_CURE} ({text[:200]})")
    if ("token" in low or "login" in low or "aadsts" in low
            or "authentication" in low or "authorization" in low
            or "permission" in low):
        return ("auth",
                "the AAD credential was refused or unavailable — "
                f"cure: az login, then retry. ({text[:200]})")
    return ("execution",
            f"the run failed: {text[:300]} — if this repeats, check "
            "network reach to the server and the read-only grant")


def run_step(sql: str, execute, cap: int = 200,
             cap_wrap=cap_wrap_tsql, source: str = "") -> RunResult:
    """Execute ONE certified SELECT through the gate. `execute` is
    any read-only `(sql) -> list[dict]` (the extractor's connection
    Protocol tenant-side; sqlite for the CI fixture). The +1 row
    probe makes 'capped' a fact, never a guess."""
    check_single_select(sql)
    wrapped = cap_wrap(sql, cap)
    t0 = time.monotonic()
    raw = execute(wrapped)
    elapsed = int((time.monotonic() - t0) * 1000)
    capped = len(raw) > cap
    rows = raw[:cap]
    columns = list(rows[0].keys()) if rows else []
    return RunResult(columns=columns, rows=rows,
                     row_count=len(rows), capped=capped,
                     elapsed_ms=elapsed,
                     stamps={"source": source, "cap": cap})
