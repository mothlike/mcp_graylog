"""Typed MCP tool registration for Graylog."""

from dataclasses import dataclass
from typing import Annotated, Any, Literal, Protocol

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .models import AggregateLogsInput, MessageSearchInput, RelativeTimeRange

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class GraylogToolClient(Protocol):
    def search_messages(self, search: MessageSearchInput) -> dict[str, Any]: ...

    def aggregate(self, aggregation: AggregateLogsInput) -> dict[str, Any]: ...

    def list_streams(self) -> list[dict[str, Any]]: ...

    def get_stream(self, stream_id: str) -> dict[str, Any]: ...

    def get_system_info(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ToolHandlers:
    graylog: GraylogToolClient

    def search_logs(self, search: MessageSearchInput) -> dict[str, Any]:
        return self.graylog.search_messages(search)

    def search_stream_logs(
        self, stream_id: str, search: MessageSearchInput
    ) -> dict[str, Any]:
        clean_stream_id = stream_id.strip()
        if not clean_stream_id:
            raise ValueError("stream_id must not be empty")

        stream_search = search.model_copy(update={"streams": [clean_stream_id]})
        return self.graylog.search_messages(stream_search)

    def aggregate_logs(self, aggregation: AggregateLogsInput) -> dict[str, Any]:
        return self.graylog.aggregate(aggregation)

    def list_streams(self) -> dict[str, list[dict[str, Any]]]:
        return {"streams": self.graylog.list_streams()}

    def get_stream_info(self, stream_id: str) -> dict[str, Any]:
        return self.graylog.get_stream(stream_id)

    def search_streams_by_name(
        self, stream_name: Annotated[str, Field(min_length=1)]
    ) -> dict[str, Any]:
        search_term = stream_name.strip()
        if not search_term:
            raise ValueError("stream_name must not be empty")

        matches: list[dict[str, Any]] = []
        normalized_search_term = search_term.lower()
        for stream in self.graylog.list_streams():
            title = str(stream.get("title", ""))
            if normalized_search_term in title.lower():
                match = {
                    "id": stream.get("id"),
                    "title": stream.get("title"),
                }
                if "description" in stream:
                    match["description"] = stream["description"]
                if "disabled" in stream:
                    match["disabled"] = stream["disabled"]
                matches.append(match)

        return {
            "search_term": stream_name,
            "matches": matches,
            "total_matches": len(matches),
        }

    def get_system_info(self) -> dict[str, Any]:
        return self.graylog.get_system_info()

    def get_error_logs(
        self,
        hours: Annotated[int, Field(ge=1)] = 1,
        limit: Annotated[int, Field(ge=1, le=1000)] = 100,
    ) -> dict[str, Any]:
        if hours < 1:
            raise ValueError("hours must be at least 1")

        search = MessageSearchInput(
            query="level:ERROR OR level:CRITICAL OR level:FATAL",
            timerange=RelativeTimeRange(value=hours, unit="h"),
            fields=["timestamp", "source", "level", "message"],
            limit=limit,
            offset=0,
        )
        return self.graylog.search_messages(search)

    def get_log_count_by_level(
        self, hours: Annotated[int, Field(ge=1)] = 1
    ) -> dict[str, Any]:
        if hours < 1:
            raise ValueError("hours must be at least 1")

        aggregation = AggregateLogsInput(
            query="*",
            timerange=RelativeTimeRange(value=hours, unit="h"),
            field="level",
            metric="count",
            metric_field=None,
            percentile=None,
            limit=10,
        )
        return self.graylog.aggregate(aggregation)


def create_tool_handlers(graylog: GraylogToolClient) -> ToolHandlers:
    return ToolHandlers(graylog=graylog)


def create_mcp_server(
    graylog: GraylogToolClient, log_level: LogLevel = "INFO"
) -> FastMCP:
    mcp = FastMCP("graylog", log_level=log_level)
    handlers = create_tool_handlers(graylog)

    mcp.tool()(handlers.search_logs)
    mcp.tool()(handlers.search_stream_logs)
    mcp.tool()(handlers.aggregate_logs)
    mcp.tool()(handlers.list_streams)
    mcp.tool()(handlers.get_stream_info)
    mcp.tool()(handlers.search_streams_by_name)
    mcp.tool()(handlers.get_system_info)
    mcp.tool()(handlers.get_error_logs)
    mcp.tool()(handlers.get_log_count_by_level)

    return mcp


__all__ = ["ToolHandlers", "create_mcp_server", "create_tool_handlers"]
