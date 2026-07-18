"""Test Collibra adapter connection and publish a single test record.

Usage:
    python scripts/test_collibra_connection.py

Prerequisites:
    - pip install requests
    - org_config.yaml with adapters.collibra section configured
"""

from src.config import load_config
from src.adapters.collibra import CollibraAdapter, CollibraConfig
from src.adapters.base import MetadataRecord


def main():
    # Load config
    config = load_config()

    if not config.adapters or not config.adapters.collibra:
        print("ERROR: No Collibra adapter configured in org_config.yaml")
        print("Add an 'adapters.collibra' section. See org_config.example.yaml for reference.")
        return

    collibra_cfg = config.adapters.collibra
    adapter = CollibraAdapter(CollibraConfig(
        base_url=collibra_cfg.base_url,
        username=collibra_cfg.username,
        password=collibra_cfg.password,
        api_key=collibra_cfg.api_key,
        domain_id=collibra_cfg.domain_id,
        community_id=collibra_cfg.community_id,
        asset_type_id=collibra_cfg.asset_type_id,
    ))

    # Step 1: Test connection
    print("Testing Collibra connection...")
    if adapter.test_connection():
        print("  Connected to Collibra!")
    else:
        print("  Connection FAILED. Check your base_url, username, and password.")
        return

    # Step 2: Push a single test record
    print("\nPublishing test record...")
    test_record = MetadataRecord(
        asset_id="test:delete_me",
        asset_type="metric",
        name="TEST - Delete Me",
        description="Auto-generated test term from sql-query-agent. Safe to delete.",
    )

    result = adapter.publish(test_record)
    print(f"  Status: {result.status}")
    print(f"  Message: {result.message}")

    if result.status.value == "success":
        print("\nTest record published successfully!")
        print("Check the Clinical Glossary in Collibra to verify, then delete it manually.")
    else:
        print("\nPublish failed. Check your domain_id, asset_type_id, and permissions.")


if __name__ == "__main__":
    main()
