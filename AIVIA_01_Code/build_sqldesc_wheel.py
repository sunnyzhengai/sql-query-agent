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
VERSION = "0.6.1"  # the tenant day-1 build (2026-10-07):
# PARSE/TRY_PARSE join the cast kind (the conversion family's
# string-input members) + sweep() — the parse-only construct
# census (collect-and-continue at the four RED BUILD stops;
# deliver/describe keep the hard stop).
# 0.6.0 — the work scale-up (2026-10-07): D13 views +
# D12 incremental (ledger, skip/defer, max_new) + D11 path 2
# (recursive tmdl, qualified identity, collision preflight).
# Before 0.6.0 — the rehearsal-night ladder: 0.5.1 env-first
# key, 0.5.2 names-asset offer, 0.5.3 corpus offer (AI_SQL_DIR)
# — the parents[1] sweep says that was the last repo-relative
# default (2026-10-05)

# 0.5.0 (RULED 2026-10-05, "approve the wheel change" — the
# Brief_Packaging amendment): the LLM phases join the wheel;
# the KEY never rides — offered at runtime (env/Key Vault).
MODULES = ("scriptdom_loader.py", "semantic_graph.py",
           "technical_descriptions.py", "pbi_lineage.py",
           "business_descriptions.py", "business_terms.py",
           "ai_delivery.py", "sqldesc_cli.py")

# the stamped manifest: the wheel's exact payload (assets
# package renamed ai_sqldesc_assets 2026-10-05, her ruling)
ALLOWLIST = tuple(sorted(
    MODULES + ("ai_sqldesc_assets/__init__.py",
               f"ai_sqldesc_assets/{DLL}",
               "ai_sqldesc_assets/05_kind_library.json",
               "ai_sqldesc_assets/MANIFEST.txt")))


def _scrub(text):
    """THE BRAND SCRUB (RULED 2026-10-05, her word: 'replace
    aivia with ai everywhere in the wheel'): staged COPIES are
    cleaned, case-preserving; repo sources keep citing the real
    AIVIA_01 folder names. The no-aivia packaging lock enforces
    the result on every member."""
    return (text.replace("AIVIA", "AI").replace("Aivia", "Ai")
                .replace("aivia", "ai"))

_PYPROJECT = f'''[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ai01-sqldesc"
version = "{VERSION}"
description = "Deterministic SQL description engine with a runtime-offered LLM seat. The key never rides."
requires-python = ">=3.11"
dependencies = ["pythonnet>=3.0.1", "openai>=3"]

[project.scripts]
ai-describe = "sqldesc_cli:main"

[tool.setuptools]
py-modules = {list(m.removesuffix(".py") for m in MODULES)}
packages = ["ai_sqldesc_assets"]

[tool.setuptools.package-data]
ai_sqldesc_assets = ["*.dll", "*.json", "MANIFEST.txt"]
'''


def build(out_dir=None):
    """Stage, build, return the wheel path. Offline by law."""
    out = Path(out_dir) if out_dir else CODE / "dist"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage"
        stage.mkdir()
        for m in MODULES:
            (stage / m).write_text(
                _scrub((CODE / m).read_text()))
        assets = stage / "ai_sqldesc_assets"
        assets.mkdir()
        (assets / "__init__.py").write_text(
            '"""The work wheel\'s assets: the ScriptDom DLL and '
            'its own manifest (Brief_Packaging)."""\n')
        shutil.copy(REPO / "libs" / DLL, assets / DLL)
        # the ratified closed vocabulary TRAVELS (the
        # portability split: our rulings, no customer rows;
        # the canary lock verifies); provenance line scrubbed
        # in the staged copy only
        (assets / "05_kind_library.json").write_text(
            _scrub((REPO / "AIVIA_01_Data" / "05_semantic_graph"
                    / "05_kind_library.json").read_text()))
        # renamed ai01-sqldesc 2026-10-05 (her ask: no "aivia"
        # in the wheel file name — the work-transition artifact)
        (assets / "MANIFEST.txt").write_text(
            "ai01-sqldesc " + VERSION + " — the allowlist "
            "(Brief_Packaging, stamped 2026-10-04; LLM phases "
            "joined 2026-10-05, key never rides):\n" +
            "\n".join(ALLOWLIST) + "\n")
        (stage / "pyproject.toml").write_text(_PYPROJECT)
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--no-deps",
             "--no-build-isolation", "-w", str(out), str(stage)],
            check=True, capture_output=True)
    whl = sorted(out.glob(f"ai01_sqldesc-{VERSION}-*.whl"))[-1]
    print(f"built {whl}")
    return str(whl)


if __name__ == "__main__":
    build()
