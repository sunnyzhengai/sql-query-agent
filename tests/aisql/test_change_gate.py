"""THE HARD GATE — Brief_Hard_Gate_Hook (P2 ruled 2026-09-16).

The hook (devtools/change_gate.py) runs before every Edit/Write/
NotebookEdit. A covered code path passes only when a brief with
status APPROVED or BUILT lists that exact path in its
`## Files declared` section (H5: one exact path per line, no
wildcards). Exempt: AIVIA_Design/ and every .md — verdicts must
always land. CLOSED/PRESENTED/DRAFT briefs do not unlock (H3).
The gate guards its own files (H4) and FAILS CLOSED (H6).

Pins run the real script as a subprocess against a throwaway
project tree — never against the live briefs, so a brief's later
status flip cannot silently change these pins.

Pins H1-H6 of Brief_Hard_Gate_Hook.

Proves: contract:aisql-design-to-code
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "devtools" / "change_gate.py"

APPROVED_BRIEF = """# Brief_A — a change

**Status: APPROVED**

## Files declared

    aisql/flows/foo.py
    AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json

done.
"""

CLOSED_BRIEF = """# Brief_B — finished long ago

**Status: CLOSED**

## Files declared

    aisql/flows/closed.py
"""

PRESENTED_BRIEF = """# Brief_C — not yet approved

**Status: PRESENTED**

## Files declared

    aisql/flows/draft.py
"""


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("gate_project")
    briefs = root / "AIVIA_Design" / "briefs"
    briefs.mkdir(parents=True)
    (briefs / "Brief_A.md").write_text(APPROVED_BRIEF)
    (briefs / "Brief_B.md").write_text(CLOSED_BRIEF)
    (briefs / "Brief_C.md").write_text(PRESENTED_BRIEF)
    return root


def run_gate(project, tool_name, path_key, path):
    payload = {"tool_name": tool_name, "tool_input": {path_key: path}}
    return subprocess.run(
        [sys.executable, str(GATE)],
        input=json.dumps(payload),
        capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(project), "PATH": "/usr/bin:/bin"},
    )


def edit(project, rel):
    return run_gate(project, "Edit", "file_path", str(project / rel))


def test_blocks_covered_path_without_brief(project):
    r = edit(project, "aisql/flows/bar.py")
    assert r.returncode == 2
    assert "HARD GATE" in r.stderr
    assert "aisql/flows/bar.py" in r.stderr


def test_allows_covered_path_declared_in_approved_brief(project):
    assert edit(project, "aisql/flows/foo.py").returncode == 0
    # the answer key rides the same brief (H1: AIVIA_Product covered)
    assert edit(
        project,
        "AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json",
    ).returncode == 0


def test_covered_roots_each_block(project):
    for rel in ("src/x.py", "devtools/x.py", "tests/x.py",
                "AIVIA_Test/x.py", "services/x.cs",
                "AIVIA_Product/estates/e/key.json", "pipeline.ipynb"):
        assert edit(project, rel).returncode == 2, rel


def test_exempt_paths_always_pass(project):
    for rel in ("AIVIA_Design/Contract_Logic_Layer.md",
                "AIVIA_Design/registries/kg1.json",
                "AIVIA_Design/briefs/Brief_A.md",
                "README.md", "docs/notes.md",
                ".claude/settings.local.json", ".gitignore"):
        assert edit(project, rel).returncode == 0, rel


def test_closed_and_presented_briefs_do_not_unlock(project):
    assert edit(project, "aisql/flows/closed.py").returncode == 2
    assert edit(project, "aisql/flows/draft.py").returncode == 2


def test_the_gate_guards_itself(project):
    assert edit(project, ".claude/settings.json").returncode == 2
    assert edit(project, "devtools/change_gate.py").returncode == 2


def test_notebook_edits_are_gated(project):
    r = run_gate(project, "NotebookEdit", "notebook_path",
                 str(project / "pipeline.ipynb"))
    assert r.returncode == 2


def test_outside_the_project_passes(project):
    assert edit(project, "../elsewhere/thing.py").returncode == 0


def test_fails_closed_on_garbage_input(project):
    r = subprocess.run(
        [sys.executable, str(GATE)], input="not json {",
        capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(project), "PATH": "/usr/bin:/bin"},
    )
    assert r.returncode == 2
    assert r.stderr  # it says why, never a silent block
