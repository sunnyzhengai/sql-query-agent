"""Tests for the F21 notebook sync (AIVIA_01_Code/sync_notebook.py).

Design under test:
    AIVIA_01_Design/01_subject_sql_files.md — F21: notebook definitions
    sync from AIVIA_01_Code via the sync script; running stays by
    Sunny's hand.

Written test-first: RED until sync_notebook.py exposes split_cells()
and merge_definition(), and the notebook source file exists.

The live GET/merge/push against Fabric is acceptance-tested by Sunny's
first real sync (same cell visible in the portal, lakehouse/environment
attachments intact, run by her hand).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
NOTEBOOK_SOURCE = CODE_DIR / "notebook_f11_load_lh_table.py"

sys.path.insert(0, str(CODE_DIR))
from sync_notebook import merge_definition, split_cells  # noqa: E402

sys.path.remove(str(CODE_DIR))


# ---------------------------------------------------------------------------
# split_cells - pure
# ---------------------------------------------------------------------------


def test_no_marker_means_one_cell():
    cells = split_cells("a = 1\nb = 2\n")
    assert cells == ["a = 1\nb = 2"]


def test_cell_markers_split_and_are_not_included():
    text = "# %% first\na = 1\n\n# %% second\nb = 2\n"
    cells = split_cells(text)
    assert cells == ["a = 1", "b = 2"]
    assert all("# %%" not in c for c in cells)


# ---------------------------------------------------------------------------
# merge_definition - pure, the never-detach rule
# ---------------------------------------------------------------------------


def fabric_like_notebook():
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "dependencies": {
                "lakehouse": {"default_lakehouse_name": "AIVIA_01_LH"},
                "environment": {"environmentId": "1b87c0e2"},
            }
        },
        "cells": [
            {"cell_type": "code", "source": ["old = True\n"], "metadata": {},
             "outputs": [], "execution_count": 3},
        ],
    }


def test_merge_replaces_cells_and_keeps_metadata_byte_equal():
    original = fabric_like_notebook()
    metadata_before = json.dumps(original["metadata"], sort_keys=True)

    merged = merge_definition(original, ["new = 1", "newer = 2"])

    assert json.dumps(merged["metadata"], sort_keys=True) == metadata_before, (
        "lakehouse/environment attachments must survive the sync untouched"
    )
    assert merged["nbformat"] == 4
    assert len(merged["cells"]) == 2
    for cell in merged["cells"]:
        assert cell["cell_type"] == "code"
    assert "".join(merged["cells"][0]["source"]) == "new = 1"
    assert "old = True" not in json.dumps(merged["cells"])


def test_merge_refuses_unrecognized_shapes():
    with pytest.raises(ValueError):
        merge_definition({"no_cells_here": True}, ["x = 1"])
    with pytest.raises(ValueError):
        merge_definition("not a notebook", ["x = 1"])


# ---------------------------------------------------------------------------
# the notebook source file agrees with the F11/F13 rulings
# ---------------------------------------------------------------------------


def test_notebook_source_matches_the_rulings():
    text = NOTEBOOK_SOURCE.read_text(encoding="utf-8")
    assert "to_table_rows" in text
    assert 'saveAsTable("f01_subject_sql_files_lh_table")' in text
    assert "f01_subject_sql_files_graph" in text, (
        "the embedding-free graph export (ruled 2026-09-27) must ride the notebook"
    )
    assert 'drop("fileNameEmbedding")' in text


# ---------------------------------------------------------------------------
# the command fails loudly without its ids
# ---------------------------------------------------------------------------


def test_command_refuses_to_run_without_ids_naming_them():
    proc = subprocess.run(
        [sys.executable, str(CODE_DIR / "sync_notebook.py")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "--workspace" in proc.stderr
    assert "--notebook" in proc.stderr
    assert "--source" in proc.stderr
