# MCP Graylog

MCP Graylog is a Model Context Protocol server for querying Graylog 6+ from AI
assistants. The default transport is Codex stdio. Streamable HTTP is available
only when you explicitly opt in for a remote, shared, or containerized runtime.

## Install Dependencies

Use Python 3.11 or newer. If you are new to Python projects, the safest setup is
to keep this server in its own virtual environment.

1. Install Python 3.11+ and `uv`.

   On macOS with Homebrew:

   ```sh
   brew install python@3.11 uv
   ```

   If Python is already installed, you can install `uv` with pip:

   ```sh
   python3 -m pip install --user uv
   ```

2. Create and activate a virtual environment from the repository root:

   ```sh
   uv venv venv --python 3.11
   source venv/bin/activate
   ```

3. Install the server dependencies:

   ```sh
   uv pip install -e .
   ```

   For development, tests, linting, and type checks, install the dev extras:

   ```sh
   uv pip install -e ".[dev]"
   ```

4. Check that the command is available:

   ```sh
   uv run mcp-graylog --help
   ```

5. If you installed the dev extras, run the test suite:

   ```sh
   uv run pytest -q
   ```

## Quick Start: Codex Stdio

Install the project dependencies, then add this server to your Codex config:

```toml
[mcp_servers.graylog]
command = "uv"
args = ["run", "mcp-graylog"]

[mcp_servers.graylog.env]
GRAYLOG_ENDPOINT = "https://graylog.example.com"
GRAYLOG_TOKEN = "gl2-your-token"
MCP_SERVER_TRANSPORT = "stdio"
```

Run the command from this repository when Codex starts the MCP server:

```sh
uv run mcp-graylog
```

Token authentication with `GRAYLOG_TOKEN` is preferred. Legacy basic
credentials are still supported by the runtime for older installations, but new
setups should use a Graylog access token.

## MCP Client Configuration Examples

All local client examples use stdio. Run them from this repository checkout, or
replace `uv` with an absolute command that can start `mcp-graylog` in your
environment.

### Codex

Add this to `~/.codex/config.toml`:

```toml
[mcp_servers.graylog]
command = "uv"
args = ["run", "mcp-graylog"]

[mcp_servers.graylog.env]
GRAYLOG_ENDPOINT = "https://graylog.example.com"
GRAYLOG_TOKEN = "gl2-your-token"
MCP_SERVER_TRANSPORT = "stdio"
```

### Claude Code

For a project-shared server, add `.mcp.json` at the repository root:

```json
{
  "mcpServers": {
    "graylog": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "mcp-graylog"],
      "env": {
        "GRAYLOG_ENDPOINT": "https://graylog.example.com",
        "GRAYLOG_TOKEN": "gl2-your-token",
        "MCP_SERVER_TRANSPORT": "stdio"
      }
    }
  }
}
```

Equivalent CLI setup:

```sh
claude mcp add-json graylog '{"type":"stdio","command":"uv","args":["run","mcp-graylog"],"env":{"GRAYLOG_ENDPOINT":"https://graylog.example.com","GRAYLOG_TOKEN":"gl2-your-token","MCP_SERVER_TRANSPORT":"stdio"}}'
```

### Cursor

Add `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` globally:

```json
{
  "mcpServers": {
    "graylog": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "mcp-graylog"],
      "env": {
        "GRAYLOG_ENDPOINT": "https://graylog.example.com",
        "GRAYLOG_TOKEN": "gl2-your-token",
        "MCP_SERVER_TRANSPORT": "stdio"
      }
    }
  }
}
```

### OpenCode

Add this to `opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "graylog": {
      "type": "local",
      "command": ["uv", "run", "mcp-graylog"],
      "environment": {
        "GRAYLOG_ENDPOINT": "https://graylog.example.com",
        "GRAYLOG_TOKEN": "gl2-your-token",
        "MCP_SERVER_TRANSPORT": "stdio"
      },
      "enabled": true
    }
  }
}
```

### Hermes

