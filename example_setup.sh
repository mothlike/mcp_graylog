#!/bin/sh
# Token-first setup example for MCP Graylog.

set -eu

export GRAYLOG_ENDPOINT="${GRAYLOG_ENDPOINT:-https://your-graylog-server:9000}"
export GRAYLOG_TOKEN="${GRAYLOG_TOKEN:-gl2-your-token}"
export GRAYLOG_VERIFY_SSL="${GRAYLOG_VERIFY_SSL:-true}"
export GRAYLOG_TIMEOUT="${GRAYLOG_TIMEOUT:-30}"

export MCP_SERVER_TRANSPORT="${MCP_SERVER_TRANSPORT:-stdio}"
export MCP_SERVER_HOST="${MCP_SERVER_HOST:-127.0.0.1}"
export MCP_SERVER_PORT="${MCP_SERVER_PORT:-8000}"
export MCP_SERVER_PATH="${MCP_SERVER_PATH:-/mcp}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

printf '%s\n' "MCP Graylog environment:"
printf '  GRAYLOG_ENDPOINT=%s\n' "$GRAYLOG_ENDPOINT"
printf '  GRAYLOG_TOKEN=%s\n' '[set]'
printf '  MCP_SERVER_TRANSPORT=%s\n' "$MCP_SERVER_TRANSPORT"

printf '\n%s\n' "Codex stdio command:"
printf '  uv run mcp-graylog\n'

printf '\n%s\n' "Streamable HTTP command:"
printf '  uv run mcp-graylog --transport streamable-http --host %s --port %s --path %s\n' \
  "$MCP_SERVER_HOST" "$MCP_SERVER_PORT" "$MCP_SERVER_PATH"
