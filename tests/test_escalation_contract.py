"""The Escalation Contract (ADR 0045) — checked in RED before
implementation, the ADR 0044 gating pattern: strict xfail per clause,
CI fails the moment a clause passes with its marker still present, and
removing the marker is the exit gate.

Sunny 2026-08-19: "HITL for every decision — no silent failing; always
bring the human in if the result of a step is not something the LLM or
our Python code can resolve. New SQL shape we didn't know before → add
it to the human's checklist."

Intended API surface (nothing below exists yet):
    src/schemas.py                 FALLOUT gains `resolution` (no NULL)
    src/governance/checklist.py    build_checklist(fallout_rows) -> rows
                                   for ops_human_checklist
"""

import inspect
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
ADR = REPO_ROOT / "docs" / "decisions" / \
    "0045-escalation-contract-human-checklist.md"


def clause(n: int):
    return pytest.mark.xfail(
        strict=True,
        reason=f"Escalation Contract clause {n} (ADR 0045); remove this "
               f"marker when the clause ships",
    )


class TestClause1TerminalStateLaw:
    @clause(1)
    def test_fallout_schema_requires_resolution_no_third_state(self):
        from src.schemas import TABLE_REGISTRY
        contract = TABLE_REGISTRY["ops_fallout"]
        cols = {name: (typ, nullable)
                for name, typ, nullable in contract["columns"]}
        assert "resolution" in cols, "undeclared residue is banned"
        assert cols["resolution"][1] is False, "no NULL, no third state"
        assert any("resolution" in inv and "escalated" in inv
                   for inv in contract["invariants"]), \
            "allowed values {auto_resolved, escalated} must be an invariant"

    @clause(1)
    def test_fallout_writers_must_declare_resolution(self):
        # The declaration IS the review: no default argument — every
        # writer states, at write time, whether a human must act.
        from src.governance.funnel import fallout_row
        param = inspect.signature(fallout_row).parameters["resolution"]
        assert param.default is inspect.Parameter.empty


class TestClause2TheChecklistIsAQuery:
    @clause(2)
    def test_checklist_is_escalated_open_rows_one_per_entity_reason(self):
        from src.governance.checklist import build_checklist
        fallout = [
            {"entity_id": "USP_X", "reason_code": "dynamic_sql",
             "stage": "300_tree_unextracted", "resolution": "escalated",
             "run_at": "2026-08-19T01:00:00"},
            {"entity_id": "USP_X", "reason_code": "dynamic_sql",
             "stage": "300_tree_unextracted", "resolution": "escalated",
             "run_at": "2026-08-19T02:00:00"},
            {"entity_id": "USP_Y", "reason_code": "retry_recovered",
             "stage": "600_generate_descriptions",
             "resolution": "auto_resolved",
             "run_at": "2026-08-19T02:00:00"},
        ]
        rows = build_checklist(fallout)
        assert len(rows) == 1, "auto_resolved never reaches the checklist; " \
            "repeats collapse to one item per (entity, reason)"
        item = rows[0]
        assert item["entity_id"] == "USP_X"
        assert item["status"] == "open"
        assert item["first_seen_run_at"] < item["last_seen_run_at"]


class TestClause3NoveltyAlwaysEscalates:
    @clause(3)
    def test_unknown_census_shape_escalates(self):
        # A new M shape is exactly the case where neither code nor LLM
        # has authority — it must become a checklist item, not only a
        # census counter.
        from src.mquery.census import census_fallout_rows
        rows = census_fallout_rows(
            [{"signature": "opaque-binary-1", "supported": False}],
            report_name="R")
        assert rows and all(r["resolution"] == "escalated" for r in rows)

    @clause(3)
    def test_flagged_round_trip_descriptions_escalate(self):
        from src.tree.pipeline import provenance_fallout_row
        row = provenance_fallout_row("step:USP_X:Base_Pop", "flagged")
        assert row["resolution"] == "escalated"


class TestClause4EscalationsCiteTheirContract:
    @clause(4)
    def test_every_escalated_row_names_a_contract_id(self):
        from src.governance.checklist import build_checklist
        rows = build_checklist([
            {"entity_id": "USP_X", "reason_code": "dynamic_sql",
             "stage": "300_tree_unextracted", "resolution": "escalated",
             "run_at": "2026-08-19T01:00:00"},
        ])
        assert rows[0]["contract_id"].startswith("contract:"), \
            "the admin self-serves from the row itself (ADR 0039 pattern)"


class TestContractIsLocked:
    """Green today — binds ADR 0045's clauses to this file."""

    def test_adr_0045_exists_and_states_all_four_clauses(self):
        text = ADR.read_text()
        for anchor in (
            "Terminal-state law",
            "checklist is a query",
            "Novelty always escalates",
            "cite their contract",
        ):
            assert anchor in text, f"ADR 0045 lost clause anchor: {anchor}"

    def test_every_clause_has_a_strict_exit_gate_in_this_file(self):
        source = Path(__file__).read_text()
        for n in range(1, 5):
            assert f"clause({n})" in source, \
                f"clause {n} has no exit-gate skeleton"
        assert "strict=True" in source
