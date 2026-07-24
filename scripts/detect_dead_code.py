#!/usr/bin/env python3
"""Detect unreachable src/ modules and unused public functions.

Walks all .py files in the project, builds an import graph, and reports:
1. src/ modules not imported by any test, notebook, script, or other src module
2. Public functions/classes defined in src/ but never referenced elsewhere

Exit code 0 = clean, 1 = dead code found.
Run in CI to prevent dead code accumulation.

Usage:
    python scripts/detect_dead_code.py [--strict]

    --strict: exit 1 on any dead code (for CI gating)
    default:  print report only, exit 0
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Directories to scan for imports (consumers of src/)
CONSUMER_DIRS = [
    PROJECT_ROOT / "src",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "notebooks",
    PROJECT_ROOT / "scripts",
]

# Files to exclude from dead code analysis (infrastructure, not logic)
EXCLUDED_FILES = {
    "__init__.py",
    "detect_dead_code.py",
}


def get_module_name(file_path: Path) -> str:
    """Convert file path to Python module name relative to project root."""
    rel = file_path.relative_to(PROJECT_ROOT)
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def get_src_modules() -> dict[str, Path]:
    """Find all src/ modules (excluding __init__.py and excluded files)."""
    modules = {}
    for py_file in SRC_DIR.rglob("*.py"):
        if py_file.name in EXCLUDED_FILES:
            continue
        mod_name = get_module_name(py_file)
        modules[mod_name] = py_file
    return modules


def get_public_names(file_path: Path) -> list[str]:
    """Extract public function and class names from a Python file."""
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return []

    names = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
    return names


def extract_imports(file_path: Path) -> set[str]:
    """Extract all import targets from a Python file.

    Returns a set of module names (e.g., 'src.parser.sql_parser')
    and individual names imported (e.g., 'parse_sql').
    """
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                # Also record individual names for function-level detection
                if node.names:
                    for alias in node.names:
                        imports.add(alias.name)
    return imports


def extract_all_references(file_path: Path) -> set[str]:
    """Extract all Name references from a Python file (for function usage detection)."""
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return set()

    refs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            refs.add(node.id)
        elif isinstance(node, ast.Attribute):
            refs.add(node.attr)
    return refs


def find_all_consumer_files() -> list[Path]:
    """Find all .py files that might import from src/."""
    files = []
    for d in CONSUMER_DIRS:
        if d.exists():
            files.extend(d.rglob("*.py"))
    return [f for f in files if f.name not in EXCLUDED_FILES]


def build_import_graph() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build two maps:
    1. module_importers: src module -> set of files that import it
    2. name_references: public name -> set of files that reference it
    """
    consumer_files = find_all_consumer_files()

    # Collect all imports and references from all consumer files
    all_imports: dict[Path, set[str]] = {}
    all_refs: dict[Path, set[str]] = {}
    for f in consumer_files:
        all_imports[f] = extract_imports(f)
        all_refs[f] = extract_all_references(f)

    # Check which src modules are imported
    src_modules = get_src_modules()
    module_importers: dict[str, set[str]] = {mod: set() for mod in src_modules}

    for consumer_file, imports in all_imports.items():
        consumer_name = str(consumer_file.relative_to(PROJECT_ROOT))
        for mod_name in src_modules:
            # Check if any import matches this module
            # e.g., "src.parser.sql_parser" matches "from src.parser.sql_parser import ..."
            # Also check partial matches for "from src.parser import sql_parser"
            for imp in imports:
                if mod_name == imp or mod_name.startswith(imp + ".") or imp.startswith(mod_name + "."):
                    module_importers[mod_name].add(consumer_name)
                    break
                # Check if the last part of the module name is imported
                # e.g., "sql_parser" from "from src.parser import sql_parser"
                mod_parts = mod_name.split(".")
                if mod_parts[-1] == imp:
                    module_importers[mod_name].add(consumer_name)
                    break

    # Check which public names are referenced
    name_references: dict[str, set[str]] = {}
    for mod_name, mod_path in src_modules.items():
        for pub_name in get_public_names(mod_path):
            key = f"{mod_name}::{pub_name}"
            name_references[key] = set()
            for consumer_file, refs in all_refs.items():
                # Skip self-references
                if consumer_file == mod_path:
                    continue
                if pub_name in refs:
                    consumer_name = str(consumer_file.relative_to(PROJECT_ROOT))
                    name_references[key].add(consumer_name)

    return module_importers, name_references


def main() -> int:
    strict = "--strict" in sys.argv

    print("=" * 60)
    print("Dead Code Detection Report")
    print("=" * 60)

    module_importers, name_references = build_import_graph()
    src_modules = get_src_modules()

    # 1. Find unreachable modules
    dead_modules = []
    for mod_name, importers in sorted(module_importers.items()):
        # Filter out self-imports (module importing itself)
        external_importers = {
            imp for imp in importers
            if not imp.startswith(mod_name.replace(".", "/"))
        }
        if not external_importers:
            dead_modules.append(mod_name)

    print(f"\n{'─' * 60}")
    print(f"UNREACHABLE MODULES ({len(dead_modules)} found)")
    print(f"{'─' * 60}")
    if dead_modules:
        for mod in dead_modules:
            path = src_modules[mod]
            lines = len(path.read_text().splitlines())
            print(f"  ✗ {mod} ({lines} lines) — {path.relative_to(PROJECT_ROOT)}")
    else:
        print("  ✓ All src/ modules are reachable")

    # 2. Find unreferenced public functions/classes
    dead_names = []
    for key, refs in sorted(name_references.items()):
        if not refs:
            mod_name, pub_name = key.split("::")
            # Skip if the whole module is already dead
            if mod_name in dead_modules:
                continue
            dead_names.append((mod_name, pub_name))

    print(f"\n{'─' * 60}")
    print(f"UNREFERENCED PUBLIC FUNCTIONS/CLASSES ({len(dead_names)} found)")
    print(f"{'─' * 60}")
    if dead_names:
        current_mod = None
        for mod_name, pub_name in dead_names:
            if mod_name != current_mod:
                current_mod = mod_name
                print(f"\n  {mod_name}:")
            print(f"    ✗ {pub_name}()")
    else:
        print("  ✓ All public names are referenced")

    # 3. Summary
    total_modules = len(src_modules)
    total_names = len(name_references)
    dead_lines = sum(
        len(src_modules[m].read_text().splitlines())
        for m in dead_modules
    )

    print(f"\n{'─' * 60}")
    print(f"SUMMARY")
    print(f"{'─' * 60}")
    print(f"  Modules:    {total_modules - len(dead_modules)}/{total_modules} reachable")
    print(f"  Functions:  {total_names - len(dead_names)}/{total_names} referenced")
    print(f"  Dead lines: ~{dead_lines}")

    if dead_modules or dead_names:
        print(f"\n  Action: Review and remove dead code, or add tests/imports.")
        if strict:
            print(f"\n  ✗ FAILED (--strict mode)")
            return 1
    else:
        print(f"\n  ✓ PASSED — no dead code detected")

    return 0


if __name__ == "__main__":
    sys.exit(main())
