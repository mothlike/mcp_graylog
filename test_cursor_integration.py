#!/usr/bin/env python3
"""Generate current MCP Graylog client configuration examples."""

import json
from typing import Any


def stdio_env() -> dict[str, str]:
    return {
        "GRAYLOG_ENDPOINT": "https://graylog.example.com",
        "GRAYLOG_TOKEN": "gl2-your-token",
        "MCP_SERVER_TRANSPORT": "stdio",
    }


def stdio_server_config(*, include_type: bool = False) -> dict[str, Any]:
    config: dict[str, Any] = {
        "command": "uv",
        "args": ["run", "mcp-graylog"],
        "env": stdio_env(),
    }
    if include_type:
        config = {"type": "stdio", **config}
    return config


def codex_stdio_config() -> dict[str, Any]:
    return {
        "mcp_servers": {
            "graylog": stdio_server_config()
        }
    }


def claude_code_config() -> dict[str, Any]:
    return {"mcpServers": {"graylog": stdio_server_config(include_type=True)}}


def cursor_config() -> dict[str, Any]:
    return {"mcpServers": {"graylog": stdio_server_config(include_type=True)}}


def opencode_config() -> dict[str, Any]:
    return {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {
            "graylog": {
                "type": "local",
                "command": ["uv", "run", "mcp-graylog"],
                "environment": stdio_env(),
                "enabled": True,
            }
        },
    }


def hermes_config() -> dict[str, Any]:
    return {"mcp_servers": {"graylog": stdio_server_config()}}


def openclaw_config() -> dict[str, Any]:
    return {"mcp": {"servers": {"graylog": stdio_server_config()}}}


def streamable_http_config() -> dict[str, Any]:
    return {
        "command": "uv",
        "args": [
            "run",
            "mcp-graylog",
            "--transport",
            "streamable-http",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--path",
            "/mcp",
        ],
        "env": {
            "GRAYLOG_ENDPOINT": "https://graylog.example.com",
            "GRAYLOG_TOKEN": "gl2-your-token",
        },
    }


def main() -> int:
    examples = {
        "Codex stdio config": codex_stdio_config(),
        "Claude Code config": claude_code_config(),
        "Cursor config": cursor_config(),
        "OpenCode config": opencode_config(),
        "Hermes config": hermes_config(),
        "OpenClaw config": openclaw_config(),
        "Streamable HTTP config": streamable_http_config(),
    }
    for title, config in examples.items():
        print(f"{title}:")
        print(json.dumps(config, indent=2))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
