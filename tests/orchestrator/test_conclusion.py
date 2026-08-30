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


class TestRW23StringFieldsNeverIterateAsChars:
    """RW-23 (Sunny's walk find): source_tables arrives as a STRING
    on metric facts and the map card spelled 'DIAGNOSIS_CODES' as
    'D, I, A, G…' — for the tables question, the garbled field IS
    the answer. Content-asserted: full names render."""

    def _out(self, rows):
        return [{"component": {"op": "retrieve", "params": {}},
                 "result": {"op": "retrieve", "rows": rows,
                            "params": {}, "complete": True,
                            "universe": "u"}}]

    def test_string_source_tables_render_full_names(self):
        rows = [{"id": "m1", "kind": "metric", "name": "A",
                 "business_name": "Active Diabetic Patients",
                 "description": "d",
                 "source_tables": "DIAGNOSIS_CODES, MEDICATION_ORDERS"},
                {"id": "m2", "kind": "metric", "name": "B",
                 "business_name": "B", "description": "d",
                 "source_tables": "ENCOUNTERS"}]
        c = compose_conclusion(self._out(rows), "", True)
        assert c["kind"] == "map"
        assert c["items"][0]["source_tables"] == [
            "DIAGNOSIS_CODES", "MEDICATION_ORDERS"]
        assert c["items"][1]["source_tables"] == ["ENCOUNTERS"]
        # the char-split corpse can never return
        assert "D" not in c["items"][0]["source_tables"]

    def test_list_source_tables_pass_through(self):
        rows = [{"id": "m1", "kind": "metric", "name": "A",
                 "business_name": "A", "description": "",
                 "source_tables": ["T1", "T2"]},
                {"id": "m2", "kind": "metric", "name": "B",
                 "business_name": "B", "description": "",
                 "source_tables": []}]
        c = compose_conclusion(self._out(rows), "", True)
        assert c["items"][0]["source_tables"] == ["T1", "T2"]


def test_rw24_no_positional_language_in_composed_text():
    """RW-24 (Sunny's census read): positional words break under the
    folded answer-first layout — composed card text links the round
    ref instead. The census card carries its ref; a grep gate holds
    the page template and composer clean of layout-positional
    phrases."""
    from pathlib import Path
    repo = Path(__file__).resolve().parents[2]
    for rel in ("src/orchestrator/conclusion.py",
                "src/webapp/app.py"):
        text = (repo / rel).read_text()
        for phrase in ("table above", "table below", "listed above",
                       "shown above", "shown below", "see above",
                       "see below"):
            assert phrase not in text, f"{rel}: positional {phrase!r}"
    out = [{"component": {"op": "census", "params": {}},
            "result": {"op": "census", "ref": "R3", "params": {},
                       "complete": True, "universe": "u",
                       "headline": "30 metric(s)",
                       "rows": [{"id": f"m{i}", "kind": "metric",
                                 "name": f"M{i}",
                                 "business_name": f"M{i}",
                                 "description": ""}
                                for i in range(30)]}}]
    c = compose_conclusion(out, "", True)
    assert c["ref"] == "R3"          # the linkable round ref
    assert c["total"] == 30 and len(c["items"]) == 12


