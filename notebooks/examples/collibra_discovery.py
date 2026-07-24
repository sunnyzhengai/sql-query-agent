# Collibra API Discovery
# Run this locally or in Fabric to explore the Collibra data model.
# Fill in your credentials below.

# %% Cell 1: Connect and discover
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
# For local: sys.path.insert(0, ".")

from src.adapters.collibra_lineage import CollibraClient

# ── Fill in your credentials ──
COLLIBRA_URL = "https://YOUR_INSTANCE.collibra.com"  # TODO: fill in
USERNAME = "YOUR_USERNAME"  # TODO: fill in
PASSWORD = "YOUR_PASSWORD"  # TODO: fill in

client = CollibraClient(COLLIBRA_URL, USERNAME, PASSWORD)

# Run discovery — optionally pass a report name you know exists
client.discover()

# %% Cell 2: Search for a specific report (optional)
# Uncomment and change the name to search for a specific PBI report
# client.discover(sample_report_name="Census Dashboard")
