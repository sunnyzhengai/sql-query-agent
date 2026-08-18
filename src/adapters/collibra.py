"""Collibra adapter.

Pushes metadata to Collibra's REST API for bulk-loading business terms,
report summaries, and asset descriptions.

Auth: Uses Collibra API credentials (username/password or API key).
API: https://developer.collibra.com/rest/
"""

from __future__ import annotations

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


class CollibraLookupError(RuntimeError):
    """An asset lookup FAILED (network/HTTP error) — distinct from 'asset not
    found'. Reading a failed lookup as 'absent' made publish() CREATE
    duplicate assets on transient errors (audit 2026-08-15)."""


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
    # Enterprise layouts often display a DIFFERENT attribute as the
    # description box (field find 2026-08-17: written, wrong field
    # shown). Default = Collibra OOTB Description.
    description_attr_type_id: str = "00000000-0000-0000-0000-000000003114"

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
        except Exception as e:  # noqa: BLE001 — failure becomes a visible FAILED result / logged False
            logger.error(f"Collibra connection test failed: {e}")
            return False

    def publish(self, record: MetadataRecord) -> PublishResult:
        """Publish a single metadata record as a Collibra asset.

        Collibra assets carry name/displayName only; the description lives in
        a separate Description ATTRIBUTE. Both writes must land for SUCCESS —
        the old payload-only version reported SUCCESS while every description
        was silently dropped (audit 2026-08-15).
        """
        session = self._get_session()

        try:
            existing_id = self._find_asset(record.asset_id)
        except CollibraLookupError as e:
            return PublishResult(
                asset_id=record.asset_id,
                status=PublishStatus.FAILED,
                message=f"{e} — not creating, to avoid duplicate assets",
            )

        try:
            if existing_id:
                resp = session.patch(
                    f"{self.config.base_url}/assets/{existing_id}",
                    json=self._to_update_payload(record),
                    timeout=30,
                )
            else:
                resp = session.post(
                    f"{self.config.base_url}/assets",
                    json=self._to_create_payload(record),
                    timeout=30,
                )

            if resp.status_code not in (200, 201):
                return PublishResult(
                    asset_id=record.asset_id,
                    status=PublishStatus.FAILED,
                    message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            collibra_id = resp.json().get("id", "") or existing_id or ""
            action = "Updated" if existing_id else "Created"

            message = f"{action}. ID: {collibra_id}"
            if record.description:
                self._set_description_attribute(collibra_id, record.description)
                message += " (description set)"
            if record.owner:
                # Ownership needs Collibra's responsibilities API, which this
                # adapter does not integrate yet. Say so instead of dropping it.
                message += f" (owner '{record.owner}' NOT pushed — responsibilities API not integrated)"

            return PublishResult(
                asset_id=record.asset_id,
                status=PublishStatus.SUCCESS,
                message=message,
            )
        except Exception as e:  # noqa: BLE001 — failure becomes a visible FAILED result / logged False
            return PublishResult(
                asset_id=record.asset_id,
                status=PublishStatus.FAILED,
                message=str(e),
            )

    def publish_bulk(self, records: list[MetadataRecord]) -> BulkPublishResult:
        """Publish records one by one.

        Collibra's /assets/bulk endpoint cannot set attributes, so bulk
        publishing through it silently dropped every description (audit
        2026-08-15). Per-record publish is slower and correct.
        """
        result = BulkPublishResult()
        for record in records:
            result.add(self.publish(record))
        return result

    def update_description(
        self,
        asset_name: str,
        description: str,
        asset_type_id: str | None = None,
    ) -> PublishResult:
        """Update the Description attribute on an existing Collibra asset.

        Finds the asset by name, then creates or updates the Description
        attribute. Use this to enrich existing assets (e.g., Power BI Reports
        ingested by Collibra's integration) without recreating them.

        Args:
            asset_name: Exact name of the asset in Collibra.
            description: The description text to set.
            asset_type_id: Optional type ID filter to narrow the search.
        """
        session = self._get_session()
        type_id = asset_type_id or self.config.asset_type_id

        # 1. Find the asset — try EXACT first, then CONTAINS
        try:
            params: dict[str, Any] = {
                "name": asset_name,
                "nameMatchMode": "EXACT",
                "limit": 1,
            }
            if type_id:
                params["typeId"] = type_id
            resp = session.get(
                f"{self.config.base_url}/assets",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            assets = resp.json().get("results", [])

            # Fallback to CONTAINS if EXACT found nothing
            # (Collibra report names often include bracketed UUIDs)
            if not assets:
                params["nameMatchMode"] = "CONTAINS"
                params["limit"] = 5
                resp = session.get(
                    f"{self.config.base_url}/assets",
                    params=params,
                    timeout=10,
                )
                resp.raise_for_status()
                assets = resp.json().get("results", [])

            if not assets:
                return PublishResult(
                    asset_id=asset_name,
                    status=PublishStatus.FAILED,
                    message=f"Asset not found: {asset_name}",
                )
            matched_asset = assets[0]
            collibra_asset_id = matched_asset["id"]
            matched_name = matched_asset.get("name", "")
            logger.info("Matched '%s' → '%s' (ID: %s)", asset_name, matched_name, collibra_asset_id)
        except Exception as e:  # noqa: BLE001 — failure becomes a visible FAILED result / logged False
            return PublishResult(
                asset_id=asset_name,
                status=PublishStatus.FAILED,
                message=f"Asset lookup failed: {e}",
            )

        # 2. Create or update the Description attribute (shared helper)
        try:
            action = self._set_description_attribute(collibra_asset_id, description)
            return PublishResult(
                asset_id=asset_name,
                status=PublishStatus.SUCCESS,
                message=f"{action} description on '{matched_name}' (ID: {collibra_asset_id})",
            )
        except Exception as e:  # noqa: BLE001 — failure becomes a visible FAILED result / logged False
            return PublishResult(
                asset_id=asset_name,
                status=PublishStatus.FAILED,
                message=f"Attribute write failed: {e}",
            )

    def update_descriptions_bulk(
        self,
        records: list[MetadataRecord],
    ) -> BulkPublishResult:
        """Update Description attributes on multiple existing assets.

        Args:
            records: List of MetadataRecords — uses name and description fields.
        """
        result = BulkPublishResult()
        for record in records:
            r = self.update_description(record.name, record.description)
            result.add(r)
        return result

    def _find_asset(self, asset_id: str) -> str | None:
        """Look up an existing Collibra asset by qualified name.

        Returns None ONLY when the lookup succeeded and found nothing.
        Raises CollibraLookupError on any failure — a failed lookup must
        never be read as "absent" (that path created duplicate assets).
        """
        session = self._get_session()
        try:
            resp = session.get(
                f"{self.config.base_url}/assets",
                params={"name": asset_id, "limit": 1},
                timeout=10,
            )
        except Exception as e:  # noqa: BLE001 — failure becomes a visible FAILED result / logged False
            raise CollibraLookupError(f"asset lookup failed for {asset_id!r}: {e}") from e
        if resp.status_code != 200:
            raise CollibraLookupError(
                f"asset lookup for {asset_id!r} returned HTTP {resp.status_code}: {resp.text[:200]}"
            )
        results = resp.json().get("results", [])
        return results[0].get("id") if results else None

    def _set_description_attribute(self, collibra_asset_id: str, description: str) -> str:
        """Create or update the Description attribute on a Collibra asset.

        Returns "Updated" or "Created". Raises on any failure — callers must
        not report SUCCESS when the description did not land.
        """
        session = self._get_session()
        resp = session.get(
            f"{self.config.base_url}/attributes",
            params={
                "assetId": collibra_asset_id,
                "typeId": self.config.description_attr_type_id,
                "limit": 1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        existing_attrs = resp.json().get("results", [])

        if existing_attrs:
            resp = session.patch(
                f"{self.config.base_url}/attributes/{existing_attrs[0]['id']}",
                json={"value": description},
                timeout=30,
            )
        else:
            resp = session.post(
                f"{self.config.base_url}/attributes",
                json={
                    "assetId": collibra_asset_id,
                    "typeId": self.config.description_attr_type_id,
                    "value": description,
                },
                timeout=30,
            )
        resp.raise_for_status()
        return "Updated" if existing_attrs else "Created"

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
        """Convert a MetadataRecord to a Collibra asset update payload.

        Name fields only by design: the description travels separately via
        _set_description_attribute (Collibra models it as an attribute).
        """
        return {
            "name": record.name,
            "displayName": record.name,
        }
