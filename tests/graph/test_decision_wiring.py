"""Decision nodes in the graph (ADR 0044 1b) + the reachability law.

Sunny's design, verbatim intent: every WHERE clause is a node connected
to the columns it uses, and "every parsed item should be connected to
the tree and eventually connected to end nodes, which are technical
nodes" — connected or counted, no dangling decisions."""

import json

from src.steps.build_graph import build_graph_step

DICT_TABLES = [
    {"TABLE_NAME": "HOSPITAL_ENCOUNTERS", "DESCRIPTION": "encounters"},
    {"TABLE_NAME": "PATIENTS", "DESCRIPTION": "patients"},
]
DICT_COLUMNS = [
    {"TABLE_NAME": "HOSPITAL_ENCOUNTERS", "COLUMN_NAME": "ENCOUNTER_ID",
     "DESCRIPTION": "id"},
    {"TABLE_NAME": "HOSPITAL_ENCOUNTERS", "COLUMN_NAME": "ADT_ARRIVAL_DATE",
     "DESCRIPTION": "arrival"},
    {"TABLE_NAME": "PATIENTS", "COLUMN_NAME": "PATIENT_ID", "DESCRIPTION": "id"},
]


def _parse_row(metric_id, ctes):
    return {
        "metric_id": metric_id, "name": metric_id.split(".")[-1],
        "ctes_json": json.dumps(ctes),
        "final_select_tables": "[]", "final_select_cte_refs": "[]",
        "final_select_columns": "[]", "normalized_sql": "",
        "cte_count": len(ctes), "table_count": 0, "line_count": 1,
    }


def _cte(name, fragment, tables=(), depends=()):
    return {
        "name": name, "sql_fragment": fragment,
        "column_refs": [],
        "table_refs": [{"table": t, "schema": "dbo", "database": None}
                       for t in tables],
        "depends_on": list(depends),
    }


def _build(fragment, tables=("HOSPITAL_ENCOUNTERS",), extra_ctes=()):
    ctes = [_cte("Base_Pop", fragment, tables)] + list(extra_ctes)
    return build_graph_step(
        [_parse_row("dbo.USP_X", ctes)], DICT_TABLES, DICT_COLUMNS)


class TestDecisionNodesAndEdges:
    def test_where_decision_connects_to_the_column_end_node(self):
        out = _build(
            "SELECT a INTO #Base_Pop FROM dbo.HOSPITAL_ENCOUNTERS HE "
            "WHERE HE.ADT_ARRIVAL_DATE BETWEEN @s AND @e")
        decision_nodes = [n for n in out.nodes_rows if n["layer"] == "decision"]
        assert len(decision_nodes) == 1
        edges = {(e["source_id"], e["target_id"], e["edge_type"])
                 for e in out.edges_rows}
        step = "transform:dbo.USP_X:Base_Pop"
        dec = decision_nodes[0]["node_id"]
        assert (step, dec, "step_to_decision") in edges
        assert (dec, "tech:DBO.HOSPITAL_ENCOUNTERS.ADT_ARRIVAL_DATE",
                "decision_to_column") in edges
        row = [r for r in out.decision_rows if r["status"] == "extracted"][0]
        assert row["reachability"] == "connected"

    def test_undictionaried_column_falls_back_to_table_grain(self):
        out = _build(
            "SELECT a INTO #Base_Pop FROM dbo.HOSPITAL_ENCOUNTERS HE "
            "WHERE HE.NOT_IN_DICT_COL = 1")
        edges = {(e["source_id"], e["target_id"], e["edge_type"])
                 for e in out.edges_rows}
        dec = [n["node_id"] for n in out.nodes_rows if n["layer"] == "decision"][0]
        assert (dec, "tech:DBO.HOSPITAL_ENCOUNTERS", "decision_to_column") in edges

    def test_temp_side_decision_connects_through_the_step(self):
        prior = _cte("Prior", "SELECT x INTO #Prior FROM dbo.PATIENTS",
                     ("PATIENTS",))
        out = _build(
            "SELECT a INTO #Base_Pop FROM #Prior P "
            "WHERE P.PATIENT_ID = 5", tables=(), extra_ctes=[prior])
        edges = {(e["source_id"], e["target_id"], e["edge_type"])
                 for e in out.edges_rows}
        dec = [n["node_id"] for n in out.nodes_rows
               if n["layer"] == "decision"
               and "Base_Pop" in n["node_id"]][0]
        assert (dec, "transform:dbo.USP_X:Prior", "decision_to_step") in edges

    def test_literal_only_decision_is_counted_not_dangling(self):
        out = _build(
            "SELECT a INTO #Base_Pop FROM dbo.HOSPITAL_ENCOUNTERS "
            "WHERE 1 = 1")
        row = [r for r in out.decision_rows if r["status"] == "extracted"][0]
        assert row["reachability"] == "literal_only"

    def test_parameter_default_site_reaches_rows_and_graph(self):
        out = _build(
            "IF @StartDate IS NULL SET @dStart = dbo.fn_parse_date('MB-12')")
        rows = [r for r in out.decision_rows
                if r["context"] == "parameter_default"]
        assert len(rows) == 1
        assert rows[0]["status"] == "extracted"
        assert rows[0]["reachability"] == "parameter_only"
        assert "'MB-12'" in json.loads(rows[0]["tree"])["operands"]

    def test_reachability_law_no_third_state(self):
        """Connected or counted — every extracted site carries a verdict."""
        out = _build(
            "SELECT a INTO #Base_Pop FROM dbo.HOSPITAL_ENCOUNTERS HE "
            "INNER JOIN dbo.PATIENTS P ON P.PATIENT_ID = HE.ENCOUNTER_ID "
            "WHERE HE.ADT_ARRIVAL_DATE BETWEEN @s AND @e AND 1 = 1")
        for r in out.decision_rows:
            if r["status"] == "extracted":
                assert r["reachability"] in (
                    "connected", "literal_only", "parameter_only",
                    "unresolved_alias", "unqualified"), r
