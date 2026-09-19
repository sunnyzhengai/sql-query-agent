"""Brief_Packaging slice 1 (Sunny's "all four as proposed, build
it", 2026-09-19): THE SHIP SURFACE. Every GitHub zip download is
built by `git archive`, and `.gitattributes` export-ignore rules
shrink that archive to the minimum engine — his rulings made
mechanical: no SQL files ("i don't need to download any sql
files. i will use my work's"), no design docs ("i don't want any
design docs to go to work. i only want the minimum set of files
for the engine to work."). These pins read the actual archive
listing; they are the allowlist law, not a hope. Any future
relocation of a shipped file (the queued slice-2 moves, F-P1..
F-P4) fails a pin here and forces its declaration.

Proves: contract:aivia-design-to-code
"""
import io
import pathlib
import subprocess
import tarfile

import pytest

from aivia.graph.metamodel import REGISTRY_NAMES

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def archive_paths():
    """The file list of `git archive HEAD` under the CURRENT
    attribute rules (--worktree-attributes: the .gitattributes on
    disk governs, so the pin holds pre- and post-commit)."""
    out = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--worktree-attributes",
         "--format=tar", "HEAD"],
        capture_output=True, check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(out)) as tar:
        return [m.name for m in tar.getmembers() if m.isfile()]


# The ship set, exactly as the brief's table declares it.
_ALLOWED_DIR_PREFIXES = ("aivia/", "libs/", "pilots/")
_ALLOWED_EXACT = {
    "devtools/scribe_draft.py",
    "AIVIA_Product/SOP_Extract_Runbook.md",
}
_ALLOWED_CONSTRAINED = (
    # (prefix, required suffix) — files under prefix must match
    ("AIVIA_Design/registries/", ".json"),
    ("AIVIA_Product/source_packs/", ""),
)


def _allowed(path: str) -> bool:
    if path.startswith(_ALLOWED_DIR_PREFIXES) or path in _ALLOWED_EXACT:
        return True
    return any(path.startswith(p) and path.endswith(s)
               for p, s in _ALLOWED_CONSTRAINED)


def test_everything_shipped_is_allowlisted(archive_paths):
    strays = sorted(p for p in archive_paths if not _allowed(p))
    assert not strays, (
        f"{len(strays)} path(s) outside the ship set, first 20: "
        f"{strays[:20]}")


def test_no_sql_ships(archive_paths):
    """His ruling banned DATA sql ("i don't need to download any
    sql files. i will use my work's"); the source-pack scripts are
    PRODUCT TOOLS he ruled INTO the zip the same week ("every
    hospital customer who uses epic would use the exact same
    scripts") — the two intents meet here: no SQL ships outside
    the packs."""
    strays = [p for p in archive_paths if p.endswith(".sql")
              and not p.startswith("AIVIA_Product/source_packs/")]
    assert not strays, strays


def test_the_wheel_rides_its_own_road(archive_paths):
    """Brief_Fabric_Resident FR2: the zip is the SOURCE route, the
    wheel is the FABRIC route — dist/ never enters the archive."""
    assert not [p for p in archive_paths
                if p.startswith("dist/") or p.endswith(".whl")]


def test_no_design_docs_ship(archive_paths):
    assert not [p for p in archive_paths
                if p.startswith("AIVIA_Design/") and p.endswith(".md")]


def test_required_engine_files_present(archive_paths):
    required = {
        "aivia/console.py",
        "libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll",
        "pilots/work_dryrun/README_Runbook.md",
        "pilots/work_dryrun/registration_template.json",
        "devtools/scribe_draft.py",
        "AIVIA_Product/SOP_Extract_Runbook.md",
    } | {f"AIVIA_Design/registries/{n}.json" for n in REGISTRY_NAMES}
    missing = sorted(required - set(archive_paths))
    assert not missing, f"ship set incomplete: {missing}"
