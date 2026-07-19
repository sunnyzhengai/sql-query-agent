"""Load and validate org_config.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LakehouseConfig(BaseModel):
    dict_tables: str
    dict_columns: str
    sql_sources: str
    graph_nodes: str
    graph_edges: str


class DictionaryConfig(BaseModel):
    table_name_col: str = "TABLE_NAME"
    table_id_col: str = ""                     # if dict_columns uses an ID instead of name, set this
    table_description_col: str = "DESCRIPTION" # description column in dict_tables (may differ from dict_columns)
    column_name_col: str = "COLUMN_NAME"
    description_col: str = "DESCRIPTION"       # description column in dict_columns


class MetricsConfig(BaseModel):
    catalog_path: str


class SqlServerConfig(BaseModel):
    host: str
    port: int = 1433
    database: str
    gateway_connection_name: str = ""  # Fabric gateway linked connection name
    driver: str = "ODBC Driver 17 for SQL Server"  # local dev only
    trusted_connection: bool = True  # local dev only (Windows auth)


class DomainFilterConfig(BaseModel):
    schemas: list[str] = []
    base_tables: list[str] = []
    object_types: list[str] = ["VIEW"]


class ExtractorConfig(BaseModel):
    sql_server: SqlServerConfig
    domain: DomainFilterConfig = DomainFilterConfig()
    tracking_table: str = "extraction_tracking"


class PurviewAdapterConfig(BaseModel):
    account_name: str
    collection_name: str = ""
    custom_type_name: str = "ai_business_term"


class CollibraAdapterConfig(BaseModel):
    base_url: str
    username: str = ""
    password: str = ""
    api_key: str = ""
    domain_id: str = ""
    community_id: str = ""
    asset_type_id: str = ""


class AdaptersConfig(BaseModel):
    purview: Optional[PurviewAdapterConfig] = None
    collibra: Optional[CollibraAdapterConfig] = None


class OrgConfig(BaseModel):
    name: str


class Config(BaseModel):
    org: OrgConfig
    lakehouse: LakehouseConfig
    dictionary: DictionaryConfig = DictionaryConfig()
    metrics: MetricsConfig
    extractor: Optional[ExtractorConfig] = None
    adapters: Optional[AdaptersConfig] = None


def load_config(path: Path | str | None = None) -> Config:
    """Load config from org_config.yaml.

    Args:
        path: Explicit path to config file. If None, looks for org_config.yaml
              in the project root (next to pyproject.toml).
    """
    if path is None:
        path = Path(__file__).resolve().parent.parent / "org_config.yaml"
    else:
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Config not found at {path}. "
            "Copy org_config.example.yaml to org_config.yaml and fill in your values."
        )

    with open(path) as f:
        raw = yaml.safe_load(f)

    config = Config(**raw)
    logger.info("Loaded config for org: %s", config.org.name)
    return config
