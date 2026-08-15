"""Release consistency: a version bump must land in ALL THREE places.

A version lives in pyproject.toml, as a wheel in dist/, and as the custom
library inside the sql-logic-env Environment item — the third is what the
Fabric workspace actually installs. Pushes have shipped these out of sync
more than once (2026-08-15: dist/ had 1.6.0 while the Environment still
carried 1.5.6, so notebooks kept running old code). CI runs on every push,
so any inconsistent push goes red here.

The dist/ half is already pinned by tests/test_build_deployment_package.py;
this file pins the Environment half.
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


def test_environment_ships_exactly_one_product_wheel():
    wheels = sorted(ENV_LIBS.glob("sql_query_agent-*.whl"))
    assert len(wheels) == 1, (
        f"sql-logic-env must carry exactly one product wheel, found "
        f"{[w.name for w in wheels]} — Fabric installs whatever is here."
    )


def test_environment_wheel_matches_pyproject_version():
    version = pyproject_version()
    expected = f"sql_query_agent-{version}-py3-none-any.whl"
    wheels = [w.name for w in ENV_LIBS.glob("sql_query_agent-*.whl")]
    assert expected in wheels, (
        f"pyproject.toml says {version} but sql-logic-env ships {wheels}. "
        f"Release checklist: bump pyproject -> python -m build --wheel -> "
        f"copy dist/{expected} into {ENV_LIBS.relative_to(REPO)}/ "
        f"(replacing the old wheel) -> commit all three together."
    )


def test_environment_wheel_is_byte_identical_to_dist():
    """Same filename is not enough — a stale copy with the right name would
    still ship old code. The Environment wheel must BE the dist wheel."""
    version = pyproject_version()
    name = f"sql_query_agent-{version}-py3-none-any.whl"
    dist_wheel = REPO / "dist" / name
    env_wheel = ENV_LIBS / name
    if not dist_wheel.exists() or not env_wheel.exists():
        return  # the two tests above already report the actionable failure
    assert env_wheel.read_bytes() == dist_wheel.read_bytes(), (
        f"{name} differs between dist/ and the Environment item — "
        f"re-copy from dist/ so Fabric installs the wheel you built."
    )
