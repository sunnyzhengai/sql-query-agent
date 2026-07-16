# Setup

## Local Development

```bash
# 1. Clone and install
git clone https://github.com/sunnyzhengai/sql-query-agent.git
cd sql-query-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Create your org config
cp org_config.example.yaml org_config.yaml
# Edit org_config.yaml with your org-specific values

# 3. Validate config
python scripts/validate_config.py

# 4. Generate sample data (for demo without real data)
python scripts/seed_sample_data.py

# 5. Run tests
pytest
```

## Fabric Setup

See [FABRIC_SETUP.md](FABRIC_SETUP.md) for deploying to Microsoft Fabric.
