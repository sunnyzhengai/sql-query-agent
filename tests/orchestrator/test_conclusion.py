"""The Answer Format Contract's composer (RW-10): card class is
data-driven from displayed results, machine fields always win, prose
is additive. RW-11's policy card recognized by its fixed sentence.

Proves: contract:suite-legibility
"""

from src.orchestrator.conclusion import (
    FLAG_GLOSS,
    POLICY_REFUSAL,
    compose_conclusion,
)


def _out(op, rows, note="", universe=""):
    return {"result": {"op": op, "rows": rows, "note": note,
                       "universe": universe, "ref": "R1"}}


def test_flag_rows_compose_the_flags_card_with_glosses():
    c = compose_conclusion([_out("census", [
        {"flag_class": "cousin_conflict", "identity": "Diabetic "
         "Patients", "severity": "CONFLICT", "member_count": 10,
         "distinct_logics": 10, "disposition": "open",
         "description": "10 metrics answer to 'Diabetic Patients'…"},
    ], note="sweep receipt: 103 item(s) swept")],
        "some prose", True)
    assert c["kind"] == "flags"
    card = c["cards"][0]
    assert card["gloss"] == FLAG_GLOSS["cousin_conflict"]
    assert card["why"].startswith("10 metrics")
    assert "flags disclose, never gate" in c["closing"]
    assert "sweep receipt" in c["closing"]


def test_compare_composes_verdict_and_machine_diff_lines():
    c = compose_conclusion([
        _out("compare",
             [{"group": 1, "members": ["a"]},
              {"group": 2, "members": ["b"]},
              {"diff_between_two_largest_groups":
               "--- a\n+++ b\n+ 'E11.80'\n- nothing"}],
             note="2 hash groups — logic DIFFERS."),
        _out("retrieve", [{"kind": "metric", "business_name": "A",
                           "description": "d1", "id": "a"}]),
    ], "prose", True)
    assert c["kind"] == "compare" and c["verdict"] == "DIFFERS"
    assert c["diff_lines"] == ["+ 'E11.80'", "- nothing"]
    assert c["items"][0]["name"] == "A"


def test_records_compose_the_definition_card():
    c = compose_conclusion([_out("retrieve", [
        {"kind": "metric", "business_name": "X", "description": "dx",
         "id": "r.X", "decision_sites": [
             {"expression": "ICD_CODE LIKE 'E11%'"}]}])],
        "prose", True)
    assert c["kind"] == "definition"
    assert c["criteria"] == "ICD_CODE LIKE 'E11%'"


def test_policy_refusal_recognized_by_the_fixed_sentence():
    c = compose_conclusion(
        [_out("retrieve", [{"kind": "metric", "business_name": "X",
                            "description": "dx", "id": "r.X"}])],
        POLICY_REFUSAL + " Here is the certified definition.", False)
    assert c["kind"] == "policy_refusal"
    assert c["definition"]["name"] == "X"


def test_no_stamped_fields_returns_none():
    assert compose_conclusion([], "just prose", False) is None


def test_diff_distills_the_literal_delta_first():
    # glass check 2026-08-28: E11.80 sat buried at the end of two
    # 80-literal lines — the card leads with the exact delta
    c = compose_conclusion([
        _out("compare",
             [{"group": 1, "members": ["a"]},
              {"group": 2, "members": ["b"]},
              {"diff_between_two_largest_groups":
               "-WHERE X IN ('E11.79', 'E11.10')\n"
               "+WHERE X IN ('E11.79', 'E11.10', 'E11.80')"}],
             note="2 hash groups — logic DIFFERS."),
    ], "prose", True)
    assert c["diff_lines"][0] == \
        "+ E11.80 — present only in one definition"


class TestBatch6ComposerShapes:
    """RW-BATCH-6 item 2 (E-battery): feeds card for report links,
    map card for multi-record retrieves, and NO successful retrieve
    left cardless — a bare kind-None conclusion is a composer gap,
    never an answer."""

    def _out(self, rows, op="retrieve"):
        return [{"component": {"op": op, "params": {}},
                 "result": {"op": op, "rows": rows, "params": {},
                            "complete": True, "universe": "u"}}]

    def test_report_links_compose_the_feeds_card(self):
        c = compose_conclusion(self._out([{
            "id": "report:x", "kind": "report",
            "name": "Diabetes Registry Dashboard",
            "executes_metrics": [{"id": "reporting.USP_A",
                                  "name": "Active Diabetics"}],
            "reads_tables": [{"id": "table:DM", "name": "DM_REGISTRY"}],
            "measures": []}]), "", True)
        assert c["kind"] == "feeds"
        assert c["executes_metrics"] == ["Active Diabetics"]
        assert c["reads_tables"] == ["DM_REGISTRY"]

    def test_two_records_compose_the_map_card_not_definition(self):
        rows = [{"id": "transform:a:X", "kind": "step", "name": "X",
                 "description": "d1", "steps": [],
                 "source_tables": ["T1"]},
                {"id": "transform:b:X", "kind": "step", "name": "X",
                 "description": "d2", "steps": [],
                 "source_tables": ["T2"]}]
        c = compose_conclusion(self._out(rows), "", True)
        assert c["kind"] == "map"
        assert len(c["items"]) == 2
        assert c["items"][0]["source_tables"] == ["T1"]

    def test_single_record_still_composes_definition(self):
        c = compose_conclusion(self._out([{
            "id": "m", "kind": "metric", "name": "M",
            "business_name": "Metric M", "description": "d"}]),
            "", True)
        assert c["kind"] == "definition"

    def test_any_retrieved_row_composes_never_none(self):
        c = compose_conclusion(self._out([{
            "id": "table:ENCOUNTERS", "kind": "table",
            "name": "ENCOUNTERS"}]), "", True)
        assert c is not None and c["kind"] == "map"


class TestRW22CensusCard:
    """RW-22 (extended battery, the sole blocker): a census composes
    the census card — count line + rows; the composer-gap law is
    amended to ANY successful op."""

    def test_census_composes_count_line_and_rows(self):
        out = [{"component": {"op": "census", "params": {}},
                "result": {"op": "census", "params": {},
                           "complete": True,
                           "universe": "every certified metric",
                           "headline": "4 metric(s) — exact",
                           "rows": [
                               {"id": f"m{i}", "kind": "metric",
                                "name": f"M{i}",
                                "business_name": f"Metric {i}",
                                "description": f"d{i}"}
                               for i in range(4)]}}]
        c = compose_conclusion(out, "", True)
        assert c["kind"] == "census"
        assert c["count_line"] == "4 metric(s) — exact"
        assert c["total"] == 4
        assert c["items"][0] == {"name": "Metric 0",
                                 "description": "d0"}

    def test_any_op_rows_compose_the_law_amended(self):
        # a hypothetical future op with rows still composes — the
        # law reads ANY successful op, not any retrieve
        out = [{"component": {"op": "search", "params": {}},
                "result": {"op": "search", "params": {},
                           "complete": False, "universe": "u",
                           "rows": [{"id": "x", "kind": "term",
                                     "name": "X"}]}}]
        c = compose_conclusion(out, "", True)
        assert c is not None and c["kind"] == "map"
