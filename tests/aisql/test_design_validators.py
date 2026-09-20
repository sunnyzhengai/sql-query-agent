"""Slice 0: the design validators run in CI — every push re-proves the
answer keys and the stamp discipline.

Wires binding mechanisms (a) and (b) plus the Graph Validity Contract's
fixture rules into pytest: RG (registries: stamps, doc compare,
rule-to-check closure) and GV (fixtures F1-F6). A red here means the
design data and the code no longer describe the same system — the
same-breath rule as a build failure, not a review comment.

Proves: contract:aisql-design-to-code
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _run(script):
    return subprocess.run(
        [sys.executable, str(ROOT / script)],
        capture_output=True, text=True, check=False,
    )


def test_registry_validator_green():
    proc = _run("AIVIA_Design/registries/validate_registries.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "VIOLATIONS: none" in proc.stdout


def test_registry_validator_has_no_not_runnable_left():
    proc = _run("AIVIA_Design/registries/validate_registries.py")
    assert "NOT-RUNNABLE" not in proc.stdout


def test_fixture_validator_green():
    proc = _run("AIVIA_Product/fixtures/validate_fixtures.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "VIOLATIONS: none" in proc.stdout


def test_conversion_is_deterministic():
    """Rerunning the converter must be byte-identical — the registry
    JSON is generated data; a diff after rerun means someone edited
    outputs by hand or the converter grew nondeterminism."""
    before = {p: p.read_bytes()
              for p in (ROOT / "AIVIA_Design/registries").glob("*.json")}
    proc = _run("AIVIA_Design/registries/convert_from_xlsx.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = {p: p.read_bytes()
             for p in (ROOT / "AIVIA_Design/registries").glob("*.json")}
    assert before == after
