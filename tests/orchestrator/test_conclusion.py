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
    # CONSOLE-4 v2: members carry the story; fragments stay in
    # the event record
    assert c["members"] and c["members"][0]["name"] == "A"


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


def test_literal_delta_leads_the_card():
    # glass check 2026-08-28 (E11.80 buried), CONSOLE-4 v2: the
    # delta now LEADS as the difference sentence + set summary;
    # raw fragments live in the event record, not the display
    c = compose_conclusion([
        _out("compare",
             [{"group": 1, "members": ["a"]},
              {"group": 2, "members": ["b"]},
              {"diff_between_two_largest_groups":
               "-WHERE X IN ('E11.79', 'E11.10', 'E11.20')\n"
               "+WHERE X IN ('E11.79', 'E11.10', 'E11.20', "
               "'E11.80')"}],
             note="2 hash groups — logic DIFFERS."),
    ], "prose", True)
    assert "E11.80 only in" in c["set_summary"]
    assert c["difference_lead"].startswith("The one difference:")
    assert "diff_lines" not in c        # display carries no SQL


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


class TestConsole4V2GridCard:
    """CONSOLE-4 v2 (design ratified): ONE distinguishing-set
    computation renders the GRID card for pairs — difference-lead
    sentence first, sames marked, pattern line deterministic,
    NO SQL in any steward-facing field, developer snippets labeled
    per member. The bare-name and false-count invariants carry
    forward."""

    def _codeset_outputs(self, n_extra=1):
        codes_a = ", ".join(f"'E11.{i:02d}'" for i in range(80))
        codes_b = codes_a + "".join(
            f", 'E11.{80 + i}'" for i in range(n_extra))
        diff = ("--- a\n+++ b\n"
                f"-WHERE ED.DX_CODE IN ({codes_a})\n"
                f"+WHERE ED.DX_CODE IN ({codes_b})")
        return [
            {"component": {"op": "retrieve", "params": {}},
             "result": {"op": "retrieve", "params": {},
                        "complete": True, "universe": "u",
                        "rows": [
                {"id": "reporting.USP_CodesetA", "kind": "metric",
                 "business_name": "Diabetic Codeset",
                 "description": "The hand-maintained list.",
                 "source_tables": "DIAGNOSIS_CODES",
                 "steward": "s@x",
                 "decision_sites": [{
                     "expression_sql":
                         f"ED.DX_CODE IN ({codes_a})",
                     "columns": ["DX_CODE"]}]},
                {"id": "reports.USP_CodesetB", "kind": "metric",
                 "business_name": "Diabetic Codeset",
                 "description": "The other list.",
                 "source_tables": "DIAGNOSIS_CODES",
                 "steward": "",
                 "decision_sites": [{
                     "expression_sql":
                         f"ED.DX_CODE IN ({codes_b})",
                     "columns": ["DX_CODE"]}]}]}},
            {"component": {"op": "compare", "params": {}},
             "result": {"op": "compare", "params": {},
                        "complete": True, "universe": "u",
                        "note": "2 hash groups — DIFFERS.",
                        "rows": [
                {"group": 1,
                 "members": ["reporting.USP_CodesetA"],
                 "diff_between_two_largest_groups": diff},
                {"group": 2,
                 "members": ["reports.USP_CodesetB"]}]}},
        ]

    def test_grid_mode_with_difference_lead_first(self):
        c = compose_conclusion(self._codeset_outputs(), "", True)
        assert c["mode"] == "grid"
        lead = c["difference_lead"]
        assert lead.startswith("The one difference:")
        assert "E11.80 only in Diabetic Codeset " \
               "(reports.USP_CodesetB)" in lead

    def test_sames_marked_in_the_grid(self):
        c = compose_conclusion(self._codeset_outputs(), "", True)
        rows = {r["aspect"]: r for r in c["grid"]}
        assert rows["selects from"]["same"] is True
        assert rows["the distinguishing element"]["same"] is False

    def test_pattern_line_superset_by_one(self):
        c = compose_conclusion(self._codeset_outputs(), "", True)
        assert "stale copy" in c["pattern_line"]

    def test_no_sql_reaches_steward_fields(self):
        c = compose_conclusion(self._codeset_outputs(), "", True)
        steward_blob = " ".join(
            [c["difference_lead"], c["pattern_line"],
             c["set_summary"]]
            + [cell for r in c["grid"] for cell in r["cells"]]
            + [p for m in c["members"]
               for p in m["distinguishing_plain"]])
        for token in ("SELECT", "WHERE", "IN ('", "NOT EXISTS"):
            assert token not in steward_blob, token

    def test_developer_snippets_labeled_per_member(self):
        c = compose_conclusion(self._codeset_outputs(), "", True)
        b = next(m for m in c["members"]
                 if m["id"] == "reports.USP_CodesetB")
        assert b["snippets"] and "E11.80" in b["snippets"][0]
        assert b["name"].endswith("(reports.USP_CodesetB)")

    def test_set_summary_and_qualified_names_carry_forward(self):
        c = compose_conclusion(self._codeset_outputs(), "", True)
        assert "80 value(s) shared" in c["set_summary"]
        assert "(reports.USP_CodesetB)" in c["set_summary"]

    def test_true_counts_in_business_words(self):
        c = compose_conclusion(self._codeset_outputs(), "", True)
        b = next(m for m in c["members"]
                 if m["id"] == "reports.USP_CodesetB")
        assert "81 listed value(s)" in b["distinguishing_plain"][0]


