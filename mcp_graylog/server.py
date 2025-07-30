"""MCP server for Graylog integration."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from pydantic import BaseModel, Field, validator

from .client import GraylogClient, QueryParams, AggregationParams
from .config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.server.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(title="MCP Graylog Server", version="1.0.0")

# Initialize FastMCP server
mcp_server = FastMCP("graylog")

# Initialize Graylog client
graylog_client = GraylogClient()


class SearchLogsRequest(BaseModel):
    """Request model for searching logs."""

    query: str = Field(..., description="Search query (Elasticsearch syntax)")
    time_range: Optional[str] = Field(
        None,
        description="Time range (e.g., '1h', '24h', '7d'). Defaults to '1h' if not specified.",
    )
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    limit: int = Field(50, description="Maximum number of results")
    offset: int = Field(0, description="Result offset")
    sort: Optional[str] = Field(None, description="Sort field")
    sort_direction: str = Field("desc", description="Sort direction (asc/desc)")
    stream_id: Optional[str] = Field(None, description="Stream ID to search in")

    @validator("query")
    def validate_query(cls, v):
        """Validate that query is not empty."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @validator("limit")
    def validate_limit(cls, v):
        """Validate limit is within reasonable bounds."""
        if v < 1:
            raise ValueError("Limit must be at least 1")
        if v > 1000:
            raise ValueError("Limit cannot exceed 1000")
        return v

    @validator("time_range")
    def validate_time_range(cls, v):
        """Validate time range format."""
        if v is None:
            return v

        # Check for relative time ranges (e.g., '1h', '24h', '7d')
        import re

        relative_pattern = r"^\d+[smhdw]$"
        if re.match(relative_pattern, v):
            return v

        # Check for ISO 8601 format (absolute time ranges)
        try:
            from datetime import datetime

            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError(
                f"Invalid time range format: {v}. Use relative (e.g., '1h') or ISO 8601 format"
            )


class AggregationRequest(BaseModel):
    """Request model for log aggregations."""

    query: str = Field(..., description="Search query")
    time_range: str = Field(..., description="Time range")
    aggregation_type: str = Field(
        ..., description="Aggregation type (terms, date_histogram, etc.)"
    )
    field: str = Field(..., description="Field to aggregate on")
    size: int = Field(10, description="Number of buckets")
    interval: Optional[str] = Field(
        None, description="Time interval for date histograms"
    )

    @validator("query")
    def validate_query(cls, v):
        """Validate that query is not empty."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @validator("aggregation_type")
    def validate_aggregation_type(cls, v):
        """Validate aggregation type."""
        valid_types = [
            "terms",
            "date_histogram",
            "cardinality",
            "stats",
            "min",
            "max",
            "avg",
            "sum",
        ]
        if v not in valid_types:
            raise ValueError(
                f"Invalid aggregation type: {v}. Valid types: {valid_types}"
            )
        return v

    @validator("field")
    def validate_field(cls, v):
        """Validate that field is not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @validator("size")
    def validate_size(cls, v):
        """Validate size is within reasonable bounds."""
        if v < 1:
            raise ValueError("Size must be at least 1")
        if v > 100:
            raise ValueError("Size cannot exceed 100")
        return v

    @validator("time_range")
    def validate_time_range(cls, v):
        """Validate time range format."""
        if not v or not v.strip():
            raise ValueError("Time range is required")

        # Check for relative time ranges (e.g., '1h', '24h', '7d')
        import re

        relative_pattern = r"^\d+[smhdw]$"
        if re.match(relative_pattern, v):
            return v

        # Check for ISO 8601 format (absolute time ranges)
        try:
            from datetime import datetime

            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError(
                f"Invalid time range format: {v}. Use relative (e.g., '1h') or ISO 8601 format"
            )


