#!/usr/bin/env python3
"""Print current MCP Graylog configuration and typed tool input examples."""

import json

from mcp_graylog.models import (
    AggregateLogsInput,
    KeywordTimeRange,
    MessageSearchInput,
    RelativeTimeRange,
)


def print_json(title: str, payload: object) -> None:
    print(f"\n{title}")
    print(json.dumps(payload, indent=2))


def codex_stdio_config() -> dict[str, object]:
    return {
        "mcp_servers": {
            "graylog": {
                "command": "uv",
                "args": ["run", "mcp-graylog"],
                "env": {
                    "GRAYLOG_ENDPOINT": "https://graylog.example.com",
                    "GRAYLOG_TOKEN": "gl2-your-token",
                    "MCP_SERVER_TRANSPORT": "stdio",
                },
            }
        }
    }


def streamable_http_command() -> list[str]:
    return [
        "uv",
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
    ]


def main() -> None:
    search = MessageSearchInput(
        query="level:ERROR",
        timerange=RelativeTimeRange(value=1, unit="h"),
        fields=["timestamp", "source", "level", "message"],
        limit=25,
        offset=0,
    )
    stream_search = MessageSearchInput(
        query="source:api",
        timerange=RelativeTimeRange(value=24, unit="h"),
        streams=["000000000000000000000001"],
        fields=["timestamp", "source", "message"],
        limit=10,
        offset=0,
    )
    aggregation = AggregateLogsInput(
        query="*",
        timerange=KeywordTimeRange(keyword="Last 24 hours"),
        field="level",
        metric="count",
        limit=10,
    )

    print_json("Codex stdio config", codex_stdio_config())
    print_json("Streamable HTTP command", streamable_http_command())
    print_json("search_logs input", search.model_dump(mode="json"))
    print_json("search_stream_logs input", stream_search.model_dump(mode="json"))
    print_json("aggregate_logs input", aggregation.model_dump(mode="json"))


if __name__ == "__main__":
    main()
