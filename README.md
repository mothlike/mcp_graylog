# MCP Graylog Server

A Model Context Protocol (MCP) server for integrating with Graylog, enabling AI assistants to query and analyze log data.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## Quick Start

### Using Docker (Recommended)

```bash
# Build and run with docker-compose
docker-compose up -d

# Or run directly with docker
docker run -d \
  --name mcp-graylog \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  -p 8000:8000 \
  mcp-graylog:latest
```

### Local Development

```bash
# Clone and setup
git clone <repository-url>
cd mcp_graylog

# Install dependencies
./install_deps.sh

# Start the server
./start.sh
```

## Features

- **Advanced Log Querying**: Query Graylog logs using Elasticsearch query syntax
- **Stream Management**: Search across multiple indices and streams
- **Time-based Filtering**: Filter logs by time range, fields, and custom criteria
- **Statistics & Aggregations**: Retrieve log statistics and aggregations
- **Docker Support**: Full container support with environment-based configuration
- **Cursor Integration**: Seamless integration with Cursor AI assistant
- **Health Monitoring**: Built-in health checks and system monitoring
- **Error Handling**: Comprehensive error handling and logging
- **Development Tools**: Complete development toolchain with testing and linting

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Additional Documentation](#additional-documentation)

## Installation

### Using Docker (Recommended)

The Docker container uses a custom entrypoint script that provides:
- Environment validation and setup
- Application configuration validation
- Proper logging and error handling
- Graceful startup process

#### Quick Setup

```bash
# Build the image
docker build -t mcp-graylog .

# Run with docker-compose (recommended)
docker-compose up -d

# Or run directly with docker
docker run -d \
  --name mcp-graylog \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  -p 8000:8000 \
  mcp-graylog:latest
```

#### Advanced Docker Deployment

```bash
docker run -d \
  --name mcp-graylog \
  -p 8000:8000 \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  -e GRAYLOG_VERIFY_SSL=true \
  -e GRAYLOG_TIMEOUT=30 \
  -e MCP_SERVER_PORT=8000 \
  -e MCP_SERVER_HOST=0.0.0.0 \
  -e LOG_LEVEL=INFO \
  -e LOG_FORMAT=json \
  --restart unless-stopped \
  mcp-graylog:latest
```

### Local Development

1. **Clone the repository:**
```bash
git clone <repository-url>
cd mcp_graylog
```

2. **Install dependencies:**
```bash
# Using the installation script (recommended)
./install_deps.sh

# Or install manually
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

3. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your Graylog credentials
```

4. **Run the server:**
```bash
# Using the startup script (recommended)
./start.sh

# Or run directly
python -m mcp_graylog.server
```

## Configuration

The server can be configured using environment variables:

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

## Usage

### Available Tools

The MCP Graylog server provides the following tools:

#### Core Search Tools
- `search_logs`: Search logs using Elasticsearch query syntax
- `search_stream_logs`: Search logs within a specific Graylog stream
- `get_last_event_from_stream`: Get the most recent event from a specific stream

#### Stream Management Tools
- `list_streams`: List all available Graylog streams
- `search_streams_by_name`: Search for streams by name or partial name
- `get_stream_info`: Get detailed information about a specific stream

#### Analysis Tools
- `get_log_statistics`: Get log statistics and aggregations
- `get_error_logs`: Get error logs from the last specified time range
- `get_log_count_by_level`: Get log count aggregated by log level

#### System Tools
- `get_system_info`: Get Graylog system information and status
- `test_connection`: Test connection to Graylog server

### Example Queries

#### Basic Log Query
```python
# Query logs from the last hour
{
    "query": "*",
    "time_range": "1h",
    "limit": 50
}
```

#### Stream-Specific Queries
```python
# Get last event from 1c_eventlog stream
{
    "stream_id": "5abb3f2f7bb9fd00011595fe",
    "query": "*",
    "limit": 1
}

# Search for error messages in a specific stream
{
    "stream_id": "5abb3f2f7bb9fd00011595fe",
    "query": "level:ERROR",
    "time_range": "24h",
    "limit": 10
}
```

#### Advanced Query with Filters
```python
# Query error logs from specific source
{
    "query": "level:ERROR AND source:web-server",
    "time_range": "24h",
    "fields": ["message", "level", "source", "timestamp"],
    "limit": 50
}
```

#### Aggregation Query
```python
# Get error count by source
{
    "query": "level:ERROR",
    "time_range": "7d",
    "aggregation": {
        "type": "terms",
        "field": "source",
        "size": 10
    }
}
```

## Important Note on Request Format

All API/tool requests that accept parameters (such as search_logs, search_stream_logs, get_log_statistics, etc.) must be provided as JSON objects, NOT as strings. Passing a string will result in an error.

**Correct:**
```json
{
  "stream_id": "5abb3f2f7bb9fd00011595fe",
  "query": "*",
  "limit": 10
}
```
**Incorrect:**
```json
"{stream_id:5abb3f2f7bb9fd00011595fe, query: *, limit: 10}"
```

## Development

### Available Commands

The project includes a comprehensive Makefile with the following commands:

```bash
# Development
make install          # Install the package in development mode
make test            # Run tests
make lint            # Run linting checks
make format          # Format code
make clean           # Clean build artifacts
make check           # Run all checks (format, lint, test)

# Docker
make docker-build    # Build Docker image
make docker-run      # Run Docker container
make docker-stop     # Stop Docker container
make docker-logs     # Show Docker container logs

# Testing
make test-entrypoint # Test the entrypoint configuration
make test-pydantic   # Test the Pydantic fix
make test-fixes      # Test the Pydantic and FastMCP fixes

# Setup
make install-deps    # Install dependencies using the installation script
make start           # Start the server using the startup script

# Docker Compose
make docker-compose-up    # Start services with docker-compose
make docker-compose-down  # Stop services with docker-compose
make docker-compose-logs  # Show docker-compose logs
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_client.py -v

# Run with coverage
pytest tests/ --cov=mcp_graylog
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
black --check .
isort --check-only .
mypy .

# Run all checks
make check
```

## Cursor Integration

### Setting up MCP Graylog Server in Cursor

The Docker container uses a custom entrypoint script that provides enhanced startup capabilities including environment validation, configuration checks, and proper logging.

#### Quick Setup

1. **Test your setup first:**
   ```bash
   # Run the integration test script
   python3 test_cursor_integration.py
   ```

2. **Deploy the MCP Graylog server using Docker:**
   ```bash
   # Build the image
   docker build -t mcp-graylog .
   
   # Run the MCP Graylog server container
   docker run -d \
     --name mcp-graylog \
     -p 8000:8000 \
           -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
      -e GRAYLOG_USERNAME=your-username \
      -e GRAYLOG_PASSWORD=your-password \
      -e GRAYLOG_VERIFY_SSL=true \
      -e GRAYLOG_TIMEOUT=30 \
      mcp-graylog:latest
   ```

3. **Configure Cursor to use the MCP server:**

   Open Cursor's settings and add one of the following configurations:

       **Username/Password Authentication**
   ```json
   {
     "mcpServers": {
       "graylog": {
         "command": "docker",
         "args": [
           "run", 
           "--rm", 
           "-i", 
           "-e", "GRAYLOG_ENDPOINT=https://your-graylog-server:9000",
           "-e", "GRAYLOG_USERNAME=your-username",
           "-e", "GRAYLOG_PASSWORD=your-password",
           "-e", "GRAYLOG_VERIFY_SSL=true",
           "-e", "GRAYLOG_TIMEOUT=30",
           "mcp-graylog:latest"
         ],
         "env": {}
       }
     }
   }
   ```

4. **Restart Cursor** to load the new MCP server configuration.

### Using the MCP Graylog Server in Cursor

Once configured, you can use the Graylog integration directly in Cursor's chat:

#### Example Queries:

**Search for error logs:**
```
Search for error logs from the last hour in Graylog
```

**Get log statistics:**
```
Get log count by level for the last 24 hours
```

**Search specific streams:**
```
List all available Graylog streams and show me the logs from the web-server stream
```

**Complex queries:**
```
Search for timeout errors from web-server or api-server in the last 7 days
```

### Example Workflow in Cursor

1. **Debugging Issues:**
   ```
   "I'm seeing errors in my application. Can you check the Graylog logs for any ERROR level messages from the last 2 hours?"
   ```

2. **Performance Analysis:**
   ```
   "Show me the log count by level for the last 24 hours to understand the application's health"
   ```

3. **Stream-specific Analysis:**
   ```
   "List all Graylog streams and then search for any timeout errors in the web-server stream"
   ```

4. **System Monitoring:**
   ```
   "Get the Graylog system information and check if the connection is healthy"
   ```

## Troubleshooting

### Connection Issues
- Verify Graylog endpoint is accessible
- Check credentials are correct
- Ensure firewall allows connections to Graylog port

### MCP Server Issues
- Check server logs: `docker logs mcp-graylog`
- Check entrypoint logs: `docker logs mcp-graylog | grep -E "(ERROR|WARNING|Starting|Checking)"`
- Test connection: Use the `test_connection` function
- Verify environment variables are set correctly
- Test entrypoint manually: `docker run --rm mcp-graylog:latest ./entrypoint.sh`

### Pydantic Import Errors
- If you see `PydanticImportError: BaseSettings has been moved to pydantic-settings`, run: `./install_deps.sh`
- Ensure `pydantic-settings>=2.0.0` is installed: `pip install pydantic-settings>=2.0.0`
- Test the fix: `make test-pydantic`

### FastMCP API Errors
- If you see `AttributeError: 'FastMCP' object has no attribute 'function'`, the API has been updated to use `@app.tool()` instead of `@app.function()`
- Test the fixes: `make test-fixes`

### Cursor Integration Issues
- Restart Cursor after configuration changes
- Check Cursor's developer console for MCP errors
- Verify the MCP server is running on the expected port
- Use the test script: `python3 test_cursor_integration.py`

## Additional Documentation

- **[Complete Documentation](DOCUMENTATION.md)** - Comprehensive guide with detailed examples and advanced usage
- **[Examples](examples/)** - Usage examples and test scripts

## Project Structure

```
mcp_graylog/
├── mcp_graylog/           # Main package
│   ├── __init__.py
│   ├── client.py          # Graylog client
│   ├── config.py          # Configuration management
│   ├── server.py          # MCP server implementation
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
├── examples/              # Usage examples
├── logs/                  # Log files
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Docker image definition
├── entrypoint.sh         # Docker entrypoint script
├── start.sh              # Development startup script
├── install_deps.sh       # Dependency installation script
├── Makefile              # Development commands
├── pyproject.toml        # Project metadata
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `make test`
5. Format your code: `make format`
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Check the [complete documentation](DOCUMENTATION.md)
- **Examples**: See the [examples directory](examples/) for usage examples
- **Testing**: Use the provided test scripts to verify your setup 