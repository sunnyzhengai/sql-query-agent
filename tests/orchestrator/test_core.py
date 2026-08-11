"""Tests for the orchestrator core — ADR 0032's line, mechanically held."""

from src.orchestrator import (
    parse_pick,
    produce_search_token,
    resolve,
)
from src.orchestrator.core import RESOLVE_QUERY
from src.orchestrator.kusto import KustoClient


def rows(*specs):
    return [
        {"node_id": n, "kind": k, "ref": r, "name": nm,
         "business_name": bn, "display_text": f"{nm} display",
         "closeness": c, "total_matches": t}
        for (n, k, r, nm, bn, c, t) in specs
    ]

SAMPLE = rows(
    ("transform:a.M1:Readmit", "step", "a.M1", "Base_Pop_ED_Readmit", "", 0.51, 3),
    ("canonical:a.M1", "metric", "a.M1", "USP_ED", "ED Screening", 0.44, 3),
    ("canonical:b.M2", "metric", "b.M2", "USP_X", "", 0.40, 3),
)


class TestEntryEdge:
    def test_token_is_sanitized_single_line(self):
        chat = lambda sys, usr: '  "cancelled\nappointments"  '
        assert produce_search_token("q?", chat) == "cancelled appointments"

    def test_token_length_capped(self):
        chat = lambda sys, usr: "x " * 200
        assert len(produce_search_token("q?", chat)) <= 120


class TestCore:
    def test_one_fixed_command_token_is_a_parameter(self):
        seen = {}
        def run_kql(query, params):
            seen.update(query=query, params=params)
            return SAMPLE
        resolve("cancelled appointments", run_kql)
        assert seen["query"] == RESOLVE_QUERY          # never reconstructed
        assert seen["params"] == {"token": "cancelled appointments"}

    def test_ranked_by_closeness_ties_by_node_id(self):
        tied = rows(
            ("b", "step", "r", "B", "", 0.5, 2),
            ("a", "step", "r", "A", "", 0.5, 2),
        )
        result = resolve("t", lambda q, p: tied)
        assert [c.node_id for c in result.candidates] == ["a", "b"]

    def test_replay_property_identical_results(self):
        r1 = resolve("token", lambda q, p: list(SAMPLE))
        r2 = resolve("token", lambda q, p: list(SAMPLE))
        assert r1 == r2                                # byte-identical

    def test_empty_is_a_result_not_an_error(self):
        result = resolve("unicorn velocity", lambda q, p: [])
        assert result.candidates == () and result.total_matches == 0
        assert "0 above threshold" in result.basis

    def test_basis_is_stamped_by_code(self):
        result = resolve("sepsis screening", lambda q, p: SAMPLE)
        assert result.basis.startswith("semantic_search('sepsis screening')")
        assert "3 above threshold" in result.basis


class TestStratification:
    def test_metrics_group_before_steps_despite_closeness(self):
        # stratified plurality: the step outscores both metrics (0.51)
        # but the metric group leads; order within groups is closeness
        c = resolve("t", lambda q, p: SAMPLE).candidates
        assert [x.kind for x in c] == ["metric", "metric", "step"]
        assert c[0].business_name == "ED Screening"     # 0.44 > 0.40

    def test_per_proc_cap_frees_slots_for_other_procs(self):
        flood = rows(*[
            (f"transform:a.M1:S{i}", "step", "a.M1", f"S{i}", "",
             0.60 - i / 100, 9)
            for i in range(6)
        ], ("transform:b.M2:Other", "step", "b.M2", "Other", "", 0.40, 9))
        c = resolve("t", lambda q, p: flood).candidates
        step_refs = [x.ref for x in c if x.kind == "step"]
        assert step_refs.count("a.M1") == 2             # capped
        assert "b.M2" in step_refs                      # diversity slot


class TestStructuralPick:
    def cands(self):
        # stratified order: metrics first, then steps
        return resolve("t", lambda q, p: SAMPLE).candidates

    def test_number_pick(self):
        assert parse_pick("2", self.cands()) == 1

    def test_out_of_range_number_rejected(self):
        assert parse_pick("9", self.cands()) is None

    def test_exact_business_name_case_folded(self):
        assert parse_pick("ed screening", self.cands()) == 0

    def test_exact_ref_pick(self):
        assert parse_pick("b.M2", self.cands()) == 1

    def test_fuzzy_reply_rejected_not_guessed(self):
        assert parse_pick("the readmit one", self.cands()) is None


class TestKustoParsing:
    def test_primary_result_extraction(self):
        frames = [
            {"FrameType": "DataSetHeader"},
            {"FrameType": "DataTable", "TableKind": "QueryProperties",
             "Columns": [{"ColumnName": "x"}], "Rows": [[1]]},
            {"FrameType": "DataTable", "TableKind": "PrimaryResult",
             "Columns": [{"ColumnName": "node_id"}, {"ColumnName": "closeness"}],
             "Rows": [["a", 0.5], ["b", 0.4]]},
            {"FrameType": "DataSetCompletion"},
        ]
        rows = KustoClient._primary_rows(frames)
        assert rows == [{"node_id": "a", "closeness": 0.5},
                        {"node_id": "b", "closeness": 0.4}]
