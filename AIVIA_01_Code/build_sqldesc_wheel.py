# =====================================================================
# build_sqldesc_wheel.py — THE WHEEL BUILDER (Brief_Packaging,
# STAMPED 2026-10-04).
#
# PSEUDO: stage the ALLOWLIST (and nothing else) into a scratch
# package dir; write the work wheel's own pyproject (name
# aivia01-sqldesc, pythonnet the one dependency, aivia-describe
# the one entry point); the DLL rides inside the tiny assets
# package; `pip wheel --no-deps --no-build-isolation` (offline);
# the three locks verify the artifact's own bytes — manifest
# equality, no secret shapes, the census canary.
# =====================================================================

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CODE = Path(__file__).resolve().parent
REPO = CODE.parent
DLL = "Microsoft.SqlServer.TransactSql.ScriptDom.dll"
VERSION = "0.4.0"

MODULES = ("scriptdom_loader.py", "semantic_graph.py",
           "technical_descriptions.py", "pbi_lineage.py",
           "sqldesc_cli.py")

# the stamped manifest: the wheel's exact payload
ALLOWLIST = tuple(sorted(
    MODULES + ("aivia_sqldesc_assets/__init__.py",
               f"aivia_sqldesc_assets/{DLL}",
               "aivia_sqldesc_assets/05_kind_library.json",
               "aivia_sqldesc_assets/MANIFEST.txt")))

_PYPROJECT = f'''[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aivia01-sqldesc"
version = "{VERSION}"
description = "AIVIA deterministic SQL description engine. No keys, no network."
requires-python = ">=3.11"
dependencies = ["pythonnet>=3.0.1"]

[project.scripts]
aivia-describe = "sqldesc_cli:main"

[tool.setuptools]
py-modules = {list(m.removesuffix(".py") for m in MODULES)}
packages = ["aivia_sqldesc_assets"]

[tool.setuptools.package-data]
aivia_sqldesc_assets = ["*.dll", "*.json", "MANIFEST.txt"]
'''


def build(out_dir=None):
    """Stage, build, return the wheel path. Offline by law."""
    out = Path(out_dir) if out_dir else CODE / "dist"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage"
        stage.mkdir()
        for m in MODULES:
            shutil.copy(CODE / m, stage / m)
        assets = stage / "aivia_sqldesc_assets"
        assets.mkdir()
        (assets / "__init__.py").write_text(
            '"""The work wheel\'s assets: the ScriptDom DLL and '
            'its own manifest (Brief_Packaging)."""\n')
        shutil.copy(REPO / "libs" / DLL, assets / DLL)
        # the ratified closed vocabulary TRAVELS (the
        # portability split: AIVIA's rulings, no customer rows;
        # the canary lock verifies)
        shutil.copy(REPO / "AIVIA_01_Data" / "05_semantic_graph"
                    / "05_kind_library.json",
                    assets / "05_kind_library.json")
        (assets / "MANIFEST.txt").write_text(
            "aivia01-sqldesc " + VERSION + " — the allowlist "
            "(Brief_Packaging, stamped 2026-10-04):\n" +
            "\n".join(ALLOWLIST) + "\n")
        (stage / "pyproject.toml").write_text(_PYPROJECT)
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--no-deps",
             "--no-build-isolation", "-w", str(out), str(stage)],
            check=True, capture_output=True)
    whl = sorted(out.glob(f"aivia01_sqldesc-{VERSION}-*.whl"))[-1]
    print(f"built {whl}")
    return str(whl)


if __name__ == "__main__":
    build()
