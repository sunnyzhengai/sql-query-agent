"""Tests for the ADR 0035 toolset: find, read, list, verify — and the
dispatch guarantees (no unsurfaced facts; errors as visible results)."""

import json

import pytest

from src.orchestrator.assemble import METRIC_FACTS_QUERY, NODE_FACTS_QUERY
from src.orchestrator.core import RESOLVE_QUERY
from src.orchestrator.tools import (
    BATCH_FRAGMENTS_QUERY,
    FIND_BY_NAME_QUERY,
    LIST_CATALOG_QUERY,
    DECISIONS_OF_STEP_QUERY,
    NAME_CONTAINS_QUERY,
    NAME_CONTAINS_TOKENS_QUERY,
    STEPS_OF_QUERY,
    TABLE_USED_BY_QUERY,
    Session,
    ToolError,
    check_same_logic,
    dispatch,
    find_by_name,
    get_facts,
    list_catalog,
    list_steps,
    search_catalog,
)

REF_A = "reporting.USP_ED_Sepsis"
REF_B = "reports.USP_ED_Sepsis"
STEP_1 = f"transform:{REF_A}:Scores"
STEP_2 = f"transform:{REF_B}:Scores"
STEP_3 = f"transform:{REF_B}:Labs"

METRIC_ROWS = {
    REF_A: {"metric_id": REF_A, "metric_name": "USP_ED_Sepsis",
            "business_name": "ED Sepsis Screening", "description": "d",
            "steward": "Pat", "developer": "Jane", "report_name": None,
            "report_url": None, "transform_count": 2,
            "source_tables": "ADT, LABS", "calculation_logic": "SELECT 1"},
    REF_B: {"metric_id": REF_B, "metric_name": "USP_ED_Sepsis",
            "business_name": "ED Sepsis (Regulatory)", "description": "d",
            "steward": "Pat", "developer": "Sam", "report_name": None,
            "report_url": None, "transform_count": 2,
            "source_tables": "ADT, MEDS", "calculation_logic": "SELECT 2"},
}
FRAGMENTS = {
    STEP_1: "SELECT S FROM T WHERE X >= 2",
    STEP_2: "select  s from t  where x >= 2",   # same logic, respaced
    STEP_3: "SELECT L",
}


