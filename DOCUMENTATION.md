# MCP Graylog Server - Complete Documentation

A comprehensive guide for the Model Context Protocol (MCP) server for integrating with Graylog, enabling AI assistants to query and analyze log data.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Docker Setup](#docker-setup)
7. [Cursor Integration](#cursor-integration)
8. [Development](#development)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)
11. [Best Practices](#best-practices)
12. [Support](#support)

## Overview

The MCP Graylog Server provides a Model Context Protocol (MCP) interface for Graylog, allowing AI assistants like Cursor to query and analyze log data directly. It supports both Docker container deployment and local development setups.

## Features

- **Log Querying**: Query Graylog logs using Elasticsearch query syntax
- **Stream Management**: Search across multiple indices and streams
- **Advanced Filtering**: Filter logs by time range, fields, and custom criteria
- **Statistics & Aggregations**: Retrieve log statistics and aggregations
- **Docker Support**: Full container support with environment-based configuration
- **Cursor Integration**: Seamless integration with Cursor AI assistant
- **Health Monitoring**: Built-in health checks and system monitoring
- **Error Handling**: Comprehensive error handling and logging

## Installation

### Using Docker (Recommended)

The Docker container uses a custom entrypoint script that provides:
- Environment validation and setup
- Application configuration validation
- Proper logging and error handling
- Graceful startup process

#### Quick Start

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
cp .env.example .env
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

### Environment Variables

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
| `LOG_FORMAT` | Log format | No | json |

*Both username and password are required.

### Docker Compose Setup

For easier management, use Docker Compose:

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  mcp-graylog:
    build: .
    container_name: mcp-graylog
    ports:
      - "8000:8000"
    environment:
      - GRAYLOG_ENDPOINT=${GRAYLOG_ENDPOINT}
      - GRAYLOG_USERNAME=${GRAYLOG_USERNAME}
      - GRAYLOG_PASSWORD=${GRAYLOG_PASSWORD}

      - GRAYLOG_VERIFY_SSL=${GRAYLOG_VERIFY_SSL:-true}
      - GRAYLOG_TIMEOUT=${GRAYLOG_TIMEOUT:-30}
      - MCP_SERVER_PORT=8000
      - MCP_SERVER_HOST=0.0.0.0
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_FORMAT=${LOG_FORMAT:-json}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

**.env file:**
```bash
GRAYLOG_ENDPOINT=https://your-graylog-server:9000
GRAYLOG_USERNAME=your-username
GRAYLOG_PASSWORD=your-password
GRAYLOG_VERIFY_SSL=true
GRAYLOG_TIMEOUT=30
LOG_LEVEL=INFO
LOG_FORMAT=json
```

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

### Basic Log Query

```python
# Query logs from the last hour
{
    "query": "*",
    "time_range": "1h",
    "limit": 50
}
```

### Stream-Specific Queries

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

### Stream Discovery

```python
# Find streams by name
search_streams_by_name("1c_eventlog")

# Get stream information
get_stream_info("5abb3f2f7bb9fd00011595fe")
```

### Advanced Query with Filters

```python
# Query error logs from specific source
{
    "query": "level:ERROR AND source:web-server",
    "time_range": "24h",
    "fields": ["message", "level", "source", "timestamp"],
    "limit": 50
}
```

### Aggregation Query

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

## Docker Setup

### Building the Docker Image

#### Basic Build Commands

**Standard build:**
```bash
docker build -t mcp-graylog .
```

**Build with specific tag:**
```bash
docker build -t mcp-graylog:latest .
docker build -t mcp-graylog:v1.0.0 .
docker build -t mcp-graylog:dev .
```

**Build with no cache (clean build):**
```bash
docker build --no-cache -t mcp-graylog .
```

**Build with progress output:**
```bash
docker build --progress=plain -t mcp-graylog .
```

#### Multi-Platform Builds

**Build for multiple platforms:**
```bash
# Enable buildx
docker buildx create --use

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t mcp-graylog .

# Build and push to registry
docker buildx build --platform linux/amd64,linux/arm64 -t your-registry/mcp-graylog:latest --push .
```

**Build for specific platform:**
```bash
# For AMD64 (Intel/AMD)
docker buildx build --platform linux/amd64 -t mcp-graylog .

# For ARM64 (Apple Silicon, ARM servers)
docker buildx build --platform linux/arm64 -t mcp-graylog .
```

#### Advanced Build Options

**Build with build arguments:**
```bash
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t mcp-graylog .
```

**Build with custom Dockerfile:**
```bash
docker build -f Dockerfile.custom -t mcp-graylog:custom .
```

### Build Verification

#### 1. Check Image Details

```bash
# List built images
docker images | grep mcp-graylog

# Inspect image details
docker inspect mcp-graylog

# Check image layers
docker history mcp-graylog
```

#### 2. Test Image Functionality

**Basic import test:**
```bash
docker run --rm mcp-graylog python -c "
import mcp_graylog
print('Package imported successfully')
print('Version:', mcp_graylog.__version__)
"
```

**Configuration test:**
```bash
docker run --rm \
  -e GRAYLOG_ENDPOINT=https://test:9000 \
  -e GRAYLOG_USERNAME=test \
  -e GRAYLOG_PASSWORD=test \
  mcp-graylog python -c "
from mcp_graylog.config import config
print('Endpoint:', config.graylog.endpoint)
print('Username:', config.graylog.username)
"
```

### Publishing the Image

#### Tagging for Registry

```bash
# Tag for Docker Hub
docker tag mcp-graylog your-username/mcp-graylog:latest

# Tag for private registry
docker tag mcp-graylog registry.company.com/mcp-graylog:latest

# Tag with version
docker tag mcp-graylog your-username/mcp-graylog:v1.0.0
```

#### Pushing to Registry

```bash
# Login to registry
docker login

# Push to Docker Hub
docker push your-username/mcp-graylog:latest

# Push to private registry
docker push registry.company.com/mcp-graylog:latest
```

#### Export/Import

**Save image to file:**
```bash
docker save mcp-graylog:latest > mcp-graylog.tar
```

**Load image from file:**
```bash
docker load < mcp-graylog.tar
```

**Export as tar.gz:**
```bash
docker save mcp-graylog:latest | gzip > mcp-graylog.tar.gz
```

### Build Optimization

#### Multi-Stage Build

Create a `Dockerfile.optimized` for smaller images:

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --user -e .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY mcp_graylog/ ./mcp_graylog/

ENV PATH=/root/.local/bin:$PATH

USER app
EXPOSE 8000
CMD ["python", "-m", "mcp_graylog.server"]
```

#### Build with .dockerignore

Create a `.dockerignore` file to exclude unnecessary files:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.idea
.vscode
*.swp
*.swo
*~
.DS_Store
```

## Cursor Integration

### Setting up MCP Graylog Server in Cursor

The Docker container now uses a custom entrypoint script that provides enhanced startup capabilities including environment validation, configuration checks, and proper logging.

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

   **Environment Variables in Cursor Config**
   ```json
   {
     "mcpServers": {
       "graylog": {
         "command": "docker",
         "args": ["run", "--rm", "-i", "mcp-graylog:latest"],
         "env": {
           "GRAYLOG_ENDPOINT": "https://your-graylog-server:9000",
           "GRAYLOG_USERNAME": "your-username",
           "GRAYLOG_PASSWORD": "your-password",
           "GRAYLOG_VERIFY_SSL": "true",
           "GRAYLOG_TIMEOUT": "30"
         }
       }
     }
   }
   ```

4. **Restart Cursor** to load the new MCP server configuration.

#### Testing Your Setup

Use the provided test script to verify your configuration:

```bash
# Set your environment variables
export GRAYLOG_ENDPOINT=https://your-graylog-server:9000
export GRAYLOG_USERNAME=your-username
export GRAYLOG_PASSWORD=your-password

# Run the test script
python3 test_cursor_integration.py
```

The test script will:
- ✅ Check if required environment variables are set
- ✅ Verify Docker image exists
- ✅ Test container startup
- ✅ Generate the correct Cursor configuration

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

#### Available Functions in Cursor:

- `search_logs` - Search logs with custom queries
- `get_log_statistics` - Get log aggregations and statistics
- `list_streams` - List available Graylog streams
- `get_stream_info` - Get detailed stream information
- `search_stream_logs` - Search logs within specific streams
- `get_system_info` - Get Graylog system information
- `test_connection` - Test Graylog connectivity
- `get_error_logs` - Get error logs from specified time range
- `get_log_count_by_level` - Get log counts aggregated by level
- `health_check` - Health check endpoint

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

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy .
```

### Entrypoint Script

The Docker container uses a custom entrypoint script (`entrypoint.sh`) that provides:

#### Features
- **Environment Validation**: Checks for required environment variables and provides warnings for missing ones
- **Configuration Validation**: Verifies that the application files exist and are accessible
- **Application Setup**: Creates necessary directories and sets proper permissions
- **Graceful Startup**: Provides detailed logging during the startup process
- **Error Handling**: Proper error handling and exit codes

#### Entrypoint Process
1. **Dependency Check**: Validates environment variables and configuration
2. **Application Validation**: Ensures all required files are present
3. **Setup**: Creates logs directory and sets permissions
4. **Startup**: Launches the MCP server with proper logging

### Development Script
For local development, use the `start.sh` script which:
- Sets up a Python virtual environment
- Installs dependencies
- Validates environment variables
- Starts the server in development mode

## Troubleshooting

### Container Issues

**Container not starting:**
```bash
# Check container logs (now with entrypoint logging)
docker logs mcp-graylog

# Check entrypoint logs specifically
docker logs mcp-graylog | grep -E "(ERROR|WARNING|Starting|Checking)"

# Check container status
docker ps -a | grep mcp-graylog

# Restart container
docker restart mcp-graylog

# Test entrypoint manually
docker run --rm mcp-graylog:latest ./entrypoint.sh
```

**Environment variable issues:**
```bash
# Test environment variables in a new container
docker run --rm mcp-graylog:latest env | grep GRAYLOG

# Check entrypoint environment validation
docker run --rm -e GRAYLOG_ENDPOINT=test mcp-graylog:latest ./entrypoint.sh

# Update environment variables
# Re-run with correct environment variables in Cursor config
```

**Port conflicts:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
docker run -d \
  --name mcp-graylog \
  -p 8001:8000 \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  mcp-graylog:latest
```

### Connection Issues

**Graylog connection fails:**
```bash
# Test Graylog connectivity from container
docker run --rm mcp-graylog:latest python -c "
from mcp_graylog.client import GraylogClient
client = GraylogClient()
print('Connected:', client.test_connection())
"
```

**SSL certificate issues:**
```bash
# Disable SSL verification
docker run -d \
  --name mcp-graylog \
  -p 8000:8000 \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  -e GRAYLOG_VERIFY_SSL=false \
  mcp-graylog:latest
```

### Cursor Integration Issues

**MCP server not recognized:**
- Restart Cursor after configuration changes
- Check Cursor's developer console for MCP errors
- Verify the Docker image exists: `docker images | grep mcp-graylog`
- Test the container manually: `docker run --rm mcp-graylog:latest`
- Check entrypoint functionality: `docker run --rm mcp-graylog:latest ./entrypoint.sh`

**Environment variable conflicts:**
- Use `env: {}` in Cursor config if using Option C (inline environment variables)
- Pass environment variables through Cursor config if using Option A
- Check for duplicate environment variable definitions
- Ensure Docker image is built with correct default environment variables if using Option B

### Common Build Issues

**Build fails with dependency errors:**
```bash
# Clean build with no cache
docker build --no-cache -t mcp-graylog .

# Check if pyproject.toml is valid
docker run --rm -v $(pwd):/app python:3.11-slim bash -c "cd /app && pip install -e ."
```

**Permission issues:**
```bash
# Build with different user
docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) -t mcp-graylog .
```

**Platform-specific issues:**
```bash
# Force platform
docker build --platform linux/amd64 -t mcp-graylog .

# Use buildx for multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t mcp-graylog .
```

### Pydantic Import Errors

**If you see `PydanticImportError: BaseSettings has been moved to pydantic-settings`:**
```bash
# Run the installation script
./install_deps.sh

# Ensure pydantic-settings>=2.0.0 is installed
pip install pydantic-settings>=2.0.0

# Test the fix
make test-pydantic
```

### FastMCP API Errors

**If you see `AttributeError: 'FastMCP' object has no attribute 'function'`:**
The API has been updated to use `@app.tool()` instead of `@app.function()`

```bash
# Test the fixes
make test-fixes
```

## API Reference

### Core Functions

#### `search_logs`
Search logs using Elasticsearch query syntax.

**Parameters:**
- `query` (string): Search query in Elasticsearch syntax
- `time_range` (string, optional): Time range (e.g., '1h', '24h', '7d')
- `fields` (array, optional): Fields to return
- `limit` (integer, optional): Maximum number of results (default: 50)
- `offset` (integer, optional): Result offset (default: 0)
- `sort` (string, optional): Sort field
- `sort_direction` (string, optional): Sort direction (asc/desc, default: desc)
- `stream_id` (string, optional): Stream ID to search in

**Example:**
```python
{
    "query": "level:ERROR",
    "time_range": "24h",
    "limit": 100
}
```

#### `search_stream_logs`
Search logs within a specific Graylog stream.

**Parameters:**
- `stream_id` (string): The ID of the stream to search in
- `query` (string): Search query
- `time_range` (string, optional): Time range (default: '1h')
- `fields` (array, optional): Fields to return
- `limit` (integer, optional): Maximum number of results (default: 50)

**Example:**
```python
{
    "stream_id": "5abb3f2f7bb9fd00011595fe",
    "query": "level:ERROR",
    "time_range": "24h",
    "limit": 10
}
```

#### `get_log_statistics`
Get log statistics and aggregations.

**Parameters:**
- `query` (string): Search query
- `time_range` (string): Time range
- `aggregation_type` (string): Aggregation type (terms, date_histogram, etc.)
- `field` (string): Field to aggregate on
- `size` (integer, optional): Number of buckets (default: 10)
- `interval` (string, optional): Time interval for date histograms

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
- `stream_name` (string): Partial or full stream name to search for

**Example:**
```python
search_streams_by_name("1c_eventlog")
```

#### `get_stream_info`
Get detailed information about a specific Graylog stream.

**Parameters:**
- `stream_id` (string): The ID of the stream to get information for

**Example:**
```python
get_stream_info("5abb3f2f7bb9fd00011595fe")
```

### Analysis Functions

#### `get_error_logs`
Get error logs from the last specified time range.

**Parameters:**
- `time_range` (string, optional): Time range to search (default: '1h')
- `limit` (integer, optional): Maximum number of results (default: 100)

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
- `stream_id` (string): The ID of the stream to get the last event from
- `time_range` (string, optional): Time range to search in (default: '1h')

**Example:**
```python
{
    "stream_id": "5abb3f2f7bb9fd00011595fe",
    "time_range": "1h"
}
```

## Best Practices

### 1. Security

#### Use Username/Password Authentication
```bash
docker run -d \
  --name mcp-graylog \
  -p 8000:8000 \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  mcp-graylog:latest
```

#### Use Docker Secrets (Production)
```bash
# Create secret
echo "your-password" | docker secret create graylog_password -

# Use secret in container
docker run -d \
  --name mcp-graylog \
  -p 8000:8000 \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  --secret graylog_password \
  mcp-graylog:latest
```

#### Network Security
```bash
# Use custom network
docker network create mcp-network

# Run container on custom network
docker run -d \
  --name mcp-graylog \
  --network mcp-network \
  -p 8000:8000 \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  mcp-graylog:latest
```

### 2. Performance

#### Resource Limits
```bash
docker run -d \
  --name mcp-graylog \
  -p 8000:8000 \
  --memory=512m \
  --cpus=1.0 \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  mcp-graylog:latest
```

#### Volume Mounting (for persistent logs)
```bash
docker run -d \
  --name mcp-graylog \
  -p 8000:8000 \
  -v /path/to/logs:/app/logs \
  -e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
  -e GRAYLOG_USERNAME=your-username \
  -e GRAYLOG_PASSWORD=your-password \
  mcp-graylog:latest
```

### 3. Monitoring

#### Health Checks
```bash
# Manual health check
curl http://localhost:8000/health_check

# Automated health check
docker exec mcp-graylog python -c "
import requests
response = requests.get('http://localhost:8000/health_check')
print('Health:', response.json())
"
```

#### Log Monitoring
```bash
# View container logs (now with entrypoint logging)
docker logs mcp-graylog

# Follow logs in real-time
docker logs -f mcp-graylog

# View logs with timestamps
docker logs -t mcp-graylog

# View entrypoint-specific logs
docker logs mcp-graylog | grep -E "(Starting|Checking|Validating|Setup|ERROR|WARNING)"

# View application logs only
docker logs mcp-graylog | grep -v -E "(Starting|Checking|Validating|Setup)"
```

### 4. Versioning
- Use semantic versioning for tags
- Keep `latest` tag updated
- Use git commit hashes for development builds

### 5. Testing
- Test builds in CI/CD
- Verify functionality after build
- Test with different configurations
- Validate security compliance

## Support

### For Build Issues
- Check Docker logs: `docker build --progress=plain -t mcp-graylog .`
- Verify dependencies: `pip install -e .`
- Test locally before pushing
- Use build cache for faster builds

### For Container Issues
- Test Graylog connection: Use the `test_connection` function in Cursor
- Verify environment variables: `docker run --rm mcp-graylog:latest env | grep GRAYLOG`
- Test container functionality: `docker run --rm mcp-graylog:latest`
- Check entrypoint functionality: `docker run --rm mcp-graylog:latest ./entrypoint.sh`

### For Cursor Integration Issues
- Restart Cursor after configuration changes
- Check Cursor's developer console for MCP errors
- Verify the Docker image exists: `docker images | grep mcp-graylog`
- Test the container manually: `docker run --rm mcp-graylog:latest`
- Check entrypoint functionality: `docker run --rm mcp-graylog:latest ./entrypoint.sh`

## License

MIT License - see LICENSE file for details. 