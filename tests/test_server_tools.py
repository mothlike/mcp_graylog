from typing import Any

import pytest
from mcp import Client
from mcp.server import MCPServer

from mcp_graylog.models import AggregateLogsInput, MessageSearchInput, RelativeTimeRange
from mcp_graylog.server import create_mcp_server, create_tool_handlers


class FakeGraylogClient:
    def __init__(self) -> None:
        self.search_input: MessageSearchInput | None = None
        self.aggregate_input: AggregateLogsInput | None = None
        self.stream_id: str | None = None

    def search_messages(self, search: MessageSearchInput) -> dict[str, Any]:
        self.search_input = search
        return {"messages": [{"message": {"message": "hello"}}], "total_results": 1}

    def aggregate(self, aggregation: AggregateLogsInput) -> dict[str, Any]:
        self.aggregate_input = aggregation
        return {"datarows": [{"key": ["ERROR"], "values": [3]}]}

    def list_streams(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "stream-1",
                "title": "App Logs",
                "description": "Application events",
                "disabled": False,
            },
            {
                "id": "stream-2",
                "title": "Audit",
                "description": "Audit events",
            },
        ]

    def get_stream(self, stream_id: str) -> dict[str, Any]:
        self.stream_id = stream_id
        return {"id": stream_id, "title": "App Logs", "disabled": False}

    def get_system_info(self) -> dict[str, Any]:
        return {"version": "6.3.0"}


def test_search_logs_returns_dict_and_passes_typed_search() -> None:
    fake = FakeGraylogClient()
    handlers = create_tool_handlers(fake)
    search = MessageSearchInput(query="level:ERROR", limit=50, offset=0)

    result = handlers.search_logs(search)

    assert result == {
        "messages": [{"message": {"message": "hello"}}],
        "total_results": 1,
    }
    assert fake.search_input is search


def test_search_stream_logs_adds_stream_without_mutating_original_search() -> None:
    fake = FakeGraylogClient()
    handlers = create_tool_handlers(fake)
    search = MessageSearchInput(
        query="source:api",
        streams=["original"],
        limit=50,
        offset=0,
    )

    result = handlers.search_stream_logs("stream-1", search)

    assert result["total_results"] == 1
    assert search.streams == ["original"]
    assert fake.search_input is not search
    assert fake.search_input is not None
    assert fake.search_input.streams == ["stream-1"]
    assert fake.search_input.query == "source:api"


def test_aggregate_logs_delegates_typed_aggregation() -> None:
    fake = FakeGraylogClient()
    handlers = create_tool_handlers(fake)
    aggregation = AggregateLogsInput(
        query="*",
        field="level",
        metric="count",
        metric_field=None,
        percentile=None,
        limit=10,
    )

    result = handlers.aggregate_logs(aggregation)

    assert result == {"datarows": [{"key": ["ERROR"], "values": [3]}]}
    assert fake.aggregate_input is aggregation


def test_list_streams_and_get_stream_info_delegate() -> None:
    fake = FakeGraylogClient()
    handlers = create_tool_handlers(fake)

    streams = handlers.list_streams()
    stream = handlers.get_stream_info("stream-1")

    assert streams == {"streams": fake.list_streams()}
    assert stream == {"id": "stream-1", "title": "App Logs", "disabled": False}
    assert fake.stream_id == "stream-1"


def test_search_streams_by_name_filters_case_insensitive() -> None:
    handlers = create_tool_handlers(FakeGraylogClient())

    result = handlers.search_streams_by_name("app")

    assert result == {
        "search_term": "app",
        "matches": [
            {
                "id": "stream-1",
                "title": "App Logs",
                "description": "Application events",
                "disabled": False,
            }
        ],
        "total_matches": 1,
    }


def test_search_streams_by_name_rejects_blank_term() -> None:
    handlers = create_tool_handlers(FakeGraylogClient())

    with pytest.raises(ValueError, match="stream_name must not be empty"):
        handlers.search_streams_by_name("  ")


def test_get_error_logs_builds_expected_search() -> None:
    fake = FakeGraylogClient()
    handlers = create_tool_handlers(fake)

    handlers.get_error_logs(hours=4, limit=25)

    assert fake.search_input is not None
    assert fake.search_input.query == "level:ERROR OR level:CRITICAL OR level:FATAL"
    assert fake.search_input.timerange == RelativeTimeRange(value=4, unit="h")
    assert fake.search_input.fields == ["timestamp", "source", "level", "message"]
    assert fake.search_input.limit == 25


def test_get_log_count_by_level_builds_expected_aggregation() -> None:
    fake = FakeGraylogClient()
    handlers = create_tool_handlers(fake)

    handlers.get_log_count_by_level(hours=3)

    assert fake.aggregate_input is not None
    assert fake.aggregate_input.query == "*"
    assert fake.aggregate_input.timerange == RelativeTimeRange(value=3, unit="h")
    assert fake.aggregate_input.field == "level"
    assert fake.aggregate_input.metric == "count"


def test_hours_must_be_at_least_one() -> None:
    handlers = create_tool_handlers(FakeGraylogClient())

    with pytest.raises(ValueError, match="hours must be at least 1"):
        handlers.get_error_logs(hours=0)

    with pytest.raises(ValueError, match="hours must be at least 1"):
        handlers.get_log_count_by_level(hours=0)


def test_create_mcp_server_returns_current_mcp_server() -> None:
    server = create_mcp_server(FakeGraylogClient())

    assert isinstance(server, MCPServer)
    assert server.version == "0.3.2"


@pytest.mark.asyncio
async def test_tool_schemas_expose_validation_constraints() -> None:
    server = create_mcp_server(FakeGraylogClient())

    tools = {tool.name: tool.input_schema for tool in await server.list_tools()}

    stream_name = tools["search_streams_by_name"]["properties"]["stream_name"]
    error_hours = tools["get_error_logs"]["properties"]["hours"]
    error_limit = tools["get_error_logs"]["properties"]["limit"]
    count_hours = tools["get_log_count_by_level"]["properties"]["hours"]

    assert stream_name["minLength"] == 1
    assert error_hours["minimum"] == 1
    assert error_limit["minimum"] == 1
    assert error_limit["maximum"] == 1000
    assert count_hours["minimum"] == 1


@pytest.mark.asyncio
async def test_mcp_v2_client_can_discover_and_call_tools() -> None:
    server = create_mcp_server(FakeGraylogClient())

    async with Client(server) as client:
        tools = await client.list_tools()
        result = await client.call_tool("get_system_info", {})

    assert "get_system_info" in {tool.name for tool in tools.tools}
    assert result.is_error is False
    assert result.structured_content == {"version": "6.3.0"}