def fake_kql(query, params):
    if query == RESOLVE_QUERY:
        return [
            {"node_id": f"canonical:{REF_A}", "kind": "metric", "ref": REF_A,
             "name": "USP_ED_Sepsis", "business_name": "ED Sepsis Screening",
             "display_text": "d", "closeness": 0.7, "total_matches": 3},
            {"node_id": STEP_1, "kind": "step", "ref": REF_A,
             "name": "Scores", "business_name": "", "display_text": "d",
             "closeness": 0.6, "total_matches": 3},
        ]
    if query == FIND_BY_NAME_QUERY:
        name = params["p_name"].lower()
        if name == "scores":
            return [{"node_id": s, "kind": "step", "ref": s.split(":")[1],
                     "name": "Scores", "business_name": ""}
                    for s in (STEP_1, STEP_2)]
        if name in ("ed sepsis screening", REF_A.lower()):
            return [{"node_id": f"canonical:{REF_A}", "kind": "metric",
                     "ref": REF_A, "name": "USP_ED_Sepsis",
                     "business_name": "ED Sepsis Screening"}]
        return []
    if query == DECISIONS_OF_STEP_QUERY:
        if params["p_step"] == STEP_1:
            return [{
                "node_id": f"decision:{REF_A}:Scores:w1",
                "name": "Scores/WHERE",
                "description": "filters scored rows",
                "properties": json.dumps({
                    "metric_id": REF_A, "step_name": "Scores",
                    "site_id": "w1", "context": "WHERE",
                    "predicate_count": 2,
                    "expression_sql":
                        "PatientName = 'John Smith' AND SepsisDX = 1",
                }),
            }]
        return []
    if query == TABLE_USED_BY_QUERY:
        # the fake graph: technical table IP_SEPSIS is read by both
        # metrics (walk find 2026-08-21 — table identity for phrases
        # the catalog surfaces cannot see)
        if params["p_phrase"].lower() in "ip_sepsis":
            return [
                {"table_name": "IP_SEPSIS", "ref": REF_A,
                 "business_name": "ED Sepsis Screening"},
                {"table_name": "IP_SEPSIS", "ref": REF_B,
                 "business_name": "ED Sepsis (Regulatory)"},
            ]
        return []
    if query == NAME_CONTAINS_TOKENS_QUERY:
        toks = [str(t).lower() for t in params["p_tokens"]]
        return [{"node_id": f"canonical:{ref}", "kind": "metric",
                 "ref": ref, "name": row["metric_name"],
                 "business_name": row["business_name"]}
                for ref, row in sorted(METRIC_ROWS.items())
                if all(t in (row["metric_name"] + " "
                             + row["business_name"]).lower()
                       for t in toks)]
    if query == NAME_CONTAINS_QUERY:
        p = params["p_phrase"].lower()
        return [{"node_id": f"canonical:{ref}", "kind": "metric",
                 "ref": ref, "name": row["metric_name"],
                 "business_name": row["business_name"]}
                for ref, row in sorted(METRIC_ROWS.items())
                if p in row["metric_name"].lower()
                or p in row["business_name"].lower()]
    if query == LIST_CATALOG_QUERY:
        kind = params["p_kind"]
        if kind == "metric":
            return [{"node_id": f"canonical:{ref}", "kind": "metric",
                     "ref": ref, "name": row["metric_name"],
                     "business_name": row["business_name"]}
                    for ref, row in sorted(METRIC_ROWS.items())]
        if kind == "step":
            return [{"node_id": s, "kind": "step",
                     "ref": s.split(":")[1], "name": s.split(":")[-1],
                     "business_name": ""}
                    for s in sorted(FRAGMENTS)]
        return []
    if query == METRIC_FACTS_QUERY:
        row = METRIC_ROWS.get(params["p_ref"])
        return [row] if row else []
    if query == NODE_FACTS_QUERY:
        node_id = params["p_node_id"]
        if node_id in FRAGMENTS:
            return [{"node_id": node_id, "name": node_id.split(":")[-1],
                     "properties": json.dumps(
                         {"metric_id": node_id.split(":")[1],
                          "sql_fragment": FRAGMENTS[node_id]})}]
        return []
    if query == STEPS_OF_QUERY:
        ref = params["p_ref"]
        return [{"node_id": s, "name": s.split(":")[-1]}
                for s in FRAGMENTS if f":{ref}:" in s]
    if query == BATCH_FRAGMENTS_QUERY:
        wanted = set(json.loads(params["p_ids"]))
        out = [{"node_id": s, "name": s.split(":")[-1],
                "description": f"what {s.split(':')[-1]} computes",
                "properties": json.dumps(
                    {"sql_fragment": FRAGMENTS[s], "step_no": 1})}
               for s in FRAGMENTS if s in wanted]
        for ref, row in METRIC_ROWS.items():
            cid = f"canonical:{ref}"
            if cid in wanted:
                out.append({"node_id": cid, "name": row["metric_name"],
                            "description": f"measures {row['business_name']}",
                            "properties": json.dumps(
                                {"business_name": row["business_name"],
                                 "steward": row["steward"],
                                 "developer": row["developer"]})})
        return out
    raise AssertionError(f"unexpected query: {query}")


class TestFind:
    def test_search_surfaces_ids_for_later_reads(self):
        s = Session()
        out = search_catalog("ed sepsis", fake_kql, s)
        ids = [c["id"] for c in out["candidates"]]
        assert REF_A in ids and STEP_1 in ids      # metric by ref, step by node_id
        assert s.permitted(REF_A) and s.permitted(STEP_1)

    def test_find_by_name_forgives_temp_table_spelling(self):
        s = Session()
        out = find_by_name("#Scores", fake_kql, s)
        assert out["count"] == 2
        assert s.permitted(STEP_1) and s.permitted(STEP_2)

    def test_find_by_business_name_and_ref(self):
        # live find (2026-08-10): users say business names and refs;
        # exact lookup must honor all three spellings
        s = Session()
        assert find_by_name("ED Sepsis Screening", fake_kql, s)["count"] == 1
        assert find_by_name(REF_A, fake_kql, s)["count"] == 1
        assert s.permitted(REF_A)

    def test_empty_name_lookup_blocks_the_none_exist_overclaim(self):
        """Field find (2026-08-20, web-UI test): 'how many metrics' was
        planned as find_by_name('metrics'); the honest empty was then
        captioned 'no metrics exist'. The empty result now carries the
        E6 guard pointing at the census tool."""
        out = find_by_name("metrics", fake_kql, Session())
        assert out["count"] == 0
        assert "list_catalog" in out["note"]


