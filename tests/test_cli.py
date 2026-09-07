from __future__ import annotations

from typing import Any

import pytest
from mcp.server.transport_security import TransportSecuritySettings

from mcp_graylog import cli
from mcp_graylog.cli import Transport


class FakeMcpSettings:
    def __init__(self) -> None:
        self.log_level: str | None = None


class FakeMcpServer:
    def __init__(self) -> None:
        self.settings = FakeMcpSettings()
        self.run_calls: list[dict[str, Any]] = []

    def run(self, transport: Transport = "stdio", **kwargs: object) -> None:
        call: dict[str, Any] = {"transport": transport, **kwargs}
        self.run_calls.append(call)


class FakeGraylogClient:
    instances: list[FakeGraylogClient] = []

    def __init__(self, settings: object) -> None:
        self.settings = settings
        self.closed = False
        FakeGraylogClient.instances.append(self)

    def __enter__(self) -> FakeGraylogClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self.closed = True


def test_parse_args_defaults_to_stdio_transport() -> None:
    args = cli.parse_args([])

    assert args.transport == "stdio"


def test_parse_args_accepts_explicit_streamable_http_options() -> None:
    args = cli.parse_args(
        [
            "--transport",
            "streamable-http",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--path",
            "/graylog",
            "--log-level",
            "DEBUG",
            "--allowed-host",
            "10.100.125.139:*",
            "--allowed-origin",
            "https://app.example.test",
        ]
    )

    assert args.transport == "streamable-http"
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.path == "/graylog"
    assert args.log_level == "DEBUG"
    assert "10.100.125.139:*" in args.allowed_hosts
    assert "https://app.example.test" in args.allowed_origins


def test_parse_args_rejects_invalid_log_level() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args(["--log-level", "TRACE"])


def test_parse_args_can_disable_host_validation_from_environment(
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("MCP_SERVER_DNS_REBINDING_PROTECTION", "false")

    args = cli.parse_args([])

    assert args.dns_rebinding_protection is False


def test_parse_args_does_not_require_graylog_env(monkeypatch: Any) -> None:
    for name in (
        "GRAYLOG_ENDPOINT",
        "GRAYLOG_TOKEN",
        "GRAYLOG_USERNAME",
        "GRAYLOG_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    args = cli.parse_args([])

    assert args.transport == "stdio"
    assert args.log_level == "INFO"


def test_main_defaults_to_stdio_without_http_settings(monkeypatch: Any) -> None:
    fake_settings = object()
    fake_mcp = FakeMcpServer()
    FakeGraylogClient.instances = []

    monkeypatch.setattr(cli, "load_graylog_settings", lambda: fake_settings)
    monkeypatch.setattr(cli, "GraylogClient", FakeGraylogClient)

    def fake_create_mcp_server(
        graylog: object, log_level: str = "INFO"
    ) -> FakeMcpServer:
        fake_mcp.settings.log_level = log_level
        return fake_mcp

    monkeypatch.setattr(cli, "create_mcp_server", fake_create_mcp_server)

    cli.main([])

    assert fake_mcp.run_calls == [{"transport": "stdio"}]
    assert fake_mcp.settings.log_level == "INFO"
    assert len(FakeGraylogClient.instances) == 1
    assert FakeGraylogClient.instances[0].settings is fake_settings
    assert FakeGraylogClient.instances[0].closed is True


def test_main_configures_streamable_http_transport(monkeypatch: Any) -> None:
    fake_mcp = FakeMcpServer()
    FakeGraylogClient.instances = []

    monkeypatch.setattr(cli, "load_graylog_settings", lambda: object())
    monkeypatch.setattr(cli, "GraylogClient", FakeGraylogClient)

    def fake_create_mcp_server(
        graylog: object, log_level: str = "INFO"
    ) -> FakeMcpServer:
        fake_mcp.settings.log_level = log_level
        return fake_mcp

    monkeypatch.setattr(cli, "create_mcp_server", fake_create_mcp_server)

    cli.main(
        [
            "--transport",
            "streamable-http",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--path",
            "/graylog",
            "--log-level",
            "DEBUG",
        ]
    )

    assert fake_mcp.run_calls == [
        {
            "transport": "streamable-http",
            "host": "0.0.0.0",
            "port": 9000,
            "streamable_http_path": "/graylog",
            "transport_security": fake_mcp.run_calls[0]["transport_security"],
        }
    ]
    transport_security = fake_mcp.run_calls[0]["transport_security"]
    assert isinstance(transport_security, TransportSecuritySettings)
    assert transport_security.enable_dns_rebinding_protection is True
    assert transport_security.allowed_hosts == [
        "127.0.0.1:*",
        "localhost:*",
        "[::1]:*",
    ]
    assert fake_mcp.settings.log_level == "DEBUG"
    assert len(FakeGraylogClient.instances) == 1
    assert FakeGraylogClient.instances[0].closed is True
