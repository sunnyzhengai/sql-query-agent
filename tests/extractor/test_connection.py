"""Connection factory: profile routing and AAD token handling.

pyodbc is Fabric-runtime-provided (see tests/test_dependency_declarations),
so the token profile is tested against a stub module — what matters here
is the routing, the token packing (UTF-16-LE, length-prefixed, attribute
1256), and that the token provider is called per-connection (the
getToken() session cache breaks >1h batch runs when a connection is
held; a fresh connection must mean a fresh token).
"""

from __future__ import annotations

import struct
import sys
from types import SimpleNamespace

from src.config import SqlServerConfig
from src.extractor.connection import (
    _SQL_COPT_SS_ACCESS_TOKEN,
    FabricJdbcConnection,
    create_connection,
)


class _StubPyodbc:
    def __init__(self):
        self.calls = []

    def drivers(self):
        return ["ODBC Driver 17 for SQL Server"]

    def connect(self, conn_str, attrs_before=None):
        self.calls.append({"conn_str": conn_str, "attrs_before": attrs_before})
        return SimpleNamespace(cursor=lambda: None)


def _config(source_type: str) -> SqlServerConfig:
    return SqlServerConfig(
        host="example.database.windows.net",
        database="AdventureDW",
        source_type=source_type,
    )


def test_onprem_gateway_with_spark_routes_to_jdbc():
    conn = create_connection(_config("onprem_gateway"), spark_session=object())
    assert isinstance(conn, FabricJdbcConnection)


def test_token_profiles_route_to_aad_pyodbc(monkeypatch):
    stub = _StubPyodbc()
    monkeypatch.setitem(sys.modules, "pyodbc", stub)

    for source_type in ("azure_direct", "fabric_native"):
        create_connection(_config(source_type), token_provider=lambda: "tok-abc")

    assert len(stub.calls) == 2
    for call in stub.calls:
        assert "example.database.windows.net" in call["conn_str"]
        assert "Trusted_Connection" not in call["conn_str"]  # token auth, not Windows
        assert _SQL_COPT_SS_ACCESS_TOKEN in call["attrs_before"]


def test_token_is_utf16le_length_prefixed(monkeypatch):
    stub = _StubPyodbc()
    monkeypatch.setitem(sys.modules, "pyodbc", stub)

    create_connection(_config("azure_direct"), token_provider=lambda: "tok")
    packed = stub.calls[0]["attrs_before"][_SQL_COPT_SS_ACCESS_TOKEN]
    expected_bytes = "tok".encode("utf-16-le")
    length = struct.unpack_from("<I", packed)[0]
    assert length == len(expected_bytes)
    assert packed[4:] == expected_bytes


def test_fresh_connection_fetches_fresh_token(monkeypatch):
    stub = _StubPyodbc()
    monkeypatch.setitem(sys.modules, "pyodbc", stub)

    tokens = iter(["token-1", "token-2"])
    provider = lambda: next(tokens)  # noqa: E731
    create_connection(_config("fabric_native"), token_provider=provider)
    create_connection(_config("fabric_native"), token_provider=provider)

    packed_tokens = [
        c["attrs_before"][_SQL_COPT_SS_ACCESS_TOKEN][4:].decode("utf-16-le")
        for c in stub.calls
    ]
    assert packed_tokens == ["token-1", "token-2"]


class TestDriverResolution:
    """Turn-key driver pick (live find 2026-08-16: config said Driver 17,
    Fabric ships Driver 18 — hardcoded defaults fail at first contact)."""

    def test_configured_driver_wins_when_installed(self):
        from src.extractor.connection import _resolve_driver
        assert _resolve_driver("My Custom Driver",
                               ["My Custom Driver", "ODBC Driver 18 for SQL Server"]) \
            == "My Custom Driver"

    def test_falls_back_to_newest_microsoft_driver(self):
        from src.extractor.connection import _resolve_driver
        assert _resolve_driver("ODBC Driver 17 for SQL Server",
                               ["ODBC Driver 18 for SQL Server"]) \
            == "ODBC Driver 18 for SQL Server"

    def test_any_sql_server_driver_as_last_resort(self):
        from src.extractor.connection import _resolve_driver
        assert _resolve_driver("ODBC Driver 17 for SQL Server",
                               ["FreeTDS", "SQL Server Native Client 11.0"]) \
            == "SQL Server Native Client 11.0"

    def test_no_driver_fails_with_installed_list(self):
        import pytest

        from src.extractor.connection import _resolve_driver
        with pytest.raises(RuntimeError, match="installed drivers"):
            _resolve_driver("ODBC Driver 17 for SQL Server", ["FreeTDS"])


def test_token_connection_resolves_driver(monkeypatch):
    import sys
    stub = _StubPyodbc()
    stub.drivers = lambda: ["ODBC Driver 18 for SQL Server"]
    monkeypatch.setitem(sys.modules, "pyodbc", stub)
    create_connection(_config("fabric_native"), token_provider=lambda: "t")
    assert "ODBC Driver 18 for SQL Server" in stub.calls[0]["conn_str"]
