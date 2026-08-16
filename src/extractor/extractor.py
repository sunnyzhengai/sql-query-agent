"""View extractor orchestrator.

Wires together discovery, tracking, and output formatting to produce
sql_sources records ready for build_graph().
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.config import DomainFilterConfig
from src.extractor.connection import SqlConnection
from src.extractor.discovery import DiscoveredObject, discover_objects
from src.extractor.tracker import ExtractionDelta, ExtractionTracker

logger = logging.getLogger(__name__)


@dataclass
class ExtractionSummary:
    total_discovered: int
    new_count: int
    changed_count: int
    unchanged_count: int
    deleted_count: int

    def __str__(self) -> str:
        return (
            f"Discovered: {self.total_discovered} | "
            f"New: {self.new_count} | Changed: {self.changed_count} | "
            f"Unchanged: {self.unchanged_count} | Deleted: {self.deleted_count}"
        )


@dataclass
class ExtractionResult:
    sql_sources: list[dict[str, Any]]
    tracking_records: list[dict[str, Any]]
    summary: ExtractionSummary
    delta: ExtractionDelta


class ViewExtractor:
    """Orchestrates: discover → diff → produce sql_sources."""

    def __init__(self, conn: SqlConnection, domain: DomainFilterConfig) -> None:
        self.conn = conn
        self.domain = domain

    def extract(self, existing_tracking: list[dict[str, Any]] | None = None) -> ExtractionResult:
        """Run the full extraction pipeline.

        Args:
            existing_tracking: Previously tracked records (list of dicts).
                If None, treats everything as new.

        Returns:
            ExtractionResult with sql_sources for new+changed objects,
            updated tracking records, and a summary.
        """
        # Step 1: Discover objects from SQL Server
        discovered = discover_objects(self.conn, self.domain)
        logger.info("Discovered %d objects from SQL Server", len(discovered))

        # Step 2: Compute delta against tracking
        tracker = ExtractionTracker(existing_tracking)
        delta = tracker.compute_delta(discovered)
        logger.info(
            "Delta: %d new, %d changed, %d unchanged, %d deleted",
            len(delta.new), len(delta.changed), len(delta.unchanged), len(delta.deleted),
        )

        # Step 3: Produce sql_sources for new + changed objects
        sql_sources = []
        for obj in delta.new + delta.changed:
            sql_sources.append(_to_sql_source(obj))

        # Step 4: Build updated tracking records
        tracking_records = tracker.build_updated_records(delta, discovered)

        summary = ExtractionSummary(
            total_discovered=len(discovered),
            new_count=len(delta.new),
            changed_count=len(delta.changed),
            unchanged_count=len(delta.unchanged),
            deleted_count=len(delta.deleted),
        )

        return ExtractionResult(
            sql_sources=sql_sources,
            tracking_records=tracking_records,
            summary=summary,
            delta=delta,
        )


# sys.objects type_desc -> input_sql_sources.source_type vocabulary.
# The CONTRACT vocabulary is "procedure"/"view" (allowed-values invariant;
# 01_install derives the same via extract_object_identity). The extractor
# merges directly, so it must speak contract vocabulary itself.
_SOURCE_TYPE = {
    "VIEW": "view",
    "SQL_STORED_PROCEDURE": "procedure",
}


def _to_sql_source(obj: DiscoveredObject) -> dict[str, Any]:
    """Convert a DiscoveredObject to an input_sql_sources record.

    The definition is stored AS EXTRACTED — no stripping. 02_parse's
    ScriptDom understands full CREATE VIEW/PROCEDURE wrappers natively
    (the 790-proc corpus went in unstripped); routing definitions through
    another parser to pre-chew them only added a corruption path.

    Line endings are normalized at this entry point: sys.sql_modules
    returns \r\n, and the input_sql_sources contract promises \n.
    """
    sql = obj.sql_definition.replace("\r\n", "\n").replace("\r", "\n")
    return {
        "metric_id": f"{obj.schema_name}.{obj.object_name}",
        "name": obj.object_name,
        "sql": sql,
        "steward": None,
        "developer": None,
        "source_type": _SOURCE_TYPE.get(obj.object_type, obj.object_type.lower()),
        "source_schema": obj.schema_name,
    }