class TestCensus:
    def test_enumerates_every_metric_with_exact_count(self):
        s = Session()
        out = list_catalog("metric", fake_kql, s)
        assert out["count"] == 2
        assert {i["id"] for i in out["items"]} == {REF_A, REF_B}
        assert s.permitted(REF_A) and s.permitted(REF_B)
        assert "complete enumeration" in out["note"]

    def test_plural_kind_word_is_understood(self):
        out = list_catalog("metrics", fake_kql, Session())
        assert out["kind"] == "metric" and out["count"] == 2

    def test_unknown_kind_answers_with_the_kinds(self):
        with pytest.raises(ToolError, match="metric, step, term"):
            list_catalog("dashboards", fake_kql, Session())

    def test_dispatch_route(self):
        out = dispatch("list_catalog", {"kind": "metric"}, fake_kql, Session())
        assert out["count"] == 2


class TestGuarantee1:
    def test_unsurfaced_read_is_refused(self):
        with pytest.raises(ToolError, match="not surfaced"):
            get_facts(REF_A, fake_kql, Session())

    def test_user_named_id_is_allowed(self):
        s = Session()
        s.note_user(f"tell me about {REF_A}")
        assert get_facts(REF_A, fake_kql, s)["facts"]["business_name"] \
            == "ED Sepsis Screening"

    def test_surfaced_id_is_allowed(self):
        s = Session()
        search_catalog("ed sepsis", fake_kql, s)
        assert get_facts(STEP_1, fake_kql, s)["kind"] == "step"

    def test_dispatch_returns_errors_as_results(self):
        out = dispatch("get_facts", {"id": "ghost"}, fake_kql, Session())
        assert "not surfaced" in out["error"]
        assert dispatch("no_such_tool", {}, fake_kql, Session())["error"]


class TestReadAndList:
    def session(self):
        s = Session()
        s.note_user(f"{REF_A} {REF_B} {STEP_1} {STEP_2} {STEP_3}")
        return s

    def test_metric_and_step_facts(self):
        s = self.session()
        m = get_facts(REF_A, fake_kql, s)
        assert m["kind"] == "metric" and m["facts"]["developer"] == "Jane"
        st = get_facts(STEP_1, fake_kql, s)
        assert st["kind"] == "step"
        assert st["facts"]["sql_fragment"] == FRAGMENTS[STEP_1]

    def test_list_steps_surfaces_step_ids(self):
        s = self.session()
        out = list_steps(REF_B, fake_kql, s)
        assert {x["name"] for x in out["steps"]} == {"Scores", "Labs"}
        assert s.permitted(STEP_3)


class TestVerify:
    def session(self):
        s = Session()
        s.allow([REF_A, REF_B, STEP_1, STEP_2, STEP_3])
        return s

    def test_partition_whitespace_case_forgiven(self):
        out = check_same_logic([STEP_1, STEP_2], fake_kql, self.session())
        assert out["all_same"] is True
        assert out["distinct_definitions"] == 1

    def test_partition_diff_between_groups(self):
        out = check_same_logic([STEP_1, STEP_3], fake_kql, self.session())
        assert out["all_same"] is False
        assert out["distinct_definitions"] == 2
        assert "SELECT L" in out["diff_between_two_largest_groups"]

    def test_metric_refs_compare_whole_logic(self):
        out = check_same_logic([REF_A, REF_B], fake_kql, self.session())
        assert out["distinct_definitions"] == 2   # SELECT 1 vs SELECT 2

    def test_unrecorded_sql_is_never_sameness(self):
        s = self.session()
        s.allow(["transform:x.Y:Ghost"])
        out = check_same_logic([STEP_1, "transform:x.Y:Ghost"],
                               fake_kql, s)
        assert out["not_comparable"] == ["transform:x.Y:Ghost"]
        assert out["all_same"] is not True

    def test_requires_two_ids_and_surfacing(self):
        with pytest.raises(ToolError, match="at least two"):
            check_same_logic([STEP_1], fake_kql, self.session())
        with pytest.raises(ToolError, match="not surfaced"):
            check_same_logic([STEP_1, "transform:q.Q:Hidden"],
                             fake_kql, self.session())


class TestInfraErrorsAreResults:
    def test_kusto_outage_becomes_visible_tool_error(self):
        # Live find (2026-08-13): paused capacity surfaced as a raw 500.
        def dead_kql(query, params):
            raise RuntimeError("connection refused")
        s = Session()
        out = dispatch("search_catalog", {"phrase": "x"}, dead_kql, s)
        assert "unreachable" in out["error"]
        assert "RuntimeError" in out["error"]
