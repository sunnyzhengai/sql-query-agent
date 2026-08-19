"""The native-parser law (ADR 0001, hardened 2026-08-19).

Sunny, verbatim: "can we remove sqlglot from ALL code base? under no
circumstances should we use it." The failure mode this bans is
demonstrated, not hypothetical: sqlglot-era artifacts carried corrupted
column names (a /* comment */ inside a column), missed 192 JOINs in
unparseable statements, and rewrote CONVERT to CAST in stored
expressions. The dialect's native parser (ScriptDom for T-SQL) is the
only parser, everywhere — Fabric, dev, CI. No fallback exists; where
ScriptDom cannot load, parsing fails with the remediation.

Enforcement is total: any import of a non-native SQL parser anywhere in
the repo fails CI, and the banned packages may not be declared as
dependencies.
"""

import re
from pathlib import Path

REPO = Path(__file__).parent.parent

BANNED = ("sqlglot", "sqlparse")

_IMPORT = re.compile(
    r"^\s*(?:import\s+({0})\b|from\s+({0})[.\s])".format("|".join(BANNED)),
    re.M,
)

_SCAN_DIRS = ("src", "tests", "scripts", "devtools", "notebooks")


def _python_files():
    for d in _SCAN_DIRS:
        yield from (REPO / d).rglob("*.py")
    yield from REPO.glob("*.Notebook/notebook-content.py")


def test_no_banned_parser_import_anywhere():
    offenders = []
    for py in _python_files():
        if "__pycache__" in str(py):
            continue
        if _IMPORT.search(py.read_text(errors="replace")):
            offenders.append(str(py.relative_to(REPO)))
    assert not offenders, (
        f"banned SQL parser imported in {offenders} — the native-parser "
        f"law (ADR 0001): ScriptDom via src/parser/scriptdom_loader is "
        f"the ONLY parser, under no circumstances sqlglot/sqlparse"
    )


def test_banned_parsers_are_not_declared_dependencies():
    for f in ("pyproject.toml", "environment/requirements.txt"):
        text = (REPO / f).read_text()
        for pkg in BANNED:
            assert not re.search(rf'^\s*"?{pkg}[=<>"]', text, re.M), (
                f"{pkg} declared in {f} — removing the import is not "
                f"enough; the dependency itself is banned"
            )


def test_the_native_loader_is_the_single_parse_door():
    """Every module that parses SQL text goes through scriptdom_loader
    — one initialization home, one parser class, one law."""
    loader = (REPO / "src" / "parser" / "scriptdom_loader.py").read_text()
    assert "TSql160Parser" in loader
    offenders = []
    for py in (REPO / "src").rglob("*.py"):
        if py.name in ("scriptdom_loader.py",) or "__pycache__" in str(py):
            continue
        text = py.read_text(errors="replace")
        if "TSql160Parser(" in text:  # instantiation, not docstring mention
            offenders.append(str(py.relative_to(REPO)))
    assert not offenders, (
        f"{offenders} instantiate the parser outside scriptdom_loader"
    )
