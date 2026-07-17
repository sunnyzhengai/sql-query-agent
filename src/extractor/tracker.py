"""Change detection for extracted SQL objects.

Compares discovered objects against previously tracked extractions
using SHA-256 hashes of normalized SQL definitions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.extractor.discovery import DiscoveredObject


def compute_sql_hash(sql_definition: str) -> str:
    """Normalize whitespace/case and compute SHA-256."""
    normalized = " ".join(sql_definition.split()).strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


@dataclass
class ExtractionDelta:
    new: list[DiscoveredObject] = field(default_factory=list)
    changed: list[DiscoveredObject] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)  # object_ids
    deleted: list[str] = field(default_factory=list)  # object_ids


class ExtractionTracker:
    """Compare discovered objects against tracked state."""

    def __init__(self, tracking_records: list[dict[str, Any]] | None = None) -> None:
        self._tracked: dict[str, dict[str, Any]] = {}
        if tracking_records:
            for r in tracking_records:
                self._tracked[r["object_id"]] = r

    def compute_delta(self, discovered: list[DiscoveredObject]) -> ExtractionDelta:
        """Classify each discovered object as new, changed, or unchanged.
        Objects in tracking but not discovered are classified as deleted.
        """
        delta = ExtractionDelta()
        seen_ids: set[str] = set()

        for obj in discovered:
            object_id = f"{obj.schema_name}.{obj.object_name}"
            seen_ids.add(object_id)
            current_hash = compute_sql_hash(obj.sql_definition)

            if object_id not in self._tracked:
                delta.new.append(obj)
            elif self._tracked[object_id].get("sql_hash") != current_hash:
                delta.changed.append(obj)
            else:
                delta.unchanged.append(object_id)

        # Deleted: tracked but not discovered
        for object_id in self._tracked:
            if object_id not in seen_ids and self._tracked[object_id].get("status") != "deleted":
                delta.deleted.append(object_id)

        return delta

    def build_updated_records(
        self, delta: ExtractionDelta, discovered: list[DiscoveredObject]
    ) -> list[dict[str, Any]]:
        """Return the full set of updated tracking records to persist."""
        now = datetime.now(timezone.utc).isoformat()
        records: dict[str, dict[str, Any]] = dict(self._tracked)

        # New objects
        for obj in delta.new:
            object_id = f"{obj.schema_name}.{obj.object_name}"
            records[object_id] = {
                "object_id": object_id,
                "schema_name": obj.schema_name,
                "object_name": obj.object_name,
                "object_type": obj.object_type,
                "sql_hash": compute_sql_hash(obj.sql_definition),
                "extracted_at": now,
                "sql_definition": obj.sql_definition,
                "status": "current",
            }

        # Changed objects
        for obj in delta.changed:
            object_id = f"{obj.schema_name}.{obj.object_name}"
            records[object_id] = {
                "object_id": object_id,
                "schema_name": obj.schema_name,
                "object_name": obj.object_name,
                "object_type": obj.object_type,
                "sql_hash": compute_sql_hash(obj.sql_definition),
                "extracted_at": now,
                "sql_definition": obj.sql_definition,
                "status": "current",
            }

        # Deleted objects
        for object_id in delta.deleted:
            if object_id in records:
                records[object_id]["status"] = "deleted"

        return list(records.values())
