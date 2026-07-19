"""Fabric Power BI report description updater.

Updates the description field on Power BI reports using the
Fabric REST API. Designed to run inside a Fabric Notebook where
authentication is handled automatically via mssparkutils.

API: PATCH https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports/{reportId}
Docs: https://learn.microsoft.com/en-us/rest/api/fabric/report/items/update-report
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PBIReport:
    """A Power BI report with its metadata."""
    report_id: str
    name: str
    description: str = ""
    workspace_id: str = ""


@dataclass
class UpdateResult:
    """Result of updating one report."""
    report_id: str
    report_name: str
    status: str  # "success", "failed", "skipped"
    message: str = ""


@dataclass
class BulkUpdateResult:
    """Result of updating multiple reports."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[UpdateResult] = field(default_factory=list)

    def add(self, result: UpdateResult) -> None:
        self.total += 1
        if result.status == "success":
            self.succeeded += 1
        elif result.status == "failed":
            self.failed += 1
        else:
            self.skipped += 1
        self.results.append(result)

    def __str__(self) -> str:
        return f"Total: {self.total} | Succeeded: {self.succeeded} | Failed: {self.failed} | Skipped: {self.skipped}"


class FabricPBIUpdater:
    """Updates Power BI report descriptions via the Fabric REST API.

    Authentication: uses mssparkutils.credentials.getToken() in Fabric,
    or an explicit access token for testing outside Fabric.
    """

    BASE_URL = "https://api.fabric.microsoft.com/v1"

    def __init__(self, workspace_id: str = "", access_token: str = "") -> None:
        self.workspace_id = workspace_id
        self._access_token = access_token

    def _get_token(self) -> str:
        """Get an access token for the Fabric API."""
        if self._access_token:
            return self._access_token
        try:
            # In Fabric Notebooks, mssparkutils is available globally
            import mssparkutils  # type: ignore
            return mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
        except ImportError:
            raise RuntimeError(
                "mssparkutils not available. Either run in a Fabric Notebook "
                "or pass access_token explicitly."
            )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def list_reports(self, workspace_id: str = "") -> list[PBIReport]:
        """List all Power BI reports in a workspace."""
        import requests

        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            raise ValueError("workspace_id is required")

        resp = requests.get(
            f"{self.BASE_URL}/workspaces/{ws_id}/reports",
            headers=self._get_headers(),
            timeout=30,
        )

        if resp.status_code != 200:
            logger.error("Failed to list reports: %s %s", resp.status_code, resp.text[:200])
            return []

        reports = []
        for item in resp.json().get("value", []):
            reports.append(PBIReport(
                report_id=item["id"],
                name=item.get("displayName", ""),
                description=item.get("description", ""),
                workspace_id=ws_id,
            ))

        logger.info("Found %d reports in workspace %s", len(reports), ws_id)
        return reports

    def update_description(
        self,
        report_id: str,
        description: str,
        workspace_id: str = "",
    ) -> UpdateResult:
        """Update the description of a single Power BI report."""
        import requests

        ws_id = workspace_id or self.workspace_id
        if not ws_id:
            return UpdateResult(report_id=report_id, report_name="", status="failed",
                              message="workspace_id is required")

        try:
            resp = requests.patch(
                f"{self.BASE_URL}/workspaces/{ws_id}/reports/{report_id}",
                headers=self._get_headers(),
                json={"description": description},
                timeout=30,
            )

            if resp.status_code in (200, 204):
                return UpdateResult(
                    report_id=report_id, report_name="",
                    status="success", message="Description updated",
                )
            else:
                return UpdateResult(
                    report_id=report_id, report_name="",
                    status="failed",
                    message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            return UpdateResult(
                report_id=report_id, report_name="",
                status="failed", message=str(e),
            )

    def update_descriptions_bulk(
        self,
        updates: list[dict[str, str]],
        workspace_id: str = "",
    ) -> BulkUpdateResult:
        """Update descriptions for multiple reports.

        Args:
            updates: List of dicts with 'report_id', 'report_name', and 'description'.
            workspace_id: Workspace ID (uses default if not specified).

        Returns:
            BulkUpdateResult with per-report outcomes.
        """
        result = BulkUpdateResult()

        for update in updates:
            report_id = update["report_id"]
            report_name = update.get("report_name", "")
            description = update["description"]

            if not description:
                result.add(UpdateResult(
                    report_id=report_id, report_name=report_name,
                    status="skipped", message="Empty description",
                ))
                continue

            r = self.update_description(report_id, description, workspace_id)
            r.report_name = report_name
            result.add(r)
            logger.info("  %s: %s — %s", report_name, r.status, r.message)

        return result


def match_reports_to_metrics(
    reports: list[PBIReport],
    graph_nodes: dict[str, Any],
) -> list[dict[str, str]]:
    """Match Power BI reports to canonical graph nodes by name similarity.

    Simple matching: checks if the report name contains the metric name
    or vice versa (case-insensitive). Returns a list of updates with
    generated descriptions.

    Args:
        reports: List of PBIReport objects from list_reports().
        graph_nodes: Dict of node_id -> GraphNode from the builder.

    Returns:
        List of dicts with report_id, report_name, description, matched_metric.
    """
    from src.models import NodeLayer

    # Build lookup of canonical nodes
    canonicals = {
        n.name.lower(): n
        for n in graph_nodes.values()
        if n.layer == NodeLayer.CANONICAL
    }

    matches = []
    for report in reports:
        report_name_lower = report.name.lower().replace("_", " ").replace("-", " ")

        # Try to match report name to a canonical metric
        best_match = None
        for metric_name_lower, node in canonicals.items():
            clean_metric = metric_name_lower.lower().replace("_", " ").replace("usp ", "").replace(" pbi", "")
            if clean_metric in report_name_lower or report_name_lower in clean_metric:
                best_match = node
                break

        if best_match and best_match.description:
            matches.append({
                "report_id": report.report_id,
                "report_name": report.name,
                "description": best_match.description,
                "matched_metric": best_match.name,
            })

    logger.info("Matched %d/%d reports to graph metrics", len(matches), len(reports))
    return matches
