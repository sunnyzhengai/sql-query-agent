"""Load and validate org_config.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LakehouseConfig(BaseModel):
    dict_tables: str = "input_dict_tables"
    dict_columns: str = "input_dict_columns"
    sql_sources: str = "input_sql_sources"
    graph_nodes: str = "graph_nodes"
    graph_edges: str = "graph_edges"


class DictionaryConfig(BaseModel):
    table_name_col: str = "TABLE_NAME"
    table_id_col: str = ""                     # if dict_columns uses an ID instead of name, set this
    table_description_col: str = "DESCRIPTION" # description column in dict_tables (may differ from dict_columns)
    column_name_col: str = "COLUMN_NAME"
    description_col: str = "DESCRIPTION"       # description column in dict_columns
    # Dictionary matching is schema-agnostic (ADR 0016). When 500_validate
    # detects the same bare table name in multiple schemas, deployment blocks
    # unless the admin acknowledges the ambiguity by setting this to true.
    accept_schema_ambiguity: bool = False


class SqlServerConfig(BaseModel):
    host: str
    port: int = 1433
    database: str
    # Which connection profile the extractor uses (discovery is identical
    # across all three — sys.objects/sys.sql_modules exist everywhere):
    #   onprem_gateway — JDBC through an On-premises Data Gateway
    #   azure_direct   — Azure SQL / Managed Instance, AAD token, no gateway
    #   fabric_native  — Fabric Warehouse / SQL DB / mirrored DB T-SQL
    #                    endpoint, AAD token straight from the notebook
    source_type: Literal["onprem_gateway", "azure_direct", "fabric_native"] = "onprem_gateway"
    gateway_connection_name: str = ""  # Fabric gateway linked connection name
    driver: str = "ODBC Driver 17 for SQL Server"  # local dev only
    trusted_connection: bool = True  # local dev only (Windows auth)


class DomainFilterConfig(BaseModel):
    schemas: list[str] = []
    base_tables: list[str] = []
    # Turn-key default: customers must not hand-export files, and the
    # corpus is procs + views — both come through the front door.
    object_types: list[str] = ["VIEW", "SQL_STORED_PROCEDURE"]


class ExtractorConfig(BaseModel):
    sql_server: SqlServerConfig
    domain: DomainFilterConfig = DomainFilterConfig()
    tracking_table: str = "ops_extraction_tracking"


class DevOpsGitConfig(BaseModel):
    org: str
    project: str
    repo: str
    # PAT is fetched at run time from Key Vault (notebookutils in Fabric),
    # NEVER stored in config — these two fields say where to fetch it.
    key_vault_url: str = ""
    pat_secret_name: str = ""


class SemanticModelsConfig(BaseModel):
    # workspace: Fabric REST getDefinition — any workspace, no git needed
    #            (the turn-key default).
    # folder: git-synced workspace checkout / uploaded Files.
    # devops_git: Azure DevOps repos (DevOpsTmdlClient).
    source_type: Literal["workspace", "folder", "devops_git"] = "workspace"
    # Reports commonly live across several PBI workspaces (field find
    # 2026-08-18). Naming is refuse-over-guess (amended same day): a
    # metric consumed by differently-titled reports gets NO derived name
    # (all consumers listed for steward review); same-title workspace
    # copies name it. List order only fixes the listing order.
    workspace_ids: "list[str]" = []
    workspace_id: str = ""  # single-value sugar; empty = current workspace
    folder_path: str = ""
    devops: Optional[DevOpsGitConfig] = None

    def resolved_workspace_ids(self) -> "list[str]":
        """workspace_ids wins; else the single id; else [""] meaning
        'the workspace the notebook runs in'."""
        if self.workspace_ids:
            return list(self.workspace_ids)
        return [self.workspace_id or ""]


class PurviewAdapterConfig(BaseModel):
    account_name: str
    collection_name: str = ""
    custom_type_name: str = "DataSet"
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""


class CollibraAdapterConfig(BaseModel):
    base_url: str
    username: str = ""
    password: str = ""
    api_key: str = ""
    domain_id: str = ""
    community_id: str = ""
    asset_type_id: str = ""
    # If descriptions land but display in the wrong field, run
    # collibra_discovery on one asset and set this to the attribute type
    # your layout shows (enterprise layouts customize the description box).
    description_attr_type_id: str = "00000000-0000-0000-0000-000000003114"


class AdaptersConfig(BaseModel):
    purview: Optional[PurviewAdapterConfig] = None
    collibra: Optional[CollibraAdapterConfig] = None


class FabricGraphConfig(BaseModel):
    workspace_id: str
    graph_model_id: str
    data_agent_id: str = ""  # Fabric Data Agent ID for description generation
    enabled: bool = False  # opt-in during parallel testing


class FreshnessConfig(BaseModel):
    # Trust staleness threshold (Question Map gap 2): 500_validate WARNS
    # when a metric's source extraction is older than this — health
    # signal only, never a deployment gate.
    stale_after_days: int = 30


class OrgConfig(BaseModel):
    name: str


class Config(BaseModel):
    org: OrgConfig
    lakehouse: LakehouseConfig
    dictionary: DictionaryConfig = DictionaryConfig()
    extractor: Optional[ExtractorConfig] = None
    semantic_models: Optional[SemanticModelsConfig] = None
    adapters: Optional[AdaptersConfig] = None
    fabric_graph: Optional[FabricGraphConfig] = None
    freshness: FreshnessConfig = FreshnessConfig()


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
