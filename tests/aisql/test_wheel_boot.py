"""Brief_Fabric_Resident FR7 (Sunny's "all eight as proposed,
build it", 2026-09-19): THE NO-REPO BOOT PIN. The wheel is the
turn-key carrier — code + the 7 registry JSONs + the ScriptDom
DLL in ONE file ("all that can be packaged into .wheel, must be
packaged"). These pins build the wheel and prove it stands alone:
the engine boots from the wheel's own contents with NO repo
anywhere near it — the exact posture of a Fabric Environment or
a future marketplace customer's tenant.

Proves: contract:aisql-design-to-code
"""
import os
import pathlib
import subprocess
import sys
import zipfile

import pytest

from aisql.graph.metamodel import REGISTRY_NAMES

ROOT = pathlib.Path(__file__).resolve().parents[2]
WHEEL_NAME = "sql_query_agent-2.3.0-py3-none-any.whl"
DLL = "Microsoft.SqlServer.TransactSql.ScriptDom.dll"
PACK_SCRIPTS = ("01_tables.sql", "02_columns.sql", "03_pk.sql",
                "04_joins.sql", "05_values.sql", "06_manifest.sql",
                "pack.json")


@pytest.fixture(scope="module")
def wheel(tmp_path_factory):
    from devtools import build_wheel
    out = tmp_path_factory.mktemp("wheelbuild")
    return pathlib.Path(build_wheel.build(out))


def test_wheel_carries_the_whole_engine(wheel):
    names = set(zipfile.ZipFile(wheel).namelist())
    # EVERY tracked non-.py file in the package must ride the wheel
    # (2.1.1 field fix — Sunny's Fabric run hit FileNotFoundError on
    # flows/econ_params.json: the wheel shipped code without its
    # data; enumerate the whole class — TRACKED files, so local
    # junk like .DS_Store never enters the contract)
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "aisql/"],
        capture_output=True, text=True, check=True).stdout.splitlines()
    package_data = {f for f in tracked if not f.endswith(".py")}
    missing = sorted(
        ({f"aisql/_registries/{n}.json" for n in REGISTRY_NAMES}
         | {f"aisql/_source_packs/clarity/{s}" for s in PACK_SCRIPTS}
         | package_data
         | {f"aisql/_libs/{DLL}", "aisql/console.py",
            "aisql/fabric_run.py"}) - names)
    assert not missing, f"wheel incomplete: {missing}"
    assert wheel.name == WHEEL_NAME
    strays = sorted(n for n in names if n.startswith("src/"))
    assert not strays, f"the retired src/ tree leaked in: {strays[:5]}"


def test_wheel_metadata_is_lean(wheel):
    with zipfile.ZipFile(wheel) as z:
        meta_name = next(n for n in z.namelist()
                         if n.endswith(".dist-info/METADATA"))
        meta = z.read(meta_name).decode()
    assert "\nVersion: 2.3.0" in meta
    hard_deps = [line for line in meta.splitlines()
                 if line.startswith("Requires-Dist:")
                 and "extra ==" not in line]
    assert len(hard_deps) == 1 and "pythonnet" in hard_deps[0], (
        f"the engine's only dependency is pythonnet; got {hard_deps}")


def test_wheel_boots_with_no_repo_present(wheel, tmp_path):
    site = tmp_path / "site"
    zipfile.ZipFile(wheel).extractall(site)
    code = (
        "import aisql.graph.metamodel as m; rs = m.load_all(); "
        "assert len(rs) == 7, rs; "
        "assert all(r.ratified for r in rs.values()); "
        "from aisql.graph.kg2_mapper import scriptdom_loader as s; "
        "p = s._find_dll(); assert '_libs' in p, p; "
        "print('WHEEL-BOOT-OK')")
    env = {"PATH": os.environ.get("PATH", ""),
           "HOME": str(tmp_path),
           "PYTHONPATH": str(site)}
    proc = subprocess.run([sys.executable, "-c", code],
                          cwd=str(tmp_path), env=env,
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0 and "WHEEL-BOOT-OK" in proc.stdout, (
        f"no-repo boot failed:\n{proc.stderr[-1500:]}")
