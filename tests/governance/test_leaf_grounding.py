"""Leaf grounding (spec:C4) — completely_parsed is computed, never felt.

Unit shapes plus the recorded corpus: the verdict must be deterministic
over production-parser truth, and every ungrounded file must produce an
escalated fallout row (spec:H2 — novelty always escalates)."""

import json
from pathlib import Path

from src.governance.leaf_grounding import (
    FALLOUT_STAGE,
    grounding_lines,
    leaf_grounding,
)

FIXTURES = Path(__file__).parent.parent / "fixtures" / "recorded"


def _parse_row(metric_id, cte_tables, final_tables):
    return {
        "metric_id": metric_id,
        "ctes_json": json.dumps([
            {"name": "s1", "table_refs": [
                {"table": t, "schema": "dbo", "database": None}
                for t in cte_tables]}
        ]),
        "final_select_tables": json.dumps([
            {"table": t, "schema": "dbo", "database": None}
            for t in final_tables]),
    }


DICT = [{"TABLE_NAME": "HOSPITAL_ENCOUNTERS"}, {"TABLE_NAME": "Patients"}]


class TestVerdicts:
    def test_grounded_file_is_completely_parsed(self):
        r = leaf_grounding(
            [_parse_row("m1", ["HOSPITAL_ENCOUNTERS"], ["PATIENTS"])], DICT)
        assert r.verdicts[0]["completely_parsed"] is True
        assert r.fraction_grounded == 1.0 and not r.fallout_rows

    def test_matching_is_case_insensitive(self):
        r = leaf_grounding(
            [_parse_row("m1", ["hospital_encounters"], [])], DICT)
        assert r.verdicts[0]["completely_parsed"] is True

    def test_unknown_leaf_is_counted_and_escalated(self):
        r = leaf_grounding(
            [_parse_row("m1", ["HOSPITAL_ENCOUNTERS", "MYSTERY_TBL"], [])],
            DICT, run_at="2026-08-19T00:00:00")
        v = r.verdicts[0]
        assert v["completely_parsed"] is False
        assert v["ungrounded_leaves"] == ["MYSTERY_TBL"]
        row = r.fallout_rows[0]
        assert row["stage"] == FALLOUT_STAGE
        assert row["resolution"] == "escalated"
        assert "MYSTERY_TBL" in row["reason_text"]
        assert r.fraction_grounded == 0.0

    def test_empty_corpus_is_vacuously_grounded(self):
        r = leaf_grounding([], DICT)
        assert r.fraction_grounded == 1.0

    def test_summary_lines_name_the_offenders(self):
        r = leaf_grounding(
            [_parse_row("m1", ["MYSTERY_TBL"], []),
             _parse_row("m2", ["PATIENTS"], [])], DICT)
        lines = grounding_lines(r)
        assert "1/2" in lines[0]
        assert any("MYSTERY_TBL" in ln for ln in lines)


class TestRecordedCorpus:
    def test_verdict_is_deterministic_over_recorded_fixtures(self):
        parse_rows = json.loads((FIXTURES / "parse_results.json").read_text())
        dict_rows = json.loads((FIXTURES / "dict_tables.json").read_text())
        r1 = leaf_grounding(parse_rows, dict_rows)
        r2 = leaf_grounding(parse_rows, dict_rows)
        assert r1.verdicts == r2.verdicts
        assert r1.total_files == len(parse_rows) == 28
        # the honest number exists and every ungrounded file has fallout
        assert 0.0 <= r1.fraction_grounded <= 1.0
        assert len(r1.fallout_rows) == sum(
            1 for v in r1.verdicts if not v["completely_parsed"])
