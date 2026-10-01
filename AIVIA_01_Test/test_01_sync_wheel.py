"""Tests for the wheel-sync script (AIVIA_01_Code/sync_wheel.py).

Design under test:
    AIVIA_01_Design/01_subject_sql_files.md — the wheel arrives in the
    Fabric Environment item via this sync script, run by Sunny's hand.

Written test-first: RED until sync_wheel.py exposes build_wheel() and
refuses to run without --workspace/--environment.

Only the local steps are pytest-able. Sign-in, upload and publish touch
the live Fabric service and Sunny's own sign-in; their acceptance test is
her first real run (she eyeballs aivia01 in the environment's library
list in the portal).
"""

import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"

sys.path.insert(0, str(CODE_DIR))
from sync_wheel import build_wheel  # noqa: E402

sys.path.remove(str(CODE_DIR))


def test_build_wheel_produces_aivia01_wheel_with_both_modules():
    """Pseudo code step 1: one aivia01 wheel, and it really contains the
    two modules the notebook will import (a wheel is a zip - look inside)."""
    wheel = build_wheel()
    assert wheel.exists()
    assert wheel.name.startswith("aivia01-0.3.0"), wheel.name
    assert wheel.suffix == ".whl"
    names = zipfile.ZipFile(wheel).namelist()
    assert "build_data_sheet.py" in names, names
    assert "local_chat.py" in names, names
    assert "load_lh_table.py" in names, names
    # the 04 loader and its import closure (M02, wheel 0.3.0)
    assert "load_dictionary_tables.py" in names, names
    assert "dictionary_graph.py" in names, names
    assert "chat_bot.py" in names, names
    assert "build_abstract_names.py" in names, names


def test_command_refuses_to_run_without_ids_naming_them():
    """The ids are parameters, never in code - and forgetting one fails
    loudly BEFORE any build, sign-in or upload happens."""
    proc = subprocess.run(
        [sys.executable, str(CODE_DIR / "sync_wheel.py")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "--workspace" in proc.stderr
    assert "--environment" in proc.stderr


def test_stale_wheel_names_lists_every_other_aivia01_wheel():
    """The version-collision mechanism (ruled 2026-09-27): a version bump
    changes the wheel FILE NAME, so Fabric would keep old and new side by
    side. Before uploading, the script deletes every stale aivia01 wheel
    from the environment's staging; this pins which names it targets."""
    from sync_wheel import build_wheel, stale_wheel_names

    current = build_wheel()
    stale = stale_wheel_names(current)
    assert current.name not in stale, "must never delete the wheel being shipped"
    assert all(n.startswith("aivia01-") and n.endswith(".whl") for n in stale)
    dist_names = {p.name for p in current.parent.glob("aivia01-*.whl")}
    assert set(stale) == dist_names - {current.name}, (
        "stale = every OTHER aivia01 wheel in dist"
    )
