"""Brief_Fabric_Resident FR7 (2026-09-19): THE ONE WHEEL BUILD.

Copies the source-of-truth registry JSONs (AIVIA_Design/registries
— the converter's output, the only home) and the ScriptDom DLL
(libs/) into the package as aisql/_registries and aisql/_libs FOR
THE BUILD ONLY — gitignored, removed in finally; derivable is
never stored. Then `python -m build --wheel` produces the turn-key
carrier: sql_query_agent-2.0.0-py3-none-any.whl, everything a
Fabric Environment or a marketplace customer needs in one file.

Release build (dist/): python3.11 devtools/build_wheel.py
The FR7 pin (tests/aisql/test_wheel_boot.py) builds into a temp
dir and proves the wheel boots with no repo present.
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DLL = "Microsoft.SqlServer.TransactSql.ScriptDom.dll"


def build(outdir) -> str:
    if str(ROOT) not in sys.path:  # script mode: repo root on path
        sys.path.insert(0, str(ROOT))
    from aisql.graph.metamodel import REGISTRY_NAMES
    reg_src = ROOT / "AIVIA_Design" / "registries"
    reg_dst = ROOT / "aisql" / "_registries"
    lib_dst = ROOT / "aisql" / "_libs"
    pack_src = ROOT / "AIVIA_Product" / "source_packs" / "clarity"
    pack_dst = ROOT / "aisql" / "_source_packs" / "clarity"
    try:
        reg_dst.mkdir(exist_ok=True)
        lib_dst.mkdir(exist_ok=True)
        pack_dst.mkdir(parents=True, exist_ok=True)
        for name in REGISTRY_NAMES:
            shutil.copy2(reg_src / f"{name}.json",
                         reg_dst / f"{name}.json")
        shutil.copy2(ROOT / "libs" / DLL, lib_dst / DLL)
        # the pack rides whole: scripts + pack.json (the vendor
        # facts the engine reads — Brief_Pilot_Build_1 ruling (5))
        for part in sorted(pack_src.glob("*.sql")) + \
                [pack_src / "pack.json"]:
            shutil.copy2(part, pack_dst / part.name)
        proc = subprocess.run(
            [sys.executable, "-m", "build", "--wheel",
             "--no-isolation", "--outdir", str(outdir)],
            cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"wheel build failed:\n{proc.stderr[-2000:]}")
    finally:
        shutil.rmtree(reg_dst, ignore_errors=True)
        shutil.rmtree(lib_dst, ignore_errors=True)
        shutil.rmtree(ROOT / "aisql" / "_source_packs",
                      ignore_errors=True)
    wheels = sorted(pathlib.Path(outdir).glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"no wheel appeared in {outdir}")
    return str(wheels[-1])


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "dist")
    print(build(target))
