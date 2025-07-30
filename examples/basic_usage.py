#!/usr/bin/env python3
"""
Basic usage example for MCP Graylog server.

This script demonstrates how to use the MCP Graylog server
to query logs and get statistics.
"""

import json
import os
import sys
from typing import Dict, Any

# Add the parent directory to the path so we can import mcp_graylog
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp_graylog.client import GraylogClient, QueryParams, AggregationParams


def example_search_logs():
    """Example: Search for error logs from the last hour."""
    print("=== Example: Search Error Logs ===")
    
    # Create query parameters
    params = QueryParams(
        query="level:ERROR OR level:CRITICAL OR level:FATAL",
        time_range="1h",
        fields=["message", "level", "source", "timestamp"],
        limit=10
    )
    
    # This would be called by the MCP server
    # result = graylog_client.search_logs(params)
    # print(json.dumps(result, indent=2))
    
    print("Query parameters:")
    print(json.dumps(params.dict(), indent=2))
    print()


def example_get_statistics():
    """Example: Get log count by level for the last 24 hours."""
    print("=== Example: Log Statistics by Level ===")
    
    # Create aggregation parameters
    aggregation = AggregationParams(
        type="terms",
        field="level",
        size=10
    )
    
    # This would be called by the MCP server
    # result = graylog_client.get_log_statistics(
    #     query="*",
    #     time_range="24h",
    #     aggregation=aggregation
    # )
    # print(json.dumps(result, indent=2))
    
    print("Aggregation parameters:")
    print(json.dumps(aggregation.dict(), indent=2))
    print()


def example_stream_search():
    """Example: Search logs in a specific stream."""
    print("=== Example: Stream Search ===")
    
    # Create query parameters for a specific stream
    params = QueryParams(
        query="source:web-server",
        time_range="24h",
        fields=["message", "level", "source"],
        limit=20,
        stream_id="stream-id-here"
    )
    
    print("Stream search parameters:")
    print(json.dumps(params.dict(), indent=2))
    print()


def example_complex_query():
    """Example: Complex query with multiple conditions."""
    print("=== Example: Complex Query ===")
    
    # Complex query with multiple conditions
    complex_query = """
    (level:ERROR OR level:CRITICAL) AND 
    (source:web-server OR source:api-server) AND 
    message:"timeout" AND 
    timestamp:[2024-01-01 TO 2024-01-02]
    """.strip()
    
    params = QueryParams(
        query=complex_query,
        time_range="7d",
        fields=["message", "level", "source", "timestamp", "host"],
        limit=50,
        sort="timestamp",
        sort_direction="desc"
    )
    
    print("Complex query parameters:")
    print(json.dumps(params.dict(), indent=2))
    print()


def example_time_range_parsing():
    """Example: Different time range formats."""
    print("=== Example: Time Range Parsing ===")
    
    time_ranges = ["1h", "24h", "7d", "1w", "30m"]
    
    for time_range in time_ranges:
        print(f"Time range '{time_range}':")
        # This would be parsed by the client
        # parsed = client._parse_time_range(time_range)
        # print(json.dumps(parsed, indent=2))
        print(f"  - Would search logs from the last {time_range}")
    print()


def main():
    """Run all examples."""
    print("MCP Graylog Server - Usage Examples")
    print("=" * 50)
    print()
    
    example_search_logs()
    example_get_statistics()
    example_stream_search()
    example_complex_query()
    example_time_range_parsing()
    
    print("=== Configuration Example ===")
    print("Environment variables needed:")
    print("GRAYLOG_ENDPOINT=https://your-graylog-server:9000")
    print("GRAYLOG_USERNAME=your-username")
    print("GRAYLOG_PASSWORD=your-password")
    print()
    
    print("=== Docker Usage ===")
    print("docker run -d \\")
    print("  --name mcp-graylog \\")
    print("  -p 8000:8000 \\")
    print("  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \\")
    print("  -e GRAYLOG_USERNAME=your-username \\")
    print("  -e GRAYLOG_PASSWORD=your-password \\")
    print("  mcp-graylog")


if __name__ == "__main__":
    main() 