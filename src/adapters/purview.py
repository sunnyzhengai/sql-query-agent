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
    custom_type_name: str = "DataSet"          # Purview entity type for metrics
    tenant_id: str = ""                        # Azure AD tenant ID (for service principal auth)
    client_id: str = ""                        # App registration client ID
    client_secret: str = ""                    # App registration client secret


class PurviewAdapter:
    """Publishes metadata to Microsoft Purview Data Map.

    Uses the Atlas REST API to create/update entities with
    AI-generated descriptions and business metadata.

    Requires:
        pip install azure-identity requests
    """

    def __init__(self, config: PurviewConfig, access_token: str = "") -> None:
        self.config = config
        self.base_url = f"https://{config.account_name}.purview.azure.com"
        self._explicit_token = access_token
        self._cached_token = ""

    def _get_token_via_service_principal(self) -> str:
        """Get token using client credentials (service principal)."""
        import requests as _requests

        token_url = f"https://login.microsoftonline.com/{self.config.tenant_id}/oauth2/v2.0/token"
        resp = _requests.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": "https://purview.azure.net/.default",
        })
        if resp.status_code != 200:
            raise RuntimeError(f"Token request failed: {resp.status_code} {resp.text[:200]}")
        return resp.json()["access_token"]

    def _get_headers(self) -> dict[str, str]:
        """Get auth headers.

        Priority:
        1. Explicit access_token (passed directly)
        2. Service principal credentials (tenant_id + client_id + client_secret)
        3. DefaultAzureCredential fallback (local dev)
        """
        if self._explicit_token:
            return {
                "Authorization": f"Bearer {self._explicit_token}",
                "Content-Type": "application/json",
            }

        if self.config.tenant_id and self.config.client_id and self.config.client_secret:
            if not self._cached_token:
                self._cached_token = self._get_token_via_service_principal()
            return {
                "Authorization": f"Bearer {self._cached_token}",
                "Content-Type": "application/json",
            }

        # Fallback to DefaultAzureCredential (local dev only)
        try:
            from azure.identity import DefaultAzureCredential
            cred = DefaultAzureCredential()
            token = cred.get_token("https://purview.azure.net/.default")
            return {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json",
            }
        except Exception as e:  # noqa: BLE001 — failure becomes PublishResult(FAILED) with the message
            raise RuntimeError(
                f"No auth method available for Purview. Provide access_token, "
                f"service principal credentials, or install azure-identity. Error: {e}"
            )

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
        except Exception as e:  # noqa: BLE001 — failure becomes PublishResult(FAILED) with the message
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
        except Exception as e:  # noqa: BLE001 — failure becomes PublishResult(FAILED) with the message
            return PublishResult(
                asset_id=record.asset_id,
                status=PublishStatus.FAILED,
                message=str(e),
            )

    # ---- Glossary (ADR 0031: business terms at term grain) ----

    def publish_bulk(self, records: list[MetadataRecord]) -> BulkPublishResult:
        """Publish multiple records using individual entity calls.

        Uses the single entity API (not bulk) because the Atlas v2 bulk
        API has issues with collectionId and entity routing in Purview.
        """
        result = BulkPublishResult()
        for record in records:
            result.add(self.publish(record))
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

        # Note: collectionId in the entity payload causes 404 errors
        # with the Atlas v2 API. Purview assigns to the default collection
        # automatically. If collection routing is needed, use the Purview
        # collections API separately.

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
