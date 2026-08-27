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
    # Decision layer (ADR 0044 phase 1b): WHERE/JOIN/CASE decisions as
    # first-class nodes — Sunny's original design, connected to columns
    DECISION = "decision"
    # Governance layer (ADR 0057 "Clusters are nodes", Sunny's demo
    # law 2026-08-25): reified name_cluster and logic_group nodes —
    # the sweep's verdicts as graph truth, membership via edges,
    # dispositions attach here. Deterministic detection only.
    GOVERNANCE = "governance"


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
    # Projection-grain column lineage (ADR 0053, Sunny's order
    # 2026-08-22): the step's SELECT-list/fragment column refs,
    # resolved against the dictionary — minted ⊎ dropped-counted.
    TRANSFORM_TO_COLUMN = "transform_to_column"
    # Consumption layer (ADR 0040) — all deterministic, never guessed.
    # REPORT_TO_TECHNICAL covers DirectLake: the partition names a
    # warehouse TABLE directly, so the report attaches to the technical
    # layer, not to a canonical proc.
    # Decision layer (ADR 0044 1b): step owns its decisions; decisions
    # reach end nodes (columns/tables) or the steps they filter through
    STEP_TO_DECISION = "step_to_decision"
    DECISION_TO_COLUMN = "decision_to_column"
    DECISION_TO_STEP = "decision_to_step"
    REPORT_TO_CANONICAL = "report_to_canonical"
    REPORT_TO_TECHNICAL = "report_to_technical"
    REPORT_TO_MEASURE = "report_to_measure"
    MEASURE_TO_COLUMN = "measure_to_column"
    # Governance clusters (ADR 0057): org node -> logic_group and
    # logic_group -> name_cluster — membership is the ONLY relation;
    # N-member clusters never explode into pairwise edges.
    MEMBER_OF = "member_of"
    # Derived at export time (ADR 0018): metric -> table transitive closure.
    # Never stored in graph_edges; materialized into graph_edge_uses_table.
    USES_TABLE = "uses_table"


# ADR 0059 G2 (RATIFIED 2026-08-26): every edge type carries exactly
# ONE provenance class — parsed (ScriptDom/TMDL evidence, source
# recoverable) / declared (dictionary/config) / derived
# (deterministic build computation, recomputable byte-identically) /
# asserted (human testimony, ADR 0056 — none minted yet; the
# disposition write surface adds variant_of/supersedes/duplicate_of
# under this class when it ships). Totality is CI-checked (the 0052
# pattern): an edge type outside this map cannot ship.
EDGE_PROVENANCE = {
    EdgeType.CANONICAL_TO_TRANSFORM: "parsed",
    EdgeType.TRANSFORM_TO_TRANSFORM: "parsed",
    EdgeType.TRANSFORM_TO_TECHNICAL: "parsed",
    EdgeType.STEP_TO_DECISION: "parsed",
    EdgeType.DECISION_TO_COLUMN: "parsed",
    EdgeType.DECISION_TO_STEP: "parsed",
    EdgeType.REPORT_TO_CANONICAL: "parsed",
    EdgeType.REPORT_TO_TECHNICAL: "parsed",
    EdgeType.REPORT_TO_MEASURE: "parsed",
    EdgeType.MEASURE_TO_COLUMN: "parsed",
    EdgeType.TABLE_TO_COLUMN: "declared",
    EdgeType.TRANSFORM_TO_COLUMN: "derived",
    EdgeType.MEMBER_OF: "derived",
    EdgeType.USES_TABLE: "derived",
}

PROVENANCE_CLASSES = ("parsed", "declared", "derived", "asserted")


class GraphEdge(BaseModel):
    """A directed edge in the graph."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: dict[str, Any] = {}
