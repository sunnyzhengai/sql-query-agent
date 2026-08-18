"""Step 07b logic: incremental plan, rejection persistence, batch saves.

Pins the field-note properties (2026-08-18): rejected rows persist with
status=rejected and retry next run; saves always carry the FULL row set
(resume-by-rerun); batch tallies and final tallies are distinct."""

from __future__ import annotations

from src.steps.agent_descriptions import (
    STATUS_OK,
    STATUS_REJECTED,
    is_rejection,
    plan_generation,
    run_generation,
    sql_hash,
)


class TestPlan:
    def test_new_metric_needs_generation(self):
        plan = plan_generation(["A"], {"A": "h1"}, [])
        assert plan.needs_generation == ["A"] and not plan.reused

    def test_unchanged_ok_row_is_reused(self):
        existing = [{"metric_name": "A", "sql_hash": "h1", "status": STATUS_OK}]
        plan = plan_generation(["A"], {"A": "h1"}, existing)
        assert plan.reused == ["A"] and not plan.needs_generation

    def test_changed_hash_regenerates(self):
        existing = [{"metric_name": "A", "sql_hash": "OLD", "status": STATUS_OK}]
        plan = plan_generation(["A"], {"A": "h1"}, existing)
        assert plan.needs_generation == ["A"]

    def test_rejected_rows_always_retry(self):
        existing = [{"metric_name": "A", "sql_hash": "h1", "status": STATUS_REJECTED}]
        plan = plan_generation(["A"], {"A": "h1"}, existing)
        assert plan.needs_generation == ["A"]
        assert plan.retrying_rejected == ["A"]

    def test_legacy_rows_without_status_count_as_ok(self):
        existing = [{"metric_name": "A", "sql_hash": "h1"}]
        plan = plan_generation(["A"], {"A": "h1"}, existing)
        assert plan.reused == ["A"]


class TestRejection:
    def test_non_answer_phrases(self):
        assert is_rejection("I wasn't able to find that metric.")
        assert is_rejection("I'm happy to help with other questions!")
        assert not is_rejection("Tracks sepsis screening compliance rates.")


class TestRunner:
    def _run(self, needs, answers, save_every=2):
        saves = []
        rows = {}
        result = run_generation(
            needs,
            generate=lambda n: answers[n],
            rows=rows,
            current_hashes={n: "h" for n in needs},
            save=lambda r: saves.append(list(r)),
            progress=lambda line: None,
            save_every=save_every,
        )
        return result, rows, saves

    def test_rejected_rows_persist_with_status(self):
        result, rows, saves = self._run(
            ["A", "B"],
            {"A": ("success", "Real description."),
             "B": ("success", "I wasn't able to find that.")},
        )
        assert result.succeeded == ["A"] and result.rejected == ["B"]
        assert rows["B"]["status"] == STATUS_REJECTED
        # the rejected row is IN the saved set — queryable, not stdout-only
        assert any(r["metric_name"] == "B" for r in saves[-1])

    def test_saves_carry_full_row_set(self):
        result, rows, saves = self._run(
            ["A", "B", "C", "D"],
            {n: ("success", f"Desc {n}.") for n in "ABCD"},
            save_every=2,
        )
        assert result.saves >= 2
        assert {r["metric_name"] for r in saves[-1]} == {"A", "B", "C", "D"}

    def test_errors_do_not_write_rows(self):
        result, rows, _ = self._run(
            ["A"], {"A": ("error", "HTTP 500")})
        assert result.failed == [("A", "HTTP 500")]
        assert "A" not in rows

    def test_final_summary_names_rejected_metrics(self):
        result, _, _ = self._run(
            ["A"], {"A": ("success", "not found in the knowledge base")})
        text = "\n".join(result.summary_lines())
        assert "rejected (agent non-answer): 1" in text
        assert "    A" in text


def test_sql_hash_stable():
    assert sql_hash("SELECT 1") == sql_hash("SELECT 1")
    assert sql_hash("SELECT 1") != sql_hash("SELECT 2")
