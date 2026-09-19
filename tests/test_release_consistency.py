"""Release consistency — the era-2 law (Brief_Fabric_Resident +
The Retirement Law, 2026-09-19): a version lives in pyproject.toml
and as EXACTLY ONE wheel in dist/ — the turn-key carrier a Fabric
Environment installs (downloaded from GitHub, uploaded by hand).

The era-1 law bound a THIRD place — the git-synced sql-logic-env
Environment item (2026-08-15: dist/ had 1.6.0 while the Environment
carried 1.5.6, so notebooks ran old code). That item is FROZEN
era-1 residue: it keeps its last era-1 wheel (1.83.0) untouched
until the Retirement Brief rules its removal. The freeze is pinned
here so any drift in either direction — feeding it new wheels, or
silent edits — goes red.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENV_LIBS = REPO / "sql-logic-env.Environment" / "Libraries" / "CustomLibraries"


def pyproject_version() -> str:
    # regex, not tomllib — CI's oldest matrix interpreter is 3.9
    text = (REPO / "pyproject.toml").read_text()
    match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    assert match, "pyproject.toml has no version line"
    return match.group(1)


def test_dist_ships_exactly_the_pyproject_wheel():
    """The living law: dist/ carries EXACTLY ONE product wheel and
    its name matches pyproject (FR2: one current wheel, old wheels
    live in git history)."""
    version = pyproject_version()
    wheels = [w.name for w in (REPO / "dist").glob("sql_query_agent-*.whl")]
    assert wheels == [f"sql_query_agent-{version}-py3-none-any.whl"], (
        f"pyproject.toml says {version} but dist/ holds {wheels}. "
        f"Release: bump pyproject -> python3.11 devtools/build_wheel.py "
        f"-> git rm the superseded wheel, git add the new one."
    )


def test_era1_environment_item_stays_retired():
    """Brief_Retirement (RT1 ruled: no workspace git-syncs this
    repo): the era-1 sql-logic-env item LEFT the tree — the freeze
    ended by ruling, exactly as the freeze pin's epitaph said. This
    pin keeps it retired: nothing may recreate the folder."""
    assert not ENV_LIBS.parent.parent.exists(), (
        "sql-logic-env.Environment reappeared — it was retired by "
        "Brief_Retirement (2026-09-19); the wheel in dist/ is the "
        "only carrier."
    )


def test_devtools_can_never_ship():
    """Moved here from tests/test_build_deployment_package.py when
    that module retired with its era-1 subject (Brief_Retirement).
    The living law: the wheel packages the aivia engine
    (Brief_Fabric_Resident FR6); devtools stays out of the config."""
    pyproject = (REPO / "pyproject.toml").read_text()
    assert 'include = ["aivia", "aivia.*"]' in pyproject
    assert "devtools" not in pyproject


# test_requirements_match_environment_item_libraries retired with
# its subject (Brief_Retirement, 2026-09-19): the era-1 Environment
# item's environment.yml left the tree; environment/requirements.txt
# stays as CI's constraint file until the CI-trim slice re-rules it.
