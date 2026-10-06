# scriptdom_loader.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/02_emr_data_dictionary.md (L03, L07)
# Contract: AIVIA_01_Design/02_emr_data_dictionary_data_contract.md
#           (output file 1 chain starts here)
# Tests:    AIVIA_01_Test/test_02_emr_data_dictionary_data_contract.py
#           (written RED first)
#
# THE ONE PARSE DOOR. ScriptDom is the only T-SQL parser, per ADR 0001
# (docs/decisions/0001-native-parsers-per-dialect.md): the dialect's
# native parser everywhere, no fallback grammar; where ScriptDom cannot
# load, parsing FAILS LOUDLY with a remediation message. No other file
# in AIVIA_01_Code/ may instantiate the parser.
#
# PORT PROVENANCE: ported near-verbatim from
# aisql/graph/kg2_mapper/scriptdom_loader.py, which carries four
# field-fixed lessons we must not relearn:
#   1. Assembly.LoadFrom with the full DLL file path — clr.AddReference
#      by assembly name failed (git 08170ca, edfd31f).
#   2. DOTNET_ROOT is only asserted when the folder actually EXISTS —
#      forcing ~/.dotnet where it doesn't exist poisons the runtime
#      discovery that would have succeeded (Fabric field fix 2026-08-20).
#      And setdefault, never overwrite.
#   3. macOS ONLY: Apple's hardened system Python SIGKILLs (uncatchable)
#      when hosting coreclr, so the load is probed in a THROWAWAY
#      subprocess first; in-process load only after the probe survives.
#      Linux failure modes are catchable — no probe there.
#   4. An already-loaded runtime is detected (pythonnet.get_runtime_info)
#      and respected — load coreclr only when nothing has.
#
# PORT ADJUSTMENTS (the only deltas from the source file, both narrowing):
#   - DLL candidates reduced to TWO: the SCRIPTDOM_DLL env var override,
#     then <repo root>/libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll
#     (version 18.0.78.1, tracked in git). The source file also searched
#     inside the installed wheel and a lakehouse Files path — dropped
#     here because the phase-02 parse runs ONCE, LOCALLY; only the data
#     sheets travel to Fabric. If a Fabric-side parse need ever arrives,
#     the candidates come back with it (declared debt, not a silent cap).
#   - Repo root is parents[1] of this file (AIVIA_01_Code/ sits directly
#     under the repo root).
#
# PSEUDO CODE
#
# Module constants:
#   _REPO_ROOT      = parent of AIVIA_01_Code/
#   _DLL_CANDIDATES = (env SCRIPTDOM_DLL, _REPO_ROOT/libs/<the DLL>)
#   REMEDIATION     = the human fix-it message: Homebrew python3.11,
#                     pip install pythonnet, .NET 8 runtime or
#                     DOTNET_ROOT, keep libs/<DLL>; no fallback parser
#                     by design (ADR 0001).
#
# class ScriptDomUnavailable(RuntimeError) — the one loud failure type.
#
# Module cache: _parser_cls, _string_reader — filled once, reused.
#
# _dotnet_root() -> str | None
#     DOTNET_ROOT env var if set; else ~/.dotnet if that folder EXISTS;
#     else None (leave discovery alone — lesson 2).
#
# _probe_coreclr() -> (ok, detail)
#     Run `sys.executable -c "from pythonnet import load; load('coreclr')"`
#     in a subprocess (60s timeout), DOTNET_ROOT asserted in its env.
#     returncode 0 -> (True, ""). Negative or 137 -> killed by signal,
#     the hardened-host fingerprint (lesson 3). Else last 400 chars of
#     stderr as detail.
#
# _find_dll() -> str
#     First existing candidate wins; none -> ScriptDomUnavailable
#     naming every path looked at + REMEDIATION.
#
# ensure_scriptdom() -> None      (idempotent)
#     Cached? return.
#     import pythonnet (missing -> ScriptDomUnavailable + REMEDIATION).
#     If no runtime loaded yet (lesson 4):
#         on darwin, probe first (lesson 3); assert DOTNET_ROOT via
#         setdefault only if real (lesson 2); pythonnet.load("coreclr"),
#         any failure -> ScriptDomUnavailable + REMEDIATION.
#     Assembly.LoadFrom(_find_dll())  (lesson 1)
#     Cache TSql160Parser and System.IO.StringReader.
#
# parse_tsql(sql) -> (fragment, messages)
#     ensure_scriptdom(); parser = TSql160Parser(True)  # quoted
#     identifiers ON. Parse(StringReader(sql), None) -> fragment, errors.
#     Each error rendered "L{line}C{col}: {message}". An errorful parse
#     is the CALLER's decision to reject — this function reports,
#     never hides (counted, never silently partial).
#
# NOTE: \r\n normalization is NOT this file's job — it happens at the
# tree-mapping entry (parse_sql_tree.py, next file), before any evidence
# offset is taken, per the phase-01 normalize-at-entry ruling.

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

