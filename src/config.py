"""Load and validate org_config.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class LakehouseConfig(BaseModel):
    dict_tables: str
    dict_columns: str
    sql_sources: str
    graph_nodes: str
    graph_edges: str


class DictionaryConfig(BaseModel):
    table_name_col: str = "TABLE_NAME"
    column_name_col: str = "COLUMN_NAME"
    description_col: str = "DESCRIPTION"


class MetricsConfig(BaseModel):
    catalog_path: str


class OrgConfig(BaseModel):
    name: str


class Config(BaseModel):
    org: OrgConfig
    lakehouse: LakehouseConfig
    dictionary: DictionaryConfig = DictionaryConfig()
    metrics: MetricsConfig


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

    return Config(**raw)