class TestGraphPanel1Subgraph:
    """GRAPH-PANEL-1: the subgraph derives EXCLUSIVELY from stamped
    results — receipts only, deterministic, P4/P5-safe (ids, names,
    kinds; never rows)."""

    def _out(self, op, rows, params=None):
        return {"component": {"op": op, "params": params or {}},
                "result": {"op": op, "rows": rows,
                           "params": params or {}, "complete": True,
                           "universe": "u"}}

    def _metric_turn(self):
        return [
            self._out("retrieve", [
                {"id": "m1", "kind": "metric",
                 "business_name": "Active Diabetics",
                 "steps": [{"id": "transform:m1:Reg",
                            "name": "Reg"}],
                 "source_tables": "DIAGNOSIS_CODES, ENCOUNTERS"}],
                {"ids": ["m1"]}),
            self._out("compare", [
                {"group": 1, "members": ["transform:a:X"]},
                {"group": 2, "members": ["transform:b:X"]}]),
        ]

    def test_nodes_edges_from_receipts_with_derived_marked(self):
        from src.orchestrator.conclusion import compose_subgraph
        g = compose_subgraph(self._metric_turn())
        ids = {n["id"] for n in g["nodes"]}
        assert {"m1", "transform:m1:Reg", "table:DIAGNOSIS_CODES",
                "table:ENCOUNTERS"} <= ids
        kinds = {(e["from"], e["to"]): e for e in [
            dict(e) for e in g["edges"]]}
        assert kinds[("m1", "transform:m1:Reg")]["label"] == "step"
        derived = [e for e in g["edges"] if e["derived"]]
        assert derived and derived[0]["label"] == "compared"
        # anchor emphasis from the retrieve params
        m1 = next(n for n in g["nodes"] if n["id"] == "m1")
        assert m1.get("anchor") is True

    def test_deterministic_identical_pictures(self):
        from src.orchestrator.conclusion import compose_subgraph
        a = compose_subgraph(self._metric_turn())
        b = compose_subgraph(self._metric_turn())
        assert a == b

    def test_p5_shape_ids_names_kinds_only(self):
        from src.orchestrator.conclusion import compose_subgraph
        g = compose_subgraph(self._metric_turn())
        for n in g["nodes"]:
            assert set(n) <= {"id", "kind", "name", "flag_class",
                              "anchor"}

    def test_empty_turn_is_none(self):
        from src.orchestrator.conclusion import compose_subgraph
        assert compose_subgraph([]) is None


class TestConsole2Fingerprints:
    """CONSOLE-2 (Sunny's glass — "not clear HOW they differ"):
    compare leads with member fingerprints; the contrast line is
    machine-assembled naming owners; the diff carries its labeled
    receipt line. One composer serves every surface."""

    def _outputs(self):
        return [
            {"component": {"op": "retrieve", "params": {}},
             "result": {"op": "retrieve", "params": {},
                        "complete": True, "universe": "u",
                        "rows": [
                {"id": "reporting.USP_DX", "kind": "metric",
                 "business_name": "Diabetic Patients (DX)",
                 "description": "Selects by diagnosis codes.",
                 "source_tables": "DIAGNOSIS_CODES, ENCOUNTERS",
                 "decision_sites": [
                     {"expression": "DX_CODE LIKE 'E11%'"}]},
                {"id": "reports.USP_MED", "kind": "metric",
                 "business_name": "Diabetic Patients (Med)",
                 "description": "Selects by medication orders.",
                 "source_tables": ["MEDICATION_ORDERS"],
                 "decision_sites": [
                     {"expression":
                      "ORDER_NAME IN ('METFORMIN')"}]}]}},
            {"component": {"op": "compare", "params": {}},
             "result": {"op": "compare", "params": {},
                        "complete": True, "universe": "u",
                        "note": "2 hash groups — DIFFERS.",
                        "rows": [
                {"group": 1, "members": ["reporting.USP_DX"]},
                {"group": 2, "members": ["reports.USP_MED"]}]}},
        ]

    def test_fingerprints_lead_with_reads_criterion_why(self):
        c = compose_conclusion(self._outputs(), "", True)
        assert c["kind"] == "compare"
        fps = {fp["id"]: fp for fp in c["fingerprints"]}
        dx = fps["reporting.USP_DX"]
        assert dx["reads"] == ["DIAGNOSIS_CODES", "ENCOUNTERS"]
        assert dx["criterion"] == "DX_CODE LIKE 'E11%'"
        assert dx["description"].startswith("Selects by diagnosis")
        assert dx["owner"] == "reporting"

    def test_contrast_names_owners_machine_assembled(self):
        c = compose_conclusion(self._outputs(), "", True)
        assert "reporting — DX_CODE LIKE 'E11%'" in c["contrast"]
        assert "reports — ORDER_NAME IN ('METFORMIN')" in \
            c["contrast"]

    def test_diff_receipt_labels_its_sides(self):
        c = compose_conclusion(self._outputs(), "", True)
        assert c["diff_label"] == ("receipt: − reporting.USP_DX · "
                                   "+ reports.USP_MED")

    def test_identical_verdict_has_no_contrast(self):
        outs = self._outputs()
        outs[1]["result"]["note"] = "1 hash group — IDENTICAL."
        outs[1]["result"]["rows"] = [
            {"group": 1, "members": ["reporting.USP_DX",
                                     "reports.USP_MED"]}]
        c = compose_conclusion(outs, "", True)
        assert c["contrast"] == ""