class StreamSearchRequest(BaseModel):
    """Request model for searching logs in a specific stream."""

    stream_id: str = Field(
        ..., description="Stream ID (e.g., '5abb3f2f7bb9fd00011595fe' for 1c_eventlog)"
    )
    query: str = Field(
        ...,
        description="Search query (e.g., '*' for all messages, 'level:ERROR' for errors)",
    )
    time_range: Optional[str] = Field(
        None,
        description="Time range (e.g., '1h', '24h', '7d'). Defaults to '1h' if not specified.",
    )
    fields: Optional[List[str]] = Field(
        None, description="Fields to return (e.g., ['message', 'level', 'source'])"
    )
    limit: int = Field(50, description="Maximum number of results (1-100)")

    @validator("stream_id")
    def validate_stream_id(cls, v):
        """Validate that stream_id is not empty."""
        if not v or not v.strip():
            raise ValueError("Stream ID cannot be empty")
        return v.strip()

    @validator("query")
    def validate_query(cls, v):
        """Validate that query is not empty."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @validator("limit")
    def validate_limit(cls, v):
        """Validate limit is within reasonable bounds."""
        if v < 1:
            raise ValueError("Limit must be at least 1")
        if v > 100:
            raise ValueError("Limit cannot exceed 100")
        return v

    @validator("time_range")
    def validate_time_range(cls, v):
        """Validate time range format."""
        if v is None:
            return v

        # Check for relative time ranges (e.g., '1h', '24h', '7d')
        import re

        relative_pattern = r"^\d+[smhdw]$"
        if re.match(relative_pattern, v):
            return v

        # Check for ISO 8601 format (absolute time ranges)
        try:
            from datetime import datetime

            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError(
                f"Invalid time range format: {v}. Use relative (e.g., '1h') or ISO 8601 format"
            )


# Health check endpoint
@app.get("/health_check")
async def health_check():
    """Basic health check endpoint."""
    try:
        is_connected = graylog_client.test_connection()

        health_status = {
            "status": "healthy" if is_connected else "unhealthy",
            "graylog_connected": is_connected,
            "graylog_endpoint": config.graylog.endpoint,
            "server_config": {"host": config.server.host, "port": config.server.port},
        }

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "graylog_connected": False,
            },
        )


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "MCP Graylog Server",
        "version": "1.0.0",
        "endpoints": {
            "health_check": "/health_check",
            "mcp_server": "Available via MCP protocol",
        },
    }


@mcp_server.tool()
def search_logs(request: SearchLogsRequest) -> str:
    """
    Search logs in Graylog using Elasticsearch query syntax.

    Request format: JSON object (not a string) with the following fields:
      {
        "query": "*",
        "time_range": "24h",
        "fields": ["message", "level"],
        "limit": 10,
        "offset": 0,
        "sort": "timestamp",
        "sort_direction": "desc",
        "stream_id": "<stream_id>"
      }
    All fields except 'query' are optional. If no time_range is specified, defaults to 1 hour.

    Args:
        request: Search parameters as a JSON object (not a string).

    Returns:
        JSON string containing search results with messages and metadata
    """
    # --- BEGIN PATCH ---
    # Accept both dict and string input for request
    if isinstance(request, str):
        try:
            request_dict = json.loads(request)
            request = SearchLogsRequest(**request_dict)
        except Exception as e:
            return json.dumps({"error": f"Request must be a JSON object or a JSON string that can be parsed into an object. Error: {str(e)}"}, indent=2)
    # --- END PATCH ---
    try:
        # Validate request
        if not request.query:
            return json.dumps({"error": "Query parameter is required"}, indent=2)

        params = QueryParams(
            query=request.query,
            time_range=request.time_range,
            fields=request.fields,
            limit=request.limit,
            offset=request.offset,
            sort=request.sort,
            sort_direction=request.sort_direction,
            stream_id=request.stream_id,
        )

        result = graylog_client.search_logs(params)
        return json.dumps(result, indent=2)

    except ValueError as e:
        logger.error(f"Validation error in search_logs: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Search logs failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def get_log_statistics(request: AggregationRequest) -> str:
    """
    Get log statistics and aggregations from Graylog.

    Request format: JSON object (not a string) with the following fields:
      {
        "query": "*",
        "time_range": "24h",
        "aggregation_type": "terms",
        "field": "source",
        "size": 10,
        "interval": "1h"
      }
    All fields except 'query', 'time_range', 'aggregation_type', and 'field' are optional.

    Args:
        request: Aggregation parameters as a JSON object (not a string).

    Returns:
        JSON string containing aggregation results
    """
    if isinstance(request, str):
        return json.dumps({"error": "Request must be a JSON object, not a string."}, indent=2)
    try:
        # Validate request
        if not request.query:
            return json.dumps({"error": "Query parameter is required"}, indent=2)
        if not request.field:
            return json.dumps({"error": "Field parameter is required"}, indent=2)
        if not request.time_range:
            return json.dumps({"error": "Time range parameter is required"}, indent=2)

        aggregation = AggregationParams(
            type=request.aggregation_type,
            field=request.field,
            size=request.size,
            interval=request.interval,
        )

        result = graylog_client.get_log_statistics(
            query=request.query, time_range=request.time_range, aggregation=aggregation
        )
        return json.dumps(result, indent=2)

    except ValueError as e:
        logger.error(f"Validation error in get_log_statistics: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Get log statistics failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def list_streams() -> str:
    """
    List all available Graylog streams.

    Returns:
        JSON string containing list of streams with their IDs and metadata
    """
    try:
        streams = graylog_client.list_streams()
        return json.dumps({"streams": streams}, indent=2)

    except Exception as e:
        logger.error(f"List streams failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def get_stream_info(stream_id: str) -> str:
    """
    Get detailed information about a specific Graylog stream.

    Args:
        stream_id: The ID of the stream to get information for

    Returns:
        JSON string containing stream details
    """
    try:
        if not stream_id or not stream_id.strip():
            return json.dumps({"error": "Stream ID is required"}, indent=2)

        stream_info = graylog_client.get_stream_info(stream_id.strip())
        return json.dumps(stream_info, indent=2)

    except ValueError as e:
        logger.error(f"Validation error in get_stream_info: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Get stream info failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def search_stream_logs(request: StreamSearchRequest) -> str:
    """
    Search logs within a specific Graylog stream.

    Request format: JSON object (not a string) with the following fields:
      {
        "stream_id": "<stream_id>",
        "query": "*",
        "time_range": "24h",
        "fields": ["message", "level"],
        "limit": 10
      }
    All fields except 'stream_id' and 'query' are optional. If no time_range is specified, defaults to 1 hour.

    Args:
        request: Stream search parameters as a JSON object (not a string).

    Returns:
        JSON string containing search results with messages and metadata from the specified stream
    """
    if isinstance(request, str):
        return json.dumps({"error": "Request must be a JSON object, not a string."}, indent=2)
    try:
        # Validate request
        if not request.stream_id or not request.stream_id.strip():
            return json.dumps({"error": "Stream ID is required"}, indent=2)
        if not request.query or not request.query.strip():
            return json.dumps({"error": "Query is required"}, indent=2)

        # Create query parameters for stream search
        params = QueryParams(
            query=request.query,
            time_range=request.time_range,
            fields=request.fields,
            limit=request.limit,
            stream_id=request.stream_id,
        )

        # Use the client's search_stream_logs method
        result = graylog_client.search_stream_logs(request.stream_id, params)
        return json.dumps(result, indent=2)

    except ValueError as e:
        logger.error(f"Validation error in search_stream_logs: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Search stream logs failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def get_system_info() -> str:
    """
    Get Graylog system information and status.

    Returns:
        JSON string containing system information
    """
    try:
        system_info = graylog_client.get_system_info()
        return json.dumps(system_info, indent=2)

    except Exception as e:
        logger.error(f"Get system info failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def test_connection() -> str:
    """
    Test connection to Graylog server.

    Returns:
        JSON string indicating connection status
    """
    try:
        is_connected = graylog_client.test_connection()
        return json.dumps(
            {"connected": is_connected, "endpoint": config.graylog.endpoint}, indent=2
        )

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return json.dumps(
            {"connected": False, "error": str(e), "endpoint": config.graylog.endpoint},
            indent=2,
        )


@mcp_server.tool()
def get_error_logs(time_range: str = "1h", limit: int = 100) -> str:
    """
    Get error logs from the last specified time range.

    Args:
        time_range: Time range to search (default: 1h)
        limit: Maximum number of results (default: 100)

    Returns:
        JSON string containing error logs
    """
    try:
        # Validate parameters
        if limit < 1 or limit > 1000:
            return json.dumps({"error": "Limit must be between 1 and 1000"}, indent=2)

        params = QueryParams(
            query="level:ERROR OR level:CRITICAL OR level:FATAL",
            time_range=time_range,
            limit=limit,
            fields=["message", "level", "source", "timestamp"],
        )

        result = graylog_client.search_logs(params)
        return json.dumps(result, indent=2)

    except ValueError as e:
        logger.error(f"Validation error in get_error_logs: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Get error logs failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def get_log_count_by_level(time_range: str = "1h") -> str:
    """
    Get log count aggregated by log level.

    Args:
        time_range: Time range to analyze (default: 1h)

    Returns:
        JSON string containing log counts by level
    """
    try:
        aggregation = AggregationParams(type="terms", field="level", size=10)

        result = graylog_client.get_log_statistics(
            query="*", time_range=time_range, aggregation=aggregation
        )
        return json.dumps(result, indent=2)

    except ValueError as e:
        logger.error(f"Validation error in get_log_count_by_level: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Get log count by level failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def search_streams_by_name(stream_name: str) -> str:
    """
    Search for Graylog streams by name or partial name.

    This tool helps you find the correct stream ID by searching for streams
    that contain the specified name in their title.

    Args:
        stream_name: Partial or full stream name to search for (e.g., '1c_eventlog', 'nginx')

    Returns:
        JSON string containing matching streams with their IDs and metadata
    """
    try:
        if not stream_name or not stream_name.strip():
            return json.dumps({"error": "Stream name is required"}, indent=2)

        all_streams = graylog_client.list_streams()

        # Filter streams by name (case-insensitive)
        matching_streams = []
        search_term = stream_name.lower()

        for stream in all_streams:
            title = stream.get("title", "").lower()
            if search_term in title:
                matching_streams.append(
                    {
                        "id": stream.get("id"),
                        "title": stream.get("title"),
                        "description": stream.get("description"),
                        "disabled": stream.get("disabled", False),
                    }
                )

        return json.dumps(
            {
                "search_term": stream_name,
                "matches": matching_streams,
                "total_matches": len(matching_streams),
            },
            indent=2,
        )

    except ValueError as e:
        logger.error(f"Validation error in search_streams_by_name: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Search streams by name failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp_server.tool()
def get_last_event_from_stream(stream_id: str, time_range: str = "1h") -> str:
    """
    Get the last event from a specific Graylog stream.

    This tool provides a simple way to get the most recent log message
    from a specified stream within the given time range.

    Args:
        stream_id: The ID of the stream to get the last event from
        time_range: Time range to search in (default: '1h')

    Returns:
        JSON string containing the last event from the specified stream
    """
    try:
        if not stream_id or not stream_id.strip():
            return json.dumps({"error": "Stream ID is required"}, indent=2)

        params = QueryParams(
            query="*", time_range=time_range, limit=1, stream_id=stream_id
        )

        result = graylog_client.search_stream_logs(stream_id, params)
        return json.dumps(result, indent=2)

    except ValueError as e:
        logger.error(f"Validation error in get_last_event_from_stream: {e}")
        return json.dumps({"error": f"Validation error: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Get last event from stream failed: {e}")
        return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting MCP Graylog server on {config.server.host}:{config.server.port}"
    )
    logger.info(f"Graylog endpoint: {config.graylog.endpoint}")

    # Test connection on startup
    if graylog_client.test_connection():
        logger.info("Successfully connected to Graylog")
    else:
        logger.warning("Failed to connect to Graylog - check configuration")

    # Run the FastMCP server over stdio (for MCP protocol)
    mcp_server.run()
