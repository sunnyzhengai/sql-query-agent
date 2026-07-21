"""Persistent error log for tracking parse failures across runs.

Every time the pipeline runs, errors are logged with:
- Run timestamp (which build produced this error)
- Metric ID and name
- Error type (extraction vs parse)
- Error message
- Line count (proc complexity)
- Whether it was previously resolved (regression detection)

This creates a historical record that shows:
- Are we fixing errors over time? (error count trending down)
- Did we introduce regressions? (previously-passing procs now failing)
- Which procs consistently fail? (need manual review)
- Which error types are most common? (where to invest fixes)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ErrorEntry:
    """A single error log entry."""
    run_id: str
    run_timestamp: str
    metric_id: str
    metric_name: str
    error_type: str  # "extraction" or "parse"
    error_message: str
    line_count: int = 0
    query_count: int = 0
    clean_sql_preview: str = ""
    status: str = "new"  # "new", "known", "regressed", "resolved"


class ErrorLog:
    """Persistent error log that tracks failures across pipeline runs.

    Usage:
        log = ErrorLog()
        log.load_history(previous_records)  # from Delta table
        log.start_run()
        log.record_error(...)  # for each failure
        log.finish_run()  # detects regressions and resolutions
        log.to_records()  # save to Delta table
    """

    def __init__(self) -> None:
        self.current_run: list[ErrorEntry] = []
        self.history: list[ErrorEntry] = []
        self.run_id: str = ""
        self.run_timestamp: str = ""
        self._previous_failures: set[str] = set()  # metric_ids that failed last run
        self._previous_successes: set[str] = set()  # metric_ids that passed last run

    def load_history(self, records: list[dict[str, Any]]) -> None:
        """Load error history from previous runs (e.g., from Delta table)."""
        for r in records:
            self.history.append(ErrorEntry(
                run_id=r.get("run_id", ""),
                run_timestamp=r.get("run_timestamp", ""),
                metric_id=r.get("metric_id", ""),
                metric_name=r.get("metric_name", ""),
                error_type=r.get("error_type", ""),
                error_message=r.get("error_message", ""),
                line_count=r.get("line_count", 0),
                query_count=r.get("query_count", 0),
                clean_sql_preview=r.get("clean_sql_preview", ""),
                status=r.get("status", ""),
            ))

        # Find the most recent run's failures
        if self.history:
            last_run_id = max(r.run_id for r in self.history)
            self._previous_failures = {
                r.metric_id for r in self.history
                if r.run_id == last_run_id
            }

        logger.info("Loaded %d historical error entries", len(self.history))

    def set_previous_successes(self, metric_ids: list[str]) -> None:
        """Set the list of metric_ids that passed in the previous run."""
        self._previous_successes = set(metric_ids)

    def start_run(self, run_id: str = "") -> None:
        """Start a new pipeline run."""
        self.run_timestamp = datetime.now(timezone.utc).isoformat()
        self.run_id = run_id or self.run_timestamp
        self.current_run = []
        logger.info("Error log: starting run %s", self.run_id)

    def record_error(
        self,
        metric_id: str,
        metric_name: str,
        error_type: str,
        error_message: str,
        line_count: int = 0,
        query_count: int = 0,
        clean_sql_preview: str = "",
    ) -> ErrorEntry:
        """Record a single error in the current run."""
        # Determine status
        if metric_id in self._previous_failures:
            status = "known"  # failed before, still failing
        elif metric_id in self._previous_successes:
            status = "regressed"  # was passing, now failing
        else:
            status = "new"  # first time seeing this metric

        entry = ErrorEntry(
            run_id=self.run_id,
            run_timestamp=self.run_timestamp,
            metric_id=metric_id,
            metric_name=metric_name,
            error_type=error_type,
            error_message=error_message[:500],
            line_count=line_count,
            query_count=query_count,
            clean_sql_preview=clean_sql_preview[:300],
            status=status,
        )
        self.current_run.append(entry)
        return entry

    def finish_run(self, all_metric_ids: list[str]) -> dict[str, Any]:
        """Finish the current run and compute statistics.

        Returns a summary dict with counts and regression detection.
        """
        current_failures = {e.metric_id for e in self.current_run}
        current_successes = set(all_metric_ids) - current_failures

        # Detect resolutions (failed before, passes now)
        resolved = self._previous_failures - current_failures

        # Count by status
        new_errors = sum(1 for e in self.current_run if e.status == "new")
        known_errors = sum(1 for e in self.current_run if e.status == "known")
        regressions = sum(1 for e in self.current_run if e.status == "regressed")

        summary = {
            "run_id": self.run_id,
            "run_timestamp": self.run_timestamp,
            "total_metrics": len(all_metric_ids),
            "total_errors": len(self.current_run),
            "success_count": len(current_successes),
            "success_rate": round(100 * len(current_successes) / len(all_metric_ids), 1) if all_metric_ids else 0,
            "new_errors": new_errors,
            "known_errors": known_errors,
            "regressions": regressions,
            "resolved": len(resolved),
            "resolved_metrics": sorted(resolved),
        }

        if regressions > 0:
            regressed_list = [e.metric_id for e in self.current_run if e.status == "regressed"]
            summary["regressed_metrics"] = regressed_list
            logger.warning("REGRESSIONS DETECTED: %d metrics that previously passed now fail: %s",
                          regressions, regressed_list[:5])

        logger.info(
            "Run complete: %d/%d passed (%.1f%%), %d new errors, %d known, %d regressions, %d resolved",
            summary["success_count"], summary["total_metrics"], summary["success_rate"],
            new_errors, known_errors, regressions, len(resolved),
        )

        return summary

    def to_records(self) -> list[dict[str, Any]]:
        """Export current run errors as list-of-dicts for Delta table persistence."""
        return [
            {
                "run_id": e.run_id,
                "run_timestamp": e.run_timestamp,
                "metric_id": e.metric_id,
                "metric_name": e.metric_name,
                "error_type": e.error_type,
                "error_message": e.error_message,
                "line_count": e.line_count,
                "query_count": e.query_count,
                "clean_sql_preview": e.clean_sql_preview,
                "status": e.status,
            }
            for e in self.current_run
        ]

    def to_all_records(self) -> list[dict[str, Any]]:
        """Export history + current run for full persistence."""
        all_entries = self.history + self.current_run
        return [
            {
                "run_id": e.run_id,
                "run_timestamp": e.run_timestamp,
                "metric_id": e.metric_id,
                "metric_name": e.metric_name,
                "error_type": e.error_type,
                "error_message": e.error_message,
                "line_count": e.line_count,
                "query_count": e.query_count,
                "clean_sql_preview": e.clean_sql_preview,
                "status": e.status,
            }
            for e in all_entries
        ]

    def summary_text(self) -> str:
        """Return a human-readable summary of the current run."""
        if not self.current_run:
            return "No errors recorded in current run."

        # Group by error type
        by_type: dict[str, int] = {}
        for e in self.current_run:
            by_type[e.error_type] = by_type.get(e.error_type, 0) + 1

        # Group by status
        by_status: dict[str, int] = {}
        for e in self.current_run:
            by_status[e.status] = by_status.get(e.status, 0) + 1

        lines = [
            f"Error Log Summary (run: {self.run_id[:20]}...)",
            f"  Total errors: {len(self.current_run)}",
            f"  By type: {by_type}",
            f"  By status: {by_status}",
        ]

        # Top errors by line count
        sorted_errors = sorted(self.current_run, key=lambda e: e.line_count, reverse=True)
        lines.append("  Largest failing procs:")
        for e in sorted_errors[:5]:
            lines.append(f"    {e.metric_id} ({e.line_count} lines) [{e.status}]: {e.error_message[:60]}")

        return "\n".join(lines)
