"""Microsoft Purview adapter.

Pushes metadata to Purview's Data Map via the Atlas-based REST APIs.
Requires the Data Curator role on the target collection.

Auth: Uses Microsoft Entra ID (via azure-identity DefaultAzureCredential).
API: https://learn.microsoft.com/en-us/rest/api/purview/datamapdataplane
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from src.adapters.base import (
    BulkPublishResult,
    CatalogAdapter,
    MetadataRecord,
    PublishResult,
    PublishStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class PurviewConfig:
    """Configuration for Purview adapter."""
    account_name: str                          # e.g., "myorg-purview"
    collection_name: str = ""                  # target collection for new assets
    custom_type_name: str = "ai_business_term" # custom type for AI-generated terms


class PurviewAdapter:
    """Publishes metadata to Microsoft Purview Data Map.

    Uses the Atlas REST API to create/update entities with
    AI-generated descriptions and business metadata.

    Requires:
        pip install azure-identity requests
    """

    def __init__(self, config: PurviewConfig) -> None:
        self.config = config
        self.base_url = f"https://{config.account_name}.purview.azure.com"
        self._credential = None
        self._token = None

    def _get_headers(self) -> dict[str, str]:
        """Get auth headers using DefaultAzureCredential."""
        if self._credential is None:
            try:
                from azure.identity import DefaultAzureCredential
                self._credential = DefaultAzureCredential()
            except ImportError:
                raise ImportError(
                    "azure-identity is required for Purview integration. "
                    "Install with: pip install azure-identity"
                )

        token = self._credential.get_token("https://purview.azure.net/.default")
        return {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
        }

    def test_connection(self) -> bool:
        """Verify connectivity to the Purview account."""
        try:
            import requests
            resp = requests.get(
                f"{self.base_url}/catalog/api/atlas/v2/types/typedefs",
                headers=self._get_headers(),
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Purview connection test failed: {e}")
            return False

    def publish(self, record: MetadataRecord) -> PublishResult:
        """Publish a single metadata record as a Purview entity."""
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Purview integration.")

        entity = self._to_atlas_entity(record)
        payload = {"entity": entity}

        try:
            resp = requests.post(
                f"{self.base_url}/catalog/api/atlas/v2/entity",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                guid = resp.json().get("guidAssignments", {})
                return PublishResult(
                    asset_id=record.asset_id,
                    status=PublishStatus.SUCCESS,
                    message=f"Published. GUIDs: {json.dumps(guid)}",
                )
            else:
                return PublishResult(
                    asset_id=record.asset_id,
                    status=PublishStatus.FAILED,
                    message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as e:
            return PublishResult(
                asset_id=record.asset_id,
                status=PublishStatus.FAILED,
                message=str(e),
            )

    def publish_bulk(self, records: list[MetadataRecord]) -> BulkPublishResult:
        """Publish multiple records using the bulk entity API."""
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Purview integration.")

        result = BulkPublishResult()

        # Purview bulk API accepts up to ~50 entities per call
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            entities = [self._to_atlas_entity(r) for r in batch]
            payload = {"entities": entities}

            try:
                resp = requests.post(
                    f"{self.base_url}/catalog/api/atlas/v2/entity/bulk",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=60,
                )

                if resp.status_code in (200, 201):
                    for r in batch:
                        result.add(PublishResult(
                            asset_id=r.asset_id,
                            status=PublishStatus.SUCCESS,
                        ))
                else:
                    for r in batch:
                        result.add(PublishResult(
                            asset_id=r.asset_id,
                            status=PublishStatus.FAILED,
                            message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                        ))
            except Exception as e:
                for r in batch:
                    result.add(PublishResult(
                        asset_id=r.asset_id,
                        status=PublishStatus.FAILED,
                        message=str(e),
                    ))

        return result

    def _to_atlas_entity(self, record: MetadataRecord) -> dict[str, Any]:
        """Convert a MetadataRecord to a Purview Atlas entity payload."""
        attributes: dict[str, Any] = {
            "qualifiedName": record.asset_id,
            "name": record.name,
            "description": record.description,
        }

        # Merge any extra properties
        if record.owner:
            attributes["owner"] = record.owner
        for key, value in record.properties.items():
            attributes[key] = value

        entity: dict[str, Any] = {
            "typeName": self._map_asset_type(record.asset_type),
            "attributes": attributes,
            "status": "ACTIVE",
        }

        if self.config.collection_name:
            entity["collectionId"] = self.config.collection_name

        return entity

    def _map_asset_type(self, asset_type: str) -> str:
        """Map generic asset types to Purview type names."""
        type_map = {
            "report": "powerbi_report",
            "metric": self.config.custom_type_name,
            "table": "azure_sql_table",
            "column": "azure_sql_column",
        }
        return type_map.get(asset_type, asset_type)
