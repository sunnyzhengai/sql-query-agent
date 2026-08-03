"""Tests for the AgentBackend layer: prompts, retrieval, refusals, replay."""

import pytest

from src.agent_backend import (
    ReplayBackend,
    build_description_prompt,
    is_refusal,
    retrieve_metric_rows,
)

ROWS = [
    {"metric_id": "reporting.USP_ED_SEPSIS", "metric_name": "USP_ED_SEPSIS",
     "calculation_logic": "1. filter ED encounters 2. flag sepsis criteria",
     "source_tables": "encounter, department",
     "table_descriptions": "encounter: visits; department: units"},
    {"metric_id": "reporting.USP_READMIT", "metric_name": "USP_READMIT",
     "calculation_logic": "1. index admissions 2. 30-day window",
     "source_tables": "admission",
     "table_descriptions": "admission: inpatient stays"},
]


def test_description_prompt_grounds_in_contract_row():
    prompt = build_description_prompt(ROWS[0])
    assert "reporting.USP_ED_SEPSIS" in prompt
    assert "filter ED encounters" in prompt
    assert "encounter, department" in prompt


def test_retrieval_matches_metric_and_table_names_case_folded():
    hits = retrieve_metric_rows("how is reporting.usp_ed_sepsis calculated?", ROWS)
    assert [r["metric_id"] for r in hits] == ["reporting.USP_ED_SEPSIS"]
    hits = retrieve_metric_rows("what uses the ADMISSION table?", ROWS)
    assert [r["metric_id"] for r in hits] == ["reporting.USP_READMIT"]
    assert retrieve_metric_rows("unrelated question", ROWS) == []


def test_refusal_detection():
    assert is_refusal("I don't have that information in the certified knowledge base.")
    assert not is_refusal("The metric uses encounter and department tables.")


class FakeBackend:
    def __init__(self):
        self.calls = 0

    def answer(self, question):
        self.calls += 1
        return f"live answer to: {question}"

    def describe_metric(self, row):
        self.calls += 1
        return f"live description of {row['metric_id']}"


class TestReplayBackend:
    def test_record_then_replay_without_backend(self, tmp_path):
        cassette = tmp_path / "cassette.jsonl"
        fake = FakeBackend()
        recorder = ReplayBackend(cassette, backend=fake, mode="record")
        assert recorder.answer("q1") == "live answer to: q1"
        assert recorder.describe_metric(ROWS[0]) == "live description of reporting.USP_ED_SEPSIS"
        assert fake.calls == 2

        replayer = ReplayBackend(cassette, mode="replay")  # no backend at all
        assert replayer.answer("q1") == "live answer to: q1"
        assert replayer.describe_metric(ROWS[0]).endswith("USP_ED_SEPSIS")

    def test_replay_miss_raises_with_guidance(self, tmp_path):
        replayer = ReplayBackend(tmp_path / "empty.jsonl", mode="replay")
        with pytest.raises(KeyError, match="re-record"):
            replayer.answer("never recorded")

    def test_auto_mode_records_misses_and_replays_hits(self, tmp_path):
        cassette = tmp_path / "cassette.jsonl"
        fake = FakeBackend()
        auto = ReplayBackend(cassette, backend=fake, mode="auto")
        auto.answer("q1")
        auto.answer("q1")  # hit — no second live call
        assert fake.calls == 1

    def test_record_mode_requires_backend(self, tmp_path):
        with pytest.raises(ValueError, match="requires a wrapped backend"):
            ReplayBackend(tmp_path / "c.jsonl", mode="record")
