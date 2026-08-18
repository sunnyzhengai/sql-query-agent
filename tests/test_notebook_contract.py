"""The notebook contract (ADR 0042): mechanical enforcement of the
driver layer. Threat model: AI-collaborator expedience under deadline —
regex in notebooks, logic patched into notebooks. Every plank here is a
tripwire for that failure mode, enforced against the actual sources.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from src.notebook_registry import (
    ALLOWED_IMPORTS,
    FAMILIES,
    NOTEBOOK_REGISTRY,
    QUESTION_FAMILIES,
)

ROOT = Path(__file__).resolve().parent.parent


def _notebook_dirs() -> "dict[str, Path]":
    out = {}
    for d in sorted(ROOT.glob("[0-9][0-9]*.Notebook")):
        out[d.name.replace(".Notebook", "")] = d / "notebook-content.py"
    return out


def _source(path: Path) -> str:
    return path.read_text()


def _tree(path: Path) -> ast.AST:
    code = "\n".join(
        line for line in _source(path).splitlines()
        if not line.startswith("# META")
    )
    return ast.parse(code)


NOTEBOOKS = _notebook_dirs()


# --- Plank 0: the registry itself -----------------------------------

def test_registry_covers_exactly_the_pipeline_notebooks():
    assert set(NOTEBOOK_REGISTRY) == set(NOTEBOOKS), (
        "NOTEBOOK_REGISTRY and the [0-9]*.Notebook dirs must stay 1:1 — "
        "an unregistered notebook has no contract; a registered ghost "
        "has no notebook"
    )


def test_registry_fields_valid():
    for nb, entry in NOTEBOOK_REGISTRY.items():
        assert entry["family"] in FAMILIES, nb
        assert entry["purpose"], nb
        assert re.fullmatch(r"\d+\.\d+", entry["requires_engine"]), nb


def test_every_notebook_serves_a_question_family():
    """The traceability rule (QUESTION_MAP, approved): a notebook serving
    no Layer-0 family is by definition a ghost."""
    for nb, entry in NOTEBOOK_REGISTRY.items():
        served = entry["serves"]
        assert served, f"{nb} serves no question family — ghost by definition"
        assert set(served) <= set(QUESTION_FAMILIES), nb


# --- Plank 1: regex ban ---------------------------------------------

def test_no_regex_in_notebooks():
    """`import re` / `re.` fails CI in notebook sources. Regex lives in
    src/ with tests — no allowlist: a legitimate need argues for a src/
    function, which is the point."""
    for nb, path in NOTEBOOKS.items():
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" or a.name.startswith("re.")
                               for a in node.names), f"{nb}: import re"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", f"{nb}: from re import"
            if (isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "re"):
                pytest.fail(f"{nb}: re.{node.attr} usage")


# --- Plank 2: thinness by AST ---------------------------------------

def test_no_classes_and_only_whitelisted_functions():
    for nb, path in NOTEBOOKS.items():
        tree = _tree(path)
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert not classes, f"{nb} defines classes {classes} — logic goes in src/"
        allowed = set(NOTEBOOK_REGISTRY[nb]["wrappers"])
        funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        illegal = funcs - allowed
        assert not illegal, (
            f"{nb} defines {sorted(illegal)} — not in the registry's "
            f"wrapper whitelist; move the logic to src/ (or, for a true "
            f"runtime shim, add it to the registry with justification)"
        )


def test_imports_restricted_to_allowed_list():
    for nb, path in NOTEBOOKS.items():
        used = set()
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Import):
                used.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                used.add(node.module.split(".")[0])
        illegal = used - ALLOWED_IMPORTS
        assert not illegal, (
            f"{nb} imports {sorted(illegal)} — not on the allowed list; "
            f"logic belongs in src/ (extend ALLOWED_IMPORTS only for "
            f"runtime surface, never for logic)"
        )


def test_steps_imports_match_declared_entry_points():
    """A notebook may only reach the src.steps entry points its registry
    entry permits (src.steps.gates is globally permitted)."""
    for nb, path in NOTEBOOKS.items():
        permitted = set(NOTEBOOK_REGISTRY[nb]["entry_points"])
        for node in ast.walk(_tree(path)):
            if (isinstance(node, ast.ImportFrom) and node.module
                    and node.module.startswith("src.steps")
                    and node.module != "src.steps.gates"):
                names = {a.name for a in node.names}
                illegal = names - permitted
                assert not illegal, (
                    f"{nb} imports {sorted(illegal)} from {node.module} — "
                    f"not in its registry entry_points"
                )


# --- Plank 3: gates by family (registry-declared) -------------------

def test_declared_gates_present_in_source():
    for nb, path in NOTEBOOKS.items():
        src_text = _source(path)
        for required in NOTEBOOK_REGISTRY[nb]["gates"]:
            assert required in src_text, (
                f"{nb} must reference {required} (registry-declared gate)"
            )


def test_derivation_notebooks_have_precondition_gates():
    """Family doctrine: derivation never starts on missing inputs."""
    for nb, entry in NOTEBOOK_REGISTRY.items():
        if entry["family"] == "derivation":
            assert "precondition_gate" in entry["gates"], (
                f"{nb} is derivation but declares no precondition_gate"
            )


# --- Plank 4: version binding ---------------------------------------

def test_version_binding_present_and_matches_registry():
    for nb, path in NOTEBOOKS.items():
        src_text = _source(path)
        floor = NOTEBOOK_REGISTRY[nb]["requires_engine"]
        assert f'REQUIRES_ENGINE = "{floor}"' in src_text, (
            f"{nb}: REQUIRES_ENGINE literal missing or != registry ({floor})"
        )
        assert "require_engine(src.__version__, REQUIRES_ENGINE" in src_text, (
            f"{nb}: cell 0 must call require_engine"
        )


# --- Plank 5: field-patch law ---------------------------------------

def test_field_patch_marker_illegal_in_repo():
    """Patches exist only in deployments (marked cells) and die on sync.
    The marker in the repo means a patch was committed instead of being
    folded into src/ — exactly the black hole the contract prevents."""
    for nb, path in NOTEBOOKS.items():
        assert "FIELD PATCH" not in _source(path), (
            f"{nb} contains a FIELD PATCH marker — fold the fix into "
            f"src/ with tests; patches never merge"
        )


# --- Plank 6 (added 2026-08-18): Fabric py-format integrity ----------
# Field failure: six file-authored notebooks carried a dangling
# '# CELL' marker at EOF — valid Python, but Fabric's py->ipynb
# converter dies on it (PyToIPynbFailure, "Additional text encountered
# after finished reading JSON"), which blocked the whole git update
# batch at the workspace. The repo must only contain notebooks the
# converter can ingest.

def test_fabric_notebook_format_integrity():
    import json as _json
    for nb, path in NOTEBOOKS.items():
        text = _source(path)
        assert text.startswith("# Fabric notebook source"), (
            f"{nb}: missing the Fabric header line")
        assert not text.rstrip().endswith("# CELL ********************"), (
            f"{nb}: dangling '# CELL' marker at EOF — Fabric's py->ipynb "
            f"converter rejects it (PyToIPynbFailure)")
        # every '# META ' block must be one valid JSON object
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("# META "):
                block = []
                while i < len(lines) and (
                        lines[i] == "# META" or lines[i].startswith("# META ")):
                    block.append(lines[i][7:] if lines[i].startswith("# META ")
                                 else "")
                    i += 1
                try:
                    _json.loads("\n".join(block))
                except _json.JSONDecodeError as e:
                    pytest.fail(f"{nb}: malformed META JSON block: {e}")
            else:
                i += 1
