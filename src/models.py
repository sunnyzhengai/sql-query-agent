"""Graph node and edge data models for the three-layer graph."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class NodeLayer(str, Enum):
    CANONICAL = "canonical"
    TRANSFORMATION = "transformation"
    TECHNICAL = "technical"
    DIMENSION = "dimension"


class CertificationStatus(str, Enum):
    DRAFT = "draft"
    DEV_CERTIFIED = "dev_certified"
    STEWARD_CERTIFIED = "steward_certified"


class GraphNode(BaseModel):
    """A node in the three-layer graph.

    Canonical nodes: business metrics (e.g., ER_LOS) with ownership.
    Transformation nodes: CTE/logic pipeline steps with sql_fragments.
    Technical nodes: physical tables/columns with data dictionary descriptions.
    Dimension nodes: branch from technical tables for dynamic filtering.
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
    TECHNICAL_TO_DIMENSION = "technical_to_dimension"


class GraphEdge(BaseModel):
    """A directed edge in the graph."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: dict[str, Any] = {}
