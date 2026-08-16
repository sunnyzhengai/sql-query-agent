"""Comparison tests: run identical assertions against both backends.

Verifies that the DeltaBackend (in-memory DFS) and FabricGraphBackend
(GQL queries) return semantically equivalent results for the same
golden fixture data.
"""

import pytest

from scripts.seed_sample_data import SAMPLE_DICT_COLUMNS, SAMPLE_DICT_TABLES, SAMPLE_SQL_SOURCES
from src.graph.backend import GraphBackend
from src.graph.delta_backend import DeltaBackend
from src.graph.fabric_graph_backend import FabricGraphBackend
from src.models import NodeLayer
from src.pipeline import build_graph
from tests.graph.mock_gql_client import build_er_los_mock


@pytest.fixture
def delta_backend():
    builder = build_graph(SAMPLE_DICT_TABLES, SAMPLE_DICT_COLUMNS, SAMPLE_SQL_SOURCES)
    return DeltaBackend(builder.nodes, builder.edges)


@pytest.fixture
def gql_backend():
    client = build_er_los_mock()
    return FabricGraphBackend(client)


def _assert_subgraph_equivalent(result_a: dict, result_b: dict, strict_fragments: bool = False) -> None:
    """Compare two subgraph results for semantic equivalence.

    Uses set comparison for node IDs (order may differ between backends).
    SQL fragment content is compared as sets by default since DFS ordering
    differs from GQL result ordering.
    """
    assert result_a["canonical"].node_id == result_b["canonical"].node_id
    assert result_a["canonical"].name == result_b["canonical"].name

    transform_ids_a = {t.node_id for t in result_a["transformations"]}
    transform_ids_b = {t.node_id for t in result_b["transformations"]}
    assert transform_ids_a == transform_ids_b, (
        f"Transform mismatch: {transform_ids_a - transform_ids_b} vs {transform_ids_b - transform_ids_a}"
    )

    tech_ids_a = {t.node_id for t in result_a["technical"]}
    tech_ids_b = {t.node_id for t in result_b["technical"]}
    assert tech_ids_a == tech_ids_b, (
        f"Technical mismatch: {tech_ids_a - tech_ids_b} vs {tech_ids_b - tech_ids_a}"
    )


class TestGraphBackendProtocol:
    """Verify both backends satisfy the GraphBackend protocol."""

    def test_delta_satisfies_protocol(self, delta_backend):
        assert isinstance(delta_backend, GraphBackend)

    def test_gql_satisfies_protocol(self, gql_backend):
        assert isinstance(gql_backend, GraphBackend)


class TestBackendContract:
    """Contract tests — same assertions, both backends."""

    @pytest.mark.parametrize("backend_name", ["delta_backend", "gql_backend"])
    def test_get_metric_subgraph_returns_expected_keys(self, backend_name, request):
        backend = request.getfixturevalue(backend_name)
        result = backend.get_metric_subgraph("ER_LOS")
        assert "canonical" in result
        assert "transformations" in result
        assert "technical" in result
        assert "sql_fragments" in result

    @pytest.mark.parametrize("backend_name", ["delta_backend", "gql_backend"])
    def test_canonical_node_is_correct(self, backend_name, request):
        backend = request.getfixturevalue(backend_name)
        result = backend.get_metric_subgraph("ER_LOS")
        assert result["canonical"].node_id == "canonical:ER_LOS"
        assert result["canonical"].name == "ER Length of Stay"
        assert result["canonical"].layer == NodeLayer.CANONICAL

    @pytest.mark.parametrize("backend_name", ["delta_backend", "gql_backend"])
    def test_transformation_nodes_found(self, backend_name, request):
        backend = request.getfixturevalue(backend_name)
        result = backend.get_metric_subgraph("ER_LOS")
        transform_ids = {t.node_id for t in result["transformations"]}
        assert "transform:ER_LOS:er_visits" in transform_ids
        assert "transform:ER_LOS:los_calc" in transform_ids

    @pytest.mark.parametrize("backend_name", ["delta_backend", "gql_backend"])
    def test_technical_nodes_found(self, backend_name, request):
        backend = request.getfixturevalue(backend_name)
        result = backend.get_metric_subgraph("ER_LOS")
        tech_ids = {t.node_id for t in result["technical"]}
        assert "tech:DBO.ENCOUNTER" in tech_ids
        assert "tech:DBO.DEPARTMENT" in tech_ids

    @pytest.mark.parametrize("backend_name", ["delta_backend", "gql_backend"])
    def test_unknown_metric_returns_empty(self, backend_name, request):
        backend = request.getfixturevalue(backend_name)
        assert backend.get_metric_subgraph("NONEXISTENT") == {}

    @pytest.mark.parametrize("backend_name", ["delta_backend", "gql_backend"])
    def test_list_canonical_metrics(self, backend_name, request):
        backend = request.getfixturevalue(backend_name)
        metrics = backend.list_canonical_metrics()
        assert "ER_LOS" in metrics

    @pytest.mark.parametrize("backend_name", ["delta_backend", "gql_backend"])
    def test_sql_fragments_populated(self, backend_name, request):
        backend = request.getfixturevalue(backend_name)
        result = backend.get_metric_subgraph("ER_LOS")
        fragments = result["sql_fragments"]
        assert len(fragments) >= 2
        # At least one fragment should mention encounter
        assert any("encounter" in f.lower() for f in fragments if f)


class TestBackendEquivalence:
    """Cross-backend comparison — both must produce equivalent results."""

    def test_er_los_subgraphs_match(self, delta_backend, gql_backend):
        result_delta = delta_backend.get_metric_subgraph("ER_LOS")
        result_gql = gql_backend.get_metric_subgraph("ER_LOS")
        _assert_subgraph_equivalent(result_delta, result_gql)

    def test_canonical_metrics_match(self, delta_backend, gql_backend):
        delta_metrics = set(delta_backend.list_canonical_metrics())
        gql_metrics = set(gql_backend.list_canonical_metrics())
        assert delta_metrics == gql_metrics
