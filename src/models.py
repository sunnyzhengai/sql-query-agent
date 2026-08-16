"""Graph node and edge data models for the three-layer graph."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class NodeLayer(str, Enum):
    CANONICAL = "canonical"
    TRANSFORMATION = "transformation"
    TECHNICAL = "technical"
    # Consumption layer (ADR 0040): what sits ABOVE the metrics
    REPORT = "report"
    MEASURE = "measure"


class CertificationStatus(str, Enum):
    DRAFT = "draft"
    DEV_CERTIFIED = "dev_certified"
    STEWARD_CERTIFIED = "steward_certified"


class GraphNode(BaseModel):
    """A node in the three-layer graph.

    Canonical nodes: business metrics (e.g., ER_LOS) with ownership.
    Transformation nodes: CTE/logic pipeline steps with sql_fragments.
    Technical nodes: physical tables/columns with data dictionary descriptions.
    Report nodes: Power BI reports whose semantic models execute metrics.
    Measure nodes: DAX measures/calculated columns, expression stored
    like a transformation's sql_fragment (ADR 0040).
    """

    node_id: str
    layer: NodeLayer
    name: str
    description: str = ""
    properties: dict[str, Any] = {}


class EdgeType(str, Enum):
    CANONICAL_TO_TRANSFORM = "canonical_to_transform"
    TRANSFORM_TO_TRANSFORM = "transform_to_transform"
    TRANSFORM_TO_TECHNICAL = "transform_to_technical"
    TABLE_TO_COLUMN = "table_to_column"
    # Consumption layer (ADR 0040) — all deterministic, never guessed.
    # REPORT_TO_TECHNICAL covers DirectLake: the partition names a
    # warehouse TABLE directly, so the report attaches to the technical
    # layer, not to a canonical proc.
    REPORT_TO_CANONICAL = "report_to_canonical"
    REPORT_TO_TECHNICAL = "report_to_technical"
    REPORT_TO_MEASURE = "report_to_measure"
    MEASURE_TO_COLUMN = "measure_to_column"
    # Derived at export time (ADR 0018): metric -> table transitive closure.
    # Never stored in graph_edges; materialized into graph_edge_uses_table.
    USES_TABLE = "uses_table"


class GraphEdge(BaseModel):
    """A directed edge in the graph."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: dict[str, Any] = {}
