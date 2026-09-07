# MCP Graylog Reference

This repository provides an MCP server for Graylog 6+. Codex stdio is the
primary transport. Streamable HTTP is opt-in for shared, remote, or container
deployments.

## Installing Dependencies

Requirements:

- Python 3.11 or newer.
- `uv` for virtual environment and dependency management.
- A Graylog access token for real queries.

Recommended setup for inexperienced users:

1. Install Python 3.11+ and `uv`.

   On macOS with Homebrew:

   ```sh
   brew install python@3.11 uv
   ```

   If Python is already available:

   ```sh
   python3 -m pip install --user uv
   ```

2. Create a project-local virtual environment:

   ```sh
   uv venv venv --python 3.11
   source venv/bin/activate
   ```

3. Install runtime dependencies:

   ```sh
   uv pip install -e .
   ```

4. Install developer dependencies when you need tests, linting, or type checks:

   ```sh
   uv pip install -e ".[dev]"
   ```

5. Verify the installation:

   ```sh
   uv run mcp-graylog --help
   uv run pytest -q
   ```

## Codex Stdio

Add this to the Codex config from the repository checkout:

```toml
[mcp_servers.graylog]
command = "uv"
args = ["run", "mcp-graylog"]

[mcp_servers.graylog.env]
GRAYLOG_ENDPOINT = "https://graylog.example.com"
GRAYLOG_TOKEN = "gl2-your-token"
MCP_SERVER_TRANSPORT = "stdio"
```

Start command:

```sh
uv run mcp-graylog
```

## MCP Client Configuration Examples

### Codex

`~/.codex/config.toml`:

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

Project `.mcp.json`:

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

CLI equivalent:

```sh
claude mcp add-json graylog '{"type":"stdio","command":"uv","args":["run","mcp-graylog"],"env":{"GRAYLOG_ENDPOINT":"https://graylog.example.com","GRAYLOG_TOKEN":"gl2-your-token","MCP_SERVER_TRANSPORT":"stdio"}}'
```

### Cursor

Project `.cursor/mcp.json` or global `~/.cursor/mcp.json`:

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

`opencode.jsonc`:

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

`~/.hermes/config.yaml`:

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

`~/.openclaw/openclaw.json`:

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

The equivalent OpenClaw CLI form is
`openclaw mcp set graylog '{"command":"uv","args":["run","mcp-graylog"],"env":{"GRAYLOG_ENDPOINT":"https://graylog.example.com","GRAYLOG_TOKEN":"gl2-your-token","MCP_SERVER_TRANSPORT":"stdio"}}'`.

## Streamable HTTP

Use Streamable HTTP only when stdio is not appropriate:

```sh
GRAYLOG_ENDPOINT="https://graylog.example.com" \
GRAYLOG_TOKEN="gl2-your-token" \
MCP_SERVER_ALLOWED_HOSTS="mcp.example.com,mcp.example.com:*" \
uv run mcp-graylog --transport streamable-http --host 0.0.0.0 --port 8000 --path /mcp
```

Streamable HTTP validates the `Host` header. Set
`MCP_SERVER_ALLOWED_HOSTS` to a comma-separated list of public hostnames or IP
addresses. Include `hostname:*` when the exposed port can vary. Browser clients
must also list their origins in `MCP_SERVER_ALLOWED_ORIGINS`.
Set `MCP_SERVER_DNS_REBINDING_PROTECTION=false` to accept any Host and Origin
only when a trusted reverse proxy performs equivalent validation.

Transport selection is explicit:

- `stdio`: local Codex integration, default.
- `streamable-http`: remote, shared, or container mode.

## Authentication

Use `GRAYLOG_TOKEN` for new installations. The runtime keeps a legacy basic-auth
fallback for older environments, but examples and setup scripts are token-first.

## Graylog Endpoints

The Graylog client calls:

- `POST /api/search/messages`
- `POST /api/search/aggregate`
- `GET /api/streams`
- `GET /api/streams/{stream_id}`
- `GET /api/system`

Message searches use `query`, `timerange`, `streams`, `fields`, `size`, and
`from`. Aggregations use `query`, `timerange`, `group_by`, and `metrics`.

## Tool Inputs

`search_logs(search)` accepts:

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

`search_stream_logs(stream_id, search)` accepts a stream id plus the same search
shape:

```json
{
  "stream_id": "000000000000000000000001",
  "search": {
    "query": "*",
    "timerange": {"value": 24, "unit": "h"},
    "fields": ["timestamp", "source", "message"],
    "limit": 25,
    "offset": 0
  }
}
```

`aggregate_logs(aggregation)` accepts:

```json
{
  "query": "*",
  "timerange": {"value": 24, "unit": "h"},
  "streams": [],
  "field": "level",
  "metric": "count",
  "limit": 10
}
```

Available helper tools:

- `list_streams()`
- `get_stream_info(stream_id)`
- `search_streams_by_name(stream_name)`
- `get_system_info()`
- `get_error_logs(hours=1, limit=100)`
- `get_log_count_by_level(hours=1)`

## Time Ranges

Typed time ranges are model-shaped:

- Relative: `{"value": 1, "unit": "h"}`
- Absolute: `{"from": "2026-05-18T00:00:00Z", "to": "2026-05-18T01:00:00Z"}`
- Keyword: `{"keyword": "Last 15 minutes"}`
