"""Tests for the local web chat's ranking logic (AIVIA_01_Code/local_chat.py).

Design under test:
    AIVIA_01_Design/01_subject_sql_files.md — the local-web-chat step:
    reads the data sheet json, embeds the question with the same model,
    ranks all files by cosine similarity, returns all file names with scores.

Written test-first: RED until local_chat.py exposes
    cosine_similarity(a, b), rank_files(question_embedding, rows),
    answer(question, sheet_path, embedder).

The pure-math tests use handmade vectors — rank_files is arithmetic, not an
LLM call. Every question embedding is the REAL OpenAI API (CLAUDE.md law:
no fake calls), reusing real_embedder from the contract test file.

Sunny's hand cases pinned mechanically here: the CCMC top-2 and the
Hospitalist #1. The inpatient-census case stays Sunny's-eye-only — her md
says those three "may or may not" rank highest.
"""

import sys
from pathlib import Path

from test_01_subject_sql_files_data_contract import SHEET_PATH, real_embedder

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"

sys.path.insert(0, str(CODE_DIR))
from local_chat import answer, cosine_similarity, rank_files  # noqa: E402

sys.path.remove(str(CODE_DIR))

CCMC_FILES = {
    "Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_Detail_PBI",
    "Reporting_USP_CCMC_LOTE_Census_Interpreter_Services_Summary_PBI",
}
HOSPITALIST_FILE = "Reporting_USP_Hospitalist_Daily_Census_Report_92a_PBI"


# ---------------------------------------------------------------------------
# Pure math - no API calls
# ---------------------------------------------------------------------------


def test_cosine_similarity_of_a_vector_with_itself_is_one():
    v = [0.3, -1.2, 4.5, 0.01]
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-9


def test_rank_files_returns_all_rows_sorted_by_score():
    rows = [
        {"file_name": "OPPOSITE", "file_name_embedding": [-1.0, 0.0]},
        {"file_name": "EXACT", "file_name_embedding": [1.0, 0.0]},
        {"file_name": "SIDEWAYS", "file_name_embedding": [0.0, 1.0]},
    ]
    ranked = rank_files([1.0, 0.0], rows)
    assert [r["file_name"] for r in ranked] == ["EXACT", "SIDEWAYS", "OPPOSITE"]
    assert abs(ranked[0]["score"] - 1.0) < 1e-9
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# The real sheet + real question embeddings
# ---------------------------------------------------------------------------


def test_census_question_returns_all_files_scored_and_sorted():
    """Sunny's case 1: 'What reports are for census?' -> all 8 returned."""
    ranked = answer("What reports are for census?", SHEET_PATH, real_embedder)
    assert len(ranked) == 8, "chat must return ALL files, never a subset"
    for r in ranked:
        assert isinstance(r["score"], float)
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True), "highest score must come first"


def test_ccmc_question_returns_all_files():
    """Sunny's md (ruled 2026-09-26): the 2 CCMC names 'may or may not be
    ranked higher' — the embeddings cannot tell CCMC from CCHCS on file
    names alone, so no ranking is pinned. Only the firm part holds:
    all 8 files come back, both CCMC files among them."""
    ranked = answer("Which reports for for CCMC?", SHEET_PATH, real_embedder)
    assert len(ranked) == 8
    names = {r["file_name"] for r in ranked}
    assert CCMC_FILES <= names


def test_hospitalist_question_ranks_the_hospitalist_file_first():
    """Sunny's md: the Hospitalist report 'should be ranked higher than
    other files' -> position 1."""
    ranked = answer(
        "Which reports are for hospitalist census?", SHEET_PATH, real_embedder
    )
    assert ranked[0]["file_name"] == HOSPITALIST_FILE, (
        f"position 1 was {ranked[0]['file_name']}"
    )
