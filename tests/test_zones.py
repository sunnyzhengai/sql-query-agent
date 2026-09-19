"""The declared-zones law (Sunny's verdict, 2026-08-20): governed ⊎
internal covers the repo — no unclassified top-level path, and nothing
in the internal zone can ever reach the deployment package."""

import subprocess
from pathlib import Path

from src.zones import INTERNAL_ZONE, classify

REPO = Path(__file__).resolve().parent.parent


def _top_level_entries():
    """Tracked AND about-to-be-tracked (untracked, not ignored).
    THE ECHO FIX (2026-09-19, second firing of the same class:
    pilots/ at the M7 close, .gitattributes at the Packaging push):
    enumerating only committed files let a new top-level path ride
    every pre-commit suite green and fail AFTER the push. Now the
    latch fires on the working tree, before any commit."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    return sorted({line.split("/", 1)[0] for line in out.splitlines() if line})


def test_every_top_level_path_is_classified():
    unclassified = [e for e in _top_level_entries() if classify(e) is None]
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


def test_internal_zone_stays_out_of_the_ship_surfaces():
    """Era 2 (Brief_Retirement, 2026-09-19: the deployment package
    and its FORBIDDEN pattern retired with era 1): the shipped
    boundaries are the zip (git archive) and the wheel — the
    internal zone must be export-ignored, so no archive carries it."""
    attrs = (REPO / ".gitattributes").read_text()
    assert "/* export-ignore" in attrs, (
        "the ship-surface default-deny is gone from .gitattributes")
    assert f"/{INTERNAL_ZONE} -export-ignore" not in attrs, (
        "internal/ must never be re-included in the ship zip")


def test_old_internal_home_is_gone():
    assert not (REPO / "docs" / "internal").exists(), (
        "docs/internal has moved to internal/docs — nothing may recreate it"
    )
