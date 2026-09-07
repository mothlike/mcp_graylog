"""Command line entrypoint for mcp-graylog."""

import argparse
from collections.abc import Sequence
from typing import Literal

from mcp.server.transport_security import TransportSecuritySettings

from .config import load_graylog_settings, load_server_settings
from .graylog_client import GraylogClient
from .server import LogLevel, create_mcp_server

Transport = Literal["stdio", "streamable-http"]
LOG_LEVELS: tuple[LogLevel, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments with MCP_SERVER_* environment defaults."""

    defaults = load_server_settings()
    parser = argparse.ArgumentParser(prog="mcp-graylog")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default=defaults.transport,
        help="MCP transport to run. Defaults to stdio for Codex.",
    )
    parser.add_argument(
        "--host",
        default=defaults.host,
        help="Host for streamable HTTP transport.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=defaults.port,
        help="Port for streamable HTTP transport.",
    )
    parser.add_argument(
        "--path",
        default=defaults.path,
        help="Mount path for streamable HTTP transport.",
    )
    parser.add_argument(
        "--log-level",
        default=defaults.log_level,
        choices=LOG_LEVELS,
        help="MCP server log level.",
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        dest="allowed_hosts",
        default=defaults.allowed_host_values(),
        help="Allowed HTTP Host value. Repeat for multiple hosts.",
    )
    parser.add_argument(
        "--allowed-origin",
        action="append",
        dest="allowed_origins",
        default=defaults.allowed_origin_values(),
        help="Allowed browser Origin value. Repeat for multiple origins.",
    )
    parser.add_argument(
        "--disable-dns-rebinding-protection",
        action="store_false",
        dest="dns_rebinding_protection",
        default=defaults.dns_rebinding_protection,
        help="Disable Host and Origin validation behind a trusted reverse proxy.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    transport: Transport = args.transport
    log_level: LogLevel = args.log_level

    graylog_settings = load_graylog_settings()
    with GraylogClient(graylog_settings) as graylog:
        mcp = create_mcp_server(graylog, log_level=log_level)

        if transport == "streamable-http":
            transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=args.dns_rebinding_protection,
                allowed_hosts=args.allowed_hosts,
                allowed_origins=args.allowed_origins,
            )
            mcp.run(
                transport="streamable-http",
                host=args.host,
                port=args.port,
                streamable_http_path=args.path,
                transport_security=transport_security,
            )
        else:
            mcp.run(transport="stdio")
