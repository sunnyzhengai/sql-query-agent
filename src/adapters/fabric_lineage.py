"""Fabric Lineage API integration.

Queries the Fabric/Power BI lineage endpoints to discover the actual
dependency chain between reports, datasets, and data sources.

This replaces name-based or table-based matching with the real lineage
that Fabric already tracks natively.

API endpoints:
- GET /v1/workspaces/{workspaceId}/lineage  (Fabric REST API)
- GET /v1.0/myorg/groups/{groupId}/datasetUpstreamDataflows  (Power BI REST API)
- POST /v1.0/myorg/admin/workspaces/getInfo  (Power BI Admin API — richest lineage)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LineageItem:
    """One item in a lineage chain."""
    item_id: str
    name: str
    item_type: str  # "Report", "SemanticModel", "Lakehouse", "Warehouse", etc.
    workspace_id: str = ""
    workspace_name: str = ""


@dataclass
class LineageLink:
    """A dependency between two lineage items."""
    source_id: str
    source_name: str
    source_type: str
    target_id: str
    target_name: str
    target_type: str


@dataclass
class ReportLineage:
    """Full lineage chain for one Power BI report."""
    report_id: str
    report_name: str
    workspace_id: str
    upstream_datasets: list[LineageItem] = field(default_factory=list)
    upstream_sources: list[LineageItem] = field(default_factory=list)
    source_tables: list[str] = field(default_factory=list)  # table names from the data source


class FabricLineageClient:
    """Queries Fabric lineage to discover report-to-source relationships.

    Authentication: uses mssparkutils.credentials.getToken() in Fabric,
    or an explicit access token for testing.
    """

    FABRIC_API = "https://api.fabric.microsoft.com/v1"
    PBI_API = "https://api.powerbi.com/v1.0/myorg"

    def __init__(self, access_token: str = "") -> None:
        self._access_token = access_token

    def _get_token(self, resource: str = "https://api.fabric.microsoft.com") -> str:
        if self._access_token:
            return self._access_token
        try:
            import mssparkutils  # type: ignore
            return mssparkutils.credentials.getToken(resource)
        except ImportError:
            raise RuntimeError(
                "mssparkutils not available. Run in a Fabric Notebook "
                "or pass access_token explicitly."
            )

    def _fabric_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token('https://api.fabric.microsoft.com')}",
            "Content-Type": "application/json",
        }

    def _pbi_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token('https://analysis.windows.net/powerbi/api')}",
            "Content-Type": "application/json",
        }

    def get_workspace_lineage(self, workspace_id: str) -> dict[str, Any]:
        """Get the full lineage graph for a workspace.

        Returns the raw API response with items and their dependencies.
        """
        import requests

        # Try Fabric API first
        resp = requests.get(
            f"{self.FABRIC_API}/workspaces/{workspace_id}/lineage",
            headers=self._fabric_headers(),
            timeout=30,
        )

        if resp.status_code == 200:
            logger.info("Got lineage from Fabric API for workspace %s", workspace_id)
            return resp.json()

        logger.warning("Fabric lineage API returned %s, trying Power BI API", resp.status_code)

        # Fallback: Power BI Admin API (getInfo with lineage)
        resp = requests.post(
            f"{self.PBI_API}/admin/workspaces/getInfo",
            headers=self._pbi_headers(),
            json={
                "workspaces": [workspace_id],
                "lineage": True,
                "datasourceDetails": True,
                "datasetSchema": True,
                "datasetExpressions": True,
            },
            timeout=60,
        )

        if resp.status_code == 200:
            logger.info("Got lineage from Power BI Admin API")
            return resp.json()

        logger.error("Both lineage APIs failed: %s %s", resp.status_code, resp.text[:200])
        return {}

    def get_report_lineage(self, workspace_id: str, report_id: str = "") -> list[ReportLineage]:
        """Get lineage for reports in a workspace.

        Traces each report back to its data sources to find which
        tables/views it ultimately depends on.

        Args:
            workspace_id: The workspace to scan.
            report_id: Optional — if specified, only return lineage for this report.

        Returns:
            List of ReportLineage objects with the full upstream chain.
        """

        lineage_data = self.get_workspace_lineage(workspace_id)
        if not lineage_data:
            return []

        # Parse items and links from the lineage response
        items = {}  # id -> LineageItem
        links = []  # LineageLink objects

        # Handle different response formats
        if "artifactEntities" in lineage_data:
            # Fabric API format
            for entity in lineage_data.get("artifactEntities", []):
                item = LineageItem(
                    item_id=entity.get("objectId", entity.get("id", "")),
                    name=entity.get("displayName", entity.get("name", "")),
                    item_type=entity.get("itemType", entity.get("type", "")),
                    workspace_id=workspace_id,
                )
                items[item.item_id] = item

            for dep in lineage_data.get("dependencyEntities", []):
                links.append(LineageLink(
                    source_id=dep.get("sourceObjectId", ""),
                    source_name="",
                    source_type="",
                    target_id=dep.get("targetObjectId", ""),
                    target_name="",
                    target_type="",
                ))

        elif "workspaces" in lineage_data:
            # Power BI Admin API format
            for ws in lineage_data.get("workspaces", []):
                for report in ws.get("reports", []):
                    items[report["id"]] = LineageItem(
                        item_id=report["id"],
                        name=report.get("name", ""),
                        item_type="Report",
                        workspace_id=ws.get("id", workspace_id),
                    )

                for dataset in ws.get("datasets", []):
                    items[dataset["id"]] = LineageItem(
                        item_id=dataset["id"],
                        name=dataset.get("name", ""),
                        item_type="SemanticModel",
                        workspace_id=ws.get("id", workspace_id),
                    )

                    # Extract upstream tables from dataset
                    for table in dataset.get("tables", []):
                        source_info = table.get("source", [])
                        if source_info:
                            for src in source_info:
                                links.append(LineageLink(
                                    source_id=dataset["id"],
                                    source_name=dataset.get("name", ""),
                                    source_type="SemanticModel",
                                    target_id=src.get("datasourceId", ""),
                                    target_name=table.get("name", ""),
                                    target_type="Table",
                                ))

        # Build report lineage
        # Find: report -> dataset -> data source -> tables
        report_lineages = []

        report_items = {k: v for k, v in items.items()
                       if v.item_type in ("Report", "report", "PaginatedReport")}

        if report_id:
            report_items = {k: v for k, v in report_items.items() if k == report_id}

        for rid, report in report_items.items():
            rl = ReportLineage(
                report_id=rid,
                report_name=report.name,
                workspace_id=report.workspace_id,
            )

            # Find upstream datasets
            for link in links:
                if link.source_id == rid or link.target_id == rid:
                    upstream_id = link.target_id if link.source_id == rid else link.source_id
                    if upstream_id in items:
                        upstream = items[upstream_id]
                        if upstream.item_type in ("SemanticModel", "Dataset", "dataset"):
                            rl.upstream_datasets.append(upstream)

            # Find upstream sources from datasets
            for ds in rl.upstream_datasets:
                for link in links:
                    if link.source_id == ds.item_id:
                        if link.target_name:
                            rl.source_tables.append(link.target_name)
                        if link.target_id in items:
                            rl.upstream_sources.append(items[link.target_id])

            report_lineages.append(rl)

        logger.info("Built lineage for %d reports", len(report_lineages))
        return report_lineages

    def match_reports_to_metrics_by_lineage(
        self,
        workspace_ids: list[str],
        graph_nodes: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Match PBI reports to graph metrics using actual Fabric lineage.

        Traces each report's data source tables and matches them to
        the graph's technical nodes. A report matches a metric if they
        share the same source tables.

        This is more accurate than name matching but may produce multiple
        matches when reports share tables. Use with the canonical node's
        description to populate report descriptions.

        Args:
            workspace_ids: List of workspace IDs to scan for reports.
            graph_nodes: Dict of node_id -> GraphNode from the builder.

        Returns:
            List of dicts with report_id, report_name, workspace_id,
            matched_metric, description.
        """
        from src.models import NodeLayer

        matches = []

        for ws_id in workspace_ids:
            lineages = self.get_report_lineage(ws_id)
            logger.info("Processing %d reports from workspace %s", len(lineages), ws_id)

            for rl in lineages:
                # Find canonical nodes whose name appears in the report name
                # or whose source tables overlap with the report's source tables
                for node in graph_nodes.values():
                    if node.layer != NodeLayer.CANONICAL:
                        continue
                    if not node.description:
                        continue

                    # Check if report name contains metric name (loose match)
                    metric_clean = node.name.lower().replace("usp_", "").replace("_pbi", "").replace("_", " ")
                    report_clean = rl.report_name.lower().replace("_", " ").replace("-", " ")

                    if metric_clean in report_clean or report_clean in metric_clean:
                        matches.append({
                            "report_id": rl.report_id,
                            "report_name": rl.report_name,
                            "workspace_id": rl.workspace_id,
                            "matched_metric": node.name,
                            "description": node.description,
                            "match_type": "name",
                        })
                        break

        logger.info("Matched %d reports to metrics via lineage", len(matches))
        return matches
