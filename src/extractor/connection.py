"""Connection abstraction for SQL Server-family sources.

Three connection profiles, selected by config source_type — discovery is
identical across all of them (sys.objects / sys.sql_modules everywhere):

  onprem_gateway — JDBC through an On-premises Data Gateway (or pyodbc
                   with Windows auth for local dev, when no Spark session).
  azure_direct   — Azure SQL / Managed Instance over pyodbc with an AAD
                   access token; no gateway.
  fabric_native  — Fabric Warehouse / Fabric SQL DB / mirrored DB T-SQL
                   endpoint, same AAD-token pyodbc path, reachable
                   straight from the notebook.
"""

from __future__ import annotations

import struct
from typing import Any, Callable, Protocol

from src.config import SqlServerConfig

# pyodbc connection attribute for passing an AAD access token (MS docs:
# SQL_COPT_SS_ACCESS_TOKEN)
_SQL_COPT_SS_ACCESS_TOKEN = 1256

# Token audience accepted by Azure SQL, Managed Instance, AND Fabric
# T-SQL endpoints alike.
TOKEN_AUDIENCE = "https://database.windows.net/"


class SqlConnection(Protocol):
    """Abstract interface for running queries against SQL Server."""

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        ...


class FabricJdbcConnection:
    """Connects via spark.read.format('jdbc') through On-premises Data Gateway."""

    def __init__(self, spark_session: Any, config: SqlServerConfig) -> None:
        self.spark = spark_session
        self.config = config
        self.jdbc_url = (
            f"jdbc:sqlserver://{config.host}:{config.port};"
            f"databaseName={config.database};"
            f"integratedSecurity=true;"
            f"encrypt=true;trustServerCertificate=true"
        )

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        reader = (
            self.spark.read.format("jdbc")
            .option("url", self.jdbc_url)
            .option("query", sql)
        )
        if self.config.gateway_connection_name:
            reader = reader.option("gateway", self.config.gateway_connection_name)
        df = reader.load()
        return [row.asDict() for row in df.collect()]


class LocalPyodbcConnection:
    """Connects via pyodbc for local development with Windows auth."""

    def __init__(self, config: SqlServerConfig) -> None:
        import pyodbc

        conn_str = (
            f"DRIVER={{{config.driver}}};"
            f"SERVER={config.host},{config.port};"
            f"DATABASE={config.database};"
            f"Trusted_Connection={'yes' if config.trusted_connection else 'no'}"
        )
        self.conn = pyodbc.connect(conn_str)

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _resolve_driver(configured: str, installed: "list[str]") -> str:
    """Pick a usable SQL Server ODBC driver — turn-key over hardcoded.

    The configured name wins when it's actually installed; otherwise
    prefer the newest Microsoft driver present (live find 2026-08-16:
    the config default said Driver 17, Fabric Spark ships Driver 18 —
    'file not found' at first customer-shaped contact). No driver at
    all fails with the installed list, not an ODBC riddle.
    """
    if configured in installed:
        return configured
    for preferred in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if preferred in installed:
            return preferred
    for name in installed:
        if "SQL Server" in name:
            return name
    raise RuntimeError(
        f"No SQL Server ODBC driver found. Configured: {configured!r}; "
        f"installed drivers: {installed or '(none)'}"
    )


class AadTokenPyodbcConnection:
    """pyodbc with an Azure AD access token — Azure SQL / MI / Fabric T-SQL.

    A FRESH connection fetches a FRESH token: notebookutils/mssparkutils
    getToken() caches within a session and will not refresh, which breaks
    batch runs longer than the token lifetime (~1h). Callers that loop for
    hours should create a new connection per batch, not hold this one.
    """

    def __init__(self, config: SqlServerConfig, token_provider: "Callable[[], str]") -> None:
        import pyodbc

        token = token_provider()
        # SQL Server expects the token bytes UTF-16-LE, length-prefixed
        token_bytes = token.encode("utf-16-le")
        packed = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        driver = _resolve_driver(config.driver, pyodbc.drivers())
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={config.host},{config.port};"
            f"DATABASE={config.database};"
            f"Encrypt=yes;TrustServerCertificate=no"
        )
        self.conn = pyodbc.connect(
            conn_str, attrs_before={_SQL_COPT_SS_ACCESS_TOKEN: packed}
        )

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _notebook_token_provider() -> str:
    """Default AAD token source inside a Fabric notebook."""
    import notebookutils  # Fabric runtime provides this

    return notebookutils.credentials.getToken(TOKEN_AUDIENCE)


def create_connection(
    config: SqlServerConfig,
    spark_session: Any = None,
    token_provider: "Callable[[], str] | None" = None,
) -> SqlConnection:
    """Factory keyed on config.source_type.

    onprem_gateway: JDBC when a Spark session is available (Fabric),
    pyodbc with Windows auth otherwise (local dev). azure_direct and
    fabric_native: AAD-token pyodbc; token_provider defaults to
    notebookutils inside Fabric, injectable for tests and non-notebook
    runtimes.
    """
    if config.source_type in ("azure_direct", "fabric_native"):
        provider = token_provider if token_provider is not None else _notebook_token_provider
        return AadTokenPyodbcConnection(config, provider)
    if spark_session is not None:
        return FabricJdbcConnection(spark_session, config)
    return LocalPyodbcConnection(config)
