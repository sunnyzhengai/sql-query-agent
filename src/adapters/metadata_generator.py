"""Metadata generator — converts graph nodes into catalog-ready MetadataRecords.

This is the core engine of the "wedge" product. It takes the output of
the graph builder (canonical nodes, transformation chains, technical nodes)
and produces MetadataRecord objects that any CatalogAdapter can consume.

The generator is catalog-agnostic — it doesn't know whether records will
go to Collibra, Purview, or both. That's the adapter's job.
"""

from __future__ import annotations

from src.adapters.base import MetadataRecord
from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.models import NodeLayer


def generate_metric_records(builder: GraphBuilder) -> list[MetadataRecord]:
    """Generate MetadataRecords for all canonical (business metric) nodes.

    Each record includes the metric name, description, ownership,
    and a summary of the transformation pipeline and source tables
    derived from the graph.
    """
    traverser = GraphTraverser(builder.nodes, builder.edges)
    records = []

    for node in builder.nodes.values():
        if node.layer != NodeLayer.CANONICAL:
            continue

        metric_id = node.node_id.replace("canonical:", "")
        subgraph = traverser.get_metric_subgraph(metric_id)

        if not subgraph:
            continue

        # Build a human-readable summary from the graph
        source_tables = [t.name for t in subgraph.get("technical", []) if t.properties.get("column") is None]
        transform_steps = [t.name for t in subgraph.get("transformations", [])]

        description_parts = []
        if node.description:
            description_parts.append(node.description)
        if source_tables:
            description_parts.append(f"Source tables: {', '.join(source_tables)}")
        if transform_steps:
            description_parts.append(f"Calculation steps: {' -> '.join(transform_steps)}")

        records.append(MetadataRecord(
            asset_id=node.node_id,
            asset_type="metric",
            name=node.name,
            description="\n".join(description_parts),
            owner=node.properties.get("steward", ""),
            properties={
                "developer": node.properties.get("developer", ""),
                "source_tables": source_tables,
                "transform_steps": transform_steps,
                "sql_fragments": subgraph.get("sql_fragments", []),
            },
        ))

    return records


def generate_table_records(builder: GraphBuilder) -> list[MetadataRecord]:
    """Generate MetadataRecords for all technical table nodes.

    These can be used to enrich table descriptions in Purview or Collibra
    with data dictionary information.
    """
    records = []

    for node in builder.nodes.values():
        if node.layer != NodeLayer.TECHNICAL:
            continue
        # Only tables (not columns)
        if node.properties.get("column") is not None:
            continue

        records.append(MetadataRecord(
            asset_id=node.node_id,
            asset_type="table",
            name=node.name,
            description=node.description,
        ))

    return records


def generate_all_records(builder: GraphBuilder) -> list[MetadataRecord]:
    """Generate MetadataRecords for all publishable assets in the graph."""
    records = []
    records.extend(generate_metric_records(builder))
    records.extend(generate_table_records(builder))
    return records
