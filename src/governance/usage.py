"""Usage tracking — grows the knowledge graph from user interactions.

Every question a user asks creates or updates:
1. A user node (who asked)
2. A queried_by edge (which metric they asked about)
3. Usage weight on the canonical node (how often it's asked)

This is the flywheel: more usage → higher weight → better prioritization →
more governance → better answers → more usage.

Usage data answers:
- Which metrics does the organization care about most?
- Who asks about what? (cross-department demand signals)
- Which metrics are trending up/down?
- When should a metric be promoted to a dashboard?
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.graph.builder import GraphBuilder
from src.models import GraphNode, GraphEdge, NodeLayer, EdgeType

logger = logging.getLogger(__name__)


# Usage-specific node layer and edge types (extend the graph model)
USAGE_LAYER = "usage"
QUERIED_BY_EDGE = "queried_by"


@dataclass
class QueryEvent:
    """A single user query event."""
    user_id: str
    user_name: str
    metric_id: str
    question: str
    timestamp: str = ""
    department: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class UsageTracker:
    """Tracks metric usage and grows the knowledge graph.

    Maintains user nodes and queried_by edges in the graph,
    and increments usage_weight on canonical nodes.
    """

    def __init__(self, builder: GraphBuilder) -> None:
        self.builder = builder
        self.events: list[QueryEvent] = []

    def record_query(self, event: QueryEvent) -> None:
        """Record a user query event.

        Creates/updates:
        - User node (if new user)
        - queried_by edge (user → metric)
        - usage_weight on the canonical node
        """
        self.events.append(event)

        # Create or update user node
        user_node_id = f"user:{event.user_id}"
        if user_node_id not in self.builder.nodes:
            self.builder.nodes[user_node_id] = GraphNode(
                node_id=user_node_id,
                layer=NodeLayer.CANONICAL,  # reuse enum, stored as "usage" in properties
                name=event.user_name,
                description=f"User: {event.user_name}",
                properties={
                    "node_type": "user",
                    "user_id": event.user_id,
                    "department": event.department,
                    "first_query": event.timestamp,
                    "last_query": event.timestamp,
                    "query_count": 1,
                },
            )
        else:
            # Update existing user node
            user_node = self.builder.nodes[user_node_id]
            user_node.properties["last_query"] = event.timestamp
            user_node.properties["query_count"] = user_node.properties.get("query_count", 0) + 1

        # Increment usage weight on canonical node
        canonical_id = f"canonical:{event.metric_id}"
        if canonical_id in self.builder.nodes:
            node = self.builder.nodes[canonical_id]
            node.properties["usage_weight"] = node.properties.get("usage_weight", 0) + 1
            node.properties["last_queried"] = event.timestamp
            node.properties["last_queried_by"] = event.user_name

        # Add queried_by edge (or update existing)
        edge_exists = any(
            e.source_id == user_node_id
            and e.target_id == canonical_id
            and e.edge_type.value == "canonical_to_transform"  # reuse closest type
            for e in self.builder.edges
        )

        if not edge_exists and canonical_id in self.builder.nodes:
            self.builder.edges.append(GraphEdge(
                source_id=user_node_id,
                target_id=canonical_id,
                edge_type=EdgeType.CANONICAL_TO_TRANSFORM,  # closest available
                properties={
                    "edge_type_detail": "queried_by",
                    "first_query": event.timestamp,
                    "last_query": event.timestamp,
                    "query_count": 1,
                    "question": event.question,
                },
            ))
        else:
            # Update existing edge
            for e in self.builder.edges:
                if (e.source_id == user_node_id
                        and e.target_id == canonical_id
                        and e.properties.get("edge_type_detail") == "queried_by"):
                    e.properties["last_query"] = event.timestamp
                    e.properties["query_count"] = e.properties.get("query_count", 0) + 1
                    break

        logger.info("Recorded query: %s asked about %s (weight: %s)",
                    event.user_name, event.metric_id,
                    self.builder.nodes.get(canonical_id, GraphNode(
                        node_id="", layer=NodeLayer.CANONICAL, name=""
                    )).properties.get("usage_weight", 0))

    def record_queries_bulk(self, events: list[QueryEvent]) -> None:
        """Record multiple query events."""
        for event in events:
            self.record_query(event)
        logger.info("Recorded %d query events", len(events))

    def load_from_records(self, records: list[dict[str, Any]]) -> None:
        """Load historical query events from list-of-dicts (e.g., Delta table)."""
        for r in records:
            event = QueryEvent(
                user_id=r["user_id"],
                user_name=r["user_name"],
                metric_id=r["metric_id"],
                question=r.get("question", ""),
                timestamp=r.get("timestamp", ""),
                department=r.get("department", ""),
            )
            self.record_query(event)
        logger.info("Loaded %d historical query events", len(records))

    def get_top_metrics(self, n: int = 10) -> list[tuple[str, int]]:
        """Return the top N most-queried metrics by usage weight."""
        metrics = []
        for node in self.builder.nodes.values():
            if node.layer == NodeLayer.CANONICAL and "usage_weight" in node.properties:
                metrics.append((node.name, node.properties["usage_weight"]))
        metrics.sort(key=lambda x: x[1], reverse=True)
        return metrics[:n]

    def get_trending_metrics(self, recent_events: int = 50) -> list[tuple[str, int]]:
        """Return metrics trending in recent events."""
        recent = self.events[-recent_events:] if len(self.events) > recent_events else self.events
        counts: dict[str, int] = {}
        for e in recent:
            counts[e.metric_id] = counts.get(e.metric_id, 0) + 1
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_counts[:10]

    def get_user_activity(self, user_id: str) -> dict[str, Any]:
        """Get activity summary for a specific user."""
        user_events = [e for e in self.events if e.user_id == user_id]
        if not user_events:
            return {"user_id": user_id, "query_count": 0}

        metrics_queried = set(e.metric_id for e in user_events)
        return {
            "user_id": user_id,
            "user_name": user_events[0].user_name,
            "query_count": len(user_events),
            "unique_metrics": len(metrics_queried),
            "first_query": min(e.timestamp for e in user_events),
            "last_query": max(e.timestamp for e in user_events),
            "top_metrics": sorted(
                [(m, sum(1 for e in user_events if e.metric_id == m)) for m in metrics_queried],
                key=lambda x: x[1], reverse=True
            )[:5],
        }

    def get_cross_department_demand(self) -> list[dict[str, Any]]:
        """Find metrics queried by users from multiple departments.

        These are alignment opportunities — shared definitions needed.
        """
        metric_departments: dict[str, set[str]] = {}
        for e in self.events:
            if e.department:
                metric_departments.setdefault(e.metric_id, set()).add(e.department)

        cross_dept = []
        for metric_id, depts in metric_departments.items():
            if len(depts) > 1:
                cross_dept.append({
                    "metric_id": metric_id,
                    "departments": sorted(depts),
                    "department_count": len(depts),
                })

        cross_dept.sort(key=lambda x: x["department_count"], reverse=True)
        return cross_dept

    def get_promotion_candidates(self, threshold: int = 100) -> list[tuple[str, int]]:
        """Find metrics that should be promoted to dashboards.

        Metrics queried more than `threshold` times are candidates
        for formal Power BI dashboards.
        """
        candidates = []
        for node in self.builder.nodes.values():
            if node.layer == NodeLayer.CANONICAL:
                weight = node.properties.get("usage_weight", 0)
                if weight >= threshold:
                    candidates.append((node.name, weight))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def to_event_records(self) -> list[dict[str, str]]:
        """Export all events as list-of-dicts (for writing to Delta table)."""
        return [
            {
                "user_id": e.user_id,
                "user_name": e.user_name,
                "metric_id": e.metric_id,
                "question": e.question,
                "timestamp": e.timestamp,
                "department": e.department,
            }
            for e in self.events
        ]

    def summary(self) -> str:
        """Return a text summary of usage stats."""
        total_events = len(self.events)
        unique_users = len(set(e.user_id for e in self.events))
        unique_metrics = len(set(e.metric_id for e in self.events))
        top = self.get_top_metrics(5)

        lines = [
            f"Usage Summary:",
            f"  Total queries: {total_events}",
            f"  Unique users: {unique_users}",
            f"  Unique metrics queried: {unique_metrics}",
            f"  Top 5 metrics:",
        ]
        for name, weight in top:
            lines.append(f"    {name}: {weight} queries")

        return "\n".join(lines)
