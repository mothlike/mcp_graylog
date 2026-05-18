#!/bin/sh
set -eu

if [ -x "./venv/bin/mcp-graylog" ]; then
  exec ./venv/bin/mcp-graylog "$@"
fi

exec mcp-graylog "$@"
