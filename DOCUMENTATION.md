# MCP Graylog Server Documentation

## Overview

The MCP Graylog Server provides a Model Context Protocol (MCP) interface to Graylog, enabling AI assistants to query logs, analyze data, and manage streams through a standardized API.

## Features

- 🔍 **Log Search**: Search logs using Elasticsearch query syntax
- 📊 **Stream Management**: List and search Graylog streams
- 📈 **Analytics**: Get log statistics and aggregations
- 🛠️ **System Info**: Retrieve Graylog system information
- ✅ **Connection Testing**: Test connectivity to Graylog server

## Installation

### Prerequisites

- Python 3.8+
- Graylog server with REST API access
- Graylog username and password

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mcp_graylog
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your Graylog credentials
   ```

4. **Run the server**:
   ```bash
   python run_server.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GRAYLOG_ENDPOINT` | Graylog server URL | Yes | - |
| `GRAYLOG_USERNAME` | Graylog username | Yes | - |
| `GRAYLOG_PASSWORD` | Graylog password | Yes | - |
| `GRAYLOG_VERIFY_SSL` | Verify SSL certificates | No | true |
| `GRAYLOG_TIMEOUT` | Request timeout (seconds) | No | 30 |
| `MCP_SERVER_PORT` | MCP server port | No | 8000 |
| `MCP_SERVER_HOST` | MCP server host | No | 0.0.0.0 |
| `LOG_LEVEL` | Logging level | No | INFO |
| `LOG_FORMAT` | Log format (json/text) | No | json |

*Both username and password are required.*

## API Reference

### Request Format Validation

The MCP server now includes comprehensive request validation to ensure all requests conform to Graylog API specifications:

#### Time Range Format
- **Relative ranges**: `1h`, `24h`, `7d`, `30m`, `1w`
- **Absolute ranges**: ISO 8601 format (e.g., `2024-01-01T00:00:00Z`)

#### Query Validation
- Queries cannot be empty
- Must be valid Elasticsearch syntax
- Proper escaping for special characters

#### Parameter Bounds
- `limit`: 1-1000 for search queries
- `size`: 1-100 for aggregations
- `offset`: Non-negative integers

### Core Search Functions

#### `search_logs`
Search logs using Elasticsearch query syntax.

> ⚠️ **Request must be a JSON object, not a string.**

**Parameters:**
- `query` (string, required): Search query (Elasticsearch syntax)
- `time_range` (string, optional): Time range (e.g., '1h', '24h', '7d'). Defaults to '1h'
- `fields` (array, optional): Fields to return
- `limit` (integer, optional): Maximum number of results (1-1000, default: 50)
- `offset` (integer, optional): Result offset (default: 0)
- `sort` (string, optional): Sort field
- `sort_direction` (string, optional): Sort direction ('asc' or 'desc', default: 'desc')
- `stream_id` (string, optional): Stream ID to search in

**Example:**
```python
{
    "query": "level:ERROR AND source:web-server",
    "time_range": "24h",
    "fields": ["message", "level", "source", "timestamp"],
    "limit": 100,
    "sort": "timestamp",
    "sort_direction": "desc"
}
```

#### `search_stream_logs`
Search logs within a specific Graylog stream.

> ⚠️ **Request must be a JSON object, not a string.**

**Parameters:**
- `stream_id` (string, required): Stream ID to search in
- `query` (string, required): Search query
- `time_range` (string, optional): Time range (default: '1h')
- `fields` (array, optional): Fields to return
- `limit` (integer, optional): Maximum number of results (1-100, default: 50)

**Example:**
```python
{
    "stream_id": "5abb3f2f7bb9fd00011595fe",
    "query": "level:ERROR",
    "time_range": "7d",
    "fields": ["message", "level", "source"],
    "limit": 50
}
```

### Analytics Functions

#### `get_log_statistics`
Get log statistics and aggregations from Graylog.

> ⚠️ **Request must be a JSON object, not a string.**

**Parameters:**
- `query` (string, required): Search query
- `time_range` (string, required): Time range
- `aggregation_type` (string, required): Aggregation type
- `field` (string, required): Field to aggregate on
- `size` (integer, optional): Number of buckets (1-100, default: 10)
- `interval` (string, optional): Time interval for date histograms

**Valid aggregation types:**
- `terms`: Count occurrences of field values
- `date_histogram`: Time-based aggregations
- `cardinality`: Count unique values
- `stats`: Statistical aggregations
- `min`, `max`, `avg`, `sum`: Mathematical aggregations

**Example:**
```python
{
    "query": "level:ERROR",
    "time_range": "7d",
    "aggregation_type": "terms",
    "field": "source",
    "size": 10
}
```

### Stream Management Functions

#### `list_streams`
List all available Graylog streams.

**Returns:** JSON string containing list of streams with their IDs and metadata.

#### `search_streams_by_name`
Search for Graylog streams by name or partial name.

**Parameters:**
- `stream_name` (string, required): Partial or full stream name to search for

**Example:**
```python
search_streams_by_name("1c_eventlog")
```

#### `get_stream_info`
Get detailed information about a specific Graylog stream.

**Parameters:**
- `stream_id` (string, required): The ID of the stream to get information for

**Example:**
```python
get_stream_info("5abb3f2f7bb9fd00011595fe")
```

### Analysis Functions

#### `get_error_logs`
Get error logs from the last specified time range.

**Parameters:**
- `time_range` (string, optional): Time range to search (default: '1h')
- `limit` (integer, optional): Maximum number of results (1-1000, default: 100)

**Example:**
```python
{
    "time_range": "24h",
    "limit": 50
}
```

#### `get_log_count_by_level`
Get log count aggregated by log level.

**Parameters:**
- `time_range` (string, optional): Time range to analyze (default: '1h')

**Example:**
```python
{
    "time_range": "24h"
}
```

### System Functions

#### `get_system_info`
Get Graylog system information and status.

**Returns:** JSON string containing system information.

#### `test_connection`
Test connection to Graylog server.

**Returns:** JSON string indicating connection status.

#### `get_last_event_from_stream`
Get the last event from a specific Graylog stream.

**Parameters:**
- `stream_id` (string, required): The ID of the stream to get the last event from
- `time_range` (string, optional): Time range to search in (default: '1h')

**Example:**
```python
{
    "stream_id": "5abb3f2f7bb9fd00011595fe",
    "time_range": "1h"
}
```

## Graylog API Compatibility

### Request Format

The MCP server ensures all requests conform to Graylog API specifications:

#### Search Endpoints
- **Endpoint**: `/api/search/universal/relative`
- **Method**: GET
- **Parameters**: Query parameters for filtering and pagination

#### Aggregation Endpoints
- **Endpoint**: `/api/search/universal/relative/{aggregation_type}`
- **Method**: POST
- **Body**: JSON with query, range, field, and aggregation parameters

#### Time Range Handling
- **Relative ranges**: Converted to seconds (e.g., `1h` → `3600`)
- **Absolute ranges**: ISO 8601 format preserved
- **Validation**: Ensures proper format before sending to Graylog

### Error Handling

The server provides comprehensive error handling:

- **Validation errors**: Clear messages for invalid parameters
- **Authentication errors**: Specific handling for 401 responses
- **Connection errors**: Graceful handling of network issues
- **Graylog API errors**: Proper error propagation from Graylog

## Best Practices

### 1. Security

#### Use Username/Password Authentication
```bash
export GRAYLOG_USERNAME="your-username"
export GRAYLOG_PASSWORD="your-password"
```

#### Enable SSL Verification
```bash
export GRAYLOG_VERIFY_SSL="true"
```

### 2. Performance

#### Optimize Query Limits
- Use appropriate `limit` values (1-1000)
- Implement pagination with `offset`
- Filter results with specific `fields`

#### Efficient Time Ranges
- Use relative ranges for recent data (`1h`, `24h`)
- Use absolute ranges for historical analysis
- Avoid overly broad time ranges

### 3. Query Optimization

#### Use Specific Queries
```python
# Good: Specific query
{"query": "level:ERROR AND source:web-server"}

# Avoid: Too broad
{"query": "*"}
```

#### Leverage Fields Filtering
```python
{
    "query": "level:ERROR",
    "fields": ["message", "level", "source", "timestamp"]
}
```

### 4. Error Handling

#### Check Connection Status
```python
# Test connection before making queries
test_connection()
```

#### Handle Validation Errors
```python
# All functions return JSON with error details
result = search_logs(request)
if "error" in result:
    print(f"Error: {result['error']}")
```

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Authentication failed (401)
```
**Solution**: Verify username and password in environment variables.

#### Connection Errors
```
Error: Connection test failed
```
**Solution**: Check Graylog server URL and network connectivity.

#### Validation Errors
```
Error: Invalid time range format
```
**Solution**: Use supported formats: relative (`1h`, `24h`) or ISO 8601.

#### Query Errors
```
Error: Query parameter is required
```
**Solution**: Ensure query is not empty and uses valid Elasticsearch syntax.

### Debug Mode

Enable debug logging for detailed request/response information:

```bash
export LOG_LEVEL="DEBUG"
```

### Health Check

Use the health check endpoint to verify server status:

```bash
curl http://localhost:8000/health_check
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Run linting
flake8 mcp_graylog/

# Run type checking
mypy mcp_graylog/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 