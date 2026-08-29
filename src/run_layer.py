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
        count, schema, elapsed. No rows, no values."""
        return {"row_count": self.row_count,
                "columns": list(self.columns),
                "capped": self.capped,
                "elapsed_ms": self.elapsed_ms}


def cap_wrap_tsql(sql: str, n: int) -> str:
    return f"SELECT TOP ({n + 1}) * FROM (\n{sql}\n) AS certified_step"

def cap_wrap_sqlite(sql: str, n: int) -> str:
    return f"SELECT * FROM (\n{sql}\n) AS certified_step LIMIT {n + 1}"


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
