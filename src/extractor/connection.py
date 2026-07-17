"""Connection abstraction for SQL Server.

Fabric uses JDBC through an On-premises Data Gateway.
Local dev uses pyodbc with Windows auth.
"""

from __future__ import annotations

from typing import Any, Protocol

from src.config import SqlServerConfig


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


def create_connection(config: SqlServerConfig, spark_session: Any = None) -> SqlConnection:
    """Factory: use JDBC in Fabric (when spark is available), pyodbc locally."""
    if spark_session is not None:
        return FabricJdbcConnection(spark_session, config)
    return LocalPyodbcConnection(config)