_DLL_CANDIDATES = (
    os.environ.get("SCRIPTDOM_DLL", ""),
    str(_REPO_ROOT / "libs" / "Microsoft.SqlServer.TransactSql.ScriptDom.dll"),
)

REMEDIATION = (
    "ScriptDom (the native T-SQL parser) is unavailable in this Python. "
    "Fix: use a non-hardened Python (Homebrew python3.11 on macOS), "
    "`pip install pythonnet`, install the .NET 8 runtime "
    "(dotnet-install.sh --runtime dotnet --channel 8.0, or set "
    "DOTNET_ROOT), and keep libs/Microsoft.SqlServer.TransactSql."
    "ScriptDom.dll (ships in this repo). There is no fallback parser "
    "by design (ADR 0001)."
)


class ScriptDomUnavailable(RuntimeError):
    pass


_parser_cls = None
_string_reader = None


def _dotnet_root():
    # Only assert a root that actually exists (lesson 2).
    env_root = os.environ.get("DOTNET_ROOT")
    if env_root:
        return env_root
    home = os.path.expanduser("~/.dotnet")
    return home if os.path.isdir(home) else None


def _probe_coreclr():
    # A hardened host dies with SIGKILL, uncatchable in-process — try
    # the load in a throwaway subprocess first (lesson 3).
    env = dict(os.environ)
    root = _dotnet_root()
    if root:
        env["DOTNET_ROOT"] = root
    try:
        proc = subprocess.run(
            [sys.executable, "-c",
             "from pythonnet import load; load('coreclr')"],
            env=env, capture_output=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        return False, str(err)
    if proc.returncode == 0:
        return True, ""
    detail = (proc.stderr or b"").decode(errors="replace").strip()
    if proc.returncode < 0 or proc.returncode == 137:
        detail = f"process killed (signal, hardened host?) {detail}"
    return False, detail[-400:]


def _find_dll():
    # AMENDED 2026-10-06 (rehearsal find #5, the frozen
    # candidates): the env var is read AT CALL TIME, every
    # call — a pointer staged after import must be seen (the
    # preflight imports engines before staging the DLL).
    candidates = (os.environ.get("SCRIPTDOM_DLL", ""),
                  ) + _DLL_CANDIDATES
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise ScriptDomUnavailable(
        f"ScriptDom DLL not found (looked in: "
        f"{[c for c in candidates if c]}). {REMEDIATION}")


def ensure_scriptdom():
    global _parser_cls, _string_reader
    if _parser_cls is not None:
        return

    try:
        import pythonnet
    except ImportError as err:
        raise ScriptDomUnavailable(
            f"pythonnet missing: {err}. {REMEDIATION}") from err

    if pythonnet.get_runtime_info() is None:  # lesson 4
        if sys.platform == "darwin":
            ok, detail = _probe_coreclr()
            if not ok:
                raise ScriptDomUnavailable(
                    f"coreclr cannot be hosted here ({detail}). {REMEDIATION}")
        root = _dotnet_root()
        if root:
            os.environ.setdefault("DOTNET_ROOT", root)
        try:
            pythonnet.load("coreclr")
        except Exception as err:  # noqa: BLE001 — one remediation message, never a raw stack
            raise ScriptDomUnavailable(
                f"coreclr load failed ({err}). {REMEDIATION}") from err

    dll = _find_dll()
    from System.Reflection import Assembly  # noqa: E402 (pythonnet import)
    Assembly.LoadFrom(dll)  # lesson 1: full path, never AddReference
    from Microsoft.SqlServer.TransactSql.ScriptDom import (  # noqa: E402
        TSql160Parser,
    )
    from System.IO import StringReader  # noqa: E402
    _parser_cls, _string_reader = TSql160Parser, StringReader


def parse_tsql(sql):
    """Parse T-SQL with the native parser. Returns (fragment, messages) —
    messages as human strings; an errorful parse is the CALLER's
    decision to reject (counted, never silently partial)."""
    ensure_scriptdom()
    parser = _parser_cls(True)
    result = parser.Parse(_string_reader(sql), None)
    fragment, errors = (result if isinstance(result, tuple)
                        else (result, None))
    messages = []
    if errors is not None:
        for i in range(errors.Count):
            e = errors[i]
            messages.append(f"L{e.Line}C{e.Column}: {e.Message}")
    return fragment, messages
