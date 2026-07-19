"""Fabric Notebook: Test Collibra Connection

Test connectivity and publish a single test record to Collibra.
Kept as .py for version control — copy cells into a Fabric Notebook.

Prerequisites:
    - %pip install pydantic pyyaml sqlglot requests
    - org_config.yaml uploaded to Files/sql-query-agent/ with adapters.collibra configured
"""

# %% Cell 1: Setup
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")

from src.config import load_config
from src.adapters.collibra import CollibraAdapter, CollibraConfig
from src.adapters.base import MetadataRecord

# %% Cell 2: Load config and create adapter
config = load_config("/lakehouse/default/Files/sql-query-agent/org_config.yaml")

collibra_cfg = config.adapters.collibra
adapter = CollibraAdapter(CollibraConfig(
    base_url=collibra_cfg.base_url,
    username=collibra_cfg.username,
    password=collibra_cfg.password,
    domain_id=collibra_cfg.domain_id,
    asset_type_id=collibra_cfg.asset_type_id,
))

print(f"Config loaded for: {config.org.name}")
print(f"Collibra URL: {collibra_cfg.base_url}")

# %% Cell 3: Test connection
print("Testing Collibra connection...")
if adapter.test_connection():
    print("Connected to Collibra!")
else:
    print("Connection FAILED — check base_url, username, and password in org_config.yaml")

# %% Cell 4: Publish a test record (only run after Cell 3 succeeds)
test_record = MetadataRecord(
    asset_id="test:delete_me",
    asset_type="metric",
    name="TEST - Delete Me",
    description="Auto-generated test term from sql-query-agent. Safe to delete.",
)

print("Publishing test record...")
result = adapter.publish(test_record)
print(f"Status: {result.status}")
print(f"Message: {result.message}")

if result.status.value == "success":
    print("\nSuccess! Check the Clinical Glossary in Collibra to verify.")
    print("Delete the test record manually when done.")
else:
    print("\nFailed. Check domain_id, asset_type_id, and your permissions.")
