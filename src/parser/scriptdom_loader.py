"""One initialization home for ScriptDom — Fabric, dev machines, CI.

The native-parser law (ADR 0001, hardened 2026-08-19): production
parsing and extraction use the dialect's native parser — ScriptDom for
T-SQL — everywhere. There is no fallback parser; where ScriptDom
cannot load, parsing fails loudly with the remediation, never silently
degrades to a different grammar.

Runtime facts this module encodes:
- In Fabric, 200's cell 0 loads coreclr + the lakehouse DLL first; we
  detect the already-loaded runtime and only ensure the assembly.
- On dev machines, coreclr is loaded here (DOTNET_ROOT or ~/.dotnet).
- Apple's hardened CommandLineTools Python KILLS the process (SIGKILL,
  uncatchable) when coreclr is hosted in it, so the load is probed in a
  SUBPROCESS first; the in-process load only happens after the probe
  survives. Homebrew Python works (this repo's local standard: 3.11).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

_DLL_CANDIDATES = (
    os.environ.get("SCRIPTDOM_DLL", ""),
    str(_REPO_ROOT / "libs" / "Microsoft.SqlServer.TransactSql.ScriptDom.dll"),
    "/lakehouse/default/Files/sql-query-agent/libs/"
    "Microsoft.SqlServer.TransactSql.ScriptDom.dll",
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


def _dotnet_root() -> str:
    return os.environ.get("DOTNET_ROOT") or os.path.expanduser("~/.dotnet")


def _probe_coreclr() -> "tuple[bool, str]":
    """Attempt the coreclr load in a THROWAWAY process — a hardened
    host dies with SIGKILL, which cannot be caught in-process."""
    env = {**os.environ, "DOTNET_ROOT": _dotnet_root()}
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


def _find_dll() -> str:
    for candidate in _DLL_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    raise ScriptDomUnavailable(
        f"ScriptDom DLL not found (looked in: "
        f"{[c for c in _DLL_CANDIDATES if c]}). {REMEDIATION}")


def ensure_scriptdom() -> None:
    """Idempotent: load coreclr if needed, reference the DLL, cache the
    parser class. Raises ScriptDomUnavailable with remediation."""
    global _parser_cls, _string_reader
    if _parser_cls is not None:
        return

    try:
        import pythonnet
    except ImportError as err:
        raise ScriptDomUnavailable(f"pythonnet missing: {err}. {REMEDIATION}") from err

    if pythonnet.get_runtime_info() is None:
        ok, detail = _probe_coreclr()
        if not ok:
            raise ScriptDomUnavailable(
                f"coreclr cannot be hosted here ({detail}). {REMEDIATION}")
        os.environ.setdefault("DOTNET_ROOT", _dotnet_root())
        pythonnet.load("coreclr")

    dll = _find_dll()
    from System.Reflection import Assembly  # noqa: E402 (pythonnet import)
    Assembly.LoadFrom(dll)
    from Microsoft.SqlServer.TransactSql.ScriptDom import (  # noqa: E402
        TSql160Parser,
    )
    from System.IO import StringReader  # noqa: E402
    _parser_cls, _string_reader = TSql160Parser, StringReader


def parse_tsql(sql: str) -> "tuple[object, list[str]]":
    """Parse T-SQL with the native parser. Returns (fragment, errors) —
    errors as human strings; an errorful parse is the CALLER's decision
    to reject (conservation: counted, never silently partial)."""
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
