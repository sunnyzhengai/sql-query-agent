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


def test_frozen_era1_environment_item_is_untouched():
    """The freeze pin: sql-logic-env keeps exactly its last era-1
    wheel until the Retirement Brief rules its removal. If this
    fires because the folder is GONE, the freeze ended by ruling —
    retire this whole module's ENV_LIBS half in the same act."""
    wheels = [w.name for w in ENV_LIBS.glob("sql_query_agent-*.whl")]
    assert wheels == ["sql_query_agent-1.83.0-py3-none-any.whl"], (
        f"the frozen era-1 Environment item changed: {wheels} — "
        f"nothing lands there anymore (The Retirement Law, 2026-09-19)."
    )


def test_requirements_match_environment_item_libraries():
    """Two lists, one truth (2026-08-17 drift find): a customer building
    from environment/requirements.txt must get the same packages as the
    git-synced sql-logic-env item's environment.yml."""
    import re as _re

    yml = (REPO / "sql-logic-env.Environment" / "Libraries" /
           "PublicLibraries" / "environment.yml").read_text()
    yml_pins = set(_re.findall(r"-\s*([\w\-]+==[\w\.]+)", yml))
    req_pins = {
        line.strip() for line in
        (REPO / "environment" / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert yml_pins == req_pins, (
        f"environment.yml vs requirements.txt drift:\n"
        f"  only in yml: {sorted(yml_pins - req_pins)}\n"
        f"  only in requirements: {sorted(req_pins - yml_pins)}"
    )