Add this to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  graylog:
    command: "uv"
    args: ["run", "mcp-graylog"]
    env:
      GRAYLOG_ENDPOINT: "https://graylog.example.com"
      GRAYLOG_TOKEN: "gl2-your-token"
      MCP_SERVER_TRANSPORT: "stdio"
```

Run `/reload-mcp` in Hermes after changing the file.

### OpenClaw

Add this to `~/.openclaw/openclaw.json` under `mcp.servers`, or use
`openclaw mcp set graylog '<json>'` with the same server object:

```json
{
  "mcp": {
    "servers": {
      "graylog": {
        "command": "uv",
        "args": ["run", "mcp-graylog"],
        "env": {
          "GRAYLOG_ENDPOINT": "https://graylog.example.com",
          "GRAYLOG_TOKEN": "gl2-your-token",
          "MCP_SERVER_TRANSPORT": "stdio"
        }
      }
    }
  }
}
```

## Streamable HTTP

Use Streamable HTTP only when the server must be reachable from another process
or host:

```sh
GRAYLOG_ENDPOINT="https://graylog.example.com" \
GRAYLOG_TOKEN="gl2-your-token" \
uv run mcp-graylog --transport streamable-http --host 0.0.0.0 --port 8000 --path /mcp
```

The equivalent environment setting is:

```sh
MCP_SERVER_TRANSPORT=streamable-http
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_PATH=/mcp
```

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `GRAYLOG_ENDPOINT` | yes | - | Base URL for Graylog, without embedded credentials. |
| `GRAYLOG_TOKEN` | yes for new setups | - | Preferred Graylog access token. |
| `GRAYLOG_VERIFY_SSL` | no | `true` | Verify TLS certificates. |
| `GRAYLOG_TIMEOUT` | no | `30` | Graylog HTTP timeout in seconds. |
| `MCP_SERVER_TRANSPORT` | no | `stdio` | `stdio` or `streamable-http`. |
| `MCP_SERVER_HOST` | no | `127.0.0.1` | Streamable HTTP bind host. |
| `MCP_SERVER_PORT` | no | `8000` | Streamable HTTP bind port. |
| `MCP_SERVER_PATH` | no | `/mcp` | Streamable HTTP MCP path. |
| `LOG_LEVEL` | no | `INFO` | Server log level. |

## Graylog 6+ API Compatibility

The server uses the current Graylog Search Scripting and system APIs:

- `POST /api/search/messages`
- `POST /api/search/aggregate`
- `GET /api/streams`
- `GET /api/streams/{stream_id}`
- `GET /api/system`

It does not use the legacy universal search API. Search payloads use `query`,
`timerange`, `streams`, `fields`, `size`, and `from`.

## MCP Tools

- `search_logs(search)` searches messages with a typed
  `MessageSearchInput`.
- `search_stream_logs(stream_id, search)` searches messages in one stream.
- `aggregate_logs(aggregation)` runs grouped aggregations with
  `AggregateLogsInput`.
- `list_streams()` returns available Graylog streams.
- `get_stream_info(stream_id)` returns one stream definition.
- `search_streams_by_name(stream_name)` filters streams locally by title.
- `get_system_info()` returns Graylog system information.
- `get_error_logs(hours=1, limit=100)` searches recent error and critical logs.
- `get_log_count_by_level(hours=1)` aggregates recent logs by `level`.

### Tool Input Examples

```json
{
  "query": "level:ERROR",
  "timerange": {"value": 1, "unit": "h"},
  "streams": [],
  "fields": ["timestamp", "source", "level", "message"],
  "limit": 50,
  "offset": 0
}
```

```json
{
  "query": "*",
  "timerange": {"keyword": "Last 24 hours"},
  "field": "source",
  "metric": "count",
  "limit": 10
}
```

```json
{
  "stream_id": "000000000000000000000001",
  "search": {
    "query": "source:api",
    "timerange": {"value": 24, "unit": "h"},
    "fields": ["timestamp", "source", "message"],
    "limit": 25,
    "offset": 0
  }
}
```

## Development

```sh
uv sync --extra dev
uv run pytest
uv run ruff check .
```

The package entrypoint is `mcp-graylog`, provided by `mcp_graylog.cli:main`.
