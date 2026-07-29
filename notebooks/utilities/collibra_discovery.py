# Collibra API Discovery
# Run this locally or in Fabric to explore the Collibra data model.
# Uses credentials from org_config.yaml.

# %% Cell 1: Connect and discover
import sys
sys.path.insert(0, "/lakehouse/default/Files/sql-query-agent")
# For local: sys.path.insert(0, ".")

from src.config import load_config
from src.adapters.collibra_lineage import CollibraClient

config = load_config()
collibra_cfg = config.adapters.collibra

base = collibra_cfg.base_url.replace("/rest/2.0", "")
client = CollibraClient(base, collibra_cfg.username, collibra_cfg.password)

# Run discovery — optionally pass a report name you know exists
client.discover()

# %% Cell 2: Search for a specific report (optional)
# Uncomment and change the name to search for a specific PBI report
# client.discover(sample_report_name="Census Dashboard")
