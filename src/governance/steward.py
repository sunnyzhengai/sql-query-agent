"""Steward assignment management.

Manages the assignment of data stewards to canonical metrics.
Steward assignments are stored in a Delta table and also updated
on the canonical graph nodes.

Supports:
- Assign steward to individual metrics
- Bulk assign steward to all metrics matching a pattern (department, category)
- List unassigned metrics
- List all steward assignments
- Update graph nodes with steward info
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.graph.builder import GraphBuilder
from src.models import NodeLayer

logger = logging.getLogger(__name__)


@dataclass
class StewardAssignment:
    """A single steward assignment record."""
    metric_id: str
    metric_name: str
    steward_name: str
    steward_email: str = ""
    department: str = ""
    assigned_date: str = ""
    assigned_by: str = ""


class StewardManager:
    """Manages steward assignments for canonical metrics.

    Assignments are stored as a list of StewardAssignment records.
    In Fabric, these are persisted as a Delta table (steward_assignments).
    """

    def __init__(self) -> None:
        self.assignments: dict[str, StewardAssignment] = {}  # metric_id -> assignment

    def load_from_records(self, records: list[dict[str, Any]]) -> None:
        """Load existing assignments from list-of-dicts (e.g., from Delta table)."""
        for r in records:
            self.assignments[r["metric_id"]] = StewardAssignment(
                metric_id=r["metric_id"],
                metric_name=r.get("metric_name", ""),
                steward_name=r["steward_name"],
                steward_email=r.get("steward_email", ""),
                department=r.get("department", ""),
                assigned_date=r.get("assigned_date", ""),
                assigned_by=r.get("assigned_by", ""),
            )
        logger.info("Loaded %d existing steward assignments", len(self.assignments))

    def assign(
        self,
        metric_id: str,
        metric_name: str,
        steward_name: str,
        steward_email: str = "",
        department: str = "",
        assigned_by: str = "",
    ) -> StewardAssignment:
        """Assign a steward to a single metric."""
        assignment = StewardAssignment(
            metric_id=metric_id,
            metric_name=metric_name,
            steward_name=steward_name,
            steward_email=steward_email,
            department=department,
            assigned_date=datetime.now(timezone.utc).isoformat(),
            assigned_by=assigned_by,
        )
        self.assignments[metric_id] = assignment
        logger.info("Assigned %s as steward for %s", steward_name, metric_name)
        return assignment

    def assign_bulk(
        self,
        metric_ids: list[str],
        metric_names: dict[str, str],
        steward_name: str,
        steward_email: str = "",
        department: str = "",
        assigned_by: str = "",
    ) -> list[StewardAssignment]:
        """Assign a steward to multiple metrics at once."""
        results = []
        for mid in metric_ids:
            name = metric_names.get(mid, mid)
            results.append(self.assign(
                metric_id=mid,
                metric_name=name,
                steward_name=steward_name,
                steward_email=steward_email,
                department=department,
                assigned_by=assigned_by,
            ))
        logger.info("Bulk assigned %s to %d metrics", steward_name, len(results))
        return results

    def assign_by_pattern(
        self,
        pattern: str,
        steward_name: str,
        all_metrics: list[dict[str, str]],
        steward_email: str = "",
        department: str = "",
        assigned_by: str = "",
    ) -> list[StewardAssignment]:
        """Assign a steward to all metrics matching a name pattern.

        Args:
            pattern: Case-insensitive substring to match in metric names.
            steward_name: The steward's name.
            all_metrics: List of dicts with 'metric_id' and 'name' keys.
        """
        pattern_lower = pattern.lower()
        matched = [
            m for m in all_metrics
            if pattern_lower in m["name"].lower()
        ]

        results = []
        for m in matched:
            results.append(self.assign(
                metric_id=m["metric_id"],
                metric_name=m["name"],
                steward_name=steward_name,
                steward_email=steward_email,
                department=department,
                assigned_by=assigned_by,
            ))

        logger.info("Pattern '%s' matched %d metrics, assigned to %s",
                    pattern, len(results), steward_name)
        return results

    def get_unassigned(self, all_metric_ids: list[str]) -> list[str]:
        """Return metric IDs that have no steward assigned."""
        return [mid for mid in all_metric_ids if mid not in self.assignments]

    def get_assignments_by_steward(self, steward_name: str) -> list[StewardAssignment]:
        """Return all assignments for a given steward."""
        return [a for a in self.assignments.values()
                if a.steward_name.lower() == steward_name.lower()]

    def to_records(self) -> list[dict[str, str]]:
        """Export all assignments as list-of-dicts (for writing to Delta table)."""
        return [
            {
                "metric_id": a.metric_id,
                "metric_name": a.metric_name,
                "steward_name": a.steward_name,
                "steward_email": a.steward_email,
                "department": a.department,
                "assigned_date": a.assigned_date,
                "assigned_by": a.assigned_by,
            }
            for a in self.assignments.values()
        ]

    def apply_to_graph(self, builder: GraphBuilder) -> int:
        """Update canonical graph nodes with steward assignments.

        Sets the steward property on each canonical node that has
        an assignment. Returns the number of nodes updated.
        """
        updated = 0
        for node in builder.nodes.values():
            if node.layer != NodeLayer.CANONICAL:
                continue
            metric_id = node.node_id.replace("canonical:", "")
            if metric_id in self.assignments:
                assignment = self.assignments[metric_id]
                node.properties["steward"] = assignment.steward_name
                node.properties["steward_email"] = assignment.steward_email
                node.properties["department"] = assignment.department
                updated += 1

        logger.info("Applied steward assignments to %d graph nodes", updated)
        return updated

    def summary(self, total_metrics: int) -> str:
        """Return a text summary of steward coverage."""
        assigned = len(self.assignments)
        unassigned = total_metrics - assigned
        stewards = set(a.steward_name for a in self.assignments.values())
        departments = set(a.department for a in self.assignments.values() if a.department)

        return (
            f"Steward Coverage:\n"
            f"  Total metrics: {total_metrics}\n"
            f"  Assigned: {assigned} ({100 * assigned // total_metrics if total_metrics else 0}%)\n"
            f"  Unassigned: {unassigned}\n"
            f"  Unique stewards: {len(stewards)}\n"
            f"  Departments: {len(departments)}"
        )
