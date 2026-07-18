"""Publisher — orchestrates metadata publishing to one or more catalogs.

Config-driven: reads org_config.yaml to determine which adapters to enable.
A customer who only uses Purview never has to know Collibra support exists,
and vice versa.
"""

from __future__ import annotations

import logging
from typing import Any

from src.adapters.base import BulkPublishResult, CatalogAdapter, MetadataRecord

logger = logging.getLogger(__name__)


class Publisher:
    """Publishes MetadataRecords to all configured catalog adapters.

    Usage:
        publisher = Publisher()
        publisher.add_adapter("purview", purview_adapter)
        publisher.add_adapter("collibra", collibra_adapter)
        results = publisher.publish_all(records)
    """

    def __init__(self) -> None:
        self._adapters: dict[str, CatalogAdapter] = {}

    def add_adapter(self, name: str, adapter: CatalogAdapter) -> None:
        """Register a catalog adapter."""
        self._adapters[name] = adapter

    def test_connections(self) -> dict[str, bool]:
        """Test connectivity for all registered adapters."""
        results = {}
        for name, adapter in self._adapters.items():
            try:
                results[name] = adapter.test_connection()
            except Exception as e:
                logger.error(f"Connection test failed for {name}: {e}")
                results[name] = False
        return results

    def publish_all(self, records: list[MetadataRecord]) -> dict[str, BulkPublishResult]:
        """Publish records to all registered adapters.

        Returns a dict of adapter_name -> BulkPublishResult.
        """
        results = {}
        for name, adapter in self._adapters.items():
            logger.info(f"Publishing {len(records)} records to {name}...")
            try:
                results[name] = adapter.publish_bulk(records)
                logger.info(f"{name}: {results[name]}")
            except Exception as e:
                logger.error(f"Failed to publish to {name}: {e}")
                result = BulkPublishResult()
                results[name] = result
        return results

    @property
    def adapter_names(self) -> list[str]:
        """List registered adapter names."""
        return list(self._adapters.keys())


def create_publisher_from_config(config: dict[str, Any]) -> Publisher:
    """Factory: create a Publisher with adapters based on config.

    Expected config structure (from org_config.yaml):
        adapters:
          purview:
            account_name: "myorg-purview"
            collection_name: "default"
          collibra:
            base_url: "https://myorg.collibra.com/rest/2.0"
            api_key: "..."
            domain_id: "..."
    """
    publisher = Publisher()

    adapter_configs = config.get("adapters", {})

    if "purview" in adapter_configs:
        from src.adapters.purview import PurviewAdapter, PurviewConfig
        purview_cfg = PurviewConfig(**adapter_configs["purview"])
        publisher.add_adapter("purview", PurviewAdapter(purview_cfg))

    if "collibra" in adapter_configs:
        from src.adapters.collibra import CollibraAdapter, CollibraConfig
        collibra_cfg = CollibraConfig(**adapter_configs["collibra"])
        publisher.add_adapter("collibra", CollibraAdapter(collibra_cfg))

    return publisher
