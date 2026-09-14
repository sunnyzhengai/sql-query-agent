"""The NULL-marker law: serialized database NULLs are absence, not content.

The incident (found 2026-09-14): 38 dictionary rows carried the literal
string "NULL" in DESCRIPTION; paraphrase_dictionary.py sent it to the
LLM, which faithfully rendered "No value is present." — placeholder
prose that then voiced as column meaning, entered grammar subjects
(#Base_Pop::cond#4), and blocked 4 blessings. The fix is at the
generator: null markers pass through as empty and never reach the
model. These pins keep the failure class dead.

Proves: law:walk-finds
"""

import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "paraphrase_dictionary", ROOT / "scripts" / "paraphrase_dictionary.py")
paraphrase_dictionary = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(paraphrase_dictionary)

SENTINEL = "No value is present."

DICTIONARY_FILES = [
    (ROOT / "data/synthetic/dict_tables.csv", "DESCRIPTION"),
    (ROOT / "data/synthetic/dict_columns.csv", "DESCRIPTION"),
    (ROOT / "AIVIA_Product/estates/ed_sepsis_dev/sepsis_snapshot/tables.csv", "description"),
    (ROOT / "AIVIA_Product/estates/ed_sepsis_dev/sepsis_snapshot/columns.csv", "description"),
    (ROOT / "AIVIA_Product/estates/sepsis/sepsis_snapshot/tables.csv", "description"),
    (ROOT / "AIVIA_Product/estates/sepsis/sepsis_snapshot/columns.csv", "description"),
]


def test_null_markers_are_absence():
    is_null = paraphrase_dictionary.is_null_marker
    for marker in ("NULL", " null ", "None", "N/A", "na", ""):
        assert is_null(marker), marker


def test_real_prose_is_never_a_null_marker():
    is_null = paraphrase_dictionary.is_null_marker
    for prose in (
        "The category value that identifies the patient's sex.",
        "null pointer flag for the event record",  # full-field match only
        "NA-accredited facility indicator",
    ):
        assert not is_null(prose), prose


def test_shipped_dictionaries_carry_no_manufactured_absence():
    """No row ships the sentinel prose or a bare null marker — absence
    in a description field is an empty field, nothing else."""
    for path, field in DICTIONARY_FILES:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                desc = row[field]
                assert desc != SENTINEL, (path.name, row)
                assert not (desc.strip() and paraphrase_dictionary.is_null_marker(desc)), (
                    path.name, row)
