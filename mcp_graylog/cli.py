"""Command line entrypoint for mcp-graylog."""

import argparse
from collections.abc import Sequence
from typing import Literal

from .config import load_graylog_settings
from .graylog_client import GraylogClient
from .server import LogLevel, create_mcp_server

Transport = Literal["stdio", "streamable-http"]
LOG_LEVELS: tuple[LogLevel, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments without loading environment-backed settings."""

    parser = argparse.ArgumentParser(prog="mcp-graylog")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="MCP transport to run. Defaults to stdio for Codex.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for streamable HTTP transport.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for streamable HTTP transport.",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="Mount path for streamable HTTP transport.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=LOG_LEVELS,
        help="MCP server log level.",
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
            mcp.settings.host = args.host
            mcp.settings.port = args.port
            mcp.settings.streamable_http_path = args.path

        mcp.run(transport=transport)