class TestConsole4V2Roster:
    def _ten_cousins(self):
        rows, groups = [], []
        for i in range(10):
            mid = f"reporting.USP_Cousin_{i}"
            rows.append({
                "id": mid, "kind": "metric",
                "business_name": "Diabetic Patients",
                "description": f"variant {i}",
                "source_tables": ("ENCOUNTERS" if i % 2
                                  else "DIAGNOSIS_CODES"),
                "steward": "",
                "decision_sites": [{
                    "expression_sql": f"HBA1C >= {6 + i}",
                    "columns": ["HBA1C"]}]})
            groups.append({"group": i + 1, "members": [mid]})
        return [
            {"component": {"op": "retrieve", "params": {}},
             "result": {"op": "retrieve", "params": {},
                        "complete": True, "universe": "u",
                        "rows": rows}},
            {"component": {"op": "compare", "params": {}},
             "result": {"op": "compare", "params": {},
                        "complete": True, "universe": "u",
                        "note": "10 hash groups — DIFFERS.",
                        "rows": groups}},
        ]

    def test_roster_law_above_three(self):
        c = compose_conclusion(self._ten_cousins(), "", True)
        assert c["mode"] == "roster"
        assert c["roster"], "no roster groups"
        total = sum(len(g["members"]) for g in c["roster"])
        assert total == 10
        # every roster line qualified (all ten share the name)
        for g in c["roster"]:
            for m in g["members"]:
                assert m["name"].endswith(f"({m['id']})")

    def test_grid_stays_at_three_or_fewer(self):
        outs = self._ten_cousins()
        outs[0]["result"]["rows"] = outs[0]["result"]["rows"][:3]
        outs[1]["result"]["rows"] = outs[1]["result"]["rows"][:3]
        c = compose_conclusion(outs, "", True)
        assert c["mode"] == "grid"


