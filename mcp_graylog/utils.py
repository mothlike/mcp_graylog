"""Utility functions for MCP Graylog server."""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any


def parse_time_range(time_range: str) -> Dict[str, Union[str, datetime]]:
    """
    Parse time range string into start and end times.

    Args:
        time_range: Time range string (e.g., '1h', '24h', '7d', '1w')

    Returns:
        Dictionary with 'from' and 'to' datetime objects
    """
    if not time_range:
        return {}

    now = datetime.utcnow()

    # Parse relative time ranges
    if time_range.endswith("h"):
        hours = int(time_range[:-1])
        from_time = now - timedelta(hours=hours)
    elif time_range.endswith("d"):
        days = int(time_range[:-1])
        from_time = now - timedelta(days=days)
    elif time_range.endswith("w"):
        weeks = int(time_range[:-1])
        from_time = now - timedelta(weeks=weeks)
    elif time_range.endswith("m"):
        minutes = int(time_range[:-1])
        from_time = now - timedelta(minutes=minutes)
    else:
        # Assume absolute time range or return empty
        return {}

    return {"from": from_time, "to": now}


def build_elasticsearch_query(base_query: str, filters: Dict[str, str]) -> str:
    """
    Build Elasticsearch query with filters.

    Args:
        base_query: Base search query
        filters: Dictionary of field filters

    Returns:
        Combined Elasticsearch query string
    """
    if not filters:
        return base_query

    filter_conditions = []
    for field, value in filters.items():
        if isinstance(value, str) and " " in value:
            # Quote values with spaces
            filter_conditions.append(f'{field}:"{value}"')
        else:
            filter_conditions.append(f"{field}:{value}")

    if base_query == "*":
        return " AND ".join(filter_conditions)
    else:
        return f"({base_query}) AND ({' AND '.join(filter_conditions)})"


def extract_log_level(message: str) -> Optional[str]:
    """
    Extract log level from log message.

    Args:
        message: Log message

    Returns:
        Log level if found, None otherwise
    """
    level_patterns = [
        r"\b(ERROR|CRITICAL|FATAL)\b",
        r"\b(WARN|WARNING)\b",
        r"\b(INFO|INFORMATION)\b",
        r"\b(DEBUG|TRACE)\b",
    ]

    for pattern in level_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return None


def format_log_entry(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format log entry for consistent output.

    Args:
        log_entry: Raw log entry from Graylog

    Returns:
        Formatted log entry
    """
    formatted = {
        "timestamp": log_entry.get("timestamp"),
        "message": log_entry.get("message", ""),
        "source": log_entry.get("source", ""),
        "level": log_entry.get(
            "level", extract_log_level(log_entry.get("message", ""))
        ),
        "raw": log_entry,
    }

    # Add any additional fields that might be present
    for key, value in log_entry.items():
        if key not in ["timestamp", "message", "source", "level"]:
            formatted[key] = value

    return formatted


def validate_query_syntax(query: str) -> bool:
    """
    Basic validation of Elasticsearch query syntax.

    Args:
        query: Query string to validate

    Returns:
        True if query appears valid, False otherwise
    """
    if not query or query.strip() == "":
        return False

    # Check for balanced parentheses
    if query.count("(") != query.count(")"):
        return False

    # Check for balanced quotes
    if query.count('"') % 2 != 0:
        return False

    return True


def get_common_log_fields() -> List[str]:
    """
    Get list of common log fields.

    Returns:
        List of common log field names
    """
    return [
        "timestamp",
        "message",
        "source",
        "level",
        "logger_name",
        "thread_name",
        "process_id",
        "host",
        "facility",
        "severity",
    ]


def parse_graylog_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and format Graylog API response.

    Args:
        response: Raw response from Graylog API

    Returns:
        Formatted response with metadata
    """
    formatted = {
        "total_results": response.get("total_results", 0),
        "execution_time": response.get("execution_time", 0),
        "messages": [],
        "metadata": {
            "query": response.get("query", ""),
            "time_range": response.get("timerange", {}),
            "fields": response.get("fields", []),
        },
    }

    # Format messages
    for message in response.get("messages", []):
        if "message" in message:
            formatted["messages"].append(format_log_entry(message["message"]))

    return formatted
