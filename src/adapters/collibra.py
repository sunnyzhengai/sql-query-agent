"""Collibra adapter.

Pushes metadata to Collibra's REST API for bulk-loading business terms,
report summaries, and asset descriptions.

Auth: Uses Collibra API credentials (username/password or API key).
API: https://developer.collibra.com/rest/
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
class CollibraConfig:
    """Configuration for Collibra adapter."""
    base_url: str              # e.g., "https://myorg.collibra.com/rest/2.0"
    username: str = ""
    password: str = ""
    api_key: str = ""          # alternative to username/password
    domain_id: str = ""        # target domain for new assets
    community_id: str = ""     # target community
    asset_type_id: str = ""    # Collibra asset type ID for business terms


class CollibraAdapter:
    """Publishes metadata to Collibra Data Governance Center.

    Supports both individual and bulk asset creation/update.

    Requires:
        pip install requests
    """

    def __init__(self, config: CollibraConfig) -> None:
        self.config = config
        self._session = None

    def _get_session(self) -> Any:
        """Get an authenticated requests session."""
        if self._session is not None:
            return self._session

        try:
            import requests
        except ImportError:
            raise ImportError("requests is required for Collibra integration.")

        self._session = requests.Session()

        if self.config.api_key:
            self._session.headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self.config.username and self.config.password:
            self._session.auth = (self.config.username, self.config.password)

        self._session.headers["Content-Type"] = "application/json"
        return self._session

    def test_connection(self) -> bool:
        """Verify connectivity to the Collibra instance."""
        try:
            session = self._get_session()
            resp = session.get(
                f"{self.config.base_url}/users/current",
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Collibra connection test failed: {e}")
            return False

    def publish(self, record: MetadataRecord) -> PublishResult:
        """Publish a single metadata record as a Collibra asset."""
        session = self._get_session()

        # Try to find existing asset first
        existing_id = self._find_asset(record.asset_id)

        try:
            if existing_id:
                # Update existing asset
                payload = self._to_update_payload(record)
                resp = session.patch(
                    f"{self.config.base_url}/assets/{existing_id}",
                    json=payload,
                    timeout=30,
                )
            else:
                # Create new asset
                payload = self._to_create_payload(record)
                resp = session.post(
                    f"{self.config.base_url}/assets",
                    json=payload,
                    timeout=30,
                )

            if resp.status_code in (200, 201):
                return PublishResult(
                    asset_id=record.asset_id,
                    status=PublishStatus.SUCCESS,
                    message=f"{'Updated' if existing_id else 'Created'}. ID: {resp.json().get('id', '')}",
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
        """Publish multiple records using Collibra's bulk import API."""
        session = self._get_session()
        result = BulkPublishResult()

        # Collibra bulk import uses a different endpoint
        # Build the import payload
        import_records = []
        for record in records:
            import_records.append(self._to_import_record(record))

        # Collibra bulk import processes in batches
        batch_size = 100
        for i in range(0, len(import_records), batch_size):
            batch = import_records[i : i + batch_size]
            batch_records = records[i : i + batch_size]

            try:
                resp = session.post(
                    f"{self.config.base_url}/assets/bulk",
                    json=batch,
                    timeout=60,
                )

                if resp.status_code in (200, 201):
                    for r in batch_records:
                        result.add(PublishResult(
                            asset_id=r.asset_id,
                            status=PublishStatus.SUCCESS,
                        ))
                else:
                    for r in batch_records:
                        result.add(PublishResult(
                            asset_id=r.asset_id,
                            status=PublishStatus.FAILED,
                            message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                        ))
            except Exception as e:
                for r in batch_records:
                    result.add(PublishResult(
                        asset_id=r.asset_id,
                        status=PublishStatus.FAILED,
                        message=str(e),
                    ))

        return result

    def _find_asset(self, asset_id: str) -> str | None:
        """Look up an existing Collibra asset by qualified name."""
        session = self._get_session()
        try:
            resp = session.get(
                f"{self.config.base_url}/assets",
                params={"name": asset_id, "limit": 1},
                timeout=10,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    return results[0].get("id")
        except Exception:
            pass
        return None

    def _to_create_payload(self, record: MetadataRecord) -> dict[str, Any]:
        """Convert a MetadataRecord to a Collibra asset creation payload."""
        payload: dict[str, Any] = {
            "name": record.name,
            "displayName": record.name,
        }

        if self.config.domain_id:
            payload["domainId"] = self.config.domain_id
        if self.config.asset_type_id:
            payload["typeId"] = self.config.asset_type_id

        return payload

    def _to_update_payload(self, record: MetadataRecord) -> dict[str, Any]:
        """Convert a MetadataRecord to a Collibra asset update payload."""
        return {
            "name": record.name,
            "displayName": record.name,
        }

    def _to_import_record(self, record: MetadataRecord) -> dict[str, Any]:
        """Convert a MetadataRecord to a Collibra bulk import record."""
        entry: dict[str, Any] = {
            "name": record.name,
            "displayName": record.name,
        }

        if self.config.domain_id:
            entry["domainId"] = self.config.domain_id
        if self.config.asset_type_id:
            entry["typeId"] = self.config.asset_type_id

        return entry
