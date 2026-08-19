"""Every third-party import must be declared in pyproject.toml.

CI installs `-e ".[dev]"`; an import that is not declared works on any
machine where the package happens to be installed and goes red everywhere
else — exactly how the webapp's fastapi import shipped four red CI pushes
before anyone noticed (2026-08-15). The table contracts police
declared-vs-written; this file polices imported-vs-declared.

Scope: src/, tests/, and marketplace_host/ — everything `pytest` imports.
Notebook-runtime modules that Fabric injects (spark, notebookutils) never
appear as imports, so they need no exemption here.
"""

import ast
import importlib.util
import re
import sys
import sysconfig
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_STDLIB_DIR = sysconfig.get_paths()["stdlib"]
SCANNED_DIRS = ("src", "tests", "marketplace_host")

# Import root -> PyPI distribution, where the two differ. "azure" is a
# namespace package: azure.identity comes from the declared azure-identity;
# azure.functions is deploy-time only (the Functions host provides it) and
# is imported solely in marketplace_host/function_app.py.
IMPORT_ROOT_TO_DIST = {
    "yaml": "pyyaml",
    "azure": "azure-identity",
    "jwt": "pyjwt",
}

# Provided by the execution environment, never installable from pyproject.
# Each entry must say who provides it.
ENVIRONMENT_PROVIDED = {
    "clr": "pythonnet CLR bridge — sql-logic-env ships pythonnet (ADR: ScriptDom)",
    "Microsoft": "CLR namespace injected by pythonnet at runtime (ScriptDom)",
    "System": "CLR namespace injected by pythonnet at runtime (.NET BCL)",
    "pyspark": "Fabric Spark runtime",
    "mssparkutils": "Fabric Spark runtime (notebook utilities)",
    "notebookutils": "Fabric Spark runtime (notebook utilities)",
    "pyodbc": "Fabric Spark runtime preinstalls it (extractor runs in-notebook)",
}


def _normalize(dist: str) -> str:
    # PEP 503 name normalization
    return re.sub(r"[-_.]+", "-", dist).lower()


def declared_distributions() -> "set[str]":
    """All distribution names from [project] dependencies + every extra."""
    text = (REPO / "pyproject.toml").read_text()
    blocks = []
    dep_match = re.search(r"^dependencies = \[(.*?)\]", text, re.M | re.S)
    assert dep_match, "pyproject.toml has no dependencies block"
    blocks.append(dep_match.group(1))
    extras_match = re.search(
        r"^\[project\.optional-dependencies\](.*?)(?=^\[)", text, re.M | re.S
    )
    if extras_match:
        blocks.append(extras_match.group(1))
    declared = set()
    for block in blocks:
        for entry in re.findall(r'"([^"]+)"', block):
            name = re.split(r"[><=~!;\s\[]", entry, maxsplit=1)[0]
            if name:
                declared.add(_normalize(name))
    return declared


def imported_roots() -> "dict[str, Path]":
    """Top-level module name -> first file that imports it (for the message)."""
    roots: "dict[str, Path]" = {}
    for base in SCANNED_DIRS:
        for py in sorted((REPO / base).rglob("*.py")):
            tree = ast.parse(py.read_text(), filename=str(py))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        roots.setdefault(alias.name.split(".")[0], py)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    roots.setdefault(node.module.split(".")[0], py)
    return roots


def _is_repo_local(root: str) -> bool:
    return (REPO / root).is_dir() or (REPO / f"{root}.py").exists()


def _is_stdlib(root: str) -> bool:
    # 3.10+ knows its own stdlib; 3.9 falls back to locating the module.
    if hasattr(sys, "stdlib_module_names"):
        return root in sys.stdlib_module_names
    try:
        spec = importlib.util.find_spec(root)
    except (ImportError, ValueError):
        return False
    if spec is None or spec.origin is None:  # missing, or namespace package
        return root in sys.builtin_module_names
    if spec.origin in ("built-in", "frozen"):
        return True
    return spec.origin.startswith(_STDLIB_DIR)


def test_every_thirdparty_import_is_declared():
    declared = declared_distributions()
    undeclared = []
    for root, first_file in sorted(imported_roots().items()):
        if root == "__future__" or _is_stdlib(root):
            continue
        if _is_repo_local(root) or root in ENVIRONMENT_PROVIDED:
            continue
        dist = _normalize(IMPORT_ROOT_TO_DIST.get(root, root))
        if dist not in declared:
            undeclared.append(
                f"{root} (first import: {first_file.relative_to(REPO)}) — "
                f"declare '{dist}' in pyproject.toml dependencies or an extra"
            )
    assert not undeclared, (
        "Imported but not declared in pyproject.toml — CI installs only "
        "what pyproject declares:\n  " + "\n  ".join(undeclared)
    )
