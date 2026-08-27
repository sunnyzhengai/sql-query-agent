"""The toolchain contract (ruled by Sunny 2026-08-19, delivered 1.30.0).

Runtime libraries have a version spine (environment/requirements.txt,
enforced by test_release_consistency). Developer TOOLS had none — ruff
resolved fresh on CI while dev ran a 3-year-old version, producing
three lint-only CI failures in one day. The contract: every tool that
can fail CI is pinned EXACTLY in the dev extra; a floor (>=) on a tool
is drift waiting to happen and fails here with the incident named.

Proves: contract:toolchain
"""

import re
from pathlib import Path

PYPROJECT = (Path(__file__).parent.parent / "pyproject.toml").read_text()

# Tools that run in CI and can fail the build.
CI_TOOLS = ("pytest", "pytest-cov", "ruff", "build")


def _dev_extra() -> str:
    m = re.search(r"dev = \[(.*?)\]", PYPROJECT, re.S)
    assert m, "pyproject has no dev extra"
    return m.group(1)


def test_every_ci_tool_is_pinned_exactly():
    dev = _dev_extra()
    for tool in CI_TOOLS:
        m = re.search(rf'"{re.escape(tool)}([=<>!~][^"]*)"', dev)
        assert m, f"{tool} missing from the dev extra"
        assert m.group(1).startswith("=="), (
            f"{tool} declared as '{tool}{m.group(1)}' — CI tools are pinned "
            f"EXACTLY (the 2026-08-19 ruff skew incident); update the pin "
            f"deliberately, never float it"
        )


def test_no_ci_tool_hides_outside_the_dev_extra():
    """A CI tool declared in runtime dependencies would dodge the pin
    check above."""
    runtime = re.search(r"^dependencies = \[(.*?)\]", PYPROJECT, re.S | re.M)
    assert runtime
    for tool in CI_TOOLS:
        assert f'"{tool}' not in runtime.group(1), (
            f"{tool} belongs in the dev extra, pinned")
