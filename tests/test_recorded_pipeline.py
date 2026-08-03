"""Replay recorded ScriptDom fixtures through the full offline pipeline.

Skips until fixtures are recorded (see tests/fixtures/recorded/README.md).
When present: re-verifies anonymization (defense in depth — the export
notebook already gated), then requires the pipeline to reach DEPLOYMENT
READY on production-parser truth.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from src.anonymization import get_scan_terms, load_crosswalk, scan_for_missed

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "recorded"
CROSSWALK = REPO_ROOT / "data" / "synthetic" / "crosswalk.json"

pytestmark = pytest.mark.skipif(
    not (FIXTURES / "parse_results.json").exists(),
    reason="no recorded fixtures yet — run the export notebook on Fabric",
)


def _runner():
    spec = importlib.util.spec_from_file_location(
        "run_pipeline_local", REPO_ROOT / "scripts" / "run_pipeline_local.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixtures_contain_no_proprietary_terms():
    terms = get_scan_terms(load_crosswalk(CROSSWALK))
    assert terms, "crosswalk must define _scan_terms"
    for fname in ("parse_results.json", "dict_tables.json", "dict_columns.json"):
        leaks = scan_for_missed((FIXTURES / fname).read_text(), terms)
        assert not leaks, f"{fname} leaked proprietary terms:\n" + "\n".join(leaks[:5])


def test_recorded_pipeline_reaches_deployment_ready():
    runner = _runner()
    parse_results, tables, columns = runner.load_recorded(FIXTURES)
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    assert len(parse_results) == manifest["parse_results"]

    blocked, lines = runner.run_pipeline(parse_results, tables, columns)
    report = "\n".join(lines)
    assert not blocked, f"recorded pipeline BLOCKED:\n{report}"
