"""End-to-end pipeline tests using seed sample data."""

from scripts.seed_sample_data import SAMPLE_DICT_COLUMNS, SAMPLE_DICT_TABLES, SAMPLE_SQL_SOURCES
from src.graph.traversal import GraphTraverser
from src.models import NodeLayer
from src.pipeline import build_graph


class TestPipeline:
    def _build(self):
        return build_graph(SAMPLE_DICT_TABLES, SAMPLE_DICT_COLUMNS, SAMPLE_SQL_SOURCES)

    def test_builds_without_error(self):
        builder = self._build()
        assert len(builder.nodes) > 0
        assert len(builder.edges) > 0

    def test_canonical_node_exists(self):
        builder = self._build()
        assert "canonical:ER_LOS" in builder.nodes
        node = builder.nodes["canonical:ER_LOS"]
        assert node.name == "ER Length of Stay"
        assert node.properties["steward"] == "Dr. Smith"
        assert node.properties["developer"] == "jane.doe"

    def test_technical_nodes_from_dictionary(self):
        builder = self._build()
        # Table nodes
        assert "tech:encounter" in builder.nodes
        assert "tech:department" in builder.nodes
        assert "tech:patient" in builder.nodes
        # Column nodes
        assert "tech:encounter.admit_dt" in builder.nodes
        assert builder.nodes["tech:encounter.admit_dt"].description == "Admission date/time"

    def test_transformation_nodes_from_sql(self):
        builder = self._build()
        assert "transform:ER_LOS:er_visits" in builder.nodes
        assert "transform:ER_LOS:los_calc" in builder.nodes
        # sql_fragment should be populated
        er_visits = builder.nodes["transform:ER_LOS:er_visits"]
        assert "encounter" in er_visits.properties["sql_fragment"]

    def test_edges_connect_layers(self):
        builder = self._build()
        edge_pairs = [(e.source_id, e.target_id) for e in builder.edges]

        # Canonical -> last transformation
        assert ("canonical:ER_LOS", "transform:ER_LOS:los_calc") in edge_pairs

        # Transformation -> transformation (los_calc depends on er_visits)
        assert ("transform:ER_LOS:los_calc", "transform:ER_LOS:er_visits") in edge_pairs

        # Transformation -> technical (er_visits references encounter and department)
        assert ("transform:ER_LOS:er_visits", "tech:encounter") in edge_pairs
        assert ("transform:ER_LOS:er_visits", "tech:department") in edge_pairs

    def test_node_layer_counts(self):
        builder = self._build()
        layers = [n.layer for n in builder.nodes.values()]
        assert layers.count(NodeLayer.CANONICAL) == 1
        assert layers.count(NodeLayer.TRANSFORMATION) == 2
        # 3 tables + 9 columns = 12 technical nodes
        assert layers.count(NodeLayer.TECHNICAL) == 12

    def test_traversal_finds_full_subgraph(self):
        builder = self._build()
        traverser = GraphTraverser(builder.nodes, builder.edges)
        result = traverser.get_metric_subgraph("ER_LOS")

        assert result["canonical"].name == "ER Length of Stay"
        assert len(result["transformations"]) == 2
        assert len(result["technical"]) >= 2  # at least encounter + department
        assert len(result["sql_fragments"]) == 2