class TestConsole4c:
    """CONSOLE-4c (roster leaked plumbing): equijoins never enter
    the distinguishing set; aliases never face the steward; group
    headers are worded dominant READS; degraded templates yield to
    the RW-6 description; phrases cap at one breath."""

    def test_equijoins_are_structural_never_criteria(self):
        from src.orchestrator.conclusion import (
            _is_equijoin,
            _member_elements,
        )
        assert _is_equijoin("CC.PATIENT_ID = E.PATIENT_ID")
        assert not _is_equijoin("HBA1C = 6.5")       # literal side
        assert not _is_equijoin("X.CODE IN ('a','b')")
        els = _member_elements({
            "source_tables": "T1",
            "decision_sites": [
                {"expression_sql": "CC.PID = E.PID"},
                {"expression_sql": "HBA1C >= 6.5"}]})
        preds = [v for k, v in els if k == "pred"]
        assert preds == ["HBA1C >= 6.5"]

    def test_aliases_never_face_the_steward(self):
        from src.orchestrator.conclusion import _business_words
        assert _business_words(
            "pred", "CC.CPT_CODE IN ('a','b','c','d')") == \
            "limits CPT_CODE to 4 listed value(s)"
        assert _business_words("pred", "E.HBA1C >= 6.5") == \
            "requires HBA1C at least 6.5"

    def _cousins(self, specs):
        rows, groups = [], []
        for i, (tbl, expr) in enumerate(specs):
            mid = f"reporting.USP_C{i}"
            rows.append({
                "id": mid, "kind": "metric",
                "business_name": "Diabetic Patients",
                "description": f"Selects via {tbl.lower()}.",
                "source_tables": tbl, "steward": "",
                "decision_sites": ([{"expression_sql": expr}]
                                   if expr else [])})
            groups.append({"group": i + 1, "members": [mid]})
        return [
            {"component": {"op": "retrieve", "params": {}},
             "result": {"op": "retrieve", "params": {},
                        "complete": True, "universe": "u",
                        "rows": rows}},
            {"component": {"op": "compare", "params": {}},
             "result": {"op": "compare", "params": {},
                        "complete": True, "universe": "u",
                        "note": f"{len(specs)} hash groups — "
                                "DIFFERS.",
                        "rows": groups}},
        ]

    def test_roster_groups_by_worded_dominant_read(self):
        specs = [("DIAGNOSIS_CODES", "DX IN ('a','b','c','d')"),
                 ("DIAGNOSIS_CODES", "DX IN ('a','b','c','e')"),
                 ("LAB_RESULTS", "HBA1C >= 6.5"),
                 ("LAB_RESULTS", "HBA1C >= 7.0"),
                 ("MEDICATION_ORDERS", None),
                 ("BILLING_CLAIMS", None)]
        c = compose_conclusion(self._cousins(specs), "", True)
        assert c["mode"] == "roster"
        headers = {g["header"] for g in c["roster"]}
        assert "By diagnosis codes" in headers
        assert "By lab results" in headers
        # groups hold PAIRS, not singletons
        sizes = sorted(len(g["members"]) for g in c["roster"])
        assert max(sizes) >= 2

    def test_degraded_template_yields_to_description(self):
        specs = [("MEDICATION_ORDERS", None),
                 ("BILLING_CLAIMS", None),
                 ("LAB_RESULTS", None),
                 ("DIAGNOSIS_CODES", None)]
        c = compose_conclusion(self._cousins(specs), "", True)
        for g in c["roster"]:
            for m in g["members"]:
                assert len(m["phrase"]) <= 70
                assert "developer view" not in m["phrase"]


