"""Collibra lineage discovery and retrieval.

Connects to Collibra REST API to:
1. Discover the data model (asset types, relation types, attribute types)
2. Retrieve lineage between stored procs/views and Power BI reports

Usage:
    from src.adapters.collibra_lineage import CollibraClient
    client = CollibraClient("https://your-instance.collibra.com", "user", "pass")
    client.discover()  # prints asset types, relations, attributes
"""

from __future__ import annotations

import requests
from typing import Any


class CollibraClient:
    """Client for Collibra REST API v2."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/rest/2.0"
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """GET request to Collibra API."""
        url = f"{self.api_url}/{endpoint}"
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint: str, json_body: dict | None = None) -> dict:
        """POST request to Collibra API."""
        url = f"{self.api_url}/{endpoint}"
        resp = self.session.post(url, json=json_body)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, endpoint: str, json_body: dict | None = None) -> dict:
        """PATCH request to Collibra API."""
        url = f"{self.api_url}/{endpoint}"
        resp = self.session.patch(url, json=json_body)
        resp.raise_for_status()
        return resp.json()

    # ── Discovery ──────────────────────────────────────────────

    def test_connection(self) -> bool:
        """Test API connectivity."""
        try:
            self._get("users/current")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def find_asset_types(self, name_filter: str = "") -> list[dict]:
        """List asset types, optionally filtered by name."""
        params = {"offset": 0, "limit": 100}
        if name_filter:
            params["name"] = name_filter
        result = self._get("assetTypes", params=params)
        return result.get("results", [])

    def find_asset_by_name(self, name: str, asset_type_id: str | None = None) -> list[dict]:
        """Find assets by name."""
        params = {"name": name, "nameMatchMode": "EXACT", "offset": 0, "limit": 10}
        if asset_type_id:
            params["typeId"] = asset_type_id
        result = self._get("assets", params=params)
        return result.get("results", [])

    def find_assets_by_name_contains(self, name: str, asset_type_id: str | None = None, limit: int = 10) -> list[dict]:
        """Find assets where name contains the search string."""
        params = {"name": name, "nameMatchMode": "CONTAINS", "offset": 0, "limit": limit}
        if asset_type_id:
            params["typeId"] = asset_type_id
        result = self._get("assets", params=params)
        return result.get("results", [])

    def get_asset_relations(self, asset_id: str) -> list[dict]:
        """Get all relations for an asset (both directions)."""
        # Relations where this asset is the source
        outgoing = self._get("relations", params={
            "sourceId": asset_id, "offset": 0, "limit": 100
        }).get("results", [])

        # Relations where this asset is the target
        incoming = self._get("relations", params={
            "targetId": asset_id, "offset": 0, "limit": 100
        }).get("results", [])

        return outgoing + incoming

    def get_asset_attributes(self, asset_id: str) -> list[dict]:
        """Get all attributes for an asset."""
        result = self._get("attributes", params={
            "assetId": asset_id, "offset": 0, "limit": 100
        })
        return result.get("results", [])

    def find_attribute_types(self, name_filter: str = "") -> list[dict]:
        """List attribute types, optionally filtered by name."""
        params = {"offset": 0, "limit": 100}
        if name_filter:
            params["name"] = name_filter
        result = self._get("attributeTypes", params=params)
        return result.get("results", [])

    def find_relation_types(self, name_filter: str = "") -> list[dict]:
        """List relation types."""
        params = {"offset": 0, "limit": 100}
        if name_filter:
            params["name"] = name_filter
        result = self._get("relationTypes", params=params)
        return result.get("results", [])

    def discover(self, sample_report_name: str = "") -> None:
        """Run full discovery: find asset types, sample a PBI report, list its relations and attributes.

        Args:
            sample_report_name: Name (or partial name) of a PBI report to examine.
                               If empty, searches for any 'Power BI Report' asset.
        """
        print("=" * 60)
        print("Collibra Discovery")
        print("=" * 60)

        # 1. Test connection
        print("\n1. Testing connection...")
        if not self.test_connection():
            return
        print("   Connected!")

        # 2. Find Power BI Report asset type
        print("\n2. Looking for Power BI asset types...")
        pbi_types = self.find_asset_types("Power BI")
        if pbi_types:
            for at in pbi_types:
                print(f"   Asset Type: {at['name']} (ID: {at['id']})")
        else:
            print("   No 'Power BI' asset types found. Searching all types...")
            all_types = self.find_asset_types()
            for at in all_types:
                if "report" in at["name"].lower() or "bi" in at["name"].lower():
                    print(f"   Asset Type: {at['name']} (ID: {at['id']})")

        # 3. Find stored proc/view asset types
        print("\n3. Looking for stored proc/view asset types...")
        for search in ["Stored Procedure", "View", "Database View", "SQL"]:
            types = self.find_asset_types(search)
            for at in types:
                print(f"   Asset Type: {at['name']} (ID: {at['id']})")

        # 4. Find a sample PBI report
        print("\n4. Searching for a sample Power BI Report asset...")
        sample = None
        if sample_report_name:
            assets = self.find_assets_by_name_contains(sample_report_name)
            if assets:
                sample = assets[0]
        if not sample and pbi_types:
            # Search for any asset of the PBI Report type
            for pbi_type in pbi_types:
                if "report" in pbi_type["name"].lower():
                    params = {"typeId": pbi_type["id"], "offset": 0, "limit": 1}
                    result = self._get("assets", params=params)
                    assets = result.get("results", [])
                    if assets:
                        sample = assets[0]
                        break

        if not sample:
            print("   No sample PBI report found. Run with a specific report name:")
            print("   client.discover(sample_report_name='My Report Name')")
            return

        print(f"   Found: {sample['name']} (ID: {sample['id']})")
        print(f"   Type: {sample['type']['name']} (ID: {sample['type']['id']})")
        if sample.get("domain"):
            print(f"   Domain: {sample['domain'].get('name', 'N/A')}")

        # 5. List relations on this asset
        print(f"\n5. Relations for '{sample['name']}':")
        relations = self.get_asset_relations(sample["id"])
        if relations:
            for rel in relations:
                rel_type = rel.get("type", {})
                source = rel.get("source", {})
                target = rel.get("target", {})
                direction = "→" if source.get("id") == sample["id"] else "←"
                other = target if direction == "→" else source
                print(f"   {direction} {rel_type.get('role', 'unknown')} "
                      f"[{rel_type.get('sourceType', {}).get('name', '?')} → {rel_type.get('targetType', {}).get('name', '?')}]")
                print(f"     Other asset: {other.get('name', '?')} (Type: {other.get('type', {}).get('name', '?')})")
        else:
            print("   No relations found")

        # 6. List attributes on this asset
        print(f"\n6. Attributes for '{sample['name']}':")
        attributes = self.get_asset_attributes(sample["id"])
        if attributes:
            for attr in attributes:
                attr_type = attr.get("type", {})
                value = attr.get("value", "")
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {attr_type.get('name', '?')} (ID: {attr_type.get('id', '?')}): {value}")
        else:
            print("   No attributes found")

        # 7. Find Description attribute type
        print("\n7. Looking for Description attribute type...")
        desc_types = self.find_attribute_types("Description")
        for at in desc_types:
            print(f"   Attribute Type: {at['name']} (ID: {at['id']})")

        print("\n" + "=" * 60)
        print("Discovery complete. Use the IDs above to configure lineage retrieval.")
        print("=" * 60)
