"""Base protocol and models for catalog adapters.

All catalog adapters (Collibra, Purview, etc.) implement the CatalogAdapter
protocol so the pipeline can push metadata to any supported catalog without
knowing which one it's talking to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class PublishStatus(str, Enum):
    """Outcome of a single metadata publish operation."""
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class MetadataRecord:
    """A single metadata record to push to a catalog.

    This is the common format produced by the metadata generator.
    Adapters translate this into catalog-specific API payloads.
    """
    asset_id: str                          # unique identifier (e.g., report path, metric_id)
    asset_type: str                        # "report", "metric", "table", "column"
    name: str                              # display name
    description: str = ""                  # AI-generated or human-authored description
    owner: str = ""                        # steward / owner
    properties: dict[str, Any] = field(default_factory=dict)  # catalog-specific extras


@dataclass
class PublishResult:
    """Result of publishing a single record."""
    asset_id: str
    status: PublishStatus
    message: str = ""


@dataclass
class BulkPublishResult:
    """Aggregate result of a bulk publish operation."""
    total: int = 0
    succeeded: int = 0
    skipped: int = 0
    failed: int = 0
    results: list[PublishResult] = field(default_factory=list)

    def add(self, result: PublishResult) -> None:
        self.total += 1
        if result.status == PublishStatus.SUCCESS:
            self.succeeded += 1
        elif result.status == PublishStatus.SKIPPED:
            self.skipped += 1
        else:
            self.failed += 1
        self.results.append(result)

    def __str__(self) -> str:
        return (
            f"Total: {self.total} | "
            f"Succeeded: {self.succeeded} | "
            f"Skipped: {self.skipped} | "
            f"Failed: {self.failed}"
        )


@runtime_checkable
class CatalogAdapter(Protocol):
    """Protocol for catalog integrations.

    Each adapter handles authentication and API translation for a specific
    governance catalog (Collibra, Purview, etc.).
    """

    def publish(self, record: MetadataRecord) -> PublishResult:
        """Publish a single metadata record to the catalog."""
        ...

    def publish_bulk(self, records: list[MetadataRecord]) -> BulkPublishResult:
        """Publish multiple metadata records in batch."""
        ...

    def test_connection(self) -> bool:
        """Verify the adapter can reach the catalog API."""
        ...