class TestConsole4dRosterTruth:
    """CONSOLE-4d (roster truth defects): each member's elements
    come from ITS OWN parsed steps only; every label is the
    qualified business-name form; an all-distinct family never
    phrases "(shared logic only)"; and the phrases match the real
    SQL (spot-asserted against the seeded estate's shapes)."""

    def _family(self):
        """The shapes estate's real family, shaped as the store
        delivers it: DX selects on ICD codes, Lab on HbA1c,
        Billing on CPT — three distinct methods, one name."""
        specs = [
            ("reporting.USP_Diabetic_Patients_DX", "DIAGNOSIS_CODES",
             "DC.ICD_CODE LIKE 'E11%'",
             "Diabetic patients identified from diagnosis codes."),
            ("reporting.USP_Diabetic_Patients_Lab", "LAB_RESULTS",
             "LR.HBA1C_VALUE >= 6.5",
             "Diabetic patients identified from lab results."),
            ("reporting.USP_Diabetic_Billing", "BILLING_CLAIMS",
             "CC.CPT_CODE IN ('99213', '99214', '99215', '99216')",
             "Diabetic patients identified from billing claims."),
        ]
        rows, groups = [], []
        for i, (mid, tbl, expr, desc) in enumerate(specs):
            rows.append({
                "id": mid, "kind": "metric",
                "business_name": "Diabetic Patients",
                "description": desc,
                "source_tables": tbl, "steward": "",
                "decision_sites": [{"expression_sql": expr,
                                    "step": "Base_Cohort"}]})
            groups.append({"group": i + 1, "members": [mid]})
        return [
            {"component": {"op": "retrieve", "params": {}},
             "result": {"op": "retrieve", "params": {},
                        "complete": True, "universe": "u",
                        "rows": rows}},
            {"component": {"op": "compare", "params": {}},
             "result": {"op": "compare", "params": {},
                        "complete": True, "universe": "u",
                        "note": "3 hash groups — DIFFERS.",
                        "rows": groups}},
        ]

    def _lines(self, card):
        if card["mode"] == "roster":
            return {m["id"]: m["phrase"]
                    for g in card["roster"] for m in g["members"]}
        return {m["id"]: "; ".join(m["distinguishing_plain"])
                for m in card["members"]}

    def test_no_cross_member_attribution(self):
        """The truth bug: DX carried HbA1c and MED_NAME criteria.
        Each phrase names only ITS member's own parsed predicate."""
        c = compose_conclusion(self._family(), "", True)
        lines = self._lines(c)
        dx = lines["reporting.USP_Diabetic_Patients_DX"]
        lab = lines["reporting.USP_Diabetic_Patients_Lab"]
        bill = lines["reporting.USP_Diabetic_Billing"]
        assert "ICD_CODE" in dx or "E11%" in dx
        assert "HBA1C" not in dx.upper()
        assert "CPT" not in dx.upper()
        assert "HBA1C" in lab.upper()
        assert "E11%" not in lab
        assert "CPT_CODE" in bill.upper()
        assert "HBA1C" not in bill.upper()

    def test_spot_asserts_against_the_real_sql(self):
        c = compose_conclusion(self._family(), "", True)
        lines = self._lines(c)
        assert "matches the pattern E11% on ICD_CODE" in \
            lines["reporting.USP_Diabetic_Patients_DX"]
        assert "requires HBA1C_VALUE at least 6.5" in \
            lines["reporting.USP_Diabetic_Patients_Lab"]
        assert "limits CPT_CODE to 4 listed value(s)" in \
            lines["reporting.USP_Diabetic_Billing"]

    def test_all_labels_are_qualified_business_names(self):
        """Item 2: no raw ids, no bare colliding names — every
        label is "<business name> (<ref>)" in one form."""
        c = compose_conclusion(self._family(), "", True)
        names = ([m["name"] for g in c["roster"]
                  for m in g["members"]] if c["mode"] == "roster"
                 else [m["name"] for m in c["members"]])
        assert len(names) == 3
        for n in names:
            assert n.startswith("Diabetic Patients (")
            assert n.endswith(")")

    def test_all_distinct_family_never_says_shared_logic_only(self):
        """The hash partition proved three groups for three members
        — claiming shared logic would be a lie."""
        c = compose_conclusion(self._family(), "", True)
        for phrase in self._lines(c).values():
            assert "(shared logic only)" not in phrase
            assert phrase.strip()


class TestConsole4dCompoundAndLabels:
    """CONSOLE-4d items 2-3: compound predicates phrase EVERY
    clause (the gestational twins' whole difference IS the second
    clause), and one label form holds across a family."""

    def test_gestational_twins_read_differently(self):
        from src.orchestrator.conclusion import _business_words
        excl = _business_words(
            "pred", "ED.DX_CODE LIKE 'E11%' AND "
                    "ED.DX_CODE NOT LIKE 'O24.4%'")
        incl = _business_words(
            "pred", "ED.DX_CODE LIKE 'E11%' OR "
                    "ED.DX_CODE LIKE 'O24.4%'")
        assert excl != incl
        assert "excludes the pattern O24.4%" in excl
        assert "also matches the pattern O24.4%" in incl

    def test_one_label_form_across_a_family(self):
        """A uniquely-named member beside colliding siblings still
        carries its ref — no bare/qualified mixture in a roster."""
        rows, groups = [], []
        names = ["Diabetic Patients", "Diabetic Patients",
                 "Diabetic Patients (Panel)", "D4", "D5", "D6"]
        for i, nm in enumerate(names):
            mid = f"reporting.USP_M{i}"
            rows.append({"id": mid, "kind": "metric",
                         "business_name": nm, "description": "d",
                         "source_tables": f"T{i}", "steward": "",
                         "decision_sites": [{
                             "expression_sql": f"C{i} >= {i}"}]})
            groups.append({"group": i + 1, "members": [mid]})
        c = compose_conclusion([
            {"component": {"op": "retrieve", "params": {}},
             "result": {"op": "retrieve", "params": {},
                        "complete": True, "universe": "u",
                        "rows": rows}},
            {"component": {"op": "compare", "params": {}},
             "result": {"op": "compare", "params": {},
                        "complete": True, "universe": "u",
                        "note": "6 hash groups — DIFFERS.",
                        "rows": groups}}], "", True)
        labels = [m["name"] for g in c["roster"]
                  for m in g["members"]]
        assert len(labels) == 6
        assert all(lb.endswith(")") and "(reporting.USP_M" in lb
                   for lb in labels), labels
