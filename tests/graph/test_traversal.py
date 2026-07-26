"""Unit tests for graph traversal."""

from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.parser.sql_parser import parse_sql


class TestGraphTraversal:
    def _build_sample_graph(self) -> GraphBuilder:
        gb = GraphBuilder()
        gb.add_canonical_node("ER_LOS", "ER Length of Stay")
        gb.add_technical_node("encounter")
        gb.add_technical_node("department")

        sql = """
        WITH er_visits AS (
            SELECT e.encounter_id FROM encounter e
            INNER JOIN department d ON e.department_id = d.department_id
        ),
        los_calc AS (
            SELECT encounter_id FROM er_visits
        )
        SELECT * FROM los_calc
        """
        parsed = parse_sql(sql)
        gb.build_from_parsed_sql("ER_LOS", parsed)
        return gb

    def test_get_metric_subgraph(self):
        gb = self._build_sample_graph()
        traverser = GraphTraverser(gb.nodes, gb.edges)
        result = traverser.get_metric_subgraph("ER_LOS")

        assert result["canonical"].name == "ER Length of Stay"
        assert len(result["transformations"]) == 2
        assert len(result["technical"]) >= 1

    def test_unknown_metric_returns_empty(self):
        gb = self._build_sample_graph()
        traverser = GraphTraverser(gb.nodes, gb.edges)
        result = traverser.get_metric_subgraph("NONEXISTENT")
        assert result == {}
