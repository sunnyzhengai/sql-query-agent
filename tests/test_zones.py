"""The declared-zones law (Sunny's verdict, 2026-08-20): governed ⊎
internal covers the repo — no unclassified top-level path, and nothing
in the internal zone can ever reach the deployment package."""

import subprocess
from pathlib import Path

from src.zones import INTERNAL_ZONE, classify

REPO = Path(__file__).resolve().parent.parent


def _top_level_tracked():
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True,
        check=True,
    ).stdout
    return sorted({line.split("/", 1)[0] for line in out.splitlines() if line})


def test_every_top_level_path_is_classified():
    unclassified = [e for e in _top_level_tracked() if classify(e) is None]
    assert not unclassified, (
        f"unclassified top-level path(s) {unclassified} — declare them in "
        f"src/zones.py GOVERNED_ENTRIES or move them under {INTERNAL_ZONE}/"
    )


def test_internal_zone_exists_and_is_internal():
    assert classify(INTERNAL_ZONE) == "internal"
    assert (REPO / INTERNAL_ZONE / "docs").is_dir(), (
        "internal/docs missing — the 2026-08-20 carve-out moved "
        "docs/internal there"
    )


def test_internal_zone_can_never_ship():
    """The deployment package's FORBIDDEN pattern is the shipped-boundary
    enforcement; the zone name must stay inside it."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bdp", REPO / "scripts" / "build_deployment_package.py")
    bdp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bdp)
    assert bdp.FORBIDDEN.search(f"{INTERNAL_ZONE}/docs/ROADMAP.md")


def test_old_internal_home_is_gone():
    assert not (REPO / "docs" / "internal").exists(), (
        "docs/internal has moved to internal/docs — nothing may recreate it"
    )
