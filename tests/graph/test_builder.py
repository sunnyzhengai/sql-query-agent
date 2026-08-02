"""Unit tests for graph builder."""

from src.graph.builder import GraphBuilder
from src.models import NodeLayer
from src.parser.sql_parser import parse_sql


class TestGraphBuilder:
    def test_add_technical_node(self):
        gb = GraphBuilder()
        node_id = gb.add_technical_node("encounter", "admit_dt", "Admission date")
        assert node_id == "tech:DBO.ENCOUNTER.ADMIT_DT"
        assert gb.nodes[node_id].layer == NodeLayer.TECHNICAL
        assert gb.nodes[node_id].properties["schema"] == "dbo"

    def test_add_technical_node_with_schema(self):
        gb = GraphBuilder()
        node_id = gb.add_technical_node("encounter", schema="reporting", description="Encounters")
        assert node_id == "tech:REPORTING.ENCOUNTER"
        assert gb.nodes[node_id].properties["schema"] == "reporting"

    def test_case_variants_resolve_to_one_node(self):
        """Dictionary case and SQL case must meet at the same node (ADR 0016)."""
        gb = GraphBuilder()
        dict_id = gb.add_technical_node("ENCOUNTER", description="Patient encounters")
        sql_id = gb.add_technical_node("encounter")
        assert dict_id == sql_id == "tech:DBO.ENCOUNTER"
        # First writer's description survives; display name preserved
        assert gb.nodes[dict_id].description == "Patient encounters"
        assert gb.nodes[dict_id].name == "ENCOUNTER"

    def test_add_canonical_node(self):
        gb = GraphBuilder()
        node_id = gb.add_canonical_node("ER_LOS", "ER Length of Stay", steward="Dr. Smith")
        assert node_id == "canonical:ER_LOS"
        assert gb.nodes[node_id].properties["steward"] == "Dr. Smith"

    def test_build_from_parsed_sql(self):
        gb = GraphBuilder()

        # Set up prerequisite nodes
        gb.add_canonical_node("ER_LOS", "ER Length of Stay")
        gb.add_technical_node("encounter")
        gb.add_technical_node("department")

        sql = """
        WITH er_visits AS (
            SELECT e.encounter_id, e.admit_dt
            FROM encounter e
            INNER JOIN department d ON e.department_id = d.department_id
        ),
        los_calc AS (
            SELECT encounter_id, DATEDIFF(MINUTE, admit_dt, discharge_dt) / 60.0 AS los_hours
            FROM er_visits
        )
        SELECT AVG(los_hours) FROM los_calc
        """
        parsed = parse_sql(sql)
        gb.build_from_parsed_sql("ER_LOS", parsed)

        # Should have transformation nodes for both CTEs
        assert "transform:ER_LOS:er_visits" in gb.nodes
        assert "transform:ER_LOS:los_calc" in gb.nodes

        # Should have edges
        assert len(gb.edges) > 0
